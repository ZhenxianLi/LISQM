"""Markdown output: a .md twin of every page, llms.txt, llms-full.txt, README tables and CHANGELOG.md.

Links point to absolute URLs of the HTML pages, so the text stays useful when it is copied or quoted.
"""

from __future__ import annotations

import re

from .data import (ACCESS, GROUP_NAMES, GROUPS, IMPL_STATUS, IMPL_STATUS_LONG, KINDS, PROJECT_KINDS, REGISTRIES,
                   VALIDATION, VALIDATION_LONG, Index)
from .describe import (COVERAGE_COLUMNS, GROUP_RULE, NEW_LABEL, activity_text, ai_guide, by_language, coverage, dedupe,
                       highlight_sentence, highlighted,
                       covers, dependence_note, derived_names, edition_state, faq, how_to_cite, in_sentence, in_short,
                       introduce,
                       legacy_label, licence_flag, licence_flag_text, licence_names, licence_terms, name_note,
                       ref_status, release_text,
                       silent_line, standing_sentence, stated_conventions, timeline, validation_also,
                       validation_groups, validation_label, version_label)
from . import relations as RL
from .paths import (ABOUT, AI, BIBTEX, FAQ, HOME, LANGUAGES, MAP, METRICS, PROJECTS, STANDARDS, UPDATES, absolute,
                    md_twin, metric_path, project_path)
from .text import first_sentence, join_words, long_date, month, oneline, plain, plural

def _plain(text: str) -> str:
    return text


def _bold(p: dict, text: str) -> str:
    """A project's name or link, in bold for a super project."""
    return f"**{text}**" if p["_super"] else text


def _namer(index: Index, target=None):
    """Project names as links (to the web page, or to `target(p)`), in bold for super projects."""
    return lambda p: _bold(p, f"[{p['name']}]({target(p) if target else absolute(index, project_path(p))})")


def _metric_link(index: Index, m: dict, label: str | None = None) -> str:
    return f"[{label or m['name']}]({absolute(index, metric_path(m))})"


def _ref_link(r: dict) -> str:
    url = r.get("url") or (f"https://doi.org/{r['doi']}" if r.get("doi") else "")
    return f"[{r['label']}]({url})" if url else r["label"]


def _header(index: Index, path: str) -> str:
    site = index.site
    return (f"> Part of [{site['name']}]({site['base_url']}) ({site['title']}), a list of open-source "
            f"implementations of psychoacoustic metrics. Data as of {index.as_of()}. Web page: {absolute(index, path)}")


def _table(head: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(oneline(c) or "—" for c in row) + " |" for row in rows]
    return out


def _impl_note(i: dict) -> str:
    bits = {"newly-released": ["Newly released project, not yet seen to be widely used."],
            "developing": ["Developing project: no publication or documented use by others."],
            "legacy": ["Legacy project, no longer maintained."]}.get(i["_project"]["_group"], [])
    if licence_flag(i["_project"], i):
        bits.append(licence_flag_text(i["_project"], i))
    if i["status"] != "available":
        label = IMPL_STATUS[i["status"]]
        bits.append(label[:1].upper() + label[1:] + (f" ({i['link']})" if i.get("link") else "") + ".")
    if i.get("partial"):
        bits.append("Partial: computes only part of the metric.")
    if i.get("_via"):
        bits.append(f"Computed by {i['_via']['name']}.")
    if i.get("_uses"):
        bits.append(f"Uses {join_words([q['name'] for q in i['_uses']])}.")
    if i.get("note"):
        bits.append(i["note"].strip())
    return " ".join(bits)


def _edition_link(index: Index, r: dict) -> str:
    """The edition linked to the standard or paper, or to its full citation on the Standards page."""
    if r.get("url") or r.get("doi"):
        return _ref_link(r)
    return f"[{r['label']}]({absolute(index, STANDARDS)}#ref-{r['id']})"


def _edition(index: Index, i: dict) -> str:
    extra = ([i["scope"]] if i.get("scope") else []) + ([f"since {i['since']}"] if i.get("since") else [])
    return _edition_link(index, i["_ref"]) + (f" ({'; '.join(extra)})" if extra else "")


def _validation(i: dict) -> str:
    """Table cell: the stated evidence, naming what the implementation was compared with."""
    also = validation_also(i)
    scope = f" ({i['validation_scope']})" if i.get("validation_scope") else ""
    return validation_label(i) + scope + (f"; {also}" if also else "")


def _validation_section(index: Index, impls: list[dict], on_metric: bool) -> list[str]:
    """Markdown twin of the "How it was validated" section of the HTML pages."""
    name = _namer(index)
    groups, silent = validation_groups(impls, (lambda i: i["_project"]["id"]) if on_metric else (lambda i: ""))
    triples = [(i["_project"]["id"], i["metric"], i["reference"]) for i in impls]

    def title(i: dict, named: bool = True) -> str:
        edition = i["_ref"]["label"]
        if i.get("scope") and triples.count((i["_project"]["id"], i["metric"], i["reference"])) > 1:
            edition += f" ({i['scope']})"
        if not named:
            return edition
        head = name(i["_project"]) if on_metric else _metric_link(index, i["_metric"])
        if on_metric and i.get("_via"):
            head += f" (via {i['_via']['name']})"
        return f"{head}, {edition}"

    who = "each project" if on_metric else "the project"
    lines = [f"## How {'they were' if on_metric else 'it was'} validated", "",
             f"As reported by {who}; {index.site['name']} has not run the code. Two implementations that agree can "
             "still share the same error.", ""]
    if not on_metric and impls and impls[0]["_project"].get("maintainer_check"):
        lines += [maintainer_check(index, impls[0]["_project"]), ""]
    checked_by_maintainer: set[str] = set()
    for group in groups:
        i = group[0]
        evidence = validation_label(i, name) + (f" ({i['validation_scope']})" if i.get("validation_scope") else "")
        also = validation_also(i, name)
        # On a metric page a group is one project: name it once, then the editions.
        heads = [title(group[0])] + [title(j, named=not on_metric) for j in group[1:]]
        # Names stay as they are (super projects in bold), so the entry is not wrapped in bold.
        lines.append(f"- {'; '.join(heads)}: {evidence}" + (f"; {also}" if also else ""))
        own = " (the author's own code)" if i.get("derived_by_author") else ""
        origin = ([f"Ported or adapted from {join_words(derived_names(i, name))}{own}."] if i.get("_derived") else [])
        origin += [dependence_note(i)] if dependence_note(i) else []
        if origin:
            lines.append(f"  - {' '.join(origin)}")
        lines += [f"  - {oneline(d)}" for d in i.get("validation_details") or []]
        p = i["_project"]
        if on_metric and p.get("maintainer_check") and p["id"] not in checked_by_maintainer:
            lines.append(f"  - {maintainer_check(index, p)}")
            checked_by_maintainer.add(p["id"])
    if groups:
        lines.append("")
    if silent:
        if not groups:
            lines.append("None of these projects says how its code was validated." if on_metric
                         else "The project does not say how any of these were validated.")
        else:
            lines.append(silent_line(impls, groups, silent, on_metric))
        lines.append("")
    return lines


def maintainer_check(index: Index, p: dict) -> str:
    """The list maintainer's own observation about a project, set apart from what the project states."""
    return f"**Checked by the maintainer of {index.site['name']}:** {oneline(p['maintainer_check'])}"


def _labelled(impls: list[dict], name) -> list[str]:
    """Each project of these rows once, with its group when that is newly released, developing or legacy, and
    "unreleased" or "PR" (proposed) when none of its rows is released (the tags of the web pages, in words)."""
    rows: dict[str, list[dict]] = {}
    for i in impls:
        rows.setdefault(i["_project"]["id"], []).append(i)
    out = []
    for its in rows.values():
        p = its[0]["_project"]
        bits = [GROUP_NAMES[p["_group"]]] if p["_group"] in ("newly-released", "developing", "legacy") else []
        if not any(i["status"] == "available" for i in its):
            bits.append("unreleased" if any(i["status"] == "unreleased" for i in its) else IMPL_STATUS["proposed"])
        out.append(name(p) + (f" ({', '.join(bits)})" if bits else ""))
    return out


def _relation_lines(index: Index, rel: dict, level: str) -> list[str]:
    """The relations of a project map in words, one heading per kind of line (`level`: "##" or "###"), each with
    the metrics it is about; a map of one metric names the editions instead and leaves out kinds it has no line of."""
    name = _namer(index)

    def source(e: dict) -> str:
        return name(e["source"]) if e["source"] else e["name"]

    def what(names: list[str]) -> str:
        return f" ({join_words(names)})"

    sections: list[tuple[str, list[str]]] = []
    for own, heading in ((False, "Ported or adapted from another project"), (True, "The author's own code")):
        groups: dict[str, list[dict]] = {}
        for e in rel["taken"]:
            if e["own"] == own:
                groups.setdefault(e["key"], []).append(e)
        items = []
        for es in groups.values():
            people = list(dict.fromkeys(m for e in es for m in e["shared"]))
            who = f" ({join_words(people)})" if own and people else ""
            items.append(f"- From {source(es[0])}{who}: " + "; ".join(name(e["project"]) + what(e["metrics"])
                                                                       for e in es))
        sections.append((heading, items))
    uses = []
    for (a, b), d in rel["uses"].items():
        bits = ([f"calls {name(index.project[b])}{what(d['calls'])}"] if d["calls"] else []) + \
               ([f"needs {name(index.project[b])}{what(d['needs'])}"] if d["needs"] else [])
        uses.append(f"- {name(index.project[a])} {' and '.join(bits)}")
    sections.append(("Used at run time", uses))
    sections.append(("Results checked against another project",
                     [f"- {name(index.project[a])} against {name(index.project[b])}{what(ms)}"
                      for (a, b), ms in rel["compares"].items()]))
    sections.append(("Same contributor", [f"- {name(index.project[a])} and {name(index.project[b])} "
                                          f"({join_words(names)})" for (a, b), names in rel["people"].items()]))
    lines: list[str] = []
    for heading, items in sections:
        if items or not rel.get("metric"):
            lines += [f"{level} {heading}", ""] + items + [""]
    return lines


def _metric_map(index: Index, m: dict) -> list[str]:
    """Markdown twin of a metric page's project map: the lines of that metric, in words."""
    rel = RL.relations(index, m)
    if not RL.count_lines(rel):
        return []
    lines = ["## Project map", "",
             f"The lines of the project map for {in_sentence(m['name'])} only (the whole map: "
             f"{index.site['base_url']}{md_twin(MAP)})."
             + (" Agreement between a project and the code it was ported or adapted from only checks the port."
                if rel["taken"] else ""), ""]
    lines += _relation_lines(index, rel, "###")
    alone = RL.alone(index, rel)
    if alone:
        name = _namer(index)
        lines += ["On the map without a line, as no relation is recorded for them: "
                  + join_words([name(p) for p in alone]) + ".", ""]
    return lines


def _conventions(index: Index, impls: list[dict], general: list[str], on_metric: bool) -> list[str]:
    """Markdown twin of "Before you compare numbers"."""
    stated = stated_conventions(impls, on_metric)
    if not general and not stated:
        return []
    name = _namer(index)
    lines = ["## Before you compare numbers", "",
             "Implementations of the same metric can give different numbers without either being wrong. Check these "
             "choices first.", ""]
    lines += [f"- {oneline(c)}" for c in general]
    if general:
        lines.append("")
    if stated and (on_metric or general):
        lines += ["What the projects state:" if on_metric else "For single metrics:", ""]
    for i, items in stated:
        who = name(i["_project"]) if on_metric else f"{_metric_link(index, i['_metric'])} ({i['_ref']['label']})"
        lines.append(f"- {who}: " + " ".join(oneline(c) for c in items))
    return lines + [""]


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

def metric_page(index: Index, m: dict) -> str:
    name = _namer(index)
    fam = m["_family"]
    lines = [f"# {m['title']}", "", _header(index, metric_path(m)), ""]
    facts = [f"**Quantity:** {fam['name']}", f"**Unit:** {m['unit']}"]
    if m.get("aka"):
        facts.append(f"**Also known as:** {', '.join(m['aka'])}")
    lines += [" · ".join(facts), "", m["summary"].strip(), "",
              in_short(index, m, name, _plain), ""]
    if m.get("notes"):
        lines += [m["notes"].strip(), ""]

    lines += ["## Editions and who implements them", ""]
    rows = []
    for rid in reversed(m["references"]):
        r = index.ref[rid]
        impls = dedupe([i for i in m["_impls"] if i["reference"] == rid])
        who = ", ".join(name(i["_project"]) + ("" if i["status"] == "available" else f" ({IMPL_STATUS[i['status']]})")
                        for i in impls)
        status = ref_status(r) + (f"; {r['revision']}" if r.get("revision") else "")
        rows.append([month(r.get("date")) or "—", _edition_link(index, r), status,
                     (m.get("edition_notes") or {}).get(rid, ""), who])
    lines += _table(["Date", "Edition", "Status", "What changed", "Implemented by"], rows) + [""]

    lines += ["## Implementations", ""]
    if m["_impls"]:
        rows = [[name(i["_project"]), ", ".join(i["_project"]["languages"]), _edition(index, i), _functions(i),
                 _validation(i), _impl_note(i)] for i in m["_impls"]]
        lines += _table(["Project", "Language", "Edition", "Functions", "Validation (as stated)", "Notes"], rows)
    else:
        lines.append("No open-source implementation has been found yet. "
                     f"If you know one, please [open an issue]({index.site['repository']}/issues/new/choose).")
    lines += [""]
    if m["_via_impls"]:
        lines += ["Also available through tools that call one of these implementations: " + join_words(
            [f"{name(i['_project'])} (via {i['_via']['name']}, {i['_ref']['label']})" for i in dedupe(m["_via_impls"])])
            + ".", ""]
    if m.get("see_also"):
        lines += ["**See also:** " + ", ".join(_metric_link(index, index.metric[s], index.metric[s]["title"])
                                              for s in m["see_also"]), ""]
    checked = m["_all_impls"]  # every row, also those computed by another project
    if checked:
        lines += _validation_section(index, checked, on_metric=True)
    lines += _metric_map(index, m)
    lines += _conventions(index, checked, m.get("conventions") or [], on_metric=True)
    lines += ["## References", ""] + _reference_list([index.ref[r] for r in m["references"]]) + [""]
    return "\n".join(lines)


def project_page(index: Index, p: dict) -> str:
    lines = [f"# {p['name']}", "", _header(index, project_path(p)), ""]
    if p.get("access"):
        lines += [f"**Status unknown.** {ACCESS[p['access']]} {oneline(p['access_note'])} What it implements has not "
                  "been verified, so it is not listed under the metrics.", ""]
    if p["standing"] == "newly-released" and not p.get("access"):
        lines += [f"**Newly released project.** {standing_sentence(p)} Check its validation before relying on it.", ""]
    elif p["_group"] == "legacy":
        lines += [f"**Legacy project.** {standing_sentence(p)} Its code may follow an older edition and may not run "
                  "with current software.", ""]
    lines += [p["summary"].strip(), ""]
    facts = [("Full name", p["full_name"])] if p.get("full_name") else []
    facts.append(("Repository", p["repository"]))
    for key, label in (("homepage", "Homepage"), ("docs", "Documentation")):
        if p.get(key):
            facts.append((label, p[key]))
    facts += [("Language", ", ".join(p["languages"])), ("Kind", f"{PROJECT_KINDS[p['kind']]} ({KINDS[p['kind']]})"),
              ("Group", f"{GROUP_NAMES[p['_group']]} ({GROUPS[p['_group']]}"
                        + (" " + highlight_sentence(p) if highlight_sentence(p) else "")
                        + ")")]
    facts += [
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
        link = p["paper"].get("url") or (f"https://doi.org/{p['paper']['doi']}" if p["paper"].get("doi") else "")
        facts.append(("Paper", oneline(p["paper"]["citation"]) + (f" {link}" if link else "")))
    facts.append(("How to cite", how_to_cite(p)))
    facts.append(("Entry checked", str(p["checked"])))
    lines += [f"- **{k}:** {v}" for k, v in facts] + [""]

    if p.get("access"):
        lines += ["## What it is said to implement", "", oneline(p["claim"]), "",
                  "As described in the sources below; the code itself could not be checked.", ""]
    else:
        lines += ["## What it implements", ""]
        rows = [[_metric_link(index, i["_metric"]), _edition(index, i), _functions(i), IMPL_STATUS[i["status"]],
                 _validation(i), (i.get("note") or "").strip()] for i in p["_impls"]]
        lines += _table(["Metric", "Edition", "Functions", "Status", "Validation (as stated)", "Notes"], rows) + [""]
        lines += _validation_section(index, p["_impls"], on_metric=False)
        lines += _conventions(index, p["_impls"], p["_general_conventions"], on_metric=False)
    if p.get("notes"):
        lines += ["## Notes", ""] + [f"- {oneline(n)}" for n in p["notes"]] + [""]
    if p.get("caveats"):
        lines += ["## Before you rely on it", ""] + [f"- {oneline(c)}" for c in p["caveats"]] + [""]
    lines += ["## Sources", ""] + [f"- {s}" for s in p["sources"]] + [""]
    return "\n".join(lines)


def overview_rows(index: Index, link_metrics: bool = True) -> list[list[str]]:
    name = _namer(index)
    rows = []
    for fam, metrics in index.families_with_metrics():
        for m in metrics:
            groups = by_language(m["_current_impls"], name)
            cell = " · ".join(f"{lng}: {', '.join(names)}" for lng, names in groups) or "none found"
            older = [i for i in dedupe(m["_older_impls"]) if i["_ref"]["status"] != "in-development"]
            if older:
                cell += " · earlier or related: " + ", ".join(
                    f"{name(i['_project'])} ({i['_ref']['label']})" for i in older)
            rows.append([fam["name"], _metric_link(index, m) if link_metrics else m["name"],
                         join_words([index.ref[r]["label"] for r in m["current"]]), cell])
    return rows


COVERAGE_MARK = {"current": "●", "new": "◐", "partial": "○", "": "—"}


def coverage_table(index: Index) -> str:
    cols = [c for c, _ in COVERAGE_COLUMNS] + ["Other"]
    head = ["Metric"] + cols
    rows = []
    for m in index.metrics:
        cov = coverage(m)
        rows.append([_metric_link(index, m, m["name"])] + [COVERAGE_MARK[cov[c]] for c in cols])
    legend = ("● an available implementation of the current edition; ◐ the same, but only from newly released projects "
              "not yet seen to be widely used; ○ only unreleased, proposed, older-edition or partial implementations; "
              "— none found. Bindings count: a C library with a Python interface counts for Python.")
    return "\n".join(_table(head, rows)) + "\n\n" + legend


def _timeline_impl(i: dict, name) -> str:
    p = i["_project"]
    first = ", ".join(p["languages"]) + (f", {version_label(i)}" if version_label(i) else "")
    bits = [first]
    if i.get("_via"):
        bits.append(f"via {i['_via']['name']}")
    if p["_group"] == "legacy":
        bits.append(legacy_label(p))
    elif p["_activity"] in ("inactive", "archived"):
        bits.append(activity_text(p))
    if p["_group"] == "newly-released":
        bits.append(NEW_LABEL)
    elif p["_group"] == "developing":
        bits.append("developing")
    return f"{name(p)} ({'; '.join(bits)})"


def timeline_md(index: Index) -> list[str]:
    """The home-page timeline as nested lists: metric, then each edition (oldest first) and who implements it."""
    name = _namer(index)
    states = {"current": "current", "old": "", "dev": "in development", "": ""}
    lines = []
    for fam, rows in timeline(index):
        lines += [f"### {fam['name']}", ""]
        for row in rows:
            m = row["metric"]
            lines.append(f"- **{_metric_link(index, m)}** ({m['unit']})")
            for cell in row["cells"]:
                for ref, impls in cell:
                    state = edition_state(m, ref)
                    label = f"**{ref['label']}**" if state == "current" else ref["label"]
                    status = states[state] or (ref_status(ref) if ref["status"] != "published" else "")
                    who = ", ".join(_timeline_impl(i, name) for i in impls) or "no open-source implementation found"
                    when = month(ref.get("date")) or "undated"
                    lines.append(f"  - {when} · {label}" + (f" ({status})" if status else "") + f": {who}")
        lines.append("")
    return lines


def home(index: Index) -> str:
    site = index.site
    lines = [f"# {site['tagline']}", "", _header(index, HOME), "",
             site["description"].strip(), "",
             f"{plural(len(index.metrics), 'metric')} · {plural(len(index.projects), 'project')} · "
             f"languages: {', '.join(index.languages())}", ""]
    lines += ["## Editions and implementations", "",
              "Each metric is listed with the standard editions or model papers that define it, oldest first, and "
              "the projects that implement each one. The current edition is in bold. Each project is followed by its "
              "language and the first release that included the edition. Established projects come first. Projects "
              f"marked \"{NEW_LABEL}\" were first released less than about a year ago, and projects marked "
              "\"legacy\" are archived or have had no commit for three years or more.", ""]
    lines += timeline_md(index)
    lines += [f"The Languages page shows which metrics can be computed in each programming language: "
              f"{absolute(index, LANGUAGES)}", ""]
    gaps = index.gaps()
    if gaps:
        lines += ["## Gaps", "", "No available open-source implementation of the current edition was found for:", ""]
        lines += [f"- {_metric_link(index, m, m['title'])}" for m in gaps] + [""]
    if index.new_only():
        lines += ["For the following metrics, the only released implementations of the current edition come from "
                  "newly released projects, not yet seen to be widely used:", ""]
        lines += [f"- {_metric_link(index, m, m['title'])}" for m in index.new_only()] + [""]
    if index.updates:
        lines += ["## Recent updates", ""]
        for u in index.updates[:3]:
            first_paragraph = u["body"].strip().split("\n\n")[0]
            lines += [f"- **{u['date']}: {u['title']}.** {plain(first_paragraph)}"]
        lines += [""]
    return "\n".join(lines)


def metrics_page(index: Index) -> str:
    name = _namer(index)
    lines = ["# Metrics", "", _header(index, METRICS), "",
             f"{plural(len(index.metrics), 'metric')} in {plural(len(index.families), 'group')}: for each, the edition "
             "that an up-to-date implementation should follow and the projects that implement it.", ""]
    for fam, metrics in index.families_with_metrics():
        lines += [f"## {fam['name']}", ""]
        if fam.get("summary"):
            lines += [" ".join(fam["summary"].split()), ""]
        rows = []
        for m in metrics:
            current = join_words([index.ref[r]["label"] for r in m["current"]])
            who = ", ".join(_labelled(m["_current_impls"], name)) or "none found"
            rows.append([_metric_link(index, m), m["unit"], current, who])
        lines += _table(["Metric", "Unit", "Current edition", "Implementations of it"], rows) + [""]
    return "\n".join(lines)


LANGUAGE_SECTIONS = [("Python", {"Python"}), ("MATLAB and Octave", {"MATLAB", "Octave"}), ("C and C++", {"C", "C++"}),
                     ("C#", {"C#"}), ("Rust", {"Rust"}), ("Julia", {"Julia"}), ("Pure Data", {"Pure Data"})]


def languages_page(index: Index) -> str:
    name = _namer(index)
    listed = [p for p in index.projects_by_group() if p["_group"] not in ("others", "unknown")]
    lines = ["# Languages", "", _header(index, LANGUAGES), "",
             "Which metrics can be computed from each programming language, and how to use each project from it. "
             "Some projects are written in the language itself, some have a compiled core with an interface for it, "
             "and some are ports of another project.",
             "", "## Coverage by language", "", coverage_table(index), ""]
    for title, langs in LANGUAGE_SECTIONS:
        projects = [p for p in listed if langs & set(p["languages"])]
        if not projects:
            continue
        lines += [f"## {title}", ""]
        rows = []
        for p in projects:
            core = p.get("core") or p["languages"][0]
            lang = sorted(langs & set(p["languages"]))[0]
            how = f"Written in {core}" + ("" if core in langs else f", with a {lang} interface")
            if p.get("based_on"):
                how += f"; based on {index.project[p['based_on']]['name']}"
            how += "."
            if p.get("install"):
                how += f" `{p['install']}`"
            if p.get("language_note"):
                how += " " + " ".join(p["language_note"].split())
            metrics = list(dict.fromkeys(i["_metric"]["name"] + (" (partial)" if i.get("partial") else "")
                                         for i in p["_impls"]
                                         if i["reference"] in i["_metric"]["current"] and i["status"] == "available"
                                         and not i.get("_via")))
            group = GROUP_NAMES[p["_group"]]
            flags = ([group] if p["_group"] in ("newly-released", "developing", "legacy") else []) + (
                [licence_flag(p)] if licence_flag(p) else [])
            rows.append([name(p) + (f" ({', '.join(flags)})" if flags else ""), how,
                         ", ".join(metrics) or "older editions or unreleased code only"])
        lines += _table(["Project", "How it is used", "Current editions it implements"], rows) + [""]
    lines += ["## Calling code across languages", "",
              "- MATLAB code from Python: the MATLAB Engine API for Python "
              "(https://www.mathworks.com/help/matlab/matlab-engine-for-python.html) runs MATLAB functions from "
              "Python and needs a MATLAB installation and licence. This is how SQAT or the Auditory Modeling Toolbox "
              "can be used from Python. Without MATLAB, there are Python ports: pySQAT of SQAT, and torch_amt and "
              "NumpyLibforPsychoAcoustic of some AMT loudness models.",
              "- Octave code from Python: oct2py (https://pypi.org/project/oct2py/) runs GNU Octave functions from "
              "Python, without a MATLAB licence.",
              "- Python packages from MATLAB: MATLAB can call Python libraries directly "
              "(https://www.mathworks.com/help/matlab/call-python-libraries.html), for example MoSQITo.",
              "- C libraries from other languages: through ctypes or cffi in Python, ccall in Julia, or the foreign "
              "function interface of Rust and most other languages. MetaSona's Python package loads its C library "
              "this way, and iso532-1-rs has a C interface.",
              "- Python from Julia: PythonCall.jl (https://github.com/JuliaPy/PythonCall.jl).", ""]
    return "\n".join(lines)


def ai_page(index: Index) -> str:
    intro, sections = ai_guide(index)
    lines = ["# For AI agents and language models", "", _header(index, AI), "", intro, ""]
    for _, heading, items in sections:
        lines += [f"## {heading}", ""] + [f"- {item}" for item in items] + [""]
    return "\n".join(lines)


GROUP_HEADINGS = [("established", "Established projects"), ("newly-released", "Newly released projects"),
                  ("developing", "Developing projects"), ("legacy", "Legacy projects")]
OTHERS = GROUPS["others"] + " They are not listed under the metrics."


def _calls(p: dict) -> list[str]:
    """The listed projects that a tool under Others calls."""
    return list(dict.fromkeys(i["_via"]["name"] for i in p["_impls"] if i.get("_via")))


def projects_page(index: Index) -> str:
    name = _namer(index)
    lines = ["# Projects", "", _header(index, PROJECTS), "",
             f"{plural(len(index.projects), 'project')}. "
             + highlighted(index.super_projects(), lambda p: p["name"]) + " are in bold and come first, followed by "
             "the other established projects, then newly released, developing and legacy projects. Tools that only "
             "call another project's implementation are listed under Others, and projects whose code could not be "
             "opened under Status unknown. The project map shows how the projects are connected: "
             f"{absolute(index, MAP)}", ""]
    for key, title in GROUP_HEADINGS:
        projects = index.group(key)
        if not projects:
            continue
        lines += [f"## {title}", "", GROUPS[key], ""]
        rows = [[name(p), ", ".join(p["languages"]),
                 PROJECT_KINDS[p["kind"]], p["license"], release_text(p), p["_last_commit"] or "unknown",
                 activity_text(p), ", ".join(m["name"] + (f" ({IMPL_STATUS.get(state, state)})" if state else "")
                                             for m, state in covers(p))]
                for p in projects]
        lines += _table(["Project", "Language", "Kind", "Licence", "Latest release", "Last commit", "Activity",
                         "Covers"], rows) + [""]
    others = index.others()
    if others:
        lines += ["## Others", "", OTHERS, ""]
        rows = [[name(p), ", ".join(p["languages"]),
                 PROJECT_KINDS[p["kind"]], p["license"], release_text(p), p["_last_commit"] or "unknown",
                 activity_text(p), join_words(_calls(p))] for p in others]
        lines += _table(["Project", "Language", "Kind", "Licence", "Latest release", "Last commit", "Activity",
                         "Calls"], rows) + [""]
    unknown = index.group("unknown")
    if unknown:
        lines += ["## Status unknown", "", GROUPS["unknown"], ""]
        rows = [[name(p), ", ".join(p["languages"]),
                 PROJECT_KINDS[p["kind"]], p["license"], ACCESS[p["access"]], first_sentence(p["claim"])]
                for p in unknown]
        lines += _table(["Project", "Language", "Kind", "Licence", "Why unknown", "Claims"], rows) + [""]
    return "\n".join(lines)


def map_page(index: Index) -> str:
    """Markdown twin of the project map: the same relations, in words."""
    rel = RL.relations(index)
    name = _namer(index)
    lines = ["# Project map", "", _header(index, MAP), "",
             "Each line of the map joins two projects: code ported or adapted from another project, the author's own "
             "code moved between projects, a project that uses another one at run time, results checked against "
             "another project, or a shared contributor. The lines come from the implementation rows on the project "
             "pages. On the web page, arrows point from the source to the project that uses it, and a check points "
             "from the project to the one it checked its results against.", "",
             "## Kinds of line", ""]
    lines += [f"- **{kind_name}.** {text}" for _, kind_name, text in RL.KINDS] + [""]
    lines += _relation_lines(index, rel, "##")
    alone = RL.alone(index, rel)
    if alone:
        lines += ["On the map without a line, as no relation is recorded for them: "
                  + join_words([name(p) for p in alone]) + "."]
    unknown = index.group("unknown")
    if unknown:
        lines += ["", "Left out, as their code could not be opened: " + join_words([name(p) for p in unknown]) + "."]
    return "\n".join(lines).rstrip("\n") + "\n"


def standards_page(index: Index) -> str:
    lines = ["# Standards and models", "", _header(index, STANDARDS), "",
             "All documents the list refers to, newest first. Each implementation in the list is tied to one of "
             "these editions. They are also available as BibTeX, together with the papers that describe the listed "
             f"software: {index.site['base_url']}{BIBTEX}", ""]
    docs = [r for r in index.references if r["kind"] not in ("paper", "book", "thesis")]
    papers = [r for r in index.references if r["kind"] in ("paper", "book", "thesis")]
    for title, refs in (("Standards and regulations", docs), ("Model papers, books and theses", papers)):
        lines += [f"## {title}", ""]
        rows = []
        for r in sorted(refs, key=lambda r: (str(r.get("date") or "9999"), r["label"]), reverse=True):
            rows.append([month(r.get("date")) or "—", _ref_link(r), plain(r["title"]), ref_status(r),
                         ", ".join(_metric_link(index, m) for m in r["_metrics"])])
        lines += _table(["Date", "Document", "Title", "Status", "Used by"], rows) + [""]
    return "\n".join(lines)


def updates_page(index: Index) -> str:
    lines = ["# Updates", "", _header(index, UPDATES), ""]
    for u in index.updates:
        lines += [f"## {long_date(u['date'])}: {u['title']}", "", u["body"].strip(), ""]
    return "\n".join(lines)


def about_page(index: Index) -> str:
    site = index.site
    lines = [f"# About {site['name']}", "", _header(index, ABOUT), ""]
    if site.get("about_story"):
        def absolute_links(text: str) -> str:  # and super projects in bold, as everywhere
            text = re.sub(r"\]\((?!https?://)([^)\s]+)\)", lambda m: f"]({site['base_url']}{m.group(1)})", text)

            def bold(m: re.Match[str]) -> str:
                p = index.project.get(m.group(2))
                return f"**{m.group(0)}**" if p and p["_super"] else m.group(0)
            return re.sub(r"(?<!\*\*)\[([^\]]+)\]\([^)\s]*projects/([a-z0-9-]+)\.(?:html|md)\)", bold, text)
        lines += [absolute_links(" ".join(site["about_lead"].split())), "",
                  f"{site['name']} stands for {site['title']}. {name_note(site)}", "",
                  f"## Why I built {site['name']}", "", absolute_links(site["about_story"].strip()), "",
                  f"— {site['maintainer']['name']}", ""]
    else:
        lines += [introduce(site), "", name_note(site), ""]
    lines += ["## What is included", "",
              "The list includes open-source code that computes a psychoacoustic metric and says which model or "
              "standard edition it follows. Quantities: "
              + join_words([f["name"].lower() for f in index.families]) + ". "
              "Not included: LUFS / ITU-R BS.1770, speech intelligibility, codec quality metrics (PEAQ, PESQ, "
              "ViSQOL), psychophysics experiment software, music sensory-dissonance models, feature extractors "
              "whose loudness or sharpness follow no named psychoacoustic model, and closed-source tools. The ISO "
              "532 reference programs (free to download, not modifiable) are described on the standards' entries. "
              f"Reviewed exclusions are listed with reasons in {site['repository']}/blob/main/data/ignored.yaml.", ""]
    lines += ["## How entries are checked", "",
              "Each entry is written from the project's own README, documentation, release notes, licence file "
              "and package metadata, with links to those sources. The list records what a project claims. It "
              "does not run the code. Repository dates, releases and package versions are refreshed monthly "
              "by a GitHub Action, which also searches for new candidate projects and watches the standards "
              "bodies for new editions. A person reviews the findings before anything is added.", ""]
    lines += ["## Status of an implementation", ""]
    lines += _table(["Value", "Meaning"], [[IMPL_STATUS[k], v] for k, v in IMPL_STATUS_LONG.items()]) + [""]
    lines += ["## Validation evidence", "",
              "Validation is recorded as each project states it. When a project says what it compared its results "
              "with (MoSQITo, SQAT, the model authors' code or commercial software), the list names it, and the "
              "project page gives the details under *How it was validated*. Two implementations that agree compute "
              "the same values, but an error they share goes unnoticed.", ""]
    lines += _table(["Value", "Meaning"], [[VALIDATION[k], v] for k, v in VALIDATION_LONG.items()]) + [""]
    lines += ["## Standing of a project", "",
              GROUP_RULE + ": " + highlighted(index.super_projects(), lambda p: p["name"])
              + ". They are never listed as legacy, and neither are reference programs published with a standard.", ""]
    lines += _table(["Group", "Meaning"], [[GROUP_NAMES[k], v] for k, v in GROUPS.items()]) + [""]
    lines += ["## Kinds of project", "",
              "The kind says what a project is for someone who wants to use it. Each project page names it.", ""]
    lines += _table(["Kind", "Meaning"], [[PROJECT_KINDS[k], v] for k, v in KINDS.items()]) + [""]
    lines += ["## Leads not yet verified", "",
              "Candidates that may belong in the list but could not be checked yet. Nothing here has been "
              "confirmed.", ""]
    lines += [f"- [{l['name']}]({l['url']}) ({', '.join(l.get('languages') or [])}): {oneline(l['claim'])} {oneline(l['why'])}"
              for l in index.leads] + [""]
    lines += ["Not listed because they are closed source: MATLAB Audio Toolbox, HEAD acoustics ArtemiS SUITE, "
              "Simcenter Testlab, HBK BK Connect and Ansys Sound.", ""]
    lines += ["## Machine-readable data", "",
              f"- [index.json]({site['base_url']}index.json): the whole index as JSON",
              f"- [llms.txt]({site['base_url']}llms.txt) and [llms-full.txt]({site['base_url']}llms-full.txt): "
              "summaries for language models",
              f"- [feed.xml]({site['base_url']}feed.xml): Atom feed of updates",
              f"- [{BIBTEX}]({site['base_url']}{BIBTEX}): every standard, model paper and software paper, as BibTeX",
              f"- Source data and schema: {site['repository']}/tree/main/data", ""]
    if site.get("cloudflare_analytics_token"):
        lines += ["Visits to the website are counted with Cloudflare Web Analytics, which sets no cookies.", ""]
    lines += ["## Contributing and citing", "",
              f"Corrections and new projects are welcome through issues or pull requests: {site['repository']}. "
              "To cite the list, use the CITATION.cff file in the repository, and cite the implementations you "
              "used as each project page says under *How to cite*. The standards and papers are in "
              f"{site['base_url']}{BIBTEX}.", "",
              "## Licence", "",
              f"The data and the text (the list, the website, the README, llms.txt and index.json) are released under "
              f"{licence_names(site)[0]} ({site['license_url']}): {licence_terms(site)}. The code that builds the "
              f"website is released under the {licence_names(site)[1]} licence ({site['repository']}/blob/main/LICENSE). "
              "The listed projects have their own licences.", "",
              site["credit"], ""]
    return "\n".join(lines)


def faq_page(index: Index) -> str:
    lines = ["# Frequently asked questions", "", _header(index, FAQ), "",
             "Questions, corrections and suggestions are welcome as GitHub issues: "
             f"{index.site['repository']}/issues/new", ""]
    for q, a in faq(index, _namer(index), lambda m: _metric_link(index, m, m["title"]), _plain,
                    lambda target, label: f"[{label}]({absolute(index, target)})"):
        lines += [f"## {q}", "", a, ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------- LLM files

def llms_txt(index: Index) -> str:
    site = index.site
    twin = _namer(index, lambda p: f"{site['base_url']}{md_twin(project_path(p))}")
    lines = [f"# {site['name']}: {site['title']}", "", f"> {plain(site['description'])}", "",
             f"Data as of {index.as_of()}. {plural(len(index.metrics), 'metric')}, "
             f"{plural(len(index.projects), 'project')}, languages: {', '.join(index.languages())}. Each "
             "implementation is tied to the standard edition or model paper it follows, with its validation "
             "evidence as stated by the project. Repository and package metadata are refreshed monthly. "
             "Implementations are listed with established projects first, "
             + highlighted(index.super_projects(), lambda p: p["name"]) + " at the top and in bold. Projects marked "
             "(newly released) were "
             "first released less than about a year ago and are not yet seen to be widely used in the community; projects "
             "marked (legacy) are archived or have had no commit for three years or more.", "",
             site["credit"], ""]
    for fam, metrics in index.families_with_metrics():
        lines += [f"## {fam['name']}", ""]
        for m in metrics:
            current = join_words([index.ref[r]["label"] for r in m["current"]])
            projects = ", ".join(_labelled(m["_current_impls"], lambda p: p["name"])) or "none found"
            lines.append(f"- [{m['title']}]({site['base_url']}{md_twin(metric_path(m))}): current edition "
                         f"{current}; implementations: {projects}")
        lines.append("")
    lines += ["## Projects", ""]
    for p in index.projects_by_group():
        if p["_group"] in ("others", "unknown"):
            continue
        group = {"newly-released": "newly released (not yet seen to be widely used)", "legacy": legacy_label(p)}.get(p["_group"], p["_group"])
        if p.get("highlight"):
            group += ", " + p["highlight"]
        lines.append(f"- {twin(p)}: {', '.join(p['languages'])}; {group}; {first_sentence(p['summary'])}")
    if index.others():
        lines += ["", "## Others", "", OTHERS, ""]
        for p in index.others():
            lines.append(f"- {twin(p)}: "
                         f"{', '.join(p['languages'])}; calls {join_words(_calls(p))}"
                         + ("; newly released (not yet seen to be widely used)" if p["standing"] == "newly-released" else "")
                         + f"; {first_sentence(p['summary'])}")
    if index.group("unknown"):
        lines += ["", "## Status unknown", "", GROUPS["unknown"], ""]
        for p in index.group("unknown"):
            lines.append(f"- {twin(p)}: "
                         f"{', '.join(p['languages'])}; {ACCESS[p['access']].rstrip('.').lower()}; claims: "
                         f"{first_sentence(p['claim'])}")
    lines += ["", "## Data", "",
              f"- [index.json]({site['base_url']}index.json): the complete index as JSON",
              f"- [{BIBTEX}]({site['base_url']}{BIBTEX}): every standard, model paper and software paper as BibTeX",
              f"- [llms-full.txt]({site['base_url']}llms-full.txt): all pages in one Markdown file",
              f"- [Data schema]({site['repository']}/blob/main/data/SCHEMA.md)", "",
              "## Optional", "",
              f"- [For AI agents]({site['base_url']}{md_twin(AI)}): how to retrieve, read and cite this list",
              f"- [Metrics]({site['base_url']}{md_twin(METRICS)}): every metric with its current edition",
              f"- [Languages]({site['base_url']}{md_twin(LANGUAGES)}): coverage and calling details by language",
              f"- [Project map]({site['base_url']}{md_twin(MAP)}): code ported or adapted from another project, use "
              "at run time, results checked against another project, and shared contributors",
              f"- [Frequently asked questions]({site['base_url']}{md_twin(FAQ)})",
              f"- [About]({site['base_url']}{md_twin(ABOUT)}): scope, how entries are checked, definitions and data access",
              f"- [Standards timeline]({site['base_url']}{md_twin(STANDARDS)})",
              f"- [Updates]({site['base_url']}{md_twin(UPDATES)})",
              f"- [Source repository]({site['repository']})", ""]
    return "\n".join(lines)


def llms_full(index: Index) -> str:
    parts = [llms_txt(index), "", "---", "", about_page(index), "", "---", "", faq_page(index)]
    for m in index.metrics:
        parts += ["", "---", "", metric_page(index, m)]
    for p in index.projects_by_group():
        parts += ["", "---", "", project_page(index, p)]
    parts += ["", "---", "", map_page(index), "", "---", "", standards_page(index)]
    return "\n".join(parts).rstrip() + "\n"


# ---------------------------------------------------------------------------------------------- README

def readme_overview(index: Index) -> str:
    head = ["Quantity", "Metric", "Current edition", "Open-source implementations (by language)"]
    return "\n".join(_table(head, overview_rows(index)))


def readme_projects(index: Index) -> str:
    head = ["Project", "Standing", "Language", "Licence", "Latest release", "Last commit", "Activity"]

    def standing(p: dict) -> str:
        group = p["_group"]
        if group == "others":
            return f"other: calls {join_words(_calls(p))}"
        if group == "unknown":
            return "status unknown: code not public"
        if group == "legacy":
            return legacy_label(p)
        if group == "newly-released":
            return NEW_LABEL
        return group + (", " + p["highlight"] if p.get("highlight") else "")

    rows = [[_bold(p, f"[{p['name']}]({p['repository']})"), standing(p),
             ", ".join(p["languages"]), p["license"], release_text(p), p["_last_commit"] or "unknown",
             activity_text(p)]
            for p in index.projects_by_group()]
    return "\n".join(_table(head, rows))


def readme_gaps(index: Index) -> str:
    def item(m: dict) -> str:
        return f"- {_metric_link(index, m, m['title'])}"

    gaps = index.gaps()
    lines = [item(m) for m in gaps] or ["None at the moment."]
    if index.new_only():
        lines += ["", "For the following metrics, the only released implementations of the current edition come "
                  "from newly released projects, not yet seen to be widely used:", ""]
        lines += [item(m) for m in index.new_only()]
    return "\n".join(lines)


def readme_stats(index: Index) -> str:
    return (f"Data as of {index.as_of()}: {plural(len(index.metrics), 'metric')}, "
            f"{plural(len(index.projects), 'project')}, languages: {', '.join(index.languages())}.")


def changelog(index: Index) -> str:
    lines = ["# Changelog", "",
             "Notable changes to the list. This file is generated from `data/updates.yaml`; the same notes are "
             f"on the website ({absolute(index, UPDATES)}) and in its Atom feed.", ""]
    for u in index.updates:
        lines += [f"## {u['date']}: {u['title']}", "", u["body"].strip(), ""]
    return "\n".join(lines)
