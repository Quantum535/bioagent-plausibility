import json, os, time, traceback
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; OUT = Path(__file__).parent
for line in (ROOT / ".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip().strip('"'))
# The model client (openai SDK -> httpx) must ignore proxy/certificate env settings; the agent's database code
# (requests/urllib) still honours them, so only database traffic is routed through the proxy.
import httpx
for _cls in (httpx.Client, httpx.AsyncClient):
    _orig = _cls.__init__
    def _noenv(self, *a, _o=_orig, **k):
        k["trust_env"] = False; return _o(self, *a, **k)
    _cls.__init__ = _noenv
from biomni.agent import A1
tasks = json.load(open(ROOT / "data/tasks_v2.json"))["tasks"][:15] + json.load(open(ROOT / "data/chem/tasks.json"))["tasks"][:10]
agent = A1(path=str(ROOT / "results/biomni_spike/biomni_data"), llm="deepseek-ai/DeepSeek-V4.1-Flash-1017", source="Custom",
           base_url="https://api.together.xyz/v1", api_key=os.environ["TOGETHER_API_KEY"], timeout_seconds=600, expected_data_lake_files=[])
# Proxy settings go in AFTER the agent and its model client exist: the model client read its settings at construction,
# while requests/urllib in the agent's generated code read them on every call, so only database traffic is routed through the proxy.
CA = os.path.expanduser("~/.mitmproxy/combined-ca.pem")
os.environ.update({"HTTPS_PROXY": "http://127.0.0.1:8899", "HTTP_PROXY": "http://127.0.0.1:8899",
                   "NO_PROXY": "api.together.xyz,api.anthropic.com,localhost,127.0.0.1",
                   "SSL_CERT_FILE": CA, "REQUESTS_CA_BUNDLE": CA, "CURL_CA_BUNDLE": CA})
import requests
print("proxy check:", requests.get("https://rest.uniprot.org/uniprotkb/P04637.json", timeout=20).status_code, flush=True)
CUR = Path("/tmp/biomni_current_task")
for t in tasks:
    CUR.write_text(t["task_id"]); os.environ["NETLOG"] = str(OUT / f"net_{t['task_id']}.jsonl"); t0 = time.time()
    try: result = agent.go(t["prompt"])
    except Exception as e: result = f"ERROR {e}\n{traceback.format_exc()[-800:]}"
    (OUT / f"out_{t['task_id']}.json").write_text(json.dumps({"task_id": t["task_id"], "gold": t["gold"], "elapsed": time.time() - t0, "result": str(result)}, indent=1))
    print(f"{t['task_id']}  {time.time()-t0:5.0f}s", flush=True)
CUR.write_text("idle")
