"""Tests for scripts/release.py: which update notes a release lists, its title and the version check."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import _common  # noqa: E402
import release  # noqa: E402

UPDATES = [
    {"date": "2026-11-02", "title": "Version 0.6.0: a new page", "body": "The new page.\nIt has two lines.\n"},
    {"date": "2026-10-30", "title": "Two newly released projects", "body": "Added two."},
    {"date": "2026-10-27", "title": "Version 0.5.10: ROTA added", "body": "- first\n  item\n- second"},
    {"date": "2026-10-09", "title": "Version 0.5: search", "body": "Search."},
    {"date": "2026-10-08", "title": "An older note", "body": "Old."},
]
INDEX = {"as_of": "2026-11-02", "url": "https://example.github.io/LIST/",
         "counts": {"metrics": 22, "projects": 41, "references": 55}}


class ReleaseTest(unittest.TestCase):
    def test_versions(self) -> None:
        self.assertEqual(release.version_tuple("0.5"), (0, 5, 0))
        self.assertEqual(release.version_tuple("0.5.10"), (0, 5, 10))
        self.assertGreater(release.version_tuple("0.5.10"), release.version_tuple("0.5.9"))
        self.assertEqual(release.note_version("Version 0.5.9: SQAT's layout"), ((0, 5, 9), "SQAT's layout"))
        self.assertIsNone(release.note_version("Two newly released projects"))

    def test_notes_since_the_previous_release(self) -> None:
        titles = [u["title"] for u in release.select(UPDATES, "0.6.0", "0.5.0", "2026-10-09")]
        # The previous release (0.5) and what came before it are left out; notes without a version count by date.
        self.assertEqual(titles, ["Version 0.6.0: a new page", "Two newly released projects",
                                  "Version 0.5.10: ROTA added"])
        self.assertEqual(len(release.select(UPDATES, "0.6.0", None, None)), 5)
        # A later note does not belong to an earlier release.
        self.assertNotIn("Version 0.6.0: a new page",
                         [u["title"] for u in release.select(UPDATES, "0.5.10", "0.5.0", "2026-10-09")])

    def test_markdown_and_title(self) -> None:
        self.assertEqual(release.markdown("The new page.\nIt has two lines.\n"), "The new page. It has two lines.")
        self.assertEqual(release.markdown("- first\n  item\n- second"), "- first item\n- second")
        self.assertEqual(release.title(UPDATES, "0.6.0"), "LISQM 0.6.0: a new page")
        self.assertEqual(release.title(UPDATES, "0.7.0"), "LISQM 0.7.0")
        text = release.notes(UPDATES, "0.6.0", "0.5.0", "2026-10-09", INDEX)
        self.assertTrue(text.startswith("LISQM 0.6.0, the list as of 2026-11-02: 22 metrics, 41 projects"))
        self.assertIn("lisqm-0.6.0.json", text)
        self.assertIn("## Changes since 0.5.0", text)
        self.assertIn("### 2026-10-27: Version 0.5.10: ROTA added\n\n- first item\n- second", text)
        self.assertNotIn("Version 0.5: search", text)

    def test_check_against_the_data(self) -> None:
        current = str(_common.load_yaml(_common.DATA_DIR / "site.yaml")["version"])
        self.assertEqual(release.check(current), [], "data/site.yaml and CITATION.cff must carry the same version")
        self.assertTrue(release.check("99.0.0"))
        self.assertIn("not a version", release.check("0.6")[0])


if __name__ == "__main__":
    unittest.main()
