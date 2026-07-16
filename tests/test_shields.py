"""Kilpien (pelitesti 24) testit: skill tree -portitus, kaksikätisyys,
kilpitierit, SHIELD BASH ja blokin staminasäännöt.

Säännöt:
- Kilpi vaatii Shieldbearer-noden (EI tule heti Knightista - kilpi on
  kova yhdiste minkä tahansa aseen kanssa).
- Paremmat kilvet (tier 2) vaativat Tower Discipline -noden.
- Kaksikätiset aseet (jousi/varsijousi/keihäs/sauva) eivät salli
  off-handia; dagger+kilpi onnistuu (panostus kahteen haaraan).
- LMB blokin aikana = SHIELD BASH (vahinko + horjutus + työntö).
- Etäaseilla ja nyrkeillä ei voi blokata; blokki kuluttaa staminaa.
"""
import random

import pygame
import pytest

from settings import PLAYER_TEAM, ENEMY_TEAM


def _unit(x=500, y=500, team=PLAYER_TEAM):
    from units.human import Human
    u = Human("U", x, y, team)
    u.equipment["off_hand"] = None
    u.calculate_final_stats()
    u.current_hp = u.max_hp
    u.current_stamina = u.max_stamina
    return u


def _shield():
    from items.shields.weak_shield import WeakShield
    return WeakShield()


def test_shield_requires_shieldbearer_node():
    u = _unit()
    ok, reason = u.can_equip_item_to_slot("off_hand", _shield())
    assert not ok and "Shield" in reason

    u.weapon_masteries.add("shield")
    ok, _ = u.can_equip_item_to_slot("off_hand", _shield())
    assert ok


def test_skill_tree_gates_shields_deeper_than_knight():
    from skills.skills_data import SKILL_TREE
    assert "weapon_prof" not in SKILL_TREE["str_knight"]["effects"], (
        "Knight ei saa antaa kilpiä - Shieldbearer on erillinen node")
    sb = SKILL_TREE["str_shieldbearer"]
    assert "shield" in sb["effects"]["weapon_prof"]
    assert "str_knight" in sb["requires"], "Shieldbearer on Knightin takana"
    bw = SKILL_TREE["str_bulwark"]
    assert bw["effects"].get("shield_tier") == 2
    assert "str_shield_master" in bw["requires"]


def test_advanced_shield_requires_tower_discipline():
    from items.offhand.shields import SlimeShield
    u = _unit()
    u.weapon_masteries.add("shield")
    ok, reason = u.can_equip_item_to_slot("off_hand", SlimeShield())
    assert not ok and "Tower" in reason

    u.shield_tier = 2
    ok, _ = u.can_equip_item_to_slot("off_hand", SlimeShield())
    assert ok


def test_two_handed_weapons_forbid_offhand():
    from items.bows.weak_bow import WeakBow
    from items.spears.weak_spear import WeakSpear
    u = _unit()
    u.level = 5   # ohita level-portti - testataan kaksikätisyyttä
    u.weapon_masteries.update({"shield", "bow", "spear"})
    for weapon in (WeakBow(), WeakSpear()):
        u.equipment["main_hand"] = weapon
        ok, reason = u.can_equip_item_to_slot("off_hand", _shield())
        assert not ok and "both hands" in reason, weapon.name
    # Ja toisinpäin: kilpi kädessä -> kaksikätistä ei voi ottaa
    u.equipment["main_hand"] = None
    u.equipment["off_hand"] = _shield()
    ok, reason = u.can_equip_item_to_slot("main_hand", WeakBow())
    assert not ok and "both hands" in reason


def test_dagger_and_shield_combo_allowed():
    from items.daggers.weak_dagger import WeakDagger
    u = _unit()
    u.weapon_masteries.update({"dagger", "shield"})
    u.equipment["main_hand"] = WeakDagger()
    ok, _ = u.can_equip_item_to_slot("off_hand", _shield())
    assert ok, "dagger+kilpi on sallittu combo (kaksi puuta)"


def test_shield_bash_damages_staggers_and_pushes(manager):
    random.seed(3)
    a = _unit()
    a.equipment["off_hand"] = _shield()
    a.calculate_final_stats()
    # HUOM: calculate_final_stats rakentaa masteryt nodeista - lisää jälkeen
    a.weapon_masteries.add("shield")
    a.current_stamina = a.max_stamina
    e = _unit(x=545, team=ENEMY_TEAM)
    manager.all_units.add(a, e)
    a.set_blocking(True)
    assert a.is_blocking
    old_x = e.rect.centerx
    stamina_before = a.current_stamina
    assert a.perform_shield_bash((700, 500), manager)
    assert e.current_hp < e.max_hp, "bash ei tehnyt vahinkoa"
    assert e.stun_timer > 0, "bash ei horjuttanut"
    assert e.rect.centerx > old_x, "bash ei työntänyt"
    assert a.current_stamina < stamina_before, "bash ei maksanut staminaa"
    # Cooldown estää spämmin
    assert not a.perform_shield_bash((700, 500), manager)


def test_shield_bash_requires_shield_and_block(manager):
    a = _unit()
    a.set_blocking(True)   # ei kilpeä eikä asetta -> blokki ei nouse
    assert not a.perform_shield_bash((700, 500), manager)
    a.equipment["off_hand"] = _shield()
    a.calculate_final_stats()
    a.weapon_masteries.add("shield")
    a.is_blocking = False
    assert not a.perform_shield_bash((700, 500), manager), (
        "bash ilman aktiivista blokkia ei saa onnistua")


def test_ranged_and_fists_cannot_block():
    from items.bows.weak_bow import WeakBow
    u = _unit()
    u.weapon_masteries.add("bow")
    u.equipment["main_hand"] = WeakBow()
    u.calculate_final_stats()
    u.set_blocking(True)
    assert not u.is_blocking, "jousella ei voi blokata"

    u2 = _unit()   # nyrkit
    u2.set_blocking(True)
    assert not u2.is_blocking, "nyrkeillä ei voi blokata"


def test_block_drains_stamina_and_breaks_when_empty(manager):
    random.seed(3)
    a = _unit()
    a.equipment["off_hand"] = _shield()
    a.calculate_final_stats()
    a.weapon_masteries.add("shield")
    a.current_stamina = a.max_stamina
    a.current_hp = a.max_hp
    attacker = _unit(x=560, team=ENEMY_TEAM)
    manager.all_units.add(a, attacker)
    a.set_blocking(True)
    a.block_timer = 999      # ohita parry-ikkuna - testataan blokkia
    a.parry_cooldown = 999
    before = a.current_stamina
    a.take_damage(30, "Physical", attacker=attacker, manager=manager)
    assert a.current_stamina < before, "blokki ei kuluttanut staminaa"

    # Stamina loppu -> blokki murtuu ja osumasta tulee vahinkoa
    a.current_stamina = 1
    a.is_blocking = True
    hp_before = a.current_hp
    a.take_damage(30, "Physical", attacker=attacker, manager=manager)
    assert not a.is_blocking, "tyhjä stamina ei murtanut blokkia"
    assert a.current_hp < hp_before
