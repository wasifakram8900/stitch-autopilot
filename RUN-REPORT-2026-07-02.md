# 🏭 STITCH FACTORY — FIRST LIVE RUN REPORT
**Date:** 2026-07-02 · **Run:** [28554471249](https://github.com/wasifakram8900/stitch-autopilot/actions/runs/28554471249) · **Commit:** `afaf1cd`

---

## TL;DR
The whole autopilot pipeline was **built, pushed, and executed end-to-end against REAL Google
Stitch on GitHub's cloud for the first time** — no Mac involved. Setup, secrets, Stitch calls,
QA, and the persist step all ran. **BUT: 0 of 3 sites shipped.** The technical-team QA gate
**correctly blocked every build** because the real Stitch output was incomplete/broken. So the
machine works; the *material coming out of Stitch* doesn't clear the quality bar yet.

**Nothing broken deployed — which is the gate doing its job.** But also nothing good deployed.

---

## WHAT RAN (all green)
| Step | Result |
|------|--------|
| Checkout / Python / install deps / Playwright chromium | ✅ |
| Write secrets (STITCH_KEY, NETLIFY_TOKEN) | ✅ loaded |
| Build asset packs | ✅ |
| **Autopilot batch (real Stitch × 3, 2 attempts each)** | ✅ ran, **shipped 0/3** |
| Persist manifest + ledger | ⚠️ "nothing to commit" (did NOT persist — see bug 3) |
| Total wall time | 33m 38s |

---

## THE RESULT — 0/3 SHIPPED
| Business | Attempt 1 | Attempt 2 (surgical) | Outcome |
|----------|-----------|----------------------|---------|
| Brewhaus Coffee | F 49.2 — missing faq/footer/booking_page + 6 booking JS fns | A 91.7 static, **booking_headless FAIL** | ❌ not deployed |
| IronPeak Fitness | F 51.5 — missing footer/booking_page + 6 booking JS fns | B 89.2 static, **booking_headless FAIL** | ❌ not deployed |
| BrightSmile Dental | gen error (Stitch throttle) → A 91.2, **headless FAIL** | B 83.3 — missing toggleService/selectDate | ❌ not deployed |

---

## ROOT CAUSES (real Stitch behavior, finally observed live)
1. **Partial HTML on attempt 1 (the long-known issue, now confirmed live).** Every first
   generation came back missing whole sections (faq, footer, the entire `page-book` booking view)
   and 6+ booking JS functions. Either `stitch_client` polling returns before Stitch finishes,
   or Stitch simply does not build the full hand-coded booking app from our prompt.
2. **`booking_headless` hard gate never passes.** Even when a 2nd attempt reached A/91.7 on
   static checks (structure + booking JS present), the Playwright click-through (select service →
   date → time → confirm → "you're all set") failed. So the booking flow isn't actually clickable —
   either Stitch's markup/onclick contract differs from what the headless test drives, or the JS
   is present but non-functional.
3. **Manifest/ledger did NOT persist back** (`git add -f ... ` → "nothing to commit"). Combined
   with 0 shipped, this means a live cron would **rebuild all 3 every run forever** = continuous
   credit burn for zero output. → **cron paused** until builds pass.
4. **Stitch throttles** rapid back-to-back gens (one `TaskGroup` gen error, auto-retried OK) —
   confirms the existing backoff is needed; parallel/rapid scheduling must stay throttled.

---

## DECISIONS TAKEN
- **10-min cron PAUSED** in `scheduler.yml` (commented; `workflow_dispatch` still works). Stops the
  credit bleed. Re-enable = uncomment two lines, once a real build passes QA.
- Everything else stays live/pushed. Manual runs still available from the Actions tab.

---

## FIX ORDER (to get the first real site live)
1. **Make Stitch return a COMPLETE booking build.** Options, cheapest first:
   - Harden `stitch_client` polling: wait longer / require ALL of `page-book` + the 7 booking
     core fns + faq + footer present before returning (poll more tries, bigger settle window).
   - If Stitch genuinely won't build the booking app from one prompt: split the ask, or inject a
     known-good booking `page-book` HTML/JS block into the prompt as "include verbatim".
2. **Reconcile `booking_headless` with real markup.** Run one Stitch output locally, open it, and
   either fix the site's onclick contract in the prompt OR relax the headless selectors to match.
   Consider making `booking_headless` a SOFT (warn) gate until static passes reliably, so a good
   static build can ship while the click-through is tuned.
3. **Fix persist step** so manifest/ledger commit back (verify `git add -f` path; the files exist
   under `out/` — confirm they're written before the add, and that `out/` isn't blocking `-f`).
4. Only THEN re-enable the cron.

---

## WHAT'S PROVEN vs NOT
- ✅ Pipeline runs end-to-end on GitHub cloud, hands-off, real Stitch + real secrets.
- ✅ QA gate correctly blocks broken output (0 junk shipped).
- ✅ Surgical regen + 2-attempt loop fire as designed.
- ❌ Not one real site has passed QA / gone live yet.
- ❌ Real Stitch output is incomplete (booking view) — the core thing to fix next.
