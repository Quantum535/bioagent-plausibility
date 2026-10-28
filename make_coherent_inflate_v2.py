"""Coherent inflate v2: reach the same target length as v1 with a natural segment from a different benchmark protein
(no internal tandem repeat). v1 vs v2 isolates the visible-repeat cue; P1 is evaluated on v2."""
import json, random
from Bio.SeqUtils import molecular_weight
import domains, tasks as ptasks
from matching import match_answer
from harness.checks import check_protein
rng = random.Random(1); dom = domains.load("protein")
Ts = dom.Table("data/proteins_v2.json"); Tf = dom.Table("data/proteins_v2.json", record_format="full")
full = json.load(open("data/uniprot_full.json")); full = {r["primaryAccession"]: r for r in (full.values() if isinstance(full, dict) else full)}
by_acc = Ts.by_acc; src = json.load(open("data/coherent_inflate.json")); out = []
shares = lambda a, b, k=12: any(a[i:i + k] in b for i in range(len(a) - k + 1))
for t in src["tasks"]:
    t = json.loads(json.dumps(t)); c = t["corruptions"]["coherent_plausible"]; acc = t["target_accession"]
    seq = full[acc]["sequence"]["value"]; need = c["fields"]["length"] - len(seq)
    for _ in range(500):
        d_acc = rng.choice([a for a in by_acc if a != acc]); donor = full[d_acc]["sequence"]["value"]
        if len(donor) < need + 2: continue
        start = rng.randrange(1, len(donor) - need + 1); seg = donor[start:start + need]
        if not shares(seg, seq): break
    else: raise SystemExit(f"no donor found for {t['task_id']}")
    new = seq + seg; mass = int(round(molecular_weight(new, seq_type="protein")))
    c.update({"fields": {"length": len(new), "mass": mass}, "corrupted_value": {"length": len(new), "mass": mass}[t["target_field"]],
              "full_patch": {"sequence": new, "mass": mass}, "construction": "natural_segment", "donor": d_acc, "donor_start": start})
    c["implied"] = ptasks.TEMPLATES[t["template"]]["compute"](t, ptasks.records_for(t, by_acc, "coherent_plausible"))
    assert not match_answer(c["implied"], t["gold"], t["answer_type"]), t["task_id"]
    r = Ts.by_acc[acc]; v = check_protein(json.loads(dom.render(Ts, r, c)), Ts, full=json.loads(dom.render(Tf, r, c)))
    assert not any(x.get("status") in ("mismatch", "not_found") for x in v.values()), (t["task_id"], v)
    out.append(t)
json.dump(dict(src, n_tasks=len(out), tasks=out), open("data/coherent_inflate_v2.json", "w"), indent=1)
print(f"coherent_inflate_v2: {len(out)} tasks; same target lengths as v1; no shared 12-mer; derivation checks pass on all")
