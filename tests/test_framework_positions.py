"""G2 companion — FWF's own framework/DPS position, derived from the bid-library export.

These pin the HONESTY CEILING as much as the logic. A folder proves work, never
membership: the ladder must stop at `response_drafted`, and no amount of files may
promote an agreement to "member" or "submitted". Getting that wrong would manufacture
exactly the false record this project exists to prevent.

Offline: builds a fake export tree in tmp_path, so it runs in CI where the real
(gitignored, client-confidential) export doesn't exist.
"""
import os

os.environ.setdefault("LOCAL_AUTH_BYPASS", "1")

import framework_positions as FP  # noqa: E402


def _export(tmp_path, tree):
    """tree = {kind: {folder: {subdir: [filenames]}}} -> a fake bid-library export."""
    root = tmp_path / "04 Portal Registrations"
    for kind, folders in tree.items():
        for folder, subs in folders.items():
            for sub, files in subs.items():
                d = root / kind / folder / sub
                d.mkdir(parents=True, exist_ok=True)
                for f in files:
                    (d / f).write_text("x")
            if not subs:
                (root / kind / folder).mkdir(parents=True, exist_ok=True)
    return str(root)


def test_empty_folder_is_planned_not_pursued():
    """An empty scaffold (MOD AI & Edge, RM6396) is INTENT, not work."""
    assert FP._status(0, []) == "planned"


def test_docs_but_no_response_is_preparing():
    assert FP._status(12, []) == "preparing"


def test_response_file_is_the_top_of_the_ladder():
    """`response_drafted` is as far as folder evidence can honestly take us — it does NOT
    mean submitted, and it certainly does not mean we're a member."""
    status = FP._status(108, ["Tender Response Master - GCloud 15.xlsx"])
    assert status == "response_drafted"
    assert status not in ("submitted", "member", "won")


def test_rm_code_is_extracted_and_the_source_typo_normalised():
    """The real folder is 'AI DPS RM62000' — a typo for RM6200. Normalise on read; we
    don't own the source, so don't rewrite it."""
    assert FP.rm_code("Automation Marketplace DPS RM6173") == "RM6173"
    assert FP.rm_code("AI DPS RM62000") == "RM6200"
    assert FP.rm_code("Bluelight Commercial Framework") is None


def test_missing_export_degrades_and_never_fabricates(tmp_path):
    """No export (CI, fresh clone) -> unavailable. Never an empty-but-confident answer."""
    res = FP.positions(root=str(tmp_path / "nope"))
    assert res["available"] is False
    assert res["positions"] == []


def test_positions_reads_a_real_shaped_tree(tmp_path):
    root = _export(tmp_path, {
        "Frameworks": {
            "G Cloud 15": {"01 Framework Docs": ["a.pdf"],
                           "02 Submission Master": ["Tender Response Master.xlsx"]},
            "MOD AI & Edge Framework DDAD": {},
        },
        "DPS": {"Spark DPS - RM6094": {"Bid Pack": ["Attachment 1.xlsx"]}},
    })
    res = FP.positions(root=root)
    assert res["available"] is True
    by_name = {p["name"]: p for p in res["positions"]}

    gc = by_name["G Cloud 15"]
    assert gc["status"] == "response_drafted"
    assert gc["agreement_id"] == "RM1557.15"     # mapped by hand: no RM code in the name
    assert gc["kind"] == "Framework"

    assert by_name["MOD AI & Edge Framework DDAD"]["status"] == "planned"
    assert by_name["Spark DPS - RM6094"]["agreement_id"] == "RM6094"
    assert by_name["Spark DPS - RM6094"]["kind"] == "DPS"


def test_annotate_flags_the_radar_contradiction(tmp_path):
    """The whole point: the radar says 'not a member, go prepare' while a response is
    already drafted. That must surface, not sit quietly in two places."""
    root = _export(tmp_path, {"Frameworks": {
        "G Cloud 15": {"02 Submission Master": ["Tender Response Master.xlsx"]}}})
    agreements = [{"id": "RM1557.15", "fwf_status": "not_member"},
                  {"id": "RM6190", "fwf_status": "not_member"}]
    res = FP.annotate(agreements, root=root)
    by_id = {a["id"]: a for a in res["agreements"]}

    assert by_id["RM1557.15"]["contradicts_radar"] is True
    assert by_id["RM1557.15"]["our_position"]["status"] == "response_drafted"
    # Nothing in the library about TS4 -> no position, and no invented contradiction.
    assert by_id["RM6190"]["our_position"] is None
    assert by_id["RM6190"]["contradicts_radar"] is False


def test_agreements_we_work_on_but_the_radar_never_heard_of(tmp_path):
    root = _export(tmp_path, {"Frameworks": {
        "Bluelight Commercial Framework": {"02 Submission Master": ["resp.docx"]}}})
    res = FP.annotate([{"id": "RM6190", "fwf_status": "not_member"}], root=root)
    names = [p["name"] for p in res["not_on_radar"]]
    assert "Bluelight Commercial Framework" in names
