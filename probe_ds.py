"""Dump full inputSchema for the design-system + generate tools."""
import asyncio, os, json
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
KEY=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),".stitch_key")).read().strip()
WANT={"upload_design_md","create_design_system_from_design_md","create_design_system","generate_screen_from_text","apply_design_system","list_design_systems"}
async def main():
    async with streamablehttp_client("https://stitch.googleapis.com/mcp",headers={"X-Goog-Api-Key":KEY}) as (r,w,_):
        async with ClientSession(r,w) as s:
            await s.initialize()
            for t in (await s.list_tools()).tools:
                if t.name in WANT:
                    print("\n#####",t.name,"#####")
                    print(json.dumps(t.inputSchema,indent=1,default=str))
asyncio.run(main())
