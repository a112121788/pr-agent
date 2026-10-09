"""Small records that connect evidence, verdict, and merge without calling a model."""

from __future__ import annotations

import re

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


def latest_intake_intent(comments) -> str:
    """Read an explicitly recorded intake intent. Ordinary prose never counts."""
    for comment in comments or []:
        body = getattr(comment, "body", "") or ""
        match = re.search(r"^- 意图：(?P<intent>新业务|旧版迭代|新版升级|双线)$", body, re.MULTILINE)
        if match and "受理记录" in body:
            return match.group("intent")
    return ""
