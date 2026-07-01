"""
Outreach handoff — closes the loop to money. After the factory ships sites, it writes
the live preview URL + QA grade back to each lead row, producing a DM-ready CSV:
"made you a preview: <url>". Reads results from manifest.json (source of truth).

  python report_back.py leads.csv            -> leads_outreach.csv (adds preview cols)
  python report_back.py leads.csv out.csv    -> explicit output path

Also usable programmatically: report_back.write_csv(src, out).
For a live Google Sheet, sheets_client.mark() already handles write-back in autopilot.py.
"""
import csv, os
import manifest
import leads as leads_mod

ADDED_COLS = ["preview_url", "preview_grade", "preview_score", "preview_status", "built_at"]


def _match(row):
    """Find this row's manifest record by stable key, then fall back to name-only."""
    b = leads_mod.row_to_business(row)
    if not b:
        return None
    rec = manifest.get(b)
    if rec:
        return rec
    name_slug = manifest.slug(b["name"])
    for v in manifest._load().values():
        if manifest.slug(v.get("name", "")) == name_slug:
            return v
    return None


def write_csv(src_csv, out_csv=None):
    out_csv = out_csv or os.path.splitext(src_csv)[0] + "_outreach.csv"
    with open(src_csv, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    for c in ADDED_COLS:
        if c not in fields:
            fields.append(c)
    matched = 0
    for row in rows:
        rec = _match(row)
        if rec:
            matched += 1
            row["preview_url"] = rec.get("url") or ""
            row["preview_grade"] = rec.get("grade") or ""
            row["preview_score"] = rec.get("score") or ""
            row["preview_status"] = rec.get("status") or ""
            row["built_at"] = rec.get("ts") or ""
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return {"out": out_csv, "rows": len(rows), "matched": matched}


def dm_ready():
    """List shipped previews ready to DM: [{name, url, grade}]."""
    return [{"name": v.get("name"), "url": v.get("url"), "grade": v.get("grade")}
            for v in manifest._load().values()
            if v.get("status") == "Done" and v.get("url")]


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        ready = dm_ready()
        print(f"{len(ready)} previews ready to DM:")
        for r in ready:
            print(f"  {r['grade'] or '-':<2} {r['name']:<30} {r['url']}")
        print("\nusage: python report_back.py <leads.csv> [out.csv]  to write preview cols back")
        raise SystemExit(0)
    res = write_csv(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(f"wrote {res['out']}  ({res['matched']}/{res['rows']} rows matched a shipped preview)")
