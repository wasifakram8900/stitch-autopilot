# HANDOFF — Stitch Autopilot "Agent-Team Factory"

**Read this first in a new session.** Full state of the website-mill as of commit `c87865e` (main).
Repo: `github.com/wasifakram8900/stitch-autopilot` (public). Dir: `/Users/wasifali/Claude/stitch-autopilot/`.
Also see: `FACTORY-PLAN.md` (design doc), memory `stitch-autopilot-2026-06-19.md`.

---

## 1. GOAL
Cold-outreach website mill. ~100 preview sites/day. DM prospect "made you a preview". Each site =
**unique look + fully working booking page + all sections + no AI images + good copy**. A designer
team shapes it, a technical team verifies it works **before** deploy. Runs in **Stitch + GitHub +
Netlify only** — no other software, no LLM/API bill (deterministic core).

## 2. HOW IT WORKS (the loop)
```
Reference Scout → Designer team → Stitch build → Technical team (gates) → Deploy
  (best refs)     (unique look     (poll til      (grep markers +          (Netlify)
                   + effects+copy)   complete)      headless booking test)
                                                    PASS → deploy
                                                    FAIL → regen w/ fixes (×2)
  ↑ all businesses run in PARALLEL via GitHub matrix (throttled)
```
Nothing broken / generic / AI-image ever deploys.

## 3. THE AGENTS (what each file is)
| Agent / role | File | What it does |
|---|---|---|
| **Niche registry** | `niches.py` | ONE source of truth. 42 local-business niches → design prefs + effect bias + copy + keywords. `resolve()` maps any text→canonical niche. |
| **Design Director** | `design_dna.py` | Seeded, niche-weighted pick: font pairing (122) · palette (15) · layout (8) · type-scale · animation pack · signature move. Never repeats. |
| **Asset library** | `asset_lib.py` | Effects catalog (gradient/glass/glow/cursor/animation/hover). Each = prompt + verbatim CSS/JS + **QA marker**. `bundle()` = niche-weighted set. |
| **Bulk importer** | `import_assets.py` | Offline generators → `assets/*.json` (108 font pairings, 84 gradients, animate.css/Hover.css packs). |
| **Copywriter** | `copywriter.py` | Deterministic niche copy (eyebrow/headline/CTA/about/FAQ). Gym→"Book a Free Session", HVAC→"Get a Free Quote". |
| **Reference Scout** | `reference_scout.py` | Loads `references/*.md`, auto-tags niche+style, picks best per business → "match this caliber" block + style bias. |
| **Brief Compiler** | `brief_compiler.py` | Assembles Stitch prompt = SKELETON (booking spec + 16 JS fns + rules) + DNA + effects + copy + scout + data. `fixes` param → MUST FIX block. |
| **Builder** | `stitch_client.py` | Stitch MCP call, **polls `get_screen` until booking JS present + bytes settle** (fixes partial HTML). |
| **Technical team** | `qa.py` | Gates: structure, booking JS, images (no AI/stock), animation, a11y, links + optional Playwright booking click-through → scorecard {pass, score, grade, fixes}. |
| **Orchestrator** | `orchestrator.py` | Per-business chain: build→Stitch→QA→regen (SURGICAL patch first, full re-roll only if same gate stays broken)→deploy. Logs every attempt to ledger; records manifest. `DRY_RUN=1` tests w/o credits. |
| **Businesses** | `businesses.py` | 3 rich fake businesses (coffee/gym/dental) w/ services/reviews/hours. |
| **Lead adapter** | `leads.py` | Any CSV (gmaps-lead-engine / enrich exports) → business dict. Tolerant column aliasing, niche auto-resolve. `from_csv(path)`. |
| **QA Learner** | `ledger.py` | Appends every attempt to `out/qa_ledger.jsonl`; `penalties()` = per-DNA-value fail-rate. `design_dna.pick()` drops chronic failers (>55% fail, ≥3 samples) from the tier. Closed loop, no LLM. |
| **Manifest** | `manifest.py` | `out/manifest.json` dedupe/resume — a shipped lead never rebuilds. Idempotent re-runs. |
| **Scheduler** | `scheduler.py` | The autopilot: pull unbuilt leads → build BATCH → record → write DM-ready CSV. Cron/hands-off. `DRY_RUN=1` supported. |
| **Outreach handoff** | `report_back.py` | Writes live URL + QA grade back to the lead CSV (`*_outreach.csv`); `dm_ready()` lists shipped previews. |
| **Cloud** | `.github/workflows/factory.yml` (dispatch, parallel matrix) · `scheduler.yml` (daily cron, full chain, commits manifest+ledger back) | Secrets: STITCH_KEY, NETLIFY_TOKEN (set). |

## 4. THE NON-GENERIC ENGINE
`design_dna` × `asset_lib` seeded by `hash(name+date)`:
- 122 font pairings × 15 palettes × 8 layouts = **15,616 combos** before effects/anims/signatures.
- Each effect injects real CSS/JS + a **marker** the tech team greps → effect guaranteed, not hoped.
- Niche-weighted so gym≠spa (gym→Bebas Neue/dark/bold; dental→Epilogue/light/clean).

## 5. THE 42 NICHES (in `niches.py`, add more there only)
- **Trade** (14): hvac, plumbing, electrician, roofing, contractor, landscaping, cleaning, pest-control, painting, handyman, moving, solar, pool, auto
- **Beauty** (6): medspa, spa, salon, barber, nails, tattoo
- **Medical** (7): dental, chiropractor, physical-therapy, dermatology, veterinary, optometry, clinic
- **Food** (5): coffee, restaurant, bakery, catering, florist
- **Professional** (5): real-estate, law, accounting, photography, interior-design
- **Events** (2): venue, events · **Fitness** (2): gym, yoga · **Tech** (1): agency

## 6. ✅ DONE + PROVEN
- Full pipeline built, compiles clean, **DRY-RUN end-to-end** (0 credits): 3 businesses → 3 distinct A-grade designs → deploy.
- **QA gates proven on real HTML**: hand-built site → PASS 100/A; old partial Stitch → FAIL 30/F (caught missing sections + broken booking JS + banned AI image). This gate blocks the broken deploys that happened before.
- Netlify digest deploy serves correct `text/html` (earlier bug fixed).
- Stitch polling fix landed. Niche-weighting fixed (no more gym-gets-serif). Targeted regen proven (retry changed palette + injected MUST FIX). 42-niche registry proven (resolve + per-niche design/copy/effects).
- Pushed: commits `834ddac` → `71a133e` → `c87865e`.

## 6b. ✅ AUTOPILOT LAYER — BUILT + DRY-RUN PROVEN (2026-07-02)
The self-driving loop (was "missing roles") is now built & tested end-to-end at 0 credits:
- **Lead adapter** (`leads.py`) — parsed a gmaps-ish 5-lead CSV → business dicts, niches auto-resolved.
- **QA Learner** (`ledger.py`) — logs every attempt; **proven** it demotes a chronic failer (poisoned palette penalty 0.9 → pick moved to a still-niche-correct alt).
- **Surgical regen** — first regen keeps the good DNA & patches only the failing gate ("SURGICAL FIX" block); escalates to full re-roll only if the same gate stays broken.
- **Manifest dedupe** (`manifest.py`) — run 2 of the same batch built **0** (all shipped). Idempotent.
- **Scheduler** (`scheduler.py`) — DRY-RUN batch: 5 leads → 5 A-grade → shipped → DM-ready CSV, one command, no human trigger.
- **Outreach handoff** (`report_back.py`) — appended `preview_url/grade/score/status/built_at` back to the lead CSV.
- **Cloud cron** (`scheduler.yml`) — daily, runs the full chain, commits manifest+ledger back so dedupe/learning persist.
- **Bonus fix** — `niches.resolve()` now prefers specific trades over generic parents ("Roofing contractor"→roofing, "HVAC contractor"→hvac; plain "Contractor"→contractor).

## 7. ❌ LEFT / NOT DONE
1. **ONE REAL STITCH RUN** *(still the only real blocker)* — everything above proven on *sample* HTML, NOT live Stitch output. To confirm: `DRY_RUN=` unset `LEADS_CSV=leads.csv ./venv/bin/python scheduler.py`, or trigger `scheduler.yml`/`factory.yml` (Actions). Needs `.stitch_key`+`.netlify_token`, ~4-5 credits/site, sandbox OFF (RAM).
2. **User's 100 reference `.md`** — not provided yet. Drop in `references/` (3 samples are placeholders). Scout auto-tags on load.
3. **Real lead CSV** — drop a `leads.csv` (any columns; `leads.py` maps them) to feed real prospects instead of the 3 fakes. Ties to gmaps-lead-engine output.
4. **Throughput (3.6)** — 100/day vs Stitch throttle; matrix ≤4 parallel + poll ~5min/site may need chunked scheduling / credit headroom.
5. **Google Sheets intake (optional)** — `autopilot.py`/`sheets_client.py` path still there; CSV via `leads.py` is now the simpler default.

## 8. ⚠️ NEEDS IMPROVEMENT (ranked)
1. ✅ **DONE (2026-07-02)** — Palettes now mood-tagged; niches carry `palette` mood prefs. `design_dna.PALETTES` each has `mood`; `niches.ARCHETYPES[*].palette` + `niches.PALETTE_OVERRIDE` (barber/tattoo/landscaping/pool/solar/auto/yoga/florist/nails). `_wpick` keys palette on name+scheme+mood. Verified: roofing→navy mustard, gym→ink&lime, dental→clinical, medspa→blush plum, barber→graphite ember, landscaping→olive linen.
2. ✅ **DONE (2026-07-02)** — Palette pool 15 → **24** (added steel blue, graphite ember, hunter brass, terracotta clay, arctic sky, burgundy cream, charcoal amber, sage stone, plum orchid — fills masculine/industrial/corporate/clinical-light gap). Combos now ≈ 45M.
3. **Small-ref-set bias dilution** — with <~5 references, scout style_bias = all tags → muddies palette pick. Self-resolves at 100 refs. 
4. **Copywriter = templated** (good, not great). Optional cheap-LLM copy pass later for real voice (breaks "no LLM" slightly).
5. **100/day scaling** — poll adds ~5min/site; matrix parallel built but Stitch throttles (max-parallel 4). May need credit/rate headroom or chunked scheduling.
6. **Images photo-free only** — premium but not "their own photos". Real personalization = scrape prospect IG/GBP photos (parked, heavy).
7. **No per-fix precision on regen** — regen re-rolls whole design + appends fixes; could surgically keep good parts.

## 9. KEY GOTCHAS (Stitch/infra)
- Stitch MCP: `https://stitch.googleapis.com/mcp`, header `X-Goog-Api-Key`. `deviceType` UPPERCASE (DESKTOP/MOBILE). `get_screen(pid,sid,name)` works; `list_screens`/`get_project` return no screens.
- Stitch returns HTML immediately but PARTIAL — agent keeps building → MUST poll (handled in stitch_client).
- Sandbox OOM (exit 137) reading big Stitch responses → run with sandbox off.
- Stitch throttles rapid gens → `generate_with_retry` backoff exists.
- Netlify: digest deploy (POST /sites → POST deploys w/ sha1 → PUT only `required`). Subdomain = slugified business name, clash→suffix.

## 10. NEXT-SESSION QUICKSTART
```bash
cd /Users/wasifali/Claude/stitch-autopilot
DRY_RUN=1 ./venv/bin/python orchestrator.py      # prove chain, 0 credits
./venv/bin/python niches.py                        # see 42 niches + resolve
./venv/bin/python qa.py out/beautyspot/index.html  # see gates
# REAL run (credits): ./venv/bin/python orchestrator.py   (or trigger factory.yml in Actions)
```
Opener suggestion: *"Continue stitch-autopilot factory. Read HANDOFF-FACTORY.md. Next: [real run / fix palettes / wire my references]."*
