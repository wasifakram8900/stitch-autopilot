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
  2 HERO: min-height 100vh, centered; eyebrow badge with the star rating; huge H1 (word-split animated);
    tagline; two CTAs (filled "Book Appointment"->showPage('book') + ghost "View Services" scroll). NO photo.
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

IMAGES — NON-NEGOTIABLE: this is a NO-PHOTO premium build. Use styled CSS/gradient/icon visuals only.
  NEVER lh3.googleusercontent.com/aida-public, NEVER gstatic.com/labs-code, NEVER unsplash/picsum/placeholder
  services, NEVER invent an image URL, NEVER generate AI images. Any image slot -> styled placeholder div.

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


def _fix_block(fixes):
    if not fixes:
        return ""
    return ("MUST FIX — the previous attempt FAILED automated QA. Address ALL of these, they are "
            "mandatory:\n" + "\n".join(f"- {f}" for f in fixes))


def build_prompt(b, date=None, salt="", fixes=None):
    """salt re-seeds the DNA on a regen so a failed look changes. fixes = QA feedback to force-correct."""
    date = (date or datetime.date.today().isoformat()) + (f"#{salt}" if salt else "")
    niche = b.get("niche")
    seed_name = b["name"] + (f"#{salt}" if salt else "")
    # designer team: scout references -> style bias -> niche-weighted look + niche effects + copy
    refs = reference_scout.select(niche, seed=seed_name)
    bias = reference_scout.style_bias(refs)
    ds = design_dna.pick(b["name"], date=date, niche=niche, extra_tags=bias)
    bundle = asset_lib.bundle(b["name"], date=date, niche=niche)
    copy = copywriter.pick(b, seed=seed_name)
    parts = [SKELETON]
    if fixes:
        parts.append(_fix_block(fixes))
    if refs:
        parts.append(reference_scout.to_block(refs))
    parts += [design_dna.to_prompt_block(ds), asset_lib.compose_block(bundle),
              copywriter.to_block(copy, b), _data_block(b)]
    markers = list(dict.fromkeys(asset_lib.markers(bundle) + CORE_FUNCS))
    return {"prompt": "\n\n".join(parts), "ds": ds, "bundle": bundle,
            "markers": markers, "copy": copy, "refs": [r["name"] for r in refs]}


if __name__ == "__main__":
    import businesses
    out = build_prompt(businesses.BUSINESSES[1])  # IronPeak
    print(f"prompt chars={len(out['prompt'])}  markers={len(out['markers'])}")
    print(f"font={out['ds']['font']['head']}/{out['ds']['font']['body']}  palette={out['ds']['palette']['name']}")
    print("\n----- first 1400 chars -----\n", out["prompt"][:1400])
    print("\n----- data block -----\n", _data_block(businesses.BUSINESSES[1]))
