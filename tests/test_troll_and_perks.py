# tests/test_troll_and_perks.py
"""
Testit trollibossille (regeneraatio + tuliheikkous), seppäperkille
(train_unit-alennus) ja vihollistehtaan Forest Troll -mäppäykselle.
"""
import pytest


def _make_troll():
    from units.troll import Troll
    t = Troll("Forest Troll", 0, 0)
    return t


def test_troll_boss_stats():
    t = _make_troll()
    assert t.is_boss is True
    assert t.max_hp == 600
    assert t.current_hp == 600
    # AI ei pakene
    assert getattr(t.ai_controller, "no_retreat", False) is True


def test_troll_regenerates_when_not_burning():
    t = _make_troll()
    t.current_hp = 300
    # Aja 61 framea (regeneraatio laukeaa 60 framen välein)
    for _ in range(61):
        t.update(obstacles=None, manager=None)
    assert t.current_hp > 300, "Trollin pitäisi regeneroida ilman paloa"


def test_troll_regen_blocked_by_burn():
    t = _make_troll()
    t.current_hp = 300
    # Sytytä pitkä palo (kestää läpi testin)
    t.apply_status("Burn", 600, damage=0)
    hp_before = t.current_hp
    for _ in range(61):
        # Pidä palo päällä (älä anna gladiator.update kuluttaa sitä loppuun)
        if not t._is_burning():
            t.apply_status("Burn", 600, damage=0)
        t.update(obstacles=None, manager=None)
    assert t.current_hp <= hp_before, "Regeneraation pitää estyä kun trolli palaa"


def test_enemy_factory_creates_forest_troll(manager):
    from units.troll import Troll
    e1 = manager.create_enemy_by_name("Forest Troll")
    e2 = manager.create_enemy_by_name("Troll")
    assert isinstance(e1, Troll)
    assert isinstance(e2, Troll)


def test_forest_troll_boss_hunt_registered():
    from mission_data import BOSS_HUNTS
    assert "boss_forest_troll" in BOSS_HUNTS
    hunt = BOSS_HUNTS["boss_forest_troll"]
    assert ("Forest Troll", 1) in hunt["enemies"]


def test_troll_loot_key_maps_to_troll(manager):
    from loot_data import LOOT_DROPS
    t = _make_troll()
    key = manager._loot_key_for(t)
    assert key == "Troll"
    assert "Troll" in LOOT_DROPS


def test_smith_discount_applied_to_training(manager):
    # Yksinkertainen kohde-yksikkö
    from units.human import Human
    from settings import PLAYER_TEAM
    unit = Human("Trainee", 0, 0, PLAYER_TEAM)
    unit.upgrade_cost = 100

    # Ilman seppää: täysi hinta
    manager.has_smith = False
    assert manager.smith_discount() == 1.0
    manager.gold = 100
    ok = manager.train_unit(unit, "str")
    assert ok is True
    assert manager.gold == 0

    # Sepän kanssa: 20% alennus (100 -> 80)
    unit.upgrade_cost = 100
    manager.has_smith = True
    assert manager.smith_discount() == 0.8
    manager.gold = 80
    ok = manager.train_unit(unit, "str")
    assert ok is True
    assert manager.gold == 0
