"""Sentences and labels shared by the HTML and Markdown renderers.

Each function takes formatting callbacks so the same wording is produced in both outputs:
`name(project)` formats a project name (a link), `t(text)` escapes plain text.
"""

from __future__ import annotations

from typing import Callable

from .data import REF_STATUS, Index
from .text import join_words, month

Fmt = Callable[[dict], str]
Esc = Callable[[str], str]

PAPER_KINDS = {"paper", "book", "thesis"}


def ref_status(ref: dict) -> str:
    return REF_STATUS[ref["status"]]


def edition_short(ref: dict) -> str:
    """Compact label for tables: the label, e.g. 'ECMA-418-2:2025 (4th ed.)'."""
    return ref["label"]


def impl_extras(impl: dict, with_ref: bool = False) -> list[str]:
    extras: list[str] = []
    if with_ref:
        extras.append(impl["_ref"]["label"])
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


def in_short(index: Index, m: dict, name: Fmt, t: Esc) -> str:
    """One paragraph that answers 'what should I use for this metric?' from the data alone."""
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
    current = dedupe(m["_current_impls"])
    if current:
        s += " Open-source implementations of it: " + join_words(
            [impl_phrase(i, name, t, with_ref=len(refs) > 1) for i in current]) + "."
    else:
        s += " No open-source implementation of it has been found."
    older = [i for i in dedupe(m["_older_impls"]) if i["_ref"]["status"] != "in-development"]
    if older:
        s += " Implementations of earlier editions or related models: " + join_words(
            [impl_phrase(i, name, t, with_ref=True) for i in older]) + "."
    return s


def by_language(impls: list[dict], name: Fmt) -> list[tuple[str, list[str]]]:
    """Group implementations by each project's main (first-listed) language: [('Python', ['MoSQITo', …]), …]."""
    groups: dict[str, list[str]] = {}
    for i in dedupe(impls):
        p = i["_project"]
        extras = []
        if len(p["languages"]) > 1:
            extras.append("also " + ", ".join(p["languages"][1:]))
        if i["status"] == "unreleased":
            extras.append("unreleased")
        elif i["status"] == "proposed":
            extras.append("proposed")
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
    """Per language column: 'current' (an available implementation of the current edition), 'partial' (only
    unreleased, proposed or older-edition implementations) or '' (none). Bindings count: a C library with a
    Python interface covers Python."""
    known = set().union(*(langs for _, langs in COVERAGE_COLUMNS))
    out = {}
    for col, langs in COVERAGE_COLUMNS + [("Other", None)]:
        def matches(p: dict) -> bool:
            return bool(set(p["languages"]) & langs) if langs is not None else bool(set(p["languages"]) - known)
        impls = [i for i in m["_impls"] if matches(i["_project"]) and i["_ref"]["status"] != "in-development"]
        if any(i["status"] == "available" and i["reference"] in m["current"] for i in impls):
            out[col] = "current"
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


def faq(index: Index, name: Fmt, method_link: Callable[[dict], str], t: Esc) -> list[tuple[str, str]]:
    """Question/answer pairs generated from the data. Answers are HTML or Markdown depending on the callbacks."""
    qa: list[tuple[str, str]] = []
    for col, _ in COVERAGE_COLUMNS:
        covered = [m for m in index.methods if coverage(m)[col] == "current"]
        if not covered:
            continue
        lang_projects = sorted({i["_project"]["name"] for m in covered for i in m["_current_impls"]
                                if i["status"] == "available"
                                and set(i["_project"]["languages"]) & dict(COVERAGE_COLUMNS)[col]})
        qa.append((f"Which psychoacoustic metrics can I compute in {col}?",
                   f"Current editions of {len(covered)} methods have an available implementation that can be "
                   f"called from {t(col)}: " + join_words([method_link(m) for m in covered]) + ". Projects: "
                   + t(", ".join(lang_projects)) + "."))
    for m in index.methods:
        qa.append((f"Which open-source code implements {in_sentence(m['title'])}?", in_short(index, m, name, t)))
    gaps = index.gaps()
    qa.append(("Which psychoacoustic metrics have no open-source implementation yet?",
               ("No available open-source implementation of the current edition was found for "
                + join_words([method_link(m) for m in gaps]) + ".") if gaps else
               "Every method in the index has at least one available implementation of its current edition."))
    qa.append(("Why does it matter which edition a tool implements?",
               "Psychoacoustic standards change between editions. ECMA-418-2, for example, has had four editions "
               "since 2020 that changed the hearing model, roughness and loudness, and all three parts of ISO 532 "
               "are being revised. Two tools that both claim to implement a standard can therefore give different "
               "values for the same sound. Each method page lists the editions and which tool follows which."))
    qa.append(("How are the entries checked?",
               "From each project's own README, documentation, release notes, licence file and package metadata, "
               "with links to those sources. The index records what a project claims and does not run the code. "
               "Repository and package metadata are refreshed every week, and a person reviews new findings."))
    return qa
