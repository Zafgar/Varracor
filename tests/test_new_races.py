# tests/test_new_races.py
"""
Uudet rodut: Werewolf (Bloodmoon Frenzy) ja Tortle (Shell Guard).
Koodipiirretty grafiikka, racial-kyvyt, ja rekisterointi factoryihin.
"""
import pytest
from settings import PLAYER_TEAM, ENEMY_TEAM


def test_races_registered_with_weakness():
    from races import RACES
    assert RACES["Werewolf"]["weakness"] == "Fire"
    assert RACES["Tortle"]["weakness"] == "Magic"
    # Werewolf nopea, Tortle hidas & panssaroitu
    assert RACES["Werewolf"]["spd_mult"] > 1.0
    assert RACES["Tortle"]["defense"] >= 4


def test_units_construct():
    from units.werewolf import Werewolf
    from units.tortle import Tortle
    w = Werewolf("Fang", 0, 0, PLAYER_TEAM)
    t = Tortle("Shellwick", 0, 0, PLAYER_TEAM)
    assert w.race_name == "Werewolf"
    assert t.race_name == "Tortle"
    assert w.image is not None and t.image is not None  # fallback-grafiikka
    assert t.max_hp > w.max_hp  # tortle sitkeampi


def test_werewolf_frenzy_activates():
    from units.werewolf import Werewolf
    w = Werewolf("Fang", 0, 0, PLAYER_TEAM)
    assert w.use_racial_ability(manager=None) is True
    assert w.frenzy_timer > 0
    assert w.racial_cooldown > 0
    # cooldownin aikana ei uudelleen
    assert w.use_racial_ability(manager=None) is False


def test_werewolf_frenzy_lifesteal():
    from units.werewolf import Werewolf
    from units.orc import Orc
    w = Werewolf("Fang", 0, 0, PLAYER_TEAM)
    w.frenzy_timer = 300
    w.current_hp = 40
    foe = Orc("Dummy", 0, 0, ENEMY_TEAM)
    hp_before = w.current_hp
    foe.take_damage(30, "Physical", attacker=w)
    assert w.current_hp > hp_before, "Frenzyn pitaisi imea elamaa osuessa"


def test_tortle_shell_reduces_damage():
    from units.tortle import Tortle
    t = Tortle("Shellwick", 0, 0, PLAYER_TEAM)
    t.defense = 0  # eristetaan pelkka shell-vaikutus
    t.current_hp = t.max_hp
    t.shell_timer = 300
    before = t.current_hp
    t.take_damage(40, "Physical")
    lost = before - t.current_hp
    assert lost <= 12, f"Shell -75%: 40 dmg pitaisi tehda ~10, teki {lost}"


def test_tortle_shell_roots_movement():
    from units.tortle import Tortle
    t = Tortle("Shellwick", 300, 300, PLAYER_TEAM)
    t.shell_timer = 300
    t.update(obstacles=None, manager=None)
    assert t.speed == 0.0, "Shell juurruttaa (ei liiku)"


def test_new_races_in_save_map():
    from save_manager import _unit_class_map
    m = _unit_class_map()
    assert "Werewolf" in m
    assert "Tortle" in m


def test_new_races_have_name_generator():
    from races import get_random_name
    assert get_random_name("Werewolf") != "Unknown"
    assert get_random_name("Tortle") != "Unknown"
