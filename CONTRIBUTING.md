# Contributing

Thank you for helping to keep the Psychoacoustic Metrics Index complete and accurate. The index lists
open-source implementations of psychoacoustic metrics, organised by the standard edition or model paper each
one follows. The repository holds data and a static-site generator, not metric code: the website, the README
tables and `data/index.json` are all generated from the YAML files in [`data/`](data/), which are described in
[`data/SCHEMA.md`](data/SCHEMA.md).

Everyone taking part is expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

- [Ways to contribute](#ways-to-contribute)
- [What the index includes](#what-the-index-includes)
- [Proposing a project](#proposing-a-project)
- [Correcting an entry](#correcting-an-entry)
- [Reporting a new standard edition](#reporting-a-new-standard-edition)
- [Writing rules](#writing-rules)
- [Local checks](#local-checks)
- [The weekly automation](#the-weekly-automation)
- [Review process](#review-process)

## Ways to contribute

| You want to | Open an issue | Or send a pull request that |
|---|---|---|
| Add a project | [Add a project][issue-add] | adds `data/projects/<id>.yaml` |
| Fix a wrong or outdated fact | [Correction][issue-fix] | edits the YAML file concerned |
| Report a new or revised standard | [Standard edition][issue-std] | edits `data/references.yaml` and `data/metrics.yaml` |
| Anything else (website, wording, ideas) | [Blank issue][issue-blank] | changes what is needed |

An issue is enough: you do not have to write YAML. Pull requests are welcome if you prefer to write the
entry yourself. Security problems go through private reporting instead; see [SECURITY.md](SECURITY.md).

A good place to start is [`data/leads.yaml`](data/leads.yaml), shown on the website's About page as "Leads not
yet verified": candidates that could not be checked yet, often because their host was unreachable. If you can
read one of them, propose it as a project or say why it does not qualify.

## What the index includes

A project is included when all three of these hold:

1. **The source code is public**, on any host. The code that computes the metric must be readable; a binary,
   a web service or a wrapper around a closed library is not enough. A repository without a licence file can
   still be listed, with `license: none`.
2. **It states which model or standard it implements**, and which edition where there is more than one.
3. **It computes at least one in-scope quantity.** These are the methods tracked at present; others can be
   added (see [Adding an edition or a method](#adding-an-edition-or-a-method)).

| Family | Methods and the documents that define them |
|---|---|
| Loudness | Zwicker (ISO 532-1, DIN 45631); Moore–Glasberg (ISO 532-2, ANSI S3.4); Moore–Glasberg–Schlittenlacher time-varying loudness (ISO 532-3); Sottek Hearing Model (ECMA-418-2) |
| Sharpness | DIN 45692; Aures; von Bismarck |
| Roughness | Daniel and Weber; Sottek Hearing Model (ECMA-418-2); DIN 38455 |
| Fluctuation strength | Osses et al.; Fastl and Zwicker; Sottek Hearing Model (ECMA-418-2) |
| Tonality | Aures/Terhardt; Sottek Hearing Model (ECMA-418-2); tone-to-noise and prominence ratio (ECMA-418-1); DIN 45681; ISO/TS 20065; ISO 1996-2; IEC 61400-11 |
| Impulsiveness | ISO/PAS 1996-3; NT ACOU 112 |
| Psychoacoustic annoyance | Widmann; Zwicker and Fastl; More; Di et al. |
| Related quantities | Equal-loudness contours (ISO 226); perceived noise level and EPNL (ICAO Annex 16, 14 CFR Part 36); aural detectability |

**Out of scope:**

- broadcast and programme loudness: LUFS, ITU-R BS.1770, EBU R128;
- speech intelligibility;
- audio and speech codec quality metrics such as PEAQ, PESQ and ViSQOL;
- software for running psychophysics or listening experiments;
- music sensory-dissonance models (Plomp–Levelt, Sethares, Vassilakis), which estimate the roughness of musical
  intervals rather than the sound-quality metric;
- feature extractors whose "loudness" or "sharpness" descriptors do not follow a named psychoacoustic model
  (for example Meyda, LibXtract, Yaafe);
- closed-source tools, including free-of-charge tools whose metric code is not published.

Inclusion is not an endorsement and does not depend on popularity, activity or quality. Inactive and archived
projects stay in the index and are marked as such. Borderline cases are decided case by case; candidates
that were reviewed and not included are recorded in `data/ignored.yaml` with the reason.

## Proposing a project

**By issue.** Fill in the [Add a project][issue-add] form, with links for what you state. The maintainer
writes the entry.

**By pull request.**

1. Copy [`data/projects/metasona.yaml`](data/projects/metasona.yaml), a complete example, to
   `data/projects/<id>.yaml`. The `id` is lowercase kebab-case, usually the project name, and equals the file
   name. It never changes once published, because it is part of page URLs.
2. Fill in the required fields: `name`, `repository`, `languages`, `kind`, `standing`, `license`,
   `summary`, `ai_assistance`, `implements`, `sources` and `checked`. `standing` is `established`,
   `developing` or `new`; a project first released less than about a year ago is `new` and needs a
   `standing_note` saying when it was first released. Lists put new projects last, so a project that has not
   yet been used much is never the first suggestion. The optional fields are described in
   [`data/SCHEMA.md`](data/SCHEMA.md). Leave out what you do not know rather than guessing.
3. Add one `implements` entry per method and edition. A project that implements two editions of the same
   method gets two entries.

   ```yaml
   implements:
     - method: loudness-zwicker          # a method id from data/metrics.yaml
       reference: iso-532-1-2017         # a reference id listed under that method
       functions: [stationary_loudness, time_varying_loudness]
       status: available                 # available | unreleased | proposed
       validation: standard-data         # as the project states it; not-stated if it says nothing
   ```

4. Do not add stars, versions or commit dates. The weekly refresh fetches them from GitHub, PyPI, crates.io
   and npm. For a repository hosted elsewhere, fill in `manual` (last commit, latest release, archived).
5. Run the [local checks](#local-checks) and open the pull request. One project per pull request is preferred.

### Adding an edition or a method

If a project follows an edition or a paper that is not in [`data/references.yaml`](data/references.yaml)
yet, add it there with `id`, `label`, `kind`, `body`, `title`, `date`, `status`, a `url` or `doi`, and
`checked`. Then add its id to the method's `references` in [`data/metrics.yaml`](data/metrics.yaml), in
chronological order. A new method needs its own entry in `metrics.yaml` with a short, neutral summary; please
explain in the pull request why it belongs in the index.

## Correcting an entry

Open a [Correction][issue-fix] issue with the page or entry, what is wrong, the correct information and a
source. Or edit the YAML file in a pull request: change the fact, add its source to `sources` (or link it in
the text), and set `checked` to the date you checked the entry.

Authors and maintainers of listed projects are welcome to check and correct their own entries; please mention
your role in the issue or pull request.

## Reporting a new standard edition

Open a [Standard edition][issue-std] issue for a new standard, a new edition, an amendment, a draft stage or a
withdrawal. To make the change yourself in a pull request:

1. Add the document to `data/references.yaml`. A draft has `kind: draft` and `status: in-development`.
2. On the edition it will replace, set `superseded_by` to the new id. While the new document is a draft, keep
   `status: current` there and describe the stage in `revision`; once it is published, set
   `status: superseded` (or `withdrawn`).
3. In `data/metrics.yaml`, add the new id to the method's `references` (in chronological order) and, once it
   is published, put it in `current` in place of the old edition.
4. Do not change project entries: a project moves to the new edition only when the project itself says so.

To have the weekly job watch a standard that it does not cover yet, add a pattern or a page to
[`data/standards-watch.yaml`](data/standards-watch.yaml).

## Writing rules

- **Neutral and factual.** Record what the project or the standards body states; do not rate, rank or
  recommend. Write "The README calls the current version experimental", not "unstable". Leave out words such
  as *fast*, *accurate* or *robust* unless you attribute them ("the README reports a speed-up over …").
- **Sourced.** Every fact needs a source URL, listed in `sources` or linked in the text. Prefer the project's
  own README, documentation, release notes, changelog or package page, and the standards body's catalogue
  page. When a statement may change, link to a release, a tag or a commit.
- **Claims, not tests.** `validation` records the evidence the project describes: `standard-data`,
  `reference-code`, `cross-implementation`, `self-tests` or `not-stated`. The index does not run the code.
- **AI assistance** is `disclosed` only when the project itself says so; `ai_note` says where. Otherwise it
  is `not-stated`.
- **Caveats** are limitations the project states or documents, such as a known deviation or an open issue,
  with a link.
- **Update `checked`** (`YYYY-MM-DD`) whenever you compare an entry with its sources, even if nothing changed.
- **Plain English**, short sentences, inline Markdown only (links, `code`, *emphasis*). Write designations as
  the publisher does, for example ISO 532-1:2017 or DIN 45692:2009.

## Local checks

You need Python 3 (CI uses 3.12) and the packages in `requirements.txt`.

```sh
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/build.py --check        # validate data/ only; lists any problems and exits with status 1
python scripts/build.py                # validate, then build the website into site/
python -m unittest discover -s tests   # only needed when you change the scripts
```

Open `site/index.html` in a browser to look at the result; the pages use relative links, so they work from the
local folder. The full build also rewrites the generated files kept in the repository: the tables in
`README.md` and `README.zh-CN.md` (between `GENERATED` markers), `CHANGELOG.md`, `llms.txt`, `llms-full.txt`
and `data/index.json`. Never edit these by hand, and there is no need to commit them: after every merge into
`main` the Pages workflow regenerates and commits them, and leaving them out avoids conflicts between pull
requests.

The CI workflow runs the same checks (validation, unit tests and a full build) on every pull request.

## The weekly automation

The Weekly refresh workflow ([`.github/workflows/refresh.yml`](.github/workflows/refresh.yml)) runs every
Monday at 05:17 UTC and can also be started by hand:

1. **Refresh.** [`scripts/refresh.py`](scripts/refresh.py) fetches repository metadata from GitHub (stars,
   last commit on the default branch, latest release, archived flag, licence) and the latest versions from
   PyPI, crates.io and npm into `data/snapshot.json`. A failed fetch keeps the previous value and records the
   error. The snapshot and the regenerated files are committed to `main`.
2. **Discovery.** [`scripts/discover.py`](scripts/discover.py) searches GitHub, crates.io and npm for
   candidates that are neither indexed nor in `data/ignored.yaml`, leaving out forks and projects without
   activity in the last three years. PyPI cannot be searched and other hosts are not covered, so suggestions
   for projects published elsewhere are particularly useful.
3. **Standards watch.** [`scripts/watch_standards.py`](scripts/watch_standards.py) checks the sources in
   `data/standards-watch.yaml` (ISO's open data on its deliverables and the Ecma standard pages) for new
   editions and stage changes, and commits the last seen state to `data/standards-watch.json`.
4. **Weekly review.** The three reports go into one open issue labelled `weekly-review`, which is updated with
   each week's findings (or opened if none is open); nothing is posted when there is nothing to review. A
   person works through the issue, adding or rejecting candidates, recording new editions, confirming status
   changes after releases (for example `unreleased` to `available`) and updating `checked` dates, and closes
   it when done.
5. **Publish.** The website is rebuilt and deployed to GitHub Pages.

The automation writes only machine-written files (`data/snapshot.json`, `data/standards-watch.json`) and
generated output. Everything that describes a project, a method or an edition is changed by a person.

## Review process

- The maintainer reviews issues and pull requests, usually together with the weekly review.
- For a new project, the review checks the inclusion criteria, compares each fact with its source and reads
  the wording. Expect questions or small edits; the maintainer may also finish an entry started in an issue.
- The CI checks must pass before a pull request is merged.
- A candidate that is not included is added to `data/ignored.yaml` with the reason, so discovery does not
  report it again. It can be reconsidered when the project changes, for example when it states which edition
  it follows. A candidate that cannot be checked yet goes to `data/leads.yaml`, which the website shows as
  unverified leads, never as facts.
- Disagreements about an entry are settled with sources: the index records what projects and standards bodies
  state.

By contributing, you agree that your contribution is published under the [MIT License](LICENSE) of this
repository.

[issue-add]: https://github.com/ZhenxianLi/psychoacoustic-metrics-index/issues/new?template=add-project.yml
[issue-fix]: https://github.com/ZhenxianLi/psychoacoustic-metrics-index/issues/new?template=correction.yml
[issue-std]: https://github.com/ZhenxianLi/psychoacoustic-metrics-index/issues/new?template=standard-edition.yml
[issue-blank]: https://github.com/ZhenxianLi/psychoacoustic-metrics-index/issues/new
