#!/usr/bin/env python3
"""Refresh repository and package metadata of every indexed project into data/snapshot.json.

For each data/projects/*.yaml file this fetches
  - GitHub, when the repository is on github.com: stars, forks, archived flag, default branch, last push,
    licence, description, topics, open issues, the date of the last commit on the default branch and the
    latest release (renamed or transferred repositories are followed);
  - PyPI, crates.io and npm packages: the latest version, its release date and a newer pre-release.
Other hosts and registries are skipped; the build then uses the project's `manual` block.

A failed fetch keeps the previous value and adds a message to the project's "errors" list (errors are reset
on every run). Entries of projects that no longer exist are removed. The file is only rewritten when more
than its timestamps changed, so a run without real changes leaves the working tree clean. The format is
described in data/SCHEMA.md.

GitHub requests use the token in GITHUB_TOKEN or GH_TOKEN; without a token GitHub data is not refreshed.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.parse
from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

from _common import (DATA_DIR, FETCH_ERRORS, GITHUB_API, Http, HttpError, day, describe_error, dump_json,
                     github_repo, github_token, load_json, load_projects, log, md_text, parse_time, plural,
                     timestamp, utc_now, write_report)

REGISTRY_LABELS = {"pypi": "PyPI", "crates": "crates.io", "npm": "npm"}

# Sections of the change report, in display order.
SECTIONS = ("Releases", "Last commits", "Archived", "Licences", "Descriptions", "Moved repositories", "Errors")

# PEP 440 pre-release and development versions: 1.0a1, 1.0b2, 1.0rc1, 1.0.dev3 (and unnormalised spellings).
_PEP440_PRERELEASE = re.compile(r"(a|alpha|b|beta|c|rc|pre|preview|dev)\d*", re.IGNORECASE)


def is_pep440_prerelease(version: str) -> bool:
    return _PEP440_PRERELEASE.search(version) is not None


def is_semver_prerelease(version: str) -> bool:
    """Semantic versioning (crates.io, npm): 1.0.0-beta.1 is a pre-release, 1.0.0+build is not."""
    return "-" in version.split("+", 1)[0]


# ---------------------------------------------------------------------------------------------- GitHub


def fetch_github(http: Http, owner: str, name: str, old: dict[str, Any] | None) -> tuple[dict | None, list[str]]:
    """Repository facts, last commit and latest release, plus error messages. Whatever cannot be fetched
    keeps its previous value."""
    try:
        repo = http.get_json(f"{GITHUB_API}/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(name)}")
        info: dict[str, Any] = {
            "full_name": repo["full_name"],
            "stars": repo["stargazers_count"],
            "forks": repo["forks_count"],
            "archived": repo["archived"],
            "default_branch": repo["default_branch"],
            "pushed_at": repo.get("pushed_at"),
            "license": (repo.get("license") or {}).get("spdx_id"),
            "description": repo.get("description"),
            "topics": sorted(repo.get("topics") or []),
            "open_issues": repo["open_issues_count"],
        }
    except FETCH_ERRORS as err:
        return old, [f"GitHub: {describe_error(err)}"]

    old = old or {}
    errors = []
    # Use the name GitHub returned, so that a renamed repository is not redirected on every request.
    api = f"{GITHUB_API}/repos/{info['full_name']}"
    query = urllib.parse.urlencode({"sha": info["default_branch"], "per_page": 1})
    try:
        commits = http.get_json(f"{api}/commits?{query}")
        info["last_commit"] = day(parse_time(commits[0]["commit"]["committer"]["date"])) if commits else None
    except FETCH_ERRORS as err:
        if isinstance(err, HttpError) and err.status == 409:  # "Git Repository is empty"
            info["last_commit"] = None
        else:
            info["last_commit"] = old.get("last_commit")
            errors.append(f"GitHub last commit: {describe_error(err)}")
    try:
        release = http.get_json(f"{api}/releases/latest")
        info["latest_release"] = {"tag": release["tag_name"], "date": day(parse_time(release.get("published_at"))),
                                  "url": release["html_url"]}
    except FETCH_ERRORS as err:
        if isinstance(err, HttpError) and err.status == 404:  # no published (non-draft, non-pre-) release
            info["latest_release"] = None
        else:
            info["latest_release"] = old.get("latest_release")
            errors.append(f"GitHub latest release: {describe_error(err)}")
    return info, errors


# ---------------------------------------------------------------------------------------------- registries


def newer_prerelease(published: dict[str, datetime], version: str | None,
                     is_prerelease: Callable[[str], bool]) -> dict[str, str | None] | None:
    """The most recently published pre-release if it came out after `version`, else None."""
    since = published.get(version) if version else None
    newer = [v for v in published if is_prerelease(v) and v != version and (since is None or published[v] > since)]
    if not newer:
        return None
    newest = max(newer, key=lambda v: (published[v], v))
    return {"version": newest, "date": day(published[newest])}


def fetch_pypi(http: Http, name: str) -> dict[str, Any]:
    data = http.get_json(f"https://pypi.org/pypi/{urllib.parse.quote(name)}/json")
    # First upload of every version that still has a file that is not yanked (yanked-only versions are ignored).
    uploaded: dict[str, datetime] = {}
    for version, files in (data.get("releases") or {}).items():
        times = [parse_time(f.get("upload_time_iso_8601")) for f in files if not f.get("yanked")]
        times = [t for t in times if t]
        if times:
            uploaded[version] = min(times)
    version = data["info"]["version"]
    if version not in uploaded:  # every file of info.version was yanked: use the newest remaining stable version
        stable = [v for v in uploaded if not is_pep440_prerelease(v)]
        version = max(stable, key=lambda v: (uploaded[v], v)) if stable else None
    return {
        "version": version,
        "date": day(uploaded.get(version)) if version else None,
        "url": data["info"].get("package_url") or f"https://pypi.org/project/{name}/",
        "prerelease": newer_prerelease(uploaded, version, is_pep440_prerelease),
    }


def fetch_crate(http: Http, name: str) -> dict[str, Any]:
    data = http.get_json(f"https://crates.io/api/v1/crates/{urllib.parse.quote(name)}")
    crate = data["crate"]
    published = {v["num"]: t for v in data.get("versions") or []
                 if not v.get("yanked") and (t := parse_time(v.get("created_at")))}
    version = crate.get("max_stable_version") or crate.get("newest_version")
    return {
        "version": version,
        "date": day(published.get(version)) if version else None,
        "url": f"https://crates.io/crates/{name}",
        "prerelease": newer_prerelease(published, version, is_semver_prerelease),
    }


def fetch_npm(http: Http, name: str) -> dict[str, Any]:
    data = http.get_json(f"https://registry.npmjs.org/{urllib.parse.quote(name, safe='@')}")
    times = data.get("time") or {}
    # "time" also lists unpublished versions and the "created"/"modified" keys; "versions" is what exists.
    published = {v: t for v in data.get("versions") or {} if (t := parse_time(times.get(v)))}
    version = (data.get("dist-tags") or {}).get("latest")
    return {
        "version": version,
        "date": day(published.get(version)) if version else None,
        "url": f"https://www.npmjs.com/package/{name}",
        "prerelease": newer_prerelease(published, version, is_semver_prerelease),
    }


PACKAGE_FETCHERS: dict[str, Callable[[Http, str], dict[str, Any]]] = {
    "pypi": fetch_pypi,
    "crates": fetch_crate,
    "npm": fetch_npm,
}


# ---------------------------------------------------------------------------------------------- snapshot


def refresh_project(project: dict[str, Any], old: dict[str, Any] | None, http: Http,
                    use_github: bool) -> dict[str, Any]:
    """A fresh snapshot entry (without its timestamp) for one project."""
    old = old or {}
    entry: dict[str, Any] = {"github": None, "packages": {}, "errors": []}
    repo = github_repo(project.get("repository"))
    if repo and use_github:
        entry["github"], errors = fetch_github(http, *repo, old.get("github"))
        entry["errors"] += errors
    elif repo:
        entry["github"] = old.get("github")
        entry["errors"].append("GitHub: not refreshed, neither GITHUB_TOKEN nor GH_TOKEN is set")
    for package in project.get("packages") or []:
        registry, name = package.get("registry"), str(package.get("name") or "")
        if registry not in PACKAGE_FETCHERS or not name:
            continue  # julia, cran, conda-forge, …: the build falls back to the project's `manual` block
        key = f"{registry}:{name}"
        try:
            entry["packages"][key] = PACKAGE_FETCHERS[registry](http, name)
        except FETCH_ERRORS as err:
            entry["packages"][key] = (old.get("packages") or {}).get(key)
            entry["errors"].append(f"{REGISTRY_LABELS[registry]} {name}: {describe_error(err)}")
    return entry


def refresh(previous: dict[str, Any], projects: list[dict[str, Any]], selected: list[str], http: Http,
            now: datetime, use_github: bool) -> dict[str, Any]:
    """The new snapshot: selected projects fetched again, others kept, entries of deleted projects dropped."""
    stamp = timestamp(now)
    old_entries = previous.get("projects") or {}
    entries = {}
    for project in projects:
        pid = project["id"]
        if pid in selected:
            entry = refresh_project(project, old_entries.get(pid), http, use_github)
            entry["fetched"] = stamp
            log(f"{pid}: {summarize(entry)}")
            entries[pid] = entry
        elif pid in old_entries:
            entries[pid] = old_entries[pid]
    return {"generated": stamp, "projects": entries}


def summarize(entry: dict[str, Any]) -> str:
    """One log line per project, e.g. "GitHub owner/repo (3 stars, last commit 2026-09-25); PyPI x 0.2.2 (…)"."""
    parts = []
    github = entry.get("github")
    if github:
        parts.append(f"GitHub {github['full_name']} ({github['stars']} stars, last commit {github['last_commit']})")
    for key, package in entry["packages"].items():
        registry, name = key.split(":", 1)
        if package:
            parts.append(f"{REGISTRY_LABELS[registry]} {name} {package['version']} ({package['date']})")
    parts += [f"error: {error}" for error in entry["errors"]]
    return "; ".join(parts) or "nothing to fetch"


def snapshot_content(snapshot: dict[str, Any]) -> dict[str, Any]:
    """The snapshot without its timestamps ("generated" and each "fetched")."""
    return {pid: {key: value for key, value in entry.items() if key != "fetched"}
            for pid, entry in (snapshot.get("projects") or {}).items()}


def write_snapshot(path: Path, snapshot: dict[str, Any], previous: dict[str, Any]) -> bool:
    """Write the snapshot unless only its timestamps changed; True when the file was written."""
    if path.exists() and snapshot_content(snapshot) == snapshot_content(previous):
        return False
    path.write_text(dump_json(snapshot), encoding="utf-8")
    return True


# ---------------------------------------------------------------------------------------------- report


def _was(old: Any) -> str:
    return f", previously {md_text(old)}" if old else ""


def compare(old: dict[str, Any], new: dict[str, Any]) -> Iterator[tuple[str, str]]:
    """(section, Markdown text) for every reportable difference between two entries of one project."""
    old_gh, new_gh = old.get("github") or {}, new.get("github") or {}
    if old_gh and new_gh:
        old_release, new_release = old_gh.get("latest_release"), new_gh.get("latest_release")
        if (old_release or {}).get("tag") != (new_release or {}).get("tag"):
            if new_release:
                yield "Releases", (f"GitHub release [{md_text(new_release['tag'])}]({new_release['url']}) "
                                   f"({new_release['date']}){_was((old_release or {}).get('tag'))}")
            else:
                yield "Releases", f"no published GitHub release any more{_was(old_release['tag'])}"
        if new_gh.get("last_commit") and old_gh.get("last_commit") != new_gh.get("last_commit"):
            yield "Last commits", f"{old_gh.get('last_commit') or 'unknown'} → {new_gh['last_commit']}"
        if old_gh.get("archived") != new_gh.get("archived"):
            yield "Archived", "archived on GitHub" if new_gh.get("archived") else "no longer archived on GitHub"
        if old_gh.get("license") != new_gh.get("license"):
            yield "Licences", f"{old_gh.get('license') or 'none'} → {new_gh.get('license') or 'none'}"
        if old_gh.get("description") != new_gh.get("description"):
            yield "Descriptions", (f"“{md_text(old_gh.get('description'))}” → "
                                   f"“{md_text(new_gh.get('description'))}”")
    for key, new_package in (new.get("packages") or {}).items():
        old_package = (old.get("packages") or {}).get(key)
        if not old_package or not new_package:
            continue  # first fetch of this package, or it failed and nothing is known
        registry, name = key.split(":", 1)
        label = f"{REGISTRY_LABELS.get(registry, registry)} {md_text(name)}"
        if old_package.get("version") != new_package.get("version"):
            yield "Releases", (f"{label} [{md_text(new_package['version'])}]({new_package['url']}) "
                               f"({new_package['date']}){_was(old_package.get('version'))}")
        old_pre, new_pre = old_package.get("prerelease"), new_package.get("prerelease")
        if new_pre and (old_pre or {}).get("version") != new_pre.get("version"):
            yield "Releases", f"{label} pre-release {md_text(new_pre['version'])} ({new_pre['date']})"


def render_report(previous: dict[str, Any], current: dict[str, Any], projects: list[dict[str, Any]],
                  refreshed: list[str]) -> str:
    """Markdown report of the changes since the previous snapshot; a single line when there are none."""
    by_id = {project["id"]: project for project in projects}
    sections: dict[str, list[str]] = {name: [] for name in SECTIONS}
    old_entries = previous.get("projects") or {}
    for pid in refreshed:
        project, new = by_id[pid], current["projects"][pid]
        label = f"**{md_text(project.get('name') or pid)}** (`{pid}`)"
        if old_entries.get(pid):
            for section, text in compare(old_entries[pid], new):
                sections[section].append(f"- {label}: {text}")
        repo, github = github_repo(project.get("repository")), new.get("github")
        if repo and github and github["full_name"].lower() != "/".join(repo).lower():
            sections["Moved repositories"].append(
                f"- {label}: `{'/'.join(repo)}` is now [{github['full_name']}](https://github.com/{github['full_name']});"
                f" update `repository` in `data/projects/{pid}.yaml`")
        sections["Errors"] += [f"- {label}: {md_text(error, limit=500)}" for error in new["errors"]]

    lines = []
    for name, items in sections.items():
        if items:
            lines += [f"### {name}", "", *items, ""]
    if not lines:
        return f"No changes in repository or package metadata ({plural(len(refreshed), 'project')} refreshed).\n"
    return f"Metadata of {plural(len(refreshed), 'project')} refreshed.\n\n" + "\n".join(lines)


# ---------------------------------------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="example: python scripts/refresh.py --only metasona --dry-run")
    parser.add_argument("--only", action="append", default=[], metavar="ID",
                        help="refresh only this project (repeatable); the other entries are kept as they are")
    parser.add_argument("--report", type=Path, metavar="PATH",
                        help="write the Markdown change report to PATH (default: print it); it is a "
                             "single line when nothing changed")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the refreshed entries and the report; write no files")
    args = parser.parse_args(argv)

    projects = load_projects(DATA_DIR / "projects")
    ids = [project["id"] for project in projects]
    unknown = sorted(set(args.only) - set(ids))
    if unknown:
        parser.error(f"unknown project id: {', '.join(unknown)}")
    selected = [pid for pid in ids if not args.only or pid in args.only]

    path = DATA_DIR / "snapshot.json"
    previous = load_json(path)
    token = github_token()
    if token is None:
        log("Neither GITHUB_TOKEN nor GH_TOKEN is set: GitHub metadata is not refreshed.")
    snapshot = refresh(previous, projects, selected, Http(token), utc_now(), use_github=token is not None)
    report = render_report(previous, snapshot, projects, selected)

    if args.dry_run:
        print(dump_json({pid: snapshot["projects"][pid] for pid in selected}), end="")
        print(report, end="")
        return 0
    log(f"Wrote {path}" if write_snapshot(path, snapshot, previous) else f"No changes; {path} left untouched")
    write_report(report, args.report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
