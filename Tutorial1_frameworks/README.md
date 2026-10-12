# Tutorial 1 — Agent frameworks

Two Colab notebooks, about 25 minutes each. Run them in order.

| | Notebook | What it covers | |
|---|---|---|---|
| **A** | [`01a_what_is_an_agent.ipynb`](01a_what_is_an_agent.ipynb) | An agent is an LLM in a loop with tools. Write that loop by hand in ~20 lines, then see the same agent in LangChain/LangGraph, Pydantic AI and DeepAgents. | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AgentForgeWorkshop/Tutorials/blob/main/Tutorial1_frameworks/01a_what_is_an_agent.ipynb) |
| **B** | [`01b_workflows_vs_agents.ipynb`](01b_workflows_vs_agents.ipynb) | Who decides the next step — you, your code, or the LLM? The same task built as an LLM call, a workflow, an agentic workflow and an agent, then compared on cost and reproducibility. | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AgentForgeWorkshop/Tutorials/blob/main/Tutorial1_frameworks/01b_workflows_vs_agents.ipynb) |

Both use the same scientific task: find this week's arXiv papers on a topic you choose, and
turn them into a summary, a literature table, or an email digest.

## What you need

An OpenRouter API key from <https://openrouter.ai/keys>, added to Colab's Secrets panel
(🔑 in the left sidebar) as `OPENROUTER_API_KEY` with *Notebook access* on. A run costs well
under a cent. Step 0 of either notebook switches to Google AI Studio's free tier instead, with
`PROVIDER = "google"` and a `GOOGLE_API_KEY` secret.

arXiv needs no key, and nothing has to be installed locally.
