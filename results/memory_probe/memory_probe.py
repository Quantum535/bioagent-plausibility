"""Ask each model, with no tools, for the length of each historical protein. Run from the repository root."""
import json, os, re, sys, time
sys.path.insert(0, ".")
for line in open(".env"):
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip().strip(chr(34)))
from providers import make_provider
from agent import cost_usd
tasks = json.load(open("data/phase5_tasks.json"))["tasks"]
P = json.load(open("data/proteins_v2.json")); P = P.get("proteins", P) if isinstance(P, dict) else P
by_acc = {p["accession"]: p for p in P}
MODELS = {"opus5": "anthropic:claude-opus-5", "argon": "gemini:gemini-4-argon", "deepseek": "together:deepseek-ai/DeepSeek-V4.1-Flash-1017"}
SYSTEM = ("You are a bioinformatics assistant. No tools are available; answer from memory. "
          "Reply with exactly one line of JSON: {\"length\": <integer or null>, \"confidence\": \"high\"|\"medium\"|\"low\"}.")
out = open("results/memory_probe/answers.jsonl", "a"); done = set()
try: done = {(json.loads(l)["model"], json.loads(l)["task_id"]) for l in open("results/memory_probe/answers.jsonl")}
except FileNotFoundError: pass
total = 0.0
for name, spec in MODELS.items():
    prov = make_provider(spec, SYSTEM, [])
    for t in tasks:
        if (name, t["task_id"]) in done: continue
        acc = t["target_accession"]; p = by_acc[acc]; c = t["corruptions"]["superseded"]
        cur = int(p["length"]); sup = cur + int(c["d_length"])
        q = (f"What is the length in amino acids of the canonical sequence of the human protein {p.get('protein_name', '')} "
             f"(gene {p.get('gene_symbol', '')}, UniProt accession {acc})? If unsure, give your best estimate and mark confidence low.")
        rec = {"model": name, "task_id": t["task_id"], "accession": acc, "current": cur, "superseded": sup}
        for attempt in range(3):
            try:
                turn = prov.complete([prov.user_msg(q)], force_no_tools=True); text = turn.text or ""
                m = re.search(r"\{[^{}]*\}", text, re.S); j = json.loads(m.group(0)) if m else {}
                rec.update({"answer": j.get("length"), "confidence": j.get("confidence"), "raw": text[:300]})
                total += cost_usd(prov.price(), turn.usage); break
            except Exception as e:
                rec["error"] = str(e)[:200]; time.sleep(5 * (attempt + 1))
        out.write(json.dumps(rec) + "\n"); out.flush()
    print(f"{name}: done; running cost ${total:.2f}")
