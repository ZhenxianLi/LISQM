"""Checks on the generated website: the data validates, every internal link resolves, every page has a
Markdown twin, structured data parses, and the README markers are intact."""

from __future__ import annotations

import contextlib
import html
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build  # noqa: E402
from pmi.data import GROUP_ORDER, KINDS, load, update_anchor  # noqa: E402
from pmi.describe import timeline  # noqa: E402
from pmi import relations as RL, render_html  # noqa: E402
from pmi.text import blocks  # noqa: E402
from pmi.render_html import LANG_CODES, _analytics  # noqa: E402


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

    def test_every_metric_and_project_has_a_page(self) -> None:
        for m in self.index.metrics:
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
        self.assertEqual(len(data["metrics"]), len(self.index.metrics))
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

        for m in self.index.metrics:
            self.assertEqual(ranks(m["_impls"]), sorted(ranks(m["_impls"])), m["id"])
        for _, rows in timeline(self.index):
            for row in rows:
                for cell in row["cells"]:
                    for ref, impls in cell:
                        self.assertEqual(ranks(impls), sorted(ranks(impls)), f"{row['metric']['id']} {ref['id']}")
        ordered = self.index.projects_by_group()
        self.assertEqual([p["_group"] for p in ordered], sorted((p["_group"] for p in ordered), key=GROUP_ORDER.get))
        tail = self.index.others() + self.index.group("unknown")
        self.assertEqual(ordered[-len(tail):], tail, "Others, then Status unknown, come last")
        supers = ["sqat", "mosqito", "sottek-hearing-model"]
        self.assertEqual([p["id"] for p in ordered[:len(supers)]], supers)
        self.assertEqual(self.index.group("newly-released")[0]["id"], "metasona")
        self.assertEqual([p["id"] for p in self.index.super_projects()], supers)

    def test_legacy_projects(self) -> None:
        legacy = {p["id"] for p in self.index.group("legacy")}
        self.assertIn("psychoacoustic-parameters-measurer", legacy)
        self.assertIn("python-acoustics", legacy, "archived projects are legacy")
        for p in self.index.projects:
            if p["_super"] or p["kind"] == "reference-program" or p["standing"] == "newly-released":
                self.assertNotIn(p["id"], legacy, "widely used projects and reference programs stay")
        self.assertEqual(self.index.project["mosqito"]["_group"], "established")
        html = (self.site / "projects" / "psychoacoustic-parameters-measurer.html").read_text(encoding="utf-8")
        self.assertIn("Legacy project.", html)
        home = (self.site / "index.html").read_text(encoding="utf-8")
        self.assertIn('<li class="quiet" title="PsychoacousticParametersMeasurer:', home)
        self.assertNotRegex(home, r'<li class="quiet" title="MoSQITo:')

    def test_others_are_not_listed_under_metrics(self) -> None:
        others = {p["id"] for p in self.index.others()}
        self.assertTrue({"psychobox", "soundscapy"} <= others)
        for m in self.index.metrics:
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
        self.assertEqual(len(marks), len(self.index.metrics) * 6)
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
            if p["standing"] != "newly-released" or p.get("access"):  # status unknown has its own notice
                continue
            text = (self.site / "projects" / f"{p['id']}.html").read_text(encoding="utf-8")
            self.assertIn("not yet seen to be widely used", text.lower(), p["id"])

    def test_home_page_opens_with_the_timeline(self) -> None:
        html = (self.site / "index.html").read_text(encoding="utf-8")
        body = html[html.index("<main"):]
        self.assertTrue(body[body.index("<h2"):].startswith('<h2 id="timeline">'), "the first section is not the timeline")
        self.assertLess(body.index('<table class="timeline">'), body.index('id="gaps"'))
        for m in self.index.metrics:
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
                       if row["metric"]["id"] == "loudness-zwicker")
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
        self.assertIn('also compared with <a href="../projects/mosqito.html"><strong>MoSQITo</strong></a>', section)
        self.assertIn('reference code: <a href="../projects/sqat.html"><strong>SQAT</strong></a>', section)
        self.assertIn('compared with <a href="../projects/sqat.html"><strong>SQAT</strong></a></span>', section)
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
        page = (self.site / "metrics/sharpness.html").read_text(encoding="utf-8")
        self.assertIn('<h2 id="validation">How they were validated</h2>', page)
        self.assertIn('href="#v-kirin-hypha-din-45692-2009"', page)
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

    def test_super_projects_are_bold_and_first_everywhere(self) -> None:
        supers = [p["id"] for p in self.index.super_projects()]
        self.assertEqual(supers, ["sqat", "mosqito", "sottek-hearing-model"])
        link = re.compile(r'<a href="(?:\.\./)*projects/([a-z0-9-]+)\.html"[^>]*>(<strong>)?')

        def ids(html: str) -> list[str]:
            return list(dict.fromkeys(pid for pid, _ in link.findall(html)))

        def first(found: list[str], where: str) -> None:
            flags = [pid in supers for pid in found]
            self.assertEqual(flags, sorted(flags, reverse=True), f"{where}: super projects first in {found}")

        def rows(html: str) -> list[str]:  # the first project of each table row
            return [found[0] for row in re.findall(r"<tr>(.*?)</tr>", html, re.S) if (found := ids(row))]

        for page in self.pages:
            html = page.read_text(encoding="utf-8")
            where = str(page.relative_to(self.site))
            for pid, strong in link.findall(html):
                self.assertEqual(bool(strong), pid in supers, f"{where}: {pid} bold only if a super project")
            for table in re.findall(r'<table class="grid ([a-z]+)"[^>]*>(.*?)</table>', html, re.S):
                for cell in re.findall(r"<td[^>]*>(.*?)</td>", table[1], re.S):
                    first(ids(cell), f"{where} {table[0]} cell")
                if table[0] in ("projects", "impls", "langs"):  # one project per row
                    first(rows(table[1]), f"{where} {table[0]} table")
            for block in re.findall(r'<div class="edition[^"]*">(.*?)</div>', html, re.S):
                first(ids(block), f"{where} timeline")
            for block in re.findall(r'<ul class="by-lang">(.*?)</ul>', html, re.S):
                for item in re.findall(r"<li>(.*?)</li>", block, re.S):
                    first(ids(item), f"{where} in short")
            for block in re.findall(r'<p class="older">(.*?)</p>', html, re.S):
                first(ids(block), f"{where} older editions")
            for block in re.findall(r'<dl class="(?:validation on-metric|conventions)">(.*?)</dl>', html, re.S):
                first([found[0] for dt in re.findall(r"<dt[^>]*>(.*?)</dt>", block, re.S) if (found := ids(dt))],
                      f"{where} details")
            for side in re.findall(r'<aside class="sidebar"[^>]*>(.*?)</aside>', html, re.S):
                for block in re.findall(r"<ul>(.*?)</ul>", side, re.S):
                    first(ids(block), f"{where} sidebar")
        # The Markdown versions, llms.txt and the README use bold for the same projects.
        md_link = re.compile(r"(\*\*)?\[([^\]]+)\]\([^)]*?projects/([a-z0-9-]+)\.(?:html|md)\)")
        texts = [page.with_suffix(".md") for page in self.pages if page.name != "404.html"]
        texts += [self.site / "llms.txt", self.site / "llms-full.txt", ROOT / "README.md"]
        for path in texts:
            for stars, text, pid in md_link.findall(path.read_text(encoding="utf-8")):
                # Project pages only (not the project map), and not file names given as examples ("projects/sqat.md").
                if pid in self.index.project and text == self.index.project[pid]["name"]:
                    self.assertEqual(bool(stars), pid in supers, f"{path.name}: {pid} bold only if a super project")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        table = readme[readme.index("BEGIN GENERATED: projects"):readme.index("END GENERATED: projects")]
        self.assertEqual(re.findall(r"^\| \*\*\[([^\]]+)\]", table, re.M),
                         [p["name"] for p in self.index.super_projects()], "README: super projects first, in bold")
        data = json.loads((self.site / "index.json").read_text(encoding="utf-8"))
        self.assertEqual([p["id"] for p in data["projects"] if p.get("highlight")], supers)

    def test_highlights_and_kinds(self) -> None:
        def page(pid: str) -> str:
            return re.sub(r"\s+", " ", (self.site / "projects" / f"{pid}.html").read_text(encoding="utf-8"))
        self.assertIn("A widely used project.", page("sqat"))
        self.assertIn("A widely used project.", page("mosqito"))
        self.assertIn("A very good implementation.", page("sottek-hearing-model"))
        for pid in ("amt", "ita-toolbox"):  # widely used toolboxes, not in bold
            self.assertFalse(self.index.project[pid]["_super"], pid)
            self.assertRegex(page(pid), r"A widely used toolbox for [^<]* that also includes some psychoacoustic "
                                        r"functions\.", pid)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("| established, widely used |", readme)
        self.assertIn("| established, a very good implementation |", readme)
        about = (self.site / "about.html").read_text(encoding="utf-8")
        self.assertIn("SQAT and MoSQITo (widely used), and sottek-hearing-model (a very good implementation)", about)
        for kind, meaning in KINDS.items():  # every kind is used and explained
            self.assertIn(html.escape(meaning, quote=False), about, kind)
            self.assertTrue(any(p["kind"] == kind for p in self.index.projects), f"kind {kind} is not used")
        self.assertIn(html.escape(KINDS["library"], quote=False), page("sqat"))
        self.assertIn("<td>Library/Toolbox<br>", page("sqat"), "MATLAB toolboxes and Python packages share a kind")

    def test_the_super_project_tag_is_not_published(self) -> None:
        # super_project is the maintainer's display setting: only its effect (bold, first) is shown, and no page
        # calls a project "the most widely used".
        outputs = [path for path in sorted(self.site.rglob("*")) if path.suffix in (".html", ".md", ".txt", ".json",
                                                                                   ".xml", ".bib")]
        outputs += [ROOT / "README.md", ROOT / "CHANGELOG.md"]
        for path in outputs:
            text = path.read_text(encoding="utf-8").lower()
            self.assertNotRegex(text, r"super[ _-]?projects?\b", f"{path.name} names the super_project tag")
            self.assertNotIn("most widely used", text, path.name)
            self.assertNotIn("most_widely_used", text, path.name)

    def test_dark_mode_switch(self) -> None:
        light = not self.index.site.get("dark_mode")
        for page in self.pages:  # dark_mode: false puts every page in the light version
            self.assertEqual('<html lang="en" data-theme="light">' in page.read_text(encoding="utf-8"), light,
                             page.name)

    def test_analytics_only_with_a_token(self) -> None:
        self.assertEqual(_analytics({}), "")
        token = "0123456789abcdef0123456789abcdef"
        snippet = _analytics({"cloudflare_analytics_token": token})
        self.assertEqual(snippet, '<script type="module" src="https://static.cloudflareinsights.com/beacon.min.js" '
                                  f'data-cf-beacon=\'{{"token": "{token}"}}\'></script>\n')
        self.assertEqual(_analytics({"cloudflare_analytics_token": "x\" onload=\"alert(1)"}), "")
        configured = bool(self.index.site.get("cloudflare_analytics_token"))
        for page in self.pages:  # on every page, or on none
            self.assertEqual("cloudflareinsights" in page.read_text(encoding="utf-8"), configured, page.name)

    def test_a_super_project_must_be_established(self) -> None:
        p = self.index.project["metasona"]
        p["super_project"] = 9
        try:
            problems = "\n".join(self.index.validate())
        finally:
            p.pop("super_project")
        self.assertIn("a super project must be established", problems)
        self.assertIn("a super project needs a highlight", problems)
        self.assertIn("a super project is ordered by super_project; remove rank", problems)

    def test_ports_and_related_comparisons(self) -> None:
        kirin = (self.site / "projects/kirin-hypha.html").read_text(encoding="utf-8")
        self.assertIn('compared with <a href="../projects/mosqito.html"><strong>MoSQITo</strong></a> (its source)',
                      kirin)
        self.assertIn('class="tag tag-neutral"', kirin, "a comparison only with its source is grey")
        self.assertIn("Ported or adapted from", kirin)
        pysqat = (self.site / "projects/pysqat.html").read_text(encoding="utf-8")
        self.assertIn("(also ported from ", pysqat, "pySQAT's ECMA-418-2 rows and SQAT share RefMap's code")
        zwicker = (self.site / "metrics/loudness-zwicker.html").read_text(encoding="utf-8")
        self.assertIn('<h2 id="map">Project map</h2>', zwicker)
        self.assertIn('The <a href="#map">project map</a> below shows which project took code from which.', zwicker)
        if shutil.which("dot"):
            picture = zwicker[zwicker.index('<svg class="map-graph"'):]
            picture = picture[:picture.index("</svg>")]
            self.assertIn("<title>Project map for Zwicker loudness</title>", picture)
            self.assertIn("Code taken: MoSQITo to Kirin Hypha, for ISO 532&#45;1:2017", picture)  # Graphviz escapes -
            self.assertIn("BASIC program (DIN 45631, 1991)", picture)
        data = json.loads((self.site / "index.json").read_text(encoding="utf-8"))
        rows = [i for m in data["metrics"] for i in m["implementations"] if i["project"] == "kirin-hypha"]
        self.assertEqual(rows[0]["comparison_relations"], {"mosqito": "source"})
        refmap = self.index.project["refmap-psychoacoustics"]
        self.assertFalse(any(f.startswith("shm_") for i in refmap["implements"] for f in i.get("functions") or []),
                         "RefMap's Python functions use sottek-hearing-model and are listed there")

    def test_conventions_citation_and_bibtex(self) -> None:
        zwicker = (self.site / "metrics/loudness-zwicker.html").read_text(encoding="utf-8")
        section = zwicker[zwicker.index('<h2 id="conventions">'):zwicker.index('<h2 id="references">')]
        self.assertIn("Sample rate.", section)
        self.assertIn("What the projects state:", section)
        self.assertIn("projects/metasona.html", section)
        sqat = (self.site / "projects/sqat.html").read_text(encoding="utf-8")
        self.assertIn('<th scope="row">How to cite</th>', sqat)
        self.assertIn("https://doi.org/10.5281/zenodo.7934709", sqat)
        net = (self.site / "projects/mosqito-net.html").read_text(encoding="utf-8")
        self.assertIn("The project does not say how to cite it", net)
        bib = (self.site / "references.bib").read_text(encoding="utf-8")
        self.assertEqual(bib.count("{"), bib.count("}"))
        for key in ("@techreport{iso-532-1-2017,", "@article{moore-1997,", "@book{zwicker-fastl-1999,",
                    "@phdthesis{widmann-1992,", "@inproceedings{sqat-paper,"):
            self.assertIn(key, bib)
        self.assertEqual(len(re.findall(r"^@\w+\{", bib, re.M)),
                         len(self.index.references) + len(re.findall(r"^% The paper describing", bib, re.M)))
        standards = (self.site / "standards.html").read_text(encoding="utf-8")
        self.assertIn('href="references.bib"', standards)

    def test_status_unknown(self) -> None:
        self.assertEqual([p["id"] for p in self.index.group("unknown")], ["psytools"])
        page = (self.site / "projects/psytools.html").read_text(encoding="utf-8")
        self.assertIn("<strong>Status unknown.</strong>", page)
        self.assertNotIn("Newly released project.", page)
        projects = (self.site / "projects/index.html").read_text(encoding="utf-8")
        self.assertLess(projects.index('id="others"'), projects.index('id="unknown"'))
        for m in self.index.metrics:
            html = (self.site / "metrics" / f"{m['id']}.html").read_text(encoding="utf-8")
            self.assertNotIn("projects/psytools.html", html, m["id"])

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

    def test_licences_of_the_list(self) -> None:
        cc = "https://creativecommons.org/licenses/by/4.0/"
        about = (self.site / "about.html").read_text(encoding="utf-8")
        self.assertIn(f'<a href="{cc}">CC BY 4.0</a>', about)
        self.assertIn("MIT licence</a>", about)
        home = (self.site / "index.html").read_text(encoding="utf-8")
        self.assertIn(f'Data and text: <a href="{cc}">CC BY 4.0</a>; code: ', home)
        self.assertIn(f'"license": "{cc}"', home, "the Dataset in the structured data")
        data = json.loads((self.site / "index.json").read_text(encoding="utf-8"))
        self.assertEqual((data["license"], data["license_url"], data["code_license"]), ("CC-BY-4.0", cc, "MIT"))
        self.assertIn("CC BY 4.0", (self.site / "about.md").read_text(encoding="utf-8"))
        self.assertIn("Creative Commons Attribution 4.0 International", (ROOT / "LICENSE-DATA").read_text(encoding="utf-8"))
        self.assertTrue((ROOT / "LICENSE").read_text(encoding="utf-8").startswith("MIT License"))
        self.assertIn("license: CC-BY-4.0", (ROOT / "CITATION.cff").read_text(encoding="utf-8"))

    def test_project_map_relations(self) -> None:
        rel = RL.relations(self.index)
        kinds = {(line["source"], line["user"]): line["kind"] for line in RL.lines(self.index, rel)
                 if line["kind"] != "people"}
        # Code that its own author or team moved is drawn apart from code that someone else took.
        self.assertEqual(kinds[("refmap-psychoacoustics", "sqat")], "own")
        self.assertEqual(kinds[("fluctuation-strength-tue", "sqat")], "own")
        self.assertEqual(kinds[("psysound3", "aarae")], "own")
        self.assertEqual(kinds[("aarae", "sqat")], "port")
        self.assertEqual(kinds[("BASIC program of DIN 45631 (Zwicker et al., 1991)", "mosqito")], "port")
        # Sources stand on the left of every line, also for run-time use and comparisons.
        self.assertEqual(kinds[("mosqito", "psychobox")], "uses")
        self.assertEqual(kinds[("zwickerloudness-jl", "psychoacousticmetrics-jl")], "uses")
        self.assertEqual(kinds[("mosqito", "iso532-1-rs")], "compare")
        # A check points from the project to the one it checked its results against (A's results checked against B).
        edges = [e for e in RL.dot_source(self.index, rel, "projects/map.html", LANG_CODES).splitlines() if " -> " in e]
        self.assertTrue(edges)
        for edge in edges:
            self.assertEqual("dir=back" in edge, "style=dashed" in edge, edge)
        # Every line with a direction has ends of its own: no two lines share the end of a box.
        tails, heads = [], []
        for edge in edges:
            source, user, attrs = re.match(r'\s*"((?:[^"\\]|\\.)*)" -> "((?:[^"\\]|\\.)*)" \[(.*)\];$', edge).groups()
            if "dir=none" not in attrs:
                tails.append((source, re.search(r'tailport="(o\d+):e"', attrs).group(1)))
                heads.append((user, re.search(r'headport="(i\d+):w"', attrs).group(1)))
        self.assertEqual(len(tails), len(set(tails)))
        self.assertEqual(len(heads), len(set(heads)))
        self.assertEqual(len(tails), sum(line["kind"] != "people" for line in RL.lines(self.index, rel)))
        # Code taken is not drawn again as a comparison. A shared contributor has a grey line of its own, also beside
        # a line of another kind, but not beside the author's own code, which says the same.
        self.assertEqual(kinds[("mosqito", "zwickerloudness-jl")], "port")
        by_pair: dict[frozenset, list[str]] = {}
        for line in RL.lines(self.index, rel):
            by_pair.setdefault(frozenset((line["source"], line["user"])), []).append(line["kind"])
        for pair, both in by_pair.items():
            self.assertTrue(len(both) == 1 or (len(both) == 2 and "people" in both and "own" not in both), pair)
        self.assertEqual(sorted(by_pair[frozenset(("mosqito", "mosqito-fdp"))]), ["people", "port"])
        self.assertEqual(by_pair[frozenset(("sqat", "sottek-hearing-model"))], ["people"], "Mike Lotinga")
        self.assertEqual(by_pair[frozenset(("refmap-psychoacoustics", "sqat"))], ["own"])
        self.assertEqual(by_pair[frozenset(("acoustic-toolbox", "soundscapy"))], ["people"])
        # A person on both sides of a code line is recorded on the rows, not guessed: at least one row of the pair
        # says derived_by_author (MoSQITo-FDP took its author's hearing model from MoSQITo, and others' TNR/PR code).
        for e in rel["taken"]:
            if e["shared"]:
                self.assertTrue(any(i.get("derived_by_author") for i in e["rows"]),
                                f"{e['key']} -> {e['project']['id']}: derived_by_author?")

    def test_project_map_page(self) -> None:
        page = (self.site / "projects/map.html").read_text(encoding="utf-8")
        self.assertIn("<h1>Project map</h1>", page)
        if shutil.which("dot"):
            self.assertIn('<svg class="map-graph"', page)
            self.assertIn('xlink:href="../projects/mosqito.html"', page)
            self.assertNotIn("<title>map</title>", page)
        self.assertIn("<h3>The author's own code</h3>", page)
        md = (self.site / "projects/map.md").read_text(encoding="utf-8")
        self.assertIn("## Used at run time", md)
        self.assertIn("projects/map.html", (self.site / "sitemap.xml").read_text(encoding="utf-8"))
        self.assertIn("projects/map.md", (self.site / "llms.txt").read_text(encoding="utf-8"))
        for path in ("projects/index.html", "projects/sqat.html", "metrics/loudness-zwicker.html"):
            self.assertIn('href="../projects/map.html"', (self.site / path).read_text(encoding="utf-8"), path)
        # The map also opens the Projects page, and the sidebar lists the map page under All projects.
        projects = (self.site / "projects/index.html").read_text(encoding="utf-8")
        if shutil.which("dot"):
            self.assertLess(projects.index('<svg class="map-graph"'), projects.index("<h2 id="))
        self.assertIn('<a href="../projects/index.html">All projects</a></p><ul><li><a href="../projects/map.html" '
                      'aria-current="page">Project map</a></li></ul>', page)
        # The example of ported code on a metric page points to a page that has that section.
        example = re.search(r'href="\.\./(metrics/[a-z0-9-]+\.html)#map"', page).group(1)
        self.assertIn('<h2 id="map">', (self.site / example).read_text(encoding="utf-8"))
        self.assertIn("<h3>Same contributor</h3>", page)

    def test_project_map_without_graphviz(self) -> None:
        with mock.patch.object(RL.shutil, "which", return_value=None), mock.patch.dict(os.environ):
            os.environ.pop("CI", None)
            with contextlib.redirect_stdout(io.StringIO()):
                page = render_html.map_page(self.index)
            self.assertNotIn('<svg class="map-graph"', page)
            self.assertIn("Graphviz is missing", page)
            self.assertIn("<h3>Code taken from another project</h3>", page)
            os.environ["CI"] = "true"
            with self.assertRaises(SystemExit):
                render_html.map_page(self.index)

    def test_relation_fields_are_checked(self) -> None:
        sharpness = next(i for i in self.index.project["metasona"]["_impls"] if i["metric"] == "sharpness")
        self.assertEqual(sharpness["_derived_ids"], [], "an empty derived_from overrides based_on")
        p = self.index.project["kirin-hypha"]
        impl, saved = p["implements"][0], dict(p["implements"][0])
        try:
            impl["derived_by_author"] = "yes"
            impl["uses"] = ["kirin-hypha"]
            problems = "\n".join(self.index.validate())
            self.assertIn("derived_by_author can only be true", problems)
            self.assertIn("uses must name another project than itself", problems)
            impl["derived_by_author"] = True
            impl["derived_from"] = []
            impl["uses"] = ["no-such-project"]
            problems = "\n".join(self.index.validate())
            self.assertIn("derived_by_author needs the code it came from", problems)
            self.assertIn("uses must be a non-empty list of listed project ids", problems)
            impl.clear()
            impl.update(saved)
            p["contributors"] = list(p["maintainers"])
            self.assertIn("contributors repeats a name from maintainers", "\n".join(self.index.validate()))
            del p["contributors"]
            p["id"] = "map"
            self.assertIn("the id 'map' is reserved", "\n".join(self.index.validate()))
        finally:
            p["id"] = "kirin-hypha"
            impl.clear()
            impl.update(saved)
        self.assertEqual(self.index.validate(), [])

    def test_metric_maps(self) -> None:
        def lines(mid: str) -> dict:
            rel = RL.relations(self.index, self.index.metric[mid])
            return {(line["source"], line["user"]): line for line in RL.lines(self.index, rel)
                    if line["kind"] != "people"}
        # A metric page draws only the lines of its own rows, each naming the edition it is about: SQAT took AARAE's
        # ISO 532-1 code, while AARAE's code from PsySound3 is for Chalupper & Fastl (2002).
        zwicker = lines("loudness-zwicker")
        self.assertTrue(zwicker[("aarae", "sqat")]["tip"].endswith("for ISO 532-1:2017"))
        self.assertTrue(zwicker[("psysound3", "aarae")]["tip"].endswith("for Chalupper & Fastl (2002)"))
        # MoSQITo-FDP took its author's own hearing model from MoSQITo, but someone else's TNR/PR code.
        self.assertEqual(lines("loudness-ecma-418-2")[("mosqito", "mosqito-fdp")]["kind"], "own")
        self.assertEqual(lines("tone-to-noise-prominence-ratio")[("mosqito", "mosqito-fdp")]["kind"], "port")
        # A metric without any recorded relation has no map; the Markdown twin lists the lines in words.
        aural = (self.site / "metrics/aural-detectability.html").read_text(encoding="utf-8")
        self.assertNotIn('<h2 id="map">', aural)
        self.assertNotIn("Who ported code from whom", aural)
        md = (self.site / "metrics/loudness-zwicker.md").read_text(encoding="utf-8")
        self.assertIn("## Project map", md)
        self.assertIn("- From [AARAE](https://zhenxianli.github.io/LISQM/projects/aarae.html): "
                      "**[SQAT](https://zhenxianli.github.io/LISQM/projects/sqat.html)** (ISO 532-1:2017)", md)

    def test_data_texts_are_whole(self) -> None:
        # In YAML, " #" in an unquoted text starts a comment and ": " makes a mapping: both once cut a sentence.
        self.assertTrue(self.index.project["mosqito"]["caveats"][0].endswith("low-pass filter (#92, #95)."))
        phonometry = (self.site / "projects/phonometry.html").read_text(encoding="utf-8")
        self.assertIn("Not implemented: Daniel &amp; Weber roughness", phonometry)
        p = self.index.project["kirin-hypha"]
        saved = p.get("caveats")
        try:
            p["caveats"] = ["Bug reports on TNR/PR (", {"Not implemented": "Aures tonality"}]
            problems = "\n".join(self.index.validate())
            self.assertIn("every item of caveats must be text", problems)
            self.assertIn("unbalanced brackets", problems)
        finally:
            if saved is None:
                del p["caveats"]
            else:
                p["caveats"] = saved
        self.assertEqual(self.index.validate(), [])

    def test_update_anchors_are_unique(self) -> None:
        anchors = [update_anchor(u) for u in self.index.updates]
        self.assertEqual(len(anchors), len(set(anchors)), "two updates of one day share an anchor")
        self.assertLessEqual(set(anchors), self.parse(self.site / "updates.html").ids)
        ids = re.findall(r"<id>([^<]+)</id>", (self.site / "feed.xml").read_text(encoding="utf-8"))
        self.assertEqual(len(ids), len(set(ids)), "feed entries need their own ids")
        self.index.updates.append(dict(self.index.updates[0]))
        try:
            self.assertIn("another update has the same date and title", "\n".join(self.index.validate()))
        finally:
            self.index.updates.pop()

    def test_sidebars_list_each_section_once(self) -> None:
        def side(page: str) -> str:
            text = (self.site / page).read_text(encoding="utf-8")
            text = text[text.index('<aside class="sidebar"'):]
            return text[:text.index("</aside>")]
        about = (self.site / "about.html").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r'href="#([^"]+)"', side("about.html")), re.findall(r'<h2 id="([^"]+)"', about))
        labels = re.findall(r">([^<>]+)</a>", side("standards.html"))
        self.assertEqual(len(labels), len(set(labels)), "a document used by two metrics is listed once")
        # A group with one metric of the same name is one heading, linking to the metric.
        self.assertIn('<p class="side-family"><a href="../metrics/sharpness.html" aria-current="page">Sharpness',
                      side("metrics/sharpness.html"))
        self.assertIn("<h1>Frequently asked questions</h1>", (self.site / "faq.html").read_text(encoding="utf-8"))

    def test_states_are_kept_in_every_list(self) -> None:
        # A row that is not released, or computes only part of a metric, is marked wherever its project is named.
        home = (self.site / "index.html").read_text(encoding="utf-8")
        for p in self.index.projects:
            if not p.get("_release"):
                self.assertNotRegex(home, rf'title="{re.escape(html.escape(p["name"]))}: [^"]*released in',
                                    p["id"])
        self.assertIn("; on the default branch, no release;", home)
        llms = (self.site / "llms.txt").read_text(encoding="utf-8")
        self.assertRegex(llms, r"Tonality, Aures/Terhardt model\]\([^)]+\): [^\n]*MoSQITo \(PR\)")
        projects = (self.site / "projects/index.html").read_text(encoding="utf-8")
        mosqito = projects[projects.index('<td data-label="Project"><a href="../projects/mosqito.html"'):]
        mosqito = mosqito[:mosqito.index("</tr>")]
        self.assertRegex(mosqito, r'tonality-aures\.html">[^<]+</a> <span class="tag[^"]*"[^>]*>PR<')
        self.assertIn("(PR)", (self.site / "projects/index.md").read_text(encoding="utf-8"))
        # Zhen-Ni computes PNL and PNLT only: listed with a tag, not counted as an EPNL implementation.
        zhen = self.index.project["zhen-ni-epnl"]["_impls"][0]
        self.assertTrue(zhen["partial"])
        self.assertNotIn(zhen, self.index.metric["epnl"]["_current_impls"])
        for _, rows in timeline(self.index):
            for row in rows:
                for cell in row["cells"]:
                    for _, impls in cell:
                        self.assertNotIn(zhen, impls)
        epnl = (self.site / "metrics/epnl.html").read_text(encoding="utf-8")
        self.assertIn(">partial<", epnl)
        self.assertIn("For the following metrics, the only released implementations of the current edition come "
                      "from newly released projects", home)

    def test_conventions_of_other_metrics_stay_on_the_project_page(self) -> None:
        epnl = (self.site / "metrics/epnl.html").read_text(encoding="utf-8")
        self.assertNotIn("time_skip", epnl, "SQAT's statistics are for other metrics")
        roughness = (self.site / "metrics/roughness-ecma-418-2.html").read_text(encoding="utf-8")
        self.assertIn("at least 320 ms", roughness)
        self.assertNotIn("at least 304 ms", roughness)
        self.assertIn("at least 304 ms", (self.site / "projects/sqat.html").read_text(encoding="utf-8"))
        impl = self.index.project["mosqito-net"]["implements"][0]
        conventions = self.index.project["mosqito-net"]["conventions"]
        saved = list(conventions)
        try:
            conventions[0] = {"text": "Resamples to 48 kHz.", "metrics": ["epnl"]}
            self.assertIn("conventions must be", "\n".join(self.index.validate()), impl["metric"])
        finally:
            conventions[:] = saved
        self.assertEqual(self.index.validate(), [])
        words = (self.site / "projects/map.html").read_text(encoding="utf-8")
        self.assertIn('Left out, as their code could not be opened: <a href="../projects/psytools.html">PsyTools',
                      words)

    def test_standards_in_force_look_current(self) -> None:
        # A national standard in force (DIN 45631, ANSI S3.4, NT ACOU 112) has its own scope beside the ISO one: it
        # is current on the timeline too, although the metric names one edition to follow.
        home = (self.site / "index.html").read_text(encoding="utf-8")
        for rid in ("din-45631-a1-2010", "ansi-s3-4-2007", "nt-acou-112-2002"):
            ref = self.index.ref[rid]
            self.assertEqual(ref["status"], "current", rid)
            title = html.escape(f'{ref["title"]}. Current.')
            self.assertIn(f'<div class="edition ed-current"><span class="ed-label" title="{title}">', home, rid)
        self.assertNotIn("not the current edition", home)

    def test_one_vocabulary_and_one_name(self) -> None:
        # Code not in a release is "unreleased", an open pull request "PR" (the owner's choice), on every page.
        for page in self.pages:
            text = page.read_text(encoding="utf-8")
            self.assertNotRegex(text, r'class="tag [^"]*"[^>]*>(main|proposed)<', page.name)
        self.assertIn(">unreleased</span>", (self.site / "index.html").read_text(encoding="utf-8"))
        self.assertIn(">PR</a>", (self.site / "metrics/tonality-aures.html").read_text(encoding="utf-8"))
        self.assertIn(">PR</span> open pull request", (self.site / "metrics/index.html").read_text(encoding="utf-8"))
        # A project has one name, the same in the sidebar, the timeline, the map and its own page.
        amt = self.index.project["amt"]
        self.assertEqual((amt["name"], amt["full_name"]), ("AMT", "Auditory Modeling Toolbox"))
        page = (self.site / "projects/amt.html").read_text(encoding="utf-8")
        self.assertIn("<h1>AMT</h1>", page)
        self.assertIn("<td>Auditory Modeling Toolbox</td>", page)
        self.assertIn('"alternateName": "Auditory Modeling Toolbox"', page)
        projects = (self.site / "projects/index.html").read_text(encoding="utf-8")
        for pid in ("refmap-psychoacoustics", "zhen-ni-epnl", "rapid-loudness-sharpness"):
            name = html.escape(self.index.project[pid]["name"], quote=False)
            self.assertIn(f'<a href="../projects/{pid}.html">{name}</a>', projects, pid)
        svg = (self.site / "projects/map.html").read_text(encoding="utf-8")
        self.assertIn(">refmap&#45;psychoacoustics</text>", svg, "Graphviz writes - as &#45;")
        p = self.index.project["amt"]
        try:
            p["short_name"] = "AMT"
            p["full_name"] = "AMT"
            problems = "\n".join(self.index.validate())
            self.assertIn("short_name is no longer used", problems)
            self.assertIn("full_name must be a longer title than name", problems)
        finally:
            del p["short_name"]
            p["full_name"] = "Auditory Modeling Toolbox"
        self.assertEqual(self.index.validate(), [])
        # N5 is a value taken from Zwicker loudness, not another name for it.
        zwicker = self.index.metric["loudness-zwicker"]
        self.assertNotIn("N5", zwicker["aka"])
        self.assertIn("N5, the loudness exceeded 5 % of the time", " ".join(zwicker["summary"].split()))

    def test_validation_scope_is_shown_with_the_evidence(self) -> None:
        page = (self.site / "metrics/loudness-zwicker.html").read_text(encoding="utf-8")
        self.assertIn('standard or paper data</a><br><span class="small muted">(in v1.3, test signal 10 is off by '
                      '18.14 %)</span>', page)
        self.assertIn('standard or paper data</span> <span class="muted">(outcome not stated)</span>', page)
        md = (self.site / "metrics/loudness-ecma-418-2.md").read_text(encoding="utf-8")
        self.assertIn("standard or paper data (calibration signal only; outside the allowed adjustment)", md)
        impl = self.index.project["sqat"]["implements"][0]
        try:
            impl["validation_scope"] = "x" * 61
            self.assertIn("validation_scope must be a few words", "\n".join(self.index.validate()))
        finally:
            impl["validation_scope"] = "in v1.3, test signal 10 is off by 18.14 %"
        self.assertEqual(self.index.validate(), [])

    def test_licence_flags_where_projects_are_compared(self) -> None:
        def notes(page: str, pid: str, edition: str) -> str:
            text = (self.site / page).read_text(encoding="utf-8")
            table = text[text.index('<h2 id="implementations">'):text.index('<h2 id="validation">')]
            for row in table.split("<tr>")[1:]:
                if f'projects/{pid}.html"' in row and f">{edition}</a>" in row:
                    return row
            self.fail(f"{pid} {edition} not in {page}")
        # No licence file, a non-commercial or a source-available licence is tagged on the metric pages; SQAT's
        # releases are non-commercial, while its default branch is under the GPL.
        self.assertIn(">no licence<", notes("metrics/loudness-moore-glasberg-time-varying.html", "js2251-iso532-3",
                                            "ISO 532-3:2023"))
        self.assertIn(">source-available<", notes("metrics/loudness-zwicker.html", "soundpalette", "ISO 532-1:2017"))
        ecma = "metrics/loudness-ecma-418-2.html"
        self.assertIn(">non-commercial<", notes(ecma, "sqat", "ECMA-418-2:2024 (3rd ed.)"))
        self.assertNotIn(">non-commercial<", notes(ecma, "sqat", "ECMA-418-2:2025 (4th ed.)"))
        languages = (self.site / "languages.html").read_text(encoding="utf-8")
        self.assertRegex(languages, r'projects/soundpalette\.html">SoundPalette</a> <span class="tag tag-new"[^>]*>new'
                                    r'</span> <span class="tag tag-neutral"[^>]*>source-available<')
        self.assertIn("(newly released, source-available)", (self.site / "languages.md").read_text(encoding="utf-8"))
        # The project's own page gives the licence once, in its facts.
        self.assertNotIn(">non-commercial<", (self.site / "projects/sqat.html").read_text(encoding="utf-8"))

    def test_metric_groups_and_authority_reports(self) -> None:
        self.assertIn("Four models are standardised", " ".join(self.index.family["loudness"]["summary"].split()))
        faq = (self.site / "faq.html").read_text(encoding="utf-8")
        self.assertIn("Being listed here is not a certification or an approval", faq)
        # A question of its own, after the others: the first answer stays as it is.
        self.assertIn('<h2 id="q1">Which code should I use for a psychoacoustic metric?</h2>', faq)
        self.assertIn('<h2 id="q7">Can I rely on a listed implementation in a report that an authority will check?'
                      "</h2>", faq)

    def test_owner_texts_are_kept(self) -> None:
        # Texts written or dictated by the owner (docs/maintaining/owner-decisions.md) change only when the owner
        # asks; update this test together with that table.
        def text(page: str) -> str:
            plain = re.sub(r"<[^>]+>", "", (self.site / page).read_text(encoding="utf-8"))
            return " ".join(html.unescape(plain).split())
        self.assertIn("Find an open-source method to calculate psychoacoustic metrics such as loudness, sharpness, "
                      "roughness and tonality, one that you can trust and that best fits your coding environment, "
                      "whether Python, MATLAB, C/C++, Rust, Julia or another language. Each implementation is listed "
                      "under the edition of the standard or model it follows, with the validation it reports, so that "
                      "you can judge whether its results are credible.", text("index.html"))
        self.assertIn("This page is for AI agents, crawlers and LLMs that read the list on someone's behalf. Humans "
                      "are welcome too: it lists the same data in forms that are easy to retrieve, parse and quote.",
                      text("ai.html"))
        about = text("about.html")
        for key in ("about_lead", "about_story"):
            first = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", self.index.site[key]).split(". ")[0]
            self.assertIn(" ".join(first.split()), about, key)
        self.assertIn("is renewed monthly", about)
        faq = text("faq.html")
        self.assertIn("MetaSona is a C library written for fast, real-time analysis, with a rolling analyser for audio "
                      "that arrives in chunks", faq)
        self.assertIn("pySQAT ports SQAT to Python", faq)
        self.assertNotIn("Kirin Hypha is", faq)
        for name in ("README.md", "review-issue.md", "pages.md", "repository.md", "owner-decisions.md"):
            self.assertTrue((ROOT / "docs" / "maintaining" / name).exists(), name)
        self.assertIn("docs/maintaining/owner-decisions.md", (ROOT / "AGENTS.md").read_text(encoding="utf-8"))

    def test_bullets_may_wrap(self) -> None:
        self.assertEqual(blocks("Intro.\n\n- One item\n  that wraps.\n- Two."),
                         "<p>Intro.</p>\n<ul><li>One item that wraps.</li><li>Two.</li></ul>")
        updates = (self.site / "updates.html").read_text(encoding="utf-8")
        self.assertNotIn("<p>- ", updates, "every bullet list of the updates is a list")

    def test_phone_layout_hooks(self) -> None:
        # On phones, rows of these tables become blocks labelled with their column names; the labels and the
        # phone-only hint are invisible on wider screens.
        projects = (self.site / "projects/index.html").read_text(encoding="utf-8")
        self.assertIn('<td data-label="Licence">', projects)
        self.assertIn('class="empty" data-label=', (self.site / "projects/sqat.html").read_text(encoding="utf-8"))
        self.assertIn('class="small muted phone-only"', (self.site / "projects/map.html").read_text(encoding="utf-8"))
        css = (self.site / "style.css").read_text(encoding="utf-8")
        narrow = css[css.index("@media (max-width: 40rem)"):]
        self.assertIn(".phone-only {\n  display: none;", css[:css.index("@media (max-width: 40rem)")])
        self.assertIn("content: attr(data-label);", narrow)

    def test_search(self) -> None:
        import hashlib
        # search.json holds every kind, every metric and project, and only entries that lead to a page and an anchor
        # that exist.
        entries = json.loads((self.site / "search.json").read_text(encoding="utf-8"))
        self.assertEqual({e["k"] for e in entries}, {"Metric", "Standard", "Paper", "Project", "Function", "Page"})
        names = {(e["k"], e["t"]) for e in entries}
        for m in self.index.metrics:
            self.assertIn(("Metric", m["name"]), names)
        for p in self.index.projects:
            self.assertIn(("Project", p["name"]), names)
        self.assertIn(("Page", "Frequently asked questions"), names)
        anchors: dict[Path, set[str]] = {}
        for e in entries:
            target, _, fragment = e["u"].partition("#")
            path = self.site / target
            self.assertTrue(path.is_file(), e["u"])
            if fragment:
                self.assertIn(fragment, anchors.setdefault(path, self.parse(path).ids), e["u"])
        old = {e["t"] for e in entries if e.get("old")}
        self.assertTrue(old and all(r["status"] in ("superseded", "withdrawn") for r in self.index.references
                                    if r["label"] in old))
        # Every page but the error page has the field, the button and the dialog, and asks for search.js by its
        # version, with the way back to the root of the site.
        version = hashlib.sha256((self.site / "search.js").read_bytes()).hexdigest()[:10]
        for page in self.pages:
            text = page.read_text(encoding="utf-8")
            if page.name == "404.html":
                self.assertNotIn("search", text.lower().replace("research", ""), page.name)
                continue
            root = re.search(rf'search\.js\?v={version}" data-root="([./]*)" defer>', text)
            self.assertTrue(root, page.name)
            self.assertEqual((page.parent / root.group(1)).resolve(), self.site.resolve(), page.name)
            for hook in ('<form class="site-search" role="search">', '<button class="search-open" type="button">',
                         '<dialog class="search-dialog"'):
                self.assertEqual(text.count(hook), 1, f"{page.name}: {hook}")
            self.assertIn("document.documentElement.classList.add('js');", text, page.name)
        # The filter of the Projects page; nothing of the search shows without JavaScript.
        projects = (self.site / "projects/index.html").read_text(encoding="utf-8")
        self.assertLess(projects.index('<div class="table-filter">'), projects.index('<h2 id="established">'))
        self.assertIn('<label for="project-filter">Filter projects</label><input id="project-filter"', projects)
        css = (self.site / "style.css").read_text(encoding="utf-8")
        self.assertIn(".site-search,\n.search-open,\n.table-filter {\n  display: none;\n}", css)
        self.assertIn("table.projects tr[hidden]", css)

if __name__ == "__main__":
    unittest.main()
