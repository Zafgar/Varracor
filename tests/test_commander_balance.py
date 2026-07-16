"""Commander vs gladiaattorit -tasapainon regressiotestit (pelitesti 23).

Kolme vahtia:
1. base_attributes["hp"] OIKEASTI vaikuttaa (max_hp-jäädytysbugi korjattu:
   troll 600, corrupted_crow 50, commander 120 eivät toteutuneet koskaan).
2. Commanderin base-statit pysyvät Elite-rekryytin haarukassa (ei OP:ta
   takaisin hivuttamalla). Vortex Blade on AINOA sallittu poikkeus - se on
   tarinaesine jonka Devourer vie introssa.
3. Commander käyttää SAMAA nopeuskaavaa kuin gladiaattorit (ei omaa
   liikesääntöä - sama äly ohjaa kaikkia).
"""
import pygame
import pytest

from settings import PLAYER_TEAM, ENEMY_TEAM


def _no_gear_commander():
    from units.commander import Commander
    c = Commander("BalanceCmd", 0, 0)
    c.equipment["main_hand"] = None   # ilman tarinamiekkaa (intro vie sen)
    c.calculate_final_stats()
    return c


def test_base_hp_applies_after_subclass_override(manager):
    """max_hp ei saa jäätyä rodun perusarvoon ennen aliluokan hp-asetusta."""
    from units.troll import Troll
    from units.corrupted_crow import CorruptedCrow
    t = Troll("T", 0, 0, ENEMY_TEAM)
    assert t.max_hp >= 600, (
        "Trollin base hp 600 ei toteudu (max_hp-avain jäätyi initissä?)")
    crow = CorruptedCrow("C", 0, 0, ENEMY_TEAM)
    assert crow.max_hp <= 80, "Glass cannon -variksen 50 hp ei toteudu"


def test_commander_hp_base_applies(manager):
    c = _no_gear_commander()
    # 120 base + STR*2, ei gearia
    assert 120 <= c.max_hp <= 160, c.max_hp


def test_rat_king_keeps_explicit_max_hp(manager):
    """max_hp-avain on yhä sallittu ylikirjoitus sitä käyttäville."""
    from units.rat_king import RatKing
    rk = RatKing("RK", 0, 0)
    assert rk.max_hp >= 800


def test_commander_stats_in_elite_band(manager):
    """Commander ei ole OP: melee-statit korkeintaan 40 % yli Eliten."""
    from units.human import Human
    c = _no_gear_commander()
    e = Human("E", 0, 0, ENEMY_TEAM, quality="Elite")
    cmd_martial = c.base_attributes["str"] + c.base_attributes["dex"]
    elite_martial = e.base_attributes["str"] + e.base_attributes["dex"]
    assert cmd_martial <= elite_martial * 1.4, (
        f"Commander STR+DEX {cmd_martial} vs Elite {elite_martial}: "
        "liian suuri etu (OP)")
    assert c.max_hp <= e.max_hp * 1.1, (
        f"Commander HP {c.max_hp} vs Elite {e.max_hp}")


def test_commander_speed_uses_shared_formula(manager):
    """Sama nopeuskaava kuin gladiaattoreilla (gladiator.py: walk_speed =
    (2 + DEX*0.025 + mod) * mult) - ei omaa liikesääntöä. Rekryyttiproxy ei
    kelpaa vertailuun (satunnaisperkit), joten verrataan suoraan kaavaan."""
    c = _no_gear_commander()
    expected = (2.0 + c.dexterity * 0.025) * c.speed_multiplier
    assert abs(c.walk_speed - expected) <= 0.1, (
        f"Commander walk_speed {c.walk_speed} eroaa jaetusta kaavasta "
        f"{expected:.2f} - onko Commanderille tullut oma liikesääntö?")


def test_commander_beats_common_but_not_untouchable(manager):
    """Duel samalla AI:lla ja aseella: Commander-statit voittavat Common-
    rekryytin (sankari ei ole heikko), mutta Elite vie hänet pitkille
    (ei salamavoittoja = ei ylivoimaa)."""
    import random
    from tests.conftest import run_duel
    from units.human import Human
    from items.swords.scrap_sword import ScrapSword

    c_ref = _no_gear_commander()

    random.seed(1234)
    a = Human("CmdProxy", 300, 500, PLAYER_TEAM)
    a.base_attributes = dict(c_ref.base_attributes)
    a.base_attributes.pop("max_hp", None)
    a.equipment["main_hand"] = ScrapSword()
    a.calculate_final_stats()
    a.current_hp = a.max_hp
    b = Human("Opp", 700, 500, ENEMY_TEAM, quality="Common")
    b.equipment["main_hand"] = ScrapSword()
    b.calculate_final_stats()
    b.current_hp = b.max_hp
    r = run_duel(manager, a, b, max_frames=5400)
    assert r["ended"] and r["winner"] is a, "Commander-statit hävisivät Commonille"

    # Elite-mittelö kestää: nopea lyttäys = OP-hälytys
    from game_manager import GameManager
    m2 = GameManager()
    random.seed(1234)
    a2 = Human("CmdProxy", 300, 500, PLAYER_TEAM)
    a2.base_attributes = dict(c_ref.base_attributes)
    a2.base_attributes.pop("max_hp", None)
    a2.equipment["main_hand"] = ScrapSword()
    a2.calculate_final_stats()
    a2.current_hp = a2.max_hp
    b2 = Human("Elite", 700, 500, ENEMY_TEAM, quality="Elite")
    b2.equipment["main_hand"] = ScrapSword()
    b2.calculate_final_stats()
    b2.current_hp = b2.max_hp
    r2 = run_duel(m2, a2, b2, max_frames=5400)
    if r2["ended"] and r2["winner"] is a2:
        assert r2["frames"] >= 300, (
            f"Commander lyttäsi Eliten {r2['frames']} framessa - OP")


def test_vortex_blade_is_the_only_god_item(manager):
    """Tarinamiekka saa olla jumalesine - mutta commanderin statit ilman
    sitä eivät."""
    from units.commander import Commander
    c = Commander("Cmd", 0, 0)
    blade = c.equipment.get("main_hand")
    if blade is not None:
        assert blade.name == "Vortex Blade"
        assert blade.passive_bonuses.get("str", 0) >= 100  # tarkoituksella OP
    c2 = _no_gear_commander()
    assert c2.strength <= 15 and c2.dexterity <= 15
