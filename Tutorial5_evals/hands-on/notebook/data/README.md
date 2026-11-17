# Tutorial 5 data — weekly paper triage for a microplastics lab

50 real paper abstracts, served as 8 weekly feeds to a paper-triage agent, plus the answer keys used to
grade it. Used by `../05_evaluating_a_triage_agent.ipynb`, which loads these files from the tag `tutorial5-v1`.

| File | What it is |
|---|---|
| `projects.md` | The lab's three projects and the rules for judging relevance (core / related / not relevant). The agent's prompt v2 is this text. |
| `papers.csv` | The 50 papers: `paper_id`, `week` (the feed it appears in), `title`, `authors`, `source`, `posted`, `url`, `license`, `abstract`. |
| `answer_key.csv` | Answer key v2, one row per paper. `P1`, `P2`, `P3`: `core`, `related` or empty (not relevant). `acceptable`: extra projects an expert could defend, which graders do not penalise. `reason_P1..3`: an expert's reference reason (the LLM judge uses it for calibration). `difficulty`: easy / medium / hard (hard = deliberate near-misses). `note`: why a label is tricky. |
| `answer_key_v1.csv` | The first, topic-only answer key (`yes` or empty, no levels). Kept to show how changing the eval changes the score. |
| `tasks.json` | The 8 eval tasks (one per week): `feed` (paper IDs in order), `already_triaged` (what the lab database holds from earlier weeks), `reposted` (papers that reappear and must not be triaged again). |

**The three projects** — measure, understand, capture:
P1 detecting small microplastics in drinking water · P2 microplastic transport from urban rivers to the
estuary · P3 capturing microplastics from water with biochar.

**Twists in the tasks.** Week 4 contains no relevant paper (the agent should still send a digest).
In week 6, `MP052` from week 2 reappears and must be skipped.

**Sources and licences.** Preprints from bioRxiv, ChemRxiv, EarthArXiv and arXiv under Creative Commons
licences, and journal articles found through PubMed in open-access journals that publish under CC BY 4.0
(MDPI, Frontiers, Beilstein Journal of Nanotechnology; licence taken from the journal's policy). Each row
keeps the authors, a link to the original and the licence. Abstracts are verbatim apart from whitespace and
markup clean-up. Copyright stays with the authors; this data is for non-commercial teaching. Please cite the
original papers, not this folder.
