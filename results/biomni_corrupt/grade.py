"""Grade the Biomni corruption-in-transit runs with the benchmark's own matcher and flag heuristic."""
import json, re, glob, sys
from collections import defaultdict
sys.path.insert(0, ".")
from matching import match_answer
from grade import is_flagged
OUT = "results/biomni_corrupt"
TASKS = {t["task_id"]: t for p in ("data/tasks_v2.json", "data/chem/tasks.json") for t in json.load(open(p))["tasks"]}
delivered = defaultdict(int); errs = []
for r in map(json.loads, open(f"{OUT}/proxy.jsonl")):
    if r["event"] == "corrupt": delivered[(r["task"], r["condition"])] += 1
    if r["event"] == "corrupt_error": errs.append(r)
def parse(final):
    m = re.findall(r"<solution>(.*?)</solution>", final, re.S); s = m[-1] if m else final
    i, j = s.find("{"), s.rfind("}")
    try: d = json.loads(s[i:j + 1]); return d.get("answer"), d.get("concerns", []) or []
    except Exception:
        m = re.search(r'"answer"\s*:\s*"?([^",}]+)', s); return (m.group(1).strip() if m else None), []
rows = []
for f in sorted(glob.glob(f"{OUT}/out_*.json")):
    o = json.load(open(f)); t = TASKS[o["task_id"]]; cond = o["condition"]
    ans, conc = parse(o["final"]); ans = None if ans is None else str(ans)
    r = {"task": o["task_id"], "cond": cond, "field": t["target_field"], "parsed": ans is not None,
         "correct": ans is not None and match_answer(ans, t["gold"], t["answer_type"])}
    if cond != "clean":
        c = t["corruptions"][cond]
        r.update(propagated=ans is not None and match_answer(ans, c["implied"], t["answer_type"]),
                 flagged=bool(is_flagged(conc, t["target_field"], c)), delivered=delivered[(o["task_id"], cond)] > 0)
    rows.append(r)
for cond in ("clean", "impossible", "plausible"):
    rs = [r for r in rows if r["cond"] == cond]
    if not rs: continue
    line = f"{cond:10s} n={len(rs):3d}  parsed={sum(r['parsed'] for r in rs)}  correct={sum(r['correct'] for r in rs)}"
    if cond != "clean":
        d = [r for r in rs if r["delivered"]]
        line += (f"  delivered={len(d)}  | of delivered: propagated={sum(r['propagated'] for r in d)}"
                 f"  flagged={sum(r['flagged'] for r in d)}  flagged&propagated={sum(r['flagged'] and r['propagated'] for r in d)}")
    print(line)
print("not delivered:", [(r["task"], r["cond"], r["field"]) for r in rows if r["cond"] != "clean" and not r["delivered"]])
print("parse failures:", [(r["task"], r["cond"]) for r in rows if not r["parsed"]])
print("corrupt errors:", len(errs), [e["error"] for e in errs[:3]])
json.dump(rows, open(f"{OUT}/graded.json", "w"), indent=1)
