<!--
Thank you for contributing. CONTRIBUTING.md explains the inclusion criteria and the writing rules,
and data/SCHEMA.md describes every field. One project per pull request is preferred.
-->

## What this changes

<!-- For example: "Adds data/projects/example.yaml" or "Corrects the ISO 532-1 edition implemented by example".
     Link a related issue with "Closes #123". -->

## Checklist

- [ ] Every new or changed fact has a source URL (in `sources`, or as a link in the text).
- [ ] `checked` is set to the date I checked each entry I edited.
- [ ] `python scripts/build.py --check` passes.
- [ ] The wording is neutral and factual: it records what the project or the standard states, without judging it.
- [ ] One project per pull request (or a short note above on why several are changed together).
- [ ] I did not edit generated output by hand (`data/index.json`, `llms.txt`, `llms-full.txt`, `CHANGELOG.md`, the generated README tables).

<!-- If you are an author or maintainer of a project you add or change, please say so above. -->
