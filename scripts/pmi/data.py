"""Load, validate and enrich the list data in data/.

The YAML files are the source of truth (see data/SCHEMA.md). data/snapshot.json holds metadata fetched by
scripts/refresh.py. Everything derived here (activity, latest release, per-method implementation lists) is
recomputed on every build and never written back to the YAML files.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

import yaml

from .text import date_str

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

# What a project is, for someone who wants to use it: its name and what it means.
PROJECT_KINDS = {
    "library": "Library/Toolbox",
    "research-code": "Research code",
    "application": "Application",
    "plugin": "Plug-in",
    "reference-program": "Reference program",
}
KINDS = {
    "library": "Functions to call from your own code: a Python package, a MATLAB toolbox, or a C, C++, C#, Rust or "
               "Julia library.",
    "research-code": "Code published with a study, a thesis or a student project, to run or adapt; not packaged as a "
                     "library.",
    "application": "A program to run, with a graphical or command-line interface; no programming needed.",
    "plugin": "Runs inside other software: a plug-in for an audio workstation, or a Pure Data external.",
    "reference-program": "Code published with a standard or by the authors of the model, as the reference for it.",
}
IMPL_STATUS = {
    "available": "available",
    "unreleased": "unreleased",
    "proposed": "proposed",
}
IMPL_STATUS_LONG = {
    "available": "In the latest release, or on the default branch of a project without releases.",
    "unreleased": "Merged on the default branch but newer than the latest release.",
    "proposed": "Open pull request or separate branch, not merged.",
}
VALIDATION = {
    "standard-data": "standard or paper data",
    "reference-code": "reference code",
    "cross-implementation": "compared with another implementation",
    "self-tests": "own tests only",
    "not-stated": "not stated",
}
VALIDATION_LONG = {
    "standard-data": "Compared with test signals or values published in the standard or the model paper.",
    "reference-code": "Compared with the reference program or the model authors' own code.",
    "cross-implementation": "Compared with another implementation, named where the project says which. Agreement "
                            "shows that both compute the same values, not that either follows the standard.",
    "self-tests": "Tests exist, but without external reference data.",
    "not-stated": "The project does not say how it was validated.",
}
REF_KINDS = {
    "standard", "technical-specification", "publicly-available-specification", "amendment", "draft",
    "paper", "book", "thesis", "regulation", "method",
}
REF_STATUS = {
    "current": "current",
    "superseded": "superseded",
    "withdrawn": "withdrawn",
    "in-development": "in development",
    "published": "published",
}
REGISTRIES = {
    "pypi": ("PyPI", "https://pypi.org/project/{name}/"),
    "crates": ("crates.io", "https://crates.io/crates/{name}"),
    "npm": ("npm", "https://www.npmjs.com/package/{name}"),
    "julia": ("Julia General", "https://juliahub.com/ui/Packages/General/{name}"),
    "cran": ("CRAN", "https://cran.r-project.org/package={name}"),
    "conda-forge": ("conda-forge", "https://anaconda.org/conda-forge/{name}"),
    "file-exchange": ("MATLAB File Exchange", ""),
    "other": ("package", ""),
}
AI_ASSISTANCE = {"disclosed", "not-stated"}
# A port's record of how it credits each source it ports (`ported_from` in the project file).
PORTED_KEYS = {"source", "authors", "license", "credit", "checked"}
# Licence terms that bind code derived from the source: copyleft (the GPL family) and non-commercial.
BINDING_TERMS = {"copyleft": re.compile(r"GPL"), "non-commercial": re.compile(r"CC-BY-NC")}
STATUS_ORDER = {"available": 0, "unreleased": 1, "proposed": 2}
STANDING = {
    "established": "Described in a publication, used by others, or written by the authors of the model, with more "
                   "than a year of history.",
    "newly-released": "First released less than about a year ago, and not yet seen to be widely used in the community.",
    "developing": "Public for more than a year, but without a publication or documented use by others: research, "
                  "teaching or personal code.",
}
# Every project is in exactly one group, decided in this order: status unknown (its code cannot be opened), others
# (it computes nothing itself), legacy (archived, or no commit for `legacy_after_days`, except super
# projects and reference programs, which are not expected to change), then the standing recorded in the project file.
# Every list uses the order of GROUPS.
GROUPS = {
    "established": STANDING["established"],
    "newly-released": STANDING["newly-released"],
    "developing": STANDING["developing"],
    "legacy": "Archived, or no commit for three years or more. Kept for reference: the code may follow an older "
              "edition and may not run with current software.",
    "others": "Tools that do not compute the metrics themselves: interfaces, front ends and wrappers that call one "
              "of the listed projects.",
    "unknown": "Projects whose code could not be opened, for example because the repository needs a login. What "
               "they implement is unverified, so they are listed with what they claim and not under the metrics.",
}
GROUP_ORDER = {key: n for n, key in enumerate(GROUPS)}
# The meta tag each search engine's webmaster tools look for on the home page to verify the site.
VERIFICATION_META = {"google": "google-site-verification", "bing": "msvalidate.01",
                     "baidu": "baidu-site-verification", "yandex": "yandex-verification"}

GROUP_NAMES = {"established": "established", "developing": "developing", "newly-released": "newly released",
               "legacy": "legacy", "others": "other", "unknown": "status unknown"}
# Why a project's code cannot be checked (`access` in its file); such a project is in the group "unknown".
ACCESS = {"restricted": "The repository cannot be opened without a login."}
ACTIVITY_ORDER = {"active": 0, "unknown": 1, "inactive": 2, "archived": 3}


def super_order(p: dict) -> tuple[int, int]:
    """(0, n) for the n-th super project, (1, 0) for every other project. Super projects (`super_project` in the
    project file) are the maintainer's display setting: shown in bold, with their `highlight`, and first in their group, which is
    always established, so they head every list."""
    return (0, int(p["super_project"])) if p.get("super_project") else (1, 0)


def project_rank(p: dict) -> int:
    """A project's place within its group, set by the maintainer (1 first); unranked projects follow."""
    return int(p.get("rank") or 999)


def project_tier(p: dict) -> int:
    """Within a group, after the super projects: ranked projects that are still active first, then ranked but
    inactive ones, then other active projects, then the rest."""
    active = p.get("_activity") == "active"
    if p.get("rank"):
        return 0 if active else 1
    return 2 if active else 3


def impl_rank(impl: dict) -> tuple:
    """The order of implementations everywhere: always by group first (established, newly released, developing,
    legacy); within a group the super projects first, then released code before unreleased before proposed, then
    active, ranked projects (see `project_tier`)."""
    p = impl["_project"]
    return (GROUP_ORDER[p["_group"]], *super_order(p), STATUS_ORDER[impl["status"]], project_tier(p),
            project_rank(p), 1 if impl.get("_via") else 0, p["name"].lower())


def only_new(m: dict) -> bool:
    """True when every released implementation of a method's current edition comes from a newly released project."""
    released = [i for i in m["_current_impls"] if i["status"] == "available"]
    return bool(released) and all(i["_project"]["standing"] == "newly-released" for i in released)


def keeps_terms(source_license: str | None, port_license: str) -> bool:
    """False when the licence of the ported code is copyleft (GPL family) or non-commercial and the port has no
    licence or one without those terms. It only compares licence names: it says that the conditions of the source
    apply, not whether they are met."""
    binding = [rule for rule in BINDING_TERMS.values() if rule.search(source_license or "")]
    if not binding:
        return True
    return port_license not in ("none", "unknown") and all(rule.search(port_license) for rule in binding)


def derived_sources(p: dict) -> list[str]:
    """The code a project ports, in order: every row's `derived_from`, else the project's `based_on` (a row computed
    by another project ports nothing)."""
    out: list[str] = []
    for impl in p.get("implements") or []:
        ids = impl.get("derived_from") or ([p["based_on"]] if p.get("based_on") and not impl.get("via") else [])
        out += [c for c in ids if c not in out]
    return out


_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_DATE = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")


class DataError(Exception):
    """Raised when the data does not validate; carries the list of problems."""

    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


def _load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalise_url(url: str) -> str:
    u = url.strip().lower().rstrip("/")
    u = re.sub(r"^http://", "https://", u)
    u = u.replace("://www.", "://")
    return re.sub(r"\.git$", "", u)


def github_slug(url: str | None) -> str | None:
    m = re.match(r"^https?://(?:www\.)?github\.com/([^/]+)/([^/#?]+)", url or "")
    return f"{m.group(1)}/{re.sub(r'.git$', '', m.group(2))}" if m else None


class Index:
    """All list data plus lookups and derived fields (keys starting with '_' are derived)."""

    def __init__(self, root: Path = ROOT):
        data = root / "data"
        self.root = root
        self.site: dict = _load_yaml(data / "site.yaml") or {}
        metrics = _load_yaml(data / "metrics.yaml") or {}
        self.families: list[dict] = metrics.get("families") or []
        self.methods: list[dict] = metrics.get("methods") or []
        self.references: list[dict] = _load_yaml(data / "references.yaml") or []
        self.projects: list[dict] = []
        self.project_files: dict[str, Path] = {}
        for path in sorted((data / "projects").glob("*.yaml")):
            p = _load_yaml(path) or {}
            self.projects.append(p)
            self.project_files[str(p.get("id"))] = path
        self.updates: list[dict] = (_load_yaml(data / "updates.yaml") or []) if (data / "updates.yaml").exists() else []
        self.ignored: list[dict] = (_load_yaml(data / "ignored.yaml") or []) if (data / "ignored.yaml").exists() else []
        self.leads: list[dict] = (_load_yaml(data / "leads.yaml") or []) if (data / "leads.yaml").exists() else []
        snap_path = data / "snapshot.json"
        self.snapshot: dict = json.loads(snap_path.read_text(encoding="utf-8")) if snap_path.exists() else {}

        self.family = {f.get("id"): f for f in self.families}
        self.method = {m.get("id"): m for m in self.methods}
        self.ref = {r.get("id"): r for r in self.references}
        self.project = {p.get("id"): p for p in self.projects}

    # ------------------------------------------------------------------ validation

    def validate(self) -> list[str]:
        problems: list[str] = []
        add = problems.append

        for key in ("name", "title", "tagline", "description", "base_url", "repository", "maintainer", "license",
                    "credit"):
            if not self.site.get(key):
                add(f"data/site.yaml: missing '{key}'")
        if self.site.get("base_url") and not str(self.site["base_url"]).endswith("/"):
            add("data/site.yaml: base_url must end with '/'")
        key = self.site.get("indexnow_key")
        if key is not None and not re.fullmatch(r"[A-Za-z0-9-]{8,128}", str(key)):
            add("data/site.yaml: indexnow_key must be 8 to 128 letters, digits or hyphens")
        token = str(self.site.get("cloudflare_analytics_token") or "")
        if token and not re.fullmatch(r"[A-Za-z0-9]{16,64}", token):
            add("data/site.yaml: cloudflare_analytics_token must be the token of the snippet (letters and digits)")
        unknown = set(self.site.get("verification") or {}) - set(VERIFICATION_META)
        if unknown:
            add(f"data/site.yaml: verification: unknown search engine {', '.join(sorted(unknown))} "
                f"(known: {', '.join(VERIFICATION_META)})")

        def check_ids(items: list[dict], where: str) -> None:
            seen: set[str] = set()
            for i, item in enumerate(items):
                ident = item.get("id")
                if not isinstance(ident, str) or not _ID.match(ident):
                    add(f"{where}[{i}]: id {ident!r} must be lowercase kebab-case")
                elif ident in seen:
                    add(f"{where}: duplicate id '{ident}'")
                seen.add(str(ident))

        def check_date(value: Any, where: str, required: bool = True) -> None:
            if value in (None, ""):
                if required:
                    add(f"{where}: missing date")
                return
            if not _DATE.match(date_str(value)):
                add(f"{where}: date {value!r} must be YYYY, YYYY-MM or YYYY-MM-DD")

        check_ids(self.families, "data/metrics.yaml: families")
        check_ids(self.methods, "data/metrics.yaml: methods")
        check_ids(self.references, "data/references.yaml")
        for f in self.families:
            for key in ("name", "summary"):
                if not f.get(key):
                    add(f"data/metrics.yaml: family '{f.get('id')}' missing '{key}'")

        for m in self.methods:
            w = f"data/metrics.yaml: method '{m.get('id')}'"
            for key in ("family", "name", "title", "summary", "unit", "references", "current"):
                if not m.get(key):
                    add(f"{w}: missing '{key}'")
            if m.get("family") and m["family"] not in self.family:
                add(f"{w}: unknown family '{m['family']}'")
            conventions = m.get("conventions")
            if conventions is not None and not (isinstance(conventions, list) and conventions
                                                and all(isinstance(c, str) and c.strip() for c in conventions)):
                add(f"{w}: conventions must be a non-empty list of strings")
            for rid in m.get("references") or []:
                if rid not in self.ref:
                    add(f"{w}: unknown reference '{rid}'")
            for rid in m.get("current") or []:
                if rid not in (m.get("references") or []):
                    add(f"{w}: current '{rid}' is not in its references")
            for mid in m.get("see_also") or []:
                if mid not in self.method:
                    add(f"{w}: see_also '{mid}' is not a method")

        for r in self.references:
            w = f"data/references.yaml: '{r.get('id')}'"
            for key in ("label", "kind", "body", "title", "status"):
                if not r.get(key):
                    add(f"{w}: missing '{key}'")
            if r.get("kind") and r["kind"] not in REF_KINDS:
                add(f"{w}: kind '{r['kind']}' not one of {sorted(REF_KINDS)}")
            if r.get("status") and r["status"] not in REF_STATUS:
                add(f"{w}: status '{r['status']}' not one of {sorted(REF_STATUS)}")
            if not (r.get("url") or r.get("doi") or r.get("citation")):
                add(f"{w}: needs a url, doi or citation")
            check_date(r.get("date"), w, required=r.get("status") != "in-development")
            if r.get("superseded_by") and r["superseded_by"] not in self.ref:
                add(f"{w}: superseded_by '{r['superseded_by']}' is not a reference")
            if not any(r.get("id") in (m.get("references") or []) for m in self.methods):
                add(f"{w}: not used by any method")

        repos: dict[str, str] = {}
        super_places: dict[int, str] = {}
        check_ids(self.projects, "data/projects")
        for p in self.projects:
            pid = p.get("id")
            path = self.project_files.get(str(pid))
            w = f"data/projects/{path.name if path else pid}"
            if path and path.stem != pid:
                add(f"{w}: id '{pid}' must match the file name")
            required = ["name", "repository", "languages", "kind", "license", "summary", "ai_assistance",
                        "standing", "sources", "checked"]
            if p.get("access"):  # code that cannot be opened: what it claims instead of what it implements
                if p["access"] not in ACCESS:
                    add(f"{w}: access must be one of {sorted(ACCESS)}")
                required += ["access_note", "claim"]
                if p.get("implements"):
                    add(f"{w}: a project whose code cannot be opened lists a claim, not implements")
            else:
                required.append("implements")
            for key in required:
                if not p.get(key):
                    add(f"{w}: missing '{key}'")
            conventions = p.get("conventions")
            if conventions is not None and not (isinstance(conventions, list) and conventions
                                                and all(isinstance(c, str) and c.strip() for c in conventions)):
                add(f"{w}: conventions must be a non-empty list of strings")
            if p.get("maintainer_check") is not None and not (isinstance(p["maintainer_check"], str)
                                                              and p["maintainer_check"].strip()):
                add(f"{w}: maintainer_check must be a non-empty string")
            cite = p.get("cite")
            if cite is not None:
                if not isinstance(cite, dict) or not set(cite) <= {"doi", "cff", "text"}:
                    add(f"{w}: cite takes doi, cff and text")
                elif cite.get("doi") and not re.fullmatch(r"10\.\d{4,9}/\S+", str(cite["doi"])):
                    add(f"{w}: cite.doi must look like 10.xxxx/…")
                elif cite.get("cff") and not str(cite["cff"]).startswith("https://"):
                    add(f"{w}: cite.cff must be the https URL of the CITATION.cff file")
            if p.get("kind") and p["kind"] not in PROJECT_KINDS:
                add(f"{w}: kind '{p['kind']}' not one of {sorted(PROJECT_KINDS)}")
            if p.get("standing") and p["standing"] not in STANDING:
                add(f"{w}: standing must be one of {sorted(STANDING)}")
            if p.get("standing") == "newly-released" and not p.get("standing_note"):
                add(f"{w}: a newly released project needs a standing_note (when it was first released)")
            if p.get("standing") == "developing" and p.get("paper"):
                add(f"{w}: a project described in a publication (paper) is established, not developing")
            if p.get("rank") is not None and (not isinstance(p["rank"], int) or p["rank"] < 1):
                add(f"{w}: rank must be a positive whole number")
            place = p.get("super_project")
            if place is not None:
                if not isinstance(place, int) or isinstance(place, bool) or place < 1:
                    add(f"{w}: super_project must be a positive whole number (its place among the super projects)")
                elif place in super_places:
                    add(f"{w}: super_project {place} is also given to {super_places[place]}")
                else:
                    super_places[place] = pid
                if p.get("rank"):
                    add(f"{w}: a super project is ordered by super_project; remove rank")
                if p.get("standing") != "established" or p.get("access"):
                    add(f"{w}: a super project must be established, so that it heads every list")
                if not p.get("highlight"):
                    add(f"{w}: a super project needs a highlight, the short label shown with it (e.g. widely used)")
            elif p.get("highlight"):
                add(f"{w}: highlight is only for a super project")
            if p.get("based_on") and p["based_on"] not in self.project:
                add(f"{w}: based_on '{p['based_on']}' is not a project id")
            if p.get("core") and p["core"] not in (p.get("languages") or []):
                add(f"{w}: core must be one of its languages")
            if p.get("ai_assistance") and p["ai_assistance"] not in AI_ASSISTANCE:
                add(f"{w}: ai_assistance must be one of {sorted(AI_ASSISTANCE)}")
            if not isinstance(p.get("languages", []), list):
                add(f"{w}: languages must be a list")
            check_date(p.get("checked"), f"{w}: checked")
            repo = p.get("repository")
            if repo:
                if not str(repo).startswith("https://"):
                    add(f"{w}: repository must be an https URL")
                key = normalise_url(str(repo))
                if key in repos:
                    add(f"{w}: repository already used by '{repos[key]}'")
                repos[key] = str(pid)
            for j, pkg in enumerate(p.get("packages") or []):
                if pkg.get("registry") not in REGISTRIES:
                    add(f"{w}: packages[{j}].registry must be one of {sorted(REGISTRIES)}")
                if not pkg.get("name"):
                    add(f"{w}: packages[{j}] missing name")
            manual = p.get("manual") or {}
            check_date(manual.get("last_commit"), f"{w}: manual.last_commit", required=False)
            if manual.get("latest_release"):
                check_date(manual["latest_release"].get("date"), f"{w}: manual.latest_release.date", required=False)
            seen_pairs: set[tuple] = set()
            for j, impl in enumerate(p.get("implements") or []):
                wi = f"{w}: implements[{j}]"
                mid, rid = impl.get("method"), impl.get("reference")
                if mid not in self.method:
                    add(f"{wi}: unknown method '{mid}'")
                elif rid not in (self.method[mid].get("references") or []):
                    add(f"{wi}: reference '{rid}' is not listed for method '{mid}'")
                if impl.get("status") not in IMPL_STATUS:
                    add(f"{wi}: status must be one of {sorted(IMPL_STATUS)}")
                if impl.get("validation") not in VALIDATION:
                    add(f"{wi}: validation must be one of {sorted(VALIDATION)}")
                if impl.get("functions") is not None and not isinstance(impl["functions"], list):
                    add(f"{wi}: functions must be a list")
                if impl.get("via") and impl["via"] not in self.project:
                    add(f"{wi}: via '{impl['via']}' is not a listed project")
                if impl.get("via") == pid:
                    add(f"{wi}: via must name another project")
                for key in ("compared_with", "validation_details", "derived_from", "conventions"):
                    value = impl.get(key)
                    if value is not None and not (isinstance(value, list) and value
                                                  and all(isinstance(v, str) and v.strip() for v in value)):
                        add(f"{wi}: {key} must be a non-empty list of strings")
                if pid in (impl.get("compared_with") or []):
                    add(f"{wi}: compared_with must name other implementations")
                if pid in (impl.get("derived_from") or []):
                    add(f"{wi}: derived_from must name another project or code")
                pair = (mid, rid, impl.get("status"), impl.get("scope"))
                if pair in seen_pairs:
                    add(f"{wi}: duplicate of an earlier entry")
                seen_pairs.add(pair)
            # A port records how it credits each source it ports, one entry per source.
            ported = derived_sources(p)
            credited: set[str] = set()
            entries = p.get("ported_from")
            if entries is not None and not (isinstance(entries, list) and entries):
                add(f"{w}: ported_from must be a non-empty list")
                entries = []
            for j, e in enumerate(entries or []):
                we = f"{w}: ported_from[{j}]"
                if not isinstance(e, dict) or not set(e) <= PORTED_KEYS:
                    add(f"{we}: takes {', '.join(sorted(PORTED_KEYS))}")
                    continue
                src = e.get("source")
                if not src:
                    add(f"{we}: missing 'source'")
                elif src in credited:
                    add(f"{we}: '{src}' is recorded twice")
                elif src not in ported:
                    add(f"{we}: '{src}' is not in based_on or any derived_from")
                credited.add(str(src))
                if not (isinstance(e.get("credit"), str) and e["credit"].strip()):
                    add(f"{we}: credit must say where the port names the source, or be 'none'")
                authors = e.get("authors")
                if authors is not None and not (isinstance(authors, list) and authors
                                                and all(isinstance(a, str) and a.strip() for a in authors)):
                    add(f"{we}: authors must be a non-empty list of names")
                if e.get("license") is not None and not (isinstance(e["license"], str) and e["license"].strip()):
                    add(f"{we}: license must be the licence of the ported code")
                check_date(e.get("checked"), f"{we}: checked")
            for src in ported:
                if src not in credited:
                    add(f"{w}: ported_from has no entry for '{src}' (how the port credits that code)")

        for i, u in enumerate(self.updates):
            w = f"data/updates.yaml[{i}]"
            check_date(u.get("date"), w)
            for key in ("title", "body"):
                if not u.get(key):
                    add(f"{w}: missing '{key}'")
        for i, lead in enumerate(self.leads):
            for key in ("name", "url", "claim", "why"):
                if not lead.get(key):
                    add(f"data/leads.yaml[{i}]: missing '{key}'")
            if lead.get("url") and normalise_url(lead["url"]) in repos:
                add(f"data/leads.yaml[{i}]: {lead['url']} is already a listed project")
        for i, ig in enumerate(self.ignored):
            if not ig.get("url") or not ig.get("reason"):
                add(f"data/ignored.yaml[{i}]: needs url and reason")
            elif normalise_url(ig["url"]) in repos:
                add(f"data/ignored.yaml[{i}]: {ig['url']} is also a listed project")
        return problems

    # ------------------------------------------------------------------ derived data

    def as_of(self) -> str:
        """The date the data was last refreshed or checked (keeps builds reproducible)."""
        dates = [date_str(p.get("checked")) for p in self.projects]
        dates += [date_str(r.get("checked")) for r in self.references if r.get("checked")]
        dates += [date_str(u.get("date")) for u in self.updates]
        gen = (self.snapshot.get("generated") or "")[:10]
        if gen:
            dates.append(gen)
        return max(d for d in dates if d) if any(dates) else dt.date.today().isoformat()

    def enrich(self) -> None:
        as_of = dt.date.fromisoformat(self.as_of())
        inactive_after = int(self.site.get("inactive_after_days", 365))
        legacy_after = int(self.site.get("legacy_after_days", 1095))
        snap_projects = self.snapshot.get("projects") or {}

        for m in self.methods:
            m["_impls"] = []
            m["_via_impls"] = []
            m["_family"] = self.family.get(m.get("family"), {})
        for r in self.references:
            r["_methods"] = [m for m in self.methods if r["id"] in (m.get("references") or [])]
            r["_impls"] = []

        for p in self.projects:
            snap = snap_projects.get(p["id"]) or {}
            gh = snap.get("github") or {}
            manual = p.get("manual") or {}
            p["_github"] = github_slug(p.get("repository"))
            p["_stars"] = gh.get("stars")
            p["_archived"] = bool(gh.get("archived", manual.get("archived", False)))
            p["_last_commit"] = gh.get("last_commit") or date_str(manual.get("last_commit")) or None

            releases = []
            if gh.get("latest_release"):
                lr = gh["latest_release"]
                releases.append({"version": lr.get("tag"), "date": lr.get("date"), "source": "GitHub release"})
            prerelease = None
            for pkg in p.get("packages") or []:
                ps = (snap.get("packages") or {}).get(f"{pkg['registry']}:{pkg['name']}") or {}
                if ps.get("version"):
                    releases.append({"version": ps["version"], "date": ps.get("date"),
                                     "source": REGISTRIES[pkg["registry"]][0]})
                if ps.get("prerelease"):
                    prerelease = ps["prerelease"]
            if not releases and manual.get("latest_release"):
                lr = manual["latest_release"]
                releases.append({"version": str(lr.get("version")), "date": date_str(lr.get("date")),
                                 "source": lr.get("source", "")})
            releases = [r for r in releases if r.get("version")]
            p["_release"] = max(releases, key=lambda r: r.get("date") or "") if releases else None
            p["_prerelease"] = prerelease

            age = (as_of - dt.date.fromisoformat(p["_last_commit"][:10])).days if p["_last_commit"] else None
            if p["_archived"]:
                p["_activity"] = "archived"
            elif age is not None:
                p["_activity"] = "active" if age <= inactive_after else "inactive"
            else:
                p["_activity"] = "unknown"
            p["_super"] = bool(p.get("super_project"))  # bold and first everywhere; see super_order()
            p["_legacy"] = (p["standing"] != "newly-released" and not p["_super"] and p["kind"] != "reference-program"
                            and (p["_archived"] or (age is not None and age >= legacy_after)))

            # How the port credits each source it ports, with the authors and the licence of that code (the source
            # project's maintainers and licence unless the entry names the authors or licence of the code ported).
            p["_ported_from"] = []
            for e in p.get("ported_from") or []:
                src = self.project.get(e["source"])
                licence = e.get("license") or (src["license"] if src else None)
                p["_ported_from"].append({
                    "source": e["source"], "name": src["name"] if src else e["source"], "project": src,
                    "authors": list(e.get("authors") or (src.get("maintainers") if src else None) or []),
                    "license": licence, "credit": None if e["credit"].strip() == "none" else e["credit"],
                    "checked": date_str(e["checked"]), "terms_differ": not keeps_terms(licence, p["license"])})
            credit = {e["source"]: e for e in p["_ported_from"]}

            p["_impls"] = []
            for impl in p.get("implements") or []:
                impl = dict(impl)
                impl["_project"] = p
                impl["_method"] = self.method[impl["method"]]
                impl["_ref"] = self.ref[impl["reference"]]
                impl["_via"] = self.project.get(impl.get("via"))
                # What it was compared with, and the code it was ported or adapted from (the row's
                # `derived_from`, else the project's `based_on`; a row computed by another project ports nothing):
                # listed projects by id, anything else by name.
                named = lambda ids: [(self.project[c]["name"], self.project[c]) if c in self.project else (c, None)
                                     for c in ids]  # noqa: E731
                impl["_compared"] = named(impl.get("compared_with") or [])
                impl["_derived_ids"] = impl.get("derived_from") or (
                    [p["based_on"]] if p.get("based_on") and not impl.get("via") else [])
                impl["_derived"] = named(impl["_derived_ids"])
                impl["_ported"] = [credit[c] for c in impl["_derived_ids"] if c in credit]
                # What to check before comparing its numbers: the project's general points, then the row's own.
                impl["_conventions"] = list(dict.fromkeys((p.get("conventions") or []) + (impl.get("conventions") or [])))
                p["_impls"].append(impl)
                if impl["_via"]:  # the computation is done by another listed project
                    self.method[impl["method"]]["_via_impls"].append(impl)
                    continue
                self.method[impl["method"]]["_impls"].append(impl)
                self.ref[impl["reference"]]["_impls"].append(impl)
            # Tools whose results all come from other listed projects are listed under "Others".
            p["_others"] = bool(p["_impls"]) and all(i["_via"] for i in p["_impls"])
            p["_group"] = ("unknown" if p.get("access") else "others" if p["_others"] else
                           "legacy" if p["_legacy"] else p["standing"])

        self._relate_comparisons()

        for m in self.methods:
            order = {rid: i for i, rid in enumerate(m.get("references") or [])}

            # The group comes before everything, so a newly released or legacy project never heads a list; within
            # a group the super projects come first, then the newest editions.
            def method_rank(i: dict, order: dict = order) -> tuple:
                return (GROUP_ORDER[i["_project"]["_group"]], *super_order(i["_project"]), -order[i["reference"]],
                        *impl_rank(i)[3:])
            m["_impls"].sort(key=method_rank)
            m["_via_impls"].sort(key=impl_rank)
            # Every row, including those computed by another project, in the same order (validation, ports).
            m["_all_impls"] = sorted(m["_impls"] + m["_via_impls"], key=method_rank)
            current = set(m.get("current") or [])
            m["_current_impls"] = [i for i in m["_impls"] if i["reference"] in current]
            m["_older_impls"] = [i for i in m["_impls"] if i["reference"] not in current]
            m["_languages"] = sorted({lang for i in m["_current_impls"] if i["status"] == "available"
                                      for lang in i["_project"]["languages"]})
        for p in self.projects:
            p["_impls"].sort(key=lambda i: (self.methods.index(i["_method"]),
                                            -(i["_method"]["references"].index(i["reference"]))))

    def _relate_comparisons(self) -> None:
        """Mark the comparisons that are not independent checks: with the code a row was ported from ("source"),
        with a port of it ("port"), or with another port of the same code ("shared", naming that code). Ports are
        followed through the rows of the same method, so that a port of a port still counts."""
        rows: dict[tuple[str, str], list[dict]] = {}
        for p in self.projects:
            for impl in p["_impls"]:
                rows.setdefault((p["id"], impl["method"]), []).append(impl)

        def sources(pid: str, mid: str, seen: frozenset) -> list[str]:
            """Listed projects whose code for this method the project's code comes from, nearest first."""
            out: list[str] = []
            for impl in rows.get((pid, mid), []):
                for c in impl["_derived_ids"]:
                    if c in self.project and c not in seen and c not in out:
                        out.append(c)
                        out += [a for a in sources(c, mid, seen | {c}) if a not in out]
            return out

        for p in self.projects:
            for impl in p["_impls"]:
                mid, own = impl["method"], []
                for c in impl["_derived_ids"]:
                    if c in self.project and c not in own:
                        own += [c] + [a for a in sources(c, mid, frozenset({p["id"], c})) if a not in own]
                if impl.get("via"):  # computed by another listed project: what it is compared with is that code
                    own += [impl["via"]] + [a for a in sources(impl["via"], mid, frozenset({p["id"]}))
                                            if a not in own]
                me = {p["id"], impl.get("via")} - {None}
                relation: dict[str, tuple[str, dict | None]] = {}
                for c in impl.get("compared_with") or []:
                    if c not in self.project:
                        continue
                    theirs = sources(c, mid, frozenset({c}))
                    if c in own:
                        relation[c] = ("source", None)
                    elif me & set(theirs):
                        relation[c] = ("port", None)
                    elif shared := [a for a in theirs if a in own]:
                        relation[c] = ("shared", self.project[shared[0]])
                impl["_relation"] = relation

    # ------------------------------------------------------------------ queries used by renderers

    def families_with_methods(self) -> list[tuple[dict, list[dict]]]:
        return [(f, [m for m in self.methods if m.get("family") == f["id"]]) for f in self.families]

    def projects_by_group(self) -> list[dict]:
        """All projects by group (established, newly released, developing, legacy, others, status unknown); within
        each group the super projects first, then ranked and active projects."""
        return sorted(self.projects, key=lambda p: (GROUP_ORDER[p["_group"]], *super_order(p), project_tier(p),
                                                    project_rank(p), p["name"].lower()))

    def group(self, key: str) -> list[dict]:
        return [p for p in self.projects_by_group() if p["_group"] == key]

    def others(self) -> list[dict]:
        """Tools that do not compute the metrics themselves but call another listed project."""
        return self.group("others")

    def super_projects(self) -> list[dict]:
        """The super projects (bold and first everywhere), in their order (`super_project` in the project file)."""
        return sorted((p for p in self.projects if p["_super"]), key=super_order)

    def languages(self) -> list[str]:
        return sorted({lang for p in self.projects for lang in p.get("languages") or []}, key=str.lower)

    def gaps(self) -> list[dict]:
        """Methods whose current edition has no available open implementation."""
        return [m for m in self.methods
                if not any(i["status"] == "available" for i in m["_current_impls"])]

    def new_only(self) -> list[dict]:
        """Methods whose current edition has released implementations only from newly released projects."""
        return [m for m in self.methods if only_new(m)]


def load(root: Path = ROOT) -> Index:
    index = Index(root)
    problems = index.validate()
    if problems:
        raise DataError(problems)
    index.enrich()
    return index
