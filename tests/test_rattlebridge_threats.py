# tests/test_rattlebridge_threats.py
"""
Rattlebridgen uhat: Hush-Mantle (akustinen tyhjio -> Silence), Gutter Vermin
(myrkkyparvi) ja Red Lantern Cadaver (tarttuva kuume, tuliheikko).
"""
import pytest
from settings import PLAYER_TEAM, ENEMY_TEAM


def test_factory_and_loot_keys(manager):
    from units.rattlebridge_threats import HushMantle, GutterVermin, RedLanternCadaver
    from loot_data import LOOT_DROPS
    cases = {
        "Hush-Mantle": (HushMantle, "Hush-Mantle"),
        "Gutter Vermin": (GutterVermin, "Gutter Vermin"),
        "Red Lantern Cadaver": (RedLanternCadaver, "Red Lantern Cadaver"),
    }
    for name, (cls, lootkey) in cases.items():
        e = manager.create_enemy_by_name(name)
        assert isinstance(e, cls)
        assert manager._loot_key_for(e) == lootkey
        assert lootkey in LOOT_DROPS


def test_hush_mantle_is_boss_and_silences():
    from units.rattlebridge_threats import HushMantle
    from units.human import Human
    from game_manager import GameManager
    m = GameManager(); m.match_in_progress = True; m.current_arena = None
    hush = HushMantle("Hush-Mantle", 300, 300, ENEMY_TEAM)
    assert hush.is_boss is True
    assert getattr(hush.ai_controller, "no_retreat", False) is True
    mage = Human("Mage", 340, 300, PLAYER_TEAM)
    m.all_units.add(hush, mage)
    for _ in range(95):
        hush.update(None, manager=m)
    assert mage.has_status("Silence")


def test_gutter_vermin_poisons_nearby():
    from units.rattlebridge_threats import GutterVermin
    from units.human import Human
    from game_manager import GameManager
    m = GameManager(); m.match_in_progress = True; m.current_arena = None
    g = GutterVermin("gv", 300, 320, ENEMY_TEAM)
    foe = Human("F", 330, 300, PLAYER_TEAM)
    m.all_units.add(g, foe)
    g._tox_tick = 59
    g.update(None, manager=m)
    assert foe.has_status("Poison")
    assert g.max_hp < 60  # hauras


def test_cadaver_fever_and_fire_weakness():
    from units.rattlebridge_threats import RedLanternCadaver
    from units.human import Human
    from game_manager import GameManager
    import races
    m = GameManager(); m.match_in_progress = True; m.current_arena = None
    c = RedLanternCadaver("c", 300, 300, ENEMY_TEAM)
    foe = Human("F", 325, 300, PLAYER_TEAM)
    m.all_units.add(c, foe)
    c._fever_tick = 69
    c.update(None, manager=m)
    assert foe.has_status("Poison")
    assert races.RACES["Undead"]["weakness"] == "Fire"
