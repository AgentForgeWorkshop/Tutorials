"""System A — the agent: the LLM decides which tools to call, and in which order."""
import time

from langchain.agents import create_agent

from . import config, data
from .env import TriageEnv
from .prompts import agent_system_prompt, agent_task_message


def usage_from_messages(messages) -> dict:
    u = dict(input_tokens=0, output_tokens=0, total_tokens=0, llm_calls=0)
    for m in messages:
        if getattr(m, "type", "") == "ai":
            u["llm_calls"] += 1
            md = getattr(m, "usage_metadata", None) or {}
            for k in ("input_tokens", "output_tokens", "total_tokens"):
                u[k] += md.get(k, 0) or 0
    return u


def run_agent(task: dict, prompt_version: str = "v2", model=None, papers: dict | None = None,
              run_config: dict | None = None) -> dict:
    """Run the agent on one weekly task and return everything the graders need."""
    env = TriageEnv(task, papers)
    model = model or config.make_model()
    agent = create_agent(model, tools=env.tools(), system_prompt=agent_system_prompt(prompt_version),
                         name=f"triage-agent-{prompt_version}")
    cfg = {"recursion_limit": config.RECURSION_LIMIT,
           "run_name": f"agent-{prompt_version} {task['task_id']}",
           "tags": ["example1", "agent", f"prompt-{prompt_version}"],
           "metadata": {"task_id": task["task_id"], "system": "agent", "prompt": prompt_version}}
    cfg.update(run_config or {})
    t0, error, messages = time.time(), None, []
    try:
        state = agent.invoke({"messages": [{"role": "user", "content": agent_task_message(task)}]}, config=cfg)
        messages = state["messages"]
    except Exception as e:  # e.g. step limit reached, provider error — keep partial results
        error = f"{type(e).__name__}: {e}"
    out = env.results()
    out.update(system=f"agent-{prompt_version}", task_id=task["task_id"], error=error,
               latency_s=round(time.time() - t0, 2), usage=usage_from_messages(messages),
               final_message=(messages[-1].content if messages else ""))
    return out


if __name__ == "__main__":  # quick manual check: python -m example1.agent week_01 v2
    import json, sys
    t = data.task(sys.argv[1] if len(sys.argv) > 1 else "week_01")
    r = run_agent(t, sys.argv[2] if len(sys.argv) > 2 else "v2")
    print(json.dumps({k: r[k] for k in ("saved", "digests", "usage", "latency_s", "error")}, indent=2))
