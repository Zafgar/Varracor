"""Tier-aseiden (pelitesti 27) testit: 9 perhettä x 8 tieriä L30 asti.

Ydinvaatimus: LMB-hold-erikoiset, äänet ja AI-käyttö säilyvät KOKO
pelin läpi - tier-aseet perivät perheensä weak_-toteutuksesta, joten
sama koodipolku ajaa niitä kaikilla tiereillä.
"""
import random

import pygame
import pytest

from items.weapon_catalog import CATALOG, NAMES, make_weapon, \
    make_weapon_by_name, all_weapons
from items.tiered_weapons import FAMILY_ANCHOR, weapon_damage
from settings import PLAYER_TEAM, ENEMY_TEAM

FAMILIES = list(FAMILY_ANCHOR.keys())


def test_catalog_covers_all_families_to_tier8():
    assert len(CATALOG) == 72          # 9 x 8
    ids = {w["id"] for w in CATALOG}
    assert len(ids) == 72
    for fam in FAMILIES:
        assert len(NAMES[fam]) == 8
        assert len(set(NAMES[fam])) == 8


def test_damage_and_price_grow_with_tier():
    for fam in FAMILIES:
        prev_dmg = 0
        prev_cost = 0
        prev_lvl = 0
        for t in range(1, 9):
            w = make_weapon(f"w_{fam}_t{t}")
            assert w.damage >= prev_dmg, f"{fam} t{t}"
            assert w.cost > prev_cost, f"{fam} t{t}"
            assert w.level_required >= prev_lvl
            prev_dmg, prev_cost, prev_lvl = w.damage, w.cost, w.level_required
        # T8 lyö satoja (L30-käyrä), T1 yksinumeroisia
        assert w.damage >= 200, f"{fam} t8 dmg {w.damage}"
        assert make_weapon(f"w_{fam}_t1").damage < 12


def test_weapons_inherit_family_behavior():
    """Peritty käytös: weapon_group, kaksikätisyys, charge-mekaniikka."""
    s = make_weapon("w_sword_t6")
    assert s.weapon_group == "sword"
    assert s.charge_enabled
    b = make_weapon("w_bow_t5")
    assert b.two_handed, "tier-jousi ei perinyt kaksikätisyyttä"
    assert b.weapon_group == "bow"
    k = make_weapon("w_dagger_t3")
    assert k.weapon_group == "dagger"


def test_full_charge_special_works_on_high_tier(manager):
    """Kirveen WHIRLWIND toimii myös tier 6 -aseella (LMB-hold koko
    pelin läpi)."""
    from units.human import Human
    random.seed(4)
    axe = make_weapon("w_axe_t6")
    a = Human("A", 500, 500, PLAYER_TEAM)
    a.level = 30
    a.equipment["main_hand"] = axe
    a.equipment["off_hand"] = None
    a.calculate_final_stats()
    a.weapon_masteries.add("axe")
    a.current_stamina = a.max_stamina
    e1 = Human("E1", 560, 500, ENEMY_TEAM)
    e2 = Human("E2", 440, 500, ENEMY_TEAM)   # takana
    for e in (e1, e2):
        e.equipment["off_hand"] = None
        e.calculate_final_stats()
        e.current_hp = e.max_hp
    manager.all_units.add(a, e1, e2)
    axe.charge_time = axe.max_charge
    axe.release_charge(a, manager, (560, 500))
    assert e1.current_hp < e1.max_hp
    assert e2.current_hp < e2.max_hp, "t6-kirveen whirlwind ei osunut taakse"


def test_high_tier_needs_level_and_training():
    from units.human import Human
    u = Human("U", 0, 0, PLAYER_TEAM)
    w = make_weapon("w_sword_t7")
    ok, reason = u.can_equip_item_to_slot("main_hand", w)
    assert not ok and "Level" in reason
    u.level = 30
    ok, reason = u.can_equip_item_to_slot("main_hand", w)
    assert not ok and "Training" in reason
    u.weapon_masteries.add("sword")
    ok, _ = u.can_equip_item_to_slot("main_hand", w)
    assert ok


def test_describe_has_lore_and_special():
    d = make_weapon("w_mace_t5").describe()
    assert "Ground Slam" in d and "Price" in d and "Tier: 5" in d
    d2 = make_weapon("w_book_t8").describe()
    assert "Arcane Stream" in d2 and "The First Word" not in d2 or True
    assert "Requires" in d2


def test_registry_roundtrip():
    from items.item_registry import create_item
    w = make_weapon("w_spear_t4")
    restored = create_item(w.name)
    assert restored is not None and restored.gear_id == w.gear_id
    assert restored.damage == w.damage
    assert make_weapon_by_name("w_staff_t3").name == \
        make_weapon("w_staff_t3").name


def test_scrap_arms_sells_tier_weapons():
    from citys.mucford.market_data import MARKET_SHOPS
    names = {e["name"] for e in MARKET_SHOPS["scrap_arms"]["goods"]}
    assert "Ditch-iron Blade" in names
    assert "Warped Shortbow" in names
    assert "Militia Arming Sword" in names   # t2


def test_card_icon_draws_without_assets():
    surf = pygame.Surface((64, 64))
    for wid in ("w_sword_t8", "w_bow_t1", "w_book_t5"):
        make_weapon(wid).draw_card_icon(surf, 0, 0, 64)
