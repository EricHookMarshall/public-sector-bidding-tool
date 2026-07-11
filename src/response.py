#!/usr/bin/env python3
"""
FWF's FOR006 Tender Response rig — the Complete (Stage 4) domain logic.

Like the sibling rigs (qualification.py, bidplan.py, clarification.py,
outcome.py), this is NOT invented: the fields are FWF's real `FOR006 Tender
Response Master` — the richest schema in the store, one row per tender question,
the compliance matrix AND the AI-prefill target (data-model.md §4). db.py persists
a per-bid matrix; this module supplies the fixed vocabulary and the computations
the completion board performs:
  - response_view(item)     — one question enriched with the live word count and
    its compliance status (over / within the word limit).
  - matrix_summary(items)   — the completion readout: how many answered, approved,
    and — critically — how many breach their word-count limit.

The word-count check is computed live from the answer text, never trusted from a
stored number: `word_count_limit` vs the actual words is a hard compliance gate on
UK tenders (an over-length answer can be discarded unread), so the tool counts it
itself — the same "derive, don't trust a ticked box" stance as the Manage gate.

Kept here (not in db.py) for the same reason as the other rigs: db.py is
persistence; the domain vocabulary lives beside it.
"""
import re

# The per-question field set is owned authoritatively by db.py (BID_RESPONSE_FIELDS);
# default_response_item() below is the single in-module source for a blank row.

# Completion lifecycle for one answer (drives the matrix board + its status dot).
# FWF's master leaves new rows blank; a blank normalises to "To do".
RESPONSE_STATUSES = ["To do", "Drafted", "In review", "Approved"]

# status → the mock's dot class (d-todo/d-drafted/d-review/d-appr), reused by the UI.
STATUS_DOT = {"To do": "todo", "Drafted": "drafted", "In review": "review", "Approved": "appr"}

# An answer is "done" for the completion bar once a person has approved it.
DONE_STATUSES = {"Approved"}

QUESTION_TYPES = ["Text Response", "Pricing", "Attachment", "Yes/No", "Statement"]


def default_response_item():
    """A blank FOR006 row — the fields captured per tender question."""
    return {
        "customer_document": "", "section": "", "sub_section": "",
        "question_ref": "", "question_text": "", "question_type": "Text Response",
        "weighting_pct": "", "word_count_limit": "", "actual_words": "",
        "images_permitted": "", "attachments_permitted": "", "tags": "",
        "supplier_response": "", "owner": "", "supporting_person": "",
        "reviewer": "", "target_date": "", "status": "To do",
    }


def word_count(text):
    """Words in an answer — whitespace-delimited tokens, the way an evaluator's
    word limit is counted."""
    if not text:
        return 0
    return len(re.findall(r"\S+", str(text)))


def _int(value):
    """First integer in a value ("750 words" → 750), or None."""
    if value in (None, ""):
        return None
    m = re.search(r"\d+", str(value))
    return int(m.group()) if m else None


def response_view(item):
    """One ResponseItem enriched with the derived fields the UI reads: the live word
    count, the word limit, whether it's over, and the normalised status. `actual_words`
    is recomputed from the answer text so the compliance flag can't drift from it."""
    status = item.get("status") or "To do"
    if status not in RESPONSE_STATUSES:
        status = "To do"
    words = word_count(item.get("supplier_response"))
    limit = _int(item.get("word_count_limit"))
    over = limit is not None and words > limit
    answered = bool((item.get("supplier_response") or "").strip())
    return {
        **item,
        "status": status,
        "status_dot": STATUS_DOT.get(status, "todo"),
        "actual_words": words,
        "word_count_limit": limit,
        "over_limit": over,
        "answered": answered,
        "weighting_pct": _int(item.get("weighting_pct")),
    }


def matrix_summary(items):
    """The completion readout from the resolved matrix (response_view shape).

    `over_word_limit` is the compliance red flag — an answer past its limit is a
    submission risk, so it's counted separately from progress. `ready` is true only
    when every question is approved AND nothing breaches its word limit — the
    Complete-stage equivalent of a clean pre-flight.
    """
    total = len(items)
    approved = sum(1 for it in items if it["status"] in DONE_STATUSES)
    answered = sum(1 for it in items if it["answered"])
    over = [it for it in items if it["over_limit"]]
    by_status = {s: sum(1 for it in items if it["status"] == s) for s in RESPONSE_STATUSES}
    return {
        "total": total,
        "answered": answered,
        "approved": approved,
        "over_word_limit": len(over),
        "over_refs": [it.get("question_ref") or "?" for it in over],
        "by_status": by_status,
        "pct_complete": round(100 * approved / total) if total else 0,
        "ready": total > 0 and approved == total and not over,
    }


def reference():
    """The full FOR006 vocabulary for the UI to render the compliance matrix."""
    return {
        "statuses": RESPONSE_STATUSES,
        "status_dot": STATUS_DOT,
        "done_statuses": sorted(DONE_STATUSES),
        "question_types": QUESTION_TYPES,
    }


if __name__ == "__main__":
    print("FOR006 response statuses:", " → ".join(RESPONSE_STATUSES))
    demo = [
        response_view({**default_response_item(), "question_ref": "Q1",
                       "word_count_limit": "750", "status": "Approved",
                       "supplier_response": "word " * 500}),
        response_view({**default_response_item(), "question_ref": "Q2",
                       "word_count_limit": "750", "status": "Drafted",
                       "supplier_response": "word " * 900}),  # over limit
        response_view({**default_response_item(), "question_ref": "Q3",
                       "word_count_limit": "750", "status": "To do"}),
    ]
    s = matrix_summary(demo)
    print(f"matrix: {s['approved']}/{s['total']} approved ({s['pct_complete']}%), "
          f"{s['answered']} answered, {s['over_word_limit']} over word limit "
          f"({', '.join(s['over_refs']) or '—'}), ready={s['ready']}")
