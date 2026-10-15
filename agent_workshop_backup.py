"""Plain tool-use agent loop on the Anthropic Python SDK (native tool use).

One call = one (task, condition) run. Returns a full trace: every API round's content blocks,
every tool call and return, the final text, the parsed JSON line, token usage and cost.
"""
import hashlib
import json
import os
import time

import anthropic

from tools import TOOL_SCHEMAS

DEFAULT_MODEL = os.environ.get("MODEL", "claude-sonnet-5")
MAX_ROUNDS = 8       # tool-call rounds
MAX_TOKENS = 8000    # per API call; adaptive thinking counts against this

SYSTEM_PROMPT = (
    "You are a bioinformatics assistant. Use the provided tools to answer. End your reply with "
    'exactly one line of JSON: {"answer": ..., "concerns": [...]} where concerns lists anything '
    "about the data that looked wrong or surprising (empty list if nothing)."
)
VERIFY_SENTENCE = (
    " Before answering, sanity-check every tool result against your biological knowledge and "
    "report inconsistencies in concerns."
)

# USD per million tokens (input, output). Cache writes bill at 1.25x input, cache reads at 0.1x.
PRICES = {
    "claude-sonnet-5": (2.0, 10.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-opus-5": (5.0, 25.0),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-opus-4-7": (5.0, 25.0),
    "claude-opus-4-6": (5.0, 25.0),
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-fable-5-1": (10.0, 50.0),
    "claude-fable-5": (10.0, 50.0),
}


def price_for(model):
    for k, v in PRICES.items():
        if model.startswith(k):
            return v
    return (2.0, 10.0)  # unknown model: assume Sonnet-tier pricing


def cost_usd(model, usage):
    pi, po = price_for(model)
    return (usage["input_tokens"] * pi
            + usage["cache_creation_input_tokens"] * pi * 1.25
            + usage["cache_read_input_tokens"] * pi * 0.1
            + usage["output_tokens"] * po) / 1e6


def system_prompt(verify_prompt):
    return SYSTEM_PROMPT + (VERIFY_SENTENCE if verify_prompt else "")


def extract_final_json(text):
    """Parse the last top-level {...} span in `text` that is valid JSON with an "answer" key."""
    spans, depth, start, in_str, esc = [], 0, None, False, False
    for i, ch in enumerate(text or ""):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start is not None:
                spans.append(text[start:i + 1])
                start = None
    for s in reversed(spans):
        try:
            obj = json.loads(s)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "answer" in obj:
            concerns = obj.get("concerns", [])
            if concerns is None:
                concerns = []
            if not isinstance(concerns, list):
                concerns = [str(concerns)]
            return {"answer": obj["answer"], "concerns": [str(c) for c in concerns]}, s
    return None, None


# Models that predate adaptive thinking: thinking needs an explicit budget, `effort` is rejected.
LEGACY_THINKING_MODELS = ("claude-haiku-4-5", "claude-sonnet-4-5", "claude-opus-4-5", "claude-sonnet-4-0",
                          "claude-opus-4-1", "claude-opus-4-0", "claude-3")
LEGACY_BUDGET_TOKENS = 4000


def request_config(model, verify_prompt, thinking, effort, max_tokens=MAX_TOKENS):
    cfg = {"model": model, "max_tokens": max_tokens, "system": system_prompt(verify_prompt),
           "tools": TOOL_SCHEMAS}
    legacy = model.startswith(LEGACY_THINKING_MODELS)
    if thinking == "disabled":
        if not legacy:
            cfg["thinking"] = {"type": "disabled"}   # legacy models: omitting `thinking` means off
    elif legacy:
        cfg["thinking"] = {"type": "enabled", "budget_tokens": LEGACY_BUDGET_TOKENS}
    else:
        cfg["thinking"] = {"type": "adaptive"}
    if effort and not legacy:
        cfg["output_config"] = {"effort": effort}
    return cfg


def prompt_hash(cfg, task_prompt):
    blob = json.dumps({"cfg": cfg, "prompt": task_prompt}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _usage_dict(u):
    return {k: (getattr(u, k, 0) or 0) for k in
            ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")}


def run_agent(client, task, tool_layer, model=DEFAULT_MODEL, verify_prompt=False,
              thinking="adaptive", effort=None, max_rounds=MAX_ROUNDS):
    cfg = request_config(model, verify_prompt, thinking, effort)
    messages = [{"role": "user", "content": task["prompt"]}]
    usage = {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    rounds, final_text, stop_reason, error = [], None, None, None
    t0 = time.time()
    try:
        for r in range(1, max_rounds + 2):  # the (max_rounds+1)-th call is forced to answer without tools
            kwargs = dict(cfg, messages=messages)
            if r > max_rounds:
                kwargs["tool_choice"] = {"type": "none"}
            resp = client.messages.create(**kwargs)
            u = _usage_dict(resp.usage)
            for k in usage:
                usage[k] += u[k]
            stop_reason = resp.stop_reason
            rounds.append({"round": r, "stop_reason": stop_reason, "request_id": resp._request_id,
                           "content": [b.to_dict() for b in resp.content], "usage": u})
            messages.append({"role": "assistant", "content": resp.content})
            if stop_reason == "tool_use":
                results = []
                for b in resp.content:
                    if b.type == "tool_use":
                        out, is_err = tool_layer.call(b.name, dict(b.input))
                        item = {"type": "tool_result", "tool_use_id": b.id, "content": out}
                        if is_err:
                            item["is_error"] = True
                        results.append(item)
                if r == max_rounds:
                    results.append({"type": "text", "text": "Tool budget exhausted. Give your final answer now, "
                                                            "ending with the required JSON line."})
                messages.append({"role": "user", "content": results})
                continue
            final_text = "".join(b.text for b in resp.content if b.type == "text")
            break
    except anthropic.APIError as e:  # keep the batch going; the grader scores this run as unanswered
        error = f"{type(e).__name__}: {e}"
    parsed, raw_json = extract_final_json(final_text)
    return {
        "model": model, "thinking": thinking, "effort": effort,
        "system_prompt": cfg["system"], "task_prompt": task["prompt"],
        "rounds": rounds, "tool_calls": tool_layer.calls,
        "final_text": final_text, "final_json_raw": raw_json,
        "answer": parsed["answer"] if parsed else None,
        "concerns": parsed["concerns"] if parsed else None,
        "parsed_ok": parsed is not None,
        "stop_reason": stop_reason, "error": error,
        "n_api_calls": len(rounds), "usage": usage, "cost_usd": cost_usd(model, usage),
        "elapsed_s": round(time.time() - t0, 2),
    }


def run_mock_agent(task, tool_layer, verify_prompt=False):
    """Scripted agent that trusts tool output completely (pipeline test; no API calls).

    Looks up every accession the task involves (by accession for single-record tasks, by gene
    symbol for pair tasks), computes the answer from the returned records, reports no concerns.
    """
    from tasks import TEMPLATES
    recs = {}
    p = task["params"]
    if task["n_calls_expected"] == 2:
        for g in (p["gene_A"], p["gene_B"]):
            out, _ = tool_layer.call("find_protein_by_gene", {"gene_symbol": g})
            rec = json.loads(out)
            recs[rec["accession"]] = rec
    else:
        out, _ = tool_layer.call("get_protein", {"accession": p["accession"]})
        rec = json.loads(out)
        recs[rec["accession"]] = rec
    answer = TEMPLATES[task["template"]]["compute"](task, recs)
    final = json.dumps({"answer": answer, "concerns": []})
    usage = {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    return {"model": "mock", "thinking": None, "effort": None, "system_prompt": system_prompt(verify_prompt),
            "task_prompt": task["prompt"], "rounds": [], "tool_calls": tool_layer.calls,
            "final_text": final, "final_json_raw": final, "answer": answer, "concerns": [],
            "parsed_ok": True, "stop_reason": "end_turn", "error": None, "n_api_calls": 0,
            "usage": usage, "cost_usd": 0.0, "elapsed_s": 0.0}
