# tests/test_rattlebridge_content.py
"""
Rattlebridgen kaupunkisisalto: kanoniset tiimikokoonpanot ja rikastetut
avainhahmojen dialogit.
"""
import pytest


def test_local_teams_match_canon():
    from citys.rattlebridge.rattlebridge_data import LOCAL_TEAMS
    runners = LOCAL_TEAMS["rattlebridge_runners"]
    assert runners["manager"] == "Corwin Hale"
    assert "Olek Ironside" in runners["members"]  # Dwarf
    assert "Miri Vale" in runners["members"]      # Pure Magic novice
    guard = LOCAL_TEAMS["bridgeguard_five"]
    assert guard["manager"] == "Halden Pike"
    assert "Bruk" in guard["members"]             # Orc
    assert "Sel Copper" in guard["members"]       # Dwarf


def test_key_npcs_have_rich_dialogue():
    from citys.rattlebridge.rattlebridge_data import NAMED_NPCS
    for npc_id in ("sera_quench", "hendrik_ironspan", "prior_jannik_voss",
                   "captain_mara_chain"):
        lines = NAMED_NPCS[npc_id]["dialogue"]
        assert len(lines) >= 6, f"{npc_id} dialogue too short"


def test_dialogue_covers_city_themes():
    from citys.rattlebridge.rattlebridge_data import NAMED_NPCS
    alltext = " ".join(
        line.lower()
        for v in NAMED_NPCS.values()
        for line in v["dialogue"]
    )
    for theme in ("hush-mantle", "toll", "sponsor", "fever", "union"):
        assert theme in alltext, f"theme '{theme}' not surfaced in dialogue"
