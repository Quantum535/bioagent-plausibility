"""LLM cue classifier (Haiku 4.5) using the annotator guidelines (cue_prompt.txt), scored against the consensus gold labels.
Usage: python classify_cues.py dev|test   (results cached in results/cue_classifier_cache.json)"""
import anthropic, json, csv, sys, os, re, hashlib
PROMPT = open("cue_prompt.txt").read(); CUES = ["crossfield", "recall", "rule", "none"]
CACHE = "results/cue_classifier_cache.json"; cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
client = anthropic.Anthropic()
def classify(text):
    h = hashlib.sha256((PROMPT + "\n" + text).encode()).hexdigest()[:24]
    if h not in cache:
        raw = client.messages.create(model="claude-haiku-4-5", max_tokens=150, system=PROMPT,
                                     messages=[{"role": "user", "content": f"Concern:\n{text}"}]).content[0].text
        m = re.search(r"\{.*\}", raw, re.S); out = json.loads(m.group(0)) if m else {}
        lab = {c: int(bool(out.get(c))) for c in CUES[:3]}; lab["none"] = int(not any(lab.values())); cache[h] = lab
        json.dump(cache, open(CACHE, "w"))
    return cache[h]
def kappa(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n; pa, pb = sum(a) / n, sum(b) / n; pe = pa * pb + (1 - pa) * (1 - pb)
    return ((po - pe) / (1 - pe) if pe < 1 else float("nan")), po
part = sys.argv[1]; split = json.load(open("results/validation_split.json"))
for dom, d in (("protein", "results/v2/validation"), ("chem", "results/chem/validation")):
    text = {r["id"]: r["concern_text"] for r in csv.DictReader(open(f"{d}/concerns_to_label.csv"))}
    gold = {r["id"]: {c: int(r[c]) for c in CUES} for r in csv.DictReader(open(f"{d}/labels_consensus.csv"))}
    ids = split[dom][part]; pred = {i: classify(text[i]) for i in ids}
    print(f"{dom} {part} (n = {len(ids)}): " + "  ".join(
        f"{c} kappa {kappa([pred[i][c] for i in ids], [gold[i][c] for i in ids])[0]:.2f} (clf {sum(pred[i][c] for i in ids)}, gold {sum(gold[i][c] for i in ids)})" for c in CUES))
    miss = [i for i in ids if pred[i] != gold[i]]
    if part == "dev":
        for i in miss[:6]: print(f"   {i} gold {gold[i]} clf {pred[i]} :: {text[i][:150]}")
