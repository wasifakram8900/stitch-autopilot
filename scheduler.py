"""
Scheduler — the actual autopilot. Wakes, pulls the next batch of UNBUILT leads,
runs the full factory chain per lead, records results, and writes DM-ready links
back. No human trigger — cron this (see .github/workflows/autopilot.yml) or run once.

  DRY_RUN=1 ./venv/bin/python scheduler.py            # no credits — proves the loop
  LEADS_CSV=leads.csv BATCH=25 ./venv/bin/python scheduler.py
  ./venv/bin/python scheduler.py                        # falls back to businesses.BUSINESSES

Flow per run:
  1. load leads (LEADS_CSV or the 3 built-in fakes)
  2. drop anything already shipped (manifest dedupe -> idempotent, safe to re-run)
  3. build up to BATCH of them (orchestrator.process: design -> Stitch -> QA -> regen -> deploy)
  4. record manifest + qa_ledger (handled inside orchestrator)
  5. write live URL + grade back to the lead CSV (report_back) -> outreach-ready
"""
import os, datetime, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
from dotenv import load_dotenv
load_dotenv(os.path.join(HERE, ".env"))

import orchestrator
import manifest
import report_back

LEADS_CSV = os.environ.get("LEADS_CSV", "").strip()
if LEADS_CSV and not os.path.exists(LEADS_CSV):
    print(f"LEADS_CSV={LEADS_CSV} not found — falling back to built-in businesses")
    LEADS_CSV = ""
BATCH = int(os.environ.get("BATCH", "25"))
DRY_RUN = os.environ.get("DRY_RUN", "") not in ("", "0", "false")


def source_items():
    if LEADS_CSV:
        import leads
        items = leads.from_csv(LEADS_CSV)
        print(f"source: {LEADS_CSV} -> {len(items)} leads")
        return items
    import businesses
    print(f"source: businesses.BUSINESSES -> {len(businesses.BUSINESSES)} leads (no LEADS_CSV set)")
    return businesses.BUSINESSES


def run_once():
    mode = "DRY-RUN (no Stitch/Netlify)" if DRY_RUN else "LIVE"
    all_items = source_items()
    todo = manifest.unbuilt(all_items)
    batch = todo[:BATCH]
    print(f"AUTOPILOT {datetime.datetime.now():%Y-%m-%d %H:%M} — {mode} · "
          f"{len(all_items)} total · {len(todo)} unbuilt · building {len(batch)} (BATCH={BATCH})")
    if not batch:
        print("nothing to build — all leads already shipped. idle.")
        return []
    results = []
    for i, b in enumerate(batch, 1):
        try:
            r = orchestrator.process(i, len(batch), b)
        except Exception as e:
            print(f"  !! ERROR: {e}", flush=True)
            traceback.print_exc()
            r = {"name": b["name"], "status": f"Error: {str(e)[:160]}", "url": None}
        manifest.record(b, r)
        results.append(r)

    if LEADS_CSV:
        try:
            res = report_back.write_csv(LEADS_CSV)
            print(f"\noutreach handoff: {res['out']}  ({res['matched']}/{res['rows']} rows have previews)")
        except Exception as e:
            print(f"report_back skipped: {e}")

    shipped = [r for r in results if r.get("url")]
    print(f"\n{'#'*60}\nAUTOPILOT RUN DONE — shipped {len(shipped)}/{len(batch)}\n{'#'*60}")
    for r in results:
        if r.get("url"):
            print(f"  ✅ {r['name']:<28} {r.get('grade','')} {r.get('score','')}  {r['url']}")
        else:
            print(f"  ❌ {r['name']:<28} {r.get('status')}")
    return results


if __name__ == "__main__":
    run_once()
