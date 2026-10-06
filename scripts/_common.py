"""Helpers shared by refresh.py, discover.py and watch_standards.py.

Standard library plus PyYAML only: repository paths, YAML/JSON files, a small HTTP client (GitHub
authentication, retries, rate limits), timestamps, URL normalisation and escaping of untrusted text for the
Markdown reports.
"""

from __future__ import annotations

import http.client
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
GITHUB_API = "https://api.github.com"


def log(message: str) -> None:
    """Progress messages go to stderr, so that stdout only carries reports and --dry-run output."""
    print(message, file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------------------------- files


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_projects(projects_dir: Path) -> list[dict[str, Any]]:
    """Every data/projects/*.yaml file, sorted by id (which defaults to the file name)."""
    projects = []
    for path in sorted(projects_dir.glob("*.yaml")):
        project = load_yaml(path)
        if not isinstance(project, dict):
            raise SystemExit(f"{path}: expected a mapping")
        project.setdefault("id", path.stem)
        projects.append(project)
    return sorted(projects, key=lambda project: str(project["id"]))


def load_json(path: Path) -> dict[str, Any]:
    """The JSON object stored in path, or {} when the file does not exist yet."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(data: Any) -> str:
    """Deterministic JSON: sorted keys, two-space indent, UTF-8 text, trailing newline."""
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_report(text: str, path: Path | None) -> None:
    """Write a Markdown report to path, or print it when no path was given."""
    if path is None:
        print(text, end="")
    else:
        path.write_text(text, encoding="utf-8")
        log(f"Report written to {path}")


# ---------------------------------------------------------------------------------------------- time


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def timestamp(moment: datetime) -> str:
    """UTC timestamp as written in the data files, e.g. 2026-10-06T06:00:00Z."""
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_time(text: Any) -> datetime | None:
    """An ISO 8601 timestamp as returned by GitHub, PyPI, crates.io or npm (UTC), or None if missing or invalid."""
    if not isinstance(text, str) or not text.strip():
        return None
    try:
        # fromisoformat() only accepts a trailing "Z" from Python 3.11 on.
        moment = datetime.fromisoformat(text.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def day(moment: datetime | None) -> str | None:
    """YYYY-MM-DD of a UTC timestamp, or None."""
    return moment.date().isoformat() if moment else None


# ---------------------------------------------------------------------------------------------- URLs and text


def normalize_url(url: str) -> str:
    """Canonical form for comparing URLs.

    Lower case, https, no "www.", user info, port, query, fragment, trailing slash or ".git". Git remote forms
    (git+https://…, git://…, ssh://git@…, git@host:owner/repo) become https URLs, and GitHub URLs are cut to
    the repository (https://github.com/owner/repo), so that a project kept in a subfolder of a repository
    still matches that repository.
    """
    text = url.strip().lower()
    text = re.sub(r"^git\+", "", text)
    text = re.sub(r"^git@([^:/]+):", r"https://\1/", text)
    if "://" not in text:
        text = "https://" + text
    parts = urllib.parse.urlsplit(text)
    host = (parts.hostname or "").removeprefix("www.")
    path = re.sub(r"(?:\.git)?/*$", "", parts.path)
    if host == "github.com":
        path = "/".join(path.split("/")[:3])
    return f"https://{host}{path}"


def github_repo(url: Any) -> tuple[str, str] | None:
    """(owner, name) of a github.com repository URL, or None for any other host."""
    if not isinstance(url, str):
        return None
    parts = urllib.parse.urlsplit(url.strip())
    if (parts.hostname or "").lower() not in ("github.com", "www.github.com"):
        return None
    segments = [segment for segment in parts.path.split("/") if segment]
    if len(segments) < 2:
        return None
    return segments[0], segments[1].removesuffix(".git")


def plural(count: int, noun: str) -> str:
    """'1 project', '2 projects'."""
    return f"{count} {noun if count == 1 else noun + 's'}"


_MARKDOWN_SPECIAL = re.compile(r"([\\`*_\[\]<>|])")
_URL = re.compile(r"https?://[^\s<>()\[\]]+")


def _md_escape(text: str) -> str:
    text = _MARKDOWN_SPECIAL.sub(r"\\\1", text)
    return text.replace("@", "@\u200b").replace("#", "#\u200b")


def md_text(text: Any, limit: int = 300) -> str:
    """Untrusted text (descriptions, titles, error messages) as one line of Markdown.

    Whitespace is collapsed, the text is shortened to `limit` characters, Markdown syntax is escaped, and
    @mentions and #references are broken with a zero-width space, so that the monthly review issue built
    from the reports neither notifies people nor links unrelated issues. URLs are kept as they are, so that
    they still work as links.
    """
    text = " ".join(str(text or "").split())
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    parts, position = [], 0
    for url in _URL.finditer(text):
        parts += [_md_escape(text[position:url.start()]), url.group(0)]
        position = url.end()
    return "".join(parts) + _md_escape(text[position:])


# ---------------------------------------------------------------------------------------------- HTTP


def github_token() -> str | None:
    """Token for the GitHub API from GITHUB_TOKEN or GH_TOKEN, or None when neither is set."""
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def user_agent() -> str:
    """Names the index and where to reach its maintainers, as the crates.io crawler policy asks."""
    try:
        repository = (load_yaml(DATA_DIR / "site.yaml") or {}).get("repository")
    except (OSError, yaml.YAMLError, AttributeError):
        repository = None
    name = "PsyMI-bot"
    return f"{name} (+{repository})" if repository else name


class FetchError(Exception):
    """Data could not be fetched; the message is short enough for a report."""


class HttpError(FetchError):
    """A request that still failed after all retries. `status` is None for network errors."""

    def __init__(self, url: str, status: int | None, detail: str) -> None:
        super().__init__(f"{detail} ({url})")
        self.url = url
        self.status = status


# Everything that can go wrong while fetching and reading a response: HTTP and network errors (URLError,
# timeouts and connection resets are OSErrors), and responses that do not have the expected shape.
FETCH_ERRORS = (FetchError, OSError, http.client.HTTPException, ValueError, KeyError, IndexError, TypeError,
                AttributeError)


def describe_error(err: Exception) -> str:
    """A one-line description of an exception from FETCH_ERRORS."""
    if isinstance(err, FetchError):
        return str(err)
    if isinstance(err, (OSError, http.client.HTTPException)):
        return f"network error: {err}"
    return f"unexpected response ({type(err).__name__}: {err})"


class _RedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follows redirects (GitHub answers 301 for renamed or transferred repositories) without forwarding the
    Authorization header to a different host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None and urllib.parse.urlsplit(newurl).hostname != urllib.parse.urlsplit(req.full_url).hostname:
            new.remove_header("Authorization")
        return new


_OPENER = urllib.request.build_opener(_RedirectHandler)


def _urlopen(request: urllib.request.Request, timeout: float) -> Any:
    """The only place where requests leave the process (the unit tests replace it)."""
    return _OPENER.open(request, timeout=timeout)


class Http:
    """GET requests with a User-Agent, GitHub authentication and retries.

    Network errors, 5xx responses and rate limits (403/429 with Retry-After, with x-ratelimit-remaining: 0, or
    a "secondary rate limit" message) are retried up to `tries` times in all, waiting as long as the server
    asks or with exponential backoff; a wait longer than `max_wait` seconds is not attempted. The token is
    only ever sent to api.github.com.
    """

    def __init__(self, token: str | None = None, *, timeout: float = 60.0, tries: int = 3,
                 max_wait: float = 120.0) -> None:
        self.token = token
        self.timeout = timeout
        self.tries = tries
        self.max_wait = max_wait
        self.user_agent = user_agent()

    def get(self, url: str) -> bytes:
        """The complete response body."""
        return self._request(url, stream=False)

    def get_json(self, url: str) -> Any:
        body = self.get(url)
        try:
            return json.loads(body)
        except ValueError as err:
            raise HttpError(url, None, f"invalid JSON: {err}") from None

    def open(self, url: str) -> Any:
        """An open response, to be used as a context manager and read line by line (large downloads).
        Only opening is retried; an error while reading propagates as OSError or HTTPException."""
        return self._request(url, stream=True)

    def _headers(self, url: str) -> dict[str, str]:
        headers = {"User-Agent": self.user_agent}
        if urllib.parse.urlsplit(url).hostname == "api.github.com":
            headers["Accept"] = "application/vnd.github+json"
            headers["X-GitHub-Api-Version"] = "2022-11-28"
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, url: str, stream: bool) -> Any:
        request = urllib.request.Request(url, headers=self._headers(url))
        for attempt in range(1, self.tries + 1):
            try:
                response = _urlopen(request, self.timeout)
                if stream:
                    return response
                with response:
                    return response.read()
            except urllib.error.HTTPError as err:
                body = _error_body(err)
                detail = f"HTTP {err.code} {_error_message(body) or err.reason}"
                wait = _retry_delay(err.code, err.headers, body, attempt)
                if wait is None or attempt == self.tries:
                    raise HttpError(url, err.code, detail) from None
                if wait > self.max_wait:
                    raise HttpError(url, err.code, f"{detail} (rate limited for {wait:.0f} s)") from None
            except (OSError, http.client.HTTPException) as err:
                if attempt == self.tries:
                    reason = getattr(err, "reason", None) or err
                    raise HttpError(url, None, f"network error: {reason}") from None
                wait = 2.0**attempt
            log(f"  retrying in {wait:.0f} s: {url}")
            time.sleep(wait)
        raise AssertionError("unreachable")


def _retry_delay(status: int, headers: Any, body: bytes, attempt: int) -> float | None:
    """Seconds to wait before retrying a failed request, or None when the error is not transient."""
    if status < 500 and status not in (403, 429):
        return None
    retry_after = (headers.get("Retry-After") or "").strip() if headers else ""
    if retry_after.isdigit():
        return float(retry_after)
    if status >= 500:
        return 2.0**attempt
    reset = (headers.get("x-ratelimit-reset") or "").strip() if headers else ""
    if headers and headers.get("x-ratelimit-remaining") == "0" and reset.isdigit():
        return max(int(reset) - time.time(), 0.0) + 1.0
    if status == 429 or b"secondary rate limit" in body.lower():
        return 60.0
    return None  # a plain 403: forbidden, not rate limited


def _error_body(err: urllib.error.HTTPError) -> bytes:
    try:
        return err.read() or b""
    except (OSError, http.client.HTTPException):
        return b""


def _error_message(body: bytes) -> str:
    """The message in a JSON error body (GitHub, PyPI, npm and crates.io formats), or ""."""
    try:
        data = json.loads(body)
    except ValueError:
        return ""
    if not isinstance(data, dict):
        return ""
    for key in ("message", "error"):
        if isinstance(data.get(key), str):
            return data[key][:200]
    errors = data.get("errors")
    if isinstance(errors, list) and errors and isinstance(errors[0], dict):
        return str(errors[0].get("detail") or "")[:200]
    return ""
