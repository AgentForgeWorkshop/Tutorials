# Evaluating AI agents — Tutorial 5 hands-on

Example 1 builds a weekly **paper-triage agent** for a (fictional) microplastics lab and evaluates it.
Each week the agent reads new papers, decides which of three projects each paper is relevant to
(**core** or **related**), saves its decisions, and sends one digest.

| Project | Topic |
|---|---|
| P1 | Detecting small microplastics in drinking water (measure) |
| P2 | Microplastic transport from urban rivers to the estuary (understand) |
| P3 | Capturing microplastics from water with biochar (capture) |

## What is in here

```
data/
  projects.md      project descriptions + relevance rules (prompt v2 uses this text)
  papers.json      50 real paper abstracts (frozen corpus, 8 weekly feeds)
  tasks.json       the eval suite: one task per week (feed, database state, a reposted paper)
  gold.json        answer key v2: core / related per project, acceptable extras, reference reasons
  gold_v1.json     answer key v1: topic-only (used to show "improve the eval")
example1/
  env.py           the environment: feed, lab database, outbox, tool functions, trace log
  prompts.py       prompt v1 vs v2 (they differ only in the project description)
  agent.py         System A — agent (LangChain create_agent; the LLM picks tools and order)
  workflow.py      System B — LLM workflow (code picks the steps; LLM labels papers + writes digest)
  graders.py       code graders (labels, digest, trace, cost), LLM judge for reasons, pass@k / pass^k
  harness.py       platform-free eval harness: tasks x trials -> run -> grade -> summary
  langsmith_eval.py  the same eval as LangSmith experiments (dataset, evaluators, repetitions)
tests/             pytest, no API keys needed
scripts/
  make_tasks.py             rebuilds data/tasks.json from papers.json
  build_public.py           writes notebook/ (participant notebook + CSV data + data README)
  check_public_notebook.py  runs that notebook with real models (local data) and checks it against example1/
  build_review_page.py      HTML page of the answer key, for checking labels by eye
notebook/                   GENERATED — the participant notebook + data (opened from Colab)
```

See **HANDOFF.md** for the full context, decisions, results so far and next steps.

## Participant notebook (public)

`notebook/05_evaluating_a_triage_agent.ipynb` walks through the same eval in plain Python:
task and data, the agent and its trace, graders, the harness (pass@k / pass^k), prompt v1 vs v2,
answer key v1 vs v2, and agent vs LLM workflow. It loads its data from the public Tutorials repo at the
tag `tutorial5-v1`. Keys come from Colab Secrets (`OPENROUTER_API_KEY`, optional `LANGSMITH_API_KEY`), as
in Tutorial 1.

```bash
uv run python scripts/build_public.py           # after changing data/, prompts or graders
uv run python scripts/check_public_notebook.py  # must print "cell errors: none" and "MISMATCHES 0"
```

## Setup (your laptop) — with uv

```bash
uv sync                     # creates .venv with the exact locked versions (uv.lock)
cp .env.example .env        # add OPENROUTER_API_KEY (and LANGSMITH_API_KEY for tracing)
uv run pytest -q            # sanity check, free
```

Then prefix commands with `uv run`, e.g. `uv run python -m example1.harness run ...`.
Without uv: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.

In **Colab** you don't need uv: the participant notebook installs what it needs with `pip` in its first cell.

## Run the evals

```bash
# real runs (OpenRouter)
uv run python -m example1.harness run --system agent    --prompt v1 --trials 3
uv run python -m example1.harness run --system agent    --prompt v2 --trials 3
uv run python -m example1.harness run --system workflow --prompt v2 --trials 3

uv run python -m example1.harness summary results/agent-v1.jsonl results/agent-v2.jsonl results/workflow-v2.jsonl
uv run python -m example1.harness summary results/agent-v2.jsonl --gold v1     # re-score with the old key
uv run python -m example1.harness errors  results/agent-v1.jsonl               # error analysis
```

With `LANGSMITH_TRACING=true` and a LangSmith key in `.env`, every run's trace appears in LangSmith.

## LangSmith experiments (instructor demo)

One experiment = one version of the system on the 8 weekly tasks, 3 repetitions each.

```bash
uv run python -m example1.langsmith_eval upload              # once: dataset "mp-triage-weeks"
uv run python -m example1.langsmith_eval run agent v1        # ~5-10 min each
uv run python -m example1.langsmith_eval run agent v2
uv run python -m example1.langsmith_eval run workflow v2
uv run python -m example1.langsmith_eval rescore <agent-v2 experiment name>   # answer key v1, no new runs
```

In LangSmith: **Datasets & Experiments → mp-triage-weeks**. Pin `agent-v1` as **baseline**, select the
experiments and click **Compare**: green/red marks the weeks each score improved or regressed.
Per-run scores: passed, core/related recall, precision, level accuracy, reason_pass (judge), read_before_save,
duplicate_saves, digest_ok, repost_detected, llm_calls, tokens. Experiment-level: pass@1, pass@3, pass^3.
After `rescore`, the agent-v2 experiment also shows the same scores with the suffix `(key v1)`.

## The story the results tell (slides 30+)

1. **Agent v1** — traces, scores, pass@k / pass^k.
2. **Improve the agent** — prompt v1 → v2 (only the project description changes).
3. **Improve the eval** — re-score the same agent-v2 runs with answer key v1 vs v2.
4. **Agent vs LLM workflow** — same eval, same model, same spec; compare quality, consistency, cost.

Paper abstracts are from bioRxiv, ChemRxiv, EarthArXiv, arXiv and PubMed (open-access journals);
each record keeps its authors, link and licence. Lightly normalised (whitespace, markup artefacts).
