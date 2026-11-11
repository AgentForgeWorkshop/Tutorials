# Step 2: Online literature

**Goal:** paste an API key and get a cited review of published literature.

## 2.1 Add your keys

```bash
python setup_workshop.py
```

Press Enter to keep your folder, then paste your keys:

| Key | Needed for | Where to get it |
|---|---|---|
| **AI key** | Automatic reviews and `chat.py` | The same [OpenRouter](https://openrouter.ai/keys) key as in Tutorial 1 (`sk-or-...`, the workshop gives you credit), a free [Google AI Studio](https://aistudio.google.com/apikey) key (`AIza...`), or an [Anthropic](https://platform.claude.com/settings/keys) or [OpenAI](https://platform.openai.com/api-keys) key. The provider is detected for you. |
| **OpenAlex key** (optional, free) | A personal search budget | [openalex.org/settings/api](https://openalex.org/settings/api) |

> **Why bother with an OpenAlex key?** Without one, everyone on the same network shares a small
> daily budget, so a full room can use it up in minutes. If that happens, search keeps working
> through arXiv and Europe PMC, and the result tells you OpenAlex was unavailable.

The setup makes one tiny test request and tells you whether your AI key works.

## 2.2 Search without AI

```bash
python try_server.py online "lithium dendrite interlayer"
```

✅ **Checkpoint:** real papers with links and abstracts. This step needs no AI key.

## 2.3 Ask for a review

In your AI app:

```text
Use review_online_literature: do interlayers still suppress lithium dendrites at high stack pressure?
```

Or from the terminal:

```bash
python try_server.py review "Do interlayers suppress lithium dendrites at high stack pressure?"
```

✅ **Checkpoint:** a short answer, a table with [n] citations, disagreements, gaps, and a reference list.

## 2.4 Why the references can be trusted

Open `research_tools/review.py`. Only two of the four steps use AI:

```text
question -> [AI] search queries -> [code] search databases
         -> [AI] review of abstracts -> [code] check citations, add references
```

- The **reference list comes from database records**, so the model cannot invent a paper.
- A **citation check** warns you if the model cites a number it was not given.
- The result **says it is based on abstracts only**. Read the papers before relying on a claim.

**Design lesson:** give the model the judgement, and keep the facts in code.

## Try this

1. Ask about your own research field. Follow two references and check that they support the claim.
2. Limit the date: `search_online` and `review_online_literature` both accept `year_from`.
3. Set `LLM_MODEL` in `.env` to a stronger model, for example `anthropic/claude-sonnet-5.5` on
   OpenRouter, and compare the reviews and the cost.

**Cost:** each review makes two model calls. The defaults are low-cost models:
`deepseek/deepseek-v4.1-flash` on OpenRouter (as in Tutorial 1), `gemini-3.5-flash` on Google,
`claude-haiku-5-5` on Anthropic and `gpt-6-luna` on OpenAI. Check your provider's dashboard for
your actual spend.

**Next:** [Step 3: Calculator skill](03-calculator-skill.md)
