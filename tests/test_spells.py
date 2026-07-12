# tests/test_spells.py
"""
Loitsut alkavat Tier 2:sta. Firebolt (hyokkays) + Minor Heal (parannus).
Tier 0/1 pysyvat loitsuttomina.
"""
import pytest
from settings import PLAYER_TEAM, ENEMY_TEAM


def test_spells_resolve():
    from items.item_registry import create_item
    assert create_item("Firebolt") is not None
    assert create_item("Minor Heal") is not None


def _has_any_spell(u):
    return any(u.equipment.get(s) for s in ("spell1", "spell2", "spell3"))


def test_tier2_has_a_caster():
    from leagues.league_data import generate_league_teams
    casters = []
    for t in generate_league_teams(3):
        for u in t.members:
            if _has_any_spell(u):
                casters.append(u)
    assert casters, "Tier 2 should have at least one caster"
    lysa = casters[0]
    assert lysa.max_spell_tier >= 1
    assert 1 in lysa.spell_slots_unlocked


def test_tier0_is_spell_free():
    """Muckford (Tier 0) on loitsuton; Tier 1:sta alkaen Pure Magic -noviisit
    (esim. Miri Vale/Enna Reed) voivat kayttaa perusloitsuja."""
    from leagues.league_data import generate_league_teams
    for t in generate_league_teams(1):  # engine tier 1 = lore Tier 0
        for u in t.members:
            assert not _has_any_spell(u), \
                f"Tier 0 unit {u.name} unexpectedly has a spell"


def test_minor_heal_heals_ally():
    from items.item_registry import create_item
    from units.human import Human
    caster = Human("Caster", 0, 0, PLAYER_TEAM)
    caster.intelligence = 10
    ally = Human("Ally", 0, 0, PLAYER_TEAM)
    ally.current_hp = 20
    heal = create_item("Minor Heal")
    heal.cast(caster, ally, manager=None)
    assert ally.current_hp > 20


def test_firebolt_is_offensive_projectile():
    from items.item_registry import create_item
    fb = create_item("Firebolt")
    assert fb.is_skillshot is True
    assert fb.damage > 0
    assert "heal" not in fb.name.lower()
