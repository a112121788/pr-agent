"""Small records that connect evidence, verdict, and merge without calling a model."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import SimpleNamespace

VERDICTS = ("放行", "退回", "等待")
COMMIT_LINE = re.compile(r"^(?:- )?提交号：(?P<sha>[0-9a-fA-F]{7,64})$", re.MULTILINE)
VERDICT_LINE = re.compile(r"^(?:- )?判定：(?P<verdict>放行|退回|等待)$", re.MULTILINE)
INTENTS = ("新业务", "旧版迭代", "新版升级", "双线")
_INTENT_LINE = re.compile(
    r"(?:^|\n)\s*(?:[-*]\s*)?意图：(?P<intent>新业务|旧版迭代|新版升级|双线)\s*(?:\n|$)"
)


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


def _body(comment) -> str:
    if isinstance(comment, Mapping):
        return comment.get("body") or ""
    return getattr(comment, "body", "") or ""


def latest_verdict(comments) -> tuple[str | None, str]:
    """Read the newest valid verdict comment. Review text cannot satisfy this check."""
    for comment in comments or []:
        body = _body(comment)
        verdict = VERDICT_LINE.search(body)
        commit = COMMIT_LINE.search(body)
        if verdict and commit and "判定记录" in body:
            return verdict.group("verdict"), commit.group("sha")
    return None, ""


def latest_evidence_sha(comments) -> str:
    """Read the newest evidence comment. A verdict record is not evidence."""
    for comment in comments or []:
        body = _body(comment)
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
    return _body(comment)


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
        body = _body(comment)
        match = re.search(r"^- 意图：(?P<intent>新业务|旧版迭代|新版升级|双线)$", body, re.MULTILINE)
        if match and "受理记录" in body:
            return match.group("intent")
    return ""


def explicit_intent(text: str) -> str:
    """Return one exact intent written by a person. Missing or mixed text stays empty."""
    found = list(dict.fromkeys(_INTENT_LINE.findall(text or "")))
    if len(found) != 1:
        return ""
    return found[0]


@dataclass(frozen=True)
class DriveDecision:
    """One next step. Flags are the only permission to write or merge."""

    action: str
    reason: str
    intent: str = ""
    verdict: str = ""
    head_sha: str = ""
    write_intake: bool = False
    collect_evidence: bool = False
    write_verdict: bool = False
    merge: bool = False


def merge_allowed(verdict: str | None, verdict_sha: str, current_sha: str, intent: str = "") -> bool:
    """Allow a merge only when this commit itself carries 放行 and the change is not dual-line."""
    if intent == "双线":
        return False
    return bool(verdict == "放行" and verdict_sha and current_sha and verdict_sha == current_sha)


def comments_from_records(records) -> list:
    """Rebuild the comment shapes the gate already knows how to read."""
    comments = []
    for record in records or []:
        if record.stage == "受理" and record.intent:
            comments.append(SimpleNamespace(body=f"## 受理记录\n\n- 意图：{record.intent}"))
        elif record.stage == "判定" and record.verdict:
            comments.append(SimpleNamespace(
                body=f"## 判定记录\n\n判定：{record.verdict}\n提交号：{record.head_sha}"
            ))
        elif record.stage == "取证" and record.head_sha:
            title = "PR 代码建议" if record.record_type == "建议" else "PR 审查指南"
            comments.append(SimpleNamespace(body=f"提交号：{record.head_sha}\n\n## {title}"))
    return comments


def _hold(reason: str, **fields) -> DriveDecision:
    return DriveDecision("留给人工", reason, **fields)


def decide_drive(
    comments,
    head_sha: str,
    stated_intent: str = "",
    rule_findings=None,
    allow_merge: bool = False,
) -> DriveDecision:
    """Choose the next autopilot step. Model prose never becomes 放行."""
    intent = latest_intake_intent(comments)
    evidence_sha = latest_evidence_sha(comments)
    verdict, verdict_sha = latest_verdict(comments)
    common = {"intent": intent, "head_sha": head_sha}

    if intent == "双线":
        return _hold("双线需要先拆开，不能放行，也不能汇入", **common)

    if verdict:
        if merge_allowed(verdict, verdict_sha, head_sha, intent):
            if not allow_merge:
                return DriveDecision(
                    "留给人工", "可以由人合并。默认不自动汇入", verdict=verdict, merge=False, **common
                )
            return DriveDecision(
                "汇入", "当前提交已有放行", verdict=verdict, merge=True, **common
            )
        if verdict_sha != head_sha:
            reason = "判定对应的提交已经变化，不能汇入"
        else:
            reason = f"最新判定是{verdict}，不能汇入"
        return _hold(reason, verdict=verdict, **common)

    if evidence_sha != head_sha:
        return DriveDecision("取证", "提交后直接审查，证据绑定当前提交", collect_evidence=True, **common)

    if rule_findings is None:
        return _hold("无法判定。审查里的批准不能当成放行", **common)
    proposed = "退回" if list(rule_findings) else "放行"
    if proposed not in VERDICTS or (proposed == "放行" and intent == "双线"):
        return _hold("无法判定，留给人工", **common)
    return DriveDecision(
        "判定", f"判定为{proposed}", verdict=proposed, write_verdict=True, **common
    )


def apply_drive(decision: DriveDecision, effects) -> list[str]:
    """Perform at most the flags on a decision. A 退回 or 双线 still cannot merge."""
    done = []
    if decision.write_intake and decision.intent in INTENTS:
        effects.write_intake(decision.intent, decision.head_sha)
        done.append("受理")
    if decision.collect_evidence and decision.head_sha:
        effects.collect_evidence(decision.head_sha)
        done.append("取证")
    blocked_pass = decision.verdict == "放行" and decision.intent == "双线"
    if decision.write_verdict and decision.verdict in VERDICTS and not blocked_pass:
        effects.write_verdict(decision.verdict, decision.head_sha)
        done.append("判定")
    if decision.merge and decision.verdict == "放行" and decision.intent != "双线" and decision.head_sha:
        effects.merge(decision.head_sha)
        done.append("汇入")
    return done
