"""Output paths and absolute URLs of every generated page (one place, so links never drift)."""

from __future__ import annotations

from .data import Index

HOME = "index.html"
METRICS = "metrics/index.html"
PROJECTS = "projects/index.html"
LANGUAGES = "languages.html"
AI = "ai.html"
STANDARDS = "standards.html"
UPDATES = "updates.html"
ABOUT = "about.html"
FAQ = "faq.html"
BIBTEX = "references.bib"  # every standard, model paper and software paper, as BibTeX


def method_path(m: dict) -> str:
    return f"metrics/{m['id']}.html"


def project_path(p: dict) -> str:
    return f"projects/{p['id']}.html"


def md_twin(path: str) -> str:
    return path[: -len(".html")] + ".md"


def pretty(path: str) -> str:
    """URL path as served by GitHub Pages: 'index.html' -> '', 'projects/index.html' -> 'projects/'."""
    if path == "index.html":
        return ""
    if path.endswith("/index.html"):
        return path[: -len("index.html")]
    return path


def absolute(index: Index, path: str) -> str:
    return index.site["base_url"] + pretty(path)


def relative(from_path: str, to_path: str) -> str:
    """Relative link between two output files, so the site also works when opened from a local folder."""
    return "../" * from_path.count("/") + to_path
