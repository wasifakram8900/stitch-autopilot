"""Send the FULL master prompt (booking spec + design system + filled data) to Stitch's agent.
This is what the user actually does in the Stitch UI. Proves the API triggers the same agent build."""
import asyncio, os, json, re, time
from datetime import timedelta
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
KEY = open(os.path.join(HERE, ".stitch_key")).read().strip()
URL = "https://stitch.googleapis.com/mcp"
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)

PROMPT = open(os.path.join(HERE, "full_prompt.txt")).read()

def d(o):
    try: return json.loads(o.model_dump_json())
    except Exception: return str(o)

async def main():
    async with streamablehttp_client(URL, headers={"X-Goog-Api-Key": KEY},
            timeout=timedelta(seconds=60), sse_read_timeout=timedelta(seconds=900)) as (r,w,_):
        async with ClientSession(r,w) as s:
            await s.initialize()
            cp = await s.call_tool("create_project", {"title":"BeautySpot FULL"})
            pid = re.findall(r"projects/(\d+)", json.dumps([d(c) for c in cp.content]+[cp.structuredContent], default=str))[0]
            print("projectId =", pid, "| prompt chars =", len(PROMPT), flush=True)
            t=time.time()
            gen = await s.call_tool("generate_screen_from_text",
                  {"projectId":pid, "prompt":PROMPT, "deviceType":"DESKTOP"}, read_timeout_seconds=timedelta(seconds=900))
            print(f"generate {time.time()-t:.0f}s isError={gen.isError}", flush=True)
            gj = {"structured":gen.structuredContent}
            if gen.isError:
                print("ERR:", " ".join(getattr(b,'text','') or '' for b in gen.content)); return
            dl=None
            for c in (gj["structured"].get("outputComponents") or []):
                for sc in (c.get("design") or {}).get("screens", []):
                    if sc.get("screenType")=="DESIGN" and (sc.get("htmlCode") or {}).get("downloadUrl"):
                        dl=sc["htmlCode"]["downloadUrl"]
            print("htmlCode url:", "yes" if dl else "NO", flush=True)
            gj=None  # free memory before download
            if dl:
                p=f"{OUT}/beautyspot_full/index.html"; os.makedirs(os.path.dirname(p),exist_ok=True)
                with requests.get(dl, headers={"X-Goog-Api-Key":KEY}, timeout=180, stream=True) as resp:
                    with open(p,"wb") as f:
                        for chunk in resp.iter_content(8192):
                            f.write(chunk)
                print(f"SAVED {os.path.getsize(p)} bytes -> {p}")

asyncio.run(main())
