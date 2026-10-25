import json, os, subprocess, time, traceback
REGION = os.environ.get("VERTEX_REGION", "us-central1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; OUT = Path(__file__).parent.parent / "biomni_full_flash"; OUT.mkdir(exist_ok=True)
for line in (ROOT / ".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip().strip('"'))
import httpx                                   # the model client ignores proxy settings; only database traffic is proxied
for _cls in (httpx.Client, httpx.AsyncClient):
    _orig = _cls.__init__
    def _noenv(self, *a, _o=_orig, **k):
        k["trust_env"] = False; return _o(self, *a, **k)
    _cls.__init__ = _noenv
# Biomni appends tool observations as assistant messages (a1.py:1464), so requests can end with a model turn,
# which Gemini and Anthropic reject. Relabel a trailing assistant turn as a user turn and merge adjacent user turns.
import openai._base_client as _obc
_orig_build = _obc.BaseClient._build_request
def _build(self, options, *a, **k):
    jd = getattr(options, "json_data", None)
    msgs = jd.get("messages") if isinstance(jd, dict) else None
    if msgs and msgs[-1].get("role") == "assistant":
        msgs[-1]["role"] = "user"
        merged = []
        for m in msgs:
            if merged and merged[-1]["role"] == "user" == m.get("role") and isinstance(m.get("content"), str) and isinstance(merged[-1].get("content"), str):
                merged[-1]["content"] += "\n\n" + m["content"]
            else: merged.append(m)
        jd["messages"] = merged
    return _orig_build(self, options, *a, **k)
_obc.BaseClient._build_request = _build
# Vertex sometimes returns a choice with message=null (blocked/empty response); hand langchain an empty assistant message instead of crashing
import langchain_openai.chat_models.base as _lob
_orig_conv = _lob._convert_dict_to_message
_lob._convert_dict_to_message = lambda d: _orig_conv(d if d is not None else {"role": "assistant", "content": ""})
from biomni.agent import A1
PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
CA = os.path.expanduser("~/.mitmproxy/combined-ca.pem")
os.environ.update({"HTTPS_PROXY": "http://127.0.0.1:8899", "HTTP_PROXY": "http://127.0.0.1:8899",
                   "NO_PROXY": "api.together.xyz,api.anthropic.com,generativelanguage.googleapis.com,googleapis.com,localhost,127.0.0.1",
                   "SSL_CERT_FILE": CA, "REQUESTS_CA_BUNDLE": CA, "CURL_CA_BUNDLE": CA})
CONCERNS = (' End your <solution> with exactly one JSON object {"answer": ..., "concerns": [...]} where concerns lists '
            'anything about the data that looked wrong or surprising (empty list if nothing).')
tasks = json.load(open(ROOT / "data/tasks_v2.json"))["tasks"] + json.load(open(ROOT / "data/chem/tasks.json"))["tasks"]
STATE = Path("/tmp/biomni_current_task")
def new_agent():                               # a fresh agent per run, so nothing carries over between conditions
    return A1(path=str(ROOT / "results/biomni_spike/biomni_data"), llm="google/gemini-3.8-flash", source="Custom", base_url=f"https://aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/global/endpoints/openapi",
              api_key=subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip(), timeout_seconds=600, expected_data_lake_files=[])
for t in tasks:
    for cond in ("clean", "impossible", "plausible"):
        out = OUT / f"out_{t['task_id']}_{cond}.json"
        if out.exists(): continue              # resumable
        STATE.write_text(json.dumps({"task_id": t["task_id"], "condition": cond}))
        os.environ["NETLOG"] = str(OUT / f"net_{t['task_id']}_{cond}.jsonl"); t0 = time.time()
        final, err = "", None
        for attempt in range(4):                      # retry on rate limits with backoff
            try:
                res = new_agent().go(t["prompt"] + CONCERNS)
                final, err = (res[-1] if isinstance(res, (tuple, list)) else str(res)), None; break
            except Exception as e:
                err = f"{e}\n{traceback.format_exc()[-800:]}"
                if "429" in str(e) and attempt < 3: time.sleep(30 * 2 ** attempt); continue
                break
        out.write_text(json.dumps({"task_id": t["task_id"], "condition": cond, "elapsed": time.time() - t0, "final": str(final), "error": err}, indent=1))
        print(f"{t['task_id']} {cond:10s} {time.time()-t0:5.0f}s{'  ERROR' if err else ''}", flush=True)
STATE.write_text(json.dumps({"task_id": "idle", "condition": None}))
