<p align="center"><img src="assets/agentforge-logo.png" alt="AgentForge" width="360"></p>

# Tutorial 3: Build your own research MCP server

**AgentForge Workshop · Tutorial 3 hands-on · 50 minutes.** Author: Kosiachevskyi Dmytro (NUS).

Can't install it on your laptop? Use the Colab version instead: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AgentForgeWorkshop/Tutorials/blob/main/Tutorial3_mcp_skills/03_mcp_skills_colab.ipynb)

By the end you will have an MCP server running on your laptop that gives your AI app four abilities:

| Step | What you add | You provide | Time |
|---|---|---|---|
| [1. Local library](docs/01-local-library.md) | Search and read your own PDFs, with page citations | The path to your folder | 15 min |
| [2. Online literature](docs/02-online-literature.md) | A cited review of published papers | Your API key | 10 min |
| [3. Calculator skill](docs/03-calculator-skill.md) | Exact arithmetic, plus the know-how to use it | Nothing | 5 min |
| [4. Lay abstract](docs/04-lay-abstract.md) | Plain-language summaries that are checked, not just written | A document | 10 min |
| [5. Valency in ChatGPT](docs/05-valency-chatgpt.md) | A hosted MCP server across 500M+ papers, with no code | A free Valency sign-in | 5 min |

Something not working? See [Troubleshooting](docs/troubleshooting.md).

## Quick start

You need Python 3.10 or newer. Check with `python3 --version` (Windows: `py --version`).

**macOS or Linux**

```bash
git clone https://github.com/AgentForgeWorkshop/Tutorials.git
cd Tutorials/Tutorial3_mcp_skills
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python setup_workshop.py
```

**Windows (PowerShell)**

```powershell
git clone https://github.com/AgentForgeWorkshop/Tutorials.git
cd Tutorials/Tutorial3_mcp_skills
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python setup_workshop.py
```

No git? On [the Tutorials page](https://github.com/AgentForgeWorkshop/Tutorials), click **Code → Download ZIP**, unzip it, and open a terminal in the `Tutorial3_mcp_skills` folder.

The setup asks for your library folder (you can drag it into the terminal) and your API key: the
same OpenRouter key as in Tutorial 1, a free Google AI Studio key, or an Anthropic or OpenAI key. Both
are saved in `.env` on your computer, which git ignores. It then prints how to connect your AI
app. **Then start with [Step 1](docs/01-local-library.md).**

## How it fits together

```text
 Your AI app  <--- MCP --->  server.py  ---> your folder of documents
 Claude, Cursor,             11 tools   ---> OpenAlex, arXiv, Europe PMC
 VS Code, chat.py            3 skills   ---> your AI API key, for automatic reviews
```

| File | What it does |
|---|---|
| `server.py` | The MCP server. **Read this one first.** |
| `research_tools/` | Plain Python with no MCP: library, online search, review, lay abstract checks |
| `skills/` | The know-how: calculator, lay-abstract, literature-review, and a template for your own |
| `setup_workshop.py` | Asks for your folder and key, then shows how to connect your app |
| `try_server.py` | Calls the server directly, with no AI, for testing |
| `chat.py` | A small AI app for your terminal, if you have no other |
| `03_mcp_skills_colab.ipynb` | The same steps in Google Colab, with nothing to install |
| `sample_library/` | Five practice papers |
| `get_demo_papers.py` | Downloads three real, freely available papers into `sample_library/` (optional) |
| `tests/` | `pip install -r requirements-dev.txt`, then `python -m pytest` (no key or internet needed) |

## What leaves your computer

- **Your documents stay on your disk.** Your AI app sends the passages it reads to its model provider.
- **Online searches** send your search words to OpenAlex, arXiv and Europe PMC.
- **`review_online_literature`** sends your question and public abstracts to your AI provider.
- **Your API key** stays in `.env`. Never commit that file or put a key in a shared config.

Use your organisation's approved AI tools for confidential or unpublished work.

## About the sample papers

The five PDFs in `sample_library/` are **synthetic**. They were written for this workshop, with
invented authors and data, and papers 1 and 5 partly disagree on purpose. Do not cite them.

`python get_demo_papers.py` adds three real review papers on semiconductors (Wong et al. 2021,
Woods-Robinson et al. 2020, Yue et al. 2020), downloaded from arXiv and OSTI.gov. Only their links
are in this repository; the PDFs stay on your computer.

## Keep going

- **Add your own tool:** write a Python function in `server.py` with `@mcp.tool()` and a clear docstring.
- **Add your own skill:** copy `skills/_template/` and follow the instructions inside.
- **Licence:** MIT, so you can reuse all of this in your hackathon project.
