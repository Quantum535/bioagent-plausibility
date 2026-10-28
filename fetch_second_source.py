"""Second-source records for the blind-spot experiment: AlphaFold DB (proteins) and NCI CACTUS (compounds)."""
import json, time, urllib.parse, requests
from pathlib import Path
out = {}
prots = json.load(open("data/proteins_v2.json")); prots = prots if isinstance(prots, list) else list(prots.values())
hit = 0
for i, p in enumerate(prots):
    acc = p["accession"]
    try:
        r = requests.get(f"https://alphafold.ebi.ac.uk/api/prediction/{acc}", timeout=30)
        if r.status_code == 200 and r.json():
            e = r.json()[0]; out[acc] = {"sequence": e.get("uniprotSequence"), "length": len(e.get("uniprotSequence", "")), "organism": e.get("organismScientificName"), "gene": e.get("gene")}; hit += 1
        else: out[acc] = None
    except Exception as ex: out[acc] = None
    if i % 50 == 49: print(f"  AlphaFold {i+1}/{len(prots)}: {hit} found", flush=True)
    time.sleep(0.2)
Path("data/second_source_alphafold.json").write_text(json.dumps(out, indent=1))
print(f"AlphaFold DB: {hit}/{len(prots)} proteins covered")
chem = json.load(open("data/chem/compounds.json")); out, hit = {}, 0
for i, c in enumerate(chem):
    q = urllib.parse.quote(c["name"]); rec = {}
    for prop in ("formula", "mw", "smiles"):
        try:
            r = requests.get(f"https://cactus.nci.nih.gov/chemical/structure/{q}/{prop}", timeout=30)
            if r.status_code == 200 and r.text.strip(): rec[prop] = r.text.strip().split("\n")[0]
        except Exception: pass
        time.sleep(0.15)
    out[str(c["cid"])] = rec or None; hit += bool(rec)
    if i % 50 == 49: print(f"  CACTUS {i+1}/{len(chem)}: {hit} found", flush=True)
Path("data/second_source_cactus.json").write_text(json.dumps(out, indent=1))
print(f"NCI CACTUS: {hit}/{len(chem)} compounds resolved by name")
