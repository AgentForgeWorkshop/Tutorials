"""A scripted stand-in for the LLM, so the whole pipeline can run for free (tests, dry runs, Colab
without an API key). It "knows" the answer key and makes random mistakes at `error_rate`, so the
graders and summary tables have something realistic to show. It is NOT a model — never report its
scores as results.
"""
import json
import random
import re
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import RunnableLambda

from . import data

GENERIC = "It is about microplastics."


class FakeTriageModel(BaseChatModel):
    seed: int = 0
    error_rate: float = 0.1
    model_name: str = "fake-triage"

    @property
    def _llm_type(self) -> str:
        return "fake-triage"

    # ---------------------------------------------------------------- the "decisions"
    def _plan(self, pid: str) -> list[tuple[str, str, str]]:
        """[(project, level, reason)] for one paper: the answer key plus seeded mistakes."""
        rng = random.Random(f"{self.seed}-{pid}")
        g = data.gold("v2")[pid]
        out = []
        for proj, lvl in g["labels"].items():
            if rng.random() < self.error_rate * (1.5 if lvl == "related" else 0.6):
                continue  # missed label
            if rng.random() < self.error_rate * 0.5:
                lvl = "core" if lvl == "related" else "related"  # wrong level
            reason = GENERIC if rng.random() < self.error_rate * 0.5 else g["reasons"][proj]
            out.append((proj, lvl, reason))
        for proj in g["acceptable"]:
            if rng.random() < 0.3:
                out.append((proj, "related", "Defensible extra link."))
        if not g["labels"] and rng.random() < self.error_rate:
            out.append((rng.choice(data.PROJECTS), rng.choice(data.LEVELS), GENERIC))  # false positive
        return out

    def _usage(self, messages, output: str) -> dict:
        i = sum(len(str(getattr(m, "content", m))) for m in messages) // 4
        o = max(1, len(output) // 4)
        return {"input_tokens": i, "output_tokens": o, "total_tokens": i + o}

    @staticmethod
    def _digest(rows) -> str:
        titles = data.papers()
        lines = []
        for p in data.PROJECTS:
            lines.append(f"## {p}")
            items = [r for r in rows if r[1] == p]
            lines += [f"- {pid} ({lvl}): {titles[pid]['title']} — {reason}" for pid, _, lvl, reason in items] \
                or ["- nothing this week"]
        return "\n".join(lines)

    # ---------------------------------------------------------------- chat interface (agent)
    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs: Any) -> ChatResult:
        system = str(messages[0].content) if messages else ""
        if system.startswith("You write the weekly paper digest"):  # workflow digest step
            rows = json.loads(str(messages[-1].content).split("\n", 1)[1])
            text = self._digest([(r["paper_id"], r["project"], r["level"], r["reason"]) for r in rows])
            return self._result(AIMessage(content=text), messages)

        calls = [tc for m in messages if isinstance(m, AIMessage) for tc in (m.tool_calls or [])]
        results = {m.tool_call_id: str(m.content) for m in messages if isinstance(m, ToolMessage)}
        done = lambda name: [tc for tc in calls if tc["name"] == name]

        if not done("list_new_papers"):
            return self._tool_calls([("list_new_papers", {})], messages)
        feed = [p["paper_id"] for p in json.loads(results[done("list_new_papers")[0]["id"]])]
        read = {tc["args"]["paper_id"] for tc in done("read_paper")}
        habits = random.Random(f"{self.seed}-habits")
        forgets = feed[-1] if habits.random() < self.error_rate * 0.4 else None  # labels one paper unread
        ignores_db = habits.random() < self.error_rate * 0.4                     # re-triages reposts
        todo = [pid for pid in feed if pid not in read and pid != forgets]
        if todo:
            return self._tool_calls([("read_paper", {"paper_id": pid}) for pid in todo], messages)
        checked = {tc["args"]["paper_id"]: results.get(tc["id"], "") for tc in done("check_database")}
        if not checked:
            return self._tool_calls([("check_database", {"paper_id": pid}) for pid in feed], messages)
        in_db = set() if ignores_db else {pid for pid, res in checked.items() if "already triaged" in res}
        plan = [(pid, proj, lvl, reason) for pid in feed if pid not in in_db for proj, lvl, reason in self._plan(pid)]
        if plan and not done("save_triage"):
            return self._tool_calls([("save_triage", dict(paper_id=pid, project=proj, level=lvl, reason=reason))
                                     for pid, proj, lvl, reason in plan], messages)
        if not done("send_digest"):
            return self._tool_calls([("send_digest", {"text": self._digest(plan)})], messages)
        return self._result(AIMessage(content="Done — all papers triaged and the digest is sent."), messages)

    def _tool_calls(self, calls, messages) -> ChatResult:
        tcs = [dict(name=n, args=a, id=f"call_{i}_{random.random():.6f}", type="tool_call") for i, (n, a) in enumerate(calls)]
        return self._result(AIMessage(content="", tool_calls=tcs), messages)

    def _result(self, msg: AIMessage, messages) -> ChatResult:
        msg.usage_metadata = self._usage(messages, str(msg.content) + json.dumps(msg.tool_calls or []))
        return ChatResult(generations=[ChatGeneration(message=msg)])

    # ---------------------------------------------------------------- structured output (workflow, judge)
    def with_structured_output(self, schema, include_raw: bool = False, **kwargs):
        def run(messages):
            user = str(messages[-1][1] if isinstance(messages[-1], tuple) else messages[-1].content)
            if schema.__name__ == "PaperDecision":
                pid = re.search(r"Paper (MP\d{3})", user).group(1)
                obj = schema(assessments=[dict(project=p, level=l, reason=r) for p, l, r in self._plan(pid)])
            elif schema.__name__ == "ReasonVerdicts":
                items = json.loads(user)
                obj = schema(verdicts=[dict(paper_id=it["paper_id"], project=it["project"],
                                            specific=it["assistant_reason"] != GENERIC, faithful=True,
                                            fits_level=True,
                                            verdict="pass" if it["assistant_reason"] != GENERIC else "fail",
                                            comment="scripted verdict") for it in items])
            else:
                raise ValueError(f"fake model has no script for {schema.__name__}")
            if not include_raw:
                return obj
            raw = AIMessage(content="", usage_metadata=self._usage(messages, obj.model_dump_json()))
            return {"raw": raw, "parsed": obj, "parsing_error": None}
        return RunnableLambda(run)
