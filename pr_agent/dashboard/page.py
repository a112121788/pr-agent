"""Render the factory dashboard from stored stage records."""

from html import escape

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


def render_dashboard(limit: int = 50) -> str:
    """Return one Chinese HTML page. The database URL itself is not shown."""
    store = FactoryStore(database_url())
    store.setup()
    records = store.latest(limit)
    counts = _counts(records)
    summary = "\n".join(
        f"<li><span>{escape(stage)}</span><strong>{count}</strong></li>"
        for stage, count in counts.items()
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>审核工厂看板</title>
<style>
body {{ margin: 0; background: #f6f3ec; color: #243036; font-family: "PingFang SC", sans-serif; }}
main {{ max-width: 980px; margin: auto; padding: 32px 20px 64px; }}
h1 {{ margin: 0 0 8px; font-size: 36px; letter-spacing: -.04em; }}
.lead {{ color: #66717a; }}
ol {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; padding: 0; list-style: none; }}
li {{ background: white; border: 1px solid #e4ddd0; border-radius: 8px; padding: 14px; }}
li span {{ display: block; color: #66717a; }}
li strong {{ font-size: 28px; }}
.cards {{ display: grid; gap: 12px; }}
.card {{ background: white; border: 1px solid #e4ddd0; border-radius: 8px; padding: 16px; }}
.stage {{ float: right; background: #e7f4ee; color: #0f6b4c; border-radius: 99px; padding: 2px 8px; }}
a {{ display: block; margin: 8px 0; color: #0f6b4c; overflow-wrap: anywhere; }}
.card p, small {{ color: #66717a; }}
.empty {{ background: white; border-radius: 8px; padding: 28px; text-align: center; }}
@media (max-width: 720px) {{ ol {{ grid-template-columns: 1fr 1fr; }} }}
</style>
</head>
<body>
<main>
<h1>审核工厂看板</h1>
<p class="lead">受理、取证、判定、汇入检查都留在这里。合并仍由人在 Gitee 上完成。</p>
<ol>{summary}</ol>
<section class="cards">{_cards(records)}</section>
</main>
</body>
</html>
"""
