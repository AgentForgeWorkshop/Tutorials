"""Example 1 as LangSmith experiments (instructor demo).

One experiment = one version of the system run over the 8 weekly tasks, 3 times each (repetitions).
Compare versions in the UI: Datasets & Experiments -> mp-triage-weeks -> select experiments -> Compare.

    uv run python -m example1.langsmith_eval upload                 # once: create the dataset
    uv run python -m example1.langsmith_eval run agent v1           # experiment "agent-v1-..."
    uv run python -m example1.langsmith_eval run agent v2
    uv run python -m example1.langsmith_eval run workflow v2
    uv run python -m example1.langsmith_eval rescore <agent-v2 experiment name>   # answer key v1, no new runs

Needs LANGSMITH_API_KEY and OPENROUTER_API_KEY (in .env).
Do not set LANGSMITH_TEST_CACHE here: cached calls would make the repetitions identical.
"""
import statistics
import sys
from collections import defaultdict

from langsmith import Client, evaluate

from . import config, data
from .agent import run_agent
from .graders import grade_run, judge_reasons, pass_at_k, pass_hat_k
from .workflow import run_workflow

DATASET = "mp-triage-weeks"
TRIALS = 3


# ------------------------------------------------------------------ dataset: one example per week
def examples() -> list[dict]:
    gold = data.gold("v2")
    return [dict(inputs=dict(task_id=t["task_id"], week=t["week"], feed=t["feed"], reposted=t["reposted"]),
                 outputs=dict(answer_key={pid: gold[pid]["labels"] for pid in t["feed"]
                                          if pid not in t["already_triaged"]}))
            for t in data.tasks()]


def upload():
    client = Client()
    if client.has_dataset(dataset_name=DATASET):
        return print(f"dataset {DATASET!r} already exists")
    ds = client.create_dataset(DATASET, description="Example 1: 8 weekly paper-triage tasks (Tutorial 5)")
    client.create_examples(dataset_id=ds.id, examples=examples())
    print(f"created dataset {DATASET!r} with {len(data.tasks())} examples")


# ------------------------------------------------------------------ target: the system under test
def target(system: str, prompt: str, model):
    run = run_agent if system == "agent" else run_workflow

    def triage_week(inputs: dict) -> dict:
        return run(data.task(inputs["task_id"]), prompt, model=model)
    return triage_week


# ------------------------------------------------------------------ evaluators (our graders)
def code_graders(gold: str = "v2"):
    """All code graders for one run; key v1 scores get a ' (key v1)' suffix."""
    def graders(inputs: dict, outputs: dict) -> list[dict]:
        g = grade_run(outputs, data.task(inputs["task_id"]), gold)
        L = g["labels"]
        scores = dict(passed=g["passed"], core_recall=L["core_recall"], related_recall=L["related_recall"],
                      precision=L["precision"], level_accuracy=L["level_accuracy"])
        if gold == "v2":  # process and cost do not depend on the answer key
            scores.update(read_before_save=g["trace"]["read_before_save"],
                          duplicate_saves=g["trace"]["duplicate_saves"],
                          digest_ok=g["digest"]["digest_sent_once"] and g["digest"]["digest_format_ok"],
                          llm_calls=g["ops"]["llm_calls"],
                          k_tokens=g["ops"]["total_tokens"] / 1000)  # LangSmith caps scores at 99,999
            if inputs["reposted"]:
                scores["repost_detected"] = g["trace"]["repost_detected"]
        sfx = "" if gold == "v2" else " (key v1)"
        return [dict(key=k + sfx, score=v) for k, v in scores.items() if v is not None]
    return graders


def reason_judge(judge_model):
    def reason_pass(inputs: dict, outputs: dict) -> dict:
        j = judge_reasons(outputs, data.task(inputs["task_id"]), data.gold("v2"), judge_model)
        return dict(key="reason_pass", score=j["reason_pass_rate"],
                    comment="; ".join(f"{v['paper_id']} {v['project']}: {v['comment']}"
                                      for v in j["reason_verdicts"] if v["verdict"] == "fail"))
    return reason_pass


def pass_k(gold: str = "v2"):
    """Experiment-level pass@1, pass@k and pass^k (k = repetitions) — not built into LangSmith."""
    def pass_metrics(runs: list, examples: list) -> dict:
        by_task = defaultdict(list)
        for r in runs:
            by_task[r.inputs["task_id"]].append(grade_run(r.outputs, data.task(r.inputs["task_id"]), gold)["passed"])
        k = min(len(v) for v in by_task.values())
        mean = lambda f: round(statistics.mean(f(len(v), sum(v)) for v in by_task.values()), 3)
        sfx = "" if gold == "v2" else " (key v1)"
        return {"results": [dict(key="pass@1" + sfx, score=mean(lambda n, c: c / n)),
                            dict(key=f"pass@{k}" + sfx, score=mean(lambda n, c: pass_at_k(n, c, k))),
                            dict(key=f"pass^{k}" + sfx, score=mean(lambda n, c: pass_hat_k(n, c, k)))]}
    return pass_metrics


# ------------------------------------------------------------------ experiments
def run_experiment(system: str, prompt: str, model=None, judge_model=None, data_=DATASET,
                   trials: int = TRIALS, upload_results: bool = True):
    model = model or config.make_model()
    judge_model = judge_model or config.make_model(config.JUDGE_MODEL)
    return evaluate(
        target(system, prompt, model), data=data_,
        evaluators=[code_graders("v2"), reason_judge(judge_model)],
        summary_evaluators=[pass_k("v2")],
        experiment_prefix=f"{system}-{prompt}",
        description=f"{system}, prompt {prompt}, {trials} repetitions",
        metadata=dict(system=system, prompt=prompt, models=[config.AGENT_MODEL], judge=config.JUDGE_MODEL),
        num_repetitions=trials, max_concurrency=4, upload_results=upload_results)


def rescore(experiment: str):
    """Score an existing experiment against answer key v1 — graders only, the system is not run again."""
    return evaluate(experiment, evaluators=[code_graders("v1")], summary_evaluators=[pass_k("v1")])


if __name__ == "__main__":
    cmd, *args = sys.argv[1:] or ["help"]
    if cmd == "upload":
        upload()
    elif cmd == "run" and len(args) == 2:
        print(run_experiment(*args))
    elif cmd == "rescore" and len(args) == 1:
        print(rescore(args[0]))
    else:
        print(__doc__)
