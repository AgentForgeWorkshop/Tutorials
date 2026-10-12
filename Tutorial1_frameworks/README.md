# Tutorial 1 — Agent frameworks

Two hands-on Colab notebooks, about 25 minutes each, built around one scientific task:
**find this week's arXiv papers on a topic and turn them into something useful.**

| | Notebook | The question it answers | Open |
|---|---|---|---|
| **A** | [`01a_what_is_an_agent.ipynb`](01a_what_is_an_agent.ipynb) | What *is* an agent? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AgentForgeWorkshop/Tutorials/blob/main/Tutorial1_frameworks/01a_what_is_an_agent.ipynb) |
| **B** | [`01b_workflows_vs_agents.ipynb`](01b_workflows_vs_agents.ipynb) | Should this be an agent at all? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AgentForgeWorkshop/Tutorials/blob/main/Tutorial1_frameworks/01b_workflows_vs_agents.ipynb) |

Run them in order: A builds the agent, B shows when not to build one.

*(`01_agents_for_science.ipynb` is the earlier single-notebook version of this material,
superseded by A + B.)*

## The two ideas

**A: an agent is an LLM running in a loop, plus a harness that builds the context and runs the
tools.** Attendees write that loop by hand in about twenty lines before seeing any framework,
so that LangChain, Pydantic AI and DeepAgents all read afterwards as "the loop, plus
conveniences". Nobody has to take agents on faith.

**B: ask who decides the next step — you, your code, or the LLM.** The same digest task is
built four ways, and the comparison is measured rather than asserted. The agent is one of the
four options, and often not the best one.

## Prerequisites

* A Google account, for Colab.
* An **OpenRouter API key** from <https://openrouter.ai/keys>, stored in Colab's Secrets panel
  (🔑 in the left sidebar) as `OPENROUTER_API_KEY` with *Notebook access* on. The workshop
  provides credit; outside the workshop, a dollar covers both notebooks many times over.
* Python you can read. No prior exposure to agents, LangChain or LLM APIs is assumed.
* No local install. arXiv's API needs no key.

The default model is `deepseek/deepseek-v4.1-flash` (~$0.13 per million input tokens). Setting
`PROVIDER = "google"` in Step 0 switches to Gemini on Google AI Studio's free tier instead —
free, but shared with the world, so it queues and returns `429`/`503` under load.

## Notebook A — What is an agent?

| Step | What | Min |
|---|---|---|
| 0 | Setup | 3 |
| 1 | A bare LLM fails at a literature question — refuses, or invents citations | 2 |
| 2 | A tool is just a Python function (`search_arxiv`) | 4 |
| 3 | **The loop**, written by hand, printed as Thought → Action → Observation | 6 |
| 4 | The same agent via `create_agent`, and the LangGraph drawn | 4 |
| 5 | The same agent in Pydantic AI, returning a validated table | 3 |
| 6 | DeepAgents: the same loop with a bigger harness (to-dos, files) | 3 |

Three moments carry the notebook:

* **Step 1** motivates everything. A bare model either refuses or produces plausible fake
  references — the failure mode that ends up in a bibliography.
* **Step 3's second run** deliberately uses a query too specific to match anything. The tool
  returns *"No papers found… try broader terms"*, the model reads that and picks a new query.
  Nobody wrote "if empty, retry". That is the whole difference between an agent and a script.
* **Step 2's aside on `build_arxiv_query`** teaches that arXiv reads each search term as a
  single word, so an unprocessed topic string returns near-random papers. The lesson is
  general: **the tool has to be right before the agent can be.**

## Notebook B — Which level does your task need?

| Step | Level | Who decides | Built with | Min |
|---|---|---|---|---|
| 1 | LLM call | You | a chat model | 2 |
| 2 | LLM workflow | Your code | LangGraph | 5 |
| 3 | Agentic workflow | Your code, with the LLM inside one step | LangGraph | 6 |
| 4 | Agent | The LLM | LangChain (+ optional human approval) | 5 |
| 5 | Compare all four | | pandas | 4 |

Each run is tracked, so Step 5 ends in a real table rather than an opinion. The punchline is
the **narrow topic**: a query too specific to match anything. The plain workflow runs its fixed
steps and writes a digest about nothing; only the levels where an LLM decides recover.

### Measured on one real run

DeepSeek V4.1 Flash via OpenRouter, 12 Oct 2026. Your numbers will differ — these are the
shape to expect, not constants.

| Topic | Level | LLM calls | Tokens | Seconds | Papers found |
|---|---|---|---|---|---|
| normal | LLM call | 1 | 708 | 2.3 | 1 |
| normal | LLM workflow | 2 | 5,575 | 16.7 | 5 |
| normal | Agentic workflow | 2 | 5,310 | 17.4 | 5 |
| normal | Agent | 4 | 23,791 | 9.9 | 17 |
| **narrow** | LLM workflow | 2 | 1,533 | 8.9 | **0** |
| **narrow** | Agentic workflow | 3 | 6,846 | 29.3 | 5 |
| **narrow** | Agent | 10 | 111,744 | 40.8 | 25 |

Two results worth reading out to the room:

* **Cost grows with autonomy, steeply.** On the narrow topic the agent spent **73× the tokens**
  of the plain workflow — because it resends its whole context every step, and it took ten
  steps to get there.
* **Reproducibility falls with autonomy.** Re-run on the same topic, the workflow returned the
  same papers (`True`); the agent did not (`False`). Its search queries are its own choice.
* The agentic workflow got the agent's robustness on the narrow topic at roughly the
  workflow's cost on the normal one. That is why it is the shape of most useful research
  pipelines.

## Frameworks, and what each is for

| Framework | Used for | Why it is here |
|---|---|---|
| **LangChain 1.x** (`create_agent`) | A, step 4; B, step 4 | Small post-1.0 API, model-agnostic, and the name attendees will meet again |
| **LangGraph** | A, step 4 (drawn); B, steps 2–3 | The graph under `create_agent` — and the thing you use to build workflows *without* a loop |
| **Pydantic AI** | A, step 5 | The strongest typed-output story: a validated object back, not prose |
| **DeepAgents** | A, step 6 | Same loop, bigger harness: planning to-dos, a virtual filesystem, sub-agents |

> ⚠️ Most LangChain material online predates the 1.0 rewrite and uses `initialize_agent`,
> `AgentExecutor` or `LLMChain`. That API is gone. Both notebooks warn about this; expect to
> repeat it when someone googles mid-session.

**Library, framework or SDK?** Someone always asks. A **library** is code you call; a
**framework** calls *your* code. In A/step 2 you call `search_arxiv` yourself; in A/step 4 you
hand it to `create_agent` and it decides when to call it. That handover of control is the real
distinction. Strictly, most of these are libraries that invert control for one call — but
"agent framework" is the settled term for the category, so the notebooks use *framework* for
the category, *library* for a specific package, and *SDK* for a vendor's own client. The
packages do not agree with each other either: Pydantic AI calls itself a framework,
smolagents a library, OpenAI's an SDK, DeepAgents a harness.

## Logistics that matter more than the framework

* **One API key per attendee.** Thirty people on one key hit the rate limit in minutes. Send
  <https://openrouter.ai/keys> out *before* the session and ask people to arrive with the key
  already in Colab Secrets.
* **arXiv as the source.** No key, tolerant of a classroom, good coverage of
  physics/CS/quant-bio. A's take-home exercise adds PubMed (NCBI E-utilities, also keyless,
  ≤3 req/s) for life-science audiences; OpenAlex covers every other field.
* **Abstracts, not full text.** Fast, cheap, and keeps the lesson about the agent rather than
  PDF parsing.
* **Choosing a different model.** Any id from <https://openrouter.ai/models> works, but it
  **must support tool calling** — filter for *Tools*. A model without it chats happily, never
  calls `search_arxiv`, and merely looks broken. Free `:free` ids churn (DeepSeek's were
  retired), so check the live list rather than trusting one written down here.

## Running locally

Colab is the intended route. Locally:

```bash
python -m venv .venv && source .venv/bin/activate
pip install "langchain==1.4.2" "langchain-google-genai==4.4.0" \
            "langchain-openai==1.6.2" "deepagents==0.7.16" \
            "pydantic-ai==2.46.0" pandas jupyterlab
export OPENROUTER_API_KEY=...    # or GOOGLE_API_KEY; getpass prompts if neither is set
jupyter lab
```

Versions are pinned in both notebooks on purpose — this ecosystem moves fast enough to break a
notebook between semesters. Drop the `==` pins for the newest releases, and expect to fix a
thing or two. The model id appears in both notebooks' Step 0; change both.

## Instructor notes

Where the room gets stuck, roughly in order:

1. **The key.** Secret name misspelt, or *Notebook access* left off — the symptom is a
   `userdata` error or a `getpass` prompt. Budget five minutes and walk the room.
2. **Red pip output.** The install cell prints `ERROR: pip's dependency resolver...` about
   `google-auth`: Colab pins one version, the Gemini client needs a newer one, and the two
   cannot both be satisfied. It is a warning, the install succeeded. Say so *before* running
   the cell. The first LLM call then logs a one-off `automatic function calling (AFC)` warning
   from Google's SDK — also harmless.
3. **`429` or `503 UNAVAILABLE`.** Quota, rate limit or an empty OpenRouter balance; or
   provider capacity, which hits the whole room at once. The client already retries with
   backoff, so a 503 that reaches an attendee will not fix itself on a re-run. Have a fallback
   ready to call from the front — another model id, or `PROVIDER = "google"`. Verify your
   chosen model the morning of the workshop and keep a second provider's key in your pocket.
4. **A/step 1 is the motivation — don't rush it.** Ask someone to read the fabricated
   citations out loud. A refusal instead of a hallucination lands the point equally well.
5. **A/step 3 is the lesson.** If you are short on time, cut steps 5 and 6, never step 3. Ask
   someone to narrate the trace before you explain it.
6. **B/step 2's narrow topic is B's punchline.** Let people see the workflow confidently
   produce a digest about nothing before you show step 3 fixing it.
7. **Non-determinism.** The same cell can make one search or three, and B/step 5 proves the
   agent is not reproducible. Say so up front, or the variation across laptops reads as
   breakage.
8. **"Agents can't run code."** Worth stating twice: the model emits a *request*; your Python
   decides whether to honour it. That framing carries the whole safety discussion.
9. **"Is this a library or a framework?"** See above; the short answer is that a framework
   calls your code, which is exactly what happens in A/step 4.

## Scientific caveats the notebooks make attendees confront

Hallucinated citations (the agent read abstracts, not papers — verify every link);
non-reproducibility by default, now measured rather than claimed; recency ≠ relevance in a
date-sorted preprint feed; cost that scales with loop steps rather than questions; `relevance`
scores that are the model's opinion, not a measurement; tools as permissions, with human
approval shown in B/step 4 for anything hard to undo; and not sending embargoed or patient data
to a model provider.

## Where this sits in the series

Tutorial 1 establishes the mental model the rest build on. Both notebooks point forward:
DeepAgents' filesystem is a form of **memory** (Tutorial 2), and an agent whose tools are other
agents is a **multi-agent system** (Tutorial 4).

## Verification status

Both notebooks ship with executed outputs from a full run on 12 Oct 2026 (DeepSeek V4.1 Flash
via OpenRouter): no cell errored, the arXiv query fix returns on-topic papers, and Pydantic AI
reaches OpenRouter through its `openrouter:` prefix. The committed outputs are what the room
should expect to see, not a guarantee — model behaviour and the arXiv feed both move.
