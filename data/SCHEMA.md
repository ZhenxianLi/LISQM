# Data model

Everything on the website, in the README tables and in `index.json` is generated from the files in this
directory. Edit these files, never the generated output.

| File | Edited by | Contents |
|---|---|---|
| `site.yaml` | people | Short name (PsyMI), full name, subtitle, base URL, maintainer, thresholds |
| `metrics.yaml` | people | Metric families and methods (one page per method) |
| `references.yaml` | people | Standard editions, model papers and books that methods are defined by |
| `projects/<id>.yaml` | people | One file per indexed project, including what it implements |
| `updates.yaml` | people | Dated notes shown on the Updates page, in the Atom feed and in `CHANGELOG.md` |
| `ignored.yaml` | people | Candidates that were reviewed and not included, so discovery does not report them again |
| `leads.yaml` | people | Candidates that could not be checked yet (shown on the About page, never as facts) |
| `snapshot.json` | `scripts/refresh.py` | Repository and package metadata fetched from GitHub, PyPI, crates.io and npm |
| `standards-watch.yaml` | people | Standards sources checked every month (ISO Open Data patterns, Ecma pages) |
| `standards-watch.json` | `scripts/watch_standards.py` | Last seen state of those sources (format described in `scripts/watch_standards.py`) |
| `index.json` | `scripts/build.py` | The whole index as one JSON document (generated, do not edit) |

Identifiers (`id`) are lowercase kebab-case and never change once published, because they are part of page URLs.
Dates are written `YYYY-MM-DD`, `YYYY-MM` or `YYYY`. Text fields marked *markdown* accept inline Markdown:
`[text](url)`, `` `code` ``, `*emphasis*` and `**strong**`.

## `metrics.yaml`

```yaml
families:
  - id: loudness
    name: Loudness
    name_zh: 响度                              # optional, used in README.zh-CN.md
    summary: One or two sentences.            # markdown

methods:                                      # one page per method, in display order
  - id: loudness-zwicker
    family: loudness                          # a family id
    name: Zwicker loudness                    # short name used in tables
    name_zh: Zwicker 响度（ISO 532-1）          # optional, used in README.zh-CN.md
    title: Zwicker loudness (ISO 532-1, DIN 45631)   # page title
    aka: [ISO 532-1, ISO 532B, DIN 45631]     # other names people search for
    unit: sone, phon
    summary: >-                               # markdown, 2–5 sentences
      What the method computes and how its editions differ.
    references: [iso-532-1975, din-45631-1991, iso-532-1-2017, iso-cd-532-1]   # chronological
    current: [iso-532-1-2017]                 # the edition(s) an up-to-date implementation should follow
    edition_notes:                            # optional: what each edition changed for this method (markdown)
      iso-532-1-2017: Stationary and time-varying procedures.
    notes: optional markdown paragraph
    see_also: [loudness-moore-glasberg]       # method ids
```

## `references.yaml`

A list of documents. A document can be shared by several methods (ECMA-418-2 defines loudness, tonality,
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
name: MetaSona
short_name: optional shorter name for dense views such as the home-page timeline
repository: https://github.com/huaaudio/metasona   # canonical source location (any host)
homepage: optional URL
docs: optional URL
languages: [Python, C]                        # programming languages a user calls it from
kind: library                                 # library | toolbox | research-code | reference-program | wrapper
                                              # | application | plugin | teaching
core: C                                       # optional: the language the computation is written in, when it is
                                              # not the first of `languages`
based_on: sqat                                # optional: id of the indexed project this one ports
language_note: optional markdown              # how the project is built and called (shown on the Languages page)
standing: newly-released                      # established | developing | newly-released (see below)
standing_note: First released in September 2026.   # required for newly-released: when it was first released
rank: 1                                       # optional: place within its group, 1 first (see below)
license: GPL-3.0-only                         # SPDX expression, or "none" (no licence file) or "proprietary-free"
license_note: optional markdown
packages:                                     # optional
  - registry: pypi                            # pypi | crates | npm | julia | cran | conda-forge | file-exchange | other
    name: metasona
    url: optional URL
install: pip install metasona                 # optional one-liner
maintainers: [Jiahua Zhang]
summary: >-                                   # markdown, 1–3 sentences: what it is, who it is for
ai_assistance: disclosed                      # disclosed | not-stated
ai_note: optional markdown (where and how the project discloses AI assistance)
paper:                                        # optional: a publication describing the software itself
  citation: ...
  doi: optional
  url: optional
notes: [optional markdown strings]            # neutral facts worth knowing
caveats: [optional markdown strings]          # known problems a user should check before relying on it
implements:
  - method: loudness-zwicker                  # a method id
    reference: iso-532-1-2017                 # a reference id listed in that method's references
    functions: [stationary_loudness, time_varying_loudness]
    scope: optional short text, e.g. "stationary and time-varying"
    status: available                         # available | unreleased | proposed
    since: optional version
    link: optional URL (folder, pull request …)
    via: optional project id, when another indexed project does the computation (wrappers; a project whose
         rows all have via is listed under Others and not under the metrics)
    validation: standard-data                 # standard-data | reference-code | cross-implementation
                                              # | self-tests | not-stated
    note: optional markdown
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
| `newly-released` | First released less than about a year ago, and not yet widely used in the community |
| `developing` | Public for more than a year, but without a publication or documented use by others: research, teaching or personal code |

Two more groups follow from the data rather than from the project file:

- **legacy**: archived, or no commit for `legacy_after_days` (three years, see `site.yaml`). The most widely used
  projects and reference programs (`kind: reference-program`) are never legacy.
- **others**: every implementation row has `via`, so the tool does not compute the metrics itself.

Every project is in exactly one group, decided in this order: others, legacy, then its standing. All lists follow
the order established, newly released, developing, legacy, others, so a project that is new, little used or no
longer maintained is never the first suggestion. Review the standing of `newly-released` projects once they are a
year old: they become `established` or `developing`.

Within a group, projects with a `rank` come first, in rank order. Established projects with a rank are the most
widely used ones, at present SQAT (1), the Auditory Modeling Toolbox (2) and MoSQITo (3): they are shown in bold
and never listed as legacy. MetaSona has rank 1 among the newly released projects.

### Status of an implementation

| Value | Meaning |
|---|---|
| `available` | In the latest release, or on the default branch of a project that does not make releases |
| `unreleased` | Merged on the default branch but newer than the latest release |
| `proposed` | Open pull request or separate branch, not merged |

### Validation evidence (as stated by the project)

| Value | Meaning |
|---|---|
| `standard-data` | Compared with test signals or values published in the standard or the model paper |
| `reference-code` | Compared with the reference program or the model authors' own code |
| `cross-implementation` | Compared with another independent implementation |
| `self-tests` | Tests exist, but without external reference data |
| `not-stated` | The project does not say how it was validated |

These record what the project itself claims. The index does not run the code.

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
