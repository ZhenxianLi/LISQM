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
from pmi.data import GROUP_ORDER, load  # noqa: E402
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
        self.assertTrue(llms.startswith(f"# {self.index.site['name']}: {self.index.site['title']}\n\n> "))

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

    def test_new_and_legacy_projects_never_come_first(self) -> None:
        def ranks(impls: list[dict]) -> list[int]:
            return [GROUP_ORDER[i["_project"]["_group"]] for i in impls]

        for m in self.index.methods:
            self.assertEqual(ranks(m["_impls"]), sorted(ranks(m["_impls"])), m["id"])
        for _, rows in timeline(self.index):
            for row in rows:
                for cell in row["cells"]:
                    for ref, impls in cell:
                        self.assertEqual(ranks(impls), sorted(ranks(impls)), f"{row['method']['id']} {ref['id']}")
        ordered = self.index.projects_by_group()
        self.assertEqual([p["_group"] for p in ordered], sorted((p["_group"] for p in ordered), key=GROUP_ORDER.get))
        self.assertEqual(ordered[-len(self.index.others()):], self.index.others(), "tools under Others come last")
        self.assertEqual([p["id"] for p in ordered[:3]], ["sqat", "amt", "mosqito"])
        self.assertEqual(self.index.group("newly-released")[0]["id"], "metasona")
        self.assertEqual([p["id"] for p in self.index.mainstream()], ["sqat", "amt", "mosqito"])

    def test_legacy_projects(self) -> None:
        legacy = {p["id"] for p in self.index.group("legacy")}
        self.assertIn("psychoacoustic-parameters-measurer", legacy)
        self.assertIn("python-acoustics", legacy, "archived projects are legacy")
        for p in self.index.projects:
            if p["_mainstream"] or p["kind"] == "reference-program" or p["standing"] == "newly-released":
                self.assertNotIn(p["id"], legacy, "the most widely used projects and reference programs stay")
        self.assertEqual(self.index.project["mosqito"]["_group"], "established")
        html = (self.site / "projects" / "psychoacoustic-parameters-measurer.html").read_text(encoding="utf-8")
        self.assertIn("Legacy project.", html)
        home = (self.site / "index.html").read_text(encoding="utf-8")
        self.assertIn('<li class="quiet" title="PsychoacousticParametersMeasurer:', home)
        self.assertNotRegex(home, r'<li class="quiet" title="MoSQITo:')

    def test_others_are_not_listed_under_metrics(self) -> None:
        others = {p["id"] for p in self.index.others()}
        self.assertTrue({"psychobox", "soundscapy"} <= others)
        for m in self.index.methods:
            self.assertFalse(any(i.get("_via") for i in m["_impls"]), m["id"])
            self.assertFalse(others & {i["_project"]["id"] for i in m["_impls"]}, m["id"])
        html = (self.site / "index.html").read_text(encoding="utf-8")
        table = html[html.index('<table class="timeline">'):html.index("</table>", html.index('<table class="timeline">'))]
        self.assertNotIn("projects/psychobox.html", table)
        llms = (self.site / "llms.txt").read_text(encoding="utf-8")
        projects, rest = llms.split("\n## Others\n")
        for p in self.index.others():
            self.assertNotIn(f"projects/{p['id']}.md", projects[projects.index("\n## Projects\n"):], p["id"])
            self.assertIn(f"projects/{p['id']}.md", rest, p["id"])
        data = json.loads((self.site / "index.json").read_text(encoding="utf-8"))
        flagged = {p["id"]: p for p in data["projects"] if p["group"] == "others"}
        self.assertEqual(set(flagged), others)
        self.assertEqual(flagged["psychobox"]["calls"], ["mosqito"])

    def test_coverage_marks_are_drawn(self) -> None:
        html = (self.site / "languages.html").read_text(encoding="utf-8")
        legend = html[html.index('class="small mark-key"'):]
        legend = legend[:legend.index("</p>")]
        for state in ("current", "new", "partial", "none"):
            self.assertIn(f'class="mark mark-{state}"', legend, state)
        table = html[html.index('<table class="grid coverage">'):]
        table = table[:table.index("</table>")]
        cells = re.findall(r"<td[^>]*>(.*?)</td>", table)
        marks = [c for c in cells if 'class="mark ' in c]
        self.assertEqual(len(marks), len(self.index.methods) * 6)
        self.assertFalse(re.search("[●◐○]", table), "coverage marks should be drawn, not typed")

    def test_a_project_is_named_once_per_language(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        overview = readme[readme.index("BEGIN GENERATED: overview"):readme.index("END GENERATED: overview")]
        for row in overview.splitlines()[3:]:
            for group in row.split(" · "):
                names = re.findall(r"\[([^\]]+)\]\([^)]+/projects/", group.split("earlier or related")[0])
                self.assertEqual(len(names), len(set(names)), group[:120])

    def test_newly_released_projects_are_marked(self) -> None:
        for p in self.index.projects:
            if p["standing"] != "newly-released":
                continue
            text = (self.site / "projects" / f"{p['id']}.html").read_text(encoding="utf-8")
            self.assertIn("not yet widely used", text.lower(), p["id"])

    def test_home_page_opens_with_the_timeline(self) -> None:
        html = (self.site / "index.html").read_text(encoding="utf-8")
        body = html[html.index("<main"):]
        self.assertTrue(body[body.index("<h2"):].startswith('<h2 id="timeline">'), "the first section is not the timeline")
        self.assertLess(body.index('<table class="timeline">'), body.index('id="gaps"'))
        for m in self.index.methods:
            self.assertIn(f'href="metrics/{m["id"]}.html"', html, m["id"])
        for f in self.index.families:
            self.assertIn(f'id="{f["id"]}"', html, f["id"])

    def test_long_timeline_cells_fold_three_groups_together(self) -> None:
        from pmi.render_html import LONG_CELL
        html = (self.site / "index.html").read_text(encoding="utf-8")
        table = html[html.index('<table class="timeline">'):html.index("</table>")]
        group = {p["id"]: p["_group"] for p in self.index.projects}
        folds = 0
        for cell in re.findall(r'<td class="bin[^"]*">(.*?)</td>', table):
            if "<details" not in cell:
                continue
            self.assertGreaterEqual(cell.count("<li"), LONG_CELL, "only long cells fold")
            for edition in cell.split('<div class="edition')[1:]:
                self.assertLessEqual(edition.count("<details"), 1, "one fold per edition")
                if "<details" not in edition:
                    continue
                folds += 1
                inside = edition[edition.index("<details"):edition.index("</details>")]
                outside = edition.replace(inside, "")
                folded = {group[pid] for pid in re.findall(r'href="projects/([^"#]+)\.html"', inside)}
                self.assertLessEqual(folded, {"newly-released", "developing", "legacy"}, "established stay visible")
                visible = {group[pid] for pid in re.findall(r'href="projects/([^"#]+)\.html"', outside)}
                self.assertFalse(visible & folded, "a kind is either folded or shown, not split")
        self.assertGreater(folds, 0)
        iso = table[table.index("ISO 532-1:2017"):]
        summary = iso[iso.index("<summary>"):iso.index("</summary>")]
        for kind in ("tag-new", "tag-dev", "tag-legacy"):
            self.assertIn(kind, summary, "the three groups share one fold")

    def test_every_tab_has_its_own_sidebar(self) -> None:
        pages = {"index.html": "Home", "metrics/index.html": "Metrics", "metrics/sharpness.html": "Metrics",
                 "projects/index.html": "Projects", "projects/sqat.html": "Projects", "languages.html": "Languages",
                 "standards.html": "Standards", "faq.html": "FAQ", "updates.html": "Updates", "ai.html": "For AI",
                 "about.html": "About"}
        for page, tab in pages.items():
            html = (self.site / page).read_text(encoding="utf-8")
            nav = html[html.index('<nav class="tabs"'):html.index("</nav>")]
            self.assertEqual(re.findall(r'aria-current="page">([^<]+)<', nav), [tab], page)
            self.assertIn('<aside class="sidebar"', html, page)
            self.assertIn('id="top"', html, page)
        side = (self.site / "projects/pysqat.html").read_text(encoding="utf-8")
        side = side[side.index('<aside class="sidebar"'):]
        self.assertIn('projects/pysqat.html" aria-current="page"', side)
        self.assertIn('projects/metasona.html"', side)

    def test_languages_page(self) -> None:
        html = (self.site / "languages.html").read_text(encoding="utf-8")
        for anchor in ("coverage", "python", "matlab", "c", "rust", "julia", "across"):
            self.assertIn(f'id="{anchor}"', html, anchor)
        python = html[html.index('id="python"'):html.index('id="matlab"')]
        self.assertIn("Written in C, with a Python interface", python, "MetaSona's C core")
        self.assertIn("MATLAB Engine API for Python", html)

    def test_message_box_and_ai_page(self) -> None:
        faq = (self.site / "faq.html").read_text(encoding="utf-8")
        self.assertIn(f'action="{self.index.site["repository"]}/issues/new"', faq)
        self.assertIn('name="title"', faq)
        self.assertIn('name="body"', faq)
        self.assertNotIn("giscus", faq)
        self.assertLess(faq.index('class="message-form"'), faq.index('id="q1"'), "the message box comes first")
        self.assertLessEqual(faq.count('<h2 id="q'), 8, "only the key questions")
        ai = (self.site / "ai.html").read_text(encoding="utf-8")
        for name in ("llms.txt", "llms-full.txt", "index.json"):
            self.assertIn(f'{self.index.site["base_url"]}{name}', ai, name)
        self.assertTrue((self.site / "ai.md").exists())
        llms = (self.site / "llms.txt").read_text(encoding="utf-8")
        self.assertIn(f"{self.index.site['base_url']}ai.md", llms)


if __name__ == "__main__":
    unittest.main()
