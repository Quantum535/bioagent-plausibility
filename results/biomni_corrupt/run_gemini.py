import json, os, subprocess, time, traceback
REGION = os.environ.get("VERTEX_REGION", "us-central1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; OUT = Path(__file__).parent.parent / "biomni_corrupt_gemini"; OUT.mkdir(exist_ok=True)
for line in (ROOT / ".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip().strip('"'))
import httpx                                   # the model client ignores proxy settings; only database traffic is proxied
for _cls in (httpx.Client, httpx.AsyncClient):
    _orig = _cls.__init__
    def _noenv(self, *a, _o=_orig, **k):
        k["trust_env"] = False; return _o(self, *a, **k)
    _cls.__init__ = _noenv
from biomni.agent import A1
PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
CA = os.path.expanduser("~/.mitmproxy/combined-ca.pem")
os.environ.update({"HTTPS_PROXY": "http://127.0.0.1:8899", "HTTP_PROXY": "http://127.0.0.1:8899",
                   "NO_PROXY": "api.together.xyz,api.anthropic.com,generativelanguage.googleapis.com,googleapis.com,localhost,127.0.0.1",
                   "SSL_CERT_FILE": CA, "REQUESTS_CA_BUNDLE": CA, "CURL_CA_BUNDLE": CA})
CONCERNS = (' End your <solution> with exactly one JSON object {"answer": ..., "concerns": [...]} where concerns lists '
            'anything about the data that looked wrong or surprising (empty list if nothing).')
tasks = json.load(open(ROOT / "data/tasks_v2.json"))["tasks"][:15] + json.load(open(ROOT / "data/chem/tasks.json"))["tasks"][:10]
STATE = Path("/tmp/biomni_current_task")
def new_agent():                               # a fresh agent per run, so nothing carries over between conditions
    return A1(path=str(ROOT / "results/biomni_spike/biomni_data"), llm="google/gemini-4-argon", source="Custom", base_url=f"https://aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/global/endpoints/openapi",
              api_key=subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip(), timeout_seconds=600, expected_data_lake_files=[])
for t in tasks:
    for cond in ("clean", "impossible", "plausible"):
        out = OUT / f"out_{t['task_id']}_{cond}.json"
        if out.exists(): continue              # resumable
        STATE.write_text(json.dumps({"task_id": t["task_id"], "condition": cond}))
        os.environ["NETLOG"] = str(OUT / f"net_{t['task_id']}_{cond}.jsonl"); t0 = time.time()
        try:
            res = new_agent().go(t["prompt"] + CONCERNS)
            final, err = (res[-1] if isinstance(res, (tuple, list)) else str(res)), None
        except Exception as e:
            final, err = "", f"{e}\n{traceback.format_exc()[-800:]}"
        out.write_text(json.dumps({"task_id": t["task_id"], "condition": cond, "elapsed": time.time() - t0, "final": str(final), "error": err}, indent=1))
        print(f"{t['task_id']} {cond:10s} {time.time()-t0:5.0f}s{'  ERROR' if err else ''}", flush=True)
STATE.write_text(json.dumps({"task_id": "idle", "condition": None}))
