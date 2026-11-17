"""Run the generated notebook version end to end with real models, and check it against example1/.

    uv run python scripts/check_public_notebook.py

- needs OPENROUTER_API_KEY (real API calls: 3 suites x 8 weeks x 3 trials, plus the judge — costs money)
- reads the data from notebook/data, so it works before the tag exists
- fails if any cell errors, or if the notebook's graders / answer keys disagree with example1/
Needs the dev dependencies (nbclient, ipykernel).
"""
import pathlib
import sys

import nbformat
from nbclient import NotebookClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
NB = ROOT / "notebook" / "05_evaluating_a_triage_agent.ipynb"
LOCAL_DATA = str(ROOT / "notebook" / "data") + "/"

CHECK = f'''
import sys; sys.path.insert(0, {str(ROOT)!r})
from example1 import graders as G, data as D
close = lambda a, b: (a is None and b is None) or (a is not None and b is not None and abs(a - b) < 1e-3)
bad = 0
for recs in (agent_v1, agent_v2, workflow_v2):
    for r in recs:
        for key in ("v2", "v1"):
            ref, mine = G.grade_run(r["result"], D.task(r["task_id"]), key), r["grades"][key]
            bad += mine["passed"] != ref["passed"]
            bad += any(not close(mine["labels"][m], ref["labels"][m])
                       for m in ("core_recall", "related_recall", "precision", "level_accuracy"))
            bad += any(mine["labels"][m] != ref["labels"][m]
                       for m in ("false_positives", "false_core", "missed_core", "retriaged"))
for v in ("v2", "v1"):
    for pid, g in D.gold(v).items():
        m = GOLD[v][pid]
        bad += (m["labels"] != g["labels"]) + (m["acceptable"] != g["acceptable"]) + (v == "v2" and m["reasons"] != g["reasons"])
print("MISMATCHES", bad)
'''

nb = nbformat.read(NB, as_version=4)
for c in nb.cells:
    if c.cell_type == "code":
        if c.source.startswith("%pip"):
            c.source = "# pip install skipped"
        if c.source.lstrip().startswith("import json\nimport urllib.request"):
            c.source = c.source.replace(c.source.split('BASE = "')[1].split('"')[0], LOCAL_DATA)
nb.cells.append(nbformat.v4.new_code_cell(CHECK))
NotebookClient(nb, timeout=3600, allow_errors=True).execute()

errors = [(i, o["ename"], o["evalue"][:200]) for i, c in enumerate(nb.cells) if c.cell_type == "code"
          for o in c.get("outputs", []) if o.get("output_type") == "error"]
last = "".join(o.get("text", "") for o in nb.cells[-1].outputs)
(ROOT / "results").mkdir(exist_ok=True)
nbformat.write(nb, ROOT / "results" / "notebook_executed.ipynb")  # for reading the outputs; not committed
print("cell errors:", errors or "none")
print(last.strip())
sys.exit(1 if errors or "MISMATCHES 0" not in last else 0)
