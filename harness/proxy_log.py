"""mitmproxy addon: log every request/response to the database APIs, tagged with the current task id."""
import json, os, time
from pathlib import Path
LOG = Path(os.environ["PROXYLOG"]); CUR = Path("/tmp/biomni_current_task")
API = ("uniprot.org", "pubchem.ncbi.nlm.nih.gov", "ebi.ac.uk", "ncbi.nlm.nih.gov", "ensembl")
def _task(): return CUR.read_text().strip() if CUR.exists() else "?"
def _write(**kw):
    with LOG.open("a") as f: f.write(json.dumps({"t": time.time(), "task": _task(), **kw}) + "\n")
def request(flow):
    if any(h in flow.request.pretty_host for h in API):
        _write(event="request", host=flow.request.pretty_host, method=flow.request.method, path=flow.request.path[:300])
def response(flow):
    if any(h in flow.request.pretty_host for h in API):
        _write(event="response", host=flow.request.pretty_host, path=flow.request.path[:300], status=flow.response.status_code,
               ctype=flow.response.headers.get("content-type", ""), size=len(flow.response.raw_content or b""))
