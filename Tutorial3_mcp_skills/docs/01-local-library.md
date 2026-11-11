# Step 1: Your local library

**Goal:** your AI app can search and read your own PDFs and cite the page. **No API key needed.**

## 1.1 Choose your folder

If you have not already, run:

```bash
python setup_workshop.py
```

When asked for the folder, paste its path or drag it into the terminal. Subfolders are included.
PDF, `.txt` and `.md` files are read. Press Enter to practise with `sample_library/` instead.

To change the folder later, run the setup again or edit `LIBRARY_PATH` in `.env`. It takes effect
immediately, so you do not need to restart anything.

## 1.2 Test the server, with no AI

```bash
python try_server.py
python try_server.py local "stack pressure"
```

✅ **Checkpoint:** you see 11 tools, your documents, and passages labelled with a file and page.

This is what every AI app does when it connects: start the server, discover what it offers, call a tool.

## 1.3 Connect your AI app

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
> to servers on the internet, which is what you will do in [Step 5](05-valency-chatgpt.md).

## 1.4 Ask about your papers

```text
What documents are in my library?
```

```text
Do my papers agree on stack pressure versus interlayers? Cite the file and page.
```

✅ **Checkpoint:** the answer cites pages, and you can open the PDF and confirm them.

## 1.5 See how little code it took

Open `server.py` and find `search_papers`:

```python
@mcp.tool()
def search_papers(query: str, top_k: int = 5) -> str:
    """Search the user's local document library by keyword. ..."""
```

- The **type hints** become the tool's input schema.
- The **docstring** is what the model reads to decide when to use the tool.
- The real work is in `research_tools/library.py`, which knows nothing about MCP.

## Practise with real papers

After the checkpoint, add three real review papers on semiconductors to the practice library:

```bash
python get_demo_papers.py
```

They are free author versions, downloaded from arXiv and OSTI.gov into
`sample_library/demo_semiconductors/`. Git ignores that folder, because publishers' PDFs must not be
shared publicly: the repository keeps only the links. Then try:

```text
Which semiconductors in my library have the widest band gaps, and what limits their use?
```

Two related papers have no free copy. The script prints their DOI links, in case your institution
has access.

## Try this

1. Add a new PDF to your folder and search for its topic. No restart is needed.
2. Change the docstring of `search_papers` to "Searches stuff", restart your app, and ask again.
   Does the model still use the tool well?

**Next:** [Step 2: Online literature](02-online-literature.md)
