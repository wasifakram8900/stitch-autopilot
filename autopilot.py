"""
Autopilot loop: poll Google Sheet for Pending rows -> Stitch single-page site
-> deploy to Netlify -> write live URL + Done back to the sheet. Respects a daily cap.

Run continuously:   ./venv/bin/python autopilot.py
One pass + exit:    ./venv/bin/python autopilot.py --once
"""
import os, sys, json, time, datetime, traceback
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

import stitch_client
import netlify_deploy
import sheets_client

HERE = os.path.dirname(os.path.abspath(__file__))

SHEET_ID = os.environ.get("SHEET_ID")
DAILY_CAP = int(os.environ.get("DAILY_CAP", "44"))
PER_RUN_CAP = int(os.environ.get("PER_RUN_CAP", "0"))   # 0 = no per-pass limit
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "180"))
DEVICE = os.environ.get("DEVICE", "DESKTOP")

PROMPT_TMPL = """Create a polished, modern, SINGLE-PAGE landing website for this business. \
Everything on ONE long scrolling page (no separate pages).

BUSINESS
- Name: {name}
- Industry: {industry}
- Location: {location}
- Services: {services}
- Target audience: {audience}

BRANDING
- Brand colors: {colors}
- Design style: {design_style}
- Phone: {phone}
- Email: {email}

SPECIAL REQUIREMENTS: {requirements}

SECTIONS (in order): sticky nav with a primary CTA button; hero with headline, subtext and CTA; \
services/offerings grid; about/story; testimonials or social proof; a contact section showing \
phone {phone} and email {email}; footer. Fully responsive. Use the brand colors throughout."""


def build_prompt(rec):
    def g(k):
        v = (rec.get(k) or "").strip()
        return v if v else "(not specified)"
    return PROMPT_TMPL.format(
        name=g("name"), industry=g("industry"), location=g("location"),
        services=g("services"), audience=g("audience"), colors=g("colors"),
        design_style=g("design_style"), phone=g("phone"), email=g("email"),
        requirements=g("requirements"))


def process_row(rec):
    print(f"  -> generating site for '{rec['name']}' ({rec['industry']}) ...", flush=True)
    out = stitch_client.generate_site_html(build_prompt(rec), device=DEVICE, title=rec["name"][:60] or "Site")
    print(f"     html {len(out['html'])} bytes, deploying to Netlify ...", flush=True)
    url, sid = netlify_deploy.deploy_html(out["html"])
    print(f"     LIVE: {url}", flush=True)
    return url


def one_pass():
    if not SHEET_ID:
        raise SystemExit("SHEET_ID not set (.env)")
    today = datetime.date.today().isoformat()
    done_today = sheets_client.done_today_count(SHEET_ID)
    remaining = DAILY_CAP - done_today
    if remaining <= 0:
        print(f"daily cap {DAILY_CAP} reached ({done_today} done today). idle until reset.")
        return
    budget = remaining if PER_RUN_CAP <= 0 else min(remaining, PER_RUN_CAP)
    rows = sheets_client.read_pending(SHEET_ID)
    print(f"{datetime.datetime.now():%H:%M:%S}  {len(rows)} pending | {done_today}/{DAILY_CAP} today | budget this pass {budget}")
    made = 0
    for rec in rows:
        if made >= budget:
            print(f"pass budget {budget} reached, stopping.")
            break
        try:
            url = process_row(rec)
            sheets_client.mark(SHEET_ID, rec["row"], "Done", url, done_at=today)
            made += 1
        except Exception as e:
            print(f"  !! row {rec['row']} ERROR: {e}")
            traceback.print_exc()
            try:
                sheets_client.mark(SHEET_ID, rec["row"], f"Error: {str(e)[:120]}")
            except Exception:
                pass
    print(f"pass done: made {made}, total today {done_today + made}/{DAILY_CAP}")


def main():
    once = "--once" in sys.argv
    if once:
        one_pass()
        return
    print(f"autopilot loop: poll every {POLL_SECONDS}s, cap {DAILY_CAP}/day, device {DEVICE}")
    while True:
        try:
            one_pass()
        except Exception as e:
            print("loop error:", e)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
