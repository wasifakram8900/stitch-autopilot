# FACTORY-PLAN — agent-team website mill (Stitch + GitHub only)

Goal: 100 unique, non-generic preview sites/day for cold outreach. Each site = different
fonts / bold color theme / animations, all sections present, **booking page fully working**,
real (not AI) imagery, good copy. A **designer team** shapes it, a **technical team** verifies
it works **before** deploy. Runtime = GitHub Actions + Stitch API + Netlify. Nothing else.

---

## 0. Core reframe (read first)

- `full_prompt.txt` already makes a *complete* site (8 sections + full booking + 12 animations).
  Its ONE flaw = it's **hardcoded** → every site is the same med-spa look. "Generic" comes from
  a fixed brief, not from Stitch being weak.
- So the fix is NOT a bigger prompt. It's a **team around the prompt**:
  1. vary the brief per business so every site is visually unique (the **Design DNA engine**),
  2. **gate** the Stitch output with hard checks so nothing broken/generic ships.
- "200 agents" reframed: a 100/day FREE cloud mill cannot spawn 200 LLM agents per site (cost +
  can't run in GitHub free minutes). The **team = pipeline STAGES (roles)**, most of them
  deterministic Python (free, robust), with an OPTIONAL thin LLM "taste" layer. Same outcome,
  feasible at scale.

---

## 1. The team (pipeline roles)

Per business, sequential. Each role = one module. ⚙️ = deterministic (free). 🧠 = optional LLM.

### DESIGNER TEAM
| Role | Does | Type |
|------|------|------|
| **Reference Scout** | From the 100 reference `.md` files, pick top-K matching the niche + target vibe (files tagged by niche/style). | ⚙️ |
| **Design Director** | Build a **unique design system** for THIS site: font pairing + bold palette + layout archetype + animation pack + one "signature move". Seeded so no two sites repeat. | ⚙️ (🧠 optional) |
| **Copywriter** | Headline, tagline, section copy in niche voice. Deterministic templates per niche, or LLM for real voice. | ⚙️/🧠 |
| **Brief Compiler** | Fill the parametrized master prompt with DNA + copy + business data → the Stitch prompt. | ⚙️ |

### BUILD
| **Stitch Builder** | Send brief → Stitch → **poll `get_screen` until HTML is COMPLETE** (full booking/calendar/data, byte count settled). Solves the known partial-HTML bug. | ⚙️ |

### TECHNICAL TEAM (gates — must pass before deploy)
| Role | Checks | Fail action |
|------|--------|-------------|
| **Structure Auditor** | All 8 home sections + `#page-book` present. | regen / re-prompt |
| **Booking Tester** | Every required JS fn present (`showPage`,`renderCalendar`,`toggleService`,`confirmBooking`,…). Headless render → click Book → pick service/date/time → fill form → assert confirmation screen. | regen |
| **Animation Auditor** | Greps 12 animation hooks (reveal, word-split, glass nav, counters, blobs…) + `prefers-reduced-motion`. | re-prompt |
| **Image Cop** | NO banned AI img (`googleusercontent.com/aida`, `gstatic…labs-code`). Images = real provided photos OR styled placeholder. | strip/regen |
| **A11y + Responsive** | Contrast ≥4.5:1, 375px no horizontal scroll, alt text, touch ≥44px. | warn/fix |
| **Console/Link** | Headless load → 0 console errors, no dead `href="#"`. | regen |
| **Scorecard** | All gates → pass/fail + score 0–100. Hard-fail = no deploy. | gate |

### ART DIRECTION (optional taste gate)
| **Art Director** 🧠 | Screenshot rendered site → score uniqueness/polish vs reference, veto "generic". Weak → regen with stronger brief. | optional |

### SHIP
| **Deploy** | Netlify digest deploy (already working, serves `text/html`). | ⚙️ |
| **Orchestrator** | Runs chain 1→2→3…, sequential, 100/day, logs scorecards, retries, prints live URLs. | ⚙️ |

---

## 2. Design DNA engine — how "unique every time" works WITHOUT per-site AI

Seeded combinatorial selector. `seed = hash(business_name + date)`. Pools sourced from the
`ui-ux-pro-max` skill (57 font pairings, 161 palettes, animation rules):

- **Font pairing**: ~40 options (heading + body, real Google Fonts).
- **Color theme**: ~60 palettes incl. bold / dark / vibrant / duotone.
- **Layout archetype**: ~8 (centered-massive-type, split-hero, asymmetric, magazine, bento,
  full-bleed-image, sidebar-rail, scroll-snap-sections).
- **Animation pack**: ~6 signature sets (word-reveal, marquee, parallax-lite, cursor-glow,
  stagger-grid, scroll-snap).
- **Signature move**: 1 differentiator (sticky side index, animated gradient mesh, marquee strip,
  hover-tilt cards, scroll progress rail…).

`40 × 60 × 8 × 6 × N-copy` ≈ effectively never repeats. The master prompt becomes a **template**
with `{{heading_font}} {{body_font}} {{palette}} {{type_scale}} {{anim_pack}} {{layout}} {{signature}}`
slots that the Design Director fills. This is the whole "non-generic" trick — free, deterministic.

---

## 2c. Asset Library — "tons of effects" the agents compose from  → `asset_lib.py` ✅ built

Curated catalog of effects, each = `{id, tags, marker, prompt, css?, js?}` across categories
**gradient / background / cursor / glass / glow / animation / hover**. The trick that makes it
real + verifiable:
- **`prompt`** = the line injected into the Stitch brief.
- **`css`/`js`** = the literal snippet appended as a "include VERBATIM" contract.
- **`marker`** = a class/fn name we MANDATE → the technical team **greps the generated HTML for it
  to PROVE the effect shipped** (else regen). Effects guaranteed, not hoped for.

`bundle(name,date,niche)` = seeded + **niche-weighted** pick (gym→bold/dark/interactive,
dental→calm/minimal) of a coherent set; `compose_block()` renders the brief section;
`markers()` feeds QA. Verified: 3 businesses → 3 distinct bundles, gym got magnetic-btn/glow-border,
coffee got breathe/image-zoom.

**Reaching "10000s" (no hand-authoring 10000):**
1. **Curated core** (~200, quality-controlled — here in `asset_lib.py`).
2. **Bulk import** of free MIT libs as `assets/*.json` (loaded by `load_external()`): full
   **~1500 Google Fonts**, **animate.css**, **Hover.css**, CSS gradient galleries. Just data files
   in the repo — no runtime service, honors "Stitch + agents + GitHub only".
3. **Parametric variants**: 1 gradient recipe × palettes × angle × stops = thousands; 1 glow ×
   color seed = thousands. Combination across packs → ≫10000 distinct looks, all offline.

## 3. Build order (milestones)

1. **`design_dna.py`** — pools + seeded selector → returns a `DesignSystem` dict. (pull real
   fonts/palettes from ui-ux-pro-max)
2. **Templatize `full_prompt.txt` → `prompt_template.txt`** — Brief Compiler merges
   `design_dna.to_prompt_block()` + `asset_lib.compose_block()` + business + copy into the prompt.
2b. **Bulk-import packs** → `import_assets.py` writes `assets/*.json` (full Google Fonts list,
   animate.css, Hover.css, parametric gradient/glow generators). `asset_lib.load_external()` merges.
3. **`stitch_client.py` polling** — `generate` → poll `get_screen(pid,sid,name)` ~25s until HTML
   complete (calendar + data + settled bytes); only then return. *(known open task)*
4. **`qa/` technical team** — `structure.py`, `booking.py` (Playwright headless), `animation.py`,
   `images.py`, `a11y.py`, `console.py` → each returns `(pass, score, fixes)`; `scorecard.py` folds.
5. **`reference_scout.py`** — load `references/*.md`, tag by niche/style, select top-K.
6. **`orchestrator.py`** — per business: Scout → Director → Brief → Stitch(poll) → QA gates →
   (regen on fail, max 2) → Deploy → log. Sequential chain.
7. **3 fake businesses** already in `run_batch.py` (coffee / gym / dental) → swap to orchestrator
   so each comes out visually distinct + gated.
8. **GitHub Actions** `factory.yml` — cron + dispatch; secrets `STITCH_KEY`, `NETLIFY_TOKEN`
   (+ `ANTHROPIC_API_KEY` only if LLM layer on); installs Playwright; uploads scorecards + URLs.
9. **Sheets intake** — LAST, after the above is green.

---

## 4. Decisions — LOCKED 2026-06-25
1. **Taste layer = Deterministic first.** DNA combinatorics for uniqueness + grep/headless QA.
   No LLM, no API key. Optional LLM art-director bolted on later.
2. **Images = Photo-free premium.** Gradients / CSS art / animated mesh / icons, self-contained.
   No stock service, no scrape. (revisit per-lead scrape later for real outreach personalization.)
3. **References = `references/*.md`, Scout auto-tags** by niche+style on load. User drops 100 files in.

### (original options, for reference)

1. **Taste layer**: fully deterministic (free, "unique" via DNA combinatorics + grep/headless QA,
   stays inside Stitch+GitHub) vs **hybrid** (add cheap Claude art-director/copy for real judgment,
   needs `ANTHROPIC_API_KEY`). → recommend: ship deterministic first, add LLM veto later.
2. **Images "their own, not AI"**: for cold prospects we have no photos. Options:
   (a) **photo-free premium** (gradients/CSS art/icons — self-contained, Awwwards-tier, recommended
   for a mill), (b) niche **stock** via Pexels/Unsplash API (real photos, +1 API key), (c) **scrape
   prospect's real** photos from IG/Google Business (best outreach, heavy). → recommend (a) default,
   (b) opt-in.
3. **Reference files**: where do the 100 `.md` go (`references/` in repo?) and are they pre-tagged by
   niche/style, or should Scout auto-tag on load?

---

## 5. Constraints honored
- Runtime = GitHub Actions + Stitch + Netlify only (Playwright = pip lib in Actions, not new software).
- Deterministic core = no LLM cost, no extra service → satisfies "no other software".
- Booking + animations verified by code, not vibes → "fully working before deploy" is literal.
