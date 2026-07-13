# Standard Answers (A-series) — the deterministic answer bank

The questions every bid asks and that need **no reasoning** to answer: *"What is your
company registration number?"*, *"Do you hold Employers' Liability insurance?"*,
*"Do you have a Modern Slavery policy? If yes, attach it."*

Each has exactly one correct answer, it is a matter of record, and a model can only
add the chance of getting it wrong. So the bank **answers from record — with
provenance — or it refuses.** It never drafts. Anything needing judgement (the H&S
narrative, the GDPR technical measures, technical-ability contract examples) stays
with Complete (Stage 4) and its AI pre-fill; those are deliberately *not* in the bank.

## Where it lives

| Piece | File |
|---|---|
| Domain: bank, seeding, matching, the readiness gate | [`src/answers.py`](../src/answers.py) |
| Storage: `standard_answers` table + CRUD | [`src/db.py`](../src/db.py) |
| API: `/api/answers/{reference,board,lookup}`, `PUT /api/answers/{key}`, `POST /api/answers/sync-from-library` | [`src/api.py`](../src/api.py) |
| Tests (incl. a regression per defect below) | [`tests/test_answers.py`](../tests/test_answers.py) |

**Question definitions are committed; values are not.** The bank ships as questions,
aliases, answer types and which document backs each one. The *values* are company data,
seeded into the gitignored `bids.db` from the gitignored library export at startup
(CLAUDE.md hard rule: no confidential content in git). This reuses the `LocalMirror`
provider seam, so live `GraphSharePoint` will drop in behind it unchanged.

## The readiness gate

The reason the bank is safe to auto-fill from. Status is **derived live against today**,
never stored — an answer backed by a certificate that lapses tomorrow is correct today
and bid-losing next week.

| Status | Meaning |
|---|---|
| `ready` | Answer on record, evidence present and in date. **The only auto-fillable state.** |
| `wrong_entity` | The evidence belongs to a **different legal person** (the Romanian sister company). Attaching it is a misrepresentation. |
| `conflict` | We have already answered this **two different ways** on live portals. Not an answer — a decision nobody has made. |
| `evidence_expired` | We hold it, but the document has lapsed. Blocks auto-fill. |
| `unverified` | A thing that *expires*, with no expiry on record. We can't show it's current, so we don't get to claim it is. |
| `evidence_missing` | Answer is "Yes" but there's no file to attach. |
| `confirm_per_bid` | A declaration (debarment, sub-contracting). Last answer is context, never a default. |
| `gap` | Nothing evidences this. The honest answer is **No**. |

Wrong-entity evidence outranks everything, then a known conflict. Per-bid declarations
settle next (never `ready`, never `gap`). Every expiry check then sits ahead of `ready`,
so no answer can route around another company's certificate, a contradiction, or a lapsed
document to reach an auto-fillable state.

---

## Why `conflict` exists: the GCA review

The [GCA portal review](gca_findings/FINDINGS.md) of 13/07/2026 found FWF answering the
*same no-reasoning questions differently across three live portals*:

| Question | RM6173 | AI DPS / Spark | The library (truth) |
|---|---|---|---|
| Cyber Essentials? | **Yes** (06/06/2025) | **No** (Q155) | certificate lapsed ~06/06/2026 |
| Professional Indemnity cover? | £10m declared | £10m declared | **£2m actual** (Hiscox) |
| Annual turnover? | "<£36m" on the SQs | "<£36m" on the SQs | **£100m** on the Modern Slavery Assessment |
| Legal name? | *Future Work Force Limited* | *Future Work Force Company Limited* | *FWF Solutions* in the supply-chain narrative |

**This is the disease the bank exists to cure**, and it is exactly why the store must be
a lookup rather than a generator. A bank that silently picked one side of these would
*industrialise* the inconsistency — answering fast and wrong, at scale, in FWF's name.
So a conflicted answer is never auto-fillable, cites the finding that raised it, and
stays flagged until a human reconciles it. `KNOWN_CONFLICTS` in `answers.py` is a dated
snapshot in the manner of `knowledge/VERIFIED_FACTS.md`: **delete the entry once
reconciled** — a stale conflict flag is its own kind of lie.

---

## What the real library actually says

Seeded from FWF's live bid-library export on **2026-07-13**: **33 questions — 16 ready,
7 gaps, 4 conflicts, 4 per-bid declarations, 2 wrong-entity.** Re-run
`POST /api/answers/sync-from-library` for the current picture; the numbers below decay.

> The full source review is [bid-library-deep-review.md](bid-library-deep-review.md). It
> **corrects** the insurance finding below and surfaces the wrong-entity problem.

### Gaps — documents that do not exist

The bank cannot answer these, and says so rather than inventing a Yes:

- **Modern Slavery policy / statement** — *no such document in the library.*
- **Anti-Bribery & Corruption policy** — no document.
- **Environmental & Sustainability policy** — no document.
- **Carbon Reduction Plan (PPN 06/21)** — no document. Commonly *mandatory* on central-government work.
- **CDP unique identifier** — not in any canonical library doc (it *is* in a past PSQ; confirm it once via `PUT /api/answers/cdp_identifier` and it sticks).
- **SME status** and **parent-company guarantee** — both answered on the portals (Yes / Yes) but nowhere in the library. Confirm once and they stick.

The Bid Library Tracker lists the first two as *"Aligned to Public Contracts
Regulations"* with no owner, no date and no file — a tracker row is an intention, not a
policy. That distinction is the whole reason the bank checks the filesystem rather than
trusting the tracker.

### Wrong entity — the most dangerous class

- **ISO 9001** and **ISO 27001** — both certificates are issued to **Future Work Force SRL
  (Romania)**, not to Future Work Force Limited (UK, company 11934102), and both have also
  expired. FWF Ltd holds no ISO certification of its own. For 27001 there is a real
  group-level mitigation (Bureau Veritas letter, Arobs Group, ISO 27001:2022, Oct 2025) —
  but that must be stated as *group* certification, not as FWF's own.

### Expired — held, but not submittable today

- **Cyber Essentials** — correct entity, but certified 06/06/2025 and CE runs 12 months, so
  **recertification was due 06/06/2026**. Lapsed ~5 weeks ago.

### Insurance — CURRENT (this corrects an earlier finding)

All cover is **in date to 27/05/2027** (Hiscox policy `.../11`): EL £5m, Public **and
Products** Liability £10m, PI £2m, Cyber £1m. `Insurance Tracker.xlsx` was never updated at
the 2026 renewal and still shows the superseded `/08` policy — so the bank now reads the
**certificates**, which are authoritative. Product Liability is therefore *not* a gap: it
is covered by the same "public and products liability" certificate.

### Conflicts — answered two ways already

Annual turnover, Professional Indemnity cover, Cyber Essentials, and the legal company
name. See the table above. None of these can be auto-filled until reconciled.

### Ready

Company identity (legal name, company number, VAT, D-U-N-S, registered address,
incorporation date, company type), the four filed policies (Health & Safety, Data
Protection, Equality & Diversity, Social Value) and the 2024 audited accounts.

---

## Five defects the real data exposed

Seeding against the real library — rather than a fixture — surfaced five ways a "simple
lookup" produces a confident wrong answer. Every one would have gone out in a bid.
Each now has a regression test.

1. **The buyer's own form answered as ours.** Evidence search reached into
   `03 FWF Bids/`, found `05 Scottish Water/01 Customer Documents/Supplier Modern
   Slavery Declaration.docx` — a blank form the *buyer* sent us to fill in — and
   answered *"Do you have a Modern Slavery policy?"* with **Yes, here's the file.**
   Evidence is now confined to `02 Bid Library/`. A buyer's document is not our
   credential; this is a correctness boundary, not tidiness.
2. **A greedy regex hid a lapsed certificate.** Both ISO expiries live in one free-text
   tracker note (`9001 Expires: 09/01/2026 27001 Expires 31 Oct 2025`). A loose `\S+`
   matched `09/01/2026 2700`, eating the `27001` marker — so ISO 27001 came back with
   *no expiry*, and therefore read as fine.
3. **`_Expired.pdf` resolved to `ready`.** No parsable date, so nothing blocked it. A
   filename the library itself marked as lapsed now forces `evidence_expired`.
4. **"Most recent audited accounts" picked 2022**, not 2024 — shortest-path tiebreak.
   Newest wins now.
5. **No expiry read as "no problem".** A cert with no date on record resolved to
   `ready`. Silence about an expiry is not evidence of validity — hence `unverified`.

The through-line: every defect failed *toward* a confident yes. A store that answers
"do you have X" must be built so its failure mode is **refusal**, not optimism.

## Re-seeding

`_bootstrap_standard_answers` runs on **every** startup, not just on an empty table —
the library is the moving part (a policy gets filed, a cert renewed) and the bank must
track it. `upsert_standard_answers` is keyed on `answer_key`, so re-running never
duplicates, and it **will not overwrite a human-verified value**: once someone sets
`verified_on`, the library stops being authoritative over that answer. Values nobody has
confirmed keep following the library.
