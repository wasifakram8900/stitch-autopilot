"""
MANIFEST — dedupe / resume. Makes the whole factory idempotent: re-running never
rebuilds a lead that already shipped. Like gmaps campaign.sh's MANIFEST.

out/manifest.json:  { lead_key: {status, url, grade, score, local, ts} }
lead_key = slug(name)+"|"+slug(location)  — stable per business, survives re-runs.
"""
import os, re, json, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "out", "manifest.json")


def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower())
    return re.sub(r"-{2,}", "-", s).strip("-")


def key(b):
    return slug(b.get("name", "")) + "|" + slug(b.get("location", ""))


def _load():
    if not os.path.exists(PATH):
        return {}
    try:
        return json.load(open(PATH))
    except Exception:
        return {}


def _save(d):
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    json.dump(d, open(PATH, "w"), indent=2)


def is_built(b):
    """True only if this lead already shipped (status Done with a URL)."""
    rec = _load().get(key(b))
    return bool(rec and rec.get("status") == "Done" and rec.get("url"))


def get(b):
    return _load().get(key(b))


def record(b, result):
    d = _load()
    d[key(b)] = {
        "name": b.get("name"),
        "location": b.get("location"),
        "status": "Done" if result.get("url") else result.get("status", "Failed"),
        "url": result.get("url"),
        "grade": result.get("grade"),
        "score": result.get("score"),
        "local": result.get("local"),
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    _save(d)
    return d[key(b)]


def unbuilt(items):
    """Filter a list of business dicts down to those not yet shipped."""
    return [b for b in items if not is_built(b)]


if __name__ == "__main__":
    d = _load()
    done = [v for v in d.values() if v.get("status") == "Done"]
    print(f"manifest: {PATH}")
    print(f"entries={len(d)} shipped={len(done)}")
    for v in list(d.values())[:20]:
        print(f"  {v.get('status'):<8} {v.get('grade') or '-':<2} {v.get('name')}  {v.get('url') or ''}")
