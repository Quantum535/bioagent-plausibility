"""Concern gate: predict 'this answer is wrong' from the concern text + field, on the native-loop runs.
Within-domain (task-grouped CV), protein->chemistry transfer, and leave-one-vendor-out; baseline = keyword flag heuristic."""
import json, re, sys
import numpy as np
sys.path.insert(0, ".")
from analysis import load_runs, score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
from scipy.sparse import hstack, csr_matrix

vendor = lambda m: "anthropic" if "claude" in m else "google" if "gemini" in m else "openai" if "gpt" in m else "deepseek" if "deepseek" in m.lower() else "moonshot"
rows = []
for dom, globs in (("protein", ["results/v2/traces_*.jsonl"]), ("chemistry", ["results/chem/traces_*.jsonl"])):
    for r in load_runs(globs):
        s = score(r)
        if s["verify_prompt"]: continue
        rows.append({"dom": dom, "task": s["task_id"], "model": s["model"], "vendor": vendor(s["model"]), "field": s["target_field"],
                     "text": " ".join(str(c) for c in (s["concerns"] or [])), "flagged": int(bool(s["flagged"])), "wrong": int(not s["correct"])})
print(f"{len(rows)} runs; wrong-answer rate {np.mean([r['wrong'] for r in rows]):.2f}")
FIELDS = sorted({r["field"] for r in rows})
def feats(vec, rs, fit=False):
    X = vec.fit_transform([r["text"] for r in rs]) if fit else vec.transform([r["text"] for r in rs])
    F = csr_matrix([[int(r["field"] == f) for f in FIELDS] + [int(bool(r["text"].strip())), min(len(r["text"]), 2000) / 2000] for r in rs])
    return hstack([X, F]).tocsr()
def evaluate(train, test, label):
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=20000, sublinear_tf=True)
    Xtr, Xte = feats(vec, train, True), feats(vec, test)
    clf = LogisticRegression(C=1.0, max_iter=2000, class_weight="balanced").fit(Xtr, [r["wrong"] for r in train])
    p = clf.predict_proba(Xte)[:, 1]; y = np.array([r["wrong"] for r in test]); base = np.array([r["flagged"] for r in test])
    thr = 0.5; pred = (p >= thr).astype(int)
    P, R, F, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    Pb, Rb, Fb, _ = precision_recall_fscore_support(y, base, average="binary", zero_division=0)
    print(f"  {label:34s} n={len(test):5d}  gate AUC={roc_auc_score(y, p):.2f} P={P:.2f} R={R:.2f} F1={F:.2f} fires={pred.mean():.2f}  |  keyword flag P={Pb:.2f} R={Rb:.2f} F1={Fb:.2f} fires={base.mean():.2f}")
print("== within-domain, 5-fold CV grouped by task")
for dom in ("protein", "chemistry"):
    rs = [r for r in rows if r["dom"] == dom]; g = [r["task"] for r in rs]
    tr_idx, te_idx = next(GroupKFold(5).split(rs, groups=g))
    evaluate([rs[i] for i in tr_idx], [rs[i] for i in te_idx], f"{dom} (held-out tasks)")
print("== cross-domain transfer")
evaluate([r for r in rows if r["dom"] == "protein"], [r for r in rows if r["dom"] == "chemistry"], "train protein -> test chemistry")
evaluate([r for r in rows if r["dom"] == "chemistry"], [r for r in rows if r["dom"] == "protein"], "train chemistry -> test protein")
print("== leave-one-vendor-out (both domains)")
for v in sorted({r["vendor"] for r in rows}):
    evaluate([r for r in rows if r["vendor"] != v], [r for r in rows if r["vendor"] == v], f"held-out vendor: {v}")
