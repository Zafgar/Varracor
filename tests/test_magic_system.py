# tests/test_magic_system.py
"""
Magiajarjestelman perusta: koulukunnat, data-driven loitsukirjasto ja
arcane strain (loitsiminen ei ole ilmaista).
"""
import pytest
from settings import PLAYER_TEAM, ENEMY_TEAM


def test_schools_and_tiers_defined():
    from magic.schools import SCHOOLS, SPELL_TIERS
    for k in ("pure", "holy", "necromancy", "druidism", "manipulation", "abyssal"):
        assert k in SCHOOLS
    assert SCHOOLS["abyssal"].get("hero_only") is True
    assert len(SPELL_TIERS) == 8
    assert SPELL_TIERS[1] == "Apprentice" and SPELL_TIERS[8] == "Grand"


def test_library_spells_resolve_via_create_item():
    from items.item_registry import create_item
    for n in ("Spark Bolt", "Light Mend", "Prime Equation", "Judgment"):
        sp = create_item(n)
        assert sp is not None, f"{n} missing"
        assert 1 <= sp.tier <= 8
        assert sp.strain > 0
        assert sp.school in ("pure", "holy", "necromancy", "druidism",
                             "manipulation", "abyssal")


def test_higher_tier_costs_more():
    from items.item_registry import create_item
    t1 = create_item("Spark Bolt")
    t8 = create_item("Prime Equation")
    assert t8.strain > t1.strain
    assert t8.mana_cost > t1.mana_cost
    assert t8.damage > t1.damage


def test_max_strain_scales_with_intelligence():
    from units.human import Human
    low = Human("Low", 0, 0, PLAYER_TEAM)
    low.base_attributes["int"] = 5
    low.calculate_final_stats()
    high = Human("High", 0, 0, PLAYER_TEAM)
    high.base_attributes["int"] = 25
    high.calculate_final_stats()
    assert high.max_strain > low.max_strain


def test_strain_blocks_repeated_casting():
    from game_manager import GameManager
    from items.item_registry import create_item
    from units.human import Human
    from units.orc import Orc
    m = GameManager(); m.match_in_progress = True; m.current_arena = None
    mage = Human("Mage", 300, 300, PLAYER_TEAM)
    mage.base_attributes["int"] = 10
    mage.base_attributes["mana"] = 500
    mage.calculate_final_stats()
    mage.current_mana = mage.max_mana
    mage.spell_slots_unlocked = {1}
    mage.max_spell_tier = 2
    mage.equipment["spell1"] = create_item("Spark Bolt")
    foe = Orc("Foe", 500, 300, ENEMY_TEAM)
    m.all_units.add(mage, foe)
    casts = 0
    for _ in range(300):
        if mage.try_cast_spells(foe, [mage, foe], manager=m):
            casts += 1
            mage.spell_cooldowns["spell1"] = 0  # eristetaan strain (ei cd)
        if mage.current_strain >= mage.max_strain - 6:
            break
    assert casts > 0
    # nyt uupunut -> ei enaa castia
    assert not mage.try_cast_spells(foe, [mage, foe], manager=m)


def test_all_five_schools_have_content():
    from magic.spell_data import SPELL_LIBRARY
    from collections import Counter
    by_school = Counter(v["school"] for v in SPELL_LIBRARY.values())
    for sk in ("pure", "holy", "necromancy", "druidism", "manipulation"):
        assert by_school[sk] >= 5, f"{sk} too few spells: {by_school[sk]}"
    assert len(SPELL_LIBRARY) >= 40


def test_every_library_spell_resolves():
    from magic.spell_data import SPELL_LIBRARY
    from items.item_registry import create_item
    for n in SPELL_LIBRARY:
        assert create_item(n) is not None, f"{n} does not resolve"


def test_lore_named_spells_present():
    from magic.spell_data import SPELL_LIBRARY
    for n in ("Spark Bolt", "Prime Equation", "Light Mend", "Resurrection Seal",
              "Grave Chill", "Death Sovereignty", "Thorn Lash", "Worldroot Awakening",
              "Minor Illusion", "Perfect Lie"):
        assert n in SPELL_LIBRARY, f"lore spell {n} missing"


def test_warded_buff_reduces_damage():
    from units.human import Human
    u = Human("T", 0, 0, PLAYER_TEAM)
    u.defense = 0
    u.current_hp = u.max_hp
    u.apply_status("Warded", 300, 0)
    before = u.current_hp
    u.take_damage(50, "Physical")
    lost = before - u.current_hp
    assert 30 <= lost <= 40  # ~30% reduction


def test_summon_spawns_ally():
    from game_manager import GameManager
    from items.item_registry import create_item
    from units.human import Human
    m = GameManager(); m.match_in_progress = True; m.current_arena = None
    necro = Human("Necro", 300, 300, PLAYER_TEAM)
    before = len(list(m.my_team))
    create_item("Raise Servant").cast(necro, None, m)
    assert len(list(m.my_team)) > before


def test_debuff_applies_status():
    from game_manager import GameManager
    from items.item_registry import create_item
    from units.human import Human
    from units.orc import Orc
    m = GameManager(); m.match_in_progress = True; m.current_arena = None
    caster = Human("C", 300, 300, PLAYER_TEAM)
    foe = Orc("F", 400, 300, ENEMY_TEAM)
    create_item("Grave Chill").cast(caster, foe, m)
    assert any(e["type"] == "Slow" for e in foe.status_effects)


def test_strain_regenerates():
    from units.human import Human
    u = Human("Mage", 0, 0, PLAYER_TEAM)
    u.calculate_final_stats()
    u.current_strain = 50.0
    for _ in range(200):
        u.update(obstacles=None, manager=None)
    assert u.current_strain < 50.0
