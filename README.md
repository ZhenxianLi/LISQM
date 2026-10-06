# Psychoacoustic Metrics Index

An index of open-source implementations of psychoacoustic metrics (loudness, sharpness, roughness,
fluctuation strength, tonality, impulsiveness and psychoacoustic annoyance), organised by the standard edition
or model paper each implementation follows. Any programming language. Refreshed every week.

**Website:** <https://zhenxianli.github.io/psychoacoustic-metrics-index/>
**Data:** [`data/index.json`](data/index.json) · [`llms.txt`](llms.txt) · [`llms-full.txt`](llms-full.txt) · [schema](data/SCHEMA.md)
**中文说明：** [README.zh-CN.md](README.zh-CN.md)

[![Site](https://github.com/ZhenxianLi/psychoacoustic-metrics-index/actions/workflows/pages.yml/badge.svg)](https://github.com/ZhenxianLi/psychoacoustic-metrics-index/actions/workflows/pages.yml)
[![Weekly refresh](https://github.com/ZhenxianLi/psychoacoustic-metrics-index/actions/workflows/refresh.yml/badge.svg)](https://github.com/ZhenxianLi/psychoacoustic-metrics-index/actions/workflows/refresh.yml)
[![Licence: MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](LICENSE)

<!-- BEGIN GENERATED: stats -->
Data as of 2026-10-06: 22 methods, 1 project, languages: C, Python.
<!-- END GENERATED: stats -->

## Why this index exists

The definitions of psychoacoustic metrics keep changing. ECMA-418-2 has had four editions since 2020, and all
three parts of ISO 532 are being revised. Two tools that both say they implement "ECMA-418-2 roughness" can
follow different editions and give different numbers, and some projects carry important fixes on their main
branch long before the next release.

For every open-source implementation it knows about, this index records:

- which **standard edition or model paper** it follows, and which functions to call;
- how the project says it was **validated** (standard test data, reference code, another tool, own tests, or
  nothing stated);
- the **licence**, the latest **release**, the last **commit**, and whether the project discloses **AI
  assistance**;
- the **source** of every fact (README, documentation, release notes, package metadata).

The index contains no metric code. It records what each project claims and does not run the code; listing a
project is not an endorsement.

## Overview

The current edition of each method and the projects that implement it, by language. Each method has its own
page on the website with the full edition history, function names and validation notes.

<!-- BEGIN GENERATED: overview -->
| Quantity | Method | Current edition | Open-source implementations (by language) |
|---|---|---|---|
| Loudness | [Zwicker loudness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-zwicker.html) | ISO 532-1:2017 | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C) |
| Loudness | [Moore–Glasberg loudness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg.html) | ISO 532-2:2017 | none found |
| Loudness | [Time-varying loudness (Moore–Glasberg–Schlittenlacher)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg-time-varying.html) | ISO 532-3:2023 | none found |
| Loudness | [Sottek Hearing Model loudness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-ecma-418-2.html) | ECMA-418-2:2025 (4th ed.) | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C) |
| Sharpness | [Sharpness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/sharpness.html) | DIN 45692:2009 | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C) |
| Roughness | [Roughness (Daniel & Weber)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-daniel-weber.html) | Daniel & Weber (1997) | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C) |
| Roughness | [Sottek Hearing Model roughness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-ecma-418-2.html) | ECMA-418-2:2025 (4th ed.) | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C) |
| Roughness | [Roughness (DIN 38455)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-din-38455.html) | DIN 38455:2024 | none found |
| Fluctuation strength | [Fluctuation strength (Osses et al.)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-osses.html) | Osses et al. (2016) | none found |
| Fluctuation strength | [Sottek Hearing Model fluctuation strength](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-ecma-418-2.html) | ECMA-418-2:2025 (4th ed.) | none found |
| Tonality | [Tonality (Aures)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-aures.html) | Aures (1985b) | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C) |
| Tonality | [Sottek Hearing Model tonality](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-ecma-418-2.html) | ECMA-418-2:2025 (4th ed.) | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C) |
| Tonality | [Tone-to-noise ratio and prominence ratio](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tone-to-noise-prominence-ratio.html) | ECMA-418-1:2024 (3rd ed.) | none found |
| Tonality | [Tonal components (DIN 45681)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-din-45681.html) | DIN 45681:2005 | none found |
| Tonality | [Audibility of tones in noise (ISO/TS 20065)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-20065.html) | ISO/TS 20065:2022 | none found |
| Tonality | [Tonal audibility (ISO 1996-2)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-1996-2.html) | ISO 1996-2:2017 | none found |
| Tonality | [Tonal audibility of wind turbines (IEC 61400-11)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iec-61400-11.html) | IEC 61400-11:2012+AMD1:2018 | none found |
| Impulsiveness | [Impulse prominence](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/impulsiveness.html) | ISO/PAS 1996-3:2022 | none found |
| Psychoacoustic annoyance | [Psychoacoustic annoyance](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/psychoacoustic-annoyance.html) | Widmann (1992), Zwicker & Fastl (1999), More (2010), and Di et al. (2016) | none found |
| Related quantities | [Equal-loudness contours](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/equal-loudness-contours.html) | ISO 226:2023 | none found |
| Related quantities | [Perceived noise level and EPNL](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/epnl.html) | ICAO Annex 16, Vol. I and 14 CFR Part 36 | none found |
| Related quantities | [Aural detectability](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/aural-detectability.html) | Fidell et al. (1974) | none found |
<!-- END GENERATED: overview -->

### Gaps

No available open-source implementation of the current edition has been found for:

<!-- BEGIN GENERATED: gaps -->
- [Moore–Glasberg loudness of stationary sounds (ISO 532-2, ANSI S3.4)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg.html)
- [Time-varying loudness, Moore–Glasberg–Schlittenlacher (ISO 532-3)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg-time-varying.html)
- [Roughness, DIN 38455](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-din-38455.html)
- [Fluctuation strength, Osses et al. model and Fastl & Zwicker formula](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-osses.html)
- [Fluctuation strength from the Sottek Hearing Model (ECMA-418-2)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-ecma-418-2.html)
- [Tone-to-noise ratio and prominence ratio (ECMA-418-1)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tone-to-noise-prominence-ratio.html)
- [Tonal components and tone adjustment (DIN 45681)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-din-45681.html)
- [Audibility of tones in noise (ISO/TS 20065)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-20065.html)
- [Tonal audibility in environmental noise (ISO 1996-2)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-1996-2.html)
- [Tonal audibility of wind turbine noise (IEC 61400-11)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iec-61400-11.html)
- [Prominence of impulsive sounds (ISO/PAS 1996-3, NT ACOU 112)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/impulsiveness.html)
- [Psychoacoustic annoyance (Widmann, Zwicker & Fastl, More, Di et al.)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/psychoacoustic-annoyance.html)
- [Equal-loudness-level contours (ISO 226)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/equal-loudness-contours.html)
- [Perceived noise level, PNLT and EPNL (ICAO Annex 16, 14 CFR Part 36)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/epnl.html)
- [Aural detectability of sounds in background noise](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/aural-detectability.html)
<!-- END GENERATED: gaps -->

### Coverage by language

Which languages have an implementation of each method.

<!-- BEGIN GENERATED: coverage -->
| Method | Python | MATLAB/Octave | C/C++ | Rust | Julia | Other |
|---|---|---|---|---|---|---|
| [Zwicker loudness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-zwicker.html) | ● | — | ● | — | — | — |
| [Moore–Glasberg loudness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg.html) | — | — | — | — | — | — |
| [Time-varying loudness (Moore–Glasberg–Schlittenlacher)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg-time-varying.html) | — | — | — | — | — | — |
| [Sottek Hearing Model loudness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-ecma-418-2.html) | ● | — | ● | — | — | — |
| [Sharpness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/sharpness.html) | ● | — | ● | — | — | — |
| [Roughness (Daniel & Weber)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-daniel-weber.html) | ● | — | ● | — | — | — |
| [Sottek Hearing Model roughness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-ecma-418-2.html) | ● | — | ● | — | — | — |
| [Roughness (DIN 38455)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-din-38455.html) | — | — | — | — | — | — |
| [Fluctuation strength (Osses et al.)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-osses.html) | — | — | — | — | — | — |
| [Sottek Hearing Model fluctuation strength](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-ecma-418-2.html) | — | — | — | — | — | — |
| [Tonality (Aures)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-aures.html) | ● | — | ● | — | — | — |
| [Sottek Hearing Model tonality](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-ecma-418-2.html) | ● | — | ● | — | — | — |
| [Tone-to-noise ratio and prominence ratio](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tone-to-noise-prominence-ratio.html) | — | — | — | — | — | — |
| [Tonal components (DIN 45681)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-din-45681.html) | — | — | — | — | — | — |
| [Audibility of tones in noise (ISO/TS 20065)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-20065.html) | — | — | — | — | — | — |
| [Tonal audibility (ISO 1996-2)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-1996-2.html) | — | — | — | — | — | — |
| [Tonal audibility of wind turbines (IEC 61400-11)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iec-61400-11.html) | — | — | — | — | — | — |
| [Impulse prominence](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/impulsiveness.html) | — | — | — | — | — | — |
| [Psychoacoustic annoyance](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/psychoacoustic-annoyance.html) | — | — | — | — | — | — |
| [Equal-loudness contours](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/equal-loudness-contours.html) | — | — | — | — | — | — |
| [Perceived noise level and EPNL](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/epnl.html) | — | — | — | — | — | — |
| [Aural detectability](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/aural-detectability.html) | — | — | — | — | — | — |

● an available implementation of the current edition; ○ only unreleased, proposed or older-edition implementations; — none found. Bindings count: a C library with a Python interface counts for Python.
<!-- END GENERATED: coverage -->

## Projects

<!-- BEGIN GENERATED: projects -->
| Project | Language | Licence | Latest release | Last commit | Activity |
|---|---|---|---|---|---|
| [MetaSona](https://github.com/huaaudio/metasona) | Python, C | GPL-3.0-only AND Apache-2.0 AND BSD-3-Clause AND MIT | 0.2.2 (2026-09) | 2026-09-25 | active |
<!-- END GENERATED: projects -->

"Activity" is computed from the last commit on the default branch (inactive after 365 days without a commit).

## How it is maintained

- **Data.** Everything lives in [`data/`](data/): methods in `metrics.yaml`, standard editions and model papers
  in `references.yaml`, one file per project in `projects/`. The format is described in
  [`data/SCHEMA.md`](data/SCHEMA.md).
- **Build.** [`scripts/build.py`](scripts/build.py) validates the data and generates the website, the tables in
  this README, `llms.txt`, `llms-full.txt` and `data/index.json`.
- **Weekly refresh.** A GitHub Action updates repository and package metadata (last commit, releases, PyPI and
  crates.io versions), searches GitHub and package registries for new candidate projects, and checks ISO and
  Ecma for new editions. Its findings are collected in one issue labelled `weekly-review`, which a person
  reviews before anything is added or changed.

## Using the data

- [`data/index.json`](data/index.json) contains the whole index (methods, editions, projects,
  implementations) in one JSON document; the same file is served at
  <https://zhenxianli.github.io/psychoacoustic-metrics-index/index.json>.
- [`llms.txt`](llms.txt) and [`llms-full.txt`](llms-full.txt) are plain-text summaries for language models and
  other tools. Every page on the website also has a Markdown version (replace `.html` with `.md`).
- An Atom feed of updates is at <https://zhenxianli.github.io/psychoacoustic-metrics-index/feed.xml>.

To build the website locally:

```sh
pip install -r requirements.txt
python scripts/build.py          # writes site/; open site/index.html
python scripts/build.py --check  # validate the data only
```

## Contributing

New projects, corrections and news about standards are welcome. Open an issue with one of the
[templates](https://github.com/ZhenxianLi/psychoacoustic-metrics-index/issues/new/choose), or send a pull
request that adds or edits a file in `data/projects/`. See [CONTRIBUTING.md](CONTRIBUTING.md). Project authors
are encouraged to check their own entry.

## Citing

If the index helped your work, please cite it using [CITATION.cff](CITATION.cff) (GitHub shows a "Cite this
repository" button), together with the date you accessed it, and cite the implementations you actually used.

## Licence

[MIT](LICENSE), for the data, the text and the code. The indexed projects have their own licences, listed in
the tables above.
