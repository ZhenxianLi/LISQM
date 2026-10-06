# Security policy

This repository contains data (YAML and JSON files under `data/`), a small Python static-site generator
(`scripts/`) and the GitHub Actions workflows that refresh the data and publish the website. It does not
contain or distribute any psychoacoustic metric code; the indexed projects live in their own repositories.

## Supported versions

Only the `main` branch, and the website built from it, is supported. There are no separately maintained
releases.

## Reporting a vulnerability

Please do not report security problems in public issues or pull requests. Use GitHub's private
vulnerability reporting instead: open the repository's **Security** tab and choose
**Report a vulnerability**, or go directly to
<https://github.com/ZhenxianLi/LISQM/security/advisories/new>.

Please include what is affected (a script, a workflow, the generated website or the data), how to
reproduce the problem and what an attacker could do with it. The maintainer will reply in the advisory,
agree on a fix and publish the advisory once it is fixed. Reporters are credited unless they prefer not
to be.

Examples of what belongs here:

- data fields or fetched metadata that end up as unescaped HTML or script in the generated pages;
- workflows that could leak a token or run untrusted code with write permissions;
- a link in the index that points to a compromised repository or a malicious package.

A vulnerability in an indexed project should be reported to that project, following its own security
policy. If the problem also makes an entry in this index misleading, open a
[correction](https://github.com/ZhenxianLi/LISQM/issues/new?template=correction.yml)
once the issue is public.
