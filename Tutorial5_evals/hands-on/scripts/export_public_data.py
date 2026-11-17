"""Export the Example 1 data in reader-friendly formats for the public Tutorials repo.

    python scripts/export_public_data.py [out_dir]     (default: notebook/data)

Writes README.md (data card), projects.md, papers.csv, answer_key.csv, answer_key_v1.csv, tasks.json.
CSV renders as a searchable table on GitHub and loads with pandas; the notebook version reads these.
"""
import csv
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "notebook" / "data"
OUT.mkdir(parents=True, exist_ok=True)
PROJECTS = ("P1", "P2", "P3")

papers = json.loads((DATA / "papers.json").read_text())
papers.sort(key=lambda p: p["paper_id"])
gold = json.loads((DATA / "gold.json").read_text())
gold_v1 = json.loads((DATA / "gold_v1.json").read_text())


def write_csv(name, rows, fields):
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


write_csv("papers.csv", papers,
          ["paper_id", "week", "title", "authors", "source", "posted", "url", "license", "abstract"])

rows = []
for p in papers:
    g = gold[p["paper_id"]]
    rows.append({"paper_id": p["paper_id"], "week": p["week"], "title": p["title"],
                 **{proj: g["labels"].get(proj, "") for proj in PROJECTS},
                 "acceptable": ";".join(g["acceptable"]), "difficulty": g["difficulty"], "note": g["note"],
                 **{f"reason_{proj}": g["reasons"].get(proj, "") for proj in PROJECTS}})
write_csv("answer_key.csv", rows, ["paper_id", "week", "title", *PROJECTS, "acceptable", "difficulty", "note",
                                   *[f"reason_{p}" for p in PROJECTS]])

rows = []
for p in papers:
    g = gold_v1[p["paper_id"]]
    rows.append({"paper_id": p["paper_id"], "week": p["week"], "title": p["title"],
                 **{proj: ("yes" if proj in g["projects"] else "") for proj in PROJECTS},
                 "acceptable": ";".join(g.get("acceptable", [])), "note": g.get("note", "")})
write_csv("answer_key_v1.csv", rows, ["paper_id", "week", "title", *PROJECTS, "acceptable", "note"])

shutil.copy(DATA / "projects.md", OUT / "projects.md")
shutil.copy(DATA / "tasks.json", OUT / "tasks.json")

n_lab = {lvl: sum(lvl == l for g in gold.values() for l in g["labels"].values()) for lvl in ("core", "related")}
n_none = sum(1 for g in gold.values() if not g["labels"])
(OUT / "README.md").write_text(f"""# Tutorial 5 data — paper triage for a microplastics lab

The data behind Example 1 of Tutorial 5 (evaluating an agent). A fictional freshwater research
lab runs three projects; each week new papers arrive and an agent decides which project(s) each
paper matters to. These files are the agent's world and the answer key used to grade it.

| File | What it is |
|---|---|
| [`projects.md`](projects.md) | The three projects and the rules for judging relevance (**core** / **related** / not relevant). The agent's prompt v2 is this text. |
| [`papers.csv`](papers.csv) | {len(papers)} real paper abstracts, assigned to 8 weekly feeds. |
| [`answer_key.csv`](answer_key.csv) | The answer key (v2): for each paper and project, `core`, `related` or blank. |
| [`answer_key_v1.csv`](answer_key_v1.csv) | The first, topic-only answer key (v1), kept to show how improving an eval changes scores. |
| [`tasks.json`](tasks.json) | The eval suite: one task per week (the feed, and what the lab database already holds). |

## The three projects

| | Project | Role in the story |
|---|---|---|
| P1 | Detecting small microplastics in drinking water | measure |
| P2 | Microplastic transport from urban rivers to the estuary | understand |
| P3 | Capturing microplastics from water with biochar | capture |

## Columns

**papers.csv** — `paper_id` (MP001…), `week` (1–8, the weekly feed it appears in), `title`, `authors`
(first three), `source` (bioRxiv, ChemRxiv, EarthArXiv, arXiv, PubMed), `posted` (date first available),
`url`, `license`, `abstract`.

**answer_key.csv** — one row per paper:

- `P1`, `P2`, `P3`: `core` (directly advances an aim), `related` (the project lead would compare
  against it, borrow from it, or cite it), or blank (not relevant).
- `acceptable`: extra projects an expert could defend (separated by `;`). A lenient grader does not
  count them as mistakes.
- `difficulty`: `easy`, `medium` or `hard` (hard = borderline cases and look-alike traps).
- `note`: why a paper is hard, or why it is not relevant.
- `reason_P1` … `reason_P3`: an expert's reference answer to "how is it relevant?" — used to calibrate
  the LLM judge, not as an exact answer.

In total: {n_lab['core']} core and {n_lab['related']} related (paper, project) pairs; {n_none} papers are
relevant to no project.

**answer_key_v1.csv** — the older key: `P1`–`P3` are `yes` or blank (no levels), plus `acceptable` and `note`.

**tasks.json** — a list of 8 tasks: `task_id`, `week`, `feed` (paper IDs shown that week),
`already_triaged` (papers the lab database already holds), `reposted` (papers that reappear and must not
be triaged twice). Two tasks have a twist: in week 4 nothing is relevant; in week 6, MP052 from week 2
reappears.

## Where the papers come from

Abstracts were retrieved from preprint servers (bioRxiv, ChemRxiv, EarthArXiv, arXiv) and from PubMed
(open-access journals: MDPI, Frontiers, Beilstein). Each row keeps the authors, link and licence; all are
Creative Commons licences, and the abstracts are reproduced unchanged except for whitespace and markup
clean-up, for non-commercial teaching. The project descriptions are fictional; the labels were written for
this tutorial and reviewed by the tutorial author.
""")
print("wrote", sorted(f.name for f in OUT.iterdir()), "to", OUT)
