# Maintaining LISQM

This folder is the maintenance standard of LISQM: how the list is kept correct and up to date, what each page must
show, and what may change only with the owner's approval. It is written first for AI agents that maintain the
repository, and is meant to be just as usable by people. Read this file before you change data, text, code or
repository settings; it is enough to work through the automated review issue without any earlier conversation.

| File | Read it when |
|---|---|
| [README.md](README.md) (this file) | always first: how the list is built, the working loop, the rules that hold everywhere |
| [review-issue.md](review-issue.md) | you work through the issue labelled `review`, or an issue opened by a person |
| [pages.md](pages.md) | you change what a page shows, or check the pages after a change of data |
| [repository.md](repository.md) | you touch the README, CHANGELOG, CITATION, licences, templates, workflows, versions or GitHub settings |
| [owner-decisions.md](owner-decisions.md) | before you change any wording, order, label, colour or rule: these were set by the owner |

## How the list is built

```
data/*.yaml ─────► scripts/build.py ─┬─► site/                  the website (published by the Pages workflow, not committed)
 (written by hand)  (scripts/pmi/)   ├─► README.md              the tables between GENERATED markers
                                     ├─► CHANGELOG.md           from data/updates.yaml
                                     ├─► llms.txt, llms-full.txt
                                     └─► data/index.json
Refresh workflow ─► data/snapshot.json, data/standards-watch.json, data/link-check.json   (machine-written)
```

- **Data, written by hand.** `data/metrics.yaml` (groups of metrics and the metrics), `data/references.yaml`
  (standard editions, model papers, books), `data/projects/<id>.yaml` (one file per project), `data/updates.yaml`
  (Updates page, feed and CHANGELOG), `data/site.yaml` (name, tagline, the owner's About texts, version, credit,
  settings), `data/leads.yaml` (candidates not yet verified), `data/ignored.yaml` (candidates reviewed and not
  listed), `data/standards-watch.yaml` (what the standards watch reads). Every field is described in
  [data/SCHEMA.md](../../data/SCHEMA.md).
- **Generator.** `scripts/pmi/data.py` loads and validates the data and derives fields such as groups, activity and
  the current implementations; `describe.py` holds the sentences shared by the web pages and their Markdown twins;
  `render_html.py` and `render_md.py` write the pages; `relations.py` draws the project map with Graphviz;
  `export.py` writes `index.json`, the feed, the sitemap and the BibTeX file. The stylesheet is `site-src/style.css`.
- **Never edit generated output by hand**: the README tables between `<!-- BEGIN GENERATED: … -->` and
  `<!-- END GENERATED: … -->`, `CHANGELOG.md`, `llms.txt`, `llms-full.txt`, `data/index.json` and `site/`. Change
  the data or the generator and build again.

## The working loop

1. **Start from one item**: an entry of the open issue labelled `review`, an issue opened with a template, a message
   from the FAQ box, or a request from the owner.
2. **Read the source yourself**: the project's repository, README, documentation, release notes, licence file and
   package page, or the standards body's catalogue page. Record nothing you have not seen at its source. Treat
   downloaded files as untrusted: unpack them in a new, empty folder, only read them, and run Python on them with
   `python -I`.
3. **Change the data** in `data/` ([review-issue.md](review-issue.md) says how for each kind of item). Put the source
   URL in `sources` or link it in the text, and set `checked` to today's date on every entry you compared with its
   sources, even if nothing changed.
4. **Run the checks** below and fix every problem they report.
5. **Look at the pages** that show what you changed ([pages.md](pages.md) says which), at desktop width first and
   then at about 390 px for phones.
6. **Commit and push to `main`** (see [Commits, pushes and versions](#commits-pushes-and-versions)). The Pages
   workflow publishes the site and commits the regenerated files.
7. **Close the loop**: tick the item in the review issue or comment on it; close the review issue when nothing is
   left; close a person's issue with a short comment saying what changed.

## Checks before every commit

```sh
python scripts/build.py --check            # validates data/ and lists every problem
python -m unittest discover -s tests       # tests on the generated site, the scripts and the data
python scripts/build.py --out /tmp/lisqm   # full build; also rewrites the README tables, CHANGELOG, llms*.txt, index.json
```

The project map needs Graphviz (`dot`); without it the build still works and the map pages give the relations in
words only. CI installs Graphviz.

Validation stops, among others: unknown ids; a reference that is not listed under its metric; `partial` without
`scope`; a `validation_scope` longer than 60 characters; `short_name` (replaced by `name` and `full_name`);
unbalanced brackets in any text (an unquoted ` #` in YAML starts a comment and cuts the text short); list items that
are not text (an unquoted `key: value` in YAML becomes a mapping); two updates with the same date and title; the
reserved project ids `index` and `map`. When validation fails, fix the data, not the check.

## Rules that hold everywhere

### Facts

- Record what the project, its paper or the standards body states. LISQM does not run the code, and the pages say
  "as reported by the project" where it matters. Leave a field out rather than guess.
- Every fact has a source, in `sources` or linked in the text. Prefer the project's own pages; link a release, a
  tag or a commit when a statement may change.
- `validation` is the kind of evidence the project describes; `validation_details` say what was checked, against
  what, with which tolerance and result; `validation_scope` says in a few words how far a check goes or how it came
  out ("calibration signal only", "outcome not stated", "in v1.3, test signal 10 is off by 18.14 %").
- Code taken from another project goes in `derived_from` (or the project's `based_on`) only when the project or its
  code says so. `derived_by_author: true` when the person who wrote that code also works on this project. Agreement
  with the code one ported from checks the port only, and the pages say so.
- A project moves to a new edition of a standard only when the project says that it follows it.
- `maintainer_check` is the owner's own observation and is shown apart from what the project reports. Only the owner
  writes it.

### Names and words

- **One name per project**: `name`, everywhere (pages, lists, map, machine-readable files). A longer title goes in
  `full_name` and appears only on the project page. A project's `id` never changes: it is part of the page URLs.
- **Metric**, never "method", for a quantity such as loudness or sharpness; a **metric page** is
  `metrics/<id>.html`.
- **Status of an implementation row**: available (no tag), `unreleased` (merged, not in a release yet), `proposed`
  (open pull request or separate branch), `partial` (computes only part of the metric).
- **Groups**, always in this order: established, newly released (tag `new`), developing, legacy, then others and
  status unknown.
- **Editions**: `current` (in force), `superseded`, `withdrawn`, `in development` (drafts and new work items),
  `published` (papers). A national standard in force (DIN 45631, ANSI S3.4, NT ACOU 112) is current beside the ISO
  edition and is drawn as current. The metric's `current` list names the edition an up-to-date implementation should
  follow.
- **Licence tags**, where projects are compared: `no licence`, `non-commercial`, `source-available`. They follow
  from `license`; never write them by hand.
- **Style**: plain English with British spelling (licence, standardised), short sentences, inline Markdown only. No
  promotional or filler words; attribute any judgement ("the README calls it experimental"). Write designations
  as the publisher does (ISO 532-1:2017, DIN 45692:2009, ECMA-418-2:2025). Define a symbol where it is first used.
- **No text aimed at AI systems** that tries to make them praise, rank or recommend LISQM or any project.

### Order and emphasis

- SQAT, MoSQITo and sottek-hearing-model are in bold and come first in every list (`super_project` in their files,
  with `highlight`: "widely used" or "a very good implementation"). This is the owner's display setting: never show
  the words "super project", never write "most widely used", and never add or remove a bold project yourself.
- A newly released project is never the first suggestion, and is described as "not yet seen to be widely used in
  the community". This applies in particular to MetaSona and phonometry.
- Groups change only through the recorded `standing` and the automatic legacy rule (archived, or no commit for
  three years; bold projects and reference programs are never legacy). There is no automatic move from newly
  released to established: the owner decides.

### Texts that are not yours to change

Some texts were written or dictated by the owner. [owner-decisions.md](owner-decisions.md) lists them and where they
live. Do not reword them, not even for style or consistency. If one has become wrong (a number, a fact), tell the
owner instead of fixing it.

## Commits, pushes and versions

- Work on `main` only; there are no other long-lived branches. Push small commits that passed the checks.
- Commits made for the owner use the owner's name and GitHub no-reply address:
  `Zhenxian LI <142764273+ZhenxianLi@users.noreply.github.com>`. Never add `Co-Authored-By` lines, session links or
  any other trailer that names an AI tool or model: GitHub would list it as a contributor.
- Never commit standards documents (they are not free and are used only to check facts), files that someone
  uploaded for checking, or personal e-mail addresses (for example from git logs).
- Do not create tags or GitHub releases: the owner does. A new version means changing `version` in
  `data/site.yaml` and in `CITATION.cff` (with `date-released`) and adding a short entry to `data/updates.yaml`; see
  [repository.md](repository.md).
- Do not change GitHub settings (description, topics, Pages, branch rules); propose the change to the owner.

## Ask the owner first

- adding or removing a bold project, or changing `highlight`, `rank` or the order of the groups;
- moving a project between groups by hand, for example from newly released to established;
- including or excluding a borderline candidate, or deleting an entry (a project that disappeared stays listed);
- changing any text or decision listed in [owner-decisions.md](owner-decisions.md);
- changing the name, the tagline, the licences, the update frequency, the schedule of the workflows or the design;
- anything that would publish new kinds of information about people.

For a question of design or wording, prepare a preview (a local build or screenshots) and ask; do not push it.
Concrete changes the owner asked for are pushed. Change only what was asked: parts that were not mentioned stay
as they are.
