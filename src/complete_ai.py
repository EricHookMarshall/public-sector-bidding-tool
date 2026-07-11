#!/usr/bin/env python3
"""
AI pre-fill for Complete (Stage 4) — drafts a FOR006 tender answer from FWF's real
bid library so a novice edits rather than faces a blank box. This is the "AI drafts
from past bids / the Approved Answer Bank" piece the journey promises for Complete.

Same shape as triage_ai.py: the prompt is provider-agnostic (llm.py isolates the
model), the draft is **never auto-saved** (the API returns it for review; a person
approves each answer), and it degrades to `LLMUnavailable` (→ 503) so the manual
matrix keeps working without AI.

What makes this Complete-specific: the draft is **retrieval-grounded**. The library
provider (library.py / LocalMirror) supplies the best-matching real LibraryItems for
the question, and the model is told to write *from that evidence* and cite which
items it leaned on — so the answer is anchored to FWF's actual credentials/case
studies, not invented. The answer must respect the question's word-count limit (the
hard compliance gate the tool also checks independently in response.py).
"""
import response as R
from llm import get_provider
from triage_ai import resolve_profile, _guidance_block


def _draft_schema():
    """JSON schema for the AI draft — the answer plus what it drew on, for review."""
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "supplier_response": {"type": "string"},
            "win_themes": {"type": "string"},
            "evidence_used": {"type": "array", "items": {"type": "string"}},
            "gaps": {"type": "string"},
        },
        "required": ["supplier_response", "evidence_used"],
    }


def _prompt(question, matches, guidance=None):
    """Build the user prompt from the FOR006 question + the retrieved library items."""
    limit = question.get("word_count_limit")
    q_lines = "\n".join(
        f"{label}: {val}" for label, val in [
            ("Section", question.get("section")),
            ("Sub-section", question.get("sub_section")),
            ("Question reference", question.get("question_ref")),
            ("Question", question.get("question_text")),
            ("Type", question.get("question_type")),
            ("Weighting %", question.get("weighting_pct")),
            ("Word-count limit", f"{limit} words (do not exceed)" if limit else None),
            ("Tags", question.get("tags")),
        ] if val not in (None, "")
    )
    if matches:
        lib_lines = "\n".join(
            f"  [{m.get('category')}] {m.get('item')} — {m.get('description') or ''}".strip()
            for m in matches
        )
    else:
        lib_lines = "  (no close matches found in the library — draft cautiously and flag the gaps)"

    limit_rule = (f"Keep the answer within {limit} words — an over-length answer can be "
                  f"discarded unread." if limit else "Keep the answer concise.")
    return f"""Draft FWF's answer to this UK public-sector tender question so a non-expert can review
and edit rather than start from a blank page. Ground the answer in the FWF library evidence below —
write from what FWF can actually evidence; do not invent capabilities, certifications or case studies.
Be honest: this tool exists because a missed detail lost a real bid. {limit_rule}

QUESTION (from the FOR006 compliance matrix):
{q_lines}

FWF LIBRARY — best matches (the Approved Answer Bank / evidence register):
{lib_lines}

Write a first-draft answer, name the win themes to emphasise, list which library items you drew on
(`evidence_used`), and flag any gaps where FWF lacks the evidence to back a claim. Record everything
via the tool.{_guidance_block(guidance)}"""


def draft_response(question, matches, profile=None, guidance=None):
    """Draft a FOR006 answer for one question, grounded in retrieved library items.

    `question` is a ResponseItem-shaped dict; `matches` are LibraryItems from
    library.search(). Returns `(draft, meta)`: `draft` carries the answer text +
    the derived live word count so the UI can show the compliance check immediately;
    `meta` carries the win themes / evidence / gaps for the reviewer. Nothing is
    persisted. Raises `LLMUnavailable` (→ 503) if no provider is configured.
    """

    provider = get_provider()
    raw = provider.complete_json(
        system="You are a UK public-sector bid writer for FWF. " + resolve_profile(profile),
        user=_prompt(question, matches, guidance),
        schema=_draft_schema(),
        tool_name="record_response",
        tool_description="Record the drafted FOR006 tender answer for human review.",
        max_tokens=4096,
    )

    answer = raw.get("supplier_response") or ""
    draft = {
        "supplier_response": answer,
        "actual_words": R.word_count(answer),
    }
    meta = {
        "provider": provider.name,
        "model": getattr(provider, "model", None),
        "win_themes": raw.get("win_themes"),
        "evidence_used": raw.get("evidence_used") or [],
        "gaps": raw.get("gaps"),
        "matches_offered": [m.get("item") for m in matches],
    }
    return draft, meta
