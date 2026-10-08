# Changelog

Notable changes to the list. This file is generated from `data/updates.yaml`; the same notes are on the website (https://zhenxianli.github.io/LISQM/updates.html) and in its Atom feed.

## 2026-10-08: Version 0.4: the project map

A new page, the [project map](https://zhenxianli.github.io/LISQM/projects/map.html), shows how the listed
projects are connected: code taken from another project, the author's own code, use at run time, results
checked against another project, and shared maintainers.

- The relations were checked again against the projects' code. Among the corrections: SQAT's fluctuation
  strength is Alejandro Osses's own code, MoSQITo's Zwicker loudness follows the 1991 BASIC program, and the
  time-varying loudness of ZwickerLoudness.jl is transcribed from MoSQITo.
- Plainer wording across the site.

## 2026-10-08: Licence: CC BY 4.0 for the data and the text

The data and the text of LISQM are now released under CC BY 4.0: they may be reused, also commercially, with
credit. The code that builds the website stays under MIT. Versions up to 0.3.0 remain available under MIT.

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
