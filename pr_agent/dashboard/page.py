"""Render the factory dashboard from stored stage records."""

from html import escape

from pr_agent.algo.factory_record import records_from_comments
from pr_agent.dashboard.actions import open_pulls, pull_comments
from pr_agent.dashboard.store import FactoryStore, database_url


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
        rows = "".join(
            "<li class='pr'>"
            f"<a href='/dashboard/pr?url={escape(item['url'])}'>"
            f"#{escape(str(item['number']))} {escape(item['title'])}</a>"
            "<form method='post' action='/dashboard/run'>"
            f"<input type='hidden' name='pr_url' value='{escape(item['url'])}'>"
            "<button name='command' value='review'>审查</button>"
            "<button class='secondary' name='command' value='improve'>建议</button>"
            "<button class='secondary' name='command' value='status'>状态</button>"
            "</form></li>"
            for item in pulls
        ) or "<li>没有打开的拉取请求</li>"
        blocks.append(
            "<section class='repo'><h2>"
            f"{escape(owner)}/{escape(repo)}"
            "</h2><form method='post' action='/dashboard/repos/remove'>"
            f"<input type='hidden' name='owner' value='{escape(owner)}'>"
            f"<input type='hidden' name='repo' value='{escape(repo)}'>"
            "<button class='secondary'>移除</button></form>"
            f"{notice}<ul>{rows}</ul></section>"
        )
    return "\n".join(blocks) or "<p class='empty'>还没有登记仓库</p>"


def render_conversation_body(pr_url: str) -> str:
    """Return the pipeline feed without the page frame."""
    store = FactoryStore(database_url())
    store.setup()
    jobs = store.jobs_for(pr_url)
    error = ""
    try:
        records = records_from_comments(pr_url, pull_comments(pr_url))
    except Exception as exc:
        records = []
        error = str(exc)
    steps = "".join(
        f"<li class='{'done' if any(record.stage == stage for record in records) else ''}'>{escape(stage)}</li>"
        for stage in ("受理", "取证", "判定", "汇入")
    )
    messages = []
    if error:
        messages.append(f"<article class='card'><span class='stage'>失败</span><strong>Gitee</strong><p>{escape(error)}</p></article>")
    for _job_id, command, status, summary, _created in jobs:
        messages.append(
            "<article class='card'>"
            f"<span class='stage'>{escape(status)}</span><strong>{escape(command)}</strong>"
            f"<p>{escape(summary or '正在处理')}</p></article>"
        )
    for record in records:
        text = escape(record.summary or "没有摘要").replace("\n", "<br>")
        messages.append(
            "<article class='card'>"
            f"<span class='stage'>{escape(record.stage)}</span>"
            f"<strong>{escape(record.record_type)}</strong>"
            f"<small>{escape(record.created_at or '')}</small>"
            f"<div class='message'>{text}</div></article>"
        )
    feed = "\n".join(messages) or "<p class='empty'>还没有审核记录</p>"
    return f"<ol class='steps'>{steps}</ol><section class='cards'>{feed}</section>"


def render_conversation(pr_url: str) -> str:
    """Render one pull request's jobs and records from oldest to newest."""
    safe_url = escape(pr_url)
    content = f"""<a href="/dashboard">返回驾驶舱</a>
<h1>审核流水线</h1>
<p class="lead"><a href="{safe_url}">在 Gitee 打开这张拉取请求</a></p>
<div id="pipeline">{render_conversation_body(pr_url)}</div>
<form class="dock" method="post" action="/dashboard/run">
<input type="hidden" name="pr_url" value="{safe_url}">
<button name="command" value="review">审查</button>
<button class="secondary" name="command" value="improve">建议</button>
<button class="secondary" name="command" value="status">状态</button>
</form>
<script>
const target = new URLSearchParams(location.search).get("url");
async function refreshPipeline() {{
  if (document.hidden) return;
  const response = await fetch("/dashboard/pr/fragment?url=" + encodeURIComponent(target));
  if (response.ok) document.querySelector("#pipeline").innerHTML = await response.text();
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
<p class="lead">登记仓库、查看打开的拉取请求，并发起审查。合并仍由人在 Gitee 上完成。</p>
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
main {{ max-width: 980px; margin: auto; padding: 32px 20px 64px; }}
h1 {{ margin: 0 0 8px; font-size: 36px; letter-spacing: -.04em; }}
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
.steps {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 18px 0; padding: 0; list-style: none; }}
.steps li {{ text-align: center; color: #66717a; }}
.steps li.done {{ background: #e7f4ee; color: #0f6b4c; font-weight: 700; }}
.message {{ max-height: 280px; overflow: auto; line-height: 1.6; white-space: pre-wrap; }}
.dock {{ position: sticky; bottom: 12px; display: flex; gap: 8px; background: white; border: 1px solid #e4ddd0; border-radius: 8px; padding: 12px; }}
@media (max-width: 720px) {{
  ol {{ grid-template-columns: 1fr 1fr; }}
  .pr {{ display: block; }}
  .pr form {{ margin-top: 8px; }}
}}
</style>
</head>
<body><main>{content}</main></body>
</html>
"""
