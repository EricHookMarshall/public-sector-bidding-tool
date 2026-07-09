#!/usr/bin/env python3
"""
Runtime LLM config for the Settings screen — read current settings, and safely
write provider/model/key into discovery/.env so a novice never hand-edits a
dotfile (the "even a novice" goal). Secrets stay local: `.env` is git-ignored and
the API key is **write-only** — `current()` never returns it, only whether it's
set + its last 4 chars. Writes are whitelisted to the three LLM keys, so this
can't smuggle arbitrary env vars onto the box.
"""
import os

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
DEFAULT_MODEL = "claude-haiku-4-5"

# The models worth offering, cheapest first (cost = input / output per 1M tokens,
# from the current Anthropic pricing). Haiku is the default for this
# review-before-save drafting task; Opus is the escape hatch if quality slips.
MODEL_OPTIONS = [
    {"id": "claude-haiku-4-5", "label": "Claude Haiku 4.5",
     "note": "Fastest & cheapest · $1 / $5 per 1M", "default": True},
    {"id": "claude-sonnet-5", "label": "Claude Sonnet 5",
     "note": "Balanced · $3 / $15 per 1M"},
    {"id": "claude-opus-4-8", "label": "Claude Opus 4.8",
     "note": "Most capable · $5 / $25 per 1M"},
]
MODEL_IDS = {o["id"] for o in MODEL_OPTIONS}

PROVIDER_OPTIONS = [
    {"id": "anthropic", "label": "Anthropic", "available": True},
    {"id": "azure_openai", "label": "Azure OpenAI", "available": False,
     "note": "Planned — not built yet (see llm.py)"},
]
AVAILABLE_PROVIDERS = {o["id"] for o in PROVIDER_OPTIONS if o["available"]}

# Only these may be written to .env from the Settings screen.
_ALLOWED_KEYS = {"LLM_PROVIDER", "ANTHROPIC_MODEL", "ANTHROPIC_API_KEY"}


def key_status():
    """Non-secret view of the API key: is it set, and its last 4 chars."""
    k = os.environ.get("ANTHROPIC_API_KEY") or ""
    return {"set": bool(k), "last4": k[-4:] if len(k) >= 4 else None}


def current():
    """The full non-secret config the Settings screen renders. Never returns the key."""
    return {
        "provider": os.environ.get("LLM_PROVIDER", "anthropic"),
        "providers": PROVIDER_OPTIONS,
        "model": os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL),
        "model_default": DEFAULT_MODEL,
        "models": MODEL_OPTIONS,
        "key_status": key_status(),
    }


def _read_lines():
    if not os.path.exists(ENV_PATH):
        return []
    with open(ENV_PATH, encoding="utf-8") as fh:
        return fh.read().splitlines()


def upsert_env(updates):
    """Write whitelisted key=value pairs into .env (preserving other lines and
    comments) and update os.environ so the change takes effect without a restart.
    Silently ignores non-whitelisted keys and None values."""
    updates = {k: v for k, v in updates.items() if k in _ALLOWED_KEYS and v is not None}
    if not updates:
        return
    out, seen = [], set()
    for line in _read_lines():
        s = line.strip()
        if s and not s.startswith("#") and "=" in s:
            existing_key = s.split("=", 1)[0].strip()
            if existing_key in updates:
                out.append(f"{existing_key}={updates[existing_key]}")
                seen.add(existing_key)
                continue
        out.append(line)
    for key, val in updates.items():
        if key not in seen:
            out.append(f"{key}={val}")
    with open(ENV_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out).rstrip("\n") + "\n")
    # Override (not setdefault) — the user just chose this, it wins immediately.
    for key, val in updates.items():
        os.environ[key] = val
