"""
Technical team — gates a generated site BEFORE deploy. Static checks (no deps) + an OPTIONAL
headless booking click-through (Playwright, used in CI). scorecard() folds them into pass/fail.

HARD gates (must pass to deploy): structure sections, booking core functions, images clean.
SOFT gates (warn, don't block): animation/effect coverage, accessibility, links.
"""
import re

# ── home sections: name -> regexes (any match = present) ────────────────────────
SECTIONS = {
    "navbar": [r"<nav", r"showPage\('home'\)"],
    "hero": [r'id=["\']page-home["\']'],
    "about": [r">\s*about", r"our story", r"who we are"],
    "services": [r">\s*services", r"our services", r"pricing"],
    "reviews": [r"review", r"testimonial", r"what .* say"],
    "contact": [r"contact", r"location", r"maps\.google", r"tel:"],
    "faq": [r"faq", r"frequently asked", r"toggleFaq"],
    "footer": [r"<footer", r"&copy;", r"©"],
    "booking_page": [r'id=["\']page-book["\']'],
}
# booking JS that MUST exist for the flow to actually work
BOOKING_CORE = ["showPage", "renderCalendar", "confirmBooking", "toggleService",
                "selectDate", "selectTime", "updateSummary"]
BOOKING_FULL = BOOKING_CORE + ["prevMonth", "nextMonth", "resetBooking", "splitWords", "initReveal"]
# banned image sources (AI / stock / placeholder) — must be ZERO
BANNED_IMG = [r"googleusercontent\.com/aida", r"gstatic\.com/labs-code", r"unsplash\.com",
              r"picsum\.photos", r"placeholder\.com", r"placehold\.co", r"via\.placeholder",
              r"loremflickr", r"dummyimage"]


def _has(html, pats):
    return any(re.search(p, html, re.I) for p in pats)


def structure(html):
    found = {name: _has(html, pats) for name, pats in SECTIONS.items()}
    missing = [k for k, v in found.items() if not v]
    return {"ok": not missing, "score": sum(found.values()) / len(found),
            "missing": missing}


def booking(html):
    core = {fn: (fn + "(") in html or (fn + " =") in html or ("function " + fn) in html for fn in BOOKING_CORE}
    full = {fn: (fn + "(") in html or (fn + " =") in html or ("function " + fn) in html for fn in BOOKING_FULL}
    core_missing = [k for k, v in core.items() if not v]
    return {"ok": not core_missing, "score": sum(full.values()) / len(full),
            "core_missing": core_missing,
            "full_missing": [k for k, v in full.items() if not v]}


def images(html):
    hits = [p for p in BANNED_IMG if re.search(p, html, re.I)]
    return {"ok": not hits, "score": 1.0 if not hits else 0.0, "banned_hits": hits}


def animation(html, expected_markers=None):
    base = ["IntersectionObserver", "splitWords", "prefers-reduced-motion"]
    exp = list(dict.fromkeys(base + (expected_markers or [])))
    present = {m: (m in html) for m in exp}
    miss = [m for m, v in present.items() if not v]
    return {"ok": sum(present.values()) / len(exp) >= 0.7, "score": sum(present.values()) / len(exp),
            "missing": miss[:12], "missing_count": len(miss)}


def accessibility(html):
    checks = {
        "lang": bool(re.search(r"<html[^>]+lang=", html, re.I)),
        "viewport": "width=device-width" in html,
        "h1": bool(re.search(r"<h1", html, re.I)),
        "title": bool(re.search(r"<title>", html, re.I)),
        "reduced_motion": "prefers-reduced-motion" in html,
        "no_zoom_block": "user-scalable=no" not in html and "maximum-scale=1" not in html,
    }
    return {"ok": sum(checks.values()) >= 5, "score": sum(checks.values()) / len(checks),
            "fails": [k for k, v in checks.items() if not v]}


def links(html):
    dead = len(re.findall(r'href=["\']#["\']', html))
    alerts = len(re.findall(r"\balert\s*\(", html))
    return {"ok": dead == 0 and alerts == 0, "score": 1.0 if (dead == 0 and alerts == 0) else 0.5,
            "dead_anchors": dead, "alerts": alerts}


def booking_headless(path):
    """OPTIONAL: real click-through with Playwright (installed in CI). Returns None if unavailable."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None
    import pathlib
    url = pathlib.Path(path).resolve().as_uri()
    try:
        with sync_playwright() as p:
            br = p.chromium.launch()
            pg = br.new_page()
            errs = []
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            pg.goto(url, wait_until="networkidle", timeout=20000)
            pg.eval_on_selector_all  # noqa - ensure api loaded
            # go to booking
            pg.evaluate("showPage('book')")
            # pick first service card, a future date, a time slot
            clicked = pg.evaluate("""() => {
                const card = document.querySelector('#page-book [onclick*="toggleService"], #page-book .service-card, #page-book [data-service]');
                if(card) card.click();
                const day = [...document.querySelectorAll('#page-book [onclick*="selectDate"]')].find(d=>!d.classList.contains('disabled'));
                if(day) day.click();
                const slot = document.querySelector('#page-book [onclick*="selectTime"]');
                if(slot) slot.click();
                return {service:!!card, date:!!day, time:!!slot};
            }""")
            pg.evaluate("""() => {
                const set=(id,v)=>{const e=document.getElementById(id); if(e){e.value=v;}};
                set('input-name','Test User'); set('input-phone','5551234567'); set('input-email','t@t.com');
            }""")
            pg.evaluate("confirmBooking && confirmBooking()")
            confirmed = pg.evaluate("""() => /you're all set|all set|confirmed|booking confirmed/i.test(document.body.innerText)""")
            br.close()
            ok = bool(confirmed) and not errs
            return {"ok": ok, "score": 1.0 if ok else 0.0, "steps": clicked,
                    "confirmed": bool(confirmed), "console_errors": errs[:5]}
    except Exception as e:
        return {"ok": False, "score": 0.0, "error": str(e)[:160]}


# weights for the soft composite score (hard gates are pass/fail separately)
_WEIGHTS = {"structure": .25, "booking": .30, "images": .15, "animation": .12,
            "accessibility": .10, "links": .08}


def scorecard(html, expected_markers=None, path=None, headless=False):
    g = {
        "structure": structure(html),
        "booking": booking(html),
        "images": images(html),
        "animation": animation(html, expected_markers),
        "accessibility": accessibility(html),
        "links": links(html),
    }
    if headless and path:
        hb = booking_headless(path)
        if hb is not None:
            g["booking_headless"] = hb
    score = round(100 * sum(_WEIGHTS[k] * g[k]["score"] for k in _WEIGHTS), 1)
    # HARD gates that block deploy
    hard = {
        "structure": g["structure"]["ok"],
        "booking": g["booking"]["ok"],
        "images": g["images"]["ok"],
    }
    if "booking_headless" in g:
        hard["booking_headless"] = g["booking_headless"]["ok"]
    passed = all(hard.values())
    fixes = []
    if g["structure"]["missing"]:
        fixes.append("add missing sections: " + ", ".join(g["structure"]["missing"]))
    if g["booking"]["core_missing"]:
        fixes.append("booking broken — missing JS: " + ", ".join(g["booking"]["core_missing"]))
    if g["images"]["banned_hits"]:
        fixes.append("remove AI/stock images: " + ", ".join(g["images"]["banned_hits"]))
    if g["animation"]["missing_count"]:
        fixes.append(f"add {g['animation']['missing_count']} missing animations/effects")
    grade = "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F"
    return {"pass": passed, "score": score, "grade": grade, "hard": hard, "gates": g, "fixes": fixes}


if __name__ == "__main__":
    import sys, json
    for path in sys.argv[1:]:
        html = open(path).read()
        card = scorecard(html, path=path, headless="--headless" in sys.argv)
        print(f"\n{path}\n  PASS={card['pass']} score={card['score']} grade={card['grade']}")
        print("  hard gates:", card["hard"])
        if card["fixes"]:
            print("  fixes:", *[f"\n    - {f}" for f in card["fixes"]])
