# 🗺️ STITCH FACTORY — ROADMAP TO AUTOPILOT
Companion to `HANDOFF-FACTORY.md`. Structured "what's left → how we get to 100 sites/day on GitHub, hands-off."
Updated 2026-07-02 (after palette-mood fix).

---

## 0. WHERE WE ARE (one line)
Full agent chain + **the whole self-driving loop built & DRY-RUN proven** (lead adapter, QA-learner ledger,
surgical regen, manifest dedupe, scheduler, outreach handoff, daily cron). **Only gap left = one real Stitch run.**

> **UPDATE 2026-07-02 (autopilot layer):** Phases 2.1, 3.1, 3.2, 3.3, 3.4, 3.5 are now BUILT + tested at 0 credits.
> New files: `leads.py`, `ledger.py`, `manifest.py`, `scheduler.py`, `report_back.py`, `.github/workflows/scheduler.yml`.
> Proven: 5-lead CSV → 5 A-grade → shipped → DM-ready CSV; re-run built 0 (dedupe); poisoned palette got demoted (learner);
> `niches.resolve` specificity fixed (roofing/hvac vs contractor). **Do next: 1.1 real Stitch run** (below).

---

## 1. THE PIPELINE AS AN AGENT ORG (architect view)
Think of it as a small agency. Each box = one deterministic "agent" (a `.py`), no LLM bill.

```
                        ┌──────────────────────────────────────────────┐
   INTAKE               │  Lead source (gmaps-lead-engine / Sheet / CSV)│
   (data)               └───────────────────┬──────────────────────────┘
                                            │  business dict {name,niche,services,reviews,hours}
                        ┌───────────────────▼──────────────────────────┐
   CREATIVE DIRECTOR    │  niches.resolve()  → archetype + prefs        │  ← 1 source of truth
                        └───────────────────┬──────────────────────────┘
             ┌──────────────────────────────┼───────────────────────────────┐
   DESIGN    │ design_dna (font/palette/layout/anim/signature, niche-weighted)│
   TEAM      │ asset_lib (effects+CSS/JS+markers) · copywriter · ref_scout    │
             └──────────────────────────────┬───────────────────────────────┘
                        ┌───────────────────▼──────────────────────────┐
   BRIEF                │  brief_compiler → one Stitch prompt + markers │
                        └───────────────────┬──────────────────────────┘
                        ┌───────────────────▼──────────────────────────┐
   BUILDER              │  stitch_client → poll til booking JS complete │
                        └───────────────────┬──────────────────────────┘
                        ┌───────────────────▼──────────────────────────┐
   TECH TEAM (QA)       │  qa.scorecard: HARD gates + headless booking  │
                        └──────────┬──────────────────────┬────────────┘
                             PASS  │                  FAIL │ (fixes fed back)
                        ┌──────────▼─────────┐   ┌─────────▼───────────┐
   SHIP                 │ netlify_deploy     │   │ regen ×2 w/ MUST FIX│
                        └────────────────────┘   └─────────────────────┘
                        ┌───────────────────────────────────────────────┐
   FLEET MGR            │ orchestrator (seq) / factory.yml (parallel ×4) │
                        └───────────────────────────────────────────────┘
```

**Missing roles** (see Phase 3 — the "loop" upgrade):
- **QA Learner** — remembers which design DNA fails most, down-weights it.
- **Scheduler** — cron pulls N new leads/day, no human trigger.
- **Outreach handoff** — pushes live URL + screenshot back to the lead row for the DM.

---

## 2. WHAT'S LEFT — STRUCTURED BY PHASE

### PHASE 1 — TRUST THE OUTPUT  *(blocks everything; do first)*
| # | Task | File / action | Done-when |
|---|------|---------------|-----------|
| 1.1 | **One real Stitch run** (1 business) | `./venv/bin/python orchestrator.py 1` (sandbox OFF, ~4-5 credits) | live Netlify URL, QA pass on REAL output |
| 1.2 | Eyeball the real site | open URL | booking works, colors right, no AI image |
| 1.3 | Fix whatever the real run breaks | prompt/skeleton tweaks | 2nd run clean |
| 1.4 | Run all 3 fakes in parallel | trigger `factory.yml` (Actions) | 3 live URLs from cloud |

### PHASE 2 — REAL DATA IN  *(makes it a business, not a demo)*
| # | Task | File / action | Done-when |
|---|------|---------------|-----------|
| 2.1 | Wire lead source → `businesses.py` shape | adapter from gmaps-lead-engine CSV → business dict | `businesses.from_csv(path)` returns list |
| 2.2 | Drop the 100 reference `.md` | `references/` (replace 3 placeholders) | scout picks real refs per niche |
| 2.3 | Niche auto-detect from lead | `niches.resolve(lead.category)` already exists — just call it | every lead gets a niche |
| 2.4 | Google Sheets intake (optional) | `sheets_client.py` + `autopilot.yml` cron + SHEET_ID/GCP_SA_JSON secrets | sheet row → build |

### PHASE 3 — THE SELF-DRIVING LOOP  *(the "autopilot" the goal names)*
| # | Task | File / action | Done-when |
|---|------|---------------|-----------|
| 3.1 | **Scheduler** — pull N leads/day, no human | new `scheduler.py` + cron in `autopilot.yml` (e.g. 06:00 daily, batch 25) | wakes, builds, sleeps, unattended |
| 3.2 | **QA Learner** — log every {DNA, score, fail-reason} | append `out/qa_ledger.jsonl`; `design_dna` reads it, down-weights repeat failers | bad combos stop recurring |
| 3.3 | **Regen precision** — keep good parts, fix only broken | surgical fix block instead of full re-roll | 2nd attempt changes only failed gate |
| 3.4 | **Outreach handoff** — live URL + screenshot → lead row | `report_back.py` writes URL/shot to source CSV/Sheet | DM-ready artifact per lead |
| 3.5 | **Dedupe / resume** — never rebuild same lead | MANIFEST like gmaps campaign.sh | safe to re-run, idempotent |
| 3.6 | **Throughput** — 100/day vs Stitch throttle | chunked scheduling + credit headroom; matrix stays ≤4 parallel | 100 sites land in a day |

### PHASE 4 — POLISH (after money flows)
| # | Task | Note |
|---|------|------|
| 4.1 | Barber/tattoo own archetype | today they borrow "beauty" fonts/layouts (palette already fixed via override) |
| 4.2 | Real photos | scrape prospect GBP/IG images (heavy, parked) — ties to site-audit `images.py` |
| 4.3 | Optional LLM copy pass | cheap `claude -p` voice polish; breaks strict "no LLM" — keep behind a flag |
| 4.4 | A/B design auto-promote | build 2 DNAs, keep higher QA score |

---

## 3. LOOP IMPROVEMENTS (detail — Phase 3 expanded)

The current loop is **open** (build → gate → ship, forgets everything). Autopilot needs it **closed** (learns).

### 3a. Learning ledger (cheapest, highest ROI)
- Every attempt appends one line to `out/qa_ledger.jsonl`:
  `{date, name, niche, font, palette, layout, anim, score, grade, pass, fail_gates:[...]}`
- `design_dna.pick()` reads the ledger at import, builds a `penalty[combo] = fail_rate`, and adds it as a
  negative term in `_wpick` scoring. Result: combos that keep failing QA quietly stop being chosen.
- **No LLM.** Pure counting. Gets smarter every run for free.

### 3b. Surgical regen (stop wasting the 2nd attempt)
- Today: fail → re-roll the WHOLE design + append fixes. Loses the good parts.
- Better: on fail, keep the same DNA, and pass QA `fixes` + `missing_markers` as the ONLY delta in the prompt
  ("keep everything, add just these"). Re-roll design only if the SAME gate fails twice.

### 3c. Scheduler = the actual autopilot
- `autopilot.yml` cron (already stubbed) → `scheduler.py`:
  1. pull next `BATCH` unbuilt leads (dedupe via MANIFEST),
  2. run orchestrator per lead (matrix ×4),
  3. write live URL + screenshot back to the lead row,
  4. commit `out/` + ledger, push.
- Human never triggers. You wake up to N new preview sites + DM-ready links.

### 3d. Feedback from reality (later)
- If outreach tracks opens/replies per site, feed "which designs converted" back into the ledger as a POSITIVE
  weight. Now the factory drifts toward designs that actually book calls, not just designs that pass QA.

**Loop maturity ladder:** open (now) → logged (3a) → self-correcting (3b) → self-driving (3c) → self-optimizing (3d).

---

## 4. PRIORITIZED BACKLOG (do in this order)
1. **1.1 real Stitch run** — unblocks trust. *Nothing else matters until this is green.* ← **ONLY ITEM LEFT of the core**
2. ✅ **2.1 lead adapter** — `leads.py` (DONE 2026-07-02).
3. ✅ **3.1 scheduler + 3.5 dedupe** — `scheduler.py` + `manifest.py` (DONE).
4. ✅ **3.2 QA ledger** — `ledger.py`, wired into `design_dna.pick` (DONE).
5. ✅ **3.4 outreach handoff** — `report_back.py` (DONE).
6. ✅ **3.3 surgical regen** — orchestrator surgical-patch-then-escalate (DONE).
7. **2.2** drop 100 reference `.md` · **3.6** 100/day throughput · Phase 4 polish.

---

## 5. GO-LIVE CHECKLIST (autopilot definition of done)
- [ ] Real Stitch site passed QA + eyeballed (1.1–1.3)
- [ ] `factory.yml` ran 3 in parallel from cloud (1.4)
- [ ] Lead CSV/Sheet → `businesses` adapter (2.1)
- [ ] 100 real reference `.md` dropped (2.2)
- [ ] `scheduler.py` + cron builds a daily batch unattended (3.1)
- [ ] MANIFEST dedupe so re-runs are safe (3.5)
- [ ] Live URL + screenshot written back per lead (3.4)
- [ ] QA ledger accumulating + influencing picks (3.2)
- [ ] Credits/rate headroom confirmed for 100/day (3.6)

When all boxed → DM prospect "made you a preview" with zero manual steps.
