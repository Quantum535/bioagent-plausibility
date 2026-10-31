"""Import before analysis.py or the figure scripts: replaces analysis._classify_one and _classify_one_chem with lookups of the
validated cue labels (frozen Sonnet 5 classifier, results/cue_corpus/**/run_labels.jsonl). Unmatched concerns fall back to the
regex and are counted; the counts print at exit."""
import json, glob, os, collections, atexit, sys
ROOT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ROOT)
import analysis as A
L = {}
for p in glob.glob(os.path.join(ROOT, "results/cue_corpus/**/run_labels.jsonl"), recursive=True):
    for l in open(p):
        for c in json.loads(l)["concerns"]: L[c["text"]] = {k: bool(c[k]) for k in ("crossfield", "recall", "rule")}
STATS = collections.Counter()
def _make(orig):
    def f(text, *a, **k):
        if text in L: STATS["validated"] += 1; return dict(L[text])
        STATS["regex_fallback"] += 1; return orig(text, *a, **k)
    return f
for _n in ("_classify_one", "_classify_one_chem"): setattr(A, _n, _make(getattr(A, _n)))
atexit.register(lambda: print("cue label lookups:", dict(STATS)))
