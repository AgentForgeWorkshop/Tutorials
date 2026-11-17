"""Settings and model setup — same key handling as Tutorial 1 (Colab Secrets, env, or a prompt)."""
import getpass
import os
import pathlib

try:
    from dotenv import load_dotenv
except ImportError:  # dotenv is optional (e.g. in Colab)
    load_dotenv = None

ROOT = pathlib.Path(__file__).resolve().parents[1]
if load_dotenv:
    load_dotenv(ROOT / ".env")

DATA_DIR = pathlib.Path(os.getenv("MP_DATA_DIR", ROOT / "data"))
RESULTS_DIR = pathlib.Path(os.getenv("MP_RESULTS_DIR", ROOT / "results"))

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# Any id from https://openrouter.ai/models that supports tool calling ("Tools" filter).
AGENT_MODEL = os.getenv("AGENT_MODEL", "openai/gpt-5-mini")    # small model: the agent / workflow
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "openai/gpt-5.6-terra")  # large model: the LLM judge

# Max agent steps (one step = one model call or one round of tool calls)
RECURSION_LIMIT = int(os.getenv("AGENT_RECURSION_LIMIT", "80"))


def get_key(name: str) -> str:
    """Read an API key from Colab's Secrets panel, or the environment / .env, or ask for it."""
    try:
        from google.colab import userdata
        return userdata.get(name)
    except Exception:  # not in Colab, or that secret is not set
        return os.environ.get(name) or getpass.getpass(f"{name}: ")


def make_model(model_id: str | None = None, **kwargs):
    """A chat model served through OpenRouter (OpenRouter speaks the OpenAI API)."""
    from langchain.chat_models import init_chat_model
    if not os.environ.get("OPENROUTER_API_KEY"):
        os.environ["OPENROUTER_API_KEY"] = get_key("OPENROUTER_API_KEY")
    return init_chat_model(f"openai:{model_id or AGENT_MODEL}", base_url=OPENROUTER_BASE_URL,
                           api_key=os.environ["OPENROUTER_API_KEY"], max_retries=4, **kwargs)
