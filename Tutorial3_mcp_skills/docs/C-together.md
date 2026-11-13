# Part C · MCP and Skills together

**Goal:** combine access and method in one task: a cited literature review. **C1 needs an AI key.**
About 8 minutes.

MCP retrieves the evidence; the skill decides how to use it; code checks what can be checked.

## Add your AI key

If you skipped it during setup, run it again and paste your key:

```bash
python setup_workshop.py
```

| Key | Where to get it |
|---|---|
| **AI key** | The same [OpenRouter](https://openrouter.ai/keys) key as in Tutorial 1 (`sk-or-...`, the workshop gives you credit), a free [Google AI Studio](https://aistudio.google.com/apikey) key (`AIza...`), or an [Anthropic](https://platform.claude.com/settings/keys) or [OpenAI](https://platform.openai.com/api-keys) key. The provider is detected for you. |

The setup makes one tiny test request and tells you whether your key works.

## C1. A cited review from published literature

In your AI app:

```text
Use review_online_literature: what limits ultrawide-bandgap semiconductors in power electronics?
```

Or from the terminal:

```bash
python try_server.py review "What limits ultrawide-bandgap semiconductors in power electronics?"
```

✅ **Checkpoint:** a short answer, a table with [n] citations, disagreements, gaps, and a reference list.

**Why the references can be trusted.** Open `research_tools/review.py`. Only two of the four steps use AI:

```text
question -> [AI] search queries -> [code] search databases (MCP)
         -> [AI] review of abstracts -> [code] check citations, add references
```

- The **reference list comes from database records**, so the model cannot invent a paper.
- A **citation check** warns you if the model cites a number it was not given.
- The result **says it is based on abstracts only**. Open two of the papers and check the claims.

## C2. The literature-review skill on your library

Now the same idea on your own papers, driven by a skill instead of one tool:

```text
Use the literature-review skill: what do my papers say about semiconductor materials?
```

Watch the tool calls. The skill makes the agent:

1. `list_papers`: map the library
2. `search_papers` 3–5 times: search widely
3. `read_page`: read before citing
4. `read_skill_file`: open the grading rubric, only when it starts grading
5. `calculate`: check any number it derives

✅ **Checkpoint:** a table of the material families in your papers (what each is for, and what limits
it), cited by file and page, with a verdict and a confidence level.

**MCP gives it the papers; the skill gives it the method.** These are the same tools as in Part A,
now used in a fixed, repeatable order.

## Try this

1. Ask C1 about your own research field. Follow two references and check that they support the claim.
2. Limit the date: `search_online` and `review_online_literature` both accept `year_from`.
3. Set `LLM_MODEL` in `.env` to a stronger model, for example `anthropic/claude-sonnet-5.5` on
   OpenRouter, and compare the reviews and the cost.

**Cost:** each C1 review makes two model calls. The defaults are low-cost models:
`deepseek/deepseek-v4.1-flash` on OpenRouter (as in Tutorial 1), `gemini-3.5-flash` on Google,
`claude-haiku-5-5` on Anthropic and `gpt-6-luna` on OpenAI. Check your provider's dashboard for
your actual spend.

**Next:** [Part D · MCP on a platform](D-platform.md)
