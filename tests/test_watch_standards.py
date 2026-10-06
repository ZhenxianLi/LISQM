"""Tests for scripts/watch_standards.py, using mock ISO open data and a mock Ecma page (no network access)."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
sys.path[:0] = [str(TESTS.parent / "scripts"), str(TESTS / "fixtures")]

import _common  # noqa: E402
import watch_standards  # noqa: E402
from fakehttp import FakeWeb, Reply, fixture_bytes  # noqa: E402

ISO_URL = "https://opendata.example/iso_deliverables_metadata.jsonl"
PAGE_URL = "https://ecma.example/standards/ecma-418/"
ISO_SOURCE = {"id": "iso", "name": "ISO Open Data", "type": "iso-open-data", "url": ISO_URL,
              "patterns": [r"^ISO(/\w+)? 532(-[123])?\b", r"^ISO(/\w+)? 226\b", r"^ISO(/\w+)? 20065\b",
                           r"^ISO(/\w+)? 1996-[23]\b"]}
PAGE_SOURCE = {"id": "ecma-418", "name": "ECMA-418", "type": "page", "url": PAGE_URL,
               "extract": r"(?i)\b\d+(?:st|nd|rd|th) edition\b"}

ISO_STATE = {"deliverables": {
    "4603": {"reference": "ISO 532:1975", "currentStage": 9599, "publicationDate": "1975-08-01", "edition": 1,
             "replacedBy": [63077, 63078]},
    "63077": {"reference": "ISO 532-1:2017", "currentStage": 9092, "publicationDate": "2017-06-15", "edition": 1,
              "replacedBy": [90809]},
    "81518": {"reference": "ISO/TS 20065:2022", "currentStage": 6060, "publicationDate": "2022-03-10", "edition": 1,
              "replacedBy": []},
    "83117": {"reference": "ISO 226:2023", "currentStage": 6060, "publicationDate": "2023-01-05", "edition": 3,
              "replacedBy": []},
    "90809": {"reference": "ISO/CD 532-1", "currentStage": 3020, "publicationDate": None, "edition": 2,
              "replacedBy": []},
}}


def routes() -> dict:
    return {ISO_URL: Reply(body=fixture_bytes("standards/iso_deliverables.jsonl")),
            PAGE_URL: Reply(body=fixture_bytes("standards/ecma-418.html"), headers={"Content-Type": "text/html"})}


class WatchCase(unittest.TestCase):
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


class IsoTest(WatchCase):
    def test_matching_deliverables_are_recorded(self) -> None:
        self.serve(routes())
        # Not recorded: ISO 5320, ISO 2260 (other numbers) and ISO 1996-1 (other part).
        self.assertEqual(watch_standards.check_iso(_common.Http(), ISO_SOURCE), ISO_STATE)

    def test_first_check_lists_everything(self) -> None:
        self.serve(routes())
        state, sections, errors = watch_standards.check_all(_common.Http(), [ISO_SOURCE], {})
        self.assertEqual((state, errors), ({"iso": ISO_STATE}, []))
        self.assertEqual(sections, [("ISO Open Data", [
            "First check; 5 matching deliverables recorded:",
            "",
            "- [ISO 226:2023](https://www.iso.org/standard/83117.html): stage 60.60 (published), "
            "published 2023-01-05, edition 3",
            "- [ISO 532-1:2017](https://www.iso.org/standard/63077.html): stage 90.92 (to be revised), "
            "published 2017-06-15, edition 1",
            "- [ISO 532:1975](https://www.iso.org/standard/4603.html): stage 95.99 (withdrawn), "
            "published 1975-08-01, edition 1",
            "- [ISO/CD 532-1](https://www.iso.org/standard/90809.html): stage 30.20 (committee), edition 2",
            "- [ISO/TS 20065:2022](https://www.iso.org/standard/81518.html): stage 60.60 (published), "
            "published 2022-03-10, edition 1",
        ])])

    def test_changes_are_reported(self) -> None:
        self.serve(routes())
        previous = copy.deepcopy(ISO_STATE)
        del previous["deliverables"]["90809"]
        previous["deliverables"]["63077"].update(currentStage=9093, replacedBy=[])
        previous["deliverables"]["83117"].update(currentStage=5020, publicationDate=None)
        previous["deliverables"]["66941"] = {"reference": "ISO/PAS 20065:2016", "currentStage": 9599,
                                             "publicationDate": "2016-08-01", "edition": 1, "replacedBy": [81518]}
        _, sections, _ = watch_standards.check_all(_common.Http(), [ISO_SOURCE], {"iso": previous})
        self.assertEqual(sections, [("ISO Open Data", [
            "- [ISO 226:2023](https://www.iso.org/standard/83117.html): stage 50.20 (approval) → 60.60 (published); "
            "publication date none → 2023-01-05",
            "- [ISO 532-1:2017](https://www.iso.org/standard/63077.html): stage 90.93 (confirmed) → "
            "90.92 (to be revised); replaced by [ISO/CD 532-1](https://www.iso.org/standard/90809.html)",
            "- New: [ISO/CD 532-1](https://www.iso.org/standard/90809.html): stage 30.20 (committee), edition 2",
            "- No longer in the data set: [ISO/PAS 20065:2016](https://www.iso.org/standard/66941.html)",
        ])])

    def test_truncated_download_keeps_the_previous_state(self) -> None:
        body = fixture_bytes("standards/iso_deliverables.jsonl")
        at_line_end = body.rindex(b"\n", 0, len(body) - 1) + 1  # drop the last line
        self.serve({ISO_URL: [Reply(body=body[:at_line_end], headers={"Content-Length": str(len(body))}),
                              Reply(body=body[:-100])]})
        previous = {"iso": ISO_STATE}
        state, sections, errors = watch_standards.check_all(_common.Http(), [ISO_SOURCE], previous)
        self.assertEqual((state, sections), (previous, []))
        self.assertEqual(errors, [f"- ISO Open Data (`iso`): incomplete download: {at_line_end} of {len(body)} "
                                  f"bytes; previous state kept"])
        state, sections, errors = watch_standards.check_all(_common.Http(), [ISO_SOURCE], previous)
        self.assertEqual((state, sections), (previous, []))
        self.assertTrue(errors[0].startswith("- ISO Open Data (`iso`): invalid JSON on line 9: "), errors)

    def test_no_match_at_all_is_an_error(self) -> None:
        self.serve(routes())
        source = ISO_SOURCE | {"patterns": [r"^ISO 99999\b"]}
        state, _, errors = watch_standards.check_all(_common.Http(), [source], {"iso": ISO_STATE})
        self.assertEqual(state, {"iso": ISO_STATE})
        self.assertIn("none of the 8 deliverables matches the patterns", errors[0])

    def test_stage_label(self) -> None:
        self.assertEqual(watch_standards.stage_label(9599), "95.99 (withdrawn)")
        self.assertEqual(watch_standards.stage_label(4020), "40.20 (enquiry)")
        self.assertEqual(watch_standards.stage_label(None), "unknown stage")


class PageTest(WatchCase):
    def test_visible_edition_strings_and_hash(self) -> None:
        self.serve(routes())
        result = watch_standards.check_page(_common.Http(), PAGE_SOURCE)
        # Strings in <style>, <script> and <noscript> are not visible; <sup> does not split words.
        self.assertEqual(result["editions"], ["3rd edition", "4th Edition"])
        text = watch_standards.visible_text(fixture_bytes("standards/ecma-418.html").decode())
        self.assertIn("ECMA-418-1, 3rd edition, December 2024 ECMA-418-2, 4th Edition, June 2025", text)
        self.assertIn("(December 2024)", text)
        self.assertEqual(result["text_sha256"], hashlib.sha256(text.encode()).hexdigest())

    def test_page_changes(self) -> None:
        url = PAGE_URL
        new = {"editions": ["3rd edition", "4th edition"], "text_sha256": "b"}
        self.assertEqual(watch_standards.diff_page({"editions": ["3rd edition"], "text_sha256": "a"}, new, url),
                         [f"- New on [the page]({url}): “4th edition”"])
        self.assertEqual(watch_standards.diff_page({"editions": new["editions"], "text_sha256": "a"}, new, url),
                         [f"- The text of [the page]({url}) changed; the matched strings did not"])
        self.assertEqual(watch_standards.diff_page(new, new, url), [])

    def test_unreachable_page_keeps_the_previous_state(self) -> None:
        self.serve({PAGE_URL: Reply(503)})
        previous = {"ecma-418": {"editions": ["3rd edition"], "text_sha256": "a"}}
        state, sections, errors = watch_standards.check_all(_common.Http(), [PAGE_SOURCE], previous)
        self.assertEqual((state, sections), (previous, []))
        self.assertEqual(errors, [f"- ECMA-418 (`ecma-418`): HTTP 503 Service Unavailable ({PAGE_URL}); "
                                  f"previous state kept"])
        self.assertEqual(self.sleep.call_count, 2)  # three tries
        report = watch_standards.render_report(sections, errors, 1)
        self.assertTrue(report.startswith("### Errors\n\n- ECMA-418"))


class MainTest(WatchCase):
    def test_state_is_written_only_when_something_changed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            config = [ISO_SOURCE, PAGE_SOURCE]
            (data / "standards-watch.yaml").write_text(json.dumps(config), encoding="utf-8")  # JSON is valid YAML
            state_path, report_path = data / "standards-watch.json", data / "standards.md"
            state_path.write_text("{}\n", encoding="utf-8")
            self.serve(routes())
            with mock.patch.object(watch_standards, "DATA_DIR", data):
                self.assertEqual(watch_standards.main(["--report", str(report_path)]), 0)
                written = state_path.read_text(encoding="utf-8")
                self.assertEqual(json.loads(written)["iso"], ISO_STATE)
                self.assertEqual(written, _common.dump_json(json.loads(written)))
                self.assertIn("### ECMA-418\n\n- First check of [the page]", report_path.read_text(encoding="utf-8"))
                modified = state_path.stat().st_mtime_ns
                self.assertEqual(watch_standards.main(["--report", str(report_path)]), 0)
            self.assertEqual(state_path.stat().st_mtime_ns, modified)
            self.assertEqual(report_path.read_text(encoding="utf-8"),
                             "No changes in the watched standards (2 sources checked).\n")

    def test_shipped_configuration_is_valid(self) -> None:
        sources = watch_standards.load_sources(_common.DATA_DIR / "standards-watch.yaml")
        self.assertTrue(sources)

    def test_invalid_pattern_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "standards-watch.yaml"
            path.write_text("- {id: x, type: page, url: 'https://example.org', extract: '(unclosed'}\n",
                            encoding="utf-8")
            with self.assertRaises(SystemExit) as raised:
                watch_standards.load_sources(path)
            self.assertIn("invalid regular expression", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
