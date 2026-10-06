"""Small text helpers shared by the HTML and Markdown renderers."""

from __future__ import annotations

import datetime as dt
import html
import re

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]

_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_CODE = re.compile(r"`([^`]+)`")
_STRONG = re.compile(r"\*\*([^*]+)\*\*")
_EM = re.compile(r"(?<![\w*])\*([^*\s][^*]*?)\*(?![\w*])")


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def inline(text: str | None) -> str:
    """Render the inline Markdown subset used in data files ([link](url), `code`, **strong**, *em*) to HTML."""
    if not text:
        return ""
    # Protect code spans first so their contents are not parsed as emphasis or links.
    codes: list[str] = []

    def keep_code(m: re.Match[str]) -> str:
        codes.append(f"<code>{esc(m.group(1))}</code>")
        return f"\x00{len(codes) - 1}\x00"

    out = _CODE.sub(keep_code, str(text))
    out = esc(out)
    out = _LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', out)
    out = _STRONG.sub(r"<strong>\1</strong>", out)
    out = _EM.sub(r"<em>\1</em>", out)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], out)


def blocks(text: str | None) -> str:
    """Render paragraphs and '- ' bullet lists (the block subset used in updates and notes) to HTML."""
    if not text:
        return ""
    out: list[str] = []
    for chunk in re.split(r"\n\s*\n", str(text).strip()):
        lines = [ln.rstrip() for ln in chunk.splitlines() if ln.strip()]
        if lines and all(ln.lstrip().startswith("- ") for ln in lines):
            items = "".join(f"<li>{inline(ln.lstrip()[2:])}</li>" for ln in lines)
            out.append(f"<ul>{items}</ul>")
        else:
            out.append(f"<p>{inline(' '.join(ln.strip() for ln in lines))}</p>")
    return "\n".join(out)


def plain(text: str | None) -> str:
    """Strip the inline Markdown subset, for meta descriptions and JSON-LD."""
    if not text:
        return ""
    out = _LINK.sub(r"\1", str(text))
    out = _CODE.sub(r"\1", out)
    out = _STRONG.sub(r"\1", out)
    out = _EM.sub(r"\1", out)
    return re.sub(r"\s+", " ", out).strip()


def oneline(text: str | None) -> str:
    """Collapse whitespace so Markdown text can sit in a table cell."""
    return re.sub(r"\s+", " ", str(text or "")).strip().replace("|", "\\|")


def date_str(value: object) -> str:
    """Normalise YAML dates (date objects or 'YYYY[-MM[-DD]]' strings) to ISO strings."""
    if value is None or value == "":
        return ""
    if isinstance(value, (dt.date, dt.datetime)):
        return value.strftime("%Y-%m-%d")
    return str(value)


def long_date(value: object) -> str:
    """'2026-10-06' -> '6 October 2026'; partial dates keep their precision."""
    s = date_str(value)
    parts = s.split("-")
    try:
        if len(parts) == 3:
            return f"{int(parts[2])} {MONTHS[int(parts[1]) - 1]} {parts[0]}"
        if len(parts) == 2:
            return f"{MONTHS[int(parts[1]) - 1]} {parts[0]}"
    except (ValueError, IndexError):
        pass
    return s


def month(value: object) -> str:
    """'2026-10-06' -> '2026-10' (tables show months, which is the precision that matters here)."""
    s = date_str(value)
    return s[:7] if len(s) >= 7 else s


def join_words(items: list[str], conj: str = "and") -> str:
    items = [i for i in items if i]
    if len(items) <= 1:
        return "".join(items)
    if len(items) == 2:
        return f"{items[0]} {conj} {items[1]}"
    return ", ".join(items[:-1]) + f", {conj} {items[-1]}"


def plural(n: int, word: str, many: str | None = None) -> str:
    return f"{n} {word if n == 1 else (many or word + 's')}"
