# Page standards

What each page of the website is for, where its content comes from, and what must stay true. The pages are
generated: change the data (or the generator), never the HTML. Every web page has a Markdown twin (`.md`) with the
same content, so a change to what a page shows is made in both `render_html.py` and `render_md.py`, and, where it
applies, in `llms.txt` and `llms-full.txt` (written by `render_md.py`).

After any change, build the site and look at the pages listed under *Check* for the page concerned, at desktop
width first and then at about 390 px.

## On every page

- **Masthead and tabs.** LISQM, the tagline (`tagline` in `data/site.yaml`), the logo, and the tabs Home, Metrics,
  Projects, Languages, Standards, FAQ, Updates, For AI and About; the current tab is marked. The logo is the only
  tribute to the owner's laboratory: no text names it.
- **Search.** A field at the right end of the tab bar; where the tabs leave no room for it (about 1025 to 1150 px)
  it folds to a magnifier and opens over the tabs while in use. Below 64rem a Search button at the right of the
  masthead opens the same search in a dialog, which fills the screen on phones. `site-src/search.js` looks through
  `search.json` in the browser: metrics, standards and papers, projects (with their languages and the maintainers
  named on their pages), function names and page sections, all built from the data by `scripts/pmi/search.py`.
  Results come in groups, metrics first unless another group matches better, function names last. "/" starts a
  search. Shown only when JavaScript runs (the `js` class); not on the error page. Every entry must lead to a page
  and an anchor that exist (a test checks this). *Check* the field at about 1280 and 1100 px and the dialog at
  390 px after a change to the masthead or the tabs.
- **Sidebar.** Each tab has its own sidebar with the content of that tab: the sections of the page, or the metrics,
  projects, standards or updates of the tab. A group that holds a single metric of the same name is one heading
  that links to the metric. Each entry appears once. The sidebar ends with empty space, so that its last line can
  be scrolled into view.
- **Footer.** The credit line from `data/site.yaml`, word for word: "Developed by Zhenxian LI with assistance from
  Claude Code." (a test checks every page, the README, the llms files and CITATION.cff), the licences (data and
  text CC BY 4.0, code MIT) and the date of the data.
- **One vocabulary of tags.** Groups: `new`, `developing`, `legacy`. Rows: `unreleased`, `PR`, `partial`.
  Licences: `no licence`, `non-commercial`, `source-available`. Evidence tags name what was compared ("compared
  with MoSQITo"), grey when the comparison is with related code. Names in bold are the projects with
  `super_project`.
- **Design.** Plain, blog-like pages in the green of the masthead, with colour where it helps reading; no rounded
  cards or decorative boxes. All text (paragraphs, lists, legends, bylines, notes) has one reading width
  (`--measure`), so that it ends at the same right edge; only tables, the timeline and the maps are wider, and the
  text inside them follows their width. The desktop layout is the reference: styles for narrow screens (below
  40rem) must not change the desktop view. Dark mode exists in the code but is off (`dark_mode: false`); keep it
  off.
- **Links and anchors.** Internal links are relative and must resolve (a test checks every link and anchor).
  Keep the anchors of sections stable: other sites link to them.
- **Machine-readable parts.** JSON-LD (`schema.org`) in every page, the Markdown twin, the sitemap, the feed. The
  Cloudflare analytics snippet appears only when `cloudflare_analytics_token` is set; search-engine verification
  tags are on the home page only.

## Home (`index.html`)

The first answer to "which open-source code implements which edition of each metric?". Built by `home()`.

- The heading is the tagline; the byline (date and counts) is generated.
- **Lead**: the owner's text in `home()` ("Find an open-source method to calculate psychoacoustic metrics …").
  Do not reword it. The page description for search engines ("Find an open-source method you can trust …") is also
  the owner's.
- **Editions and implementations** (the timeline) comes first. Columns are periods of years; each edition or model
  paper sits in the column of its year, with the projects that implement it. A green box is a current edition,
  including national standards in force; grey is a superseded or withdrawn edition or an earlier model paper; drafts
  carry `in development`. Each label links to the document's entry on the Standards page. At most four projects per edition, the most established first; "+N more" opens the rest
  in place. Marks: `new` and `dev` after the name, a grey name for legacy, `unreleased` and `PR` tags. The
  line of years stays more visible than the borders of the table, and no border cuts it.
- **Gaps**: the metrics without an available implementation of the current edition, then those whose only released
  implementations come from newly released projects. Generated from the data.
- **Recent updates**: the newest entries of `data/updates.yaml`, linked by their anchors.
- **Contribute**: how to propose a project or a correction.
- *Check* after a new edition, a new project, a change of status or group.

## Metrics (`metrics/index.html`)

Built by `metrics_page()`.

- The lead and a key: the language codes and the tags used in the lists.
- One section per group of metrics (`families` in `data/metrics.yaml`) with a short summary. Summaries use the
  wording most common in the field and keep their length; change one only when it is wrong.
- A table: the metric and its unit, the current edition (`current`), and the projects that implement it, with their
  tags. Rows that compute only part of a metric (`partial`) are not counted.
- *Check* after a change to a metric, an edition or a row.

## Metric pages (`metrics/<id>.html`)

Built by `metric_page()` from the metric in `data/metrics.yaml`, its editions in `data/references.yaml` and the
`implements` rows of the projects.

- Title, other names (`aka`: other names for the same metric only; a value taken from it, such as N5, is not one),
  unit, summary and notes. Define every symbol where it is first used.
- **The answer first**: the current edition and its implementations by language, a caution when only newly
  released projects implement it, then earlier editions and related models.
- **Editions and who implements them**: each edition with its date, status, what changed (`revision`) and its
  implementations.
- **Project map**, before the implementations: the map with only the lines of this metric's rows, each naming the
  edition, and only between projects listed for this metric (a link to another project stays on the whole map). The
  metric's projects that no line joins are boxes without lines in rows under the rest, below the words "no relation
  recorded", as on the whole map; a single one stays in the first column. There is no such section when the metric
  has no relation.
- **Implementations**: one row per project and edition. Project and languages; edition with `scope` and `since`;
  functions; validation (the evidence tag, `validation_scope` under it, "also compared with …"); notes (group tag,
  licence tag, `unreleased`, `PR` or `partial`, the project it is computed by or uses, the row's `note`).
- **How they were validated**: as reported by each project. The owner's own check (`maintainer_check`) appears
  apart, under the project's first entry.
- **Before you compare numbers**: the metric's `conventions`, then the projects' (their rows' conventions, and the
  project conventions that hold for this metric; a project convention with `metrics` appears only on those pages).
- **References**.
- *Check* after any change to a row, an edition or a convention of the metric.

## Projects (`projects/index.html`)

Built by `projects_page()`.

- A paragraph on the order of the lists first (the bold projects are named from the data).
- Then the full project map, with its legend above it, and a line pointing to the map page.
- **Filter projects**: a field above the tables (JavaScript only) that hides the rows that do not match its words,
  and the groups left empty, and says how many projects are shown. It reads the text of each row: name, kind,
  languages, licence, release, activity and metrics.
- One table per group (established, newly released, developing, legacy, others, status unknown): project and kind,
  languages, licence, latest release, last commit and activity, and what it covers (metrics, with `unreleased`,
  `PR` or `partial` where no row of that metric is available).
- *Check* after a new project, a change of group, licence, release or rows.

## Project pages (`projects/<id>.html`)

Built by `project_page()` from `data/projects/<id>.yaml` and the snapshot.

- The heading is `name`, with tags for kind, group and activity, then the summary: what the project is and what it
  computes, neutrally.
- **Facts**: full name (when there is one), repository, homepage, documentation, languages, kind (with its meaning),
  group (with the standing note), licence (with `license_note`), packages, install command, latest release, last
  commit, stars, maintainers, AI assistance (only as disclosed by the project), paper, how to cite, the date the
  entry was checked. The licence is given here, not as a tag.
- **What it implements**, **How it was validated** (with the owner's `maintainer_check` where there is one),
  **Before you compare numbers** (the project's conventions), **Notes**, **Before you rely on it** (`caveats`: known
  problems, with links), **Sources**.
- A project whose code cannot be opened shows *Status unknown*, its `access_note` and `claim`, and is not listed
  under the metrics.
- *Check* after any change to the project's file, and after a refresh that changed its release or activity.

## Project map (`projects/map.html`)

Drawn at build time by Graphviz (`scripts/pmi/relations.py`) from the `implements` rows; the fields are described
in `data/SCHEMA.md`. Built by `map_page()`.

- **Kinds of line**: ported or adapted from another project (black arrow; never "taken", which sounds like taking
  without leave); the author's own code (green arrow, `derived_by_author`); used at run time (dotted arrow, `uses`);
  results checked against another project (dashed blue arrow, `compared_with`); same contributor (grey line without an
  arrow: a name in `maintainers` or `contributors` of both projects; drawn also beside a line of another kind, but not
  beside a green line, which already says that the same person is involved).
- **Direction**: sources stand on the left, and an arrow points from the source to the project that uses it. A
  check points from the project to the one it checked its results against: "A's results checked against B" is
  drawn A → B. Every line has an end of its own: it leaves a box on its right side and enters the next box on its
  left side, and the ends are ordered by the box at the other end (the map is laid out twice for this), so lines
  neither share an end nor cross where they meet a box. A box with many lines grows taller. A grey line between
  boxes of the same column joins them directly.
- **Boxes**: bold for the bold projects, faded for legacy projects, dashed for programs published with a standard
  or a paper. The largest group of joined boxes is on top, the smaller groups (such as AMT's) under it. Projects
  that no line joins are boxes without lines in rows under the lowest box or line of the columns they take, below
  the words "no relation recorded": a box under each column of the map, or side by side from the left when that
  takes fewer rows. Each box links to its page; each line has a tooltip naming the metrics (on a metric page, the
  editions).
- **In words**: the same relations as text, the projects drawn without a line, and those left out because their
  code could not be opened.
- `contributors` holds people with code of their own in a project, taken from its commit history or documentation;
  never e-mail addresses. When a contributor of both projects wrote the code that was ported or adapted, mark the row
  with `derived_by_author` (a test checks this).
- *Check* the picture after any change to `derived_from`, `based_on`, `derived_by_author`, `uses`, `compared_with`,
  `maintainers` or `contributors`: no label covered, no line through a box, the arrows in the right direction.

## Languages (`languages.html`)

Built by `languages_page()`.

- **Coverage by language**: for each metric and language column, ● an available implementation of the current
  edition, ◐ the same but only from newly released projects, ○ only unreleased, proposed, older-edition or partial
  implementations, — none. A library with bindings counts for every language it can be called from.
- One section per language: the project with its group and licence tags; how it is used (language of the
  computation, interfaces, install command, `language_note`, `based_on`); the current editions it implements, with
  `partial` where it applies.
- **Calling code across languages**: general routes (the MATLAB Engine API for Python, Octave, C interfaces …).
  Keep it general and correct; name projects only as examples.

## Standards (`standards.html`)

Built by `standards_page()`.

- Every entry of `data/references.yaml`: standards and regulations, then model papers, books and theses, each with
  status, date, link or DOI and the metrics that use it. The sidebar lists each document once.
- Each row carries the id `ref-<id>`: links from the Home timeline, the metric pages and the maps open the page at
  that row, which is marked in light yellow (also near the end of the page, where it cannot reach the top).
- `references.bib` holds all of them as BibTeX (generated).
- Standards are not free: link the publisher's catalogue page; never host or commit a copy.

## FAQ (`faq.html`)

Built by `faq()` in `describe.py`, so that the numbers in the answers stay true.

- The message box comes first. It opens a prefilled GitHub issue; there is no comment system on the page.
- At most eight questions.
- Question 1 ("Which code should I use …") was shaped by the owner. Keep its points: choose by your own environment;
  the widely used projects come first but are not the only choice; newer projects often check their results
  against MoSQITo or SQAT; MetaSona is a C library written for fast, real-time analysis, with a rolling analyser for
  audio that arrives in chunks; pySQAT in one sentence. The examples stay when their projects change group.
- The last question says that a listing is not a certification, and that a report for an authority follows the
  edition the regulation or contract names.

## Updates (`updates.html`)

Built by `updates_page()` from `data/updates.yaml`, newest first; the same entries make the Atom feed and
`CHANGELOG.md`.

- Each entry has an anchor made from its date and the first words of its title; two entries of one day need
  different titles.
- Short: a sentence or two and a few bullets, saying what changed for a reader rather than how it was done.
- Never rewrite old entries, even when the site's wording has changed since: they record what was said then.

## For AI (`ai.html`)

Built from `ai_guide()` in `describe.py`.

- It opens with the owner's sentence: "This page is for AI agents, crawlers and LLMs that read the list on someone's
  behalf. Humans are welcome too: it lists the same data in forms that are easy to retrieve, parse and quote."
- Then the entry points (llms.txt, llms-full.txt, index.json, the Markdown twins, the feed, the BibTeX file), what
  the data contains, how to answer questions with it, how it is kept accurate, and how to cite it.
- Facts only. Nothing that asks AI systems to praise or recommend LISQM.

## About (`about.html`)

Built by `about_page()`.

- It opens with the owner's texts `about_lead` and `about_story` in `data/site.yaml`. Do not edit them; "renewed
  monthly" stays although the workflow runs twice a month.
- Then: what is included, how entries are checked, status of an implementation, validation evidence, groups of
  projects, kinds of project, leads not yet verified, machine-readable data, contributing, citing and licence. The
  sidebar lists every section.
- There is no separate section on how LISQM uses AI: the credit line says it.

## Error page (`404.html`)

Links back to the home page and the tabs. It has no Markdown twin and no search: it is served from any path, so
the search could not find its files.
