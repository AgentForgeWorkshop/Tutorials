"""Build the participant folder notebook/: the participant notebook + its data.

    python scripts/build_public.py   ->  notebook/
        05_evaluating_a_triage_agent.ipynb   (loads its data from GitHub, pinned to DATA_TAG)
        data/README.md, projects.md, papers.csv, answer_key.csv, answer_key_v1.csv, tasks.json

Commit notebook/ and push to main of AgentForgeWorkshop/Tutorials, then create the tag DATA_TAG
(the notebook's data URLs only work once that tag exists on GitHub).
"""
import csv
import json
import pathlib
import shutil

import nbformat as nbf

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_DIR = ROOT / "notebook"
OUT = OUT_DIR / "05_evaluating_a_triage_agent.ipynb"

REPO = "AgentForgeWorkshop/Tutorials"
FOLDER = "Tutorial5_evals/hands-on/notebook"
DATA_TAG = "tutorial5-v1"
COLAB_PATH = f"{REPO}/blob/main/{FOLDER}/05_evaluating_a_triage_agent.ipynb"
BASE_URL = f"https://raw.githubusercontent.com/{REPO}/{DATA_TAG}/{FOLDER}/data/"
BROWSE_URL = f"https://github.com/{REPO}/tree/{DATA_TAG}/{FOLDER}/data"

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip("\n")))
code = lambda s, form=False: cells.append(
    nbf.v4.new_code_cell(s.strip("\n"), metadata={"cellView": "form"} if form else {}))

# =====================================================================================  intro
md(f"""
# Tutorial 5: Evaluating an agent

**AgentForge Workshop · Tutorial 5 · Example 1 · about 40 minutes, self-paced**

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/{COLAB_PATH})

In the slides, an eval had four parts: a **task** (input and environment), a **grader**, **metrics**,
and **trials**, all run by an **eval harness** that sits around the agent. In this notebook you
build that harness yourself, in plain Python, for the paper-triage agent from the demo:

> Each week a lab gets new papers. The agent reads them, decides which of the lab's three projects
> each paper matters to (**core** or **related**), saves its decisions, and sends one digest.

Then you use the harness the way the demo did: **improve the agent**, **improve the eval**, and
**compare the agent with an LLM workflow**. The demo showed these steps in LangSmith; here you see
every line.

| Step | What | Min |
|---|---|---|
| 0 | Setup | 3 |
| 1 | The task: three projects, weekly papers, an answer key | 4 |
| 2 | The agent, and one run with its trace | 6 |
| 3 | Graders: code for labels and trace, an LLM judge for reasons | 7 |
| 4 | The harness: tasks × trials → pass@k and pass^k | 6 |
| 5 | Improve the agent: prompt v1 vs v2 | 5 |
| 6 | Improve the eval: the same runs, an older answer key | 4 |
| 7 | Agent vs LLM workflow | 5 |
| | *Exercises* | |
""")

# =====================================================================================  step 0
md("""
---
## Step 0: Setup

Run the next cell once. It takes about a minute. A warning about "pip dependency google-colab" is
expected and harmless.
""")
code('%pip install -q "langchain==1.4.2" "langchain-openai==1.6.2"')
md("""
### Your API key

1. Open <https://openrouter.ai/keys> and create a key (the workshop gives you credit).
2. In Colab, click the **🔑 key icon** in the left sidebar (Secrets).
3. Add a secret named exactly `OPENROUTER_API_KEY`, paste your key, and turn on
   **Notebook access**.

A key pasted into a cell gets saved into the notebook, and notebooks get shared. Treat an API
key like a password.

This notebook uses two models: a **small** one that runs the agent, and a **large** one that acts as
the LLM judge.
""")
code('''
import getpass
import os

from langchain.chat_models import init_chat_model


def get_key(name: str) -> str:
    """Read an API key from Colab's Secrets panel, or ask for it if there is none."""
    try:
        from google.colab import userdata

        return userdata.get(name)
    except Exception:  # not in Colab, or that secret is not set
        return os.environ.get(name) or getpass.getpass(f"{name}: ")


# Any id from https://openrouter.ai/models that supports tool calling ("Tools" filter).
AGENT_MODEL = "openai/gpt-5-mini"     # small model: runs the agent and the workflow
JUDGE_MODEL = "openai/gpt-5.6-terra"  # large model: the LLM judge


def make_model(model_id: str):
    """OpenRouter speaks the OpenAI API, so LangChain's OpenAI class works with a different URL."""
    return init_chat_model(f"openai:{model_id}", base_url="https://openrouter.ai/api/v1",
                           api_key=os.environ["OPENROUTER_API_KEY"], max_retries=4)


os.environ["OPENROUTER_API_KEY"] = get_key("OPENROUTER_API_KEY")
''')
md("""
**Optional: traces in LangSmith.** Everything below works without it. If you have a LangSmith key
(free at <https://smith.langchain.com>), add it as a secret named `LANGSMITH_API_KEY`, set
`USE_LANGSMITH = True` and every run will appear there as a trace, like in the demo.
""")
code('''
USE_LANGSMITH = False

if USE_LANGSMITH:
    os.environ["LANGSMITH_API_KEY"] = get_key("LANGSMITH_API_KEY")
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = "tutorial5-paper-triage"
''')

# ---- data: loaded from GitHub (files written by export_data() below)
md(f"""
### The data

The data sits next to this notebook on GitHub, in [`{FOLDER}/data`]({BROWSE_URL}). Have a look there:
`papers.csv` and `answer_key.csv` show as searchable tables, and the folder's README explains every
column. The next cell loads the same files. The link is pinned to the tag `{DATA_TAG}`, so the data
cannot change under you.
""")
code(f'''
import json
import urllib.request

import pandas as pd

BASE = "{BASE_URL}"


def fetch(name):
    """Text of one data file (BASE can also be a local folder)."""
    if BASE.startswith("http"):
        return urllib.request.urlopen(BASE + name).read().decode("utf-8")
    return open(BASE + name, encoding="utf-8").read()


PROJECTS = ("P1", "P2", "P3")
LEVELS = ("core", "related")

PROJECTS_MD = fetch("projects.md")                       # the three projects + relevance rules
TASKS = json.loads(fetch("tasks.json"))                  # 8 weekly tasks
papers_df = pd.read_csv(BASE + "papers.csv")             # 50 papers
key_df = pd.read_csv(BASE + "answer_key.csv").fillna("")        # answer key v2: core / related
key_v1_df = pd.read_csv(BASE + "answer_key_v1.csv").fillna("")  # answer key v1: topic only

PAPERS = {{p["paper_id"]: p for p in papers_df.to_dict("records")}}


def read_key(df):
    """Answer-key table -> {{paper_id: labels, acceptable extras, reference reasons, note}}."""
    key = {{}}
    for row in df.to_dict("records"):
        # "core" / "related" in key v2; "yes" in key v1, which has no levels (None)
        labels = {{p: (row[p] if row[p] in LEVELS else None) for p in PROJECTS if row[p]}}
        key[row["paper_id"]] = dict(labels=labels, acceptable=set(row["acceptable"].split()),
                                    reasons={{p: row.get(f"reason_{{p}}", "") for p in labels}},
                                    note=row.get("note", ""))
    return key


GOLD = {{"v2": read_key(key_df), "v1": read_key(key_v1_df)}}


def task(task_id):
    return next(t for t in TASKS if t["task_id"] == task_id)


print(f"{{len(PAPERS)}} papers, {{len(TASKS)}} weekly tasks, answer keys: {{list(GOLD)}}")
''')

code('''
model, judge_model = make_model(AGENT_MODEL), make_model(JUDGE_MODEL)
print("Agent model:", AGENT_MODEL, "| judge model:", JUDGE_MODEL)
print(model.invoke("Reply with exactly: ready").text)
''')

# =====================================================================================  step 1
md("""
---
## Step 1: The task

A (fictional) lab runs three projects on microplastics that follow one story:
**measure** (P1) → **understand** (P2) → **capture** (P3).

For each project a paper is **core** (it directly advances an aim), **related** (the project lead
would *compare* against it, *borrow* a method from it, or *cite* it), or **not relevant**. These
rules live in one text, `PROJECTS_MD`. The agent's prompt v2 uses it, and the answer key was labelled
with it: **the agent and the eval share one spec.**
""")
code('''
print(PROJECTS_MD[: PROJECTS_MD.index("## P1")])
''')
md("""
One **task** is one week: the papers in that week's feed, plus the lab database as it was that week.
The eval suite has 8 tasks. Two have a twist:

* **Week 4**: nothing is relevant. Does the agent still send a digest saying so?
* **Week 6**: `MP052` was already triaged in week 2 and shows up again (a revised preprint). It
  must not be triaged twice.

The **answer key** says, for each paper, which projects it matters to and at what level. Some
papers also list *acceptable* extras: links an expert could defend, which a grader should not punish.
""")
code('''
try:  # in Colab: interactive tables you can sort, filter and search
    from google.colab import data_table
    data_table.enable_dataframe_formatter()
except ImportError:
    pass


def week_table(task_id):
    """One week's feed with its answer key."""
    t = task(task_id)
    df = papers_df.set_index("paper_id").loc[t["feed"], ["title", "source"]]
    df = df.join(key_df.set_index("paper_id")[["P1", "P2", "P3", "acceptable", "note"]])
    df["already_in_database"] = df.index.isin(t["already_triaged"])
    return df.reset_index()


week_table("week_06")
''')
md("""
Try `week_table("week_04")`, or explore the whole answer key: `key_df`.
""")

# =====================================================================================  step 2
md("""
---
## Step 2: The agent

### The environment and its tools

The agent works on a small **environment**: this week's feed, a lab database (SQLite) and an outbox.
Its five tools are ordinary Python functions on that environment. Every call is written to a
**log**: that log is the trace your graders will read in Step 3.

Two design choices worth noticing:

* The database accepts duplicates and re-triaged papers, like a real one without constraints. So a
  mistake shows up in the **outcome**, not only in the trace.
* Later, the LLM workflow uses **the same environment and tools**. Only who decides the steps changes.
""")
code('''
import functools
import sqlite3
import threading

from langchain_core.tools import StructuredTool


def _locked(fn):
    """Agents may call several tools at once (threads): one at a time for the DB and the log."""
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return fn(self, *args, **kwargs)
    return wrapper


class TriageEnv:
    def __init__(self, task):
        self._lock = threading.RLock()
        self.task, self.feed = task, list(task["feed"])
        self.db = sqlite3.connect(":memory:", check_same_thread=False)
        self.db.execute("CREATE TABLE history (paper_id TEXT PRIMARY KEY, week INT)")
        self.db.execute("CREATE TABLE triage (paper_id TEXT, project TEXT, level TEXT, reason TEXT)")
        self.db.executemany("INSERT INTO history VALUES (?, ?)",
                            [(pid, int(PAPERS[pid]["week"])) for pid in task["already_triaged"]])
        self.outbox, self.log = [], []

    def _record(self, tool, args, ok, note=""):
        self.log.append(dict(step=len(self.log), tool=tool, args=args, ok=ok, note=note))

    @_locked
    def triaged_before(self, paper_id):
        row = self.db.execute("SELECT week FROM history WHERE paper_id=?", (paper_id,)).fetchone()
        return row[0] if row else None

    # ---- the five tools (the docstrings are what the model sees)
    @_locked
    def list_new_papers(self) -> str:
        """List this week's new papers (paper_id and title)."""
        self._record("list_new_papers", {}, True)
        return json.dumps([{"paper_id": p, "title": PAPERS[p]["title"]} for p in self.feed])

    @_locked
    def read_paper(self, paper_id: str) -> str:
        """Read one paper: title, authors, source, date and abstract."""
        if paper_id not in self.feed:
            self._record("read_paper", {"paper_id": paper_id}, False, "not in feed")
            return f"Error: {paper_id} is not in this week's feed."
        self._record("read_paper", {"paper_id": paper_id}, True)
        p = PAPERS[paper_id]
        return json.dumps({k: p[k] for k in ("paper_id", "title", "authors", "source", "posted", "abstract")})

    @_locked
    def check_database(self, paper_id: str) -> str:
        """Check whether a paper was already triaged in an earlier week. Papers can reappear
        (e.g. revised preprints); a paper that is already in the database must not be triaged again."""
        week = self.triaged_before(paper_id)
        self._record("check_database", {"paper_id": paper_id}, True, f"in db (week {week})" if week else "new")
        return (f"{paper_id} was already triaged in week {week}. Do not triage it again." if week
                else f"{paper_id} is not in the database yet.")

    @_locked
    def save_triage(self, paper_id: str, project: str, level: str, reason: str) -> str:
        """Save that a paper is relevant to ONE project. Call once per relevant project.
        project: 'P1', 'P2' or 'P3'. level: 'core' or 'related'.
        reason: 1-2 sentences on specifically how the paper helps that project.
        Do not save anything for papers that are not relevant to any project."""
        args = dict(paper_id=paper_id, project=project, level=level, reason=reason)
        problems = [msg for bad, msg in [(paper_id not in self.feed, f"{paper_id} is not in this week's feed"),
                                         (project not in PROJECTS, f"project must be one of {PROJECTS}"),
                                         (level not in LEVELS, f"level must be one of {LEVELS}")] if bad]
        if problems:
            self._record("save_triage", args, False, "; ".join(problems))
            return "Error: " + "; ".join(problems) + ". Nothing saved."
        self.db.execute("INSERT INTO triage VALUES (?, ?, ?, ?)", (paper_id, project, level, reason))
        self._record("save_triage", args, True)
        return f"Saved: {paper_id} -> {project} ({level})."

    @_locked
    def send_digest(self, text: str) -> str:
        """Send the weekly digest to the lab. Call exactly once, after all papers are triaged."""
        self.outbox.append(text)
        self._record("send_digest", {"chars": len(text)}, True)
        return "Digest sent."

    def tools(self):
        fns = [self.list_new_papers, self.read_paper, self.check_database, self.save_triage, self.send_digest]
        return [StructuredTool.from_function(f, name=f.__name__, description=f.__doc__.strip()) for f in fns]

    @_locked
    def results(self):
        rows = self.db.execute("SELECT paper_id, project, level, reason FROM triage").fetchall()
        return dict(saved=[dict(zip(("paper_id", "project", "level", "reason"), r)) for r in rows],
                    digests=list(self.outbox), tool_log=list(self.log))
''')
md("""
### The prompts: v1 and v2 differ in one place only

Both prompts give the same instructions, tools and digest format. They differ only in how the
projects are described:

* **v1**: the project titles, plus "core if directly relevant, related if somewhat relevant". This is
  what most people write first.
* **v2**: the full `PROJECTS_MD`, with aims and the core / related / not-relevant rules.

Changing one thing at a time is what lets you say *why* a score changed (Step 5).
""")
code('''
DIGEST_FORMAT = """## P1
- MP012 (core): <title> — <one-sentence reason>
- MP015 (related): <title> — <one-sentence reason>
## P2
- nothing this week
## P3
- ..."""

TITLES = dict(re.findall(r"^## (P\\d) — (.+)$", PROJECTS_MD, flags=re.M))


def projects_block(version):
    if version == "v1":
        lines = "\\n".join(f"- {p}: {t}" for p, t in TITLES.items())
        return ("The lab's projects:\\n" + lines + "\\n\\nUse level \\"core\\" if a paper is directly relevant "
                "to a project and \\"related\\" if it is somewhat relevant.")
    return "The lab's projects and how to judge relevance:\\n\\n" + PROJECTS_MD


def agent_system_prompt(version):
    return f"""You are the paper-triage assistant for a freshwater microplastics research lab.
Each week new papers arrive. For every paper, decide which of the lab's projects it is relevant to
(zero, one or several) and at what level, then send one digest to the lab.

How to work:
- Use list_new_papers to see this week's papers, and read_paper to read each paper before deciding.
- Use check_database for each paper; papers already triaged in an earlier week must be skipped.
- For each relevant (paper, project) pair call save_triage with the level and a 1-2 sentence reason
  that says specifically how the paper helps that project. Save nothing for irrelevant papers.
- Finally call send_digest exactly once, even if nothing is relevant, in this format
  (one heading per project; list only papers you saved):

{DIGEST_FORMAT}

{projects_block(version)}"""


print(projects_block("v1"))
''')
md("""
### The agent

`create_agent` is the loop from Tutorial 1 (LLM → tool calls → results → LLM …), with conveniences.
`run_agent` runs one week and returns everything a grader needs: the saved decisions, the digest, the
trace (tool log), the token usage and the time taken.
""")
code('''
import time

from langchain.agents import create_agent


def usage_of(messages):
    u = dict(input_tokens=0, output_tokens=0, total_tokens=0, llm_calls=0)
    for m in messages:
        if m.type == "ai":
            u["llm_calls"] += 1
            for k in ("input_tokens", "output_tokens", "total_tokens"):
                u[k] += (m.usage_metadata or {}).get(k, 0) or 0
    return u


def run_agent(task, prompt_version, model):
    env = TriageEnv(task)
    agent = create_agent(model, tools=env.tools(), system_prompt=agent_system_prompt(prompt_version))
    t0, error, messages = time.time(), None, []
    try:
        state = agent.invoke(
            {"messages": [{"role": "user", "content": f"Week {task['week']}: please triage this week's new papers and send the digest."}]},
            config={"recursion_limit": 80, "run_name": f"agent-{prompt_version} {task['task_id']}"})
        messages = state["messages"]
    except Exception as e:  # e.g. step limit reached: keep what was done so far
        error = f"{type(e).__name__}: {e}"
    return dict(env.results(), system=f"agent-{prompt_version}", task_id=task["task_id"], error=error,
                latency_s=round(time.time() - t0, 1), usage=usage_of(messages))
''')
md("""
### One run, and its trace

Run the agent with prompt **v1** on week 6 and read the trace before looking at any score. Check
three things:

1. Did it **read** every paper before saving a decision about it?
2. Did it **check the database**, and skip `MP052`?
3. How many **LLM calls** and tokens did one week cost?
""")
code('''
def show_trace(result):
    for e in result["tool_log"]:
        a = e["args"]
        detail = (f"{a['paper_id']} -> {a['project']} ({a['level']})" if e["tool"] == "save_triage"
                  else a.get("paper_id", "") or (f"{a['chars']} characters" if "chars" in a else ""))
        print(f"[{e['step']:2d}] {e['tool']:16s} {detail}  {'' if e['ok'] else '!! ' + e['note']}")
    print(f"\\n{result['usage']['llm_calls']} LLM calls, {result['usage']['total_tokens']} tokens, "
          f"{result['latency_s']} s{', ERROR: ' + result['error'] if result['error'] else ''}")


run = run_agent(task("week_06"), "v1", model)
show_trace(run)
print("\\n" + (run["digests"][-1] if run["digests"] else "(no digest sent)"))
''')

# =====================================================================================  step 3
md("""
---
## Step 3: Graders

The grid from the talk, filled in for this agent:

| What ↓ / How → | Code | LLM judge | Human |
|---|---|---|---|
| **Outcome** | projects and levels vs the answer key; digest format and coverage | is each *reason* specific and faithful? | spot-check reasons to calibrate the judge |
| **Trace** | read before save; checked the database; no duplicate saves | | |
| **Operational** | LLM calls, tokens, time | | |

### Code graders for the outcome

The unit is a **(paper, project) pair**. Against the answer key we count:

* **core recall** and **related recall**: which expected pairs were found;
* **precision**: of the pairs the agent saved, how many are expected *or acceptable*;
* **level accuracy**: of the pairs found, how many have the right level.

A week **passes** when every core pair is found, nothing irrelevant is marked core, no paper is
triaged twice, and exactly one digest is sent. Related pairs earn partial credit in the scores but
do not decide pass/fail: that is a choice, and you could make another.
""")
code('''
def to_triage(task):
    return [p for p in task["feed"] if p not in task["already_triaged"]]


def label_grades(result, task, gold):
    todo = to_triage(task)
    pred = {}
    for r in result["saved"]:
        if r["paper_id"] in todo:
            pred.setdefault((r["paper_id"], r["project"]), r["level"])
    expected = {(p, proj): lvl for p in todo for proj, lvl in gold[p]["labels"].items()}
    acceptable = {(p, proj) for p in todo for proj in gold[p]["acceptable"]}
    has_levels = any(l is not None for g in gold.values() for l in g["labels"].values())

    core = {k for k, l in expected.items() if l in ("core", None)}
    related = {k for k, l in expected.items() if l == "related"}
    found = set(pred) & set(expected)
    extra_ok = (set(pred) - set(expected)) & acceptable
    wrong = set(pred) - set(expected) - acceptable
    leveled = [k for k in found if expected[k] is not None]
    frac = lambda a, b: round(len(a) / len(b), 3) if b else 1.0
    return dict(
        core_recall=frac(found & core, core),
        related_recall=frac(found & related, related) if related else None,  # None: nothing related to find
        precision=round((len(found) + len(extra_ok)) / len(pred), 3) if pred else 1.0,
        level_accuracy=round(sum(pred[k] == expected[k] for k in leveled) / len(leveled), 3) if leveled else None,
        missed_core=sorted(core - found), missed_related=sorted(related - found),
        false_positives=sorted(wrong), false_core=sorted(k for k in wrong if pred[k] == "core"),
        level_mismatches=sorted((k, pred[k], expected[k]) for k in leveled if pred[k] != expected[k]),
        retriaged=sorted({r["paper_id"] for r in result["saved"] if r["paper_id"] in task["already_triaged"]}),
        gold_has_levels=has_levels)


def digest_grades(result):
    text = result["digests"][-1] if result["digests"] else ""
    shown, section = set(), None
    for line in text.splitlines():
        h = re.match(r"^\\s*#+\\s*(P[123])\\b", line)
        if h:
            section = h.group(1)
        elif section:
            shown |= {(pid, section) for pid in re.findall(r"\\bMP\\d{3}\\b", line)}
    saved = {(r["paper_id"], r["project"]) for r in result["saved"]}
    return dict(digest_sent_once=len(result["digests"]) == 1,
                digest_format_ok=all(re.search(rf"^\\s*#+\\s*{p}\\b", text, re.M) for p in PROJECTS),
                digest_coverage=round(len(saved & shown) / len(saved), 3) if saved else 1.0)


def week_pass(labels, digest):
    blocking = labels["false_core"] if labels["gold_has_levels"] else labels["false_positives"]
    return (labels["core_recall"] == 1.0 and not blocking and not labels["retriaged"]
            and digest["digest_sent_once"])
''')
md("""
### Code graders for the trace

These read the tool log, not the answer. They catch problems that a lucky outcome can hide: a
decision saved about a paper the agent never read is a guess, even when the guess is right.
""")
code('''
def trace_grades(result, task):
    read_at, checked, saves, seen, dups = {}, set(), [], set(), 0
    for e in result["tool_log"]:
        pid = e["args"].get("paper_id")
        if e["tool"] == "read_paper" and e["ok"]:
            read_at.setdefault(pid, e["step"])
        elif e["tool"] == "check_database":
            checked.add(pid)
        elif e["tool"] == "save_triage" and e["ok"]:
            saves.append(e)
            dups += (pid, e["args"]["project"]) in seen
            seen.add((pid, e["args"]["project"]))
    read_first = [s for s in saves if read_at.get(s["args"]["paper_id"], 10**9) < s["step"]]
    return dict(read_all_papers=all(p in read_at for p in to_triage(task)),
                read_before_save=round(len(read_first) / len(saves), 3) if saves else 1.0,
                repost_detected=all(p in checked for p in task["reposted"]) and
                                not any(s["args"]["paper_id"] in task["reposted"] for s in saves),
                duplicate_saves=dups, n_tool_calls=len(result["tool_log"]))
''')
md("""
### An LLM judge for the reasons

"How is it relevant?" is open-ended, so code cannot grade it. The judge gets the project rules, the
abstract, the agent's reason and an expert's reference reason, and checks three things. Each check is
a yes/no question, which makes the judge more consistent than a 1–10 score.

Two cautions from the talk:
* **Calibrate the judge against humans.** Read ~10 of its verdicts yourself (Exercise 4). If you
  disagree often, fix the rubric before trusting the numbers.
* Here the judge and the agent come from the **same model family**, and judges can favour their
  family's style. A judge from another provider is a cheap check.
""")
code('''
from typing import Literal

from pydantic import BaseModel, Field


class ReasonVerdict(BaseModel):
    paper_id: str
    project: str
    specific: bool = Field(description="Names what in the paper connects to which aim of the project")
    faithful: bool = Field(description="Every claim, number and finding is supported by the abstract")
    fits_level: bool = Field(description="core: says how it advances an aim; related: says what the lead would do with it")
    verdict: Literal["pass", "fail"]
    comment: str = Field(description="One short sentence explaining the verdict")


class ReasonVerdicts(BaseModel):
    verdicts: list[ReasonVerdict]


JUDGE_PROMPT = """You grade the reasons a paper-triage assistant gave for marking papers as relevant to a
research lab's projects. The lab's projects and relevance rules are below.

For each item, judge ONLY the assistant's reason (not whether the project choice was right):
- specific  : it names what in the paper connects to which aim or aspect of the project.
              Generic reasons ("it is about microplastics") fail.
- faithful  : every claim, number and finding in the reason is supported by the abstract.
- fits_level: for "core" it says how the paper advances an aim; for "related" it says what the
              project lead would do with it (compare against, borrow from, or cite).
verdict = "pass" only if all three are true. A reference reason written by an expert is given for
calibration; the assistant's reason does not need to match its wording.

PROJECTS
""" + PROJECTS_MD


def judge_reasons(result, task, gold, judge_model):
    todo = to_triage(task)
    reasons = {}
    for r in result["saved"]:
        if r["paper_id"] in todo:
            reasons.setdefault((r["paper_id"], r["project"]), (r["level"], r["reason"]))
    items = [k for k in reasons if k[1] in gold[k[0]]["labels"]]  # judge the correctly found pairs
    if not items:
        return dict(reason_pass_rate=None, verdicts=[])
    payload = [dict(paper_id=p, project=proj, level=reasons[(p, proj)][0], assistant_reason=reasons[(p, proj)][1],
                    reference_reason=gold[p]["reasons"].get(proj, ""), title=PAPERS[p]["title"],
                    abstract=PAPERS[p]["abstract"]) for p, proj in items]
    judge = judge_model.with_structured_output(ReasonVerdicts, method="function_calling")
    out = judge.invoke([("system", JUDGE_PROMPT), ("user", json.dumps(payload, ensure_ascii=False))])
    verdicts = [v.model_dump() for v in out.verdicts]
    return dict(reason_pass_rate=round(sum(v["verdict"] == "pass" for v in verdicts) / len(verdicts), 3),
                verdicts=verdicts)
''')
md("""
### Grade the run from Step 2

`grade_run` puts the graders together. Look at what failed and why before moving on.
""")
code('''
def grade_run(result, task, gold_version="v2", judge_model=None):
    gold = GOLD[gold_version]
    labels, digest = label_grades(result, task, gold), digest_grades(result)
    g = dict(passed=week_pass(labels, digest), labels=labels, digest=digest, trace=trace_grades(result, task),
             ops=dict(result["usage"], latency_s=result["latency_s"], error=result["error"]))
    if judge_model is not None:
        g["judge"] = judge_reasons(result, task, gold, judge_model)
    return g


def report(g):
    L = g["labels"]
    print("PASS" if g["passed"] else "FAIL",
          f"| core recall {L['core_recall']} | related recall {L['related_recall']} | precision {L['precision']}"
          f" | level accuracy {L['level_accuracy']}")
    for name in ("missed_core", "missed_related", "false_positives", "level_mismatches", "retriaged"):
        if L[name]:
            print(f"  {name}: {L[name]}")
    print("  digest:", g["digest"], "\\n  trace:", g["trace"])
    for v in g.get("judge", {}).get("verdicts", []):
        if v["verdict"] == "fail":
            print(f"  judge FAIL {v['paper_id']} {v['project']}: {v['comment']}")


report(grade_run(run, task("week_06"), "v2", judge_model))
''')

# =====================================================================================  step 4
md("""
---
## Step 4: The harness — tasks × trials

One run on one week tells you little: the agent is not deterministic. The harness runs **every task
several times** (trials), grades every run, and summarises.

From the talk (backup slides), with *n* trials of a task and *c* passes:

* **pass@k** = 1 − C(n−c, k) / C(n, k): the chance that **at least one** of *k* tries passes;
* **pass^k** = C(c, k) / C(n, k): the chance that **all** *k* tries pass. For a weekly job that must
  work every week, pass^k is the one to watch.
""")
code('''
from concurrent.futures import ThreadPoolExecutor
from math import comb


def pass_at_k(n, c, k):
    return 1.0 if n - c < k else 1 - comb(n - c, k) / comb(n, k)


def pass_hat_k(n, c, k):
    return comb(c, k) / comb(n, k)


print("n=5 trials, c=3 passes:",
      {f"pass@{k}": round(pass_at_k(5, 3, k), 2) for k in (1, 2, 3)},
      {f"pass^{k}": round(pass_hat_k(5, 3, k), 2) for k in (1, 2, 3)})
''')
code('''
import collections
import statistics

import pandas as pd

TRIALS = 3  # runs per task; more trials = steadier numbers, higher cost


def run_suite(system_fn, prompt_version, tasks=TASKS, trials=TRIALS, judge=True, concurrency=8):
    """Every task x every trial: run, then grade against both answer keys."""
    def one(job):
        t, trial = job
        result = system_fn(t, prompt_version, model)
        return dict(task_id=t["task_id"], trial=trial, system=result["system"], result=result,
                    grades={"v2": grade_run(result, t, "v2", judge_model if judge else None),
                            "v1": grade_run(result, t, "v1")})
    jobs = [(t, k) for t in tasks for k in range(trials)]
    with ThreadPoolExecutor(concurrency) as pool:
        records = list(pool.map(one, jobs))
    print(f"{len(records)} runs done, {sum(1 for r in records if r['result']['error'])} with errors")
    return records


def summarize(records, gold="v2", k=TRIALS):
    G = [r["grades"][gold] for r in records]
    by_task = collections.defaultdict(list)
    for r, g in zip(records, G):
        by_task[r["task_id"]].append(g["passed"])
    mean = lambda xs: round(statistics.mean([x for x in xs if x is not None]), 3) if any(x is not None for x in xs) else None
    return {"pass@1": mean([sum(v) / len(v) for v in by_task.values()]),
            f"pass@{k}": mean([pass_at_k(len(v), sum(v), k) for v in by_task.values()]),
            f"pass^{k}": mean([pass_hat_k(len(v), sum(v), k) for v in by_task.values()]),
            "core recall": mean([g["labels"]["core_recall"] for g in G]),
            "related recall": mean([g["labels"]["related_recall"] for g in G]),
            "precision": mean([g["labels"]["precision"] for g in G]),
            "level accuracy": mean([g["labels"]["level_accuracy"] for g in G]),
            "reason pass (judge)": mean([g.get("judge", {}).get("reason_pass_rate") for g in G]),
            "read before save": mean([g["trace"]["read_before_save"] for g in G]),
            "duplicate saves": sum(g["trace"]["duplicate_saves"] for g in G),
            "LLM calls / week": mean([g["ops"]["llm_calls"] for g in G]),
            "tokens / week": mean([g["ops"]["total_tokens"] for g in G]),
            "seconds / week": mean([g["ops"]["latency_s"] for g in G])}


def compare(**named):
    """compare(agent_v1=(records, 'v2'), ...) -> one column per system."""
    return pd.DataFrame({name: summarize(recs, gold) for name, (recs, gold) in named.items()})


def error_report(records, gold="v2", top=10):
    c = collections.Counter()
    for r in records:
        L = r["grades"][gold]["labels"]
        c.update((p, proj, "missed core") for p, proj in L["missed_core"])
        c.update((p, proj, "missed related") for p, proj in L["missed_related"])
        c.update((p, proj, "false positive") for p, proj in L["false_positives"])
        c.update((p, proj, f"level {got}, want {want}") for (p, proj), got, want in L["level_mismatches"])
    return pd.DataFrame([dict(times=n, paper=p, project=proj, error=kind, title=PAPERS[p]["title"][:60])
                         for (p, proj, kind), n in c.most_common(top)])
''')
md("""
Now run **agent v1** on all 8 weeks, 3 times each (24 runs). With `gpt-5-mini` this takes a few
minutes and a small amount of credit.
""")
code('''
agent_v1 = run_suite(run_agent, "v1")
compare(agent_v1=(agent_v1, "v2"))
''')
md("""
Read the table top to bottom:

* Compare **pass@1** with **pass^3**. A large gap means the agent is *inconsistent*: it can do the
  week, but not reliably.
* **Core recall** high but **related recall** low? The agent finds the obvious papers and misses the
  "compare / borrow / cite" ones.

Then find out *which* papers go wrong. This is the start of error analysis: always read failures
before changing anything.
""")
code('''
error_report(agent_v1)
''')
code('''
def find_runs(records, paper_id):
    """Runs whose week contained this paper — to read the trace and the reason given."""
    return [r for r in records if paper_id in task(r["task_id"])["feed"]]


PAPER = error_report(agent_v1)["paper"].iloc[0]   # the paper that went wrong most often
r = find_runs(agent_v1, PAPER)[0]
print(PAPER, "—", PAPERS[PAPER]["title"], "\\nanswer key:", GOLD["v2"][PAPER]["labels"], GOLD["v2"][PAPER]["note"])
print("agent saved:", [s for s in r["result"]["saved"] if s["paper_id"] == PAPER] or "nothing")
''')

# =====================================================================================  step 5
md("""
---
## Step 5: Improve the agent — prompt v1 → v2

Look back at the errors: are they mostly *related* papers that v1 had no way to recognise? Its only
guidance was "somewhat relevant". Prompt v2 gives the agent the same rules the answer key was
labelled with. **Nothing else changes**: same model, same tools, same tasks, same graders.
""")
code('''
agent_v2 = run_suite(run_agent, "v2")
compare(agent_v1=(agent_v1, "v2"), agent_v2=(agent_v2, "v2"))
''')
code('''
error_report(agent_v2)
''')
md("""
What improved, and what did not? Errors that remain after v2 are the interesting ones: some are agent
mistakes, and some may be **mistakes in the answer key**. That is the next step.
""")

# =====================================================================================  step 6
md("""
---
## Step 6: Improve the eval — same runs, an older answer key

The first answer key (**v1**) was topic-only: a paper counted for a project only if it was *about*
that project. Discussing it, we realised a biochar researcher also needs papers on *other* capture
materials to compare against. So the key gained the **core / related** levels (**v2**).

Re-score the **same agent v2 runs** with both keys. No new runs, no new cost.
""")
code('''
compare(agent_v2_scored_with_key_v1=(agent_v2, "v1"), agent_v2_scored_with_key_v2=(agent_v2, "v2"))
''')
code('''
# Pairs the old key calls "false positives" that the new key accepts
flips = collections.Counter(fp for r in agent_v2 for fp in r["grades"]["v1"]["labels"]["false_positives"]
                            if fp not in r["grades"]["v2"]["labels"]["false_positives"])
pd.DataFrame([dict(times=n, paper=p, project=proj, key_v2=GOLD["v2"][p]["labels"].get(proj, "acceptable"),
                   title=PAPERS[p]["title"][:60]) for (p, proj), n in flips.most_common(10)])
''')
md("""
The agent did not change; **the score did**. When a "failure" turns out to be a sensible answer the
key did not allow, the fix belongs in the eval. A good task is one where two experts would agree on
pass or fail; if they would not, clarify the spec, not the prompt.
""")

# =====================================================================================  step 7
md("""
---
## Step 7: Agent vs LLM workflow

Does this task need an agent at all? In an **LLM workflow**, Python decides the steps and the LLM is
used only where judgement is needed:

```text
for each paper (code):  skip it if the database has it        (code)
                        LLM -> projects, levels, reasons       (structured output)
                        save the decisions                     (code)
LLM -> digest text, then send it                               (code)
```

Same environment, same instructions and inputs (prompt v2 wording, the same paper record), same model,
same graders. Only the architecture changes.
""")
code('''
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable


class Assessment(BaseModel):
    project: Literal["P1", "P2", "P3"]
    level: Literal["core", "related"]
    reason: str = Field(description="1-2 sentences on specifically how the paper helps this project")


class PaperDecision(BaseModel):
    """Projects this paper is relevant to (empty list if none)."""
    assessments: list[Assessment] = Field(default_factory=list)


def classify_prompt(version):
    """The agent's wording, minus the tool steps: only the architecture differs."""
    return f"""You are the paper-triage assistant for a freshwater microplastics research lab.
Each week new papers arrive. For every paper, decide which of the lab's projects it is relevant to
(zero, one or several) and at what level.

How to work:
- You get one paper at a time; read it before deciding.
- For each relevant (paper, project) pair give the level and a 1-2 sentence reason
  that says specifically how the paper helps that project. Save nothing for irrelevant papers
  (return an empty list).

{projects_block(version)}"""


DIGEST_PROMPT = ("You write the weekly paper digest for a freshwater microplastics research lab. You get the triage "
                 "decisions saved this week. Write the digest in exactly this format (one heading per project; list "
                 "only the papers given to you; write \\"- nothing this week\\" if a project has no papers). Do not "
                 "add papers or facts that are not in the decisions.\\n\\n" + DIGEST_FORMAT)


@traceable(name="workflow", tags=["workflow"])  # groups each week into one trace in LangSmith (if on)
def run_workflow(task, prompt_version, model):
    env = TriageEnv(task)
    usage = dict(input_tokens=0, output_tokens=0, total_tokens=0, llm_calls=0)
    def count(msg):
        usage["llm_calls"] += 1
        for k in ("input_tokens", "output_tokens", "total_tokens"):
            usage[k] += (msg.usage_metadata or {}).get(k, 0) or 0
    t0, error = time.time(), None
    try:
        env.list_new_papers()
        todo = [p for p in env.feed if "not in the database" in env.check_database(p)]   # code skips reposts
        paper_texts = [env.read_paper(p) for p in todo]   # exactly what the agent's read_paper returns
        classifier = model.with_structured_output(PaperDecision, method="function_calling", include_raw=True)
        outs = classifier.batch([[SystemMessage(classify_prompt(prompt_version)),
                                  HumanMessage(f"Week {task['week']}. Paper {p}:\\n{text}")]
                                 for p, text in zip(todo, paper_texts)], config={"max_concurrency": 6})
        for p, out in zip(todo, outs):                    # one LLM call per paper (in parallel)
            count(out["raw"])
            for a in (out["parsed"] or PaperDecision()).assessments:
                env.save_triage(p, a.project, a.level, a.reason)
        saved = [dict(s, title=PAPERS[s["paper_id"]]["title"]) for s in env.results()["saved"]]
        digest = model.invoke([SystemMessage(DIGEST_PROMPT),
                               HumanMessage("Decisions saved this week:\\n" + json.dumps(saved, ensure_ascii=False))])
        count(digest)
        env.send_digest(digest.text)
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
    return dict(env.results(), system=f"workflow-{prompt_version}", task_id=task["task_id"], error=error,
                latency_s=round(time.time() - t0, 1), usage=usage)
''')
code('''
workflow_v2 = run_suite(run_workflow, "v2")
compare(agent_v2=(agent_v2, "v2"), workflow_v2=(workflow_v2, "v2"))
''')
md("""
How to read it:

* **Quality**: are recall, precision and reason pass rate about the same?
* **Consistency**: compare pass^3. Fixed steps remove a whole class of failures (a skipped paper, a
  forgotten digest, a re-triaged repost), so the trace graders have nothing left to catch.
* **Cost and speed**: LLM calls, tokens and seconds per week.

If the workflow matches the agent's quality for less, ship the workflow. Agents earn their cost when
the task is open-ended: deciding what to search, how much to read, when to stop. That is Example 2.
""")

# =====================================================================================  exercises
md("""
---
## Exercises

1. **Agent problem or eval problem?** Take the top row of `error_report(agent_v2)`. Read the abstract,
   the answer key note and the agent's reason. Who is right? If the key is wrong, how would you fix it?
2. **Add a grader.** Write a code grader that fails a digest longer than 250 words, or one that checks
   that every reason names an aim number ("Aim 2"). Add it to `grade_run` and re-run `compare`.
3. **Change one thing.** Set `AGENT_MODEL` to another tool-calling model from OpenRouter, run agent v2
   again, and compare pass^3, tokens and seconds. Is the cheaper model good enough?
4. **Calibrate the judge.** Print 10 judge verdicts (`agent_v2[0]["grades"]["v2"]["judge"]["verdicts"]`),
   write your own pass/fail for each, and count disagreements. Change `JUDGE_PROMPT` and try again.
5. **Stricter pass rule.** Make related pairs count towards pass/fail too (e.g. related recall ≥ 0.5).
   How do pass@1 and pass^3 change for the agent and the workflow?
""")

nb = nbf.v4.new_notebook(cells=cells)
nb.metadata = {"colab": {"provenance": [], "toc_visible": True},
               "kernelspec": {"name": "python3", "display_name": "Python 3"},
               "language_info": {"name": "python"}}


# =====================================================================================  data files
DATA_README = f"""# Tutorial 5 data — weekly paper triage for a microplastics lab

50 real paper abstracts, served as 8 weekly feeds to a paper-triage agent, plus the answer keys used to
grade it. Used by `../05_evaluating_a_triage_agent.ipynb`, which loads these files from the tag `{DATA_TAG}`.

| File | What it is |
|---|---|
| `projects.md` | The lab's three projects and the rules for judging relevance (core / related / not relevant). The agent's prompt v2 is this text. |
| `papers.csv` | The 50 papers: `paper_id`, `week` (the feed it appears in), `title`, `authors`, `source`, `posted`, `url`, `license`, `abstract`. |
| `answer_key.csv` | Answer key v2, one row per paper. `P1`, `P2`, `P3`: `core`, `related` or empty (not relevant). `acceptable`: extra projects an expert could defend, which graders do not penalise. `reason_P1..3`: an expert's reference reason (the LLM judge uses it for calibration). `difficulty`: easy / medium / hard (hard = deliberate near-misses). `note`: why a label is tricky. |
| `answer_key_v1.csv` | The first, topic-only answer key (`yes` or empty, no levels). Kept to show how changing the eval changes the score. |
| `tasks.json` | The 8 eval tasks (one per week): `feed` (paper IDs in order), `already_triaged` (what the lab database holds from earlier weeks), `reposted` (papers that reappear and must not be triaged again). |

**The three projects** — measure, understand, capture:
P1 detecting small microplastics in drinking water · P2 microplastic transport from urban rivers to the
estuary · P3 capturing microplastics from water with biochar.

**Twists in the tasks.** Week 4 contains no relevant paper (the agent should still send a digest).
In week 6, `MP052` from week 2 reappears and must be skipped.

**Sources and licences.** Preprints from bioRxiv, ChemRxiv, EarthArXiv and arXiv under Creative Commons
licences, and journal articles found through PubMed in open-access journals that publish under CC BY 4.0
(MDPI, Frontiers, Beilstein Journal of Nanotechnology; licence taken from the journal's policy). Each row
keeps the authors, a link to the original and the licence. Abstracts are verbatim apart from whitespace and
markup clean-up. Copyright stays with the authors; this data is for non-commercial teaching. Please cite the
original papers, not this folder.
"""

P = ("P1", "P2", "P3")
PAPER_FIELDS = ["paper_id", "week", "title", "authors", "source", "posted", "url", "license", "abstract"]


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def export_data(out):
    out.mkdir(parents=True, exist_ok=True)
    papers = sorted(json.loads((DATA / "papers.json").read_text()), key=lambda p: p["paper_id"])
    gold = json.loads((DATA / "gold.json").read_text())
    gold_v1 = json.loads((DATA / "gold_v1.json").read_text())
    write_csv(out / "papers.csv", [{k: p[k] for k in PAPER_FIELDS} for p in papers])
    write_csv(out / "answer_key.csv", [
        dict(paper_id=p["paper_id"], **{x: gold[p["paper_id"]]["labels"].get(x, "") for x in P},
             acceptable=" ".join(gold[p["paper_id"]]["acceptable"]),
             **{f"reason_{x}": gold[p["paper_id"]]["reasons"].get(x, "") for x in P},
             difficulty=gold[p["paper_id"]]["difficulty"], note=gold[p["paper_id"]]["note"]) for p in papers])
    write_csv(out / "answer_key_v1.csv", [
        dict(paper_id=p["paper_id"], **{x: "yes" if x in gold_v1[p["paper_id"]]["projects"] else "" for x in P},
             acceptable=" ".join(gold_v1[p["paper_id"]].get("acceptable", []))) for p in papers])
    shutil.copy(DATA / "projects.md", out / "projects.md")
    shutil.copy(DATA / "tasks.json", out / "tasks.json")
    (out / "README.md").write_text(DATA_README)


export_data(OUT_DIR / "data")
nbf.write(nb, OUT)
print("wrote", OUT_DIR, "-", sorted(p.name for p in (OUT_DIR / "data").iterdir()),
      f"- notebook {OUT.stat().st_size // 1024} KB, {len(cells)} cells")
