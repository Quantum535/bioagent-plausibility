"""Phase 4 step 1: candidate new chemistry fields. PubChem values vs RDKit derivations from the stored SMILES,
to classify each field's derivation route empirically (exact / approximate / none) before pre-registration."""
import json, time, requests, statistics
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, Crippen, rdMolDescriptors, GraphDescriptors
from scipy.stats import spearmanr
RDLogger.DisableLog("rdApp.*")
comps = json.load(open("data/chem/compounds.json")); cids = [str(c["cid"]) for c in comps]
props = "MonoisotopicMass,TPSA,HBondAcceptorCount,RotatableBondCount,XLogP,Complexity"
pc = {}
for i in range(0, len(cids), 100):
    r = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{','.join(cids[i:i + 100])}/property/{props}/JSON", timeout=60)
    for p in r.json()["PropertyTable"]["Properties"]: pc[str(p["CID"])] = p
    time.sleep(0.5)
json.dump(pc, open("data/chem/pubchem_extra_props.json", "w"), indent=1)
print(f"PubChem: {len(pc)}/{len(cids)} compounds returned")
pairs = {k: [] for k in ("MonoisotopicMass", "TPSA", "TPSA_SP", "HBondAcceptorCount", "RotatableBondCount", "XLogP", "Complexity")}
for c in comps:
    m = Chem.MolFromSmiles(c.get("smiles") or c.get("isomeric_smiles") or ""); p = pc.get(str(c["cid"]), {})
    if m is None: continue
    rd = {"MonoisotopicMass": Descriptors.ExactMolWt(m), "TPSA": rdMolDescriptors.CalcTPSA(m), "TPSA_SP": rdMolDescriptors.CalcTPSA(m, includeSandP=True),
          "HBondAcceptorCount": rdMolDescriptors.CalcNumHBA(m), "RotatableBondCount": rdMolDescriptors.CalcNumRotatableBonds(m),
          "XLogP": Crippen.MolLogP(m), "Complexity": GraphDescriptors.BertzCT(m)}
    for k, v in rd.items():
        src = p.get("TPSA" if k == "TPSA_SP" else k)
        if src is not None: pairs[k].append((float(src), float(v)))
tol = {"MonoisotopicMass": 0.001, "TPSA": 0.1, "TPSA_SP": 0.1, "HBondAcceptorCount": 0, "RotatableBondCount": 0, "XLogP": 0.5, "Complexity": 0}
for k, xs in pairs.items():
    d = sorted(abs(a - b) for a, b in xs); within = sum(x <= tol[k] + 1e-9 for x in d)
    rho = spearmanr([a for a, _ in xs], [b for _, b in xs]).correlation
    lo, hi = min(a for a, _ in xs), max(a for a, _ in xs)
    print(f"{k:20s} n={len(xs):3d}  within ±{tol[k]}: {within:3d} ({100 * within / len(xs):5.1f}%)  median |Δ| {statistics.median(d):7.3f}  p95 {d[int(.95 * len(d))]:7.3f}  Spearman {rho:.3f}  PubChem range [{lo:g}, {hi:g}]")
