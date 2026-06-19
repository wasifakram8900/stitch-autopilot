"""Find the valid arg shape for generate_screen_from_text. Stops on first success, then fetches the screen."""
import asyncio, os, json, time, re
from datetime import timedelta
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

HERE = os.path.dirname(os.path.abspath(__file__))
KEY = open(os.path.join(HERE, ".stitch_key")).read().strip()
URL = "https://stitch.googleapis.com/mcp"
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
PROMPT = ("Modern landing page for 'Bright Smile Dental', a dental clinic in Austin TX. "
          "Hero with 'Book Appointment' CTA, services grid, testimonials, contact form. Teal and white.")

def dump(o):
    try: return json.loads(o.model_dump_json())
    except Exception: return str(o)

async def main():
    async with streamablehttp_client(URL, headers={"X-Goog-Api-Key": KEY},
            timeout=timedelta(seconds=60), sse_read_timeout=timedelta(seconds=900)) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            # fresh project
            cp = await s.call_tool("create_project", {"title": "Retry Test"})
            pid = re.findall(r"projects/(\d+)", json.dumps(dump(cp[0]) if False else [dump(c) for c in cp.content], default=str) + json.dumps(cp.structuredContent, default=str))
            pid = pid[0] if pid else None
            print("projectId =", pid)

            combos = [
                {"projectId": pid, "prompt": PROMPT},
                {"projectId": pid, "prompt": PROMPT, "deviceType": "DESKTOP"},
                {"projectId": pid, "prompt": PROMPT, "deviceType": "WEB"},
                {"projectId": pid, "prompt": PROMPT, "deviceType": "mobile"},
                {"projectId": pid, "prompt": PROMPT, "deviceType": "MOBILE"},
            ]
            ok = None
            for i, c in enumerate(combos):
                key = {k: v for k, v in c.items() if k != "prompt"}
                print(f"\n[{i}] try args={key} ...", flush=True)
                t = time.time()
                try:
                    res = await s.call_tool("generate_screen_from_text", c, read_timeout_seconds=timedelta(seconds=900))
                except Exception as e:
                    print(f"    EXC {time.time()-t:.0f}s: {e}"); continue
                txt = " ".join(getattr(b, "text", "") or "" for b in res.content)
                print(f"    {time.time()-t:.0f}s isError={res.isError} :: {txt[:120]}")
                if not res.isError:
                    ok = (c, res); break

            if not ok:
                print("\nAll combos failed. deviceType not the issue — schema mismatch elsewhere."); return

            c, res = ok
            data = {"content": [dump(b) for b in res.content], "structured": res.structuredContent}
            json.dump(data, open(os.path.join(OUT, "gen_ok.json"), "w"), indent=2, default=str)
            print("\nSUCCESS shape:", {k: v for k, v in c.items() if k != "prompt"})
            sids = re.findall(r'"screenId"\s*:\s*"([0-9a-f]+)"', json.dumps(data, default=str)) + re.findall(r"screens/([0-9a-f]+)", json.dumps(data, default=str))
            sids = list(dict.fromkeys(sids))
            print("screenIds =", sids)
            for sid in sids[:1]:
                g = await s.call_tool("get_screen", {"projectId": pid, "screenId": sid, "name": f"projects/{pid}/screens/{sid}"})
                gd = {"content": [dump(b) for b in g.content], "structured": g.structuredContent}
                json.dump(gd, open(os.path.join(OUT, "get_screen_ok.json"), "w"), indent=2, default=str)
                print("get_screen saved -> out/get_screen_ok.json")

asyncio.run(main())
