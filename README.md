# OpenSQMI

**An Index of Open-Source Implementations of Psychoacoustic and Sound Quality Metrics**

OpenSQMI stands for Open Sound Quality Metric Implementations. It lists open-source implementations of
psychoacoustic metrics, also called sound quality (SQ) metrics: loudness, sharpness, roughness, fluctuation
strength, tonality, impulsiveness and psychoacoustic annoyance. Each implementation is listed under the standard
edition or model paper it follows. Any programming language. Refreshed every month. OpenSQMI computes nothing
itself; it lists and compares the implementations.

Developed by Zhenxian LI with assistance from Claude Code.

**Website:** <https://zhenxianli.github.io/psychoacoustic-metrics-index/>
**Data:** [`data/index.json`](data/index.json) · [`llms.txt`](llms.txt) · [`llms-full.txt`](llms-full.txt) · [schema](data/SCHEMA.md)
**中文说明：** [README.zh-CN.md](README.zh-CN.md)

[![Site](https://github.com/ZhenxianLi/psychoacoustic-metrics-index/actions/workflows/pages.yml/badge.svg)](https://github.com/ZhenxianLi/psychoacoustic-metrics-index/actions/workflows/pages.yml)
[![Monthly refresh](https://github.com/ZhenxianLi/psychoacoustic-metrics-index/actions/workflows/refresh.yml/badge.svg)](https://github.com/ZhenxianLi/psychoacoustic-metrics-index/actions/workflows/refresh.yml)
[![Licence: MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](LICENSE)

<!-- BEGIN GENERATED: stats -->
Data as of 2026-10-06: 22 methods, 32 projects, languages: C, C++, Julia, MATLAB, Octave, Pure Data, Python, Rust.
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

The website opens with a timeline: every standard edition and model paper in the year it appeared, with the
projects that implement it. Its tabs list the metrics, the projects, the languages (which metrics can be computed
in each language, and how each project is called from it), the standards, questions and answers with a message
box, updates, and a page for AI agents. The table below is the short version: the current edition of each method
and the projects that implement it, by language. Within each language, established projects come first;
projects marked *newly released* were first released less than about a year ago and are not yet widely used in
the community, and *legacy* projects are archived or have had no commit for three years. Each method has its own
page on the website with the full edition history, function names and validation notes.

<!-- BEGIN GENERATED: overview -->
| Quantity | Method | Current edition | Open-source implementations (by language) |
|---|---|---|---|
| Loudness | [Zwicker loudness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-zwicker.html) | ISO 532-1:2017 | Python: [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html), [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (newly released; also C), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (newly released), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html) (developing), [PsychoacousticParametersMeasurer](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psychoacoustic-parameters-measurer.html) (legacy) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html), [AARAE](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/aarae.html) · C++: [SoundPalette](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/soundpalette.html) (newly released) · Rust: [iso532-1-rs](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/iso532-1-rs.html) (newly released; also C, Python) · Julia: [ZwickerLoudness.jl](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/zwickerloudness-jl.html) (newly released) · earlier or related: [AARAE](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/aarae.html) (Chalupper & Fastl (2002)), [PsySound3](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psysound3.html) (Chalupper & Fastl (2002)), [loudness (deeuu)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/deeuu-loudness.html) (DIN 45631:1991), [Zwicker's Loudness Calculation SW + Tool (ISO 532B)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/zwickerloudness-sourceforge.html) (DIN 45631:1991) |
| Loudness | [Moore–Glasberg loudness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg.html) | ISO 532-2:2017 | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (newly released) · earlier or related: [Auditory Modeling Toolbox (AMT)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/amt.html) (Chen et al. (2011)), [Auditory Modeling Toolbox (AMT)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/amt.html) (Moore, Glasberg & Baer (1997)), [AARAE](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/aarae.html) (Moore, Glasberg & Baer (1997)), [NumpyLibforPsychoAcoustic](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/numpylib-psychoacoustic.html) (Moore, Glasberg & Baer (1997)), [loudness (deeuu)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/deeuu-loudness.html) (Chen et al. (2011)), [loudness (deeuu)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/deeuu-loudness.html) (ANSI/ASA S3.4-2007), [PsySound3](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psysound3.html) (Moore, Glasberg & Baer (1997)) |
| Loudness | [Time-varying loudness (Moore–Glasberg–Schlittenlacher)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg-time-varying.html) | ISO 532-3:2023 | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (newly released) · MATLAB: [iso532-3 (tv2018.m)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/js2251-iso532-3.html) · earlier or related: [Auditory Modeling Toolbox (AMT)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/amt.html) (Moore et al. (2016)), [Auditory Modeling Toolbox (AMT)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/amt.html) (Glasberg & Moore (2002)), [AARAE](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/aarae.html) (Glasberg & Moore (2002)), [torch_amt](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/torch-amt.html) (Moore et al. (2016)), [NumpyLibforPsychoAcoustic](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/numpylib-psychoacoustic.html) (Glasberg & Moore (2002)), [torch_amt](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/torch-amt.html) (Glasberg & Moore (2002)), [LoudnessModel](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/loudnessmodel.html) (Moore et al. (2018)), [loudness (deeuu)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/deeuu-loudness.html) (Glasberg & Moore (2002)), [PsySound3](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psysound3.html) (Glasberg & Moore (2002)) |
| Loudness | [Sottek Hearing Model loudness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-ecma-418-2.html) | ECMA-418-2:2025 (4th ed.) | Python: [sottek-hearing-model](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sottek-hearing-model.html), [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (newly released; also C), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (newly released) · MATLAB: [refmap-psychoacoustics](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/refmap-psychoacoustics.html) (also Python), [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (unreleased) · earlier or related: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (ECMA-418-2:2024 (3rd ed.)), [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html) (ECMA-418-2:2022 (2nd ed.)), [MoSQITo-FDP](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito-fdp.html) (ECMA-418-2:2020 (1st ed.)) |
| Sharpness | [Sharpness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/sharpness.html) | DIN 45692:2009 | Python: [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html), [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (newly released; also C), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (newly released), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html) (developing), [PsychoacousticParametersMeasurer](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psychoacoustic-parameters-measurer.html) (legacy) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html), [refmap-psychoacoustics](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/refmap-psychoacoustics.html) (also Python) · C++: [SoundPalette](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/soundpalette.html) (newly released) · earlier or related: [AARAE](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/aarae.html) (Fastl & Zwicker (2007)) |
| Roughness | [Roughness (Daniel & Weber)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-daniel-weber.html) | Daniel & Weber (1997) | Python: [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html), [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (newly released; also C), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html) (developing) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html), [AARAE](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/aarae.html), [PsySound3](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psysound3.html) (legacy) · C++: [SoundPalette](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/soundpalette.html) (newly released) |
| Roughness | [Sottek Hearing Model roughness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-ecma-418-2.html) | ECMA-418-2:2025 (4th ed.) | Python: [sottek-hearing-model](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sottek-hearing-model.html), [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (newly released; also C), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (newly released) · MATLAB: [refmap-psychoacoustics](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/refmap-psychoacoustics.html) (also Python), [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (unreleased) · earlier or related: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (ECMA-418-2:2024 (3rd ed.)), [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html) (ECMA-418-2:2022 (2nd ed.)) |
| Roughness | [Roughness (DIN 38455)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-din-38455.html) | DIN 38455:2024 | none found |
| Fluctuation strength | [Fluctuation strength (Osses et al.)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-osses.html) | Osses et al. (2016) | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (newly released), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html) (developing) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html), [fluctuation-strength-TUe](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/fluctuation-strength-tue.html) (legacy) · earlier or related: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (Fastl & Zwicker (2007)), [PsychoacousticParametersMeasurer](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psychoacoustic-parameters-measurer.html) (Fastl & Zwicker (2007)) |
| Fluctuation strength | [Sottek Hearing Model fluctuation strength](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-ecma-418-2.html) | ECMA-418-2:2025 (4th ed.) | Python: [sottek-hearing-model](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sottek-hearing-model.html) (unreleased), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (newly released) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (proposed) |
| Tonality | [Tonality (Aures)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-aures.html) | Aures (1985b) | Python: [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html) (proposed), [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (newly released; also C), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html) (developing) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) |
| Tonality | [Sottek Hearing Model tonality](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-ecma-418-2.html) | ECMA-418-2:2025 (4th ed.) | Python: [sottek-hearing-model](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sottek-hearing-model.html), [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (newly released; also C), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (newly released) · MATLAB: [refmap-psychoacoustics](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/refmap-psychoacoustics.html) (also Python), [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (unreleased) · earlier or related: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (ECMA-418-2:2024 (3rd ed.)) |
| Tonality | [Tone-to-noise ratio and prominence ratio](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tone-to-noise-prominence-ratio.html) | ECMA-418-1:2024 (3rd ed.) | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (newly released) · earlier or related: [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html) (ECMA-74:2019 (17th ed.)), [MoSQITo-FDP](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito-fdp.html) (ECMA-74:2019 (17th ed.)) |
| Tonality | [Tonal components (DIN 45681)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-din-45681.html) | DIN 45681:2005 | none found |
| Tonality | [Audibility of tones in noise (ISO/TS 20065)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-20065.html) | ISO/TS 20065:2022 | none found · earlier or related: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (ISO/PAS 20065:2016) |
| Tonality | [Tonal audibility (ISO 1996-2)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-1996-2.html) | ISO 1996-2:2017 | Python: [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html) (proposed), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (newly released) · earlier or related: [acoustic-toolbox](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/acoustic-toolbox.html) (ISO 1996-2:2007), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (ISO 1996-2:2007), [python-acoustics](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/python-acoustics.html) (ISO 1996-2:2007) |
| Tonality | [Tonal audibility of wind turbines (IEC 61400-11)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iec-61400-11.html) | IEC 61400-11:2012+AMD1:2018 | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (newly released) |
| Impulsiveness | [Impulse prominence](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/impulsiveness.html) | ISO/PAS 1996-3:2022 | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (newly released) · earlier or related: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (NT ACOU 112) |
| Psychoacoustic annoyance | [Psychoacoustic annoyance](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/psychoacoustic-annoyance.html) | Widmann (1992), Zwicker & Fastl (1999), More (2010), and Di et al. (2016) | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (newly released), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html) (developing), [PsychoacousticParametersMeasurer](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psychoacoustic-parameters-measurer.html) (legacy) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html), [refmap-psychoacoustics](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/refmap-psychoacoustics.html) (also Python) |
| Related quantities | [Equal-loudness contours](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/equal-loudness-contours.html) | ISO 226:2023 | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (newly released) · earlier or related: [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html) (ISO 226:2003), [PSYCHO (pd-psycho)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pd-psycho.html) (ISO 226:2003), [PyDSM](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pydsm.html) (ISO 226:2003), [IoSR Matlab Toolbox](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/iosr-matlab-toolbox.html) (ISO 226:2003) |
| Related quantities | [Perceived noise level and EPNL](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/epnl.html) | ICAO Annex 16, Vol. I and 14 CFR Part 36 | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (newly released), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html) (developing), [SUAVE](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/suave.html) (legacy) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) · Rust: [epnl (Zhen-Ni)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/zhen-ni-epnl.html) (legacy) |
| Related quantities | [Aural detectability](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/aural-detectability.html) | Fidell et al. (1974) | MATLAB: [refmap-psychoacoustics](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/refmap-psychoacoustics.html) (also Python) · earlier or related: [refmap-psychoacoustics](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/refmap-psychoacoustics.html) (Rizzi et al. (2025)) |
<!-- END GENERATED: overview -->

### Gaps

No available open-source implementation of the current edition has been found for:

<!-- BEGIN GENERATED: gaps -->
- [Roughness, DIN 38455](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-din-38455.html)
- [Tonal components and tone adjustment (DIN 45681)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-din-45681.html)
- [Audibility of tones in noise (ISO/TS 20065)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-20065.html)

Released implementations of the current edition come only from newly released projects, which are not yet widely used, for:

- [Moore–Glasberg loudness of stationary sounds (ISO 532-2, ANSI S3.4)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg.html)
- [Fluctuation strength from the Sottek Hearing Model (ECMA-418-2)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-ecma-418-2.html)
- [Tone-to-noise ratio and prominence ratio (ECMA-418-1)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tone-to-noise-prominence-ratio.html)
- [Tonal audibility in environmental noise (ISO 1996-2)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-1996-2.html)
- [Tonal audibility of wind turbine noise (IEC 61400-11)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iec-61400-11.html)
- [Prominence of impulsive sounds (ISO/PAS 1996-3, NT ACOU 112)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/impulsiveness.html)
- [Equal-loudness-level contours (ISO 226)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/equal-loudness-contours.html)
<!-- END GENERATED: gaps -->

### Coverage by language

Which languages have an implementation of each method.

<!-- BEGIN GENERATED: coverage -->
| Method | Python | MATLAB/Octave | C/C++ | Rust | Julia | Other |
|---|---|---|---|---|---|---|
| [Zwicker loudness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-zwicker.html) | ● | ● | ◐ | ◐ | ◐ | — |
| [Moore–Glasberg loudness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg.html) | ◐ | ○ | ○ | — | — | — |
| [Time-varying loudness (Moore–Glasberg–Schlittenlacher)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg-time-varying.html) | ◐ | ● | ○ | — | — | — |
| [Sottek Hearing Model loudness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-ecma-418-2.html) | ● | ● | ◐ | — | — | — |
| [Sharpness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/sharpness.html) | ● | ● | ◐ | — | — | — |
| [Roughness (Daniel & Weber)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-daniel-weber.html) | ● | ● | ◐ | — | — | — |
| [Sottek Hearing Model roughness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-ecma-418-2.html) | ● | ● | ◐ | — | — | — |
| [Roughness (DIN 38455)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-din-38455.html) | — | — | — | — | — | — |
| [Fluctuation strength (Osses et al.)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-osses.html) | ● | ● | — | — | — | — |
| [Sottek Hearing Model fluctuation strength](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-ecma-418-2.html) | ◐ | ○ | — | — | — | — |
| [Tonality (Aures)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-aures.html) | ● | ● | ◐ | — | — | — |
| [Sottek Hearing Model tonality](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-ecma-418-2.html) | ● | ● | ◐ | — | — | — |
| [Tone-to-noise ratio and prominence ratio](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tone-to-noise-prominence-ratio.html) | ◐ | — | — | — | — | — |
| [Tonal components (DIN 45681)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-din-45681.html) | — | — | — | — | — | — |
| [Audibility of tones in noise (ISO/TS 20065)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-20065.html) | ○ | — | — | — | — | — |
| [Tonal audibility (ISO 1996-2)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-1996-2.html) | ◐ | — | — | — | — | — |
| [Tonal audibility of wind turbines (IEC 61400-11)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iec-61400-11.html) | ◐ | — | — | — | — | — |
| [Impulse prominence](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/impulsiveness.html) | ◐ | — | — | — | — | — |
| [Psychoacoustic annoyance](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/psychoacoustic-annoyance.html) | ● | ● | — | — | — | — |
| [Equal-loudness contours](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/equal-loudness-contours.html) | ◐ | ○ | ○ | — | — | ○ |
| [Perceived noise level and EPNL](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/epnl.html) | ● | ● | — | ● | — | — |
| [Aural detectability](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/aural-detectability.html) | ● | ● | — | — | — | — |

● an available implementation of the current edition; ◐ the same, but only from newly released projects that are not yet widely used; ○ only unreleased, proposed or older-edition implementations; — none found. Bindings count: a C library with a Python interface counts for Python.
<!-- END GENERATED: coverage -->

## Projects

<!-- BEGIN GENERATED: projects -->
| Project | Standing | Language | Licence | Latest release | Last commit | Activity |
|---|---|---|---|---|---|---|
| [SQAT](https://github.com/ggrecow/SQAT) | established, most widely used | MATLAB | GPL-3.0-or-later (main) / CC-BY-NC-4.0 (releases) | v1.3 (2025-04) | 2026-10-02 | active |
| [Auditory Modeling Toolbox (AMT)](https://sourceforge.net/p/amtoolbox/code/) | established, most widely used | MATLAB, Octave | GPL-3.0 | 1.6.0 (2024-10) | 2026-06-14 | active |
| [MoSQITo](https://github.com/Eomys/MoSQITo) | established, most widely used | Python | Apache-2.0 | 1.2.1 (2024-04) | 2024-04-22 | inactive since 2024-04 |
| [acoustic-toolbox](https://github.com/Universite-Gustave-Eiffel/acoustic-toolbox) | established | Python | BSD-3-Clause | 0.2.2 (2026-01) | 2026-02-12 | active |
| [PSYCHO (pd-psycho)](https://github.com/porres/pd-psycho) | established | Pure Data, C | GPL-3.0-or-later | 1.1 (2025-10) | 2025-10-14 | active |
| [refmap-psychoacoustics](https://github.com/acoustics-code-salford/refmap-psychoacoustics) | established | MATLAB, Python | GPL-3.0 | no release | 2026-10-02 | active |
| [sottek-hearing-model](https://github.com/mlotinga/sottek-hearing-model) | established | Python | GPL-3.0-only | 0.1.14 (2026-03) | 2026-09-18 | active |
| [AARAE](https://github.com/densilcabrera/aarae) | established | MATLAB | BSD-3-Clause | no release | 2024-08-09 | inactive since 2024-08 |
| [iso532-3 (tv2018.m)](https://github.com/js2251/iso532-3) | established | MATLAB | none | no release | 2021-10-08 | inactive since 2021-10 |
| [PyDSM](https://github.com/sergiocallegari/PyDSM) | established | Python | GPL-3.0-or-later | 0.15.2 (2025-08) | 2025-08-22 | inactive since 2025-08 |
| [MetaSona](https://github.com/huaaudio/metasona) | newly released, not yet widely used | Python, C | GPL-3.0-only AND Apache-2.0 AND BSD-3-Clause AND MIT | 0.2.2 (2026-09) | 2026-09-25 | active |
| [iso532-1-rs](https://github.com/cclin99/iso532-1-rs) | newly released, not yet widely used | Rust, C, Python | Apache-2.0 | 0.1.0 (2026-07) | 2026-07-21 | active |
| [NumpyLibforPsychoAcoustic](https://github.com/Ryrybros/NumpyLibforPsychoAcoustic) | newly released, not yet widely used | Python | none | no release | 2026-06-07 | active |
| [phonometry](https://github.com/jmrplens/phonometry) | newly released, not yet widely used | Python | MIT | 3.3.0 (2026-07) | 2026-10-01 | active |
| [SoundPalette](https://github.com/onyx-prismantium/soundpalette) | newly released, not yet widely used | C++ | FSL-1.1-Apache-2.0 | v0.8.0 (2026-09) | 2026-09-27 | active |
| [torch_amt](https://github.com/StefanoGiacomelli/torch_amt) | newly released, not yet widely used | Python | GPL-3.0-or-later | 0.2.0 (2026-02) | 2026-03-19 | active |
| [ZwickerLoudness.jl](https://github.com/slink/ZwickerLoudness.jl) | newly released, not yet widely used | Julia | MIT | 0.3.0 (2026-07) | 2026-09-02 | active |
| [pySQAT](https://github.com/PALILA-TUDelft/pySQAT) | developing | Python | none | no release | 2026-06-27 | active |
| [LoudnessModel](https://github.com/MalcolmSlaney/LoudnessModel) | developing | Python | BSD-2-Clause | no release | 2025-03-20 | inactive since 2025-03 |
| [epnl (Zhen-Ni)](https://github.com/Zhen-Ni/epnl) | legacy, no commit since 2023-07 | Rust | none | no release | 2023-07-10 | inactive since 2023-07 |
| [fluctuation-strength-TUe](https://github.com/aosses-tue/fluctuation-strength-TUe) | legacy, no commit since 2020-01 | MATLAB | none | 1.0 (2019-12) | 2020-01-02 | inactive since 2020-01 |
| [IoSR Matlab Toolbox](https://github.com/IoSR-Surrey/MatlabToolbox) | legacy, no commit since 2017-08 | MATLAB | MIT | v2.8 (2017-06) | 2017-08-18 | inactive since 2017-08 |
| [loudness (deeuu)](https://github.com/deeuu/loudness) | legacy, no commit since 2019-08 | C++, Python | GPL-3.0-or-later | no release | 2019-08-08 | inactive since 2019-08 |
| [MoSQITo-FDP](https://github.com/djcaminero/MoSQITo-FDP) | legacy, archived | Python | Apache-2.0 | no release | 2021-07-05 | archived |
| [PsychoacousticParametersMeasurer](https://github.com/AndreaCastiella/PsychoacousticParametersMeasurer) | legacy, no commit since 2021-06 | Python | none | no release | 2021-06-06 | inactive since 2021-06 |
| [PsySound3](https://github.com/densilcabrera/psysound3) | legacy, no commit since 2015-03 | MATLAB | none | no release | 2015-03-28 | inactive since 2015-03 |
| [python-acoustics](https://github.com/python-acoustics/python-acoustics) | legacy, archived | Python | BSD-3-Clause | 0.2.6 (2022-07) | 2023-08-20 | archived |
| [SUAVE](https://github.com/suavecode/SUAVE) | legacy, no commit since 2022-12 | Python | LGPL-2.1 | 2.5.2 (2022-03) | 2022-12-23 | inactive since 2022-12 |
| [Zwicker's Loudness Calculation SW + Tool (ISO 532B)](https://sourceforge.net/projects/zwickerloudness/) | legacy, no commit since 2018-06 | C | GPL-2.0 | zwickerloudness-020 (2011-07) | 2018-06-05 | inactive since 2018-06 |
| [PsychoBox](https://github.com/henriquealende/PsychoBox) | other: calls MoSQITo | Python | MIT | no release | 2026-03-16 | active |
| [Soundscapy](https://github.com/MitchellAcoustics/Soundscapy) | other: calls MoSQITo | Python | BSD-3-Clause | 0.8.5 (2026-05) | 2026-05-14 | active |
| [ZwickerLoudnessAudio.jl](https://github.com/slink/ZwickerLoudnessAudio.jl) | other: calls ZwickerLoudness.jl | Julia | MIT | 0.3.0 (2026-07) | 2026-09-02 | active |
<!-- END GENERATED: projects -->

Every project is in exactly one group: *established* (described in a publication, used by others, or written by
the authors of the model, with more than a year of history), *newly released* (first released less than about a
year ago and not yet widely used in the community), *developing* (public for more than a year, but without a
publication or documented use by others: research, teaching or personal code), *legacy* (archived, or no commit
for three years or more) or *other* (a tool that does not compute the metrics itself but calls another indexed
project, such as an interface or a wrapper; it is listed with the project it calls and not counted under the
metrics). All lists follow this order. The most widely used projects (SQAT, the Auditory Modeling Toolbox and
MoSQITo) come first and are never listed as legacy, and neither are reference programs published with a
standard. "Activity" is computed from the last commit on the default branch (inactive after 365 days without a
commit).

## How it is maintained

- **Data.** Everything lives in [`data/`](data/): methods in `metrics.yaml`, standard editions and model papers
  in `references.yaml`, one file per project in `projects/`. The format is described in
  [`data/SCHEMA.md`](data/SCHEMA.md).
- **Build.** [`scripts/build.py`](scripts/build.py) validates the data and generates the website, the tables in
  this README, `llms.txt`, `llms-full.txt` and `data/index.json`.
- **Monthly refresh.** Once a month, a GitHub Action updates repository and package metadata (last commit,
  releases, PyPI and crates.io versions), searches GitHub and package registries for new candidate projects,
  and checks ISO and Ecma for new editions. Its findings are collected in one issue labelled `monthly-review`,
  which a person reviews before anything is added or changed.

## Using the data

- [`data/index.json`](data/index.json) contains the whole index (methods, editions, projects,
  implementations) in one JSON document; the same file is served at
  <https://zhenxianli.github.io/psychoacoustic-metrics-index/index.json>.
- [`llms.txt`](llms.txt) and [`llms-full.txt`](llms-full.txt) are plain-text summaries for language models and
  other tools. Every page on the website also has a Markdown version (replace `.html` with `.md`), and the
  [For AI](https://zhenxianli.github.io/psychoacoustic-metrics-index/ai.html) page explains how agents can
  retrieve and cite the index.
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
