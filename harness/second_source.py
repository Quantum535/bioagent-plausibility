"""Second-source check: compare record fields against an independent database.
AlphaFold DB (proteins, keyed by accession) and NCI CACTUS (compounds, keyed by CID; only the 270 whose CACTUS formula
matches PubChem are used, the rest return 'unavailable'). Tolerances as calibrated: mass +-3 Da, MW +-0.5 Da, counts exact."""
import json
from Bio.SeqUtils import molecular_weight
from rdkit import Chem, RDLogger
RDLogger.DisableLog("rdApp.*")
_AF = json.load(open("data/second_source_alphafold.json"))
_CA = json.load(open("data/second_source_cactus.json"))
_PC = {str(r["cid"]): r for r in json.load(open("data/chem/compounds.json"))}
_CA_OK = {cid for cid, e in _CA.items() if e and e.get("formula") == _PC.get(cid, {}).get("formula")}

def _cmp(have, ref, tol):
    if have is None or ref is None: return {"status": "unavailable"}
    ok = abs(float(have) - float(ref)) <= tol
    return {"status": "ok" if ok else "mismatch", "record": have, "second_source": ref}

def check_protein_ss(acc, rec):
    e = _AF.get(acc)
    if not e: return {k: {"status": "unavailable"} for k in ("length", "mass")}
    return {"length": _cmp(rec.get("length"), e["length"], 0),
            "mass": _cmp(rec.get("mass"), molecular_weight(e["sequence"], seq_type="protein"), 3.0)}

def check_compound_ss(cid, rec):
    cid = str(cid)
    if cid not in _CA_OK: return {k: {"status": "unavailable"} for k in ("molecular_weight", "heavy_atom_count")}
    e = _CA[cid]; m = Chem.MolFromSmiles(e.get("smiles", "")) if e.get("smiles") else None
    return {"molecular_weight": _cmp(rec.get("molecular_weight"), e.get("mw"), 0.5),
            "heavy_atom_count": _cmp(rec.get("heavy_atom_count"), m.GetNumHeavyAtoms() if m else None, 0)}
