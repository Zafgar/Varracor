# tests/test_dwarf_and_rattlebridge.py
"""
Dwarf-rotu (oma yksikkoluokka) ja Rattlebridgen kanoniset areenatiimit
(Rattlebridge Runners + Bridgeguard Five) lore-kokoonpanoineen.
"""
import pytest
from settings import PLAYER_TEAM


def test_dwarf_unit_constructs():
    from units.dwarf import Dwarf
    d = Dwarf("Olek", 0, 0, PLAYER_TEAM)
    assert d.race_name == "Dwarf"
    assert d.image is not None
    assert d.defense >= 3  # kaapiot sitkeita


def test_dwarf_has_stoneform_racial():
    from units.dwarf import Dwarf
    d = Dwarf("Olek", 0, 0, PLAYER_TEAM)
    d.racial_cooldown = 0
    assert d.use_racial_ability(manager=None) is True
    assert d.stoneform_timer > 0


def test_dwarf_in_save_map_and_build_team():
    from save_manager import _unit_class_map
    assert "Dwarf" in _unit_class_map()


def test_rattlebridge_runners_canonical_roster():
    from leagues.premades.tier1.rattlebridge_runners import create_team
    t = create_team(2)
    assert t.manager == "Corwin Hale"
    names = {u.name for u in t.members}
    assert {"Jax Merrin", "Sila Vorn", "Brenna Kest", "Olek Ironside",
            "Miri Vale"} <= names
    races = {u.name: u.race_name for u in t.members}
    assert races["Olek Ironside"] == "Dwarf"
    # Miri Vale on Pure Magic -noviisi
    miri = [u for u in t.members if u.name == "Miri Vale"][0]
    assert miri.equipment.get("spell1") is not None


def test_bridgeguard_five_canonical_roster():
    from leagues.premades.tier1.bridgeguard_five import create_team
    t = create_team(2)
    assert t.manager == "Halden Pike"
    races = {u.name: u.race_name for u in t.members}
    assert races.get("Bruk") == "Orc"
    assert races.get("Sel Copper") == "Dwarf"
    enna = [u for u in t.members if u.name == "Enna Reed"][0]
    assert enna.equipment.get("spell1") is not None


def test_tier1_features_dwarves():
    from leagues.league_data import generate_league_teams
    races = set()
    for t in generate_league_teams(2):
        for u in t.members:
            races.add(u.race_name)
    assert "Dwarf" in races
