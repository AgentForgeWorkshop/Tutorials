#!/usr/bin/env python3
"""Set up your MCP server: choose your library folder and paste your API key.

    python setup_workshop.py

Writes everything to .env, which stays on your computer and is ignored by git. You can run
this again at any time to change the folder or the key.
"""
from __future__ import annotations

import getpass
import json
import os
import platform
import shlex
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
SERVER = ROOT / "server.py"
SAMPLE = ROOT / "sample_library"
DEMO = SAMPLE / "demo_semiconductors"   # filled by get_demo_papers.py
EXTENSIONS = {".pdf", ".txt", ".md"}


def clean_path(raw: str) -> Path:
    """Accept a typed path or a folder dragged into the terminal, which may add quotes or
    backslashes before spaces."""
    text = raw.strip().strip("'\"")
    if os.name != "nt":
        text = text.replace("\\ ", " ")
    return Path(text).expanduser()


def count_documents(folder: Path) -> int:
    return sum(1 for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSIONS)


def read_env() -> dict[str, str]:
    values = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"')
    return values


def write_env(values: dict[str, str]) -> None:
    lines = ["# Written by setup_workshop.py. Never commit this file."]
    lines += [f'{key}="{value}"' for key, value in values.items() if value]
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if os.name != "nt":
        ENV_FILE.chmod(0o600)        # readable only by you


def ask_library(current: str) -> str:
    print("\n1. YOUR LIBRARY")
    print("   Paste the path to your folder of PDFs, or drag the folder into this window.")
    default = current or (str(DEMO) if DEMO.is_dir() and any(DEMO.glob("*.pdf")) else str(SAMPLE))
    print(f"   Press Enter to keep: {default}")
    while True:
        raw = input("   Folder: ").strip()
        folder = clean_path(raw) if raw else Path(default)
        if not folder.is_dir():
            print(f"   That is not a folder: {folder}. Please try again.")
            continue
        folder = folder.resolve()
        found = count_documents(folder)
        print(f"   OK: {found} document(s) in {folder}")
        if not found:
            print("   This folder has no PDF, .txt or .md files yet. You can add them later.")
        return str(folder)


def ask_secret(title: str, explanation: list[str], current: str) -> str:
    print(f"\n{title}")
    for line in explanation:
        print(f"   {line}")
    state = f"Press Enter to keep the current key (ending ...{current[-4:]})" if current else "Press Enter to skip"
    print(f"   {state}. What you paste stays hidden.")
    return getpass.getpass("   Key: ").strip() or current


def test_key(values: dict[str, str]) -> None:
    """Make one very small request, so a wrong key shows up now rather than mid-workshop."""
    sys.path.insert(0, str(ROOT))
    from research_tools.config import load_settings
    from research_tools.llm import LLMError, complete

    settings = load_settings()
    print(f"   Testing the key with {settings.model} ...", end=" ", flush=True)
    try:
        complete(settings, "Reply with the single word OK.", "Are you there?", max_tokens=2000)
        print("works.")
    except LLMError as err:
        print(f"failed.\n   {err}")


def desktop_config_path() -> Path:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    if system == "Windows":
        return Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
    return Path.home() / ".config/Claude/claude_desktop_config.json"


def add_to_claude_desktop() -> None:
    """Add this server to Claude Desktop, keeping everything else and saving a backup."""
    path = desktop_config_path()
    config = {}
    if path.exists():
        try:
            config = json.loads(path.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            print(f"   Not changed: {path} is not valid JSON. Add the block below by hand.")
            return
        backup = path.with_name(f"{path.stem}.backup-{datetime.now():%Y%m%d-%H%M%S}.json")
        shutil.copy2(path, backup)
        print(f"   Backup saved: {backup}")
    config.setdefault("mcpServers", {})["research-mcp"] = {"command": sys.executable, "args": [str(SERVER)]}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"   Added to {path}")
    print("   Now fully quit Claude Desktop and open it again.")


def print_connection_guide() -> None:
    quote = (lambda s: f'"{s}"') if os.name == "nt" else shlex.quote
    block = {"mcpServers": {"research-mcp": {"command": sys.executable, "args": [str(SERVER)]}}}
    print("\n4. CONNECT YOUR AI APP (pick one)")
    print("\n   Claude Code:")
    print(f"     claude mcp add --scope user research-mcp -- {quote(sys.executable)} {quote(str(SERVER))}")
    print("\n   Claude Desktop, Cursor or VS Code: add this to the app's MCP settings:")
    print("     " + json.dumps(block, indent=2).replace("\n", "\n     "))
    print("\n   No AI app? Use the terminal chat included here (needs an API key):")
    print(f"     {quote(sys.executable)} chat.py")


def main() -> None:
    print("=" * 66)
    print("  research-mcp setup")
    print("=" * 66)

    try:
        import dotenv, httpx, mcp, pypdf, yaml  # noqa: E401, F401
    except ImportError as err:
        sys.exit(f"Missing package: {err.name}. Activate your environment, then run:\n"
                 "  pip install -r requirements.txt")

    values = read_env()
    values["LIBRARY_PATH"] = ask_library(values.get("LIBRARY_PATH", ""))
    values["LLM_API_KEY"] = ask_secret(
        "2. YOUR AI API KEY (for automatic online reviews and for chat.py)",
        ["OpenRouter (sk-or-..., the workshop gives you credit), Google AI Studio (AIza..., free tier),",
         "Anthropic (sk-ant-...) or OpenAI (sk-...). The provider is detected for you."],
        values.get("LLM_API_KEY", ""),
    )
    values["OPENALEX_API_KEY"] = ask_secret(
        "3. FREE OPENALEX KEY (optional, recommended in a workshop)",
        ["Get one at https://openalex.org/settings/api",
         "Without it, everyone on the same network shares one small daily budget."],
        values.get("OPENALEX_API_KEY", ""),
    )
    write_env(values)
    print(f"\nSaved to {ENV_FILE} (ignored by git).")

    if values.get("LLM_API_KEY"):
        test_key(values)
    print_connection_guide()

    if desktop_config_path().parent.exists():
        answer = input("\nAdd research-mcp to Claude Desktop now? A backup is saved first. [y/N] ")
        if answer.strip().lower() == "y":
            add_to_claude_desktop()

    print(f"\nNext, test the server without any AI:\n  {sys.executable} try_server.py\n")


if __name__ == "__main__":
    main()
