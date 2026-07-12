# tests/test_tier0_teams.py
"""
Tier 0 -areenan joukkueiden tasapainotestit. Nappaa erityisesti aiemman
bugin, jossa vaarat itemnimet (esim. "Rusty Sword") jattivat gladiaattorit
nyrkeille, ja Rusty Buckets -bugin (vain 2 jasenta).
"""
import pytest


def _tier0_teams():
    from leagues.league_data import generate_league_teams
    # engine tier 1 = lore Tier 0
    return generate_league_teams(1)


def _roster(t):
    from leagues.league_engine import _safe_roster
    return _safe_roster(t)


def test_seven_teams_load():
    teams = _tier0_teams()
    assert len(teams) == 7


def test_every_team_has_five_members():
    for t in _tier0_teams():
        roster = _roster(t)
        assert len(roster) == 5, f"{getattr(t,'name','?')} has {len(roster)} members"


def test_no_gladiator_is_unarmed():
    """Jokaisella on oikea ase (ei Fists) -> vaarat itemnimet kiinni."""
    for t in _tier0_teams():
        for u in _roster(t):
            w = u.equipment.get("main_hand")
            wn = getattr(w, "name", "")
            assert wn and wn not in ("Fists", "Fist"), \
                f"{getattr(t,'name','?')}: {u.name} is unarmed ({wn})"


def test_roster_property_tracks_members():
    """t.members = [] premadeissa ei saa katkaista roster-aliasta."""
    from leagues.premades import lost_soliders
    t = lost_soliders.create_team(1)
    assert t.roster is t.members
    assert len(t.roster) == 5


def test_weapon_variety_across_teams():
    """Koko arsenaali kaytossa: vahintaan 8 eri asetta Tier 0:ssa."""
    weapons = set()
    for t in _tier0_teams():
        for u in _roster(t):
            weapons.add(getattr(u.equipment.get("main_hand"), "name", "?"))
    assert len(weapons) >= 8, f"Only {len(weapons)} weapon types: {sorted(weapons)}"


def test_teams_have_named_gladiators_and_reputation():
    """Ei geneerisia 'Ranger 1' -nimia; jokaisella tiimilla maine."""
    from leagues.premades import (lost_soliders, drunken_brawlers, bandit_clan,
                                   forest_walkers, arena_rats, goblin_looters,
                                   rusty_bucket)
    for mod in (lost_soliders, drunken_brawlers, bandit_clan, forest_walkers,
                arena_rats, goblin_looters, rusty_bucket):
        t = mod.create_team(1)
        assert getattr(t, "reputation", ""), f"{t.name} missing reputation"
        for u in t.members:
            # Nimi ei saa paattya pelkkaan numeroon (esim. 'Ranger 1')
            assert not u.name.strip().split()[-1].isdigit(), \
                f"{t.name} has generic name: {u.name}"


def test_power_spread_has_top_and_bottom():
    """Selkea voimahierarkia: paras selvasti heikointa vahvempi."""
    from leagues.league_engine import _unit_power
    powers = []
    for t in _tier0_teams():
        roster = _roster(t)
        p = sum(_unit_power(u) for u in roster) / max(1, len(roster))
        powers.append(p)
    powers.sort()
    assert powers[-1] > powers[0] * 1.1, \
        f"Power spread too flat: {[round(p,1) for p in powers]}"
