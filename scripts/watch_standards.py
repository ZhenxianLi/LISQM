#!/usr/bin/env python3
"""Watch the standards the index relies on for new editions and stage changes.

The sources are listed in data/standards-watch.yaml:
  - iso-open-data: ISO's open data set of deliverables (JSON Lines, about 80 MB, streamed). Every deliverable
    whose reference matches one of the source's `patterns` is recorded with its reference, currentStage,
    publicationDate, edition and replacedBy.
  - page: a web page. The sorted set of strings matched by the source's `extract` regex in the page's
    visible text (edition statements, for example) and a SHA-256 hash of that text are recorded.

The results are compared with the last seen state in data/standards-watch.json, the differences are written
as a Markdown report, and the state file is only rewritten when something changed. A source that cannot be
loaded is reported and keeps its previous state.

State format: {"<source id>": {"deliverables": {"<ISO id>": {"reference": …, "currentStage": 6060,
"publicationDate": "YYYY-MM-DD", "edition": 1, "replacedBy": [ids]}}}} for ISO sources and
{"<source id>": {"editions": [strings], "text_sha256": "…"}} for pages.
"""

from __future__ import annotations

import argparse
import hashlib
import html.parser
import json
import re
import sys
from pathlib import Path
from typing import Any

from _common import (DATA_DIR, FETCH_ERRORS, FetchError, Http, describe_error, dump_json, load_json, load_yaml, log,
                     md_text, plural, write_report)

ISO_FIELDS = ("reference", "currentStage", "publicationDate", "edition", "replacedBy")

# ISO harmonized stage codes (https://www.iso.org/stage-codes.html): names of a few frequent codes, else the
# name of the stage group given by the first two digits.
STAGE_NAMES = {6000: "under publication", 6060: "published", 9092: "to be revised", 9093: "confirmed",
               9599: "withdrawn"}
STAGE_GROUPS = {0: "preliminary", 10: "proposal", 20: "preparatory", 30: "committee", 40: "enquiry",
                50: "approval", 60: "publication", 90: "review", 95: "withdrawal"}


class SourceError(FetchError):
    """A source was fetched but its content cannot be trusted (truncated or empty)."""


# ---------------------------------------------------------------------------------------------- configuration


def load_sources(path: Path) -> list[dict[str, Any]]:
    """The sources of data/standards-watch.yaml; exits with a message when the file is invalid."""
    sources = load_yaml(path) or []
    if not isinstance(sources, list):
        raise SystemExit(f"{path}: expected a list of sources")
    seen = set()
    for number, source in enumerate(sources):
        where = f"{path.name}[{number}]"
        if not isinstance(source, dict) or not source.get("id") or not source.get("url"):
            raise SystemExit(f"{where}: every source needs an id and a url")
        if source["id"] in seen:
            raise SystemExit(f"{where}: duplicate id {source['id']!r}")
        seen.add(source["id"])
        if source.get("type") == "iso-open-data":
            patterns = source.get("patterns")
            if not patterns or not isinstance(patterns, list):
                raise SystemExit(f"{where}: an iso-open-data source needs a list of patterns")
        elif source.get("type") == "page":
            if not source.get("extract"):
                raise SystemExit(f"{where}: a page source needs an extract pattern")
            patterns = [source["extract"]]
        else:
            raise SystemExit(f"{where}: type must be iso-open-data or page")
        for pattern in patterns:
            try:
                re.compile(pattern)
            except (re.error, TypeError) as err:
                raise SystemExit(f"{where}: invalid regular expression {pattern!r}: {err}") from None
    return sources


# ---------------------------------------------------------------------------------------------- checks


def check_iso(http: Http, source: dict[str, Any]) -> dict[str, Any]:
    """Matching deliverables of ISO's open data set, read line by line without holding the file in memory."""
    patterns = [re.compile(pattern) for pattern in source["patterns"]]
    deliverables = {}
    records = received = 0
    with http.open(source["url"]) as response:
        expected = response.headers.get("Content-Length")
        for number, line in enumerate(response, 1):
            received += len(line)
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except ValueError as err:  # usually a download cut off in the middle of a line
                raise SourceError(f"invalid JSON on line {number}: {err}") from None
            records += 1
            if any(pattern.search(record.get("reference") or "") for pattern in patterns):
                entry = {key: record.get(key) for key in ISO_FIELDS}
                if isinstance(entry["replacedBy"], list):
                    entry["replacedBy"] = sorted(entry["replacedBy"])
                deliverables[str(record["id"])] = entry
    if expected and expected.isdigit() and received != int(expected):
        raise SourceError(f"incomplete download: {received} of {expected} bytes")
    if not records:
        raise SourceError("the data set is empty")
    if not deliverables:  # rather than reporting every recorded standard as gone
        raise SourceError(f"none of the {records} deliverables matches the patterns; has the data format changed?")
    return {"deliverables": deliverables}


class _VisibleText(html.parser.HTMLParser):
    """Collects the text a browser shows: no scripts, styles or templates; block elements separate words."""

    HIDDEN = {"script", "style", "noscript", "template", "svg"}
    BLOCKS = {"address", "article", "aside", "blockquote", "br", "dd", "div", "dl", "dt", "figcaption", "footer",
              "form", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "li", "main", "nav", "ol", "p", "pre",
              "section", "table", "td", "th", "title", "tr", "ul"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.HIDDEN:
            self.hidden += 1
        elif tag in self.BLOCKS:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.HIDDEN:
            self.hidden = max(self.hidden - 1, 0)
        elif tag in self.BLOCKS:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


def visible_text(markup: str) -> str:
    """The page's visible text with whitespace collapsed."""
    parser = _VisibleText()
    parser.feed(markup)
    parser.close()
    return " ".join("".join(parser.parts).split())


def check_page(http: Http, source: dict[str, Any]) -> dict[str, Any]:
    text = visible_text(http.get(source["url"]).decode("utf-8", errors="replace"))
    pattern = re.compile(source["extract"])
    return {
        "editions": sorted({" ".join(match.group(0).split()) for match in pattern.finditer(text)}),
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


CHECKS = {"iso-open-data": check_iso, "page": check_page}


# ---------------------------------------------------------------------------------------------- differences


def stage_label(code: Any) -> str:
    """"60.60 (published)" for 6060."""
    if not isinstance(code, int):
        return "unknown stage"
    name = STAGE_NAMES.get(code) or STAGE_GROUPS.get(code // 100, "unknown")
    return f"{code // 100:02d}.{code % 100:02d} ({name})"


def _iso_link(deliverable_id: str, deliverable: dict[str, Any]) -> str:
    reference = md_text(deliverable.get("reference") or f"ISO deliverable {deliverable_id}")
    return f"[{reference}](https://www.iso.org/standard/{deliverable_id}.html)"


def _iso_summary(deliverable_id: str, deliverable: dict[str, Any]) -> str:
    facts = [f"stage {stage_label(deliverable.get('currentStage'))}"]
    if deliverable.get("publicationDate"):
        facts.append(f"published {deliverable['publicationDate']}")
    if deliverable.get("edition"):
        facts.append(f"edition {deliverable['edition']}")
    return f"{_iso_link(deliverable_id, deliverable)}: {', '.join(facts)}"


def _by_reference(deliverables: dict[str, dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
    return sorted(deliverables.items(), key=lambda item: (str(item[1].get("reference") or ""), item[0]))


def diff_iso(old: dict[str, Any] | None, new: dict[str, Any]) -> list[str]:
    current = new["deliverables"]
    if old is None:
        return [f"First check; {plural(len(current), 'matching deliverable')} recorded:", "",
                *[f"- {_iso_summary(did, d)}" for did, d in _by_reference(current)]]
    previous = old.get("deliverables") or {}

    def replaced_by(ids: list[int] | None) -> str:
        return ", ".join(_iso_link(str(i), current.get(str(i)) or {}) for i in ids or []) or "nothing"

    lines = []
    for did, deliverable in _by_reference(current):
        before = previous.get(did)
        if before is None:
            lines.append(f"- New: {_iso_summary(did, deliverable)}")
            continue
        changes = []
        if before.get("reference") != deliverable.get("reference"):
            changes.append(f"reference was {md_text(before.get('reference'))}")
        if before.get("currentStage") != deliverable.get("currentStage"):
            changes.append(f"stage {stage_label(before.get('currentStage'))} → "
                           f"{stage_label(deliverable.get('currentStage'))}")
        if before.get("publicationDate") != deliverable.get("publicationDate"):
            changes.append(f"publication date {before.get('publicationDate') or 'none'} → "
                           f"{deliverable.get('publicationDate') or 'none'}")
        if before.get("edition") != deliverable.get("edition"):
            changes.append(f"edition {before.get('edition')} → {deliverable.get('edition')}")
        if before.get("replacedBy") != deliverable.get("replacedBy"):
            changes.append(f"replaced by {replaced_by(deliverable.get('replacedBy'))}")
        if changes:
            lines.append(f"- {_iso_link(did, deliverable)}: {'; '.join(changes)}")
    lines += [f"- No longer in the data set: {_iso_link(did, d)}"
              for did, d in _by_reference(previous) if did not in current]
    return lines


def diff_page(old: dict[str, Any] | None, new: dict[str, Any], url: str) -> list[str]:
    def quoted(strings: list[str]) -> str:
        return ", ".join(f"“{md_text(text)}”" for text in strings) or "none"

    if old is None:
        return [f"- First check of [the page]({url}); matched: {quoted(new['editions'])}"]
    added = sorted(set(new["editions"]) - set(old.get("editions") or []))
    removed = sorted(set(old.get("editions") or []) - set(new["editions"]))
    lines = []
    if added:
        lines.append(f"- New on [the page]({url}): {quoted(added)}")
    if removed:
        lines.append(f"- No longer on [the page]({url}): {quoted(removed)}")
    if not lines and old.get("text_sha256") != new["text_sha256"]:
        lines.append(f"- The text of [the page]({url}) changed; the matched strings did not")
    return lines


def check_all(http: Http, sources: list[dict[str, Any]],
              previous: dict[str, Any]) -> tuple[dict[str, Any], list[tuple[str, list[str]]], list[str]]:
    """(new state, report sections as (title, lines), errors). Sources that are no longer configured are
    dropped from the state; a source that fails keeps its previous state."""
    state: dict[str, Any] = {}
    sections, errors = [], []
    for source in sources:
        sid, title = source["id"], md_text(source.get("name") or source["id"])
        old = previous.get(sid)
        log(f"Checking {sid}: {source['url']}")
        try:
            new = CHECKS[source["type"]](http, source)
        except FETCH_ERRORS as err:
            errors.append(f"- {title} (`{sid}`): {md_text(describe_error(err), limit=500)}; previous state kept")
            if old is not None:
                state[sid] = old
            continue
        state[sid] = new
        lines = diff_iso(old, new) if source["type"] == "iso-open-data" else diff_page(old, new, source["url"])
        if lines:
            sections.append((title, lines))
    return state, sections, errors


def render_report(sections: list[tuple[str, list[str]]], errors: list[str], checked: int) -> str:
    """Markdown report; a single line when nothing changed."""
    if not sections and not errors:
        return f"No changes in the watched standards ({plural(checked, 'source')} checked).\n"
    lines = []
    for title, items in sections:
        lines += [f"### {title}", "", *items, ""]
    if errors:
        lines += ["### Errors", "", *errors, ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--report", type=Path, metavar="PATH",
                        help="write the Markdown report to PATH (default: print it); it is a single line "
                             "when there is nothing to report")
    parser.add_argument("--dry-run", action="store_true", help="print the report; do not update the state file")
    args = parser.parse_args(argv)

    sources = load_sources(DATA_DIR / "standards-watch.yaml")
    state_path = DATA_DIR / "standards-watch.json"
    previous = load_json(state_path)
    state, sections, errors = check_all(Http(), sources, previous)
    report = render_report(sections, errors, len(sources))
    if args.dry_run:
        print(report, end="")
        return 0
    if state != previous:
        state_path.write_text(dump_json(state), encoding="utf-8")
        log(f"Wrote {state_path}")
    else:
        log(f"No changes; {state_path} left untouched")
    write_report(report, args.report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
