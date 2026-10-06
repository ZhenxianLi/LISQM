"""Tests for scripts/refresh.py, using recorded and mock HTTP responses (no network access)."""

from __future__ import annotations

import copy
import io
import json
import os
import sys
import tempfile
import time
import unittest
import urllib.request
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
sys.path[:0] = [str(TESTS.parent / "scripts"), str(TESTS / "fixtures")]

import _common  # noqa: E402
import refresh  # noqa: E402
from fakehttp import FakeWeb, Reply, fixture_bytes, fixture_json, json_reply  # noqa: E402

API = "https://api.github.com/repos/huaaudio/metasona"
COMMITS = f"{API}/commits?sha=main&per_page=1"
RELEASE = f"{API}/releases/latest"
PYPI = "https://pypi.org/pypi/metasona/json"
NOW = datetime(2026, 10, 6, 6, 0, tzinfo=timezone.utc)

PROJECT = {"id": "metasona", "name": "MetaSona", "repository": "https://github.com/huaaudio/metasona",
           "packages": [{"registry": "pypi", "name": "metasona"}]}

EXPECTED_ENTRY = {
    "github": {
        "full_name": "huaaudio/metasona", "stars": 3, "forks": 0, "archived": False, "default_branch": "main",
        "pushed_at": "2026-09-25T15:50:48Z", "last_commit": "2026-09-25", "license": "GPL-3.0",
        "description": "Source-informed C and Python implementations of psychoacoustic metrics",
        "topics": ["acoustics", "loudness", "psychoacoustics"], "open_issues": 0,
        "latest_release": {"tag": "v0.2.2", "date": "2026-09-25",
                           "url": "https://github.com/huaaudio/metasona/releases/tag/v0.2.2"},
    },
    "packages": {"pypi:metasona": {"version": "0.2.2", "date": "2026-09-25",
                                   "url": "https://pypi.org/project/metasona/", "prerelease": None}},
    "errors": [],
}


def metasona_routes(overrides: dict | None = None) -> dict:
    routes = {API: Reply(body=fixture_bytes("refresh/github_repo_metasona.json")),
              COMMITS: Reply(body=fixture_bytes("refresh/github_commits_metasona.json")),
              RELEASE: Reply(body=fixture_bytes("refresh/github_release_metasona.json")),
              PYPI: Reply(body=fixture_bytes("refresh/pypi_metasona.json"))}
    routes.update(overrides or {})
    return routes


class FakeWebCase(unittest.TestCase):
    """Serves canned responses instead of the network, records sleeps instead of waiting, hides the log."""

    def setUp(self) -> None:
        for name, patcher in (("sleep", mock.patch("time.sleep")),
                              ("stderr", mock.patch("sys.stderr", new_callable=io.StringIO))):
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)

    def serve(self, routes: dict) -> FakeWeb:
        web = FakeWeb(routes)
        patcher = mock.patch.object(_common, "_urlopen", web)
        patcher.start()
        self.addCleanup(patcher.stop)
        return web

    def refresh_metasona(self, old: dict | None = None, token: str | None = "secret") -> dict:
        return refresh.refresh_project(PROJECT, old, _common.Http(token), use_github=token is not None)


class GitHubTest(FakeWebCase):
    def test_entry_from_github_and_pypi(self) -> None:
        self.serve(metasona_routes())
        # PyPI: 0.2.1 has only yanked files and is ignored; 0.2.2 is the latest version.
        self.assertEqual(self.refresh_metasona(), EXPECTED_ENTRY)

    def test_token_and_api_headers_only_go_to_github(self) -> None:
        web = self.serve(metasona_routes())
        self.refresh_metasona()
        self.assertEqual(len(web.requests), 4)
        for request in web.requests:
            headers = {name.lower(): value for name, value in request.header_items()}
            self.assertTrue(headers["user-agent"].startswith("OpenSQMI-bot"))
            if request.host == "api.github.com":
                self.assertEqual(headers["authorization"], "Bearer secret")
                self.assertEqual(headers["accept"], "application/vnd.github+json")
                self.assertEqual(headers["x-github-api-version"], "2022-11-28")
            else:
                self.assertNotIn("authorization", headers)

    def test_renamed_repository_is_followed_and_reported(self) -> None:
        moved = "https://api.github.com/repos/metasona-org/metasona"
        repo = fixture_json("refresh/github_repo_metasona.json") | {"full_name": "metasona-org/metasona"}
        routes = metasona_routes({API: json_reply(repo)})  # what urllib returns after following GitHub's 301
        del routes[COMMITS], routes[RELEASE]
        commits, release = (Reply(body=fixture_bytes(f"refresh/github_{name}_metasona.json"))
                            for name in ("commits", "release"))
        routes[f"{moved}/commits?sha=main&per_page=1"], routes[f"{moved}/releases/latest"] = commits, release
        self.serve(routes)
        snapshot = refresh.refresh({}, [PROJECT], ["metasona"], _common.Http("t"), NOW, use_github=True)
        self.assertEqual(snapshot["projects"]["metasona"]["github"]["full_name"], "metasona-org/metasona")
        report = refresh.render_report({}, snapshot, [PROJECT], ["metasona"])
        self.assertIn("### Moved repositories", report)
        self.assertIn("`huaaudio/metasona` is now [metasona-org/metasona](https://github.com/metasona-org/metasona)",
                      report)

    def test_failed_fetches_keep_previous_values(self) -> None:
        self.serve(metasona_routes({API: json_reply({"message": "Not Found"}, 404),
                                    PYPI: [Reply(503), Reply(502), Reply(503)]}))
        entry = self.refresh_metasona(old=copy.deepcopy(EXPECTED_ENTRY))
        self.assertEqual(entry["github"], EXPECTED_ENTRY["github"])
        self.assertEqual(entry["packages"], EXPECTED_ENTRY["packages"])
        self.assertEqual(entry["errors"], [
            f"GitHub: HTTP 404 Not Found ({API})",
            f"PyPI metasona: HTTP 503 Service Unavailable ({PYPI})",
        ])
        self.assertEqual([call.args[0] for call in self.sleep.call_args_list], [2.0, 4.0])  # backoff, 3 tries

    def test_missing_release_and_empty_repository_are_null(self) -> None:
        self.serve(metasona_routes({RELEASE: json_reply({"message": "Not Found"}, 404),
                                    COMMITS: json_reply({"message": "Git Repository is empty."}, 409)}))
        entry = self.refresh_metasona(old=copy.deepcopy(EXPECTED_ENTRY))
        self.assertIsNone(entry["github"]["latest_release"])
        self.assertIsNone(entry["github"]["last_commit"])
        self.assertEqual(entry["errors"], [])

    def test_secondary_rate_limit_waits_for_retry_after(self) -> None:
        limited = json_reply({"message": "You have exceeded a secondary rate limit."}, 403, {"Retry-After": "7"})
        self.serve(metasona_routes({API: [limited, Reply(body=fixture_bytes("refresh/github_repo_metasona.json"))]}))
        self.assertEqual(self.refresh_metasona(), EXPECTED_ENTRY)
        self.sleep.assert_called_once_with(7.0)

    def test_exhausted_rate_limit_is_not_waited_for(self) -> None:
        reset = str(int(time.time()) + 3600)
        limited = json_reply({"message": "API rate limit exceeded"}, 403,
                             {"x-ratelimit-remaining": "0", "x-ratelimit-reset": reset})
        web = self.serve(metasona_routes({API: limited}))
        entry = self.refresh_metasona()
        self.sleep.assert_not_called()
        self.assertEqual(web.urls.count(API), 1)
        self.assertIsNone(entry["github"])
        self.assertTrue(entry["errors"][0].startswith("GitHub: HTTP 403 API rate limit exceeded (rate limited for"))

    def test_without_token_github_is_not_fetched(self) -> None:
        web = self.serve(metasona_routes())
        old = copy.deepcopy(EXPECTED_ENTRY)
        entry = self.refresh_metasona(old=old, token=None)
        self.assertEqual(web.urls, [PYPI])
        self.assertEqual(entry["github"], old["github"])
        self.assertEqual(entry["errors"], ["GitHub: not refreshed, neither GITHUB_TOKEN nor GH_TOKEN is set"])

    def test_other_hosts_and_registries_are_skipped(self) -> None:
        web = self.serve({})
        project = {"id": "x", "repository": "https://gitlab.com/group/x",
                   "packages": [{"registry": "julia", "name": "X"}, {"registry": "cran", "name": "x"}]}
        entry = refresh.refresh_project(project, None, _common.Http("t"), use_github=True)
        self.assertEqual(entry, {"github": None, "packages": {}, "errors": []})
        self.assertEqual(web.urls, [])

    def test_redirects_drop_the_token_when_leaving_the_host(self) -> None:
        handler = _common._RedirectHandler()
        request = urllib.request.Request(API, headers={"Authorization": "Bearer t"})
        same_host = handler.redirect_request(request, None, 301, "Moved", {}, "https://api.github.com/repositories/1")
        other_host = handler.redirect_request(request, None, 302, "Found", {}, "https://objects.example.com/x")
        self.assertEqual(same_host.get_header("Authorization"), "Bearer t")
        self.assertIsNone(other_host.get_header("Authorization"))


class RegistryTest(FakeWebCase):
    def fetch_pypi(self, data: dict) -> dict:
        self.serve({PYPI: json_reply(data)})
        return refresh.fetch_pypi(_common.Http(), "metasona")

    def test_pypi_newer_prerelease(self) -> None:
        data = fixture_json("refresh/pypi_metasona.json")
        data["releases"]["0.3.0rc1"] = [{"upload_time_iso_8601": "2026-10-02T09:00:00.000000Z", "yanked": False}]
        data["releases"]["0.2.0b1"] = [{"upload_time_iso_8601": "2026-09-16T05:00:00.000000Z", "yanked": False}]
        result = self.fetch_pypi(data)
        self.assertEqual((result["version"], result["date"]), ("0.2.2", "2026-09-25"))
        self.assertEqual(result["prerelease"], {"version": "0.3.0rc1", "date": "2026-10-02"})

    def test_pypi_yanked_latest_version_falls_back_to_previous_release(self) -> None:
        data = fixture_json("refresh/pypi_metasona.json")
        for file in data["releases"]["0.2.2"]:
            file["yanked"] = True
        result = self.fetch_pypi(data)
        self.assertEqual((result["version"], result["date"]), ("0.2.0", "2026-09-16"))  # 0.2.1 is yanked as well

    def test_crate(self) -> None:
        self.serve({"https://crates.io/api/v1/crates/zimtohrli-sys":
                    Reply(body=fixture_bytes("refresh/crates_zimtohrli-sys.json"))})
        self.assertEqual(refresh.fetch_crate(_common.Http(), "zimtohrli-sys"),
                         {"version": "0.2.0", "date": "2025-12-26", "url": "https://crates.io/crates/zimtohrli-sys",
                          "prerelease": None})

    def test_npm_scoped_package_with_newer_prerelease(self) -> None:
        data = fixture_json("refresh/npm_audio-auditory.json")
        data["versions"]["1.1.0-beta.1"] = {"name": "@audio/auditory", "version": "1.1.0-beta.1"}
        data["time"]["1.1.0-beta.1"] = "2026-08-01T10:00:00.000Z"
        data["time"]["2.0.0-alpha.1"] = "2026-09-01T10:00:00.000Z"  # unpublished: listed in "time" only
        self.serve({"https://registry.npmjs.org/@audio%2Fauditory": json_reply(data)})
        self.assertEqual(refresh.fetch_npm(_common.Http(), "@audio/auditory"),
                         {"version": "1.0.2", "date": "2026-07-11", "url": "https://www.npmjs.com/package/@audio/auditory",
                          "prerelease": {"version": "1.1.0-beta.1", "date": "2026-08-01"}})


class SnapshotTest(FakeWebCase):
    def test_unselected_projects_are_kept_and_deleted_ones_dropped(self) -> None:
        self.serve({})
        previous = {"generated": "2026-09-29T05:17:00Z",
                    "projects": {"metasona": EXPECTED_ENTRY | {"fetched": "2026-09-29T05:17:00Z"},
                                 "deleted": {"fetched": "2026-09-29T05:17:00Z", "github": None, "packages": {},
                                             "errors": []}}}
        projects = [PROJECT, {"id": "other", "repository": "https://example.org/other"}]
        snapshot = refresh.refresh(previous, projects, ["other"], _common.Http("t"), NOW, use_github=True)
        self.assertEqual(snapshot, {
            "generated": "2026-10-06T06:00:00Z",
            "projects": {"metasona": previous["projects"]["metasona"],
                         "other": {"fetched": "2026-10-06T06:00:00Z", "github": None, "packages": {}, "errors": []}},
        })

    def test_file_is_only_written_when_more_than_timestamps_change(self) -> None:
        first = {"generated": "2026-09-29T05:17:00Z",
                 "projects": {"x": {"fetched": "2026-09-29T05:17:00Z", "github": None, "packages": {}, "errors": []}}}
        later = copy.deepcopy(first)
        later["generated"] = later["projects"]["x"]["fetched"] = "2026-10-06T05:17:00Z"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "snapshot.json"
            self.assertTrue(refresh.write_snapshot(path, first, {}))
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text, json.dumps(first, indent=2, sort_keys=True) + "\n")
            self.assertFalse(refresh.write_snapshot(path, later, first))
            self.assertEqual(path.read_text(encoding="utf-8"), text)
            later["projects"]["x"]["errors"] = ["GitHub: HTTP 500"]
            self.assertTrue(refresh.write_snapshot(path, later, first))


class ReportTest(unittest.TestCase):
    def test_changes_are_reported(self) -> None:
        old = copy.deepcopy(EXPECTED_ENTRY)
        old["github"].update(last_commit="2026-09-01", license="MIT", description="Old text",
                             latest_release={"tag": "v0.2.1", "date": "2026-09-20", "url": "https://example.org/r"})
        old["packages"]["pypi:metasona"].update(version="0.2.1", date="2026-09-20")
        new = copy.deepcopy(EXPECTED_ENTRY)
        new["github"].update(archived=True, description="New text by @someone, see #3")
        new["packages"]["pypi:metasona"]["prerelease"] = {"version": "0.3.0rc1", "date": "2026-10-02"}
        new["errors"] = ["PyPI metasona: HTTP 500 Internal Server Error (https://pypi.org/pypi/metasona/json)"]
        report = refresh.render_report({"projects": {"metasona": old}}, {"projects": {"metasona": new}}, [PROJECT],
                                       ["metasona"])
        label = "- **MetaSona** (`metasona`): "
        for expected in (
            "### Releases",
            label + "GitHub release [v0.2.2](https://github.com/huaaudio/metasona/releases/tag/v0.2.2) "
                    "(2026-09-25), previously v0.2.1",
            label + "PyPI metasona [0.2.2](https://pypi.org/project/metasona/) (2026-09-25), previously 0.2.1",
            label + "PyPI metasona pre-release 0.3.0rc1 (2026-10-02)",
            "### Last commits\n\n" + label + "2026-09-01 → 2026-09-25",
            "### Archived\n\n" + label + "archived on GitHub",
            "### Licences\n\n" + label + "MIT → GPL-3.0",
            "### Descriptions\n\n" + label + "“Old text” → “New text by @\u200bsomeone, see #\u200b3”",
            "### Errors\n\n" + label + "PyPI metasona: HTTP 500 Internal Server Error "
                                       "(https://pypi.org/pypi/metasona/json)",
        ):
            self.assertIn(expected, report)

    def test_no_changes_is_a_single_line(self) -> None:
        previous = {"projects": {"metasona": EXPECTED_ENTRY}}
        report = refresh.render_report(previous, previous, [PROJECT], ["metasona"])
        self.assertEqual(report, "No changes in repository or package metadata (1 project refreshed).\n")


class MainTest(FakeWebCase):
    def setUp(self) -> None:
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.data = Path(tmp.name)
        (self.data / "projects").mkdir()
        (self.data / "projects" / "metasona.yaml").write_text(
            "id: metasona\nname: MetaSona\nrepository: https://github.com/huaaudio/metasona\n"
            "packages:\n  - registry: pypi\n    name: metasona\n", encoding="utf-8")
        for patcher in (mock.patch.object(refresh, "DATA_DIR", self.data),
                        mock.patch.dict(os.environ, {"GITHUB_TOKEN": "secret"})):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.serve(metasona_routes())

    def test_dry_run_prints_and_writes_nothing(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(refresh.main(["--only", "metasona", "--dry-run"]), 0)
        self.assertIn('"pypi:metasona"', output.getvalue())
        self.assertFalse((self.data / "snapshot.json").exists())

    def test_second_run_without_changes_leaves_the_snapshot_untouched(self) -> None:
        report = self.data / "refresh.md"
        self.assertEqual(refresh.main(["--report", str(report)]), 0)
        snapshot = (self.data / "snapshot.json").read_text(encoding="utf-8")
        self.assertEqual(json.loads(snapshot)["projects"]["metasona"]["github"], EXPECTED_ENTRY["github"])
        with mock.patch.object(refresh, "utc_now", return_value=datetime(2030, 1, 1, tzinfo=timezone.utc)):
            self.assertEqual(refresh.main(["--report", str(report)]), 0)
        self.assertEqual((self.data / "snapshot.json").read_text(encoding="utf-8"), snapshot)
        self.assertEqual(report.read_text(encoding="utf-8"),
                         "No changes in repository or package metadata (1 project refreshed).\n")

    def test_unknown_project_id_is_a_usage_error(self) -> None:
        with self.assertRaises(SystemExit) as raised:
            refresh.main(["--only", "nonexistent"])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
