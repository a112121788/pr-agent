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


def _pull_path(pr_url: str) -> tuple[str, str, str]:
    """Return owner, repo, and number. Enterprise URLs keep the real repo before /pulls/."""
    match = re.search(r"/([^/]+)/([^/]+)/pulls/(\d+)(?:$|[/?#])", pr_url)
    if not match:
        raise ValueError("无法识别 Gitee 拉取请求地址")
    return match.group(1), match.group(2), match.group(3)


def pull_detail(pr_url: str) -> dict:
    """Read the title, author, and branches shown at the top of the pipeline."""
    owner, repo, number = _pull_path(pr_url)
    payload = _client().request("GET", f"/repos/{owner}/{repo}/pulls/{number}")
    if not isinstance(payload, dict):
        raise ValueError("Gitee 没有返回这张拉取请求")
    user = payload.get("user") or {}
    head = payload.get("head") or {}
    base = payload.get("base") or {}
    state = payload.get("state") or ""
    if payload.get("merged"):
        state_label = "已合并"
    elif state == "open":
        state_label = "开放中"
    elif state == "closed":
        state_label = "已关闭"
    else:
        state_label = state or "未知状态"
    return {
        "number": payload.get("number") or number,
        "title": payload.get("title") or "",
        "author": user.get("login") if isinstance(user, dict) else "",
        "head": head.get("ref") if isinstance(head, dict) else "",
        "base": base.get("ref") if isinstance(base, dict) else "",
        "url": payload.get("html_url") or pr_url,
        "state_label": state_label,
    }


def pull_comments(pr_url: str) -> list[dict]:
    """Read published comments oldest first, following pages so a new verdict is not hidden."""
    owner, repo, number = _pull_path(pr_url)
    comments = []
    for page in range(1, 21):
        payload = _client().request(
            "GET", f"/repos/{owner}/{repo}/pulls/{number}/comments",
            params={"page": page, "per_page": 100, "direction": "asc"},
        )
        if not isinstance(payload, list) or not payload:
            break
        comments.extend(item for item in payload if isinstance(item, dict))
        if len(payload) < 100:
            break
    return comments


def open_pulls(owner: str, repo: str) -> list[dict]:
    """Return the open pull requests for one watched repository."""
    payload = _client().request("GET", f"/repos/{owner}/{repo}/pulls", params={"state": "open"})
    if not isinstance(payload, list):
        return []
    pulls = []
    for item in payload:
        if not item.get("html_url"):
            continue
        head = item.get("head") or {}
        pulls.append({
            "number": item.get("number"),
            "title": item.get("title") or "",
            "body": item.get("body") or "",
            "url": item.get("html_url") or "",
            "sha": head.get("sha") if isinstance(head, dict) else "",
        })
    return pulls


async def run_review(pr_url: str, command: str) -> str:
    """Run one existing command. Merge remains outside this cockpit."""
    if command not in COMMANDS:
        raise ValueError("不支持的操作")
    await PRAgent().handle_request(pr_url, f"/{command}")
    return f"已完成 {command}"
