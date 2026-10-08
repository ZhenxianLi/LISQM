# Changelog

Notable changes to the list. This file is generated from `data/updates.yaml`; the same notes are on the website (https://zhenxianli.github.io/LISQM/updates.html) and in its Atom feed.

## 2026-10-08: Ported code: credit and licences

Each project that ports code has a new section, *Ported code*: where it credits the original code, with that
code's authors and licence. Method pages name them too, and the tree of who ported code from whom shows each
project's licence.

- When GPL or non-commercial code is ported to a project without those terms, a note says so; LISQM does not
  judge whether licence terms are met.

## 2026-10-07: Version 0.3: ported code, citations and new projects

Method pages show which implementations were ported from which; a comparison with an implementation's own
source is marked as such. A new section, *Before you compare numbers*, lists the settings that make correct
implementations give different results.

- Every project page says how to cite the project, and all references are available as BibTeX.
- New projects: ITA-Toolbox, Mosqito.NET, two legacy MATLAB tools, and PsyTools in a new group,
  *Status unknown*.
- SQAT and MoSQITo (widely used) and sottek-hearing-model (a very good implementation) come first, in bold.
- Each project page explains its kind: library/toolbox, research code, application, plug-in or reference
  program.
- The monthly refresh also reports broken links.

## 2026-10-07: Version 0.2: how each implementation was validated

A new section, *How it was validated*, says what each project checked, against what, and with what result.
Validation tags name the reference, for example "compared with MoSQITo".

- On the home page, "+ more" opens the remaining projects in place.
- Edition labels link to the standard or paper.

## 2026-10-07: Two newly released projects

Added PsychoacousticMetrics.jl, a Julia library, and Kirin Hypha, a measurement plug-in for audio workstations
written in Rust. Both were found by the first scheduled search for new projects.

## 2026-10-06: Version 0.1: the first public version

LISQM starts with 32 projects in eight languages and 22 methods, from Zwicker loudness to aural detectability.
Every implementation is tied to the standard edition or model paper it follows, with links to its sources.
Repository and package data are refreshed monthly.
