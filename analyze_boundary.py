"""Override boundary: propagation vs scale factor per model/domain/direction, logistic fit of override
probability on |log factor|, and the 50% override point with a task-cluster bootstrap interval."""
import glob, json, math, random, re, sys
from collections import defaultdict
sys.path.insert(0, ".")
from analysis import load_runs, score
import numpy as np
from scipy.optimize import minimize

rows = defaultdict(list); dropped = defaultdict(int)
for f in sorted(glob.glob("results/boundary/traces_*.jsonl")):
    model, domain, direction = re.match(r".*/traces_(\w+?)_(protein|chem)_(shrink|inflate)\.jsonl", f).groups()
    for r in {(x.get("run_key") or id(x)): x for x in load_runs([f])}.values():  # last record per run wins
        s = score(r)
        if s["base_condition"] == "clean": continue
        tr = r.get("trace") or {}
        if tr.get("error") or not tr.get("parsed_ok", True):  # failed at the API or no parseable answer
            dropped[(model, domain, direction)] += 1; continue
        rows[(model, domain, direction)].append((float(s["base_condition"][1:].split("_")[0]), s["task_id"], bool(s["propagated"])))

def fit50(data):
    x = np.array([abs(math.log(f)) for f, _, _ in data]); y = np.array([0.0 if p else 1.0 for _, _, p in data])
    if y.sum() == 0 or y.sum() == len(y): return float("nan")
    nll = lambda w: np.sum(np.logaddexp(0, -(w[0] + w[1] * x)) * y + np.logaddexp(0, w[0] + w[1] * x) * (1 - y)) + 1e-3 * w[1] ** 2
    w = minimize(nll, [0.0, 1.0], method="Nelder-Mead").x
    return -w[0] / w[1] if w[1] > 0 else float("nan")

for key in sorted(rows):
    data = rows[key]; model, domain, direction = key
    facs = sorted({f for f, _, _ in data}, reverse=(direction == "shrink"))
    curve = "  ".join(f"×{f:g}:{100*np.mean([p for ff, _, p in data if ff == f]):3.0f}%" for f in facs)
    tasks = sorted({t for _, t, _ in data}); by_task = defaultdict(list)
    for d in data: by_task[d[1]].append(d)
    rng = random.Random(0)
    boots = [b for b in (fit50([d for t in rng.choices(tasks, k=len(tasks)) for d in by_task[t]]) for _ in range(400)) if not math.isnan(b)]
    x50 = fit50(data); lo, hi = (np.percentile(boots, 2.5), np.percentile(boots, 97.5)) if boots else (float("nan"), float("nan"))
    to_f = lambda v: float("nan") if math.isnan(v) else (math.exp(-v) if direction == "shrink" else math.exp(v))
    a, b = sorted([to_f(lo), to_f(hi)])
    print(f"{model:9s} {domain:8s} {direction:8s}  {curve}")
    print(f"{'':28s} 50% override at ×{to_f(x50):.2f}  [×{a:.2f}, ×{b:.2f}]   (n = {len(data)} runs, {len(tasks)} tasks, {dropped[key]} excluded)")
