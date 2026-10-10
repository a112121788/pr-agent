import base64
import copy
import hashlib
import hmac
import os
import time
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import unquote

from fastapi import APIRouter, Form, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from starlette.background import BackgroundTasks
from starlette.middleware import Middleware
from starlette_context import context
from starlette_context.middleware import RawContextMiddleware

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.config_loader import get_settings, global_settings
from pr_agent.dashboard.actions import parse_repo, run_review
from pr_agent.dashboard.drive import continue_pull, execute_registered
from pr_agent.dashboard.home import home_view
from pr_agent.dashboard.page import (
    build_id,
    pipeline_payload,
    render_conversation,
    render_conversation_body,
    render_dashboard,
)
from pr_agent.dashboard.store import FactoryRecord, FactoryStore, database_url, record_factory_event
from pr_agent.git_providers.utils import apply_repo_settings
from pr_agent.log import LoggingFormat, get_logger, setup_logger
from pr_agent.servers.request_body_limit import create_server_app
from pr_agent.servers.utils import get_pr_commands, is_command_comment
from pr_agent.telemetry.prometheus import attach_metrics_endpoint, prometheus_metrics_enabled

setup_logger(fmt=LoggingFormat.JSON, level=get_settings().get("CONFIG.LOG_LEVEL", "DEBUG"))
router = APIRouter()
_STATIC = Path(__file__).resolve().parents[1] / "dashboard" / "static"
_HOME_JS = _STATIC / "home.js"
_PIPELINE_JS = _STATIC / "pipeline.js"
_RUN_COMMANDS = {"review", "improve", "status"}

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


def _home_payload() -> dict:
    store = FactoryStore(database_url())
    store.setup()
    payload = home_view(store)
    payload["build"] = build_id()
    return payload


@router.get("/dashboard")
async def factory_dashboard():
    """Show the cockpit shell. Opening the page does not start a review."""
    return Response(render_dashboard(), media_type="text/html")


@router.get("/dashboard/static/home.js")
async def dashboard_home_script():
    """Serve the homepage client. It renders data from the JSON API."""
    return FileResponse(_HOME_JS, media_type="text/javascript")


@router.get("/dashboard/static/pipeline.js")
async def dashboard_pipeline_script():
    """Serve the pipeline client. It refreshes one pull request without reloading the page."""
    return FileResponse(_PIPELINE_JS, media_type="text/javascript")


@router.get("/dashboard/api/pr")
async def dashboard_pipeline(url: str):
    """Return one pipeline. The client replaces only that region."""
    if not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="无法识别拉取请求")
    return pipeline_payload(url)


@router.get("/dashboard/api/home")
async def dashboard_home():
    """Return the repositories and review states for the homepage client."""
    return _home_payload()


@router.post("/dashboard/api/repos")
async def dashboard_watch_repo(request: Request):
    """Register one repository and return the updated homepage payload."""
    body = await request.json()
    try:
        owner, name = parse_repo(str(body.get("repo") or ""))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    store = FactoryStore(database_url())
    store.setup()
    store.add_repo(owner, name)
    return _home_payload()


@router.post("/dashboard/api/repos/remove")
async def dashboard_forget_repo(request: Request):
    """Drop one watched repository and return the updated homepage payload."""
    body = await request.json()
    try:
        owner, name = parse_repo(f"{body.get('owner') or ''}/{body.get('repo') or ''}")
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    store = FactoryStore(database_url())
    store.setup()
    store.remove_repo(owner, name)
    return _home_payload()


@router.post("/dashboard/api/drive")
async def dashboard_drive(background_tasks: BackgroundTasks):
    """Start one batch pass and return the homepage payload. This does not reload the page."""
    store = FactoryStore(database_url())
    store.setup()
    execute_registered(store, start_review=_start_review(background_tasks))
    return _home_payload()


@router.post("/dashboard/api/run")
async def dashboard_run(request: Request, background_tasks: BackgroundTasks):
    """Queue one command and return its job. The client updates that row in place."""
    body = await request.json()
    pr_url = str(body.get("pr_url") or "")
    command = str(body.get("command") or "")
    if not pr_url.startswith("https://") or command not in _RUN_COMMANDS:
        raise HTTPException(status_code=400, detail="不支持的操作")
    store = FactoryStore(database_url())
    store.setup()
    job_id, created = store.claim_job(pr_url, command)
    status = "排队" if created else store.get_job(job_id)["status"]
    if created:
        background_tasks.add_task(_finish_review_job, job_id, pr_url, command)
    return {"job_id": job_id, "status": status, "created": created}


@router.get("/dashboard/api/jobs/{job_id}")
async def dashboard_job(job_id: int):
    """Return one review job so the homepage can update a single row."""
    store = FactoryStore(database_url())
    store.setup()
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="没有这条任务")
    return job


@router.post("/dashboard/repos")
async def watch_repo(repo: str = Form(...)):
    """Remember one owner/repo so its open pull requests appear in the cockpit."""
    owner, name = parse_repo(repo)
    store = FactoryStore(database_url())
    store.setup()
    store.add_repo(owner, name)
    return RedirectResponse("/dashboard", status_code=303)


def _start_review(background_tasks: BackgroundTasks):
    def start(pr_url: str, job_id: int, head_sha: str = ""):
        background_tasks.add_task(_finish_review_job, job_id, pr_url, "review", head_sha)

    return start


@router.post("/dashboard/drive")
async def drive_once(background_tasks: BackgroundTasks):
    """Run one autopilot pass. The decision function still gates every write."""
    store = FactoryStore(database_url())
    store.setup()
    execute_registered(store, start_review=_start_review(background_tasks))
    return RedirectResponse("/dashboard", status_code=303)


def _write_verdict(pr_url: str, verdict: str) -> str:
    """Publish one verdict record. This never calls the Gitee merge API."""
    from pr_agent.algo.factory_record import parse_verdict, render_verdict
    from pr_agent.git_providers import get_git_provider

    word = parse_verdict([verdict])
    provider = get_git_provider()(pr_url)
    sha = provider.get_pr_head_sha() or ""
    comment = render_verdict(word, sha, "驾驶舱")
    record_factory_event(FactoryRecord(
        pr_url, "判定", "判定", "", word, sha, "驾驶舱",
    ))
    if get_settings().config.publish_output:
        provider.publish_comment(comment)
    return word


@router.post("/dashboard/verdict")
async def submit_verdict(pr_url: str = Form(...), verdict: str = Form(...)):
    """Write one human verdict and return to the pipeline page."""
    _write_verdict(pr_url, verdict)
    return RedirectResponse(f"/dashboard/pr?url={pr_url}", status_code=303)


@router.post("/dashboard/api/verdict")
async def dashboard_verdict(request: Request):
    """Write one verdict and return JSON so the pipeline stays on this page."""
    body = await request.json()
    pr_url = str(body.get("pr_url") or "")
    if not pr_url.startswith("https://"):
        raise HTTPException(status_code=400, detail="无法识别拉取请求")
    try:
        word = _write_verdict(pr_url, str(body.get("verdict") or ""))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {"verdict": word, "pr_url": pr_url}


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
    request: Request,
    background_tasks: BackgroundTasks,
    pr_url: str = Form(...),
    command: str = Form(...),
):
    """Queue one command and return immediately. The worker updates the conversation."""
    store = FactoryStore(database_url())
    store.setup()
    job_id = store.begin_job(pr_url, command)
    if job_id is not None:
        background_tasks.add_task(_finish_review_job, job_id, pr_url, command)
    headers = {"X-Job-Id": str(job_id)} if job_id is not None else {}
    if request.headers.get("x-requested-with") == "fetch":
        return Response(render_conversation_body(pr_url), media_type="text/html", headers=headers)
    return RedirectResponse(f"/dashboard/pr?url={pr_url}", status_code=303, headers=headers)


async def _finish_review_job(job_id: int, pr_url: str, command: str, head_sha: str = ""):
    store = FactoryStore(database_url())
    store.finish_job(job_id, "运行中", "正在审查")
    try:
        summary = await run_review(pr_url, command)
        store.finish_job(job_id, "完成", summary)
    except Exception as error:
        store.finish_job(job_id, "失败", str(error))
        return
    if command == "review" and head_sha:
        continue_pull(store, pr_url, head_sha)


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
