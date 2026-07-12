# tests/test_spell_balance.py
"""
Loitsujen tasapaino: vahinko/mana/strain kasvavat tason myota, jokaisella
koululla on oma VFX-vari, ja korkeat tasot ovat strain-rajoitettuja.
"""
import pytest


def test_school_colors_are_distinct():
    from magic.schools import school_color, SCHOOLS
    colors = [tuple(school_color(k)) for k in SCHOOLS]
    assert len(set(colors)) == len(SCHOOLS)  # jokaisella oma vari


def test_damage_scales_with_tier_within_school():
    from magic.spell_data import SPELL_LIBRARY
    dmg = [(v["tier"], v["power"]) for v in SPELL_LIBRARY.values()
           if v["school"] == "pure" and v["kind"] in ("damage", "debuff")]
    dmg.sort()
    powers = [p for _, p in dmg]
    assert powers == sorted(powers) and powers[-1] > powers[0]


def test_strain_and_mana_increase_with_tier():
    from magic.spell_data import strain_for, mana_for
    for t in range(1, 8):
        assert strain_for(t + 1) > strain_for(t)
        assert mana_for(t + 1) > mana_for(t)


def test_high_tier_more_efficient_but_costlier():
    from items.item_registry import create_item
    t1 = create_item("Spark Bolt")
    t8 = create_item("Prime Equation")
    # tehokkaampi per mana...
    assert (t8.damage / t8.mana_cost) > (t1.damage / t1.mana_cost)
    # ...mutta kalliimpi absoluuttisesti (strain + cooldown)
    assert t8.strain > t1.strain
    assert t8.cooldown_max > t1.cooldown_max


def test_every_school_has_a_vfx_color():
    from magic.schools import SCHOOLS
    for k, v in SCHOOLS.items():
        assert "color" in v and len(v["color"]) == 3
