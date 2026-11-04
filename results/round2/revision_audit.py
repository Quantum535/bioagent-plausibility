"""Why was each of the 79 superseded UniProt sequences revised? Run from the repository root."""
import json, os, time, urllib.request, urllib.error, collections
from Bio.SeqUtils.CheckSum import crc64
C = "results/round2/revision_audit_cache.json"; cache = json.load(open(C)) if os.path.exists(C) else {}
def get(url, accept="*/*", tries=2):
    if url in cache: return cache[url]
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "bioagent-plausibility audit"}), timeout=15) as r:
                cache[url] = r.read().decode(); return cache[url]
        except urllib.error.HTTPError as e:
            if e.code < 500: return None
            time.sleep(1 + i)
        except Exception: time.sleep(1 + i)
    return None
UNIPARC_UP = True
REST_UP = True
def uniparc(acc, o):
    """Return (UPI, cross-references as dicts with database, id, active) for sequence o among the UniParc entries of accession acc."""
    global UNIPARC_UP, REST_UP
    if not UNIPARC_UP: return "pending", []
    j = get(f"https://rest.uniprot.org/uniparc/search?query=accession:{acc}&format=json&size=50") if REST_UP else None
    if j is None: REST_UP = False
    if j:
        for r in json.loads(j).get("results", []):
            if (r.get("sequence") or {}).get("value") == o:
                xr = r.get("uniParcCrossReferences") or []
                if not xr:
                    d = get(f"https://rest.uniprot.org/uniparc/{r['uniParcId']}/databases?format=json&size=500"); xr = json.loads(d).get("results", []) if d else []
                return r["uniParcId"], [{"database": x.get("database"), "id": x.get("id"), "active": x.get("active")} for x in xr]
        return None, []
    j = get(f"https://www.ebi.ac.uk/proteins/api/uniparc?accession={acc}&size=-1", accept="application/json")
    if j:
        for r in json.loads(j):
            if (r.get("sequence") or {}).get("content") == o:
                return r.get("accession"), [{"database": x.get("type"), "id": x.get("id"), "active": x.get("active") in (True, "Y")} for x in r.get("dbReference", [])]
        return None, []
    UNIPARC_UP = False; return "pending", []
def fasta(txt):
    out, h = {}, None
    for l in (txt or "").splitlines():
        if l.startswith(">"): h = l[1:].split()[0]; out[h] = ""
        elif h: out[h] += l.strip()
    return out
old = json.load(open("data/unisave_old_sequences.json"))
full = json.load(open("data/uniprot_full.json")); full = {e["primaryAccession"]: e for e in (full if isinstance(full, list) else full.values())}
ERR = {"Erroneous initiation", "Frameshift", "Erroneous gene model prediction", "Erroneous termination", "Erroneous translation"}
UNI = ("UniProtKB/Swiss-Prot", "UniProtKB/TrEMBL", "UniProtKB/Swiss-Prot protein isoforms")
res = []
for n, t in enumerate(json.load(open("data/phase5_tasks.json"))["tasks"]):
    acc = t["target_accession"]; c = t["corruptions"]["superseded"]; e = full[acc]; cur = e["sequence"]["value"]
    o = next(x["sequence"] for x in old[acc] if x["seq_version"] == c["seq_version"])
    p = 0
    while p < min(len(o), len(cur)) and o[p] == cur[p]: p += 1
    s = 0
    while s < min(len(o), len(cur)) - p and o[-1 - s] == cur[-1 - s]: s += 1
    loc = "N-terminal" if p < 3 else "C-terminal" if s < 3 else "internal"
    iso = fasta(get(f"https://rest.uniprot.org/uniprotkb/search?query=accession:{acc}&includeIsoform=true&format=fasta&size=50"))
    iso_acc = [h.split("|")[1] for h, sq in iso.items() if sq == o and "|" in h]
    upi, xr = uniparc(acc, o)
    embl = {str(x.get("id", "")).split(".")[0] for x in xr if "EMBL" in str(x.get("database", ""))}
    active = sorted({str(x.get("database")) for x in xr if x.get("active") and x.get("database") not in UNI and "EMBL" not in str(x.get("database"))})
    caut = sorted({cc.get("sequenceCautionType") for cc in e.get("comments", []) if cc.get("commentType") == "SEQUENCE CAUTION" and str(cc.get("sequence", "")).split(".")[0] in embl})
    if any("-" in a for a in iso_acc): cls = "current isoform"
    elif set(caut) & ERR: cls = "documented error"
    elif caut: cls = "flagged discrepancy"
    elif active: cls = "matches a current " + "/".join(active) + " model"
    elif upi == "pending": cls = "pending (UniParc unavailable)"
    elif not upi: cls = "not found in UniParc"
    else: cls = "retired, reason not recorded"
    res.append({"task": t["task_id"], "accession": acc, "d_length": c.get("d_length"), "direction": c.get("direction"), "location": loc, "class": cls,
                "caution_types": caut, "isoform_match": iso_acc, "uniparc": upi, "n_xrefs": len(xr), "active_in": active})
    if n == 0: print("first protein:", acc, "| isoforms fetched:", len(iso), "| UniParc:", upi, "| cross-references:", len(xr), "| sample:", json.dumps(xr[:1])[:200])
    print(f"  {n + 1}/79 {acc} {cls}", flush=True)
    if n % 10 == 9: json.dump(cache, open(C, "w"))
json.dump(cache, open(C, "w")); json.dump(res, open("results/round2/revision_audit.json", "w"), indent=1)
print("\nclass:", dict(collections.Counter(r["class"] for r in res)))
print("location:", dict(collections.Counter(r["location"] for r in res)))
print("caution types among documented errors:", dict(collections.Counter(x for r in res for x in r["caution_types"])))
print("class by size of change:", dict(collections.Counter((r["class"], "1-5" if abs(r["d_length"] or 0) <= 5 else "6-50" if abs(r["d_length"] or 0) <= 50 else ">50") for r in res)))
