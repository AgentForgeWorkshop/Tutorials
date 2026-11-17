"""Run the generated participant notebook end to end, for free, and check it against example1/.

    uv run python scripts/check_public_notebook.py

- DRY_RUN = True (scripted stand-in model, no API keys) and the data read from notebook/data
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
        c.source = c.source.replace("DRY_RUN = False ", "DRY_RUN = True  ")
        if c.source.startswith("%pip"):
            c.source = "# pip install skipped"
        if c.source.lstrip().startswith("import json\nimport urllib.request"):
            c.source = c.source.replace(c.source.split('BASE = "')[1].split('"')[0], LOCAL_DATA)
nb.cells.append(nbformat.v4.new_code_cell(CHECK))
NotebookClient(nb, timeout=900, allow_errors=True).execute()

errors = [(i, o["ename"], o["evalue"][:200]) for i, c in enumerate(nb.cells) if c.cell_type == "code"
          for o in c.get("outputs", []) if o.get("output_type") == "error"]
last = "".join(o.get("text", "") for o in nb.cells[-1].outputs)
print("cell errors:", errors or "none")
print(last.strip())
sys.exit(1 if errors or "MISMATCHES 0" not in last else 0)
