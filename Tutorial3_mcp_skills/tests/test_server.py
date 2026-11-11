"""Tests for the workshop server. No API key and no internet needed: `python -m pytest`.

The server tests start the real server.py and talk to it over real MCP. External services are
replaced with local fakes.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import httpx
import pytest
from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "skills" / "calculator" / "scripts"))

import calc  # noqa: E402
from research_tools import lay_abstract, online, review, skills  # noqa: E402
from research_tools.config import SKILLS_DIR, Settings, load_settings  # noqa: E402
from research_tools.library import PaperLibrary  # noqa: E402


def call_server(library: Path, steps, extra_env: dict | None = None):
    """Start the real server with a given library folder and run `steps` against it."""
    env = {**os.environ, "LIBRARY_PATH": str(library), "LLM_API_KEY": "", "ANTHROPIC_API_KEY": "",
           "OPENAI_API_KEY": "", **(extra_env or {})}

    async def run():
        params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "server.py")], env=env)
        async with Client(params) as client:
            return await steps(client)

    return asyncio.run(run())


def text_of(result) -> str:
    return "\n".join(block.text for block in result.content if block.type == "text")


@pytest.fixture
def library(tmp_path: Path) -> Path:
    folder = tmp_path / "my library"          # a space, as in many real folder names
    (folder / "nested").mkdir(parents=True)
    shutil.copy(ROOT / "sample_library" / "paper5_stack_pressure.pdf", folder)
    shutil.copy(ROOT / "sample_library" / "paper1_dendrite_interlayers.pdf", folder / "nested")
    (folder / "notes.txt").write_text("Perovskite solar cells degrade under humidity.", encoding="utf-8")
    (folder / "ignored.docx").write_text("not supported", encoding="utf-8")
    return folder


# ---- the server over real MCP ----------------------------------------------
def test_server_lists_all_capabilities(library):
    async def steps(client):
        return ((await client.list_tools()).tools, (await client.list_resources()).resources,
                (await client.list_prompts()).prompts)

    tools, resources, prompts = call_server(library, steps)
    assert {t.name for t in tools} == {
        "list_papers", "search_papers", "read_page", "search_online", "review_online_literature",
        "calculate", "prepare_lay_abstract", "review_lay_abstract", "list_skills", "load_skill",
        "read_skill_file",
    }
    assert [str(r.uri) for r in resources] == ["library://catalog"]
    assert {p.name for p in prompts} == {"literature_review", "lay_abstract"}


def test_library_folder_comes_from_settings(library):
    async def steps(client):
        return (text_of(await client.call_tool("list_papers", {})),
                text_of(await client.call_tool("search_papers", {"query": "perovskite humidity"})),
                text_of(await client.call_tool("read_page", {"paper": "paper5", "page": 1})))

    listing, hit, page = call_server(library, steps)
    assert str(library) in listing and "3 document(s)" in listing
    assert "nested/paper1_dendrite_interlayers.pdf" in listing and "ignored.docx" not in listing
    assert hit.startswith("[1] notes.txt, p. 1")
    assert "Stack Pressure" in page


def test_missing_folder_gives_clear_message(tmp_path):
    async def steps(client):
        return text_of(await client.call_tool("list_papers", {}))

    assert "does not exist" in call_server(tmp_path / "nope", steps)


def test_calculator_skill_through_mcp(library):
    async def steps(client):
        return (text_of(await client.call_tool("calculate", {"expression": "412/487*100"})),
                text_of(await client.call_tool("calculate", {"expression": "__import__('os')"})),
                text_of(await client.call_tool("load_skill", {"name": "calculator"})),
                text_of(await client.call_tool("read_skill_file",
                                               {"name": "calculator", "path": "references/formulas.md"})),
                text_of(await client.call_tool("read_skill_file",
                                               {"name": "calculator", "path": "../../.env"})))

    result, blocked, body, formulas, escape = call_server(library, steps)
    assert result == "412/487*100 = 84.5996"
    assert blocked.startswith("ERROR")
    assert "Never compute a number" in body
    assert "Theoretical capacity" in formulas
    assert "outside the skill" in escape


def test_lay_abstract_accepts_a_file_or_pasted_text(library):
    pasted = "We measured how salt water corrodes steel over ten years. " * 20

    async def steps(client):
        return (text_of(await client.call_tool("prepare_lay_abstract", {"document": "paper5"})),
                text_of(await client.call_tool("prepare_lay_abstract", {"document": pasted, "audience": "students"})),
                text_of(await client.call_tool("prepare_lay_abstract", {"document": "missing"})),
                text_of(await client.call_tool("review_lay_abstract", {
                    "draft": "Squeezing batteries made them last 9.9 times longer. This helps phones.",
                    "document": "paper5"})))

    from_file, from_paste, missing, checked = call_server(library, steps)
    assert "[page 1]" in from_file and "Stack Pressure" in from_file
    assert "pasted document" in from_paste and "students" in from_paste
    assert missing.startswith("ERROR")
    assert "REVISE" in checked and "9.9" in checked


def test_review_tool_without_key_explains_what_to_do(library):
    async def steps(client):
        return text_of(await client.call_tool("review_online_literature", {"question": "anything"}))

    assert "needs an API key" in call_server(library, steps)


# ---- library ---------------------------------------------------------------
def test_new_file_is_found_without_restart(library):
    lib = PaperLibrary(library)
    assert len(lib.list_papers()) == 3
    (library / "new.md").write_text("Graphene membranes filter seawater.", encoding="utf-8")
    assert lib.search("graphene")[0].paper == "new.md"


def test_scanned_pdf_is_reported_not_fatal(library):
    (library / "broken.pdf").write_bytes(b"this is not a pdf")
    lib = PaperLibrary(library)
    assert len(lib.list_papers()) == 3
    assert "broken.pdf" in lib.unreadable


def test_ambiguous_name_is_refused(library):
    lib = PaperLibrary(library)
    with pytest.raises(ValueError, match="several files"):
        lib.resolve("paper")


def test_absolute_paths_cannot_escape_the_library(library, tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("private", encoding="utf-8")
    with pytest.raises(ValueError):
        PaperLibrary(library).read_page(str(secret), 1)


# ---- calculator ------------------------------------------------------------
@pytest.mark.parametrize("expression, expected", [
    ("412/487*100", "84.5996"), ("(100-84.5996)/500", "0.0308008"), ("2^10", "1024"),
    ("1*F/(3.6*157.76)", "169.888"), ("sqrt(16)", "4"), ("round(2.456, 1)", "2.5"),
])
def test_calculator_results(expression, expected):
    assert calc.calculate(expression) == f"{expression} = {expected}"


@pytest.mark.parametrize("bad", [
    "__import__('os').system('ls')", "open('x')", "1/0", "9**9**9", "(10**1000)**1000",
    "((2**4000)**2)**2", "sqrt(-1)", "(-8)**0.5", "1 +", "x" * 501, "2.5**1000",
])
def test_calculator_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        calc.calculate(bad)


# ---- lay abstract checker ---------------------------------------------------
def test_plain_draft_passes():
    draft = ("Batteries can fail when thin metal spikes grow inside them. Researchers tested 20 cells. "
             "Pressing the cells made them last 2.4 times longer. The result suggests pressure helps. "
             "Other groups still need to repeat the test.")
    result = lay_abstract.review_draft(draft, "We tested 20 cells. Life grew 2.4 times.")
    assert result["verdict"] == "PASS", result["problems"]


def test_hard_draft_is_flagged():
    draft = ("Electrochemical characterization demonstrated heterogeneous electrodeposition "
             "morphologies attributable to interfacial inhomogeneities within SEI microstructures, "
             "necessitating comprehensive investigation of polycrystalline electrolyte stabilization "
             "methodologies across multidimensional operational parameters and configurations.")
    result = lay_abstract.review_draft(draft)
    assert result["verdict"] == "REVISE"
    assert result["grade_level"] > 10
    assert any("jargon" in p for p in result["problems"])


def test_invented_number_is_flagged_and_decimals_survive_splitting():
    result = lay_abstract.review_draft("Life grew 2.4 times. It cost 50 dollars.", "Life grew 2.4 times.")
    assert result["sentences"] == 2
    assert any("50" in p and "2.4" not in p for p in result["problems"])


def test_explained_term_is_not_jargon():
    result = lay_abstract.review_draft("Dendrites form. An electrolyte (the liquid inside) helps a lot.")
    assert not any("electrolyte" in p for p in result["problems"])


# ---- online search, with fake services ---------------------------------------
OPENALEX_RESPONSE = {"results": [{
    "id": "https://openalex.org/W1", "title": "Interlayers <i>in</i> cells", "publication_year": 2024,
    "doi": "https://doi.org/10.1/ABC", "cited_by_count": 7,
    "abstract_inverted_index": {"Interlayers": [0], "help": [1], "cells": [2]},
    "authorships": [{"author": {"display_name": "A. Author"}}, {"author": {"display_name": "B. Author"}}],
    "primary_location": {"source": {"display_name": "J. Batteries"}},
}]}
ARXIV_RESPONSE = """<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
<entry><id>http://arxiv.org/abs/2401.1</id><published>2024-01-01T00:00:00Z</published>
<title>Stack
 pressure</title><summary>Pressure helps.</summary><author><name>C. Writer</name></author></entry>
<entry><id>http://arxiv.org/abs/1001.1</id><published>2010-01-01T00:00:00Z</published>
<title>Old work</title><summary>Old.</summary></entry></feed>"""
EUROPEPMC_RESPONSE = {"resultList": {"result": [
    {"id": "1", "source": "MED", "title": "Interlayers in cells", "doi": "10.1/abc", "pubYear": "2024",
     "abstractText": "Duplicate of the OpenAlex record.", "authorString": "A. Author, B. Author."},
    {"id": "2", "source": "MED", "title": "No abstract here", "pubYear": "2023", "authorString": "D. Doe."},
]}}


def fake_transport(request: httpx.Request) -> httpx.Response:
    host = request.url.host
    if "openalex" in host:
        return httpx.Response(200, json=OPENALEX_RESPONSE)
    if "arxiv" in host:
        return httpx.Response(200, text=ARXIV_RESPONSE)
    return httpx.Response(200, json=EUROPEPMC_RESPONSE)


@pytest.fixture
def fake_web(monkeypatch):
    def fake_get(url, **kwargs):
        request = httpx.Request("GET", url, params=kwargs.get("params"))
        response = fake_transport(request)
        response.request = request
        return response

    monkeypatch.setattr(online.httpx, "get", fake_get)


def test_search_merges_sources_and_removes_duplicates(fake_web):
    papers, notes = online.search_all("interlayers", limit=10, year_from=2020)
    titles = [p.title for p in papers]
    assert notes == []
    assert titles.count("Interlayers in cells") == 1          # same DOI, different case
    assert "Stack pressure" in titles and "Old work" not in titles
    assert titles[-1] == "No abstract here"                   # papers without abstracts go last
    first = papers[0]
    assert first.abstract == "Interlayers help cells"
    assert first.url == "https://doi.org/10.1/ABC"
    assert first.reference().startswith("A. Author et al. (2024) Interlayers in cells.")


def test_one_failed_source_does_not_stop_search_and_never_leaks_the_key(monkeypatch):
    def fake_get(url, **kwargs):
        request = httpx.Request("GET", url, params=kwargs.get("params"))
        if "openalex" in url:
            response = httpx.Response(429, request=request)
        elif "arxiv" in url:
            response = httpx.Response(200, text=ARXIV_RESPONSE, request=request)
        else:
            raise httpx.ConnectError("no route", request=request)
        return response

    monkeypatch.setattr(online.httpx, "get", fake_get)
    papers, notes = online.search_all("x", openalex_key="SECRET-KEY")
    assert [p.source for p in papers] == ["arXiv", "arXiv"]
    assert any("OpenAlex" in n and "429" in n for n in notes)
    assert any("Europe PMC" in n for n in notes)
    assert "SECRET-KEY" not in " ".join(notes)


# ---- the online review pipeline, with a fake model ---------------------------
def settings() -> Settings:
    return Settings(library_path=Path("."), llm_api_key="sk-ant-test", llm_model="", openalex_api_key="")


def test_review_adds_real_references_and_catches_invented_citations(fake_web, monkeypatch):
    replies = iter(['["interlayer cells"]', "## Short answer\nThey help [1], and also [99]."])
    prompts = []

    def fake_complete(_settings, system, user, max_tokens=8000):
        prompts.append(user)
        return next(replies)

    monkeypatch.setattr(review, "complete", fake_complete)
    result = review.review_literature(settings(), "Do interlayers help?")
    assert "Citation check failed" in result and "99" in result
    assert "## References\n1. A. Author et al. (2024)" in result
    assert "https://doi.org/10.1/ABC" in result
    assert "Based on abstracts only" in result
    assert "No abstract here" not in result               # no abstract, so no basis for claims
    assert '<paper number="1">' in prompts[1]


def test_bad_query_reply_falls_back_to_the_question():
    assert review.parse_queries("not json", "My question") == ["My question"]
    assert review.parse_queries('Sure: ["a b", "c d", "e f"]', "Q") == ["a b", "c d"]
    assert review.parse_queries('[1, 2]', "Q") == ["Q"]


def test_provider_is_detected_from_the_key():
    assert settings().provider == "anthropic" and settings().model == "claude-haiku-5-5"
    openai_settings = Settings(Path("."), "sk-proj-abc", "", "")
    assert openai_settings.provider == "openai" and openai_settings.model == "gpt-6-luna"
    assert Settings(Path("."), "", "", "").provider == ""
    router = Settings(Path("."), "sk-or-v1-abc", "", "")
    assert router.provider == "openrouter" and router.model == "deepseek/deepseek-v4.1-flash"
    assert router.base_url == "https://openrouter.ai/api/v1"
    google = Settings(Path("."), "AIzaSyABC", "", "")
    assert google.provider == "google" and google.model == "gemini-3.5-flash"
    assert "generativelanguage" in google.base_url
    assert openai_settings.base_url is None


def test_env_file_wins_over_shell(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "from-shell")
    env = tmp_path / ".env"
    env.write_text('LLM_MODEL="from-file"\nLIBRARY_PATH="~/papers"\n', encoding="utf-8")
    loaded = load_settings(env)
    assert loaded.model == "from-file"
    assert loaded.library_path == Path.home() / "papers"


def test_every_skill_is_valid():
    found = skills.discover(SKILLS_DIR)
    assert set(found) == {"calculator", "lay-abstract", "literature-review"}
    for name, skill in found.items():
        assert skill["folder"].name == name                # the Agent Skills format requires this
        assert len(skill["description"]) <= 1024


# ---- setup_workshop.py -----------------------------------------------------
def test_setup_cleans_dragged_paths_and_merges_desktop_config(tmp_path, monkeypatch):
    import setup_workshop as setup

    if os.name != "nt":
        assert setup.clean_path("/Users/me/My\\ Papers ") == Path("/Users/me/My Papers")
    assert setup.clean_path("'/tmp/a b'") == Path("/tmp/a b")

    config = tmp_path / "Claude" / "claude_desktop_config.json"
    config.parent.mkdir()
    config.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}, "keep": 1}), encoding="utf-8")
    monkeypatch.setattr(setup, "desktop_config_path", lambda: config)
    setup.add_to_claude_desktop()
    merged = json.loads(config.read_text(encoding="utf-8"))
    assert merged["keep"] == 1 and "other" in merged["mcpServers"]
    assert merged["mcpServers"]["research-mcp"]["args"] == [str(ROOT / "server.py")]
    assert len(list(config.parent.glob("*.backup-*.json"))) == 1


def test_setup_leaves_a_broken_desktop_config_alone(tmp_path, monkeypatch):
    import setup_workshop as setup

    config = tmp_path / "claude_desktop_config.json"
    config.write_text("{broken", encoding="utf-8")
    monkeypatch.setattr(setup, "desktop_config_path", lambda: config)
    setup.add_to_claude_desktop()
    assert config.read_text(encoding="utf-8") == "{broken"


# ---- chat.py against fake model APIs: the loop, the MCP calls and the SDK usage --------------
class FakeModelAPI(BaseHTTPRequestHandler):
    """First reply asks for the calculate tool. Second reply, sent once the tool's result has
    come back, repeats that result, which proves the whole loop worked."""
    bodies: list = []

    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["content-length"])))
        FakeModelAPI.bodies.append(body)
        if self.path.endswith("/chat/completions"):
            reply = self._chat(body)
        elif "messages" in self.path:
            reply = self._anthropic(body)
        else:
            reply = self._openai(body)
        data = json.dumps(reply).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    @staticmethod
    def _anthropic(body):
        last = body["messages"][-1]["content"]
        base = {"id": "msg", "type": "message", "role": "assistant", "model": body["model"],
                "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1}}
        if isinstance(last, list) and last[0]["type"] == "tool_result":
            return {**base, "stop_reason": "end_turn",
                    "content": [{"type": "text", "text": f"FINAL: {last[0]['content']}"}]}
        return {**base, "stop_reason": "tool_use", "content": [
            {"type": "tool_use", "id": "t1", "name": "calculate", "input": {"expression": "6*7"}}]}

    @staticmethod
    def _chat(body):
        base = {"id": "c", "object": "chat.completion", "created": 0, "model": body["model"]}
        last = body["messages"][-1]
        if "tools" not in body:                    # a plain completion, as review.py makes
            message = {"role": "assistant", "content": f"PLAIN: {last['content']}"}
            return {**base, "choices": [{"index": 0, "message": message, "finish_reason": "stop"}]}
        if last["role"] == "tool":
            message = {"role": "assistant", "content": f"FINAL: {last['content']}"}
            finish = "stop"
        else:
            message = {"role": "assistant", "content": None, "tool_calls": [{"id": "call1", "type": "function",
                       "function": {"name": "calculate", "arguments": json.dumps({"expression": "6*7"})}}]}
            finish = "tool_calls"
        return {**base, "choices": [{"index": 0, "message": message, "finish_reason": finish}]}

    @staticmethod
    def _openai(body):
        outputs = [i for i in body["input"] if isinstance(i, dict) and i.get("type") == "function_call_output"]
        base = {"id": "resp", "object": "response", "created_at": 0, "model": body["model"], "status": "completed",
                "parallel_tool_calls": True, "tool_choice": "auto", "tools": []}
        if outputs:
            return {**base, "output": [{"type": "message", "id": "m", "role": "assistant", "status": "completed",
                                        "content": [{"type": "output_text", "text": f"FINAL: {outputs[0]['output']}",
                                                     "annotations": []}]}]}
        return {**base, "output": [{"type": "function_call", "id": "f", "call_id": "c1", "name": "calculate",
                                    "arguments": json.dumps({"expression": "6*7"}), "status": "completed"}]}


@pytest.mark.parametrize("key, base_url_var, base_url_path", [
    ("sk-ant-test", "ANTHROPIC_BASE_URL", ""),          # Anthropic Messages API
    ("sk-test", "OPENAI_BASE_URL", "/v1"),              # OpenAI Responses API
    ("sk-or-test", "LLM_BASE_URL", "/v1"),              # OpenRouter and Google: chat completions
])
def test_chat_runs_the_full_agent_loop(library, tmp_path, key, base_url_var, base_url_path):
    FakeModelAPI.bodies = []
    fake = HTTPServer(("127.0.0.1", 0), FakeModelAPI)
    threading.Thread(target=fake.serve_forever, daemon=True).start()
    try:
        env = {**os.environ, "LLM_API_KEY": key, "LIBRARY_PATH": str(library),
               base_url_var: f"http://127.0.0.1:{fake.server_port}{base_url_path}"}
        done = subprocess.run([sys.executable, str(ROOT / "chat.py"), "What is 6 times 7?"], env=env,
                              capture_output=True, text=True, timeout=120)
    finally:
        fake.shutdown()
    assert done.returncode == 0, done.stderr
    assert "[tool] calculate" in done.stdout
    assert "FINAL: 6*7 = 42" in done.stdout
    assert len(FakeModelAPI.bodies) == 2


def test_review_completions_work_through_an_openai_compatible_service():
    from research_tools.llm import complete

    fake = HTTPServer(("127.0.0.1", 0), FakeModelAPI)
    threading.Thread(target=fake.serve_forever, daemon=True).start()
    try:
        router = Settings(Path("."), "sk-or-test", "", "", llm_base_url=f"http://127.0.0.1:{fake.server_port}/v1")
        assert complete(router, "system", "hello") == "PLAIN: hello"
    finally:
        fake.shutdown()


# ---- get_demo_papers.py ---------------------------------------------------------
def test_demo_papers_download_skips_existing_and_rejects_non_pdf(tmp_path, monkeypatch):
    import get_demo_papers as demo

    def fake_get(url, **kwargs):
        body = b"<html>sign in</html>" if "osti" in url else b"%PDF-1.7 fake"
        return httpx.Response(200, content=body, request=httpx.Request("GET", url))

    monkeypatch.setattr(demo.httpx, "get", fake_get)
    monkeypatch.setattr(demo.time, "sleep", lambda seconds: None)
    (tmp_path / demo.FREE[1]["file"]).write_bytes(b"%PDF already here")

    assert demo.main(tmp_path) == 1                    # one source sent HTML, not a PDF
    assert not (tmp_path / demo.FREE[0]["file"]).exists()
    assert (tmp_path / demo.FREE[1]["file"]).read_bytes() == b"%PDF already here"
    assert (tmp_path / demo.FREE[2]["file"]).read_bytes().startswith(b"%PDF")


def test_downloaded_papers_are_never_committed():
    rules = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "sample_library/demo_semiconductors/" in rules
