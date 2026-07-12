# tests/test_power_model.py
"""
Gear-tietoinen voimamalli: level painaa alussa, mutta gear (ase, panssari,
kilpi) vaikuttaa. Nain liigasimulaatio heijastaa todellista vahvuutta.
Kaytetaan Team.equip_unit-reittia (kuten premade-tiimit), joka myontaa
proficiencyt ennen varustamista.
"""
import pytest
from settings import PLAYER_TEAM


def _team():
    from leagues.league_data import Team
    return Team("Test", (100, 100, 100), tier=1)


def _human(team, name="T", level=3, weapons=(), armors=()):
    from units.human import Human
    u = Human(name, 0, 0, team.color)
    u.level = level
    for w in weapons:
        team.equip_unit(u, w)
    for a in armors:
        team.equip_unit(u, a)
    u.calculate_final_stats()
    u.current_hp = u.max_hp
    return u


def test_armed_beats_unarmed_in_power():
    from leagues.league_engine import _unit_power
    t = _team()
    bare = _human(t, "Bare")
    armed = _human(t, "Armed", weapons=("Iron Sword",))
    assert armed.equipment.get("main_hand").name != "Fists"
    assert _unit_power(armed) > _unit_power(bare)


def test_gear_and_level_both_contribute():
    from leagues.league_engine import _unit_power
    t = _team()
    u = _human(t, weapons=("Iron Sword",), armors=("Rusty Mail",))
    power = _unit_power(u)
    level_part = u.level * 12.0
    gear_part = power - level_part
    assert level_part > 0
    assert gear_part > 0
    assert level_part >= gear_part  # Lv3:lla level >= gear (alussa tarkea)


def test_shield_adds_power():
    from leagues.league_engine import _unit_power, _has_shield
    t = _team()
    plain = _human(t, "Plain", weapons=("Iron Sword",))
    shielded = _human(t, "Shield", weapons=("Iron Sword", "Wooden Buckler"))
    assert _has_shield(shielded) is True
    assert _unit_power(shielded) > _unit_power(plain)


def test_higher_level_outweighs_gear_early():
    """Lv6 ilman asetta voittaa Lv3:n aseella -> level tarkea alussa."""
    from leagues.league_engine import _unit_power
    t = _team()
    low = _human(t, "Low", level=3, weapons=("Iron Sword",))
    high = _human(t, "High", level=6)
    assert _unit_power(high) > _unit_power(low)
