"""
Reference Scout — loads references/*.md, auto-tags each by niche + style, and picks the
best matches per business to steer the Design Director. Works on whatever's in the folder
(0, 3, or 100 files). Drop the user's 100 "greatest sites" .md into references/.

Tagging: honors an optional comment  <!-- niche: dental, gym; style: bold, dark -->
otherwise infers tags by scanning the content.
"""
import os, re, glob, hashlib
import niches

HERE = os.path.dirname(os.path.abspath(__file__))

NICHE_WORDS = niches.NICHE_WORDS   # central registry keywords (40+ niches)
STYLE_WORDS = ["bold", "dark", "minimal", "editorial", "elegant", "luxury", "playful",
               "kinetic", "brutalist", "glass", "glassmorphism", "gradient", "neon", "glow",
               "modern", "clean", "retro", "vibrant", "premium", "industrial", "calm", "warm"]


def _tags_from_comment(text, key):
    m = re.search(rf"{key}\s*:\s*([^\n;>-]+)", text, re.I)
    return [t.strip().lower() for t in m.group(1).split(",")] if m else []


def _infer(text, vocab):
    low = text.lower()
    return [w for w in vocab if w in low]


def load_references(folder="references"):
    refs = []
    for fp in sorted(glob.glob(os.path.join(HERE, folder, "*.md"))):
        if os.path.basename(fp).lower() == "readme.md":
            continue
        text = open(fp, encoding="utf-8", errors="ignore").read()
        niche = _tags_from_comment(text, "niche") or _infer(text, NICHE_WORDS)
        style = _tags_from_comment(text, "style") or _infer(text, STYLE_WORDS)
        head = next((l.strip("# ").strip() for l in text.splitlines() if l.strip().startswith("#")), None)
        essence = head or os.path.basename(fp)[:-3].replace("-", " ").title()
        refs.append({"name": os.path.basename(fp)[:-3], "path": fp,
                     "niche": niche, "style": style, "essence": essence})
    return refs


def _seed(s):
    return int(hashlib.sha256(s.encode()).hexdigest(), 16)


def select(niche=None, k=3, seed="", folder="references"):
    refs = load_references(folder)
    if not refs:
        return []
    niche = (niche or "").lower()

    def score(r):
        s = 0
        if niche and any(niche.split()[0] in n or n in niche for n in r["niche"]):
            s += 2
        if r["style"]:
            s += 1
        return s

    ranked = sorted(refs, key=lambda r: (-score(r), _seed(seed + r["name"])))
    top = [r for r in ranked if score(r) > 0] or ranked
    return top[:k]


def style_bias(selected):
    """Aggregate style tags of the chosen references -> extra bias for design picks."""
    tags = []
    for r in selected:
        tags += r["style"]
    return list(dict.fromkeys(tags))


def to_block(selected):
    if not selected:
        return ""
    lines = ["DESIGN INSPIRATION — match this caliber and energy, do NOT copy them:"]
    for r in selected:
        st = f" [{', '.join(r['style'])}]" if r["style"] else ""
        lines.append(f"  · {r['essence']}{st}")
    return "\n".join(lines)


if __name__ == "__main__":
    refs = load_references()
    print(f"loaded {len(refs)} references")
    for r in refs:
        print(f"  {r['name']:<22} niche={r['niche']} style={r['style']}")
    for niche in ["gym", "dental", "coffee"]:
        sel = select(niche)
        print(f"\nselect('{niche}') -> {[r['name'] for r in sel]}  bias={style_bias(sel)}")
        print(to_block(sel))
