"""mitmproxy addon: cache genuine UniProt/PubChem responses, and corrupt one field of one record in transit.
The runner writes the current task and condition to /tmp/biomni_current_task as JSON."""
import base64, csv, hashlib, io, json, os, re, time
from pathlib import Path
from urllib.parse import unquote
from mitmproxy import http

ROOT = Path.cwd()
LOG = Path(os.environ["PROXYLOG"]); STATE = Path(os.environ.get("AGENT_STATE", "/tmp/biomni_current_task"))
SCHED = json.load(open(os.environ["RERUN_SCHEDULE"])) if os.environ.get("RERUN_SCHEDULE") else None  # slot -> condition, per task
CACHE = ROOT / "harness" / "cache"; CACHE.mkdir(parents=True, exist_ok=True)
TASKS = {t["task_id"]: t for p in ("data/tasks_v2.json", "data/chem/tasks.json") for t in json.load(open(ROOT / p))["tasks"]}
NAMES = {str(c["cid"]): c["name"].lower() for c in json.load(open(ROOT / "data/chem/compounds.json"))}
HOSTS = ("rest.uniprot.org", "pubchem.ncbi.nlm.nih.gov")
UNI_JSON = {"length": ("sequence", "length"), "mass": ("sequence", "molWeight"),
            "organism": ("organism", "scientificName"), "gene_symbol": ("genes", 0, "geneName", "value")}
UNI_TSV = {"length": ("Length",), "mass": ("Mass",), "organism": ("Organism",), "gene_symbol": ("Gene Names (primary)", "Gene Names")}
UNI_FASTA = {"organism": r"(OS=)(.*?)(?= OX=)", "gene_symbol": r"(GN=)(\S+)"}
PUB = {"molecular_weight": "MolecularWeight", "heavy_atom_count": "HeavyAtomCount", "h_bond_donors": "HBondDonorCount", "name": "Title"}


def _state():
    try: s = json.loads(STATE.read_text())
    except Exception: return "?", None, None
    cond = SCHED[s["task_id"]][str(s["slot"])] if (SCHED and "slot" in s and s.get("task_id") in SCHED) else s.get("condition")
    t = TASKS.get(s.get("task_id"))
    if t is None or cond in (None, "clean"): return s.get("task_id", "?"), cond, None
    return s["task_id"], cond, t


def _log(**kw):
    with LOG.open("a") as f: f.write(json.dumps({"t": time.time(), **kw}, default=str) + "\n")


def _key(flow):
    return hashlib.sha1(f"{flow.request.method} {flow.request.pretty_host}{flow.request.path}".encode()).hexdigest()


def _num(old, v):
    """Write the corrupted value in the type the source used."""
    if isinstance(v, str) or isinstance(old, bool): return v
    if isinstance(old, int): return int(round(v))
    if isinstance(old, float): return float(v)
    if isinstance(old, str): return str(int(round(v))) if re.fullmatch(r"-?\d+", old.strip()) else str(v)
    return v


def uni_json(text, target, fields):
    d = json.loads(text); hits, seen = {}, False
    for e in (d.get("results", [d]) if isinstance(d, dict) else []):
        if not isinstance(e, dict) or e.get("primaryAccession") != target: continue
        seen = True
        for f, v in fields.items():
            path = UNI_JSON.get(f); node = e
            if not path: continue
            try:
                for p in path[:-1]: node = node[p]
                old = node[path[-1]]
            except (KeyError, IndexError, TypeError): continue
            node[path[-1]] = _num(old, v); hits[f] = (old, node[path[-1]])
    return json.dumps(d, separators=(",", ":"), ensure_ascii=False), hits, seen


def uni_flat(text, target, fields):
    """UniProt flat-file (.txt): ID/SQ carry length, SQ carries mass, OS organism, GN gene symbol."""
    hits, seen = {}, False
    if not re.search(rf"^AC   {re.escape(target)};", text, re.M): return text, hits, seen
    seen = True
    def sub(pat, repl, f, flags=re.M):
        nonlocal text
        m = re.search(pat, text, flags)
        if m: hits.setdefault(f, (m.group(2), str(repl))); text = re.sub(pat, lambda g: g.group(1) + str(repl) + g.group(3), text, count=1, flags=flags)
    if "length" in fields:
        v = int(round(fields["length"])); sub(r"(^ID   \S+\s+\S+\s+)(\d+)( AA\.)", v, "length"); sub(r"(^SQ   SEQUENCE\s+)(\d+)( AA;)", v, "length")
    if "mass" in fields: sub(r"(^SQ   SEQUENCE\s+\d+ AA;\s+)(-?\d+)( MW;)", int(round(fields["mass"])), "mass")
    if "organism" in fields: sub(r"(^OS   )([^\n(]+?)(\s*\(|\.$|$)", fields["organism"] + " ", "organism")
    if "gene_symbol" in fields: sub(r"(^GN   Name=)([^;{]+)(;| \{)", fields["gene_symbol"], "gene_symbol")
    return text, hits, seen


def uni_text(text, target, fields):
    hits, seen = {}, False
    if text.startswith("ID   "): return uni_flat(text, target, fields)
    if text.startswith(">"):                                   # FASTA
        lines = text.split("\n")
        for i, ln in enumerate(lines):
            m = re.match(r">\w+\|([^|]+)\|", ln)
            if not m or m.group(1) != target: continue
            seen = True
            for f, v in fields.items():
                pat = UNI_FASTA.get(f); mm = re.search(pat, ln) if pat else None
                if mm: hits[f] = (mm.group(2), v); ln = re.sub(pat, lambda g: g.group(1) + str(v), ln, count=1)
            lines[i] = ln
        return "\n".join(lines), hits, seen
    rows = text.split("\n"); hdr = rows[0].split("\t")            # TSV
    if "Entry" not in hdr: return text, hits, seen
    ei = hdr.index("Entry")
    for r, line in enumerate(rows[1:], 1):
        cells = line.split("\t")
        if len(cells) != len(hdr) or cells[ei] != target: continue
        seen = True
        for f, v in fields.items():
            for col in UNI_TSV.get(f, ()):
                if col not in hdr: continue
                j = hdr.index(col); old = cells[j]
                if col == "Gene Names": parts = old.split(" "); parts[0] = str(v); cells[j] = " ".join(parts)
                else: cells[j] = str(_num(old, v))
                hits.setdefault(f, (old, cells[j]))
        rows[r] = "\t".join(cells)
    return "\n".join(rows), hits, seen


def _pub_index(path, target):
    m = re.search(r"/compound/cid/([\d,]+)/", path)
    if m:
        ids = m.group(1).split(","); return ids.index(target) if target in ids else None
    m = re.search(r"/compound/name/([^/]+)/", path)
    return 0 if m and unquote(m.group(1)).strip().lower() == NAMES.get(target) else None


def pub(text, ctype, path, target, fields):
    hits, seen = {}, False
    if ctype == "application/json":
        d = json.loads(text)
        for p in (d.get("PropertyTable") or {}).get("Properties", []):
            if str(p.get("CID")) != target: continue
            seen = True
            for f, v in fields.items():
                k = PUB.get(f)
                if k in p: old = p[k]; p[k] = _num(old, v); hits[f] = (old, p[k])
        for info in (d.get("InformationList") or {}).get("Information", []):
            if str(info.get("CID")) != target: continue
            seen = True
            if "name" in fields and info.get("Synonym"):
                old = info["Synonym"][0]; info["Synonym"][0] = fields["name"]; hits["name"] = (old, fields["name"])
        return json.dumps(d, separators=(",", ":"), ensure_ascii=False), hits, seen
    if ctype == "text/csv":
        rows = list(csv.reader(io.StringIO(text)))
        if not rows or "CID" not in rows[0]: return text, hits, seen
        hdr = rows[0]; ci = hdr.index("CID")
        for row in rows[1:]:
            if len(row) != len(hdr) or row[ci] != target: continue
            seen = True
            for f, v in fields.items():
                k = PUB.get(f)
                if k in hdr: j = hdr.index(k); old = row[j]; row[j] = str(_num(old, v)); hits[f] = (old, row[j])
        buf = io.StringIO(); csv.writer(buf, lineterminator="\n").writerows(rows); return buf.getvalue(), hits, seen
    if ctype == "text/plain":
        i = _pub_index(path, target); m = re.search(r"/property/([^/]+)/TXT", path)
        if i is None or not m: return text, hits, seen
        seen = True; lines = text.rstrip("\n").split("\n")
        for f, v in fields.items():
            if PUB.get(f) == m.group(1) and i < len(lines): old = lines[i]; lines[i] = str(_num(old, v)); hits[f] = (old, lines[i])
        return "\n".join(lines) + "\n", hits, seen
    return text, hits, seen


def request(flow):
    if flow.request.pretty_host not in HOSTS: return
    f = CACHE / f"{_key(flow)}.json"
    if f.exists():
        c = json.loads(f.read_text())
        flow.response = http.Response.make(c["status"], base64.b64decode(c["body"]), c["headers"]); flow.metadata["cached"] = True


def response(flow):
    if flow.request.pretty_host not in HOSTS: return
    cached = bool(flow.metadata.get("cached"))
    if not cached and flow.response.status_code == 200:          # store the genuine record before any corruption
        (CACHE / f"{_key(flow)}.json").write_text(json.dumps({"status": 200, "headers": {k: v for k, v in flow.response.headers.items() if k.lower() not in ("content-encoding", "content-length", "transfer-encoding")},
                                                              "body": base64.b64encode(flow.response.content or b"").decode()}))
    tid, cond, t = _state()
    ctype = flow.response.headers.get("content-type", "").split(";")[0].strip()
    base = dict(task=tid, condition=cond, host=flow.request.pretty_host, path=flow.request.path[:300],
                status=flow.response.status_code, ctype=ctype, cached=cached)
    _log(event="response", **base)
    if t is None or flow.response.status_code != 200: return
    target, fields = str(t["target_accession"]), t["corruptions"][cond]["fields"]
    try:
        text = flow.response.get_text(strict=False)
        if "uniprot" in flow.request.pretty_host:
            new, hits, seen = uni_json(text, target, fields) if ctype == "application/json" else uni_text(text, target, fields)
        else:
            new, hits, seen = pub(text, ctype, flow.request.path, target, fields)
    except Exception as e:
        _log(event="corrupt_error", error=f"{type(e).__name__}: {e}"[:300], **base); return
    if hits: flow.response.set_text(new); _log(event="corrupt", fields=hits, **base)
    elif seen: _log(event="target_unaltered", **base)
