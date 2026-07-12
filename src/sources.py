#!/usr/bin/env python3
"""
Source registry — the single list of connectors the UI can run.

Each entry exposes a uniform `run(**search_params)` callable (see
find_tender_filter.run / contracts_finder_filter.run) so api.py can fan a search
out across any selected subset without knowing each source's internals.

Adding a new source is a small code change: write a connector with the same
`run(days, cpv_codes, stage, open_only, published_from, published_to, use_db)`
signature and append one entry here. Nothing else needs to know about it.
"""
import find_tender_filter as ft
import contracts_finder_filter as cf
import public_contracts_scotland as pcs
import sell2wales as s2w

# key -> registry entry. `key` is the stable id the UI/API pass around;
# `name` is the human label (and matches the connector's SOURCE_NAME so it lines
# up with stored rows / source_runs).
SOURCES = {
    "find_a_tender": {
        "name": ft.SOURCE_NAME,
        "endpoint": ft.API,
        "run": ft.run,
        "note": "UK Find a Tender — higher-value (>£139k) notices, filtered on 'updated'.",
    },
    "contracts_finder": {
        "name": cf.SOURCE_NAME,
        "endpoint": cf.API,
        "run": cf.run,
        "note": "UK Contracts Finder — lower-value notices; rate-limited, slower to run.",
    },
    "public_contracts_scotland": {
        "name": pcs.SOURCE_NAME,
        "endpoint": pcs.API,
        "run": pcs.run,
        "note": "Public Contracts Scotland — Scottish notices incl. sub-threshold (OCDS).",
    },
    "sell2wales": {
        "name": s2w.SOURCE_NAME,
        "endpoint": s2w.API,
        "run": s2w.run,
        "note": "Sell2Wales — Welsh notices incl. sub-threshold (OCDS). Upstream list API "
                "currently unreliable; degrades per-partition rather than failing.",
    },
}

# Default CPV scope + stage list live in the reference connector so there is one
# source of truth; the UI seeds its controls from these.
DEFAULT_CPV = ft.TARGET_CPV
STAGES = ft.STAGES


def options():
    """Search-form options for the UI (available sources, stages, default CPV)."""
    return {
        "sources": [
            {"key": k, "name": v["name"], "note": v.get("note", "")}
            for k, v in SOURCES.items()
        ],
        "stages": STAGES,
        "default_cpv": DEFAULT_CPV,
    }
