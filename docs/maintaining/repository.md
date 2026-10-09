# Repository standards

What the GitHub repository shows besides the website, who changes it, and how.

## Settings on GitHub

These are set in the repository settings, not in files, and only the owner changes them. Propose a change in an
issue or to the owner; do not change them yourself. Current values:

| Setting | Value |
|---|---|
| Repository | `ZhenxianLi/LISQM` |
| Description | "LISQM: List of Implementations of Sound Quality Metrics. A living list of open-source implementations of psychoacoustic and sound quality metrics, tracked by standard edition and refreshed twice a month." |
| Website | https://zhenxianli.github.io/LISQM/ |
| Topics | acoustics, awesome-list, awesome-lists, ecma-418-2, fluctuation-strength, iso-532-1, loudness, nvh, psychoacoustic-metrics, psychoacoustics, roughness, sharpness, signal-processing, sound-quality, tonality |
| Social preview | `assets/social-preview.png`, drawn from `assets/social-preview.svg` with the tagline as subtitle; uploaded by the owner. The build also copies it into the site for link previews. |
| Branches | `main` only; delete any other branch after it is merged (Dependabot's are temporary) |
| Pages | source: GitHub Actions |
| Releases and tags | only for version 1.0, made by the owner; earlier versions are only pushed (one old tag, `v0.5.0`) |
| Comments | none on the website; the FAQ message box opens an issue |

When the name, the tagline or the scope changes, the description, the topics and the social preview may need to
follow: list what to change for the owner.

## Files on the repository page

| File | Standard |
|---|---|
| `README.md` | Generated parts sit between `<!-- BEGIN GENERATED: key -->` and `<!-- END GENERATED: key -->` (stats, overview, gaps, coverage, projects): never edit them; the build rewrites them. Everything else is written by hand: the title and tagline, the bright website badge (the main way from GitHub to the site), the introduction, the credit line, the data links and badges, "Why this list exists", the introduction to the overview, the paragraph on groups after the projects table, "How it is maintained", "Using the data", "Contributing", "Citing" and "Licence". When a hand-written part repeats the data (the names of the bold projects, the update frequency, the licences), update it in the same commit as the data. English only. |
| `CHANGELOG.md` | Generated from `data/updates.yaml`; never edit it. |
| `CITATION.cff` | The owner is the only author. `version` equals `version` in `data/site.yaml` (a test checks), `date-released` is the date of that version, `license: CC-BY-4.0`, and `message` ends with the credit line. LISQM has no DOI and does not need one. |
| `LICENSE`, `LICENSE-DATA` | MIT for the code (`scripts/`, `site-src/`, `tests/`); CC BY 4.0 for the data and the text. Versions up to 0.3.0 were MIT as a whole (the README and the About page say so). Change only with the owner. |
| `CONTRIBUTING.md` | Inclusion rules, how to propose, correct and report, writing rules, local checks, the automation and the review process. Keep it in step with `data/SCHEMA.md` and the validation in `scripts/pmi/data.py`. |
| `data/SCHEMA.md` | Every field of the data and what it means. Change it in the same commit as a new or changed field. |
| `CODE_OF_CONDUCT.md`, `SECURITY.md` | Stable; change only with the owner. |
| `AGENTS.md`, `CLAUDE.md`, `docs/maintaining/` | These standards. Change them in the same commit as a change of practice; record new owner decisions in `owner-decisions.md`. |
| `.github/ISSUE_TEMPLATE/` | Forms for adding a project, a correction and a standard edition; `config.yml` keeps blank issues and links to the website and the schema. |
| `.github/pull_request_template.md` | The checklist for pull requests. |
| `requirements.txt` | Python packages for the build. Graphviz is installed by the workflows. |

Labels: `review` (the automated review issue), `new-project`, `correction` and `standards`. The Refresh workflow
creates them when they are missing.

## Versions and releases

- Versions follow semantic versioning: `0.Y.0` for a version with new pages or features, `0.Y.Z` for corrections.
  The owner decides when to make a version.
- A version is prepared in one commit: `version` in `data/site.yaml`; `version` and `date-released` in
  `CITATION.cff`; an entry "Version 0.Y: <what is new>" at the top of `data/updates.yaml`, short.
- That commit is only pushed: no tag and no GitHub release. The one release the owner plans is version 1.0, which
  the owner creates. The tag `v0.5.0` (on the first commit of that version) stays as it is. Agents do not create or
  push tags.

## Workflows

| Workflow | Runs | Does |
|---|---|---|
| CI (`ci.yml`) | pull requests, and pushes to branches other than `main` | validation, tests and a full build |
| Pages (`pages.yml`) | pushes to `main` that touch `data/`, `scripts/`, `site-src/`, `assets/`, the README or `requirements.txt`; by hand; called by Refresh | builds the site, commits the regenerated files, deploys to GitHub Pages |
| Refresh (`refresh.yml`) | 05:17 UTC on the 1st and the 15th of every month; by hand | commits the metadata refresh, then discovery, standards watch, link check, the review issue, Pages and search engines |
| Search engines (`indexnow.yml`) | after Refresh; by hand | submits the pages in the sitemap to IndexNow |
| Dependabot (`dependabot.yml`) | monthly | proposes newer versions of the actions; merge when CI passes |

The site says the list is renewed "monthly" while Refresh runs twice a month: the owner wants it more active while
the list is young, and will move the schedule to once a month later. Then change only the `cron` line, and the
GitHub description.

The workflows commit as `github-actions[bot]`, and only generated files and machine-written data
(`data/snapshot.json`, `data/standards-watch.json`, `data/link-check.json`). Everything that describes a project,
a metric or an edition is changed by a person or an agent working for the owner.

## Services outside GitHub

- **Website**: GitHub Pages, https://zhenxianli.github.io/LISQM/.
- **Analytics**: Cloudflare Web Analytics; the token is `cloudflare_analytics_token` in `data/site.yaml` (it is
  public in every page). Visits by bots are kept in the counts, because the owner wants to see visits by AI agents.
- **Search engines**: the Google verification tag is under `verification` in `data/site.yaml`; IndexNow (Bing,
  Yandex and others) uses `indexnow_key`, whose key file the build publishes. After a large change, run the Search
  engines workflow by hand.
