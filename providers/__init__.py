import os

from providers.anthropic_p import AnthropicProvider
from providers.openai_p import OpenAICompatProvider
from providers.vertex_p import VertexGeminiProvider


def make_provider(spec, system, tools, thinking="adaptive", effort=None):
    """spec: 'anthropic:claude-sonnet-5', 'openai:<model>', 'together:<org/model>'."""
    if ":" not in spec:
        spec = "anthropic:" + spec  # backward-compatible with bare Claude model names
    kind, model = spec.split(":", 1)
    if kind == "anthropic":
        return AnthropicProvider(model, system, tools, thinking=thinking, effort=effort)
    if kind == "openai":
        return OpenAICompatProvider(model, system, tools, reasoning_effort=effort, name="openai")
    if kind == "gemini":
        return VertexGeminiProvider(model, system, tools, reasoning_effort=effort)
    if kind == "together":
        return OpenAICompatProvider(model, system, tools, name="together",
                                    base_url="https://api.together.xyz/v1",
                                    api_key=os.environ["TOGETHER_API_KEY"])
    raise ValueError(f"unknown provider spec: {spec}")


def safe_name(spec):
    """Model spec made safe for filenames/cache paths."""
    return spec.replace(":", "_").replace("/", "_")
