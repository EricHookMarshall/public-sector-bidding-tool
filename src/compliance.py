#!/usr/bin/env python3
"""
Compliance & Renewals (C-series) domain logic — the app-owned compliance-asset
register's vocabulary + derived views. Keeps api.py thin (mirrors qualification.py
/ clarification.py).

Two things live here:
  - **Expiry status is derived, not stored.** From an asset's `expiry_date` (or, if
    blank, any renewal date mined out of its name/notes) we compute expired /
    expiring_soon / ok / none *live against today* — never persisted, because it
    decays (knowledge/VERIFIED_FACTS.md, "an expired cert at bid time is the
    founding-class failure"). Reuses library.py's date maths so Complete's evidence
    ledger and this org-level view compute expiry identically.
  - **Seeding from the bid library.** Turns the LocalMirror Company-Credentials /
    Governance / Commercial items into seed asset dicts, so the register starts
    populated with the org's known credentials — including any already expired.
"""
import library as LIB

# Categories a compliance asset can sit in — the library's evidence categories
# plus Frameworks (C4: framework/contract membership periods) and a catch-all.
# Text-tolerant: the API accepts any non-empty category, this just drives the UI.
CATEGORIES = [
    "Company Credentials", "Governance", "Commercial",
    "Insurance", "Frameworks", "Other",
]

# An expiry this many days out (or nearer) is "expiring soon" — one source of
# truth shared with the library's evidence ledger (90 days).
EXPIRING_SOON_DAYS = LIB.EXPIRING_SOON_DAYS

# Board sort order: expired first, then expiring, then dated-ok, then undated.
_RANK = {"expired": 0, "expiring_soon": 1, "ok": 2, "none": 3}


def derive_expiry(asset, now=None):
    """Return a copy of `asset` with live-derived expiry fields added:
    `expiry_status` (expired/expiring_soon/ok/none), `days_to_expiry`, and
    `effective_expiry` (the date actually used). Never mutates the stored row.
    Falls back to mining the name/notes text so a date typed only into the notes
    still drives an alert — the same extractor the library uses."""
    a = dict(asset)
    iso = (a.get("expiry_date") or "").strip()
    if not iso:
        found = LIB.extract_expiries(f"{a.get('name', '')} {a.get('notes', '')}")
        iso = found[0] if found else ""
    if not iso:
        a["effective_expiry"] = ""
        a["expiry_status"] = "none"
        a["days_to_expiry"] = None
        return a
    days = LIB._days_until(iso, now)
    a["effective_expiry"] = iso
    a["days_to_expiry"] = days
    if days is not None and days < 0:
        a["expiry_status"] = "expired"
    elif days is not None and days <= EXPIRING_SOON_DAYS:
        a["expiry_status"] = "expiring_soon"
    else:
        a["expiry_status"] = "ok"
    return a


def board(assets, now=None):
    """The org-level view: every asset with derived status, sorted urgency-first
    (soonest-to-lapse leads, so a cert about to expire is impossible to miss)."""
    rows = [derive_expiry(a, now) for a in assets]
    rows.sort(key=lambda a: (
        _RANK.get(a["expiry_status"], 3),
        a["days_to_expiry"] if a["days_to_expiry"] is not None else 10 ** 6,
    ))
    return rows


def summary(rows):
    """Status counts for the header banner (rows already carry expiry_status)."""
    out = {"total": len(rows), "expired": 0, "expiring_soon": 0, "ok": 0, "none": 0}
    for a in rows:
        out[a.get("expiry_status", "none")] = out.get(a.get("expiry_status", "none"), 0) + 1
    return out


def seed_assets_from_library(items):
    """Turn library evidence items (Company Credentials / Governance / Commercial)
    into seed compliance-asset dicts (source=seed:library), carrying the extracted
    expiry. These are REFERENCES — no uploaded file — so the register starts
    populated with the org's known credentials, incl. any already expired."""
    seeds = []
    for it in items:
        if it.get("category") not in LIB.EVIDENCE_CATEGORIES:
            continue
        if not (it.get("item") or "").strip():
            continue
        seeds.append({
            "category": it.get("category") or "Company Credentials",
            "name": it.get("item") or "",
            "file_name": "",
            "stored_path": "",
            "content_type": "",
            "size_bytes": "",
            "expiry_date": it.get("expiry_date") or "",
            "review_frequency": it.get("review_frequency") or "",
            "owner": it.get("owner") or "",
            "notes": it.get("notes") or "",
            "source": "seed:library",
        })
    return seeds


def reference():
    """Vocabulary for the UI (categories + the expiring-soon window)."""
    return {"categories": CATEGORIES, "expiring_soon_days": EXPIRING_SOON_DAYS}
