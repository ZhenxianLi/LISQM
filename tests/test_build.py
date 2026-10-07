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
                target = target.partition("?")[0]  # style.css?v=…
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
        for name in ("README.md",):
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
        for name in ("README.md", "llms.txt", "llms-full.txt", "CITATION.cff"):
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

    def test_timeline_editions_show_at_most_four_projects(self) -> None:
        from pmi.render_html import TIMELINE_SHOWN
        html = (self.site / "index.html").read_text(encoding="utf-8")
        table = html[html.index('<table class="timeline">'):html.index("</table>")]
        group = {p["id"]: p["_group"] for p in self.index.projects}
        more = 0
        for edition in table.split('<div class="edition')[1:]:
            edition = edition[:edition.index("</div>")]
            shown, _, hidden = edition.partition("<details>")
            self.assertLessEqual(shown.count("<li"), TIMELINE_SHOWN, edition[:80])
            order = [GROUP_ORDER[group[pid]] for pid in re.findall(r'href="projects/([^"#]+)\.html"', edition)]
            self.assertEqual(order, sorted(order), "the most established projects come first")
            found = re.search(r'<li class="more"><details><summary[^>]*><span class="closed">\+(\d+) more</span>',
                              edition)
            self.assertEqual(bool(found), bool(hidden), edition[:80])
            if found:
                more += 1
                self.assertGreaterEqual(int(found.group(1)), 2, "never just one more")
                self.assertEqual(hidden.count("<li"), int(found.group(1)), "the rest open in place")
                self.assertNotIn("#editions", edition, "+ more no longer leads away")
                self.assertIn('<span class="opened" hidden>show fewer</span>', edition, "hidden without the stylesheet")
        self.assertGreater(more, 0)
        iso = table[table.index("ISO 532-1:2017"):]
        iso = iso[:iso.index("</div>")]
        zwicker = next(row for _, rows in timeline(self.index) for row in rows
                       if row["method"]["id"] == "loudness-zwicker")
        current = next(impls for cell in zwicker["cells"] for ref, impls in cell if ref["id"] == "iso-532-1-2017")
        self.assertIn(f">+{len(current) - (TIMELINE_SHOWN - 1)} more</span>", iso)
        self.assertIn('class="mk mk-new"', table)

    def test_search_engine_key_and_verification_tags(self) -> None:
        from pmi import render_html
        key = self.index.site["indexnow_key"]
        self.assertEqual((self.site / f"{key}.txt").read_text(encoding="utf-8").strip(), key)
        saved = self.index.site.get("verification")
        self.index.site["verification"] = {"google": "g-code", "baidu": "codeva-b"}
        try:
            home = render_html.home(self.index)
            about = render_html.about_page(self.index)
        finally:
            self.index.site["verification"] = saved
        self.assertIn('<meta name="google-site-verification" content="g-code">', home)
        self.assertIn('<meta name="baidu-site-verification" content="codeva-b">', home)
        self.assertNotIn("site-verification", about)

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

    def test_version_matches_citation(self) -> None:
        cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
        self.assertIn(f'version: "{self.index.site["version"]}"', cff, "data/site.yaml and CITATION.cff disagree")

    def test_stylesheet_is_versioned(self) -> None:
        import hashlib
        version = hashlib.sha256((self.site / "style.css").read_bytes()).hexdigest()[:10]
        for page in self.pages:
            text = page.read_text(encoding="utf-8")
            self.assertIn(f'style.css?v={version}">', text, page.name)

    def test_validation_details(self) -> None:
        html = (self.site / "projects/psychoacousticmetrics-jl.html").read_text(encoding="utf-8")
        section = html[html.index('<h2 id="validation">How it was validated</h2>'):]
        section = section[:section.index("<h2", 4)]
        self.assertIn('also compared with <a href="../projects/mosqito.html">MoSQITo</a>', section)
        self.assertIn('reference code: <a href="../projects/sqat.html">SQAT</a>', section)
        self.assertIn('compared with <a href="../projects/sqat.html">SQAT</a></span>', section)
        self.assertIn("41 reference signals of DIN 45692:2009", section)
        self.assertIn("840-case formula grid", section)
        table = html[html.index('<h2 id="implements">'):html.index('<h2 id="validation">')]
        self.assertIn('href="#v-psychoacoustic-annoyance-widmann-1992"', table, "the table links to the details")
        self.assertIn(">compared with SQAT</a>", table)
        self.assertIn("also compared with MoSQITo", table)
        self.assertNotIn(">another implementation<", html)
        # Rows with the same evidence and details are described once; nothing stated is summed up in one line.
        pysqat = (self.site / "projects/pysqat.html").read_text(encoding="utf-8")
        self.assertEqual(pysqat.count("generated reports are not committed"), 1)
        sqat = (self.site / "projects/sqat.html").read_text(encoding="utf-8")
        self.assertIn("Not stated for Sottek Hearing Model fluctuation strength · ECMA-418-2:2025", sqat)
        method = (self.site / "metrics/sharpness.html").read_text(encoding="utf-8")
        self.assertIn('<h2 id="validation">How they were validated</h2>', method)
        self.assertIn('href="#v-kirin-hypha-din-45692-2009"', method)
        twin = (self.site / "projects/psychoacousticmetrics-jl.md").read_text(encoding="utf-8")
        self.assertIn("## How it was validated", twin)
        self.assertIn("  - Cross-checked against MoSQITo for all four weightings.", twin)
        data = json.loads((self.site / "index.json").read_text(encoding="utf-8"))
        jl = next(p for p in data["projects"] if p["id"] == "psychoacousticmetrics-jl")
        self.assertEqual(jl["implements"][0]["compared_with"], ["mosqito"])
        self.assertTrue(jl["implements"][0]["validation_details"])

    def test_validation_fields_are_checked(self) -> None:
        impl = self.index.project["kirin-hypha"]["implements"][0]
        saved = dict(impl)
        try:
            impl["compared_with"] = "mosqito"
            impl["validation_details"] = []
            problems = "\n".join(self.index.validate())
            self.assertIn("compared_with must be a non-empty list of strings", problems)
            self.assertIn("validation_details must be a non-empty list of strings", problems)
            impl["compared_with"] = ["kirin-hypha"]
            impl.pop("validation_details")
            self.assertIn("compared_with must name other implementations", "\n".join(self.index.validate()))
        finally:
            impl.clear()
            impl.update(saved)
        self.assertEqual(self.index.validate(), [])

    def test_edition_links_and_main_language(self) -> None:
        html = (self.site / "projects/psychoacousticmetrics-jl.html").read_text(encoding="utf-8")
        table = html[html.index('<h2 id="implements">'):html.index('<h2 id="validation">')]
        url = self.index.ref["din-45692-2009"]["url"]
        self.assertIn(f'<a href="{url}">DIN 45692:2009</a>', table, "the edition links to the standard")
        self.assertEqual(self.index.project["metasona"]["languages"][0], "C")
        home = (self.site / "index.html").read_text(encoding="utf-8")
        self.assertIn('<span class="lb lang-c" title="C">c</span><span class="nm"><a href="projects/metasona.html">',
                      home, "MetaSona is shown as C on the home page")
        page = (self.site / "projects/metasona.html").read_text(encoding="utf-8")
        self.assertIn('<span class="lang lang-c">C</span> <span class="lang lang-py">Python</span>', page)

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
