#!/usr/bin/env python3
"""Checks and bookkeeping around the automated review (scripts/review_agent.py, .github/workflows/review.yml).

The review agent edits data files in a checkout of `main`. Its changes are published only when they pass the
checks here, which hold whatever a source read during the review asked for:

  - only data files change: data/projects/<id>.yaml (new or changed, never deleted), data/references.yaml,
    data/metrics.yaml, data/ignored.yaml, data/leads.yaml and data/standards-watch.yaml;
  - the owner's fields stay as they are: no project gains or changes super_project, highlight or rank, an
    existing project keeps its id and its standing, and a new project is not listed as established;
  - no added line carries an e-mail address.

    python scripts/review_guard.py check [--report r.json]   # the working tree against HEAD; exit 1 on a problem
    python scripts/review_guard.py finish report.json        # new third version number and update note
    python scripts/review_guard.py comment report.json URL   # Markdown comment for the review issue
    python scripts/review_guard.py can-close report.json     # "true" when every item was settled

`finish` raises the third number of the version (data/site.yaml, CITATION.cff) and adds a dated note to
data/updates.yaml when the review changed what the website shows.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from _common import REPO_ROOT, md_text

ALLOWED = re.compile(r"data/projects/[a-z0-9][a-z0-9-]*\.yaml|data/(references|metrics|ignored|leads|"
                     r"standards-watch)\.yaml")
# Files whose changes do not show on the website: no new version or update note for them alone.
UNPUBLISHED = {"data/ignored.yaml", "data/standards-watch.yaml"}
OWNER_FIELDS = ("super_project", "highlight", "rank")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
MAX_ADDED_LINES = 3000
OUTCOMES = ("changed", "no_change", "needs_owner", "unreachable", "failed")
MARKER = "<!-- review-agent body={sha} -->"


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout


def changes(root: Path = REPO_ROOT) -> list[tuple[str, str]]:
    """(status, path) of every changed or new file in the working tree, as `git status --porcelain` gives them."""
    out = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries, parts = [], out.split("\0")
    i = 0
    while i < len(parts):
        entry = parts[i]
        i += 1
        if not entry:
            continue
        status, path = entry[:2], entry[3:]
        if "R" in status or "C" in status:
            i += 1  # the source path of a rename or copy follows
        entries.append((status, path))
    return entries


def _head_yaml(root: Path, path: str) -> Any:
    try:
        return yaml.safe_load(git(root, "show", f"HEAD:{path}"))
    except subprocess.CalledProcessError:
        return None


def check(root: Path = REPO_ROOT) -> list[str]:
    """Problems that keep the review's changes from being published (an empty list when there are none)."""
    problems = []
    for status, path in changes(root):
        if not ALLOWED.fullmatch(path):
            problems.append(f"{path}: only data files may change in an automated review")
            continue
        if "D" in status or "R" in status or "C" in status:
            problems.append(f"{path}: files are not deleted or renamed in an automated review")
            continue
        try:
            new = yaml.safe_load((root / path).read_text(encoding="utf-8"))
        except yaml.YAMLError as err:
            problems.append(f"{path}: not valid YAML ({err})")
            continue
        if not path.startswith("data/projects/"):
            continue
        if not isinstance(new, dict):
            problems.append(f"{path}: a project file holds one mapping")
            continue
        old = _head_yaml(root, path)
        if isinstance(old, dict):
            for field in ("id", "standing", *OWNER_FIELDS):
                if old.get(field) != new.get(field):
                    problems.append(f"{path}: {field} is the owner's to change "
                                    f"({old.get(field)!r} -> {new.get(field)!r})")
        else:
            stem = Path(path).stem
            if new.get("id") != stem:
                problems.append(f"{path}: id must be {stem!r}, the file name")
            for field in OWNER_FIELDS:
                if field in new:
                    problems.append(f"{path}: {field} is the owner's to set")
            if new.get("standing") == "established":
                problems.append(f"{path}: only the owner lists a new project as established")
    added = [line[1:] for line in git(root, "diff", "-U0", "HEAD", "--", "data").splitlines()
             if line.startswith("+") and not line.startswith("+++")]
    for status, path in changes(root):
        if status == "??" and ALLOWED.fullmatch(path):
            added += (root / path).read_text(encoding="utf-8").splitlines()
    for line in added:
        if EMAIL.search(line):
            problems.append(f"an added line carries an e-mail address: {line.strip()[:120]}")
    if len(added) > MAX_ADDED_LINES:
        problems.append(f"{len(added)} added lines, more than the {MAX_ADDED_LINES} an automated review may add")
    return problems


def bump_version(root: Path, day: str, notes: list[str]) -> str:
    """Raise the third number of the version and add a dated update note listing `notes`; return the version."""
    site = root / "data" / "site.yaml"
    text = site.read_text(encoding="utf-8")
    current = re.search(r"^version:\s*(\d+)\.(\d+)\.(\d+)\s*$", text, re.M)
    if not current:
        raise SystemExit("data/site.yaml has no version X.Y.Z")
    major, minor, patch = (int(n) for n in current.groups())
    version = f"{major}.{minor}.{patch + 1}"
    site.write_text(text[:current.start()] + f"version: {version}" + text[current.end():], encoding="utf-8")
    cff = root / "CITATION.cff"
    text = cff.read_text(encoding="utf-8")
    text = re.sub(r'^version:\s*"?[^"\n]*"?\s*$', f'version: "{version}"', text, count=1, flags=re.M)
    text = re.sub(r'^date-released:\s*"?[^"\n]*"?\s*$', f'date-released: "{day}"', text, count=1, flags=re.M)
    cff.write_text(text, encoding="utf-8")
    updates = root / "data" / "updates.yaml"
    text = updates.read_text(encoding="utf-8")
    body = "".join(f"    - {' '.join(note.split())}\n" for note in notes)
    entry = (f"- date: {day}\n  title: \"Version {version}: automated review\"\n  body: |\n"
             f"    Changes from the automated review of {day}:\n\n{body}\n")
    first = text.find("\n- ")
    if first < 0:
        raise SystemExit("data/updates.yaml has no entry to insert before")
    updates.write_text(text[:first + 1] + entry + text[first + 1:], encoding="utf-8")
    return version


def finish(root: Path, report: dict[str, Any]) -> str | None:
    """Bump the version when the review changed what the website shows; return the new version or None."""
    published = [path for _, path in changes(root) if path not in UNPUBLISHED]
    notes = [i["public_note"] for i in report.get("items", []) if i.get("public_note")]
    if not published:
        return None
    if not notes:
        notes = ["Entries were updated from their sources."]
    return bump_version(root, report.get("date") or date.today().isoformat(), notes)


def can_close(report: dict[str, Any]) -> bool:
    """The review issue is closed when every item was settled and the run did not stop early."""
    return not report.get("stopped_early") and all(
        i.get("outcome") in ("changed", "no_change") for i in report.get("items", []))


def label(item: Any) -> str:
    """The first line of an issue item as plain words: links as "text (url)", no bold or code marks."""
    first = str(item or "").splitlines()[0] if item else ""
    first = re.sub(r"\[([^\]]*)\]\((https?://[^)\s]+)\)", r"\1 (\2)", first)
    return md_text(first.replace("**", "").replace("`", ""), 200)


def comment(report: dict[str, Any], run_url: str) -> str:
    """The Markdown comment that reports an automated review on the review issue."""
    items = report.get("items", [])
    done = [i for i in items if i.get("outcome") in ("changed", "no_change")]
    owner = [i for i in items if i.get("outcome") == "needs_owner"]
    open_ = [i for i in items if i.get("outcome") in ("unreachable", "failed")]
    what = "the owner's comment" if report.get("mode") == "owner-comment" else "the review"
    lines = [f"Automated work on {what} of {report.get('date')} ([workflow run]({run_url})): "
             f"{len(done)} of {len(items)} items settled."]
    if report.get("version"):
        lines[0] += f" Published as version {report['version']}."
    sections = [("Done", done, "x"), ("Needs the owner", owner, " "), ("Not settled", open_, " ")]
    for title, group, mark in sections:
        if not group:
            continue
        lines += ["", f"### {title}", ""]
        for i in group:
            line = f"- [{mark}] {label(i.get('item'))}: {md_text(i.get('summary'), 1200)}"
            if i.get("question"):
                line += f" **Question:** {md_text(i['question'], 600)}"
            lines.append(line)
    if report.get("stopped_early"):
        lines += ["", f"The run stopped early: {md_text(report.get('stop_reason'), 300)}. The items it did not reach "
                      "are left for the next run."]
    if report.get("rejected"):
        lines += ["", "Nothing was published, because the changes did not pass the checks:", ""]
        lines += [f"- {md_text(p, 300)}" for p in report["rejected"]]
    if owner:
        lines += ["", "Answer in a comment on this issue: the workflow reads the owner's comments and applies the "
                      "answers."]
    cost = report.get("cost_usd")
    if cost is not None:
        lines += ["", f"Model {report.get('model')}, estimated API cost ${cost:.2f}."]
    lines += ["", MARKER.format(sha=report.get("issue_body_sha256", ""))]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("check")
    p.add_argument("--report", type=Path, help="also record the problems in this report as rejected")
    p = sub.add_parser("finish")
    p.add_argument("report", type=Path)
    p = sub.add_parser("comment")
    p.add_argument("report", type=Path)
    p.add_argument("run_url")
    p = sub.add_parser("can-close")
    p.add_argument("report", type=Path)
    args = parser.parse_args(argv)
    if args.action == "check":
        problems = check()
        for problem in problems:
            print(f"::error::{problem}", file=sys.stderr)
        if problems and args.report:
            report = json.loads(args.report.read_text(encoding="utf-8"))
            report["rejected"] = problems
            args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return 1 if problems else 0
    report = json.loads(args.report.read_text(encoding="utf-8"))
    if args.action == "finish":
        version = finish(REPO_ROOT, report)
        if version:
            report["version"] = version
            args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(version or "")
        return 0
    if args.action == "can-close":
        print("true" if can_close(report) and not report.get("rejected") else "false")
        return 0
    sys.stdout.write(comment(report, args.run_url))
    return 0


if __name__ == "__main__":
    sys.exit(main())
