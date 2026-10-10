"""Render a Gitee comment as HTML. The comment's own HTML stays text."""

from __future__ import annotations

import re
from html import escape

_FENCE = re.compile(r"```[^\n`]*\n(.*?)```", re.DOTALL)
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_BULLET = re.compile(r"^\s*[-*]\s+")
_NUMBER = re.compile(r"^\s*\d+\.\s+")
_RULE = re.compile(r"^(?:-{3,}|\*{3,}|_{3,})$")
_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")
_CODE = re.compile(r"`([^`\n]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_EMPH = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")


def render_comment_markdown(source: str) -> str:
    """Turn one comment into HTML. Raw tags in the comment are not executed."""
    pieces = []
    cursor = 0
    for match in _FENCE.finditer(source or ""):
        pieces.append(_blocks(source[cursor:match.start()]))
        pieces.append(f"<pre><code>{escape(match.group(1).rstrip())}</code></pre>")
        cursor = match.end()
    pieces.append(_blocks((source or "")[cursor:]))
    return "\n".join(piece for piece in pieces if piece)


def _blocks(text: str) -> str:
    lines = text.splitlines()
    blocks = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        heading = _HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{_inline(heading.group(2).strip())}</h{level}>")
            index += 1
            continue
        if _RULE.match(line.strip()):
            blocks.append("<hr>")
            index += 1
            continue
        if line.lstrip().startswith("|") and index + 1 < len(lines) and _TABLE_SEP.match(lines[index + 1]):
            table, index = _table(lines, index)
            blocks.append(table)
            continue
        if _BULLET.match(line):
            items = []
            while index < len(lines) and _BULLET.match(lines[index]):
                items.append(f"<li>{_inline(_BULLET.sub('', lines[index], count=1))}</li>")
                index += 1
            blocks.append("<ul>" + "".join(items) + "</ul>")
            continue
        if _NUMBER.match(line):
            items = []
            while index < len(lines) and _NUMBER.match(lines[index]):
                items.append(f"<li>{_inline(_NUMBER.sub('', lines[index], count=1))}</li>")
                index += 1
            blocks.append("<ol>" + "".join(items) + "</ol>")
            continue
        if line.startswith(">"):
            quoted = []
            while index < len(lines) and lines[index].startswith(">"):
                quoted.append(lines[index][1:].lstrip())
                index += 1
            blocks.append(f"<blockquote><p>{_inline(' '.join(quoted))}</p></blockquote>")
            continue
        paragraph = [line]
        index += 1
        while index < len(lines) and lines[index].strip() and not _starts_block(lines, index):
            paragraph.append(lines[index])
            index += 1
        blocks.append(f"<p>{_inline(' '.join(paragraph))}</p>")
    return "\n".join(blocks)


def _starts_block(lines: list[str], index: int) -> bool:
    line = lines[index]
    if _HEADING.match(line) or _RULE.match(line.strip()) or _BULLET.match(line) or _NUMBER.match(line):
        return True
    if line.startswith(">"):
        return True
    return line.lstrip().startswith("|") and index + 1 < len(lines) and _TABLE_SEP.match(lines[index + 1])


def _table(lines: list[str], index: int) -> tuple[str, int]:
    header = _cells(lines[index])
    index += 2
    rows = []
    while index < len(lines) and lines[index].lstrip().startswith("|"):
        rows.append(_cells(lines[index]))
        index += 1
    head = "".join(f"<th>{_inline(cell)}</th>" for cell in header)
    body = "".join(
        "<tr>" + "".join(f"<td>{_inline(cell)}</td>" for cell in row) + "</tr>" for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>", index


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _inline(text: str) -> str:
    codes: list[str] = []
    links: list[str] = []

    def stash_link(match: re.Match) -> str:
        label = escape(match.group(1))
        href = escape(match.group(2), quote=True)
        links.append(f'<a href="{href}">{label}</a>')
        return f"\u0001{len(links) - 1}\u0001"

    def stash_code(match: re.Match) -> str:
        codes.append(escape(match.group(1)))
        return f"\u0000{len(codes) - 1}\u0000"

    marked = _LINK.sub(stash_link, text)
    marked = _CODE.sub(stash_code, marked)
    safe = escape(marked)
    safe = _BOLD.sub(r"<strong>\1</strong>", safe)
    safe = _EMPH.sub(r"<em>\1</em>", safe)
    safe = re.sub(r"\u0000(\d+)\u0000", lambda match: f"<code>{codes[int(match.group(1))]}</code>", safe)
    return re.sub(r"\u0001(\d+)\u0001", lambda match: links[int(match.group(1))], safe)
