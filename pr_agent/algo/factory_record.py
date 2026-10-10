"""Small records that connect evidence, verdict, and merge without calling a model."""

from __future__ import annotations

import re
from collections.abc import Mapping

VERDICTS = ("放行", "退回", "等待")
COMMIT_LINE = re.compile(r"^提交号：(?P<sha>[0-9a-fA-F]{7,64})$", re.MULTILINE)
VERDICT_LINE = re.compile(r"^判定：(?P<verdict>放行|退回|等待)$", re.MULTILINE)


def commit_record(head_sha: str) -> str:
    """Return the one-line record placed above a piece of evidence."""
    return f"提交号：{head_sha or '未读取'}"


def bind_commit(body: str, head_sha: str) -> str:
    """Prefix one comment with its commit. An existing record is left unchanged."""
    if body.startswith("提交号："):
        return body
    return f"{commit_record(head_sha)}\n\n{body}"


def parse_verdict(args) -> str:
    """Return one allowed verdict word and reject every other phrase."""
    words = [str(arg).strip() for arg in args or [] if str(arg).strip()]
    if len(words) != 1 or words[0] not in VERDICTS:
        raise ValueError("请使用 /verdict 放行、/verdict 退回 或 /verdict 等待")
    return words[0]


def render_verdict(verdict: str, head_sha: str, author: str) -> str:
    """Render a human verdict. Model wording never reaches this record."""
    return "\n".join([
        "## 判定记录",
        "",
        f"- 判定：{verdict}",
        f"- 提交号：{head_sha or '未读取'}",
        f"- 判定人：{author or '未读取'}",
    ])


def render_merge_check(verdict: str | None, verdict_sha: str, current_sha: str) -> str:
    """Tell a person whether they may merge. This command never merges."""
    if verdict == "放行" and verdict_sha and verdict_sha == current_sha:
        result = "可以由人合并"
        reason = "当前提交已有放行判定。"
    elif verdict is None:
        result = "不能汇入"
        reason = "还没有当前提交的判定。"
    elif verdict_sha != current_sha:
        result = "不能汇入"
        reason = "判定对应的提交已经变化。"
    else:
        result = "不能汇入"
        reason = f"最新判定是{verdict}。"
    return "\n".join([
        "## 汇入检查",
        "",
        f"- 结果：{result}",
        f"- 原因：{reason}",
        f"- 当前提交号：{current_sha or '未读取'}",
    ])


def latest_verdict(comments) -> tuple[str | None, str]:
    """Read the newest valid verdict comment. Review text cannot satisfy this check."""
    for comment in comments or []:
        body = getattr(comment, "body", "") or ""
        verdict = VERDICT_LINE.search(body)
        commit = COMMIT_LINE.search(body)
        if verdict and commit and "判定记录" in body:
            return verdict.group("verdict"), commit.group("sha")
    return None, ""


def latest_evidence_sha(comments) -> str:
    """Read the newest evidence comment. A verdict record is not evidence."""
    for comment in comments or []:
        body = getattr(comment, "body", "") or ""
        if "判定记录" in body or "汇入检查" in body or "受理记录" in body:
            continue
        match = COMMIT_LINE.search(body)
        if match and ("PR 审查指南" in body or "PR 代码建议" in body):
            return match.group("sha")
    return ""


def render_status(intent: str, evidence_sha: str, verdict: str | None, verdict_sha: str, current_sha: str) -> str:
    """Show which stage owns the next action. This command changes no other record."""
    evidence_current = bool(evidence_sha and evidence_sha == current_sha)
    verdict_current = bool(verdict and verdict_sha == current_sha)
    if not intent:
        stage = "受理"
        action = "提出人运行 /intake"
    elif not evidence_current:
        stage = "取证"
        action = "运行 /review 或 /improve"
    elif not verdict_current:
        stage = "判定"
        action = "负责人运行 /verdict"
    elif verdict == "放行":
        stage = "汇入"
        action = "有权限的人在 Gitee 上合并"
    else:
        stage = "判定"
        action = f"最新判定是{verdict}，先不要合并"
    return "\n".join([
        "## 工厂状态",
        "",
        f"- 当前段：{stage}",
        f"- 下一步：{action}",
        f"- 受理：{intent or '缺失'}",
        f"- 证据提交号：{evidence_sha or '缺失'}",
        f"- 判定：{verdict or '缺失'}",
        f"- 当前提交号：{current_sha or '未读取'}",
    ])


def _comment_body(comment) -> str:
    if isinstance(comment, Mapping):
        return comment.get("body") or ""
    return getattr(comment, "body", "") or ""


def _classify_comment(body: str) -> tuple[str, str, str] | None:
    """Return kind, stage, and short summary for one factory comment."""
    if "受理记录" in body:
        intent = re.search(r"^- 意图：(?P<intent>.+)$", body, re.MULTILINE)
        summary = intent.group("intent") if intent else ""
        return "受理", "受理", summary
    if "判定记录" in body:
        verdict = VERDICT_LINE.search(body)
        summary = verdict.group("verdict") if verdict else ""
        return "判定", "判定", summary
    if "汇入检查" in body:
        return "汇入检查", "汇入", "汇入检查"
    if "PR 审查指南" in body:
        return "审查", "取证", "PR 审查指南"
    if "PR 代码建议" in body:
        return "建议", "取证", "PR 代码建议"
    return None


def records_from_comments(pr_url: str, comments) -> list:
    """Turn published Gitee comments into factory records. Ordinary prose is ignored."""
    from pr_agent.dashboard.store import FactoryRecord

    records = []
    for comment in comments or []:
        body = _comment_body(comment)
        classified = _classify_comment(body)
        if not classified:
            continue
        kind, stage, summary = classified
        commit = COMMIT_LINE.search(body)
        sha = commit.group("sha") if commit else ""
        created = comment.get("created_at", "") if isinstance(comment, Mapping) else ""
        body_text = "\n".join(line for line in body.splitlines() if not line.startswith("提交号：")).strip()
        records.append(FactoryRecord(
            pr_url, kind, stage,
            summary if kind == "受理" else "",
            summary if kind == "判定" else "",
            sha, body_text or summary, created,
        ))
    return records


def comment_feed(comments) -> list[dict]:
    """Return every comment a person should see, including ones that are not factory records."""
    items = []
    for comment in comments or []:
        body = _comment_body(comment).strip()
        if not body:
            continue
        if isinstance(comment, Mapping):
            created = str(comment.get("created_at") or "")
            user = comment.get("user") or {}
            author = user.get("login") if isinstance(user, Mapping) else ""
            path = str(comment.get("path") or "")
            line = comment.get("new_line") or ""
            where = f"{path}:{line}" if path and line else path
        else:
            created, author, where = "", "", ""
        classified = _classify_comment(body)
        if classified:
            kind, stage, _summary = classified
            text = "\n".join(line for line in body.splitlines() if not line.startswith("提交号：")).strip()
        elif body.startswith("Failed to review PR"):
            kind, stage = "审查失败", "失败"
            rest = body.removeprefix("Failed to review PR").strip()
            text = "审查没有完成。" if not rest else f"审查没有完成。\n{rest}"
        else:
            kind, stage = "评论", "评论"
            text = "\n".join(line for line in body.splitlines() if not line.startswith("提交号：")).strip()
        items.append({
            "stage": stage,
            "kind": kind,
            "text": text or body,
            "created_at": created,
            "author": author or "",
            "where": where,
        })
    return items


def latest_intake_intent(comments) -> str:
    """Read an explicitly recorded intake intent. Ordinary prose never counts."""
    for comment in comments or []:
        body = getattr(comment, "body", "") or ""
        match = re.search(r"^- 意图：(?P<intent>新业务|旧版迭代|新版升级|双线)$", body, re.MULTILINE)
        if match and "受理记录" in body:
            return match.group("intent")
    return ""
