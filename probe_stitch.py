"""
Probe the Google Stitch MCP server: list every tool + input schema.
Reads API key from local file .stitch_key (gitignored, never printed).
Run: ./venv/bin/python probe_stitch.py
"""
import asyncio, sys, os, json
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

HERE = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(HERE, ".stitch_key")
URL = "https://stitch.googleapis.com/mcp"


async def main():
    if not os.path.exists(KEY_FILE):
        print(f"ERROR: create {KEY_FILE} with your Stitch API key on one line.")
        sys.exit(1)
    key = open(KEY_FILE).read().strip()
    if not key:
        print("ERROR: .stitch_key is empty.")
        sys.exit(1)

    headers = {"X-Goog-Api-Key": key}
    print(f"Connecting {URL} ...")
    async with streamablehttp_client(URL, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            print(f"Connected. Server: {init.serverInfo.name} v{init.serverInfo.version}\n")

            tools = await session.list_tools()
            print(f"=== {len(tools.tools)} TOOLS ===\n")
            for t in tools.tools:
                print(f"## {t.name}")
                if t.description:
                    print(f"   {t.description.strip()[:300]}")
                schema = t.inputSchema or {}
                props = schema.get("properties", {})
                required = set(schema.get("required", []))
                for pname, pinfo in props.items():
                    star = "*" if pname in required else ""
                    desc = (pinfo.get("description", "") or "")[:90]
                    print(f"     - {pname}{star}: {pinfo.get('type','?')}  {desc}")
                print()

            # also list resources/prompts if any
            try:
                res = await session.list_resources()
                if res.resources:
                    print("=== RESOURCES ===")
                    for r in res.resources:
                        print(f"  - {r.uri}  {r.name}")
            except Exception:
                pass


if __name__ == "__main__":
    asyncio.run(main())
