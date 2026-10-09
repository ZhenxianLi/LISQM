"""Sentences and labels shared by the HTML and Markdown renderers.

Each function takes formatting callbacks so the same wording is produced in both outputs:
`name(project)` formats a project name (a link), `t(text)` escapes plain text.
"""

from __future__ import annotations

import re
from typing import Callable

from .data import GROUPS as GROUPS_TEXT, REF_STATUS, STATUS_ORDER, VALIDATION, Index, impl_rank, only_new
from .paths import BIBTEX, LANGUAGES, MAP, METRICS, PROJECTS, md_twin
from .text import join_words, long_date, month, plural

Fmt = Callable[[dict], str]
Esc = Callable[[str], str]

PAPER_KINDS = {"paper", "book", "thesis"}


# How the licences of LISQM itself are named to readers.
LICENCE_NAMES = {"CC-BY-4.0": "CC BY 4.0", "MIT": "MIT"}


def licence_names(site: dict) -> tuple[str, str]:
    """The licence of the data and the text, and that of the code ("CC BY 4.0", "MIT")."""
    data, code = site["license"], site.get("code_license") or site["license"]
    return LICENCE_NAMES.get(data, data), LICENCE_NAMES.get(code, code)


def licence_terms(site: dict) -> str:
    """What the licence of the data and the text allows, and on what condition (plain text)."""
    return ("you may copy, adapt and share them, also commercially, if you credit "
            f"{site['name']} and its author, {site['maintainer']['name']}, link to the licence and say what you "
            "changed")


def ref_status(ref: dict) -> str:
    return REF_STATUS[ref["status"]]


def edition_short(ref: dict) -> str:
    """Compact label for tables: the label, e.g. 'ECMA-418-2:2025 (4th ed.)'."""
    return ref["label"]


NEW_LABEL = "newly released, not yet seen to be widely used"
ONLY_NEW = ("So far, only newly released projects, not yet seen to be widely used in the community, have released "
            "an implementation of it. Check their validation before relying on them.")


def _relation(i: dict, cid: str, name: Fmt | None, t: Esc) -> str:
    """" (its source)", " (a port of it)" or " (also ported from …)" after a comparison that is not an independent
    check, else ''."""
    kind, origin = (i.get("_relation") or {}).get(cid, (None, None))
    if kind == "source":
        return t(" (its source)")
    if kind == "port":
        return t(" (a port of it)")
    if kind == "shared":
        return t(" (also ported from ") + (name(origin) if name else t(origin["name"])) + t(")")
    return ""


def compared_names(i: dict, name: Fmt | None = None, t: Esc = str) -> list[str]:
    """What an implementation was compared with: listed projects through `name`, anything else through `t`.
    Comparisons with related code are marked: the code it was ported from "(its source)", a port of it "(a port of
    it)", and another port of the same code "(also ported from …)"."""
    return [(name(p) if p and name else t(n)) + _relation(i, cid, name, t)
            for (n, p), cid in zip(i.get("_compared") or [], i.get("compared_with") or [])]


def only_related(i: dict) -> bool:
    """True when every comparison an implementation states is with related code, so none is independent."""
    related, compared = i.get("_relation") or {}, i.get("compared_with") or []
    return bool(compared) and all(c in related for c in compared)


def dependence_note(i: dict) -> str:
    """Why comparisons with related code are not independent checks (plain text), or ''."""
    kinds = {kind for kind, _ in (i.get("_relation") or {}).values()}
    notes = []
    if "source" in kinds:
        notes.append("It was compared with the code it was ported from, which checks the port only.")
    if "port" in kinds:
        notes.append("It was compared with a port of its own code, which checks the port only.")
    if "shared" in kinds:
        notes.append("Code ported from the same source is expected to agree, so that comparison is not an "
                     "independent check.")
    return " ".join(notes)


def derived_names(i: dict, name: Fmt | None = None, t: Esc = str) -> list[str]:
    """The code an implementation was ported or adapted from: listed projects through `name`, anything else
    through `t`."""
    return [name(p) if p and name else t(n) for n, p in i.get("_derived") or []]


def validation_label(i: dict, name: Fmt | None = None, t: Esc = str) -> str:
    """The stated evidence, naming what the implementation was compared with when the project says so:
    "compared with MoSQITo", "reference code: SQAT", or the plain label ("standard or paper data" …)."""
    v, names = i["validation"], compared_names(i, name, t)
    if v == "cross-implementation" and names:
        return "compared with " + join_words(names)
    if v == "reference-code" and names:
        return "reference code: " + join_words(names)
    return t(VALIDATION[v])


def validation_also(i: dict, name: Fmt | None = None, t: Esc = str) -> str:
    """"also compared with …" when a project names comparisons beside evidence of another kind, else ''."""
    if i["validation"] in ("cross-implementation", "reference-code") or not i.get("_compared"):
        return ""
    return "also compared with " + join_words(compared_names(i, name, t))


def validation_groups(impls: list[dict], key: Callable[[dict], str]) -> tuple[list[list[dict]], list[dict]]:
    """Implementations for a "How it was validated" section, in order: groups of rows with the same key (the
    project, on a metric page), evidence, comparisons, origin and details, shown once; and the rows with nothing
    stated (a row that names the code it was ported from states something)."""
    groups: dict[tuple, list[dict]] = {}
    silent = []
    for i in impls:
        details = tuple(i.get("validation_details") or ())
        compared = tuple(n for n, _ in i.get("_compared") or ())
        derived = tuple(n for n, _ in i.get("_derived") or ())
        if i["validation"] == "not-stated" and not details and not compared and not i.get("derived_from"):
            silent.append(i)
        else:
            groups.setdefault((key(i), i["validation"], i.get("validation_scope"), compared, derived, details),
                              []).append(i)
    return list(groups.values()), silent


def silent_line(impls: list[dict], groups: list[list[dict]], silent: list[dict], on_metric: bool) -> str:
    """The implementations whose projects state nothing about validation, in one sentence. A project page names
    the metric and edition; a metric page names the project, with the editions when the project has others there."""
    if not on_metric:
        return "Not stated for " + "; ".join(dict.fromkeys(f'{i["_metric"]["name"]} · {i["_ref"]["label"]}'
                                                           for i in silent)) + "."
    stated = {i["_project"]["id"] for group in groups for i in group}
    by_project: dict[str, list[dict]] = {}
    for i in silent:
        by_project.setdefault(i["_project"]["id"], []).append(i)
    names = []
    for pid, rows in by_project.items():
        name = rows[0]["_project"]["name"]
        if pid in stated or len({i["reference"] for i in impls if i["_project"]["id"] == pid}) > 1:
            name += " for " + join_words(list(dict.fromkeys(i["_ref"]["label"] for i in rows)))
        names.append(name)
    joined = "; ".join(names) if any(" for " in n for n in names) else join_words(names)
    return f"Not stated by {joined}."


def how_to_cite(p: dict) -> str:
    """How to cite a project, in inline Markdown: what the project asks for (or its paper), its software DOI and
    CITATION.cff file; without any of these, the repository. Always with the version used, since results change
    between versions."""
    cite = p.get("cite") or {}
    bits = []
    if cite.get("text"):
        bits.append(" ".join(cite["text"].split()))
    elif p.get("paper"):
        bits.append("Cite the paper above.")
    if cite.get("doi"):
        bits.append(f"Software DOI: [{cite['doi']}](https://doi.org/{cite['doi']}).")
    if cite.get("cff"):
        bits.append(f"The repository has a [CITATION.cff]({cite['cff']}) file.")
    if not bits:
        return "The project does not say how to cite it. Cite the repository with the version or commit you used."
    return " ".join(bits) + " Name the version or commit you used."


def stated_conventions(impls: list[dict], on_metric: bool) -> list[tuple[dict, list[str]]]:
    """What implementations state about their conventions: on a metric page one entry per project (its general
    points and those of its rows for the metric); on a project page one entry per row that has its own."""
    if not on_metric:
        return [(i, i["conventions"]) for i in impls if i.get("conventions")]
    by_project: dict[str, list[dict]] = {}
    for i in impls:
        by_project.setdefault(i["_project"]["id"], []).append(i)
    out = []
    for rows in by_project.values():
        items = list(dict.fromkeys(c for i in rows for c in i["_conventions"]))
        if items:
            out.append((rows[0], items))
    return out


def covers(p: dict) -> list[tuple[dict, str]]:
    """The metrics a project's rows cover, in list order, each with what holds it back: "" (an available row),
    "partial" (it computes only part of the metric), "unreleased" or "proposed"; the best row of the metric decides."""
    rank = {"": 0, "partial": 1, "unreleased": 2, "proposed": 3}
    best: dict[str, tuple[dict, str]] = {}
    for i in p["_impls"]:
        state = "" if i["status"] == "available" else i["status"]
        state = "partial" if i.get("partial") and not state else state
        if i["metric"] not in best or rank[state] < rank[best[i["metric"]][1]]:
            best[i["metric"]] = (i["_metric"], state)
    return list(best.values())


def introduce(site: dict) -> str:
    """What the name stands for, then the site description: "LISQM stands for … It is a list …"."""
    text = site["description"].strip()
    return f"{site['name']} stands for {site['title']}. It is {text[:1].lower()}{text[1:]}"


def name_note(site: dict) -> str:
    """That the list computes nothing itself, and what is open."""
    return (f"{site['name']} does not compute anything itself; it lists the implementations and compares what they "
            "state. The listed implementations publish their source code, most under an open-source licence; a few "
            "have no licence file, or a source-available or non-commercial licence, as each project's page says. "
            f"The data of {site['name']} is open, but many of the standards the implementations follow are not free.")


GROUP_RULE = ("Each project is in one group. A project whose code could not be opened is under status unknown, one "
              "that computes nothing itself and calls another listed project is under others, and one that is "
              "archived or has had no commit for three years is legacy. Every other project keeps the standing "
              "recorded for it: established, newly released or developing. All lists follow the order established, "
              "newly released, developing, legacy, others, status unknown, so a project that is new, little used, no "
              "longer maintained or unverified is never suggested first. A few projects come before all others in "
              "every list, in bold")


def standing_sentence(p: dict) -> str:
    """For newly released projects: 'First released in … Not yet seen to be widely used.'; for legacy projects:
    since when they have not been maintained; otherwise ''."""
    if p.get("_group") == "legacy":
        last = f"its last commit was in {long_date(month(p['_last_commit']))}" if p.get("_last_commit") else ""
        if p.get("_archived"):
            return "Archived by its authors" + (f"; {last}" if last else "") + ". Kept here for reference."
        return f"Not maintained. {last[:1].upper()}{last[1:]}, more than three years ago. Kept here for reference."
    if p.get("standing") != "newly-released":
        return ""
    return f"{p.get('standing_note', '').strip()} Not yet seen to be widely used in the community.".strip()


def highlight_sentence(p: dict) -> str:
    """What a project page adds to the group: the highlight of a project shown in bold ('A widely used project.',
    'A very good implementation.'), or the standing note of an established project."""
    h = p.get("highlight")
    if h:
        return (h[0].upper() + h[1:] if h.startswith(("a ", "an ")) else f"A {h} project") + "."
    if p.get("standing") == "established" and p.get("standing_note"):
        return p["standing_note"].strip()
    return ""


def highlighted(projects: list[dict], name: Callable[[dict], str], t: Callable[[str], str] = lambda s: s) -> str:
    """The projects shown in bold, with their highlights: 'SQAT and MoSQITo (widely used), and sottek-hearing-model
    (a very good implementation)'."""
    labels: dict[str, list[str]] = {}
    for p in projects:
        labels.setdefault(p["highlight"], []).append(name(p))
    parts = [join_words(names) + t(f" ({label})") for label, names in labels.items()]
    if len(parts) < 2:
        return "".join(parts)
    return ", ".join(parts[:-1]) + ", and " + parts[-1]


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


LABELS = {"newly-released": "newly released", "developing": "developing", "legacy": "legacy", "also": "also",
          "via": "via", "unreleased": "unreleased", "proposed": "proposed"}


def by_language(impls: list[dict], name: Fmt,
                tags: dict[str, str] | None = None) -> list[tuple[str, list[str]]]:
    """Group implementations by each project's main (first-listed) language: [('Python', ['MoSQITo', …]), …].
    With `tags` ({'newly-released': …, 'legacy': …}), newly released and legacy projects get that marker after
    their name instead of the word in parentheses."""
    words = LABELS
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


LANGUAGE_ORDER = ["Python", "MATLAB", "Octave", "C", "C++", "C#", "Rust", "Julia"]
COVERAGE_COLUMNS = [("Python", {"Python"}), ("MATLAB/Octave", {"MATLAB", "Octave"}), ("C/C++", {"C", "C++"}),
                    ("Rust", {"Rust"}), ("Julia", {"Julia"})]


def language_order(lang: str) -> tuple[int, str]:
    return (LANGUAGE_ORDER.index(lang) if lang in LANGUAGE_ORDER else 99, lang.lower())


def coverage(m: dict) -> dict[str, str]:
    """Per language column: 'current' (an available implementation of the current edition), 'new' (the same,
    but only from newly released projects), 'partial' (only unreleased, proposed, older-edition or partial
    implementations) or '' (none).
    Bindings count: a C library with a Python interface covers Python."""
    known = set().union(*(langs for _, langs in COVERAGE_COLUMNS))
    out = {}
    for col, langs in COVERAGE_COLUMNS + [("Other", None)]:
        def matches(p: dict) -> bool:
            return bool(set(p["languages"]) & langs) if langs is not None else bool(set(p["languages"]) - known)
        impls = [i for i in m["_impls"] if matches(i["_project"]) and i["_ref"]["status"] != "in-development"]
        released = [i for i in impls if i["status"] == "available" and i["reference"] in m["current"]
                    and not i.get("partial")]
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
        return "unknown" if p.get("access") else "no release"
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
    """Per family, per metric: the editions in each column of the timeline and who implements each edition.

    Each metric row is {"metric", "cells": [[(ref, impls), …] per column], "first": first column used}.
    Implementations of one edition are ordered by `impl_rank`, so established projects come first.
    """
    bins = time_bins(index)
    out = []
    for fam, metrics in index.families_with_metrics():
        rows = []
        for m in metrics:
            cells: list[list[tuple[dict, list[dict]]]] = [[] for _ in bins]
            for rid in m["references"]:
                ref = index.ref[rid]
                n = bin_of(ref, bins)
                if n is None:
                    continue
                impls = sorted(dedupe([i for i in m["_impls"] if i["reference"] == rid and not i.get("partial")]),
                               key=impl_rank)
                cells[n].append((ref, impls))
            used = [n for n, c in enumerate(cells) if c]
            rows.append({"metric": m, "cells": cells, "first": used[0] if used else len(bins)})
        out.append((fam, rows))
    return out


def version_label(impl: dict) -> str:
    """What the timeline shows after a project name: the first version with this edition, or its state."""
    if impl["status"] == "proposed":
        found = re.search(r"/pull/(\d+)", impl.get("link") or "")
        return f"proposed in PR #{found.group(1)}" if found else "proposed"
    if impl["status"] == "unreleased":
        return "unreleased"
    return str(impl.get("since") or "")


def edition_state(m: dict, ref: dict) -> str:
    """'current' for the metric's current edition(s) and the other standards in force (a national standard has its
    own scope beside the ISO one), 'old' for superseded or withdrawn ones, 'dev' for drafts."""
    if ref["id"] in m["current"] or ref["status"] == "current":
        return "current"
    if ref["status"] in ("superseded", "withdrawn"):
        return "old"
    if ref["status"] == "in-development":
        return "dev"
    return ""


def faq(index: Index, name: Fmt, metric_link: Callable[[dict], str], t: Esc,
        page_link: Callable[[str, str], str]) -> list[tuple[str, str]]:
    """The key questions, answered from the data. Answers are HTML or Markdown depending on the callbacks;
    `page_link(path, label)` links another page of the site."""
    supers = index.super_projects()
    qa: list[tuple[str, str]] = []
    # Newer projects often check themselves against MoSQITo or SQAT, and some are built for a particular use.
    # The examples stay whatever group their projects move to.
    newly = index.group("newly-released")
    checked = [p for p in newly
               if any(c in ("mosqito", "sqat") for i in p["_impls"] for c in i.get("compared_with") or [])]
    uses = [name(index.project[pid]) + t(text) for pid, text in (
        ("metasona", " is a C library written for fast, real-time analysis, with a rolling analyser for audio that "
                     "arrives in chunks"),
        ("iso532-1-rs", " is a Rust engine with a streaming interface and a C interface"),
        ("torch-amt", " brings the AMT loudness models to PyTorch, differentiable and able to run on GPU"),
    ) if pid in index.project]
    choose = [
        "Choose by your own environment first: the language you work in and how the results will be used.",
        f"The {page_link(LANGUAGES, 'Languages')} page shows which metrics can be computed from each language and "
        "how each project can be called, also from another language.",
        f"The {page_link(METRICS, 'Metrics')} page names the current edition of each of the {len(index.metrics)} "
        "metrics, and each metric page lists every implementation of it, with the validation it states, the code it "
        "was ported from and the choices that change its numbers.",
    ]

    def with_langs(p: dict) -> str:
        return name(p) + t(f" ({', '.join(p['languages'])})")
    widely = [p for p in supers if p["highlight"] == "widely used"]
    others = [p for p in supers if p["highlight"] != "widely used"]
    if widely:
        choose.append("Those widely used projects, " + join_words([with_langs(p) for p in widely])
                      + ", come first in the lists"
                      + (", together with " + join_words([with_langs(p) + t(f", {p['highlight']},") for p in others])
                         if others else ",")
                      + " but they are not the only choice.")
    elif supers:
        choose.append(highlighted(supers, name, t) + " come first in the lists, but they are not the only choice.")
    if checked:
        choose.append("Newer projects, not yet seen to be widely used, often check their results against MoSQITo or "
                      f"SQAT ({len(checked)} of the {len(newly)} newly released ones do)"
                      + (", and some are built for a particular use: " + "; ".join(uses) if uses else "") + ".")
    elif uses:
        choose.append("Some newer projects are built for a particular use: " + "; ".join(uses) + ".")
    if "pysqat" in index.project:
        choose.append(name(index.project["pysqat"]) + t(" ports SQAT to Python, adds a graphical interface and checks "
                                                        "each metric against SQAT v1.3."))
    choose.append("Before relying on any of them, check the validation each project states and whether the fix you "
                  "need is in a release or only on its main branch.")
    qa.append(("Which code should I use for a psychoacoustic metric?", " ".join(choose)))
    counts = []
    for col, _ in COVERAGE_COLUMNS:
        current = sum(coverage(m)[col] == "current" for m in index.metrics)
        new = sum(coverage(m)[col] == "new" for m in index.metrics)
        if current or new:
            counts.append(t(f"{col}: {current + new} of {len(index.metrics)}")
                          + (t(f" ({new} only from newly released projects)") if new else ""))
    qa.append(("Which metrics can I compute in Python, MATLAB or C?",
               "Metrics whose current edition has a released open-source implementation, by language: "
               + "; ".join(counts) + f". The {page_link(LANGUAGES, 'Languages')} page lists them, and explains how "
               "each project can be used from another language, for example a MATLAB toolbox from Python through "
               "the MATLAB Engine API."))
    qa.append(("Why does it matter which edition a tool implements?",
               "Psychoacoustic standards change between editions. ECMA-418-2, for example, has had four editions "
               "since 2020 that changed the hearing model, roughness and loudness, and all three parts of ISO 532 "
               "are being revised. Two tools that both claim to implement a standard can therefore give different "
               "values for the same sound. Liu et al. (2026, Acoustics Australia, doi:10.1007/s40857-026-00393-3) "
               "compared four tools and found differences large enough to change the predictions of sound-quality "
               "models. Each metric page lists the editions and which tool follows which."))
    gaps = index.gaps()
    answer = (("No available open-source implementation of the current edition was found for "
               + join_words([metric_link(m) for m in gaps]) + ".") if gaps else
              "Every metric in the list has at least one available implementation of its current edition.")
    if index.new_only():
        answer += (" The current editions of " + join_words([metric_link(m) for m in index.new_only()])
                   + " have released implementations only from newly released projects, not yet seen to be widely used.")
    qa.append(("Which metrics have no open-source implementation yet?", answer))

    def names(key: str, note: Callable[[dict], str]) -> str:
        return join_words([name(p) + t(f" ({note(p)})") for p in index.group(key)])
    groups = (
        "Every project is in one group. Established: " + t(GROUPS_TEXT["established"])
        + " Newly released: " + t(GROUPS_TEXT["newly-released"])
        + " Developing: " + t(GROUPS_TEXT["developing"])
        + " Legacy: " + t(GROUPS_TEXT["legacy"])
        + " Others: " + t(GROUPS_TEXT["others"])
        + " Status unknown: " + t(GROUPS_TEXT["unknown"])
        + " Lists follow this order, so a project that is new, little used, no longer maintained or unverified "
        "is never suggested first. " + highlighted(supers, lambda p: t(p["name"]), t)
        + " come first in every list, in bold, and they and the reference programs published with a standard are "
        "never listed as legacy.")
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
               "with links to those sources. The list records what a project claims and does not run the code. "
               "Repository and package metadata are refreshed monthly, and a person reviews new findings."))
    return qa


def ai_guide(index: Index) -> tuple[str, list[tuple[str, str, list[str]]]]:
    """The For AI page, in inline Markdown with absolute links (shared by the HTML page and its Markdown twin):
    an introduction and (anchor, heading, items) sections."""
    site = index.site
    base, repo = site["base_url"], site["repository"]
    langs = join_words(index.languages())
    intro = ("This page is for AI agents, crawlers and language models that read the list for someone. It gives "
             "the same data in forms that are easy to retrieve, parse and quote.")
    sections = [
        ("start", "Where to start", [
            f"[llms.txt]({base}llms.txt): a short summary with a link to the Markdown version of every page, "
            "following the [llms.txt proposal](https://llmstxt.org/).",
            f"[llms-full.txt]({base}llms-full.txt): every page in one Markdown file.",
            f"[index.json]({base}index.json): the whole index as JSON (metrics, editions, projects, implementations, "
            f"groups and coverage). Field definitions: [data/SCHEMA.md]({repo}/blob/main/data/SCHEMA.md).",
            f"[{BIBTEX}]({base}{BIBTEX}): every standard, model paper and software paper in the list, as BibTeX.",
            "A Markdown version of every page: replace `.html` with `.md`, for example "
            f"[metrics/loudness-zwicker.md]({base}metrics/loudness-zwicker.md) or "
            f"[projects/sqat.md]({base}projects/sqat.md).",
            f"[sitemap.xml]({base}sitemap.xml) lists every page and [feed.xml]({base}feed.xml) the updates. Each HTML "
            "page also carries schema.org JSON-LD.",
            f"All crawlers, AI crawlers included, may read every page ([robots.txt]({base}robots.txt)).",
        ]),
        ("contents", "What the data contains", [
            f"{plural(len(index.metrics), 'metric')} in {plural(len(index.families), 'group')}, "
            f"{plural(len(index.projects), 'project')} in {langs}, and "
            f"{plural(len(index.references), 'standard or model paper', 'standards and model papers')}. "
            f"Data as of {index.as_of()}.",
            "Every implementation names the standard edition or model paper it follows, its functions, whether "
            "it is released, merged but unreleased, or only proposed, and its validation evidence as stated by the "
            "project.",
            "Every project belongs to a group: established, newly released (first released less than about a year "
            "ago and not yet seen to be widely used), developing, legacy (archived, or no commit for three years or more), "
            "other (it calls another listed project) or status unknown (its code could not be opened, so only what "
            "it claims is listed).",
            "Every implementation that was ported from other code names that code, and comparisons with it are "
            "marked as not independent. Each metric page has a project map with the lines for that metric, and the "
            "conventions to check before comparing numbers between implementations.",
            f"The [project map]({base}{MAP}) ([Markdown]({base}{md_twin(MAP)})) shows how the projects are "
            "connected: code taken from another project, the author's own code, use at run time, results checked "
            "against another project, and shared contributors.",
            "Every entry links the documentation its facts were taken from.",
        ]),
        ("answering", "Answering questions with it", [
            "Name the current edition first (for Zwicker loudness, ISO 532-1:2017), then the projects that "
            "implement that edition. The lists start with "
            + highlighted(index.super_projects(), lambda p: p["name"]) + ", in bold, but the right project also "
            "depends on the language the reader works in and how the results will be used: the "
            f"[Languages]({base}{LANGUAGES}) page shows what can be computed from each language, and some projects "
            "are built for a particular use, such as real-time or streaming analysis.",
            "Say when a project is newly released or legacy, and when code is only on a main branch (unreleased) "
            "or in a pull request (proposed).",
            "Validation is as stated by each project; the list does not run the code.",
            "Give the date of the data and link the metric or project page, so that the reader can check it.",
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
            "Cite the implementations themselves as each project asks: every project page has a *How to cite* line. "
            f"The standards, model papers and software papers are in [{BIBTEX}]({base}{BIBTEX}).",
            "Short description: a list of open-source implementations of psychoacoustic metrics, organised by the "
            "standard edition each one follows, with a source for every entry.",
            site["credit"],
        ]),
    ]
    return intro, sections
