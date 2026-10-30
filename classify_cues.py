"""LLM cue classifier (Haiku 4.5) using the annotator guidelines (cue_prompt.txt), scored against the consensus gold labels.
Usage: python classify_cues.py dev|test   (results cached in results/cue_classifier_cache.json)"""
import anthropic, json, csv, sys, os, re, hashlib
PROMPT = open("cue_prompt.txt").read(); MODEL = os.environ.get("CUE_MODEL", "claude-haiku-4-5"); CUES = ["crossfield", "recall", "rule", "none"]
CACHE = "results/cue_classifier_cache.json"; cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
client = anthropic.Anthropic()
def key(t): return hashlib.sha256((MODEL + PROMPT + "\n" + t).encode()).hexdigest()[:24]
def call(chunk):
    body = "\n\n".join(f"[{j + 1}] {t}" for j, t in enumerate(chunk))
    raw = client.messages.create(model=MODEL, max_tokens=60 * len(chunk) + 100, system=PROMPT,
                                 messages=[{"role": "user", "content": f"Concerns:\n\n{body}"}]).content[0].text
    m = re.search(r"\[.*\]", raw, re.S)
    try: arr = json.loads(m.group(0)) if m else []
    except json.JSONDecodeError: arr = []
    return arr if len(arr) == len(chunk) and all(isinstance(x, dict) for x in arr) else None
def classify_many(texts, size=10):
    todo = list(dict.fromkeys(t for t in texts if key(t) not in cache))
    for i in range(0, len(todo), size):
        chunk = todo[i:i + size]; arr = call(chunk)
        if arr is None: arr = [(call([t]) or [{}])[0] for t in chunk]
        for t, out in zip(chunk, arr):
            lab = {c: int(bool(out.get(c))) for c in CUES[:3]}; lab["none"] = int(not any(lab.values())); cache[key(t)] = lab
        json.dump(cache, open(CACHE, "w"))
    return [cache[key(t)] for t in texts]
def kappa(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n; pa, pb = sum(a) / n, sum(b) / n; pe = pa * pb + (1 - pa) * (1 - pb)
    return ((po - pe) / (1 - pe) if pe < 1 else float("nan")), po
part = sys.argv[1]; split = json.load(open("results/validation_split.json"))
for dom, d in (("protein", "results/v2/validation"), ("chem", "results/chem/validation")):
    text = {r["id"]: r["concern_text"] for r in csv.DictReader(open(f"{d}/concerns_to_label.csv"))}
    gold = {r["id"]: {c: int(r[c]) for c in CUES} for r in csv.DictReader(open(f"{d}/labels_consensus.csv"))}
    ids = split[dom][part]; pred = dict(zip(ids, classify_many([text[i] for i in ids])))
    print(f"[{MODEL}] {dom} {part} (n = {len(ids)}): " + "  ".join(
        f"{c} kappa {kappa([pred[i][c] for i in ids], [gold[i][c] for i in ids])[0]:.2f} (clf {sum(pred[i][c] for i in ids)}, gold {sum(gold[i][c] for i in ids)})" for c in CUES))
    miss = [i for i in ids if pred[i] != gold[i]]
    if part == "dev":
        for i in miss[:6]: print(f"   {i} gold {gold[i]} clf {pred[i]} :: {text[i][:150]}")
