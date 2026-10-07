"""HTML output: static, pre-rendered pages (no JavaScript needed) with Markdown twins and JSON-LD.

The page frame is that of an academic software site: a coloured masthead and tab bar over one container, with a
sidebar listing every metric. The text inside is set like a blog: serif type, ruled tables and plain links. Colour
is used where it helps reading: links stand out from the text, and the states that matter (current edition, new
project, release state, validation, language) are marked in colour.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .data import (ACCESS, GROUP_NAMES, GROUPS, IMPL_STATUS_LONG, KINDS, PROJECT_KINDS, REGISTRIES, VALIDATION,
                   VALIDATION_LONG, VERIFICATION_META, Index, only_new)
from .describe import (COVERAGE_COLUMNS, GROUP_RULE, ONLY_NEW, activity_text, ai_guide, by_language, coverage,
                       highlight_sentence, highlighted,
                       current_statement, dedupe, dependence_note, derived_names, edition_state, faq, how_to_cite,
                       impl_phrase, introduce, language_order, lineage, name_note, only_related, ref_status,
                       release_text, silent_line, standing_sentence, stated_conventions, time_bins, timeline,
                       validation_also, validation_groups, validation_label)
from .paths import (ABOUT, AI, BIBTEX, FAQ, HOME, LANGUAGES, METRICS, PROJECTS, STANDARDS, UPDATES, absolute,
                    md_twin, method_path, project_path, relative)
from .text import blocks, esc, first_sentence, inline, join_words, long_date, month, plain, plural

NAV = [("Home", HOME), ("Metrics", METRICS), ("Projects", PROJECTS), ("Languages", LANGUAGES), ("Standards", STANDARDS),
       ("FAQ", FAQ), ("Updates", UPDATES), ("For AI", AI), ("About", ABOUT)]

# The site's mark: an ear and three level bars, in white on green. site-src/favicon.svg is the same drawing.
LOGO = ('<svg class="brand-mark" viewBox="0 0 64 64" aria-hidden="true" focusable="false">'
        '<rect width="64" height="64" rx="14" fill="#25c59b"/>'
        '<g fill="none" stroke="#fff" stroke-width="4.4" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M26 31C26 19 33 11 42 11C51 11 56 18 56 27C56 35 50 39 47 44C44 49 45 55 38 56C34 57 31 54 31 51"/>'
        '<path d="M34 30C34 24 37 20 42 20C46.5 20 48 24.5 46 28.5C44.5 31.5 41 32.5 41 37"/></g>'
        '<g fill="#fff"><rect x="8" y="46" width="4" height="10" rx="2"/><rect x="14.5" y="40" width="4" height="16" '
        'rx="2"/><rect x="21" y="34" width="4" height="22" rx="2"/></g></svg>')

# Opens each page at its top, also when the site is shown inside another page (a preview frame keeps its scroll
# position across links). Links to a #section and the Back button keep their usual behaviour.
TOP_SCRIPT = ("<script>(function(){var n=window.performance&&performance.getEntriesByType"
              "&&performance.getEntriesByType('navigation')[0];if(location.hash||(n&&n.type!=='navigate'))return;"
              "addEventListener('load',function(){var t=document.getElementById('top');"
              "if(t&&t.scrollIntoView)t.scrollIntoView({block:'start'});});})();</script>")

# Languages: a short code for the timeline (the usual file extension) and a colour class.
LANG_CODES = {"Python": ("py", "py"), "MATLAB": ("m", "m"), "Octave": ("m", "m"), "C": ("c", "c"),
             "C++": ("c++", "c"), "C#": ("c#", "c"), "Rust": ("rs", "rs"), "Julia": ("jl", "jl"),
               "JavaScript": ("js", "js"), "Pure Data": ("pd", "pd"), "R": ("r", "r")}
VALIDATION_KIND = {"standard-data": "ok", "reference-code": "ok", "cross-implementation": "info",
                   "self-tests": "warn", "not-stated": "neutral"}
REF_KIND = {"current": "ok", "superseded": "neutral", "withdrawn": "neutral", "in-development": "warn",
            "published": "info"}
GROUP_KIND = {"established": "ok", "newly-released": "new", "developing": "dev", "legacy": "legacy",
              "others": "neutral", "unknown": "neutral"}
ACTIVITY_KIND = {"active": "ok", "inactive": "warn", "archived": "neutral", "unknown": "neutral"}
# Sections of the Languages page: anchor, heading, the languages it covers.
LANGUAGE_SECTIONS = [("python", "Python", {"Python"}), ("matlab", "MATLAB and Octave", {"MATLAB", "Octave"}),
                     ("c", "C and C++", {"C", "C++"}), ("csharp", "C#", {"C#"}), ("rust", "Rust", {"Rust"}),
                     ("julia", "Julia", {"Julia"}),
                     ("pure-data", "Pure Data", {"Pure Data"})]
ABOUT_SECTIONS = [("scope", "What is included"), ("method", "How entries are checked"), ("status", "Status"),
                  ("validation", "Validation"), ("standing", "Groups of projects"), ("leads", "Leads"),
                  ("data", "Machine-readable data"), ("contributing", "Contributing"), ("citing", "Citing"),
                  ("licence", "Licence")]
# In the order of the projects page.
GROUP_HEADINGS = [("established", "Established projects"), ("newly-released", "Newly released projects"),
                  ("developing", "Developing projects"), ("legacy", "Legacy projects"), ("others", "Others"),
                  ("unknown", "Status unknown")]


# ---------------------------------------------------------------------------------------------- layout

# Pages ask for style.css?v=<hash of its content>, so that after a deployment no browser pairs new pages with a
# stylesheet it cached before.
STYLE_VERSION = hashlib.sha256((Path(__file__).resolve().parents[2] / "site-src" / "style.css").read_bytes()
                               ).hexdigest()[:10]

def layout(index: Index, path: str, *, title: str, description: str, body: str, section: str,
           jsonld: list[dict] | None = None, og_type: str = "website", markdown: bool = True,
           side: str | None = None) -> str:
    """The page frame. The sidebar follows the tab: each tab lists its own contents (`side` overrides it)."""
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
    page_title = title if path == HOME else f"{title} · {site['name']}"
    md_head = (f'<link rel="alternate" type="text/markdown" href="{esc(rel(md_twin(path)))}" title="Markdown version">\n'
               if markdown else "")
    md_foot = f'<a href="{rel(md_twin(path))}">This page as Markdown</a> · ' if markdown else ""
    side = _sidebar(index, path, section) if side is None else side
    page_class = ("page with-sidebar" + (" narrow-side" if path == HOME else "")) if side else "page"
    # Search engines look for their verification tag on the home page only.
    verify = "".join(f'<meta name="{VERIFICATION_META[engine]}" content="{esc(str(code))}">\n'
                     for engine, code in (site.get("verification") or {}).items() if code) if path == HOME else ""
    as_of = esc(long_date(index.as_of()))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(page_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
{md_head}<link rel="alternate" type="application/atom+xml" href="{esc(rel('feed.xml'))}" title="{esc(site['name'])}: updates">
<link rel="icon" href="{esc(rel('favicon.svg'))}" type="image/svg+xml">
<link rel="stylesheet" href="{esc(rel('style.css'))}?v={STYLE_VERSION}">
{verify}<meta name="theme-color" content="#25c59b">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(site['name'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(site['base_url'])}social-preview.png">
<meta name="twitter:card" content="summary_large_image">
{ld}{TOP_SCRIPT}
</head>
<body>
<a class="skip" href="#content">Skip to content</a>
<header class="masthead" id="top">
<div class="container masthead-row">
<a class="brand" href="{rel(HOME)}">{LOGO}<span class="brand-text"><span class="brand-name">{esc(site['name'])}</span><span class="brand-tagline">{esc(site['tagline'])}</span></span></a>
<p class="masthead-meta">Version {esc(str(site.get('version', '')))} · data as of {as_of}<br><a href="{esc(site['repository'])}">Source on GitHub</a></p>
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
are welcome on <a href="{esc(site['repository'])}">GitHub</a>. Version {esc(str(site.get('version', '')))}, data as of {as_of}. {esc(site['license'])} licence.</p>
<p><a href="{rel('index.json')}">JSON</a> · <a href="{rel('llms.txt')}">llms.txt</a> · {md_foot}<a href="{rel('feed.xml')}">Atom feed</a></p>
</div>
</footer>
{_analytics(site)}</body>
</html>
"""


def _side(label: str, items: list[tuple[str, str, bool]], href: str = "", sub: bool = False) -> str:
    """One block of a sidebar: a heading and links; the link to the current page is marked."""
    head = f'<a href="{esc(href)}">{esc(label)}</a>' if href else esc(label)
    here = ' aria-current="page"'
    links = "".join(f'<li><a href="{esc(h)}"{here if cur else ""}>{text}</a></li>' for h, text, cur in items)
    return f'<p class="{"side-family" if sub else "side-head"}">{head}</p>' + (f"<ul>{links}</ul>" if items else "")


def _sidebar(index: Index, path: str, section: str) -> str:
    """The sidebar of a tab: its own contents, so that it always matches the page around it."""
    rel = lambda target: relative(path, target)  # noqa: E731
    blocks_: list[str] = []
    if section == "Home":
        blocks_.append(_side("On this page", [("#timeline", "Editions and implementations", False)]))
        blocks_.append('<ul class="side-sub">' + "".join(f'<li><a href="#{esc(f["id"])}">{esc(f["name"])}</a></li>'
                                                           for f, _ in index.families_with_methods()) + "</ul>")
        blocks_.append("<ul>" + "".join(f'<li><a href="#{a}">{t}</a></li>' for a, t in (
            ("gaps", "Gaps"), ("updates", "Recent updates"), ("contribute", "Contribute"))) + "</ul>")
    elif section == "Metrics":
        blocks_.append(_side("All metrics", [], href=rel(METRICS)))
        for fam, methods in index.families_with_methods():
            blocks_.append(_side(fam["name"], [(rel(method_path(m)), esc(m["name"]), method_path(m) == path)
                                               for m in methods], href=f"{rel(METRICS)}#{fam['id']}", sub=True))
    elif section == "Projects":
        blocks_.append(_side("All projects", [], href=rel(PROJECTS)))
        for key, title in GROUP_HEADINGS:
            projects = index.group(key)
            if projects:
                label = title.replace(" projects", "")
                blocks_.append(_side(f"{label} ({len(projects)})", [
                    (rel(project_path(p)), _strong(p, _breakable(p.get("short_name") or p["name"])),
                     project_path(p) == path) for p in projects], href=f"{rel(PROJECTS)}#{key}", sub=True))
    elif section == "Languages":
        blocks_.append(_side("On this page", [(f"{rel(LANGUAGES)}#{a}", t, False) for a, t in
                                              [("coverage", "Coverage by language")]
                                              + [(a, t) for a, t, _ in LANGUAGE_SECTIONS]
                                              + [("across", "Calling code across languages")]]))
    elif section == "Standards":
        blocks_.append(_side("On this page", [("#standards", "Standards and regulations", False),
                                              ("#models", "Model papers, books and theses", False)]))
        for fam, methods in index.families_with_methods():
            refs = list(dict.fromkeys(r for m in methods for r in m["current"]))
            blocks_.append(_side(fam["name"], [(f"{rel(STANDARDS)}#ref-{r}", esc(index.ref[r]["label"]), False)
                                               for r in refs], sub=True))
    elif section == "Updates":
        blocks_.append(_side("Updates", [(f"{rel(UPDATES)}#{esc(str(u['date']))}",
                                          f"{esc(long_date(u['date']))}: {esc(u['title'])}", False)
                                         for u in index.updates]))
    elif section == "About":
        blocks_.append(_side("On this page", [(f"#{a}", t, False) for a, t in ABOUT_SECTIONS]))
    if not blocks_:
        return ""
    return f'<aside class="sidebar" aria-label="{esc(section or "Site")} contents">' + "\n".join(blocks_) + "</aside>"


def _analytics(site: dict) -> str:
    """The Cloudflare Web Analytics beacon, on every page once data/site.yaml has the site's token. It sets no
    cookies."""
    token = str(site.get("cloudflare_analytics_token") or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9]{16,64}", token):  # validated in data.py; letters and digits need no escaping
        return ""
    return ("<script type=\"module\" src=\"https://static.cloudflareinsights.com/beacon.min.js\" "
            f"data-cf-beacon='{{\"token\": \"{token}\"}}'></script>\n")


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


def _lang_tag(lang: str) -> str:
    _, cls = LANG_CODES.get(lang, (lang, "other"))
    return f'<span class="lang lang-{cls}">{esc(lang)}</span>'


def _langs(langs: list[str]) -> str:
    return " ".join(_lang_tag(lang) for lang in langs)


def _validation(i: dict, href: str = "") -> str:
    """Table cell: the stated evidence as a tag that names what the implementation was compared with, linked to the
    details further down the page."""
    v = i["validation"]
    cell = _tag(validation_label(i), _validation_kind(i), VALIDATION_LONG[v] + (" Details below." if href else ""),
                href=href)
    also = validation_also(i)
    if also:
        cell += f'<br><span class="small muted">{esc(also)}</span>'
    return cell


def _validation_kind(i: dict) -> str:
    """The colour of an evidence tag. Comparisons only with related code (the code it was ported from, a port of it,
    or another port of the same code) are grey: they show a faithful port, not an independent check."""
    if i["validation"] in ("cross-implementation", "reference-code") and only_related(i):
        return "neutral"
    return VALIDATION_KIND[i["validation"]]


def _maintainer_check(index: Index, p: dict) -> str:
    """The list maintainer's own observation about a project, clearly set apart from what the project states."""
    if not p.get("maintainer_check"):
        return ""
    return (f'<p class="maintainer-check"><strong>Checked by the maintainer of {esc(index.site["name"])}:</strong> '
            f"{inline(p['maintainer_check'])}</p>")


def _validation_ids(impls: list[dict], first) -> dict[int, str]:
    """Anchors of the validation details, e.g. v-sharpness-din-45692-2009 (or v-mosqito-… on a method page)."""
    ids: dict[int, str] = {}
    seen: dict[str, int] = {}
    for i in impls:
        base = f"v-{first(i)}-{i['reference']}"
        seen[base] = seen.get(base, 0) + 1
        ids[id(i)] = base if seen[base] == 1 else f"{base}-{seen[base]}"
    return ids


def _validation_section(index: Index, path: str, impls: list[dict], ids: dict[int, str], *, on_method: bool) -> str:
    """"How it was validated": for each implementation (rows with the same evidence and details together), the
    evidence it states, what it was compared with and the details it gives. Rows with nothing stated share one line."""
    groups, silent = validation_groups(impls, (lambda i: i["_project"]["id"]) if on_method else (lambda i: ""))
    triples = [(i["_project"]["id"], i["method"], i["reference"]) for i in impls]
    linked = lambda q: _project_link(path, q)  # noqa: E731

    def title(i: dict) -> str:
        if on_method:
            p = i["_project"]
            head = _project_link(path, p) + (f" {GROUP_TAGS[p['_group']]}" if p["_group"] in GROUP_TAGS else "")
            if i.get("_via"):
                head += f' <span class="muted">via {esc(i["_via"]["name"])}</span>'
        else:
            head = _method_link(path, i["_method"])
        head += f' <span class="sep">·</span> {esc(i["_ref"]["label"])}'
        if i.get("scope") and triples.count((i["_project"]["id"], i["method"], i["reference"])) > 1:
            head += f' <span class="muted">({esc(i["scope"])})</span>'
        return head

    entries = []
    checked_by_maintainer: set[str] = set()
    for group in groups:
        i = group[0]
        v = i["validation"]
        names = "".join(f'<dt id="{ids[id(j)]}">{title(j)}</dt>' for j in group)
        evidence = (f'<span class="tag tag-{_validation_kind(i)}" title="{esc(VALIDATION_LONG[v])}">'
                    f"{validation_label(i, linked, esc)}</span>")
        also = validation_also(i, linked, esc)
        if also:
            evidence += f" {also}"
        origin = []
        if i.get("_derived"):
            origin.append(f"Ported or adapted from {join_words(derived_names(i, linked, esc))}.")
        if dependence_note(i):
            origin.append(esc(dependence_note(i)))
        source = f'<p class="derived">{" ".join(origin)}</p>' if origin else ""
        details = i.get("validation_details") or []
        body = ("<ul>" + "".join(f"<li>{inline(d)}</li>" for d in details) + "</ul>" if details
                else ("" if source else '<p class="muted">No further details are recorded here.</p>'))
        # On a method page, the maintainer's own check goes under the project's first entry.
        check = ""
        if on_method and i["_project"]["id"] not in checked_by_maintainer:
            check = _maintainer_check(index, i["_project"])
            checked_by_maintainer.add(i["_project"]["id"])
        entries.append(f'{names}\n<dd><p class="evidence">{evidence}</p>{source}{body}{check}</dd>')
    who = "each project" if on_method else "the project"
    parts = [f'<h2 id="validation">How {"they were" if on_method else "it was"} validated</h2>',
             f'<p class="small muted">As stated by {who}; {esc(index.site["name"])} has not run the code. Agreement '
             "with another implementation shows that both compute the same values, not that either follows the "
             f'standard. <a href="{relative(path, ABOUT)}#validation">Kinds of evidence</a>.</p>']
    if not on_method and impls:
        parts.append(_maintainer_check(index, impls[0]["_project"]))
    if entries:
        parts.append(f'<dl class="validation{" on-method" if on_method else ""}">\n' + "\n".join(entries) + "\n</dl>")
    if silent:
        if not entries:
            parts.append("<p>" + ("None of these projects says how its code was validated." if on_method
                                  else "The project does not say how any of these were validated.") + "</p>")
        else:
            parts.append(f'<p class="muted">{esc(silent_line(impls, groups, silent, on_method))}</p>')
    return "\n".join(parts)


def _lineage_section(index: Index, path: str, m: dict) -> str:
    """Who ported or adapted code from whom among a method's implementations, drawn as a tree."""
    # Every row, also a second row of one project for one edition (another scope may port other code).
    forest = lineage(m["_all_impls"])
    if not forest:
        return ""

    def node(n: tuple) -> str:
        kind, value = n
        if kind == "code":
            return f'<span class="code-node">{esc(value)}</span>'
        tag = f" {GROUP_TAGS[value['_group']]}" if value["_group"] in GROUP_TAGS else ""
        return f'{_lang_badge(value["languages"][0])}{_project_link(path, value)}{tag}'

    def tree(items: list[tuple]) -> str:
        return "<ul>" + "".join(f"<li>{node(n)}{tree(kids) if kids else ''}</li>" for n, kids in items) + "</ul>"

    return "\n".join([
        '<h2 id="lineage">Who ported code from whom</h2>',
        '<p class="small muted">As the projects state. Each branch shows code ported, translated or adapted from '
        "the code above it, so agreement between them is a check of the port, not an independent validation.</p>",
        f'<div class="lineage">{tree(forest)}</div>',
    ])


def _conventions_section(index: Index, path: str, impls: list[dict], general: list[str], *, on_method: bool) -> str:
    """"Before you compare numbers": choices that make correct implementations give different numbers. A method
    page lists the method's general points, then what each project states; a project page lists the project's
    general points, then those of single metrics."""
    stated = stated_conventions(impls, on_method)
    if not general and not stated:
        return ""
    parts = ['<h2 id="conventions">Before you compare numbers</h2>',
             "<p>Implementations of the same method can give different numbers without either being wrong. Check "
             "these choices first.</p>"]
    if general:
        parts.append('<ul class="conventions">' + "".join(f"<li>{inline(c)}</li>" for c in general) + "</ul>")
    if stated:
        parts.append("<p>What the projects state:</p>" if on_method else
                     ("<p>For single metrics:</p>" if general else ""))
        rows = []
        for i, items in stated:
            if on_method:
                p = i["_project"]
                who = _project_link(path, p) + (f" {GROUP_TAGS[p['_group']]}" if p["_group"] in GROUP_TAGS else "")
            else:
                who = _method_link(path, i["_method"]) + f' <span class="muted">({esc(i["_ref"]["label"])})</span>'
            rows.append(f"<dt>{who}</dt><dd><ul>" + "".join(f"<li>{inline(c)}</li>" for c in items) + "</ul></dd>")
        parts.append('<dl class="conventions">' + "".join(rows) + "</dl>")
    return "\n".join(part for part in parts if part)


def _ref_tag(r: dict) -> str:
    return _tag(ref_status(r), REF_KIND[r["status"]])


def _group_tag(p: dict) -> str:
    group = p["_group"]
    label = {"newly-released": "newly released", "others": "other", "unknown": "status unknown"}.get(group, group)
    return _tag(label, GROUP_KIND[group], GROUPS[group])


def _activity_tag(p: dict, short: bool = False) -> str:
    """The activity state; the short form, for tables that also show the last commit, keeps the date in a tooltip."""
    kind = ACTIVITY_KIND.get(p["_activity"], "neutral")
    if short:
        return _tag(p["_activity"], kind, activity_text(p))
    return _tag(activity_text(p), kind)


# Markers for the groups that need one; established projects have none.
NEW_TAG = _tag("newly", "new", "Newly released. " + GROUPS["newly-released"])
DEV_TAG = _tag("developing", "dev", "Developing. " + GROUPS["developing"])
LEGACY_TAG = _tag("legacy", "legacy", "Legacy. " + GROUPS["legacy"])
GROUP_TAGS = {"newly-released": NEW_TAG, "developing": DEV_TAG, "legacy": LEGACY_TAG}


def _strong(p: dict, html: str) -> str:
    """A project's name as given, in bold for a super project."""
    return f"<strong>{html}</strong>" if p["_super"] else html


def _project_link(path: str, p: dict) -> str:
    """A link to a project's page; the name of a super project is in bold, wherever it appears."""
    name = f"<strong>{esc(p['name'])}</strong>" if p["_super"] else esc(p["name"])
    return f'<a href="{relative(path, project_path(p))}">{name}</a>'


def _method_link(path: str, m: dict, label: str | None = None) -> str:
    return f'<a href="{relative(path, method_path(m))}">{esc(label or m["name"])}</a>'


def _ref_link(r: dict) -> str:
    url = r.get("url") or (f"https://doi.org/{r['doi']}" if r.get("doi") else "")
    return f'<a href="{esc(url)}">{esc(r["label"])}</a>' if url else esc(r["label"])


def _edition_link(path: str, r: dict) -> str:
    """An edition linked to the standard or paper, or, when it has no address online, to its full citation on the
    Standards page."""
    if r.get("url") or r.get("doi"):
        return _ref_link(r)
    return (f'<a href="{relative(path, STANDARDS)}#ref-{esc(r["id"])}" title="Full reference on the Standards page">'
            f'{esc(r["label"])}</a>')


def _functions(i: dict) -> str:
    return ", ".join(f"<code>{esc(f)}</code>" for f in i.get("functions") or [])


def _status_note(i: dict) -> str:
    """Notes cell: state tags first (new project, unreleased, pull request), then the free-text note."""
    bits = []
    if i["_project"]["_group"] in GROUP_TAGS:
        bits.append(GROUP_TAGS[i["_project"]["_group"]])
    if i["status"] == "unreleased":
        bits.append(_tag("unreleased", "warn", IMPL_STATUS_LONG["unreleased"], href=i.get("link", "")))
    elif i["status"] == "proposed":
        bits.append(_tag("pull request", "neutral", IMPL_STATUS_LONG["proposed"], href=i.get("link", "")))
    if i.get("_via"):
        bits.append(f'Computed by {esc(i["_via"]["name"])}.')
    if i.get("note"):
        bits.append(inline(i["note"]))
    return " ".join(bits)


def _edition_cell(path: str, i: dict) -> str:
    """Edition label, linked to the standard or paper, with scope and first version underneath."""
    cell = _edition_link(path, i["_ref"])
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
    if p["license"] not in ("none", "proprietary-free", "unknown"):
        d["license"] = p["license"]
    if p.get("_last_commit"):
        d["dateModified"] = p["_last_commit"]
    if p.get("_release"):
        d["version"] = str(p["_release"]["version"])
    return d


def _crumbs(*links: str) -> str:
    return '<p class="crumbs">' + ' <span class="sep" aria-hidden="true">›</span> '.join(links) + "</p>"


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
    if p.get("highlight"):
        tip.append(p["highlight"])
    if standing_sentence(p):
        tip.append(standing_sentence(p))
    return p["name"] + ": " + "; ".join(tip)


def _lang_badge(lang: str) -> str:
    """The language as a short code in its colour, in a box: py, m, c++, rs, jl …"""
    code, cls = LANG_CODES.get(lang, (lang[:2].lower(), "other"))
    return f'<span class="lb lang-{cls}" title="{esc(lang)}">{esc(code)}</span>'


# Light markers for the dense timeline: a word after the name instead of a boxed tag. Legacy projects are grey.
TIMELINE_MARKS = {"newly-released": ("new", "new"), "developing": ("dev", "dev")}


def _timeline_impl(path: str, i: dict) -> str:
    """One line per project: its language as a short code, the name (in bold for super projects),
    a marker if the code is not released, and a small "new" or "dev" after newly released and developing projects;
    legacy projects are grey. Version, languages and activity are in the tooltip."""
    p = i["_project"]
    name = _strong(p, _breakable(p.get("short_name") or p["name"]))
    bits = [f'<a href="{relative(path, project_path(p))}">{name}</a>']
    if i["status"] == "proposed":
        bits.append(_tag("PR", "neutral", IMPL_STATUS_LONG["proposed"], href=i.get("link", "")))
    elif i["status"] == "unreleased":
        bits.append(_tag("main", "warn", IMPL_STATUS_LONG["unreleased"]))
    if p["_group"] in TIMELINE_MARKS:
        word, kind = TIMELINE_MARKS[p["_group"]]
        bits.append(f'<span class="mk mk-{kind}" title="{esc(GROUP_NAMES[p["_group"]].capitalize())}. '
                    f'{esc(GROUPS[p["_group"]])}">{word}</span>')
    quiet = ' class="quiet"' if p["_group"] == "legacy" else ""
    return (f'<li{quiet} title="{esc(_impl_tip(i))}">{_lang_badge(p["languages"][0])}'
            f'<span class="nm">{" ".join(bits)}</span></li>')


# An edition lists at most this many projects, the most established first. When there are more, the last line
# counts the rest and shows them in place when clicked.
TIMELINE_SHOWN = 4


def _timeline_edition(path: str, m: dict, ref: dict, impls: list[dict]) -> str:
    state = edition_state(m, ref)
    tip = f'{ref["title"]}. {ref_status(ref).capitalize()}.'
    label = f'<span class="ed-label" title="{esc(tip)}">{_breakable(ref["label"])}</span>'
    if state == "dev":
        label += " " + _tag("in development", "warn")
    # `impls` is in the order established, newly released, developing, legacy.
    shown, rest = (impls, []) if len(impls) <= TIMELINE_SHOWN else (impls[:TIMELINE_SHOWN - 1], impls[TIMELINE_SHOWN - 1:])
    lines = [_timeline_impl(path, i) for i in shown]
    if rest:
        kinds = {}
        for i in rest:
            kinds.setdefault(GROUP_NAMES[i["_project"]["_group"]], []).append(i["_project"]["name"])
        also = "; ".join(f"{', '.join(names)} ({kind})" for kind, names in kinds.items())
        hidden = "".join(_timeline_impl(path, i) for i in rest)
        lines.append(f'<li class="more"><details><summary title="Also: {esc(also)}"><span class="closed">'
                     f'+{len(rest)} more</span><span class="opened" hidden>show fewer</span></summary>'
                     f"<ul>{hidden}</ul></details></li>")
    body = f'<ul>{"".join(lines)}</ul>' if lines else ""
    cls = f"edition ed-{state}" if state else "edition"
    return f'<div class="{cls}">{label}{body}</div>'


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
                editions = "".join(_timeline_edition(path, m, ref, impls) for ref, impls in cell)
                cells.append(f'<td class="{cls}">{editions}</td>')
            lines.append(f'<tr><th scope="row" class="rowhead">{_method_link(path, m)}'
                         f'<span class="unit">{esc(m["unit"])}</span></th>' + "".join(cells) + "</tr>")
        groups.append("<tbody>\n" + "\n".join(lines) + "\n</tbody>")
    used = {i["_project"]["languages"][0] for _, rows in timeline(index) for row in rows for cell in row["cells"]
            for _, impls in cell for i in impls}
    labels = {"MATLAB": "MATLAB or Octave"}
    key_langs = " ".join(f'<span class="key-lang">{_lang_badge(lang)} {esc(labels.get(lang, lang))}</span>'
                         for lang in sorted(used, key=language_order))
    legend = (
        '<div class="legend">'
        '<p><span class="key key-current">ISO 532-1:2017</span> current edition '
        '<span class="key key-old">ISO 226:2003</span> superseded or withdrawn '
        f'{_tag("in development", "warn")} draft or new work item '
        '<span class="key key-life"></span> years since the method’s first edition</p>'
        f'<p class="key-langs">Language: {key_langs}</p>'
        f"<p><strong>Bold name</strong>: {esc(' or '.join(dict.fromkeys(p['highlight'] for p in index.super_projects())))} "
        "· no marker: established · "
        '<span class="mk mk-new">new</span> newly released, first released less than about a year ago and not yet '
        'seen to be widely used · <span class="mk mk-dev">dev</span> developing: public for more than a year, without a '
        'publication or documented use by others · <span class="key-quiet">grey name</span>: legacy, archived or '
        f"no commit for three years or more · each edition shows at most {TIMELINE_SHOWN} projects, the most "
        "established first; <em>+ more</em> shows the rest</p>"
        f'<p>{_tag("main", "warn")} merged, not in a release yet · {_tag("PR", "neutral")} open pull request · '
        "hover over a name for its languages, version and status</p>"
        "</div>")
    return "\n".join([
        '<section class="timeline-section" aria-labelledby="timeline">',
        '<h2 id="timeline">Editions and implementations</h2>',
        "<p>Each standard edition or model paper sits in the column of the year it appeared. Under it are the "
        "projects that implement it: the projects in bold and the other established projects first, then newly released, "
        "developing and legacy ones. Hover over a name for details; each method links to a page with function names "
        "and validation.</p>",
        legend,
        '<div class="table-wrap"><table class="timeline"><thead><tr>' + "".join(head) + "</tr></thead>\n"
        + "\n".join(groups) + "\n</table></div>",
        _others_note(index, path),
        "</section>",
    ])


def _others_note(index: Index, path: str) -> str:
    """Tools that call one of the listed projects instead of computing the metrics themselves."""
    others = index.others()
    if not others:
        return ""
    names = join_words([f'{_project_link(path, p)} (via '
                        f'{join_words(list(dict.fromkeys(i["_via"]["name"] for i in p["_impls"])))})' for p in others])
    return (f'<p class="others-note"><strong>Others.</strong> Not in the timeline, because they call one of the '
            f'projects above instead of computing the metrics themselves: {names}. See '
            f'<a href="{relative(path, PROJECTS)}#others">Others</a> on the projects page.</p>')


# ---------------------------------------------------------------------------------------------- pages

def home(index: Index) -> str:
    path = HOME
    site = index.site
    langs = index.languages()
    parts = [
        "<h1>Open-Source Implementations of Psychoacoustic and Sound Quality Metrics</h1>",
        f'<p class="byline">Updated {esc(long_date(index.as_of()))} · {plural(len(index.methods), "method")} · '
        f'{plural(len(index.projects), "project")} · {plural(len(langs), "language")} · '
        f'{plural(len(index.references), "standard or paper", "standards and papers")}</p>',
        '<p class="lead">Which open-source code implements which edition of each psychoacoustic standard or model, '
        "in any programming language. Standards such as ECMA-418-2 and ISO 532 change between editions, so two "
        "tools that both say they implement a standard can give different results.</p>",
        _timeline(index, path),
        '<div class="columns">',
        '<section class="col-main" aria-labelledby="gaps">',
        '<h2 id="gaps">Gaps</h2>',
    ]
    gaps = index.gaps()
    if gaps:
        parts.append("<p>No available open-source implementation of the current edition has been found for:</p>")
        parts.append("<ul>" + "".join(f"<li>{_method_link(path, m, m['title'])}</li>" for m in gaps) + "</ul>")
    else:
        parts.append("<p>Every method in the list has at least one available open-source implementation of its "
                     "current edition.</p>")
    if index.new_only():
        parts.append("<p>Released implementations of the current edition come only from newly released projects "
                     f"{NEW_TAG}, not yet seen to be widely used, for:</p>")
        parts.append("<ul>" + "".join(f"<li>{_method_link(path, m, m['title'])}</li>"
                                      for m in index.new_only()) + "</ul>")
    parts.append(f'<p>Which of them can be computed in Python, MATLAB, C or another language is shown on the '
                 f'<a href="{relative(path, LANGUAGES)}">Languages</a> page.</p>')
    parts.append("</section>")
    parts.append('<section class="col-side" aria-labelledby="updates">')
    parts.append('<h2 id="updates">Recent updates</h2>')
    parts.append('<ul class="updates">' + "".join(
        f'<li><a href="{relative(path, UPDATES)}#{esc(str(u["date"]))}">{esc(long_date(u["date"]))}</a>: '
        f'{esc(u["title"])}</li>' for u in index.updates[:5]) + "</ul>")
    parts.append('<h2 id="contribute">Contribute</h2>')
    parts.append(f'<p>Know of an implementation that is missing, or a fact that is wrong? '
                 f'<a href="{esc(site["repository"])}/issues/new/choose">Open an issue</a>, send a pull request, or '
                 f'<a href="{relative(path, FAQ)}#message">leave a message</a>.</p>')
    parts.append("</section>")
    parts.append("</div>")

    ld = [
        {"@type": "WebSite", "name": site["name"], "alternateName": site["title"], "url": site["base_url"],
         "description": plain(site["description"])},
        {"@type": "Dataset", "name": f"{site['name']}: {site['title']}", "description": plain(site["description"]),
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
    return layout(index, path, title=f"{site['name']}: {site['tagline']}", description=description, body="\n".join(parts),
                  section="Home", jsonld=ld)


def _in_short_block(index: Index, m: dict, path: str) -> str:
    """The answer first: current edition, then its implementations grouped by language, then the rest."""
    name = lambda p: _project_link(path, p)  # noqa: E731
    groups = by_language(m["_current_impls"], name, tags=GROUP_TAGS)
    first = esc(current_statement(index, m)) + (" Open-source implementations of it:" if groups
                                                else " No open-source implementation of it has been found.")
    parts = ['<div class="in-short">', f"<p><strong>In short.</strong> {first}</p>"]
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
        _crumbs(f'<a href="{relative(path, METRICS)}">Metrics</a>',
                f'<a href="{relative(path, METRICS)}#{esc(fam["id"])}">{esc(fam["name"])}</a>'),
        f"<h1>{esc(m['title'])}</h1>",
        f'<p class="byline">{" · ".join(meta)}</p>',
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
        who = ", ".join(name(i["_project"]) + (f" {GROUP_TAGS[i['_project']['_group']]}"
                                               if i["_project"]["_group"] in GROUP_TAGS else "")
                        + ("" if i["status"] == "available" else
                           " " + _tag(i["status"], "warn" if i["status"] == "unreleased" else "neutral"))
                        for i in impls)
        status = _ref_tag(r)
        if r.get("revision"):
            status += f'<br><span class="muted">{inline(r["revision"])}</span>'
        label = _edition_link(path, r)
        if r["status"] in ("superseded", "withdrawn"):
            label = f'<span class="old">{label}</span>'
        elif rid in m["current"]:
            label = f"<strong>{label}</strong>"
        rows.append([esc(month(r.get("date"))) or "—", label, status,
                     inline((m.get("edition_notes") or {}).get(rid, "")), who])
    parts.append(_table("editions", ["Date", "Edition", "Status", "What changed", "Implemented by"], rows))

    parts.append('<h2 id="implementations">Implementations</h2>')
    checked = m["_all_impls"]  # every row, also those computed by another project
    ids = _validation_ids(checked, lambda i: i["_project"]["id"])
    stated = {id(i) for group in validation_groups(checked, lambda i: i["_project"]["id"])[0] for i in group}
    if m["_impls"]:
        rows = [[f'{name(i["_project"])}<br>{_langs(i["_project"]["languages"])}', _edition_cell(path, i),
                 _functions(i), _validation(i, f"#{ids[id(i)]}" if id(i) in stated else ""), _status_note(i)]
                for i in m["_impls"]]
        parts.append(_table("impls", ["Project", "Edition", "Functions", "Validation (as stated)", "Notes"], rows))
        parts.append(f'<p class="small muted">Listed with the projects in bold and the other established projects '
                     f'first, then newly released, developing and legacy ones. Validation is what each project states '
                     f'about its own testing: the details are <a href="#validation">below</a>, the kinds of evidence '
                     f'on <a href="{relative(path, ABOUT)}#validation">the About page</a>.</p>')
    else:
        parts.append("<p>No open-source implementation has been found yet. If you know one, please "
                     f'<a href="{esc(index.site["repository"])}/issues/new/choose">open an issue</a>.</p>')
    if m["_via_impls"]:
        calls = dedupe(m["_via_impls"])
        parts.append("<p>Also available through tools that call one of these implementations: " + join_words(
            [f'{name(i["_project"])} (via {esc(i["_via"]["name"])}, {esc(i["_ref"]["label"])})' for i in calls])
            + ".</p>")
    if m.get("see_also"):
        parts.append("<p>See also: " + ", ".join(_method_link(path, index.method[s], index.method[s]["title"])
                                                  for s in m["see_also"]) + ".</p>")
    if checked:
        parts.append(_validation_section(index, path, checked, ids, on_method=True))
    parts.append(_lineage_section(index, path, m))
    parts.append(_conventions_section(index, path, checked, m.get("conventions") or [], on_method=True))
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
              {"@type": "ListItem", "position": 1, "name": index.site["name"], "item": index.site["base_url"]},
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
    facts.append(("Kind", f'{esc(PROJECT_KINDS[p["kind"]])}<br><span class="muted">{esc(KINDS[p["kind"]])}</span>'))
    group = f'{_group_tag(p)} <span class="muted">{esc(GROUPS[p["_group"]])}'
    if highlight_sentence(p):
        group += " " + esc(highlight_sentence(p))
    facts.append(("Group", group + "</span>"))
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
    facts.append(("How to cite", inline(how_to_cite(p))))
    facts.append(("Entry checked", esc(long_date(p["checked"]))))

    parts = [
        _crumbs(f'<a href="{relative(path, PROJECTS)}">Projects</a>',
                f'<a href="{relative(path, PROJECTS)}#{esc(p["_group"])}">'
                f'{esc(dict(GROUP_HEADINGS)[p["_group"]])}</a>'),
        f"<h1>{esc(p['name'])}</h1>",
        f'<p class="byline">{_langs(p["languages"])} · {esc(PROJECT_KINDS[p["kind"]].lower())} · '
        f"{_group_tag(p)} {_activity_tag(p)}</p>",
    ]
    if p.get("access"):
        parts.append(f'<p class="notice notice-info"><strong>Status unknown.</strong> {esc(ACCESS[p["access"]])} '
                     f'{inline(p["access_note"])} What it implements has not been verified, so it is not listed '
                     "under the metrics.</p>")
    if p["_others"]:
        callee = join_words([_project_link(path, q) for q in {i["_via"]["id"]: i["_via"] for i in p["_impls"]}.values()])
        parts.append(f'<p class="notice notice-info"><strong>Listed under Others.</strong> It does not compute the '
                     f"metrics itself; its results come from {callee}.</p>")
    if p["standing"] == "newly-released" and not p.get("access"):
        parts.append(f'<p class="notice"><strong>Newly released project.</strong> {esc(standing_sentence(p))} '
                     "Check its validation before relying on it.</p>")
    elif p["_group"] == "legacy":
        parts.append(f'<p class="notice notice-legacy"><strong>Legacy project.</strong> {esc(standing_sentence(p))} '
                     "Its code may follow an older edition and may not run with current software.</p>")
    parts.append(blocks(p["summary"]))
    parts.append('<table class="facts"><tbody>' + "".join(f'<tr><th scope="row">{k}</th><td>{v}</td></tr>'
                                                         for k, v in facts) + "</tbody></table>")
    if p.get("access"):
        parts.append('<h2 id="claim">What it is said to implement</h2>')
        parts.append(f"<p>{inline(p['claim'])}</p>")
        parts.append('<p class="small muted">As described in the sources below; the code itself could not be '
                     "checked.</p>")
    else:
        parts.append('<h2 id="implements">What it implements</h2>')
        ids = _validation_ids(p["_impls"], lambda i: i["method"])
        stated = {id(i) for group in validation_groups(p["_impls"], lambda i: "")[0] for i in group}
        rows = [[_method_link(path, i["_method"]), _edition_cell(path, i), _functions(i),
                 _validation(i, f"#{ids[id(i)]}" if id(i) in stated else ""), _status_note(i)] for i in p["_impls"]]
        parts.append(_table("impls", ["Metric", "Edition", "Functions", "Validation (as stated)", "Notes"], rows))
        parts.append(_validation_section(index, path, p["_impls"], ids, on_method=False))
        parts.append(_conventions_section(index, path, p["_impls"], p.get("conventions") or [], on_method=False))
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
    description = f"{p['name']} ({', '.join(p['languages'])}): {plain(p['summary'])}" + (
        f" Implements: {methods}." if methods else "")
    ld = [_software_ld(index, p)]
    return layout(index, path, title=f"{p['name']}: {', '.join(p['languages'])} implementation of psychoacoustic metrics",
                  description=description[:300], body="\n".join(parts), section="Projects", jsonld=ld,
                  og_type="article")


def _project_names(path: str, impls: list[dict]) -> str:
    """Projects as a compact inline list: language code, name (bold for super projects), and markers for
    unreleased code and newly released projects; legacy projects are grey."""
    best: dict[str, dict] = {}
    for i in impls:
        key = i["_project"]["id"]
        if key not in best or (i["status"] == "available" and best[key]["status"] != "available"):
            best[key] = i
    out = []
    for i in best.values():
        p = i["_project"]
        bit = _lang_badge(p["languages"][0]) + _project_link(path, p)
        if i["status"] != "available":
            bit += " " + _tag("main" if i["status"] == "unreleased" else "PR",
                              "warn" if i["status"] == "unreleased" else "neutral", IMPL_STATUS_LONG[i["status"]])
        if p["_group"] in GROUP_TAGS:
            bit += " " + GROUP_TAGS[p["_group"]]
        cls = "pn quiet" if p["_group"] == "legacy" else "pn"
        out.append(f'<span class="{cls}" title="{esc(_impl_tip(i))}">{bit}</span>')
    return " ".join(out)


def metrics_page(index: Index) -> str:
    path = METRICS
    parts = [
        "<h1>Metrics</h1>",
        f'<p class="byline">{plural(len(index.methods), "method")} in {plural(len(index.families), "group")}</p>',
        '<p class="lead">Each metric with its unit, the edition that an up-to-date implementation should follow, and '
        "the open-source projects that implement that edition. Every method has its own page with all editions, "
        "function names and validation.</p>",
    ]
    for fam, methods in index.families_with_methods():
        parts.append(f'<h2 id="{esc(fam["id"])}">{esc(fam["name"])}</h2>')
        if fam.get("summary"):
            parts.append(f"<p>{inline(fam['summary'])}</p>")
        rows = []
        for m in methods:
            current = join_words([index.ref[r]["label"] for r in m["current"]])
            names = _project_names(path, m["_current_impls"]) or '<span class="muted">none found</span>'
            rows.append([_method_link(path, m) + f'<br><span class="muted">{esc(m["unit"])}</span>', esc(current),
                         names])
        parts.append(_table("metrics", ["Method", "Current edition", "Implementations of it"], rows))
    return layout(index, path, title="Psychoacoustic metrics and their current editions",
                  description=(f"{len(index.methods)} psychoacoustic metrics, from Zwicker loudness to aural "
                               "detectability: unit, current standard edition and open-source implementations."),
                  body="\n".join(parts), section="Metrics")


def _how(p: dict, langs: set[str], index: Index, path: str) -> str:
    """How a project is used from one language: written in it, or a core in another language with an interface
    for it; whether it is a port of another project; how to install it; and the project's own notes."""
    core = p.get("core") or p["languages"][0]
    lang = sorted(langs & set(p["languages"]))[0]
    how = f"Written in {esc(core)}" if core in langs else f"Written in {esc(core)}, with a {esc(lang)} interface"
    if p.get("based_on"):
        how += f"; a port of {_project_link(path, index.project[p['based_on']])}"
    how += "."
    install = p.get("install") or ""
    if install and (lang == "Python") == install.startswith("pip") and (lang == "Julia") == ("Pkg" in install):
        how += f" <code>{esc(install)}</code>"
    elif not p.get("packages") and not p.get("language_note"):
        how += ' <span class="muted">From the repository.</span>'
    if p.get("language_note"):
        how += f'<br><span class="muted">{inline(p["language_note"])}</span>'
    return how


def languages_page(index: Index) -> str:
    path = LANGUAGES
    cols = [c for c, _ in COVERAGE_COLUMNS] + ["Other"]
    marks = {"current": "available implementation of the current edition",
             "new": "available implementation of the current edition, but only from newly released projects",
             "partial": "only unreleased, proposed or older-edition implementations",
             "": "none found"}

    def mark(state: str) -> str:
        return (f'<span class="mark mark-{state or "none"}" role="img" aria-label="{esc(marks[state])}" '
                f'title="{esc(marks[state])}"></span>')
    listed = [p for p in index.projects_by_group() if p["_group"] not in ("others", "unknown")]
    parts = [
        "<h1>Languages</h1>",
        f'<p class="byline">{plural(len(index.languages()), "language")} · '
        f'{plural(len(listed), "project")} that compute the metrics themselves</p>',
        '<p class="lead">Which metrics can be computed from each programming language, and how each project is '
        "used from it: code written in that language, a compiled core with an interface for it, or a port of "
        "another project.</p>",
        '<h2 id="coverage">Coverage by language</h2>',
        f'<p class="small mark-key">{mark("current")} an available implementation of the current edition '
        f'· {mark("new")} the same, but only from newly released projects not yet seen to be widely used · '
        f'{mark("partial")} only unreleased, proposed or older-edition implementations · {mark("")} none '
        "found. A library with bindings counts for each language it can be called from.</p>",
    ]
    rows = []
    for m in index.methods:
        cov = coverage(m)
        rows.append([_method_link(path, m)] + [mark(cov[c]) for c in cols])
    parts.append(_table("coverage", ["Method"] + [esc(c) for c in cols], rows))
    for anchor, title, langs in LANGUAGE_SECTIONS:
        projects = [p for p in listed if langs & set(p["languages"])]
        if not projects:
            continue
        parts.append(f'<h2 id="{anchor}">{esc(title)} <span class="count">{len(projects)}</span></h2>')
        rows = []
        for p in projects:
            name = _project_link(path, p)
            if p["_group"] in GROUP_TAGS:
                name += " " + GROUP_TAGS[p["_group"]]
            methods = list(dict.fromkeys(i["_method"]["id"] for i in p["_impls"]
                                         if i["reference"] in i["_method"]["current"] and i["status"] == "available"
                                         and not i.get("_via")))
            covers = (", ".join(_method_link(path, index.method[mid]) for mid in methods) if methods else
                      '<span class="muted">older editions or unreleased code only</span>')
            rows.append([name, _how(p, langs, index, path), covers])
        parts.append(_table("langs", ["Project", "How it is used", "Current editions it implements"], rows))
    parts += [
        '<h2 id="across">Calling code across languages</h2>',
        "<p>A project can often be used from another language than its own. These general routes are not "
        "specific to any project; check that the code you call runs under them.</p>",
        "<ul>",
        "<li><strong>MATLAB code from Python.</strong> The "
        '<a href="https://www.mathworks.com/help/matlab/matlab-engine-for-python.html">MATLAB Engine API for '
        "Python</a> runs MATLAB functions from Python. It needs a MATLAB installation and licence. This is how a "
        "MATLAB toolbox such as SQAT or the Auditory Modeling Toolbox can be used from Python; without MATLAB, "
        "pySQAT is a Python port of SQAT, and torch_amt and NumpyLibforPsychoAcoustic port some AMT loudness "
        "models.</li>",
        '<li><strong>Octave code from Python.</strong> <a href="https://pypi.org/project/oct2py/">oct2py</a> runs '
        "GNU Octave functions from Python, without a MATLAB licence, for code that runs in Octave.</li>",
        "<li><strong>Python packages from MATLAB.</strong> MATLAB can "
        '<a href="https://www.mathworks.com/help/matlab/call-python-libraries.html">call Python libraries</a> '
        "directly, so a Python package such as MoSQITo can be used from MATLAB.</li>",
        "<li><strong>C libraries from other languages.</strong> A C library can be called from Python "
        '(<a href="https://docs.python.org/3/library/ctypes.html">ctypes</a> or cffi), Julia (<code>ccall</code>), '
        "Rust and most other languages. MetaSona's Python package loads its C library this way, and iso532-1-rs "
        "has a C interface for the same purpose.</li>",
        '<li><strong>Python from Julia.</strong> <a href="https://github.com/JuliaPy/PythonCall.jl">PythonCall.jl</a> '
        "calls Python packages from Julia.</li>",
        "</ul>",
    ]
    return layout(index, path, title="Psychoacoustic metrics by programming language",
                  description=("Which psychoacoustic metrics can be computed in Python, MATLAB, Octave, C, C++, Rust, "
                               "Julia and Pure Data, and how each open-source project is called."),
                  body="\n".join(parts), section="Languages")


PROJECT_COLUMNS = ["Project", "Language", "Licence", "Latest release", "Last commit"]


def _project_row(path: str, p: dict, last: str) -> list[str]:
    """A row of the projects tables: the kind of project goes under its name, and its activity under the date of
    its last commit."""
    return [f'{_project_link(path, p)}<br><span class="muted">{esc(PROJECT_KINDS[p["kind"]])}</span>',
            _langs(p["languages"]), esc(p["license"]), esc(release_text(p)),
            f'{esc(p["_last_commit"] or "unknown")}<br>{_activity_tag(p, short=True)}', last]


def projects_page(index: Index) -> str:
    path = PROJECTS
    langs = index.languages()
    parts = [
        "<h1>Projects</h1>",
        f'<p class="byline">{plural(len(index.projects), "project")} · {plural(len(langs), "language")}</p>',
        "<p>" + highlighted(index.super_projects(), lambda p: esc(p["name"]), esc)
        + " come first in every list and are in bold; then the other established projects, "
        "then newly released, developing and legacy ones. Tools that only call another project are listed under "
        "Others, and projects whose code could not "
        "be opened under Status unknown. “Last commit” is the last commit "
        f"on the default branch; a project is shown as inactive after {index.site.get('inactive_after_days', 365)} "
        "days without one, and listed as legacy after three years.</p>",
    ]
    for key, title in GROUP_HEADINGS:
        projects = index.group(key)
        if not projects or key in ("others", "unknown"):
            continue
        parts.append(f'<h2 id="{key}">{esc(title)} <span class="count">{len(projects)}</span></h2>')
        parts.append(f'<p class="muted">{esc(GROUPS[key])}</p>')
        rows = [_project_row(path, p, ", ".join(_method_link(path, m) for m in {
                    i["_method"]["id"]: i["_method"] for i in p["_impls"]}.values())) for p in projects]
        parts.append(_table("projects", PROJECT_COLUMNS + ["Covers"], rows))
    others = index.others()
    if others:
        parts.append(f'<h2 id="others">Others <span class="count">{len(others)}</span></h2>')
        parts.append(f'<p class="muted">{esc(GROUPS["others"])} They are not listed under the metrics.</p>')
        rows = [_project_row(path, p, join_words([_project_link(path, q) for q in {
                    i["_via"]["id"]: i["_via"] for i in p["_impls"]}.values()])) for p in others]
        parts.append(_table("projects", PROJECT_COLUMNS + ["Calls"], rows))
    unknown = index.group("unknown")
    if unknown:
        parts.append(f'<h2 id="unknown">Status unknown <span class="count">{len(unknown)}</span></h2>')
        parts.append(f'<p class="muted">{esc(GROUPS["unknown"])}</p>')
        rows = [_project_row(path, p, inline(first_sentence(p["claim"]))) for p in unknown]
        parts.append(_table("projects", PROJECT_COLUMNS + ["Claims"], rows))
    ld = [{"@type": "CollectionPage", "name": "Projects", "url": absolute(index, path),
           "mainEntity": {"@type": "ItemList", "numberOfItems": len(index.projects), "itemListElement": [
               {"@type": "ListItem", "position": n, "item": _software_ld(index, p)}
               for n, p in enumerate(index.projects_by_group(), 1)]}}]
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
        f'<p class="byline">{plural(len(docs), "standard document")} · {plural(len(papers), "model reference")}</p>',
        "<p>Every document the list refers to, newest first. Each implementation in the list is tied to one of "
        "these editions, so this is also a timeline of how the definitions have changed.</p>",
        f'<p class="small">All of them as BibTeX, with the papers that describe the listed software: '
        f'<a href="{relative(path, BIBTEX)}">{BIBTEX}</a>.</p>',
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
            rows.append([f'<span id="ref-{esc(r["id"])}"></span>' + (esc(month(r.get("date"))) or "—"),
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
             '<p class="byline">Notable changes to the list and to the projects it follows. '
             f'Also available as an <a href="{relative(path, "feed.xml")}">Atom feed</a>.</p>']
    for u in index.updates:
        parts.append(f'<section class="update" id="{esc(str(u["date"]))}">')
        parts.append(f'<h2>{esc(u["title"])}</h2>')
        parts.append(f'<p class="byline"><time datetime="{esc(str(u["date"]))}">{esc(long_date(u["date"]))}</time></p>')
        parts.append(blocks(u["body"]))
        parts.append("</section>")
    return layout(index, path, title="Updates", description=f"Notable changes to {index.site['name']}.",
                  body="\n".join(parts), section="Updates")


def about_page(index: Index) -> str:
    path = ABOUT
    site = index.site
    repo = esc(site["repository"])
    fams = join_words([f["name"].lower() for f in index.families])
    status_kind = {"available": "ok", "unreleased": "warn", "proposed": "neutral"}
    parts = [
        f"<h1>About {esc(site['name'])}</h1>",
        f'<p class="lead">{esc(introduce(site))}</p>',
        f"<p>{esc(name_note(site))}</p>",

        '<h2 id="scope">What is included</h2>',
        f"<p>Open-source code that computes a psychoacoustic metric and says which model or standard edition it "
        f"follows. The list covers {esc(fams)}, in any programming language.</p>",
        "<p>Not included: broadcast loudness (LUFS, ITU-R BS.1770, EBU R 128), speech intelligibility (SII, STI), "
        "codec and speech quality metrics (PEAQ, PESQ, ViSQOL), psychophysics experiment software, music "
        "sensory-dissonance models (Plomp–Levelt, Sethares, Vassilakis), feature extractors whose loudness or "
        "sharpness descriptors follow no named psychoacoustic model, and closed-source tools. The ISO 532 reference "
        "programs can be downloaded free of charge but may not be modified, so they are described on the standards' "
        "own entries rather than listed as projects. A project that only calls another listed project is included "
        "when it is an end-user application or an established library. Candidates that were reviewed and left out "
        f'are recorded, with the reason, in <a href="{repo}/blob/main/data/ignored.yaml">data/ignored.yaml</a>.</p>',
        '<h2 id="method">How entries are checked</h2>',
        "<p>Each entry is written from the project's own README, documentation, release notes, licence file and "
        "package metadata, and links to those sources. The list records what a project claims; it does not run "
        "the code, and listing a project is not an endorsement.</p>",
        "<p>Twice a month a GitHub Action refreshes repository dates, releases and package versions, searches GitHub "
        "and package registries for new candidate projects, and checks the ISO and Ecma catalogues for new "
        "editions. Dates and versions are updated directly; new candidates and editions go into one issue that a "
        "person reviews before anything is added.</p>",
        '<h2 id="status">Status of an implementation</h2>',
        _table("defs", ["Value", "Meaning"], [[_tag(k, status_kind[k]), esc(v)] for k, v in IMPL_STATUS_LONG.items()]),
        '<h2 id="validation">Validation evidence</h2>',
        "<p>As stated by each project. Where a project says what it compared its results with (MoSQITo, SQAT, the "
        "model authors' code or commercial software), the list names it, and each project page sets out the "
        "details under <em>How it was validated</em>. Agreement with another implementation shows that both "
        "compute the same values, not that either follows the standard: an error they share goes unnoticed.</p>",
        _table("defs", ["Value", "Meaning"], [[_tag(VALIDATION[k], VALIDATION_KIND[k]), esc(v)]
                                              for k, v in VALIDATION_LONG.items()]),
        '<h2 id="standing">Groups of projects</h2>',
        "<p>" + GROUP_RULE + ": " + highlighted(index.super_projects(), lambda p: esc(p["name"]), esc)
        + ". They are never listed as legacy, and neither are reference programs published with a standard, which "
        "are not expected to change.</p>",
        _table("defs", ["Group", "Meaning"], [[_tag(GROUP_NAMES[k], GROUP_KIND[k]), esc(v)]
                                              for k, v in GROUPS.items()]),
        '<h2 id="kinds">Kinds of project</h2>',
        "<p>What a project is, for someone who wants to use it. Each project page names its kind.</p>",
        _table("defs", ["Kind", "Meaning"], [[esc(PROJECT_KINDS[k]), esc(v)] for k, v in KINDS.items()]),
        '<h2 id="leads">Leads not yet verified</h2>',
        "<p>Candidates that may belong in the list but could not be checked yet. They are listed so that nobody "
        "has to rediscover them; nothing here has been confirmed.</p>",
        "<ul>" + "".join(f'<li><a href="{esc(l["url"])}">{esc(l["name"])}</a> {_langs(l.get("languages") or [])}: '
                         f'{inline(l["claim"])} <span class="muted">{inline(l["why"])}</span></li>'
                         for l in index.leads) + "</ul>",
        "<p>Not listed because they are closed source: MATLAB Audio Toolbox, HEAD acoustics ArtemiS SUITE, "
        "Simcenter Testlab, HBK BK Connect and Ansys Sound. Verification studies often use them as references.</p>",
        '<h2 id="data">Machine-readable data</h2>',
        f'<p>The <a href="{relative(path, AI)}">For AI</a> page describes every machine-readable form of the list '
        "and how to use it.</p>",
        "<ul>",
        f'<li><a href="{relative(path, "index.json")}">index.json</a>: the whole index as one JSON document.</li>',
        f'<li><a href="{relative(path, "llms.txt")}">llms.txt</a> and '
        f'<a href="{relative(path, "llms-full.txt")}">llms-full.txt</a>: summaries for language models, following '
        'the <a href="https://llmstxt.org/">llms.txt</a> proposal. Every page also has a Markdown version.</li>',
        f'<li><a href="{relative(path, "feed.xml")}">feed.xml</a>: Atom feed of updates.</li>',
        f'<li><a href="{relative(path, BIBTEX)}">{BIBTEX}</a>: every standard, model paper and software paper in '
        "the list, as BibTeX.</li>",
        f'<li><a href="{repo}/tree/main/data">Source data</a> and its '
        f'<a href="{repo}/blob/main/data/SCHEMA.md">schema</a>.</li>',
        "</ul>",
        ('<p>Visits to the website are counted with <a href="https://www.cloudflare.com/web-analytics/">Cloudflare '
         "Web Analytics</a>, which sets no cookies.</p>" if _analytics(site) else ""),
        '<h2 id="contributing">Contributing</h2>',
        f'<p>Corrections and new projects are welcome. Open an <a href="{repo}/issues/new/choose">issue</a>, or send a '
        f'pull request that adds or edits a file in <code>data/projects/</code>; '
        f'<a href="{repo}/blob/main/CONTRIBUTING.md">CONTRIBUTING.md</a> explains the format. '
        "Project authors are encouraged to check their own entry.</p>",
        '<h2 id="citing">Citing</h2>',
        f'<p>Please cite the list with the <a href="{repo}/blob/main/CITATION.cff">CITATION.cff</a> file and the date '
        "you accessed it, and cite the implementations you actually used: each project page says how, under "
        f'<em>How to cite</em>. The standards and papers are in <a href="{relative(path, BIBTEX)}">{BIBTEX}</a>.</p>',
        '<h2 id="licence">Licence</h2>',
        f"<p>Data, text and code are released under the {esc(site['license'])} licence.</p>",
        f"<p>{credit(index)}</p>",
    ]
    return layout(index, path, title="About", description=f"Scope, method, definitions and data access of {site['name']}.", body="\n".join(parts), section="About")


def _message_box(index: Index) -> str:
    """A form that opens the visitor's message as a prefilled GitHub issue (no JavaScript, no other service)."""
    repo = esc(index.site["repository"])
    return "\n".join([
        '<section class="message" aria-labelledby="message">',
        '<h2 id="message">Ask a question or leave a message</h2>',
        "<p>Questions, corrections and suggestions are welcome, from users and from project authors alike. "
        "Messages are public.</p>",
        f'<form class="message-form" action="{repo}/issues/new" method="get" target="_blank" rel="noopener">'
        '<label for="msg-title">Subject</label>'
        '<input id="msg-title" name="title" required maxlength="140" '
        'placeholder="For example: another implementation of ISO 532-1">'
        '<label for="msg-body">Message</label>'
        '<textarea id="msg-body" name="body" rows="5" required '
        'placeholder="What would you like to ask or tell? Links to code or documentation help."></textarea>'
        '<p class="form-row"><button type="submit">Continue on GitHub</button> '
        '<span class="muted small">Opens your message as a new GitHub issue, ready to send. You need a GitHub '
        "account.</span></p></form>",
        "</section>",
    ])


def faq_page(index: Index) -> str:
    path = FAQ
    pairs = faq(index, lambda p: _project_link(path, p), lambda m: _method_link(path, m, m["title"]), esc,
                lambda target, label: f'<a href="{relative(path, target)}">{esc(label)}</a>')
    parts = ["<h1>Questions and answers</h1>",
             '<p class="byline">Ask your own question below; the answers further down are generated from the list '
             "data, so they always match the tables.</p>",
             _message_box(index)]
    for n, (q, a) in enumerate(pairs, 1):
        parts.append(f'<h2 id="q{n}">{esc(q)}</h2>')
        parts.append(f"<p>{a}</p>")
    side = ('<aside class="sidebar" aria-label="Questions">' + _side("Leave a message", [], href="#message")
            + _side("Questions", [(f"#q{n}", esc(q), False) for n, (q, _) in enumerate(pairs, 1)]) + "</aside>")
    ld = [{"@type": "FAQPage", "url": absolute(index, path), "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": plain(re.sub(r"<[^>]+>", "", a))}}
        for q, a in pairs]}]
    return layout(index, path, title="Frequently asked questions about open-source psychoacoustic metrics",
                  description=("Which open-source code to use for ISO 532, ECMA-418-2, DIN 45692 and other "
                               "psychoacoustic metrics, in which languages, and how the list is kept accurate."),
                  body="\n".join(parts), section="FAQ", jsonld=ld, side=side)


def ai_page(index: Index) -> str:
    path = AI
    intro, sections = ai_guide(index)
    parts = ["<h1>For AI agents and language models</h1>",
             f'<p class="byline">Machine-readable access to the list · data as of {esc(long_date(index.as_of()))}</p>',
             f'<p class="lead">{inline(intro)}</p>']
    for anchor, heading, items in sections:
        parts.append(f'<h2 id="{anchor}">{esc(heading)}</h2>')
        parts.append("<ul>" + "".join(f"<li>{inline(item)}</li>" for item in items) + "</ul>")
    base = index.site["base_url"]
    side = ('<aside class="sidebar" aria-label="For AI">'
            + _side("On this page", [(f"#{a}", esc(h), False) for a, h, _ in sections])
            + _side("Files", [(base + f, f, False) for f in ("llms.txt", "llms-full.txt", "index.json", BIBTEX,
                                                              "sitemap.xml", "feed.xml")])
            + "</aside>")
    ld = [{"@type": "WebPage", "name": "For AI agents and language models", "url": absolute(index, path),
           "description": intro}]
    return layout(index, path, title="For AI agents and language models",
                  description=f"Machine-readable access to {index.site['name']}: llms.txt, llms-full.txt, index.json "
                              "and a Markdown version of every page.",
                  body="\n".join(parts), section="For AI", jsonld=ld, side=side)


def not_found(index: Index) -> str:
    # Served from any depth, so links are absolute.
    base = esc(index.site["base_url"])
    body = (f'<h1>Page not found</h1><p>The page you asked for does not exist. Start from the '
            f'<a href="{base}">home page</a> or the <a href="{base}projects/">list of projects</a>.</p>')
    page = layout(index, "404.html", title="Page not found", description="Page not found.", body=body, section="",
                  markdown=False, side="")
    return re.sub(r'href="(?!https?:|#|mailto:)([^"]*)"', lambda m: f'href="{base}{m.group(1)}"', page)
