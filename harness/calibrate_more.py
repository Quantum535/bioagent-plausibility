"""Calibrate the two remaining tolerances on clean records: RDKit vs PubChem H-bond donors, and the summary-record ratios."""
import json, glob
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
TOL = json.load(open("harness/tolerances.json"))
c = json.load(open("data/chem/compounds.json"))
dd = sorted(abs(rdMolDescriptors.CalcNumHBD(Chem.MolFromSmiles(r["smiles"])) - r["h_bond_donors"]) for r in c)
ratio_c = sorted(r["molecular_weight"] / r["heavy_atom_count"] for r in c)
p = json.load(open("data/proteins_v2.json")); p = p if isinstance(p, list) else list(p.values())
ratio_p = sorted(r["mass"] / r["length"] for r in p)
TOL["compound"]["h_bond_donors"] = int(dd[-1]); TOL["compound"]["h_bond_donors_calibration"] = {"n": len(dd), "max_abs_diff": int(dd[-1]), "n_nonzero": sum(1 for d in dd if d)}
TOL["compound"]["da_per_heavy_atom"] = [round(ratio_c[0] * 0.9, 2), round(ratio_c[-1] * 1.1, 2)]
TOL["protein"]["da_per_residue"] = [round(ratio_p[0] * 0.9, 1), round(ratio_p[-1] * 1.1, 1)]
json.dump(TOL, open("harness/tolerances.json", "w"), indent=1)
print(f"donors: |RDKit - PubChem| max {dd[-1]}, nonzero in {sum(1 for d in dd if d)}/{len(dd)} -> tolerance ±{TOL['compound']['h_bond_donors']}")
print(f"Da/heavy atom on clean compounds: {ratio_c[0]:.1f}-{ratio_c[-1]:.1f} -> band {TOL['compound']['da_per_heavy_atom']}")
print(f"Da/residue on clean proteins: {ratio_p[0]:.1f}-{ratio_p[-1]:.1f} -> band {TOL['protein']['da_per_residue']}")
