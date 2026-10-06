#!/usr/bin/env python3
"""Find repositories and packages that may belong in the list but are not in it yet.

Searches GitHub repositories (needs GITHUB_TOKEN or GH_TOKEN), crates.io and npm with the queries below and
leaves out everything that is already listed (data/projects/*.yaml), was reviewed and rejected
(data/ignored.yaml), forks, and anything without a push or release in the last three years. The rest is
written as a Markdown report, grouped by where it was found and ordered by relevance: number of matching
queries, then most recent activity. PyPI has no search API and is not searched.

To stop a candidate from being reported again, add its URL to data/ignored.yaml with a reason.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.parse
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from _common import (DATA_DIR, FETCH_ERRORS, GITHUB_API, Http, describe_error, github_token, load_projects,
                     load_yaml, log, md_text, normalize_url, parse_time, plural, utc_now, write_report)

# What to search for. GitHub queries use GitHub's search syntax (quotes for phrases, qualifiers such as
# topic:) and match repository names, descriptions and topics.
GITHUB_QUERIES = [
    "psychoacoustic",
    "psychoacoustics",
    '"psychoacoustic metrics"',
    '"sound quality metrics"',
    '"ISO 532"',
    '"ISO 532-1"',
    '"ECMA-418"',
    '"ECMA 418"',
    '"zwicker loudness"',
    '"loudness zwicker"',
    '"sottek hearing model"',
    '"roughness asper"',
    '"fluctuation strength"',
    '"DIN 45692"',
    '"sharpness acum"',
    '"tone-to-noise ratio"',
    '"prominence ratio"',
    '"tonality aures"',
    '"psychoacoustic annoyance"',
    "EPNL",
    '"perceived noise level"',
    '"aural detectability"',
    '"ISO/TS 20065"',
    '"DIN 45681"',
    '"time-varying loudness"',
    '"Moore Glasberg loudness"',
    "topic:psychoacoustics",
    "topic:psychoacoustic",
]

# crates.io and npm search is fuzzy, so a result only counts when every word of the query occurs in its
# name, description or keywords.
REGISTRY_QUERIES = [
    "psychoacoustic",
    "psychoacoustics",
    "zwicker",
    "ecma-418",
    "iso 532",
    "sound quality metrics",
]

MAX_ENTRIES = 60  # candidates listed in the report
ACTIVE_WITHIN = timedelta(days=3 * 365)  # older candidates are left out
GITHUB_SEARCH_INTERVAL = 2.5  # seconds between searches; GitHub allows 30 searches per minute with a token
CRATES_INTERVAL = 1.0  # crates.io asks crawlers for at most one request per second

# registry -> (label in the report, language, package page)
REGISTRIES = {
    "crates": ("crates.io", "Rust", "https://crates.io/crates/{name}"),
    "npm": ("npm", "JavaScript", "https://www.npmjs.com/package/{name}"),
}
GROUPS = ("GitHub", "crates.io", "npm")


def github_search_url(query: str) -> str:
    params = {"q": query, "sort": "updated", "order": "desc", "per_page": 50}
    return f"{GITHUB_API}/search/repositories?{urllib.parse.urlencode(params)}"


def crates_search_url(query: str) -> str:
    return f"https://crates.io/api/v1/crates?{urllib.parse.urlencode({'q': query, 'per_page': 50})}"


def npm_search_url(query: str) -> str:
    return f"https://registry.npmjs.org/-/v1/search?{urllib.parse.urlencode({'text': query, 'size': 50})}"


def package_key(registry: str, name: str) -> str:
    """crates.io treats "-" and "_" in crate names as the same; npm names are lower case."""
    name = name.lower()
    return f"{registry}:{name.replace('_', '-') if registry == 'crates' else name}"


@dataclass
class Exclusions:
    """What is not reported: listed projects and their packages, and reviewed candidates."""

    urls: set[str]  # normalised URLs
    packages: set[str]  # package_key() of listed packages

    @classmethod
    def from_data(cls, projects: list[dict[str, Any]], ignored: list[dict[str, Any]]) -> Exclusions:
        urls, packages = set(), set()
        for project in projects:
            urls.update(normalize_url(str(project[key])) for key in ("repository", "homepage") if project.get(key))
            for package in project.get("packages") or []:
                if package.get("url"):
                    urls.add(normalize_url(str(package["url"])))
                if package.get("registry") and package.get("name"):
                    packages.add(package_key(str(package["registry"]), str(package["name"])))
        urls.update(normalize_url(str(entry["url"])) for entry in ignored
                    if isinstance(entry, dict) and entry.get("url"))
        return cls(urls, packages)

    def excludes(self, *urls: str | None, package: str | None = None) -> bool:
        return package in self.packages or any(url and normalize_url(url) in self.urls for url in urls)


@dataclass
class Candidate:
    source: str  # group in the report: "GitHub", "crates.io" or "npm"
    name: str
    url: str
    description: str | None
    language: str | None
    updated: datetime  # last push (GitHub) or last publication (registries)
    stars: int | None = None
    archived: bool = False
    repository: str | None = None  # source repository of a package
    packages: list[tuple[str, str, str]] = field(default_factory=list)  # (registry label, name, page)
    queries: list[tuple[str, str]] = field(default_factory=list)  # (source, query) that found it


def mentions(query: str, *texts: Any) -> bool:
    """True when every word of the query occurs in the texts (strings or lists of strings), ignoring case."""
    words: list[str] = []
    for text in texts:
        words += [str(item) for item in text] if isinstance(text, list) else [str(text or "")]
    haystack = " ".join(words).lower()
    return all(word in haystack for word in query.lower().split())


class Search:
    """Runs the searches and collects candidates, merged by repository."""

    def __init__(self, http: Http, exclusions: Exclusions, cutoff: datetime) -> None:
        self.http = http
        self.exclusions = exclusions
        self.cutoff = cutoff
        self.found: dict[str, Candidate] = {}  # by normalised repository or package URL
        self.errors: list[str] = []
        self.searched: dict[str, int] = {}  # number of queries run per source

    def github(self, queries: list[str]) -> None:
        for item, query in self._run("GitHub", queries, github_search_url, lambda data: data["items"],
                                     GITHUB_SEARCH_INTERVAL):
            pushed = parse_time(item.get("pushed_at"))
            url = item.get("html_url")
            if not url or item.get("fork") or pushed is None or pushed < self.cutoff or self.exclusions.excludes(url):
                continue
            self._add(Candidate(source="GitHub", name=item.get("full_name") or url, url=url,
                                description=item.get("description"), language=item.get("language"),
                                updated=pushed, stars=item.get("stargazers_count"),
                                archived=bool(item.get("archived"))), ("GitHub", query))

    def crates(self, queries: list[str]) -> None:
        for item, query in self._run("crates.io", queries, crates_search_url, lambda data: data["crates"],
                                     CRATES_INTERVAL):
            self._add_package("crates", query, item.get("name"), item.get("description"), item.get("keywords"),
                              parse_time(item.get("updated_at")), item.get("repository"))

    def npm(self, queries: list[str]) -> None:
        for item, query in self._run("npm", queries, npm_search_url, lambda data: data["objects"], 0):
            package = item.get("package") or {}
            self._add_package("npm", query, package.get("name"), package.get("description"), package.get("keywords"),
                              parse_time(package.get("date")), (package.get("links") or {}).get("repository"))

    def _run(self, source: str, queries: list[str], url_for: Callable[[str], str],
             items_of: Callable[[Any], list[dict[str, Any]]], interval: float) -> Iterable[tuple[dict, str]]:
        """(result item, query) for every result of every query; failed searches are recorded as errors."""
        for number, query in enumerate(queries):
            if number:
                time.sleep(interval)
            self.searched[source] = number + 1
            try:
                items = items_of(self.http.get_json(url_for(query)))
            except FETCH_ERRORS as err:
                self.errors.append(f"{source} search `{query}`: {md_text(describe_error(err), limit=500)}")
                continue
            log(f"{source} `{query}`: {len(items)} results")
            for item in items:
                if isinstance(item, dict):
                    yield item, query

    def _add_package(self, registry: str, query: str, name: Any, description: Any, keywords: Any,
                     updated: datetime | None, repository: Any) -> None:
        label, language, page_template = REGISTRIES[registry]
        if not isinstance(name, str) or not name or not mentions(query, name, description, keywords or []):
            return
        if updated is None or updated < self.cutoff:
            return
        page = page_template.format(name=name)
        repository = repository if isinstance(repository, str) and repository else None
        if self.exclusions.excludes(page, repository, package=package_key(registry, name)):
            return
        self._add(Candidate(source=label, name=name, url=page, description=description, language=language,
                            updated=updated, repository=repository, packages=[(label, name, page)]), (label, query))

    def _add(self, candidate: Candidate, query: tuple[str, str]) -> None:
        """Record a result; results for the same repository (a GitHub repository and its packages, or several
        packages from one repository) become one candidate."""
        key = normalize_url(candidate.repository or candidate.url)
        existing = self.found.setdefault(key, candidate)
        if existing is not candidate:
            existing.packages += [package for package in candidate.packages if package not in existing.packages]
            if existing.source != "GitHub":
                existing.updated = max(existing.updated, candidate.updated)
        if query not in existing.queries:
            existing.queries.append(query)


def ranked(candidates: Iterable[Candidate]) -> list[Candidate]:
    """Most matching queries first, then most recent activity, then by name."""
    by_name = sorted(candidates, key=lambda candidate: candidate.name.lower())
    return sorted(by_name, key=lambda candidate: (len(candidate.queries), candidate.updated), reverse=True)


def render_candidate(candidate: Candidate) -> str:
    facts = [candidate.language] if candidate.language else []
    if candidate.stars is not None:
        facts.append(f"★ {candidate.stars}")
    activity = "last push" if candidate.source == "GitHub" else "updated"
    facts.append(f"{activity} {candidate.updated.date().isoformat()}")
    if candidate.archived:
        facts.append("archived")
    if candidate.repository and candidate.source != "GitHub":
        # npm and crates.io give git remotes such as git+https://github.com/owner/repo.git
        repository = re.sub(r"^git\+|\.git$", "", candidate.repository)
        facts.append(f"[repository]({repository})" if re.match(r"https?://", repository) else md_text(repository))
    packages = [f"[{label} {md_text(name)}]({page})" for label, name, page in candidate.packages]
    if packages and candidate.source == "GitHub":
        facts.append("packages: " + ", ".join(packages))
    elif len(packages) > 1:
        facts.append("also " + ", ".join(packages[1:]))
    queries = ", ".join(f"`{query}`" if source == "GitHub" else f"`{query}` ({source})"
                        for source, query in candidate.queries)
    description = md_text(candidate.description, limit=200) or "No description"
    if description[-1] not in ".!?…":
        description += "."
    return (f"- [{md_text(candidate.name)}]({candidate.url}) ({', '.join(facts)}): {description} "
            f"Matched {queries}.")


def join_words(items: list[str]) -> str:
    """'a', 'a and b', 'a, b and c'."""
    return f"{', '.join(items[:-1])} and {items[-1]}" if len(items) > 1 else "".join(items)


def render_report(search: Search, cutoff: datetime, github_skipped: bool) -> str:
    """Markdown report; a single line when there is nothing to review."""
    counts = join_words([f"{count} {source}" for source, count in search.searched.items()]) or "no"
    searched = f"{counts} {'query' if sum(search.searched.values()) == 1 else 'queries'}"
    if github_skipped:
        searched += "; GitHub was not searched because neither GITHUB_TOKEN nor GH_TOKEN is set"
    candidates = ranked(search.found.values())
    if not candidates and not search.errors:
        return f"No new candidates (searched {searched}).\n"

    shown = candidates[:MAX_ENTRIES]
    found = f"Found {plural(len(candidates), 'new candidate')}" if candidates else "No new candidates found"
    if len(candidates) > len(shown):
        found += f"; the {len(shown)} most relevant are listed"
    lines = [f"{found}. Searched {searched}. Not listed: listed projects, entries of `data/ignored.yaml`, forks, "
             f"and anything without activity since {cutoff.date().isoformat()}. Add reviewed candidates that do "
             f"not belong in the list to `data/ignored.yaml`.", ""]
    for group in GROUPS:
        members = [candidate for candidate in shown if candidate.source == group]
        if members:
            lines += [f"### {group} ({len(members)})", "", *map(render_candidate, members), ""]
    if search.errors:
        lines += ["### Errors", "", *[f"- {error}" for error in search.errors], ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--report", type=Path, metavar="PATH",
                        help="write the Markdown report to PATH (default: print it); it is a single line "
                             "when there is nothing to report")
    parser.add_argument("--max-queries", type=int, metavar="N",
                        help="run only the first N queries of each list (for testing)")
    args = parser.parse_args(argv)
    if args.max_queries is not None and args.max_queries < 0:
        parser.error("--max-queries must not be negative")

    projects = load_projects(DATA_DIR / "projects")
    ignored_path = DATA_DIR / "ignored.yaml"
    ignored = (load_yaml(ignored_path) or []) if ignored_path.exists() else []
    token = github_token()
    cutoff = utc_now() - ACTIVE_WITHIN
    search = Search(Http(token), Exclusions.from_data(projects, ignored), cutoff)

    limit = args.max_queries
    if token:
        search.github(GITHUB_QUERIES[:limit])
    else:
        log("Neither GITHUB_TOKEN nor GH_TOKEN is set: GitHub is not searched.")
    search.crates(REGISTRY_QUERIES[:limit])
    search.npm(REGISTRY_QUERIES[:limit])

    write_report(render_report(search, cutoff, github_skipped=token is None), args.report)
    print(plural(len(search.found), "new candidate"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
