"""
Stitch client — prompt in, deployable HTML out. Proven flow:
  create_project -> generate_screen_from_text -> pick DESIGN screen -> download htmlCode.
Self-contained Tailwind HTML (images inlined base64).
"""
import asyncio, os, json, re, time
from datetime import timedelta
import requests
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "https://stitch.googleapis.com/mcp"


def _key():
    f = os.path.join(HERE, ".stitch_key")
    if os.path.exists(f):
        return open(f).read().strip()
    k = os.environ.get("STITCH_API_KEY")
    if not k:
        raise RuntimeError("No Stitch key: create .stitch_key or set STITCH_API_KEY")
    return k


def _dump(o):
    try:
        return json.loads(o.model_dump_json())
    except Exception:
        return str(o)


def _design_screen(structured):
    """Return the DESIGN screen dict (the real UI) from a generate result."""
    if not structured:
        return None
    for comp in structured.get("outputComponents", []):
        d = comp.get("design")
        if not d:
            continue
        designs = [s for s in d.get("screens", []) if s.get("screenType") == "DESIGN"]
        if designs:
            return designs[-1]  # last = most complete
    return None


async def _generate(prompt, device, title):
    key = _key()
    async with streamablehttp_client(
        URL, headers={"X-Goog-Api-Key": key},
        timeout=timedelta(seconds=60), sse_read_timeout=timedelta(seconds=900)
    ) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()

            cp = await s.call_tool("create_project", {"title": title})
            blob = json.dumps([_dump(c) for c in cp.content], default=str) + json.dumps(cp.structuredContent, default=str)
            pids = re.findall(r"projects/(\d+)", blob)
            pid = pids[0] if pids else None
            if not pid:
                raise RuntimeError(f"create_project gave no projectId: {blob[:300]}")

            args = {"projectId": pid, "prompt": prompt}
            if device:                       # UPPERCASE only: "DESKTOP" / "MOBILE"
                args["deviceType"] = device.upper()

            res = await s.call_tool("generate_screen_from_text", args, read_timeout_seconds=timedelta(seconds=900))
            if res.isError:
                txt = " ".join(getattr(b, "text", "") or "" for b in res.content)
                raise RuntimeError(f"generate failed: {txt[:300]}")

            screen = _design_screen(res.structuredContent)

            # fallback: poll get_screen if html not ready inline
            if not (screen and (screen.get("htmlCode") or {}).get("downloadUrl")):
                _, sids = pid, re.findall(r"screens/([0-9a-f]+)", json.dumps(res.structuredContent, default=str))
                for _try in range(10):
                    await asyncio.sleep(30)
                    ld = await s.call_tool("list_screens", {"projectId": pid})
                    sc = _design_screen(ld.structuredContent)
                    if sc and (sc.get("htmlCode") or {}).get("downloadUrl"):
                        screen = sc
                        break

            if not screen:
                raise RuntimeError("no DESIGN screen produced")
            dl = (screen.get("htmlCode") or {}).get("downloadUrl")
            if not dl:
                raise RuntimeError("DESIGN screen has no htmlCode downloadUrl")

            html = requests.get(dl, headers={"X-Goog-Api-Key": key}, timeout=120).text
            return {"projectId": pid, "screenId": screen.get("id"), "html": html,
                    "screenshot": (screen.get("screenshot") or {}).get("downloadUrl")}


def generate_site_html(prompt, device="DESKTOP", title="Site"):
    """Sync entrypoint. Returns dict with 'html' (deployable index.html string)."""
    return asyncio.run(_generate(prompt, device, title))


if __name__ == "__main__":
    out = generate_site_html(
        "Modern single-page landing site for 'Acme Coffee Roasters', a specialty coffee shop "
        "in Portland OR. Sections: hero with 'Order Now' CTA, our beans, story, hours/location, "
        "contact. Warm earthy browns and cream. Phone (503) 555-0142.",
        device="DESKTOP", title="Acme Coffee Test")
    p = os.path.join(HERE, "out", "cli_site.html")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(out["html"])
    print(f"OK project={out['projectId']} screen={out['screenId']} bytes={len(out['html'])} -> {p}")
