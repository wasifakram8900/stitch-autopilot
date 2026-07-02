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
import qa

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


# Stitch returns HTML immediately but PARTIAL, then keeps building — we must poll past that.
# "Complete" = the build would clear the real static HARD gates (structure + all booking JS +
# clean images). Reusing qa.py as the one source of truth means we poll until it's deploy-ready,
# not until 4 arbitrary markers appear (the 1st live run returned partial builds on 4-marker check).
POLL_EVERY = int(os.environ.get("STITCH_POLL_EVERY", "25"))
POLL_TRIES = int(os.environ.get("STITCH_POLL_TRIES", "16"))   # ~6.7 min max (was 12 / 5 min)


def _complete(html):
    if not html:
        return False
    return qa.structure(html)["ok"] and qa.booking(html)["ok"] and qa.images(html)["ok"]


async def _fetch_screen_html(s, pid, sid, key):
    g = await s.call_tool("get_screen", {"projectId": pid, "screenId": sid,
                                         "name": f"projects/{pid}/screens/{sid}"})
    dl = ((g.structuredContent or {}).get("htmlCode") or {}).get("downloadUrl")
    if not dl:
        return None
    return requests.get(dl, headers={"X-Goog-Api-Key": key}, timeout=120).text


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
            model = os.environ.get("STITCH_MODEL", "GEMINI_3_1_PRO")   # PRO = the good model the UI uses
            if model:
                args["modelId"] = model

            res = await s.call_tool("generate_screen_from_text", args, read_timeout_seconds=timedelta(seconds=900))
            if res.isError:
                txt = " ".join(getattr(b, "text", "") or "" for b in res.content)
                # if the modelId enum name is off, retry once on the default model rather than hard-fail
                if "modelId" in args and re.search(r"model|invalid argument|unknown", txt, re.I):
                    print(f"     modelId '{model}' rejected ({txt[:80]}); retrying on default model", flush=True)
                    args.pop("modelId")
                    res = await s.call_tool("generate_screen_from_text", args, read_timeout_seconds=timedelta(seconds=900))
                if res.isError:
                    txt = " ".join(getattr(b, "text", "") or "" for b in res.content)
                    raise RuntimeError(f"generate failed: {txt[:300]}")

            screen = _design_screen(res.structuredContent)
            sid = (screen or {}).get("id")
            if not sid:
                ids = re.findall(r"screens/([0-9a-f]+)", json.dumps(res.structuredContent, default=str))
                sid = ids[-1] if ids else None
            if not sid:
                raise RuntimeError(f"generate produced no screen id: {json.dumps(res.structuredContent, default=str)[:300]}")

            # Poll get_screen until booking JS is fully present AND byte count stops growing
            # (Stitch's agent keeps building after the first partial HTML). Keep the largest html
            # seen as fallback; return early once complete + settled across 2 polls.
            best, best_len, prev_len, stable = None, 0, -1, 0
            for _try in range(POLL_TRIES):
                try:
                    html = await _fetch_screen_html(s, pid, sid, key)
                except Exception:
                    html = None
                if html and len(html) >= best_len:
                    best, best_len = html, len(html)
                if _complete(html):
                    if abs(len(html) - prev_len) < 200:        # size settled
                        stable += 1
                        if stable >= 2:
                            break
                    else:
                        stable = 0
                    prev_len = len(html)
                if _try < POLL_TRIES - 1:
                    await asyncio.sleep(POLL_EVERY)

            if not best:
                raise RuntimeError("no HTML produced after polling get_screen")
            return {"projectId": pid, "screenId": sid, "html": best,
                    "screenshot": (screen.get("screenshot") or {}).get("downloadUrl") if screen else None,
                    "complete": _complete(best)}


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
