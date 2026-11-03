import collections, glob, json
from scipy.stats import fisher_exact
A = [json.loads(l) for l in open("results/memory_probe/answers.jsonl")]
def cls(r):
    a = r.get("answer")
    try: a = int(a)
    except (TypeError, ValueError): return "none"
    s, c = abs(a - r["superseded"]) <= 1, abs(a - r["current"]) <= 1
    return "either" if s and c else "superseded" if s else "current" if c else "other"
mem = {(r["model"], r["task_id"]): cls(r) for r in A}
def load(path):
    seen = {}
    for i, l in enumerate(open(path)):
        t = json.loads(l); seen[t.get("run_key", i)] = t
    return [t for t in seen.values() if t.get("condition") == "superseded" and not (t.get("trace") or {}).get("error") and (t.get("trace") or {}).get("parsed_ok", True)]
ARMS = {"no second source (full)": "results/phase5/{m}_full.jsonl", "no second source (summary)": "results/phase5/{m}_summary.jsonl",
        "second source, annotate (3 samples)": "results/robustness/{m}_p5_annotate.jsonl"}
res = {}; pooled = collections.defaultdict(lambda: collections.Counter())
for m in ("opus5", "argon", "deepseek"):
    dist = collections.Counter(v for (mm, _), v in mem.items() if mm == m); print(f"\n== {m}: memory {dict(dist)}  (P1: superseded share {100*dist['superseded']/max(sum(dist.values()),1):.0f}%)")
    res[m] = {"memory": dict(dist)}
    for arm, pat in ARMS.items():
        rs = load(pat.format(m=m)); by = collections.defaultdict(lambda: [0, 0])
        for t in rs:
            k = mem.get((m, t["task_id"]), "none"); by[k][0] += bool(t.get("propagated")); by[k][1] += 1
            if "annotate" in arm: pooled[k][0 if not t.get("propagated") else 1] += 1
        line = "  ".join(f"{k}: {v[0]}/{v[1]}" for k, v in sorted(by.items()))
        s, c = by.get("superseded", [0, 0]), by.get("current", [0, 0])
        p = fisher_exact([[s[0], s[1] - s[0]], [c[0], c[1] - c[0]]], alternative="greater")[1] if s[1] and c[1] else float("nan")
        print(f"  {arm:38s} relayed by memory state: {line}   superseded>current one-sided p={p:.3g}")
        res[m][arm] = {k: v for k, v in by.items()}; res[m][arm + " p"] = p
s, c = pooled["superseded"], pooled["current"]
print(f"\nP2 pooled over models (second source): superseded-memory {s[1]}/{s[0]+s[1]} relayed vs current-memory {c[1]}/{c[0]+c[1]}; "
      f"one-sided p={fisher_exact([[s[1], s[0]], [c[1], c[0]]], alternative='greater')[1]:.3g}")
json.dump(res, open("results/memory_probe/analysis.json", "w"), indent=1, default=str)
