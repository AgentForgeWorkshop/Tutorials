# Part D · MCP on a platform: Valency in ChatGPT

**Goal:** see the other kind of MCP server, hosted by someone else and used with no code. About 6 minutes.

[Valency](https://www.valency.io/) offers an MCP server called
[MCP Bond](https://www.valency.io/bond/). It searches over 500 million research papers, including
arXiv, bioRxiv, medRxiv and PubMed, through 36 tools.

| | Your server | Valency |
|---|---|---|
| Runs | On your laptop | On the internet |
| Transport | stdio | Streamable HTTP |
| Sign-in | None, local access only | OAuth (Google, GitHub or Microsoft) |
| Sees | Your own files | Published literature |
| Works in ChatGPT | No | **Yes** |

## D1. Connect it

These steps follow [Valency's ChatGPT guide](https://docs.valency.io/guides/chatgpt/). Menu names
change, so check that page if yours looks different.

1. Open [chatgpt.com/plugins](https://chatgpt.com/plugins) and choose **Add → Add custom MCP server**.
2. Fill in the form:
   - **Name:** `Valency`
   - **Description:** `Infrastructure for Agentic Science`
   - **Connection (Server URL):** `https://mcp.valency.io/`
3. Leave **Authentication** on **OAuth**, tick **I understand and want to continue**, and click
   **Create as a plugin**.
4. Click **Sign in with Valency**, accept the consent screen, and sign in with Google, GitHub or Microsoft.
5. In a chat, click **+** beside the message box and select **Valency**. Refresh the page if it is missing.
6. Test it:

```text
Use Valency to list the sources it can search.
```

✅ **Checkpoint:** ChatGPT calls the tool and lists the sources.

> **Free limits:** Valency lists 100 calls a day for an unverified individual account, and 1,000 a
> week after you verify a work email. A single review can use several calls.

## D2. A literature review in four prompts

Send these one at a time and watch which tools are called.

**Find the papers:**

```text
Use Valency to find the 10 most relevant papers since 2022 on interlayers for suppressing
lithium dendrites in solid-state batteries. For each one, give the title, first author, year,
link and main finding in one line. Use only what Valency returns.
```

**See the trend:**

```text
Use Valency to show how publications on "solid electrolyte interlayer" have changed by year.
```

**Compare the evidence:**

```text
From those papers, make a table of material, cell type, stack pressure and main result.
Write "not reported" when the abstract does not say. Where do the papers disagree?
```

**Export the references:**

```text
Export the papers you used as BibTeX with Valency.
```

✅ **Checkpoint:** you have a table and a BibTeX list. **Open three links and check that the
papers exist and say what the table claims.**

## What to notice

- You wrote no code and installed nothing. This is what "write once, use from any host" means in practice.
- Your server and Valency speak the same protocol. Only the transport and the sign-in differ.
- The model chooses which of the 36 tools to call, so a good tool description really matters.

## Same server in Claude

From [Valency's Claude guide](https://docs.valency.io/guides/claude/): in the Claude apps, open
[claude.ai/directory/valency](https://claude.ai/directory/valency) and choose **Connect to Claude**.
In Claude Code:

```bash
claude mcp add --transport http --scope user valency https://mcp.valency.io/
```

```bash
claude mcp login valency
```

Now one conversation can use your local library **and** Valency.

## Wrap-up

```text
Compare what my library says about stack pressure with what Valency finds in the published
literature. Where is my library behind the field?
```

**Next:** [Part E · Decide](E-decide.md)
