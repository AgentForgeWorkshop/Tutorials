#!/usr/bin/env python3
"""Talk to your MCP server directly, with no AI model involved.

    python try_server.py                  what the server offers
    python try_server.py local "stack pressure"
    python try_server.py online "lithium dendrite interlayer"
    python try_server.py calc "412/487*100"
    python try_server.py lay paper5

This does what every AI app does when it connects: start the server, discover what it offers,
then call a tool. If this works and your AI app does not, the problem is in the app's settings.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

SERVER = Path(__file__).resolve().parent / "server.py"

SAMPLE_DRAFT = (
    "Lithium batteries can fail when needle-like metal growths form inside them. Researchers "
    "tested 20 battery cells to see what stops these growths. Squeezing the cells firmly helped "
    "most, and made them last about 2.4 times longer. A protective layer added little under the "
    "same pressure. The catch is that the study used only liquid-filled cells, and this much "
    "pressure is not practical for every battery shape."
)


async def show(client: Client, tool: str, arguments: dict) -> None:
    print(f"\nCALL {tool}({arguments})\n")
    result = await client.call_tool(tool, arguments)
    print("\n".join(block.text for block in result.content if block.type == "text"))


async def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "discover"
    argument = sys.argv[2] if len(sys.argv) > 2 else ""

    async with Client(StdioServerParameters(command=sys.executable, args=[str(SERVER)])) as client:
        if command == "discover":
            print("Connected to research-mcp.\n\nTOOLS: the AI model decides when to call these")
            for tool in (await client.list_tools()).tools:
                print(f"  - {tool.name}: {(tool.description or '').splitlines()[0]}")
            print("\nRESOURCES: the app decides when to read these")
            for resource in (await client.list_resources()).resources:
                print(f"  - {resource.uri}")
            print("\nPROMPTS: you pick these from a menu")
            for prompt in (await client.list_prompts()).prompts:
                print(f"  - {prompt.name}: {prompt.description}")
            await show(client, "list_papers", {})
            await show(client, "list_skills", {})
        elif command == "local":
            await show(client, "search_papers", {"query": argument or "stack pressure", "top_k": 3})
        elif command == "online":
            await show(client, "search_online", {"query": argument or "lithium dendrite interlayer", "limit": 4})
        elif command == "review":
            await show(client, "review_online_literature",
                       {"question": argument or "Do interlayers suppress lithium dendrites at high stack pressure?"})
        elif command == "calc":
            await show(client, "calculate", {"expression": argument or "412/487*100"})
        elif command == "lay":
            await show(client, "review_lay_abstract", {"draft": SAMPLE_DRAFT, "document": argument or "paper5"})
        else:
            sys.exit(__doc__)


if __name__ == "__main__":
    asyncio.run(main())
