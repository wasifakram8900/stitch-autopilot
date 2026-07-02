"""
Imagery agent — the missing "real photos" the site needs to look $10k, not barren.

Resolution order (per the brief):
  1. the LEAD's OWN photos   (from the sheet/CSV: their real gym/shop — best personalization)
  2. curated FREE 4K STOCK   (Unsplash CDN, niche-matched, license-free, no attribution/logo)
  3. graceful CSS-art hero   (only if neither exists — never ship a broken <img>)

resolve(business, ds) -> {hero, gallery:[...], about, trainers:[...], source, use_images}
to_block(imgs, b, ds) -> the IMAGES section of the Stitch brief (exact URLs + rules).

NOTE: stock URLs are curated Unsplash photo IDs (very stable). On the FIRST live run, eyeball
them once — if any 404, swap the ID in NICHE_STOCK (kept trivially editable on purpose).
No API key, no network at build time — the URLs are baked.
"""
import re
import niches

def _u(pid, w=1920):
    return f"https://images.unsplash.com/photo-{pid}?auto=format&fit=crop&w={w}&q=80"

# ── curated free 4K stock per niche (Unsplash CDN, commercial-free, no logo) ─────
# GYM is the fully-curated proof niche; others fall back to archetype/keywords.
NICHE_STOCK = {
    "gym": {
        "hero":     _u("1517836357463-d25dfeac3438"),   # athlete / dark gym
        "gallery": [_u("1534438327276-14e5300c3a48", 1200),   # lifting
                    _u("1571019613454-1cb2f99b2d8b", 1200),   # class / cardio
                    _u("1526506118085-60ce8714f8c5", 1200),   # kettlebell detail
                    _u("1541534741688-6078c6bfb5c5", 1200)],  # strength
        "about":    _u("1584735935682-2f2b69dff9d2", 1400),   # coaching
        "trainers":[_u("1567013127542-490d757e51fc", 800),
                    _u("1550345332-09e3ac987658", 800)],
        "keywords": ["gym workout", "weightlifting", "fitness class", "personal trainer"],
    },
}

# archetype fallback keyword sets (used when a niche has no curated stock table)
ARCHETYPE_KEYWORDS = {
    "fitness": ["gym", "workout", "training"], "beauty": ["salon interior", "spa", "treatment"],
    "medical": ["clinic interior", "healthcare", "professional"], "food": ["cafe interior", "food", "barista"],
    "trade": ["worker on site", "tools", "home service"], "professional": ["modern office", "team", "handshake"],
    "events": ["venue interior", "event", "celebration"], "tech": ["workspace", "team", "screens"],
}


def _lead_photos(b):
    """Prospect's own images from the lead record (sheet/CSV). Highest priority."""
    imgs = []
    v = b.get("images")
    if isinstance(v, list):
        imgs += [x for x in v if isinstance(x, str) and x.startswith("http")]
    elif isinstance(v, str):
        imgs += [x for x in re.split(r"[|,\s]+", v) if x.startswith("http")]
    for k, val in b.items():
        if re.match(r"(image|photo|img)\d*$", str(k), re.I) and isinstance(val, str) and val.startswith("http"):
            imgs.append(val)
    # dedupe, keep order
    seen, out = set(), []
    for u in imgs:
        if u not in seen:
            seen.add(u); out.append(u)
    return out


def resolve(b, ds=None, n_gallery=4):
    niche = niches.resolve(b.get("niche"))
    lead = _lead_photos(b)
    stock = NICHE_STOCK.get(niche, {})
    arch = (niches.NICHES.get(niche) or {}).get("a")
    keywords = stock.get("keywords") or ARCHETYPE_KEYWORDS.get(arch) or ["storefront", "team"]

    # fill slots: lead photos first, then stock
    pool = list(lead)
    def take():
        return pool.pop(0) if pool else None

    hero = take() or stock.get("hero")
    gallery = []
    while len(gallery) < n_gallery:
        g = take() or (stock.get("gallery", [])[len(gallery)] if len(gallery) < len(stock.get("gallery", [])) else None)
        if not g:
            break
        gallery.append(g)
    about = take() or stock.get("about")
    trainers = stock.get("trainers", []) if niche == "gym" else []

    used_lead = bool(lead)
    used_stock = bool(stock) and (not lead or len(lead) < 1 + n_gallery)
    source = "lead+stock" if (used_lead and used_stock) else ("lead" if used_lead else ("stock" if stock else "none"))
    return {"hero": hero, "gallery": [g for g in gallery if g], "about": about,
            "trainers": trainers, "keywords": keywords, "source": source,
            "use_images": bool(hero)}


def to_block(imgs, b=None, ds=None):
    if not imgs.get("use_images"):
        # no real photos available → tasteful CSS-art hero, still premium (playbook drives it)
        return ("IMAGES: no real photo available — build a premium CSS-art hero (layered brand-color "
                "gradient + subtle texture), NOT a flat color box. Do NOT use AI-generated or "
                "placeholder-service images. No logo.")
    accent = (ds or {}).get("palette", {}).get("accent", "the accent color")
    L = ["IMAGES — use these EXACT photo URLs (real <img>, object-fit:cover, lazy-load, meaningful alt). "
         "These are the ONLY images allowed. Do NOT use AI-generated images (googleusercontent/aida, "
         "gstatic labs), placeholder services (placehold/picsum/dummyimage), or invented URLs. NO logo images.",
         f"HERO (full-bleed 100vh background, dark gradient scrim for text): {imgs['hero']}"]
    for i, g in enumerate(imgs["gallery"], 1):
        L.append(f"SERVICE/CLASS or GALLERY image {i}: {g}")
    if imgs.get("about"):
        L.append(f"ABOUT section supporting image: {imgs['about']}")
    for i, t in enumerate(imgs.get("trainers", []), 1):
        L.append(f"TRAINER/TEAM photo {i}: {t}")
    L.append(f"COHESION: apply a consistent subtle dark/{accent} gradient overlay on all photos so they "
             f"read as ONE art-directed set; keep angles/crops consistent (object-fit:cover, no stretching).")
    return "\n".join(L)


if __name__ == "__main__":
    import businesses
    for b in businesses.BUSINESSES:
        im = resolve(b)
        print(f"\n{b['name']} ({b['niche']}) source={im['source']} use_images={im['use_images']}")
        print(f"  hero: {im['hero']}")
        print(f"  gallery: {len(im['gallery'])}  about: {'yes' if im['about'] else 'no'}  trainers: {len(im['trainers'])}")
    # lead-photos-first demo
    demo = {"name": "Real Gym", "niche": "gym", "images": ["http://x/own1.jpg", "http://x/own2.jpg"]}
    print("\nlead-with-own-photos:", resolve(demo)["source"], "->", resolve(demo)["hero"])
