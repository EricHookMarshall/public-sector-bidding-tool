# Harness Design Review — GPT-5

**Date:** 2026-07-10  
**Scope:** `CLAUDE.md`, `_session/`, project skills, supporting documentation,
verification discipline, and token economics  
**Primary target runner:** Claude 4.8

## Executive summary

The project has a strong agent harness in concept. It clearly defines the
product, architectural boundaries, confidentiality rules, human approval
points, and an evidence-led bidding workflow. The B00–B07 skill chain is
particularly thoughtful about deterministic gates, provenance, and preventing
unsupported content from reaching a submission.

The principal weakness is no longer missing documentation. It is overlapping
documentation that has begun to diverge. Current state, historical state,
roadmap, verification evidence, and operating instructions are repeated across
`CLAUDE.md`, `README.md`, `_session/handover.md`, `_session/todo.md`, and the
skills. This increases onboarding cost and gives Claude several competing
versions of the truth.

The recommended direction is therefore **subtraction and consolidation**:

1. Establish an explicit source-of-truth hierarchy.
2. Make the session hot state genuinely small.
3. Move completed work out of the active queue.
4. Add one canonical, deterministic verification command.
5. Make the application domain logic canonical and have skills orchestrate it.
6. Expose the B-series through Claude's actual project-skill discovery path.
7. Add a small machine-readable current-state file.

Indicative assessment:

| Area | Assessment |
|---|---:|
| Intent and structure | 8/10 |
| Current truthfulness and consistency | 5/10 |
| Token economics | 5/10 |
| Deterministic verification | 4/10 |
| Claude-centric skill discoverability | 6/10 |

## What is already strong

### `CLAUDE.md` provides an effective project spine

The file gives an agent the information it needs to act responsibly:

- The product objective and six-stage journey.
- Repository topology and principal architectural seams.
- Commands for running the backend and frontend.
- Stable data-model and deduplication invariants.
- Confidentiality and secrets boundaries.
- A clear instruction to verify rather than inherit assertions blindly.
- Honest external blockers such as live Graph/SharePoint provisioning.

This is the right purpose for `CLAUDE.md`: stable project context and working
constraints that should apply across tasks and sessions.

### The session-memory model is sound in principle

The intended separation is useful:

- `_session/handover.md` — current hot state.
- `_session/todo.md` — active queue.
- `_session/progress.md` — cold historical record.

This model can give Claude fast continuity without requiring it to rediscover
the repository. The problem is enforcement, not the underlying design.

### The B00–B07 chain contains strong outcome controls

The most valuable features of the skills are:

- `UNKNOWN` is explicit and blocking where eligibility is affected.
- Human decisions are separated from model recommendations.
- Machine-readable handoffs are defined.
- Claims require evidence and provenance.
- Drafting, red-team review, preflight, submission, and learning are distinct.
- Deterministic helper scripts own repeatable calculations and checks.
- The lifecycle closes through outcome capture and library maintenance.

These controls are more important to reliable bid outcomes than adding more
general-purpose prompting.

## Findings

### 1. The hot-state discipline has degraded

The handover describes itself as a one-page file that is replaced rather than
appended. It is currently approximately 228 lines and contains material from
multiple earlier sessions, detailed verification results, settled decisions,
operational instructions, and parked workstreams.

The active queue is approximately 258 lines and mixes:

- Current work.
- Completed milestones.
- Historical verification evidence.
- Review findings.
- Deferred work.
- Items whose commit state is now stale.

The historical progress file is approximately 827 lines. Its size is not a
problem by itself because it is intended to remain cold. It becomes expensive
only when an agent loads it without a task-specific reason.

The `/resume-prompt` workflow currently directs Claude to read roughly 600
lines across the project spine, handover, and queue before inspecting relevant
code. Loading progress as well raises this to roughly 1,400 lines. Depending on
content density, this can consume tens of thousands of tokens before productive
work begins.

More context is not always safer. When current and historical statements are
mixed, additional context increases the chance that the model selects a stale
instruction or state claim.

**Recommendation**

- Limit `handover.md` to 60–80 lines.
- Keep only unfinished work in `todo.md`.
- Do not load `progress.md` during normal resume.
- Archive completed review waves in their dated review documents.
- Keep stable operating instructions in `CLAUDE.md`, not session files.

### 2. Several sources of truth contradict one another

Material contradictions observed during the review include:

- `CLAUDE.md` says all six stages are feature-complete, while its repository map
  still calls Complete, Manage, and Learn preview screens.
- `README.md` says those stages are previews and that Complete is blocked on
  SharePoint, while the application now uses the sanctioned `LocalMirror` over
  the real gitignored export.
- `_session/todo.md` describes some committed work as uncommitted.
- The queue retains older milestone actions that have been superseded.
- The skill documentation says the historical source is Google Drive while the
  current application and project spine describe a local SharePoint export.

This is the most important stability issue. Claude cannot reliably resolve
several documents that all present themselves as authoritative but describe
different project states.

**Recommended authority order**

1. Executable code and automated tests.
2. Machine-readable current project state.
3. `CLAUDE.md` for stable invariants and operating rules.
4. `_session/handover.md` for the immediate next action.
5. `_session/todo.md` for unfinished work.
6. README and design documentation.
7. Historical progress and reviews.

The authority order should be stated explicitly in `CLAUDE.md`.

### 3. The B-series skills may not be naturally discoverable by Claude

The operational resume and end-session skills are under `.claude/skills`, which
is an appropriate project-level discovery location. The B00–B07 skills are
under the repository's `skills/` directory. Unless the Claude environment is
explicitly configured to install or load that directory, they may function as
documentation rather than automatically invocable project skills.

There are also two tender-sweep variants with the same skill name,
`fwf-tender-sweep`. Duplicate names make routing and invocation ambiguous.

**Recommendation**

Use one of these patterns:

1. Install each B-series skill into Claude's supported project-skill location.
2. Preferably, expose one small project-level bid-workflow router that selects
   and reads only the relevant B-series skill.

The router approach offers better token economics because qualifying an
opportunity does not require loading drafting, clarification, and outcome
instructions.

Rename the tender-sweep variants or combine them into one skill with an
explicit audience/output mode.

### 4. The skills and application are becoming parallel implementations

The helper scripts and the application now both implement concepts such as
qualification, compliance, clarification, preflight, and outcome learning.
Without a canonical layer, they will continue to diverge on:

- Status and action names.
- Required fields.
- Blocking conditions.
- Deadline thresholds.
- Scoring rules.
- Outcome-to-library actions.

This creates a risk that the conversational skill recommends one outcome while
the application calculates another.

**Recommendation**

Make the application domain modules canonical. Skills should gather inputs,
invoke or conform to the canonical domain functions and schemas, explain the
result, and request human decisions where required.

The desired pattern is:

```text
Claude skill
    -> collect and validate inputs
    -> invoke canonical deterministic domain function
    -> explain the result and unresolved evidence
    -> pause at the defined human decision point
```

Claude should own interaction and contextual judgement. Deterministic code
should own calculations, enums, blocking rules, and repeatable gates.

### 5. Verification is honest but predominantly procedural

The session records show extensive ad hoc verification and are careful not to
claim checks that were not observed. That discipline is excellent.

However, the repository does not currently expose a committed test suite, CI
workflow, pre-commit configuration, or single root verification command. Each
session must reconstruct what constitutes a proportionate green check. This is
expensive and makes omissions more likely.

**Recommendation**

Add one canonical command, for example `make check`, `just check`, or a small
versioned verification script. It should provide a fast default ladder:

1. Backend import and application construction.
2. Unit tests for deadline parsing, qualification, auth, preflight, and other
   high-consequence domain rules.
3. Frontend production build.
4. Optional integration or live-source tests behind explicit flags.
5. A lightweight documentation-state consistency check.

A single deterministic command is both more stable and more token-efficient
than asking Claude to infer and narrate a different verification plan each
session.

### 6. The end-session procedure is more expensive than necessary

The end-session skill currently asks the agent to reconstruct the session,
replace the handover, prepend a full progress entry, update the active queue,
stop services, and potentially reconcile prior claims. This is thorough, but it
creates substantial documentation churn for small sessions.

It also describes `progress.md` as both "append-only" and prepended, which is
understandable to a human but imprecise as an operational rule.

**Recommendation**

- Update the handover only when current state or the next action changed.
- Add a progress entry only for material work or decisions.
- Update the queue only when an item changes state.
- Describe progress as an immutable, newest-first log rather than append-only.
- Avoid repeating verification evidence in all three session files.

## Recommended Claude-first target design

```text
CLAUDE.md
    Stable mission, authority order, invariants, safety rules, commands

_session/state.yaml
    Small machine-readable current state and verification timestamps

_session/handover.md
    Human-readable status, one active task, blockers, recent decision

_session/todo.md
    Unfinished queue only

_session/progress.md
    Cold immutable history; read only on demand

.claude/skills/
    resume
    end-session
    bid-workflow-router

skills/b00...b07/
    Domain workflow specifications and references, loaded progressively

src/
    Canonical schemas, enums, calculations, and blocking rules

check command / tests
    Deterministic evidence of repository health
```

### Suggested current-state schema

```yaml
schema_version: 1
updated: 2026-07-10
phase: feature_complete_local
active_workstream: code_review_remediation
next_action: fix_fts_deadline_parsing
external_blockers:
  graph_sharepoint: credentials_and_provisioning
  azure_openai: provisioning
verified:
  backend: 2026-07-10
  frontend_build: 2026-07-10
  live_browser: partial
```

This is not intended to replace narrative documentation. It provides a cheap,
unambiguous answer to the small set of state questions every new session asks.

## Prioritised implementation plan

### Priority 0 — restore truthfulness

1. Reconcile `CLAUDE.md`, `README.md`, handover, and todo with the current code.
2. Remove obsolete preview and uncommitted claims.
3. State the source-of-truth hierarchy in `CLAUDE.md`.

### Priority 1 — reduce context cost

1. Rewrite the handover as genuine hot state.
2. Move completed work out of the active queue.
3. Keep progress cold and task-addressable.
4. Add a concise structured state file.

### Priority 2 — harden verification

1. Add the canonical check command.
2. Commit tests around the highest-consequence rules first.
3. Record verification output once, then link to it rather than duplicating it.

### Priority 3 — unify skills and application

1. Declare `src/` domain vocabulary canonical.
2. Align skill enums and handoff schemas with it.
3. Route skill calculations through shared code where practical.
4. Resolve the tender-sweep name collision.

### Priority 4 — optimise Claude routing

1. Add a small project-level bid-workflow router.
2. Load one selected B-series skill at a time.
3. Keep large references and historical context demand-driven.

## Measures of success

The redesign should be considered successful when:

- A new Claude session can identify current state and the next action from
  fewer than 150 lines of mandatory context.
- No current-state claim is contradicted by another canonical document.
- Completed work does not remain in the active queue.
- One command provides a repeatable baseline verification result.
- Skills and application use the same enums and blocking rules.
- Only the relevant bid skill and references are loaded for a task.
- A human can distinguish verified fact, current plan, historical record, and
  external blocker without interpreting several narrative files.

## Conclusion

The harness is already unusually mature in its treatment of evidence, human
intervention, confidentiality, and honest verification. Those foundations
should be preserved.

Its next improvement is not a larger instruction set. It is a smaller and more
executable one: one authority hierarchy, one compact current state, one active
queue, one canonical domain vocabulary, and one deterministic verification
command. That design will give Claude 4.8 more stable outcomes while reducing
both input-token cost and the cognitive cost of resolving stale context.
