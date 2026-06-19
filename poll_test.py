"""Test: does polling get_screen after generate eventually return the FULL site (calendar+data+no AI img)?"""
import asyncio, os, json, re, time
from datetime import timedelta
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
KEY = open(os.path.join(HERE, ".stitch_key")).read().strip()
URL = "https://stitch.googleapis.com/mcp"
PROMPT = open(os.path.join(HERE, "full_prompt.txt")).read()

def d(o):
    try: return json.loads(o.model_dump_json())
    except Exception: return str(o)

def design_screen_id(struct):
    for c in (struct or {}).get("outputComponents", []):
        for sc in (c.get("design") or {}).get("screens", []):
            if sc.get("screenType") == "DESIGN":
                return sc.get("id")
    return None

def grade(html):
    g = lambda p: len(re.findall(p, html))
    return (f"bytes={len(html)} calendar={g('renderCalendar')} prevMonth={g('prevMonth')} "
            f"toggleService={g('toggleService')} reviews={g('Taylor|Maha|Elle')} "
            f"services={g('Signature Facial|Hot Stone')} map={g('maps.google|<iframe')} "
            f"AIimg={g('googleusercontent.com/aida')}")

async def fetch(session, pid, sid):
    g = await session.call_tool("get_screen", {"projectId": pid, "screenId": sid,
                                               "name": f"projects/{pid}/screens/{sid}"})
    dl = ((g.structuredContent or {}).get("htmlCode") or {}).get("downloadUrl")
    if not dl: return None
    return requests.get(dl, headers={"X-Goog-Api-Key": KEY}, timeout=120).text

async def main():
    async with streamablehttp_client(URL, headers={"X-Goog-Api-Key": KEY},
            timeout=timedelta(seconds=60), sse_read_timeout=timedelta(seconds=900)) as (r,w,_):
        async with ClientSession(r,w) as s:
            await s.initialize()
            cp = await s.call_tool("create_project", {"title":"Poll Test"})
            pid = re.findall(r"projects/(\d+)", json.dumps([d(c) for c in cp.content]+[cp.structuredContent], default=str))[0]
            print("projectId", pid, flush=True)
            t=time.time()
            gen = await s.call_tool("generate_screen_from_text",
                  {"projectId":pid, "prompt":PROMPT, "deviceType":"DESKTOP"}, read_timeout_seconds=timedelta(seconds=900))
            sid = design_screen_id(gen.structuredContent)
            print(f"generate {time.time()-t:.0f}s isError={gen.isError} screenId={sid}", flush=True)
            if not sid: print("no screen id"); return
            # immediate
            html = await fetch(s, pid, sid)
            if html: print("t=0   ", grade(html), flush=True)
            # poll
            for i in range(8):
                await asyncio.sleep(25)
                try:
                    html = await fetch(s, pid, sid)
                    if html: print(f"t={25*(i+1):<4}", grade(html), flush=True)
                except Exception as e:
                    print(f"t={25*(i+1)} err {e}", flush=True)
            if html:
                p=f"{HERE}/out/poll_final/index.html"; os.makedirs(os.path.dirname(p),exist_ok=True)
                open(p,"w").write(html); print("saved final ->", p)

asyncio.run(main())
