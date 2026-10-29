"""Cue-taxonomy validation: Cohen's kappa per cue, each annotator vs the grader key and annotator vs annotator.
Usage: python validation_agreement.py results/v2/validation   (reads concerns_key.json and every labels_*.csv in that folder)"""
import csv, json, sys, os, glob
d = sys.argv[1]; CUES = ["crossfield", "recall", "rule", "none"]
def kappa(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n; pa, pb = sum(a) / n, sum(b) / n; pe = pa * pb + (1 - pa) * (1 - pb)
    return ((po - pe) / (1 - pe) if pe < 1 else float("nan")), po
def labels(p):
    out = {}
    for r in csv.DictReader(open(p)): out[r["id"]] = {c: int(r[c]) for c in CUES}
    return out
raw = json.load(open(os.path.join(d, "concerns_key.json")))
items = raw.items() if isinstance(raw, dict) else ((str(x.get("id")), x) for x in raw)
key = {}
for i, v in items:
    if not isinstance(v, dict): continue
    src = v.get("classifier", v); g = {c: int(bool(src.get(c, src.get(f"cue_{c}", False)))) for c in ("crossfield", "recall", "rule")}; g["none"] = int(not any(g.values())); key[str(i)] = g
ann = {os.path.basename(p)[len("labels_"):-4]: labels(p) for p in sorted(glob.glob(os.path.join(d, "labels_*.csv")))}
print(f"{d}: grader key {len(key)} items; annotators: {list(ann) or 'none yet'}")
def report(A, B, la, lb):
    ids = sorted(set(A) & set(B))
    if not ids: print(f"  {la} vs {lb}: no overlap"); return
    parts = []
    for c in CUES:
        k, po = kappa([A[i][c] for i in ids], [B[i][c] for i in ids])
        parts.append(f"{c} kappa {k:.2f} (agree {100 * po:.0f}%; {la} {sum(A[i][c] for i in ids)}, {lb} {sum(B[i][c] for i in ids)})")
    print(f"  {la} vs {lb}, n = {len(ids)}:\n    " + "\n    ".join(parts))
for a, L in ann.items(): report(L, key, a, "grader")
names = list(ann)
for i in range(len(names)):
    for j in range(i + 1, len(names)): report(ann[names[i]], ann[names[j]], names[i], names[j])
