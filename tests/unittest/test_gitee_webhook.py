"""Offline routing tests for the Gitee webhook.

The suite signs payloads locally and stubs PRAgent, so it never contacts gitee.com or runs a model.
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from pr_agent.servers.gitee_app import (
    _command_from_note,
    _should_run_pull_request,
    get_body,
    gitee_signature_is_valid,
    gitee_webhook_signature,
    handle_request,
)

SECRET = "webhook-secret"
TIMESTAMP = "1576754827988"
NOW_MS = 1576754827988


def _request(body: dict, *, timestamp=TIMESTAMP, signature=None, secret=SECRET):
    encoded = json.dumps(body).encode("utf-8")
    headers = {}
    if timestamp is not None:
        headers["X-Gitee-Timestamp"] = timestamp
    if signature is not False:
        headers["X-Gitee-Token"] = gitee_webhook_signature(timestamp, secret) if signature is None else signature
    return SimpleNamespace(
        body=AsyncMock(return_value=encoded),
        json=AsyncMock(return_value=body),
        headers=headers,
    )


def _settings(secret=SECRET):
    return SimpleNamespace(get=lambda key, default=None: secret if key == "GITEE.WEBHOOK_SECRET" else default)


def test_signature_accepts_the_documented_digest_and_rejects_stale_timestamps():
    signature = gitee_webhook_signature(TIMESTAMP, SECRET)

    assert gitee_signature_is_valid(TIMESTAMP, signature, SECRET, now_ms=NOW_MS) is True
    assert gitee_signature_is_valid(TIMESTAMP, "rLEHLuZRIQHuTPeXMib9Czoq9dVXO4TsQcmQQHtjXHA=", SECRET) is False
    assert gitee_signature_is_valid(TIMESTAMP, signature, SECRET, now_ms=NOW_MS + 60 * 60 * 1000 + 1) is False


@pytest.mark.asyncio
async def test_missing_secret_rejects_every_webhook(monkeypatch):
    monkeypatch.setattr("pr_agent.servers.gitee_app.get_settings", lambda: _settings(secret=""))

    with pytest.raises(HTTPException) as error:
        await get_body(_request({"hook_name": "merge_request_hooks"}))

    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_bad_signature_is_rejected(monkeypatch):
    monkeypatch.setattr("pr_agent.servers.gitee_app.get_settings", lambda: _settings())

    with pytest.raises(HTTPException) as error:
        await get_body(_request({"hook_name": "merge_request_hooks"}, signature="not-the-signature"))

    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_valid_signature_returns_the_payload(monkeypatch):
    monkeypatch.setattr("pr_agent.servers.gitee_app.get_settings", lambda: _settings())
    monkeypatch.setattr("pr_agent.servers.gitee_app.time.time", lambda: NOW_MS / 1000)
    body = {"hook_name": "merge_request_hooks", "timestamp": TIMESTAMP}

    assert await get_body(_request(body)) == body


@pytest.mark.asyncio
async def test_opened_pull_request_runs_the_default_commands(monkeypatch):
    agent = SimpleNamespace(handle_request=AsyncMock())
    monkeypatch.setattr("pr_agent.servers.gitee_app.apply_repo_settings", lambda url: None)
    body = {
        "hook_name": "merge_request_hooks",
        "action": "open",
        "pull_request": {"html_url": "https://gitee.com/owner/repo/pulls/7", "state": "open"},
    }

    await handle_request(body, agent)

    assert [call.args for call in agent.handle_request.await_args_list] == [
        ("https://gitee.com/owner/repo/pulls/7", "/describe"),
        ("https://gitee.com/owner/repo/pulls/7", "/review"),
        ("https://gitee.com/owner/repo/pulls/7", "/improve"),
    ]


@pytest.mark.asyncio
async def test_pull_request_update_does_not_run_commands(monkeypatch):
    agent = SimpleNamespace(handle_request=AsyncMock())
    monkeypatch.setattr("pr_agent.servers.gitee_app.apply_repo_settings", lambda url: None)
    body = {
        "hook_name": "merge_request_hooks",
        "action": "update",
        "pull_request": {"html_url": "https://gitee.com/owner/repo/pulls/7", "state": "open"},
    }

    await handle_request(body, agent)

    agent.handle_request.assert_not_awaited()


@pytest.mark.asyncio
async def test_pull_request_comment_command_is_forwarded(monkeypatch):
    agent = SimpleNamespace(handle_request=AsyncMock())
    monkeypatch.setattr("pr_agent.servers.gitee_app.apply_repo_settings", lambda url: None)
    body = {
        "hook_name": "note_hooks",
        "noteable_type": "PullRequest",
        "comment": {"body": "  /review"},
        "pull_request": {"html_url": "https://gitee.com/owner/repo/pulls/7"},
    }

    await handle_request(body, agent)

    agent.handle_request.assert_awaited_once_with("https://gitee.com/owner/repo/pulls/7", "  /review")


@pytest.mark.asyncio
async def test_plain_comment_and_issue_comment_are_ignored(monkeypatch):
    agent = SimpleNamespace(handle_request=AsyncMock())
    monkeypatch.setattr("pr_agent.servers.gitee_app.apply_repo_settings", lambda url: None)

    await handle_request({
        "hook_name": "note_hooks",
        "noteable_type": "PullRequest",
        "comment": {"body": "looks good"},
        "pull_request": {"html_url": "https://gitee.com/owner/repo/pulls/7"},
    }, agent)
    await handle_request({
        "hook_name": "note_hooks",
        "noteable_type": "Issue",
        "comment": {"body": "/review"},
        "pull_request": {"html_url": "https://gitee.com/owner/repo/pulls/7"},
    }, agent)

    agent.handle_request.assert_not_awaited()


def test_routing_predicates_cover_closed_pull_requests_and_commands():
    closed = {"action": "open", "pull_request": {"state": "closed"}}
    assert _should_run_pull_request(closed) is False
    assert _command_from_note({"noteable_type": "Commit", "comment": {"body": "/review"}}) == ""
