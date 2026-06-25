"""
Copywriter agent — deterministic, niche-aware copy so sites stop sounding generic.
NO LLM. Seeded variation = different wording per business, same quality bar.

pick(business, seed) -> {eyebrow, headline, cta, about, faq:[(q,a)...]}
brief_compiler injects this as a COPY block ("use these exact words").
"""
import hashlib

DEFAULT = {
    "eyebrow": ["TRUSTED BY LOCALS", "BOOK IN UNDER A MINUTE", "REAL SERVICE, REAL RESULTS"],
    "headlines": ["Service you'll actually recommend.", "Done right, the first time.", "Local, trusted, and ready when you are."],
    "cta": "Book Now",
    "about": "We're a local team obsessed with doing right by our customers — clear pricing, real care, and work we stand behind.",
    "faq": [("How do I book?", "Tap any “Book” button and pick a time — it takes under a minute."),
            ("Where are you located?", "See the map and address in the contact section below."),
            ("What are your hours?", "Listed in the contact section — we keep it current."),
            ("How do I reach you?", "Call or email us using the details below; we reply fast.")],
}

NICHE_COPY = {
    "gym": {
        "eyebrow": ["RESULTS WITHOUT GUESSWORK", "STRENGTH · CONDITIONING · COMMUNITY", "COACHED, NOT CROWDED"],
        "headlines": ["Get strong. Stay strong.", "Train with a plan that actually works.", "Your strongest self starts here."],
        "cta": "Book a Free Session",
        "about": "We coach busy people to move better and get measurably stronger — no fads, no guesswork. Just programmed training that fits your life and coaches who actually watch your reps.",
        "faq": [("Do I need experience?", "No. We start with an assessment and meet you exactly at your level."),
                ("How long are sessions?", "45–60 minutes, built to fit a workday."),
                ("Can I try before I commit?", "Yes — your first session is free, no pressure."),
                ("Do you help with nutrition?", "Optional macro-based coaching is available alongside training.")],
    },
    "dental": {
        "eyebrow": ["GENTLE · MODERN · FAMILY-FRIENDLY", "NEW PATIENTS WELCOME", "DENTISTRY WITHOUT THE DREAD"],
        "headlines": ["A dentist you'll actually look forward to.", "Healthy smiles, gently done.", "Modern care for your whole family."],
        "cta": "Book Appointment",
        "about": "We blend gentle, modern dentistry with honest, plain-English care. From routine cleanings to cosmetic work, we'll keep you comfortable and clearly informed at every step.",
        "faq": [("Do you take my insurance?", "We work with most major plans — ask us and we'll verify your coverage."),
                ("Are you accepting new patients?", "Yes, and new-patient visits are easy to book online."),
                ("Does it hurt?", "We prioritize comfort with gentle techniques and clear communication."),
                ("Do you offer emergency visits?", "Yes — same-day care for pain or breaks when available.")],
    },
    "coffee": {
        "eyebrow": ["SMALL-BATCH · LOCALLY ROASTED", "POURED WITH CARE", "YOUR THIRD PLACE"],
        "headlines": ["Coffee worth slowing down for.", "Roasted with intent, poured with care.", "Your new favorite morning."],
        "cta": "Order Online",
        "about": "We roast in small batches and brew every cup to order. Whether you're grabbing a pour-over on the way to work or settling in for the afternoon, you're always welcome here.",
        "faq": [("Do you sell beans to take home?", "Yes — fresh-roasted, whole or ground to your preference."),
                ("Can I order ahead?", "Absolutely, use the order button up top to skip the line."),
                ("Do you cater events?", "Yes — our coffee cart and barista can come to you."),
                ("Are you laptop-friendly?", "Plenty of seating and outlets — stay as long as you like.")],
    },
}


def _i(seed, salt, n):
    return int(hashlib.sha256(f"{seed}|{salt}".encode()).hexdigest(), 16) % n if n else 0


def pick(b, seed=""):
    niche = (b.get("niche") or "").lower().split()[0] if b.get("niche") else ""
    c = NICHE_COPY.get(niche, DEFAULT)
    seed = seed or b.get("name", "")
    return {
        "eyebrow": c["eyebrow"][_i(seed, "eyebrow", len(c["eyebrow"]))],
        "headline": b.get("tagline") or c["headlines"][_i(seed, "head", len(c["headlines"]))],
        "subhead": c["headlines"][_i(seed, "sub", len(c["headlines"]))],
        "cta": c["cta"],
        "about": c["about"],
        "faq": c["faq"],
    }


def to_block(copy, b):
    faq = "\n".join(f"  Q: {q}\n  A: {a}" for q, a in copy["faq"])
    return (f"COPY — use these EXACT words (this is the brand voice, do not rephrase):\n"
            f"EYEBROW BADGE: {copy['eyebrow']}\n"
            f"HERO HEADLINE: {copy['headline']}\n"
            f"HERO SUBTEXT: {copy['subhead']}\n"
            f"PRIMARY CTA LABEL (every Book button): {copy['cta']}\n"
            f"ABOUT PARAGRAPH: {copy['about']}\n"
            f"FAQ (use these questions + answers):\n{faq}")


if __name__ == "__main__":
    import businesses
    for b in businesses.BUSINESSES:
        c = pick(b)
        print(f"\n{b['name']} ({b['niche']})\n  eyebrow={c['eyebrow']}\n  headline={c['headline']}\n  cta={c['cta']}")
