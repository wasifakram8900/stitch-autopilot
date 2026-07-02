"""
Design Playbooks — the DESIGNER BRAIN the factory was missing. NO LLM.

QA gates enforce "not broken" (all sections + working booking). Playbooks enforce
"looks like $10k" — per-niche ART DIRECTION: what a premium site in this niche actually
looks like (hero treatment, section order + purpose, imagery, color mood, type, copy
voice, and the cheap-looking mistakes to AVOID). Injected into the Stitch brief as strong
direction so the output aims high instead of landing on a generic dark-box-with-lime.

get(niche) -> resolved playbook (specific niche > archetype default > DEFAULT).
to_block(pb, b) -> the ART DIRECTION section of the prompt.

Start: GYM is fully built out as the proof niche. Others inherit a solid archetype default
until each is deepened (roll-out order in ROADMAP).
"""
import niches

# ── DEFAULT (any niche with no specific playbook still gets real direction) ──────
DEFAULT = {
    "positioning": "premium, trustworthy local business — modern, confident, not templated",
    "hero": ("Full-bleed hero: a real photograph (provided) with a dark-to-transparent gradient "
             "scrim so the headline is readable; large confident headline OVERLAID on the image "
             "(not a plain colored box); one primary CTA + one ghost CTA; a small rating/social-proof "
             "badge. The hero image must fill the viewport (object-fit:cover), no letterboxing."),
    "sections": [
        "sticky nav (transparent over hero → solid on scroll)",
        "HERO with real background image + overlaid headline",
        "trust bar (rating + review count + years/《clients》 — one line, quiet)",
        "value props: 3 benefit cards with icons (why choose us)",
        "services/offerings grid — one card per service, each with a small relevant image or icon",
        "about/story with a real supporting image beside the text",
        "social proof: testimonials as cards (name, result, stars)",
        "location + contact (map, hours, phone, directions)",
        "FAQ accordion",
        "final CTA band (contrasting background) + footer",
    ],
    "color": "one dominant brand color + ONE saturated accent used only for CTAs; strong contrast; avoid muddy mid-tones",
    "type": "a distinctive display face for headings (never system-ui/Arial) + a clean grotesk body; big type scale, tight heading tracking",
    "imagery": {"keywords": ["storefront", "team", "detail"], "mood": "bright, real, professional"},
    "copy_voice": "clear, warm, confident; benefit-led headlines; no lorem, no 'Welcome to our website'",
    "avoid": ["empty gradient hero with no photo", "thin light fonts on headings", "centered everything",
              "stocky fake-smiling clip-art", "walls of grey text", "tiny hero type"],
}

# ── GYM — fully built proof niche ($10k reference: dark, athletic, high-energy) ──
GYM = {
    "positioning": ("high-performance, premium strength gym. Feels exclusive, intense, results-driven "
                    "— like a $10k Webflow fitness site, not a discount chain. Energy + credibility."),
    "hero": ("FULL-BLEED dark athletic PHOTO hero (100vh): a real athlete mid-lift / gritty gym shot "
             "(provided image) with a bottom-up black gradient scrim (rgba 0→.85). MASSIVE uppercase "
             "condensed headline overlaid bottom-left, tight tracking, one word accent-colored. Eyebrow "
             "with the star rating. Primary CTA 'Start Free Session' (accent, bold) + ghost 'View Classes'. "
             "A vertical member-count / rating stat pinned in a corner. NO plain colored hero box — the "
             "photo IS the hero."),
    "sections": [
        "sticky nav — transparent over hero, solid+blur on scroll; bold logo, right-aligned CTA",
        "HERO — full-bleed athlete photo + overlaid condensed headline + 2 CTAs + rating",
        "moving stat/marquee band — 'MEMBERS · CLASSES/WK · TRAINERS · YEARS' big numbers, count-up",
        "value props — 3-4 cards: expert coaching / real community / proven results / flexible hours (icon + short punch)",
        "programs & classes — grid of classes (Strength, HIIT, Personal Training…), EACH with its own action image, name, 1-liner, 'Book This'",
        "transformation / results — before-after or member-result cards with a big % or lbs number; proof, not fluff",
        "trainers — grid of coach cards: photo, name, specialty, 1-line bio; hover lift",
        "pricing — 2-3 membership tiers, middle tier highlighted 'Most Popular', clear price + perks + CTA",
        "testimonials — member quote + name + result + stars, with a small photo",
        "class schedule — a weekly timetable (days × time slots) styled as a clean table",
        "urgency CTA band — dark full-width 'Claim Your Free Week' + big button",
        "location + hours + contact (map, phone, directions)",
        "FAQ accordion (membership, freeze, trial, beginners)",
        "footer — bold logo, quick links, hours, socials",
    ],
    "color": ("DARK base (near-black #0d0f0c/#101113) + ONE electric accent (acid lime, safety orange, or "
              "blood red — pick one, use ONLY for CTAs/one headline word/stats). High contrast, punchy. "
              "NEVER pastel, never light-and-airy for a strength gym."),
    "type": ("CONDENSED/BLACK uppercase display for headings (Bebas Neue / Anton / Archivo Black / Oswald), "
             "tight/negative tracking, HUGE (clamp up to ~120px h1). Clean grotesk body (Inter/Work Sans). "
             "Real hierarchy — the display face must dominate the hero, not the body font."),
    "imagery": {
        "keywords": ["gym workout", "weightlifting", "athlete training", "fitness class", "dumbbells", "personal trainer"],
        "mood": "gritty, dramatic low-key lighting, sweat, motion; monochrome-leaning with the accent popping; ACTION not posed",
        "shots": ["hero: athlete mid-lift, dark", "class: group HIIT/strength action", "detail: barbell/kettlebell close-up", "trainer: coaching a client"],
    },
    "copy_voice": ("imperative, punchy, confident, short. 'TRAIN HARD. GET STRONG.' 'BUILT DIFFERENT.' "
                   "'NO EXCUSES, JUST REPS.' Benefit + intensity. Use the provided hero headline verbatim — "
                   "do NOT invent bland copy like 'Secure your session' or 'Welcome to our gym'."),
    "avoid": ["empty gradient/colored hero with no athlete photo", "thin/light fonts on a strength brand",
              "pastel or low-contrast palettes", "generic stocky smiling gym selfie", "small hero headline",
              "no imagery in the classes/trainers sections", "bland copy ('Secure your session')"],
}

PLAYBOOKS = {"gym": GYM}

# archetype-level defaults so every niche gets *something* better than nothing until deepened
ARCHETYPE_DEFAULT = {
    "fitness": GYM,   # yoga/gym share the athletic playbook until yoga gets its own (softer variant)
}


def get(niche):
    key = niches.resolve(niche)
    if key in PLAYBOOKS:
        return PLAYBOOKS[key]
    arch = (niches.NICHES.get(key) or {}).get("a")
    if arch in ARCHETYPE_DEFAULT:
        return ARCHETYPE_DEFAULT[arch]
    return DEFAULT


def to_block(pb, b=None):
    secs = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(pb["sections"]))
    avoid = "\n".join(f"  ✗ {a}" for a in pb["avoid"])
    img = pb["imagery"]
    return (
        "ART DIRECTION — this is the DESIGN BAR (make it look like a $10k custom site, not a template):\n"
        f"POSITIONING: {pb['positioning']}\n\n"
        f"HERO: {pb['hero']}\n\n"
        f"SECTION PLAN (in this order, each with real purpose + imagery):\n{secs}\n\n"
        f"COLOR: {pb['color']}\n"
        f"TYPOGRAPHY: {pb['type']}\n"
        f"IMAGERY MOOD: {img['mood']}. Subjects: {', '.join(img['keywords'])}.\n"
        f"COPY VOICE: {pb['copy_voice']}\n\n"
        f"DO NOT (these make it look cheap):\n{avoid}"
    )


if __name__ == "__main__":
    for n in ["gym", "yoga", "dental", "coffee"]:
        pb = get(n)
        print(f"\n{'='*64}\n{n}  ->  {'GYM playbook' if pb is GYM else ('DEFAULT' if pb is DEFAULT else 'archetype')}")
        print(f"  positioning: {pb['positioning'][:80]}...")
        print(f"  sections: {len(pb['sections'])}")
    print("\n--- sample gym art-direction block ---\n")
    print(to_block(get("gym"))[:900], "...")
