# Owner decisions

Content, wording and rules that the owner, Zhenxian LI, set explicitly. Keep them as they are; change one only when
the owner asks, and then add a row here. Texts marked *owner's text* are kept word for word.

| Date | Decision | Where |
|---|---|---|
| 2026-10-06 | The repository holds data and a website only; LISQM contains no metric code. | whole repository |
| 2026-10-06 | Information detailed enough for AI agents to find and read; a clear, concise website and README for people. | site, README, llms files |
| 2026-10-06 | Credit line, word for word: "Developed by Zhenxian LI with assistance from Claude Code." | `credit` in `data/site.yaml`, every page, README, CITATION.cff |
| 2026-10-06 | No AI tool or model appears among the contributors: commits carry no co-author or session lines. | git history |
| 2026-10-06 | Name LISQM, "List of Implementations of Sound Quality Metrics"; tagline "A List of Open-Source Implementations of Psychoacoustic and Sound Quality Metrics" (also the home heading and the social preview, 2026-10-07). The repository is named LISQM. | `data/site.yaml`, assets, GitHub |
| 2026-10-06 | LISQM is a "list", never an "index". | everywhere |
| 2026-10-06 | English only: no translated README, no multilingual site. | repository, site |
| 2026-10-06 | Only the `main` branch; Dependabot is kept. | GitHub |
| 2026-10-06 | No text names the owner's laboratory (LVA, INSA Lyon); the logo is the only tribute, and the masthead uses the laboratory's green. | site |
| 2026-10-06 | The edition timeline is the first thing on the home page. | Home |
| 2026-10-06 | Plain, blog-like pages without rounded cards; colours that help reading; desktop first. | `site-src/style.css` |
| 2026-10-06 | Each tab has its own sidebar matching its content; the home page has one too. | all pages |
| 2026-10-06 | MetaSona and phonometry are very new: never the first recommendation; always say that they are new and not yet widely used. | all lists, FAQ |
| 2026-10-06 | Group names "newly released" and "legacy" (no maintenance for three years or more); PsychoacousticParametersMeasurer is legacy; MoSQITo is mainstream and never legacy. | groups |
| 2026-10-06 | No automatic move between groups: the field changes slowly, and standing is set by hand. | `standing` |
| 2026-10-06 | MetaSona comes first among the newly released projects. The order inside a group is not explained (confirmed 2026-10-08). | `rank` in `metasona.yaml` |
| 2026-10-06 | A group "Others" for tools that do not compute the metrics themselves (for example PsychoBox, an interface). | groups |
| 2026-10-06 | The FAQ starts with a message box that opens a GitHub issue; no comment system (giscus was tried and removed); only the key questions. | FAQ |
| 2026-10-06 | The website badge in the README is bright. | README |
| 2026-10-06 | The data is refreshed twice a month; routine facts are committed without an issue, and only what needs a person goes into the review issue. | `refresh.yml` |
| 2026-10-07 | No DOI for LISQM itself: it is a list for researchers and does not need to be cited as a paper. | CITATION.cff |
| 2026-10-07 | MetaSona is shown as a C library; Python is its interface. | `languages` in `metasona.yaml` |
| 2026-10-07 | Edition labels link to the standard or paper; "+N more" on the timeline opens the list in place. | Home, tables |
| 2026-10-07 | Validation is shown in detail and names what each project compared with; a comparison with one's own source is marked as such. | metric and project pages |
| 2026-10-07 | Each project page says how to cite it; all references are exported as BibTeX. | project pages, `references.bib` |
| 2026-10-07 | A section "Before you compare numbers" per metric (sound field, calibration, sample rate, percentiles, weightings, start of the signal). | metric pages |
| 2026-10-07 | External links are checked in the refresh, and broken ones go into the review issue. | `refresh.yml` |
| 2026-10-07 | Bold and first in every list, in this order: SQAT, MoSQITo, sottek-hearing-model. SQAT and MoSQITo are "widely used"; sottek-hearing-model is "a very good implementation". AMT and ITA-Toolbox are not bold; their pages say that they are widely used toolboxes that also include some psychoacoustic functions. | `super_project`, `highlight` |
| 2026-10-07 | The bold setting is hidden: the words "super project" never appear, and "most" is not used ("most widely used"). | all pages |
| 2026-10-07 | sottek-hearing-model shows the owner's own check: very good agreement with HEAD acoustics ArtemiS SUITE in personal use. | `maintainer_check` |
| 2026-10-07 | Group order everywhere: established, newly released, developing, legacy (then others and status unknown). | all lists |
| 2026-10-07 | Newly released projects are "not yet seen to be widely used in the community". | everywhere |
| 2026-10-07 | The kind "Library/Toolbox" (so that MATLAB users recognise their toolboxes). | kinds |
| 2026-10-07 | Mosqito.NET and ITA-Toolbox are listed; a group "Status unknown" comes after Others (PsyTools). | data |
| 2026-10-07 | FAQ question 1, as shaped by the owner: choose by your own environment, not only the widely used projects; newer projects often check against MoSQITo or SQAT; MetaSona is in C for real-time analysis with input in chunks (confirmed by the owner with its author); pySQAT in one sentence; no sentence on Kirin Hypha's plug-in; the examples stay when projects change group. | `faq()` in `describe.py` |
| 2026-10-07 | Home lead, *owner's text*: "Find an open-source method to calculate psychoacoustic metrics such as loudness, sharpness, roughness and tonality, one that you can trust and that best fits your coding environment, whether Python, MATLAB, C/C++, Rust, Julia or another language. Each implementation is listed under the edition of the standard or model it follows, with the validation it reports, so that you can judge whether its results are credible. The chart below shows which projects implement which edition." The description for search engines starts "Find an open-source method you can trust …". | `home()` in `render_html.py` |
| 2026-10-07 | On the timeline, the line of years stands out more than the table borders, and no border cuts it. | Home |
| 2026-10-07 | For AI opens with, *owner's text*: "This page is for AI agents, crawlers and LLMs that read the list on someone's behalf. Humans are welcome too: it lists the same data in forms that are easy to retrieve, parse and quote." | `ai_guide()` in `describe.py` |
| 2026-10-07 | The About page opens with the owner's texts `about_lead` and `about_story` (*owner's text*), including "renewed monthly". | `data/site.yaml` |
| 2026-10-07 | Wherever the site gives the update frequency it says "monthly", although Refresh runs twice a month while the list is young. | site |
| 2026-10-07 | Updates are short. | `data/updates.yaml` |
| 2026-10-07 | Dark mode is switched off (kept in the code). | `dark_mode` in `data/site.yaml` |
| 2026-10-07 | Cloudflare Web Analytics with the owner's token; visits by bots, including AI agents, are not excluded. | `data/site.yaml` |
| 2026-10-07 | The repository description and topics are set by the owner. | GitHub |
| 2026-10-08 | Data and text under CC BY 4.0, code under MIT. | `LICENSE`, `LICENSE-DATA`, About |
| 2026-10-08 | Ported code is marked on each implementation and the project is listed as usual; no project-level "Ported code" section. | data, project pages |
| 2026-10-08 | About: no separate section on how LISQM uses AI; the current wording stays. | About |
| 2026-10-08 | The project map: drawn with Graphviz, curved lines, named "Project map", at the top of the Projects page and one level down in its sidebar. Each metric page has the map with only that metric's lines, instead of a list of who ported code from whom. | map, Projects, metric pages |
| 2026-10-08 | On the map, "A's results checked against B" points from A to B; "same contributor" (not "same maintainer") lines, backed by the `contributors` data; the lines are redrawn so that their ends are tidy. | map |
| 2026-10-08 | "Metric", never "method", also in code and data. | everywhere |
| 2026-10-08 | Plainer, less AI-sounding wording across the site; the owner's texts are not changed. | site |
| 2026-10-08 | The phone layout must not change the desktop view. | `site-src/style.css` |
| 2026-10-08 | Space at the bottom of the sidebars. | all pages |
| 2026-10-08 | The 0.4 update note was shortened; old update notes are not rewritten. | `data/updates.yaml` |
| 2026-10-08 | All "newly" tags read "new". | tags |
| 2026-10-08 | SQAT and MoSQITo stay bold (recognised in the field); iso532-3 stays as it is. | data |
| 2026-10-08 | "current" is enough: standards in force such as DIN 45631, ANSI S3.4 and NT ACOU 112 are current beside ISO editions, and the timeline draws them as current. | timeline, `data/references.yaml` |
| 2026-10-08 | "HMS" in sone_HMS and the other units is not spelled out. | units |
| 2026-10-08 | The group summaries on the Metrics page use the wording most common in the field and keep their length; change them only when they are wrong. No glossary for now. | `families` in `data/metrics.yaml` |
| 2026-10-08 | Licence tags (no licence, non-commercial, source-available) on the metric pages and the Languages page; an FAQ answer saying that a listing is not a certification. | metric pages, Languages, FAQ |
| 2026-10-08 | Not done for now: "suggest a correction" links on project pages, a change of the refresh wording, the round of phone and accessibility fixes. | – |
| 2026-10-08 | Opinions and designs are shown as previews first; concrete requested changes are pushed. Only what was asked is changed. | working rule |
| 2026-10-09 | The project map gives every line its own end on each box, in the order of the boxes at the other end, instead of meeting at one point. Same-contributor lines join every pair of projects that share a person, also beside other lines, but not beside a green line of the author's own code. | map |
| 2026-10-09 | On the project map, code from another project is "ported or adapted from another project", which names the ports; never "code taken", which sounded like taking without leave. The 0.4 update note was changed too, at the owner's request. | map, metric pages, `data/updates.yaml` |
| 2026-10-09 | On the home timeline, each standard or paper links to its entry on the Standards page. | Home |
| 2026-10-09 | Every project map, the whole map and those of the metric pages, also draws the projects that no line joins, as boxes without lines under "no relation recorded". | map, Projects, metric pages |
| 2026-10-09 | On the whole map, the smaller groups (AMT's and iso532-3's) are under the largest group, and the projects that no line joins are in rows under the map, not in a column. | map, Projects |
| 2026-10-09 | One reading width for all text, legends, bylines and notes included (option B of three previews); only tables, the timeline and the maps are wider. | every page |
| 2026-10-09 | Version 0.5.0 takes in all the changes of 2026-10-09, also those made after it was first tagged: the 0.5 update note lists them, at the owner's request. The tag `v0.5.0` stays on its first commit. | `data/updates.yaml` |
| 2026-10-09 | Versions keep their numbers (`data/site.yaml`, `CITATION.cff`, an update note) and are only pushed: no tags or GitHub releases. The owner will make one release, for version 1.0. | versions, GitHub |
| 2026-10-10 | The maps of the metric pages also put the projects that no line joins in rows, not in a column: under the columns of the map, or side by side from the left when that takes fewer rows; a single box stays where it was. | metric pages |
| 2026-10-09 | An open pull request is tagged "PR", whose meaning is clear; the value in the data stays `proposed`. Code merged but not released stays "unreleased". | tags, Markdown twins |
| 2026-10-09 | HEAD acoustics ArtemiS SUITE, a reference in psychoacoustics, is named wherever a project compared its results with it, never as "commercial software": SQAT's validation pages name it (and its version) in their source. | `compared_with` |
| 2026-10-09 | Search: a field in the tab bar on desktop and a filter above the tables of the Projects page; on phones (and tablets) a Search button that opens a dialog. | every page, Projects |
| 2026-10-06 – 2026-10-09 | Versions 0.1 (2026-10-06), 0.2 and 0.3 (2026-10-07), 0.4 (2026-10-08), 0.5 (2026-10-09). The owner creates the tags and releases. | `version`, GitHub |
