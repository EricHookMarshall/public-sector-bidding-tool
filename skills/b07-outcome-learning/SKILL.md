---
name: b07-outcome-learning
description: >
  FWF Outcome, Debrief & Library Update. Use this skill after a bid result —
  award, standstill, loss notice, or feedback — to close the learning loop and
  keep the bid library improving. Triggers include: "we won/lost the bid",
  "record the outcome", "run the debrief", "capture the feedback", "update the
  library after this bid", "lessons learned", "post-award review". It records
  the result and evaluator feedback, then produces concrete library actions —
  promote strong answers toward approved, flag criticised/losing answers as do
  not reuse, refresh expiring evidence — plus updates to qualification and
  pricing assumptions. Without this, the library goes stale.
---

# B07 — Outcome, Debrief & Library Update

Closes the loop. Turns every result into improvements to the reuse system, so
the library gets better after every bid instead of slowly rotting.

---

## What this skill does

After award / standstill / loss / feedback:

1. **Records the result** — won / lost / shortlisted / non-compliant / withdrawn.
2. **Captures evaluator scores** — overall and per-answer where available.
3. **Captures buyer feedback** — verbatim where given.
4. **Promotes proven content** — high-scoring answers from won bids → recommend
   `approved` in the Answer Bank.
5. **Retires weak content** — criticised or losing answers → recommend
   `do_not_reuse`.
6. **Refreshes evidence** — time-bound evidence gets a refresh-before-expiry
   action in the Evidence Register.
7. **Updates assumptions** — qualification (B01) inputs, pricing intelligence,
   and win-theme effectiveness for this buyer/sector.
8. **Records lessons learned** — what to repeat, what to change.

`scripts/debrief.py` generates the library-action set from the outcome data.
Actions are recommendations a human applies in SharePoint.

---

## Feeds back into

| Signal | Updates |
|--------|---------|
| Won, high-scoring answers | Answer Bank → approved |
| Criticised / losing answers | Answer Bank → do_not_reuse |
| Expiring evidence | Evidence Register → refresh action |
| Win/loss by buyer/sector | B01 qualification assumptions (win probability, buyer fit) |
| Pricing outcome | B01 pricing-competitiveness calibration |
| Feedback themes | Win themes and answer patterns (B04) |

---

## Bundled parts

- `scripts/debrief.py` — turns outcome data into promote/retire/refresh actions.
- `references/debrief_template.md` — the debrief record layout.

---

## Contract

**Inputs required:** the outcome; per-answer scores/feedback where available;
which records each answer came from.
**Output — human:** a debrief record + a list of library actions to apply.
**Output — machine:** handoff envelope, `stage: outcome_learning`, `outcome`,
`actions_summary`, `next_skill: b00-library-ingestion` (to apply updates).
**Blocking conditions:** none (advisory), but do-not-reuse flags should be
applied promptly so bad content cannot be re-served.
**Human review points:** approving promotions to `approved`; confirming
do_not_reuse; applying actions in SharePoint.
**Do-not-do:** never auto-approve content to the library; never discard buyer
feedback; never leave a losing answer reusable by default.
**SharePoint locations:** reads Bid Submissions Library; recommends updates to
Answer Bank + Evidence Register.
**Definition of done:** outcome and feedback recorded; every answer has a
promote/retire/review action; expiring evidence has a refresh date; B01/pricing
assumptions updated; lessons recorded.

---

## Relationship to other skills

Closes the chain from B06. Its actions flow back through B00 into the library
that B03 retrieves from — the loop that makes the system compound over time.
