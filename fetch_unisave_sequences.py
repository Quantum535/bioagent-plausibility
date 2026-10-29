"""Phase 5 step 2: every superseded sequence from UniSave, compared with the stored current UniProt sequence."""
import json, time, requests
from Bio.SeqUtils import molecular_weight
hist = json.load(open("data/unisave_history.json"))
full = json.load(open("data/uniprot_full.json")); full = {r["primaryAccession"]: r for r in (full.values() if isinstance(full, dict) else full)}
def mw(s):
    try: return molecular_weight(s, seq_type="protein")
    except Exception: return None
out, fail, first_fail = {}, 0, None
for acc, h in hist.items():
    sv2ev = {int(k): v for k, v in h["seqver_to_entryver"].items()}
    if len(sv2ev) < 2 or acc not in full: continue
    cur = full[acc]["sequence"]["value"]; m_cur = mw(cur)
    for sv, ev in sorted(sv2ev.items()):
        if sv == max(sv2ev): continue
        r = None
        try:
            r = requests.get(f"https://rest.uniprot.org/unisave/{acc}", params={"format": "fasta", "versions": ev}, timeout=60)
            seq = "".join(l.strip() for l in r.text.splitlines() if l and not l.startswith(">")) if r.status_code == 200 else ""
        except Exception:
            seq = ""
        if not seq:
            fail += 1; first_fail = first_fail or (acc, ev, getattr(r, "status_code", None), (getattr(r, "text", "") or "")[:200]); continue
        m_old = mw(seq)
        out.setdefault(acc, []).append({"seq_version": sv, "entry_version": ev, "sequence": seq, "length": len(seq), "mass": m_old,
                                        "same_as_stored": seq == cur, "d_length": len(seq) - len(cur),
                                        "d_mass": (m_old - m_cur) if (m_old and m_cur) else None})
        time.sleep(0.2)
json.dump(out, open("data/unisave_old_sequences.json", "w"), indent=1)
recs = [(a, x) for a, v in out.items() for x in v]
print(f"fetched {len(recs)} superseded sequences for {len(out)} proteins; failed {fail}" + (f"; first failure {first_fail}" if first_fail else ""))
print(f"identical to the stored current sequence (stored record itself outdated): {sum(x['same_as_stored'] for _, x in recs)}")
dl = [abs(x["d_length"]) for _, x in recs if not x["same_as_stored"]]
print("|length change|: 0 -> %d, 1-5 -> %d, 6-50 -> %d, >50 -> %d" % (sum(d == 0 for d in dl), sum(1 <= d <= 5 for d in dl), sum(6 <= d <= 50 for d in dl), sum(d > 50 for d in dl)))
use_len = {a for a, x in recs if not x["same_as_stored"] and x["d_length"] != 0}
use_mass = {a for a, x in recs if not x["same_as_stored"] and x["d_mass"] is not None and abs(x["d_mass"]) >= 200}
print(f"proteins usable for length tasks: {len(use_len)}; for mass tasks (|change| >= 200 Da): {len(use_mass)}; either: {len(use_len | use_mass)}")
rel = sorted(abs(x["d_mass"]) / (x["mass"] or 1) for _, x in recs if x["d_mass"] and not x["same_as_stored"])
if rel: print(f"relative mass change: median {100 * rel[len(rel) // 2]:.2f}%, p90 {100 * rel[int(.9 * len(rel))]:.1f}%, max {100 * rel[-1]:.0f}%")
