"""The environment the triage system acts on: this week's feed, the lab database and an outbox.

The same environment (and the same tool functions) serve both systems:
  - the agent calls the tools itself, in any order it chooses;
  - the LLM workflow calls them from fixed Python code.
Every call is written to `log`, which is the trace the trace-graders inspect.
"""
import functools
import json
import sqlite3
import threading

from langchain_core.tools import StructuredTool

from . import data
from .data import LEVELS, PROJECTS


def _locked(fn):
    """Agents may call several tools in parallel (threads): serialise access to the DB and the log."""
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return fn(self, *args, **kwargs)
    return wrapper


class TriageEnv:
    def __init__(self, task: dict, papers: dict | None = None):
        self._lock = threading.RLock()
        self.task = task
        self.papers = papers or data.papers()
        self.feed = list(task["feed"])
        self.db = sqlite3.connect(":memory:", check_same_thread=False)
        self.db.execute("CREATE TABLE history (paper_id TEXT PRIMARY KEY, week INT)")
        self.db.execute("CREATE TABLE triage (paper_id TEXT, project TEXT, level TEXT, reason TEXT, week INT)")
        self.db.executemany("INSERT INTO history VALUES (?, ?)",
                            [(pid, self.papers[pid]["week"]) for pid in task["already_triaged"]])
        self.outbox: list[str] = []
        self.log: list[dict] = []

    # ------------------------------------------------------------------ helpers
    def _record(self, tool: str, args: dict, ok: bool, note: str = ""):
        self.log.append(dict(step=len(self.log), tool=tool, args=args, ok=ok, note=note))

    @_locked
    def triaged_before(self, paper_id: str) -> int | None:
        row = self.db.execute("SELECT week FROM history WHERE paper_id=?", (paper_id,)).fetchone()
        return row[0] if row else None

    # ------------------------------------------------------------------ tools
    @_locked
    def list_new_papers(self) -> str:
        """List this week's new papers (paper_id and title)."""
        self._record("list_new_papers", {}, True)
        return json.dumps([{"paper_id": pid, "title": self.papers[pid]["title"]} for pid in self.feed])

    @_locked
    def read_paper(self, paper_id: str) -> str:
        """Read one paper: title, authors, source, date and abstract."""
        if paper_id not in self.feed:
            self._record("read_paper", {"paper_id": paper_id}, False, "not in feed")
            return f"Error: {paper_id} is not in this week's feed."
        p = self.papers[paper_id]
        self._record("read_paper", {"paper_id": paper_id}, True)
        return json.dumps({k: p[k] for k in ("paper_id", "title", "authors", "source", "posted", "abstract")},
                          ensure_ascii=False)

    @_locked
    def check_database(self, paper_id: str) -> str:
        """Check whether a paper was already triaged in an earlier week. Papers can reappear
        (e.g. revised preprints); a paper that is already in the database must not be triaged again."""
        week = self.triaged_before(paper_id)
        self._record("check_database", {"paper_id": paper_id}, True, f"in db (week {week})" if week else "new")
        if week:
            return f"{paper_id} was already triaged in week {week}. Do not triage it again."
        return f"{paper_id} is not in the database yet."

    @_locked
    def save_triage(self, paper_id: str, project: str, level: str, reason: str) -> str:
        """Save that a paper is relevant to ONE project. Call once per relevant project.
        project: 'P1', 'P2' or 'P3'. level: 'core' or 'related'.
        reason: 1-2 sentences on specifically how the paper helps that project.
        Do not save anything for papers that are not relevant to any project."""
        args = dict(paper_id=paper_id, project=project, level=level, reason=reason)
        problems = []
        if paper_id not in self.feed:
            problems.append(f"{paper_id} is not in this week's feed")
        if project not in PROJECTS:
            problems.append(f"project must be one of {PROJECTS}")
        if level not in LEVELS:
            problems.append(f"level must be one of {LEVELS}")
        if problems:
            self._record("save_triage", args, False, "; ".join(problems))
            return "Error: " + "; ".join(problems) + ". Nothing saved."
        # Like a real database without constraints: duplicates and re-triage are accepted
        # (graders catch them), so mistakes show up in the outcome, not only in the trace.
        self.db.execute("INSERT INTO triage VALUES (?, ?, ?, ?, ?)",
                        (paper_id, project, level, reason, self.task["week"]))
        self._record("save_triage", args, True)
        return f"Saved: {paper_id} -> {project} ({level})."

    @_locked
    def send_digest(self, text: str) -> str:
        """Send the weekly digest to the lab. Call exactly once, after all papers are triaged."""
        self.outbox.append(text)
        self._record("send_digest", {"chars": len(text)}, True)
        return "Digest sent."

    def tools(self) -> list:
        fns = [self.list_new_papers, self.read_paper, self.check_database, self.save_triage, self.send_digest]
        return [StructuredTool.from_function(f, name=f.__name__, description=f.__doc__.strip()) for f in fns]

    # ------------------------------------------------------------------ outcome
    @_locked
    def results(self) -> dict:
        rows = self.db.execute("SELECT paper_id, project, level, reason FROM triage").fetchall()
        return dict(saved=[dict(paper_id=a, project=b, level=c, reason=d) for a, b, c, d in rows],
                    digests=list(self.outbox), tool_log=list(self.log))
