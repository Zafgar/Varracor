"""Armor rework (pelitesti 26): iso panssarikatalogi.

23 linjaa x 8 tieriä: vartalot (heavy/medium/light/cloth, myös koulu-
sidonnaiset), kypärät (head-slot), kilvet (tier-portitus Tower
Disciplineen). Statit stat_curve-budjeteista, hinnat slotin mukaan.
"""
import pytest

from items.gear_catalog import CATALOG, make_gear, martial_gear, \
    make_gear_by_name
from items.tiered_gear import LINES, TieredGear
from settings import PLAYER_TEAM


BODY_LINES = [k for k, v in LINES.items()
              if v["slot"] == "body" and v["kind"] == "armor"]
HEAD_LINES = [k for k, v in LINES.items() if v["slot"] == "head"]
SHIELD_LINES = [k for k, v in LINES.items() if v["kind"] == "shield"]


def test_line_coverage():
    assert len(BODY_LINES) >= 9, BODY_LINES     # 3 vanhaa + 6 uutta
    assert len(HEAD_LINES) == 5, HEAD_LINES
    assert len(SHIELD_LINES) == 3, SHIELD_LINES
    # Kaikki panssariluokat edustettuina vartaloissa JA kypärissä
    body_groups = {LINES[l]["armor_group"] for l in BODY_LINES}
    head_groups = {LINES[l]["armor_group"] for l in HEAD_LINES}
    assert body_groups == {"cloth", "light", "medium", "heavy"}
    assert head_groups == {"cloth", "light", "medium", "heavy"}


def test_every_line_has_8_named_tiers():
    from items.gear_catalog import NAMES
    for line in LINES:
        assert line in NAMES, f"{line} puuttuu NAMES-taulusta"
        assert len(NAMES[line]) == 8, f"{line}: nimiä != 8"
        assert len(set(NAMES[line])) == 8, f"{line}: tuplanimiä"


def test_stats_and_price_grow_with_tier():
    for line in LINES:
        prev_power = -1
        prev_cost = 0
        for t in range(1, 9):
            g = make_gear(f"{line}_t{t}")
            power = (g.str_bonus + g.dex_bonus + g.int_bonus + g.defense
                     + g.health_bonus + g.mana_bonus)
            assert power >= prev_power, f"{line} t{t}: teho ei kasva"
            assert g.cost > prev_cost, f"{line} t{t}: hinta ei kasva"
            prev_power, prev_cost = power, g.cost


def test_helmets_cheaper_than_bodies():
    for t in (1, 4, 8):
        helm = make_gear(f"greathelm_t{t}")
        body = make_gear(f"juggernaut_t{t}")
        assert helm.cost < body.cost
        assert helm.slot_type == "head"


def test_heavy_helmet_requires_heavy_prof():
    from units.human import Human
    u = Human("U", 0, 0, PLAYER_TEAM)
    u.level = 30
    helm = make_gear("greathelm_t1")
    ok, reason = u.can_equip_item_to_slot("head", helm)
    assert not ok and "Heavy" in reason
    u.armor_masteries.add("heavy")
    ok, _ = u.can_equip_item_to_slot("head", helm)
    assert ok


def test_tiered_shields_gate_on_tower_discipline():
    from units.human import Human
    u = Human("U", 0, 0, PLAYER_TEAM)
    u.level = 30
    u.weapon_masteries.add("shield")
    low = make_gear("aegis_t2")
    assert low.shield_tier == 1
    ok, _ = u.can_equip_item_to_slot("off_hand", low)
    assert ok
    high = make_gear("bulwark_shield_t5")
    assert high.shield_tier == 2
    ok, reason = u.can_equip_item_to_slot("off_hand", high)
    assert not ok and "Tower" in reason
    u.shield_tier = 2
    ok, _ = u.can_equip_item_to_slot("off_hand", high)
    assert ok


def test_shield_block_grows_and_works_in_combat():
    b1 = make_gear("bulwark_shield_t1")
    b8 = make_gear("bulwark_shield_t8")
    assert b8.block_chance > b1.block_chance
    assert 0.0 < b8.block_chance <= 0.55
    # Aktiivinen blokki hyväksyy TieredGear-kilven (type "Shield")
    from units.human import Human
    u = Human("U", 0, 0, PLAYER_TEAM)
    u.equipment["off_hand"] = b1
    u.calculate_final_stats()
    u.weapon_masteries.add("shield")
    u.current_stamina = u.max_stamina
    u.set_blocking(True)
    assert u.is_blocking, "TieredGear-kilvellä ei voinut blokata"


def test_heavy_lines_have_weight_penalty():
    assert make_gear("juggernaut_t3").speed_bonus < 0
    assert make_gear("bulwark_shield_t3").speed_bonus < 0
    assert make_gear("hood_t3").speed_bonus == 0


def test_school_bodies_carry_school_bonuses():
    blood = make_gear("bloodweave_t6")
    assert blood.school == "necromancy"
    assert blood.school_bonuses.get("lifesteal_pct", 0) > 0
    verd = make_gear("verdant_t6")
    assert verd.school_bonuses.get("hot_power", 0) > 0


def test_describe_lists_price_and_slot():
    d = make_gear("bulwark_shield_t5").describe()
    assert "Shield" in d and "Price" in d and "Block" in d
    assert "Tower Discipline" in d
    d2 = make_gear("circlet_t3").describe()
    assert "Helmet" in d2 and "Price" in d2


def test_martial_gear_includes_new_lines():
    lines = {g.line for g in martial_gear()}
    assert {"warrior", "juggernaut", "ranger", "greathelm", "hood",
            "buckler", "aegis", "bulwark_shield"} <= lines
    # Koulusidonnaiset EIVÄT kuulu sepälle
    assert "bloodweave" not in lines and "zealot" not in lines


def test_registry_roundtrip_by_name():
    """Save/load: TieredGear syntyy uudelleen näyttönimellä."""
    from items.item_registry import create_item
    g = make_gear("warhelm_t4")
    restored = create_item(g.name)
    assert restored is not None, "TieredGear katosi rekisteristä"
    assert restored.gear_id == g.gear_id
    assert restored.cost == g.cost
    # Ja gear_id:llä suoraan
    assert make_gear_by_name("hood_t2").name == make_gear("hood_t2").name


def test_full_set_stats_apply():
    """Koko setti päällä: statit nousevat selvästi (gear on pääasiallinen
    statilähde pitkässä juoksussa)."""
    from units.human import Human
    u = Human("U", 0, 0, PLAYER_TEAM)
    u.level = 30
    u.armor_masteries.update({"cloth", "light", "medium", "heavy"})
    u.weapon_masteries.add("shield")
    u.shield_tier = 2
    base_str = u.strength
    u.equipment["body"] = make_gear("juggernaut_t8")
    u.equipment["head"] = make_gear("greathelm_t8")
    u.equipment["off_hand"] = make_gear("bulwark_shield_t8")
    u.calculate_final_stats()
    assert u.strength > base_str + 100, (
        f"T8-setti antoi vain +{u.strength - base_str} STR")
    assert u.defense > 200, f"T8-setin defense {u.defense}"
    assert u.max_hp > 700, f"T8-setin HP {u.max_hp}"
