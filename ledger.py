"""
QA Learner — the closed-loop memory. NO LLM, pure counting.

Every build attempt appends one line to out/qa_ledger.jsonl:
  {ts, name, niche, font, palette, layout, anim, score, grade, pass, fail_gates:[...]}

design_dna.pick() reads penalties() at pick time and down-weights DNA component
values that keep FAILING QA. A palette/font/layout that repeatedly ships broken
sites quietly stops being chosen — the factory gets smarter every run, for free.

Safety: penalties are a *fraction* (< 1.0) so they only break ties WITHIN a niche
match tier — they never override niche correctness (a niche match is worth +1).
Only values seen >= MIN_SAMPLES times count, so noise from 1-2 runs is ignored.
"""
import os, json, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "out", "qa_ledger.jsonl")

MIN_SAMPLES = 3          # ignore a value until we've seen it this many times
PENALTY_STRENGTH = 0.9   # max penalty (< 1.0 so a niche match of +1 always wins)


def record(name, niche, ds, card):
    """Append one attempt outcome. ds = design_dna dict, card = qa.scorecard dict."""
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    fail_gates = [k for k, v in (card.get("hard") or {}).items() if not v]
    entry = {
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "name": name,
        "niche": niche or "",
        "font": f"{ds['font']['head']}/{ds['font']['body']}",
        "palette": ds["palette"]["name"],
        "layout": ds["layout"]["name"],
        "anim": ds["anim"]["name"],
        "score": card.get("score"),
        "grade": card.get("grade"),
        "pass": bool(card.get("pass")),
        "fail_gates": fail_gates,
    }
    with open(LEDGER, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def _rows():
    if not os.path.exists(LEDGER):
        return []
    out = []
    for line in open(LEDGER):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def penalties():
    """fail_rate per DNA value, keyed by dimension. {dim: {value: penalty 0..PENALTY_STRENGTH}}.
    Only values with >= MIN_SAMPLES attempts are returned."""
    rows = _rows()
    agg = {}  # dim -> value -> [fails, total]
    for r in rows:
        for dim in ("font", "palette", "layout", "anim"):
            v = r.get(dim)
            if not v:
                continue
            slot = agg.setdefault(dim, {}).setdefault(v, [0, 0])
            slot[1] += 1
            if not r.get("pass"):
                slot[0] += 1
    out = {}
    for dim, vals in agg.items():
        for v, (fails, total) in vals.items():
            if total < MIN_SAMPLES:
                continue
            out.setdefault(dim, {})[v] = (fails / total) * PENALTY_STRENGTH
    return out


def summary():
    """Human-readable rollup for the CLI / dashboard."""
    rows = _rows()
    passed = sum(1 for r in rows if r.get("pass"))
    by_gate = {}
    for r in rows:
        for g in r.get("fail_gates", []):
            by_gate[g] = by_gate.get(g, 0) + 1
    return {"attempts": len(rows), "passed": passed,
            "pass_rate": round(passed / len(rows), 3) if rows else None,
            "top_failing_gates": sorted(by_gate.items(), key=lambda x: -x[1])}


if __name__ == "__main__":
    s = summary()
    print(f"ledger: {LEDGER}")
    print(f"attempts={s['attempts']} passed={s['passed']} pass_rate={s['pass_rate']}")
    print("top failing gates:", s["top_failing_gates"])
    pen = penalties()
    if pen:
        print("\npenalties (>= {} samples):".format(MIN_SAMPLES))
        for dim, vals in pen.items():
            for v, p in sorted(vals.items(), key=lambda x: -x[1]):
                print(f"  {dim:8} {v:<30} {p:.2f}")
    else:
        print("no penalties yet (need >= {} samples per value)".format(MIN_SAMPLES))
