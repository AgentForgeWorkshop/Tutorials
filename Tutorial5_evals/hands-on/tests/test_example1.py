"""Tests for Example 1's graders and data — no API keys needed, no model calls.

    pytest -q
"""
from example1 import data
from example1.graders import (digest_grades, grade_run, label_grades, parse_digest, pass_at_k,
                              pass_hat_k, trace_grades, week_pass)


def perfect_result(task, gold_version="v2"):
    """A hand-built result that matches the answer key exactly."""
    gold = data.gold(gold_version)
    todo = [p for p in task["feed"] if p not in task["already_triaged"]]
    saved, log, step = [], [], 0
    for pid in task["feed"]:
        log.append(dict(step=step, tool="check_database", args={"paper_id": pid}, ok=True)); step += 1
        log.append(dict(step=step, tool="read_paper", args={"paper_id": pid}, ok=True)); step += 1
    for pid in todo:
        for proj, lvl in gold[pid]["labels"].items():
            saved.append(dict(paper_id=pid, project=proj, level=lvl or "core", reason="r"))
            log.append(dict(step=step, tool="save_triage", args=dict(paper_id=pid, project=proj), ok=True)); step += 1
    digest = "\n".join(f"## {p}\n" + "\n".join(f"- {s['paper_id']} ({s['level']}): t — r"
                                              for s in saved if s["project"] == p) for p in data.PROJECTS)
    return dict(system="test", task_id=task["task_id"], saved=saved, digests=[digest], tool_log=log,
                usage={}, latency_s=0, error=None)


def test_data_is_consistent():
    papers, gold, tasks = data.papers(), data.gold("v2"), data.tasks()
    assert len(papers) == 50 and set(gold) == set(papers) and len(tasks) == 8
    for g in gold.values():
        assert set(g["reasons"]) == set(g["labels"])
        assert not set(g["acceptable"]) & set(g["labels"])
    assert data.gold("v1")["MP024"]["labels"] == {}          # topic-only key: coagulants not P3
    assert data.gold("v2")["MP024"]["labels"] == {"P3": "related"}


def test_perfect_result_passes_every_week():
    for t in data.tasks():
        r = perfect_result(t)
        labels, digest = label_grades(r, t, data.gold("v2")), digest_grades(r, t)
        assert labels["core_recall"] == labels["precision"] == 1.0 and labels["related_recall"] in (1.0, None)
        assert week_pass(labels, digest), t["task_id"]
        assert trace_grades(r, t)["read_before_save"] == 1.0


def test_mistakes_are_caught():
    t = data.task("week_06")
    r = perfect_result(t)
    core = next(s for s in r["saved"] if s["level"] == "core")
    r["saved"].remove(core)                                                       # miss a core pair
    r["saved"].append(dict(paper_id="MP026", project="P1", level="core", reason="x"))  # false core
    r["saved"].append(dict(paper_id="MP052", project="P3", level="core", reason="x"))  # re-triage repost
    L = label_grades(r, t, data.gold("v2"))
    assert L["core_recall"] < 1 and ("MP026", "P1") in L["false_core"] and L["retriaged"] == ["MP052"]
    assert not week_pass(L, digest_grades(r, t))


def test_v1_key_is_stricter_about_related_picks():
    t = data.task("week_05")          # contains MP024 (coagulants): v2 = P3 related, v1 = not relevant
    r = perfect_result(t, "v2")
    assert grade_run(r, t, "v2")["passed"]
    g1 = grade_run(r, t, "v1")
    assert ("MP024", "P3") in g1["labels"]["false_positives"] and not g1["passed"]


def test_digest_parser():
    text = "## P1\n- MP001 (core): a — b\n## P2\n- nothing this week\n## P3\n- MP049 (core): c — d"
    assert parse_digest(text) == {("MP001", "P1"), ("MP049", "P3")}


def test_pass_at_k_and_pass_hat_k():
    assert abs(pass_at_k(5, 3, 1) - 0.6) < 1e-9 and abs(pass_at_k(5, 3, 2) - 0.9) < 1e-9
    assert pass_at_k(5, 3, 3) == 1.0
    assert abs(pass_hat_k(5, 3, 2) - 0.3) < 1e-9   # exact estimator; (pass@1)^2 would say 0.36

