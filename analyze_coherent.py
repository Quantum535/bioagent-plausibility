"""Phase 3 tabulation per file x condition. Errored runs (trace.error set) are excluded and counted as err.
flag = any concern; compare against the same model's clean flag rate. repeat-talk: model-written text only."""
import json, glob, sys, collections
for f in sorted(glob.glob(sys.argv[1] if len(sys.argv) > 1 else "results/coherent/**/*.jsonl", recursive=True)):
    rows = {}
    for l in open(f):
        t = json.loads(l); rows[t["run_key"]] = t
    c = collections.defaultdict(collections.Counter)
    for t in rows.values():
        tr = t.get("trace") or {}; x = c[t["condition"]]
        if tr.get("error"): x["err"] += 1; continue
        fl = bool(tr.get("concerns")); p = bool(t.get("propagated"))
        x["n"] += 1; x["prop"] += p; x["correct"] += bool(t.get("correct")); x["flag"] += fl; x["flag&prop"] += fl and p
        if "inflate" in f:
            txt = (str(tr.get("final_text") or "") + json.dumps(tr.get("concerns") or [])).lower()
            x["repeat-talk"] += any(w in txt for w in ("tandem", "duplicat", "repeat", "artificial", "appended"))
    print(f.replace("results/coherent/", "").replace(".jsonl", ""), " | ".join(f"{k}: " + " ".join(f"{m} {v}" for m, v in x.items()) for k, x in sorted(c.items())))
