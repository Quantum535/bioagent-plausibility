import anthropic

from providers.base import Provider, Turn, ToolCall

LEGACY = ("claude-haiku-4-5", "claude-sonnet-4-5", "claude-opus-4-5", "claude-sonnet-4-0",
          "claude-opus-4-1", "claude-opus-4-0", "claude-3")
LEGACY_BUDGET_TOKENS = 4000

PRICES = {
    "claude-sonnet-5": (2.0, 10.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-opus-5": (5.0, 25.0),
    "claude-haiku-4-5": (1.0, 5.0),
}


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, model, system, tools, thinking="adaptive", effort=None, max_tokens=8000):
        self.client = anthropic.Anthropic()
        self.model = model
        cfg = {"model": model, "max_tokens": max_tokens, "system": system, "tools": tools}
        legacy = model.startswith(LEGACY)
        if thinking == "disabled":
            if not legacy:
                cfg["thinking"] = {"type": "disabled"}
        elif legacy:
            cfg["thinking"] = {"type": "enabled", "budget_tokens": LEGACY_BUDGET_TOKENS}
        else:
            cfg["thinking"] = {"type": "adaptive"}
        if effort and not legacy:
            cfg["output_config"] = {"effort": effort}
        self.cfg = cfg

    def config(self):
        return dict(self.cfg, provider=self.name)

    def price(self):
        for k, (pi, po) in PRICES.items():
            if self.model.startswith(k):
                return (pi, po, pi * 0.1)
        return (2.0, 10.0, 0.2)

    def user_msg(self, text):
        return {"role": "user", "content": text}

    def complete(self, history, force_no_tools=False):
        kwargs = dict(self.cfg, messages=history)
        if force_no_tools:
            kwargs["tool_choice"] = {"type": "none"}
        resp = self.client.messages.create(**kwargs)
        calls = [ToolCall(b.id, b.name, dict(b.input)) for b in resp.content if b.type == "tool_use"]
        text = "".join(b.text for b in resp.content if b.type == "text")
        u = resp.usage
        return Turn(
            text=text,
            tool_calls=calls,
            stop="tool_use" if resp.stop_reason == "tool_use" else resp.stop_reason,
            usage={
                "input_tokens": u.input_tokens + (getattr(u, "cache_creation_input_tokens", 0) or 0),
                "output_tokens": u.output_tokens,
                "cached_input_tokens": getattr(u, "cache_read_input_tokens", 0) or 0,
            },
            raw=[b.to_dict() for b in resp.content],
            assistant_msg={"role": "assistant", "content": resp.content},
        )

    def tool_result_msg(self, calls, outputs, extra_text=None):
        items = []
        for c, (out, is_err) in zip(calls, outputs):
            item = {"type": "tool_result", "tool_use_id": c.id, "content": out}
            if is_err:
                item["is_error"] = True
            items.append(item)
        if extra_text:
            items.append({"type": "text", "text": extra_text})
        return [{"role": "user", "content": items}]
