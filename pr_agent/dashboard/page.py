"""Render the factory dashboard from stored stage records."""

import hashlib
import json
import os
from html import escape

from pr_agent.algo.factory_record import comment_feed, records_from_comments
from pr_agent.dashboard.actions import pull_comments, pull_detail
from pr_agent.dashboard.markdown import render_comment_markdown
from pr_agent.dashboard.store import FactoryStore, database_url

_COMMANDS = {"review": "审查", "improve": "建议", "status": "状态", "describe": "描述"}


def _pipeline_progress(records, jobs, feed) -> tuple[str, str]:
    """Return the stage strip and one sentence that says what to do next."""
    order = ("受理", "取证", "判定", "汇入")
    present = {record.stage for record in records}
    current = "汇入" if all(stage in present for stage in order) else next(
        stage for stage in order if stage not in present
    )
    hints = {
        "受理": "还没有受理记录。可以先从下方发起审查。",
        "取证": "还没有审查或建议。从下方发起后，结果会写回 Gitee。",
        "判定": "证据已经写回。判定仍由负责人写下判定记录。",
        "汇入": "判定已记录。合并仍由有权限的人在 Gitee 上完成。",
    }
    active = [job for job in jobs if job[2] in {"排队", "运行中"}]
    if active:
        label = _COMMANDS.get(active[-1][1], active[-1][1])
        hint = f"{label}正在处理。这条流水线会自动更新。"
    elif any(item["stage"] == "失败" for item in feed) and "取证" not in present:
        hint = "最近一次审查没有写回证据。可以再次发起审查。"
    else:
        hint = hints[current]
    steps = []
    for stage in order:
        classes = []
        if stage in present:
            classes.append("done")
        if stage == current:
            classes.append("current")
        class_attr = f" class='{' '.join(classes)}'" if classes else ""
        steps.append(f"<li{class_attr}>{escape(stage)}</li>")
    return "".join(steps), hint


def _when(value: str) -> str:
    """Show a comment time as a short local stamp."""
    text = (value or "").replace("T", " ")
    return text[:16] if len(text) >= 16 else text


def _feed_card(item: dict) -> str:
    """Show a short comment in place, and keep a long one collapsed until the reader opens it."""
    meta = " · ".join(part for part in (item["author"], _when(item["created_at"]), item["where"]) if part)
    meta_html = f"<small>{escape(meta)}</small>" if meta else ""
    text = render_comment_markdown(item["text"])
    long_comment = item["text"].count("\n") > 8 or len(item["text"]) > 360
    if long_comment:
        body = (
            "<details class='message'><summary>展开正文</summary>"
            f"<div class='message-body'>{text}</div></details>"
        )
    else:
        body = f"<div class='message'>{text}</div>"
    return (
        "<article class='card'><header class='card-top'>"
        f"<strong>{escape(item['kind'])}</strong>"
        f"<span class='stage'>{escape(item['stage'])}</span></header>"
        f"{meta_html}{body}</article>"
    )


def render_conversation_body(pr_url: str) -> str:
    """Return the pipeline feed without the page frame."""
    store = FactoryStore(database_url())
    store.setup()
    jobs = store.jobs_for(pr_url)
    reviewing = any(
        command == "review" and status in {"排队", "运行中"}
        for _job, command, status, _summary, _created in jobs
    )
    error = ""
    comments = []
    try:
        comments = pull_comments(pr_url)
    except Exception as exc:
        error = str(exc)
    records = records_from_comments(pr_url, comments)
    feed = comment_feed(comments)
    steps, hint = _pipeline_progress(records, jobs, feed)
    messages = []
    if error:
        messages.append(
            "<article class='card'><header class='card-top'><strong>Gitee</strong>"
            f"<span class='stage'>失败</span></header><div class='message'>{escape(error)}</div></article>"
        )
    for _job_id, command, status, summary, created in jobs:
        label = _COMMANDS.get(command, command)
        messages.append(
            "<article class='card'><header class='card-top'>"
            f"<strong>{escape(label)}</strong><span class='stage'>{escape(status)}</span></header>"
            f"<small>{escape(_when(created or ''))}</small>"
            f"<div class='message'>{escape(summary or '正在处理')}</div></article>"
        )
    messages.extend(_feed_card(item) for item in feed)
    cards = "\n".join(messages) or "<p class='empty'>Gitee 上还没有评论。用下方的审查、建议或状态开始。</p>"
    html = (
        f"<p class='hint'>{escape(hint)}</p><ol class='steps'>{steps}</ol>"
        f"<section class='cards'>{cards}</section>"
    )
    stamp = hashlib.sha256(html.encode()).hexdigest()[:16]
    marker = " data-reviewing='1'" if reviewing else ""
    return f"<div data-stamp='{stamp}'{marker}>{html}</div>"


def pipeline_payload(pr_url: str) -> dict:
    """Return one pipeline as data. The browser draws it and refreshes that region only."""
    store = FactoryStore(database_url())
    store.setup()
    jobs = store.jobs_for(pr_url)
    reviewing = any(
        command == "review" and status in {"排队", "运行中"}
        for _job, command, status, _summary, _created in jobs
    )
    error = ""
    comments = []
    try:
        comments = pull_comments(pr_url)
    except Exception as exc:
        error = str(exc)
    records = records_from_comments(pr_url, comments)
    feed = comment_feed(comments)
    hint = _pipeline_progress(records, jobs, feed)[1]
    order = ("受理", "取证", "判定", "汇入")
    present = {record.stage for record in records}
    current = "汇入" if all(stage in present for stage in order) else next(
        stage for stage in order if stage not in present
    )
    steps = [
        {"name": stage, "done": stage in present, "current": stage == current}
        for stage in order
    ]
    messages = []
    if error:
        messages.append({
            "kind": "Gitee",
            "stage": "失败",
            "meta": "",
            "html": f"<div class='message'>{escape(error)}</div>",
        })
    for _job_id, command, status, summary, created in jobs:
        messages.append({
            "kind": _COMMANDS.get(command, command),
            "stage": status,
            "meta": _when(created or ""),
            "html": f"<div class='message'>{escape(summary or '正在处理')}</div>",
        })
    for item in feed:
        meta = " · ".join(part for part in (item["author"], _when(item["created_at"]), item["where"]) if part)
        text = render_comment_markdown(item["text"])
        long_comment = item["text"].count("\n") > 8 or len(item["text"]) > 360
        if long_comment:
            html = (
                "<details class='message'><summary>展开正文</summary>"
                f"<div class='message-body'>{text}</div></details>"
            )
        else:
            html = f"<div class='message'>{text}</div>"
        messages.append({"kind": item["kind"], "stage": item["stage"], "meta": meta, "html": html})
    try:
        detail = pull_detail(pr_url)
    except Exception:
        identity = {"named": False, "gitee_url": pr_url}
    else:
        route = f"{detail['head'] or '未知'} → {detail['base'] or '未知'}"
        meta = " · ".join(part for part in (detail["author"] or "", route, detail["state_label"]) if part)
        identity = {
            "named": True,
            "number": str(detail["number"]),
            "title": detail["title"] or "未命名拉取请求",
            "meta": meta,
            "gitee_url": detail["url"] or pr_url,
        }
    blob = json.dumps(
        {"hint": hint, "steps": steps, "messages": messages},
        ensure_ascii=False,
        sort_keys=True,
    )
    stamp = hashlib.sha256(blob.encode()).hexdigest()[:16]
    return {
        "hint": hint,
        "steps": steps,
        "reviewing": reviewing,
        "messages": messages,
        "identity": identity,
        "stamp": stamp,
    }


def render_conversation(pr_url: str) -> str:
    """Return the pipeline shell. Jobs and comments arrive from the JSON API."""
    safe_url = escape(pr_url)
    content = f"""<a href="/dashboard">返回驾驶舱</a>
<h1>审核流水线</h1>
<div id="identity">
<div class="identity-row">
<p class="identity" id="identity-title"></p>
<span class="run-slot" id="run-slot" aria-live="polite"></span>
</div>
<p class="lead" id="identity-meta"></p>
</div>
<div id="pipeline" aria-live="polite"></div>
<form class="dock" id="actions" method="post" action="/dashboard/run">
<input type="hidden" name="pr_url" value="{safe_url}">
<p id="dock-status" class="dock-status">审查会写回 Gitee。同一张正在审查时不能再开一次。</p>
<div class="dock-buttons">
<button type="submit" name="command" value="review">审查</button>
<button type="submit" class="secondary" name="command" value="improve">建议</button>
<button type="submit" class="secondary" name="command" value="status">状态</button>
</div>
</form>
<form class="dock verdicts" id="verdicts" method="post" action="/dashboard/verdict">
<input type="hidden" name="pr_url" value="{safe_url}">
<button type="submit" class="secondary" name="verdict" value="放行">放行</button>
<button type="submit" class="secondary" name="verdict" value="退回">退回</button>
<button type="submit" class="secondary" name="verdict" value="等待">等待</button>
</form>
<script src="/dashboard/static/pipeline.js"></script>"""
    return _page("审核流水线", content)


def build_id() -> str:
    """Return the short build name passed in at container start."""
    return (os.environ.get("PR_AGENT_BUILD") or "dev").strip()[:12] or "dev"


def render_dashboard(limit: int = 50) -> str:
    """Return the cockpit shell. Pull requests arrive from the JSON API."""
    content = f"""<h1>审核工厂驾驶舱</h1>
<p class="build">构建 {escape(build_id())}</p>
<div class="toolbar">
<form class="repo-form" id="register" method="post" action="/dashboard/repos">
<input name="repo" placeholder="添加仓库，例如 owner/repo" aria-label="添加仓库" required>
<button>登记</button>
</form>
<form method="post" action="/dashboard/drive" id="drive">
<button class="secondary" type="submit">批量审查</button>
</form>
</div>
<div id="repos"></div>
<ol id="counts"></ol>
<script src="/dashboard/static/home.js"></script>"""
    return _page("审核工厂驾驶舱", content)


def _page(title: str, content: str, refresh: bool = False) -> str:
    """Wrap dashboard content in the shared visual frame."""
    refresh_tag = '<meta http-equiv="refresh" content="5">' if refresh else ""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{refresh_tag}
<title>{escape(title)}</title>
<link rel="icon" type="image/svg+xml" href="/dashboard/static/favicon.svg">
<style>
body {{ margin: 0; background: #f6f3ec; color: #243036; font-family: "PingFang SC", sans-serif; }}
main {{ max-width: 980px; margin: auto; padding: 32px 20px 128px; }}
h1 {{ margin: 0 0 8px; font-size: 36px; letter-spacing: -.04em; white-space: nowrap; }}
.build {{ margin: 0; color: #66717a; font-size: 14px; }}
.lead {{ color: #66717a; }}
ol {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; padding: 0; list-style: none; }}
li {{ background: white; border: 1px solid #e4ddd0; border-radius: 8px; padding: 14px; }}
li span {{ display: block; color: #66717a; }}
li strong {{ font-size: 28px; }}
.repo-form, .repo, .card, .empty {{ background: white; border: 1px solid #e4ddd0; border-radius: 8px; }}
.toolbar {{ display: flex; gap: 8px; align-items: stretch; margin: 18px 0; }}
.toolbar .repo-form {{ flex: 1; margin: 0; }}
.toolbar form:last-child {{ display: flex; }}
.repo-form {{ display: flex; gap: 8px; padding: 12px; margin: 18px 0; }}
input, button {{ font: inherit; border-radius: 6px; }}
input {{ flex: 1; border: 1px solid #d9d3c7; padding: 10px 12px; }}
button {{ border: 0; background: #0f6b4c; color: white; padding: 8px 12px; cursor: pointer; }}
button.secondary {{ background: #e7f4ee; color: #0f6b4c; }}
.repo {{ margin: 0 0 16px; padding: 16px; }}
.repo ul {{ display: grid; gap: 10px; margin: 12px 0 0; padding: 0; list-style: none; }}
.pr {{ display: flex; justify-content: space-between; gap: 16px; align-items: center; }}
.pr-title {{ display: flex; align-items: center; gap: 8px; min-width: 0; }}
.identity-row {{ display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; margin-top: 14px; }}
.identity-row .identity {{ margin: 0; }}
.pr form, .pr-actions {{ display: flex; gap: 6px; align-items: center; }}
.run-slot {{ display: inline-flex; gap: 6px; align-items: center; min-height: 16px; color: #66717a; font-size: 13px; }}
.run-mark {{ width: 14px; height: 14px; box-sizing: border-box; border: 2px solid #d9d3c7;
  border-top-color: #0f6b4c; border-radius: 50%; animation: spin .8s linear infinite; }}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
@media (prefers-reduced-motion: reduce) {{
  .run-mark {{ animation: none; }}
}}
.cards {{ display: grid; gap: 12px; }}
.card {{ padding: 16px; }}
.stage {{ float: right; background: #e7f4ee; color: #0f6b4c; border-radius: 99px; padding: 2px 8px; }}
a {{ color: #0f6b4c; overflow-wrap: anywhere; text-decoration: none; }}
.card p, small, .error {{ color: #66717a; }}
.empty {{ padding: 28px; text-align: center; }}
.identity {{ margin: 14px 0 0; font-size: 20px; font-weight: 600; letter-spacing: -.02em; }}
.identity span {{ color: #0f6b4c; margin-right: 8px; }}
.hint {{ color: #66717a; margin: 16px 0; }}
.card-top {{ display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }}
.card-top .stage {{ float: none; }}
.steps {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 0 0 16px;
  padding: 0; list-style: none; }}
.steps li {{ text-align: center; color: #66717a; padding: 10px 8px; }}
.steps li.done {{ background: #e7f4ee; color: #0f6b4c; font-weight: 700; }}
.steps li.current {{ box-shadow: inset 0 0 0 2px #0f6b4c; color: #0f6b4c; font-weight: 700; }}
.message, .message-body {{ line-height: 1.6; }}
.message p, .message li, .message h1, .message h2, .message h3, .message td, .message th {{
  color: #243036; }}
.message pre {{ overflow: auto; background: #f6f3ec; padding: 12px; white-space: pre; }}
.message code {{ font-family: ui-monospace, SFMono-Regular, monospace; }}
.message table {{ border-collapse: collapse; width: 100%; }}
.message th, .message td {{ border: 1px solid #e4ddd0; padding: 6px 8px; text-align: left; }}
details.message summary {{ cursor: pointer; color: #0f6b4c; }}
small {{ display: block; margin: 6px 0; }}
.dock {{ position: fixed; z-index: 2; left: 50%; bottom: 16px; transform: translateX(-50%);
  width: min(940px, calc(100% - 24px)); display: flex; gap: 12px; align-items: center;
  background: white; border: 1px solid #e4ddd0; border-radius: 8px; padding: 12px;
  box-shadow: 0 8px 24px rgba(36, 48, 54, .08); }}
.dock-status {{ flex: 1; margin: 0; color: #66717a; }}
.dock-buttons, .verdicts {{ display: flex; gap: 8px; }}
.verdicts {{ position: fixed; z-index: 2; left: 50%; bottom: 84px; transform: translateX(-50%);
  width: min(940px, calc(100% - 24px)); background: white; border: 1px solid #e4ddd0;
  border-radius: 8px; padding: 8px 12px; }}
button:disabled {{ opacity: .55; cursor: progress; }}
@media (max-width: 720px) {{
  ol, .steps {{ grid-template-columns: 1fr 1fr; }}
  .pr {{ display: block; }}
  .pr form, .pr-actions {{ margin-top: 8px; }}
  .dock {{ flex-wrap: wrap; }}
  .dock-status {{ flex-basis: 100%; }}
}}
</style>
</head>
<body><main>{content}</main></body>
</html>
"""
