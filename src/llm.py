#!/usr/bin/env python3
"""
Provider-agnostic LLM seam for the bidding tool.

Today the tool runs on **Anthropic** (`claude-haiku-4-5` by default — the human
reviews every field, so the cheapest capable model fits; override with
`ANTHROPIC_MODEL`). The client will later
need it on **Azure OpenAI**, so every model call goes through one tiny interface —
`complete_json` — that returns a schema-validated dict. Swapping providers is then
a single-method implementation; the Triage prompt and FOR001 field-mapping
(`triage_ai.py`) never change.

**Why forced tool calling (not `output_config` / `messages.parse`)** for structured
output: it works across SDK versions (incl. the one pinned here) *and* maps 1:1 to
Azure OpenAI's tool/function-calling shape, so the seam stays thin:

    Anthropic:     tools=[{name, input_schema}],                  tool_choice={type:"tool", name}
    Azure OpenAI:  tools=[{type:"function", function:{name, parameters}}], tool_choice={type:"function", ...}

**Secrets** (CLAUDE.md hard rule): the API key is read from the environment by the
SDK (`ANTHROPIC_API_KEY`) — never hardcoded, never sent to the browser. The browser
calls our API; our API calls the model. A missing key/SDK/misconfig degrades to a
clear `LLMUnavailable` (→ HTTP 503), it does not crash — the manual Triage form
keeps working without AI.
"""
import os


class LLMUnavailable(RuntimeError):
    """No usable provider is configured (missing key/SDK, or a provider error).
    The API layer turns this into a 503 so the manual flow still works."""


class LLMProvider:
    name = "base"

    def complete_json(self, *, system, user, schema, tool_name, tool_description, max_tokens=4096):
        """Return a dict validated against `schema` via a single forced tool call."""
        raise NotImplementedError

    def ping(self):
        """Cheap live round-trip to verify credentials + model. Returns
        {provider, model, reply}. Raises LLMUnavailable on any failure."""
        raise NotImplementedError


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, model=None):
        # Default: Haiku 4.5 — this is a structured extraction/drafting task with a
        # human reviewing every field, so the cheapest capable model fits (~5x
        # cheaper than Opus). Bump to claude-opus-4-8 via ANTHROPIC_MODEL if draft
        # quality on the go/no-go judgement proves insufficient.
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")

    def _client(self):
        """Construct the SDK client, degrading (not crashing) if the package or
        key is missing. Returns (anthropic_module, client)."""
        try:
            import anthropic
        except ImportError as e:  # SDK not installed → degrade, don't crash the API
            raise LLMUnavailable("the `anthropic` package is not installed (pip install anthropic)") from e
        if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
            raise LLMUnavailable("ANTHROPIC_API_KEY is not set (add it on the Settings screen)")
        return anthropic, anthropic.Anthropic()  # client reads the key from the environment

    def complete_json(self, *, system, user, schema, tool_name, tool_description, max_tokens=4096):
        anthropic, client = self._client()
        try:
            resp = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                # Forced single-tool call = structured output that validates to `schema`.
                tools=[{"name": tool_name, "description": tool_description, "input_schema": schema}],
                tool_choice={"type": "tool", "name": tool_name},
                messages=[{"role": "user", "content": user}],
            )
        except anthropic.APIError as e:
            raise LLMUnavailable(f"{type(e).__name__}: {e}") from e

        for block in resp.content:
            if getattr(block, "type", None) == "tool_use" and block.name == tool_name:
                return dict(block.input)
        raise LLMUnavailable("model did not return the expected structured tool call")

    def ping(self):
        anthropic, client = self._client()
        try:
            resp = client.messages.create(
                model=self.model,
                max_tokens=8,
                messages=[{"role": "user", "content": "Reply with the single word: ok"}],
            )
        except anthropic.APIError as e:
            raise LLMUnavailable(f"{type(e).__name__}: {e}") from e
        reply = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        return {"provider": self.name, "model": self.model, "reply": reply.strip()[:40]}


# Azure OpenAI is a planned second provider (deferred deliberately — CLAUDE.md:
# "Out of scope is explicit"). The seam is one method (complete_json), so it drops
# in behind this registry once Azure access is provisioned; the design + concrete
# sketch live in docs/design/azure-target.md rather than as commented-out code here.

_PROVIDERS = {
    "anthropic": AnthropicProvider,
}


def get_provider():
    """Resolve the configured provider (LLM_PROVIDER env, default 'anthropic')."""
    key = os.environ.get("LLM_PROVIDER", "anthropic").strip().lower()
    factory = _PROVIDERS.get(key)
    if factory is None:
        raise LLMUnavailable(
            f"unknown LLM_PROVIDER '{key}' (available: {', '.join(sorted(_PROVIDERS))})"
        )
    return factory()
