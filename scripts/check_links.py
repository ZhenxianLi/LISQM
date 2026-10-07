#!/usr/bin/env python3
"""Check the external links in the list data and report the ones that are broken.

Every URL in data/projects/*.yaml, data/references.yaml, data/metrics.yaml, data/leads.yaml, data/updates.yaml
and data/site.yaml is requested once (HEAD, then GET when HEAD fails), DOIs through https://doi.org/. A link is
  - broken when the server answers 404 or 410, or its host name does not resolve: reported at once;
  - unreachable when it fails in another way (time-out, connection error, server error): reported only when it
    also failed in the previous run, so that a single network hiccup is not reported.
Answers 401, 403 and 429 are not judged: many publishers and standards bodies refuse automated requests.

The links that failed are kept in data/link-check.json, {"generated": timestamp, "failing": {url: {"since":
date, "detail": text}}}, which is rewritten only when that list changes. The report is Markdown for the review
issue and a single line when there is nothing to fix.

    python scripts/check_links.py --report links.md
    python scripts/check_links.py --dry-run
"""

from __future__ import annotations

import argparse
import http.client
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import _common
from _common import (DATA_DIR, day, dump_json, load_json, load_yaml, log, md_text, plural, timestamp, user_agent,
                     utc_now, write_report)

STATE = DATA_DIR / "link-check.json"
FILES = ("references.yaml", "metrics.yaml", "leads.yaml", "updates.yaml", "site.yaml")
GONE = {404, 410}
# "This robot may not look", not "this page is gone".
REFUSED = {401, 403, 429, 999}
_URL = re.compile(r"https?://[^\s<>()\[\]\"'`]+")


def collect(data_dir: Path = DATA_DIR) -> dict[str, list[str]]:
    """Every external URL in the data, with the files it appears in (in order of first appearance)."""
    found: dict[str, list[str]] = {}

    def add(url: str, where: str) -> None:
        url = url.rstrip(".,;:")
        found.setdefault(url, [])
        if where not in found[url]:
            found[url].append(where)

    def walk(value: Any, where: str, key: str = "") -> None:
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, where, str(k))
        elif isinstance(value, list):
            for v in value:
                walk(v, where, key)
        elif isinstance(value, str):
            if key == "doi" and not value.startswith("http"):
                add(f"https://doi.org/{value.strip()}", where)
            for url in _URL.findall(value):
                add(url, where)

    for path in sorted((data_dir / "projects").glob("*.yaml")):
        walk(load_yaml(path), f"data/projects/{path.name}")
    for name in FILES:
        path = data_dir / name
        if path.exists():
            walk(load_yaml(path), f"data/{name}")
    return found


def check(url: str, timeout: float = 30.0, retry_wait: float = 5.0) -> tuple[str, str]:
    """('ok' | 'broken' | 'refused' | 'error', detail). A server error or network failure is tried once more."""
    result = _check_once(url, timeout)
    if result[0] == "error":
        time.sleep(retry_wait)
        result = _check_once(url, timeout)
    return result


def _check_once(url: str, timeout: float) -> tuple[str, str]:
    headers = {"User-Agent": user_agent(), "Accept": "*/*"}
    for method in ("HEAD", "GET"):  # many servers refuse or mishandle HEAD, so every HEAD failure is retried as GET
        request = urllib.request.Request(url, method=method, headers=headers)
        try:
            with _common._urlopen(request, timeout):
                return "ok", ""
        except urllib.error.HTTPError as err:
            if method == "GET":
                kind = "broken" if err.code in GONE else "refused" if err.code in REFUSED else "error"
                return kind, f"HTTP {err.code}"
        except urllib.error.URLError as err:
            if isinstance(err.reason, socket.gaierror):
                return "broken", "host not found"
            if method == "GET":
                return "error", f"network error: {err.reason}"
        except (OSError, http.client.HTTPException, ValueError) as err:
            if method == "GET":
                return "error", f"network error: {err}"
    raise AssertionError("unreachable")


def check_all(urls: list[str], workers: int = 4) -> dict[str, tuple[str, str]]:
    """Check every URL, a few at a time (most are on github.com, which limits the request rate)."""
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return dict(zip(urls, pool.map(check, urls)))


def evaluate(results: dict[str, tuple[str, str]], previous: dict[str, Any],
             today: str) -> tuple[dict[str, Any], list[str], list[str]]:
    """The new list of failing links (keeping the date each first failed), the broken links, and the links that
    could not be reached in this run and the one before."""
    before = previous.get("failing") or {}
    failing = {url: {"since": (before.get(url) or {}).get("since") or today, "detail": detail}
               for url, (kind, detail) in results.items() if kind in ("broken", "error")}
    broken = [url for url, (kind, _) in results.items() if kind == "broken"]
    unreachable = [url for url, (kind, _) in results.items() if kind == "error" and url in before]
    return failing, broken, unreachable


def render_report(found: dict[str, list[str]], results: dict[str, tuple[str, str]], failing: dict[str, Any],
                  broken: list[str], unreachable: list[str]) -> str:
    """Markdown for the review issue; a single line when nothing needs fixing."""
    refused = sum(kind == "refused" for kind, _ in results.values())
    counts = f"{plural(len(results), 'link')} checked" + (
        f"; {refused} refused automated requests and were not judged" if refused else "")
    if not broken and not unreachable:
        return f"No broken links ({counts}).\n"

    def item(url: str) -> str:
        where = ", ".join(f"`{w}`" for w in found.get(url, []))
        detail = md_text(failing[url]["detail"], limit=200)
        since = f", failing since {failing[url]['since']}" if url in unreachable else ""
        return f"- {url} ({detail}{since}) in {where}"

    lines = [counts[:1].upper() + counts[1:] + ".", ""]
    if broken:
        lines += ["### Broken links", "", "The page is gone or its host no longer exists; replace or remove the link.",
                  "", *[item(url) for url in broken], ""]
    if unreachable:
        lines += ["### Unreachable twice in a row", "", "Check by hand whether the site is down or has moved.", "",
                  *[item(url) for url in unreachable], ""]
    return "\n".join(lines)


def write_state(path: Path, failing: dict[str, Any], previous: dict[str, Any], now: str) -> bool:
    """Write the list of failing links unless it is unchanged; True when the file was written."""
    if path.exists() and (previous.get("failing") or {}) == failing:
        return False
    path.write_text(dump_json({"generated": now, "failing": failing}), encoding="utf-8")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--report", type=Path, metavar="PATH",
                        help="write the Markdown report to PATH (default: print it)")
    parser.add_argument("--dry-run", action="store_true", help="print the report; do not update the state file")
    args = parser.parse_args(argv)

    found = collect()
    log(f"Checking {plural(len(found), 'link')}")
    results = check_all(list(found))
    previous = load_json(STATE)
    now = utc_now()
    failing, broken, unreachable = evaluate(results, previous, day(now) or "")
    report = render_report(found, results, failing, broken, unreachable)
    if args.dry_run:
        print(report, end="")
        return 0
    log(f"Wrote {STATE}" if write_state(STATE, failing, previous, timestamp(now)) else f"No changes; {STATE} left untouched")
    write_report(report, args.report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
