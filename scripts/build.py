#!/usr/bin/env python3
"""Validate the index data and generate the website, README tables and machine-readable files.

    python scripts/build.py            # validate, then write site/ and the generated files in the repo
    python scripts/build.py --check    # validate only (exit code 1 on problems)

Inputs:  data/*.yaml, data/projects/*.yaml, data/snapshot.json, site-src/ (stylesheet, icon), assets/
Outputs: site/ (HTML pages with Markdown twins, index.json, llms.txt, llms-full.txt, feed.xml, sitemap.xml)
         README.md and README.zh-CN.md (between GENERATED markers), CHANGELOG.md, llms.txt, llms-full.txt,
         data/index.json
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pmi import export, render_html, render_md  # noqa: E402
from pmi.data import ROOT, DataError, load  # noqa: E402
from pmi.paths import (ABOUT, AI, FAQ, HOME, LANGUAGES, METRICS, PROJECTS, STANDARDS, UPDATES, md_twin,  # noqa: E402
                       method_path, project_path)


def write(path: Path, text: str) -> bool:
    """Write text if it changed; return True when the file was (re)written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def replace_blocks(text: str, blocks: dict[str, str], name: str) -> str:
    for key, content in blocks.items():
        pattern = re.compile(rf"(<!-- BEGIN GENERATED: {key} -->).*?(<!-- END GENERATED: {key} -->)", re.S)
        if not pattern.search(text):
            raise SystemExit(f"{name}: missing '<!-- BEGIN GENERATED: {key} -->' / END marker pair")
        text = pattern.sub(lambda m: f"{m.group(1)}\n{content.strip()}\n{m.group(2)}", text)
    return text


def build_site(index, out: Path) -> int:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for src in (ROOT / "site-src").iterdir():
        if src.is_file():
            shutil.copy2(src, out / src.name)
    preview = ROOT / "assets" / "social-preview.png"
    if preview.exists():
        shutil.copy2(preview, out / "social-preview.png")

    pages = {
        HOME: (render_html.home(index), render_md.home(index)),
        METRICS: (render_html.metrics_page(index), render_md.metrics_page(index)),
        PROJECTS: (render_html.projects_page(index), render_md.projects_page(index)),
        LANGUAGES: (render_html.languages_page(index), render_md.languages_page(index)),
        STANDARDS: (render_html.standards_page(index), render_md.standards_page(index)),
        UPDATES: (render_html.updates_page(index), render_md.updates_page(index)),
        ABOUT: (render_html.about_page(index), render_md.about_page(index)),
        FAQ: (render_html.faq_page(index), render_md.faq_page(index)),
        AI: (render_html.ai_page(index), render_md.ai_page(index)),
    }
    for m in index.methods:
        pages[method_path(m)] = (render_html.method_page(index, m), render_md.method_page(index, m))
    for p in index.projects:
        pages[project_path(p)] = (render_html.project_page(index, p), render_md.project_page(index, p))
    for path, (html_text, md_text) in pages.items():
        write(out / path, html_text)
        write(out / md_twin(path), md_text)
    write(out / "404.html", render_html.not_found(index))

    write(out / "llms.txt", render_md.llms_txt(index))
    write(out / "llms-full.txt", render_md.llms_full(index))
    write(out / "index.json", export.index_json(index))
    write(out / "feed.xml", export.atom_feed(index))
    write(out / "sitemap.xml", export.sitemap(index))
    write(out / "robots.txt", export.robots(index))
    write(out / ".nojekyll", "")
    return len(pages)


def make_preview(out: Path) -> None:
    """Adapt a built site for hosts that only allow inline styles and wrap the main page themselves
    (used for private previews): inline the stylesheet everywhere and strip the document shell of index.html."""
    css = (out / "style.css").read_text(encoding="utf-8")
    link = re.compile(r'<link rel="stylesheet" href="[^"]*style\.css">')
    for page in out.rglob("*.html"):
        text = link.sub(lambda _: f"<style>\n{css}</style>", page.read_text(encoding="utf-8"))
        if page == out / "index.html":
            title = re.search(r"<title>.*?</title>", text, re.S).group(0)
            style = re.search(r"<style>.*?</style>", text, re.S).group(0)
            body = re.search(r"<body>(.*)</body>", text, re.S).group(1)
            text = f"{title}\n{style}\n{body.strip()}\n"
        page.write_text(text, encoding="utf-8")


def build_repo_files(index) -> list[str]:
    changed = []
    for name, lang in (("README.md", "en"), ("README.zh-CN.md", "zh")):
        path = ROOT / name
        if not path.exists():
            continue
        text = replace_blocks(path.read_text(encoding="utf-8"), {
            "stats": render_md.readme_stats(index, lang),
            "overview": render_md.readme_overview(index, lang),
            "gaps": render_md.readme_gaps(index, lang),
            "coverage": render_md.coverage_table(index, lang),
            "projects": render_md.readme_projects(index, lang),
        }, name)
        if write(path, text):
            changed.append(name)
    for name, text in (("CHANGELOG.md", render_md.changelog(index)),
                       ("llms.txt", render_md.llms_txt(index)),
                       ("llms-full.txt", render_md.llms_full(index)),
                       ("data/index.json", export.index_json(index))):
        if write(ROOT / name, text):
            changed.append(name)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="validate the data only")
    parser.add_argument("--out", type=Path, default=ROOT / "site", help="output directory for the website")
    parser.add_argument("--preview", action="store_true",
                        help="inline the stylesheet and strip the main page's document shell (for preview hosts)")
    args = parser.parse_args()

    try:
        index = load()
    except DataError as err:
        print(f"{len(err.problems)} problem(s) in data/:", file=sys.stderr)
        for problem in err.problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    summary = (f"{len(index.methods)} methods, {len(index.references)} references, "
               f"{len(index.projects)} projects, data as of {index.as_of()}")
    if args.check:
        print(f"Data OK: {summary}")
        return 0
    pages = build_site(index, args.out)
    if args.preview:
        make_preview(args.out)
    changed = build_repo_files(index)
    print(f"Built {pages} pages into {args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) else args.out} "
          f"({summary})")
    print("Updated: " + (", ".join(changed) if changed else "no repository files changed"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
