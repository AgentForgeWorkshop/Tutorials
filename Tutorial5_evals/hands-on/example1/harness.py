"""Eval harness without any platform: tasks x trials -> run -> grade -> summary.

    python -m example1.harness run --system agent --prompt v1 --trials 3
    python -m example1.harness run --system workflow --prompt v2 --trials 3
    python -m example1.harness summary results/*.jsonl            # compare systems
    python -m example1.harness summary results/agent-v2.jsonl --gold v1   # re-score, no new runs
    python -m example1.harness errors results/agent-v1.jsonl      # which papers go wrong most?
    add --fake to any `run` for a free dry run with a scripted model (no API keys needed)
"""
import argparse
import collections
import json
import pathlib
import statistics as st
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from . import config, data
from .graders import grade_run, pass_at_k, pass_hat_k


# ------------------------------------------------------------------ run
def run_one(system: str, prompt: str, task: dict, trial: int, model=None, judge_model=None, fake=False) -> dict:
    if fake:
        from .fake_llm import FakeTriageModel
        model = FakeTriageModel(seed=hash((task["task_id"], trial, system, prompt)) % 10**6,
                                error_rate=0.25 if prompt == "v1" else 0.08)
        judge_model = FakeTriageModel(seed=trial) if judge_model is not None else None
    if system == "agent":
        from .agent import run_agent
        result = run_agent(task, prompt, model=model)
    elif system == "workflow":
        from .workflow import run_workflow
        result = run_workflow(task, prompt, model=model)
    else:
        raise ValueError(system)
    grades = {"v2": grade_run(result, task, "v2", judge_model), "v1": grade_run(result, task, "v1")}
    return dict(run_id=uuid.uuid4().hex[:8], system=result["system"], task_id=task["task_id"], trial=trial,
                model=getattr(model, "model_name", None) or getattr(model, "model", None) or "fake",
                time=time.strftime("%Y-%m-%d %H:%M:%S"), result=result, grades=grades)


def run_suite(system="agent", prompt="v2", task_ids=None, trials=3, model=None, judge_model=None,
              judge=True, fake=False, out=None, concurrency=4, verbose=True) -> list[dict]:
    tasks = [t for t in data.tasks() if not task_ids or t["task_id"] in task_ids]
    if fake:
        judge_model = "fake" if judge else None
    else:
        model = model or config.make_model()
        judge_model = (judge_model or config.make_model(config.JUDGE_MODEL)) if judge else None
    jobs = [(t, k) for t in tasks for k in range(trials)]
    out = pathlib.Path(out or config.RESULTS_DIR / f"{system}-{prompt}{'-fake' if fake else ''}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    records = []
    with ThreadPoolExecutor(max_workers=concurrency) as pool, out.open("a") as f:
        futures = [pool.submit(run_one, system, prompt, t, k, model, judge_model, fake) for t, k in jobs]
        for fut in futures:
            rec = fut.result()
            records.append(rec)
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
            if verbose:
                g = rec["grades"]["v2"]
                print(f"{rec['system']:12s} {rec['task_id']} trial {rec['trial']}  "
                      f"{'PASS' if g['passed'] else 'fail'}  core_recall={g['labels']['core_recall']:.2f} "
                      f"precision={g['labels']['precision']:.2f}  calls={g['ops']['llm_calls']}"
                      f"{'  ERROR ' + rec['result']['error'] if rec['result']['error'] else ''}")
    if verbose:
        print(f"\nsaved {len(records)} runs to {out}")
    return records


def load(paths) -> list[dict]:
    recs = []
    for p in paths:
        recs += [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]
    return recs


# ------------------------------------------------------------------ summarise
def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(st.mean(xs), 3) if xs else None


def summarize(records: list[dict], gold: str = "v2", k: int | None = None) -> list[dict]:
    """One row per system: quality, consistency (pass@k, pass^k), process and cost."""
    if gold == "v1" or any(gold not in r["grades"] for r in records):
        from .graders import grade_run as _grade  # re-score stored results against another key
        for r in records:
            if gold not in r["grades"]:
                r["grades"][gold] = _grade(r["result"], data.task(r["task_id"]), gold)
    rows = []
    for system in sorted({r["system"] for r in records}):
        rs = [r for r in records if r["system"] == system]
        G = [r["grades"][gold] for r in rs]
        by_task = collections.defaultdict(list)
        for r, g in zip(rs, G):
            by_task[r["task_id"]].append(g["passed"])
        n_min = min(len(v) for v in by_task.values())
        kk = k or n_min
        row = dict(system=system, gold=gold, tasks=len(by_task), trials=n_min,
                   pass_at_1=_mean([sum(v) / len(v) for v in by_task.values()]),
                   **{f"pass@{kk}": _mean([pass_at_k(len(v), sum(v), kk) for v in by_task.values()]),
                      f"pass^{kk}": _mean([pass_hat_k(len(v), sum(v), kk) for v in by_task.values()])},
                   core_recall=_mean([g["labels"]["core_recall"] for g in G]),
                   related_recall=_mean([g["labels"]["related_recall"] for g in G]),
                   precision=_mean([g["labels"]["precision"] for g in G]),
                   level_accuracy=_mean([g["labels"]["level_accuracy"] for g in G]),
                   reason_pass=_mean([g.get("judge", {}).get("reason_pass_rate") for g in G]),
                   digest_ok=_mean([float(g["digest"]["digest_sent_once"] and g["digest"]["digest_format_ok"]) for g in G]),
                   read_before_save=_mean([g["trace"]["read_before_save"] for g in G]),
                   repost_detected=_mean([float(g["trace"]["repost_detected"]) for g, r in zip(G, rs)
                                          if data.task(r["task_id"])["reposted"]]),
                   duplicate_saves=sum(g["trace"]["duplicate_saves"] for g in G),
                   llm_calls=_mean([g["ops"]["llm_calls"] for g in G]),
                   tokens=_mean([g["ops"]["total_tokens"] for g in G]),
                   latency_s=_mean([g["ops"]["latency_s"] for g in G]),
                   errors=sum(1 for g in G if g["ops"]["error"]))
        rows.append(row)
    return rows


def print_table(rows: list[dict]):
    if not rows:
        return print("no runs")
    keys = list(rows[0].keys())
    print("\n".join(f"{k:18s}" + "".join(f"{str(r.get(k)):>16s}" for r in rows) for k in keys))


def error_report(records: list[dict], gold: str = "v2", top: int = 15):
    """Which (paper, project) pairs go wrong most often across trials — start of error analysis."""
    c = collections.Counter()
    for r in records:
        g = r["grades"].get(gold) or grade_run(r["result"], data.task(r["task_id"]), gold)
        L = g["labels"]
        for pid, proj in L["missed_core"]:
            c[(pid, proj, "missed core")] += 1
        for pid, proj in L["missed_related"]:
            c[(pid, proj, "missed related")] += 1
        for pid, proj in L["false_positives"]:
            c[(pid, proj, "false positive")] += 1
        for (pid, proj), got, want in L["level_mismatches"]:
            c[(pid, proj, f"level {got} (want {want})")] += 1
    papers = data.papers()
    for (pid, proj, kind), n in c.most_common(top):
        print(f"{n:3d} x  {pid} {proj}  {kind:28s} {papers[pid]['title'][:70]}")


# ------------------------------------------------------------------ CLI
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--system", choices=["agent", "workflow"], default="agent")
    r.add_argument("--prompt", choices=["v1", "v2"], default="v2")
    r.add_argument("--tasks", help="comma-separated task ids, e.g. week_01,week_04 (default: all)")
    r.add_argument("--trials", type=int, default=3)
    r.add_argument("--model", help="OpenRouter model id (default: AGENT_MODEL)")
    r.add_argument("--judge-model", help="OpenRouter model id (default: JUDGE_MODEL)")
    r.add_argument("--no-judge", action="store_true")
    r.add_argument("--fake", action="store_true", help="dry run with a scripted model, no API calls")
    r.add_argument("--concurrency", type=int, default=4)
    r.add_argument("--out")
    s = sub.add_parser("summary")
    s.add_argument("files", nargs="+")
    s.add_argument("--gold", choices=["v1", "v2"], default="v2")
    s.add_argument("--k", type=int)
    e = sub.add_parser("errors")
    e.add_argument("files", nargs="+")
    e.add_argument("--gold", choices=["v1", "v2"], default="v2")
    a = ap.parse_args()

    if a.cmd == "run":
        model = None if a.fake else config.make_model(a.model)
        judge_model = None if (a.no_judge or a.fake) else config.make_model(a.judge_model or config.JUDGE_MODEL)
        recs = run_suite(a.system, a.prompt, a.tasks.split(",") if a.tasks else None, a.trials,
                         model, judge_model, judge=not a.no_judge, fake=a.fake, out=a.out,
                         concurrency=a.concurrency)
        print_table(summarize(recs))
    elif a.cmd == "summary":
        print_table(summarize(load(a.files), a.gold, a.k))
    elif a.cmd == "errors":
        error_report(load(a.files), a.gold)


if __name__ == "__main__":
    main()
