"""Re-fetch the DESIGN screen HTML from an existing project (no regeneration). Memory-safe streamed download."""
import asyncio, os, sys, json, re
from datetime import timedelta
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
KEY = open(os.path.join(HERE, ".stitch_key")).read().strip()
URL = "https://stitch.googleapis.com/mcp"
PID = sys.argv[1] if len(sys.argv) > 1 else "6286624402441348603"
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else "out/beautyspot_full"

async def main():
    async with streamablehttp_client(URL, headers={"X-Goog-Api-Key": KEY},
            timeout=timedelta(seconds=60), sse_read_timeout=timedelta(seconds=300)) as (r,w,_):
        async with ClientSession(r,w) as s:
            await s.initialize()
            ls = await s.call_tool("list_screens", {"projectId": PID})
            sc = ls.structuredContent or {}
            screens = sc.get("screens") or []
            # find DESIGN screen id
            target = None
            for x in screens:
                if x.get("screenType") == "DESIGN":
                    target = x
            if not target:
                # fall back: any with htmlCode
                for x in screens:
                    if (x.get("htmlCode") or {}).get("downloadUrl"):
                        target = x
            if not target:
                print("no DESIGN screen. types:", [x.get("screenType") for x in screens]); return
            sid = target.get("id") or target.get("name","").split("/")[-1]
            g = await s.call_tool("get_screen", {"projectId": PID, "screenId": sid,
                                                 "name": f"projects/{PID}/screens/{sid}"})
            dl = ((g.structuredContent or {}).get("htmlCode") or {}).get("downloadUrl")
            print("screenId", sid, "| dl", "yes" if dl else "NO")
            if not dl: return
            os.makedirs(os.path.join(HERE, OUTDIR), exist_ok=True)
            p = os.path.join(HERE, OUTDIR, "index.html")
            with requests.get(dl, headers={"X-Goog-Api-Key": KEY}, timeout=180, stream=True) as resp:
                with open(p, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)
            print(f"SAVED {os.path.getsize(p)} bytes -> {p}")

asyncio.run(main())
