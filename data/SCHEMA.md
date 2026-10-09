# Data model

Everything on the website, in the README tables and in `index.json` is generated from the files in this
directory. Edit these files, never the generated output.

| File | Edited by | Contents |
|---|---|---|
| `site.yaml` | people | Short name (LISQM), what it stands for, subtitle, base URL, maintainer, thresholds, IndexNow key, search engine verification codes |
| `metrics.yaml` | people | Metric families and metrics (one page per metric) |
| `references.yaml` | people | Standard editions, model papers and books that metrics are defined by |
| `projects/<id>.yaml` | people | One file per listed project, including what it implements |
| `updates.yaml` | people | Dated notes shown on the Updates page, in the Atom feed and in `CHANGELOG.md` |
| `ignored.yaml` | people | Candidates that were reviewed and not included, so discovery does not report them again |
| `leads.yaml` | people | Candidates that could not be checked yet (shown on the About page, never as facts) |
| `snapshot.json` | `scripts/refresh.py` | Repository and package metadata fetched from GitHub, PyPI, crates.io and npm |
| `standards-watch.yaml` | people | Standards sources checked by the scheduled refresh (ISO Open Data patterns, Ecma pages) |
| `standards-watch.json` | `scripts/watch_standards.py` | Last seen state of those sources (format described in `scripts/watch_standards.py`) |
| `link-check.json` | `scripts/check_links.py` | External links that failed in the last check, with the date each first failed |
| `index.json` | `scripts/build.py` | The whole index as one JSON document (generated, do not edit) |

Identifiers (`id`) are lowercase kebab-case and never change once published, because they are part of page URLs.
Dates are written `YYYY-MM-DD`, `YYYY-MM` or `YYYY`. Text fields marked *markdown* accept inline Markdown:
`[text](url)`, `` `code` ``, `*emphasis*` and `**strong**`.

## `metrics.yaml`

```yaml
families:
  - id: loudness
    name: Loudness
    summary: One or two sentences.            # markdown

metrics:                                      # one page per metric, in display order
  - id: loudness-zwicker
    family: loudness                          # a family id
    name: Zwicker loudness                    # short name used in tables
    title: Zwicker loudness (ISO 532-1, DIN 45631)   # page title
    aka: [ISO 532-1, ISO 532B, DIN 45631]     # other names people search for
    unit: sone, phon
    summary: >-                               # markdown, 2–5 sentences
      What the metric computes and how its editions differ.
    references: [iso-532-1975, din-45631-1991, iso-532-1-2017, iso-cd-532-1]   # chronological
    current: [iso-532-1-2017]                 # the edition(s) an up-to-date implementation should follow
    edition_notes:                            # optional: what each edition changed for this metric (markdown)
      iso-532-1-2017: Stationary and time-varying procedures.
    notes: optional markdown paragraph
    see_also: [loudness-moore-glasberg]       # metric ids
```

## `references.yaml`

A list of documents. A document can be shared by several metrics (ECMA-418-2 defines loudness, tonality,
roughness and fluctuation strength).

```yaml
- id: iso-532-1-2017
  label: ISO 532-1:2017                       # short label used in tables
  kind: standard                              # standard | technical-specification | publicly-available-specification
                                              # | amendment | draft | paper | book | thesis | regulation | method
  body: ISO                                   # ISO, IEC, DIN, Ecma, ANSI/ASA, ICAO, FAA, Nordtest, or "paper"
  title: "Acoustics — Methods for calculating loudness — Part 1: Zwicker method"
  edition: 1st edition                        # optional
  date: 2017-06-15
  status: current                             # current | superseded | withdrawn | in-development | published
  superseded_by: iso-cd-532-1                 # optional reference id
  revision: optional markdown, e.g. "Under revision: ISO/CD 532-1 registered 2024-11-01."
  url: https://www.iso.org/standard/63077.html
  doi: optional
  citation: optional full citation (papers, books, theses)
  note: optional markdown
  checked: 2026-10-06
```

`published` is the status for papers, books and theses. `in-development` is for drafts (CD, DIS, AWI …).

## `projects/<id>.yaml`

```yaml
id: metasona                                  # must equal the file name
name: MetaSona                                # the one name shown everywhere: page, lists, map, files
full_name: optional longer title, shown on the project page (e.g. AMT: Auditory Modeling Toolbox)
repository: https://github.com/huaaudio/metasona   # canonical source location (any host)
homepage: optional URL
docs: optional URL
languages: [C, Python]                        # programming languages a user calls it from, the main one first
                                              # (the home page shows the first)
kind: library                                 # library | research-code | application | plugin | reference-program (below)
                                              # | application | plugin | teaching
# core: C                                     # optional: the language the computation is written in, when it is
                                              # not the first of `languages` (Pure Data objects written in C)
based_on: sqat                                # optional: id of the listed project this one ports
language_note: optional markdown              # how the project is built and called (shown on the Languages page)
standing: newly-released                      # established | developing | newly-released (see below)
standing_note: First released in September 2026.   # required for newly-released: when it was first released;
                                              # optional for established: a sentence shown with its group
rank: 1                                       # optional: place within its group, 1 first (see below)
# super_project: 1                            # maintainer only: a super project, bold and first everywhere (below)
# highlight: widely used                      # required with super_project: the short label shown with it
license: GPL-3.0-only                         # SPDX expression, or "none" (no licence file), "proprietary-free",
                                              # or "unknown" (only when the code cannot be opened)
license_note: optional markdown
packages:                                     # optional
  - registry: pypi                            # pypi | crates | npm | julia | cran | conda-forge | file-exchange | other
    name: metasona
    url: optional URL
install: pip install metasona                 # optional one-liner
maintainers: [Jiahua Zhang]
# contributors: [Name]                        # optional: others who wrote code of their own for the project and
                                              #   also work on another listed project (from the git history; not
                                              #   one-line fixes); with maintainers, they draw "same contributor"
summary: >-                                   # markdown, 1–3 sentences: what it is, who it is for
ai_assistance: disclosed                      # disclosed | not-stated
ai_note: optional markdown (where and how the project discloses AI assistance)
paper:                                        # optional: a publication describing the software itself
  citation: ...
  doi: optional
  url: optional
notes: [optional markdown strings]            # neutral facts worth knowing
caveats: [optional markdown strings]          # known problems a user should check before relying on it
conventions: [optional markdown strings]      # choices that change its numbers for every metric (sample rate,
                                              # calibration, percentiles …); shown under "Before you compare numbers"
                                              # on the project page and on every metric page of the project. An
                                              # item that holds for some metrics only is {text: …, metrics: [ids]}
                                              # and is shown on those metric pages only
cite:                                         # optional: how the project asks to be cited (shown as "How to cite";
  doi: 10.5281/zenodo.0000000                 #   without it the page says to cite the paper, or the repository)
  cff: https://github.com/…/CITATION.cff      # URL of its CITATION.cff file
  text: optional markdown, what the README asks for
maintainer_check: optional markdown           # the list maintainer's own observation, shown as such (sparingly)
# access: restricted                          # only when the repository cannot be opened: the project is listed
# access_note: optional markdown              #   under "status unknown" with access_note and claim (what it is
# claim: markdown                             #   said to implement) instead of implements
implements:
  - metric: loudness-zwicker                  # a metric id
    reference: iso-532-1-2017                 # a reference id listed in that metric's references
    functions: [stationary_loudness, time_varying_loudness]
    scope: optional short text, e.g. "stationary and time-varying"
    partial: true                             # optional: computes only part of the metric (say what in scope); the
                                              # row is listed with a "partial" tag but not counted as an
                                              # implementation of the metric (coverage, gaps, timeline)
    status: available                         # available | unreleased | proposed
    since: optional version
    link: optional URL (folder, pull request …)
    via: optional project id, when another listed project does the computation (wrappers; a project whose
         rows all have via is listed under Others and not under the metrics)
    validation: standard-data                 # standard-data | reference-code | cross-implementation
                                              # | self-tests | not-stated
    compared_with: [mosqito]                  # optional: what it was compared with, as listed project ids (linked)
                                              # or names ("ArtemiS SUITE (HEAD acoustics)")
    derived_from: [mosqito]                   # optional: the code it was ported or adapted from, as project ids or
                                              # names ("ISO 532-1 Annex A reference program"); default: based_on;
                                              # [] when the row took no code, although the project has based_on
    derived_by_author: true                   # optional: the code it was taken from was written by someone who also
                                              # maintains this project (a contribution, a move or a translation
                                              # within the same team, not a port by someone else)
    uses: [zwickerloudness-jl]                # optional: listed projects the row needs at run time, for example for
                                              # their results, although it computes the metric itself (else: via)
    validation_details: [markdown strings]    # optional: what was checked, against what, tolerance and result
    validation_scope: optional few words      # how far the check goes or how it came out, shown next to the
                                              # evidence tag (at most 60 characters): "calibration signal only",
                                              # "outcome not stated", "in v1.3, test signal 10 is off by 18.14 %"
    conventions: [markdown strings]           # optional: choices of this row that change its numbers
    note: optional markdown (other facts; validation goes in validation_details)
manual:                                       # optional fallback when the refresher cannot reach the host
  last_commit: 2026-09-25
  latest_release: {version: 0.2.2, date: 2026-09-25}
  archived: false
sources: [URLs the facts above were taken from]
checked: 2026-10-06                           # last time a person checked this entry
```

### Standing and group of a project

| Standing | Meaning |
|---|---|
| `established` | Described in a publication, used by others, or written by the authors of the model, with more than a year of history |
| `newly-released` | First released less than about a year ago, and not yet seen to be widely used in the community |
| `developing` | Public for more than a year, but without a publication or documented use by others: research, teaching or personal code |

Three more groups follow from the data rather than from the project file:

- **legacy**: archived, or no commit for `legacy_after_days` (three years, see `site.yaml`). Super projects and
  reference programs (`kind: reference-program`) are never legacy.
- **others**: every implementation row has `via`, so the tool does not compute the metrics itself.
- **status unknown**: the project has `access` (its repository cannot be opened), so it lists a `claim` and no
  implementations; it is not shown under the metrics.

Every project is in exactly one group, decided in this order: status unknown, others, legacy, then its standing.
Every list follows the order of the groups, always established, newly released, developing, legacy, then
others and status unknown, so a project that is new, little used, no longer maintained or unverified is never
the first suggestion. Review the standing of `newly-released` projects once they are a year old: they become
`established` or `developing`.

**Super projects.** `super_project: n` is the maintainer's display setting, at present for SQAT (1), MoSQITo (2)
and sottek-hearing-model (3). It is not published as such: it makes the project's name bold wherever it appears and
puts the project first in its group in every list, in the order of `n`. Its `highlight` is the short label shown with
it in the README, in llms.txt, in `index.json` and on its page: "widely used" for SQAT and MoSQITo, "a very good
implementation" for sottek-hearing-model. A super project must be established, so it heads every list, and it is
never legacy. Only the maintainer sets it. An established project that is not in bold can still say why it matters
in its `standing_note`, shown with its group on its page (the Auditory Modeling Toolbox and the ITA-Toolbox: widely
used toolboxes that also include some psychoacoustic functions). Within a group, other projects with a `rank` come next, in rank order; MetaSona has
rank 1 among the newly released projects.

### Kind of a project

What a project is, for someone who wants to use it. Each project page shows the kind with its meaning, and the
About page lists them all.

| Kind | Meaning |
|---|---|
| `library` (shown as Library/Toolbox) | Functions to call from your own code: a Python package, a MATLAB toolbox, or a C, C++, C#, Rust or Julia library |
| `research-code` | Code published with a study, a thesis or a student project, to run or adapt; not packaged as a library |
| `application` | A program to run, with a graphical or command-line interface; no programming needed |
| `plugin` | Runs inside other software: a plug-in for an audio workstation, or a Pure Data external |
| `reference-program` | Code published with a standard or by the authors of the model, as the reference for it |

### Status of an implementation

| Value | Meaning |
|---|---|
| `available` | In the latest release, or on the default branch of a project that does not make releases |
| `unreleased` | Merged on the default branch but newer than the latest release |
| `proposed` | Open pull request or separate branch, not merged; tagged `PR` on the pages |

### Validation evidence (as stated by the project)

| Value | Meaning |
|---|---|
| `standard-data` | Compared with test signals or values published in the standard or the model paper |
| `reference-code` | Compared with the reference program or the model authors' own code |
| `cross-implementation` | Compared with another implementation, named in `compared_with` where the project says which |
| `self-tests` | Tests exist, but without external reference data |
| `not-stated` | The project does not say how it was validated |

These record what the project itself claims. The list does not run the code. `compared_with` names what an
implementation was compared with: the tag then reads "compared with MoSQITo" (cross-implementation), "reference
code: SQAT" (reference-code) or adds "also compared with …" to another kind of evidence. `validation_details` are
shown, one bullet each, under *How it was validated* on the project and metric pages. Agreement with another
implementation shows that both compute the same values, not that either follows the standard.

A comparison with related code is not an independent check, and is marked so: with the code the row was ported
from, following `derived_from` (or the project's `based_on`) through further ports of the same metric, it reads
"(its source)"; with a port of the row's own code, "(a port of it)"; with another port of the same code, "(also
ported from …)". When every comparison of a row is of this kind, its evidence tag is grey. In `index.json`, such
rows carry `comparison_relations` (`source`, `port` or `shared:<project id>`).

### The project map

`projects/map.html` draws every relation between projects that the rows record, as a picture made by Graphviz when
the site is built, and lists the same relations in words; the Projects page opens with the same picture, and each
metric page draws the lines of its own rows only. Arrows point from the source to the project that uses it, and a
check points from the project to the one it checked its results against (placed like a source, on the left):

| Line | From the rows |
|---|---|
| code taken from another project | `derived_from` (or the project's `based_on`); a grey box for a published program |
| the author's own code | the same, when every row of the pair has `derived_by_author` |
| used at run time | `via` (the source does the computation) and `uses` (the row needs the source) |
| results checked against | `compared_with`, without comparisons with related code and pairs already joined |
| same contributor | a name in `maintainers` or `contributors` of both projects; no arrow; not drawn beside a line of the author's own code, which says the same |

A test fails when two projects with a person in common share code and no row of the pair has `derived_by_author`,
so that this is checked on the rows rather than guessed from the names.

## `snapshot.json` (machine-written)

```json
{
  "generated": "2026-10-06T06:00:00Z",
  "projects": {
    "metasona": {
      "fetched": "2026-10-06T06:00:00Z",
      "github": {
        "full_name": "huaaudio/metasona", "stars": 3, "forks": 0, "archived": false,
        "default_branch": "main", "pushed_at": "2026-09-25T15:50:48Z", "last_commit": "2026-09-25",
        "license": "GPL-3.0", "description": "…", "topics": [], "open_issues": 0,
        "latest_release": {"tag": "v0.2.2", "date": "2026-09-25", "url": "…"}
      },
      "packages": {
        "pypi:metasona": {"version": "0.2.2", "date": "2026-09-25", "url": "https://pypi.org/project/metasona/",
                          "prerelease": null}
      },
      "errors": []
    }
  }
}
```

Fields that cannot be fetched are `null`. When a fetch fails, the refresher keeps the previous value and
records the error. The build prefers snapshot values and falls back to `manual` in the project file.
A project counts as **inactive** when its last commit on the default branch is older than
`inactive_after_days` (see `site.yaml`), and **archived** when the host says so.

## `updates.yaml`

```yaml
- date: 2026-10-06
  title: First public version
  body: |                                     # markdown: paragraphs and "- " bullet lists
    Text.
```

## `ignored.yaml`

```yaml
- url: https://github.com/example/repo
  reason: Implements LUFS only (out of scope).
  checked: 2026-10-06
```

## `leads.yaml`

```yaml
- name: Example toolbox
  url: https://gitlab.example.org/group/toolbox
  languages: [MATLAB]
  claim: What the candidate is said to implement (markdown).
  why: Why it has not been checked yet (markdown).
  checked: 2026-10-06
```
