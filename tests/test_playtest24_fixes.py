# tests/test_playtest24_fixes.py
"""Pelitestikierros 24 (jäljelle jääneet, yhä pätevät osat).

HUOM: pelitesti 26 rakensi viemäri-questlinjan uusiksi (vivut, kampi ja
Cistern Gate Crank -mekaniikat poistettiin). Ne testit ovat nyt
test_playtest26_fixes.py:ssä. Tänne jäävät yhä pätevät palat:
- Brute Rat (iso oikea rottayksikkö, pelitesti 25)
- Retkikunta warrensissa
- Griznak seuraa Warrens-kriisilinjaa
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))

from settings import PLAYER_TEAM, ENEMY_TEAM


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


# ----------------------------------------------------------------------
# Brute Rat (iso rotta) - pelitesti 25: oikea rottayksikkö
# ----------------------------------------------------------------------

def test_brute_rat_stats_and_sprite():
    from units.rat import BruteRat, GiantRat
    brute = BruteRat("Brute", 0, 0, ENEMY_TEAM)
    giant = GiantRat("G", 0, 0, ENEMY_TEAM)
    assert brute.max_hp > giant.max_hp * 3, "brute on selvästi tukevampi"
    assert brute.image is not None


def test_brute_rats_spawn_in_warrens():
    from citys.mucford.muckford_warrens import MuckfordWarrensMenu
    from units.rat import BruteRat
    m = _manager()
    menu = MuckfordWarrensMenu(m)
    menu.on_enter()
    brutes = [mo for mo in menu.monsters if isinstance(mo, BruteRat)]
    assert len(brutes) >= 2, "tunnelit kuhisevat isoja rottia"


# ----------------------------------------------------------------------
# Retkikunta warrensissa
# ----------------------------------------------------------------------

def test_expedition_party_joins_warrens():
    from citys.mucford.muckford_warrens import MuckfordWarrensMenu
    from units.human import Human
    from systems import expedition
    m = _manager()
    hero = m.player_character
    hero.unlocked_skills.add("warband_1")
    hero.calculate_final_stats()
    for i in range(2):
        u = Human(f"Apuri{i}", 0, 0, PLAYER_TEAM)
        m.my_team.add(u)
        expedition.toggle_member(m, u)
    menu = MuckfordWarrensMenu(m)
    menu.on_enter()
    assert m.expedition_field_active
    assert len(menu.expedition_units()) == 2, "apurit mukana tunneleissa"
    surf = pygame.Surface((1920, 1080))
    menu.update()
    menu.draw(surf)   # ei kaadu


# ----------------------------------------------------------------------
# Griznak seuraa Warrens-linjaa
# ----------------------------------------------------------------------

def test_griznak_reports_warrens_crisis():
    from systems import griznak_caravan
    from citys.mucford.muckford_warrens import warrens_state
    m = _manager()
    events = griznak_caravan.world_events(m)
    assert any("Warrens" in e or "sewer hatch" in e for e in events), \
        "Griznak ohjaa viemäriin heti alussa"
    warrens_state(m)["quest_stage"] = 4
    events = griznak_caravan.world_events(m)
    assert any("stage 4" in e for e in events), "Griznak seuraa etenemistä"
