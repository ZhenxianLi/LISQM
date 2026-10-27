#!/usr/bin/env python3
"""Check, title and notes of a GitHub release of LISQM, for .github/workflows/release.yml.

A new second number of the version (0.6.0, 0.7.0, ...) is released: the commit that sets it is pushed to `main`
with a first line that reads "Release X.Y.Z" (optionally followed by ": what is new"), and the release workflow
turns it into the tag vX.Y.Z and a GitHub release, with the whole list as data (data/index.json) attached.

    python scripts/release.py check 0.6.0   # data/site.yaml and CITATION.cff carry this version
    python scripts/release.py title 0.6.0   # "LISQM 0.6.0: <the title of its update note>"
    python scripts/release.py notes 0.6.0   # Markdown: the update notes since the previous release

The notes are taken from data/updates.yaml: every note of a version above the previous release (found among the
git tags vX.Y.Z), and every note without a version that is dated after the commit of that release.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from typing import Any

from _common import DATA_DIR, REPO_ROOT, load_yaml

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
NOTE_VERSION_RE = re.compile(r"^Version (\d+(?:\.\d+){0,2})\b:?\s*(.*)$")


def version_tuple(text: str) -> tuple[int, int, int]:
    """'0.5' -> (0, 5, 0); '0.5.10' -> (0, 5, 10)."""
    parts = [int(p) for p in str(text).split(".")]
    return tuple((parts + [0, 0, 0])[:3])  # type: ignore[return-value]


def note_version(title: str) -> tuple[tuple[int, int, int], str] | None:
    """The version an update note is about and the rest of its title, from "Version 0.5.9: what is new"."""
    m = NOTE_VERSION_RE.match(str(title).strip())
    return (version_tuple(m.group(1)), m.group(2).strip()) if m else None


def select(updates: list[dict[str, Any]], version: str, previous: str | None,
           since: str | None) -> list[dict[str, Any]]:
    """The update notes that belong to a release, newest first (the order of data/updates.yaml)."""
    current, before = version_tuple(version), version_tuple(previous) if previous else None
    chosen = []
    for u in updates:
        nv = note_version(u.get("title", ""))
        if nv:
            if nv[0] <= current and (before is None or nv[0] > before):
                chosen.append(u)
        elif since is None or str(u.get("date")) > since:
            chosen.append(u)
    return chosen


def markdown(text: str | None) -> str:
    """Paragraphs and '- ' lists of an update note, with the line breaks inside them removed."""
    out = []
    for chunk in re.split(r"\n\s*\n", str(text or "").strip()):
        lines = [ln.rstrip() for ln in chunk.splitlines() if ln.strip()]
        if not lines:
            continue
        items: list[str] = []
        for ln in lines:
            if ln.lstrip().startswith("- "):
                items.append(ln.strip())
            elif items:
                items[-1] += " " + ln.strip()
            else:
                items.append(ln.strip())
        if all(i.startswith("- ") for i in items):
            out.append("\n".join(items))
        else:
            out.append(" ".join(items))
    return "\n\n".join(out)


def title(updates: list[dict[str, Any]], version: str) -> str:
    """'LISQM 0.6.0: <what is new>', from the update note of this version (or of 0.6 for 0.6.0)."""
    for u in updates:
        nv = note_version(u.get("title", ""))
        if nv and nv[0] == version_tuple(version) and nv[1]:
            return f"LISQM {version}: {nv[1]}"
    return f"LISQM {version}"


def notes(updates: list[dict[str, Any]], version: str, previous: str | None, since: str | None,
          index: dict[str, Any]) -> str:
    counts = index.get("counts", {})
    head = (f"LISQM {version}, the list as of {index.get('as_of', date.today().isoformat())}: "
            f"{counts.get('metrics', '?')} metrics, {counts.get('projects', '?')} projects and "
            f"{counts.get('references', '?')} standards and papers. Website: {index.get('url', '')}\n\n"
            f"The attached `lisqm-{version}.json` is the whole list as data, the same as `data/index.json` "
            "at this version.")
    body = [head, f"## Changes since {previous}" if previous else "## Changes"]
    for u in select(updates, version, previous, since):
        body.append(f"### {u.get('date')}: {u.get('title')}\n\n{markdown(u.get('body'))}")
    return "\n\n".join(body) + "\n"


def previous_release(version: str) -> tuple[str | None, str | None]:
    """The highest tag vX.Y.Z below `version`, and the date of its commit (YYYY-MM-DD)."""
    tags = subprocess.run(["git", "tag", "-l", "v*"], capture_output=True, text=True, check=True,
                          cwd=REPO_ROOT).stdout.split()
    lower = [t[1:] for t in tags if VERSION_RE.match(t[1:]) and version_tuple(t[1:]) < version_tuple(version)]
    if not lower:
        return None, None
    best = max(lower, key=version_tuple)
    day = subprocess.run(["git", "log", "-1", "--format=%cs", f"v{best}"], capture_output=True, text=True,
                         check=True, cwd=REPO_ROOT).stdout.strip()
    return best, day or None


def check(version: str) -> list[str]:
    """Problems that stop a release: a malformed version, or one that the data and CITATION.cff do not carry."""
    if not VERSION_RE.match(version):
        return [f"'{version}' is not a version of the form X.Y.Z"]
    problems = []
    site = str(load_yaml(DATA_DIR / "site.yaml").get("version"))
    if site != version:
        problems.append(f"data/site.yaml has version {site}, not {version}")
    cff = re.search(r'^version:\s*"?([^"\s]+)"?\s*$', (REPO_ROOT / "CITATION.cff").read_text(encoding="utf-8"),
                    re.M)
    if not cff or cff.group(1) != version:
        problems.append(f"CITATION.cff has version {cff.group(1) if cff else 'none'}, not {version}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("action", choices=("check", "title", "notes"))
    parser.add_argument("version")
    args = parser.parse_args(argv)
    if args.action == "check":
        problems = check(args.version)
        for p in problems:
            print(f"::error::{p}", file=sys.stderr)
        return 1 if problems else 0
    updates = load_yaml(DATA_DIR / "updates.yaml") or []
    if args.action == "title":
        print(title(updates, args.version))
        return 0
    index = json.loads((DATA_DIR / "index.json").read_text(encoding="utf-8"))
    previous, since = previous_release(args.version)
    sys.stdout.write(notes(updates, args.version, previous, since, index))
    return 0


if __name__ == "__main__":
    sys.exit(main())
