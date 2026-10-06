"""Markdown output: a .md twin of every page, llms.txt, llms-full.txt, README tables and CHANGELOG.md.

Links point to absolute URLs of the HTML pages, so the text stays useful when it is copied or quoted.
"""

from __future__ import annotations

from .data import IMPL_STATUS_LONG, PROJECT_KINDS, REGISTRIES, VALIDATION, VALIDATION_LONG, Index
from .describe import (COVERAGE_COLUMNS, activity_text, by_language, coverage, dedupe, faq, in_short,
                       ref_status, release_text)
from .paths import ABOUT, FAQ, HOME, PROJECTS, STANDARDS, UPDATES, absolute, md_twin, method_path, project_path
from .text import join_words, long_date, month, oneline, plain, plural

FAMILY_ZH = {
    "loudness": "响度", "sharpness": "尖锐度", "roughness": "粗糙度", "fluctuation-strength": "波动强度",
    "tonality": "音调性", "impulsiveness": "冲击性", "annoyance": "烦恼度", "related": "相关指标",
}


def _plain(text: str) -> str:
    return text


def _namer(index: Index):
    return lambda p: f"[{p['name']}]({absolute(index, project_path(p))})"


def _method_link(index: Index, m: dict, label: str | None = None) -> str:
    return f"[{label or m['name']}]({absolute(index, method_path(m))})"


def _ref_link(r: dict) -> str:
    url = r.get("url") or (f"https://doi.org/{r['doi']}" if r.get("doi") else "")
    return f"[{r['label']}]({url})" if url else r["label"]


def _header(index: Index, path: str) -> str:
    site = index.site
    return (f"> Part of the [{site['title']}]({site['base_url']}), an index of open-source implementations of "
            f"psychoacoustic metrics. Data as of {index.as_of()}. Web page: {absolute(index, path)}")


def _table(head: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(oneline(c) or "—" for c in row) + " |" for row in rows]
    return out


def _impl_note(i: dict) -> str:
    bits = []
    if i["status"] != "available":
        bits.append(i["status"].capitalize() + (f" ({i['link']})" if i.get("link") else "") + ".")
    if i.get("note"):
        bits.append(i["note"].strip())
    return " ".join(bits)


def _edition(i: dict) -> str:
    extra = ([i["scope"]] if i.get("scope") else []) + ([f"since {i['since']}"] if i.get("since") else [])
    return i["_ref"]["label"] + (f" ({'; '.join(extra)})" if extra else "")


def _functions(i: dict) -> str:
    return ", ".join(f"`{f}`" for f in i.get("functions") or [])


def _reference_list(refs: list[dict]) -> list[str]:
    out = []
    for n, r in enumerate(refs, 1):
        text = r.get("citation") or f"{r['label']}. {r['title']}."
        link = r.get("url") or (f"https://doi.org/{r['doi']}" if r.get("doi") else "")
        out.append(f"{n}. {text}" + (f" {link}" if link and link not in text else ""))
    return out


# ---------------------------------------------------------------------------------------------- pages

def method_page(index: Index, m: dict) -> str:
    name = _namer(index)
    fam = m["_family"]
    lines = [f"# {m['title']}", "", _header(index, method_path(m)), ""]
    facts = [f"**Quantity:** {fam['name']}", f"**Unit:** {m['unit']}"]
    if m.get("aka"):
        facts.append(f"**Also known as:** {', '.join(m['aka'])}")
    lines += [" · ".join(facts), "", m["summary"].strip(), "",
              "**In short.** " + in_short(index, m, name, _plain), ""]
    if m.get("notes"):
        lines += [m["notes"].strip(), ""]

    lines += ["## Editions and who implements them", ""]
    rows = []
    for rid in reversed(m["references"]):
        r = index.ref[rid]
        impls = dedupe([i for i in m["_impls"] if i["reference"] == rid])
        who = ", ".join(name(i["_project"]) + ("" if i["status"] == "available" else f" ({i['status']})")
                        for i in impls)
        status = ref_status(r) + (f"; {r['revision']}" if r.get("revision") else "")
        rows.append([month(r.get("date")) or "—", _ref_link(r), status,
                     (m.get("edition_notes") or {}).get(rid, ""), who])
    lines += _table(["Date", "Edition", "Status", "What changed", "Implemented by"], rows) + [""]

    lines += ["## Implementations", ""]
    if m["_impls"]:
        rows = [[name(i["_project"]), ", ".join(i["_project"]["languages"]), _edition(i), _functions(i),
                 VALIDATION[i["validation"]], _impl_note(i)] for i in m["_impls"]]
        lines += _table(["Project", "Language", "Edition", "Functions", "Validation (as stated)", "Notes"], rows)
    else:
        lines.append("No open-source implementation has been found yet. "
                     f"If you know one, please [open an issue]({index.site['repository']}/issues/new/choose).")
    lines += [""]
    if m.get("see_also"):
        lines += ["**See also:** " + ", ".join(_method_link(index, index.method[s], index.method[s]["title"])
                                              for s in m["see_also"]), ""]
    lines += ["## References", ""] + _reference_list([index.ref[r] for r in m["references"]]) + [""]
    return "\n".join(lines)


def project_page(index: Index, p: dict) -> str:
    lines = [f"# {p['name']}", "", _header(index, project_path(p)), "", p["summary"].strip(), ""]
    facts = [("Repository", p["repository"])]
    for key, label in (("homepage", "Homepage"), ("docs", "Documentation")):
        if p.get(key):
            facts.append((label, p[key]))
    facts += [("Language", ", ".join(p["languages"])), ("Kind", PROJECT_KINDS[p["kind"]]),
              ("Licence", p["license"] + (f" — {plain(p['license_note'])}" if p.get("license_note") else ""))]
    for pkg in p.get("packages") or []:
        reg, tmpl = REGISTRIES[pkg["registry"]]
        url = pkg.get("url") or (tmpl.format(name=pkg["name"]) if tmpl else "")
        facts.append(("Package", f"{reg} `{pkg['name']}`" + (f" ({url})" if url else "")))
    if p.get("install"):
        facts.append(("Install", f"`{p['install']}`"))
    rel = release_text(p)
    if p.get("_prerelease"):
        pr = p["_prerelease"]
        rel += f"; pre-release {pr.get('version')} ({month(pr.get('date'))})"
    facts += [("Latest release", rel),
              ("Last commit", (p["_last_commit"] or "unknown") + f" ({activity_text(p)})")]
    if p.get("_stars") is not None:
        facts.append(("GitHub stars", str(p["_stars"])))
    if p.get("maintainers"):
        facts.append(("Maintainers", ", ".join(p["maintainers"])))
    facts.append(("AI assistance", "disclosed" + (f" — {p['ai_note']}" if p.get("ai_note") else "")
                  if p["ai_assistance"] == "disclosed" else "not stated"))
    if p.get("paper"):
        facts.append(("Paper", p["paper"]["citation"] + (f" https://doi.org/{p['paper']['doi']}"
                                                         if p["paper"].get("doi") else "")))
    facts.append(("Entry checked", str(p["checked"])))
    lines += [f"- **{k}:** {v}" for k, v in facts] + [""]

    lines += ["## What it implements", ""]
    rows = [[_method_link(index, i["_method"]), _edition(i), _functions(i), i["status"], VALIDATION[i["validation"]],
             (i.get("note") or "").strip()] for i in p["_impls"]]
    lines += _table(["Metric", "Edition", "Functions", "Status", "Validation (as stated)", "Notes"], rows) + [""]
    if p.get("notes"):
        lines += ["## Notes", ""] + [f"- {oneline(n)}" for n in p["notes"]] + [""]
    if p.get("caveats"):
        lines += ["## Before you rely on it", ""] + [f"- {oneline(c)}" for c in p["caveats"]] + [""]
    lines += ["## Sources", ""] + [f"- {s}" for s in p["sources"]] + [""]
    return "\n".join(lines)


def overview_rows(index: Index, link_methods: bool = True) -> list[list[str]]:
    name = _namer(index)
    rows = []
    for fam, methods in index.families_with_methods():
        for m in methods:
            groups = by_language(m["_current_impls"], name)
            cell = " · ".join(f"{lang}: {', '.join(names)}" for lang, names in groups) or "none found"
            older = dedupe(m["_older_impls"])
            if older:
                cell += " · earlier editions: " + ", ".join(
                    f"{name(i['_project'])} ({i['_ref']['label']})" for i in older
                    if i["_ref"]["status"] != "in-development")
            rows.append([fam["name"], _method_link(index, m) if link_methods else m["name"],
                         join_words([index.ref[r]["label"] for r in m["current"]]), cell])
    return rows


COVERAGE_MARK = {"current": "●", "partial": "○", "": "—"}


def coverage_table(index: Index, lang: str = "en") -> str:
    cols = [c for c, _ in COVERAGE_COLUMNS] + ["Other"]
    head = (["方法"] if lang == "zh" else ["Method"]) + (cols if lang != "zh" else cols[:-1] + ["其它"])
    rows = []
    for m in index.methods:
        cov = coverage(m)
        label = m.get("name_zh") if lang == "zh" and m.get("name_zh") else m["name"]
        rows.append([_method_link(index, m, label)] + [COVERAGE_MARK[cov[c]] for c in cols])
    legend = ("● 现行版本有可用实现；○ 只有未发布、待合并或旧版本的实现；— 没有找到。含绑定接口：带 Python 接口的 C 库也算 Python。"
              if lang == "zh" else
              "● an available implementation of the current edition; ○ only unreleased, proposed or "
              "older-edition implementations; — none found. Bindings count: a C library with a Python interface "
              "counts for Python.")
    return "\n".join(_table(head, rows)) + "\n\n" + legend


def home(index: Index) -> str:
    site = index.site
    lines = ["# Open-source implementations of psychoacoustic metrics", "", _header(index, HOME), "",
             site["description"].strip(), "",
             f"{plural(len(index.methods), 'method')} · {plural(len(index.projects), 'project')} · "
             f"languages: {', '.join(index.languages())}", ""]
    lines += ["## Overview", ""]
    lines += _table(["Quantity", "Method", "Current edition", "Implementations of the current edition"],
                    overview_rows(index)) + [""]
    lines += ["## Coverage by language", "", coverage_table(index), ""]
    gaps = index.gaps()
    if gaps:
        lines += ["## Gaps", "", "No available open-source implementation of the current edition was found for:", ""]
        lines += [f"- {_method_link(index, m, m['title'])}" for m in gaps] + [""]
    if index.updates:
        lines += ["## Recent updates", ""]
        for u in index.updates[:3]:
            first_paragraph = u["body"].strip().split("\n\n")[0]
            lines += [f"- **{u['date']}: {u['title']}.** {plain(first_paragraph)}"]
        lines += [""]
    return "\n".join(lines)


def projects_page(index: Index) -> str:
    lines = ["# Projects", "", _header(index, PROJECTS), "",
             f"{plural(len(index.projects), 'project')}, grouped by the language you call them from. "
             "A project that offers several languages appears in each group.", ""]
    for lang in index.languages():
        projects = [p for p in index.projects if lang in p["languages"]]
        lines += [f"## {lang}", ""]
        rows = [[f"[{p['name']}]({absolute(index, project_path(p))})", PROJECT_KINDS[p["kind"]], p["license"],
                 release_text(p), p["_last_commit"] or "unknown", activity_text(p),
                 ", ".join(sorted({i["_method"]["name"] for i in p["_impls"]}))]
                for p in sorted(projects, key=lambda p: p["name"].lower())]
        lines += _table(["Project", "Kind", "Licence", "Latest release", "Last commit", "Activity", "Covers"],
                        rows) + [""]
    return "\n".join(lines)


def standards_page(index: Index) -> str:
    lines = ["# Standards and models", "", _header(index, STANDARDS), "",
             "Every document the index refers to, newest first. Each implementation in the index is tied to "
             "one of these editions.", ""]
    docs = [r for r in index.references if r["kind"] not in ("paper", "book", "thesis")]
    papers = [r for r in index.references if r["kind"] in ("paper", "book", "thesis")]
    for title, refs in (("Standards and regulations", docs), ("Model papers, books and theses", papers)):
        lines += [f"## {title}", ""]
        rows = []
        for r in sorted(refs, key=lambda r: (str(r.get("date") or "9999"), r["label"]), reverse=True):
            rows.append([month(r.get("date")) or "—", _ref_link(r), plain(r["title"]), ref_status(r),
                         ", ".join(_method_link(index, m) for m in r["_methods"])])
        lines += _table(["Date", "Document", "Title", "Status", "Used by"], rows) + [""]
    return "\n".join(lines)


def updates_page(index: Index) -> str:
    lines = ["# Updates", "", _header(index, UPDATES), ""]
    for u in index.updates:
        lines += [f"## {long_date(u['date'])}: {u['title']}", "", u["body"].strip(), ""]
    return "\n".join(lines)


def about_page(index: Index) -> str:
    site = index.site
    lines = ["# About this index", "", _header(index, ABOUT), "", site["description"].strip(), ""]
    lines += ["## What is included", "",
              "Open-source code that computes a psychoacoustic metric and says which model or standard edition "
              "it follows. Quantities: " + join_words([f["name"].lower() for f in index.families]) + ". "
              "Not included: LUFS / ITU-R BS.1770, speech intelligibility, codec quality metrics (PEAQ, PESQ, "
              "ViSQOL), psychophysics experiment software, music sensory-dissonance models, feature extractors "
              "whose loudness or sharpness follow no named psychoacoustic model, and closed-source tools. The ISO "
              "532 reference programs (free to download, not modifiable) are described on the standards' entries. "
              f"Reviewed exclusions are listed with reasons in {site['repository']}/blob/main/data/ignored.yaml.", ""]
    lines += ["## How entries are checked", "",
              "Each entry is written from the project's own README, documentation, release notes, licence file "
              "and package metadata, with links to those sources. The index records what a project claims; it "
              "does not run the code. Repository dates, releases and package versions are refreshed every week "
              "by a GitHub Action, which also searches for new candidate projects and watches the standards "
              "bodies for new editions. A person reviews the findings before anything is added.", ""]
    lines += ["## Status of an implementation", ""]
    lines += _table(["Value", "Meaning"], [[k, v] for k, v in IMPL_STATUS_LONG.items()]) + [""]
    lines += ["## Validation evidence", "", "As stated by each project:", ""]
    lines += _table(["Value", "Meaning"], [[VALIDATION[k], v] for k, v in VALIDATION_LONG.items()]) + [""]
    lines += ["## Leads not yet verified", "",
              "Candidates that may belong in the index but could not be checked yet; nothing here has been confirmed.", ""]
    lines += [f"- [{l['name']}]({l['url']}) ({', '.join(l.get('languages') or [])}): {oneline(l['claim'])} {oneline(l['why'])}"
              for l in index.leads] + [""]
    lines += ["Not indexed because they are closed source: MATLAB Audio Toolbox, HEAD acoustics ArtemiS SUITE, "
              "Simcenter Testlab, HBK BK Connect and Ansys Sound.", ""]
    lines += ["## Machine-readable data", "",
              f"- [index.json]({site['base_url']}index.json): the whole index as JSON",
              f"- [llms.txt]({site['base_url']}llms.txt) and [llms-full.txt]({site['base_url']}llms-full.txt): "
              "summaries for language models",
              f"- [feed.xml]({site['base_url']}feed.xml): Atom feed of updates",
              f"- Source data and schema: {site['repository']}/tree/main/data", ""]
    lines += ["## Contributing and citing", "",
              f"Corrections and new projects are welcome through issues or pull requests: {site['repository']}. "
              f"To cite the index, use the CITATION.cff file in the repository. Maintained by "
              f"{site['maintainer']['name']}. Licence: {site['license']}.", ""]
    return "\n".join(lines)


def faq_page(index: Index) -> str:
    lines = ["# Frequently asked questions", "", _header(index, FAQ), ""]
    for q, a in faq(index, _namer(index), lambda m: _method_link(index, m, m["title"]), _plain):
        lines += [f"## {q}", "", a, ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------- LLM files

def llms_txt(index: Index) -> str:
    site = index.site
    lines = [f"# {site['title']}", "", f"> {plain(site['description'])}", "",
             f"Data as of {index.as_of()}. {plural(len(index.methods), 'method')}, "
             f"{plural(len(index.projects), 'project')}, languages: {', '.join(index.languages())}. Each "
             "implementation is tied to the standard edition or model paper it follows, with its validation "
             "evidence as stated by the project. Repository and package metadata are refreshed weekly.", ""]
    for fam, methods in index.families_with_methods():
        lines += [f"## {fam['name']}", ""]
        for m in methods:
            current = join_words([index.ref[r]["label"] for r in m["current"]])
            projects = ", ".join(dict.fromkeys(i["_project"]["name"] for i in m["_current_impls"])) or "none found"
            lines.append(f"- [{m['title']}]({site['base_url']}{md_twin(method_path(m))}): current edition "
                         f"{current}; implementations: {projects}")
        lines.append("")
    lines += ["## Projects", ""]
    for p in sorted(index.projects, key=lambda p: p["name"].lower()):
        lines.append(f"- [{p['name']}]({site['base_url']}{md_twin(project_path(p))}): "
                     f"{', '.join(p['languages'])}; {plain(p['summary']).split('. ')[0].rstrip('.')}.")
    lines += ["", "## Data", "",
              f"- [index.json]({site['base_url']}index.json): the complete index as JSON",
              f"- [llms-full.txt]({site['base_url']}llms-full.txt): all pages in one Markdown file",
              f"- [Data schema]({site['repository']}/blob/main/data/SCHEMA.md)", "",
              "## Optional", "",
              f"- [Frequently asked questions]({site['base_url']}{md_twin(FAQ)})",
              f"- [About and method]({site['base_url']}{md_twin(ABOUT)})",
              f"- [Standards timeline]({site['base_url']}{md_twin(STANDARDS)})",
              f"- [Updates]({site['base_url']}{md_twin(UPDATES)})",
              f"- [Source repository]({site['repository']})", ""]
    return "\n".join(lines)


def llms_full(index: Index) -> str:
    parts = [llms_txt(index), "", "---", "", about_page(index), "", "---", "", faq_page(index)]
    for m in index.methods:
        parts += ["", "---", "", method_page(index, m)]
    for p in sorted(index.projects, key=lambda p: p["name"].lower()):
        parts += ["", "---", "", project_page(index, p)]
    parts += ["", "---", "", standards_page(index)]
    return "\n".join(parts).rstrip() + "\n"


# ---------------------------------------------------------------------------------------------- README

def readme_overview(index: Index, lang: str = "en") -> str:
    rows = overview_rows(index)
    if lang == "zh":
        for row, (fam, m) in zip(rows, [(f, m) for f, ms in index.families_with_methods() for m in ms]):
            row[0] = FAMILY_ZH.get(fam["id"], fam["name"])
            if m.get("name_zh"):
                row[1] = _method_link(index, m, m["name_zh"])
        head = ["类别", "方法", "现行版本", "已有的开源实现（按语言）"]
    else:
        head = ["Quantity", "Method", "Current edition", "Open-source implementations (by language)"]
    return "\n".join(_table(head, rows))


def readme_projects(index: Index, lang: str = "en") -> str:
    head = (["项目", "语言", "许可证", "最新发布", "最近提交", "状态"] if lang == "zh"
            else ["Project", "Language", "Licence", "Latest release", "Last commit", "Activity"])
    rows = [[f"[{p['name']}]({p['repository']})", ", ".join(p["languages"]), p["license"], release_text(p),
             p["_last_commit"] or "unknown", activity_text(p)]
            for p in sorted(index.projects, key=lambda p: p["name"].lower())]
    return "\n".join(_table(head, rows))


def readme_gaps(index: Index, lang: str = "en") -> str:
    gaps = index.gaps()
    if not gaps:
        return "无。" if lang == "zh" else "None at the moment."
    return "\n".join(f"- {_method_link(index, m, m.get('name_zh') if lang == 'zh' and m.get('name_zh') else m['title'])}"
                     for m in gaps)


def readme_stats(index: Index, lang: str = "en") -> str:
    if lang == "zh":
        return (f"数据截至 {index.as_of()}：{len(index.methods)} 个方法，{len(index.projects)} 个项目，"
                f"语言包括 {', '.join(index.languages())}。")
    return (f"Data as of {index.as_of()}: {plural(len(index.methods), 'method')}, "
            f"{plural(len(index.projects), 'project')}, languages: {', '.join(index.languages())}.")


def changelog(index: Index) -> str:
    lines = ["# Changelog", "",
             "Notable changes to the index. This file is generated from `data/updates.yaml`; the same notes are "
             f"on the website ({absolute(index, UPDATES)}) and in its Atom feed.", ""]
    for u in index.updates:
        lines += [f"## {u['date']}: {u['title']}", "", u["body"].strip(), ""]
    return "\n".join(lines)
