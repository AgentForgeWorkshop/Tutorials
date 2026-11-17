# AgentForge Workshop — Tutorials

Hands-on notebooks introducing AI agents for scientific work. Each tutorial is a
self-contained Google Colab notebook: no local setup, and an API key that costs cents (or nothing, on a free tier).

| # | Tutorial | What you build | Link |
|---|---|---|---|
| 1 | [mini_agent](Tutorial1_mini_agent/) |Introduction to agent loop via an in-house code "mini_agent" by Shichuan Sun | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Superionichuan/agent-tutorial/blob/main/notebooks/agent_tutorial_colab.ipynb) |
| 1 | [agent_frameworks 01a](Tutorial1_frameworks/) | What is an agent? Write the loop by hand, then the same agent in LangChain, Pydantic AI and DeepAgents | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AgentForgeWorkshop/Tutorials/blob/main/Tutorial1_frameworks/01a_what_is_an_agent.ipynb) |
| 1 | [agent_frameworks 01b](Tutorial1_frameworks/) | LLM call, workflow, agentic workflow or agent? The same task built four ways and compared | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AgentForgeWorkshop/Tutorials/blob/main/Tutorial1_frameworks/01b_workflows_vs_agents.ipynb) |
| 3 | [mcp_skills](Tutorial3_mcp_skills/) | Your own MCP server on your laptop: search your PDF library, review online literature, a calculator skill and checked lay abstracts; then Valency in ChatGPT | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AgentForgeWorkshop/Tutorials/blob/main/Tutorial3_mcp_skills/03_mcp_skills_colab.ipynb) |
| 5 | [evals](Tutorial5_evals/) | Evaluate a paper-triage agent: graders (code and LLM judge), an eval harness with pass@k and pass^k, prompt v1 vs v2, answer key v1 vs v2, agent vs LLM workflow; optionally in LangSmith | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AgentForgeWorkshop/Tutorials/blob/main/Tutorial5_evals/hands-on/notebook/05_evaluating_a_triage_agent.ipynb) |

Start with Tutorial 1 — it establishes the mental model (an agent is a short loop around an
LLM and some Python functions) that the rest build on.
