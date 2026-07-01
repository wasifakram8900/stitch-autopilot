"""
Lead adapter — turns a scraped/enriched lead CSV into the business dict shape the
factory consumes (same shape as businesses.py). Bridges gmaps-lead-engine /
gmaps-enrich output (or any CSV) into the mill. NO LLM.

Tolerant: matches columns by a big alias table (case/space/underscore-insensitive),
so master.csv / high_priority.csv / a hand-made sheet all work. Niche is auto-resolved
from the category/type column via niches.resolve(). Missing fields are fine — the
Stitch skeleton renders "omit if missing", so a bare name+category+phone lead still builds.

  leads.from_csv("path.csv")            -> [business dict, ...]
  leads.from_csv("path.csv", limit=25)  -> first 25
  python leads.py path.csv              -> preview parsed leads
"""
import csv, re
import niches

# canonical field -> possible source column names (normalized: lowercased, non-alnum stripped)
ALIASES = {
    "name":        ["name", "businessname", "business", "title", "companyname", "company"],
    "type":        ["type", "businesstype", "category", "categories", "maincategory", "niche", "industry"],
    "location":    ["location", "city", "citystate", "area", "region"],
    "address":     ["address", "fulladdress", "street", "streetaddress", "addressline"],
    "phone":       ["phone", "phonenumber", "telephone", "tel", "mobile", "internationalphonenumber"],
    "email":       ["email", "emailaddress", "email1", "primaryemail", "contactemail"],
    "hours":       ["hours", "openinghours", "workinghours", "businesshours"],
    "rating":      ["rating", "googlerating", "stars", "score", "reviewsaverage", "totalscore"],
    "website":     ["website", "url", "site", "domain", "webpage"],
    "tagline":     ["tagline", "slogan", "description", "about", "bio"],
    "requirements": ["requirements", "notes", "specialrequirements"],
    # niche hint column (explicit niche wins over category)
    "niche_hint":  ["niche", "vertical", "segment"],
}


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _build_colmap(headers):
    """source-header -> canonical field."""
    norm_headers = {_norm(h): h for h in headers}
    colmap = {}
    for canon, names in ALIASES.items():
        for n in names:
            if n in norm_headers:
                colmap[canon] = norm_headers[n]
                break
    return colmap


def _services_from_row(row):
    """Optional: some enrichers emit service_1..service_n or a 'services' cell (| or ; separated)."""
    svc = []
    blob = None
    for h, v in row.items():
        if _norm(h) in ("services", "servicesoffered", "offerings") and v:
            blob = v
            break
    if blob:
        for part in re.split(r"[|;\n]+", blob):
            part = part.strip()
            if part:
                svc.append({"name": part[:60], "price": "", "duration": "—", "desc": ""})
    return svc[:8]


def row_to_business(row):
    colmap = _build_colmap(row.keys())

    def g(field):
        col = colmap.get(field)
        return (row.get(col) or "").strip() if col else ""

    name = g("name")
    if not name:
        return None
    # niche: explicit hint > category/type text, resolved to a canonical of the 42
    niche_text = g("niche_hint") or g("type")
    niche = niches.resolve(niche_text) if niche_text else niches.resolve(name)

    b = {"name": name, "niche": niche, "source_row": True}
    for f in ("type", "tagline", "location", "address", "phone", "email", "hours", "website", "requirements"):
        v = g(f)
        if v:
            b[f] = v
    # rating -> float if parseable
    rating = g("rating")
    if rating:
        m = re.search(r"\d+(\.\d+)?", rating)
        if m:
            try:
                b["rating"] = float(m.group(0))
            except ValueError:
                pass
    svc = _services_from_row(row)
    if svc:
        b["services"] = svc
    # location fallback from address tail ("...City, ST 12345")
    if not b.get("location") and b.get("address"):
        m = re.search(r",\s*([A-Za-z .'-]+,\s*[A-Z]{2})", b["address"])
        if m:
            b["location"] = m.group(1).strip()
    return b


def from_rows(rows, limit=None):
    out = []
    for r in rows:
        b = row_to_business(r)
        if b:
            out.append(b)
        if limit and len(out) >= limit:
            break
    return out


def from_csv(path, limit=None):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return from_rows(csv.DictReader(f), limit=limit)


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 2:
        print("usage: python leads.py <leads.csv> [limit]")
        raise SystemExit(1)
    lim = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    items = from_csv(sys.argv[1], limit=lim)
    print(f"parsed {len(items)} leads (showing up to {lim}):\n")
    for b in items:
        print(f"  {b['name']:<34} niche={b['niche']:<14} "
              f"loc={b.get('location','-'):<18} phone={b.get('phone','-')}")
    print("\nfirst lead full:\n", json.dumps(items[0], indent=2) if items else "(none)")
