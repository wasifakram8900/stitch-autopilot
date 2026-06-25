"""
Bulk-import asset packs -> assets/*.json (merged by asset_lib.load_external / design_dna).
FULLY OFFLINE: built-in curated tables + parametric generators. No network, no API key,
no runtime service -> honors "Stitch + our agents + GitHub only". Run:  python import_assets.py

Produces:
  assets/fonts.json    -> {"pairings":[...]}            (design_dna merges)
  assets/gradients.json-> {"gradient":[...],"background":[...]}   (asset_lib merges)
  assets/glow.json     -> {"glow":[...]}
  assets/motion.json   -> {"animation":[...],"hover":[...]}       (animate.css/Hover.css style)
Combined with the seeded combinatorics -> >10000 distinct site looks.
"""
import os, json, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets")
os.makedirs(OUT, exist_ok=True)


def _h(s):
    return int(hashlib.sha256(s.encode()).hexdigest(), 16)


# ── 1. FONTS — curated Google Fonts (static, safe weights) -> auto-paired ────────
HEADINGS = {  # font -> mood tags
    "Playfair Display": ["editorial", "elegant", "premium"], "Cormorant Garamond": ["editorial", "elegant"],
    "DM Serif Display": ["editorial", "bold"], "Libre Baskerville": ["editorial", "classic"],
    "Lora": ["editorial", "warm"], "Bodoni Moda": ["elegant", "fashion"], "Marcellus": ["elegant", "premium"],
    "Prata": ["elegant", "fashion"], "Spectral": ["editorial", "calm"], "Cardo": ["classic", "editorial"],
    "EB Garamond": ["classic", "editorial"], "Italiana": ["elegant", "fashion"], "Abril Fatface": ["bold", "display"],
    "Bebas Neue": ["bold", "loud", "industrial"], "Oswald": ["bold", "industrial"], "Anton": ["bold", "loud"],
    "Archivo Black": ["bold", "industrial"], "Righteous": ["bold", "playful"], "Teko": ["bold", "sport"],
    "Poppins": ["modern", "friendly"], "Montserrat": ["modern", "clean"], "Raleway": ["modern", "elegant"],
    "Sora": ["modern", "tech"], "Space Grotesk": ["modern", "tech"], "Syne": ["bold", "artsy"],
    "Outfit": ["modern", "clean"], "Lexend": ["modern", "calm"], "Sora ": ["modern", "tech"],
    "Josefin Sans": ["elegant", "light"], "Fjalla One": ["bold", "industrial"], "Unbounded": ["bold", "display"],
    "Epilogue": ["modern", "clean"], "Schibsted Grotesk": ["modern", "editorial"], "Hanken Grotesk": ["modern", "clean"],
    "Bricolage Grotesque": ["bold", "display"], "Instrument Serif": ["editorial", "elegant"],
}
BODIES = ["Inter", "DM Sans", "Work Sans", "Karla", "Public Sans", "Manrope",
          "Mulish", "Nunito Sans", "Source Sans 3", "Figtree", "Rubik", "Hanken Grotesk"]


def _font_href(head, body):
    h = head.strip().replace(" ", "+")
    b = body.strip().replace(" ", "+")
    return (f"https://fonts.googleapis.com/css2?family={h}:wght@400;700"
            f"&family={b}:wght@300;400;500;600&display=swap")


def gen_fonts():
    pairings = []
    i = 0
    for head, tags in HEADINGS.items():
        head = head.strip()
        # pick 3 bodies deterministically per heading -> ~108 pairings
        picks = sorted(BODIES, key=lambda b: _h(head + b))[:3]
        for body in picks:
            if body == head:
                continue
            pairings.append({"id": f"pair-{i}", "head": head, "body": body,
                             "mood": ", ".join(tags), "tags": tags, "href": _font_href(head, body)})
            i += 1
    return {"pairings": pairings}


# ── 2. GRADIENTS — parametric + gallery-structure, recolored to brand vars ───────
ANGLES = [120, 135, 160, 200, 225, 260, 300]
# famous-gradient STRUCTURES (stop count + spread), recolored on-brand (no clashing fixed hex)
GALLERY = [("dusk", 2, "soft"), ("ember", 2, "vivid"), ("mojito", 3, "soft"), ("aurora", 3, "vivid"),
           ("velvet", 2, "dark"), ("citrus", 2, "vivid"), ("slate", 2, "soft"), ("orchid", 3, "vivid"),
           ("ocean", 3, "soft"), ("sunset", 3, "vivid"), ("mist", 2, "soft"), ("noir", 2, "dark")]
TONE_MIX = {"soft": (14, 18), "vivid": (26, 34), "dark": (40, 22)}


def gen_gradients():
    grad, bg = [], []
    n = 0
    for name, stops, tone in GALLERY:
        a, b = TONE_MIX[tone]
        for ang in ANGLES:
            cid = f"grad-{name}-{ang}"
            if stops == 2:
                css = (f".{cid}{{background:linear-gradient({ang}deg,"
                       f"color-mix(in srgb,var(--primary) {a}%,var(--bg)),"
                       f"color-mix(in srgb,var(--accent) {b}%,var(--bg)));}}")
            else:
                css = (f".{cid}{{background:linear-gradient({ang}deg,"
                       f"color-mix(in srgb,var(--primary) {a}%,var(--bg)),var(--surface),"
                       f"color-mix(in srgb,var(--accent) {b}%,var(--bg)));}}")
            grad.append({"id": cid, "tags": [tone, "section"], "marker": cid,
                         "prompt": f"Section/panel background `.{cid}`: {tone} {stops}-stop brand gradient at {ang}deg.",
                         "css": css})
            n += 1
    # parametric ANIMATED mesh backgrounds (hero)
    for name, stops, tone in GALLERY[:8]:
        a, b = TONE_MIX[tone]
        cid = f"mesh-{name}"
        css = (f"@keyframes flo_{name}{{0%,100%{{background-position:0% 50%}}50%{{background-position:100% 50%}}}}"
               f".{cid}{{background:radial-gradient(60% 80% at 25% 20%,color-mix(in srgb,var(--primary) {a}%,transparent),transparent),"
               f"radial-gradient(55% 65% at 80% 15%,color-mix(in srgb,var(--accent) {b}%,transparent),transparent),"
               f"radial-gradient(70% 70% at 60% 90%,color-mix(in srgb,var(--primary) {max(a-8,8)}%,transparent),transparent),var(--bg);"
               f"background-size:160% 160%;animation:flo_{name} 16s ease infinite;}}")
        bg.append({"id": cid, "tags": [tone, "hero", "mesh"], "marker": cid,
                   "prompt": f"Hero background `.{cid}`: animated {tone} brand mesh (no photo).", "css": css})
    return {"gradient": grad, "background": bg}


# ── 3. GLOWS — parametric ────────────────────────────────────────────────────────
def gen_glows():
    out = []
    for inten, blur, spread in [("soft", 28, 0), ("medium", 40, 6), ("strong", 60, 12)]:
        for hue in ["accent", "primary"]:
            cid = f"glow-{hue}-{inten}"
            out.append({"id": cid, "tags": [inten, "cards", "dark"], "marker": cid,
                        "prompt": f"`.{cid}` on hover: {inten} {hue} glow (box-shadow blur {blur}px).",
                        "css": f".{cid}{{transition:box-shadow .35s}}.{cid}:hover{{box-shadow:0 0 {blur}px {spread}px color-mix(in srgb,var(--{hue}) 35%,transparent)}}"})
    return {"glow": out}


# ── 4. MOTION — animate.css + Hover.css style (real keyframes, MIT-style) ─────────
_ANIM = {
    "fadeInUp": "from{opacity:0;transform:translateY(40px)}to{opacity:1;transform:none}",
    "fadeInDown": "from{opacity:0;transform:translateY(-40px)}to{opacity:1;transform:none}",
    "fadeInLeft": "from{opacity:0;transform:translateX(-40px)}to{opacity:1;transform:none}",
    "fadeInRight": "from{opacity:0;transform:translateX(40px)}to{opacity:1;transform:none}",
    "zoomIn": "from{opacity:0;transform:scale(.85)}to{opacity:1;transform:none}",
    "slideInUp": "from{transform:translateY(100%)}to{transform:none}",
    "bounceIn": "0%{opacity:0;transform:scale(.6)}60%{transform:scale(1.05)}100%{opacity:1;transform:none}",
    "flipInX": "from{opacity:0;transform:perspective(400px) rotateX(80deg)}to{opacity:1;transform:none}",
    "rotateIn": "from{opacity:0;transform:rotate(-12deg)}to{opacity:1;transform:none}",
    "backInUp": "0%{opacity:.2;transform:translateY(60px) scale(.7)}80%{transform:translateY(0) scale(.95)}100%{opacity:1;transform:none}",
    "fadeInUpBig": "from{opacity:0;transform:translateY(120px)}to{opacity:1;transform:none}",
    "blurIn": "from{opacity:0;filter:blur(12px)}to{opacity:1;filter:blur(0)}",
}
_ATTN = {
    "pulse": "0%,100%{transform:scale(1)}50%{transform:scale(1.05)}",
    "float": "0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}",
    "shake": "0%,100%{transform:translateX(0)}25%{transform:translateX(-4px)}75%{transform:translateX(4px)}",
    "tada": "0%{transform:scale(1)}10%{transform:scale(.95) rotate(-3deg)}50%{transform:scale(1.05) rotate(3deg)}100%{transform:scale(1)}",
    "heartBeat": "0%,100%{transform:scale(1)}14%{transform:scale(1.1)}28%{transform:scale(1)}42%{transform:scale(1.1)}",
    "swing": "20%{transform:rotate(8deg)}40%{transform:rotate(-6deg)}60%{transform:rotate(3deg)}100%{transform:rotate(0)}",
}
_HOVER = {
    "grow": ".hvr-grow{transition:transform .3s}.hvr-grow:hover{transform:scale(1.06)}",
    "shrink": ".hvr-shrink{transition:transform .3s}.hvr-shrink:hover{transform:scale(.95)}",
    "float": ".hvr-float{transition:transform .3s}.hvr-float:hover{transform:translateY(-6px)}",
    "bob": "@keyframes hvr-bob{0%,100%{transform:translateY(-4px)}50%{transform:translateY(0)}}.hvr-bob:hover{animation:hvr-bob .9s ease infinite}",
    "buzz": "@keyframes hvr-buzz{50%{transform:translateX(2px) rotate(1deg)}100%{transform:translateX(-2px) rotate(-1deg)}}.hvr-buzz:hover{animation:hvr-buzz .15s linear infinite}",
    "sweep-right": ".hvr-sweep{position:relative;transition:color .3s;z-index:1}.hvr-sweep::before{content:'';position:absolute;inset:0;background:var(--accent);transform:scaleX(0);transform-origin:left;transition:transform .3s;z-index:-1}.hvr-sweep:hover::before{transform:scaleX(1)}",
    "underline-center": ".hvr-uc{position:relative}.hvr-uc::after{content:'';position:absolute;left:50%;right:50%;bottom:-3px;height:2px;background:var(--accent);transition:left .3s,right .3s}.hvr-uc:hover::after{left:0;right:0}",
    "glow-ring": ".hvr-ring{transition:box-shadow .3s}.hvr-ring:hover{box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 40%,transparent)}",
}


def gen_motion():
    anim, hover = [], []
    for name, kf in {**_ANIM, **_ATTN}.items():
        rep = " infinite" if name in _ATTN else ""
        dur = "2.4s" if name in _ATTN else ".7s"
        cid = f"a-{name}"
        css = f"@keyframes {cid}{{{kf}}}.{cid}{{animation:{cid} {dur} ease both{rep}}}"
        anim.append({"id": cid, "tags": (["attention"] if name in _ATTN else ["entrance"]),
                     "marker": cid, "prompt": f"Elements with class `.{cid}` animate via @keyframes {cid} ({name}).",
                     "css": css})
    for name, css in _HOVER.items():
        cid = f"hvr-{name}"
        hover.append({"id": cid, "tags": ["hover"], "marker": css.split("{")[0].strip().lstrip("."),
                      "prompt": f"Interactive elements use class `.{cid}` ({name} hover effect).", "css": css})
    return {"animation": anim, "hover": hover}


def main():
    packs = {"fonts.json": gen_fonts(), "gradients.json": gen_gradients(),
             "glow.json": gen_glows(), "motion.json": gen_motion()}
    for fn, data in packs.items():
        json.dump(data, open(os.path.join(OUT, fn), "w"), indent=1)
    # report
    print("WROTE assets/:")
    print(f"  fonts.json     pairings={len(packs['fonts.json']['pairings'])}")
    g = packs["gradients.json"]
    print(f"  gradients.json gradient={len(g['gradient'])} background={len(g['background'])}")
    print(f"  glow.json      glow={len(packs['glow.json']['glow'])}")
    m = packs["motion.json"]
    print(f"  motion.json    animation={len(m['animation'])} hover={len(m['hover'])}")
    total = (len(packs['fonts.json']['pairings']) + len(g['gradient']) + len(g['background'])
             + len(packs['glow.json']['glow']) + len(m['animation']) + len(m['hover']))
    print(f"  TOTAL entries = {total}  (× seeded combinatorics across packs ⇒ >10000 distinct looks)")


if __name__ == "__main__":
    main()
