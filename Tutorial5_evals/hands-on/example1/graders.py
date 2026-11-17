"""Graders for Example 1 (the What x How grid from the talk).

                  code-based                                  LLM-as-judge
  Outcome   label_grades (projects, levels), digest_grades    judge_reasons ("how is it relevant")
  Trace     trace_grades (read before save, no duplicates...)
  Ops       ops_grades (LLM calls, tokens, latency)
  Human     -> LangSmith annotation queue on a sample of reasons (to calibrate the judge)

`week_pass` turns one run into pass/fail, so repeated trials give pass@k and pass^k.
"""
import json
import re
from math import comb
from typing import Literal

from pydantic import BaseModel, Field

from . import data


# ------------------------------------------------------------------ helpers
def to_triage(task: dict) -> list[str]:
    """Papers the system is expected to triage this week (reposted papers are excluded)."""
    return [pid for pid in task["feed"] if pid not in set(task["already_triaged"])]


def predicted_pairs(result: dict, papers_to_triage: list[str]) -> dict:
    """{(paper_id, project): level} from the saved records (first save wins)."""
    pred = {}
    for r in result["saved"]:
        if r["paper_id"] in papers_to_triage:
            pred.setdefault((r["paper_id"], r["project"]), r["level"])
    return pred


# ------------------------------------------------------------------ outcome: labels (code)
def label_grades(result: dict, task: dict, gold: dict) -> dict:
    todo = to_triage(task)
    pred = predicted_pairs(result, todo)
    gold_pairs = {(pid, p): lvl for pid in todo for p, lvl in gold[pid]["labels"].items()}
    acceptable = {(pid, p) for pid in todo for p in gold[pid]["acceptable"]}
    has_levels = any(l is not None for g in gold.values() for l in g["labels"].values())  # v2: yes, v1: no

    core = {k for k, l in gold_pairs.items() if l in ("core", None)}
    related = {k for k, l in gold_pairs.items() if l == "related"}
    tp = set(pred) & set(gold_pairs)
    acc_hits = (set(pred) - set(gold_pairs)) & acceptable
    fp = set(pred) - set(gold_pairs) - acceptable

    def frac(a, b):
        return round(len(a) / len(b), 4) if b else 1.0

    level_checked = [k for k in tp if gold_pairs[k] is not None]
    level_ok = [k for k in level_checked if pred[k] == gold_pairs[k]]
    false_core = sorted(k for k in fp if pred[k] == "core")
    precision = round((len(tp) + len(acc_hits)) / len(pred), 4) if pred else 1.0
    w_recall = ((len(tp & core) + 0.5 * len(tp & related)) / (len(core) + 0.5 * len(related))
                if (core or related) else 1.0)
    f1 = 2 * precision * w_recall / (precision + w_recall) if (precision + w_recall) else 0.0
    retriaged = sorted({r["paper_id"] for r in result["saved"] if r["paper_id"] in set(task["already_triaged"])})
    return dict(
        core_recall=frac(tp & core, core),
        related_recall=frac(tp & related, related) if related else None,  # None: nothing related to find
        precision=precision,
        weighted_f1=round(f1, 4),
        level_accuracy=round(len(level_ok) / len(level_checked), 4) if level_checked else None,
        n_pred=len(pred), n_gold=len(gold_pairs),
        missed_core=sorted(core - tp), missed_related=sorted(related - tp),
        false_positives=sorted(fp), false_core=false_core, acceptable_hits=sorted(acc_hits),
        level_mismatches=sorted((k, pred[k], gold_pairs[k]) for k in level_checked if k not in level_ok),
        retriaged=retriaged, gold_has_levels=has_levels,
    )


# ------------------------------------------------------------------ outcome: digest (code)
def parse_digest(text: str) -> set:
    pairs, section = set(), None
    for line in text.splitlines():
        h = re.match(r"^\s*#+\s*(P[123])\b", line)
        if h:
            section = h.group(1)
            continue
        if section:
            for pid in re.findall(r"\bMP\d{3}\b", line):
                pairs.add((pid, section))
    return pairs


def digest_grades(result: dict, task: dict) -> dict:
    digests = result["digests"]
    text = digests[-1] if digests else ""
    saved = {(r["paper_id"], r["project"]) for r in result["saved"]}
    shown = parse_digest(text)
    return dict(
        digest_count=len(digests),
        digest_sent_once=len(digests) == 1,
        digest_format_ok=all(re.search(rf"^\s*#+\s*{p}\b", text, re.M) for p in data.PROJECTS),
        digest_coverage=round(len(saved & shown) / len(saved), 4) if saved else 1.0,
        digest_unsaved_mentions=sorted(shown - saved),
    )


# ------------------------------------------------------------------ trace (code)
def trace_grades(result: dict, task: dict) -> dict:
    log = result["tool_log"]
    todo = to_triage(task)
    read_at, checked, saves, seen_pairs, dups = {}, set(), [], set(), 0
    for e in log:
        pid = e["args"].get("paper_id")
        if e["tool"] == "read_paper" and e["ok"]:
            read_at.setdefault(pid, e["step"])
        elif e["tool"] == "check_database":
            checked.add(pid)
        elif e["tool"] == "save_triage" and e["ok"]:
            saves.append(e)
            key = (pid, e["args"]["project"])
            dups += key in seen_pairs
            seen_pairs.add(key)
    before = [s for s in saves if read_at.get(s["args"]["paper_id"], 10**9) < s["step"]]
    return dict(
        read_all_papers=all(pid in read_at for pid in todo),
        read_before_save=round(len(before) / len(saves), 4) if saves else 1.0,
        checked_database_all=all(pid in checked for pid in task["feed"]),
        repost_detected=all(pid in checked for pid in task["reposted"]) and not any(
            s["args"]["paper_id"] in task["reposted"] for s in saves),
        duplicate_saves=dups,
        invalid_tool_calls=sum(1 for e in log if not e["ok"]),
        n_tool_calls=len(log),
    )


# ------------------------------------------------------------------ operational (code)
def ops_grades(result: dict) -> dict:
    u = result.get("usage", {})
    return dict(llm_calls=u.get("llm_calls", 0), input_tokens=u.get("input_tokens", 0),
                output_tokens=u.get("output_tokens", 0), total_tokens=u.get("total_tokens", 0),
                latency_s=result.get("latency_s"), error=result.get("error"))


# ------------------------------------------------------------------ pass / fail for one run
def week_pass(labels: dict, digest: dict) -> bool:
    """One weekly run passes when:
      - every core (paper, project) pair was found,
      - nothing irrelevant was marked core   (answer key without levels: no false positives at all),
      - no paper already in the database was triaged again,
      - exactly one digest was sent.
    Related pairs earn partial credit in the scores but do not decide pass/fail."""
    blocking_fp = labels["false_core"] if labels["gold_has_levels"] else labels["false_positives"]
    return (labels["core_recall"] == 1.0 and not blocking_fp and not labels["retriaged"]
            and digest["digest_sent_once"])


# ------------------------------------------------------------------ LLM judge for reasons
class ReasonVerdict(BaseModel):
    paper_id: str
    project: str
    specific: bool = Field(description="Names what in the paper connects to which aim of the project")
    faithful: bool = Field(description="Every claim, number and finding is supported by the abstract")
    fits_level: bool = Field(description="core: says how it advances an aim; related: says what the lead would do with it (compare, borrow, cite)")
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
{projects}"""


def judge_reasons(result: dict, task: dict, gold: dict, judge_model) -> dict:
    todo = to_triage(task)
    pred_reason = {}
    for r in result["saved"]:
        if r["paper_id"] in todo:
            pred_reason.setdefault((r["paper_id"], r["project"]), (r["level"], r["reason"]))
    items = [k for k in pred_reason if k[1] in gold[k[0]]["labels"]]  # judge correctly-found pairs
    if not items:
        return dict(reason_pass_rate=None, reason_verdicts=[])
    papers = data.papers()
    payload = [dict(paper_id=pid, project=proj, level=pred_reason[(pid, proj)][0],
                    assistant_reason=pred_reason[(pid, proj)][1],
                    reference_reason=gold[pid]["reasons"].get(proj, ""),
                    title=papers[pid]["title"], abstract=papers[pid]["abstract"]) for pid, proj in items]
    judge = judge_model.with_structured_output(ReasonVerdicts, method="function_calling")
    out = judge.invoke([("system", JUDGE_PROMPT.format(projects=data.projects_text())),
                        ("user", json.dumps(payload, ensure_ascii=False))],
                       config={"run_name": f"judge reasons {task['task_id']}", "tags": ["example1", "judge"]})
    verdicts = [v.model_dump() for v in out.verdicts]
    passed = sum(v["verdict"] == "pass" for v in verdicts)
    return dict(reason_pass_rate=round(passed / len(verdicts), 4) if verdicts else None,
                reason_verdicts=verdicts)


# ------------------------------------------------------------------ everything for one run
def grade_run(result: dict, task: dict, gold_version: str = "v2", judge_model=None) -> dict:
    gold = data.gold(gold_version)
    labels = label_grades(result, task, gold)
    digest = digest_grades(result, task)
    g = dict(task_id=task["task_id"], system=result["system"], gold=gold_version,
             passed=week_pass(labels, digest), labels=labels, digest=digest,
             trace=trace_grades(result, task), ops=ops_grades(result))
    if judge_model is not None:
        g["judge"] = judge_reasons(result, task, gold, judge_model)
    return g


# ------------------------------------------------------------------ trials -> pass@k, pass^k
def pass_at_k(n: int, c: int, k: int) -> float:
    """P(at least one of k sampled trials passes) — unbiased estimator from n trials with c passes."""
    return 1.0 if n - c < k else 1.0 - comb(n - c, k) / comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """P(all k sampled trials pass) — unbiased estimator C(c,k)/C(n,k)."""
    return comb(c, k) / comb(n, k) if k <= n else float("nan")
