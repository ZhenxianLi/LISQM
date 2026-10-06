"""Sentences and labels shared by the HTML and Markdown renderers.

Each function takes formatting callbacks so the same wording is produced in both outputs:
`name(project)` formats a project name (a link), `t(text)` escapes plain text.
"""

from __future__ import annotations

import re
from typing import Callable

from .data import REF_STATUS, Index, impl_rank, only_new
from .text import join_words, month

Fmt = Callable[[dict], str]
Esc = Callable[[str], str]

PAPER_KINDS = {"paper", "book", "thesis"}


def ref_status(ref: dict) -> str:
    return REF_STATUS[ref["status"]]


def edition_short(ref: dict) -> str:
    """Compact label for tables: the label, e.g. 'ECMA-418-2:2025 (4th ed.)'."""
    return ref["label"]


NEW_LABEL = "new, not yet widely used"
ONLY_NEW = ("So far only new projects, which are not yet widely used in the community, have released an "
            "implementation of it; check their validation before relying on them.")


def standing_sentence(p: dict) -> str:
    """For new projects: 'First released in … Not yet widely used in the community.'; otherwise ''."""
    if p.get("standing") != "new":
        return ""
    return f"{p.get('standing_note', '').strip()} Not yet widely used in the community.".strip()


def impl_extras(impl: dict, with_ref: bool = False) -> list[str]:
    extras: list[str] = []
    if impl["_project"].get("standing") == "new":
        extras.append(NEW_LABEL)
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


LABELS = {"en": {"new": "new", "also": "also", "via": "via", "unreleased": "unreleased", "proposed": "proposed"},
          "zh": {"new": "新项目", "also": "也支持", "via": "调用", "unreleased": "未发布", "proposed": "待合并"}}


def by_language(impls: list[dict], name: Fmt, lang: str = "en") -> list[tuple[str, list[str]]]:
    """Group implementations by each project's main (first-listed) language: [('Python', ['MoSQITo', …]), …]."""
    words = LABELS[lang]
    groups: dict[str, list[str]] = {}
    for i in dedupe(impls):
        p = i["_project"]
        extras = []
        if p.get("standing") == "new":
            extras.append(words["new"])
        if len(p["languages"]) > 1:
            extras.append(f"{words['also']} " + ", ".join(p["languages"][1:]))
        if i.get("_via"):
            extras.append(f"{words['via']} {i['_via']['name']}")
        if i["status"] == "unreleased":
            extras.append(words["unreleased"])
        elif i["status"] == "proposed":
            extras.append(words["proposed"])
        label = name(p) + (f" ({'; '.join(extras)})" if extras else "")
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
    """Per language column: 'current' (an available implementation of the current edition), 'new' (the same, but
    only from new projects), 'partial' (only unreleased, proposed or older-edition implementations) or '' (none).
    Bindings count: a C library with a Python interface covers Python."""
    known = set().union(*(langs for _, langs in COVERAGE_COLUMNS))
    out = {}
    for col, langs in COVERAGE_COLUMNS + [("Other", None)]:
        def matches(p: dict) -> bool:
            return bool(set(p["languages"]) & langs) if langs is not None else bool(set(p["languages"]) - known)
        impls = [i for i in m["_impls"] if matches(i["_project"]) and i["_ref"]["status"] != "in-development"]
        released = [i for i in impls if i["status"] == "available" and i["reference"] in m["current"]]
        if any(i["_project"]["standing"] != "new" for i in released):
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
            ("2020–2021", 2020, 2021), ("2022–2023", 2022, 2023), ("2024", 2024, 2024), (last, 2025, None)]


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


def faq(index: Index, name: Fmt, method_link: Callable[[dict], str], t: Esc) -> list[tuple[str, str]]:
    """Question/answer pairs generated from the data. Answers are HTML or Markdown depending on the callbacks."""
    qa: list[tuple[str, str]] = []
    for col, _ in COVERAGE_COLUMNS:
        covered = [m for m in index.methods if coverage(m)[col] == "current"]
        newly = [m for m in index.methods if coverage(m)[col] == "new"]
        if not covered and not newly:
            continue
        ids = {i["_project"]["id"] for m in covered + newly for i in m["_current_impls"]
               if i["status"] == "available" and set(i["_project"]["languages"]) & dict(COVERAGE_COLUMNS)[col]}
        lang_projects = [p["name"] + (" (new)" if p["standing"] == "new" else "")
                         for p in index.projects_by_standing() if p["id"] in ids]
        answer = (f"Current editions of {len(covered)} methods have an available implementation that can be "
                  f"called from {t(col)}: " + join_words([method_link(m) for m in covered]) + "."
                  if covered else f"No current edition has an established implementation in {t(col)} yet.")
        if newly:
            answer += (" Only new projects, not yet widely used, cover " + join_words([method_link(m) for m in newly])
                       + ".")
        qa.append((f"Which psychoacoustic metrics can I compute in {col}?",
                   answer + " Projects: " + t(", ".join(lang_projects)) + "."))
    for m in index.methods:
        qa.append((f"Which open-source code implements {in_sentence(m['title'])}?", in_short(index, m, name, t)))
    gaps = index.gaps()
    answer = (("No available open-source implementation of the current edition was found for "
               + join_words([method_link(m) for m in gaps]) + ".") if gaps else
              "Every method in the index has at least one available implementation of its current edition.")
    if index.new_only():
        answer += (" The current editions of " + join_words([method_link(m) for m in index.new_only()])
                   + " have released implementations only from new projects that are not yet widely used.")
    qa.append(("Which psychoacoustic metrics have no open-source implementation yet?", answer))
    qa.append(("Why does it matter which edition a tool implements?",
               "Psychoacoustic standards change between editions. ECMA-418-2, for example, has had four editions "
               "since 2020 that changed the hearing model, roughness and loudness, and all three parts of ISO 532 "
               "are being revised. Two tools that both claim to implement a standard can therefore give different "
               "values for the same sound. Liu et al. (2026, Acoustics Australia, doi:10.1007/s40857-026-00393-3) "
               "compared four tools and found differences large enough to change the predictions of sound-quality "
               "models. Each method page lists the editions and which tool follows which."))
    qa.append(("Which projects are new?",
               "Projects first released less than about a year ago, which are not yet widely used in the community: "
               + join_words([name(p) + t(f" ({p.get('standing_note', '').strip().rstrip('.')})")
                             for p in index.projects_by_standing() if p["standing"] == "new"])
               + ". The index lists them after established projects; check their validation before relying on them."))
    qa.append(("How are the entries checked?",
               "From each project's own README, documentation, release notes, licence file and package metadata, "
               "with links to those sources. The index records what a project claims and does not run the code. "
               "Repository and package metadata are refreshed every week, and a person reviews new findings."))
    return qa
