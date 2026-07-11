#!/usr/bin/env python3
"""
CPV code catalogue — the human-readable list behind the UI's "add CPV code"
dropdown, so users pick "72000000 — IT services…" instead of typing bare codes.

Scope is IT / software / digital procurement (CPV 2008), which is what this PoC
targets. The 7 codes in cpv_codes.md (the default search scope) are a subset of
this list. Add a code + description here and it shows up in the dropdown.

This is a curated subset, not the full CPV vocabulary — unknown codes are still
accepted (typed into the free-text box) and simply show without a description.
"""

# code -> description, grouped by CPV division. Order here is preserved in the UI.
CPV_CATALOG = {
    # --- 72: IT services (consulting, software development, support) ---
    "72000000": "IT services: consulting, software development, Internet and support",
    "72100000": "Hardware consultancy services",
    "72200000": "Software programming and consultancy services",
    "72210000": "Programming services of packaged software products",
    "72211000": "Programming services of systems and user software",
    "72212000": "Programming services of application software",
    "72212920": "Office automation software development services",
    "72220000": "Systems and technical consultancy services",
    "72222300": "Information technology services",
    "72223000": "Information technology requirements review services",
    "72224000": "Project management consultancy services",
    "72230000": "Custom software development services",
    "72240000": "Systems analysis and programming services",
    "72250000": "System and support services",
    "72253000": "Helpdesk and support services",
    "72260000": "Software-related services",
    "72261000": "Software support services",
    "72262000": "Software development services",
    "72263000": "Software implementation services",
    "72265000": "Software configuration services",
    "72266000": "Software consultancy services",
    "72267000": "Software maintenance and repair services",
    "72300000": "Data services",
    "72310000": "Data-processing services",
    "72320000": "Database services",
    "72400000": "Internet services",
    "72410000": "Provider services",
    "72500000": "Computer-related services",
    "72510000": "Computer-related management services",
    "72600000": "Computer support and consultancy services",
    "72610000": "Computer support services",
    "72700000": "Computer network services",
    "72710000": "Local area network services",
    "72720000": "Wide area network services",
    "72800000": "Computer audit and testing services",
    "72900000": "Computer back-up and catalogue conversion services",
    # --- 48: software packages & information systems ---
    "48000000": "Software package and information systems",
    "48100000": "Industry specific software package",
    "48200000": "Networking, Internet and intranet software package",
    "48300000": "Document creation, drawing, imaging, scheduling and productivity software",
    "48400000": "Business transaction and personal business software package",
    "48500000": "Communication and multimedia software package",
    "48600000": "Database and operating software package",
    "48610000": "Database systems",
    "48620000": "Operating systems",
    "48700000": "Software package utilities",
    "48800000": "Information systems and servers",
    "48810000": "Information systems",
    "48820000": "Servers",
    "48900000": "Miscellaneous software package and computer systems",
    # --- 30: computer & office equipment ---
    "30200000": "Computer equipment and supplies",
    "30210000": "Data-processing machines (hardware)",
    "30213000": "Personal computers",
    "30213100": "Portable computers (laptops)",
    "30230000": "Computer-related equipment",
    "30232000": "Peripheral equipment",
    # --- 32: networking & telecoms equipment ---
    "32400000": "Networks",
    "32420000": "Network equipment",
    "32500000": "Telecommunications equipment and supplies",
    # --- 50 / 51: maintenance & installation of IT ---
    "50300000": "Repair/maintenance of PCs, office, telecoms and AV equipment",
    "50310000": "Maintenance and repair of office machinery",
    "50320000": "Repair and maintenance services of personal computers",
    "51600000": "Installation services of computers and information-processing equipment",
}


def catalog():
    """Catalogue as an ordered list of {code, description} for the UI dropdown."""
    return [{"code": c, "description": d} for c, d in CPV_CATALOG.items()]
