"""Prompts. Prompt v1 and v2 differ ONLY in how the projects are described:

  v1 — project titles + a one-line definition of core/related  (what most people write first)
  v2 — the full projects.md: aims, and core / related / not-relevant rules per project

Everything else (instructions, tools, digest format) is identical, so a score difference
between v1 and v2 can be attributed to the project description alone.
"""
from . import data

DIGEST_FORMAT = """## P1
- MP012 (core): <title> — <one-sentence reason>
- MP015 (related): <title> — <one-sentence reason>
## P2
- nothing this week
## P3
- ..."""


def projects_block(version: str) -> str:
    if version == "v1":
        titles = data.project_titles()
        lines = "\n".join(f"- {p}: {t}" for p, t in titles.items())
        return ("The lab's projects:\n" + lines + "\n\n"
                "Use level \"core\" if a paper is directly relevant to a project and "
                "\"related\" if it is somewhat relevant.")
    if version == "v2":
        return "The lab's projects and how to judge relevance:\n\n" + data.projects_text()
    raise ValueError(f"unknown prompt version {version!r}")


def agent_system_prompt(version: str) -> str:
    return f"""You are the paper-triage assistant for a freshwater microplastics research lab.
Each week new papers arrive. For every paper, decide which of the lab's projects it is relevant to
(zero, one or several) and at what level, then send one digest to the lab.

How to work:
- Use list_new_papers to see this week's papers, and read_paper to read each paper before deciding.
- Use check_database for each paper; papers already triaged in an earlier week must be skipped.
- For each relevant (paper, project) pair call save_triage with the level and a 1-2 sentence reason
  that says specifically how the paper helps that project. Save nothing for irrelevant papers.
- Finally call send_digest exactly once, even if nothing is relevant, in this format
  (one heading per project; list only papers you saved):

{DIGEST_FORMAT}

{projects_block(version)}"""


def agent_task_message(task: dict) -> str:
    return f"Week {task['week']}: please triage this week's new papers and send the digest."


# ---------------------------------------------------------------- LLM workflow prompts
def classify_system_prompt(version: str) -> str:
    """Same wording as the agent's prompt, minus the tool steps (so only the architecture differs)."""
    return f"""You are the paper-triage assistant for a freshwater microplastics research lab.
Each week new papers arrive. For every paper, decide which of the lab's projects it is relevant to
(zero, one or several) and at what level.

How to work:
- You get one paper at a time; read it before deciding.
- For each relevant (paper, project) pair give the level and a 1-2 sentence reason
  that says specifically how the paper helps that project. Save nothing for irrelevant papers
  (return an empty list).

{projects_block(version)}"""


def classify_user_message(task: dict, paper_id: str, paper_text: str) -> str:
    """paper_text is exactly what the agent's read_paper tool returns."""
    return f"Week {task['week']}. Paper {paper_id}:\n{paper_text}"


DIGEST_SYSTEM_PROMPT = f"""You write the weekly paper digest for a freshwater microplastics research lab.
You get the triage decisions saved this week. Write the digest in exactly this format
(one heading per project; list only the papers given to you; write "- nothing this week" if a
project has no papers). Do not add papers or facts that are not in the decisions.

{DIGEST_FORMAT}"""
