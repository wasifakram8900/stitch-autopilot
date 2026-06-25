"""
Copywriter agent — deterministic, niche-aware copy so sites stop sounding generic.
NO LLM. Seeded variation = different wording per business, same quality bar.

pick(business, seed) -> {eyebrow, headline, cta, about, faq:[(q,a)...]}
brief_compiler injects this as a COPY block ("use these exact words").
"""
import hashlib
import niches

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

NICHE_COPY = niches.COPY   # central registry — 40+ local-business niches


def _i(seed, salt, n):
    return int(hashlib.sha256(f"{seed}|{salt}".encode()).hexdigest(), 16) % n if n else 0


def pick(b, seed=""):
    c = NICHE_COPY.get(niches.resolve(b.get("niche")), DEFAULT)
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
