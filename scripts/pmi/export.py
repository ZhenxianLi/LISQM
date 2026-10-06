"""Machine-readable output: index.json, the Atom feed, sitemap.xml and robots.txt."""

from __future__ import annotations

import json
from xml.sax.saxutils import escape as xml_escape

from .data import GROUPS, IMPL_STATUS_LONG, STANDING, VALIDATION_LONG, Index
from .describe import coverage
from .paths import (ABOUT, AI, FAQ, HOME, LANGUAGES, METRICS, PROJECTS, STANDARDS, UPDATES, absolute, method_path,
                    project_path)
from .text import blocks, date_str, plain


def _clean(d: dict) -> dict:
    """Drop derived ('_') keys and empty values, and turn dates into strings."""
    out = {}
    for k, v in d.items():
        if k.startswith("_") or v in (None, "", [], {}):
            continue
        if isinstance(v, dict):
            v = _clean(v)
        elif isinstance(v, list):
            v = [_clean(x) if isinstance(x, dict) else x for x in v]
        elif not isinstance(v, (str, int, float, bool)):
            v = date_str(v)
        out[k] = v
    return out


def index_json(index: Index) -> str:
    site = index.site
    methods = []
    for m in index.methods:
        d = _clean(m)
        d["url"] = absolute(index, method_path(m))
        d["coverage"] = coverage(m)
        d["implementations"] = [
            {"project": i["_project"]["id"], **_clean({k: v for k, v in i.items() if k != "method"})}
            for i in m["_impls"]]
        if m["_via_impls"]:  # tools that call one of the implementations above
            d["also_through"] = [
                {"project": i["_project"]["id"], **_clean({k: v for k, v in i.items() if k != "method"})}
                for i in m["_via_impls"]]
        methods.append(d)
    projects = []
    for p in index.projects_by_group():
        d = _clean({k: v for k, v in p.items() if k != "manual"})
        d["url"] = absolute(index, project_path(p))
        d["last_commit"] = p["_last_commit"]
        d["latest_release"] = p["_release"]
        d["prerelease"] = p["_prerelease"]
        d["activity"] = p["_activity"]
        d["archived"] = p["_archived"]
        d["stars"] = p["_stars"]
        d["group"] = p["_group"]
        d["most_widely_used"] = p["_mainstream"]
        if p["_others"]:
            d["calls"] = list(dict.fromkeys(i["_via"]["id"] for i in p["_impls"] if i.get("_via")))
        projects.append(d)
    doc = {
        "name": site["name"],
        "full_name": site["title"],
        "tagline": site["tagline"],
        "version": str(site.get("version", "")),
        "description": plain(site["description"]),
        "url": site["base_url"],
        "repository": site["repository"],
        "license": site["license"],
        "maintainer": site["maintainer"],
        "credit": site["credit"],
        "as_of": index.as_of(),
        "schema": f"{site['repository']}/blob/main/data/SCHEMA.md",
        "counts": {"methods": len(index.methods), "projects": len(index.projects),
                   "references": len(index.references)},
        "ordering": ("Implementations and projects are listed by group: established, newly released, developing, legacy, "
                     "others. Newly released projects were first released less than about a year ago and are not yet "
                     "widely used in the community. Legacy projects are archived or have had no commit for three "
                     "years or more; the most widely used projects (most_widely_used: true) and reference programs "
                     "are never legacy. Within each group, projects that are still active and widely recognised "
                     "come first. Projects in the others group do not compute the metrics themselves; they call "
                     "another indexed project (listed in calls), and their rows appear under also_through instead "
                     "of implementations."),
        "definitions": {"standing": STANDING, "group": GROUPS, "status": IMPL_STATUS_LONG,
                        "validation": VALIDATION_LONG,
                        "coverage": {"current": "an available implementation of the current edition",
                                     "new": "an available implementation of the current edition, but only from "
                                            "newly released projects",
                                     "partial": "only unreleased, proposed or older-edition implementations",
                                     "": "none found"}},
        "families": [_clean(f) for f in index.families],
        "methods": methods,
        "references": [_clean(r) for r in index.references],
        "projects": projects,
        "gaps": [m["id"] for m in index.gaps()],
        "newly_released_only": [m["id"] for m in index.new_only()],
        "leads": [_clean(l) for l in index.leads],
        "updates": [_clean(u) for u in index.updates],
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def atom_feed(index: Index) -> str:
    site = index.site
    feed_url = site["base_url"] + "feed.xml"
    updated = date_str(index.updates[0]["date"]) if index.updates else index.as_of()
    entries = []
    for u in index.updates:
        day = date_str(u["date"])
        link = f"{absolute(index, UPDATES)}#{day}"
        entries.append(f"""  <entry>
    <title>{xml_escape(u['title'])}</title>
    <link href="{xml_escape(link)}"/>
    <id>{xml_escape(link)}</id>
    <updated>{day}T00:00:00Z</updated>
    <content type="html">{xml_escape(blocks(u['body']))}</content>
  </entry>""")
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{xml_escape(site['name'])}: {xml_escape(site['title'])}</title>
  <subtitle>{xml_escape(plain(site['description']))}</subtitle>
  <link href="{xml_escape(feed_url)}" rel="self"/>
  <link href="{xml_escape(site['base_url'])}"/>
  <id>{xml_escape(feed_url)}</id>
  <updated>{updated}T00:00:00Z</updated>
  <author><name>{xml_escape(site['maintainer']['name'])}</name></author>
{chr(10).join(entries)}
</feed>
"""


def sitemap(index: Index) -> str:
    as_of = index.as_of()
    urls = [(absolute(index, p), as_of) for p in (HOME, METRICS, PROJECTS, LANGUAGES, STANDARDS, UPDATES, ABOUT,
                                                 FAQ, AI)]
    urls += [(absolute(index, method_path(m)), as_of) for m in index.methods]
    urls += [(absolute(index, project_path(p)), max(date_str(p["checked"]), (p["_last_commit"] or "")[:10]))
             for p in index.projects]
    body = "\n".join(f"  <url><loc>{xml_escape(u)}</loc><lastmod>{d}</lastmod></url>" for u, d in urls)
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "\n</urlset>\n")


def robots(index: Index) -> str:
    return ("# Crawlers, including AI crawlers, are welcome. For AI agents: ai.html (or ai.md), llms.txt, llms-full.txt\n"
            "# and index.json.\n"
            "User-agent: *\nAllow: /\n\n"
            f"Sitemap: {index.site['base_url']}sitemap.xml\n")
