"""Relabel benchmark concerns with the frozen cue classifier (cue_prompt.txt v3 + Sonnet 5, 10 concerns per request; freeze
recorded in results/cue_classifier_FROZEN.txt) via the Message Batches API. Requests are identical to the validated sync calls.
Usage: python classify_corpus.py plan FRAC | submit FRAC | collect      (FRAC = share of flagged runs, e.g. 1.0 or 0.4)"""
import anthropic, json, glob, sys, os, re, hashlib
PROMPT = open("cue_prompt.txt").read(); MODEL = "claude-sonnet-5"; CUES = ["crossfield", "recall", "rule"]
OUT = "results/cue_corpus"; os.makedirs(OUT, exist_ok=True); client = anthropic.Anthropic()
def runs(frac):
    R = []
    for f in sorted(glob.glob("results/v2/traces_*.jsonl") + glob.glob("results/chem/traces_*.jsonl")):
        seen = {}
        for l in open(f):
            t = json.loads(l); seen[t["run_key"]] = t
        for t in seen.values():
            cs = (t.get("trace") or {}).get("concerns") or []
            cs = [c if isinstance(c, str) else json.dumps(c) for c in (cs if isinstance(cs, list) else [cs])]
            if cs and int(hashlib.sha256(t["run_key"].encode()).hexdigest()[:8], 16) / 2 ** 32 < frac:
                R.append({"file": f, "run_key": t["run_key"], "domain": "chem" if "/chem/" in f else "protein", "concerns": cs})
    return R
def chunks(R):
    texts = {d: list(dict.fromkeys(c for r in R if r["domain"] == d for c in r["concerns"])) for d in ("protein", "chem")}
    return [texts[d][i:i + 10] for d in texts for i in range(0, len(texts[d]), 10)]
def params(chunk):
    body = "\n\n".join(f"[{j + 1}] {t}" for j, t in enumerate(chunk))
    return {"model": MODEL, "max_tokens": 4000, "system": PROMPT, "messages": [{"role": "user", "content": f"Concerns:\n\n{body}"}]}
def parse(content, n):
    raw = "".join(getattr(b, "text", "") for b in content if getattr(b, "type", "") == "text")
    m = re.search(r"\[.*\]", raw, re.S)
    try: arr = json.loads(m.group(0)) if m else []
    except json.JSONDecodeError: arr = []
    return arr if len(arr) == n and all(isinstance(x, dict) for x in arr) else None
def lab(o):
    d = {c: int(bool(o.get(c))) for c in CUES}; d["none"] = int(not any(d.values())); return d
mode = sys.argv[1]
if mode in ("plan", "submit"):
    frac = float(sys.argv[2]); R = runs(frac); C = chunks(R); n = sum(len(c) for c in C)
    print(f"frac {frac}: {len(R)} flagged runs, {n} unique concerns, {len(C)} requests; est. cost ${n * 35.10 / 9559 * 0.5:.2f} (batch price)")
    if mode == "submit":
        json.dump(R, open(f"{OUT}/runs.json", "w")); json.dump({f"q{i:05d}": c for i, c in enumerate(C)}, open(f"{OUT}/chunks.json", "w"))
        b = client.messages.batches.create(requests=[{"custom_id": f"q{i:05d}", "params": params(c)} for i, c in enumerate(C)])
        open(f"{OUT}/batch_id.txt", "w").write(b.id); print("submitted batch", b.id)
elif mode == "collect":
    bid = open(f"{OUT}/batch_id.txt").read().strip(); b = client.messages.batches.retrieve(bid)
    if b.processing_status != "ended": sys.exit(f"batch {bid}: {b.processing_status} {b.request_counts}")
    C = json.load(open(f"{OUT}/chunks.json")); R = json.load(open(f"{OUT}/runs.json")); labels, failed = {}, []
    for r in client.messages.batches.results(bid):
        arr = parse(r.result.message.content, len(C[r.custom_id])) if r.result.type == "succeeded" else None
        if arr is None: failed.append(r.custom_id); continue
        for t, o in zip(C[r.custom_id], arr): labels[t] = lab(o)
    for cid in failed:
        for t in C[cid]:
            resp = client.messages.create(**params([t])); arr = parse(resp.content, 1); labels[t] = lab(arr[0] if arr else {})
    with open(f"{OUT}/run_labels.jsonl", "w") as f:
        for r in R:
            ls = [labels[c] for c in r["concerns"]]
            f.write(json.dumps({**{k: r[k] for k in ("file", "run_key", "domain")}, "concerns": [{"text": c, **l} for c, l in zip(r["concerns"], ls)],
                                "run": {c: int(any(l[c] for l in ls)) for c in CUES}}) + "\n")
    print(f"collected: {len(labels)} concerns labelled ({sum(len(C[c]) for c in failed)} via sync fallback); wrote {OUT}/run_labels.jsonl")
