# Changelog

Notable changes to the index. This file is generated from `data/updates.yaml`; the same notes are on the website (https://zhenxianli.github.io/psychoacoustic-metrics-index/updates.html) and in its Atom feed.

## 2026-10-06: First public version of OpenSQMI

OpenSQMI (Open Sound Quality Metric Implementations) starts with 32 projects in Python, MATLAB, Octave, C,
C++, Rust, Julia and Pure Data, and 22 methods from Zwicker loudness to aural detectability. Every implementation is
tied to the standard edition or model paper it follows, with links to the documentation the facts were taken
from. Repository dates, releases and package versions are refreshed once a month.

Worth knowing as of today:

- ECMA-418-2 is at its 4th edition (June 2025), which added fluctuation strength. sottek-hearing-model and
  refmap-psychoacoustics follow it, as do phonometry and MetaSona, two newly released projects that are not yet
  widely used. SQAT has it on its main branch only, and MoSQITo still follows the 2nd edition (2022).
- SQAT's latest release (v1.3) is licensed for non-commercial use only. Its main branch is GPL-3.0 and
  carries unreleased fixes to ISO 532-1 time-varying loudness, Aures tonality and Daniel & Weber roughness
  that change results.
- All three parts of ISO 532 are being revised; committee drafts have existed since November 2024.
- No open implementation was found for DIN 38455:2024 (the first German roughness standard), DIN 45681 or
  ISO/TS 20065:2022.
- Six projects disclose that AI tools assisted their development; each project page says where.
- Every project is in one group: established, newly released (first released less than about a year ago and
  not yet widely used), developing, legacy (archived, or no commit for three years) or others (calls another
  indexed project). Lists follow this order, so a new, little-used or unmaintained project is never the first
  suggestion.
- Candidates that could not be checked yet, such as PsyTools (TU Graz) and the ITA-Toolbox, are listed on
  the About page as leads.
