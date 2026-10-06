"""Sentences and labels shared by the HTML and Markdown renderers.

Each function takes formatting callbacks so the same wording is produced in both outputs:
`name(project)` formats a project name (a link), `t(text)` escapes plain text.
"""

from __future__ import annotations

import re
from typing import Callable

from .data import GROUPS as GROUPS_TEXT, REF_STATUS, STATUS_ORDER, Index, impl_rank, only_new
from .paths import LANGUAGES, METRICS, PROJECTS
from .text import join_words, long_date, month, plural

Fmt = Callable[[dict], str]
Esc = Callable[[str], str]

PAPER_KINDS = {"paper", "book", "thesis"}


def ref_status(ref: dict) -> str:
    return REF_STATUS[ref["status"]]


def edition_short(ref: dict) -> str:
    """Compact label for tables: the label, e.g. 'ECMA-418-2:2025 (4th ed.)'."""
    return ref["label"]


NEW_LABEL = "newly released, not yet widely used"
ONLY_NEW = ("So far only newly released projects, which are not yet widely used in the community, have released an "
                 "implementation of it; check their validation before relying on them.")


def introduce(site: dict) -> str:
    """What the name stands for, then the site description: "LISQM stands for … It is an index …"."""
    text = site["description"].strip()
    return f"{site['name']} stands for {site['title']}. It is {text[:1].lower()}{text[1:]}"


def name_note(site: dict) -> str:
    """That the index computes nothing itself, and what is open."""
    return (f"{site['name']} computes nothing itself; it lists and compares the implementations. Every listed "
            f"implementation is open source and {site['name']} itself is open data, but many of the standards the "
            "implementations follow are not free.")


GROUP_RULE = ("Every project is in exactly one group, decided in this order: others if it computes nothing itself "
              "and calls another indexed project; legacy if it is archived or has had no commit for three years; "
              "otherwise the standing recorded for it: established, newly released or developing. All lists follow "
              "the order established, newly released, developing, legacy, others, so a project that is new, little "
              "used or no longer maintained is never the first suggestion. Within each group the most widely used and "
              "recognised projects come first")


def standing_sentence(p: dict) -> str:
    """For newly released projects: 'First released in … Not yet widely used in the community.'; for legacy projects:
    since when they have not been maintained; otherwise ''."""
    if p.get("_group") == "legacy":
        last = f"its last commit was in {long_date(month(p['_last_commit']))}" if p.get("_last_commit") else ""
        if p.get("_archived"):
            return "Archived by its authors" + (f"; {last}" if last else "") + ". Kept here for reference."
        return f"Not maintained: {last}, more than three years ago. Kept here for reference."
    if p.get("standing") != "newly-released":
        return ""
    return f"{p.get('standing_note', '').strip()} Not yet widely used in the community.".strip()


def legacy_label(p: dict) -> str:
    """'legacy, archived' or 'legacy, no commit since 2021-06'."""
    return "legacy, archived" if p.get("_archived") else f"legacy, no commit since {month(p['_last_commit'])}"


def impl_extras(impl: dict, with_ref: bool = False) -> list[str]:
    extras: list[str] = []
    if impl["_project"].get("standing") == "newly-released":
        extras.append(NEW_LABEL)
    elif impl["_project"].get("_group") == "legacy":
        extras.append(legacy_label(impl["_project"]))
    elif impl["_project"].get("_group") == "developing":
        extras.append("developing")
    if with_ref:
        extras.append(impl["_ref"]["label"])
    if impl.get("_via"):
        extras.append(f"via {impl['_via']['name']}")
    if impl.get("scope"):
        extras.append(impl["scope"])
    if impl["status"] == "unreleased":
        extras.append("unreleased")
    elif impl["status"] == "proposed":
        extras.append("proposed, not merged")
    return extras


def impl_phrase(impl: dict, name: Fmt, t: Esc, with_ref: bool = False) -> str:
    p = impl["_project"]
    bits = [", ".join(p["languages"])] + impl_extras(impl, with_ref)
    return f"{name(p)} ({t('; '.join(bits))})"


def dedupe(impls: list[dict]) -> list[dict]:
    """One entry per project and reference (a project may list the same edition twice with different scopes)."""
    seen: set[tuple[str, str, str]] = set()
    out = []
    for i in impls:
        key = (i["_project"]["id"], i["reference"], i["status"])
        if key not in seen:
            seen.add(key)
            out.append(i)
    return out


def current_statement(index: Index, m: dict) -> str:
    """'The current edition is …. In development: ….' (plain text)."""
    refs = [index.ref[r] for r in m["current"]]
    labels = join_words([r["label"] for r in refs])
    if all(r["kind"] in PAPER_KINDS for r in refs):
        s = (f"There is no standard; the reference model is {labels}." if len(refs) == 1 else
             f"There is no standard; the reference models are {labels}.")
    else:
        s = f"The current edition is {labels}."
    drafts = [index.ref[r] for r in m["references"] if index.ref[r]["status"] == "in-development"]
    if drafts:
        s += f" In development: {join_words([d['label'] for d in drafts])}."
    return s


def in_short(index: Index, m: dict, name: Fmt, t: Esc) -> str:
    """One paragraph that answers 'what should I use for this metric?' from the data alone."""
    refs = [index.ref[r] for r in m["current"]]
    s = current_statement(index, m)
    current = dedupe(m["_current_impls"])
    if current:
        s += " Open-source implementations of it: " + join_words(
            [impl_phrase(i, name, t, with_ref=len(refs) > 1) for i in current]) + "."
        if only_new(m):
            s += " " + ONLY_NEW
    else:
        s += " No open-source implementation of it has been found."
    older = [i for i in dedupe(m["_older_impls"]) if i["_ref"]["status"] != "in-development"]
    if older:
        s += " Implementations of earlier editions or related models: " + join_words(
            [impl_phrase(i, name, t, with_ref=True) for i in older]) + "."
    return s


LABELS = {"en": {"newly-released": "newly released", "developing": "developing", "legacy": "legacy", "also": "also", "via": "via", "unreleased": "unreleased",
                 "proposed": "proposed"},
          "zh": {"newly-released": "新发布", "developing": "发展中", "legacy": "停止维护", "also": "也支持", "via": "调用", "unreleased": "未发布",
                 "proposed": "待合并"}}


def by_language(impls: list[dict], name: Fmt, lang: str = "en",
                tags: dict[str, str] | None = None) -> list[tuple[str, list[str]]]:
    """Group implementations by each project's main (first-listed) language: [('Python', ['MoSQITo', …]), …].
    With `tags` ({'newly-released': …, 'legacy': …}), newly released and legacy projects get that marker after
    their name instead of the word in parentheses."""
    words = LABELS[lang]
    best: dict[str, dict] = {}  # a project that has a released implementation is not also listed as unreleased
    for i in dedupe(impls):
        key = i["_project"]["id"]
        if key not in best or STATUS_ORDER[i["status"]] < STATUS_ORDER[best[key]["status"]]:
            best[key] = i
    groups: dict[str, list[str]] = {}
    for i in best.values():
        p = i["_project"]
        extras = []
        group = "newly-released" if p.get("standing") == "newly-released" else p.get("_group")
        if group in ("newly-released", "developing", "legacy") and tags is None:
            extras.append(words[group])
        if len(p["languages"]) > 1:
            extras.append(f"{words['also']} " + ", ".join(p["languages"][1:]))
        if i.get("_via"):
            extras.append(f"{words['via']} {i['_via']['name']}")
        if i["status"] == "unreleased":
            extras.append(words["unreleased"])
        elif i["status"] == "proposed":
            extras.append(words["proposed"])
        label = name(p) + (f" {tags[group]}" if tags and group in tags else "")
        label += f" ({'; '.join(extras)})" if extras else ""
        lang = p["languages"][0]
        if label not in groups.setdefault(lang, []):
            groups[lang].append(label)
    return sorted(groups.items(), key=lambda kv: language_order(kv[0]))


LANGUAGE_ORDER = ["Python", "MATLAB", "Octave", "C", "C++", "Rust", "Julia"]
COVERAGE_COLUMNS = [("Python", {"Python"}), ("MATLAB/Octave", {"MATLAB", "Octave"}), ("C/C++", {"C", "C++"}),
                    ("Rust", {"Rust"}), ("Julia", {"Julia"})]


def language_order(lang: str) -> tuple[int, str]:
    return (LANGUAGE_ORDER.index(lang) if lang in LANGUAGE_ORDER else 99, lang.lower())


def coverage(m: dict) -> dict[str, str]:
    """Per language column: 'current' (an available implementation of the current edition), 'new' (the same,
    but only from newly released projects), 'partial' (only unreleased, proposed or older-edition implementations) or ''
    (none).
    Bindings count: a C library with a Python interface covers Python."""
    known = set().union(*(langs for _, langs in COVERAGE_COLUMNS))
    out = {}
    for col, langs in COVERAGE_COLUMNS + [("Other", None)]:
        def matches(p: dict) -> bool:
            return bool(set(p["languages"]) & langs) if langs is not None else bool(set(p["languages"]) - known)
        impls = [i for i in m["_impls"] if matches(i["_project"]) and i["_ref"]["status"] != "in-development"]
        released = [i for i in impls if i["status"] == "available" and i["reference"] in m["current"]]
        if any(i["_project"]["standing"] != "newly-released" for i in released):
            out[col] = "current"
        elif released:
            out[col] = "new"
        elif impls:
            out[col] = "partial"
        else:
            out[col] = ""
    return out


def release_text(p: dict) -> str:
    r = p.get("_release")
    if not r:
        return "no release"
    return f"{r['version']} ({month(r['date'])})" if r.get("date") else str(r["version"])


def activity_text(p: dict) -> str:
    a = p["_activity"]
    if a == "archived":
        return "archived"
    if a == "inactive":
        return f"inactive since {month(p['_last_commit'])}"
    if a == "active":
        return "active"
    return "unknown"


PROPER_FIRST_WORDS = {"Zwicker", "Moore–Glasberg", "Moore-Glasberg", "Sottek", "Aures", "Daniel"}


def in_sentence(title: str) -> str:
    """'Time-varying loudness, …' -> 'time-varying loudness, …' for use mid-sentence; names and acronyms stay."""
    first = title.split(" ", 1)[0]
    if first in PROPER_FIRST_WORDS or first.isupper() or not first[:1].isupper():
        return title
    return title[:1].lower() + title[1:]


# ---------------------------------------------------------------------------------------------- timeline

def time_bins(index: Index) -> list[tuple[str, int | None, int | None]]:
    """Columns of the timeline: (label, first year, last year). The last column runs to the data date."""
    year = int(index.as_of()[:4])
    last = f"2025–{year}" if year > 2025 else "2025"
    return [("≤ 1999", None, 1999), ("2000–2016", 2000, 2016), ("2017–2019", 2017, 2019),
            ("2020–2023", 2020, 2023), ("2024", 2024, 2024), (last, 2025, None)]


def bin_of(ref: dict, bins: list[tuple[str, int | None, int | None]]) -> int | None:
    """Column of a reference: by its year; documents still in development go in the last column."""
    if ref["status"] == "in-development":
        return len(bins) - 1
    found = re.match(r"\d{4}", str(ref.get("date") or ""))
    if not found:
        return None
    year = int(found.group(0))
    for n, (_, lo, hi) in enumerate(bins):
        if (lo is None or year >= lo) and (hi is None or year <= hi):
            return n
    return len(bins) - 1


def timeline(index: Index) -> list[tuple[dict, list[dict]]]:
    """Per family, per method: the editions in each column of the timeline and who implements each edition.

    Each method row is {"method", "cells": [[(ref, impls), …] per column], "first": first column used}.
    Implementations of one edition are ordered by `impl_rank`, so established projects come first.
    """
    bins = time_bins(index)
    out = []
    for fam, methods in index.families_with_methods():
        rows = []
        for m in methods:
            cells: list[list[tuple[dict, list[dict]]]] = [[] for _ in bins]
            for rid in m["references"]:
                ref = index.ref[rid]
                n = bin_of(ref, bins)
                if n is None:
                    continue
                impls = sorted(dedupe([i for i in m["_impls"] if i["reference"] == rid]), key=impl_rank)
                cells[n].append((ref, impls))
            used = [n for n, c in enumerate(cells) if c]
            rows.append({"method": m, "cells": cells, "first": used[0] if used else len(bins)})
        out.append((fam, rows))
    return out


def version_label(impl: dict) -> str:
    """What the timeline shows after a project name: the first version with this edition, or its state."""
    if impl["status"] == "proposed":
        found = re.search(r"/pull/(\d+)", impl.get("link") or "")
        return f"PR #{found.group(1)}" if found else "proposed"
    if impl["status"] == "unreleased":
        return "unreleased"
    return str(impl.get("since") or "")


def edition_state(m: dict, ref: dict) -> str:
    """'current' for the method's current edition(s), 'old' for superseded or withdrawn ones, 'dev' for drafts."""
    if ref["id"] in m["current"]:
        return "current"
    if ref["status"] in ("superseded", "withdrawn"):
        return "old"
    if ref["status"] == "in-development":
        return "dev"
    return ""


def faq(index: Index, name: Fmt, method_link: Callable[[dict], str], t: Esc,
        page_link: Callable[[str, str], str]) -> list[tuple[str, str]]:
    """The key questions, answered from the data. Answers are HTML or Markdown depending on the callbacks;
    `page_link(path, label)` links another page of the site."""
    mainstream = index.mainstream()
    qa: list[tuple[str, str]] = []
    qa.append(("Which code should I use for a psychoacoustic metric?",
               f"Start from the edition that is current for the metric: the {page_link(METRICS, 'Metrics')} page names "
               f"it for each of the {len(index.methods)} methods, and each method page lists the projects that "
               "implement it, the most widely used and established ones first. The most widely used projects are "
               + join_words([name(p) + t(f" ({', '.join(p['languages'])})") for p in mainstream])
               + ". Before relying on a result, check the validation each project states and whether the fix you "
               "need is in a release or only on its main branch."))
    counts = []
    for col, _ in COVERAGE_COLUMNS:
        current = sum(coverage(m)[col] == "current" for m in index.methods)
        new = sum(coverage(m)[col] == "new" for m in index.methods)
        if current or new:
            counts.append(t(f"{col}: {current + new} of {len(index.methods)}")
                          + (t(f" ({new} only from newly released projects)") if new else ""))
    qa.append(("Which metrics can I compute in Python, MATLAB or C?",
               "Methods whose current edition has a released open-source implementation, by language: "
               + "; ".join(counts) + f". The {page_link(LANGUAGES, 'Languages')} page lists them, and explains how "
               "each project can be used from another language, for example a MATLAB toolbox from Python through "
               "the MATLAB Engine API."))
    qa.append(("Why does it matter which edition a tool implements?",
               "Psychoacoustic standards change between editions. ECMA-418-2, for example, has had four editions "
               "since 2020 that changed the hearing model, roughness and loudness, and all three parts of ISO 532 "
               "are being revised. Two tools that both claim to implement a standard can therefore give different "
               "values for the same sound. Liu et al. (2026, Acoustics Australia, doi:10.1007/s40857-026-00393-3) "
               "compared four tools and found differences large enough to change the predictions of sound-quality "
               "models. Each method page lists the editions and which tool follows which."))
    gaps = index.gaps()
    answer = (("No available open-source implementation of the current edition was found for "
               + join_words([method_link(m) for m in gaps]) + ".") if gaps else
              "Every method in the index has at least one available implementation of its current edition.")
    if index.new_only():
        answer += (" The current editions of " + join_words([method_link(m) for m in index.new_only()])
                   + " have released implementations only from newly released projects that are not yet widely used.")
    qa.append(("Which metrics have no open-source implementation yet?", answer))

    def names(key: str, note: Callable[[dict], str]) -> str:
        return join_words([name(p) + t(f" ({note(p)})") for p in index.group(key)])
    groups = (
        "Every project is in one group. Established: " + t(GROUPS_TEXT["established"])
        + " Newly released: " + t(GROUPS_TEXT["newly-released"])
        + " Developing: " + t(GROUPS_TEXT["developing"])
        + " Legacy: " + t(GROUPS_TEXT["legacy"])
        + " Others: " + t(GROUPS_TEXT["others"])
        + " Lists follow this order, so that a project which is new, little used or no longer maintained is never "
        f"the first suggestion. The most widely used projects ({t(join_words([p['name'] for p in mainstream]))}) "
        "and reference programs published with a standard are never listed as legacy.")
    if index.group("newly-released"):
        groups += (" Newly released projects: "
                   + names("newly-released", lambda p: p.get("standing_note", "").strip().rstrip(".")) + ".")
    if index.group("legacy"):
        groups += " Legacy projects: " + names("legacy", lambda p: "archived" if p["_archived"]
                                               else "last commit " + month(p["_last_commit"])) + "."
    groups += f" All groups are on the {page_link(PROJECTS, 'Projects')} page."
    qa.append(("What do established, newly released, developing and legacy mean?", groups))
    qa.append(("How are the entries checked?",
               "From each project's own README, documentation, release notes, licence file and package metadata, "
               "with links to those sources. The index records what a project claims and does not run the code. "
               "Repository and package metadata are refreshed every month, and a person reviews new findings."))
    return qa


def ai_guide(index: Index) -> tuple[str, list[tuple[str, str, list[str]]]]:
    """The For AI page, in inline Markdown with absolute links (shared by the HTML page and its Markdown twin):
    an introduction and (anchor, heading, items) sections."""
    site = index.site
    base, repo = site["base_url"], site["repository"]
    mainstream = join_words([p["name"] for p in index.mainstream()])
    langs = join_words(index.languages())
    intro = ("This page is for AI agents, crawlers and language models that read the index on someone's behalf. "
             "People are welcome too: it lists the same data in forms that are easy to retrieve, parse and quote.")
    sections = [
        ("start", "Where to start", [
            f"[llms.txt]({base}llms.txt): a short summary with a link to the Markdown version of every page, "
            "following the [llms.txt proposal](https://llmstxt.org/).",
            f"[llms-full.txt]({base}llms-full.txt): every page in one Markdown file.",
            f"[index.json]({base}index.json): the whole index as JSON (methods, editions, projects, implementations, "
            f"groups and coverage). Field definitions: [data/SCHEMA.md]({repo}/blob/main/data/SCHEMA.md).",
            "A Markdown version of every page: replace `.html` with `.md`, for example "
            f"[metrics/loudness-zwicker.md]({base}metrics/loudness-zwicker.md) or "
            f"[projects/sqat.md]({base}projects/sqat.md).",
            f"[sitemap.xml]({base}sitemap.xml) lists every page and [feed.xml]({base}feed.xml) the updates. Each HTML "
            "page also carries schema.org JSON-LD.",
            f"All crawlers, AI crawlers included, may read every page ([robots.txt]({base}robots.txt)).",
        ]),
        ("contents", "What the data contains", [
            f"{plural(len(index.methods), 'method')} in {plural(len(index.families), 'group')}, "
            f"{plural(len(index.projects), 'project')} in {langs}, and "
            f"{plural(len(index.references), 'standard or model paper', 'standards and model papers')}. "
            f"Data as of {index.as_of()}.",
            "Every implementation names the standard edition or model paper it follows, its functions, whether "
            "it is released, merged but unreleased, or only proposed, and its validation evidence as stated by the "
            "project.",
            "Every project belongs to a group: established, newly released (first released less than about a year "
            "ago and not yet widely used), developing, legacy (archived, or no commit for three years or more) or "
            f"other (it calls another indexed project). The most widely used projects are {mainstream}.",
            "Every entry links the documentation its facts were taken from.",
        ]),
        ("answering", "Answering questions with it", [
            "Name the current edition first (for Zwicker loudness, ISO 532-1:2017), then the projects that "
            "implement that edition. Lists in the index are already in the recommended order.",
            "Say when a project is newly released or legacy, and when code is only on a main branch (unreleased) "
            "or in a pull request (proposed).",
            "Validation is as stated by each project; the index does not run the code.",
            "Give the date of the data and link the method or project page, so that the reader can check it.",
            f"When no open implementation of the current edition exists, say so: see the [gaps]({base}#gaps).",
        ]),
        ("accuracy", "How the data is kept accurate", [
            "Entries are matched to standard editions, not only to standard numbers, because results change "
            "between editions: ECMA-418-2, for example, has had four editions since 2020.",
            "Each fact comes from the project's own README, documentation, release notes, licence file or package "
            "metadata, and is linked to it.",
            "A GitHub Action refreshes repository dates, releases and package versions every month, searches for "
            "new projects and watches ISO and Ecma for new editions; a person reviews every change.",
            f"Corrections are made in public, through issues and pull requests on [GitHub]({repo}).",
        ]),
        ("citing", "Citing it", [
            f"{site['maintainer']['name']}. *{site['name']}: {site['title']}*. {base} (accessed on the date of use). "
            f"Citation metadata: [CITATION.cff]({repo}/blob/main/CITATION.cff).",
            "In one sentence: an index of open-source implementations of psychoacoustic metrics, organised by the "
            "standard edition each one follows, with a source for every entry.",
            site["credit"],
        ]),
    ]
    return intro, sections
