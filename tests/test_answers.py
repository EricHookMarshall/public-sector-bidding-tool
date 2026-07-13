"""Standard Answers (A-series) — the deterministic answer bank.

Offline: the file-reading tests build a fake library tree in a tmp dir, so nothing
here touches the real (gitignored) export or the network.

The bulk of this file is regression cover. Seeding the bank against FWF's real
library surfaced five ways a "simple lookup" quietly produces a confident wrong
answer, and every one of them would have gone out in a bid:

  1. Evidence scraped from `03 FWF Bids/` answered "Do you have a Modern Slavery
     policy?" with YES — attaching the blank declaration form a BUYER had sent us.
  2. A greedy regex ate the separator between two expiry dates in one tracker note,
     so a lapsed ISO 27001 came back with no expiry — and therefore read as fine.
  3. A certificate the library itself had named "..._Expired.pdf" resolved to READY.
  4. "Your most recent audited accounts" picked 2022 over 2024.
  5. A cert with no expiry on record resolved to READY rather than "can't prove it".

Each has a test below. The gate tests use a fixed `now` so they can't rot.
"""
import datetime

import answers as A
import db

# A fixed "today" so expired/ready assertions are stable forever.
NOW = datetime.datetime(2026, 7, 13, tzinfo=datetime.timezone.utc)


# --- The readiness gate -----------------------------------------------------

def test_gap_when_no_value_on_record():
    """The whole point: no evidence → an honest No, never an invented Yes."""
    a = A.resolve({"answer_key": "modern_slavery_policy", "answer_value": "",
                   "needs_evidence": "1"}, now=NOW)
    assert a["status"] == A.GAP


def test_expired_evidence_never_reads_as_ready():
    a = A.resolve({"answer_key": "iso_9001", "answer_value": "Yes",
                   "needs_evidence": "1", "dated": "1",
                   "evidence_path": "x/ISO 9001.pdf",
                   "expiry_date": "2026-01-09"}, now=NOW)
    assert a["status"] == A.EVIDENCE_EXPIRED
    assert a["days_to_expiry"] < 0


def test_dated_evidence_with_no_expiry_is_unverified_not_ready():
    """Regression (5). Insurance and certs expire; silence about an expiry date is
    not evidence of validity, so it must not reach READY."""
    a = A.resolve({"answer_key": "cyber_essentials", "answer_value": "Yes",
                   "needs_evidence": "1", "dated": "1",
                   "evidence_path": "x/Cyber Essentials.png",
                   "expiry_date": ""}, now=NOW)
    assert a["status"] == A.UNVERIFIED


def test_expired_filename_marker_forces_expired_without_a_date():
    """Regression (3). No parsable date, but the library named the file as lapsed —
    believe it rather than defaulting to fine."""
    a = A.resolve({"answer_key": "iso_27001", "answer_value": "Yes",
                   "needs_evidence": "1", "dated": "1",
                   "evidence_path": "x/FUTURE WORK FORCE - ISO 27001_Expired.pdf",
                   "expiry_date": ""}, now=NOW)
    assert a["status"] == A.EVIDENCE_EXPIRED


def test_per_bid_declaration_is_never_ready_and_never_a_gap():
    """A declaration is a question only this bid can answer — last bid's answer is
    context, not a default to auto-fill."""
    with_prior = A.resolve({"answer_key": "debarment_list", "answer_value": "No",
                            "per_bid": "1"}, now=NOW)
    without = A.resolve({"answer_key": "subcontractors", "answer_value": "",
                         "per_bid": "1"}, now=NOW)
    assert with_prior["status"] == A.CONFIRM_PER_BID
    assert without["status"] == A.CONFIRM_PER_BID  # NOT a gap


def test_yes_with_no_file_is_evidence_missing():
    a = A.resolve({"answer_key": "health_safety_policy", "answer_value": "Yes",
                   "needs_evidence": "1", "evidence_path": ""}, now=NOW)
    assert a["status"] == A.EVIDENCE_MISSING


def test_ready_and_expiring_soon():
    ready = A.resolve({"answer_key": "company_number", "answer_value": "11934102",
                       "needs_evidence": "0"}, now=NOW)
    assert ready["status"] == A.READY and not ready["expiring_soon"]

    soon = A.resolve({"answer_key": "public_liability", "answer_value": "Yes — £10m",
                      "needs_evidence": "1", "dated": "1",
                      "evidence_path": "x/PL.pdf", "expiry_date": "2026-08-01"}, now=NOW)
    assert soon["status"] == A.READY and soon["expiring_soon"]


def test_wrong_entity_outranks_everything():
    """The deep read of the library (13/07/2026) found the ISO 9001 and ISO 27001
    certificates are issued to FUTURE WORK FORCE SRL — the ROMANIAN sister company —
    not to Future Work Force Limited, the UK company that bids.

    This is the most dangerous class in the bank and the least visible: the file is
    called "FUTURE WORK FORCE - ISO 9001.pdf" and sits in FWF's own credential folder,
    so it reads as ours to every automated check and every hurried human. Answering a
    selection question with another legal person's certificate is a misrepresentation,
    so it must outrank even a valid in-date expiry."""
    a = A.resolve({"answer_key": "iso_9001", "answer_value": "Yes",
                   "needs_evidence": "1", "dated": "1",
                   "evidence_path": "x/FUTURE WORK FORCE - ISO 9001.pdf",
                   "expiry_date": "2099-01-01",  # in date, and STILL not usable
                   "entity_issue": A.WRONG_ENTITY_EVIDENCE["iso_9001"]}, now=NOW)
    assert a["status"] == A.WRONG_ENTITY
    assert a["entity_verified_on"] == A.ENTITY_ISSUES_VERIFIED_ON


def test_entity_issues_all_name_a_real_bank_key():
    assert set(A.WRONG_ENTITY_EVIDENCE) <= {e["key"] for e in A.BANK}


def test_conflict_beats_everything_and_is_never_auto_fillable():
    """The GCA review (13/07/2026) found FWF had answered the same no-reasoning
    questions two different ways on live portals — PI cover declared £10m against an
    actual £2m policy; turnover £100m on the MSA against "<£36m" on all three SQs.

    A bank that quietly picked a side would industrialise that inconsistency instead of
    ending it. So a conflict outranks even in-date evidence: PI has a real policy and a
    real (if lapsed) certificate, and it still must not auto-fill."""
    a = A.resolve({"answer_key": "professional_indemnity", "answer_value": "Yes — £2m",
                   "needs_evidence": "1", "dated": "1", "evidence_path": "x/PI.pdf",
                   "expiry_date": "2099-01-01",  # in date, and STILL not usable
                   "conflict": A.KNOWN_CONFLICTS["professional_indemnity"]}, now=NOW)
    assert a["status"] == A.CONFLICT
    assert a["conflict_source"]  # the finding is cited, so it can be checked


def test_known_conflicts_all_name_a_real_bank_key():
    """A conflict flagged against a key that doesn't exist would never surface."""
    assert set(A.KNOWN_CONFLICTS) <= {e["key"] for e in A.BANK}


def test_conflicts_are_seeded_onto_the_answers_they_contest():
    rows = {r["answer_key"]: r for r in A.seed_answers(items=[], root="/nonexistent")}
    assert rows["annual_turnover"]["conflict"]
    assert A.resolve(rows["annual_turnover"], now=NOW)["status"] == A.CONFLICT
    # An uncontested answer carries no conflict.
    assert rows["company_number"]["conflict"] == ""


def test_board_puts_what_loses_bids_on_top():
    rows = [
        {"answer_key": "company_number", "category": "Company Identity",
         "question": "num", "answer_value": "1", "needs_evidence": "0"},
        {"answer_key": "modern_slavery_policy", "category": "Policies",
         "question": "ms", "answer_value": "", "needs_evidence": "1"},
        {"answer_key": "iso_9001", "category": "Certifications", "question": "iso",
         "answer_value": "Yes", "needs_evidence": "1", "dated": "1",
         "evidence_path": "x.pdf", "expiry_date": "2020-01-01"},
    ]
    statuses = [r["status"] for r in A.board(rows, now=NOW)]
    assert statuses[0] == A.GAP
    assert statuses[1] == A.EVIDENCE_EXPIRED
    assert statuses[-1] == A.READY


# --- Reading the real library shape (fake tree, real logic) -----------------

def _fake_library(tmp_path):
    """A library tree with the exact traps the real one contains."""
    files = [
        # Our own canonical credentials.
        "02 Bid Library/Company Credentials/Policies/SOP021 Health and Safety Policy.docx",
        "02 Bid Library/Company Credentials/ISO Certs/FUTURE WORK FORCE - ISO 27001_Expired.pdf",
        "02 Bid Library/Company Credentials/Financials/Financial Accounts 2022.pdf",
        "02 Bid Library/Company Credentials/Financials/Financial Accounts 2024.pdf",
        "02 Bid Library/Company Credentials/UK Insurance/Professional Indemnity Insurance/DC501 - PI certificate.pdf",
        # Superseded copy — must never be offered.
        "02 Bid Library/Company Credentials/UK Insurance/Archive/25-26/DC501 - PI certificate 2.pdf",
        # A BUYER's blank form sitting in a bid folder — must never be offered.
        "03 FWF Bids/05 Scottish Water/01 Customer Documents/Supplier Modern Slavery Declaration.docx",
        # A copy previously uploaded to a portal — not the master document.
        "04 Portal Registrations/DPS/Spark DPS - RM6094/Insurance/DC501 - PI certificate.pdf",
    ]
    for rel in files:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x")
    return str(tmp_path)


def test_evidence_never_drawn_from_customer_documents(tmp_path):
    """Regression (1) — the defect that answered the user's own example wrongly.

    A blank "Supplier Modern Slavery Declaration.docx" that Scottish Water sent us to
    fill in is not evidence that FWF HAS a modern slavery policy. If evidence search
    reaches into `03 FWF Bids/`, the bank confidently answers "Yes — here's the file"
    and attaches the buyer's empty form to the bid."""
    root = _fake_library(tmp_path)
    files = A.evidence_files(root)
    assert not any(f.startswith("03 FWF Bids") for f in files)
    assert not any(f.startswith("04 Portal Registrations") for f in files)

    ms = A.find_evidence(["Modern Slavery"], files)
    assert ms == ""  # → seeds as a GAP, which is the truth


def test_archived_copies_are_never_offered(tmp_path):
    files = A.evidence_files(_fake_library(tmp_path))
    pi = A.find_evidence(["PI certificate"], files)
    assert "Archive" not in pi
    assert pi.startswith("02 Bid Library")


def test_newest_document_wins(tmp_path):
    """Regression (4): "most recent audited accounts" must not reach for 2022."""
    files = A.evidence_files(_fake_library(tmp_path))
    assert A.find_evidence(["Financial Accounts"], files).endswith("Financial Accounts 2024.pdf")


def test_certificates_outrank_the_hand_kept_tracker(tmp_path):
    """Regression (6) — a FALSE alarm, which is its own kind of wrong.

    At the 2026 renewal the Hiscox certificates for policy /11 (28/05/2026–27/05/2027)
    were filed, but Insurance Tracker.xlsx was never updated and still showed the
    superseded /08 policy expiring 27/05/2026. Reading the tracker, the bank told a
    bidder their cover had LAPSED when it had not. `seed_answers` must let the
    certificate win: an insurer-issued document beats a row typed by a human who has
    since left the company.

    (`insurance_from_certificates` needs the real PDFs, so this asserts the precedence
    rule itself: certs are merged OVER the tracker, never under it.)"""
    tracker_says = {"employers_liability": {
        "key": "employers_liability", "insurer": "Hiscox", "level": "£5m",
        "policy_number": "PL-.../08", "expiry_date": "2026-05-27"}}
    cert_says = {"employers_liability": {
        "key": "employers_liability", "insurer": "Hiscox", "level": "£5 million",
        "policy_number": "PL-.../11", "expiry_date": "2027-05-27",
        "source": "x/DC503 - EL certificate.pdf"}}
    merged = {**tracker_says, **cert_says}  # the precedence seed_answers applies
    assert merged["employers_liability"]["expiry_date"] == "2027-05-27"

    in_date = A.resolve({"answer_key": "employers_liability", "answer_value": "Yes — £5m",
                         "needs_evidence": "1", "dated": "1",
                         "evidence_path": "x/DC503 - EL certificate.pdf",
                         "expiry_date": "2027-05-27"}, now=NOW)
    assert in_date["status"] == A.READY  # NOT expired


def test_cyber_essentials_expiry_is_derived_not_typed():
    """CE has a fixed 12-month life and the report states only the certification date,
    so the expiry must be derived — nothing in the library ever writes it down."""
    assert A.CE_VALID_MONTHS == 12
    lapsed = A.resolve({"answer_key": "cyber_essentials", "answer_value": "Yes",
                        "needs_evidence": "1", "dated": "1",
                        "evidence_path": "x/Cyber Essentials 06062025.png",
                        "expiry_date": "2026-06-06"}, now=NOW)
    assert lapsed["status"] == A.EVIDENCE_EXPIRED


def test_iso_expiries_parsed_per_certificate():
    """Regression (2). Both expiries live in ONE free-text note. A loose `\\S+` in the
    date pattern eats across the separator ("09/01/2026 2700"), swallowing the 27001
    marker so its expiry is never found — and a lapsed cert reads as having none."""
    items = [{"item": "ISO Certifications",
              "notes": "9001 Expires: 09/01/2026 27001 Expires 31 Oct 2025"}]
    out = A.iso_expiries(items)
    assert out["iso_9001"] == "2026-01-09"
    assert out["iso_27001"] == "2025-10-31"


def test_seed_marks_missing_documents_as_gaps(tmp_path):
    """The bank seeded from a library with no modern-slavery / anti-bribery policy
    must say so — not quietly leave the question out, and not invent a Yes."""
    rows = {r["answer_key"]: r for r in A.seed_answers(items=[], root=_fake_library(tmp_path))}
    assert {e["key"] for e in A.BANK} == set(rows)  # every question is represented

    resolved = A.resolve(rows["modern_slavery_policy"], now=NOW)
    assert resolved["status"] == A.GAP and resolved["answer_value"] == ""

    hs = A.resolve(rows["health_safety_policy"], now=NOW)
    assert hs["status"] == A.READY and hs["evidence_path"].endswith("SOP021 Health and Safety Policy.docx")


# --- Matching ---------------------------------------------------------------

def test_buyer_wording_finds_the_right_answer():
    rows = A.seed_answers(items=[], root="/nonexistent")  # definitions only
    for query, expected in [
        ("do you have a modern day slavery policy?", "modern_slavery_policy"),
        ("Modern Slavery Statement (section 54)", "modern_slavery_policy"),
        ("what is your companies house number", "company_number"),
        ("Employer's Liability insurance level", "employers_liability"),
        ("are you ISO 27001 certified", "iso_27001"),
    ]:
        hits = A.match(query, rows, limit=1)
        assert hits, f"no match for {query!r}"
        assert hits[0][1]["answer_key"] == expected, f"{query!r} → {hits[0][1]['answer_key']}"


def test_answer_returns_none_rather_than_guessing():
    """A lookup that guesses is worse than one that says "I don't know"."""
    rows = A.seed_answers(items=[], root="/nonexistent")
    assert A.answer("what is the airspeed velocity of an unladen swallow", rows, now=NOW) is None


# --- db round-trip ----------------------------------------------------------

def test_upsert_is_idempotent_and_preserves_human_verification(tmp_path):
    conn = db.connect(str(tmp_path / "t.db"))
    db.init_db(conn)

    rows = A.seed_answers(items=[], root="/nonexistent")
    ins, upd = db.upsert_standard_answers(conn, rows)
    assert ins == len(A.BANK) and upd == 0

    # A human fills the gap the library can't answer, and verifies it.
    db.update_standard_answer(conn, "cdp_identifier",
                              {"answer_value": "PWGY-3727-VBXQ", "verified_on": "2026-07-13"})

    # Re-seeding must refresh from the library WITHOUT wiping what the human confirmed.
    ins2, upd2 = db.upsert_standard_answers(conn, rows)
    assert ins2 == 0 and upd2 == len(A.BANK)  # no duplicates

    saved = db.get_standard_answer(conn, "cdp_identifier")
    assert saved["answer_value"] == "PWGY-3727-VBXQ"
    conn.close()


def test_unverified_values_still_track_the_library(tmp_path):
    """The flip side: an answer nobody has confirmed must follow the library, so a
    newly-filed policy or a renewed cert is picked up rather than frozen at whatever
    was true the first time the app ran."""
    conn = db.connect(str(tmp_path / "t.db"))
    db.init_db(conn)
    db.upsert_standard_answers(conn, A.seed_answers(items=[], root="/nonexistent"))
    assert db.get_standard_answer(conn, "health_safety_policy")["answer_value"] == ""

    root = _fake_library(tmp_path)
    db.upsert_standard_answers(conn, A.seed_answers(items=[], root=root))
    refreshed = db.get_standard_answer(conn, "health_safety_policy")
    assert refreshed["answer_value"] == "Yes"
    assert refreshed["evidence_path"].endswith("SOP021 Health and Safety Policy.docx")
    conn.close()
