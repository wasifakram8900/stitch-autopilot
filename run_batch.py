"""
Sheets-free batch runner — proves the FULL workflow end to end, no LLM in the loop.

3 fake businesses, processed as a SEQUENTIAL TRIGGER CHAIN:
  TRIGGER 1 -> Stitch generate -> Netlify deploy -> site LIVE
     (only then) TRIGGER 2 -> ... -> site LIVE
        (only then) TRIGGER 3 -> ... -> site LIVE

Each next business starts ONLY after the previous one's website is live.
Run:  ./venv/bin/python run_batch.py
Live URLs printed at the end and saved to out/batch_results.json.
"""
import os, json, time, datetime, traceback
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(HERE, ".env"))

import stitch_client
import netlify_deploy

DEVICE = os.environ.get("DEVICE", "DESKTOP")

# ---- 3 fake businesses (the test list; replaces the Google Sheet for now) ----
BUSINESSES = [
    {
        "name": "Brewhaus Coffee Co.",
        "industry": "Specialty coffee shop",
        "location": "Portland, OR",
        "services": "Single-origin pour-overs, espresso, house-roasted beans, pastries, catering",
        "audience": "Local coffee lovers, remote workers, weekend brunch crowd",
        "colors": "warm earthy browns, cream, deep forest green",
        "design_style": "cozy, artisanal, modern minimalist",
        "phone": "(503) 555-0142",
        "email": "hello@brewhauscoffee.com",
        "requirements": "Show roast-of-the-week, an 'Order Online' CTA, and store hours.",
    },
    {
        "name": "IronPeak Fitness",
        "industry": "Strength & conditioning gym",
        "location": "Austin, TX",
        "services": "Personal training, small-group strength classes, mobility coaching, nutrition plans",
        "audience": "Busy professionals 25-45 who want results without guesswork",
        "colors": "charcoal black, electric orange, steel gray",
        "design_style": "bold, energetic, high-contrast sporty",
        "phone": "(512) 555-0188",
        "email": "train@ironpeakfitness.com",
        "requirements": "Big 'Book a Free Session' CTA, class schedule grid, trainer bios.",
    },
    {
        "name": "BrightSmile Dental",
        "industry": "Family & cosmetic dental clinic",
        "location": "Miami, FL",
        "services": "Cleanings, whitening, Invisalign, implants, emergency care",
        "audience": "Families and professionals wanting a gentle, modern dental experience",
        "colors": "clean white, calming teal, soft sky blue",
        "design_style": "clean, trustworthy, friendly medical",
        "phone": "(305) 555-0173",
        "email": "smile@brightsmiledental.com",
        "requirements": "Prominent 'Book Appointment' CTA, services with pricing hints, insurance note.",
    },
]

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


def build_prompt(b):
    return PROMPT_TMPL.format(**b)


def slug(name):
    s = "".join(c.lower() if c.isalnum() else "-" for c in name).strip("-")
    while "--" in s:
        s = s.replace("--", "-")
    return s


GEN_RETRIES = int(os.environ.get("GEN_RETRIES", "3"))


def generate_with_retry(prompt, title):
    """Stitch occasionally throttles back-to-back calls (transient auth/quota blip). Retry w/ backoff."""
    last = None
    for attempt in range(1, GEN_RETRIES + 1):
        try:
            return stitch_client.generate_site_html(prompt, device=DEVICE, title=title)
        except Exception as e:
            last = e
            if attempt < GEN_RETRIES:
                wait = 20 * attempt
                print(f"     gen attempt {attempt} failed ({str(e)[:80]}); retry in {wait}s", flush=True)
                time.sleep(wait)
    raise last


def process(idx, total, b):
    t0 = time.time()
    print(f"\n{'='*64}\nTRIGGER {idx}/{total}  ->  {b['name']}  ({b['industry']})\n{'='*64}", flush=True)

    print(f"[{idx}] Stitch: generating single-page site ...", flush=True)
    out = generate_with_retry(build_prompt(b), b["name"][:60])
    gen_s = time.time() - t0
    print(f"[{idx}] Stitch done in {gen_s:.0f}s — {len(out['html'])} bytes HTML (project {out['projectId']})", flush=True)

    # keep a local copy too
    p = os.path.join(HERE, "out", "batch", slug(b["name"]), "index.html")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(out["html"])

    print(f"[{idx}] Netlify: deploying ...", flush=True)
    url, sid = netlify_deploy.deploy_html(out["html"], site_name=b["name"])
    print(f"[{idx}] LIVE ✅  {url}   ({time.time()-t0:.0f}s total)", flush=True)
    return {"name": b["name"], "url": url, "site_id": sid, "projectId": out["projectId"],
            "local": p, "seconds": round(time.time() - t0)}


def main():
    import sys
    total = len(BUSINESSES)
    # optional: run a subset by 1-based index, e.g.  run_batch.py 3   or  run_batch.py 2 3
    only = [int(a) for a in sys.argv[1:] if a.isdigit()]
    items = [(i, BUSINESSES[i - 1]) for i in only] if only else list(enumerate(BUSINESSES, 1))
    print(f"BATCH START {datetime.datetime.now():%Y-%m-%d %H:%M:%S} — {len(items)}/{total} businesses, sequential trigger chain, device {DEVICE}")
    results = []
    for i, b in items:
        try:
            r = process(i, total, b)
            r["status"] = "Done"
            results.append(r)
            # trigger chain: previous site is LIVE before the next one starts (this loop is serial)
        except Exception as e:
            print(f"[{i}] !! ERROR: {e}", flush=True)
            traceback.print_exc()
            results.append({"name": b["name"], "status": f"Error: {str(e)[:160]}"})

    out_json = os.path.join(HERE, "out", "batch_results.json")
    merged = {}
    if only and os.path.exists(out_json):           # keep prior results when running a subset
        for r in json.load(open(out_json)):
            merged[r["name"]] = r
    for r in results:
        merged[r["name"]] = r
    final = list(merged.values())
    with open(out_json, "w") as f:
        json.dump(final, f, indent=2)
    results = final

    print(f"\n{'#'*64}\nBATCH DONE — live URLs:\n{'#'*64}")
    for r in results:
        if r.get("url"):
            print(f"  ✅ {r['name']:<24} {r['url']}")
        else:
            print(f"  ❌ {r['name']:<24} {r.get('status')}")
    print(f"\nsaved: {out_json}")


if __name__ == "__main__":
    main()
