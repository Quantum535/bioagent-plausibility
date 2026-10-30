"""Consensus labels: items both annotators agree on are copied; disagreements are shown with both answers for a joint decision.
Usage: python adjudicate.py results/v2/validation george arjun   (resumable; writes labels_consensus.csv)"""
import csv, sys, os, textwrap
d, a, b = sys.argv[1], sys.argv[2], sys.argv[3]; CUES = ["crossfield", "recall", "rule", "none"]
def lab(n):
    out = {}
    for r in csv.DictReader(open(os.path.join(d, f"labels_{n}.csv"))): out[r["id"]] = tuple(int(r[c]) for c in CUES)
    return out
A, B = lab(a), lab(b); text = {r["id"]: r["concern_text"] for r in csv.DictReader(open(os.path.join(d, "concerns_to_label.csv")))}
out = os.path.join(d, "labels_consensus.csv"); done = {}
if os.path.exists(out):
    for r in csv.DictReader(open(out)): done[r["id"]] = tuple(int(r[c]) for c in CUES)
fmt = lambda t: "".join(k for k, v in zip("crun", t) if v) or "-"
ids = sorted(set(A) & set(B)); n_dis = sum(A[i] != B[i] for i in ids)
for i in ids:
    if A[i] == B[i]: done[i] = A[i]
dis = [i for i in ids if A[i] != B[i] and i not in done]
print(f"{len(ids)} items: {len(ids) - n_dis} agreed (copied), {n_dis} disagreements, {len(dis)} still to resolve")
def save():
    with open(out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id"] + CUES)
        for i in sorted(done): w.writerow([i, *done[i]])
for n, i in enumerate(dis):
    print(f"\n--- {n + 1}/{len(dis)} [{i}]\n" + "\n".join(textwrap.wrap(text[i], 110)) + f"\n  {a}: {fmt(A[i])}    {b}: {fmt(B[i])}")
    while True:
        x = input("agreed answer (c/r/u combined, n, or q to stop)> ").strip().lower()
        if x == "q": save(); sys.exit("saved; run again to continue")
        if x == "n" or (x and not set(x) - set("cru")): break
        print("use c, r, u (combinable), n or q")
    done[i] = (int("c" in x), int("r" in x), int("u" in x), int(x == "n")); save()
save(); print(f"consensus written: {out} ({len(done)} items)")
