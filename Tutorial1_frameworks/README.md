# Tutorial 1 — Agent frameworks

A ~75-minute, hands-on introduction to AI agents for scientists, built around one task:
**find recent papers on a topic, summarise them, and produce a literature table you can
actually use.**

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AgentForgeWorkshop/Tutorials/blob/main/Tutorial1_frameworks/01_agents_for_science.ipynb)

| | |
|---|---|
| **Notebook** | [`01_agents_for_science.ipynb`](01_agents_for_science.ipynb) |
| **Audience** | Researchers who can read Python; no agent, LangChain or LLM-API experience assumed |
| **Cost** | Free — Google AI Studio free tier + the keyless arXiv API |
| **Prerequisite** | A free API key from <https://aistudio.google.com/apikey> (one minute, no card) |

## The one idea

Every agent **framework** wraps the same short loop:

> Send the conversation plus a list of tool descriptions to the LLM. If it replies asking to
> call a tool, run that Python function, append the result, and call the LLM again. Stop when
> it answers in plain text.

Attendees write that loop by hand (Step 2) **before** they see a framework (Step 3). After
that, every framework reads as "the loop, plus conveniences" — which is the mental model that
keeps people from treating agents as magic.

## Arc

| Step | Content | Min |
|---|---|---|
| 0 | Setup; ask a bare LLM for last week's papers and watch it hallucinate or refuse | 10 |
| 1 | `search_arxiv` — a tool is just a Python function, and its docstring is part of the prompt | 5 |
| 2 | **The loop**, hand-written in ~20 lines, with the trace printed | 15 |
| 3 | The same agent via `create_agent`, in four lines | 10 |
| 4 | A second tool (`save_report`) so the agent has to sequence its work | 10 |
| 5 | Structured output: a validated `LiteratureTable` → pandas → CSV | 10 |
| 6 | Exercises: change the field, add a PubMed tool, add a critic pass | 10 |
| 7 | Finale: the same task with `create_deep_agent`, plus the caveats | 5 |

An optional appendix repeats the agent in Pydantic AI, to make the point that the framework
choice is the least important decision in the notebook.

## Why these frameworks

| Framework | Case for it | Catch |
|---|---|---|
| **LangChain 1.x** (`create_agent`) — *used for the core* | Post-1.0 API is genuinely small; model-agnostic; the name attendees will meet again | Heavy install; the web is full of stale 2023 tutorials (`initialize_agent`, `AgentExecutor`) — the notebook warns about this explicitly |
| **DeepAgents** — *used for the finale* | Identical signature to `create_agent`, but adds planning, a virtual filesystem and sub-agents. "How does this scale up?" becomes a one-cell answer | Too much hidden machinery for a first lesson; more tokens; still 0.x |
| **Pydantic AI** — *optional appendix* | Cleanest API, best structured-output story | Async-first (`await` in Colab); smaller ecosystem |
| OpenAI Agents SDK | Simple, good tracing UI | OpenAI-centric |
| Google ADK | Natural with Colab + Gemini | Runners and session services make hello-world verbose |
| smolagents | Tiny, readable source | Its flagship `CodeAgent` has the LLM write Python — a second paradigm to teach on day one |
| CrewAI, Microsoft Agent Framework, LlamaIndex | Multi-agent and RAG-first framings | More concepts than lesson one needs; name LlamaIndex if a follow-up reads full PDFs |

## A note on vocabulary: library, framework or SDK?

Attendees ask, and the packages themselves do not agree. On PyPI, pydantic-ai is an "AI Agent
Framework", smolagents is "a barebones library for agents", openai-agents is an "SDK",
google-adk is a "Kit", deepagents is a "harness", and langchain dodges the question entirely.

The distinction that actually holds is **inversion of control**:

* a **library** is code *you* call — `search_arxiv(TOPIC)` in Step 1;
* a **framework** calls *your* code — you hand `search_arxiv` to `create_agent` in Step 3, and
  it decides when to call it.

Strictly applied, most of these are libraries that invert control for the duration of one call:
they do not own your program's structure the way CrewAI, Google ADK or Microsoft Agent
Framework do. But "agent framework" is the settled term of art for the category, so the
notebook uses:

| Word | For |
|---|---|
| **framework** | the category, and what one does for you — "agent frameworks", "what did the framework add?" |
| **library** | a specific package as a package — "the deepagents library", "pin the library version" |
| **SDK** | a vendor's client for its own service — `openai`, `anthropic`, `google-genai` |

"Harness", "kit" and "toolkit" are vendor branding and only confuse a first-timer. If someone
objects that LangChain is "just a library", they are not wrong — say so and move on. The point
worth defending is that handing your function to `create_agent` is where control changes hands.

## Logistics that matter more than the framework

* **One API key per attendee.** Thirty people on one key hit the rate limit in minutes. Send
  the AI Studio link out *before* the session and ask people to arrive with a key already in
  Colab's Secrets panel (🔑 in the left sidebar, named `GOOGLE_API_KEY`).
* **arXiv as the default source.** No key, tolerant of a classroom, good coverage of
  physics/CS/quant-bio. The notebook's Exercise 2 adds PubMed (NCBI E-utilities, also keyless,
  ≤3 req/s) for life-science audiences. OpenAlex is the option for every other field.
  Semantic Scholar throttles unauthenticated traffic — avoid it live.
* **Abstracts, not full text.** Fast, cheap, and keeps the lesson about the agent rather than
  PDF parsing. Reading PDFs is flagged as a follow-up.

## Running it

**Colab (what attendees do):** click the badge, add your key to Secrets, run cells top to
bottom.

**Locally:**

```bash
python -m venv .venv && source .venv/bin/activate
pip install "langchain==1.4.2" "langchain-google-genai==4.4.0" "deepagents==0.7.16" \
            "pydantic-ai==2.46.0" pandas jupyterlab
export GOOGLE_API_KEY=...        # the notebook falls back to getpass if this is unset
jupyter lab 01_agents_for_science.ipynb
```

Versions are pinned in the install cell on purpose — this ecosystem moves fast enough to break
a notebook between semesters. To run on the latest releases, drop the `==` pins and expect to
fix a thing or two.

**Switching provider** is one string in Step 0: `openai:gpt-5.2`,
`anthropic:claude-sonnet-5`, or `google_genai:gemini-3.5-flash-lite` if the free quota gets
tight. Install the matching `langchain-*` package and set the matching env var.

## Instructor notes

Where the room gets stuck, in the order it happens:

1. **The key.** Secret name misspelt, or *Notebook access* left off — the symptom is a
   `userdata` error or a `getpass` prompt. Budget five minutes and walk the room.
2. **`429 RESOURCE_EXHAUSTED`.** Free tier, or a shared key. Wait a minute, or switch to
   `gemini-3.5-flash-lite`.
3. **Red pip output at Step 0.** The install cell always prints
   `ERROR: pip's dependency resolver...` about `google-auth`: Colab pins `2.49.0`, the Gemini
   client needs `>=2.56`, and the two cannot both be satisfied. It is a warning, the install
   succeeded, and nothing here uses the affected code path. Say so before you run the cell, or
   you will lose five minutes to it. The first LLM call then logs a one-off `automatic function
   calling (AFC)` warning from Google's SDK — also harmless, and Step 3 turns it into a point
   about who runs the loop.
4. **Step 0b is the whole motivation — don't rush it.** Ask people to read the fabricated
   citations out loud before you move on. If the model refuses instead of hallucinating,
   that lands the point equally well.
5. **Step 2 is the lesson.** If you are running short, cut Step 6 or Step 7, never Step 2.
   Ask someone to narrate the trace before you explain it.
6. **Non-determinism.** The same cell can call one search or three. Say so up front, or the
   variation across laptops reads as breakage.
7. **Agents cannot run code.** Worth stating twice: the model emits a *request*; your Python
   decides whether to honour it. That framing carries the whole security discussion in Step 8.
8. **"Is this a library or a framework?"** Someone always asks. See *A note on vocabulary*
   above; the short answer is that a framework calls your code, which is exactly what happens
   in Step 3.

## Scientific caveats the notebook makes attendees confront

Hallucinated citations (the agent read abstracts, not papers — verify every link),
non-reproducibility by default, recency ≠ relevance in a date-sorted preprint feed, cost that
scales with loop steps rather than questions, tools as permissions, and not sending embargoed
or patient data to a model provider.

## Testing status

Tool code, notebook structure and agent plumbing were verified offline: the arXiv Atom parser
against a fixture feed, and every code cell executed end to end against a scripted fake model
(plus `TestModel` for the Pydantic AI cell). **The LLM cells have not been run against a live
API key** — do one full pass in Colab before teaching, so the printed traces match what the
room will see.
