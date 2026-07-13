#!/usr/bin/env python3
"""
Standard Answers (A-series) — the deterministic answer bank for the questions every
bid asks and that need no reasoning to answer: "What is your company registration
number?", "Do you hold Employers' Liability insurance?", "Do you have a Modern
Slavery policy? If yes, attach it."

Why this is a lookup and NOT AI pre-fill (complete_ai.py's job): each of these has
exactly one correct answer, it is a matter of record, and a model can only add the
chance of getting it wrong. So this store answers from record — with provenance —
or it refuses. It never drafts. Anything needing judgement (the H&S narrative, the
GDPR technical measures, technical-ability contract examples) is deliberately NOT
in the bank; those stay with Complete (Stage 4).

Four things live here:

  - **The bank (committed).** Question definitions only — canonical wording,
    aliases to match on, answer type, and which evidence document backs it. No
    values: those are company data, seeded into the gitignored `bids.db` from the
    gitignored library export (CLAUDE.md hard rule — no confidential content in git).

  - **Seeding from real data.** Company facts come from `Basic Company
    Information.docx`, insurance from `Insurance Tracker.xlsx`, and policy/cert
    existence from the files actually present on disk. If a document is not there,
    the answer seeds as a GAP — never invented. That is the whole point: the bank
    is only trustworthy because it says "no" when the answer is no.

  - **The readiness gate.** An answer is only safe to reuse *while its evidence is
    in date*. `resolve()` recomputes that live against today, so a "Yes" backed by
    an expired certificate comes back as `evidence_expired` — not `ready`. This is
    the project's founding failure in miniature (knowledge/VERIFIED_FACTS.md: an
    expired cert at bid time is what loses the bid). Expiry is never stored as a
    status, only ever derived — same rule as compliance.py.

  - **Known conflicts.** Where FWF has already answered the same question two
    different ways in writing on live portals (the GCA review of 13/07/2026 found
    four such, incl. PI cover declared at £10m against an actual £2m policy). Those
    are not answers — they are decisions nobody has made — so they can never be
    auto-filled, and they outrank every other status.
"""
import datetime
import os
import re

import library as LIB

# --- Vocabulary -------------------------------------------------------------

# What kind of thing an answer is. Drives how the UI renders it, not the logic.
#   fact     — a value to copy in ("11934102")
#   yes_no   — a Yes/No declaration, usually with a document to attach
#   evidence — the answer IS a document (attach the accounts)
ANSWER_TYPES = ["fact", "yes_no", "evidence"]

CATEGORIES = [
    "Company Identity", "Insurance", "Policies",
    "Certifications", "Financial", "Technical", "Declarations",
]

# Readiness — the gate. Only `ready` may be auto-filled into a bid.
READY = "ready"                        # answer known, evidence (if any) in date
WRONG_ENTITY = "wrong_entity"          # the evidence belongs to a DIFFERENT legal person
CONFLICT = "conflict"                  # we have already answered this two different ways
EVIDENCE_EXPIRED = "evidence_expired"  # we hold it, but the document is out of date
EVIDENCE_MISSING = "evidence_missing"  # answer says yes, but no file to attach
UNVERIFIED = "unverified"              # document held, but nothing on record proves it's current
CONFIRM_PER_BID = "confirm_per_bid"    # true last time, but must be re-declared each bid
GAP = "gap"                            # we do not have this — say so, do not invent

# An answer whose evidence expires within this window is still `ready`, but flagged.
EXPIRING_SOON_DAYS = LIB.EXPIRING_SOON_DAYS

# Board/list ordering: the things that will lose you a bid come first.
_RANK = {WRONG_ENTITY: 0, CONFLICT: 1, GAP: 2, EVIDENCE_EXPIRED: 3, UNVERIFIED: 4,
         EVIDENCE_MISSING: 5, CONFIRM_PER_BID: 6, READY: 7}


# --- The bank ---------------------------------------------------------------
# Question definitions ONLY (no company values — see the module docstring).
#   key        — stable handle, also the seed/update key
#   aliases    — extra wordings a buyer might use; matching is over question+aliases
#   evidence   — filename fragments that identify the backing document on disk;
#                [] means the answer needs no attachment
#   per_bid    — the answer is a declaration that must be re-confirmed every bid
#                (it can change between bids, so it is never auto-filled blind)
#   dated      — this thing EXPIRES (insurance, certifications). Without an expiry
#                on record we cannot show it is current, so it resolves to
#                `unverified` rather than `ready`. A policy has no expiry (it has a
#                review date) — a certificate always does, and a lapsed one is what
#                loses the bid. Silence about an expiry is not evidence of validity.
BANK = [
    # -- Company Identity: matters of public record, no expiry ----------------
    dict(key="legal_name", category="Company Identity", answer_type="fact",
         question="What is your full legal company name?",
         aliases=["supplier name", "registered company name", "name of organisation",
                  "organisation name", "company name", "what is your name"]),
    dict(key="company_number", category="Company Identity", answer_type="fact",
         question="What is your company registration number?",
         aliases=["companies house number", "registered company number",
                  "company reg no", "registration number"]),
    dict(key="vat_number", category="Company Identity", answer_type="fact",
         question="What is your VAT registration number?",
         aliases=["vat number", "vat reg"]),
    dict(key="duns_number", category="Company Identity", answer_type="fact",
         question="What is your D-U-N-S number?",
         aliases=["duns", "dun and bradstreet number"]),
    dict(key="registered_address", category="Company Identity", answer_type="fact",
         question="What is your registered company address?",
         aliases=["registered office", "company address", "head office address"]),
    dict(key="incorporation_date", category="Company Identity", answer_type="fact",
         question="When was your company incorporated?",
         aliases=["date of incorporation", "trading since", "company established"]),
    dict(key="company_type", category="Company Identity", answer_type="fact",
         question="What is your company type / legal status?",
         aliases=["legal status", "type of organisation", "private limited"]),
    dict(key="cdp_identifier", category="Company Identity", answer_type="fact",
         question="What is your Central Digital Platform (CDP) unique identifier?",
         aliases=["central digital platform identifier", "cdp unique identifier",
                  "supplier unique identifier", "cdp id"]),

    # -- Insurance: yes + level + policy, all gated on the policy being in date --
    dict(key="employers_liability", category="Insurance", answer_type="yes_no",
         question="Do you hold Employers' Liability insurance, and at what level?",
         aliases=["employers liability", "el insurance", "employer's compulsory liability"],
         evidence=["EL certificate", "Employers"], dated=True),
    dict(key="public_liability", category="Insurance", answer_type="yes_no",
         question="Do you hold Public Liability insurance, and at what level?",
         aliases=["public liability", "pl insurance"],
         evidence=["PL certificate", "Public Liability"], dated=True),
    dict(key="professional_indemnity", category="Insurance", answer_type="yes_no",
         question="Do you hold Professional Indemnity insurance, and at what level?",
         aliases=["professional indemnity", "pi insurance", "indemnity cover"],
         evidence=["PI certificate", "Professional Indemnity"], dated=True),
    dict(key="cyber_insurance", category="Insurance", answer_type="yes_no",
         question="Do you hold Cyber / Data insurance, and at what level?",
         aliases=["cyber insurance", "cyber and data insurance", "data insurance"],
         evidence=["Cyber Certificate"], dated=True),
    dict(key="product_liability", category="Insurance", answer_type="yes_no",
         question="Do you hold Product Liability insurance, and at what level?",
         aliases=["product liability"],
         evidence=["Product Liability"], dated=True),

    # -- Policies: the classic "do you have X policy, attach it" block ---------
    dict(key="health_safety_policy", category="Policies", answer_type="yes_no",
         question="Do you have a Health & Safety policy?",
         aliases=["health and safety policy", "h&s policy", "hse policy"],
         evidence=["Health and Safety Policy"]),
    dict(key="data_protection_policy", category="Policies", answer_type="yes_no",
         question="Do you have a Data Protection / GDPR policy?",
         aliases=["data protection policy", "gdpr policy", "privacy policy",
                  "information governance policy"],
         evidence=["Data Protection Policy"]),
    dict(key="equality_diversity_policy", category="Policies", answer_type="yes_no",
         question="Do you have an Equality, Diversity & Inclusion policy?",
         aliases=["equality and diversity policy", "edi policy", "equal opportunities policy",
                  "diversity and inclusion policy"],
         evidence=["Equality and Diversity Policy"]),
    dict(key="social_value_policy", category="Policies", answer_type="yes_no",
         question="Do you have a Social Value policy?",
         aliases=["social value policy", "ppn 06/20", "social value commitment"],
         evidence=["Social Value Policy"]),
    dict(key="modern_slavery_policy", category="Policies", answer_type="yes_no",
         question="Do you have a Modern Slavery policy / statement?",
         aliases=["modern slavery policy", "modern slavery statement",
                  "modern slavery act 2015", "section 54", "ppn 009",
                  "slavery and human trafficking"],
         evidence=["Modern Slavery"]),
    dict(key="anti_bribery_policy", category="Policies", answer_type="yes_no",
         question="Do you have an Anti-Bribery & Corruption policy?",
         aliases=["anti bribery policy", "bribery act", "anti-corruption policy"],
         evidence=["Anti-Bribery", "Bribery"]),
    dict(key="environmental_policy", category="Policies", answer_type="yes_no",
         question="Do you have an Environmental & Sustainability policy?",
         aliases=["environmental policy", "sustainability policy", "environment management"],
         evidence=["Environmental Policy", "Sustainability Policy"]),
    dict(key="carbon_reduction_plan", category="Policies", answer_type="yes_no",
         question="Do you have a Carbon Reduction Plan (PPN 06/21)?",
         aliases=["carbon reduction plan", "net zero", "ppn 06/21", "scope 3 emissions"],
         evidence=["Carbon Reduction"]),

    # -- Certifications: the highest-decay class ------------------------------
    dict(key="iso_9001", category="Certifications", answer_type="yes_no",
         question="Are you certified to ISO 9001 (Quality Management)?",
         aliases=["iso 9001", "iso9001", "quality management certification"],
         evidence=["ISO 9001"], dated=True),
    dict(key="iso_27001", category="Certifications", answer_type="yes_no",
         question="Are you certified to ISO 27001 (Information Security)?",
         aliases=["iso 27001", "iso27001", "information security certification"],
         evidence=["ISO 27001"], dated=True),
    dict(key="cyber_essentials", category="Certifications", answer_type="yes_no",
         question="Do you hold Cyber Essentials (or Cyber Essentials Plus)?",
         aliases=["cyber essentials", "cyber essentials plus", "ce plus"],
         evidence=["Cyber Essentials"], dated=True),

    # -- Financial ------------------------------------------------------------
    dict(key="annual_accounts", category="Financial", answer_type="evidence",
         question="Please provide your most recent audited accounts.",
         aliases=["annual accounts", "audited accounts", "financial accounts",
                  "statement of accounts", "financial standing"],
         evidence=["Financial Accounts"]),
    dict(key="annual_turnover", category="Financial", answer_type="fact",
         question="What is your annual turnover?",
         aliases=["annual turnover", "yearly revenue", "turnover figure"]),
    dict(key="sme_status", category="Financial", answer_type="yes_no",
         question="Are you a Small or Medium Enterprise (SME)?",
         aliases=["sme", "small or medium enterprise", "small business"]),
    dict(key="parent_company_guarantee", category="Financial", answer_type="yes_no",
         question="Would your parent company be willing to provide a guarantee if necessary?",
         aliases=["parent company guarantee", "pcg", "guarantor",
                  "parent company accounts"]),

    # -- Technical: the reference contracts every SQ asks for -----------------
    dict(key="reference_contracts", category="Technical", answer_type="evidence",
         question="Please provide up to three relevant contract examples.",
         aliases=["contract examples", "reference contracts", "relevant experience",
                  "three contracts", "previous contracts", "case studies"],
         evidence=["Contract Examples"]),

    # -- Declarations: true last time, but MUST be re-confirmed each bid ------
    dict(key="debarment_list", category="Declarations", answer_type="yes_no",
         question="Are you on the debarment list?",
         aliases=["debarment list", "debarred", "excluded supplier"],
         per_bid=True),
    dict(key="bidding_as", category="Declarations", answer_type="fact",
         question="Are you bidding as a single supplier, or as part of a group/consortium?",
         aliases=["single supplier", "consortium", "group bid", "bidding as"],
         per_bid=True),
    dict(key="associated_persons", category="Declarations", answer_type="yes_no",
         question="Are you relying on any associated persons to satisfy the conditions of participation?",
         aliases=["associated persons", "relying on another supplier", "subcontractor reliance"],
         per_bid=True),
    dict(key="subcontractors", category="Declarations", answer_type="yes_no",
         question="Do you intend to sub-contract any part of the contract?",
         aliases=["sub-contractors", "subcontracting", "intended sub-contractors",
                  "supply chain"],
         per_bid=True),
]

BANK_BY_KEY = {e["key"]: e for e in BANK}


def bank_entry(key):
    return BANK_BY_KEY.get(key)


# --- Known conflicts --------------------------------------------------------
# Where FWF has ALREADY answered the same question two different ways, in writing,
# on live portals. Found by the GCA Supplier Registration review of 13/07/2026 —
# see docs/gca_findings/FINDINGS.md, which is the provenance for every entry here.
#
# This is the disease the bank exists to cure. These questions need no reasoning and
# have one true answer, yet FWF has three portal records giving three answers. A bank
# that quietly picked one would industrialise the inconsistency instead of ending it —
# so a conflicted answer is NEVER auto-fillable. It is the loudest status there is,
# and it stays until a human reconciles it and records the decision.
#
# A snapshot with a date, in the manner of knowledge/VERIFIED_FACTS.md: re-verify
# against the portal before relying on it, and DELETE the entry once reconciled —
# leaving a stale conflict flag up is its own kind of lie.
CONFLICTS_VERIFIED_ON = "2026-07-13"
CONFLICTS_SOURCE = "docs/gca_findings/FINDINGS.md (GCA portal review, 13/07/2026)"

KNOWN_CONFLICTS = {
    "annual_turnover":
        "Contradiction. The Modern Slavery Assessment records turnover of £100,000,000, "
        "while all three DPS Selection Questionnaires state “we do not turnover more than "
        "£36 million annually” (and answer No to Modern Slavery Act s.54 on that basis). "
        "One is wrong — most likely £100m is the Arobs group figure and <£36m is FWF "
        "standalone. This is the exact EFS/turnover question the engagement turns on: "
        "reconcile it, then answer it the same way everywhere.",
    "professional_indemnity":
        "Contradiction. The portal Selection Questionnaires declare Professional Indemnity "
        "cover of £10m, but the current Hiscox policy is £2m (the £10m was the 2024–25 "
        "policy). The declared figure overstates actual cover.",
    "cyber_essentials":
        "Contradiction. RM6173 declares Cyber Essentials YES (certified 06/06/2025), while "
        "the AI DPS and Spark records both still answer NO to the same question (Q155). "
        "Separately, the certificate is annual and so lapsed around 06/06/2026 — confirm "
        "renewal, then make all three records say the same thing.",
    "legal_name":
        "Inconsistent naming. Three variants are in live use: the legal “Future Work Force "
        "Limited”, the trading “Future Work Force Company Limited”, and “FWF Solutions” in "
        "the supply-chain narrative. Pick one convention — the legal name is what a "
        "contract is awarded to.",
}


def conflict_for(key):
    """The recorded contradiction for a bank key, or "" if the answer is uncontested."""
    return KNOWN_CONFLICTS.get(key, "")


# --- Wrong-entity evidence --------------------------------------------------
# The bidder is Future Work Force LIMITED (UK, company 11934102). Some documents in
# the library belong to Future Work Force S.R.L. — the ROMANIAN sister company in the
# Arobs group, a different legal person. Established by reading the certificates
# themselves (they are image scans, so no parser can see this — hence a declared list
# with a verified date, in the manner of knowledge/VERIFIED_FACTS.md).
#
# This is the most dangerous class in the whole bank, and the least visible. The file
# is called "FUTURE WORK FORCE - ISO 9001.pdf" and sits in FWF's own credential folder,
# so every automated check — and every hurried human — reads it as ours. Attaching it
# to a UK bid answers "are you ISO 9001 certified?" with a certificate issued to a
# different company, in a different country, that has also expired. Answering a
# selection question with another entity's certificate is a misrepresentation, and it
# is the kind that gets a bid disregarded rather than merely marked down.
ENTITY_ISSUES_VERIFIED_ON = "2026-07-13"

WRONG_ENTITY_EVIDENCE = {
    "iso_9001":
        "The certificate in the library is issued to FUTURE WORK FORCE SRL (Cluj-Napoca, "
        "Romania — the address is even annotated “no activity”), NOT to Future Work Force "
        "Limited, the UK company that bids. It ALSO expired on 08/01/2026. Bureau Veritas "
        "cert RO23.4749175Q. FWF Ltd (UK) therefore holds no ISO 9001 certification of its "
        "own: answer No, or answer via the group and say so explicitly.",
    "iso_27001":
        "The certificate in the library is issued to FUTURE WORK FORCE S.R.L. (Romania), not "
        "to Future Work Force Limited; it expired 31/10/2025 and is against the superseded "
        "ISO/IEC 27001:2013. The mitigation is real but must be stated accurately: Bureau "
        "Veritas letter L/BUH/06.11.2025/423/BCT confirms AROBS GROUP — naming Future Work "
        "Force — passed the ISO 27001:2022 transition audit (Oct 2025). That is GROUP "
        "certification evidenced by a letter, not an FWF Ltd certificate. Say exactly that; "
        "do not attach the lapsed SRL certificate.",
}


def entity_issue_for(key):
    """The recorded wrong-entity problem for a bank key, or ""."""
    return WRONG_ENTITY_EVIDENCE.get(key, "")


# --- Reading the real data --------------------------------------------------
# Everything below reads the gitignored library export through library.py's root.
# Nothing here invents a value: a missing document yields a missing answer.

# "Label: Value" lines in Basic Company Information.docx → the fact keys they feed.
_COMPANY_FACT_LABELS = {
    "full legal company name": "legal_name",
    "registered company number": "company_number",
    "vat number": "vat_number",
    "d-u-n-s number": "duns_number",
    "company address": "registered_address",
    "incorporated": "incorporation_date",
    "company type": "company_type",
}

_COMPANY_INFO_REL = os.path.join(
    "02 Bid Library", "Company Credentials", "Basic Company Information.docx")
_INSURANCE_TRACKER_REL = os.path.join(
    "02 Bid Library", "Company Credentials", "UK Insurance", "Insurance Tracker.xlsx")

# Evidence may ONLY be drawn from our own credential library. This is a correctness
# boundary, not a tidiness one: `03 FWF Bids/` holds each buyer's OWN documents, and
# a blank "Supplier Modern Slavery Declaration.docx" that Scottish Water sent us to
# fill in is not evidence that FWF has a modern slavery policy. Search there and the
# bank answers "Yes — here's the file" by attaching the buyer's empty form. Likewise
# `04 Portal Registrations/` holds copies uploaded to portals, whose provenance is a
# past upload rather than the master document. One canonical home per credential.
_CANONICAL_ROOTS = ["02 Bid Library"]

# Folders whose files are superseded — never offer an archived cert as the one to
# attach. (The library keeps prior years under .../UK Insurance/Archive/25-26/.)
_STALE_DIRS = {"archive", "cc archive", "el archive", "pi archive", "pl archive"}

# A cert the library itself has flagged as lapsed ("... - ISO 27001_Expired.pdf").
# Trust that marker: it beats having no expiry date and defaulting to "fine".
_EXPIRED_MARKERS = ("_expired", "-expired", " expired")


# The insurance CERTIFICATES — the authoritative source for cover and dates.
# The hand-kept Insurance Tracker.xlsx is a secondary index and it goes stale: at the
# 2026 renewal the certificates for policy /11 (28/05/2026–27/05/2027) were filed here
# while the tracker still showed the superseded /08 policy expiring 27/05/2026. Read
# the tracker and the bank tells a bidder their cover has LAPSED when it has not — a
# false alarm that is every bit as damaging as a missed expiry. Documents beat
# spreadsheets: a certificate is issued by the insurer, a tracker row is typed by a
# human who may have left.
_INSURANCE_CERTS = {
    "professional_indemnity": os.path.join(
        "UK Insurance", "Professional Indemnity Insurance", "DC501 - PI certificate.pdf"),
    "public_liability": os.path.join(
        "UK Insurance", "Public Liability Insurance", "DC502 - PL certificate.pdf"),
    "employers_liability": os.path.join(
        "UK Insurance", "Employers Liability Insurance", "DC503 - EL certificate.pdf"),
    "cyber_insurance": os.path.join(
        "UK Insurance", "Cyber Certficate Insurance", "DC506 Cyber Certificate.pdf"),
}
_CREDENTIALS_REL = os.path.join("02 Bid Library", "Company Credentials")

# The Cyber Essentials assessment report — carries the certification date. CE runs for
# 12 months exactly, so expiry is derived rather than typed anywhere.
_CE_REPORT_REL = os.path.join(
    "02 Bid Library", "Company Credentials",
    "futureworkforcelimited-2025-06-11-12-04-39.pdf")
CE_VALID_MONTHS = 12

# "Period of insurance: From 28/05/2026 to 27/05/2027", and the cover line, which the
# four Hiscox certificates each word differently.
_RE_CERT_PERIOD = re.compile(
    r"[Ff]rom\s*(\d{2}/\d{2}/\d{4})\s*to\s*(\d{2}/\d{2}/\d{4})")
_RE_CERT_POLICY = re.compile(r"[Pp]olicy\s*number:?\s*([A-Z0-9\-/]+)")
_RE_CERT_LEVEL = re.compile(
    r"(?:Level of cover|Limit of indemnity|minimum amount of cover provided by the "
    r"policy is no less than)\s*:?\s*£\s?([\d,]+(?:\s*million)?)", re.IGNORECASE)
# The EL certificate states its period as two numbered lines rather than "From..to".
_RE_EL_DATES = re.compile(
    r"commencement of insurance policy\s*(\d{2}/\d{2}/\d{4}).*?"
    r"expiry of insurance policy\s*(\d{2}/\d{2}/\d{4})", re.IGNORECASE | re.DOTALL)


def _docx():
    """python-docx if installed, else None — a soft dependency, exactly like
    openpyxl in library.py. Without it the company facts seed as gaps rather than
    the app failing to start."""
    try:
        import docx
        return docx
    except ImportError:
        return None


def _pypdf():
    """pypdf if installed, else None — soft, like _docx/_openpyxl. Without it the
    insurance answers fall back to the tracker (and say so in their provenance)."""
    try:
        from pypdf import PdfReader
        return PdfReader
    except ImportError:
        return None


def _pdf_text(path, pages=2):
    reader = _pypdf()
    if reader is None or not os.path.exists(path):
        return ""
    try:
        doc = reader(path)
        return "\n".join((p.extract_text() or "") for p in doc.pages[:pages])
    except Exception:
        return ""  # a scanned/corrupt PDF is a no-read, not a crash


def company_facts(root=None):
    """{fact_key: value} read out of Basic Company Information.docx. Empty dict if
    the document (or python-docx) is absent — the caller then seeds those as gaps."""
    docx = _docx()
    path = os.path.join(root or LIB.root(), _COMPANY_INFO_REL)
    if docx is None or not os.path.exists(path):
        return {}
    facts = {}
    for para in docx.Document(path).paragraphs:
        text = para.text.strip()
        if ":" not in text:
            continue
        label, _, value = text.partition(":")
        key = _COMPANY_FACT_LABELS.get(label.strip().lower())
        # First line only: the .docx runs "Company Address: ...\nWebsite: ..." into a
        # single paragraph, so an unsplit value hands the buyer an address with the
        # company's website glued onto the end of it.
        value = value.strip().splitlines()[0].strip() if value.strip() else ""
        if key and value:
            facts[key] = value
    return facts


# Insurance Tracker "Insurance Type" wording → bank key. The sheet is hand-typed,
# so match on a normalised prefix rather than exact strings.
_INSURANCE_TYPES = {
    "employers liability": "employers_liability",
    "public liability": "public_liability",
    "professional indemnity": "professional_indemnity",
    "cyber and data": "cyber_insurance",
    "product liability": "product_liability",
}


def _iso_date(val):
    """A cell that may be a datetime or a string → ISO date string, or ""."""
    if val is None:
        return ""
    if hasattr(val, "date"):
        return val.date().isoformat()
    found = LIB.extract_expiries(f"expires {val}")
    return found[0] if found else ""


def _dmy_to_iso(s):
    d, m, y = s.split("/")
    return f"{y}-{m}-{d}"


def insurance_from_certificates(root=None):
    """{bank_key: policy dict} read from the Hiscox CERTIFICATES themselves — the
    authoritative source. Returns {} if pypdf is absent or the certs aren't there, and
    the caller then falls back to the tracker.

    Note `public_liability` also settles `product_liability`: the single Hiscox
    certificate is one of "public AND products liability" at £10m, which is why the
    tracker (with no products row at all) made Product Liability look like a gap when
    it is in fact covered."""
    base = os.path.join(root or LIB.root(), _CREDENTIALS_REL)
    out = {}
    for key, rel in _INSURANCE_CERTS.items():
        text = _pdf_text(os.path.join(base, rel))
        if not text:
            continue
        period = _RE_CERT_PERIOD.search(text) or _RE_EL_DATES.search(text)
        if not period:
            continue
        level = _RE_CERT_LEVEL.search(text)
        policy = _RE_CERT_POLICY.search(text)
        out[key] = {
            "key": key,
            "insurer": "Hiscox",
            "level": ("£" + level.group(1).strip()) if level else "",
            "policy_number": policy.group(1).strip() if policy else "",
            "start_date": _dmy_to_iso(period.group(1)),
            "expiry_date": _dmy_to_iso(period.group(2)),
            "source": os.path.join(_CREDENTIALS_REL, rel),
        }
    if "public_liability" in out:
        products = dict(out["public_liability"])
        products["key"] = "product_liability"
        out["product_liability"] = products
    return out


def cyber_essentials_expiry(root=None):
    """The Cyber Essentials expiry, derived as certification date + 12 months (CE has
    a fixed 12-month life; the report states the date but never the expiry). "" if the
    report can't be read."""
    text = _pdf_text(os.path.join(root or LIB.root(), _CE_REPORT_REL))
    m = re.search(r"Report date:\s*(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if not m:
        return ""
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        return datetime.date(y + CE_VALID_MONTHS // 12, mo, d).isoformat()
    except ValueError:
        return ""


def insurance_policies(root=None):
    """{bank_key: policy dict} for the CURRENT policy of each insurance type, read
    from Insurance Tracker.xlsx — the FALLBACK when the certificates can't be read.
    The tracker keeps prior years as extra rows, so "current" = the row with the latest
    expiry date for that type — picking by row order would silently answer with last
    year's cover."""
    openpyxl = LIB._openpyxl()
    path = os.path.join(root or LIB.root(), _INSURANCE_TRACKER_REL)
    if openpyxl is None or not os.path.exists(path):
        return {}
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    best = {}
    for ws in wb.worksheets:
        rows = ws.iter_rows(values_only=True)
        try:
            header = [str(c).strip().lower() if c else "" for c in next(rows)]
        except StopIteration:
            continue
        col = {name: i for i, name in enumerate(header)}
        for raw in rows:
            def cell(name):
                i = col.get(name)
                return raw[i] if i is not None and i < len(raw) else None

            type_text = str(cell("insurance type") or "").strip().lower()
            key = next((k for pref, k in _INSURANCE_TYPES.items()
                        if type_text.startswith(pref)), None)
            if not key:
                continue
            expiry = _iso_date(cell("expiry date"))
            policy = {
                "key": key,
                "insurer": str(cell("with") or "").strip(),
                "level": str(cell("level") or "").strip(),
                "policy_number": str(cell("policy number") or "").strip(),
                "expiry_date": expiry,
            }
            if key not in best or expiry > best[key]["expiry_date"]:
                best[key] = policy
    wb.close()
    return best


def evidence_files(root=None):
    """Every candidate evidence document in OUR credential library, as
    {relative_path: filename}. Confined to `_CANONICAL_ROOTS` and skipping archive
    folders, so neither a buyer's blank form nor a superseded certificate can be
    offered as the file to attach. This answers the "…and where is the file?" half
    of the question — the path is the thing a novice actually needs."""
    base = root or LIB.root()
    out = {}
    for canonical in _CANONICAL_ROOTS:
        start = os.path.join(base, canonical)
        if not os.path.isdir(start):
            continue
        for dirpath, dirnames, filenames in os.walk(start):
            dirnames[:] = [d for d in dirnames if d.strip().lower() not in _STALE_DIRS]
            for fn in filenames:
                if fn.startswith("~$") or fn == ".DS_Store":
                    continue
                full = os.path.join(dirpath, fn)
                out[os.path.relpath(full, base)] = fn
    return out


# A year in a filename ("Financial Accounts 2024.pdf") — used to prefer the newest.
_RE_YEAR = re.compile(r"\b(20\d{2})\b")


def find_evidence(fragments, files):
    """The best matching evidence path for a bank entry's `evidence` fragments, or
    "".

    Two deliberate choices:
      - A filename flagged `_Expired` still MATCHES. We want to find it, so the
        answer resolves to `evidence_expired` ("your cert lapsed") rather than `gap`
        ("we never had one"). Different problems, different fixes, and conflating
        them is how a bid goes out with a lapsed certificate attached.
      - Where several documents match, the NEWEST wins (by year in the filename).
        "Please provide your most recent audited accounts" must not reach for
        Financial Accounts 2022 just because it sorts first.
    """
    if not fragments:
        return ""
    hits = []
    for rel, fn in files.items():
        low = fn.lower()
        if any(frag.lower() in low for frag in fragments):
            years = [int(y) for y in _RE_YEAR.findall(fn)]
            newest = max(years) if years else 0
            hits.append((-newest, rel.count(os.sep), len(rel), rel))
    return sorted(hits)[0][3] if hits else ""


def is_marked_expired(path):
    """True if the library itself named the file as lapsed."""
    return any(mark in (path or "").lower() for mark in _EXPIRED_MARKERS)


# ISO expiries are typed into ONE free-text tracker note covering both certs —
# "9001 Expires: 09/01/2026  27001 Expires 31 Oct 2025" — so pull the date that
# follows each standard's number rather than taking the first date in the string.
# Each date alternative is fully anchored: a loose `\S+` in the middle greedily eats
# across the separator ("09/01/2026 2700"), swallowing the next cert's marker so its
# expiry is never found — which is precisely how a lapsed cert reads as having none.
_RE_ISO_EXPIRY = re.compile(
    r"(9001|27001)\D{0,15}?"
    r"(\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}|\d{4}-\d{2}-\d{2})",
    re.IGNORECASE)


def iso_expiries(items):
    """{'iso_9001': iso_date, 'iso_27001': iso_date} mined from the Bid Library
    Tracker's ISO row notes. Missing → no date, which resolves to "we cannot prove
    it is current", not to "it is fine"."""
    out = {}
    for item in items or []:
        text = f"{item.get('item', '')} {item.get('notes', '')}"
        if "iso" not in text.lower():
            continue
        for m in _RE_ISO_EXPIRY.finditer(text):
            dates = LIB.extract_expiries(f"expires {m.group(2)}")
            if dates:
                out[f"iso_{m.group(1)}"] = dates[0]
    return out


# --- Seeding ----------------------------------------------------------------

def seed_answers(items=None, root=None):
    """Build the full answer set from the real library: one row per BANK entry, with
    its value, backing file, provenance and (where knowable) expiry filled in from
    documents that actually exist. An entry the library cannot evidence is seeded
    with an empty value — `resolve()` will call that a GAP. Nothing is invented."""
    facts = company_facts(root)
    # Certificates beat the tracker; the tracker only fills what they can't answer.
    certs = insurance_from_certificates(root)
    policies = {**insurance_policies(root), **certs}
    files = evidence_files(root)
    isos = iso_expiries(items)
    ce_expiry = cyber_essentials_expiry(root)

    rows = []
    for entry in BANK:
        key = entry["key"]
        row = {
            "answer_key": key,
            "category": entry["category"],
            "question": entry["question"],
            "answer_type": entry["answer_type"],
            "answer_value": "",
            "evidence_path": find_evidence(entry.get("evidence"), files),
            "expiry_date": "",
            "needs_evidence": "1" if entry.get("evidence") else "0",
            "per_bid": "1" if entry.get("per_bid") else "0",
            "dated": "1" if entry.get("dated") else "0",
            "conflict": conflict_for(key),
            "entity_issue": entity_issue_for(key),
            "source": "",
            "notes": "",
        }

        if key in facts:
            row["answer_value"] = facts[key]
            row["source"] = _COMPANY_INFO_REL

        elif key in policies:
            p = policies[key]
            row["answer_value"] = f"Yes — {p['level']} ({p['insurer']}, policy {p['policy_number']})"
            row["expiry_date"] = p["expiry_date"]
            row["source"] = p.get("source") or _INSURANCE_TRACKER_REL
            if key == "product_liability" and key in certs:
                row["notes"] = ("Covered by the same Hiscox certificate as Public Liability — "
                                "it is a 'public AND products liability' policy.")
            # The insurance answer needs the certificate as its attachment; for Product
            # Liability that is the PL certificate, which `find_evidence` won't match.
            if not row["evidence_path"] and p.get("source"):
                row["evidence_path"] = p["source"]

        elif row["evidence_path"]:
            # The document exists in our own credential library, so the answer is Yes.
            # Cyber Essentials' expiry is derived (cert date + 12 months); the ISO
            # expiries come from the tracker note; failing both, the library may have
            # named the file as lapsed.
            row["answer_value"] = "Yes"
            row["expiry_date"] = (ce_expiry if key == "cyber_essentials"
                                  else isos.get(key, ""))
            row["source"] = row["evidence_path"]
            if is_marked_expired(row["evidence_path"]):
                row["notes"] = "The library's own copy of this certificate is marked Expired."

        rows.append(row)
    return rows


# --- The readiness gate -----------------------------------------------------

def resolve(row, now=None):
    """Return a copy of `row` with live-derived readiness: `status`, `reason`,
    `days_to_expiry`. Never persisted — recomputed every read, because it decays.

    The gate is the reason this store is safe to auto-fill from:

      wrong_entity     — the evidence belongs to a DIFFERENT legal person (the Romanian
                         sister company). Attaching it is a misrepresentation. Loudest.
      conflict         — we have answered this two different ways on live portals.
                         Not an answer at all: a decision nobody has made.
      gap              — no answer on record. Say so. Do NOT fabricate a Yes.
      evidence_expired — we have it, the document has lapsed. Blocks auto-fill.
      unverified       — a document that EXPIRES, with no expiry on record. We cannot
                         show it is current, so we do not get to claim it is.
      evidence_missing — the answer is Yes but there is no file to attach.
      confirm_per_bid  — a declaration; the last answer is shown, never auto-filled.
      ready            — answer on record, evidence (if needed) present and in date.

    Order matters. Wrong-entity evidence wins over everything, then a known conflict;
    per-bid declarations settle next (never `ready`, never a `gap`); after that every
    expiry check sits ahead of `ready`, so no answer can route around another company's
    certificate, a contradiction, or a lapsed document to reach an auto-fillable state.
    """
    a = dict(row)
    value = (a.get("answer_value") or "").strip()
    needs_evidence = str(a.get("needs_evidence") or "") == "1"
    dated = str(a.get("dated") or "") == "1"
    path = (a.get("evidence_path") or "").strip()
    expiry = (a.get("expiry_date") or "").strip()

    days = LIB._days_until(expiry, now) if expiry else None
    a["days_to_expiry"] = days
    a["expiring_soon"] = days is not None and 0 <= days <= EXPIRING_SOON_DAYS

    conflict = (a.get("conflict") or "").strip()
    entity_issue = (a.get("entity_issue") or "").strip()

    if entity_issue:
        # Above even `conflict`. A contradiction means we do not know the answer; a
        # wrong-entity document means we would be answering with someone ELSE'S
        # credential. That is not a data-quality problem, it is a misrepresentation —
        # and it is invisible, because the file is named "FUTURE WORK FORCE ...".
        a["status"] = WRONG_ENTITY
        a["reason"] = entity_issue
        a["entity_verified_on"] = ENTITY_ISSUES_VERIFIED_ON
    elif conflict:
        # The loudest status, checked before anything else — including before we look
        # at whether the evidence is in date. If we have already put two different
        # answers to this question in writing on live portals, then we do not have an
        # answer: we have a decision nobody has made. Auto-filling either side would
        # just industrialise the inconsistency the bank was built to end.
        a["status"] = CONFLICT
        a["reason"] = conflict
        a["conflict_source"] = CONFLICTS_SOURCE
        a["conflict_verified_on"] = CONFLICTS_VERIFIED_ON
    elif str(a.get("per_bid") or "") == "1":
        # Checked next, and it can never be `ready` or `gap`. A declaration ("are you
        # on the debarment list?", "are you sub-contracting?") isn't a missing document
        # — it's a question only this bid can answer, and last bid's answer is context,
        # never a default to auto-fill.
        a["status"] = CONFIRM_PER_BID
        a["reason"] = (f"A per-bid declaration — last answered “{value}”. It can change "
                       "between bids, so confirm it every time."
                       if value else
                       "A per-bid declaration with no previous answer on record — it must be "
                       "answered for this bid.")
    elif not value:
        a["status"] = GAP
        a["reason"] = ("Nothing in the bid library evidences this — the honest answer is No. "
                       "It needs creating (or recording) before it can be claimed.")
    elif needs_evidence and not path:
        a["status"] = EVIDENCE_MISSING
        a["reason"] = "Answer is on record but there is no document in the library to attach."
    elif days is not None and days < 0:
        a["status"] = EVIDENCE_EXPIRED
        a["reason"] = f"Evidence expired {abs(days)} day(s) ago ({expiry}) — it cannot be submitted."
    elif is_marked_expired(path):
        # No parsable date, but the library named the file as lapsed. Believe it.
        a["status"] = EVIDENCE_EXPIRED
        a["reason"] = "The library's own copy of this document is marked Expired."
    elif dated and not expiry:
        a["status"] = UNVERIFIED
        a["reason"] = ("This expires, but no expiry date is on record — its validity can't be "
                       "shown. Confirm it is still current before submitting.")
    else:
        a["status"] = READY
        a["reason"] = (f"Evidence expires in {days} day(s) — usable now, renew soon."
                       if a["expiring_soon"] else "Answer on record and evidence is in date.")
    return a


def board(rows, now=None):
    """Every answer, resolved, worst-first — so what will lose you a bid is on top."""
    resolved = [resolve(r, now) for r in rows]
    resolved.sort(key=lambda a: (_RANK.get(a["status"], 9), a["category"], a["question"]))
    return resolved


def summary(resolved):
    """Counts per status, for the header strip."""
    out = {s: 0 for s in (READY, CONFIRM_PER_BID, EVIDENCE_MISSING, UNVERIFIED,
                          EVIDENCE_EXPIRED, GAP, CONFLICT, WRONG_ENTITY)}
    for a in resolved:
        out[a["status"]] = out.get(a["status"], 0) + 1
    out["total"] = len(resolved)
    return out


# --- Matching ---------------------------------------------------------------
# Deterministic: normalise, then score token overlap against the question + its
# aliases. No model — a lookup that sometimes hallucinates is worse than no lookup.

_STOPWORDS = {
    "the", "a", "an", "of", "and", "or", "to", "for", "in", "on", "with", "your",
    "you", "do", "does", "have", "has", "is", "are", "what", "please", "provide",
    "confirm", "any", "we", "our", "it", "at", "as", "if", "by", "be", "this",
}


def _tokens(text):
    return {t for t in re.findall(r"[a-z0-9]+", (text or "").lower())
            if t and t not in _STOPWORDS}


def match(query, rows, limit=5):
    """Rank `rows` against a free-text question. Returns [(score, row), ...] best
    first, score in 0..1. An alias hit scores as the alias's own overlap, so
    "modern slavery statement" finds the Modern Slavery entry even though the
    canonical question says "policy"."""
    q = _tokens(query)
    if not q:
        return []
    scored = []
    for row in rows:
        entry = bank_entry(row.get("answer_key", "")) or {}
        candidates = [row.get("question", "")] + list(entry.get("aliases", []))
        best = 0.0
        for cand in candidates:
            c = _tokens(cand)
            if not c:
                continue
            # Overlap against the shorter side: a 3-word alias fully contained in a
            # long buyer question should score 1.0, not 3/20.
            best = max(best, len(q & c) / min(len(q), len(c)))
        if best > 0:
            scored.append((round(best, 3), row))
    scored.sort(key=lambda s: (-s[0], s[1].get("question", "")))
    return scored[:limit]


def answer(query, rows, now=None, threshold=0.5):
    """The one-shot lookup behind "just tell me the answer": the best match above
    `threshold`, resolved. Returns None when nothing matches well — an honest
    no-answer beats a confident wrong one."""
    hits = match(query, rows, limit=1)
    if not hits or hits[0][0] < threshold:
        return None
    score, row = hits[0]
    out = resolve(row, now)
    out["match_score"] = score
    return out


def reference():
    """Vocabulary for the UI (mirrors compliance.reference / library.reference)."""
    return {
        "categories": CATEGORIES,
        "answer_types": ANSWER_TYPES,
        "statuses": [READY, CONFIRM_PER_BID, EVIDENCE_MISSING, UNVERIFIED,
                     EVIDENCE_EXPIRED, GAP, CONFLICT, WRONG_ENTITY],
        "entity_issues_verified_on": ENTITY_ISSUES_VERIFIED_ON,
        "conflicts_verified_on": CONFLICTS_VERIFIED_ON,
        "conflicts_source": CONFLICTS_SOURCE,
        "expiring_soon_days": EXPIRING_SOON_DAYS,
        "bank_size": len(BANK),
    }
