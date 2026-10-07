"""Tests for scripts/check_links.py, with canned HTTP responses (no network access)."""

from __future__ import annotations

import io
import json
import socket
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
sys.path[:0] = [str(TESTS.parent / "scripts"), str(TESTS / "fixtures")]

import _common  # noqa: E402
import check_links  # noqa: E402
from fakehttp import FakeWeb, Reply  # noqa: E402

PROJECT = """id: demo
name: Demo
repository: https://github.com/example/demo
paper:
  citation: Someone (2020). A paper.
  doi: 10.1000/demo
notes:
  - See [the docs](https://example.org/docs). Also https://example.org/plain.
sources:
  - https://github.com/example/demo/blob/main/README.md
  - https://github.com/example/demo
"""


class CollectTest(unittest.TestCase):
    def test_urls_dois_and_markdown_links_with_their_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            (data / "projects").mkdir()
            (data / "projects" / "demo.yaml").write_text(PROJECT, encoding="utf-8")
            (data / "references.yaml").write_text("- id: r\n  url: https://example.org/plain\n", encoding="utf-8")
            found = check_links.collect(data)
        self.assertEqual(list(found), [
            "https://github.com/example/demo", "https://doi.org/10.1000/demo", "https://example.org/docs",
            "https://example.org/plain", "https://github.com/example/demo/blob/main/README.md"])
        self.assertEqual(found["https://example.org/plain"], ["data/projects/demo.yaml", "data/references.yaml"])

    def test_the_real_data_has_links(self) -> None:
        found = check_links.collect()
        self.assertIn("https://github.com/ggrecow/SQAT", found)
        self.assertTrue(all(url.startswith(("http://", "https://")) for url in found))


class CheckTest(unittest.TestCase):
    def setUp(self) -> None:
        for patcher in (mock.patch("time.sleep"), mock.patch("sys.stderr", new_callable=io.StringIO)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def serve(self, routes: dict) -> FakeWeb:
        web = FakeWeb(routes)
        patcher = mock.patch.object(_common, "_urlopen", web)
        patcher.start()
        self.addCleanup(patcher.stop)
        return web

    def test_ok_after_head_is_refused(self) -> None:
        web = self.serve({"https://a.example/": [Reply(405), Reply(200)]})
        self.assertEqual(check_links.check("https://a.example/"), ("ok", ""))
        self.assertEqual([r.get_method() for r in web.requests], ["HEAD", "GET"])

    def test_gone_refused_and_failing(self) -> None:
        self.serve({"https://gone.example/": Reply(404), "https://bot.example/": Reply(403),
                    "https://down.example/": Reply(503)})
        self.assertEqual(check_links.check("https://gone.example/"), ("broken", "HTTP 404"))
        self.assertEqual(check_links.check("https://bot.example/"), ("refused", "HTTP 403"))
        self.assertEqual(check_links.check("https://down.example/"), ("error", "HTTP 503"))

    def test_unknown_host_is_broken(self) -> None:
        def no_host(request, timeout=None):
            raise urllib.error.URLError(socket.gaierror(-2, "Name or service not known"))
        with mock.patch.object(_common, "_urlopen", no_host):
            self.assertEqual(check_links.check("https://nowhere.invalid/"), ("broken", "host not found"))


class ReportTest(unittest.TestCase):
    FOUND = {"https://gone.example/": ["data/projects/a.yaml"], "https://down.example/": ["data/references.yaml"],
             "https://new-down.example/": ["data/leads.yaml"], "https://ok.example/": ["data/site.yaml"]}
    RESULTS = {"https://gone.example/": ("broken", "HTTP 404"), "https://down.example/": ("error", "HTTP 503"),
               "https://new-down.example/": ("error", "network error: timed out"), "https://ok.example/": ("ok", "")}

    def test_broken_at_once_unreachable_only_twice(self) -> None:
        previous = {"failing": {"https://down.example/": {"since": "2026-10-01", "detail": "HTTP 503"}}}
        failing, broken, unreachable = check_links.evaluate(self.RESULTS, previous, "2026-10-15")
        self.assertEqual(broken, ["https://gone.example/"])
        self.assertEqual(unreachable, ["https://down.example/"])
        self.assertEqual(failing["https://down.example/"]["since"], "2026-10-01")
        self.assertEqual(failing["https://new-down.example/"]["since"], "2026-10-15")
        report = check_links.render_report(self.FOUND, self.RESULTS, failing, broken, unreachable)
        self.assertIn("### Broken links", report)
        self.assertIn("https://gone.example/ (HTTP 404) in `data/projects/a.yaml`", report)
        self.assertIn("failing since 2026-10-01", report)
        self.assertNotIn("new-down", report)

    def test_single_line_when_nothing_to_fix(self) -> None:
        results = {"https://ok.example/": ("ok", ""), "https://bot.example/": ("refused", "HTTP 403")}
        failing, broken, unreachable = check_links.evaluate(results, {}, "2026-10-15")
        report = check_links.render_report({}, results, failing, broken, unreachable)
        self.assertEqual(report, "No broken links (2 links checked; 1 refused automated requests and were not "
                                 "judged).\n")

    def test_state_is_written_only_when_it_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "link-check.json"
            path.write_text('{"failing": {}, "generated": null}\n', encoding="utf-8")
            self.assertFalse(check_links.write_state(path, {}, {"failing": {}}, "2026-10-15T05:17:00Z"))
            failing = {"https://down.example/": {"since": "2026-10-15", "detail": "HTTP 503"}}
            self.assertTrue(check_links.write_state(path, failing, {"failing": {}}, "2026-10-15T05:17:00Z"))
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["failing"], failing)


if __name__ == "__main__":
    unittest.main()
