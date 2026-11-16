# Troubleshooting

**First, find where the problem is:**

```bash
python try_server.py
```

If this works but your AI app shows no tools, the problem is in the app's settings. If this fails,
the problem is in your Python setup.

**Nothing works on your laptop?** Use the Colab version, which needs no install: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AgentForgeWorkshop/Tutorials/blob/main/Tutorial3_mcp_skills/03_mcp_skills_colab.ipynb)

## Python and installation

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` or `Missing package` | Activate the environment (`source .venv/bin/activate`, or on Windows `.venv\Scripts\Activate.ps1`), then run `pip install -r requirements.txt` |
| `python` not found (macOS or Linux) | Use `python3` until the environment is active |
| `python` opens the Microsoft Store (Windows) | Use `py` |
| PowerShell blocks `Activate.ps1` | Run `Set-ExecutionPolicy -Scope Process RemoteSigned`, then activate again |
| `cannot import name 'MCPServer'` | You have the old MCP SDK. Activate the environment and reinstall the requirements |
| Python older than 3.10 | Install a newer version from [python.org](https://www.python.org/downloads/), then make the environment with it: `python3.12 -m venv .venv` |
| `No matching distribution found for mcp` | Your Python is older than 3.10 (macOS's built-in Python is 3.9). Delete `.venv` and make it again with a newer Python, as above |
| `Could not open requirements file` | You are in the wrong folder. `cd` into `Tutorial3_mcp_skills` first |

## Library

| Problem | Fix |
|---|---|
| "library folder does not exist" | Run `python setup_workshop.py` and choose the folder again |
| A PDF is listed as having no readable text | It is probably a scan with no text layer. Run OCR on it first |
| No results for a search | Search matches words, not meanings. Use words that appear in the papers |
| The first search is slow | Large libraries are indexed once, then cached in `.cache/`. If your app times out, ask again and it continues from where it stopped |

## AI app connection

| Problem | Fix |
|---|---|
| Claude Desktop shows no tools | Fully quit it (not just close the window) and reopen it. Then check Settings → Developer for the error |
| `spawn ... ENOENT` | A path in the config is wrong. Run the setup again and use the paths it prints |
| macOS: the folder cannot be read from Claude Desktop | Allow access in System Settings → Privacy & Security → Files and Folders, or move the folder out of Documents, Desktop or Downloads |
| `claude mcp list` shows "Failed to connect" | Run the printed command again from the workshop folder with the environment active |
| `claude`, `gemini` or `codex`: command not found | That app isn't installed. Pick another app from [A2](A-mcp-access.md#a2-connect-your-ai-app-and-ask), or use `python chat.py` |
| ChatGPT cannot use `research-mcp` | Expected. ChatGPT needs a server on the internet, not on your laptop. See [Part D](D-platform.md) |

## API keys

| Problem | Fix |
|---|---|
| "rejected the API key" | Run the setup again and paste the full key. An API key is not the same as a Claude or ChatGPT subscription |
| "does not support tools" or a 404 on OpenRouter | Pick a model with the **Tools** filter on [openrouter.ai/models](https://openrouter.ai/models) and set `LLM_MODEL` in `.env` |
| "does not recognise the model" | Set `LLM_MODEL` in `.env` to a model your account can use |
| "rate limit" or "quota" | Wait a minute, or check your credit in the provider's console |
| "OpenAlex: daily or rate limit reached" | Search still works through the other sources. Add a [free OpenAlex key](https://openalex.org/settings/api) |
| "arXiv: daily or rate limit reached" | arXiv limits rapid requests. Wait a few seconds and try again |

**If you ever commit a key by accident,** delete it in the provider's console straight away. Removing
it from git is not enough.

## Valency

| Problem | Fix |
|---|---|
| Valency is not in the **+** menu | Refresh the page, then see [Valency's ChatGPT guide](https://docs.valency.io/guides/chatgpt/) |
| Sign-in fails or tools stop working | See [reconnecting](https://docs.valency.io/help/reconnecting/) |
| Calls are refused | You may have reached the free limit. Verify a work email to raise it |
