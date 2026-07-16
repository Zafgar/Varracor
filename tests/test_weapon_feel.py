"""Aseperheiden identiteettien (systems/weapon_feel.py) vahtitestit.

Vahtii: perhetaulun kattavuus ja arvohaarukat, DPS-pariteetti (rytmi
erottaa perheet, ei raaka DPS), backstab-geometria, point blank -sääntö,
ja että JOKAINEN aseperhe toimii AI:n käsissä (duel päättyy ja vahinkoa
syntyy - "AI osaa myös käyttää").
"""
import os
import random

import pygame
import pytest

from systems import weapon_feel
from settings import PLAYER_TEAM, ENEMY_TEAM

ALL_GROUPS = ["sword", "dagger", "axe", "mace", "spear", "fists",
              "bow", "crossbow", "staff", "book"]


def test_family_table_covers_all_groups():
    for g in ALL_GROUPS:
        assert g in weapon_feel.FAMILY, f"{g} puuttuu FAMILY-taulusta"
        fam = weapon_feel.FAMILY[g]
        assert 0.4 <= fam["cd"] <= 1.5, (g, fam["cd"])
        assert 0.5 <= fam["dmg"] <= 1.5, (g, fam["dmg"])
        assert 0.4 <= fam["stamina"] <= 1.5
        assert 0 <= fam["range"] <= 20


def test_melee_dps_parity():
    """Rytmi (cd) erottaa perheet - dmg-kompensaatio pitää DPS:n
    haarukassa. Estää esim. daggerin hivuttamisen DPS-hirviöksi."""
    for g in ("sword", "dagger", "axe", "mace", "spear", "fists"):
        fam = weapon_feel.FAMILY[g]
        rel_dps = fam["dmg"] / fam["cd"]
        assert 0.80 <= rel_dps <= 1.40, (
            f"{g}: dmg/cd = {rel_dps:.2f} - perheen DPS karannut haarukasta")


class _Dummy:
    def __init__(self, x, facing_right=True):
        self.rect = pygame.Rect(x, 100, 30, 40)
        self.facing_right = facing_right


def test_backstab_geometry():
    target = _Dummy(500, facing_right=True)   # katsoo oikealle
    assert weapon_feel.is_behind(_Dummy(400), target), "selän takana (vas)"
    assert not weapon_feel.is_behind(_Dummy(600), target), "edessä"
    target.facing_right = False
    assert weapon_feel.is_behind(_Dummy(600), target)
    assert not weapon_feel.is_behind(_Dummy(400), target)


def test_point_blank_reduces_ranged_damage(manager):
    """Etäase tekee vähemmän iholta - melee vs ranged -dynamiikan ydin."""
    from units.human import Human
    from items.bows.weak_bow import WeakBow
    random.seed(5)
    shooter = Human("S", 300, 500, ENEMY_TEAM)
    shooter.equipment["main_hand"] = WeakBow()
    shooter.equipment["off_hand"] = None
    shooter.calculate_final_stats()
    assert shooter.weapon_type == "ranged"

    victim_near = Human("VN", 330, 500, PLAYER_TEAM)   # 30 px - iholla
    victim_near.equipment["off_hand"] = None
    victim_near.calculate_final_stats()
    victim_near.current_hp = victim_near.max_hp
    near_dmg = victim_near.take_damage(30, "Physical", attacker=shooter,
                                       manager=manager)

    victim_far = Human("VF", 900, 500, PLAYER_TEAM)    # 600 px - kaukana
    victim_far.equipment["off_hand"] = None
    victim_far.calculate_final_stats()
    victim_far.current_hp = victim_far.max_hp
    far_dmg = victim_far.take_damage(30, "Physical", attacker=shooter,
                                     manager=manager)
    assert near_dmg < far_dmg, (near_dmg, far_dmg)


@pytest.mark.parametrize("family,cls_path", [
    ("sword", "items.swords.weak_sword.WeakSword"),
    ("dagger", "items.daggers.weak_dagger.WeakDagger"),
    ("axe", "items.axes.weak_axe.WeakAxe"),
    ("mace", "items.maces.weak_mace.WeakMace"),
    ("spear", "items.spears.weak_spear.WeakSpear"),
    ("bow", "items.bows.weak_bow.WeakBow"),
    ("crossbow", "items.crossbows.weak_crossbow.WeakCrossbow"),
    ("staff", "items.staves.weak_staff.WeakStaff"),
    ("book", "items.books.weak_book.WeakBook"),
])
def test_ai_can_fight_with_family(manager, family, cls_path):
    """Jokainen aseperhe AI:n käsissä: duel miekkaa vastaan päättyy tai
    ainakin tuottaa vahinkoa (ase ei ole rikki AI:lle)."""
    from tests.conftest import run_duel
    from units.human import Human
    from items.swords.weak_sword import WeakSword
    mod_path, cls_name = cls_path.rsplit(".", 1)
    mod = __import__(mod_path, fromlist=[cls_name])
    weapon_cls = getattr(mod, cls_name)

    random.seed(4242)
    a = Human("A", 400, 500, PLAYER_TEAM, quality="Veteran")
    a.equipment["main_hand"] = weapon_cls()
    a.weapon_masteries.add(family)
    a.calculate_final_stats()
    a.current_hp = a.max_hp
    b = Human("B", 800, 500, ENEMY_TEAM, quality="Veteran")
    b.equipment["main_hand"] = WeakSword()
    b.weapon_masteries.add("sword")
    b.calculate_final_stats()
    b.current_hp = b.max_hp
    r = run_duel(manager, a, b, max_frames=7200)
    assert r["damaged"], f"{family}: kumpikaan ei tehnyt vahinkoa"


def test_family_rhythms_differ(manager):
    """Dagger lyö selvästi nopeammin kuin mace - rytmi on identiteetti."""
    from units.human import Human
    from items.daggers.weak_dagger import WeakDagger
    from items.maces.weak_mace import WeakMace
    d = Human("D", 0, 0, PLAYER_TEAM)
    d.equipment["main_hand"] = WeakDagger()
    d.weapon_masteries.add("dagger")
    d.calculate_final_stats()
    m = Human("M", 0, 0, PLAYER_TEAM)
    m.equipment["main_hand"] = WeakMace()
    m.weapon_masteries.add("mace")
    m.calculate_final_stats()
    assert d.attack_speed < m.attack_speed * 0.65, (
        f"dagger {d.attack_speed} vs mace {m.attack_speed} - "
        "rytmiero kadonnut")


def test_spear_has_longest_melee_reach(manager):
    from units.human import Human
    from items.spears.weak_spear import WeakSpear
    from items.swords.weak_sword import WeakSword
    s = Human("S", 0, 0, PLAYER_TEAM)
    s.equipment["main_hand"] = WeakSpear()
    s.weapon_masteries.add("spear")
    s.calculate_final_stats()
    w = Human("W", 0, 0, PLAYER_TEAM)
    w.equipment["main_hand"] = WeakSword()
    w.weapon_masteries.add("sword")
    w.calculate_final_stats()
    assert s.attack_range > w.attack_range + 20
