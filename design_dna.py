"""
Design DNA engine — the "unique every time" core. NO LLM, NO cost.

seed = hash(business_name + date) -> deterministic, independent pick from each pool
(font pairing / color theme / layout archetype / animation pack / signature move / type scale).
~14 x 16 x 8 x 6 x 8 x 4 ≈ 480k visual combos before copy -> sites never look the same.

Pools are real (Google Fonts + hex palettes) and feed the Stitch prompt template.
Run `python design_dna.py` to print 3 sample DNAs and confirm they differ.
"""
import hashlib
import datetime
import niches


# ── FONT PAIRINGS (heading / body, real Google Fonts) ──────────────────────────
FONTS = [
    {"head": "Cormorant Garamond", "body": "DM Sans", "mood": "editorial luxe",
     "href": "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@300;400;500;700&display=swap"},
    {"head": "Playfair Display", "body": "Inter", "mood": "classic elegant",
     "href": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700;900&family=Inter:wght@300;400;500;600&display=swap"},
    {"head": "Fraunces", "body": "Work Sans", "mood": "warm editorial",
     "href": "https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,500&family=Work+Sans:wght@300;400;500;600&display=swap"},
    {"head": "Space Grotesk", "body": "Inter", "mood": "modern tech",
     "href": "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Inter:wght@300;400;500;600&display=swap"},
    {"head": "Syne", "body": "Manrope", "mood": "bold artsy",
     "href": "https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=Manrope:wght@300;400;500;600&display=swap"},
    {"head": "Bricolage Grotesque", "body": "DM Sans", "mood": "contemporary display",
     "href": "https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=DM+Sans:wght@300;400;500;700&display=swap"},
    {"head": "Libre Baskerville", "body": "Karla", "mood": "refined serif",
     "href": "https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Karla:wght@300;400;500;600&display=swap"},
    {"head": "Archivo", "body": "Archivo", "mood": "industrial grotesque",
     "href": "https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;700;900&display=swap"},
    {"head": "Epilogue", "body": "Inter", "mood": "clean modern",
     "href": "https://fonts.googleapis.com/css2?family=Epilogue:wght@500;600;800&family=Inter:wght@300;400;500&display=swap"},
    {"head": "Instrument Serif", "body": "Inter", "mood": "high-contrast editorial",
     "href": "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@300;400;500;600&display=swap"},
    {"head": "Unbounded", "body": "Inter", "mood": "rounded display bold",
     "href": "https://fonts.googleapis.com/css2?family=Unbounded:wght@500;700;800&family=Inter:wght@300;400;500&display=swap"},
    {"head": "Big Shoulders Display", "body": "Public Sans", "mood": "tall industrial",
     "href": "https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@500;700;800&family=Public+Sans:wght@300;400;500;600&display=swap"},
    {"head": "DM Serif Display", "body": "DM Sans", "mood": "high-contrast serif",
     "href": "https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;700&display=swap"},
    {"head": "Sora", "body": "Inter", "mood": "geometric tech",
     "href": "https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Inter:wght@300;400;500&display=swap"},
]

def _load_font_pack():
    """Merge bulk-imported assets/fonts.json pairings into FONTS (run import_assets.py to create it)."""
    import json, os
    fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts.json")
    if not os.path.exists(fp):
        return
    try:
        for p in (json.load(open(fp)).get("pairings") or []):
            FONTS.append({"head": p["head"], "body": p["body"], "mood": p.get("mood", ""), "href": p["href"]})
    except Exception:
        pass


_load_font_pack()


# ── COLOR THEMES (60/30/10 bg/primary/accent). Mix of light, dark, bold, vibrant ──
PALETTES = [
    {"name": "warm sand", "scheme": "light", "bg": "#fff8f4", "surface": "#fdf2ec", "primary": "#8a4853", "accent": "#56642b", "text": "#1f1b17", "muted": "#7a6e6a", "border": "rgba(138,72,83,0.12)"},
    {"name": "ink & lime", "scheme": "dark", "bg": "#0e0f0c", "surface": "#17190f", "primary": "#e6f37a", "accent": "#b6ff3d", "text": "#f4f5ee", "muted": "#9a9b8e", "border": "rgba(230,243,122,0.14)"},
    {"name": "midnight teal", "scheme": "dark", "bg": "#07111a", "surface": "#0d1c28", "primary": "#3fd2c7", "accent": "#ffb347", "text": "#eaf6f7", "muted": "#7d97a1", "border": "rgba(63,210,199,0.16)"},
    {"name": "cobalt pop", "scheme": "light", "bg": "#f4f6ff", "surface": "#e9edff", "primary": "#2433c9", "accent": "#ff4d6d", "text": "#10122b", "muted": "#5c6285", "border": "rgba(36,51,201,0.12)"},
    {"name": "forest cream", "scheme": "light", "bg": "#f6f4ee", "surface": "#eceadd", "primary": "#1f4d36", "accent": "#c9772f", "text": "#161a15", "muted": "#6b7066", "border": "rgba(31,77,54,0.12)"},
    {"name": "noir gold", "scheme": "dark", "bg": "#0c0b0a", "surface": "#161413", "primary": "#d9b35f", "accent": "#f0e6d2", "text": "#f4efe6", "muted": "#9a9186", "border": "rgba(217,179,95,0.16)"},
    {"name": "blush plum", "scheme": "light", "bg": "#fdf4f7", "surface": "#f8e7ee", "primary": "#7a2e57", "accent": "#e0608a", "text": "#241019", "muted": "#7e6470", "border": "rgba(122,46,87,0.12)"},
    {"name": "electric violet", "scheme": "dark", "bg": "#0b0814", "surface": "#150f24", "primary": "#9d6bff", "accent": "#28e0c4", "text": "#efeaff", "muted": "#8b82a6", "border": "rgba(157,107,255,0.16)"},
    {"name": "clean clinical", "scheme": "light", "bg": "#f7fbfc", "surface": "#e9f4f6", "primary": "#0e7c86", "accent": "#1f9d55", "text": "#10201f", "muted": "#5f7375", "border": "rgba(14,124,134,0.12)"},
    {"name": "tangerine slate", "scheme": "light", "bg": "#fbf8f5", "surface": "#f0ebe5", "primary": "#1c2733", "accent": "#ff6a1f", "text": "#15191f", "muted": "#69727c", "border": "rgba(28,39,51,0.12)"},
    {"name": "carbon orange", "scheme": "dark", "bg": "#0d0d0e", "surface": "#1a1b1d", "primary": "#ff7a2f", "accent": "#f4f4f4", "text": "#f2f2f3", "muted": "#8d8f94", "border": "rgba(255,122,47,0.16)"},
    {"name": "olive linen", "scheme": "light", "bg": "#f7f6f0", "surface": "#eceada", "primary": "#5c6234", "accent": "#9c4a2f", "text": "#1c1d16", "muted": "#73736a", "border": "rgba(92,98,52,0.12)"},
    {"name": "deep sea coral", "scheme": "dark", "bg": "#06121a", "surface": "#0c1f2b", "primary": "#ff6b6b", "accent": "#4ee0d0", "text": "#e9f4f6", "muted": "#7b95a0", "border": "rgba(255,107,107,0.16)"},
    {"name": "rose gold mono", "scheme": "light", "bg": "#fbf6f4", "surface": "#f4e7e2", "primary": "#b76e6e", "accent": "#3a3a3a", "text": "#211a18", "muted": "#80706c", "border": "rgba(183,110,110,0.12)"},
    {"name": "neon mint dark", "scheme": "dark", "bg": "#0a0f0d", "surface": "#111a16", "primary": "#3ef0a0", "accent": "#ff5cf0", "text": "#eafff5", "muted": "#85998f", "border": "rgba(62,240,160,0.16)"},
    {"name": "navy mustard", "scheme": "light", "bg": "#f6f5f1", "surface": "#e9e7df", "primary": "#1b2a4a", "accent": "#e0a82e", "text": "#13161f", "muted": "#646a78", "border": "rgba(27,42,74,0.12)"},
]

# ── LAYOUT ARCHETYPES ──────────────────────────────────────────────────────────
LAYOUTS = [
    {"name": "centered-massive-type", "hero": "centered ultra-large headline, breathing whitespace, single CTA below"},
    {"name": "split-hero", "hero": "two-column hero: headline+CTA left, visual/gradient panel right"},
    {"name": "asymmetric-offset", "hero": "off-center headline, overlapping cards, diagonal rhythm"},
    {"name": "magazine-editorial", "hero": "kicker + serif headline + lede paragraph, column grid below"},
    {"name": "bento-grid", "hero": "headline + a bento grid of unequal cards (services/stats/photos)"},
    {"name": "full-bleed-gradient", "hero": "full-viewport animated gradient mesh, headline overlaid centered"},
    {"name": "sidebar-index", "hero": "sticky left section-index rail, content scrolls on the right"},
    {"name": "scroll-snap-sections", "hero": "each section is a snap panel, big type, one idea per screen"},
]

# ── ANIMATION PACKS (which signature motions to emphasize) ──────────────────────
ANIM_PACKS = [
    {"name": "reveal-classic", "emphasis": "hero word-by-word split, scroll-reveal on every block, glass nav, stat count-up"},
    {"name": "kinetic-marquee", "emphasis": "looping marquee strip of services/keywords, scroll-reveal, hover-scale cards"},
    {"name": "parallax-lite", "emphasis": "subtle multi-layer parallax on hero blobs, sticky scale headings, fade-up"},
    {"name": "cursor-glow", "emphasis": "cursor-following radial glow, magnetic buttons, card hover lift + glow"},
    {"name": "stagger-grid", "emphasis": "grid items stagger-enter 40ms, number count-up, accordion FAQ, nav underline"},
    {"name": "scroll-storytelling", "emphasis": "pinned section text swaps on scroll, progress rail, shimmer headline word"},
]

# ── SIGNATURE MOVE (the one thing that makes it memorable) ──────────────────────
SIGNATURES = [
    "animated gradient-mesh hero background (no photo)",
    "sticky scroll-progress rail down the side",
    "marquee keyword strip between sections",
    "hover-tilt 3D service cards",
    "oversized outlined section numbers (01 / 02 / 03)",
    "cursor-following glow orb",
    "duotone gradient blobs drifting behind content",
    "big animated stat counters band",
]

# ── TYPE SCALES (clamp ranges) ──────────────────────────────────────────────────
TYPE_SCALES = [
    {"name": "massive", "h1": "clamp(48px,8vw,108px)", "h2": "clamp(32px,5vw,64px)", "track": "-0.04em", "lh": "1.02"},
    {"name": "balanced", "h1": "clamp(44px,7vw,92px)", "h2": "clamp(30px,4.5vw,58px)", "track": "-0.03em", "lh": "1.05"},
    {"name": "condensed", "h1": "clamp(40px,6vw,80px)", "h2": "clamp(28px,4vw,52px)", "track": "-0.02em", "lh": "1.1"},
    {"name": "editorial", "h1": "clamp(42px,6.5vw,88px)", "h2": "clamp(28px,4vw,54px)", "track": "-0.015em", "lh": "1.08"},
]


def _idx(seed, salt, n):
    h = hashlib.sha256(f"{seed}|{salt}".encode()).hexdigest()
    return int(h, 16) % n


# niche design prefs come from the central registry (niches.py) — one source of truth.
NICHE_PREFS = niches.DESIGN_PREFS


def _wpick(items, seed, salt, key_fn, prefs, extra):
    """Pick from items, preferring those whose text matches niche prefs + extra style bias.
    Falls back to pure seed pick when nothing matches (no niche) → variety preserved."""
    want = [w.lower() for w in (list(prefs) + list(extra))]
    scored = [(sum(1 for w in want if w in key_fn(it).lower()), it) for it in items]
    mx = max(s for s, _ in scored)
    tier = [it for s, it in scored if s == mx]
    return tier[_idx(seed, salt, len(tier))]


def pick(business_name, date=None, niche=None, extra_tags=None):
    """Deterministic, niche-weighted design system for this business+date."""
    date = date or datetime.date.today().isoformat()
    seed = f"{business_name}::{date}::{niche or ''}"
    key = niches.resolve(niche)
    p = NICHE_PREFS.get(key, {})
    extra = extra_tags or []
    return {
        "seed": seed,
        "font": _wpick(FONTS, seed, "font", lambda f: f.get("mood", ""), p.get("font", []), extra),
        "palette": _wpick(PALETTES, seed, "palette", lambda x: x["name"] + " " + x["scheme"], p.get("scheme", []), extra),
        "layout": _wpick(LAYOUTS, seed, "layout", lambda l: l["name"], p.get("layout", []), extra),
        "anim": ANIM_PACKS[_idx(seed, "anim", len(ANIM_PACKS))],
        "signature": SIGNATURES[_idx(seed, "sig", len(SIGNATURES))],
        "type_scale": TYPE_SCALES[_idx(seed, "type", len(TYPE_SCALES))],
    }


def to_prompt_block(ds):
    """Render the DNA as the DESIGN/FONTS/COLORS/ANIMATION block to inject into the master prompt."""
    f, p, ts = ds["font"], ds["palette"], ds["type_scale"]
    return f"""DESIGN DIRECTION: {ds['layout']['name']} — {ds['layout']['hero']}. Mood: {f['mood']}.
SIGNATURE MOVE (make it memorable): {ds['signature']}.

FONTS (Google Fonts, link exactly): {f['href']}
  Heading = "{f['head']}"  Body = "{f['body']}". NEVER Arial/Helvetica/Times/system-ui for headings.

TYPE SCALE ({ts['name']}): h1 {ts['h1']} letter-spacing {ts['track']} line-height {ts['lh']};
  h2 {ts['h2']} {ts['track']}; negative tracking on h1/h2 is NON-NEGOTIABLE.

COLOR THEME "{p['name']}" ({p['scheme']} scheme), use 60% bg / 30% primary / 10% accent:
  --bg {p['bg']}; --surface {p['surface']}; --primary {p['primary']}; --accent {p['accent']} (CTA only);
  --text {p['text']}; --muted {p['muted']}; --border {p['border']}.

ANIMATION PACK "{ds['anim']['name']}" — implement, working: {ds['anim']['emphasis']}.
  ALWAYS @media (prefers-reduced-motion: reduce) to damp all motion."""


if __name__ == "__main__":
    for name, niche in [("Brewhaus Coffee Co.", "coffee shop"),
                        ("IronPeak Fitness", "gym"),
                        ("BrightSmile Dental", "dental")]:
        d = pick(name, niche=niche)
        print(f"\n{'='*60}\n{name}  ({niche})")
        print(f"  font      : {d['font']['head']} / {d['font']['body']}  ({d['font']['mood']})")
        print(f"  palette   : {d['palette']['name']}  [{d['palette']['scheme']}]  {d['palette']['primary']}/{d['palette']['accent']}")
        print(f"  layout    : {d['layout']['name']}")
        print(f"  animation : {d['anim']['name']}")
        print(f"  signature : {d['signature']}")
        print(f"  typescale : {d['type_scale']['name']}")
