"""Tests for scripts/discover.py, using recorded and mock HTTP responses (no network access)."""

from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
sys.path[:0] = [str(TESTS.parent / "scripts"), str(TESTS / "fixtures")]

import _common  # noqa: E402
import discover  # noqa: E402
from fakehttp import FakeWeb, Reply, fixture_bytes, json_reply  # noqa: E402

NOW = datetime(2026, 10, 6, tzinfo=timezone.utc)
CUTOFF = NOW - discover.ACTIVE_WITHIN
PROJECTS = [{"id": "metasona", "repository": "https://github.com/huaaudio/metasona",
             "packages": [{"registry": "pypi", "name": "metasona"}]}]
IGNORED = [{"url": "https://www.github.com/example/ignored-meter/", "reason": "LUFS only."}]
ZWICKER = '"zwicker loudness"'


def routes() -> dict:
    def reply(name: str) -> Reply:
        return Reply(body=fixture_bytes(f"discover/{name}.json"))

    return {
        discover.github_search_url("psychoacoustic"): reply("github_search_psychoacoustic"),
        discover.github_search_url(ZWICKER): reply("github_search_zwicker"),
        discover.crates_search_url("psychoacoustic"): reply("crates_search_psychoacoustic"),
        discover.npm_search_url("psychoacoustic"): reply("npm_search_psychoacoustic"),
    }


class DiscoverCase(unittest.TestCase):
    def setUp(self) -> None:
        for name, patcher in (("sleep", mock.patch("time.sleep")),
                              ("stderr", mock.patch("sys.stderr", new_callable=io.StringIO))):
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)

    def serve(self, table: dict) -> FakeWeb:
        web = FakeWeb(table)
        patcher = mock.patch.object(_common, "_urlopen", web)
        patcher.start()
        self.addCleanup(patcher.stop)
        return web

    def search_all(self) -> discover.Search:
        self.serve(routes())
        search = discover.Search(_common.Http("t"), discover.Exclusions.from_data(PROJECTS, IGNORED), CUTOFF)
        search.github(["psychoacoustic", ZWICKER])
        search.crates(["psychoacoustic"])
        search.npm(["psychoacoustic"])
        return search


class UrlTest(unittest.TestCase):
    def test_normalize_url(self) -> None:
        cases = {
            "HTTP://www.GitHub.com/Owner/Repo.git/": "https://github.com/owner/repo",
            "git+https://github.com/audiojs/effect.git": "https://github.com/audiojs/effect",
            "git+ssh://git@github.com/advisr-io/excel4node.git": "https://github.com/advisr-io/excel4node",
            "git@github.com:Owner/Repo.git": "https://github.com/owner/repo",
            "https://github.com/org/repo/tree/main/packages/x": "https://github.com/org/repo",
            "https://gitlab.com/group/sub/repo/": "https://gitlab.com/group/sub/repo",
            "https://pypi.org/project/loudness/": "https://pypi.org/project/loudness",
            "https://example.org/page/?tab=1#readme": "https://example.org/page",
        }
        for url, expected in cases.items():
            self.assertEqual(_common.normalize_url(url), expected, url)


class SearchTest(DiscoverCase):
    def test_github_results_are_filtered_and_merged_by_repository(self) -> None:
        search = self.search_all()
        # Left out: huaaudio/metasona (listed), someone/mosqito (fork), old/zwicker-2019 (no push for 5 years),
        # Example/Ignored-Meter (in ignored.yaml), oxideav-mp2 (query word only in keywords), stale npm/crates.
        # Packages are keyed by their source repository.
        self.assertEqual(sorted(search.found), [
            "https://github.com/acoustics-lab/sqm-toolbox",
            "https://github.com/audiojs/effect",
            "https://github.com/newcomer/loudness-rs",
            "https://github.com/oxideav/oxideav-vorbis",
            "https://github.com/xnorpx/rust-zimtohrli",
        ])
        effect = search.found["https://github.com/audiojs/effect"]
        self.assertEqual(effect.source, "GitHub")
        self.assertEqual([name for _, name, _ in effect.packages], ["@audio/effect-exciter", "@audio/effect-subbass"])
        self.assertEqual(effect.queries, [("GitHub", "psychoacoustic"), ("npm", "psychoacoustic")])
        self.assertEqual(search.errors, [])
        # GitHub searches are spaced to stay under 30 per minute.
        self.sleep.assert_any_call(discover.GITHUB_SEARCH_INTERVAL)

    def test_indexed_and_ignored_packages_are_left_out(self) -> None:
        self.serve(routes())
        projects = [{"id": "z", "repository": "https://example.org/z",
                     "packages": [{"registry": "crates", "name": "zimtohrli_sys"}]}]
        ignored = [{"url": "https://github.com/OxideAV/oxideav-vorbis.git", "reason": "Codec."}]
        search = discover.Search(_common.Http(), discover.Exclusions.from_data(projects, ignored), CUTOFF)
        search.crates(["psychoacoustic"])
        self.assertEqual(search.found, {})

    def test_failed_search_is_reported(self) -> None:
        self.serve({discover.npm_search_url("psychoacoustic"): Reply(500)})
        search = discover.Search(_common.Http(), discover.Exclusions(set(), set()), CUTOFF)
        search.npm(["psychoacoustic"])
        report = discover.render_report(search, CUTOFF, github_skipped=False)
        self.assertIn("### Errors\n\n- npm search `psychoacoustic`: HTTP 500 Internal Server Error", report)


class ReportTest(DiscoverCase):
    def test_report_lists_most_relevant_first_grouped_by_source(self) -> None:
        report = discover.render_report(self.search_all(), CUTOFF, github_skipped=False)
        self.assertTrue(report.startswith("Found 5 new candidates. Searched 2 GitHub, 1 crates.io and 1 npm queries."))
        github = report.split("### GitHub (3)\n\n")[1].split("\n\n")[0].splitlines()
        self.assertEqual(github[0],
                         "- [acoustics-lab/sqm-toolbox](https://github.com/acoustics-lab/sqm-toolbox) (Python, ★ 12, "
                         "last push 2026-09-30): Sound quality metrics: Zwicker loudness, sharpness, roughness "
                         "@\u200bmaintainer see #\u200b12. Matched `psychoacoustic`, `\"zwicker loudness\"`.")
        self.assertTrue(github[1].startswith("- [audiojs/effect](https://github.com/audiojs/effect) (JavaScript, ★ 40, "
                                             "last push 2026-09-29, packages: [npm @\u200baudio/effect-exciter]"
                                             "(https://www.npmjs.com/package/@audio/effect-exciter), "))
        self.assertTrue(github[1].endswith("Matched `psychoacoustic`, `psychoacoustic` (npm)."))
        self.assertIn("(Rust, ★ 1, last push 2026-05-01): No description. Matched `\"zwicker loudness\"`.", github[2])
        crates = report.split("### crates.io (2)\n\n")[1].splitlines()
        self.assertTrue(crates[0].startswith("- [oxideav-vorbis](https://crates.io/crates/oxideav-vorbis) (Rust, "
                                             "updated 2026-09-01, [repository](https://github.com/OxideAV/oxideav-vorbis))"))
        self.assertTrue(crates[1].startswith("- [zimtohrli-sys](https://crates.io/crates/zimtohrli-sys)"))
        self.assertNotIn("### npm", report)

    def test_report_is_capped(self) -> None:
        with mock.patch.object(discover, "MAX_ENTRIES", 2):
            report = discover.render_report(self.search_all(), CUTOFF, github_skipped=False)
        self.assertTrue(report.startswith("Found 5 new candidates; the 2 most relevant are listed."))
        self.assertEqual(report.count("\n- "), 2)

    def test_nothing_found_is_a_single_line(self) -> None:
        empty = json_reply({"items": [], "crates": [], "objects": []})
        self.serve({discover.github_search_url("psychoacoustic"): empty, discover.crates_search_url("zwicker"): empty})
        search = discover.Search(_common.Http("t"), discover.Exclusions(set(), set()), CUTOFF)
        search.github(["psychoacoustic"])
        search.crates(["zwicker"])
        self.assertEqual(discover.render_report(search, CUTOFF, github_skipped=False),
                         "No new candidates (searched 1 GitHub and 1 crates.io queries).\n")


class MainTest(DiscoverCase):
    def test_without_token_only_registries_are_searched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            (data / "projects").mkdir()
            (data / "projects" / "metasona.yaml").write_text(
                "id: metasona\nrepository: https://github.com/huaaudio/metasona\n", encoding="utf-8")
            (data / "ignored.yaml").write_text("- url: https://crates.io/crates/oxideav-vorbis\n  reason: Codec.\n",
                                               encoding="utf-8")
            web = self.serve(routes())
            report_path, output = data / "discover.md", io.StringIO()
            with mock.patch.object(discover, "DATA_DIR", data), mock.patch.dict(os.environ), redirect_stdout(output):
                os.environ.pop("GITHUB_TOKEN", None)
                os.environ.pop("GH_TOKEN", None)
                self.assertEqual(discover.main(["--max-queries", "1", "--report", str(report_path)]), 0)
            self.assertEqual(output.getvalue(), "2 new candidates\n")
            self.assertFalse(any("api.github.com" in url for url in web.urls))
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("GitHub was not searched because neither GITHUB_TOKEN nor GH_TOKEN is set", report)
            self.assertIn("### npm (1)", report)


if __name__ == "__main__":
    unittest.main()
