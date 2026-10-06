"""Load, validate and enrich the index data in data/.

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

PROJECT_KINDS = {
    "library": "Library",
    "toolbox": "Toolbox",
    "research-code": "Research code",
    "reference-program": "Reference program",
    "wrapper": "Wrapper",
    "application": "Application",
    "plugin": "Plugin or external",
    "teaching": "Teaching material",
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
    "cross-implementation": "another implementation",
    "self-tests": "own tests only",
    "not-stated": "not stated",
}
VALIDATION_LONG = {
    "standard-data": "Compared with test signals or values published in the standard or the model paper.",
    "reference-code": "Compared with the reference program or the model authors' own code.",
    "cross-implementation": "Compared with another independent implementation.",
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
STATUS_ORDER = {"available": 0, "unreleased": 1, "proposed": 2}
STANDING = {
    "established": "Described in a publication, used by others, or written by the authors of the model, with a "
                   "track record of more than a year.",
    "developing": "Research, teaching or hobby code without documented use by others, or a project still in "
                  "development.",
    "new": "First released less than about a year ago and not yet widely used in the community.",
}
STANDING_ORDER = {"established": 0, "developing": 1, "new": 2}
ACTIVITY_ORDER = {"active": 0, "unknown": 1, "inactive": 2, "archived": 3}


def project_rank(p: dict) -> int:
    """Widely used, recognised projects carry a rank (1 first); the others follow."""
    return int(p.get("rank") or 999)


def impl_rank(impl: dict) -> tuple:
    """The order of implementations everywhere: established projects first and new ones last; then released code
    before unreleased before proposed; widely used projects (rank) first; own code before wrappers; active
    projects before inactive ones."""
    p = impl["_project"]
    return (STANDING_ORDER[p["standing"]], STATUS_ORDER[impl["status"]], project_rank(p),
            1 if impl.get("_via") else 0, ACTIVITY_ORDER.get(p.get("_activity", "unknown"), 1), p["name"].lower())


def only_new(m: dict) -> bool:
    """True when every released implementation of a method's current edition comes from a new project."""
    released = [i for i in m["_current_impls"] if i["status"] == "available"]
    return bool(released) and all(i["_project"]["standing"] == "new" for i in released)

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
    """All index data plus lookups and derived fields (keys starting with '_' are derived)."""

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

        for key in ("title", "description", "base_url", "repository", "maintainer", "license", "credit"):
            if not self.site.get(key):
                add(f"data/site.yaml: missing '{key}'")
        if self.site.get("base_url") and not str(self.site["base_url"]).endswith("/"):
            add("data/site.yaml: base_url must end with '/'")

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
        check_ids(self.projects, "data/projects")
        for p in self.projects:
            pid = p.get("id")
            path = self.project_files.get(str(pid))
            w = f"data/projects/{path.name if path else pid}"
            if path and path.stem != pid:
                add(f"{w}: id '{pid}' must match the file name")
            for key in ("name", "repository", "languages", "kind", "license", "summary", "ai_assistance",
                        "standing", "implements", "sources", "checked"):
                if not p.get(key):
                    add(f"{w}: missing '{key}'")
            if p.get("kind") and p["kind"] not in PROJECT_KINDS:
                add(f"{w}: kind '{p['kind']}' not one of {sorted(PROJECT_KINDS)}")
            if p.get("standing") and p["standing"] not in STANDING:
                add(f"{w}: standing must be one of {sorted(STANDING)}")
            if p.get("standing") == "new" and not p.get("standing_note"):
                add(f"{w}: a new project needs a standing_note (when it was first released)")
            if p.get("rank") is not None and (not isinstance(p["rank"], int) or p["rank"] < 1):
                add(f"{w}: rank must be a positive whole number")
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
                    add(f"{wi}: via '{impl['via']}' is not an indexed project")
                if impl.get("via") == pid:
                    add(f"{wi}: via must name another project")
                pair = (mid, rid, impl.get("status"), impl.get("scope"))
                if pair in seen_pairs:
                    add(f"{wi}: duplicate of an earlier entry")
                seen_pairs.add(pair)

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
                add(f"data/leads.yaml[{i}]: {lead['url']} is already an indexed project")
        for i, ig in enumerate(self.ignored):
            if not ig.get("url") or not ig.get("reason"):
                add(f"data/ignored.yaml[{i}]: needs url and reason")
            elif normalise_url(ig["url"]) in repos:
                add(f"data/ignored.yaml[{i}]: {ig['url']} is also an indexed project")
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
        snap_projects = self.snapshot.get("projects") or {}

        for m in self.methods:
            m["_impls"] = []
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

            if p["_archived"]:
                p["_activity"] = "archived"
            elif p["_last_commit"]:
                age = (as_of - dt.date.fromisoformat(p["_last_commit"][:10])).days
                p["_activity"] = "active" if age <= inactive_after else "inactive"
            else:
                p["_activity"] = "unknown"

            p["_impls"] = []
            for impl in p.get("implements") or []:
                impl = dict(impl)
                impl["_project"] = p
                impl["_method"] = self.method[impl["method"]]
                impl["_ref"] = self.ref[impl["reference"]]
                impl["_via"] = self.project.get(impl.get("via"))
                p["_impls"].append(impl)
                self.method[impl["method"]]["_impls"].append(impl)
                self.ref[impl["reference"]]["_impls"].append(impl)

        for m in self.methods:
            order = {rid: i for i, rid in enumerate(m.get("references") or [])}
            # Standing comes before the edition, so a new project never heads a list of implementations.
            m["_impls"].sort(key=lambda i: (STANDING_ORDER[i["_project"]["standing"]], -order[i["reference"]],
                                            *impl_rank(i)[1:]))
            current = set(m.get("current") or [])
            m["_current_impls"] = [i for i in m["_impls"] if i["reference"] in current]
            m["_older_impls"] = [i for i in m["_impls"] if i["reference"] not in current]
            m["_languages"] = sorted({lang for i in m["_current_impls"] if i["status"] == "available"
                                      for lang in i["_project"]["languages"]})
        for p in self.projects:
            p["_impls"].sort(key=lambda i: (self.methods.index(i["_method"]),
                                            -(i["_method"]["references"].index(i["reference"]))))

    # ------------------------------------------------------------------ queries used by renderers

    def families_with_methods(self) -> list[tuple[dict, list[dict]]]:
        return [(f, [m for m in self.methods if m.get("family") == f["id"]]) for f in self.families]

    def projects_by_standing(self) -> list[dict]:
        """Established projects first, new ones last; widely used projects (rank) first within each group, then
        alphabetical."""
        return sorted(self.projects, key=lambda p: (STANDING_ORDER[p["standing"]], project_rank(p), p["name"].lower()))

    def languages(self) -> list[str]:
        return sorted({lang for p in self.projects for lang in p.get("languages") or []}, key=str.lower)

    def gaps(self) -> list[dict]:
        """Methods whose current edition has no available open implementation."""
        return [m for m in self.methods
                if not any(i["status"] == "available" for i in m["_current_impls"])]

    def new_only(self) -> list[dict]:
        """Methods whose current edition has released implementations only from new projects."""
        return [m for m in self.methods if only_new(m)]


def load(root: Path = ROOT) -> Index:
    index = Index(root)
    problems = index.validate()
    if problems:
        raise DataError(problems)
    index.enrich()
    return index
