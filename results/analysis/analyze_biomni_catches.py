"""Deployment: for delivered plausible runs, separate unparseable answers from catches and classify how each catch happened,
from Biomni's final text and the proxy log. Run from the repository root."""
import collections, glob, json, os, re
CAT = [("recomputation", r"rdkit|recomput|calculat|comput(ed|ing) (the )?(length|mass|weight)|len\(|from the (sequence|formula|smiles)|independently (confirm|verif)"),
       ("redundant field", r"taxonom|lineage|organism_id|9606|_HUMAN|entry name|entry_name|cross-?referenc|hgnc|gene name"),
       ("second query", r"second (query|lookup|request)|re-?(queried|fetched)|queried again|another (lookup|query|source)|cross-?check"),
       ("memory", r"known|canonical|literature|typically|expected|well[- ]established|according to (my|prior) knowledge")]
def classify(text):
    t = (text or "").lower(); hits = [c for c, pat in CAT if re.search(pat, t)]
    return hits or ["unclassified"]
def runs(path):
    def walk(x, ctx):
        if isinstance(x, dict):
            ks = [str(k).lower() for k in x]
            if any("propag" in k or "relay" in k for k in ks) and any("field" in k for k in ks): yield {**ctx, **x}; return
            for k, v in x.items(): yield from walk(v, {**ctx, "condition": str(k).lower()} if str(k).lower() in ("clean", "impossible", "plausible") else ctx)
        elif isinstance(x, list):
            for v in x: yield from walk(v, ctx)
    pick = lambda r, *s: next((v for k, v in r.items() if any(x in str(k).lower() for x in s)), None)
    for r in walk(json.load(open(path)), {}):
        if "plausible" in str(pick(r, "cond") or "").lower() and pick(r, "deliver") is not False:
            yield str(pick(r, "task")), str(pick(r, "field")), pick(r, "propag", "relay"), pick(r, "answer"), pick(r, "correct")
out = {}
for model in ("deepseek", "flash"):
    d = f"results/biomni_full_{model}"; finals = {}
    for f in glob.glob(f"{d}/out_*_plausible.json"):
        o = json.load(open(f)); finals[str(o.get("task_id"))] = o.get("final") or ""
    reqs = collections.Counter()
    if os.path.exists(f"{d}/proxy.jsonl"):
        for l in open(f"{d}/proxy.jsonl"):
            r = json.loads(l)
            if r.get("condition") == "plausible" and r.get("event") == "response": reqs[str(r.get("task"))] += 1
    n = collections.Counter(); how = collections.defaultdict(collections.Counter); examples = collections.defaultdict(list)
    for tid, field, prop, ans, corr in runs(f"{d}/graded.json"):
        grp = "protein" if field in ("length", "mass", "organism", "gene_symbol", "name", "protein_name") else "chemistry"
        if prop: n[(grp, "relayed")] += 1; continue
        if ans in (None, "", "null") and not corr: n[(grp, "unparseable")] += 1; continue
        n[(grp, "caught")] += 1
        cats = classify(finals.get(tid, ""))
        if reqs[tid] >= 3 and "second query" not in cats: cats.append("second query")
        for c in cats:
            how[(grp, field)][c] += 1
            if len(examples[c]) < 2 and finals.get(tid): examples[c].append((model, tid, re.sub(r"\s+", " ", finals[tid])[:220]))
    out[model] = {"outcomes": {f"{g}/{k}": v for (g, k), v in sorted(n.items())}, "how_caught": {f"{g}/{f_}": dict(c) for (g, f_), c in sorted(how.items())}}
    print(f"== {model}\n  outcomes: {out[model]['outcomes']}")
    for k, v in out[model]["how_caught"].items(): print(f"  {k:28s} {dict(v)}")
    for c, ex in examples.items():
        for e in ex: print(f"  [{c}] {e[0]} {e[1]}: {e[2]}")
json.dump(out, open("results/analysis/biomni_catches.json", "w"), indent=1)
