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

The current edition of each method and the projects that implement it, by language. Each method has its own
page on the website with the full edition history, function names and validation notes.

<!-- BEGIN GENERATED: overview -->
| Quantity | Method | Current edition | Open-source implementations (by language) |
|---|---|---|---|
| Loudness | [Zwicker loudness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-zwicker.html) | ISO 532-1:2017 | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C), [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html), [PsychoacousticParametersMeasurer](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psychoacoustic-parameters-measurer.html), [PsychoBox](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psychobox.html) (via MoSQITo), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html), [Soundscapy](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/soundscapy.html) (via MoSQITo) · MATLAB: [AARAE](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/aarae.html), [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) · C++: [SoundPalette](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/soundpalette.html) · Rust: [iso532-1-rs](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/iso532-1-rs.html) (also C, Python) · Julia: [ZwickerLoudness.jl](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/zwickerloudness-jl.html), [ZwickerLoudnessAudio.jl](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/zwickerloudnessaudio-jl.html) · earlier or related: [AARAE](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/aarae.html) (Chalupper & Fastl (2002)), [PsySound3](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psysound3.html) (Chalupper & Fastl (2002)), [loudness (deeuu)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/deeuu-loudness.html) (DIN 45631:1991), [Zwicker's Loudness Calculation SW + Tool (ISO 532B)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/zwickerloudness-sourceforge.html) (ISO 532:1975) |
| Loudness | [Moore–Glasberg loudness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg.html) | ISO 532-2:2017 | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) · earlier or related: [Auditory Modeling Toolbox (AMT)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/amt.html) (Chen et al. (2011)), [loudness (deeuu)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/deeuu-loudness.html) (Chen et al. (2011)), [loudness (deeuu)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/deeuu-loudness.html) (ANSI/ASA S3.4-2007), [AARAE](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/aarae.html) (Moore, Glasberg & Baer (1997)), [Auditory Modeling Toolbox (AMT)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/amt.html) (Moore, Glasberg & Baer (1997)), [NumpyLibforPsychoAcoustic](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/numpylib-psychoacoustic.html) (Moore, Glasberg & Baer (1997)), [PsySound3](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psysound3.html) (Moore, Glasberg & Baer (1997)) |
| Loudness | [Time-varying loudness (Moore–Glasberg–Schlittenlacher)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg-time-varying.html) | ISO 532-3:2023 | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) · MATLAB: [iso532-3 (tv2018.m)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/js2251-iso532-3.html) · earlier or related: [LoudnessModel](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/loudnessmodel.html) (Moore et al. (2018)), [Auditory Modeling Toolbox (AMT)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/amt.html) (Moore et al. (2016)), [torch_amt](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/torch-amt.html) (Moore et al. (2016)), [AARAE](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/aarae.html) (Glasberg & Moore (2002)), [Auditory Modeling Toolbox (AMT)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/amt.html) (Glasberg & Moore (2002)), [loudness (deeuu)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/deeuu-loudness.html) (Glasberg & Moore (2002)), [NumpyLibforPsychoAcoustic](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/numpylib-psychoacoustic.html) (Glasberg & Moore (2002)), [PsySound3](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psysound3.html) (Glasberg & Moore (2002)), [torch_amt](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/torch-amt.html) (Glasberg & Moore (2002)) |
| Loudness | [Sottek Hearing Model loudness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-ecma-418-2.html) | ECMA-418-2:2025 (4th ed.) | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html) (via sottek-hearing-model), [sottek-hearing-model](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sottek-hearing-model.html) · MATLAB: [refmap-psychoacoustics](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/refmap-psychoacoustics.html) (also Python), [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (unreleased) · earlier or related: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (ECMA-418-2:2024 (3rd ed.)), [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html) (ECMA-418-2:2022 (2nd ed.)), [PsychoBox](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psychobox.html) (ECMA-418-2:2022 (2nd ed.)), [MoSQITo-FDP](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito-fdp.html) (ECMA-418-2:2020 (1st ed.)) |
| Sharpness | [Sharpness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/sharpness.html) | DIN 45692:2009 | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C), [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html), [PsychoacousticParametersMeasurer](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psychoacoustic-parameters-measurer.html), [PsychoBox](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psychobox.html) (via MoSQITo), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html), [Soundscapy](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/soundscapy.html) (via MoSQITo) · MATLAB: [refmap-psychoacoustics](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/refmap-psychoacoustics.html) (also Python), [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) · C++: [SoundPalette](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/soundpalette.html) · earlier or related: [AARAE](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/aarae.html) (Fastl & Zwicker (2007)) |
| Roughness | [Roughness (Daniel & Weber)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-daniel-weber.html) | Daniel & Weber (1997) | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C), [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html), [PsychoBox](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psychobox.html) (via MoSQITo), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html), [Soundscapy](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/soundscapy.html) (via MoSQITo) · MATLAB: [AARAE](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/aarae.html), [PsySound3](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psysound3.html), [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) · C++: [SoundPalette](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/soundpalette.html) |
| Roughness | [Sottek Hearing Model roughness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-ecma-418-2.html) | ECMA-418-2:2025 (4th ed.) | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html) (via sottek-hearing-model), [sottek-hearing-model](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sottek-hearing-model.html) · MATLAB: [refmap-psychoacoustics](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/refmap-psychoacoustics.html) (also Python), [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (unreleased) · earlier or related: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (ECMA-418-2:2024 (3rd ed.)), [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html) (ECMA-418-2:2022 (2nd ed.)), [PsychoBox](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psychobox.html) (ECMA-418-2:2022 (2nd ed.)) |
| Roughness | [Roughness (DIN 38455)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-din-38455.html) | DIN 38455:2024 | none found |
| Fluctuation strength | [Fluctuation strength (Osses et al.)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-osses.html) | Osses et al. (2016) | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html) · MATLAB: [fluctuation-strength-TUe](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/fluctuation-strength-tue.html), [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) · earlier or related: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (Fastl & Zwicker (2007)), [PsychoacousticParametersMeasurer](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psychoacoustic-parameters-measurer.html) (Fastl & Zwicker (2007)) |
| Fluctuation strength | [Sottek Hearing Model fluctuation strength](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-ecma-418-2.html) | ECMA-418-2:2025 (4th ed.) | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html), [sottek-hearing-model](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sottek-hearing-model.html) (unreleased) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (proposed) |
| Tonality | [Tonality (Aures)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-aures.html) | Aures (1985b) | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html), [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html) (proposed) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) |
| Tonality | [Sottek Hearing Model tonality](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-ecma-418-2.html) | ECMA-418-2:2025 (4th ed.) | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html) (via sottek-hearing-model), [sottek-hearing-model](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sottek-hearing-model.html) · MATLAB: [refmap-psychoacoustics](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/refmap-psychoacoustics.html) (also Python), [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (unreleased) · earlier or related: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (ECMA-418-2:2024 (3rd ed.)) |
| Tonality | [Tone-to-noise ratio and prominence ratio](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tone-to-noise-prominence-ratio.html) | ECMA-418-1:2024 (3rd ed.) | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) · earlier or related: [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html) (ECMA-74:2019 (17th ed.)), [MoSQITo-FDP](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito-fdp.html) (ECMA-74:2019 (17th ed.)) |
| Tonality | [Tonal components (DIN 45681)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-din-45681.html) | DIN 45681:2005 | none found |
| Tonality | [Audibility of tones in noise (ISO/TS 20065)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-20065.html) | ISO/TS 20065:2022 | none found · earlier or related: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (ISO/PAS 20065:2016) |
| Tonality | [Tonal audibility (ISO 1996-2)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-1996-2.html) | ISO 1996-2:2017 | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html), [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html) (proposed) · earlier or related: [acoustic-toolbox](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/acoustic-toolbox.html) (ISO 1996-2:2007), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (ISO 1996-2:2007), [python-acoustics](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/python-acoustics.html) (ISO 1996-2:2007) |
| Tonality | [Tonal audibility of wind turbines (IEC 61400-11)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iec-61400-11.html) | IEC 61400-11:2012+AMD1:2018 | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) |
| Impulsiveness | [Impulse prominence](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/impulsiveness.html) | ISO/PAS 1996-3:2022 | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) · earlier or related: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (NT ACOU 112) |
| Psychoacoustic annoyance | [Psychoacoustic annoyance](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/psychoacoustic-annoyance.html) | Widmann (1992), Zwicker & Fastl (1999), More (2010), and Di et al. (2016) | Python: [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html), [PsychoacousticParametersMeasurer](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/psychoacoustic-parameters-measurer.html) · MATLAB: [refmap-psychoacoustics](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/refmap-psychoacoustics.html) (also Python), [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html), [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (unreleased) |
| Related quantities | [Equal-loudness contours](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/equal-loudness-contours.html) | ISO 226:2023 | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) · earlier or related: [IoSR Matlab Toolbox](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/iosr-matlab-toolbox.html) (ISO 226:2003), [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html) (ISO 226:2003), [PSYCHO (pd-psycho)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pd-psycho.html) (ISO 226:2003), [PyDSM](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pydsm.html) (ISO 226:2003) |
| Related quantities | [Perceived noise level and EPNL](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/epnl.html) | ICAO Annex 16, Vol. I and 14 CFR Part 36 | Python: [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html), [SUAVE](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/suave.html) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) · Rust: [epnl (Zhen-Ni)](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/zhen-ni-epnl.html) |
| Related quantities | [Aural detectability](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/aural-detectability.html) | Fidell et al. (1974) | MATLAB: [refmap-psychoacoustics](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/refmap-psychoacoustics.html) (also Python) |
<!-- END GENERATED: overview -->

### Gaps

No available open-source implementation of the current edition has been found for:

<!-- BEGIN GENERATED: gaps -->
- [Roughness, DIN 38455](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-din-38455.html)
- [Tonal components and tone adjustment (DIN 45681)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-din-45681.html)
- [Audibility of tones in noise (ISO/TS 20065)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-20065.html)
<!-- END GENERATED: gaps -->

### Coverage by language

Which languages have an implementation of each method.

<!-- BEGIN GENERATED: coverage -->
| Method | Python | MATLAB/Octave | C/C++ | Rust | Julia | Other |
|---|---|---|---|---|---|---|
| [Zwicker loudness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-zwicker.html) | ● | ● | ● | ● | ● | — |
| [Moore–Glasberg loudness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg.html) | ● | ○ | ○ | — | — | — |
| [Time-varying loudness (Moore–Glasberg–Schlittenlacher)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg-time-varying.html) | ● | ● | ○ | — | — | — |
| [Sottek Hearing Model loudness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-ecma-418-2.html) | ● | ● | ● | — | — | — |
| [Sharpness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/sharpness.html) | ● | ● | ● | — | — | — |
| [Roughness (Daniel & Weber)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-daniel-weber.html) | ● | ● | ● | — | — | — |
| [Sottek Hearing Model roughness](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-ecma-418-2.html) | ● | ● | ● | — | — | — |
| [Roughness (DIN 38455)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-din-38455.html) | — | — | — | — | — | — |
| [Fluctuation strength (Osses et al.)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-osses.html) | ● | ● | — | — | — | — |
| [Sottek Hearing Model fluctuation strength](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-ecma-418-2.html) | ● | ○ | — | — | — | — |
| [Tonality (Aures)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-aures.html) | ● | ● | ● | — | — | — |
| [Sottek Hearing Model tonality](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-ecma-418-2.html) | ● | ● | ● | — | — | — |
| [Tone-to-noise ratio and prominence ratio](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tone-to-noise-prominence-ratio.html) | ● | — | — | — | — | — |
| [Tonal components (DIN 45681)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-din-45681.html) | — | — | — | — | — | — |
| [Audibility of tones in noise (ISO/TS 20065)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-20065.html) | ○ | — | — | — | — | — |
| [Tonal audibility (ISO 1996-2)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-1996-2.html) | ● | — | — | — | — | — |
| [Tonal audibility of wind turbines (IEC 61400-11)](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iec-61400-11.html) | ● | — | — | — | — | — |
| [Impulse prominence](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/impulsiveness.html) | ● | — | — | — | — | — |
| [Psychoacoustic annoyance](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/psychoacoustic-annoyance.html) | ● | ● | — | — | — | — |
| [Equal-loudness contours](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/equal-loudness-contours.html) | ● | ○ | ○ | — | — | ○ |
| [Perceived noise level and EPNL](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/epnl.html) | ● | ● | — | ● | — | — |
| [Aural detectability](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/aural-detectability.html) | ● | ● | — | — | — | — |

● an available implementation of the current edition; ○ only unreleased, proposed or older-edition implementations; — none found. Bindings count: a C library with a Python interface counts for Python.
<!-- END GENERATED: coverage -->

## Projects

<!-- BEGIN GENERATED: projects -->
| Project | Language | Licence | Latest release | Last commit | Activity |
|---|---|---|---|---|---|
| [AARAE](https://github.com/densilcabrera/aarae) | MATLAB | BSD-3-Clause | no release | 2024-08-09 | inactive since 2024-08 |
| [acoustic-toolbox](https://github.com/Universite-Gustave-Eiffel/acoustic-toolbox) | Python | BSD-3-Clause | 0.2.2 (2026-01) | 2026-02-12 | active |
| [Auditory Modeling Toolbox (AMT)](https://sourceforge.net/p/amtoolbox/code/) | MATLAB, Octave | GPL-3.0 | 1.6.0 (2024-10) | 2026-06-14 | active |
| [epnl (Zhen-Ni)](https://github.com/Zhen-Ni/epnl) | Rust | none | no release | 2023-07-10 | inactive since 2023-07 |
| [fluctuation-strength-TUe](https://github.com/aosses-tue/fluctuation-strength-TUe) | MATLAB | none | 1.0 (2019-12) | 2020-01-02 | inactive since 2020-01 |
| [IoSR Matlab Toolbox](https://github.com/IoSR-Surrey/MatlabToolbox) | MATLAB | MIT | v2.8 (2017-06) | 2017-08-18 | inactive since 2017-08 |
| [iso532-1-rs](https://github.com/cclin99/iso532-1-rs) | Rust, C, Python | Apache-2.0 | 0.1.0 (2026-07) | 2026-07-21 | active |
| [iso532-3 (tv2018.m)](https://github.com/js2251/iso532-3) | MATLAB | none | no release | 2021-10-08 | inactive since 2021-10 |
| [loudness (deeuu)](https://github.com/deeuu/loudness) | C++, Python | GPL-3.0-or-later | no release | 2019-08-08 | inactive since 2019-08 |
| [LoudnessModel](https://github.com/MalcolmSlaney/LoudnessModel) | Python | BSD-2-Clause | no release | 2025-03-20 | inactive since 2025-03 |
| [MetaSona](https://github.com/huaaudio/metasona) | Python, C | GPL-3.0-only AND Apache-2.0 AND BSD-3-Clause AND MIT | 0.2.2 (2026-09) | 2026-09-25 | active |
| [MoSQITo](https://github.com/Eomys/MoSQITo) | Python | Apache-2.0 | 1.2.1 (2024-04) | 2024-04-22 | inactive since 2024-04 |
| [MoSQITo-FDP](https://github.com/djcaminero/MoSQITo-FDP) | Python | Apache-2.0 | no release | 2021-07-05 | archived |
| [NumpyLibforPsychoAcoustic](https://github.com/Ryrybros/NumpyLibforPsychoAcoustic) | Python | none | no release | 2026-06-07 | active |
| [phonometry](https://github.com/jmrplens/phonometry) | Python | MIT | 3.3.0 (2026-07) | 2026-10-01 | active |
| [PSYCHO (pd-psycho)](https://github.com/porres/pd-psycho) | Pure Data, C | GPL-3.0-only | 1.1 (2025-10) | 2025-10-14 | active |
| [PsychoacousticParametersMeasurer](https://github.com/AndreaCastiella/PsychoacousticParametersMeasurer) | Python | none | no release | 2021-06-06 | inactive since 2021-06 |
| [PsychoBox](https://github.com/henriquealende/PsychoBox) | Python | MIT | no release | 2026-03-16 | active |
| [PsySound3](https://github.com/densilcabrera/psysound3) | MATLAB | none | no release | 2015-03-28 | inactive since 2015-03 |
| [PyDSM](https://github.com/sergiocallegari/PyDSM) | Python | GPL-3.0-or-later | 0.15.2 (2025-08) | 2025-08-22 | inactive since 2025-08 |
| [pySQAT](https://github.com/PALILA-TUDelft/pySQAT) | Python | none | no release | 2026-06-27 | active |
| [python-acoustics](https://github.com/python-acoustics/python-acoustics) | Python | BSD-3-Clause | 0.2.6 (2022-07) | 2023-08-20 | archived |
| [refmap-psychoacoustics](https://github.com/acoustics-code-salford/refmap-psychoacoustics) | MATLAB, Python | GPL-3.0-only | no release | 2026-10-02 | active |
| [sottek-hearing-model](https://github.com/mlotinga/sottek-hearing-model) | Python | GPL-3.0-only | 0.1.14 (2026-03) | 2026-09-18 | active |
| [SoundPalette](https://github.com/onyx-prismantium/soundpalette) | C++ | FSL-1.1-Apache-2.0 | v0.8.0 (2026-09) | 2026-09-27 | active |
| [Soundscapy](https://github.com/MitchellAcoustics/Soundscapy) | Python | BSD-3-Clause | 0.8.5 (2026-05) | 2026-05-14 | active |
| [SQAT](https://github.com/ggrecow/SQAT) | MATLAB | GPL-3.0-or-later (main) / CC-BY-NC-4.0 (releases) | v1.3 (2025-04) | 2026-10-02 | active |
| [SUAVE](https://github.com/suavecode/SUAVE) | Python | LGPL-2.1 | 2.5.2 (2022-03) | 2022-12-23 | inactive since 2022-12 |
| [torch_amt](https://github.com/StefanoGiacomelli/torch_amt) | Python | GPL-3.0-or-later | 0.2.0 (2026-02) | 2026-03-19 | active |
| [Zwicker's Loudness Calculation SW + Tool (ISO 532B)](https://sourceforge.net/projects/zwickerloudness/) | C | GPL-2.0 | zwickerloudness-020 (2011-07) | 2018-06-05 | inactive since 2018-06 |
| [ZwickerLoudness.jl](https://github.com/slink/ZwickerLoudness.jl) | Julia | MIT | 0.3.0 (2026-07) | 2026-09-02 | active |
| [ZwickerLoudnessAudio.jl](https://github.com/slink/ZwickerLoudnessAudio.jl) | Julia | MIT | 0.3.0 (2026-07) | 2026-09-02 | active |
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
