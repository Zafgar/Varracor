# tests/test_spell_scaling.py
"""Pelitesti 33: loitsujen tehon PERUSTA (tier-skaalaus).
Varmistaa suunnittelulinjan: osta korkeampi tier -> selkeästi parempi,
ja INT skaalaa päälle (base + INT*coef). Nämä ovat spell-pohjan invariantit.
"""
from spells.spell_scaling import (
    TIER_BASE, TIER_INT_COEF, scaled_damage, tier_base, tier_int_coef)


def test_higher_tier_is_always_stronger_at_same_int():
    # Osta korkeampi tier -> enemmän vahinkoa (samalla INT:llä)
    for intelligence in (0, 30, 400, 1000):
        vals = [scaled_damage(t, intelligence, "nuke") for t in range(1, 9)]
        assert vals == sorted(vals), f"tierien pitää nousta (INT={intelligence})"
        assert all(b < a for b, a in zip(vals, vals[1:])), \
            f"jokainen tier tiukasti parempi (INT={intelligence})"


def test_base_dominant_at_low_int_coef_dominant_at_high_int():
    # Matalalla INT:llä base ratkaisee; korkealla INT-kerroin hallitsee
    t = 4
    low = scaled_damage(t, 0)          # pelkkä base
    assert low == int(TIER_BASE[t])
    high = scaled_damage(t, 1000)
    int_part = 1000 * TIER_INT_COEF[t]
    assert int_part > TIER_BASE[t], "INT-osuus dominoi endgamessa"
    assert high > low * 5


def test_int_coefficient_grows_with_tier():
    coefs = [TIER_INT_COEF[t] for t in range(1, 9)]
    assert coefs == sorted(coefs)
    assert all(b < a for b, a in zip(coefs, coefs[1:]))


def test_archetype_ordering_per_hit():
    # Per osuma: nuke > heal > aoe > dot_tick > channel_tick > utility
    order = ["nuke", "heal", "aoe", "dot_tick", "channel_tick", "utility"]
    vals = [scaled_damage(5, 300, a) for a in order]
    assert vals == sorted(vals, reverse=True), \
        "arkkityypit järjestyksessä (per-osuma-budjetti)"


def test_scaled_damage_matches_formula():
    assert scaled_damage(2, 100, "nuke") == int(35 + 100 * 1.2)
    # AoE painottaa alas sekä basen että kertoimen
    assert scaled_damage(2, 100, "aoe") == int(35 * 0.6 + 100 * 1.2 * 0.6)


def test_helpers_and_unknown_tier_safe():
    assert tier_base(3, "nuke") == 70
    assert tier_int_coef(3, "nuke") == 1.7
    assert scaled_damage(99, 500) == 0  # tuntematon tier -> 0, ei kaadu
