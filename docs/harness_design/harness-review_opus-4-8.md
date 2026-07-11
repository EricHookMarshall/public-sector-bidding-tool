# Harness design review — token economics & stability

**Author:** Claude Opus 4.8 (`claude-opus-4-8[1m]`)
**Date:** 2026-07-10
**Scope:** the project *harness* — `_session/` triad, `.claude/` skills, `CLAUDE.md`,
docs, and `skills/` — assessed for efficient, stable, token-economical operation on a
primarily Opus 4.8 run.

---

## Verdict

The harness *architecture* is good — the triad memory model, the resume/end skill split,
per-skill model routing, and an honest verification culture are all the right shapes. The
weakness is **enforcement**: the one rule that makes the design economical (the handover
stays a disposable one-page hot-state) is not being held, so it is quietly reverting to a
second append-only log. Fix enforcement and the harness delivers the token economics its
design already intends.

---

## What is genuinely good (keep it)

- **`CLAUDE.md` is tight and load-bearing** — 125 lines: clear repo map, the record-shape
  contract (`(source, ocid)` upsert key), hard rules, verification culture. This is the
  strongest asset and reads like a spine, not a scrapbook.
- **The provider-seam + "don't fake it" discipline** keeps an agent honest — `LocalMirror`
  vs live `GraphSharePoint` behind one seam, with an explicit sanctioned/forbidden line.
- **"Quote real results, never claim green you didn't observe"** — the verification rule is
  the whole point of the project and it is stated where it will be read.
- **Skill split is sound and symmetric** — `resume-prompt` executes onboarding; `end-session`
  closes out; each names the docs as source of truth ("if those disagree, the docs win").
- **Per-skill model routing** — `end-session` pins `model: Sonnet, effort: medium` in
  frontmatter. The mechanical doc-shuffle should not burn Opus. Good instinct; extend it.

---

## The core problem: the `_session/` triad has drifted from its own design

Measured on 2026-07-10:

| File | Design intent | Actual |
|---|---|---|
| `_session/handover.md` | "one page… **replace, don't append**" | **228 lines / 18KB**, carrying sessions 13, 11, 10… |
| `_session/progress.md` | cold history, on-demand | 827 lines / 64KB |
| `_session/todo.md` | active queue | 258 lines / 21KB |

`resume-prompt` loads **`CLAUDE.md` + `handover.md` + `todo.md`** every boot ≈ **~44KB
≈ ~11k tokens before any work starts.** On a 1M-context Opus run the *room* exists — but
capacity is not the cost that matters. The real costs:

1. **Signal-to-noise at boot.** The one thing that matters — the **Active task** — is buried
   under three sessions of implementation narration. Opus 4.8 follows a crisp instruction
   well; it does *worse* when the single next action is surrounded by equally-detailed stale
   history it must disambiguate. Bloated boot context dilutes the instruction.
2. **A broken contract.** The triad rests on handover being disposable hot-state and
   `progress.md` being the archive. Right now handover *is* a mini-progress.md — so history
   is paid for twice, and the split that makes the design cheap is defeated.
3. **Anchoring risk.** When handover carries session-10 detail that later sessions superseded,
   the model can anchor on stale facts — the exact "false record" failure mode `CLAUDE.md`
   warns against, reintroduced through the memory doc itself.

---

## Opus 4.8-specific note

4.8 needs *less* redundancy than the harness currently provides. "Six stages live / journey
feature-complete" is stated in `CLAUDE.md`, `README.md`, **and** the handover Status.
Belt-and-suspenders repetition helped weaker models; for 4.8 it is pure boot tax plus a
triple-update burden — three places to keep in sync, three places to drift. Prefer **one
canonical statement + pointers**. Boot-context *quality* matters more than quantity here:
stale content actively degrades outcomes; it does not merely cost tokens.

---

## Recommended changes (prioritized)

1. **Enforce handover ≤ 1 page.** Cut to: Status (one line), Active task, Blockers, Open
   decisions. Move session-10/11/13 narrative to `progress.md` (where it partly lives
   already). Likely halves boot context. *Biggest win, ~15 min.*
2. **Split `todo.md`.** 258 lines is a backlog, not a queue. Keep the top ~15 live items;
   archive the rest to a `todo-archive.md` that does not auto-load. `resume-prompt` should
   not ingest a 21KB backlog.
3. **Add a hard cap to the `end-session` skill.** e.g. "handover must stay under N lines; if
   it grows, move the overflow to `progress.md` before finishing." Nothing currently enforces
   the one-page rule, so it silently rots. Make the skill the enforcement point.
4. **De-duplicate the status boilerplate.** Let `CLAUDE.md` own "where the journey stands";
   have handover/README point to it rather than restate it.
5. **Fold in `/codemap`.** Architecture docs under `docs/design/` are hand-written prose
   (`architecture.md`, 43 lines) that drifts. A code-anchored, regenerable map is cheaper to
   keep true and better for orientation.

---

## Net

The architecture is right — triad model, skill split, model routing, verification culture.
The gap is enforcement of the rule that keeps it economical (handover stays disposable).
Fix that in the `end-session` skill and the harness realizes the token economics it was
already designed for.
