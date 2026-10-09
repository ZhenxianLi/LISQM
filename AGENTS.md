# Notes for AI agents

LISQM is a static website generated from the YAML files in `data/`. Before you change anything, read
[docs/maintaining/README.md](docs/maintaining/README.md): how the list is built and kept up to date, how to work
through the automated review issue, what each page must show, how the GitHub repository is kept, and which
decisions belong to the owner.

The essentials:

- Change the data in `data/` (fields in [data/SCHEMA.md](data/SCHEMA.md)), never the generated files: the README
  tables, `CHANGELOG.md`, `llms.txt`, `llms-full.txt`, `data/index.json`, `site/`.
- Every fact has a source. LISQM records what projects and standards bodies state; it does not run their code.
- Before committing: `python scripts/build.py --check`, `python -m unittest discover -s tests`, a full build, and a
  look at the changed pages.
- Commit to `main` only, as the owner, with no co-author or other trailer naming an AI tool. Do not create tags or
  releases, and do not change GitHub settings.
- What is listed in [docs/maintaining/owner-decisions.md](docs/maintaining/owner-decisions.md) changes only when
  the owner asks.
