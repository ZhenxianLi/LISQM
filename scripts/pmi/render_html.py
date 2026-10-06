"""HTML output: static, pre-rendered pages (no JavaScript needed) with Markdown twins and JSON-LD.

The layout follows academic software sites: a coloured masthead and tab bar over one fixed-width container,
a sidebar that lists every metric, gridded tables, and small coloured tags for languages and states.
"""

from __future__ import annotations

import json
import re

from .data import (IMPL_STATUS_LONG, PROJECT_KINDS, REGISTRIES, STANDING, VALIDATION, VALIDATION_LONG, Index,
                   only_new)
from .describe import (COVERAGE_COLUMNS, ONLY_NEW, activity_text, by_language, coverage, current_statement,
                       dedupe, edition_state, faq, impl_phrase, ref_status, release_text, standing_sentence,
                       time_bins, timeline, version_label)
from .paths import (ABOUT, FAQ, HOME, PROJECTS, STANDARDS, UPDATES, absolute, md_twin, method_path,
                    project_path, relative)
from .text import blocks, esc, inline, join_words, long_date, month, plain, plural

NAV = [("Metrics", HOME), ("Projects", PROJECTS), ("Standards", STANDARDS), ("FAQ", FAQ), ("Updates", UPDATES),
       ("About", ABOUT)]

# Language tags: a short code for the timeline, the full name in tables, and a colour class.
LANGUAGES = {"Python": ("Py", "py"), "MATLAB": ("M", "m"), "Octave": ("Oct", "m"), "C": ("C", "c"),
             "C++": ("C++", "c"), "C#": ("C#", "c"), "Rust": ("Rs", "rs"), "Julia": ("Jl", "jl"),
             "JavaScript": ("JS", "js"), "Pure Data": ("Pd", "pd"), "R": ("R", "r")}
VALIDATION_KIND = {"standard-data": "ok", "reference-code": "ok", "cross-implementation": "info",
                   "self-tests": "warn", "not-stated": "neutral"}
REF_KIND = {"current": "ok", "superseded": "neutral", "withdrawn": "neutral", "in-development": "warn",
            "published": "info"}
STANDING_KIND = {"established": "ok", "developing": "info", "new": "new"}
ACTIVITY_KIND = {"active": "ok", "inactive": "warn", "archived": "neutral", "unknown": "neutral"}
STANDING_HEADINGS = [("established", "Established projects"), ("developing", "Developing projects"),
                     ("new", "New projects")]


# ---------------------------------------------------------------------------------------------- layout

def layout(index: Index, path: str, *, title: str, description: str, body: str, section: str,
           jsonld: list[dict] | None = None, og_type: str = "website", markdown: bool = True,
           sidebar: bool = True) -> str:
    site = index.site
    rel = lambda target: relative(path, target)  # noqa: E731
    canonical = absolute(index, path)
    current = ' aria-current="page"'
    tabs = "\n".join(f'<a href="{rel(target)}"{current if label == section else ""}>{label}</a>'
                     for label, target in NAV)
    ld = ""
    if jsonld:
        payload = jsonld[0] if len(jsonld) == 1 else {"@context": "https://schema.org", "@graph": jsonld}
        if len(jsonld) == 1:
            payload = {"@context": "https://schema.org", **payload}
        ld = ('<script type="application/ld+json">\n'
              + json.dumps(payload, ensure_ascii=False, indent=1).replace("</", "<\\/") + "\n</script>\n")
    page_title = title if path == HOME else f"{title} · {site['title']}"
    md_head = (f'<link rel="alternate" type="text/markdown" href="{esc(rel(md_twin(path)))}" title="Markdown version">\n'
               if markdown else "")
    md_foot = f'<a href="{rel(md_twin(path))}">This page as Markdown</a> · ' if markdown else ""
    side = _sidebar(index, path) if sidebar else ""
    page_class = "page with-sidebar" if sidebar else "page"
    as_of = esc(long_date(index.as_of()))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(page_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
{md_head}<link rel="alternate" type="application/atom+xml" href="{esc(rel('feed.xml'))}" title="{esc(site['title'])}: updates">
<link rel="icon" href="{esc(rel('favicon.svg'))}" type="image/svg+xml">
<link rel="stylesheet" href="{esc(rel('style.css'))}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(site['title'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(site['base_url'])}social-preview.png">
<meta name="twitter:card" content="summary_large_image">
{ld}</head>
<body>
<a class="skip" href="#content">Skip to content</a>
<header class="masthead">
<div class="container masthead-row">
<a class="brand" href="{rel(HOME)}"><span class="brand-mark" aria-hidden="true">ψ</span><span class="brand-text"><span class="brand-name">{esc(site['title'])}</span><span class="brand-tagline">{esc(site.get('tagline', ''))}</span></span></a>
<p class="masthead-meta">Data as of {as_of}<br><a href="{esc(site['repository'])}">Source on GitHub</a></p>
</div>
<nav class="tabs" aria-label="Site"><div class="container">
{tabs}
</div></nav>
</header>
<div class="container {page_class}">
<main id="content">
{body}
</main>
{side}
</div>
<footer class="site-footer">
<div class="container">
<p class="credit">{credit(index)}</p>
<p>Facts are taken from each project's own documentation and package metadata and checked by hand; corrections
are welcome on <a href="{esc(site['repository'])}">GitHub</a>. Data as of {as_of}. {esc(site['license'])} licence.</p>
<p><a href="{rel('index.json')}">JSON</a> · <a href="{rel('llms.txt')}">llms.txt</a> · {md_foot}<a href="{rel('feed.xml')}">Atom feed</a></p>
</div>
</footer>
</body>
</html>
"""


def _sidebar(index: Index, path: str) -> str:
    """Every metric by family, then the index pages and the data files."""
    rel = lambda target: relative(path, target)  # noqa: E731
    here = lambda target: ' aria-current="page"' if target == path else ""  # noqa: E731
    parts = ['<aside class="sidebar" aria-label="All metrics and pages">', '<p class="side-head">Metrics</p>']
    for fam, methods in index.families_with_methods():
        parts.append(f'<p class="side-family"><a href="{rel(HOME)}#{esc(fam["id"])}">{esc(fam["name"])}</a></p>')
        parts.append("<ul>" + "".join(f'<li><a href="{rel(method_path(m))}"{here(method_path(m))}>'
                                      f'{esc(m["name"])}</a></li>' for m in methods) + "</ul>")
    pages = (("All projects", PROJECTS), ("Standards and models", STANDARDS), ("Questions and answers", FAQ),
             ("Updates", UPDATES), ("About and method", ABOUT))
    parts.append('<p class="side-head">Index</p>')
    parts.append("<ul>" + "".join(f'<li><a href="{rel(t)}"{here(t)}>{label}</a></li>' for label, t in pages) + "</ul>")
    parts.append('<p class="side-head">Data</p>')
    parts.append(f'<ul><li><a href="{rel("index.json")}">index.json</a></li>'
                 f'<li><a href="{rel("llms.txt")}">llms.txt</a></li>'
                 f'<li><a href="{rel("feed.xml")}">Atom feed</a></li>'
                 f'<li><a href="{esc(index.site["repository"])}">GitHub repository</a></li></ul>')
    parts.append("</aside>")
    return "\n".join(parts)


def credit(index: Index) -> str:
    """The project's credit line from data/site.yaml, verbatim, with the maintainer's name linked."""
    site = index.site
    name = esc(site["maintainer"]["name"])
    link = f'<a href="https://github.com/{esc(site["maintainer"]["github"])}">{name}</a>'
    return esc(site["credit"]).replace(name, link, 1)


# ---------------------------------------------------------------------------------------------- small parts

def _tag(text: str, kind: str, title: str = "", href: str = "") -> str:
    tip = f' title="{esc(title)}"' if title else ""
    if href:
        return f'<a class="tag tag-{kind}" href="{esc(href)}"{tip}>{esc(text)}</a>'
    return f'<span class="tag tag-{kind}"{tip}>{esc(text)}</span>'


def _lang_tag(lang: str, short: bool = False) -> str:
    code, cls = LANGUAGES.get(lang, (lang[:3], "other"))
    return f'<span class="lt lt-{cls}" title="{esc(lang)}">{esc(code if short else lang)}</span>'


def _langs(langs: list[str]) -> str:
    return " ".join(_lang_tag(lang) for lang in langs)


def _validation(i: dict) -> str:
    v = i["validation"]
    return _tag(VALIDATION[v], VALIDATION_KIND[v], VALIDATION_LONG[v])


def _ref_tag(r: dict) -> str:
    return _tag(ref_status(r), REF_KIND[r["status"]])


def _standing_tag(p: dict) -> str:
    label = "new, not yet widely used" if p["standing"] == "new" else p["standing"]
    return _tag(label, STANDING_KIND[p["standing"]], STANDING[p["standing"]])


def _activity_tag(p: dict) -> str:
    return _tag(activity_text(p), ACTIVITY_KIND.get(p["_activity"], "neutral"))


NEW_TAG = _tag("new", "new", STANDING["new"])


def _project_link(path: str, p: dict) -> str:
    return f'<a href="{relative(path, project_path(p))}">{esc(p["name"])}</a>'


def _method_link(path: str, m: dict, label: str | None = None) -> str:
    return f'<a href="{relative(path, method_path(m))}">{esc(label or m["name"])}</a>'


def _ref_link(r: dict) -> str:
    url = r.get("url") or (f"https://doi.org/{r['doi']}" if r.get("doi") else "")
    return f'<a href="{esc(url)}">{esc(r["label"])}</a>' if url else esc(r["label"])


def _functions(i: dict) -> str:
    return ", ".join(f"<code>{esc(f)}</code>" for f in i.get("functions") or [])


def _status_note(i: dict) -> str:
    """Notes cell: state tags first (new project, unreleased, pull request), then the free-text note."""
    bits = []
    if i["_project"]["standing"] == "new":
        bits.append(_tag("new project", "new", STANDING["new"]))
    if i["status"] == "unreleased":
        bits.append(_tag("unreleased", "warn", IMPL_STATUS_LONG["unreleased"], href=i.get("link", "")))
    elif i["status"] == "proposed":
        bits.append(_tag("pull request", "neutral", IMPL_STATUS_LONG["proposed"], href=i.get("link", "")))
    if i.get("_via"):
        bits.append(f'Computed by {esc(i["_via"]["name"])}.')
    if i.get("note"):
        bits.append(inline(i["note"]))
    return " ".join(bits)


def _edition_cell(i: dict) -> str:
    """Edition label with scope and first version underneath."""
    cell = esc(i["_ref"]["label"])
    extra = [esc(i["scope"])] if i.get("scope") else []
    if i.get("since"):
        extra.append(f"since {esc(i['since'])}")
    if extra:
        cell += f'<br><span class="muted">{"; ".join(extra)}</span>'
    return cell


def _table(cls: str, head: list[str], rows: list[list[str]], caption: str = "") -> str:
    """A gridded table; on narrow screens it scrolls sideways inside its own box."""
    cap = f"<caption>{caption}</caption>" if caption else ""
    thead = "".join(f'<th scope="col">{h}</th>' for h in head)
    body = "\n".join("<tr>" + "".join(f"<td>{c or '—'}</td>" for c in row) + "</tr>" for row in rows)
    return (f'<div class="table-wrap"><table class="grid {cls}">{cap}<thead><tr>{thead}</tr></thead>\n'
            f"<tbody>\n{body}\n</tbody></table></div>")


def _ref_list(refs: list[dict]) -> str:
    items = []
    for r in refs:
        link = r.get("url") or (f"https://doi.org/{r['doi']}" if r.get("doi") else "")
        text = inline(r["citation"]) if r.get("citation") else f"{esc(r['label'])}. {esc(r['title'])}."
        if link:
            text += f' <a href="{esc(link)}">{esc(link)}</a>'
        items.append(f'<li id="ref-{esc(r["id"])}">{text}</li>')
    return '<ol class="refs">\n' + "\n".join(items) + "\n</ol>"


def _software_ld(index: Index, p: dict) -> dict:
    d = {"@type": "SoftwareSourceCode", "name": p["name"], "codeRepository": p["repository"],
         "programmingLanguage": p["languages"], "description": plain(p["summary"]),
         "url": absolute(index, project_path(p))}
    if p["license"] not in ("none", "proprietary-free"):
        d["license"] = p["license"]
    if p.get("_last_commit"):
        d["dateModified"] = p["_last_commit"]
    if p.get("_release"):
        d["version"] = str(p["_release"]["version"])
    return d


def _crumbs(*links: str) -> str:
    return '<nav class="crumbs" aria-label="Breadcrumb">' + ' <span aria-hidden="true">›</span> '.join(links) + "</nav>"


# ---------------------------------------------------------------------------------------------- timeline

def _breakable(text: str) -> str:
    """Escape a name and allow line breaks inside long CamelCase words and after '+', '/' and '.'."""
    out = esc(text)
    out = re.sub(r"(?<=[a-z])(?=[A-Z])", "<wbr>", out)
    return re.sub(r"(?<=[+/.])(?=\w)", "<wbr>", out)


def _impl_tip(i: dict) -> str:
    p = i["_project"]
    tip = [", ".join(p["languages"]), {"available": "released" + (f" in {i['since']}" if i.get("since") else ""),
                                       "unreleased": "merged, not yet released",
                                       "proposed": "open pull request, not merged"}[i["status"]],
           activity_text(p)]
    if i.get("_via"):
        tip.append(f"computed by {i['_via']['name']}")
    if p["standing"] == "new":
        tip.append(standing_sentence(p))
    return p["name"] + ": " + "; ".join(tip)


def _timeline_impl(path: str, i: dict) -> str:
    """One project under an edition: language, name, the first release with that edition, and markers."""
    p = i["_project"]
    bits = [_lang_tag(p["languages"][0], short=True),
            f'<a href="{relative(path, project_path(p))}">{_breakable(p.get("short_name") or p["name"])}</a>']
    version = version_label(i)
    if i["status"] == "proposed":
        bits.append(_tag(version, "neutral", IMPL_STATUS_LONG["proposed"], href=i.get("link", "")))
    elif i["status"] == "unreleased":
        bits.append(_tag("unreleased", "warn", IMPL_STATUS_LONG["unreleased"]))
    elif version:
        bits.append(f'<span class="ver">{esc(version)}</span>')
    if i.get("_via"):
        bits.append(f'<span class="via">via {esc(i["_via"].get("short_name") or i["_via"]["name"])}</span>')
    quiet = ' class="quiet"' if p["_activity"] in ("inactive", "archived") else ""
    return f'<li{quiet} title="{esc(_impl_tip(i))}">{" ".join(bits)}</li>'


def _timeline_edition(path: str, m: dict, ref: dict, impls: list[dict]) -> str:
    state = edition_state(m, ref)
    tip = f'{ref["title"]}. {ref_status(ref).capitalize()}.'
    label = f'<span class="ed-label" title="{esc(tip)}">{_breakable(ref["label"])}</span>'
    if state == "dev":
        label += " " + _tag("in development", "warn")
    regular = [i for i in impls if i["_project"]["standing"] != "new"]
    new = [i for i in impls if i["_project"]["standing"] == "new"]
    items = "".join(_timeline_impl(path, i) for i in regular)
    if new:  # new projects come last, under their own marker
        items += f'<li class="new-head">{NEW_TAG}</li>' + "".join(_timeline_impl(path, i) for i in new)
    cls = f"edition ed-{state}" if state else "edition"
    return f'<div class="{cls}">{label}' + (f"<ul>{items}</ul>" if items else "") + "</div>"


def _timeline(index: Index, path: str) -> str:
    """The editions-by-implementations matrix that opens the home page."""
    bins = time_bins(index)
    head = ['<th scope="col" class="rowhead">Method</th>']
    for n, (label, _, _) in enumerate(bins):
        head.append(f'<th scope="col" class="now">{esc(label)}</th>' if n == len(bins) - 1
                    else f'<th scope="col">{esc(label)}</th>')
    groups = []
    for fam, rows in timeline(index):
        lines = [f'<tr class="family" id="{esc(fam["id"])}"><th scope="rowgroup" colspan="{len(bins) + 1}">'
                 f'<span>{esc(fam["name"])}</span></th></tr>']
        for row in rows:
            m = row["method"]
            cells = []
            for n, cell in enumerate(row["cells"]):
                cls = "bin life" if n >= row["first"] else "bin"
                cells.append(f'<td class="{cls}">' + "".join(_timeline_edition(path, m, ref, impls)
                                                            for ref, impls in cell) + "</td>")
            lines.append(f'<tr><th scope="row" class="rowhead">{_method_link(path, m)}'
                         f'<span class="unit">{esc(m["unit"])}</span></th>' + "".join(cells) + "</tr>")
        groups.append("<tbody>\n" + "\n".join(lines) + "\n</tbody>")
    key_langs = " ".join(f"{_lang_tag(lang, short=True)} {esc(label)}" for lang, label in (
        ("Python", "Python"), ("MATLAB", "MATLAB or Octave"), ("C++", "C or C++"), ("Rust", "Rust"),
        ("Julia", "Julia"), ("JavaScript", "JavaScript"), ("Pure Data", "Pure Data")))
    legend = (
        '<div class="legend">'
        '<p><span class="key key-current">ISO 532-1:2017</span> current edition '
        '<span class="key key-old">ISO 226:2003</span> superseded or withdrawn '
        f'{_tag("in development", "warn")} draft or new work item '
        '<span class="key key-life"></span> years since the method’s first edition</p>'
        f"<p>{key_langs}</p>"
        f"<p>{NEW_TAG} first released less than about a year ago and not yet widely used, always listed last · "
        f'{_tag("unreleased", "warn")} merged, not in a release yet · {_tag("PR #97", "neutral")} open pull request · '
        '<span class="ver">v1.0</span> first release with that edition · '
        '<span class="quiet-sample">grey name</span> no commit for more than a year, or archived</p>'
        "</div>")
    return "\n".join([
        '<section class="timeline-section" aria-labelledby="timeline">',
        '<h2 id="timeline">Editions and implementations</h2>',
        "<p>Each standard edition or model paper sits in the column of the year it appeared. Under it are the "
        "projects that implement it: widely used and established projects first, new projects last. Hover over a "
        "name for details; each method links to a page with function names and validation.</p>",
        legend,
        '<div class="table-wrap"><table class="timeline"><thead><tr>' + "".join(head) + "</tr></thead>\n"
        + "\n".join(groups) + "\n</table></div>",
        "</section>",
    ])


# ---------------------------------------------------------------------------------------------- pages

def home(index: Index) -> str:
    path = HOME
    site = index.site
    langs = index.languages()
    parts = [
        "<h1>Open-source implementations of psychoacoustic metrics</h1>",
        '<p class="lead">Which open-source code implements which edition of each psychoacoustic standard or model, '
        "in any programming language. Standards such as ECMA-418-2 and ISO 532 change between editions, so two "
        "tools that both say they implement a standard can give different results.</p>",
        f'<p class="meta-line">{plural(len(index.methods), "method")} · {plural(len(index.projects), "project")} · '
        f'{plural(len(langs), "language")} · '
        f'{plural(len(index.references), "standard or paper", "standards and papers")} · '
        f'updated {esc(long_date(index.as_of()))}</p>',
        _timeline(index, path),
        '<div class="columns">',
        '<section class="col-main" aria-labelledby="coverage">',
    ]
    cols = [c for c, _ in COVERAGE_COLUMNS] + ["Other"]
    marks = {"current": ("●", "available implementation of the current edition"),
             "new": ("◐", "available implementation of the current edition, but only from new projects"),
             "partial": ("○", "only unreleased, proposed or older-edition implementations"),
             "": ("—", "none found")}
    parts.append('<h2 id="coverage">Coverage by language</h2>')
    parts.append('<p class="small"><span class="mark mark-current">●</span> an available implementation of the '
                 'current edition · <span class="mark mark-new">◐</span> the same, but only from new projects that '
                 'are not yet widely used · <span class="mark mark-partial">○</span> only unreleased, proposed or '
                 'older-edition implementations · <span class="mark mark-">—</span> none found. A library with '
                 "bindings counts for each language it can be called from.</p>")
    rows = []
    for m in index.methods:
        cov = coverage(m)
        rows.append([_method_link(path, m)] + [f'<span class="mark mark-{cov[c]}" title="{esc(marks[cov[c]][1])}">'
                                              f'{marks[cov[c]][0]}</span>' for c in cols])
    parts.append(_table("coverage", ["Method"] + [esc(c) for c in cols], rows))
    parts.append("</section>")
    parts.append('<section class="col-side" aria-labelledby="gaps">')
    gaps = index.gaps()
    parts.append('<h2 id="gaps">Gaps</h2>')
    if gaps:
        parts.append("<p>No available open-source implementation of the current edition has been found for:</p>")
        parts.append("<ul>" + "".join(f"<li>{_method_link(path, m, m['title'])}</li>" for m in gaps) + "</ul>")
    else:
        parts.append("<p>Every method in the index has at least one available open-source implementation of its "
                     "current edition.</p>")
    if index.new_only():
        parts.append(f"<p>Released implementations of the current edition come only from new projects {NEW_TAG}, "
                     "which are not yet widely used, for:</p>")
        parts.append("<ul>" + "".join(f"<li>{_method_link(path, m, m['title'])}</li>" for m in index.new_only())
                     + "</ul>")
    parts.append('<h2 id="updates">Recent updates</h2>')
    parts.append('<ul class="updates">' + "".join(
        f'<li><a href="{relative(path, UPDATES)}#{esc(str(u["date"]))}">{esc(long_date(u["date"]))}</a>: '
        f'{esc(u["title"])}</li>' for u in index.updates[:5]) + "</ul>")
    parts.append('<h2 id="contribute">Contribute</h2>')
    parts.append(f'<p>Know of an implementation that is missing, or a fact that is wrong? '
                 f'<a href="{esc(site["repository"])}/issues/new/choose">Open an issue</a> or send a pull request. '
                 f'Quick answers are in the <a href="{relative(path, FAQ)}">questions and answers</a>.</p>')
    parts.append("</section>")
    parts.append("</div>")

    ld = [
        {"@type": "WebSite", "name": site["title"], "url": site["base_url"], "description": plain(site["description"])},
        {"@type": "Dataset", "name": site["title"], "description": plain(site["description"]),
         "url": site["base_url"], "license": "https://opensource.org/licenses/MIT",
         "creator": {"@type": "Person", "name": site["maintainer"]["name"],
                     "url": f"https://github.com/{site['maintainer']['github']}"},
         "creditText": site["credit"],
         "dateModified": index.as_of(), "isAccessibleForFree": True,
         "keywords": ["psychoacoustics", "psychoacoustic metrics", "sound quality", "loudness", "sharpness",
                      "roughness", "fluctuation strength", "tonality", "ISO 532", "ECMA-418", "DIN 45692",
                      "open-source software"],
         "distribution": [
             {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": site["base_url"] + "index.json"},
             {"@type": "DataDownload", "encodingFormat": "text/markdown", "contentUrl": site["base_url"] + "llms-full.txt"}]},
    ]
    description = (f"Which open-source code implements which edition of ISO 532, ECMA-418-1/-2, DIN 45692 and other "
                   f"psychoacoustic metrics: {len(index.projects)} projects in "
                   f"{join_words(langs)}. Updated {index.as_of()}.")
    return layout(index, path, title=site["title"], description=description, body="\n".join(parts),
                  section="Metrics", jsonld=ld, sidebar=False)


def _in_short_block(index: Index, m: dict, path: str) -> str:
    """The answer first: current edition, then its implementations grouped by language, then the rest."""
    name = lambda p: _project_link(path, p)  # noqa: E731
    groups = by_language(m["_current_impls"], name, new_tag=NEW_TAG)
    first = esc(current_statement(index, m)) + (" Open-source implementations of it:" if groups else
                                                 " No open-source implementation of it has been found.")
    parts = ['<div class="box box-info">', '<p class="box-title">In short</p>', f"<p>{first}</p>"]
    if groups:
        parts.append('<ul class="by-lang">' + "".join(
            f"<li>{_lang_tag(lang)} {', '.join(names)}</li>" for lang, names in groups) + "</ul>")
    if only_new(m):
        parts.append(f'<p class="caution">{esc(ONLY_NEW)}</p>')
    older = [i for i in dedupe(m["_older_impls"]) if i["_ref"]["status"] != "in-development"]
    if older:
        parts.append('<p class="older">Earlier editions or related models: '
                     + join_words([impl_phrase(i, name, esc, with_ref=True) for i in older]) + ".</p>")
    parts.append("</div>")
    return "\n".join(parts)


def method_page(index: Index, m: dict) -> str:
    path = method_path(m)
    name = lambda p: _project_link(path, p)  # noqa: E731
    fam = m["_family"]
    meta = [f"Unit: {esc(m['unit'])}"]
    if m.get("aka"):
        meta.append("Also known as " + esc(", ".join(m["aka"])))
    parts = [
        _crumbs(f'<a href="{relative(path, HOME)}">Metrics</a>',
                f'<a href="{relative(path, HOME)}#{esc(fam["id"])}">{esc(fam["name"])}</a>'),
        f"<h1>{esc(m['title'])}</h1>",
        f'<p class="meta-line">{" · ".join(meta)}</p>',
        blocks(m["summary"]),
        _in_short_block(index, m, path),
    ]
    if m.get("notes"):
        parts.append(blocks(m["notes"]))

    parts.append('<h2 id="editions">Editions and who implements them</h2>')
    rows = []
    for rid in reversed(m["references"]):
        r = index.ref[rid]
        impls = dedupe([i for i in m["_impls"] if i["reference"] == rid])
        who = ", ".join(name(i["_project"]) + (f" {NEW_TAG}" if i["_project"]["standing"] == "new" else "")
                        + ("" if i["status"] == "available" else
                           " " + _tag(i["status"], "warn" if i["status"] == "unreleased" else "neutral"))
                        for i in impls)
        status = _ref_tag(r)
        if r.get("revision"):
            status += f'<br><span class="muted">{inline(r["revision"])}</span>'
        label = _ref_link(r)
        if r["status"] in ("superseded", "withdrawn"):
            label = f'<span class="old">{label}</span>'
        elif rid in m["current"]:
            label = f"<strong>{label}</strong>"
        rows.append([esc(month(r.get("date"))) or "—", label, status,
                     inline((m.get("edition_notes") or {}).get(rid, "")), who])
    parts.append(_table("editions", ["Date", "Edition", "Status", "What changed", "Implemented by"], rows))

    parts.append('<h2 id="implementations">Implementations</h2>')
    if m["_impls"]:
        rows = [[f'{name(i["_project"])}<br>{_langs(i["_project"]["languages"])}', _edition_cell(i),
                 _functions(i), _validation(i), _status_note(i)] for i in m["_impls"]]
        parts.append(_table("impls", ["Project", "Edition", "Functions", "Validation (as stated)", "Notes"], rows))
        parts.append(f'<p class="small muted">Listed with widely used and established projects first and new projects '
                     f'last. Validation is what each project states about its own testing; see '
                     f'<a href="{relative(path, ABOUT)}#validation">the definitions</a>.</p>')
    else:
        parts.append("<p>No open-source implementation has been found yet. If you know one, please "
                     f'<a href="{esc(index.site["repository"])}/issues/new/choose">open an issue</a>.</p>')
    if m.get("see_also"):
        parts.append("<p>See also: " + ", ".join(_method_link(path, index.method[s], index.method[s]["title"])
                                                  for s in m["see_also"]) + ".</p>")
    parts.append('<h2 id="references">References</h2>')
    parts.append(_ref_list([index.ref[r] for r in m["references"]]))

    projects = list(dict.fromkeys(i["_project"]["id"] for i in m["_impls"]))
    ld = [{"@type": "CollectionPage", "name": m["title"], "url": absolute(index, path),
           "description": plain(m["summary"]), "dateModified": index.as_of(),
           "about": {"@type": "DefinedTerm", "name": m["name"], "alternateName": m.get("aka") or [],
                     "description": plain(m["summary"])},
           "mainEntity": {"@type": "ItemList", "numberOfItems": len(projects), "itemListElement": [
               {"@type": "ListItem", "position": n, "item": _software_ld(index, index.project[pid])}
               for n, pid in enumerate(projects, 1)]}},
          {"@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": index.site["title"], "item": index.site["base_url"]},
              {"@type": "ListItem", "position": 2, "name": m["title"], "item": absolute(index, path)}]}]
    current = join_words([index.ref[r]["label"] for r in m["current"]])
    impl_names = join_words(list(dict.fromkeys(i["_project"]["name"] for i in m["_current_impls"])))
    description = (f"Open-source implementations of {m['title']}: {impl_names or 'none found yet'}. "
                   f"Current edition {current}; which tool implements which edition, functions and validation.")
    return layout(index, path, title=f"{m['title']}: open-source implementations", description=description,
                  body="\n".join(parts), section="Metrics", jsonld=ld, og_type="article")


def project_page(index: Index, p: dict) -> str:
    path = project_path(p)
    facts: list[tuple[str, str]] = [("Repository", f'<a href="{esc(p["repository"])}">{esc(p["repository"])}</a>')]
    if p.get("homepage"):
        facts.append(("Homepage", f'<a href="{esc(p["homepage"])}">{esc(p["homepage"])}</a>'))
    if p.get("docs"):
        facts.append(("Documentation", f'<a href="{esc(p["docs"])}">{esc(p["docs"])}</a>'))
    facts.append(("Language", _langs(p["languages"])))
    facts.append(("Kind", esc(PROJECT_KINDS[p["kind"]])))
    facts.append(("Standing", f'{_standing_tag(p)} <span class="muted">{esc(STANDING[p["standing"]])}</span>'))
    lic = esc(p["license"]) if p["license"] != "none" else "none stated (no licence file)"
    if p.get("license_note"):
        lic += f'<br><span class="muted">{inline(p["license_note"])}</span>'
    facts.append(("Licence", lic))
    for pkg in p.get("packages") or []:
        reg, tmpl = REGISTRIES[pkg["registry"]]
        url = pkg.get("url") or (tmpl.format(name=pkg["name"]) if tmpl else "")
        label = f"{esc(reg)} <code>{esc(pkg['name'])}</code>"
        facts.append(("Package", f'<a href="{esc(url)}">{label}</a>' if url else label))
    if p.get("install"):
        facts.append(("Install", f"<code>{esc(p['install'])}</code>"))
    rel = esc(release_text(p))
    if p.get("_prerelease"):
        pr = p["_prerelease"]
        rel += f'; pre-release {esc(pr.get("version"))} ({esc(month(pr.get("date")))})'
    facts.append(("Latest release", rel))
    facts.append(("Last commit", f'{esc(p["_last_commit"] or "unknown")} {_activity_tag(p)}'))
    if p.get("_stars") is not None:
        facts.append(("GitHub stars", esc(p["_stars"])))
    if p.get("maintainers"):
        facts.append(("Maintainers", esc(", ".join(p["maintainers"]))))
    ai = "disclosed" if p["ai_assistance"] == "disclosed" else "not stated"
    if p.get("ai_note"):
        ai += f' <span class="muted">({inline(p["ai_note"])})</span>'
    facts.append(("AI assistance", ai))
    if p.get("paper"):
        paper = inline(p["paper"]["citation"])
        link = p["paper"].get("url") or (f"https://doi.org/{p['paper']['doi']}" if p["paper"].get("doi") else "")
        if link:
            paper += f' <a href="{esc(link)}">{esc(link)}</a>'
        facts.append(("Paper", paper))
    facts.append(("Entry checked", esc(long_date(p["checked"]))))

    heading = dict(STANDING_HEADINGS)[p["standing"]]
    parts = [
        _crumbs(f'<a href="{relative(path, PROJECTS)}">Projects</a>',
                f'<a href="{relative(path, PROJECTS)}#{esc(p["standing"])}">{esc(heading)}</a>'),
        f"<h1>{esc(p['name'])}</h1>",
        f'<p class="meta-line">{_langs(p["languages"])} {_tag(PROJECT_KINDS[p["kind"]], "neutral")} '
        f"{_standing_tag(p)} {_activity_tag(p)}</p>",
    ]
    if p["standing"] == "new":
        parts.append(f'<div class="box box-warn"><p><strong>New project.</strong> {esc(standing_sentence(p))} '
                     "Check its validation before relying on it.</p></div>")
    parts.append(blocks(p["summary"]))
    parts.append('<table class="facts"><tbody>' + "".join(f'<tr><th scope="row">{k}</th><td>{v}</td></tr>'
                                                         for k, v in facts) + "</tbody></table>")
    parts.append('<h2 id="implements">What it implements</h2>')
    rows = [[_method_link(path, i["_method"]), _edition_cell(i), _functions(i), _validation(i), _status_note(i)]
            for i in p["_impls"]]
    parts.append(_table("impls", ["Metric", "Edition", "Functions", "Validation (as stated)", "Notes"], rows))
    if p.get("notes"):
        parts.append('<h2 id="notes">Notes</h2>')
        parts.append("<ul>" + "".join(f"<li>{inline(n)}</li>" for n in p["notes"]) + "</ul>")
    if p.get("caveats"):
        parts.append('<h2 id="caveats">Before you rely on it</h2>')
        parts.append('<ul class="caveats">' + "".join(f"<li>{inline(c)}</li>" for c in p["caveats"]) + "</ul>")
    parts.append('<h2 id="sources">Sources</h2>')
    parts.append('<ol class="refs">' + "".join(f'<li><a href="{esc(s)}">{esc(s)}</a></li>' for s in p["sources"])
                 + "</ol>")
    methods = join_words(list(dict.fromkeys(i["_method"]["name"] for i in p["_impls"])))
    description = f"{p['name']} ({', '.join(p['languages'])}): {plain(p['summary'])} Implements: {methods}."
    ld = [_software_ld(index, p)]
    return layout(index, path, title=f"{p['name']}: {', '.join(p['languages'])} implementation of psychoacoustic metrics",
                  description=description[:300], body="\n".join(parts), section="Projects", jsonld=ld,
                  og_type="article")


def projects_page(index: Index) -> str:
    path = PROJECTS
    langs = index.languages()
    parts = [
        "<h1>Projects</h1>",
        f'<p class="meta-line">{plural(len(index.projects), "project")} · {plural(len(langs), "language")}</p>',
        "<p>Grouped by standing: established projects first, with the most widely used ones at the top, and new "
        "projects last. “Last commit” is the last commit on the default branch; a project is shown as inactive "
        f"after {index.site.get('inactive_after_days', 365)} days without one.</p>",
        '<p class="toc">' + " · ".join(f'<a href="#{key}">{esc(title)}</a>' for key, title in STANDING_HEADINGS)
        + "</p>",
    ]
    for key, title in STANDING_HEADINGS:
        projects = [p for p in index.projects_by_standing() if p["standing"] == key]
        if not projects:
            continue
        parts.append(f'<h2 id="{key}">{esc(title)} <span class="count">{len(projects)}</span></h2>')
        parts.append(f'<p class="muted">{esc(STANDING[key])}</p>')
        rows = [[_project_link(path, p), _langs(p["languages"]), esc(PROJECT_KINDS[p["kind"]]), esc(p["license"]),
                 esc(release_text(p)), esc(p["_last_commit"] or "unknown"), _activity_tag(p),
                 ", ".join(_method_link(path, m) for m in {i["_method"]["id"]: i["_method"]
                                                           for i in p["_impls"]}.values())]
                for p in projects]
        parts.append(_table("projects", ["Project", "Language", "Kind", "Licence", "Latest release", "Last commit",
                                         "Activity", "Covers"], rows))
    ld = [{"@type": "CollectionPage", "name": "Projects", "url": absolute(index, path),
           "mainEntity": {"@type": "ItemList", "numberOfItems": len(index.projects), "itemListElement": [
               {"@type": "ListItem", "position": n, "item": _software_ld(index, p)}
               for n, p in enumerate(index.projects_by_standing(), 1)]}}]
    return layout(index, path, title="Projects that implement psychoacoustic metrics",
                  description=(f"{len(index.projects)} open-source projects implementing psychoacoustic metrics in "
                               f"{join_words(langs)}, with licence, latest release and activity."),
                  body="\n".join(parts), section="Projects", jsonld=ld)


def standards_page(index: Index) -> str:
    path = STANDARDS
    docs = [r for r in index.references if r["kind"] not in ("paper", "book", "thesis")]
    papers = [r for r in index.references if r["kind"] in ("paper", "book", "thesis")]
    parts = [
        "<h1>Standards and models</h1>",
        f'<p class="meta-line">{plural(len(docs), "standard document")} · {plural(len(papers), "model reference")}</p>',
        "<p>Every document the index refers to, newest first. Each implementation in the index is tied to one of "
        "these editions, so this is also a timeline of how the definitions have changed.</p>",
        '<p class="toc"><a href="#standards">Standards and regulations</a> · '
        '<a href="#models">Model papers, books and theses</a></p>',
    ]
    for title, anchor, refs in (("Standards and regulations", "standards", docs),
                                ("Model papers, books and theses", "models", papers)):
        parts.append(f'<h2 id="{anchor}">{title}</h2>')
        rows = []
        for r in sorted(refs, key=lambda r: (str(r.get("date") or "9999"), r["label"]), reverse=True):
            note = f'<br><span class="muted">{inline(r["revision"])}</span>' if r.get("revision") else ""
            label = _ref_link(r)
            if r["status"] in ("superseded", "withdrawn"):
                label = f'<span class="old">{label}</span>'
            rows.append([esc(month(r.get("date"))) or "—",
                         f'{label}<br><span class="muted">{esc(r["title"])}</span>',
                         _ref_tag(r) + note,
                         ", ".join(_method_link(path, m) for m in r["_methods"])])
        parts.append(_table("standards", ["Date", "Document", "Status", "Used by"], rows))
    return layout(index, path, title="Standards and model papers for psychoacoustic metrics",
                  description=("Timeline of ISO 532, ECMA-418-1, ECMA-418-2, DIN 45692, DIN 45681, ISO/TS 20065, "
                               "ISO 1996-2, ISO 226 and the model papers behind psychoacoustic metrics, with status."),
                  body="\n".join(parts), section="Standards")


def updates_page(index: Index) -> str:
    path = UPDATES
    parts = ["<h1>Updates</h1>",
             '<p class="meta-line">Notable changes to the index and to the projects it follows. '
             f'Also available as an <a href="{relative(path, "feed.xml")}">Atom feed</a>.</p>']
    for u in index.updates:
        parts.append(f'<section class="update" id="{esc(str(u["date"]))}">')
        parts.append(f'<h2>{esc(u["title"])}</h2>')
        parts.append(f'<p class="meta-line"><time datetime="{esc(str(u["date"]))}">{esc(long_date(u["date"]))}</time></p>')
        parts.append(blocks(u["body"]))
        parts.append("</section>")
    return layout(index, path, title="Updates", description="Notable changes to the Psychoacoustic Metrics Index.",
                  body="\n".join(parts), section="Updates")


def about_page(index: Index) -> str:
    path = ABOUT
    site = index.site
    repo = esc(site["repository"])
    fams = join_words([f["name"].lower() for f in index.families])
    status_kind = {"available": "ok", "unreleased": "warn", "proposed": "neutral"}
    parts = [
        "<h1>About this index</h1>",
        f'<p class="lead">{esc(site["description"])}</p>',
        '<p class="toc"><a href="#scope">What is included</a> · <a href="#method">How entries are checked</a> · '
        '<a href="#status">Status</a> · <a href="#validation">Validation</a> · <a href="#standing">Standing</a> · '
        '<a href="#leads">Leads</a> · <a href="#data">Data</a> · <a href="#contributing">Contributing</a> · '
        '<a href="#citing">Citing</a> · <a href="#licence">Licence</a></p>',
        '<h2 id="scope">What is included</h2>',
        f"<p>Open-source code that computes a psychoacoustic metric and says which model or standard edition it "
        f"follows. The index covers {esc(fams)}, in any programming language.</p>",
        "<p>Not included: broadcast loudness (LUFS, ITU-R BS.1770, EBU R 128), speech intelligibility (SII, STI), "
        "codec and speech quality metrics (PEAQ, PESQ, ViSQOL), psychophysics experiment software, music "
        "sensory-dissonance models (Plomp–Levelt, Sethares, Vassilakis), feature extractors whose loudness or "
        "sharpness descriptors follow no named psychoacoustic model, and closed-source tools. The ISO 532 reference "
        "programs can be downloaded free of charge but may not be modified, so they are described on the standards' "
        "own entries rather than listed as projects. A project that only calls another indexed project is listed "
        "when it is an end-user application or an established library. Candidates that were reviewed and left out "
        f'are recorded, with the reason, in <a href="{repo}/blob/main/data/ignored.yaml">data/ignored.yaml</a>.</p>',
        '<h2 id="method">How entries are checked</h2>',
        "<p>Each entry is written from the project's own README, documentation, release notes, licence file and "
        "package metadata, and links to those sources. The index records what a project claims; it does not run "
        "the code, and listing a project is not an endorsement.</p>",
        "<p>Every week a GitHub Action refreshes repository dates, releases and package versions, searches GitHub "
        "and package registries for new candidate projects, and checks the ISO and Ecma catalogues for new "
        "editions. Its findings go into one issue that a person reviews before anything is added or changed.</p>",
        '<h2 id="status">Status of an implementation</h2>',
        _table("defs", ["Value", "Meaning"], [[_tag(k, status_kind[k]), esc(v)] for k, v in IMPL_STATUS_LONG.items()]),
        '<h2 id="validation">Validation evidence</h2>',
        "<p>As stated by each project:</p>",
        _table("defs", ["Value", "Meaning"], [[_tag(VALIDATION[k], VALIDATION_KIND[k]), esc(v)]
                                              for k, v in VALIDATION_LONG.items()]),
        '<h2 id="standing">Standing of a project</h2>',
        "<p>Every project is marked as established, developing or new. Lists of implementations put established "
        "projects first and new projects last, so a project that has not yet been used much is never the first "
        "suggestion. Within each standing, the most widely used and recognised projects come first: SQAT, the "
        "Auditory Modeling Toolbox and MoSQITo.</p>",
        _table("defs", ["Value", "Meaning"], [[_tag(k, STANDING_KIND[k]), esc(v)] for k, v in STANDING.items()]),
        '<h2 id="leads">Leads not yet verified</h2>',
        "<p>Candidates that may belong in the index but could not be checked yet. They are listed so that nobody "
        "has to rediscover them; nothing here has been confirmed.</p>",
        "<ul>" + "".join(f'<li><a href="{esc(l["url"])}">{esc(l["name"])}</a> {_langs(l.get("languages") or [])}: '
                         f'{inline(l["claim"])} <span class="muted">{inline(l["why"])}</span></li>'
                         for l in index.leads) + "</ul>",
        "<p>Not indexed because they are closed source: MATLAB Audio Toolbox, HEAD acoustics ArtemiS SUITE, "
        "Simcenter Testlab, HBK BK Connect and Ansys Sound. Verification studies often use them as references.</p>",
        '<h2 id="data">Machine-readable data</h2>',
        "<ul>",
        f'<li><a href="{relative(path, "index.json")}">index.json</a>: the whole index as one JSON document.</li>',
        f'<li><a href="{relative(path, "llms.txt")}">llms.txt</a> and '
        f'<a href="{relative(path, "llms-full.txt")}">llms-full.txt</a>: summaries for language models, following '
        'the <a href="https://llmstxt.org/">llms.txt</a> proposal. Every page also has a Markdown version.</li>',
        f'<li><a href="{relative(path, "feed.xml")}">feed.xml</a>: Atom feed of updates.</li>',
        f'<li><a href="{repo}/tree/main/data">Source data</a> and its '
        f'<a href="{repo}/blob/main/data/SCHEMA.md">schema</a>.</li>',
        "</ul>",
        '<h2 id="contributing">Contributing</h2>',
        f'<p>Corrections and new projects are welcome. Open an <a href="{repo}/issues/new/choose">issue</a>, or send a '
        f'pull request that adds or edits a file in <code>data/projects/</code>; '
        f'<a href="{repo}/blob/main/CONTRIBUTING.md">CONTRIBUTING.md</a> explains the format. '
        "Project authors are encouraged to check their own entry.</p>",
        '<h2 id="citing">Citing</h2>',
        f'<p>Please cite the index with the <a href="{repo}/blob/main/CITATION.cff">CITATION.cff</a> file and the date '
        "you accessed it, and cite the implementations you actually used.</p>",
        '<h2 id="licence">Licence</h2>',
        f"<p>Data, text and code are released under the {esc(site['license'])} licence.</p>",
        f"<p>{credit(index)}</p>",
    ]
    return layout(index, path, title="About", description="Scope, method, definitions and data access of the "
                  "Psychoacoustic Metrics Index.", body="\n".join(parts), section="About")


def faq_page(index: Index) -> str:
    path = FAQ
    pairs = faq(index, lambda p: _project_link(path, p), lambda m: _method_link(path, m, m["title"]), esc)
    parts = ["<h1>Questions and answers</h1>",
             '<p class="meta-line">Answers are generated from the index data, so they always match the tables.</p>',
             '<ol class="faq-toc">' + "".join(f'<li><a href="#q{n}">{esc(q)}</a></li>'
                                              for n, (q, _) in enumerate(pairs, 1)) + "</ol>"]
    for n, (q, a) in enumerate(pairs, 1):
        parts.append(f'<h2 id="q{n}">{esc(q)}</h2>')
        parts.append(f"<p>{a}</p>")
    ld = [{"@type": "FAQPage", "url": absolute(index, path), "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": plain(re.sub(r"<[^>]+>", "", a))}}
        for q, a in pairs]}]
    return layout(index, path, title="Frequently asked questions about open-source psychoacoustic metrics",
                  description=("Which open-source code implements ISO 532, ECMA-418-1, ECMA-418-2, DIN 45692 and other "
                               "psychoacoustic metrics, in Python, MATLAB, C/C++ and other languages."),
                  body="\n".join(parts), section="FAQ", jsonld=ld)


def not_found(index: Index) -> str:
    # Served from any depth, so links are absolute.
    base = esc(index.site["base_url"])
    body = (f'<h1>Page not found</h1><p>The page you asked for does not exist. Start from the '
            f'<a href="{base}">timeline of metrics</a> or the <a href="{base}projects/">list of projects</a>.</p>')
    page = layout(index, "404.html", title="Page not found", description="Page not found.", body=body, section="",
                  markdown=False)
    return re.sub(r'href="(?!https?:|#|mailto:)([^"]*)"', lambda m: f'href="{base}{m.group(1)}"', page)
