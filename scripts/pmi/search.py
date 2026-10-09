"""search.json: what the search of the website looks through, built from the data with the site.

One entry per metric, standard, paper, project, function name and page section: its kind (`k`), name (`t`), page
(`u`, relative to the site root), a line under the name (`s`), and other words that should find it (`x`: other
names, designations, summaries of metrics, languages and their codes, the maintainers named on a project's page).
Projects also carry their language code (`lang`, `cls`), their group tag (`tag`) and whether they are shown in bold
(`bold`); superseded and withdrawn editions are marked `old` and come after current ones. site-src/search.js reads
it.
"""

from __future__ import annotations

import json
import re

from .data import Index
from .describe import faq
from .paths import ABOUT, AI, FAQ, HOME, LANGUAGES, MAP, METRICS, PROJECTS, STANDARDS, UPDATES, metric_path, \
    project_path

PAPERS = ("paper", "book", "thesis")
GROUP_TAG = {"newly-released": "new", "developing": "dev", "legacy": "legacy"}


def search_index(index: Index, lang_codes: dict, about_sections: list, language_sections: list) -> str:
    entries: list[dict] = []

    def add(kind: str, title: str, url: str, sub: str = "", words=(), **extra) -> None:
        entries.append({"k": kind, "t": title, "u": url, "s": sub,
                        "x": " ".join(dict.fromkeys(str(w) for w in words if w)), **extra})

    for m in index.metrics:
        current = ", ".join(index.ref[r]["label"] for r in m["current"])
        add("Metric", m["name"], metric_path(m), f"{m['unit']} · current: {current}",
            [m["title"], *(m.get("aka") or []), m["_family"].get("name"), m["unit"],
             *[index.ref[r]["label"] for r in m["references"]], m["summary"]])
    for r in index.references:
        status = {"in-development": "in development"}.get(r["status"], r["status"])
        add("Paper" if r["kind"] in PAPERS else "Standard", r["label"], f"{STANDARDS}#ref-{r['id']}",
            f"{' '.join(r['title'].split())} · {status}"[:120],
            [r["title"], r.get("body"), *[m["name"] for m in r["_metrics"]]],
            **({"old": True} if r["status"] in ("superseded", "withdrawn") else {}))
    for p in index.projects_by_group():
        code, cls = lang_codes.get(p["languages"][0], (p["languages"][0][:2].lower(), "other"))
        first = re.split(r"(?<=\.)\s", " ".join(p["summary"].split()))[0]
        extra = {"lang": code, "cls": cls}
        if GROUP_TAG.get(p["_group"]):
            extra["tag"] = GROUP_TAG[p["_group"]]
        if p.get("_super"):
            extra["bold"] = True
        codes = [lang_codes.get(lang, (lang[:2].lower(), ""))[0] for lang in p["languages"]]
        add("Project", p["name"], project_path(p), first[:110],
            [p.get("full_name"), p["id"], *p["languages"], *codes, *(p.get("maintainers") or [])], **extra)
    seen = set()
    for p in index.projects_by_group():
        for i in p["_impls"]:
            for f in i.get("functions") or []:
                if (f, p["id"]) not in seen:
                    seen.add((f, p["id"]))
                    add("Function", f, f"{metric_path(i['_metric'])}#implementations",
                        f"{p['name']} · {i['_metric']['name']}", [p["name"]])
    # The tabs, with the words of the tab bar, and some sections.
    pages = [("Metrics", METRICS, ""), ("Projects", PROJECTS, ""), ("Languages", LANGUAGES, ""),
             ("Standards and models", STANDARDS, "Standards references.bib BibTeX"),
             ("Frequently asked questions", FAQ, "FAQ"), ("Updates", UPDATES, "changelog feed"),
             ("For AI agents and language models", AI, "For AI llms.txt index.json"), ("About LISQM", ABOUT, "About"),
             ("Editions and implementations (timeline)", f"{HOME}#timeline", ""), ("Gaps", f"{HOME}#gaps", ""),
             ("Project map", MAP, "relations"), ("Ask a question or leave a message", f"{FAQ}#message", "")]
    listed = [p for p in index.projects_by_group() if p["_group"] not in ("others", "unknown")]
    pages += [(title, f"{LANGUAGES}#{anchor}", "") for anchor, title, langs in language_sections
              if any(langs & set(p["languages"]) for p in listed)]  # a language without projects has no section
    pages += [(title, f"{ABOUT}#{anchor}", "") for anchor, title in about_sections]
    questions = faq(index, lambda p: p["name"], lambda m: m["name"], str, lambda path, label: label)
    pages += [(question, f"{FAQ}#q{n}", "") for n, (question, _) in enumerate(questions, 1)]
    for title, url, words in pages:
        add("Page", title, url, words=[words])
    return json.dumps(entries, ensure_ascii=False, separators=(",", ":"))
