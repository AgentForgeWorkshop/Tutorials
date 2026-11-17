"""Load the frozen corpus, project descriptions, eval tasks and answer keys."""
import json
import re
from functools import lru_cache

from .config import DATA_DIR

PROJECTS = ("P1", "P2", "P3")
LEVELS = ("core", "related")


@lru_cache
def papers() -> dict:
    """paper_id -> paper record (title, authors, source, posted, url, abstract, ...)."""
    return {p["paper_id"]: p for p in json.loads((DATA_DIR / "papers.json").read_text())}


@lru_cache
def projects_text() -> str:
    """Full project descriptions incl. relevance rules (used by prompt v2)."""
    return (DATA_DIR / "projects.md").read_text()


@lru_cache
def project_titles() -> dict:
    """{'P1': 'Detecting small microplastics in drinking water', ...} parsed from projects.md."""
    return dict(re.findall(r"^## (P\d) — (.+)$", projects_text(), flags=re.M))


@lru_cache
def tasks() -> list:
    return json.loads((DATA_DIR / "tasks.json").read_text())


def task(task_id: str) -> dict:
    return next(t for t in tasks() if t["task_id"] == task_id)


@lru_cache
def gold(version: str = "v2") -> dict:
    """Answer key, normalised to one shape for both versions.

    v2 (gold.json)    : labels {project: 'core'|'related'}  — the current key
    v1 (gold_v1.json) : topic-only key from before relevance levels existed;
                        labels {project: None} (no level to check)
    Every entry: {'labels', 'acceptable' (set), 'reasons', 'difficulty', 'note'}
    """
    fname = "gold.json" if version == "v2" else "gold_v1.json"
    raw = json.loads((DATA_DIR / fname).read_text())
    out = {}
    for pid, g in raw.items():
        labels = g["labels"] if "labels" in g else {p: None for p in g["projects"]}
        out[pid] = dict(labels=labels, acceptable=set(g.get("acceptable", [])),
                        reasons=g.get("reasons", {}), difficulty=g.get("difficulty", ""),
                        note=g.get("note", ""))
    return out
