# tests/test_tier2_teams.py
"""
Tier 2 (The Iron Circle) omat joukkueet: 7 authored-tiimia, Blacksteel-gear
ja uudet rodut (Werewolf/Tortle) mukana. Tier 2 kovempi kuin Tier 1.
"""
import pytest


def _teams(engine_tier):
    from leagues.league_data import generate_league_teams
    return generate_league_teams(engine_tier)


def _roster(t):
    from leagues.league_engine import _safe_roster
    return _safe_roster(t)


def _avg_power(teams):
    from leagues.league_engine import _unit_power
    ps = []
    for t in teams:
        r = _roster(t)
        if r:
            ps.append(sum(_unit_power(u) for u in r) / len(r))
    return sum(ps) / len(ps) if ps else 0


def test_tier2_loads_seven_authored_teams():
    teams = _teams(3)  # engine tier 3 = lore Tier 2
    assert len(teams) == 7
    names = {t.name for t in teams}
    assert "Shellwall Sentinels" in names
    assert "Giltgate Goldclaws" in names
    for t in teams:
        assert getattr(t, "authored", False) is True


def test_tier2_full_armed_rosters():
    for t in _teams(3):
        r = _roster(t)
        assert len(r) == 5
        for u in r:
            wn = getattr(u.equipment.get("main_hand"), "name", "")
            assert wn and wn not in ("Fists", "Fist"), f"{t.name}: {u.name} unarmed"


def test_tier2_features_new_races():
    races = set()
    for t in _teams(3):
        for u in _roster(t):
            races.add(u.race_name)
    assert "Werewolf" in races
    assert "Tortle" in races


def test_tier2_uses_blacksteel_gear():
    weapons = set()
    for t in _teams(3):
        for u in _roster(t):
            weapons.add(getattr(u.equipment.get("main_hand"), "name", ""))
    # Blacksteel-sarjaa pitaa nakya
    assert any("Blacksteel" in w or w in ("Yew Longbow", "Steel Crossbow", "Runed Staff")
               for w in weapons), f"No blacksteel gear: {weapons}"


def test_tier2_harder_than_tier1():
    t1 = _avg_power(_teams(2))
    t2 = _avg_power(_teams(3))
    assert t2 > t1 * 1.15, f"Tier2 {t2:.1f} not clearly above Tier1 {t1:.1f}"


def test_tier1_champion_would_relegate_from_tier2():
    from leagues.league_engine import _unit_power

    def tp(t):
        r = _roster(t)
        return sum(_unit_power(u) for u in r) / len(r) if r else 0

    t1_best = max(tp(t) for t in _teams(2))
    t2_sorted = sorted(tp(t) for t in _teams(3))
    assert t1_best < t2_sorted[len(t2_sorted) // 2], \
        f"Tier1 best {t1_best:.1f} vs Tier2 median {t2_sorted[len(t2_sorted)//2]:.1f}"
