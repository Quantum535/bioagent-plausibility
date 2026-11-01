"""Run analysis.py with the validated cue labels (frozen Sonnet 5 classifier; results/cue_corpus/run_labels.jsonl) in place of
the regex classifier. Lookups that cannot be matched fall back to the regex and are counted."""
import json, collections
import analysis as A
L = {}
for l in open("results/cue_corpus/run_labels.jsonl"):
    for c in json.loads(l)["concerns"]: L[c["text"]] = {k: bool(c[k]) for k in ("crossfield", "recall", "rule")}
stats = collections.Counter()
def make(orig):
    def f(text, *a, **k):
        if text in L: stats["exact"] += 1; return dict(L[text])
        parts = [p.strip() for p in str(text).split("|") if p.strip()]
        if parts and all(p in L for p in parts):
            stats["joined"] += 1; return {c: any(L[p][c] for p in parts) for c in ("crossfield", "recall", "rule")}
        stats["regex_fallback"] += 1; return orig(text, *a, **k)
    return f
names = [n for n in dir(A) if n.startswith("_classify_one")]
for n in names: setattr(A, n, make(getattr(A, n)))
print("patched:", names)
if hasattr(A, "main"): A.main()
else: raise SystemExit("analysis.py has no main(); paste the grep output so the wrapper can call the right entry point")
print("label lookups:", dict(stats))
