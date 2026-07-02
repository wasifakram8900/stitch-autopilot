"""
Brief Compiler — assembles the per-site Stitch prompt from 4 parts:
  1. SKELETON   : invariant structure + full booking spec + JS contract + image/output rules
  2. DNA block  : design_dna.to_prompt_block() — unique fonts / colors / type / layout / anim pack
  3. EFFECTS    : asset_lib.compose_block() — niche-weighted signature effects, verbatim CSS/JS
  4. DATA block : the business facts (services / reviews / hours), "use exactly, omit if missing"

Returns {prompt, ds, bundle, markers} — markers feed the technical-team QA gate.
"""
import datetime
import design_dna
import asset_lib
import copywriter
import reference_scout
import playbooks
import images_agent

asset_lib.load_external()   # merge bulk-imported packs once

# Functions every site MUST define (the booking app contract). QA greps these.
CORE_FUNCS = [
    "showPage", "toggleMobileMenu", "scrollToSection", "splitWords", "initReveal", "animateCounter",
    "toggleService", "updateSummary", "selectDate", "selectTime", "renderCalendar", "prevMonth",
    "nextMonth", "confirmBooking", "resetBooking", "toggleFaq",
]

SKELETON = """Build ONE complete premium single-page local-business website WITH a fully working,
hand-coded booking system, as a SINGLE self-contained index.html. No separate pages, no backend,
no external JS libraries except Tailwind CDN and Lucide Icons CDN.

TWO VIEWS toggled by JS (no page reload, no href="#", no alert()):
  Home  -> id="page-home"   Booking -> id="page-book"   (both class="page-view")
Implement EXACTLY:
  function showPage(id){document.querySelectorAll('.page-view').forEach(p=>p.style.display='none');
    document.getElementById('page-'+id).style.display='block';window.scrollTo({top:0,behavior:'smooth'});}
"Book"/"Book Now"/"Book Appointment"/"Book This" -> showPage('book'). "Back to Home" -> showPage('home').

ICONS: Lucide only (stroke-width 1.5), CDN <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>,
call lucide.createIcons() at end of body. SPACING: strict 8pt grid; container max-width 1200px, 80px side
padding -> 20px mobile; section padding 120px -> 64px mobile; card radius 16px; button radius 8px.

HOME SECTIONS, in this exact order (every one present):
  1 STICKY NAVBAR: logo (showPage('home')) + nav links (.nav-link smooth-scroll to sections) + primary
    "Book Now" button -> showPage('book'); mobile hamburger -> full-screen overlay via toggleMobileMenu().
  2 HERO: min-height 100vh; eyebrow badge with the star rating; huge H1 (word-split animated) whose text is
    the EXACT "HERO HEADLINE" from the COPY section (do NOT invent your own headline); tagline/subtext;
    two CTAs (filled "Book Appointment"->showPage('book') + ghost "View Services" scroll). Follow the ART
    DIRECTION hero treatment (use the provided hero PHOTO as a full-bleed background when one is given).
  3 ABOUT: label + h2 + 2-3 sentence bio + one stat callout. scroll reveal.
  4 SERVICES + PRICING: label + h2 + responsive grid, ONE CARD PER SERVICE from DATA (icon, exact name,
    short desc, exact price, duration, "Book This"->showPage('book')).
  5 REVIEWS: overall "[rating] · [count] Reviews" badge; ALL reviews as cards (stars, italic text, bold
    name, date) using EXACT data.
  6 LOCATION + CONTACT: two-col; Google Maps iframe src="https://maps.google.com/maps?q=ENCODED+ADDRESS&output=embed"
    (NEVER a maps API key); address, phone tel:, hours by day; Directions/Call buttons.
  7 FAQ: 4-6 niche questions, accordion via toggleFaq() (one open at a time). scroll reveal.
  8 FOOTER: business name + tagline, quick links, © current year + business name.

BOOKING PAGE id="page-book" (same file, full-page view NOT a modal, same fonts/colors):
  HEADER: "Back to Home"->showPage('home'); business name; "Book Your Appointment" h1; star badge.
  STEP 1 SELECT SERVICES: every service as a selectable card (exact name/price/duration); click toggles
    selected (accent border+tint); selectedServices=[] multi-select; updateSummary() on toggle; inline error space.
  STEP 2 SELECT DATE: pure-JS calendar, month/year header + prev/next nav, correct weekday offsets, past
    dates greyed & non-clickable, selected highlighted; renderCalendar(year,month), prevMonth(), nextMonth().
  STEP 3 SELECT TIME: time-slot buttons grouped Morning/Afternoon/Evening; one selectable; selectTime() updates summary.
  STEP 4 YOUR INFORMATION: Full Name id="input-name" required; Phone id="input-phone" type tel required;
    Email id="input-email" type email required; Special Requests id="input-notes" textarea optional.
  LIVE BOOKING SUMMARY: sticky sidebar (desktop); selected services + prices, total duration, subtotal, tax,
    big TOTAL; selected date/time ("—" if unset); default "No services selected · $0.00".
  CONFIRM BUTTON "Confirm Booking — $[live total]" onclick confirmBooking(): inline-validate (no service ->
    error under step1; no date -> error under calendar; no time -> error under slots; empty name/phone/email ->
    red border + inline error); if valid hide form -> confirmation screen. NEVER alert().
  CONFIRMATION SCREEN: "You're all set, [firstName]!" (actual first name) + summary card + "Add to Google
    Calendar" link (calendar.google.com/calendar/render?action=TEMPLATE...) + "Book Another"->resetBooking().

ALL JS FUNCTIONS required (implement every one): %s; on DOMContentLoaded ->
  splitWords(#page-home h1), initReveal(), renderCalendar(now), lucide.createIcons().

IMAGES: use the REAL photo URLs given in the IMAGES section below (real <img>, object-fit:cover, lazy-load,
  meaningful alt). Those are the ONLY images allowed. NEVER AI-generated images (googleusercontent/aida-public,
  gstatic.com/labs-code), NEVER placeholder services (picsum/placehold/dummyimage), NEVER invent an image URL.
  If the IMAGES section says no photo is available, build a premium CSS-art hero (layered gradient + texture),
  never a flat color box. No logo images.

OUTPUT RULES: single index.html; Lucide + Google Fonts in <head>; all JS at bottom before </body>; mobile-first
  works at 375px; every button has a real onclick; booking is full-page not modal; calendar navigates months;
  summary updates live; validation inline (never alert()); confirmation uses the actual first name.""" % ", ".join(CORE_FUNCS)


def _data_block(b):
    L = ["DATA — use EXACTLY, invent nothing, omit any missing field's UI:",
         f"BUSINESS NAME: {b['name']}"]
    for k, label in [("type", "BUSINESS TYPE"), ("tagline", "TAGLINE"), ("address", "ADDRESS"),
                     ("location", "LOCATION"), ("phone", "PHONE"), ("email", "EMAIL"),
                     ("hours", "HOURS"), ("rating", "GOOGLE RATING"), ("requirements", "SPECIAL REQUIREMENTS")]:
        if b.get(k):
            L.append(f"{label}: {b[k]}")
    svc = b.get("services") or []
    if svc:
        L.append("SERVICES (one card each):")
        for i, s in enumerate(svc, 1):
            dur = f" {s['duration']}" if s.get("duration") and s["duration"] != "—" else ""
            L.append(f"  {i} {s['name']} — {s.get('price','')}{(' · '+dur.strip()) if dur else ''} — {s.get('desc','')}")
    rev = b.get("reviews") or []
    if rev:
        L.append(f"TOTAL REVIEWS: {len(rev)}")
        L.append("REVIEWS (show all):")
        for i, r in enumerate(rev, 1):
            L.append(f"  {i} {r['name']} {r.get('stars',5)}/5 ({r.get('date','')}) \"{r['text']}\"")
    return "\n".join(L)


def _fix_block(fixes, surgical=False):
    if not fixes:
        return ""
    head = ("SURGICAL FIX — the previous attempt was CLOSE but failed automated QA on the items below. "
            "KEEP the existing design, layout, colors, fonts, copy and all passing sections EXACTLY as they were. "
            "Change ONLY what is needed to satisfy these — do not redesign:") if surgical else (
            "MUST FIX — the previous attempt FAILED automated QA. Address ALL of these, they are mandatory:")
    return head + "\n" + "\n".join(f"- {f}" for f in fixes)


def build_prompt(b, date=None, salt="", fixes=None, surgical=False):
    """salt re-seeds the DNA on a regen so a failed look changes (full re-roll).
    surgical=True keeps the same DNA (pass salt="") and patches only the failing gates."""
    date = (date or datetime.date.today().isoformat()) + (f"#{salt}" if salt else "")
    niche = b.get("niche")
    seed_name = b["name"] + (f"#{salt}" if salt else "")
    # designer team: scout references -> style bias -> niche-weighted look + niche effects + copy
    refs = reference_scout.select(niche, seed=seed_name)
    bias = reference_scout.style_bias(refs)
    ds = design_dna.pick(b["name"], date=date, niche=niche, extra_tags=bias)
    bundle = asset_lib.bundle(b["name"], date=date, niche=niche)
    copy = copywriter.pick(b, seed=seed_name)
    pb = playbooks.get(niche)                       # designer brain: per-niche art direction
    imgs = images_agent.resolve(b, ds)              # real photos: lead's own -> curated stock
    parts = [SKELETON]
    if fixes:
        parts.append(_fix_block(fixes, surgical=surgical))
    parts.append(playbooks.to_block(pb, b))         # ART DIRECTION frames everything below
    if refs:
        parts.append(reference_scout.to_block(refs))
    parts += [design_dna.to_prompt_block(ds), asset_lib.compose_block(bundle),
              images_agent.to_block(imgs, b, ds), copywriter.to_block(copy, b), _data_block(b)]
    markers = list(dict.fromkeys(asset_lib.markers(bundle) + CORE_FUNCS))
    return {"prompt": "\n\n".join(parts), "ds": ds, "bundle": bundle, "images": imgs,
            "markers": markers, "copy": copy, "refs": [r["name"] for r in refs]}


if __name__ == "__main__":
    import businesses
    out = build_prompt(businesses.BUSINESSES[1])  # IronPeak
    print(f"prompt chars={len(out['prompt'])}  markers={len(out['markers'])}")
    print(f"font={out['ds']['font']['head']}/{out['ds']['font']['body']}  palette={out['ds']['palette']['name']}")
    print("\n----- first 1400 chars -----\n", out["prompt"][:1400])
    print("\n----- data block -----\n", _data_block(businesses.BUSINESSES[1]))
