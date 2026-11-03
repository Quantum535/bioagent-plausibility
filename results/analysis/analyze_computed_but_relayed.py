"""Across full-record experiments: runs whose own text (concerns or final answer) contains the correct value of the corrupted
field, yet whose answer follows the corrupted record. Run from the repository root."""
import collections, glob, json, re
def nums(text): return [float(x.replace(",", "")) for x in re.findall(r"(?<![\w.])\d[\d,]*\.?\d*(?![\w.])", text or "")]
def mentions(text, v, tol=0.005):
    try: v = float(v)
    except (TypeError, ValueError): return False
    return any(abs(x - v) <= max(tol * abs(v), 0.5) for x in nums(text))
SETS = {"benchmark full record": "results/v2_full/traces_*.jsonl", "boundary sweep": "results/boundary/traces_*.jsonl",
        "coherent (full)": "results/coherent/*_prot_*.jsonl", "new chemistry fields (full)": "results/phase4/*_full.jsonl",
        "historical (full)": "results/phase5/*_full.jsonl"}
tot = collections.Counter(); hit = collections.Counter()
for name, pat in SETS.items():
    for f in glob.glob(pat):
        seen = {}
        for i, l in enumerate(open(f)):
            t = json.loads(l); seen[t.get("run_key", i)] = t
        for t in seen.values():
            tr = t.get("trace") or {}; c = t.get("corruption") or {}
            if tr.get("error") or not tr.get("parsed_ok", True) or not t.get("propagated") or t.get("condition") == "clean": continue
            if c.get("clean_value") is None or c.get("clean_value") == c.get("corrupted_value"): continue
            m = t.get("model", "?"); tot[(name, m)] += 1
            text = " ".join(str(x) for x in (tr.get("concerns") or [])) + " " + (tr.get("final_text") or "")
            if mentions(text, c["clean_value"]) and not mentions(str(c["corrupted_value"]), c["clean_value"]): hit[(name, m)] += 1
rows = {}
for k in sorted(tot):
    rows[f"{k[0]} | {k[1]}"] = {"relayed_runs": tot[k], "stated_correct_value": hit[k], "share": round(hit[k] / tot[k], 3)}
    print(f"{k[0]:30s} {k[1]:48s} relayed {tot[k]:4d}  stated correct value in {hit[k]:4d} ({100*hit[k]/tot[k]:.0f}%)")
json.dump(rows, open("results/analysis/computed_but_relayed.json", "w"), indent=1)
