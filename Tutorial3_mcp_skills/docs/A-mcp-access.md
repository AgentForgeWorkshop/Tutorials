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

The setup printed these commands with the correct paths for your computer. Choose one.

**Claude Desktop.** Answer `y` when the setup offers to add the server, or go to
**Settings → Developer → Edit Config** and paste the printed block. Then fully quit and reopen the app.

**Claude Code.** Run the printed `claude mcp add` command, then check it:

```bash
claude mcp list
```

**Cursor or VS Code.** Paste the printed block into the app's MCP settings. VS Code uses the key
`servers` in place of `mcpServers`.

**No AI app, but you have an API key** (for example your OpenRouter key from Tutorial 1). Use the
terminal chat:

```bash
python chat.py
```

> ChatGPT is not on this list because it cannot start a program on your laptop. It connects only
> to servers on the internet, which is what you will do in [Part D](D-platform.md).

Then ask:

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
python try_server.py online "ultrawide bandgap semiconductor power electronics"
```

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
