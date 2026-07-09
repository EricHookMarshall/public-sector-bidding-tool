#!/usr/bin/env python3
"""
Region code glossary — turns the opaque NUTS / ITL codes that the OCDS feeds
carry (e.g. "UKM50") into plain-English names ("Aberdeen City and Aberdeenshire").

Why this exists: notices store a delivery `region` that is often a UK ITL code,
not a place name, so the UI shows bare codes like "UKM50" next to "UK". This map
+ prefix fallback lets the API attach a human label and gives the UI a glossary
to show "what UKM50 means vs UK".

Coverage is the UK ITL/NUTS hierarchy: all 12 ITL1 nations/regions, plus the
ITL2/ITL3 breakdown for Scotland (where UKM50 lives) and a few major English/
devolved areas. Unknown codes fall back to their longest known prefix, so an
unlisted ITL3 code still resolves to its ITL1 nation rather than nothing.
"""

# code -> human label. Ordered roughly ITL1 → ITL2 → ITL3.
REGION_LABELS = {
    "UK": "United Kingdom",
    # --- ITL1: nations & English regions ---
    "UKC": "North East (England)",
    "UKD": "North West (England)",
    "UKE": "Yorkshire and the Humber",
    "UKF": "East Midlands (England)",
    "UKG": "West Midlands (England)",
    "UKH": "East of England",
    "UKI": "London",
    "UKJ": "South East (England)",
    "UKK": "South West (England)",
    "UKL": "Wales",
    "UKM": "Scotland",
    "UKN": "Northern Ireland",
    # --- ITL2: Scotland ---
    "UKM5": "North Eastern Scotland",
    "UKM6": "Highlands and Islands",
    "UKM7": "Eastern Scotland",
    "UKM8": "West Central Scotland",
    "UKM9": "Southern Scotland",
    # --- ITL3: Scotland (selected) ---
    "UKM50": "Aberdeen City and Aberdeenshire",
    "UKM61": "Caithness & Sutherland and Ross & Cromarty",
    "UKM62": "Inverness & Nairn and Moray, Badenoch & Strathspey",
    "UKM63": "Lochaber, Skye & Lochalsh, Arran & Cumbrae and Argyll & Bute",
    "UKM64": "Na h-Eileanan Siar (Western Isles)",
    "UKM65": "Orkney Islands",
    "UKM66": "Shetland Islands",
    "UKM71": "Angus and Dundee City",
    "UKM72": "Clackmannanshire and Fife",
    "UKM73": "East Lothian and Midlothian",
    "UKM75": "Edinburgh, City of",
    "UKM76": "Falkirk",
    "UKM77": "Perth & Kinross and Stirling",
    "UKM78": "Scottish Borders",
    "UKM79": "West Lothian",
    "UKM81": "East & West Dunbartonshire and Helensburgh & Lomond",
    "UKM82": "Glasgow City",
    "UKM83": "Inverclyde, East Renfrewshire and Renfrewshire",
    "UKM84": "North Lanarkshire",
    "UKM91": "South Ayrshire and East Ayrshire",
    "UKM92": "Dumfries & Galloway",
    "UKM93": "South Lanarkshire",
    # --- ITL2: a few high-traffic English areas ---
    "UKI3": "Inner London — West",
    "UKI4": "Inner London — East",
    "UKI5": "Outer London — East and North East",
    "UKI6": "Outer London — South",
    "UKI7": "Outer London — West and North West",
    "UKD3": "Greater Manchester",
    "UKD7": "Merseyside",
    "UKG3": "West Midlands (county)",
}


def _looks_like_code(value):
    """A region string we should try to translate: a NUTS/ITL code, not a place
    name already. UK ITL codes are 'UK' + uppercase letters/digits, len 2–5."""
    return (
        isinstance(value, str)
        and 2 <= len(value) <= 5
        and value.upper() == value
        and value.startswith("UK")
        and (value[2:] == "" or value[2:].isalnum())
    )


def label(value):
    """Human name for a region value. Exact match wins; otherwise fall back to
    the longest known prefix (so an unlisted ITL3 still resolves to its nation).
    Non-code values (already place names, or None) are returned unchanged."""
    if not _looks_like_code(value):
        return value
    if value in REGION_LABELS:
        return REGION_LABELS[value]
    for n in range(len(value) - 1, 1, -1):  # try UKM5, UKM, ... longest first
        if value[:n] in REGION_LABELS:
            return f"{REGION_LABELS[value[:n]]} (area {value})"
    return value


def labels_for(values):
    """{code: label} for a set of region values — used to ship a glossary of the
    codes actually present to the UI."""
    return {v: label(v) for v in values if v and label(v) != v}
