"""Blind labelling of agent concerns for the cue-taxonomy validation.
Usage: python label_tool.py results/v2/validation/concerns_to_label.csv YOURNAME
Shows each concern (never the grader's label or the model), asks which cues it contains, saves after every item, and resumes
where you left off. Order is shuffled per annotator. 'b' goes back one item; the newer answer replaces the older."""
import csv, sys, os, textwrap, random
path, who = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(path, newline="")))
cols = list(rows[0].keys())
idc = next((c for c in cols if c.lower() in ("id", "concern_id", "item_id")), cols[0])
hide = {c for c in cols if any(w in c.lower() for w in ("model", "cue", "label", "grader"))}
show = ["concern_text"] if "concern_text" in cols else [c for c in cols if c != idc and c not in hide]
out = os.path.join(os.path.dirname(path), f"labels_{who}.csv")
done = {r["id"] for r in csv.DictReader(open(out))} if os.path.exists(out) else set()
order = list(range(len(rows))); random.Random(sum(map(ord, who))).shuffle(order)
print(f"id column: {idc} | showing: {show} | hidden: {sorted(hide) or 'none'} | {len(done)}/{len(rows)} done -> {out}")
print("Keys: c = cross-field, r = recall, u = rule (combine, e.g. 'cr'); n = none of these; b = back one; q = quit (progress is saved)\n")
new = not os.path.exists(out); f = open(out, "a", newline=""); w = csv.writer(f)
if new: w.writerow(["id", "crossfield", "recall", "rule", "none"]); f.flush()
todo = [i for i in order if rows[i][idc] not in done]; k = 0
while k < len(todo):
    r = rows[todo[k]]
    print(f"\n--- {len(done) + 1}/{len(rows)}  [{r[idc]}]")
    for c in show: print(f"{c}: " + "\n    ".join(textwrap.wrap(str(r[c]), 110) or [""]))
    a = input("cues> ").strip().lower()
    if a == "q": break
    if a == "b":
        if k > 0: k -= 1; done.discard(rows[todo[k]][idc]); print("(back one item; your new answer replaces the old)")
        continue
    if not a or (a != "n" and set(a) - set("cru")): print("use c, r, u (combinable), n, b or q"); continue
    w.writerow([r[idc], int("c" in a), int("r" in a), int("u" in a), int(a == "n")]); f.flush(); done.add(r[idc]); k += 1
f.close(); print(f"\nsaved: {len(done)}/{len(rows)} labelled in {out}")
