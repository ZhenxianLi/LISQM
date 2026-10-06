"""HTML output: static, pre-rendered pages (no JavaScript needed) with Markdown twins and JSON-LD.

The look is deliberately plain: a reading column, serif text, tables with thin rules, ordinary links.
"""

from __future__ import annotations

import json
import re

from .data import (IMPL_STATUS_LONG, PROJECT_KINDS, REF_STATUS, REGISTRIES, VALIDATION, VALIDATION_LONG,
                   Index)
from .describe import (COVERAGE_COLUMNS, activity_text, by_language, coverage, dedupe, faq, in_short,
                       ref_status, release_text)
from .paths import (ABOUT, FAQ, HOME, PROJECTS, STANDARDS, UPDATES, absolute, md_twin, method_path,
                    project_path, relative)
from .text import blocks, esc, inline, join_words, long_date, month, plain, plural

NAV = [("Metrics", HOME), ("Projects", PROJECTS), ("Standards", STANDARDS), ("Updates", UPDATES), ("About", ABOUT)]


# ---------------------------------------------------------------------------------------------- layout

def layout(index: Index, path: str, *, title: str, description: str, body: str, section: str,
           jsonld: list[dict] | None = None, og_type: str = "website", markdown: bool = True) -> str:
    site = index.site
    rel = lambda target: relative(path, target)  # noqa: E731
    canonical = absolute(index, path)
    current = ' aria-current="page"'
    nav = "\n".join(f'    <a href="{rel(target)}"{current if label == section else ""}>{label}</a>'
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
<div class="wrap">
<header class="site">
  <a class="site-name" href="{rel(HOME)}">{esc(site['title'])}</a>
  <nav aria-label="Site">
{nav}
  </nav>
</header>
<main id="content">
{body}
</main>
<footer class="site">
  <p>Data as of {esc(long_date(index.as_of()))}. Facts are taken from each project's own documentation and
  package metadata; corrections are welcome on <a href="{esc(site['repository'])}">GitHub</a>.</p>
  <p><a href="{rel('index.json')}">JSON</a> · <a href="{rel('llms.txt')}">llms.txt</a> ·
  {md_foot}<a href="{rel('feed.xml')}">Atom feed</a> ·
  Maintained by {esc(site['maintainer']['name'])} · {esc(site['license'])} licence</p>
</footer>
</div>
</body>
</html>
"""


def _project_link(path: str, p: dict) -> str:
    return f'<a href="{relative(path, project_path(p))}">{esc(p["name"])}</a>'


def _method_link(path: str, m: dict, label: str | None = None) -> str:
    return f'<a href="{relative(path, method_path(m))}">{esc(label or m["name"])}</a>'


def _ref_link(r: dict) -> str:
    url = r.get("url") or (f"https://doi.org/{r['doi']}" if r.get("doi") else "")
    return f'<a href="{esc(url)}">{esc(r["label"])}</a>' if url else esc(r["label"])


def _lang(langs: list[str]) -> str:
    return f'<span class="lang">{esc(", ".join(langs))}</span>'


def _functions(i: dict) -> str:
    return ", ".join(f"<code>{esc(f)}</code>" for f in i.get("functions") or [])


def _status_note(i: dict) -> str:
    """Notes cell: release status first (only when not available), then the free-text note."""
    status = ""
    if i["status"] == "unreleased":
        status = '<em class="status">Unreleased.</em>'
    elif i["status"] == "proposed":
        status = '<em class="status">Proposed, not merged.</em>'
    if status and i.get("link"):
        status = f'<a href="{esc(i["link"])}">{status}</a>'
    return " ".join(x for x in (status, inline(i.get("note") or "")) if x)


def _edition_cell(i: dict, label: str | None = None) -> str:
    """Edition label with scope and first version underneath."""
    cell = esc(label or i["_ref"]["label"])
    extra = [esc(i["scope"])] if i.get("scope") else []
    if i.get("since"):
        extra.append(f"since {esc(i['since'])}")
    if extra:
        cell += f'<br><span class="muted">{"; ".join(extra)}</span>'
    return cell


def _validation(i: dict) -> str:
    v = i["validation"]
    return f'<span title="{esc(VALIDATION_LONG[v])}">{esc(VALIDATION[v])}</span>'


def _table(cls: str, head: list[str], rows: list[list[str]], caption: str = "") -> str:
    """A table that stacks into labelled blocks on narrow screens (labels come from the header)."""
    cap = f"<caption>{caption}</caption>" if caption else ""
    thead = "".join(f'<th scope="col">{h}</th>' for h in head)
    body = []
    for row in rows:
        cells = "".join(f'<td data-label="{esc(plain(h))}">{c or "—"}</td>' for h, c in zip(head, row))
        body.append(f"<tr>{cells}</tr>")
    return (f'<div class="wide"><table class="{cls}">{cap}<thead><tr>{thead}</tr></thead>\n'
            f'<tbody>\n' + "\n".join(body) + "\n</tbody></table></div>")


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


# ---------------------------------------------------------------------------------------------- pages

def home(index: Index) -> str:
    path = HOME
    site = index.site
    name = lambda p: _project_link(path, p)  # noqa: E731
    toc = " · ".join(f'<a href="#{esc(f["id"])}">{esc(f["name"])}</a>' for f, _ in index.families_with_methods())
    parts = [
        "<article>",
        "<h1>Open-source implementations of psychoacoustic metrics</h1>",
        f'<p class="byline">Updated {esc(long_date(index.as_of()))} · {plural(len(index.methods), "method")} · '
        f'{plural(len(index.projects), "project")} · {plural(len(index.languages()), "language")}</p>',
        "<p>This index lists open-source code that computes psychoacoustic metrics, such as loudness, sharpness, "
        "roughness, fluctuation strength, tonality, impulsiveness and psychoacoustic annoyance. For each "
        "implementation it records which standard edition or model paper the code follows. Standards such as "
        "ECMA-418-2 and ISO 532 change between editions, so two tools that both say they implement a standard can "
        "give different results.</p>",
        "<p>Projects in every programming language are included. Each entry links to the project and to the "
        "documentation its facts were taken from. Validation is reported as each project describes it. "
        "Repository and package dates are refreshed every week.</p>",
        f'<p class="toc">Contents: {toc} · <a href="#coverage">Coverage by language</a> · <a href="#gaps">Gaps</a> · '
        f'<a href="#updates">Updates</a></p>',
    ]
    for fam, methods in index.families_with_methods():
        parts.append(f'<h2 id="{esc(fam["id"])}">{esc(fam["name"])}</h2>')
        parts.append(f'<p class="family">{inline(fam["summary"])}</p>')
        rows = []
        for m in methods:
            groups = by_language(m["_current_impls"], name)
            cell = "<br>".join(f'<span class="lang">{esc(lang)}</span> {", ".join(names)}'
                               for lang, names in groups) or '<span class="muted">none found</span>'
            older = [i for i in dedupe(m["_older_impls"]) if i["_ref"]["status"] != "in-development"]
            if older:
                cell += ('<br><span class="older">Earlier editions: ' + ", ".join(
                    f'{name(i["_project"])} ({esc(i["_ref"]["label"])})' for i in older) + "</span>")
            rows.append([_method_link(path, m),
                         esc(join_words([index.ref[r]["label"] for r in m["current"]])), cell])
        parts.append(_table("overview", ["Method", "Current edition", "Implementations of the current edition"],
                            rows))
    cols = [c for c, _ in COVERAGE_COLUMNS] + ["Other"]
    marks = {"current": ("●", "available implementation of the current edition"),
             "partial": ("○", "only unreleased, proposed or older-edition implementations"),
             "": ("—", "none found")}
    parts.append('<h2 id="coverage">Coverage by language</h2>')
    parts.append("<p>Which languages have an implementation of each method. ● an available implementation of the "
                 "current edition; ○ only unreleased, proposed or older-edition implementations; — none found. "
                 "A library with bindings counts for each language it can be called from.</p>")
    rows = []
    for m in index.methods:
        cov = coverage(m)
        rows.append([_method_link(path, m)] + [f'<span class="mark" title="{esc(marks[cov[c]][1])}">'
                                              f'{marks[cov[c]][0]}</span>' for c in cols])
    parts.append(_table("coverage", ["Method"] + [esc(c) for c in cols], rows))
    gaps = index.gaps()
    parts.append('<h2 id="gaps">Gaps</h2>')
    if gaps:
        parts.append("<p>No available open-source implementation of the current edition has been found for:</p>")
        parts.append("<ul>" + "".join(f"<li>{_method_link(path, m, m['title'])}</li>" for m in gaps) + "</ul>")
    else:
        parts.append("<p>Every method in the index has at least one available open-source implementation of its "
                     "current edition.</p>")
    parts.append(f'<p>Looking for a quick answer? See the <a href="{relative(path, FAQ)}">frequently asked questions</a>.</p>')
    parts.append(f'<p>Know of an implementation that is missing? <a href="{esc(site["repository"])}/issues/new/choose">'
                 "Open an issue</a> or send a pull request.</p>")
    parts.append('<h2 id="updates">Recent updates</h2>')
    parts.append('<ul class="updates">' + "".join(
        f'<li><a href="{relative(path, UPDATES)}#{esc(str(u["date"]))}">{esc(long_date(u["date"]))}</a>: '
        f'{esc(u["title"])}</li>' for u in index.updates[:5]) + "</ul>")
    parts.append("</article>")

    ld = [
        {"@type": "WebSite", "name": site["title"], "url": site["base_url"], "description": plain(site["description"])},
        {"@type": "Dataset", "name": site["title"], "description": plain(site["description"]),
         "url": site["base_url"], "license": "https://opensource.org/licenses/MIT",
         "creator": {"@type": "Person", "name": site["maintainer"]["name"],
                     "url": f"https://github.com/{site['maintainer']['github']}"},
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
                   f"{join_words(index.languages())}. Updated {index.as_of()}.")
    return layout(index, path, title=site["title"],
                  description=description, body="\n".join(parts), section="Metrics", jsonld=ld)


def method_page(index: Index, m: dict) -> str:
    path = method_path(m)
    name = lambda p: _project_link(path, p)  # noqa: E731
    fam = m["_family"]
    byline = [f"Unit: {esc(m['unit'])}"]
    if m.get("aka"):
        byline.append("Also known as " + esc(", ".join(m["aka"])))
    parts = [
        "<article>",
        f'<p class="crumbs"><a href="{relative(path, HOME)}#{esc(fam["id"])}">{esc(fam["name"])}</a></p>',
        f"<h1>{esc(m['title'])}</h1>",
        f'<p class="byline">{" · ".join(byline)}</p>',
        blocks(m["summary"]),
        f'<p class="in-short"><strong>In short.</strong> {in_short(index, m, name, esc)}</p>',
    ]
    if m.get("notes"):
        parts.append(blocks(m["notes"]))

    parts.append('<h2 id="editions">Editions and who implements them</h2>')
    rows = []
    for rid in reversed(m["references"]):
        r = index.ref[rid]
        impls = dedupe([i for i in m["_impls"] if i["reference"] == rid])
        who = ", ".join(name(i["_project"]) + ("" if i["status"] == "available" else
                                                f' <em class="status">({esc(i["status"])})</em>') for i in impls)
        status = esc(ref_status(r))
        if r.get("revision"):
            status += f'<br><span class="muted">{inline(r["revision"])}</span>'
        cls = "" if r["status"] in ("current", "published", "in-development") else "old"
        label = f'<span class="{cls}">{_ref_link(r)}</span>' if cls else _ref_link(r)
        rows.append([esc(month(r.get("date"))) or "—", label, status,
                     inline((m.get("edition_notes") or {}).get(rid, "")), who])
    parts.append(_table("editions", ["Date", "Edition", "Status", "What changed", "Implemented by"], rows))

    parts.append('<h2 id="implementations">Implementations</h2>')
    if m["_impls"]:
        rows = [[f'{name(i["_project"])}<br>{_lang(i["_project"]["languages"])}', _edition_cell(i),
                 _functions(i), _validation(i), _status_note(i)] for i in m["_impls"]]
        parts.append(_table("impls", ["Project", "Edition", "Functions", "Validation (as stated)", "Notes"], rows))
        parts.append(f'<p class="muted small">Validation is what each project states about its own testing; '
                     f'see <a href="{relative(path, ABOUT)}#validation">the definitions</a>.</p>')
    else:
        parts.append("<p>No open-source implementation has been found yet. If you know one, please "
                     f'<a href="{esc(index.site["repository"])}/issues/new/choose">open an issue</a>.</p>')
    if m.get("see_also"):
        parts.append("<p>See also: " + ", ".join(_method_link(path, index.method[s], index.method[s]["title"])
                                                  for s in m["see_also"]) + ".</p>")
    parts.append('<h2 id="references">References</h2>')
    parts.append(_ref_list([index.ref[r] for r in m["references"]]))
    parts.append("</article>")

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
    facts.append(("Language", esc(", ".join(p["languages"]))))
    facts.append(("Kind", esc(PROJECT_KINDS[p["kind"]])))
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
    facts.append(("Last commit", f'{esc(p["_last_commit"] or "unknown")} ({esc(activity_text(p))})'))
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

    parts = [
        "<article>",
        f'<p class="crumbs"><a href="{relative(path, PROJECTS)}">Projects</a></p>',
        f"<h1>{esc(p['name'])}</h1>",
        f'<p class="byline">{esc(", ".join(p["languages"]))} · {esc(PROJECT_KINDS[p["kind"]].lower())} · '
        f'{esc(activity_text(p))}</p>',
        blocks(p["summary"]),
        '<dl class="facts">' + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in facts) + "</dl>",
        '<h2 id="implements">What it implements</h2>',
    ]
    rows = [[_method_link(path, i["_method"]), _edition_cell(i), _functions(i), _validation(i), _status_note(i)]
            for i in p["_impls"]]
    parts.append(_table("impls", ["Metric", "Edition", "Functions", "Validation (as stated)", "Notes"], rows))
    if p.get("notes"):
        parts.append('<h2 id="notes">Notes</h2>')
        parts.append("<ul>" + "".join(f"<li>{inline(n)}</li>" for n in p["notes"]) + "</ul>")
    if p.get("caveats"):
        parts.append('<h2 id="caveats">Before you rely on it</h2>')
        parts.append("<ul>" + "".join(f"<li>{inline(c)}</li>" for c in p["caveats"]) + "</ul>")
    parts.append('<h2 id="sources">Sources</h2>')
    parts.append('<ol class="refs">' + "".join(f'<li><a href="{esc(s)}">{esc(s)}</a></li>' for s in p["sources"])
                 + "</ol>")
    parts.append("</article>")
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
        "<article>",
        "<h1>Projects</h1>",
        f'<p class="byline">{plural(len(index.projects), "project")} · {plural(len(langs), "language")}</p>',
        "<p>Grouped by the language you call them from; a project that offers several languages appears in each "
        "group. “Activity” is computed from the last commit on the default branch: a project is shown as inactive "
        f"after {index.site.get('inactive_after_days', 365)} days without a commit.</p>",
        '<p class="toc">Languages: ' + " · ".join(f'<a href="#lang-{esc(l.lower())}">{esc(l)}</a>' for l in langs)
        + "</p>",
    ]
    for lang in langs:
        projects = sorted((p for p in index.projects if lang in p["languages"]), key=lambda p: p["name"].lower())
        parts.append(f'<h2 id="lang-{esc(lang.lower())}">{esc(lang)}</h2>')
        rows = [[_project_link(path, p), esc(PROJECT_KINDS[p["kind"]]), esc(p["license"]), esc(release_text(p)),
                 esc(p["_last_commit"] or "unknown") + (f'<br><span class="muted">{esc(activity_text(p))}</span>'
                                                         if p["_activity"] != "active" else ""),
                 ", ".join(_method_link(path, m) for m in {i["_method"]["id"]: i["_method"]
                                                           for i in p["_impls"]}.values())]
                for p in projects]
        parts.append(_table("projects", ["Project", "Kind", "Licence", "Latest release", "Last commit", "Covers"], rows))
    parts.append("</article>")
    ld = [{"@type": "CollectionPage", "name": "Projects", "url": absolute(index, path),
           "mainEntity": {"@type": "ItemList", "numberOfItems": len(index.projects), "itemListElement": [
               {"@type": "ListItem", "position": n, "item": _software_ld(index, p)}
               for n, p in enumerate(sorted(index.projects, key=lambda p: p["name"].lower()), 1)]}}]
    return layout(index, path, title="Projects that implement psychoacoustic metrics",
                  description=(f"{len(index.projects)} open-source projects implementing psychoacoustic metrics in "
                               f"{join_words(langs)}, with licence, latest release and activity."),
                  body="\n".join(parts), section="Projects", jsonld=ld)


def standards_page(index: Index) -> str:
    path = STANDARDS
    docs = [r for r in index.references if r["kind"] not in ("paper", "book", "thesis")]
    papers = [r for r in index.references if r["kind"] in ("paper", "book", "thesis")]
    parts = [
        "<article>",
        "<h1>Standards and models</h1>",
        f'<p class="byline">{plural(len(docs), "standard document")} · {plural(len(papers), "model reference")}</p>',
        "<p>Every document the index refers to, newest first. Each implementation in the index is tied to one of "
        "these editions, so this is also a timeline of how the definitions have changed.</p>",
    ]
    for title, anchor, refs in (("Standards and regulations", "standards", docs),
                                ("Model papers, books and theses", "models", papers)):
        parts.append(f'<h2 id="{anchor}">{title}</h2>')
        rows = []
        for r in sorted(refs, key=lambda r: (str(r.get("date") or "9999"), r["label"]), reverse=True):
            note = f'<br><span class="muted">{inline(r["revision"])}</span>' if r.get("revision") else ""
            cls = "old" if r["status"] in ("superseded", "withdrawn") else ""
            rows.append([esc(month(r.get("date"))) or "—",
                         (f'<span class="{cls}">{_ref_link(r)}</span>' if cls else _ref_link(r))
                         + f'<br><span class="muted">{esc(r["title"])}</span>',
                         esc(REF_STATUS[r["status"]]) + note,
                         ", ".join(_method_link(path, m) for m in r["_methods"])])
        parts.append(_table("standards", ["Date", "Document", "Status", "Used by"], rows))
    parts.append("</article>")
    return layout(index, path, title="Standards and model papers for psychoacoustic metrics",
                  description=("Timeline of ISO 532, ECMA-418-1, ECMA-418-2, DIN 45692, DIN 45681, ISO/TS 20065, "
                               "ISO 1996-2, ISO 226 and the model papers behind psychoacoustic metrics, with status."),
                  body="\n".join(parts), section="Standards")


def updates_page(index: Index) -> str:
    path = UPDATES
    parts = ["<article>", "<h1>Updates</h1>",
             '<p class="byline">Notable changes to the index and to the projects it follows. '
             f'Also available as an <a href="{relative(path, "feed.xml")}">Atom feed</a>.</p>']
    for u in index.updates:
        parts.append(f'<section class="update" id="{esc(str(u["date"]))}">')
        parts.append(f'<h2>{esc(u["title"])}</h2>')
        parts.append(f'<p class="byline"><time datetime="{esc(str(u["date"]))}">{esc(long_date(u["date"]))}</time></p>')
        parts.append(blocks(u["body"]))
        parts.append("</section>")
    parts.append("</article>")
    return layout(index, path, title="Updates", description="Notable changes to the Psychoacoustic Metrics Index.",
                  body="\n".join(parts), section="Updates")


def about_page(index: Index) -> str:
    path = ABOUT
    site = index.site
    repo = esc(site["repository"])
    fams = join_words([f["name"].lower() for f in index.families])
    parts = [
        "<article>",
        "<h1>About this index</h1>",
        f"<p>{esc(site['description'])}</p>",
        '<h2 id="scope">What is included</h2>',
        f"<p>Open-source code that computes a psychoacoustic metric and says which model or standard edition it "
        f"follows. The index covers {esc(fams)}, in any programming language.</p>",
        "<p>Not included: broadcast loudness (LUFS, ITU-R BS.1770, EBU R 128), speech intelligibility (SII, STI), "
        "codec and speech quality metrics (PEAQ, PESQ, ViSQOL), psychophysics experiment software, music "
        "sensory-dissonance models (Plomp–Levelt, Sethares, Vassilakis), feature extractors whose loudness or "
        "sharpness descriptors follow no named psychoacoustic model, and closed-source tools. The ISO 532 reference "
        "programs can be downloaded free of charge but may not be modified, so they are described on the standards' "
        "own entries rather than listed as projects. Candidates that were reviewed and left out are recorded, with "
        f'the reason, in <a href="{repo}/blob/main/data/ignored.yaml">data/ignored.yaml</a>.</p>',
        '<h2 id="method">How entries are checked</h2>',
        "<p>Each entry is written from the project's own README, documentation, release notes, licence file and "
        "package metadata, and links to those sources. The index records what a project claims; it does not run "
        "the code, and listing a project is not an endorsement.</p>",
        "<p>Every week a GitHub Action refreshes repository dates, releases and package versions, searches GitHub "
        "and package registries for new candidate projects, and checks the ISO and Ecma catalogues for new "
        "editions. Its findings go into one issue that a person reviews before anything is added or changed.</p>",
        '<h2 id="status">Status of an implementation</h2>',
        _table("defs", ["Value", "Meaning"], [[esc(k), esc(v)] for k, v in IMPL_STATUS_LONG.items()]),
        '<h2 id="validation">Validation evidence</h2>',
        "<p>As stated by each project:</p>",
        _table("defs", ["Value", "Meaning"], [[esc(VALIDATION[k]), esc(v)] for k, v in VALIDATION_LONG.items()]),
        '<h2 id="leads">Leads not yet verified</h2>',
        "<p>Candidates that may belong in the index but could not be checked yet. They are listed so that nobody "
        "has to rediscover them; nothing here has been confirmed.</p>",
        "<ul>" + "".join(f'<li><a href="{esc(l["url"])}">{esc(l["name"])}</a> '
                         f'<span class="lang">{esc(", ".join(l.get("languages") or []))}</span>: {inline(l["claim"])} '
                         f'<span class="muted">{inline(l["why"])}</span></li>' for l in index.leads) + "</ul>",
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
        f"<p>Data, text and code are released under the {esc(site['license'])} licence. Maintained by "
        f'<a href="https://github.com/{esc(site["maintainer"]["github"])}">{esc(site["maintainer"]["name"])}</a>.</p>',
        "</article>",
    ]
    return layout(index, path, title="About", description="Scope, method, definitions and data access of the "
                  "Psychoacoustic Metrics Index.", body="\n".join(parts), section="About")


def faq_page(index: Index) -> str:
    path = FAQ
    pairs = faq(index, lambda p: _project_link(path, p), lambda m: _method_link(path, m, m["title"]), esc)
    parts = ["<article>", "<h1>Frequently asked questions</h1>",
             '<p class="byline">Answers are generated from the index data, so they always match the tables.</p>']
    for n, (q, a) in enumerate(pairs, 1):
        parts.append(f'<h2 id="q{n}">{esc(q)}</h2>')
        parts.append(f"<p>{a}</p>")
    parts.append("</article>")
    ld = [{"@type": "FAQPage", "url": absolute(index, path), "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": plain(re.sub(r"<[^>]+>", "", a))}}
        for q, a in pairs]}]
    return layout(index, path, title="Frequently asked questions about open-source psychoacoustic metrics",
                  description=("Which open-source code implements ISO 532, ECMA-418-1, ECMA-418-2, DIN 45692 and other "
                               "psychoacoustic metrics, in Python, MATLAB, C/C++ and other languages."),
                  body="\n".join(parts), section="", jsonld=ld)


def not_found(index: Index) -> str:
    # Served from any depth, so links are absolute.
    base = esc(index.site["base_url"])
    body = (f'<article><h1>Page not found</h1><p>The page you asked for does not exist. Start from the '
            f'<a href="{base}">index of metrics</a> or the <a href="{base}projects/">list of projects</a>.</p></article>')
    page = layout(index, "404.html", title="Page not found", description="Page not found.", body=body, section="",
                  markdown=False)
    return re.sub(r'href="(?!https?:|#|mailto:)([^"]*)"', lambda m: f'href="{base}{m.group(1)}"', page)
