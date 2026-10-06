"""Checks on the generated website: the data validates, every internal link resolves, every page has a
Markdown twin, structured data parses, and the README markers are intact."""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build  # noqa: E402
from pmi.data import STANDING_ORDER, load  # noqa: E402
from pmi.describe import timeline  # noqa: E402


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.jsonld: list[str] = []
        self._in_ld = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"] or "")
        for key in ("href", "src"):
            if a.get(key):
                self.links.append(a[key] or "")
        self._in_ld = tag == "script" and a.get("type") == "application/ld+json"

    def handle_data(self, data: str) -> None:
        if self._in_ld:
            self.jsonld.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._in_ld = False


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = load()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.site = Path(cls.tmp.name) / "site"
        build.build_site(cls.index, cls.site)
        cls.pages = sorted(cls.site.rglob("*.html"))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def parse(self, page: Path) -> _Links:
        parser = _Links()
        parser.feed(page.read_text(encoding="utf-8"))
        return parser

    def test_every_method_and_project_has_a_page(self) -> None:
        for m in self.index.methods:
            self.assertTrue((self.site / "metrics" / f"{m['id']}.html").exists(), m["id"])
        for p in self.index.projects:
            self.assertTrue((self.site / "projects" / f"{p['id']}.html").exists(), p["id"])

    def test_internal_links_resolve(self) -> None:
        anchors = {page: self.parse(page).ids for page in self.pages}
        base = self.index.site["base_url"]
        for page in self.pages:
            for link in self.parse(page).links:
                if link.startswith(base):  # absolute links to this site (404 page, feed) must exist too
                    link = str(self.site / link[len(base):]) if page.name == "404.html" else ""
                if not link or re.match(r"^(https?:|mailto:)", link):
                    continue
                target, _, fragment = link.partition("#")
                path = (page.parent / target).resolve() if target else page
                if path.is_dir():
                    path = path / "index.html"
                self.assertTrue(path.exists(), f"{page.relative_to(self.site)} links to missing {link}")
                if fragment and path.suffix == ".html":
                    self.assertIn(fragment, anchors.get(path, set()),
                                  f"{page.relative_to(self.site)} links to missing anchor {link}")

    def test_markdown_twins(self) -> None:
        for page in self.pages:
            if page.name == "404.html":
                continue
            self.assertTrue(page.with_suffix(".md").exists(), f"no Markdown twin for {page.name}")

    def test_structured_data_parses(self) -> None:
        for page in self.pages:
            for block in self.parse(page).jsonld:
                data = json.loads(block)
                self.assertEqual(data["@context"], "https://schema.org", page.name)

    def test_machine_readable_files(self) -> None:
        data = json.loads((self.site / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["projects"]), len(self.index.projects))
        self.assertEqual(len(data["methods"]), len(self.index.methods))
        for name in ("llms.txt", "llms-full.txt", "feed.xml", "sitemap.xml", "robots.txt", "style.css"):
            self.assertTrue((self.site / name).exists(), name)
        llms = (self.site / "llms.txt").read_text(encoding="utf-8")
        self.assertTrue(llms.startswith(f"# {self.index.site['title']}\n\n> "))

    def test_readme_markers(self) -> None:
        for name in ("README.md", "README.zh-CN.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            for key in ("stats", "overview", "gaps", "coverage", "projects"):
                self.assertIn(f"<!-- BEGIN GENERATED: {key} -->", text, f"{name}: {key}")
                self.assertIn(f"<!-- END GENERATED: {key} -->", text, f"{name}: {key}")

    def test_credit_line_everywhere(self) -> None:
        credit = self.index.site["credit"]
        self.assertEqual(credit, "Developed by Zhenxian LI with assistance from Claude Code.")
        for page in self.pages:
            text = re.sub(r"<[^>]+>", "", page.read_text(encoding="utf-8"))
            self.assertIn(credit, text, page.name)
        for name in ("README.md", "README.zh-CN.md", "llms.txt", "llms-full.txt", "CITATION.cff"):
            self.assertIn(credit, (ROOT / name).read_text(encoding="utf-8"), name)
        self.assertIn(credit, (self.site / "llms.txt").read_text(encoding="utf-8"))

    def test_new_projects_never_come_first(self) -> None:
        def ranks(impls: list[dict]) -> list[int]:
            return [STANDING_ORDER[i["_project"]["standing"]] for i in impls]

        for m in self.index.methods:
            self.assertEqual(ranks(m["_impls"]), sorted(ranks(m["_impls"])), m["id"])
        for _, rows in timeline(self.index):
            for row in rows:
                for cell in row["cells"]:
                    for ref, impls in cell:
                        self.assertEqual(ranks(impls), sorted(ranks(impls)), f"{row['method']['id']} {ref['id']}")
        self.assertEqual([p["standing"] for p in self.index.projects_by_standing()],
                         sorted((p["standing"] for p in self.index.projects), key=STANDING_ORDER.get))

    def test_new_projects_are_marked(self) -> None:
        for p in self.index.projects:
            if p["standing"] != "new":
                continue
            text = (self.site / "projects" / f"{p['id']}.html").read_text(encoding="utf-8")
            self.assertIn("not yet widely used", text, p["id"])

    def test_home_page_opens_with_the_timeline(self) -> None:
        html = (self.site / "index.html").read_text(encoding="utf-8")
        body = html[html.index("<main"):]
        self.assertTrue(body[body.index("<h2"):].startswith('<h2 id="timeline">'), "the first section is not the timeline")
        self.assertLess(body.index('<table class="timeline">'), body.index('id="coverage"'))
        for m in self.index.methods:
            self.assertIn(f'href="metrics/{m["id"]}.html"', html, m["id"])
        for f in self.index.families:
            self.assertIn(f'id="{f["id"]}"', html, f["id"])


if __name__ == "__main__":
    unittest.main()
