"""
Orchestrator — the full agent-team chain, per business, sequential:

  Designer team  -> brief_compiler.build_prompt (design_dna + asset_lib, niche-weighted)
  Build          -> stitch_client.generate_site_html (polls until booking complete)
  Technical team -> qa.scorecard (HARD gates: structure + booking + images [+ headless])
                    FAIL -> regen with a new design seed (up to MAX_ATTEMPTS)
                    PASS -> deploy
  Ship           -> netlify_deploy.deploy_html  -> live URL

Nothing broken/generic/AI-image ever deploys. Results + scorecards -> out/factory_results.json.

  ./venv/bin/python orchestrator.py            # all businesses
  ./venv/bin/python orchestrator.py 2          # just #2
  DRY_RUN=1 ./venv/bin/python orchestrator.py  # no Stitch/Netlify — exercises the chain on a sample
"""
import os, re, json, time, datetime, traceback, sys

HERE = os.path.dirname(os.path.abspath(__file__))
from dotenv import load_dotenv
load_dotenv(os.path.join(HERE, ".env"))

import businesses
import brief_compiler
import qa
import ledger
import manifest

DEVICE = os.environ.get("DEVICE", "DESKTOP")
MAX_ATTEMPTS = int(os.environ.get("MAX_ATTEMPTS", "2"))
HEADLESS = os.environ.get("HEADLESS", "") not in ("", "0", "false")
DRY_RUN = os.environ.get("DRY_RUN", "") not in ("", "0", "false")
GEN_RETRIES = int(os.environ.get("GEN_RETRIES", "3"))
DRY_SAMPLE = os.path.join(HERE, "out", "beautyspot", "index.html")


def slug(name):
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").lower())
    return re.sub(r"-{2,}", "-", s).strip("-") or "site"


def _generate(prompt, title):
    """Stitch with backoff (it throttles rapid back-to-back gens)."""
    if DRY_RUN:
        return {"html": open(DRY_SAMPLE).read(), "projectId": "dry", "complete": True}
    import stitch_client
    last = None
    for attempt in range(1, GEN_RETRIES + 1):
        try:
            return stitch_client.generate_site_html(prompt, device=DEVICE, title=title)
        except Exception as e:
            last = e
            if attempt < GEN_RETRIES:
                w = 20 * attempt
                print(f"     gen attempt {attempt} failed ({str(e)[:80]}); retry in {w}s", flush=True)
                time.sleep(w)
    raise last


def _deploy(html, name):
    if DRY_RUN:
        return f"https://DRY-RUN.example/{slug(name)}", "dry-site-id"
    import netlify_deploy
    return netlify_deploy.deploy_html(html, site_name=name)


def process(idx, total, b):
    t0 = time.time()
    print(f"\n{'='*66}\n[{idx}/{total}] {b['name']}  ({b.get('niche','')})\n{'='*66}", flush=True)
    attempts = []
    last_fixes = None
    prev_fail = None      # hard gates that failed on the previous attempt
    escalate = False      # True -> next regen re-rolls the whole design (surgical didn't clear it)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        if attempt == 1:
            salt, surgical = "", False
        else:
            surgical = not escalate               # first regen = surgical patch (keep the good design)
            salt = "" if surgical else f"r{attempt}"   # escalate = full re-roll with a new seed
        brief = brief_compiler.build_prompt(b, salt=salt, fixes=last_fixes, surgical=surgical)
        ds = brief["ds"]
        mode = "attempt 1" if attempt == 1 else (f"attempt {attempt} (surgical patch)" if surgical
                                                 else f"attempt {attempt} (full re-roll)")
        print(f"  {mode}: {ds['font']['head']}/{ds['font']['body']} · {ds['palette']['name']} · "
              f"{ds['layout']['name']} · {ds['anim']['name']}  (prompt {len(brief['prompt'])} ch)", flush=True)

        out = _generate(brief["prompt"], b["name"][:60])
        html = out["html"]
        local = os.path.join(HERE, "out", "factory", slug(b["name"]), "index.html")
        os.makedirs(os.path.dirname(local), exist_ok=True)
        open(local, "w").write(html)

        card = qa.scorecard(html, brief["markers"], path=local, headless=HEADLESS)
        ledger.record(b["name"], b.get("niche"), ds, card)   # QA-learner: log every attempt
        print(f"  QA: pass={card['pass']} score={card['score']} grade={card['grade']} hard={card['hard']}", flush=True)
        for f in card["fixes"]:
            print(f"      ! {f}", flush=True)
        attempts.append({"attempt": attempt, "surgical": surgical, "score": card["score"], "grade": card["grade"],
                         "pass": card["pass"], "hard": card["hard"], "fixes": card["fixes"],
                         "design": {"font": f"{ds['font']['head']}/{ds['font']['body']}",
                                    "palette": ds["palette"]["name"], "layout": ds["layout"]["name"]}})
        if card["pass"]:
            url, sid = _deploy(html, b["name"])
            print(f"  LIVE ✅  {url}   ({time.time()-t0:.0f}s)", flush=True)
            return {"name": b["name"], "status": "Done", "url": url, "site_id": sid,
                    "score": card["score"], "grade": card["grade"], "attempts": attempts,
                    "local": local, "seconds": round(time.time() - t0)}
        cur_fail = {k for k, v in card["hard"].items() if not v}
        # if a surgical patch didn't clear the same gate, escalate the NEXT regen to a full re-roll
        escalate = bool(surgical and prev_fail and (cur_fail & prev_fail))
        prev_fail = cur_fail
        last_fixes = list(card["fixes"])
        amiss = card["gates"]["animation"]["missing"]
        if amiss:
            last_fixes.append("these effects/animations MUST appear (exact class/fn names): " + ", ".join(amiss))
        nxt = ("surgical patch" if not escalate else "full re-roll") if attempt < MAX_ATTEMPTS else None
        print(f"  ✗ failed QA — {'regenerating (' + nxt + ')' if nxt else 'NOT deploying'}", flush=True)

    return {"name": b["name"], "status": "Failed QA — not deployed", "url": None,
            "score": attempts[-1]["score"], "grade": attempts[-1]["grade"],
            "attempts": attempts, "seconds": round(time.time() - t0)}


def main():
    items_all = businesses.BUSINESSES
    only = [int(a) for a in sys.argv[1:] if a.isdigit()]
    items = [(i, items_all[i - 1]) for i in only] if only else list(enumerate(items_all, 1))
    total = len(items_all)
    mode = "DRY-RUN (no Stitch/Netlify)" if DRY_RUN else f"LIVE device={DEVICE}"
    print(f"FACTORY START {datetime.datetime.now():%Y-%m-%d %H:%M} — {len(items)}/{total} businesses · "
          f"{mode} · max_attempts={MAX_ATTEMPTS} · headless={HEADLESS}")
    results = []
    for i, b in items:
        try:
            r = process(i, total, b)
        except Exception as e:
            print(f"  !! ERROR: {e}", flush=True)
            traceback.print_exc()
            r = {"name": b["name"], "status": f"Error: {str(e)[:160]}", "url": None}
        manifest.record(b, r)   # dedupe/resume ledger
        results.append(r)

    out_json = os.path.join(HERE, "out", "factory_results.json")
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    merged = {}
    if only and os.path.exists(out_json):
        for r in json.load(open(out_json)):
            merged[r["name"]] = r
    for r in results:
        merged[r["name"]] = r
    final = list(merged.values())
    json.dump(final, open(out_json, "w"), indent=2)

    print(f"\n{'#'*66}\nFACTORY DONE\n{'#'*66}")
    for r in final:
        if r.get("url"):
            print(f"  ✅ {r['name']:<24} {r.get('grade','')} {r.get('score','')}  {r['url']}")
        else:
            print(f"  ❌ {r['name']:<24} {r.get('status')}")
    print(f"\nsaved: {out_json}")


if __name__ == "__main__":
    main()
