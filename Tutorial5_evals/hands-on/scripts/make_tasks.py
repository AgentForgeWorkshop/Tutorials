"""Build data/tasks.json — the eval suite for Example 1.

One task = one weekly run of the triage system:
  feed            : paper IDs the system will see this week (in this order)
  already_triaged : papers the lab database already holds from earlier weeks
  reposted        : papers that reappear this week although they were triaged before
                    (edge case: the system should notice and not triage them again)
Expected answers are not stored here — graders read them from gold.json (or gold_v1.json).
"""
import json, pathlib

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"
REPOSTS = {6: ["MP052"]}  # a week-2 paper reappears in week 6 (e.g. a revised preprint)

papers = json.loads((DATA / "papers.json").read_text())
week_of = {p["paper_id"]: p["week"] for p in papers}

tasks = []
for w in range(1, 9):
    feed = [p["paper_id"] for p in papers if p["week"] == w]
    for i, pid in enumerate(REPOSTS.get(w, [])):
        feed.insert(min(2 + 2 * i, len(feed)), pid)
    earlier = sorted(pid for pid, wk in week_of.items() if wk < w)
    tasks.append(dict(task_id=f"week_{w:02d}", week=w, feed=feed,
                      already_triaged=earlier, reposted=REPOSTS.get(w, [])))

(DATA / "tasks.json").write_text(json.dumps(tasks, indent=2))
print(f"wrote {len(tasks)} tasks:", [(t["task_id"], len(t["feed"])) for t in tasks])
