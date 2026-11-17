"""System B — the LLM workflow: Python decides the steps; the LLM only labels papers and writes the digest.

    for each paper in the feed (code):
        skip it if the database already has it          (code)
        LLM call -> projects, levels, reasons           (structured output)
        save the decisions                              (code)
    LLM call -> digest text                             (code sends it)

Same environment, same project description, same output format as the agent.
"""
import json
import time
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from . import config, data
from .env import TriageEnv
from .prompts import DIGEST_SYSTEM_PROMPT, classify_system_prompt, classify_user_message


class Assessment(BaseModel):
    project: Literal["P1", "P2", "P3"]
    level: Literal["core", "related"]
    reason: str = Field(description="1-2 sentences on specifically how the paper helps this project")


class PaperDecision(BaseModel):
    """Projects this paper is relevant to (empty list if none)."""
    assessments: list[Assessment] = Field(default_factory=list)


def _add_usage(u: dict, msg) -> None:
    u["llm_calls"] += 1
    md = getattr(msg, "usage_metadata", None) or {}
    for k in ("input_tokens", "output_tokens", "total_tokens"):
        u[k] += md.get(k, 0) or 0


def run_workflow(task: dict, prompt_version: str = "v2", model=None, papers: dict | None = None,
                 run_config: dict | None = None, max_concurrency: int = 6) -> dict:
    env = TriageEnv(task, papers)
    model = model or config.make_model()
    usage = dict(input_tokens=0, output_tokens=0, total_tokens=0, llm_calls=0)
    meta = {"task_id": task["task_id"], "system": "workflow", "prompt": prompt_version}
    cfg = {"tags": ["example1", "workflow", f"prompt-{prompt_version}"], "metadata": meta}
    cfg.update(run_config or {})
    t0, error = time.time(), None
    try:
        env.list_new_papers()
        todo = []
        for pid in env.feed:
            env.check_database(pid)
            if env.triaged_before(pid) is None:
                todo.append(pid)
        paper_texts = [env.read_paper(pid) for pid in todo]  # exactly what the agent's read_paper returns

        # one structured-output LLM call per paper, run in parallel
        classifier = model.with_structured_output(PaperDecision, method="function_calling", include_raw=True)
        prompts = [[SystemMessage(classify_system_prompt(prompt_version)),
                    HumanMessage(classify_user_message(task, pid, text))] for pid, text in zip(todo, paper_texts)]
        outs = classifier.batch(prompts, config={**cfg, "run_name": f"workflow classify {task['task_id']}",
                                                 "max_concurrency": max_concurrency})
        for pid, out in zip(todo, outs):
            _add_usage(usage, out["raw"])
            decision = out["parsed"] or PaperDecision()
            for a in decision.assessments:
                env.save_triage(pid, a.project, a.level, a.reason)

        # one LLM call for the digest
        saved = [dict(r, title=env.papers[r["paper_id"]]["title"]) for r in env.results()["saved"]]
        digest = model.invoke([SystemMessage(DIGEST_SYSTEM_PROMPT),
                               HumanMessage("Decisions saved this week:\n" + json.dumps(saved, ensure_ascii=False))],
                              config={**cfg, "run_name": f"workflow digest {task['task_id']}"})
        _add_usage(usage, digest)
        env.send_digest(digest.content if isinstance(digest.content, str) else str(digest.content))
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
    out = env.results()
    out.update(system=f"workflow-{prompt_version}", task_id=task["task_id"], error=error,
               latency_s=round(time.time() - t0, 2), usage=usage, final_message="")
    return out
