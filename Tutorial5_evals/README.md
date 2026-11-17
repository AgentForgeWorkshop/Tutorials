# Tutorial 5 — Evaluating AI Agents

In this hands-on you evaluate a small AI agent the way you would in a real project: you look at the
data, run the agent many times, grade every run, and use the scores to decide what to change.

**The agent.** A (fictional) microplastics lab gets new research papers every week. The agent reads
them, decides which of the lab's three projects each paper matters to (**core** or **related**),
saves its decisions in the lab database, and sends one weekly digest.

**What you will do** (about 45 minutes):

| # | Part | Time |
|---|---|---|
| 1 | [Before the session: keys](#1-before-the-session-keys) | 10 min, at home |
| 2 | [Look at the data](#2-look-at-the-data) | 5 min |
| 3 | [The words we use, and where they are in the code](#3-the-words-we-use-and-where-they-are-in-the-code) | 2 min |
| 4 | [Run the notebook](#4-run-the-notebook) | 30 min |
| 5 | [See it in LangSmith (optional)](#5-see-it-in-langsmith-optional) | 5 min |
| 6 | [Going further](#6-going-further) | — |

---

## 1. Before the session: keys

You need one key and can add a second.

**OpenRouter (required).** One account gives you many models through one API. The notebook uses a
small model for the agent and a larger one as the judge.

1. Sign up at <https://openrouter.ai>.
2. Add credit (**Credits** page). The full notebook costs about **$2**, plus about **$1** for the
   optional LangSmith step. $5 leaves room to experiment.
3. Create a key (**Keys** page) and copy it.

**LangSmith (optional, free).** An eval platform: it stores every run as a trace you can click
through, and shows experiments as tables you can compare.

1. Sign up at <https://smith.langchain.com>. The free plan is enough.
2. Open **Settings → API Keys**, create a key, and copy it. It is shown only once.

**Put the keys in Colab, never in a cell.** A key pasted into a cell is saved with the notebook, and
notebooks get shared.

1. Open the notebook (Colab badge in [part 4](#4-run-the-notebook)).
2. Click the **key icon** in the left sidebar (**Secrets**).
3. Add a secret named exactly `OPENROUTER_API_KEY`, paste the key, and turn on **Notebook access**.
4. Optional: add `LANGSMITH_API_KEY` the same way.

---

## 2. Look at the data

Read the data before you read any score. A score is only as good as the answer key behind it.

All files are in [`hands-on/notebook/data/`](hands-on/notebook/data/). GitHub shows the CSV files as
searchable tables. The folder's [README](hands-on/notebook/data/README.md) explains every column.

| File | What it is |
|---|---|
| [`projects.md`](hands-on/notebook/data/projects.md) | The three projects and the rules for **core / related / not relevant**. The agent's prompt uses this same text, so the agent and the eval share one spec. |
| [`papers.csv`](hands-on/notebook/data/papers.csv) | 50 real paper abstracts, each with the week it arrives. |
| [`answer_key.csv`](hands-on/notebook/data/answer_key.csv) | The expected label for every paper and project, plus extras an expert could defend, a reference reason, and a note on why a label is tricky. |
| [`answer_key_v1.csv`](hands-on/notebook/data/answer_key_v1.csv) | An older, topic-only answer key. You will see how changing the key changes the score. |
| [`tasks.json`](hands-on/notebook/data/tasks.json) | The 8 weekly tasks: which papers arrive, and what is already in the lab database. |

**Three things to find (5 minutes):**

1. In `projects.md`, read the rules for **P3** (capturing microplastics with biochar). What makes a
   paper **related** rather than core?
2. In `answer_key.csv`, find **MP058**. It mentions biochar *and* microplastics. Why is it not
   relevant to any project? (Read its `note`.) Papers like this are deliberate near-misses.
3. In `tasks.json`, look at **week 4** and **week 6**. Week 4 has nothing relevant (the agent must
   still send a digest). In week 6, a paper from week 2 shows up again and must be skipped.

---

## 3. The words we use, and where they are in the code

Keep this table open while you run the notebook.

| Word | Meaning here | In the notebook |
|---|---|---|
| **Agent** | An LLM that decides which tools to call, in which order, until the job is done. | `run_agent` |
| **Environment** | What the agent acts on: the week's feed, the lab database, the outbox. Every tool call is logged. | `TriageEnv` |
| **Task** | One week: the papers that arrive plus the state of the database. | one entry of `TASKS` |
| **Eval suite** | All 8 tasks, plus the answer key that says what a good result is. | `TASKS` + `GOLD` |
| **Grader** | Code (or an LLM) that scores one run: labels, the trace (did it read before saving?), the digest, and the quality of the reasons. | `label_grades`, `trace_grades`, `digest_grades`, `judge_reasons` → `grade_run` |
| **Trial** | One more run of the same task. The agent is not deterministic, so each task runs 3 times. | `TRIALS = 3` |
| **Eval harness** | The code around the agent: runs every task × every trial, grades each run, sums up. | `run_suite`, `summarize`, `compare` |
| **pass@k / pass^k** | At least one of *k* tries passes / **all** *k* tries pass. For a weekly job, pass^k is the one to watch. | `pass_at_k`, `pass_hat_k` |
| **Experiment** | One version of the system run over the whole suite. Compare experiments to decide what to ship. | each `run_suite(...)` result; in LangSmith, one `evaluate(...)` |

---

## 4. Run the notebook

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AgentForgeWorkshop/Tutorials/blob/main/Tutorial5_evals/hands-on/notebook/05_evaluating_a_triage_agent.ipynb)

Run the cells from top to bottom. Each step ends with something to look at:

| Step | What | Look at |
|---|---|---|
| 0 | Setup | Does the model reply "ready"? |
| 1 | The task | One week's papers next to their expected labels. |
| 2 | The agent and one run | The trace: did it read every paper before saving? Did it skip the reposted paper? |
| 3 | Graders | Which check failed, and why. |
| 4 | The harness | pass@1 vs pass^3: how often it works vs how often it works *every* time. |
| 5 | Improve the agent: prompt v1 → v2 | Only the project description changes. Which scores move? |
| 6 | Improve the eval: the same runs, an older answer key | The agent did not change, but its score does. |
| 7 | Agent vs LLM workflow | Quality, consistency and cost. Which one would you ship? |
| 8 | *Optional:* the same eval in LangSmith | See part 5. |

Steps 4, 5 and 7 each run 24 weeks of work (8 tasks × 3 trials) and take a few minutes.

---

## 5. See it in LangSmith (optional)

In Step 0, set `USE_LANGSMITH = True` and re-run that cell. Then:

- **Traces.** Every agent run appears in LangSmith under **Tracing** in the project
  `tutorial5-paper-triage-v2`. Open one to see each model call and tool call in order: the same
  trace you printed in Step 2, but clickable.
- **Experiments (Step 8).** Step 8 uploads the 8 tasks as a dataset (`mp-triage-weeks`) and runs the
  agent as an experiment. Find it under **Datasets & Experiments → mp-triage-weeks → Experiments**:
  one row per week, one column per score. Sort by `passed`, open a failing week, read its trace.
  Run Step 8 again with prompt `"v1"`, select both experiments and click **Compare**.

Traces of runs inside an experiment live in the experiment, not in the tracing project.

---

## 6. Going further

- The **exercises** at the end of the notebook: find out whether a failure is the agent's fault or the
  answer key's, add your own grader, try a cheaper model, check the judge against your own verdicts.
- The full **instructor version** is in [`hands-on/`](hands-on/): the same agent, graders and harness as
  Python modules, a command-line harness, the LangSmith experiments, and tests. Start with
  [`hands-on/README.md`](hands-on/README.md).
