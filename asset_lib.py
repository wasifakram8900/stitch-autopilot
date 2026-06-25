"""
Asset library — the "tons of effects" catalog the designer/tech agents compose from.

Each effect = {id, tags, marker, prompt, css?, js?}:
  - prompt : the line injected into the Stitch brief ("implement EXACTLY ...")
  - css/js : literal snippet appended as the contract Stitch must reproduce
  - marker : a class/function name we MANDATE in the prompt → the tech team greps the
             generated HTML for it to PROVE the effect actually shipped (else regen).

Categories: gradient, background, cursor, glass, glow, animation, hover.
Curated core lives here (quality-controlled). `load_external()` merges bulk-imported
JSON packs (full Google Fonts, animate.css, Hover.css, parametric gradients) → 10000s.

seed = hash(name+date) → `bundle()` picks a COHERENT, niche-weighted set per site.
Run `python asset_lib.py` to see a composed bundle + the QA markers it guarantees.
"""
import hashlib, json, os, glob
import niches

HERE = os.path.dirname(os.path.abspath(__file__))


# ── CURATED EFFECT CORE ─────────────────────────────────────────────────────────
EFFECTS = {
    "gradient": [
        {"id": "aurora-mesh", "tags": ["vibrant", "hero", "premium"], "marker": "aurora-mesh",
         "prompt": "Hero background class `.aurora-mesh`: layered radial-gradients (primary + accent + a 3rd hue) forming a soft aurora mesh, no photo.",
         "css": ".aurora-mesh{background:radial-gradient(60% 80% at 20% 20%,color-mix(in srgb,var(--primary) 22%,transparent),transparent),radial-gradient(50% 60% at 80% 10%,color-mix(in srgb,var(--accent) 20%,transparent),transparent),radial-gradient(70% 70% at 60% 90%,color-mix(in srgb,var(--primary) 14%,transparent),transparent),var(--bg);}"},
        {"id": "conic-rotate", "tags": ["bold", "hero"], "marker": "@keyframes spinhue",
         "prompt": "Hero background `.conic-rotate`: slowly rotating conic-gradient (primary→accent→primary), 24s linear, behind content.",
         "css": "@keyframes spinhue{to{transform:rotate(360deg)}}.conic-rotate{position:absolute;inset:-30%;background:conic-gradient(from 0deg,var(--primary),var(--accent),var(--primary));filter:blur(70px);opacity:.18;animation:spinhue 24s linear infinite;}"},
        {"id": "duotone-diagonal", "tags": ["minimal", "section"], "marker": "duotone-diagonal",
         "prompt": "Section accent `.duotone-diagonal`: 135deg linear-gradient from --surface to color-mix primary 10%.",
         "css": ".duotone-diagonal{background:linear-gradient(135deg,var(--surface),color-mix(in srgb,var(--primary) 10%,var(--bg)));}"},
    ],
    "background": [
        {"id": "gradient-breathe", "tags": ["calm", "hero"], "marker": "@keyframes breathe",
         "prompt": "Hero `.hero-gradient-bg`: 400% linear-gradient(135deg of bg/surface/primary-8%) animated background-position `breathe` 12s infinite.",
         "css": "@keyframes breathe{0%,100%{background-position:0% 50%}50%{background-position:100% 50%}}.hero-gradient-bg{background:linear-gradient(135deg,var(--bg),var(--surface),var(--bg),color-mix(in srgb,var(--primary) 8%,var(--bg)));background-size:400% 400%;animation:breathe 12s ease infinite;}"},
        {"id": "dot-matrix", "tags": ["tech", "modern"], "marker": "dot-matrix",
         "prompt": "Section `.dot-matrix`: subtle radial-gradient dot grid (border color), 22px tile, low opacity.",
         "css": ".dot-matrix{background-image:radial-gradient(var(--border) 1px,transparent 1px);background-size:22px 22px;}"},
        {"id": "grid-fade", "tags": ["tech", "editorial"], "marker": "grid-fade",
         "prompt": "Section `.grid-fade`: thin line grid masked to fade out toward edges.",
         "css": ".grid-fade{background-image:linear-gradient(var(--border) 1px,transparent 1px),linear-gradient(90deg,var(--border) 1px,transparent 1px);background-size:40px 40px;-webkit-mask-image:radial-gradient(ellipse 70% 60% at 50% 40%,#000 40%,transparent 100%);}"},
        {"id": "drift-blobs", "tags": ["soft", "hero"], "marker": "@keyframes drift",
         "prompt": "Two absolute blurred blobs (primary + accent), blur(90px) opacity .12, slow `drift` float 18s.",
         "css": "@keyframes drift{0%,100%{transform:translate(0,0)}50%{transform:translate(40px,-30px)}}.blob{position:absolute;border-radius:50%;filter:blur(90px);opacity:.12;animation:drift 18s ease-in-out infinite}.blob-a{background:var(--primary)}.blob-b{background:var(--accent)}"},
    ],
    "cursor": [
        {"id": "glow-orb", "tags": ["premium", "dark"], "marker": "cursor-glow",
         "prompt": "Add a fixed `#cursor-glow` radial-glow div that follows the pointer (mousemove sets left/top), accent color, blur, mix-blend-mode screen, pointer-events none.",
         "css": "#cursor-glow{position:fixed;width:380px;height:380px;border-radius:50%;background:radial-gradient(circle,color-mix(in srgb,var(--accent) 40%,transparent),transparent 60%);transform:translate(-50%,-50%);pointer-events:none;mix-blend-mode:screen;z-index:5;transition:opacity .3s}",
         "js": "addEventListener('mousemove',e=>{const g=document.getElementById('cursor-glow');if(g){g.style.left=e.clientX+'px';g.style.top=e.clientY+'px'}});"},
        {"id": "magnetic-btn", "tags": ["interactive"], "marker": "data-magnetic",
         "prompt": "Buttons with attribute `data-magnetic` gently translate toward the cursor on hover (max 8px), spring back on leave.",
         "js": "document.querySelectorAll('[data-magnetic]').forEach(b=>{b.addEventListener('mousemove',e=>{const r=b.getBoundingClientRect();b.style.transform=`translate(${(e.clientX-r.left-r.width/2)/6}px,${(e.clientY-r.top-r.height/2)/6}px)`});b.addEventListener('mouseleave',()=>b.style.transform='')});"},
        {"id": "spotlight-cards", "tags": ["cards", "premium"], "marker": "--mx",
         "prompt": "Cards `.spotlight`: a radial highlight at the cursor via CSS vars --mx/--my updated on mousemove; ::before radial-gradient at (var(--mx),var(--my)).",
         "css": ".spotlight{position:relative;overflow:hidden}.spotlight::before{content:'';position:absolute;inset:0;background:radial-gradient(200px circle at var(--mx) var(--my),color-mix(in srgb,var(--primary) 16%,transparent),transparent 70%);opacity:0;transition:opacity .3s}.spotlight:hover::before{opacity:1}",
         "js": "document.querySelectorAll('.spotlight').forEach(c=>c.addEventListener('mousemove',e=>{const r=c.getBoundingClientRect();c.style.setProperty('--mx',(e.clientX-r.left)+'px');c.style.setProperty('--my',(e.clientY-r.top)+'px')}));"},
    ],
    "glass": [
        {"id": "glass-nav", "tags": ["nav", "premium"], "marker": "backdrop-filter",
         "prompt": "Sticky nav transparent at top; on window scroll>40 add `.scrolled` = background rgba(bg,0.82) + backdrop-filter blur(20px) + 1px border + soft shadow, transition .4s.",
         "css": "nav{transition:background .4s,box-shadow .4s,border-color .4s;border-bottom:1px solid transparent}nav.scrolled{background:color-mix(in srgb,var(--bg) 82%,transparent);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-bottom-color:var(--border);box-shadow:0 1px 40px rgba(0,0,0,.06)}",
         "js": "addEventListener('scroll',()=>document.querySelector('nav')?.classList.toggle('scrolled',scrollY>40));"},
        {"id": "glass-card", "tags": ["cards"], "marker": "glass-card",
         "prompt": "Optional `.glass-card`: frosted surface = background rgba(surface,0.6) + backdrop-filter blur(14px) + hairline border.",
         "css": ".glass-card{background:color-mix(in srgb,var(--surface) 60%,transparent);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border:1px solid var(--border)}"},
    ],
    "glow": [
        {"id": "glow-border", "tags": ["cards", "dark", "bold"], "marker": "glow-border",
         "prompt": "Cards `.glow-border` on hover: animated gradient ring + box-shadow glow in accent; ::before conic-gradient blurred behind, opacity 0→.5.",
         "css": ".glow-border{position:relative}.glow-border::before{content:'';position:absolute;inset:-1px;border-radius:inherit;background:conic-gradient(from 180deg,var(--primary),var(--accent),var(--primary));filter:blur(10px);opacity:0;transition:opacity .35s;z-index:-1}.glow-border:hover::before{opacity:.5}.glow-border:hover{box-shadow:0 0 40px color-mix(in srgb,var(--accent) 35%,transparent)}"},
        {"id": "neon-text", "tags": ["dark", "headline"], "marker": "neon-text",
         "prompt": "One headline word `.neon-text`: layered text-shadow glow in accent (use sparingly, dark schemes only).",
         "css": ".neon-text{color:var(--accent);text-shadow:0 0 8px color-mix(in srgb,var(--accent) 60%,transparent),0 0 24px color-mix(in srgb,var(--accent) 35%,transparent)}"},
        {"id": "cta-pulse", "tags": ["cta"], "marker": "@keyframes ctapulse",
         "prompt": "Primary CTA `.cta-pulse`: gentle glow pulse (box-shadow) `ctapulse` 2.6s infinite to draw the eye.",
         "css": "@keyframes ctapulse{0%,100%{box-shadow:0 0 0 0 color-mix(in srgb,var(--accent) 40%,transparent)}50%{box-shadow:0 0 0 14px transparent}}.cta-pulse{animation:ctapulse 2.6s ease-out infinite}"},
    ],
    "animation": [
        {"id": "word-reveal", "tags": ["hero", "essential"], "marker": "splitWords",
         "prompt": "On DOMContentLoaded `splitWords(#page-home h1)`: split into word spans, each opacity 0→1 + translateY(20px)→0, stagger .08s/word.",
         "js": "function splitWords(el){if(!el)return;const w=el.textContent.trim().split(' ');el.innerHTML=w.map((x,i)=>`<span style=\"display:inline-block;opacity:0;transform:translateY(20px);transition:opacity .5s ease ${i*0.08}s,transform .5s ease ${i*0.08}s\">${x}&nbsp;</span>`).join('');requestAnimationFrame(()=>el.querySelectorAll('span').forEach(s=>{s.style.opacity=1;s.style.transform='translateY(0)'}));}"},
        {"id": "scroll-reveal", "tags": ["sections", "essential"], "marker": "IntersectionObserver",
         "prompt": "Every section heading/card gets class `.reveal` (opacity0 translateY28); IntersectionObserver threshold .12 adds `.visible` then unobserves. `.reveal-group` children stagger .1s.",
         "css": ".reveal{opacity:0;transform:translateY(28px);transition:opacity .65s ease,transform .65s ease}.reveal.visible{opacity:1;transform:none}",
         "js": "function initReveal(){const o=new IntersectionObserver((es)=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('visible');o.unobserve(e.target)}}),{threshold:.12});document.querySelectorAll('.reveal').forEach(el=>o.observe(el))}"},
        {"id": "stat-countup", "tags": ["stats"], "marker": "animateCounter",
         "prompt": "Stat numbers count up (ease-out cubic) via `animateCounter(el,target)` when they enter the viewport.",
         "js": "function animateCounter(el,t){let s=null;const d=1400;function f(ts){s=s||ts;const p=Math.min((ts-s)/d,1);el.textContent=Math.floor((1-Math.pow(1-p,3))*t);if(p<1)requestAnimationFrame(f)}requestAnimationFrame(f)}"},
        {"id": "marquee-strip", "tags": ["kinetic", "bold"], "marker": "marquee-track",
         "prompt": "A horizontal `.marquee` strip of services/keywords with `.marquee-track` translating -50% infinitely (duplicate content for seamless loop), pause on hover.",
         "css": "@keyframes marquee{to{transform:translateX(-50%)}}.marquee{overflow:hidden;white-space:nowrap}.marquee-track{display:inline-flex;gap:3rem;animation:marquee 22s linear infinite}.marquee:hover .marquee-track{animation-play-state:paused}"},
        {"id": "hover-tilt", "tags": ["cards", "interactive"], "marker": "data-tilt",
         "prompt": "Service cards `data-tilt`: subtle 3D tilt toward cursor (max 8deg) with perspective, reset on leave.",
         "js": "document.querySelectorAll('[data-tilt]').forEach(c=>{c.style.transformStyle='preserve-3d';c.addEventListener('mousemove',e=>{const r=c.getBoundingClientRect();const rx=((e.clientY-r.top)/r.height-.5)*-8,ry=((e.clientX-r.left)/r.width-.5)*8;c.style.transform=`perspective(700px) rotateX(${rx}deg) rotateY(${ry}deg)`});c.addEventListener('mouseleave',()=>c.style.transform='')});"},
        {"id": "scroll-progress", "tags": ["nav", "editorial"], "marker": "scroll-progress",
         "prompt": "Fixed top `#scroll-progress` bar (accent) whose width = scroll %; updates on scroll.",
         "css": "#scroll-progress{position:fixed;top:0;left:0;height:3px;width:0;background:var(--accent);z-index:100;transition:width .1s}",
         "js": "addEventListener('scroll',()=>{const b=document.getElementById('scroll-progress');if(b){const h=document.documentElement;b.style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+'%'}});"},
        {"id": "shimmer-word", "tags": ["headline"], "marker": "@keyframes shimmer",
         "prompt": "One h1 word `.shimmer`: animated gradient text-fill (transparent) `shimmer` 3.5s linear.",
         "css": "@keyframes shimmer{to{background-position:200% center}}.shimmer{background:linear-gradient(90deg,var(--text),var(--primary),var(--text));background-size:200% auto;-webkit-background-clip:text;background-clip:text;color:transparent;animation:shimmer 3.5s linear infinite}"},
    ],
    "hover": [
        {"id": "hover-lift", "tags": ["cards", "essential"], "marker": "hover-lift",
         "prompt": "Cards `.hover-lift`: transition transform .25s + shadow; :hover translateY(-6px) + soft glow shadow.",
         "css": ".hover-lift{transition:transform .25s,box-shadow .25s}.hover-lift:hover{transform:translateY(-6px);box-shadow:0 20px 60px color-mix(in srgb,var(--primary) 13%,transparent)}"},
        {"id": "underline-grow", "tags": ["nav"], "marker": "nav-link",
         "prompt": "Nav links `.nav-link::after`: 0→100% width underline (accent) on hover.",
         "css": ".nav-link{position:relative}.nav-link::after{content:'';position:absolute;left:0;bottom:-4px;height:2px;width:0;background:var(--accent);transition:width .3s}.nav-link:hover::after{width:100%}"},
        {"id": "image-zoom", "tags": ["gallery"], "marker": "img-zoom",
         "prompt": "Gallery tiles `.img-zoom`: overflow hidden; inner media scale 1→1.06 on hover, .5s ease.",
         "css": ".img-zoom{overflow:hidden}.img-zoom>*{transition:transform .5s ease}.img-zoom:hover>*{transform:scale(1.06)}"},
    ],
}

# niche effect bias comes from the central registry (niches.py) — bias picks so gym ≠ spa.
NICHE_BIAS = niches.EFFECT_BIAS

# how many to pick per category for one site
BUNDLE_SHAPE = {"gradient": 1, "background": 1, "cursor": 1, "glass": 1, "glow": 1, "animation": 4, "hover": 2}
ESSENTIAL = {"word-reveal", "scroll-reveal"}   # always include these animations


def _idx(seed, salt, n):
    return int(hashlib.sha256(f"{seed}|{salt}".encode()).hexdigest(), 16) % n


def _weighted_pick(items, seed, salt, k, bias_tags, force_ids=()):
    """Pick k items, preferring those whose tags intersect bias_tags, deterministic by seed."""
    forced = [it for it in items if it["id"] in force_ids]
    pool = [it for it in items if it["id"] not in {f["id"] for f in forced}]
    # bias: tag-matches first, then the rest; stable order, then seed-rotate within each tier
    hit = [it for it in pool if set(it.get("tags", [])) & set(bias_tags)]
    miss = [it for it in pool if it not in hit]
    ordered = hit + miss
    chosen = list(forced)
    i = 0
    while len(chosen) < k and ordered:
        chosen.append(ordered.pop(_idx(seed, f"{salt}{i}", len(ordered))))
        i += 1
    return chosen[:k]


def load_external(folder="assets"):
    """Merge bulk-imported JSON packs (same entry shape) from assets/*.json into EFFECTS."""
    for fp in glob.glob(os.path.join(HERE, folder, "*.json")):
        try:
            data = json.load(open(fp))
        except Exception:
            continue
        for cat, entries in (data or {}).items():
            if cat not in EFFECTS:          # only merge real effect categories (skip e.g. font "pairings")
                continue
            EFFECTS[cat].extend(entries)


def bundle(name, date="", niche=None):
    seed = f"{name}::{date}::{niche or ''}"
    bias = NICHE_BIAS.get(niches.resolve(niche), [])
    out = {}
    for cat, k in BUNDLE_SHAPE.items():
        force = ESSENTIAL if cat == "animation" else ()
        out[cat] = _weighted_pick(EFFECTS.get(cat, []), seed, cat, k, bias, force_ids=force)
    return out


def compose_block(b):
    """Render the 'implement EXACTLY' brief section + literal CSS/JS contract."""
    lines = ["SIGNATURE EFFECTS — implement ALL, working, using the EXACT class/function names:"]
    css, js = [], []
    for cat, items in b.items():
        for it in items:
            lines.append(f"- [{cat}/{it['id']}] {it['prompt']}")
            if it.get("css"):
                css.append(f"/* {it['id']} */ " + it["css"])
            if it.get("js"):
                js.append(f"// {it['id']}\n" + it["js"])
    block = "\n".join(lines)
    if css:
        block += "\n\nINCLUDE THIS CSS VERBATIM (inside <style>):\n" + "\n".join(css)
    if js:
        block += "\n\nINCLUDE THIS JS VERBATIM (before </body>):\n" + "\n".join(js)
    block += "\nALWAYS add @media (prefers-reduced-motion: reduce){*{animation-duration:.01ms!important;transition-duration:.01ms!important}}"
    return block


def markers(b):
    """Tokens the technical team greps in the generated HTML to PROVE each effect shipped."""
    return [it["marker"] for items in b.values() for it in items]


if __name__ == "__main__":
    load_external()
    for name, niche in [("Brewhaus Coffee Co.", "coffee shop"),
                        ("IronPeak Fitness", "gym"),
                        ("BrightSmile Dental", "dental")]:
        b = bundle(name, niche=niche)
        picked = ", ".join(f"{c}:{','.join(i['id'] for i in its)}" for c, its in b.items())
        print(f"\n{'='*64}\n{name}  ({niche})\n  {picked}")
        print(f"  QA markers ({len(markers(b))}): {markers(b)}")
    print("\n--- sample composed brief block (IronPeak) ---")
    print(compose_block(bundle("IronPeak Fitness", niche="gym"))[:700], "...")
