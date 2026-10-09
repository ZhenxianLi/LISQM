"""The project map: how the listed projects are connected, as their implementation rows record it.

Sources stand to the left of the map: code and use run from the source to the project that uses it, and a check
points back from the project to the one it checked its results against.

- ported or adapted code: a row's `derived_from` (else the project's `based_on`); "own" when every row of the pair
  says `derived_by_author`, that is, the code was moved by its own author or within the same team;
- used at run time: a row's `via` (another project does the computation) and `uses` (it needs another project);
- results checked: a row's `compared_with`, leaving out comparisons with related code (`_relation`) and pairs that
  another line already joins;
- same contributor: a person named in `maintainers` or `contributors` of both projects (no direction); not drawn
  beside a line of the author's own code, which says the same.

A metric page draws the same map from the rows of that metric only. The picture is drawn by Graphviz (`dot`) when
the site is built, in two passes: every line has an end of its own on the side of each box, and the second pass
orders those ends by where the box at the other end of the line was placed in the first. Without Graphviz the
page keeps the same relations in words and says that the picture is missing; on a CI runner (`CI` set) a missing
Graphviz is an error.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from collections import Counter

from .data import Index
from .describe import in_sentence
from .paths import STANDARDS, project_path, relative
from .text import join_words

# Line styles: colour, width, Graphviz style, whether the line has an arrowhead.
LINES = {
    "port": ("#2b3137", 1.5, "solid", True),
    "own": ("#1a7f64", 2.2, "solid", True),
    "uses": ("#866600", 1.8, "dotted", True),
    "compare": ("#2463ad", 1.3, "dashed", True),
    "people": ("#aeb6bf", 1.3, "solid", False),
}
# The kinds of line, as the legend names them and as the page explains them (shared by the HTML page and its
# Markdown twin).
LEGEND = [("port", "ported or adapted from another project"), ("own", "the author's own code"),
          ("uses", "used at run time"), ("compare", "results checked against"), ("people", "same contributor")]
KINDS = [
    ("port", "Ported or adapted from another project",
     "The project's code for a metric was ported from the source (translated into another language) or adapted "
     "from it (reused with changes), or the whole project continues the source. A grey box is a program published "
     "with a standard or a paper."),
    ("own", "The author's own code",
     "The code was written by someone who also maintains the project that ported or adapted it: a contribution, a "
     "move or a translation within the same team, not a port by someone else."),
    ("uses", "Used at run time",
     "The project calls the source to compute the metric, or needs its results as input."),
    ("compare", "Results checked against",
     "The arrow points from the project to the one it checked its results against. Comparisons with the code a "
     "project was ported or adapted from, with a port of its own code or with another port of the same code are "
     "not drawn, because they only show that two versions of the same code agree."),
    ("people", "Same contributor",
     "Someone has worked on both projects, as a maintainer or with code of their own. Not drawn beside a line of "
     "the author's own code, which says the same."),
]


# The language of a box, as on the rest of the site (light colours: the site has no dark theme in use).
LANG_COLOURS = {"py": "#2463ad", "m": "#bd5512", "c": "#6b46a6", "rs": "#94471c", "jl": "#8b3aa9", "js": "#866600",
                "pd": "#36606e", "other": "#57606a"}
# Short labels for published programs, whose full names are long.
SHORT_CODE = {"ISO 532-1 Annex A reference program": "ISO 532-1 Annex A program",
              "BASIC program of DIN 45631 (Zwicker et al., 1991)": "BASIC program (DIN 45631, 1991)"}
SERIF = "Charter,'Bitstream Charter','Sitka Text',Cambria,Georgia,'Noto Serif','DejaVu Serif',serif"
# Where lines meet a box (points): every line has an end of its own, this far from the next one, and none this close
# to the rounded top or bottom of the box. A box with many lines grows taller than BOX_HEIGHT.
PORT_GAP = 6.0
PORT_EDGE = 4.0
BOX_HEIGHT = 22.0
MONO = "ui-monospace,'SF Mono',Menlo,Consolas,'Liberation Mono','DejaVu Sans Mono',monospace"


def _add(items: list, item) -> None:
    if item not in items:
        items.append(item)


def people_of(p: dict) -> list[str]:
    """Everyone named as working on a project: its maintainers, then its other contributors."""
    return list(dict.fromkeys((p.get("maintainers") or []) + (p.get("contributors") or [])))


def relations(index: Index, metric: dict | None = None) -> dict:
    """Every recorded relation between listed projects, and the published programs they took code from; with
    `metric`, only the relations recorded in the rows of that metric (and shared contributors among its projects)."""
    def rows(p: dict) -> list[dict]:
        return [i for i in p["_impls"] if metric is None or i["_metric"] is metric]

    def what(i: dict) -> str:
        """What a line is about: the metric, or on the map of one metric the edition."""
        return i["_ref"]["label"] if metric else i["_metric"]["name"]

    taken: dict[tuple, dict] = {}   # (source key, project id) -> pair
    refs: dict[str, Counter] = {}   # a published program -> the editions of the rows that took code from it
    for p in index.projects_by_group():
        for i in rows(p):
            for cid, (name, q) in zip(i["_derived_ids"], i["_derived"]):
                e = taken.setdefault((cid, p["id"]), {"key": cid, "source": q, "name": name, "project": p,
                                                       "metrics": [], "rows": []})
                _add(e["metrics"], what(i))
                e["rows"].append(i)
                if q is None:
                    refs.setdefault(cid, Counter())[i["reference"]] += 1
    for e in taken.values():
        e["own"] = all(i.get("derived_by_author") for i in e["rows"])
        e["shared"] = [m for m in people_of(e["project"]) if e["source"] and m in people_of(e["source"])]
    joined = {frozenset((k, pid)) for k, pid in taken}

    uses: dict[tuple, dict] = {}    # (user id, source id) -> {"calls": [...], "needs": [...]}
    for p in index.projects_by_group():
        for i in rows(p):
            if i.get("_via"):
                _add(uses.setdefault((p["id"], i["_via"]["id"]), {"calls": [], "needs": []})["calls"], what(i))
            for q in i.get("_uses") or []:
                _add(uses.setdefault((p["id"], q["id"]), {"calls": [], "needs": []})["needs"], what(i))
    joined |= {frozenset(k) for k in uses}

    compares: dict[tuple, list] = {}  # (project id, the project it compared with) -> metrics
    for p in index.projects_by_group():
        for i in rows(p):
            for c in i.get("compared_with") or []:
                if c in index.project and c not in (i.get("_relation") or {}) and not i.get("via") \
                        and frozenset((p["id"], c)) not in joined:
                    _add(compares.setdefault((p["id"], c), []), what(i))

    # A person on both projects: a grey line, also beside a line of another kind, but not beside a line of the
    # author's own code, which already says that the same people are involved.
    own = {frozenset((e["key"], e["project"]["id"])) for e in taken.values() if e["own"]}
    people: dict[tuple, list] = {}
    by_person: dict[str, list] = {}
    for p in index.projects_by_group():
        if p["_group"] == "unknown" or not rows(p):
            continue
        for m in people_of(p):
            by_person.setdefault(m, []).append(p)
    for m, ps in by_person.items():
        for n, a in enumerate(ps):
            for b in ps[n + 1:]:
                if frozenset((a["id"], b["id"])) not in own:
                    _add(people.setdefault((a["id"], b["id"]), []), m)
    return {"taken": list(taken.values()), "uses": uses, "compares": compares, "people": people,
            "code_refs": {k: c.most_common(1)[0][0] for k, c in refs.items()}, "metric": metric}


def metrics(names: list[str]) -> str:
    """Metric names in a sentence: 'Zwicker loudness and roughness (Daniel & Weber)'; with semicolons when a name
    has an "and" of its own."""
    names = [in_sentence(n) for n in names]
    return "; ".join(names) if any(" and " in n for n in names) else join_words(names)


def lines(index: Index, rel: dict) -> list[dict]:
    """The lines of the map as {kind, source, user, tip}: the source is drawn to the left of the user. For a check,
    the source is the project checked against, and the arrowhead is drawn at its end."""
    name = lambda pid: index.project[pid]["name"]  # noqa: E731
    about = join_words if rel.get("metric") else metrics  # editions on the map of one metric, else metrics
    out = []
    for e in rel["taken"]:
        if e["own"]:
            who = f" ({join_words(e['shared'])})" if e["shared"] else ""
            tip = f"Author's own code: {e['name']} to {e['project']['name']}{who}, for {about(e['metrics'])}"
        else:
            tip = f"Ported or adapted: {e['name']} to {e['project']['name']}, for {about(e['metrics'])}"
        out.append({"kind": "own" if e["own"] else "port", "source": e["key"], "user": e["project"]["id"],
                    "tip": tip})
    for (a, b), d in rel["uses"].items():
        bits = ([f"calls {name(b)} for {about(d['calls'])}"] if d["calls"] else []) + \
               ([f"needs {name(b)} for {about(d['needs'])}"] if d["needs"] else [])
        out.append({"kind": "uses", "source": b, "user": a, "tip": f"Used at run time: {name(a)} {' and '.join(bits)}"})
    for (a, b), ms in rel["compares"].items():
        out.append({"kind": "compare", "source": b, "user": a,
                    "tip": f"Results checked: {name(a)} against {name(b)}, for {about(ms)}"})
    for (a, b), names in rel["people"].items():
        out.append({"kind": "people", "source": a, "user": b,
                    "tip": f"Same contributor: {name(a)} and {name(b)} ({join_words(names)})"})
    return out


# ---------------------------------------------------------------------------------------------- the picture

def _q(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _ports(side: str, count: int, height: float) -> str:
    """A column of `count` line ends ("i0", "i1" … or "o0" …) spread over the height of a box."""
    if not count:
        return f'<TD WIDTH="1" HEIGHT="{height:.1f}"></TD>'
    step = (height - 2 * PORT_EDGE) / count
    pad = f'<TR><TD WIDTH="1" HEIGHT="{PORT_EDGE:g}" FIXEDSIZE="TRUE"></TD></TR>'
    ends = "".join(f'<TR><TD PORT="{side}{n}" WIDTH="1" HEIGHT="{step:.2f}" FIXEDSIZE="TRUE"></TD></TR>'
                   for n in range(count))
    return f'<TD><TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0">{pad}{ends}{pad}</TABLE></TD>'


def dot_source(index: Index, rel: dict, path: str, lang_codes: dict, pos: dict | None = None) -> str:
    """The map as a Graphviz graph, left to right, with curved lines; every box links to its page.

    A line leaves a box from an end of its own on the box's right side and enters the next box on its left side.
    With `pos` (each box's (x, y) in a first layout) the ends are ordered by the box at the other end of the line,
    top first, so that lines neither share an end nor cross where they meet a box; a grey line between two
    columns gets ends too, while one between boxes of the same column joins them directly."""
    out = ["digraph map {",
           '  graph [rankdir=LR, splines=spline, nodesep=0.22, ranksep=1.1, newrank=true, bgcolor="transparent", '
           'pad=0.1];',
           '  node [shape=plain, fontname="DejaVu Serif", fontsize=12];',
           "  edge [arrowsize=0.75];"]
    drawn = lines(index, rel)
    ended = [line for line in drawn if LINES[line["kind"]][3]]
    loose = []
    for line in drawn:
        if LINES[line["kind"]][3]:
            continue
        if pos and abs(pos[line["source"]][0] - pos[line["user"]][0]) > 20:
            left, right = sorted((line["source"], line["user"]), key=lambda k: pos[k][0])
            ended.append(dict(line, source=left, user=right))
        else:
            loose.append(line)
    ins: dict[str, list[int]] = {}
    outs: dict[str, list[int]] = {}
    for n, line in enumerate(ended):
        outs.setdefault(line["source"], []).append(n)
        ins.setdefault(line["user"], []).append(n)
    if pos:  # Graphviz's y grows upwards
        for ends, other in ((outs, "user"), (ins, "source")):
            for numbers in ends.values():
                numbers.sort(key=lambda n: -pos[ended[n][other]][1])

    def node(key: str) -> str:
        k_in, k_out = len(ins.get(key, [])), len(outs.get(key, []))
        height = max(BOX_HEIGHT, PORT_GAP * max(k_in, k_out) + 2 * PORT_EDGE)
        p = index.project.get(key)
        if p:
            code, cls = lang_codes.get(p["languages"][0], (p["languages"][0][:2].lower(), "other"))
            colour = LANG_COLOURS.get(cls, LANG_COLOURS["other"])
            label = _html(p["name"])
            if p["_super"]:
                label = f"<b>{label}</b>"
            alpha = "9e" if p["_group"] == "legacy" else ""  # legacy projects are faded, as elsewhere
            text = (f'<font face="DejaVu Sans Mono" point-size="10" color="{colour}{alpha}">{_html(code)}</font>  '
                    f'<font color="#1f2328{alpha}">{label}</font>')
            box = (f'BORDER="{2 if p["_super"] else 1}" COLOR="{"#1f2328" if p["_super"] else colour}{alpha}" '
                   'BGCOLOR="white" STYLE="rounded"')
            attrs = (f'URL={_q(relative(path, project_path(p)))}, '
                     f'tooltip={_q(p["name"] + ": " + ", ".join(p["languages"]))}')
        else:  # a program published with a standard or a paper
            full = next(e["name"] for e in rel["taken"] if e["key"] == key)
            ref = rel["code_refs"].get(key)
            text = f'<font color="#5a636e"><i>{_html(SHORT_CODE.get(full, full))}</i></font>'
            box = 'BORDER="1" COLOR="#8b949e" BGCOLOR="#f3f4f6" STYLE="rounded,dashed"'
            url = f"URL={_q(relative(path, STANDARDS) + '#ref-' + ref)}, " if ref else ""
            attrs = f'{url}tooltip={_q(full + ", published with the standard or paper")}'
        label = (f'<<TABLE {box} CELLBORDER="0" CELLSPACING="0" CELLPADDING="0"><TR>{_ports("i", k_in, height)}'
                 f'<TD HEIGHT="{height:.1f}" CELLPADDING="3">{text}</TD>{_ports("o", k_out, height)}</TR></TABLE>>')
        return f"  {_q(key)} [label={label}, {attrs}];"

    def edge(line: dict, ends: list[str]) -> str:
        colour, width, style, arrow = LINES[line["kind"]]
        attrs = [f'color="{colour}"', f"penwidth={width}", f"style={style}", f"tooltip={_q(line['tip'])}",
                 f"edgetooltip={_q(line['tip'])}"] + ends
        if not arrow:  # same contributor: no direction, and no say in the left-to-right order
            attrs += ["dir=none", "constraint=false"]
        elif line["kind"] == "compare":  # placed like a source on the left, but A's results checked against B
            attrs.append("dir=back")
        return f"  {_q(line['source'])} -> {_q(line['user'])} [{', '.join(attrs)}];"

    # The projects that no line joins (on the map of one metric, that metric's): boxes without lines, under a short
    # label, in the first column below the rest (declared first and bottom up, as Graphviz stacks a left-to-right
    # graph from the bottom).
    single = alone(index, rel)
    if single:
        out += [node(p["id"]) for p in reversed(single)]
        out.append('  "alone:label" [shape=plaintext, label=<<font color="#6e7781" point-size="11"><i>no relation '
                   'recorded</i></font>>];')
        out.append("  {rank=same; " + "; ".join(_q(k) for k in [p["id"] for p in reversed(single)] + ["alone:label"])
                   + "}")
    keys = dict.fromkeys(k for line in drawn for k in (line["source"], line["user"]))
    out += [node(key) for key in keys]
    out += [edge(line, [f'tailport="o{outs[line["source"]].index(n)}:e"',
                        f'headport="i{ins[line["user"]].index(n)}:w"']) for n, line in enumerate(ended)]
    out += [edge(line, []) for line in loose]
    return "\n".join(out + ["}"])


def svg(index: Index, rel: dict, path: str, lang_codes: dict,
        title: str = "Project map: the same relations are listed in words below the picture.") -> str:
    """The map as inline SVG, or '' when Graphviz is not installed (an error on a CI runner). `title` describes
    the whole picture."""
    if not shutil.which("dot"):
        if os.environ.get("CI"):
            raise SystemExit("Graphviz (the dot program) is needed to draw the project map; install it first.")
        print("warning: Graphviz (dot) not found; the project map is built without its picture")
        return ""
    # First pass: where the boxes go; second pass: the same, with the ends of the lines in the order of the boxes
    # they lead to.
    first = subprocess.run(["dot", "-Tjson0"], input=dot_source(index, rel, path, lang_codes), capture_output=True,
                           text=True, check=True)
    pos = {o["name"]: tuple(float(v) for v in o["pos"].split(","))
           for o in json.loads(first.stdout).get("objects", []) if "pos" in o}
    result = subprocess.run(["dot", "-Tsvg"], input=dot_source(index, rel, path, lang_codes, pos),
                            capture_output=True, text=True, check=True)
    text = result.stdout[result.stdout.index("<svg"):]
    # Scale with the page (the viewBox stays), and use the site's type where it is installed.
    # At most life size, and never so small that the labels shrink below about 9 px: a narrow screen scrolls.
    found = re.search(r'viewBox="[\d.]+ [\d.]+ ([\d.]+) [\d.]+"', text)
    width = float(found.group(1)) if found else 1000.0
    text = re.sub(r'<svg width="[^"]*" height="[^"]*"',
                  f'<svg class="map-graph" style="max-width:{width:.0f}px;min-width:{width * 0.78:.0f}px"', text,
                  count=1)
    text = text.replace('font-family="DejaVu Serif"', f'font-family="{SERIF}"')
    text = text.replace('font-family="DejaVu Sans Mono"', f'font-family="{MONO}"')
    # Tooltips: what a box or line stands for, not Graphviz's internal names.
    text = text.replace("<title>map</title>", f"<title>{_html(title)}</title>", 1)
    text = re.sub(r'<title>[^<]*</title>(\s*<g id="a_[^"]*"><a (?:xlink:href="[^"]*" )?xlink:title="([^"]*)")',
                  r"<title>\2</title>\1", text)
    # A wider, invisible line over each line, so that it is easy to hover.
    text = re.sub(r'(<g id="edge\d+" class="edge">.*?<path fill="none" [^>]*?d="([^"]*)"/>)',
                  r'\1\n<path class="hit" fill="none" stroke="transparent" stroke-width="12" d="\2"/>', text,
                  flags=re.S)
    return text


def alone(index: Index, rel: dict) -> list[dict]:
    """Listed projects that no line joins (projects with unverified code are left out); on the map of one metric,
    the projects with a row for that metric that no line joins."""
    shown = ({e["project"]["id"] for e in rel["taken"]} | {e["key"] for e in rel["taken"]}
             | {k for pair in list(rel["uses"]) + list(rel["compares"]) + list(rel["people"]) for k in pair})
    of_metric = {i["_project"]["id"] for i in rel["metric"]["_impls"]} if rel.get("metric") else None
    return [p for p in index.projects_by_group() if p["id"] not in shown and p["_group"] != "unknown"
            and (of_metric is None or p["id"] in of_metric)]


def count_lines(rel: dict) -> int:
    return len(rel["taken"]) + len(rel["uses"]) + len(rel["compares"]) + len(rel["people"])


def shown(index: Index, rel: dict) -> set[str]:
    """What the legend needs: the kinds of line drawn, and "super", "legacy" and "code" for the kinds of box."""
    out = {line["kind"] for line in lines(index, rel)}
    keys = {k for line in lines(index, rel) for k in (line["source"], line["user"])}
    keys |= {p["id"] for p in alone(index, rel)}  # the projects that no line joins are drawn too
    projects = [index.project[k] for k in keys if k in index.project]
    out |= {"super"} if any(p["_super"] for p in projects) else set()
    out |= {"legacy"} if any(p["_group"] == "legacy" for p in projects) else set()
    out |= {"code"} if any(k not in index.project for k in keys) else set()
    return out
