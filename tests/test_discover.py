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
        # Example/Ignored-Meter (in ignored.yaml), oxideav-mp2 (query word only in keywords), stale npm/crates,
        # and results that mention no tracked metric (audiojs/effect, oxideav-vorbis, zimtohrli-sys).
        # Packages are keyed by their source repository.
        self.assertEqual(sorted(search.found), [
            "https://github.com/acoustics-lab/sqm-toolbox",
            "https://github.com/newcomer/loudness-rs",
        ])
        sqm = search.found["https://github.com/acoustics-lab/sqm-toolbox"]
        self.assertEqual(sqm.source, "GitHub")
        self.assertEqual([name for _, name, _ in sqm.packages], ["@acoustics-lab/sqm"])
        self.assertEqual(sqm.queries, [("GitHub", "psychoacoustic"), ("GitHub", ZWICKER), ("npm", "psychoacoustic")])
        self.assertEqual(sorted(search.irrelevant), [
            "https://crates.io/crates/oxideav-vorbis",
            "https://crates.io/crates/zimtohrli-sys",
            "https://github.com/audiojs/effect",
            "https://npmjs.com/package/@audio/effect-exciter",
            "https://npmjs.com/package/@audio/effect-subbass",
        ])
        self.assertEqual(search.errors, [])
        # GitHub searches are spaced to stay under 30 per minute.
        self.sleep.assert_any_call(discover.GITHUB_SEARCH_INTERVAL)

    def test_relevance(self) -> None:
        for texts, expected in (
            (("slink/PsychoacousticMetrics.jl", None), True),  # CamelCase is split
            (("iso532-1-rs", "Loudness in Rust"), True),
            (("someone/sqm", "Tools", ["iso-532", "sound-quality"]), True),  # topics count
            (("amber-willow8/epnl", "content"), False),  # EPNL alone is not enough
            (("chadmed/bankstown", "A psychoacoustic bass enhancement plugin"), False),
            (("lufs-meter", "Loudness meter: LUFS, ITU-R BS.1770"), False),  # programme loudness
            (("lufs-and-zwicker", "LUFS and Zwicker loudness"), True),
        ):
            self.assertEqual(discover.relevant(*texts), expected, texts)

    def test_own_listed_and_ignored_are_left_out(self) -> None:
        exclusions = discover.Exclusions.from_data(PROJECTS, IGNORED, own="https://github.com/Example/List")
        self.assertTrue(exclusions.excludes("https://github.com/example/list"))
        self.assertTrue(exclusions.excludes("https://github.com/huaaudio/metasona"))
        self.assertTrue(exclusions.excludes("https://github.com/example/ignored-meter"))

    def test_indexed_and_ignored_packages_are_left_out(self) -> None:
        self.serve(routes())
        projects = [{"id": "z", "repository": "https://example.org/z",
                     "packages": [{"registry": "crates", "name": "zimtohrli_sys"}]}]
        ignored = [{"url": "https://github.com/OxideAV/oxideav-vorbis.git", "reason": "Codec."}]
        search = discover.Search(_common.Http(), discover.Exclusions.from_data(projects, ignored), CUTOFF)
        search.crates(["psychoacoustic"])
        self.assertEqual(search.found, {})
        self.assertEqual(search.irrelevant, set(), "listed and ignored packages are not even counted")

    def test_failed_search_is_reported(self) -> None:
        self.serve({discover.npm_search_url("psychoacoustic"): Reply(500)})
        search = discover.Search(_common.Http(), discover.Exclusions(set(), set()), CUTOFF)
        search.npm(["psychoacoustic"])
        report = discover.render_report(search, CUTOFF, github_skipped=False)
        self.assertIn("### Errors\n\n- npm search `psychoacoustic`: HTTP 500 Internal Server Error", report)


class ReportTest(DiscoverCase):
    def test_report_lists_most_relevant_first_grouped_by_source(self) -> None:
        report = discover.render_report(self.search_all(), CUTOFF, github_skipped=False)
        self.assertTrue(report.startswith("Found 2 new candidates. Searched 2 GitHub, 1 crates.io and 1 npm queries."))
        self.assertIn(" 5 other results mentioned none of the metrics, models or standards in the list and are not "
                      "shown.\n", report)
        github = report.split("### GitHub (2)\n\n")[1].split("\n\n")[0].splitlines()
        self.assertEqual(github[0],
                         "- [acoustics-lab/sqm-toolbox](https://github.com/acoustics-lab/sqm-toolbox) (Python, ★ 12, "
                         "last push 2026-09-30, packages: [npm @\u200bacoustics-lab/sqm]"
                         "(https://www.npmjs.com/package/@acoustics-lab/sqm)): Sound quality metrics: Zwicker "
                         "loudness, sharpness, roughness @\u200bmaintainer see #\u200b12. Matched `psychoacoustic`, "
                         "`\"zwicker loudness\"`, `psychoacoustic` (npm).")
        self.assertIn("(Rust, ★ 1, last push 2026-05-01): No description. Matched `\"zwicker loudness\"`.", github[1])
        self.assertNotIn("### crates.io", report)
        self.assertNotIn("### npm", report)

    def test_report_is_capped(self) -> None:
        with mock.patch.object(discover, "MAX_ENTRIES", 1):
            report = discover.render_report(self.search_all(), CUTOFF, github_skipped=False)
        self.assertTrue(report.startswith("Found 2 new candidates; the 1 most relevant are listed."))
        self.assertEqual(report.count("\n- "), 1)

    def test_nothing_found_is_a_single_line(self) -> None:
        empty = json_reply({"items": [], "crates": [], "objects": []})
        self.serve({discover.github_search_url("psychoacoustic"): empty, discover.crates_search_url("zwicker"): empty})
        search = discover.Search(_common.Http("t"), discover.Exclusions(set(), set()), CUTOFF)
        search.github(["psychoacoustic"])
        search.crates(["zwicker"])
        self.assertEqual(discover.render_report(search, CUTOFF, github_skipped=False),
                         "No new candidates (searched 1 GitHub and 1 crates.io queries).\n")

    def test_only_irrelevant_results_are_a_single_line(self) -> None:
        self.serve({discover.npm_search_url("psychoacoustic"): routes()[discover.npm_search_url("psychoacoustic")]})
        search = discover.Search(_common.Http(), discover.Exclusions.from_data(
            [], [{"url": "https://www.npmjs.com/package/@acoustics-lab/sqm"}]), CUTOFF)
        search.npm(["psychoacoustic"])
        self.assertEqual(discover.render_report(search, CUTOFF, github_skipped=False),
                         "No new candidates (searched 1 npm query; 2 other results mentioned none of the metrics, "
                         "models or standards in the list and are not shown).\n")


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
            self.assertEqual(output.getvalue(), "1 new candidate\n")
            self.assertFalse(any("api.github.com" in url for url in web.urls))
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("GitHub was not searched because neither GITHUB_TOKEN nor GH_TOKEN is set", report)
            self.assertIn("### npm (1)", report)


if __name__ == "__main__":
    unittest.main()
