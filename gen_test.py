"""
END-TO-END validation: create project -> generate 1 screen -> fetch it -> inspect.
Answers: does Stitch return usable CODE (html/react) or just image+tokens?
Dumps raw JSON to out/ and prints a verdict.
Run: ./venv/bin/python gen_test.py
"""
import asyncio, os, json, time, re
from datetime import timedelta
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

HERE = os.path.dirname(os.path.abspath(__file__))
KEY = open(os.path.join(HERE, ".stitch_key")).read().strip()
URL = "https://stitch.googleapis.com/mcp"
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

PROMPT = (
    "Landing page (home) for 'Bright Smile Dental', a modern dental clinic in Austin, TX. "
    "Services: cleanings, whitening, Invisalign, emergency care. "
    "Brand colors teal and white, friendly professional. "
    "Sections: hero with CTA 'Book Appointment', services grid, about, testimonials, "
    "contact with phone (512) 555-0199. Responsive, include a contact form."
)


def dump(obj):
    try:
        return json.loads(obj.model_dump_json())
    except Exception:
        try:
            return obj.__dict__
        except Exception:
            return str(obj)


def find_ids(blob):
    """Recursively pull anything that looks like a project/screen id."""
    s = json.dumps(blob, default=str)
    projects = re.findall(r"projects/(\d+)", s)
    proj_id = projects[0] if projects else None
    screens = re.findall(r'"screenId"\s*:\s*"([0-9a-f]+)"', s) + re.findall(r"screens/([0-9a-f]+)", s)
    return proj_id, list(dict.fromkeys(screens))


async def call(session, name, args, label):
    print(f"\n>>> {name}({list(args)}) ...", flush=True)
    t = time.time()
    res = await session.call_tool(name, args, read_timeout_seconds=timedelta(seconds=900))
    print(f"    done {time.time()-t:.0f}s  isError={res.isError}", flush=True)
    data = {"content": [dump(c) for c in res.content], "structured": res.structuredContent}
    with open(os.path.join(OUT, f"{label}.json"), "w") as f:
        json.dump(data, f, indent=2, default=str)
    return data


async def main():
    async with streamablehttp_client(
        URL, headers={"X-Goog-Api-Key": KEY},
        timeout=timedelta(seconds=60), sse_read_timeout=timedelta(seconds=900)
    ) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()

            d = await call(s, "create_project", {"title": "Validation Test Dental"}, "01_create_project")
            proj_id, _ = find_ids(d)
            print("   projectId =", proj_id)
            if not proj_id:
                print("   !! could not parse projectId. dump:"); print(json.dumps(d, indent=2)[:2000]); return

            d = await call(s, "generate_screen_from_text",
                           {"projectId": proj_id, "prompt": PROMPT, "deviceType": "desktop"},
                           "02_generate_screen")
            _, screens = find_ids(d)
            print("   screenIds from gen =", screens)

            ld = await call(s, "list_screens", {"projectId": proj_id}, "03_list_screens")
            _, screens2 = find_ids(ld)
            screens = list(dict.fromkeys(screens + screens2))
            print("   all screenIds =", screens)

            for sid in screens[:1]:
                gd = await call(s, "get_screen",
                                {"projectId": proj_id, "screenId": sid,
                                 "name": f"projects/{proj_id}/screens/{sid}"},
                                f"04_get_screen_{sid}")

            # ---- verdict ----
            blob = json.dumps(d, default=str) + json.dumps(ld, default=str)
            try:
                blob += open(os.path.join(OUT, f"04_get_screen_{screens[0]}.json")).read()
            except Exception:
                pass
            print("\n===== VERDICT =====")
            markers = {
                "HTML code": bool(re.search(r"<html|<!doctype|<div|<section", blob, re.I)),
                "React/JSX/TSX": bool(re.search(r"className=|import React|export default|\.tsx", blob)),
                "CSS": bool(re.search(r"\{[^}]*:[^}]*;[^}]*\}|tailwind|className", blob)),
                "image URL": bool(re.search(r"https?://[^\"]+\.(png|jpg|jpeg|webp)", blob, re.I)),
                "figma": bool(re.search(r"figma", blob, re.I)),
                "design tokens": bool(re.search(r"colorPalette|typography|designSystem|fontFamily", blob)),
            }
            for k, v in markers.items():
                print(f"  {'YES' if v else ' no'}  {k}")
            print(f"\n  raw dumps saved in {OUT}/  (open 04_get_screen_*.json to see real output)")


if __name__ == "__main__":
    asyncio.run(main())
