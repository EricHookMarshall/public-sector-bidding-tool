#!/usr/bin/env python3
"""
FWF's B07 Outcome rig — the Learn (Stage 6) domain logic.

Like qualification.py (Triage), bidplan.py (Plan) and clarification.py (Manage),
this is NOT invented: the vocabulary is lifted from FWF's real pipeline `Review`
sheet (Won / Not Won) + the Lessons Learned Log (docs/design/data-model.md §6).
db.py persists a per-bid outcome record; this module supplies the fixed
vocabularies and the cross-bid computations the Learn board performs:
  - outcome_view(o)            — one record enriched with the derived fields (tone,
    score %, whether it's decided/competitive, its library suggestions).
  - library_suggestions(o)     — the promote / refresh / retire actions derived
    from the result + tagged lessons (the loop back into the Stage 4 library).
  - winrate_summary(items)     — the cross-bid win-rate readout ("target win rate,
    tracked bid by bid" — what the framework doc explicitly asks for).

This is the stage that closes the journey loop: an outcome captured here (won/lost,
score, feedback, lessons) is what makes the *next* bid easier — good content gets
promoted, weak content retired, expiring evidence refreshed.

Honest boundary: the *suggested* library updates are derived here, but WRITING
them into the real reusable library needs the SharePoint/MS-Graph connection that
Stage 4 (Complete) is blocked on (see CLAUDE.md hard rules). So Learn captures the
outcome and proposes the updates for a human to approve; the approved changes flow
to the library once that connection is stood up. We don't fake the library write.

Kept here (not in db.py) for the same reason as the sibling rigs: db.py is
persistence; the domain vocabulary lives beside it.
"""
import re

# The bid result (pipeline Review sheet). "Awaiting" is the honest pre-decision
# state — a bid submitted (Stage 5) but not yet awarded; it isn't in the FOR
# enum but it's what a live pipeline actually holds before the buyer decides.
# The other three are the real Review-sheet values.
RESULTS = ["Awaiting", "Won", "Not Won", "Withdrawn"]

# Decided = the buyer/we have closed it out (drops out of "awaiting an outcome").
DECIDED = {"Won", "Not Won", "Withdrawn"}
# Competitive = counts toward the win rate. A withdrawal isn't a competitive loss
# (we pulled out), so it's excluded from the win-rate denominator on purpose.
COMPETITIVE = {"Won", "Not Won"}

# result → kcard tone class (matches PlanStage/ManageStage: go/draft/risk; a
# withdrawn bid has no tone override and shows the neutral base border).
RESULT_TONE = {"Won": "go", "Not Won": "risk", "Withdrawn": "neutral", "Awaiting": "draft"}

# Lessons Learned Log categories — the structured tags a lesson is filed under, so
# lessons roll up across bids rather than sitting as free text. Text-tolerant per
# the PoC (a lesson can be uncategorised).
LESSON_CATEGORIES = [
    "Win theme", "Technical response", "Pricing", "Social value",
    "Compliance / evidence", "Process / admin", "Relationship", "Competitor insight",
]

# What a lesson proposes doing to the reusable library. "" = just a note (no
# library action). The three real actions mirror the Stage-4 library + the
# approved mockup's promote/refresh/retire glyphs.
LIBRARY_ACTIONS = ["", "promote", "refresh", "retire"]


def default_lesson():
    """A blank Lessons Learned row — a categorised note that may carry a library
    action (promote / refresh / retire) to feed back into Stage 4."""
    return {"category": "", "note": "", "action": ""}


def default_outcome():
    """A blank Outcome record (pipeline Review + Lessons Learned). Never persisted
    until the user saves. `result` starts Awaiting — a submitted bid whose award
    isn't in yet — which is exactly what the loop-closing alert chases."""
    return {
        "result": "Awaiting",
        "score_received": "",   # e.g. "88" or "88/100" — text-tolerant
        "max_score": "",        # optional denominator if score_received is bare
        "winner": "",           # who won, if Not Won (competitor intelligence)
        "award_date": "",
        "debrief_date": "",
        "feedback": "",         # buyer / evaluator feedback text
        "lessons": [],          # [{category, note, action}]
        "library_approved": "", # "yes" once a human signs off the suggested updates
        "notes": "",
    }


def _first_number(value):
    """The first number in a string ("88/100" → 88.0, "  92 " → 92.0), or None."""
    if value in (None, ""):
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return float(m.group()) if m else None


def _denominator(value):
    """The denominator in an "x/y" score string ("88/100" → 100.0), or None."""
    if value in (None, ""):
        return None
    m = re.search(r"\d+(?:\.\d+)?\s*/\s*(\d+(?:\.\d+)?)", str(value))
    return float(m.group(1)) if m else None


def score_pct(score_received, max_score=None):
    """A 0–100 percentage from a tolerant score field. Reads "88/100", or a bare
    "88" against `max_score`, or a bare 0–100 as an already-percentage. None if
    there's no usable number."""
    val = _first_number(score_received)
    if val is None:
        return None
    out_of = _first_number(max_score) or _denominator(score_received)
    if out_of and out_of > 0:
        return round(100 * val / out_of)
    if 0 <= val <= 100:      # a bare score in range is treated as a percentage
        return round(val)
    return None


def library_suggestions(outcome):
    """The promote / refresh / retire actions this outcome implies for the Stage-4
    library — the loop-closing suggestions a human then approves.

    Two sources, honestly derived (never invented content):
      - a headline suggestion from the *result* itself (a won bid is prime reuse
        material; a lost bid's flagged answers shouldn't seed the next one unchanged);
      - one suggestion per lesson the planner tagged with a library action.

    Each: {action: promote|refresh|retire, title, detail, auto}. `auto` marks the
    result-derived headline vs a lesson the human wrote. These are proposals —
    writing them into the real library needs the SharePoint connection Stage 4 is
    blocked on, so nothing here mutates the library.
    """
    result = outcome.get("result") or "Awaiting"
    out = []
    if result == "Won":
        out.append({
            "action": "promote", "auto": True,
            "title": "Promote this bid's winning answers to the answer bank",
            "detail": "A won bid is the best reuse material — mark its strongest "
                      "responses reusable so the next bid drafts from them.",
        })
    elif result == "Not Won":
        out.append({
            "action": "refresh", "auto": True,
            "title": "Review the sections the buyer flagged before reusing them",
            "detail": "A lost bid's weak answers shouldn't seed the next one "
                      "unchanged — refresh or retire per the feedback.",
        })

    for lesson in outcome.get("lessons") or []:
        act = (lesson.get("action") or "").strip()
        if act in ("promote", "refresh", "retire"):
            out.append({
                "action": act, "auto": False,
                "title": f"{act.capitalize()} — {lesson.get('category') or 'library item'}",
                "detail": lesson.get("note") or "",
            })
    return out


def outcome_view(o):
    """One Outcome record enriched with the derived fields the UI reads: result
    tone, score %, whether it's decided/competitive, and its library suggestions."""
    result = o.get("result") or "Awaiting"
    return {
        **o,
        "result": result,
        "is_decided": result in DECIDED,
        "is_competitive": result in COMPETITIVE,
        "result_tone": RESULT_TONE.get(result, "neutral"),
        "score_pct": score_pct(o.get("score_received"), o.get("max_score")),
        "suggestions": library_suggestions(o),
    }


def winrate_summary(items):
    """The cross-bid win-rate readout — "target win rate, tracked bid by bid", the
    metric the framework doc explicitly wants.

    `items` are per-bid dicts (outcome_view shape) each carrying a `saved` flag so
    a bid nobody has recorded an outcome for doesn't count as data. Win rate is
    won / (won + not_won) — withdrawals are excluded (not a competitive loss).
    Returns None for win_rate/avg_score when there's nothing to compute, so the UI
    shows "—" rather than a misleading 0%.
    """
    counts = {r: 0 for r in RESULTS}
    scores = []
    recorded = 0
    for it in items:
        if it.get("saved"):
            recorded += 1
        result = it.get("result") or "Awaiting"
        counts[result] = counts.get(result, 0) + 1
        pct = it.get("score_pct")
        if pct is not None:
            scores.append(pct)

    won, not_won = counts.get("Won", 0), counts.get("Not Won", 0)
    competitive = won + not_won
    return {
        "recorded": recorded,
        "decided": competitive + counts.get("Withdrawn", 0),
        "awaiting": counts.get("Awaiting", 0),
        "won": won,
        "not_won": not_won,
        "withdrawn": counts.get("Withdrawn", 0),
        "competitive": competitive,
        "win_rate": round(100 * won / competitive) if competitive else None,
        "avg_score": round(sum(scores) / len(scores)) if scores else None,
        "by_result": counts,
    }


def alerts(items):
    """The Learn board's warnings, computed from real bid data. Ordered
    most-urgent first. Each: {level: crit|warn, text, bid_id?}.

    The loop-closing signal: a bid that was submitted (Stage 5) but whose outcome
    nobody has recorded — the win-rate goes stale and the lessons are lost, which
    is the slow failure this stage exists to prevent. Softer than Manage's alerts
    (no deadline being missed), so these are warn-level nudges, not crits.

    Tolerant of both shapes it's fed: the board-card shape (`suggestions_count` +
    a bool `library_approved`) and the raw outcome_view (`suggestions` list +
    "yes"/"" string).
    """
    out = []
    for it in items:
        title = it.get("title") or f"Bid {it.get('bid_id')}"
        bid_id = it.get("bid_id")
        result = it.get("result") or "Awaiting"
        n = it.get("suggestions_count")
        if n is None:
            n = len(it.get("suggestions") or [])
        approved = bool(it.get("library_approved"))  # True or "yes" → truthy

        # Submitted but no outcome recorded → record it (close the loop).
        if it.get("submitted") and result == "Awaiting":
            out.append({"level": "warn", "bid_id": bid_id,
                        "text": f"{title}: submitted but no outcome recorded yet — "
                                f"capture won/lost + feedback to close the loop"})
        # Decided with library suggestions the human hasn't signed off yet.
        elif result in DECIDED and n and not approved:
            out.append({"level": "warn", "bid_id": bid_id,
                        "text": f"{title}: {result.lower()} — {n} library update"
                                f"{'s' if n != 1 else ''} suggested, awaiting your approval"})
    return out


def reference():
    """The full B07 vocabulary for the UI to render the Learn board + outcome form."""
    return {
        "results": RESULTS,
        "decided": sorted(DECIDED),
        "competitive": sorted(COMPETITIVE),
        "result_tone": RESULT_TONE,
        "lesson_categories": LESSON_CATEGORIES,
        "library_actions": LIBRARY_ACTIONS,
    }


if __name__ == "__main__":
    print("B07 outcome results:", " · ".join(RESULTS))
    print(f"Lessons Learned categories ({len(LESSON_CATEGORIES)}):")
    for c in LESSON_CATEGORIES:
        print(f"  · {c}")
    # Smoke-check the derived maths on a couple of shapes.
    demo = [
        outcome_view({**default_outcome(), "result": "Won", "score_received": "88/100"}),
        outcome_view({**default_outcome(), "result": "Not Won", "score_received": "61",
                      "max_score": "100", "winner": "Incumbent Ltd"}),
        outcome_view({**default_outcome(), "result": "Withdrawn"}),
    ]
    for d in demo:
        d["saved"] = True
    wr = winrate_summary(demo)
    print(f"\nSample win-rate: {wr['win_rate']}% "
          f"({wr['won']} won / {wr['competitive']} competitive), "
          f"avg score {wr['avg_score']}")
