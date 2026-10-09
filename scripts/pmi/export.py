"""Machine-readable output: index.json, references.bib, the Atom feed, sitemap.xml and robots.txt."""

from __future__ import annotations

import json
import re
from xml.sax.saxutils import escape as xml_escape

from .data import ACCESS, GROUPS, IMPL_STATUS_LONG, KINDS, STANDING, VALIDATION_LONG, Index, update_anchor
from .describe import coverage
from .paths import (ABOUT, AI, FAQ, HOME, LANGUAGES, MAP, METRICS, PROJECTS, STANDARDS, UPDATES, absolute,
                    metric_path, project_path)
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


def _implementation(i: dict) -> dict:
    """An implementation row as exported: its fields, the code it was ported from (also when that comes from the
    project's `based_on`), and how each comparison with related code relates to it."""
    d = {"project": i["_project"]["id"], **_clean({k: v for k, v in i.items() if k != "metric"})}
    if i["_derived_ids"]:
        d["derived_from"] = list(i["_derived_ids"])
    relations = {cid: kind + (f":{origin['id']}" if origin else "") for cid, (kind, origin) in i["_relation"].items()}
    if relations:
        d["comparison_relations"] = relations
    return d


def index_json(index: Index) -> str:
    site = index.site
    metrics = []
    for m in index.metrics:
        d = _clean(m)
        d["url"] = absolute(index, metric_path(m))
        d["coverage"] = coverage(m)
        d["implementations"] = [_implementation(i) for i in m["_impls"]]
        if m["_via_impls"]:  # tools that call one of the implementations above
            d["also_through"] = [_implementation(i) for i in m["_via_impls"]]
        metrics.append(d)
    projects = []
    for p in index.projects_by_group():
        # super_project is the maintainer's display setting (bold and first); only its effect is published.
        d = _clean({k: v for k, v in p.items() if k not in ("manual", "super_project")})
        d["url"] = absolute(index, project_path(p))
        d["last_commit"] = p["_last_commit"]
        d["latest_release"] = p["_release"]
        d["prerelease"] = p["_prerelease"]
        d["activity"] = p["_activity"]
        d["archived"] = p["_archived"]
        d["stars"] = p["_stars"]
        d["group"] = p["_group"]
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
        "license_url": site["license_url"],
        "code_license": site.get("code_license") or site["license"],
        "maintainer": site["maintainer"],
        "credit": site["credit"],
        "as_of": index.as_of(),
        "schema": f"{site['repository']}/blob/main/data/SCHEMA.md",
        "counts": {"metrics": len(index.metrics), "projects": len(index.projects),
                   "references": len(index.references)},
        "ordering": ("Implementations and projects are listed by group: established, newly released, developing, legacy, "
                     "others, status unknown. Newly released projects were first released less than about a year ago "
                     "and are not yet seen to be widely used in the community. Legacy projects are archived or have had no "
                     "commit for three years or more; the projects with a highlight (shown in bold on the website) "
                     "and reference programs are never legacy. Within each group the projects with a highlight come "
                     "first, then ranked and active ones. Projects in the others group do "
                     "not compute the metrics "
                     "themselves; they call another listed project (listed in calls), and their rows appear under "
                     "also_through instead of implementations. Projects in the unknown group could not be opened "
                     "(access); they list a claim and no implementations."),
        "definitions": {"standing": STANDING, "group": GROUPS, "kind": KINDS, "status": IMPL_STATUS_LONG,
                        "validation": VALIDATION_LONG, "access": ACCESS,
                        "comparison_relations": {
                            "source": "the compared project is the code this implementation was ported from (or "
                                      "that code's own source)",
                            "port": "the compared project was ported from this implementation",
                            "shared:<id>": "both were ported from the same code, the project <id>"},
                        "coverage": {"current": "an available implementation of the current edition",
                                     "new": "an available implementation of the current edition, but only from "
                                            "newly released projects",
                                     "partial": "only unreleased, proposed, older-edition or partial "
                                                "implementations",
                                     "": "none found"}},
        "families": [_clean(f) for f in index.families],
        "metrics": metrics,
        "references": [_clean(r) for r in index.references],
        "projects": projects,
        "gaps": [m["id"] for m in index.gaps()],
        "newly_released_only": [m["id"] for m in index.new_only()],
        "leads": [_clean(l) for l in index.leads],
        "updates": [_clean(u) for u in index.updates],
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


# ---------------------------------------------------------------------------------------------- BibTeX

BODY_NAMES = {"ISO": "International Organization for Standardization", "DIN": "Deutsches Institut für Normung",
              "Ecma": "Ecma International", "ANSI/ASA": "Acoustical Society of America",
              "IEC": "International Electrotechnical Commission", "ICAO": "International Civil Aviation Organization",
              "FAA": "Federal Aviation Administration", "Nordtest": "Nordtest"}
DOCUMENT_TYPES = {"standard": "Standard", "amendment": "Amendment", "draft": "Draft standard",
                  "technical-specification": "Technical Specification",
                  "publicly-available-specification": "Publicly Available Specification",
                  "regulation": "Regulation", "method": "Method"}
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
_BIB_SPECIAL = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
                "_": r"\_", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
# "Moore, B. C. J., Glasberg, B. R., & Baer, T. (1997). Rest" -> authors, year, rest
_CITATION = re.compile(r"^(?P<authors>.+?) \((?P<year>\d{4})[a-z]?\)\. (?P<rest>.+)$")
_INITIALS = re.compile(r"^(?:[A-ZÀ-Ý][a-z]?\.(?:-[A-ZÀ-Ý]\.)?\s?)+$")
_CONFERENCE = re.compile(r"Proceedings of (?!Meetings)|INTER-NOISE|Inter-Noise|Forum Acusticum|DAGA|Euronoise|"
                         r"Convention|Conference|Congress|Jahrestagung", re.IGNORECASE)


def _bib(text: str) -> str:
    """Plain text for a BibTeX field: Markdown emphasis removed, special characters escaped, dashes as TeX."""
    text = " ".join(str(text).replace("*", "").split())
    text = re.sub(r"[\\{}&%$#_~^]", lambda m: _BIB_SPECIAL[m.group(0)], text)
    return text.replace("—", "---").replace("–", "--")


def _bib_title(text: str) -> str:
    """A title with its capitalised words in braces, so that bibliography styles keep them (German nouns,
    acronyms, names); punctuation around a word stays outside. The first word is protected only when it has more
    than one capital."""
    def protect(word: str, first: bool) -> str:
        lead, core, trail = re.fullmatch(r"([(\[\"'“‘]*)(.*?)([)\]\"'”’.,;:!?]*)", word).groups()
        if not core or not re.search(r"[A-ZÀ-Ý]", core) or (first and len(re.findall(r"[A-ZÀ-Ý]", core)) < 2):
            return word
        return f"{lead}{{{core}}}{trail}"
    words = _bib(text).split(" ")
    return " ".join(protect(w, n == 0) for n, w in enumerate(words))


def _bib_authors(text: str) -> str | None:
    """'Moore, B. C. J., Glasberg, B. R., & Baer, T.' -> 'Moore, B. C. J. and Glasberg, B. R. and Baer, T.', or
    None when the text is not a list of 'Surname, Initials'."""
    parts = [x.strip() for x in text.replace(", &", ",").replace(" & ", ", ").split(", ")]
    if len(parts) % 2 or not all(_INITIALS.match(parts[n + 1]) for n in range(0, len(parts), 2)):
        return None
    return " and ".join(_bib(f"{parts[n]}, {parts[n + 1]}") for n in range(0, len(parts), 2))


def _entry(kind: str, key: str, fields: list[tuple[str, str | None]]) -> str:
    body = ",\n".join(f"  {name} = {{{value}}}" if name != "month" else f"  {name} = {value}"
                      for name, value in fields if value)
    return f"@{kind}{{{key},\n{body}\n}}"


def _date_fields(date: object) -> list[tuple[str, str | None]]:
    text = date_str(date) if date else ""
    year = text[:4] if re.match(r"\d{4}", text) else None
    month = MONTHS[int(text[5:7]) - 1] if re.match(r"\d{4}-\d{2}", text) else None
    return [("year", year), ("month", month)]


def _from_citation(key: str, citation: str, doi: str | None, url: str | None, fallback_title: str,
                   date: object = None) -> str:
    """A BibTeX entry parsed from an APA-style citation: article, conference paper, book or thesis. What cannot
    be parsed becomes @misc with the full citation as a note."""
    links = [("doi", doi), ("url", url if url and not doi else None)]  # verbatim fields: not escaped
    found = _CITATION.match(" ".join(citation.split()))
    authors = _bib_authors(found.group("authors")) if found else None
    if found and not authors:  # no author list: "Title (2008). Where it appeared."
        return _entry("misc", key, [("title", _bib_title(found.group("authors"))), ("year", found.group("year")),
                                    ("note", _bib(found.group("rest")).rstrip(".")), *links])
    if found and authors:
        year, rest = found.group("year"), found.group("rest")
        book = re.match(r"^\*(?P<title>[^*]+)\*(?: \((?P<edition>[^)]+?) ed\.\))?\. (?P<publisher>[^.]+)\.$", rest)
        thesis = re.match(r"^\*(?P<title>[^*]+)\* \[(?P<type>[^,\]]+), (?P<school>[^\]]+)\]\.?(?P<note>.*)$", rest)
        paper = re.match(r"^(?P<title>.+?[.?!]) \*(?P<container>[^*]+)\*(?P<tail>.*)$", rest)
        if thesis:
            doctoral = thesis.group("type").lower().startswith("doctoral")
            return _entry("phdthesis" if doctoral else "mastersthesis", key, [
                ("author", authors), ("title", _bib_title(thesis.group("title"))),
                ("school", _bib(thesis.group("school"))), ("type", None if doctoral else _bib(thesis.group("type"))),
                ("year", year), ("note", _bib(thesis.group("note").strip(" .")) or None), *links])
        if book:
            return _entry("book", key, [
                ("author", authors), ("title", _bib_title(book.group("title"))),
                ("edition", _bib(book.group("edition")) if book.group("edition") else None),
                ("publisher", _bib(book.group("publisher"))), ("year", year), *links])
        if paper:
            title = paper.group("title").rstrip(".")
            container, tail = paper.group("container").strip(), paper.group("tail").strip(" ,.")
            pieces = [x.strip() for x in re.split(r",\s+|\.\s+", tail)] if tail else []
            volume = number = pages = None
            if pieces and (vol := re.fullmatch(r"(\d+)(?:\(([^)]+)\))?", pieces[0])):
                volume, number = vol.group(1), _bib(vol.group(2)) if vol.group(2) else None
                pieces = pieces[1:]
                if pieces and re.fullmatch(r"[A-Z]*\d+(?:[–-][A-Z]*\d+)?", pieces[0]):
                    pages, pieces = pieces[0], pieces[1:]
            note = _bib(", ".join(pieces)) or None
            if _CONFERENCE.search(container) or not volume:
                return _entry("inproceedings", key, [
                    ("author", authors), ("title", _bib_title(title)), ("booktitle", _bib(container)),
                    ("volume", volume), ("number", number), ("pages", _bib(pages) if pages else None),
                    ("year", year), ("note", note), *links])
            return _entry("article", key, [
                ("author", authors), ("title", _bib_title(title)), ("journal", _bib(container)),
                ("volume", volume), ("number", number), ("pages", _bib(pages) if pages else None),
                ("year", year), ("note", note), *links])
    return _entry("misc", key, [("title", _bib_title(fallback_title)), *_date_fields(date)[:1],
                                ("note", _bib(citation)), *links])


def _standard(r: dict) -> str:
    """A standard, draft, specification, regulation or method as @techreport: the body as institution, the label
    as number."""
    fields = [("title", _bib_title(r["title"])), ("institution", _bib(BODY_NAMES.get(r["body"], r["body"]))),
              ("type", DOCUMENT_TYPES.get(r["kind"], "Standard")), ("number", _bib(r["label"])),
              *_date_fields(r.get("date")), ("edition", _bib(r["edition"]) if r.get("edition") else None),
              ("note", _bib(r["status"].replace("-", " ").capitalize()) if r["status"] != "current" else None),
              ("doi", r.get("doi")), ("url", r.get("url"))]
    return _entry("techreport", r["id"], fields)


def bibtex(index: Index) -> str:
    """Every standard and model reference of the list, then the papers that describe listed software (once each,
    and not when the paper is already a reference)."""
    site = index.site
    out = [f"% {site['name']}: {site['title']}. Standards, model papers and software papers, as BibTeX.",
           f"% Generated from {site['repository']}/tree/main/data on {index.as_of()}. Encoding: UTF-8.",
           "% Keys of references are their ids in the list; keys of software papers end in -paper.", ""]
    for r in index.references:
        if r["kind"] in ("paper", "book", "thesis") and r.get("citation"):
            out.append(_from_citation(r["id"], r["citation"], r.get("doi"), r.get("url"), r["title"], r.get("date")))
        else:
            out.append(_standard(r))
        out.append("")
    seen = {r["doi"].lower() for r in index.references if r.get("doi")}
    seen |= {" ".join(r["citation"].split()) for r in index.references if r.get("citation")}
    for p in index.projects_by_group():
        paper = p.get("paper")
        if not paper:
            continue
        marks = {" ".join(paper["citation"].split())} | ({paper["doi"].lower()} if paper.get("doi") else set())
        if marks & seen:
            continue
        seen |= marks
        out.append(f"% The paper describing {p['name']}")
        out.append(_from_citation(f"{p['id']}-paper", paper["citation"], paper.get("doi"), paper.get("url"),
                                  p["name"]))
        out.append("")
    return "\n".join(out)


def atom_feed(index: Index) -> str:
    site = index.site
    feed_url = site["base_url"] + "feed.xml"
    updated = date_str(index.updates[0]["date"]) if index.updates else index.as_of()
    entries = []
    for u in index.updates:
        day = date_str(u["date"])
        link = f"{absolute(index, UPDATES)}#{update_anchor(u)}"
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
    urls = [(absolute(index, p), as_of) for p in (HOME, METRICS, PROJECTS, MAP, LANGUAGES, STANDARDS, UPDATES,
                                                 ABOUT, FAQ, AI)]
    urls += [(absolute(index, metric_path(m)), as_of) for m in index.metrics]
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
