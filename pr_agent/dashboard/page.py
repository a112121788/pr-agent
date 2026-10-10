"""Render the factory dashboard from stored stage records."""

import hashlib
from html import escape

from pr_agent.algo.factory_record import comment_feed, records_from_comments
from pr_agent.dashboard.actions import open_pulls, pull_comments, pull_detail
from pr_agent.dashboard.markdown import render_comment_markdown
from pr_agent.dashboard.store import FactoryStore, database_url

_COMMANDS = {"review": "审查", "improve": "建议", "status": "状态", "describe": "描述"}


def _counts(records) -> dict[str, int]:
    counts = {stage: 0 for stage in ("受理", "取证", "判定", "汇入")}
    for record in records:
        counts[record.stage] = counts.get(record.stage, 0) + 1
    return counts


def _cards(records) -> str:
    if not records:
        return "<p class='empty'>还没有审核记录</p>"
    cards = []
    for record in records:
        link = escape(record.pr_url)
        cards.append(
            "<article class='card'>"
            f"<span class='stage'>{escape(record.stage)}</span>"
            f"<strong>{escape(record.record_type)}</strong>"
            f"<a href='{link}'>{link}</a>"
            f"<p>{escape(record.summary or '没有摘要')}</p>"
            "<small>"
            f"意图 {escape(record.intent or '未记录')} · "
            f"判定 {escape(record.verdict or '未记录')} · "
            f"提交 {escape((record.head_sha or '未读取')[:12])}"
            "</small>"
            "</article>"
        )
    return "\n".join(cards)


def _repos(store: FactoryStore) -> str:
    blocks = []
    for owner, repo in store.repos():
        try:
            pulls = open_pulls(owner, repo)
        except Exception as error:
            pulls = []
            notice = f"<p class='error'>{escape(str(error))}</p>"
        else:
            notice = ""
        busy = store.reviewing()
        rows = []
        for item in pulls:
            reviewing = item["url"] in busy
            review_button = (
                "<button type='button' disabled>审查中</button>"
                if reviewing
                else "<button name='command' value='review'>审查</button>"
            )
            mark = "<span class='stage'>审查中</span>" if reviewing else ""
            rows.append(
                "<li class='pr'>"
                f"<a href='/dashboard/pr?url={escape(item['url'])}'>"
                f"#{escape(str(item['number']))} {escape(item['title'])}</a>"
                f"{mark}"
                "<form method='post' action='/dashboard/run'>"
                f"<input type='hidden' name='pr_url' value='{escape(item['url'])}'>"
                f"{review_button}"
                "<button class='secondary' name='command' value='improve'>建议</button>"
                "<button class='secondary' name='command' value='status'>状态</button>"
                "</form></li>"
            )
        rows_html = "".join(rows) or "<li>没有打开的拉取请求</li>"
        blocks.append(
            "<section class='repo'><h2>"
            f"{escape(owner)}/{escape(repo)}"
            "</h2><form method='post' action='/dashboard/repos/remove'>"
            f"<input type='hidden' name='owner' value='{escape(owner)}'>"
            f"<input type='hidden' name='repo' value='{escape(repo)}'>"
            "<button class='secondary'>移除</button></form>"
            f"{notice}<ul>{rows_html}</ul></section>"
        )
    return "\n".join(blocks) or "<p class='empty'>还没有登记仓库</p>"


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


def _identity(pr_url: str) -> str:
    """Name the pull request so the pipeline is not only a bare URL."""
    safe_url = escape(pr_url)
    try:
        detail = pull_detail(pr_url)
    except Exception:
        return (
            f"<p class='lead'><a href='{safe_url}' target='_blank' rel='noopener noreferrer'>"
            "在 Gitee 打开这张拉取请求</a></p>"
        )
    number = escape(str(detail["number"]))
    title = escape(detail["title"] or "未命名拉取请求")
    route = f"{escape(detail['head'] or '未知')} → {escape(detail['base'] or '未知')}"
    meta = " · ".join(
        part for part in (escape(detail["author"] or ""), route, escape(detail["state_label"])) if part
    )
    link = escape(detail["url"] or pr_url)
    return (
        f"<p class='identity'><span>#{number}</span>{title}</p>"
        f"<p class='lead'>{meta} · <a href='{link}' target='_blank' rel='noopener noreferrer'>在 Gitee 打开</a></p>"
    )


def render_conversation(pr_url: str) -> str:
    """Render one pull request's jobs and comments, and keep actions on screen."""
    safe_url = escape(pr_url)
    body = render_conversation_body(pr_url)
    review_disabled = " disabled" if "data-reviewing='1'" in body else ""
    content = f"""<a href="/dashboard">返回驾驶舱</a>
<h1>审核流水线</h1>
{_identity(pr_url)}
<div id="pipeline" aria-live="polite">{body}</div>
<form class="dock" id="actions" method="post" action="/dashboard/run">
<input type="hidden" name="pr_url" value="{safe_url}">
<p id="dock-status" class="dock-status" aria-live="polite">审查会写回 Gitee。同一张正在审查时不能再开一次。</p>
<div class="dock-buttons">
<button type="submit" name="command" value="review"{review_disabled}>{'审查中' if review_disabled else '审查'}</button>
<button type="submit" class="secondary" name="command" value="improve">建议</button>
<button type="submit" class="secondary" name="command" value="status">状态</button>
</div>
</form>
<script>
const target = new URLSearchParams(location.search).get("url");
const form = document.querySelector("#actions");
const statusLine = document.querySelector("#dock-status");
const buttons = [...form.querySelectorAll("button")];
const labels = new Map(buttons.map((button) => [button, button.value === "review" ? "审查" : button.textContent]));
let inflight = false;

function applyPipeline(box, next) {{
  const current = box.querySelector("[data-stamp]")?.dataset.stamp || "";
  const probe = document.createElement("template");
  probe.innerHTML = next;
  const stamp = probe.content.querySelector("[data-stamp]")?.dataset.stamp || "";
  if (stamp && stamp === current) return;
  const y = window.scrollY;
  box.innerHTML = next;
  window.scrollTo(0, y);
}}

async function refreshPipeline() {{
  if (!target || document.hidden || inflight) return;
  const box = document.querySelector("#pipeline");
  const response = await fetch("/dashboard/pr/fragment?url=" + encodeURIComponent(target));
  if (!response.ok) return;
  applyPipeline(box, await response.text());
  syncReviewButton();
}}

form.addEventListener("submit", async (event) => {{
  event.preventDefault();
  const submitter = event.submitter;
  if (!submitter || inflight) return;
  inflight = true;
  buttons.forEach((button) => {{ button.disabled = true; }});
  submitter.textContent = "排队中";
  statusLine.textContent = "已提交，正在更新流水线";
  const body = new FormData(form);
  body.set("command", submitter.value);
  try {{
    const response = await fetch("/dashboard/run", {{
      method: "POST",
      body,
      headers: {{"X-Requested-With": "fetch"}},
    }});
    if (!response.ok) {{
      statusLine.textContent = "提交没有成功，请再试一次";
      return;
    }}
    applyPipeline(document.querySelector("#pipeline"), await response.text());
    statusLine.textContent = "任务已进入流水线";
  }} catch (_error) {{
    statusLine.textContent = "网络中断，请再试一次";
  }} finally {{
    inflight = false;
    syncReviewButton();
  }}
}});

function syncReviewButton() {{
  const reviewing = Boolean(document.querySelector("#pipeline [data-reviewing]"));
  const review = form.querySelector("button[value='review']");
  if (!review) return;
  review.disabled = reviewing || inflight;
  review.textContent = reviewing ? "审查中" : labels.get(review);
  buttons.forEach((button) => {{
    if (button !== review) button.disabled = inflight;
  }});
}}
setInterval(refreshPipeline, 5000);
</script>"""
    return _page("审核流水线", content)


def render_dashboard(limit: int = 50) -> str:
    """Return one Chinese HTML page. The database URL itself is not shown."""
    store = FactoryStore(database_url())
    store.setup()
    repos = _repos(store)
    records = store.latest(limit)
    counts = _counts(records)
    summary = "\n".join(
        f"<li><span>{escape(stage)}</span><strong>{count}</strong></li>"
        for stage, count in counts.items()
    )
    content = f"""<h1>审核工厂驾驶舱</h1>
<form class="repo-form" method="post" action="/dashboard/repos">
<input name="repo" placeholder="添加仓库，例如 owner/repo" aria-label="添加仓库" required>
<button>登记</button>
</form>
{repos}
<ol>{summary}</ol>
<section class="cards">{_cards(records)}</section>"""
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
<style>
body {{ margin: 0; background: #f6f3ec; color: #243036; font-family: "PingFang SC", sans-serif; }}
main {{ max-width: 980px; margin: auto; padding: 32px 20px 128px; }}
h1 {{ margin: 0 0 8px; font-size: 36px; letter-spacing: -.04em; white-space: nowrap; }}
.lead {{ color: #66717a; }}
ol {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; padding: 0; list-style: none; }}
li {{ background: white; border: 1px solid #e4ddd0; border-radius: 8px; padding: 14px; }}
li span {{ display: block; color: #66717a; }}
li strong {{ font-size: 28px; }}
.repo-form, .repo, .card, .empty {{ background: white; border: 1px solid #e4ddd0; border-radius: 8px; }}
.repo-form {{ display: flex; gap: 8px; padding: 12px; margin: 18px 0; }}
input, button {{ font: inherit; border-radius: 6px; }}
input {{ flex: 1; border: 1px solid #d9d3c7; padding: 10px 12px; }}
button {{ border: 0; background: #0f6b4c; color: white; padding: 8px 12px; cursor: pointer; }}
button.secondary {{ background: #e7f4ee; color: #0f6b4c; }}
.repo {{ margin: 0 0 16px; padding: 16px; }}
.repo ul {{ display: grid; gap: 10px; margin: 12px 0 0; padding: 0; list-style: none; }}
.pr {{ display: flex; justify-content: space-between; gap: 16px; align-items: center; }}
.pr form {{ display: flex; gap: 6px; }}
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
.dock-buttons {{ display: flex; gap: 8px; }}
button:disabled {{ opacity: .55; cursor: progress; }}
@media (max-width: 720px) {{
  ol, .steps {{ grid-template-columns: 1fr 1fr; }}
  .pr {{ display: block; }}
  .pr form {{ margin-top: 8px; }}
  .dock {{ flex-wrap: wrap; }}
  .dock-status {{ flex-basis: 100%; }}
}}
</style>
</head>
<body><main>{content}</main></body>
</html>
"""
