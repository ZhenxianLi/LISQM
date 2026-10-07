# Changelog

Notable changes to the list. This file is generated from `data/updates.yaml`; the same notes are on the website (https://zhenxianli.github.io/LISQM/updates.html) and in its Atom feed.

## 2026-10-07: Version 0.2: how each implementation was validated

Project and method pages have a new section, *How it was validated*: what each project says it checked, and
against what (test signals of the standard, the model authors' code, MoSQITo, SQAT or commercial software),
with the tolerances and results it reports. Validation tags now name what an implementation was compared with,
for example "compared with MoSQITo", instead of "another implementation". Agreement with another implementation
shows that both compute the same values, not that either follows the standard.

Also in this version:

- On the home page, "+ more" shows the remaining projects of an edition in place.
- Edition labels in the implementation tables link to the standard or paper. Zwicker & Fastl (1999) now has its
  DOI, and five model papers and theses link to their publisher or library pages; the rest link to their full
  reference on the Standards page.
- MetaSona is listed as a C library with a Python interface.
- PsychoacousticMetrics.jl and Kirin Hypha, two newly released projects, were added the same day.

## 2026-10-07: Two newly released projects

PsychoacousticMetrics.jl (Julia) adds DIN 45692 sharpness, Daniel & Weber roughness, Osses et al. (2016)
fluctuation strength and Widmann (1992) psychoacoustic annoyance on top of ZwickerLoudness.jl, by the same
author. Kirin Hypha, a measurement plug-in for audio workstations, computes ISO 532-1 time-varying loudness and
DIN 45692 sharpness in Rust, ported from MoSQITo. Both were found by the first scheduled search for new
projects; like the other newly released projects, they are not yet widely used.

## 2026-10-06: Version 0.1, the first public version of LISQM

LISQM (List of Implementations of Sound Quality Metrics) starts with 32 projects in Python, MATLAB, Octave, C,
C++, Rust, Julia and Pure Data, and 22 methods from Zwicker loudness to aural detectability. Every implementation is
tied to the standard edition or model paper it follows, with links to the documentation the facts were taken
from. Repository dates, releases and package versions are refreshed twice a month.

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
  listed project). Lists follow this order, so a new, little-used or unmaintained project is never the first
  suggestion.
- Candidates that could not be checked yet, such as PsyTools (TU Graz) and the ITA-Toolbox, are listed on
  the About page as leads.
