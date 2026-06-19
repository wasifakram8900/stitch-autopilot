"""Full Stitch path WITH a DESIGN.md design system applied. Proves the chosen Stitch engine."""
import asyncio, os, json, re, base64, time
from datetime import timedelta
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
KEY = open(os.path.join(HERE, ".stitch_key")).read().strip()
URL = "https://stitch.googleapis.com/mcp"
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
DESIGN_MD = "/Users/wasifali/Downloads/awesome-design-md-main/design-md/apple/DESIGN.md"

PROMPT = ("Single-page website for The Beauty Spot, a calming day spa in Oro Valley, Arizona. "
          "Sticky nav with a 'Book Now' button. Hero: 5.0 star rating badge, headline, 'Book Appointment' CTA. "
          "Services grid: Signature Facial $95, Deep Tissue Massage $110, Hot Stone Massage $130, "
          "Express Glow Facial $60, Weeknight Yoga $20. About section. "
          "Three 5-star reviews from Taylor U., Elle, and Maha S. "
          "Contact section: phone +1 520-595-8565, address 10420 N La Canada Dr #120 Oro Valley AZ 85737, a Google map. "
          "FAQ. Calm, premium, minimal, lots of whitespace.")

def d(o):
    try: return json.loads(o.model_dump_json())
    except Exception: return str(o)

def jdump(res):
    return {"content":[d(c) for c in res.content], "structured":res.structuredContent}

def find(blob, pat):
    return re.findall(pat, json.dumps(blob, default=str))

async def main():
    async with streamablehttp_client(URL, headers={"X-Goog-Api-Key": KEY},
            timeout=timedelta(seconds=60), sse_read_timeout=timedelta(seconds=900)) as (r,w,_):
        async with ClientSession(r,w) as s:
            await s.initialize()

            cp = jdump(await s.call_tool("create_project", {"title":"BeautySpot DesignMD"}))
            pid = find(cp, r"projects/(\d+)")[0]
            print("projectId =", pid, flush=True)

            md_b64 = base64.b64encode(open(DESIGN_MD,"rb").read()).decode()
            up = jdump(await s.call_tool("upload_design_md", {"projectId":pid, "designMdBase64":md_b64}))
            json.dump(up, open(f"{OUT}/ds_upload.json","w"), indent=1, default=str)
            # screen instance: need id + sourceScreen
            inst_id = (find(up, r'"id"\s*:\s*"([0-9a-f]{8,})"') or [None])[0]
            src = (find(up, r'(projects/\d+/screens/[0-9a-f]+)') or [None])[0]
            print("instance id =", inst_id, "| source =", src, flush=True)

            ds_asset = None
            if inst_id and src:
                cds = jdump(await s.call_tool("create_design_system_from_design_md",
                      {"projectId":pid, "selectedScreenInstance":{"id":inst_id, "sourceScreen":src}}))
                json.dump(cds, open(f"{OUT}/ds_create.json","w"), indent=1, default=str)
                ds_asset = (find(cds, r'(assets/\d+)') or [None])[0]
            print("designSystem asset =", ds_asset, flush=True)

            args = {"projectId":pid, "prompt":PROMPT, "deviceType":"DESKTOP"}
            if ds_asset: args["designSystem"] = ds_asset
            t=time.time()
            gen = await s.call_tool("generate_screen_from_text", args, read_timeout_seconds=timedelta(seconds=900))
            print(f"generate {time.time()-t:.0f}s isError={gen.isError}", flush=True)
            gj = jdump(gen)
            json.dump(gj, open(f"{OUT}/ds_gen.json","w"), indent=1, default=str)
            if gen.isError:
                print("ERR:", " ".join(getattr(b,'text','') or '' for b in gen.content)); return

            # find DESIGN screen htmlCode downloadUrl
            screens = (gj["structured"].get("outputComponents") or [])
            dl=None
            for c in screens:
                for sc in (c.get("design") or {}).get("screens", []):
                    if sc.get("screenType")=="DESIGN" and (sc.get("htmlCode") or {}).get("downloadUrl"):
                        dl=sc["htmlCode"]["downloadUrl"]
            print("htmlCode url:", "yes" if dl else "NO", flush=True)
            if dl:
                html = requests.get(dl, headers={"X-Goog-Api-Key":KEY}, timeout=120).text
                p=f"{OUT}/beautyspot_stitch/index.html"; os.makedirs(os.path.dirname(p),exist_ok=True)
                open(p,"w").write(html)
                print(f"SAVED {len(html)} bytes -> {p}")

asyncio.run(main())
