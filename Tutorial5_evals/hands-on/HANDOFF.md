# Hand-off — Tutorial 5 hands-on (evaluating AI agents)

Status as of 2026-11-13. Read this before changing anything; `CLAUDE.md` has the short rules.

## 1. Context

- **Event:** AgentForge Workshop, Tutorial 5. Slides 1–28 are the talk (why evals; eval in the dev loop;
  what to evaluate = outcome / trace / operational; how = task, grader, metrics, trials; graders =
  code / LLM judge / human; benchmarks; pass@k and pass^k). Slides 30+ are the hands-on (~45 min).
- **Example 1** (built here): a weekly **paper-triage agent** for a fictional microplastics lab, and its eval.
  Shown live by the instructor (LangSmith) and done by participants in a Colab notebook.
- **Example 2** (not built): a 3–4 minute *teaser* only — a literature-review agent on Claude Code
  (open-ended output, live web, LLM judge + must-cite list + citation checks). Pre-run, show results.
- Previous tutorials live in the GitHub org `AgentForgeWorkshop/Tutorials` (Tutorial 1 = `01a_what_is_an_agent.ipynb`:
  Colab badge, step table with minutes, `get_key()` from Colab Secrets, OpenRouter via `init_chat_model`).
  The Tutorial 5 notebook copies that style.

## 2. Decisions (and why)

| Topic | Decision |
|---|---|
| Task | Each week: read new papers, label each paper per project as **core / related / not relevant**, save decisions, send one digest. |
| Projects | One story, *measure → understand → capture*: **P1** detecting small MPs (1–20 µm) in drinking water; **P2** MP transport from urban rivers to the estuary; **P3** capturing MPs from water **with biochar** (P3 was "effects on invertebrates" earlier; changed by the instructor). |
| Relevance | **core** = advances an aim; **related** = the lead would *compare / borrow / cite* it; **not relevant** = only "also about MPs", or same material but different task (biochar for cadmium). Written in `data/projects.md` — the single spec used by prompt v2 *and* by the labels. |
| Acceptable extras | Per paper, extra projects an expert could defend; graders don't penalise them. |
| Data | 50 real abstracts (bioRxiv, ChemRxiv, EarthArXiv, arXiv; PubMed for open-access CC BY journals — MDPI, Frontiers, Beilstein). Found with the Valency papers connector. Many deliberate near-misses (biochar for nutrients/cadmium/soil, other capture materials, ocean transport, tadpoles…). |
| Tasks | 8 weekly tasks (`data/tasks.json`). Week 4: nothing relevant (must still send a digest). Week 6: `MP052` from week 2 is reposted and must be skipped (database check). |
| Answer keys | `gold.json` = v2 (levels). `gold_v1.json` = the earlier topic-only key, kept to show "improve the eval" by re-scoring the same runs. |
| Architecture | **Agent inside a workflow**: fixed code loads the week and resets the env; inside, a LangChain `create_agent` agent with 5 tools (`list_new_papers`, `read_paper`, `check_database`, `save_triage`, `send_digest`). Every tool call is logged = the trace. |
| Comparison B | **LLM workflow**: code loops over papers, 1 structured-output call per paper + 1 digest call. Same env, tools, model, graders. Its classify prompt reuses the agent's wording (minus tool steps) and its input is exactly the `read_paper` JSON — only the architecture differs. |
| Prompts | v1 = project titles + "core if directly relevant, related if somewhat relevant"; v2 = full `projects.md`. Nothing else differs. |
| Pass rule (one run = one week) | all core pairs found; nothing irrelevant marked core (answer key v1: no false positives at all); no re-triage; exactly one digest. Related pairs and judge scores are reported but don't decide pass/fail (a deliberate choice; exercise 5 makes it stricter). |
| Metrics | core / related recall, precision (acceptable counts as correct), level accuracy, judge reason pass rate, trace checks (read before save, repost detected, duplicate saves), LLM calls / tokens / seconds, pass@1, pass@k, pass^k (exact estimators). |
| LLM judge | Grades only the *reasons* of correctly found pairs: specific / faithful / fits level → pass/fail, with the expert reference reason for calibration. Same model family as the agent → mention self-preference risk; calibrate with ~10 human verdicts. |
| Models | Through OpenRouter with `langchain-openai` (`init_chat_model("openai:<id>", base_url="https://openrouter.ai/api/v1")`). Agent/workflow: `openai/gpt-5-mini`. Judge: `openai/gpt-5.6-terra`. No temperature set (gpt-5 models need the default; trials need natural variation). |
| Keys | `get_key()`: Colab Secrets → env / `.env` → prompt. Never paste keys into cells. |
| Versions | `langchain==1.4.2`, `langchain-openai==1.6.2` (same as Tutorial 1), Python ≥ 3.11, uv + `uv.lock`. |
| Repos | Everything (instructor code, harness, tests, scripts) lives in the **public** `AgentForgeWorkshop/Tutorials` repo under `Tutorial5_evals/hands-on/`; the participant notebook + CSV data are generated into `notebook/` there (changed 2026-11-17; was a separate private repo). The notebook loads data from GitHub pinned to tag **`tutorial5-v1`**. |
| Simplicity | The instructor wants the simplest code that does the job. Prefer deleting over adding. |

## 3. Demo story and run sheet (45 min)

| Min | Part | Talk link |
|---|---|---|
| 0–3 | Platforms (LangSmith, Langfuse, Braintrust, Arize Phoenix; promptfoo; Harbor) | — |
| 3–9 | Example 1 setup: projects, data, agent, graders | slides 10–17 |
| 9–18 | Agent v1 in LangSmith: traces, scores, pass@k / pass^k | 7, 22, backup |
| 18–25 | Improve the agent: prompt v1 → v2 (one change) | loop step 5 |
| 25–31 | Improve the eval: same runs re-scored with answer key v1 vs v2 | loop step 6 |
| 31–38 | Agent v2 vs LLM workflow: quality, consistency, cost → decision | slide 8 |
| 38–42 | Example 2 teaser | 16, 17, 26 |
| 42–45 | Wrap + participant notebook | — |

## 4. Where things are

```
data/                       SOURCE OF TRUTH (JSON + projects.md)
example1/                   instructor code: env, prompts, agent, workflow, graders, harness, fake_llm
tests/                      pytest (free)
example1/langsmith_eval.py  the same eval as LangSmith experiments (instructor demo)
scripts/build_public.py     generates notebook/ (notebook + CSVs + data README)
scripts/check_public_notebook.py   executes that notebook in dry-run mode, compares with example1/
scripts/make_tasks.py       regenerates data/tasks.json (repost config inside)
scripts/build_review_page.py       HTML view of the answer key for checking labels
notebook/                   GENERATED — participant notebook + data
```

The participant notebook's code is a readable copy of `example1/` (same logic, written inline for teaching).
`check_public_notebook.py` proves they agree (graders and answer keys: 0 mismatches).

## 5. How to

```bash
uv sync && cp .env.example .env                 # add OPENROUTER_API_KEY (+ LANGSMITH_API_KEY)
uv run pytest -q                                 # 7 tests, free
uv run python -m example1.harness run --system agent --prompt v2 --trials 3 --fake   # free dry run
uv run python -m example1.harness run --system agent --prompt v1 --trials 3          # real
uv run python -m example1.harness summary results/*.jsonl
uv run python -m example1.harness summary results/agent-v2.jsonl --gold v1           # re-score, no new runs
uv run python -m example1.harness errors results/agent-v1.jsonl

uv run python scripts/build_public.py && uv run python scripts/check_public_notebook.py
```

**Publish the participant folder**
1. Rebuild `notebook/`, commit, merge to `main` of `AgentForgeWorkshop/Tutorials`.
2. Create and push the tag: `git tag tutorial5-v1 && git push origin tutorial5-v1`
   (the notebook's data URLs only work once the tag exists).
3. Open the notebook from its Colab badge and run it once with a real key (`DRY_RUN = False`).
4. Data changed later? Bump `DATA_TAG` in `scripts/build_public.py`, rebuild, commit, tag again.

## 6. Results so far (instructor's first real run of the participant notebook)

8 weeks × 3 trials, gpt-5-mini agent, gpt-5.6-terra judge. **The workflow column is from before the
workflow's prompt and input were aligned with the agent's** — re-run it.

| | agent v1 | agent v2 | workflow v2 (old, unaligned) |
|---|---|---|---|
| pass@1 | 0.667 | 0.958 | 0.750 |
| pass@3 | 0.750 | 1.000 | 0.875 |
| pass^3 | 0.625 | 0.875 | 0.500 |
| core recall | 0.958 | 1.000 | 0.981 |
| related recall | 0.680 | 0.684 | 0.857 |
| precision | 0.741 | 0.804 | 0.572 |
| level accuracy | 0.686 | 0.844 | 0.804 |
| reason pass (judge) | 0.615 | 0.825 | 0.759 |
| LLM calls / week | 17.3 | 19.0 | 7.3 |
| tokens / week | 53.7k | 82.3k | 20.1k |
| seconds / week | 55 | 65 | 37 |

- Agent v2 re-scored with answer key v1: pass@1 **0.958 → 0.083** (the "improve the eval" slide).
- The old workflow over-labelled (high related recall, low precision); a few extra *core* labels failed weeks.
  Hypotheses: one paper at a time (no comparison within the week), a forced output list invites filling it,
  and the prompt/input mismatch (now fixed). 23/24 vs 18/24 passes: p ≈ 0.1, so suggestive only.
- Step 2's single v1 run saved MP027/MP028 without reading them (read-before-save 0.75): a good live example
  of a trace grader.

## 7. Next steps (suggested order)

1. Publish the public folder + tag; test from the Colab badge with a real key.
2. Re-run the aligned workflow; update the Step 7 text and the slide with what it shows.
3. Instructor LangSmith demo — **script written: `example1/langsmith_eval.py`** (see README). Run `upload`, then
   the three experiments before the session, then `rescore` the agent-v2 experiment; pin agent-v1 as baseline
   and use Compare. Do one live run during the talk. Tested offline against a stub server (24 runs per
   experiment, all scores and pass@k/pass^k correct); **not yet run against real LangSmith**, and `rescore`
   (evaluating an existing experiment) could not be tested offline at all — check it first.
4. Slides 30–39: platforms; Example 1 (task, What×How grid, results tables, the three comparisons);
   check backup slide on pass^k (exact estimator C(c,k)/C(n,k) gives 30% where (pass@1)^k gives 36% for n=5, c=3, k=2).
5. Judge calibration: label ~10 verdicts by hand; consider a judge from another model family.
6. Example 2 teaser: build and pre-run (needs an Anthropic key; Claude Code doesn't run through OpenRouter).
7. Optional: 5 trials instead of 3 for firmer comparisons; check gpt-5.6-terra cost.

## 8. Gotchas

- **Edit the notebook through `scripts/build_public.py`, not by hand** — or port hand edits back, then rebuild.
  Cell code sits inside `'''…'''` strings there: write `\\n` to get `\n` in the notebook, `\\s` for regex `\s`.
- **Dry-run hooks** (the scripted model in `fake_llm.py` and the notebook's hidden cell): the workflow's user
  message must contain `Paper MPxxx`; the digest system prompt must start with
  `You write the weekly paper digest`; structured-output schemas are named `PaperDecision` and `ReasonVerdicts`.
- **The fake model is not a result.** Never report dry-run numbers.
- The env is thread-safe (an `RLock`) because agents issue parallel tool calls; removing it crashes SQLite.
- CSV week numbers load as numpy ints; the notebook casts them with `int()` for SQLite.
- `ChatOpenAI` + OpenRouter: structured output uses `method="function_calling"` (works for any tool-calling model).
- LangSmith traces are appended, never replaced; the notebook's `@traceable` groups each workflow week into one trace.
- LangSmith experiments: per-run evaluators may return a list of `{key, score}`, but **summary evaluators must
  return `{"results": [...]}`** in langsmith 0.14. Never set `LANGSMITH_TEST_CACHE` for these runs (identical
  cached calls would make repetitions identical and pass^k meaningless).
- Label provenance: the Valency exports and relabelling scripts were one-off and are not in this repo;
  `data/*.json` is now the source of truth.
- Licences: each paper keeps authors, link, licence. PubMed rows: CC BY inferred from the journal's policy.
  ChemRxiv rows: one of its three CC licences. Non-commercial teaching use.
