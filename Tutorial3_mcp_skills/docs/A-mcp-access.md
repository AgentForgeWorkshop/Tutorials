# Part A · MCP: give your agent access

**Goal:** your AI app can search and read your own papers, and published literature, through your
own MCP server. **No AI key needed.** About 10 minutes.

MCP is the connection: it decides what your agent can **reach**. A server offers three building
blocks: **tools** (the model calls them), **resources** (the app loads them) and **prompts** (you
pick them).

## A1. Discover what your server offers

If you have not run the setup yet, do it first: see the [README](../README.md#quick-start). It downloads three real
review papers on semiconductors (`python get_demo_papers.py`), the same papers as in the talk.

```bash
python try_server.py
python try_server.py local "band gap"
```

✅ **Checkpoint:** you see 11 tools, 1 resource and 2 prompts, then passages labelled with a file
and a page.

This is what every MCP client does when it connects: start the server, discover what it offers,
call a tool. No AI is involved, so if this works but your app doesn't, the problem is in the app's
settings.

To use another folder of papers, run `python setup_workshop.py` again or edit `LIBRARY_PATH` in
`.env`. It takes effect immediately.

## A2. Connect your AI app and ask

### Which apps can use your server?

Your server is a program on your laptop, so only apps that also run on your laptop can start it.

| Can start your local server | How |
|---|---|
| Claude Desktop | Answer `y` in the setup, or **Settings → Developer → Edit Config** |
| Claude Code | `claude mcp add` |
| Cursor, Windsurf | Paste the printed JSON block into the MCP settings |
| VS Code (Copilot agent mode) | The same block, with the key `servers` in place of `mcpServers` |
| Gemini CLI | `gemini mcp add` |
| OpenAI Codex CLI | `codex mcp add` |
| `chat.py`, in this folder | Any model, with your API key |

| Can't start it | Why |
|---|---|
| ChatGPT (web, desktop and mobile) | It reaches only remote servers over HTTPS. That is [Part D](D-platform.md). |
| claude.ai in a browser, Claude mobile | Remote connectors only. Claude Desktop, on your laptop, can. |
| Other browser chats and phone apps | They have no way to start a program on your laptop. |

To use your server from those apps, it would have to run on the internet over HTTPS, with sign-in,
like Valency in Part D.

### Connect one app, step by step

The setup printed these commands with the full paths for your computer. You can also type them
yourself: `$PWD` fills in the folder you are in.

**1. Go to the folder and switch on the environment** (use your own path):

```bash
cd ~/Tutorials/Tutorial3_mcp_skills
```

```bash
source .venv/bin/activate
```

On Windows PowerShell: `.venv\Scripts\Activate.ps1`, and write `$PWD\.venv\Scripts\python.exe`
wherever the commands below say `"$PWD/.venv/bin/python"`.

**2. Connect one app.**

*Claude Code:*

```bash
claude mcp add --scope user research-mcp -- "$PWD/.venv/bin/python" "$PWD/server.py"
```

```bash
claude mcp list
```

You should see `research-mcp: ... connected`. Then start `claude`.

*Gemini CLI:*

```bash
gemini mcp add --scope user research-mcp "$PWD/.venv/bin/python" "$PWD/server.py"
```

*OpenAI Codex CLI:*

```bash
codex mcp add research-mcp -- "$PWD/.venv/bin/python" "$PWD/server.py"
```

*Claude Desktop:* run the setup again and answer `y`, then fully quit and reopen the app.

```bash
python setup_workshop.py
```

*Cursor, Windsurf or VS Code:* paste the JSON block the setup printed into the app's MCP settings.

*No AI app, but you have an API key* (for example your OpenRouter key from Tutorial 1):

```bash
python chat.py
```

`command not found` means that app isn't installed: pick another one.

**3. Start the app and ask:**

```text
What documents are in my library?
```

```text
What do my papers say about semiconductor materials? Cite the file and page.
```

✅ **Checkpoint:** the answer cites pages, and you can open the PDF and confirm them.

## A3. A tool is a Python function

Open `server.py` and find `search_papers`:

```python
@mcp.tool()
def search_papers(query: str, top_k: int = 5) -> str:
    """Search the user's local document library by keyword. ..."""
```

- The **type hints** become the tool's input schema.
- The **docstring** is what the model reads to decide when to use the tool.
- The real work is in `research_tools/library.py`, which knows nothing about MCP.

**Try it:** change the docstring to "Searches stuff", restart your app, and ask again. Does the
model still use the tool well?

## A4. Reach published literature

The same server also reaches online databases. No AI key is needed for search:

```bash
python try_server.py online "microplastics in drinking water"
```

Try your own topic too, for example `"coffee and sleep quality"` or `"smartphones and teen sleep"`.

✅ **Checkpoint:** real papers with links and abstracts, from OpenAlex, arXiv and Europe PMC.

> **A free OpenAlex key helps.** Without one, everyone on the same network shares a small daily
> budget, so a full room can use it up in minutes. If that happens, search keeps working through
> arXiv and Europe PMC. Get a key at [openalex.org/settings/api](https://openalex.org/settings/api)
> and paste it into `python setup_workshop.py`.

## About the papers

The three papers are free author versions of published reviews (Wong et al. 2021, Woods-Robinson
et al. 2020, Yue et al. 2020), downloaded from arXiv and OSTI.gov into
`sample_library/demo_semiconductors/`. Git ignores that folder, because publishers' PDFs must not be
shared publicly: the repository keeps only the links. Page numbers differ from the journal versions.

Then try:

```text
Which semiconductors in my library have the widest band gaps, and what limits their use?
```

**Next:** [Part B · Agent Skills](B-skills.md)
