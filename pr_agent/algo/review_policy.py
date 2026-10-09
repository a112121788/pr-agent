"""Deterministic review gates that do not depend on the model."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

_BLOCKING_TAGS = re.compile(r"<\s*/?\s*(a|button)\b", re.IGNORECASE)
_FEATURE_TITLE = re.compile(r"\b(feat|feature)\b|功能更新|新功能", re.IGNORECASE)
_SPEC_PREFIXES = ("specs/", "openspecs/")


@dataclass(frozen=True)
class ReviewRuleFinding:
    severity: str
    summary: str
    file: str = ""


def _file_text(diff_file) -> tuple[str, str, str]:
    filename = str(getattr(diff_file, "filename", "") or "")
    patch = str(getattr(diff_file, "patch", "") or "")
    head_file = str(getattr(diff_file, "head_file", "") or "")
    return filename, patch, head_file


def _added_lines(patch: str) -> str:
    return "\n".join(line[1:] for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++"))


def _is_spec(filename: str) -> bool:
    normalized = filename.lstrip("./").lower()
    return any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in _SPEC_PREFIXES)


def find_blocking_tags(diff_files: Iterable) -> list[ReviewRuleFinding]:
    """Reject newly added anchor or button tags in HTML and JavaScript."""
    findings = []
    for diff_file in diff_files:
        filename, patch, _ = _file_text(diff_file)
        if not filename.lower().endswith((".html", ".htm", ".js", ".jsx")):
            continue
        added = _added_lines(patch)
        if _BLOCKING_TAGS.search(added):
            findings.append(ReviewRuleFinding(
                "严重问题",
                "包含 a 和 button 标签，请使用 reset_url 或 link_to，本次不给予通过",
                filename,
            ))
    return findings


def find_spec_violations(diff_files: Iterable, pr_title: str = "") -> list[ReviewRuleFinding]:
    """Require a spec update for a feature change and compare it with the implementation."""
    files = list(diff_files)
    feature = bool(_FEATURE_TITLE.search(pr_title))
    spec_files = [diff_file for diff_file in files if _is_spec(_file_text(diff_file)[0])]
    if feature and not spec_files:
        return [ReviewRuleFinding(
            "严重问题", "本次功能更新缺失 spec 文件，请补充 spec 文件，本次不给予通过"
        )]

    findings = []
    spec_text = "\n".join(
        _file_text(diff_file)[2] or _added_lines(_file_text(diff_file)[1]) for diff_file in spec_files
    )
    for diff_file in files:
        filename, patch, _ = _file_text(diff_file)
        if _is_spec(filename):
            continue
        for line in _added_lines(patch).splitlines():
            match = re.search(r"\b(?:SPEC|spec)[-_ ]?(?:ID)?[:：]\s*([A-Za-z0-9._/-]+)", line)
            if match and match.group(1) not in spec_text:
                findings.append(ReviewRuleFinding(
                    "严重问题",
                    "本次功能更新不符合 spec 文件中的要求，请按照 spec 文件中的要求进行开发，本次不给予通过",
                    filename,
                ))
                break
    return findings


def find_dual_line_violation(intake_intent: str = "") -> list[ReviewRuleFinding]:
    """Block only an explicitly declared dual-line change."""
    if intake_intent != "双线":
        return []
    return [ReviewRuleFinding("严重问题", "这是双线变更，请先拆成两张拉取请求，本次不给予通过")]


def review_rule_findings(diff_files: Iterable, pr_title: str = "", intake_intent: str = "") -> list[ReviewRuleFinding]:
    return (
        find_blocking_tags(diff_files)
        + find_spec_violations(diff_files, pr_title)
        + find_dual_line_violation(intake_intent)
    )


def render_review_rule_section(findings: Iterable[ReviewRuleFinding]) -> str:
    findings = list(findings)
    if not findings:
        return ""
    lines = ["## 团队强规则", "", "结论：请求修改", ""]
    for finding in findings:
        location = f"`{finding.file}`：" if finding.file else ""
        lines.append(f"- **{finding.severity}**：{location}{finding.summary}")
    return "\n".join(lines)


def review_sections(review: Mapping) -> str:
    """Group model findings into blocking issues, suggestions, and strengths."""
    if not isinstance(review, Mapping):
        return ""
    issues = review.get("key_issues_to_review")
    blocking = []
    suggestions = []
    if isinstance(issues, list):
        for issue in issues:
            if not isinstance(issue, Mapping):
                continue
            header = str(issue.get("issue_header") or "").strip()
            content = str(issue.get("issue_content") or "").strip()
            file = str(issue.get("relevant_file") or "").strip()
            text = "：".join(part for part in (header, content) if part)
            if not text:
                continue
            line = f"`{file}`：{text}" if file else text
            severity = str(issue.get("severity") or issue.get("impact") or "").lower()
            if severity in {"high", "critical", "严重", "高"}:
                blocking.append(line)
            else:
                suggestions.append(line)
    security = str(review.get("security_concerns") or "")
    if security and security.strip().lower() not in {"no", "none", "false"}:
        blocking.insert(0, security.strip())
    strengths = review.get("strengths")
    strength_lines = []
    if isinstance(strengths, list):
        strength_lines = [str(item).strip() for item in strengths if str(item).strip()]
    recommendation = str(review.get("merge_recommendation") or "").strip()
    labels = {
        "safe_to_merge": "批准",
        "merge_with_caution": "仅评论",
        "changes_required": "请求修改",
    }
    verdict = labels.get(recommendation, "请求修改" if blocking else "批准")
    lines = ["## 审查结论", "", f"结论：{verdict}", ""]
    lines += ["### 严重问题", *(f"- {item}" for item in blocking or ["无阻塞项"]), ""]
    lines += ["### 改进建议", *(f"- {item}" for item in suggestions or ["无"]), ""]
    lines.extend(["### 优点", *(f"- {item}" for item in strength_lines or ["无明确优点"])])
    return "\n".join(lines)
