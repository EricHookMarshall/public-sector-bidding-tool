#!/usr/bin/env python3
"""B04 — Answer checker (v2).

Blocking checks (fail submission):
  - over word/character limit
  - unfilled [EVIDENCE: ...] placeholders

Flagging checks (surface for human review, do not silently pass):
  - forbidden stale terms (CCS, MEAT, PCR 2015, RM6263, G-Cloud 14, DOS6 ...)
  - unsupported superlatives (leading, expert, proven, extensive, robust ...)
  - missing buyer-benefit signal
  - missing evidence citation signal
  - named people / clients (possible approval needed)
  - "we will" commitments (may need commercial approval)

Usage:
    python check_answer.py --limit "500 words" --keywords "azure,SLA" --file draft.txt
    echo "text" | python check_answer.py --limit "2000 characters"

Exit 0 = OK, 1 = needs attention. Flags alone set exit 1 too (human must clear).
"""
import argparse
import re
import sys

STALE = ["CCS", "MEAT", "PCR 2015", "PCR2015", "RM6263", "G-Cloud 14",
         "GCloud 14", "DOS6", "RM1043.8", "Crown Commercial Service"]
SUPERLATIVES = ["leading", "expert", "proven", "extensive", "robust",
                "world-class", "best-in-class", "cutting-edge", "seamless",
                "synergy", "synergies", "market-leading"]
BENEFIT_SIGNALS = ["benefit", "so that", "which means", "reduc", "saving",
                   "faster", "lower risk", "outcome", "value", "enables you"]
EVIDENCE_SIGNALS = ["[EVIDENCE:", "case study", "we delivered", "for example",
                    "certified", "ISO", "Cyber Essentials", "%", "reduced by",
                    "over ", "clients", "project"]


def parse_limit(limit):
    if not limit:
        return None, None
    m = re.search(r"(\d[\d,]*)", limit)
    if not m:
        return None, None
    n = int(m.group(1).replace(",", ""))
    return ("chars" if re.search(r"char", limit, re.I) else "words"), n


def find_terms(text, terms, whole_word=True):
    low = text.lower()
    hits = []
    for t in terms:
        pat = r"\b" + re.escape(t.lower()) + r"\b" if whole_word else re.escape(t.lower())
        if re.search(pat, low):
            hits.append(t)
    return hits


def main():
    ap = argparse.ArgumentParser(description="B04 answer checker v2")
    ap.add_argument("--limit", default="")
    ap.add_argument("--keywords", default="")
    ap.add_argument("--file")
    args = ap.parse_args()
    text = open(args.file).read() if args.file else sys.stdin.read()

    ok = True
    words = len(re.findall(r"\S+", text))
    chars = len(text)
    print(f"Words: {words}  Chars: {chars}")

    kind, n = parse_limit(args.limit)
    if kind:
        used = words if kind == "words" else chars
        over = used > n
        ok = ok and not over
        print(f"Limit: {n} {kind} -> {used} "
              f"({'OVER LIMIT **' if over else str(round(100*used/n))+'%'})")

    # blocking: placeholders
    ph = re.findall(r"\[EVIDENCE:[^\]]*\]", text)
    if ph:
        ok = False
        print(f"BLOCK: {len(ph)} unfilled evidence placeholder(s): {ph}")

    # flags — whole-word so short terms (CCS, MEAT, DOS6) don't match inside
    # unrelated words. If a future stale term genuinely needs substring matching,
    # check that subset separately with find_terms(..., whole_word=False).
    stale = find_terms(text, STALE)
    if stale:
        ok = False
        print(f"FLAG stale terms: {', '.join(sorted(set(stale)))} "
              f"(remove unless contextually valid)")

    sup = find_terms(text, SUPERLATIVES)
    if sup:
        ok = False
        print(f"FLAG unsupported claims: {', '.join(sorted(set(sup)))} "
              f"(evidence each or cut)")

    low = text.lower()
    if not any(s in low for s in [b.lower() for b in BENEFIT_SIGNALS]):
        ok = False
        print("FLAG: no clear buyer-benefit signal — state what the buyer gets")
    if not any(s.lower() in low for s in EVIDENCE_SIGNALS):
        ok = False
        print("FLAG: no evidence citation signal — every claim needs proof")

    # named people/clients: capitalised multi-word proper nouns (heuristic)
    proper = re.findall(r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b", text)
    proper = [p for p in proper if p.split()[0] not in
              ("Power", "Copilot", "Microsoft", "Azure", "Carbon", "Cyber",
               "Modern", "Cloud", "Crown")]
    if proper:
        print(f"FLAG possible named people/clients (check approval): "
              f"{', '.join(sorted(set(proper)))}")
        ok = False

    will = len(re.findall(r"\bwe will\b", low))
    if will:
        print(f"FLAG: {will} 'we will' commitment(s) — confirm commercial approval")
        ok = False

    if args.keywords:
        kws = [k.strip() for k in args.keywords.split(",") if k.strip()]
        missing = [k for k in kws if k.lower() not in low]
        if missing:
            ok = False
            print(f"FLAG missing keywords: {', '.join(missing)}")

    print("RESULT:", "OK" if ok else "NEEDS ATTENTION")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
