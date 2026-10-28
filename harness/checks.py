"""Deterministic verification of a protein or compound record. Each field gets a verdict:
ok / mismatch / not_found / no_route, with the derived value where one exists."""
import json
from pathlib import Path
from Bio.SeqUtils import molecular_weight
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
TOL = json.load(open(Path(__file__).parent / "tolerances.json"))


def _v(ok, **kw): return {"status": "ok" if ok else "mismatch", **kw}


def check_protein(rec, table, full=None):
    """rec: summary record (dict). full: full UniProt JSON for the same protein, if the harness fetched it."""
    out = {}
    if full and "sequence" in full:
        seq = full["sequence"].get("value", ""); L = full["sequence"].get("length"); M = full["sequence"].get("molWeight")
        out["length"] = _v(L == len(seq), derived=len(seq), observed=L, route="sequence")
        try:
            mw = molecular_weight(seq, seq_type="protein"); out["mass"] = _v(abs(mw - M) <= TOL["protein"]["mass_da"], derived=round(mw), observed=M, route="sequence")
        except Exception:
            out["mass"] = {"status": "no_route", "reason": "non-standard residues"}
        org = full.get("organism", {}); name = org.get("scientificName", ""); tax = org.get("taxonId"); lineage = org.get("lineage", [])
        if tax == 9606: out["organism"] = _v(name == "Homo sapiens", derived="Homo sapiens", observed=name, route="taxonId")
        elif lineage and name: out["organism"] = _v(name.split()[0] in lineage or any(name.split()[0] in l for l in lineage), observed=name, route="lineage")
        else: out["organism"] = {"status": "no_route"}
    else:  # summary-only partner checks
        L, M = rec.get("length"), rec.get("mass")
        if isinstance(L, (int, float)) and isinstance(M, (int, float)) and L > 0 and M > 0:
            lo, hi = TOL["protein"]["da_per_residue"]; ratio = M / L
            out["length"] = out["mass"] = _v(lo <= ratio <= hi, observed=f"{ratio:.1f} Da/residue", route="partner")
        else:
            out["length"] = out["mass"] = _v(False, observed=(L, M), route="rule")
        out["organism"] = {"status": "no_route"}
        from corrupt import is_eukaryote_only
        if is_eukaryote_only(rec.get("subcellular_location", "")) and rec.get("organism", "").startswith("Escherichia"):
            out["organism"] = _v(False, observed=rec["organism"], route="rule")
    sym = rec.get("gene_symbol") or (full or {}).get("genes", [{}])[0].get("geneName", {}).get("value")
    hit, err = table.lookup("find_protein_by_gene", {"gene_symbol": sym}) if sym else (None, "no symbol")
    acc = rec.get("accession") or (full or {}).get("primaryAccession")
    out["gene_symbol"] = {"status": "not_found", "observed": sym, "route": "reverse lookup"} if err else _v(hit["accession"] == acc, derived=hit["accession"], observed=sym, route="reverse lookup")
    return out


def check_compound(rec, table, full=None):
    out = {}
    smi = (full or {}).get("smiles")
    mol = Chem.MolFromSmiles(smi) if smi else None
    if mol is not None:
        W, H, D = rec.get("molecular_weight"), rec.get("heavy_atom_count"), rec.get("h_bond_donors")
        out["molecular_weight"] = _v(abs(Descriptors.MolWt(mol) - W) <= TOL["compound"]["molecular_weight_da"], derived=round(Descriptors.MolWt(mol), 2), observed=W, route="SMILES")
        out["heavy_atom_count"] = _v(mol.GetNumHeavyAtoms() == H, derived=mol.GetNumHeavyAtoms(), observed=H, route="SMILES")
        d = rdMolDescriptors.CalcNumHBD(mol); out["h_bond_donors"] = _v(abs(d - D) <= TOL["compound"]["h_bond_donors"], derived=d, observed=D, route="SMILES")
    else:
        W, H, D = rec.get("molecular_weight"), rec.get("heavy_atom_count"), rec.get("h_bond_donors")
        if isinstance(W, (int, float)) and isinstance(H, (int, float)) and W > 0 and H > 0:
            lo, hi = TOL["compound"]["da_per_heavy_atom"]; out["molecular_weight"] = out["heavy_atom_count"] = _v(lo <= W / H <= hi, observed=f"{W/H:.1f} Da/atom", route="partner")
        else: out["molecular_weight"] = out["heavy_atom_count"] = _v(False, observed=(W, H), route="rule")
        out["h_bond_donors"] = _v(isinstance(D, (int, float)) and 0 <= D <= (H if isinstance(H, (int, float)) else 10**9), observed=D, route="rule")
    name = rec.get("name"); hit, err = table.lookup("find_compound_by_name", {"name": name}) if name else (None, "no name")
    cid = str(rec.get("cid"))
    out["name"] = {"status": "not_found", "observed": name, "route": "reverse lookup"} if err else _v(str(hit["cid"]) == cid, derived=hit["cid"], observed=name, route="reverse lookup")
    return out
