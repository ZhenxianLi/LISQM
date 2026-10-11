# Exploratory suggestions: before and while you write a psychoacoustic metric function

> **Exploratory suggestions, a draft for discussion.** This document collects first ideas on what to do when
> developing a function that computes a psychoacoustic metric. It is not a standard, not a requirement and not a
> recommendation of any project. Many points still need discussion with the people who develop and use these tools,
> and they may change. It is not published on the LISQM website. Comments and disagreements are welcome in an
> [issue](https://github.com/ZhenxianLi/LISQM/issues).

A working checklist for anyone about to implement a loudness, sharpness, roughness, fluctuation strength, tonality
or similar function, either as a pull request to an existing toolbox or in a new package.

The examples come from the records of LISQM (data as of 2026-10-10): what the listed projects state about their
own code, their issues and their validation. They show where real implementations went wrong or became hard to
trust. They are not a judgement of those projects, most of which documented these points themselves.

---

## The short version

Before coding

- [ ] Name the exact standard or paper, its **edition**, and the clauses you implement.
- [ ] Name the exact **quantity**: which output of the standard, which variant, which weighting.
- [ ] List every **convention that changes the numbers** and decide each one.
- [ ] Check the **existing implementations** of the same edition, their validation and their open issues.
- [ ] If you contribute to a project, check that its maintainers **answer**, and open an issue before the code.
- [ ] Check the **licences** of everything you might read or port; decide your own.
- [ ] If you port or adapt code, note the exact **version** (release and commit) and the exact **files and
      functions** you take, and keep that note up to date.
- [ ] Get the standard legally, and check what you may **redistribute** from it (usually nothing).

While coding

- [ ] Input in pascals, with an explicit calibration; units on every output.
- [ ] Defaults are the standard's; every other choice is a named parameter.
- [ ] Clause and equation numbers in the comments.
- [ ] A written list of every **departure** from the printed text, with the reason.

Before calling it done

- [ ] All test signals of the standard pass, with **numbers** reported against the tolerances.
- [ ] Compared with an **independent** implementation of the same edition (not the code you ported).
- [ ] Real recordings and time series checked, not only single values for synthetic signals.
- [ ] Verification scripts and results in the repository; tests in CI.
- [ ] Docstring, validation page, changelog entry, citation and credits.
- [ ] Released, not only merged.

---

## 1. Pin down exactly what you implement

### Standard, edition, clauses

Write down, before any code: the document, its edition and year, and the clause numbers. Editions of the same
standard give different results, and a function that says only "ECMA-418-2" or "DIN 45681" cannot be checked.

- ECMA-418-2 had four editions in five years (2020, 2022, 2024, 2025). They give different results, and the
  current one (4th, 2025) added fluctuation strength. A tool that silently moved from one edition to the next
  changed its users' numbers: MoSQITo followed the 1st edition in versions 1.0.0–1.1.1 and the 2nd from 1.2.0.
- Recorded cases where the edition was missing or misleading:
  - MoSQITo's TNR/PR docstrings say "ECMA 418-1" without an edition, while the helper code and the bibliography
    cite ECMA-74 Annex D (17th edition, 2019).
  - MoSQITo's equal-loudness contours give no edition; the code is based on Jeff Tackett's MATLAB code for
    ISO 226:2003, which ISO 226:2023 replaced.
  - Some RefMap code comments still cite clauses of "ECMA 418-2:2022" in code that follows the 2025 edition.
  - The ITA-Toolbox tonality header cites "DIN 45681 (2002)", the draft that preceded DIN 45681:2005.
- Standards under revision: ISO 532-1, 532-2 and 532-3 have second editions at committee-draft stage since
  November 2024. Plan from the start how a new edition will be added next to the old one (section 4).

### Which quantity

One standard often defines several quantities, and implementations pick different ones under the same name.

- ECMA-418-2 loudness: Clause 5 gives the hearing model's basic loudness; from the 2nd edition on, Clause 8
  defines the loudness to report. MoSQITo and Mosqito.NET compute the Clause 5 value; the RefMap code and its
  ports compute the Clause 8 value.
- Sharpness: the DIN 45692, Aures and von Bismarck weightings give different values; Aures' depends on loudness.
  RefMap's default is Aures. Sharpness computed from another loudness model (ECMA-418-2, Moore–Glasberg) is a
  different quantity, even if it is still called sharpness.
- Model names: the psychoacoustic annoyance model usually credited to "Zwicker & Fastl" is Widmann's (1992), as
  RefMap's code and SQAT's README note. Use the original attribution and say which equations you follow.

### Conventions that change the numbers

Decide each of these explicitly, and make each one visible in the interface (section 4). The list below is what
LISQM's "Before you compare numbers" sections record for the common metrics.

| Convention | Why it matters | Example from the records |
|---|---|---|
| Sound field | Free and diffuse field give different values (ISO 532-1; ECMA-418-2 from the 3rd edition). | Most tools default to free field. |
| Calibration | Input must be pascals; tools scale files by a factor, a reference level or a full-scale level. | A wrong scaling shifts every value. |
| Sample rate | ISO 532-1 time-varying and ECMA-418-2 are defined at 48 kHz; some tools reject other rates, others resample, and resamplers differ slightly. | Osses fluctuation strength has filters for 44.1 and 48 kHz only: SQAT resamples, PsychoacousticMetrics.jl rejects. |
| Start of the signal | Filters need time to settle. | ECMA-418-2 (2025, Section 8.1.4) leaves out the first 304 ms; SQAT's `time_skip`, MetaSona's `time_skip_s`. |
| Percentiles | N5 and other percentiles depend on the method. | SQAT takes the nearest rank; MATLAB `prctile`, NumPy and Julia interpolate differently; sottek-hearing-model uses Hyndman–Fan type 7, so single values differ slightly from RefMap and SQAT. |
| Frames and hops | Time series and their percentiles change with the hop and with the last frame. | Daniel & Weber roughness works on 200 ms frames; SQAT's Aures tonality revision uses 250 ms Hann windows with a 125 ms hop. |
| Calibration constants | Nominal or adjusted factors give slightly different values. | MetaSona uses ECMA-418-2's 20 ms grid and nominal calibration factor for roughness, where SQAT uses a slightly adjusted one. |
| Weightings | Required weightings are easy to forget. | ISO/TS 20065 requires A-weighting (clause 5.3.2); one implementation does not apply it, and the ITA-Toolbox DIN 45681 code says it applies none. |

---

## 2. Look at what already exists

- **Same edition, already implemented?** Read the existing implementations of that edition: their validation, their
  open issues and their documented deviations. LISQM's metric pages list them by edition, with the evidence each
  project states.
- **Contribute or write new?** A pull request reaches existing users; a new package starts from zero users and
  splits the community. Write new code when the edition, the licence or the language is not covered.
- **Do the maintainers answer?** Look at the dates of the last replies to issues and pull requests before you
  invest weeks. As recorded, no MoSQITo maintainer has answered issues or pull requests opened since 2024, including
  bug reports on TNR/PR (#80, #81, #99) and on the ECMA-418-2 roughness low-pass filter (#92, #95); a pull request for
  ISO 1996-2 tonal audibility has waited since May 2022 and one for Aures tonality since April 2026.
- **Open an issue first.** Agree on scope, naming, edition, licence and test signals before writing code.
- **How do releases work there?** SQAT is actively developed, but several breaking fixes are on `main` and in no
  release (ISO 532-1 time-varying loudness, Aures tonality, Daniel & Weber roughness, the sound level meter time
  weighting); v1.3 and `main` give different results. Know whether your fix will reach users, and when.

---

## 3. Licences and provenance

- **What you may port depends on the licences, not on what you may read.**
  - An Apache-2.0 project (MoSQITo) cannot take GPL code (SQAT `main`, sottek-hearing-model, RefMap).
  - Code with no licence (iso532-3 `tv2018.m`) cannot be reused at all, however useful.
  - SQAT's releases up to v1.3 are CC-BY-NC-4.0 (non-commercial); its `main` branch is GPL-3.0-or-later.
- **When the licences do not fit, implement from the standard's text.** You may still compare your results with the
  GPL code: comparing is not copying.
- **Record where code comes from**: see the next subsection.
- **Choose your own licence knowingly.** Apache-2.0, BSD or MIT let any project, also a commercial one, reuse your
  code; GPL keeps derivatives open but cannot be merged into permissively licensed projects.
- **The standard itself.** ISO and DIN documents are sold; Ecma standards are free to download. Do not commit the
  text, tables or test signals of a standard unless its licence allows it; generate signals from their description
  where you can.

### When you port or adapt code: name the exact version and functions

"Ported from SQAT" or "based on MoSQITo" is not enough. Say exactly which version and which functions you took.

**Why it matters**

- **The source changes, and so do its numbers.** Two ports of the same toolbox can give different results:
  pySQAT follows SQAT v1.3, from before SQAT's September 2026 rewrite of Daniel & Weber roughness, which moved
  63 of 119 validation values up and 56 down. MetaSona, a new project, follows a later SQAT revision. Only the
  version tells a reader which numbers to expect.
- **Bugs travel with the code.** Ports of MoSQITo 1.2.1 (Mosqito.NET, Kirin Hypha) carry that version's code: a
  later fix in MoSQITo, such as the low-pass filter range in its pull request #95, reaches them only if they take it
  in. Only the version tells whether a port has a known problem or its fix.
- **Mislabels travel too.** Mosqito.NET's code comments say ISO 226:1987, while the tables it ported from MoSQITo
  follow Jeff Tackett's code for ISO 226:2003.
- **A comparison with the source checks the port only against that same version.** Name it, or the comparison
  cannot be repeated.
- **Default branches move.** sottek-hearing-model's fluctuation strength was translated from
  `acousticSHMFluctuation.m`, which its report places in the RefMap repository, but the file is not on RefMap's
  `main` branch (checked 2026-10-07). A commit hash or a permanent link would still find it.

**What to write down**

- The source project, its licence and the authors of the code.
- The exact version: the release tag if there is one, and always the commit hash, with its date. Link the files at
  that commit (a permanent link), not the default branch.
- The exact files and functions you took, and the function of yours that each one became.
- What you changed: the language, adaptations, options left out, fixes you made yourself.
- Later changes in the source that you have or have not taken in, by issue or pull request number.

**Where to write it**

- In the header or docstring of each ported file or function.
- In one central list for the whole project (a NOTICE or third-party file, or a section of the README).
- In the validation report, next to any comparison with the source.
- Update it every time you take in a newer version of the source.

**Good examples from the records**

- Kirin Hypha: a port of MoSQITo v1.2.1, naming `loudness_zwtv` and its stages.
- ZwickerLoudness.jl: its transcription reference is MoSQITo's `loudness_zwtv` at commit `d990c33f94f1`.
- MetaSona: ports SQAT revision `e6228b78` (2026-09-15), says which SQAT fixes that revision includes (#65) and
  which later fix it does not (PR #77).
- AARAE: its Daniel & Weber roughness was ported from PsySound3's `@RoughnessDW` by Ella Manor and Densil Cabrera
  (2015); SQAT's v1.x roughness then took AARAE's `roughnessDW.m` (Dik Hermes's code), adapted and verified for SQAT
  in 2023.

**A header to copy**

```text
Ported from:      <project> (<repository URL>), licence <licence>, code by <authors>
Version:          <release tag, or "not in a release">, commit <hash> (<date>)
                  <permanent link to the file at that commit>
Taken:            <file>:<function>  ->  <our function>
                  <file>:<function>  ->  <our function>
Changed:          <translated to …; adapted …; left out …; fixed …>
Upstream changes: included <#…>; not included <#…>
Compared with:    the source at the same commit; results in <validation page>
```

---

## 4. Design the interface

- **Input in pascals.** Make the calibration explicit: a single documented way to go from a file to pascals.
- **Sample rate.** If the model is defined at one rate, either reject other rates or resample, and document the
  resampler; say which in the docstring.
- **Defaults are the standard's.** Every other choice (field, binaural combination, start-up time left out,
  percentile method, frame hop, calibration constant) is a named parameter, and its value is returned with the
  result.
- **Units on every output** (sone, sone_HMS, acum, asper, asper_HMS, vacil, vacil_HMS, tu_HMS …), with the time axis
  for time series and the band axis for specific values.
- **Editions side by side.** When a new edition arrives, add it next to the old one (a separate function or an
  `edition` argument) instead of changing what an existing call returns.
- **Guards.** Check the minimum signal length (sottek-hearing-model's fluctuation strength needs at least 1.37 s)
  and empty or silent input (sottek-hearing-model fixed an empty-array bug in 0.1.14, #9).
- **Few dependencies.** `import mosqito` fails without matplotlib, which is imported but not declared (#100). Keep
  plotting optional.

---

## 5. Implement

- Follow the structure of the standard; put clause and equation numbers in the comments.
- Keep a **list of departures** from the printed text, with the reason for each. Good examples:
  sottek-hearing-model documents five departures for fluctuation strength (four equations and one interpretation of
  Section 9.1.8); phonometry (a new project) keeps an errata list of misprints it found in Clause 9 of ECMA-418-2.
- Be most careful where others went wrong (as recorded):
  - **ISO 532-1 time-varying loudness**: six deviations fixed in SQAT (#48); test signal 10 deviated by 18.14 % in
    v1.3.
  - **ECMA-418-2 roughness**: the range of a low-pass filter, which caused differences from SQAT (MoSQITo #92, #95).
  - **Aures tonality**: eight defects fixed in SQAT in September 2026 (#67), for example only one tonal component's
    level excess entered the result, and tones were removed from the wrong spectrum.
  - **Daniel & Weber roughness**: SQAT rewrote it after revised code from Dik Hermes (#65): 63 of 119 validation
    values went up and 56 down, by up to 0.155 asper; a fix to the Terhardt filter bank followed (#77).
  - **TNR/PR**: open bug reports in MoSQITo (#80, #81, #99).
- Numerics: double precision; state the filter design and the resampler; handle the first and last frames on
  purpose; make results deterministic.

---

## 6. Verify

### The evidence, from strongest to weakest

LISQM grades what projects state about their validation like this:

1. **Standard or paper data**: the test signals and target values of the standard or of the model's paper.
2. **Reference code**: the model author's own code.
3. **Comparison with another implementation**: useful when it is independent of yours.
4. **Self-tests only**: the project's own tests, with no outside reference.
5. **Not stated**.

Aim for 1 and an independent 3. Many listed rows stop at "not stated" or "outcome not stated", which leaves users
unable to judge the numbers.

### What to do

- **Run every test signal the standard provides** and report, for each: expected value, your value, deviation and
  tolerance. Check the calibration points first (1 kHz at 40 dB in free field gives 1 sone; the ECMA-418-2
  calibration signals give 1 sone_HMS, 1 tu_HMS, 1 asper_HMS and 1 vacil_HMS). Report a miss openly: one project
  states that its ECMA-418-2 loudness reads 0.984 sone_HMS at the calibration point.
- **Compare with an independent implementation of the same edition.** Agreement with the code you ported from only
  checks the port. Prefer a different lineage (for Daniel & Weber roughness, the SQAT/Hermes code and the MoSQITo
  code differ in details).
- **Use real recordings and time series**, not only single values for synthetic signals. A good example of what to
  report: sottek-hearing-model's draft fluctuation strength report gives 0.994 against 1.003 vacil_HMS for the
  calibration signal, −8 % to +12 % for the overall values of three binaural recordings against ArtemiS SUITE, and
  correlations of 0.91 to 0.998 for the time-dependent values.
- **Keep the verification in the repository**: signals (or the code that generates them), scripts and results, so
  that anyone can run it again. Comparisons kept outside the repository cannot be checked (MetaSona describes its
  comparisons with SQAT and MoSQITo that way).
- **Automate it.** Tests in CI with the standard's tolerances; regression tests that pin current results, so that an
  unintended change fails.
- **When results change on purpose, say by how much** (SQAT's note on its roughness rewrite is a good model).

---

## 7. Document

A docstring that answers:

- What: metric, standard, edition, clauses; the quantity (for example "Clause 8 loudness").
- Input: pascals, calibration, sample rate (rejected or resampled), channels.
- Options and their defaults, and which ones depart from the standard.
- Output: names, units, axes.
- Known departures from the printed text, and known limitations.
- Validation: one line, with a link to the validation page.
- References with DOI; credits for code it came from.
- A short example.

Also:

- **A validation page** per function, with the numbers from section 6.
- **A changelog** that says when results change, by how much and why.
- **An honest maturity label** (experimental, draft): MetaSona's README calls its roughness and tonality
  experimental; sottek-hearing-model marks its fluctuation strength report as a draft.
- **CITATION.cff** and the credits for any code you used.

---

## 8. Release and maintain

- **Release your fixes.** Users install releases. Fixes that stay on `main` leave users with the old numbers, and
  a README that warns against `main` while fixes sit there leaves them no good choice.
- **Publish where users install from.** sottek-hearing-model's fluctuation strength is merged but not yet on PyPI.
- **Say when results change** in the release notes, even for a patch release.
- **Answer issues, or say that the project is not maintained** in the README, so that others know to fork or move on.
- **Follow the standards.** Watch for new editions and add them next to the old ones (section 4).
- **Make the implementation easy to list correctly.** State the edition, the validation and the licence in the
  README and the docstrings. Lists such as LISQM can only record what a project says.

---

## Appendix A. A one-page specification to write before coding

```text
Function name:
Metric and quantity:           (e.g. ECMA-418-2 loudness, Clause 8 value, binaural)
Standard / paper, edition:     (e.g. ECMA-418-2:2025, 4th ed.)
Clauses and equations:
Input:                         (pascals; calibration method; channels)
Sample rate:                   (required rate; reject or resample, which resampler)
Options and defaults:          (field, start-up time left out, percentile method, frame/hop, constants)
Outputs and units:             (single values, time series, specific values)
Departures from the text:      (each with its reason)
Code it is based on:           (project, licence, release and commit, files and functions taken; what was
                               changed; later upstream fixes included or not) or "written from the standard"
Licence of this code:
Test signals and targets:      (from the standard; tolerances)
Independent comparison:        (which implementation, same edition, different lineage)
Real recordings:
Where results are published:   (validation page, scripts in the repository)
```

## Appendix B. A validation table

| Signal | Source of the target | Target | Obtained | Deviation | Tolerance | Pass |
|---|---|---|---|---|---|---|
| 1 kHz, 40 dB, free field | ISO 532-1 | 1.000 sone | | | | |
| … | | | | | | |

| Signal | Compared with (edition, version) | Overall: theirs / ours | Difference | Time series: correlation, largest difference |
|---|---|---|---|---|
| … | | | | |

## Appendix C. Sources

The examples are taken from the LISQM records of each project (project pages and metric pages at
<https://zhenxianli.github.io/LISQM/>), which cite the projects' own documentation, issues and pull requests.
Issue and pull request numbers refer to each project's own repository. Check the current state there before relying
on a detail: these records describe the situation as of 2026-10-10.

---

Developed by Zhenxian LI with assistance from Claude Code.
