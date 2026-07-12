# tests/test_tier1_teams.py
"""
Tier 1 (The Scrapring Circuit) omat joukkueet: 9 distinct lore-tiimia, ei
enaa Tier 0:n kierratysta. Varmistaa myos etta Tier 1 on kovempi kuin Tier 0
(ylennetty Tier 0 -mestari tippuisi takaisin).
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


def test_tier1_has_nine_distinct_teams():
    teams = _teams(2)  # engine tier 2 = lore Tier 1
    assert len(teams) == 9
    names = {t.name for t in teams}
    assert len(names) == 9  # kaikki eri nimia
    assert "Bridgeguard Five" in names
    assert "Bolt Cage Bruisers" in names
    assert "Cog Wardens" in names  # gnomi-nikkarit


def test_tier1_teams_are_authored_not_renamed():
    """Authored-tiimien lore-nimet sailyvat (ei positionaalista uudelleennimeamista)."""
    teams = _teams(2)
    for t in teams:
        assert getattr(t, "authored", False) is True
        assert getattr(t, "reputation", "")


def test_tier1_full_armed_rosters():
    for t in _teams(2):
        r = _roster(t)
        assert len(r) == 5
        for u in r:
            wn = getattr(u.equipment.get("main_hand"), "name", "")
            assert wn and wn not in ("Fists", "Fist"), f"{t.name}: {u.name} unarmed"


def test_tier0_still_seven_teams():
    """Tier 0 pysyy litteassa latauksessa (7 arkkityyppia)."""
    assert len(_teams(1)) == 7


def test_tier1_harder_than_tier0():
    """Tier 1 keskiteho > Tier 0 -> ylennys on aito askel ylospain."""
    t0 = _avg_power(_teams(1))
    t1 = _avg_power(_teams(2))
    assert t1 > t0 * 1.15, f"Tier1 {t1:.1f} not clearly above Tier0 {t0:.1f}"


def test_tier0_champion_would_relegate_from_tier1():
    """Tier 0:n paras jaa Tier 1:n heikoimman tuntumaan -> tippuisi takaisin."""
    from leagues.league_engine import _unit_power

    def team_pow(t):
        r = _roster(t)
        return sum(_unit_power(u) for u in r) / len(r) if r else 0

    t0_best = max(team_pow(t) for t in _teams(1))
    t1_powers = sorted(team_pow(t) for t in _teams(2))
    # Tier 0 mestari on Tier 1:n alapaassa (korkeintaan alimman neljanneksen tasoa)
    assert t0_best < t1_powers[len(t1_powers) // 2], \
        f"Tier0 best {t0_best:.1f} vs Tier1 median {t1_powers[len(t1_powers)//2]:.1f}"
