# Working through the review issue

The Refresh workflow ([`.github/workflows/refresh.yml`](../../.github/workflows/refresh.yml)) runs at 05:17 UTC on
the 1st and the 15th of every month, and by hand from Actions → Refresh → Run workflow. It:

1. commits routine metadata (last commits, versions, releases, archived flags, descriptions) to `main` without
   review, in `data/snapshot.json`, and rebuilds the generated files;
2. looks for new candidates, watches the standards and checks every link;
3. writes only what needs a person into one open issue labelled `review`, titled `Review: <date>`. The body is
   replaced at each run and a comment is added, so the latest body is the current list. Nothing is posted when
   there is nothing to review;
4. publishes the website and submits it to search engines.

The issue has four sections: *Repository and package metadata*, *New candidates*, *Standards* and *Links*. For every
item: open the source, decide, change the data, run the checks in [README.md](README.md), commit, then tick the item
or comment on it. When an item cannot be settled (the source is unreachable, or the decision belongs to the owner),
comment what is missing and leave the issue open. Close the issue when nothing is left.

## Repository and package metadata

| The issue says | What to do |
|---|---|
| licence *A* → *B*; check `license` | Open the licence file in the repository and the package metadata. Set `license` to the SPDX expression, or `none` when there is no licence file. Explain anything unusual in `license_note`: licences that disagree, files under their own licences, a different licence for the releases and for the default branch (as for SQAT). The tags `no licence`, `non-commercial` and `source-available` follow from `license`. |
| a release; check whether its `unreleased` or `proposed` implementations are in this release | Read the release notes, or compare the release tag with the commit that added the code. For each row now in a release: `status: available` and `since: <version>`; remove notes such as "on `main` only"; check that `validation_details` and `validation_scope` still describe the released code. Rows that are not in the release stay as they are. A `proposed` row whose pull request was merged becomes `unreleased`, or `available` once released. |
| `owner/repo` is now `owner2/repo2`; update `repository` | Update `repository`, and the same URL in `sources`, `docs`, `homepage`, `packages` and in the text. Keep the project `id`. |
| failed twice in a row | Open the URL. A moved repository: as above. A host that is down: leave it and say so in the issue. A repository that is gone or private: do not delete the entry; tell the owner (it may move to *status unknown*, with `access`, `access_note` and `claim`). For code hosted outside GitHub, the dates come from `manual` (last commit, latest release, archived): update them by hand. |

Everything else in the metadata (new commits, versions, archiving) was committed already and needs nothing. A
project that reaches three years without a commit becomes legacy automatically; check that its page still reads
well, and leave its `standing` as it is.

## New candidates

[`scripts/discover.py`](../../scripts/discover.py) searches GitHub, crates.io and npm, and leaves out forks, listed
projects, entries of `data/ignored.yaml` and projects without activity in the last three years.

1. **Read the candidate's README and code**, and apply the inclusion rules in
   [CONTRIBUTING.md](../../CONTRIBUTING.md#what-the-list-includes): public source that computes the metric itself,
   says which model or standard (and edition) it follows, and computes at least one quantity in scope. A wrapper is
   listed (with `via`) only when it is an end-user application or an established library. Out of scope: broadcast
   loudness (LUFS, ITU-R BS.1770, EBU R128), speech intelligibility, codec quality metrics, software for listening
   tests, music dissonance models, feature extractors that follow no named model, closed-source tools.
2. **Decide**:
   - **Include it**: copy a complete entry such as `data/projects/metasona.yaml` to `data/projects/<id>.yaml`
     (`id` in lowercase kebab-case, equal to the file name). Fill in the required fields and one `implements` row
     per metric and edition, with `functions`, `validation` and `validation_details` in the project's own words,
     `derived_from` when it says where its code comes from, and `conventions` that change its numbers.
     `standing`: `newly-released` for a project first released less than about a year ago, with a `standing_note`
     saying when; `developing` for code public for more than a year without a publication or documented use by
     others; `established` only with a publication, documented use by others, or authorship by the model's
     authors. Never set `super_project`, `highlight` or `rank`: these are the owner's.
   - **Do not include it**: add it to `data/ignored.yaml` with `url`, `reason` and `checked`, so that discovery
     does not report it again.
   - **It cannot be checked** (host unreachable, download behind a form): add it to `data/leads.yaml` with `name`,
     `url`, `claim`, `why` and `checked`. The About page lists leads as unverified, never as facts.
   - **Borderline**: write down the reasons for and against in the issue and ask the owner.
3. When projects were added, add one short dated entry to `data/updates.yaml` for the batch.

## Standards

[`scripts/watch_standards.py`](../../scripts/watch_standards.py) reads ISO's open data and the Ecma pages listed in
`data/standards-watch.yaml`.

- **A new ISO deliverable or a stage change.** The number in the ISO data (for example "ISO 86954") is an iso.org
  project id, not a standard number: use the designation that the iso.org page shows (for example ISO/AWI 26573)
  and link that page. Decide whether the document belongs to a listed metric; a work item on a related topic (for
  example procedures for listening tests) is not the next edition of a metric.
- **A draft or a new work item** of a listed metric: add it to `data/references.yaml` with `kind: draft`,
  `status: in-development` and the stage in `revision`. On the edition it will replace, set `superseded_by` to the
  new id, keeping `status: current` until the new one is published. Add the id to the metric's `references` in
  `data/metrics.yaml`, in date order.
- **A published edition**: `status: current`, `date`, `url`; the old edition `status: superseded` (or `withdrawn`);
  in `data/metrics.yaml`, the new id replaces the old one in the metric's `current`. Do not move any project to the
  new edition unless the project says that it follows it.
- **A national standard in force** beside an ISO edition (DIN, ANSI, Nordtest) stays `status: current`; it is drawn
  as current on the timeline.
- **"The text of the page changed; the matched strings did not"**: open the page; usually nothing changed for the
  list. If a watched page moved, update `data/standards-watch.yaml`.
- Check every designation, date and edition number at the standards body's own catalogue page: standards are easy
  to misnumber. Never download or commit the documents themselves.

## Links

[`scripts/check_links.py`](../../scripts/check_links.py) checks every URL in the data. A 404, a 410 or an unknown
host is reported at once; other failures only when they repeat.

- Find the new address (the project moved, the documentation was reorganised) and replace the URL everywhere it is
  used.
- When there is no new address, link an archived copy (`https://web.archive.org/…`) if it shows the same content;
  otherwise remove the link and keep the fact only if another source supports it.
- A site that refuses automated requests (often 403 from a standards body) is a false alarm when the page opens in
  a browser: leave the link.

## Issues opened by people

- **Add a project** (label `new-project`): as for new candidates. Thank the person and say in the issue what was
  added, or why not.
- **Correction** (label `correction`): check the claim at its source, change the data, set `checked`, and reply with
  what changed. An author correcting their own entry is welcome; the source still has to say it.
- **Standard edition** (label `standards`): as in [Standards](#standards).
- **Messages from the FAQ box** (prefilled issues): answer from the data and the sources; turn requests into data
  changes as above; pass questions about the list itself to the owner.
- Replies are short, factual and friendly. Never promise a ranking, a bold place or an endorsement.

## When everything is done

- Run the checks in [README.md](README.md), build, and look at the pages that changed.
- Commit with a message that says what changed and why, for example "MetaSona 0.3.0 released: ECMA-418-2 rows
  available".
- After the push, the Pages workflow publishes the site and commits the regenerated files. Check that its run
  succeeded, then close the review issue.
