import base64
import copy
import hashlib
import hmac
import os
import time
from typing import Any, Mapping
from urllib.parse import unquote

from fastapi import APIRouter, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from starlette.background import BackgroundTasks
from starlette.middleware import Middleware
from starlette_context import context
from starlette_context.middleware import RawContextMiddleware

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.config_loader import get_settings, global_settings
from pr_agent.dashboard.actions import parse_repo, run_review
from pr_agent.dashboard.page import render_conversation, render_conversation_body, render_dashboard
from pr_agent.dashboard.store import FactoryStore, database_url
from pr_agent.git_providers.utils import apply_repo_settings
from pr_agent.log import LoggingFormat, get_logger, setup_logger
from pr_agent.servers.request_body_limit import create_server_app
from pr_agent.servers.utils import get_pr_commands, is_command_comment
from pr_agent.telemetry.prometheus import attach_metrics_endpoint, prometheus_metrics_enabled

setup_logger(fmt=LoggingFormat.JSON, level=get_settings().get("CONFIG.LOG_LEVEL", "DEBUG"))
router = APIRouter()

_SIGNATURE_MAX_AGE_MS = 60 * 60 * 1000
_PULL_REQUEST_ACTIONS = {"open", "opened", "reopen", "reopened"}


def gitee_webhook_signature(timestamp: str, secret: str) -> str:
    """Return Gitee's HMAC-SHA256 signature for a timestamp and secret.

    Gitee documents the signed content as ``"<timestamp>\\n<secret>"`` and sends the Base64 digest.
    URL encoding is part of the bot-webhook recipe, so an encoded header is accepted after decoding.
    """
    digest = hmac.new(secret.encode("utf-8"), f"{timestamp}\n{secret}".encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")


def gitee_signature_is_valid(timestamp: str, signature: str, secret: str, now_ms: int | None = None) -> bool:
    """Check the signature and reject timestamps older than Gitee's one-hour window."""
    if not timestamp or not signature or not secret:
        return False
    try:
        timestamp_ms = int(timestamp)
    except (TypeError, ValueError):
        return False
    current_ms = int(time.time() * 1000) if now_ms is None else now_ms
    if abs(current_ms - timestamp_ms) > _SIGNATURE_MAX_AGE_MS:
        return False
    candidates = {signature}
    decoded = unquote(signature)
    if decoded != signature:
        candidates.add(decoded)
    expected = gitee_webhook_signature(timestamp, secret)
    return any(hmac.compare_digest(expected, candidate) for candidate in candidates)


def _pull_request_url(body: Mapping[str, Any]) -> str:
    pull_request = body.get("pull_request")
    if not isinstance(pull_request, Mapping):
        return ""
    html_url = pull_request.get("html_url")
    return html_url if isinstance(html_url, str) else ""


def _should_run_pull_request(body: Mapping[str, Any]) -> bool:
    action = str(body.get("action") or "").lower()
    if action not in _PULL_REQUEST_ACTIONS:
        return False
    pull_request = body.get("pull_request")
    state = str(pull_request.get("state") or "").lower() if isinstance(pull_request, Mapping) else ""
    return state in {"", "open", "opened"}


def _command_from_note(body: Mapping[str, Any]) -> str:
    if str(body.get("noteable_type") or "") != "PullRequest":
        return ""
    comment = body.get("comment")
    if not isinstance(comment, Mapping):
        return ""
    comment_body = comment.get("body")
    return comment_body if is_command_comment(comment_body) else ""


@router.get("/dashboard")
async def factory_dashboard():
    """Show the latest factory records. The page does not reveal the database URL."""
    return Response(render_dashboard(), media_type="text/html")


@router.post("/dashboard/repos")
async def watch_repo(repo: str = Form(...)):
    """Remember one owner/repo so its open pull requests appear in the cockpit."""
    owner, name = parse_repo(repo)
    store = FactoryStore(database_url())
    store.setup()
    store.add_repo(owner, name)
    return RedirectResponse("/dashboard", status_code=303)


@router.post("/dashboard/repos/remove")
async def forget_repo(owner: str = Form(...), repo: str = Form(...)):
    """Remove one watched repository without deleting its Gitee data or review history."""
    owner, repo = parse_repo(f"{owner}/{repo}")
    store = FactoryStore(database_url())
    store.setup()
    store.remove_repo(owner, repo)
    return RedirectResponse("/dashboard", status_code=303)


@router.get("/dashboard/pr")
async def pull_request_conversation(url: str):
    """Show one pull request's review as a conversation."""
    return Response(render_conversation(url), media_type="text/html")


@router.get("/dashboard/pr/fragment")
async def pull_request_fragment(url: str):
    """Return only the changing pipeline content so the page can refresh quietly."""
    return Response(render_conversation_body(url), media_type="text/html")


@router.post("/dashboard/run")
async def run_pull_request_command(
    background_tasks: BackgroundTasks, pr_url: str = Form(...), command: str = Form(...)
):
    """Queue one command and return immediately. The worker updates the conversation."""
    store = FactoryStore(database_url())
    store.setup()
    job_id = store.enqueue(pr_url, command)
    background_tasks.add_task(_finish_review_job, job_id, pr_url, command)
    return RedirectResponse(f"/dashboard/pr?url={pr_url}", status_code=303)


async def _finish_review_job(job_id: int, pr_url: str, command: str):
    store = FactoryStore(database_url())
    try:
        summary = await run_review(pr_url, command)
        store.finish_job(job_id, "完成", summary)
    except Exception as error:
        store.finish_job(job_id, "失败", str(error))


@router.post("/api/v1/gitee_webhooks")
async def handle_gitee_webhooks(background_tasks: BackgroundTasks, request: Request, response: Response):
    """Authenticate one Gitee webhook and queue its pull-request or comment command."""
    body = await get_body(request)
    context["settings"] = copy.deepcopy(global_settings)
    context["git_provider"] = {}
    background_tasks.add_task(handle_request, body)
    return {}


async def get_body(request: Request) -> dict:
    """Reject webhooks whose signature does not match the host secret.

    The signature is checked before the body is parsed. A forged request must not be able to
    force JSON parsing, and its body must not reach a log line.
    """
    secret = get_settings().get("GITEE.WEBHOOK_SECRET", None)
    if not secret:
        get_logger().error("Rejecting Gitee webhook: GITEE.WEBHOOK_SECRET is not configured")
        raise HTTPException(status_code=403, detail="Webhook secret not configured")

    timestamp = request.headers.get("X-Gitee-Timestamp", "")
    signature = request.headers.get("X-Gitee-Token", "")
    if not gitee_signature_is_valid(timestamp, signature, str(secret)):
        get_logger().error("Rejecting Gitee webhook: signature did not match")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        body = await request.json()
    except Exception as error:
        get_logger().error("Error parsing Gitee webhook body", artifact={"error": error})
        raise HTTPException(status_code=400, detail="Error parsing request body") from error
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Webhook body must be an object")
    return body


async def handle_request(body: Mapping[str, Any], agent: PRAgent | None = None):
    """Route a verified webhook to the commands it asks for."""
    agent = agent or PRAgent()
    hook_name = body.get("hook_name")
    pr_url = _pull_request_url(body)
    if not pr_url:
        get_logger().debug("Ignoring Gitee webhook without a pull request URL")
        return {}
    apply_repo_settings(pr_url)

    if hook_name == "merge_request_hooks" and _should_run_pull_request(body):
        for command in get_pr_commands("gitee"):
            await agent.handle_request(pr_url, command)
    elif hook_name == "note_hooks":
        command = _command_from_note(body)
        if command:
            await agent.handle_request(pr_url, command)
    return {}


middleware = [Middleware(RawContextMiddleware)]
if prometheus_metrics_enabled():
    attach_metrics_endpoint(router)
app = create_server_app(middleware=middleware)
app.include_router(router)


def start():
    """Start the Gitee webhook server."""
    port = int(os.environ.get("PORT", "3000"))
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    start()
