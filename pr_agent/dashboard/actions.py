"""Read watched Gitee repositories and start one evidence command."""

from __future__ import annotations

import re

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.config_loader import get_settings
from pr_agent.git_providers.gitee_provider import _GiteeApiClient

_REPO = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")
COMMANDS = ("review", "improve", "describe", "status")


def parse_repo(value: str) -> tuple[str, str]:
    """Accept owner/repo and reject anything that could change the API path."""
    owner, separator, repo = value.strip().partition("/")
    if not separator or not _REPO.fullmatch(owner) or not _REPO.fullmatch(repo):
        raise ValueError("仓库格式应为 owner/repo")
    return owner, repo


def _client() -> _GiteeApiClient:
    token = get_settings().get("GITEE.PERSONAL_ACCESS_TOKEN", "")
    if not token:
        raise ValueError("未配置 Gitee 令牌")
    return _GiteeApiClient(
        get_settings().get("GITEE.API_BASE", "") or "https://gitee.com/api/v5",
        token,
        verify_ssl=not bool(get_settings().get("GITEE.SKIP_SSL_VERIFICATION", False)),
        ca_cert=get_settings().get("GITEE.SSL_CA_CERT", "") or None,
    )


def open_pulls(owner: str, repo: str) -> list[dict]:
    """Return the open pull requests for one watched repository."""
    payload = _client().request("GET", f"/repos/{owner}/{repo}/pulls", params={"state": "open"})
    if not isinstance(payload, list):
        return []
    return [
        {"number": item.get("number"), "title": item.get("title") or "", "url": item.get("html_url") or ""}
        for item in payload if item.get("html_url")
    ]


async def run_review(pr_url: str, command: str) -> str:
    """Run one existing command. Merge remains outside this cockpit."""
    if command not in COMMANDS:
        raise ValueError("不支持的操作")
    await PRAgent().handle_request(pr_url, f"/{command}")
    return f"已完成 {command}"
