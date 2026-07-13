# tests/test_city_prospects.py
"""Rekryprospektit kaupungilla: Sunk Caskin vapaita taistelijoita voi
kohdata Muckfordin kokoontumispaikoilla, E avaa palkkausdialogin ja
palkattu prospekti poistuu kadulta. Lisäksi uudet juttelunaiheet."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))


def _city():
    import main  # noqa: F401
    from game_manager import GameManager
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    m = GameManager()
    m.gold = 5000
    menu = MuckfordCityMenu(m)
    menu.on_enter()
    return m, menu


def test_new_dialogue_topics_exist():
    from ai.life_ai import DIALOGUE_TOPICS
    for topic in ("market", "fishing", "recruits"):
        assert topic in DIALOGUE_TOPICS
        assert len(DIALOGUE_TOPICS[topic]) >= 6


def test_jetty_is_gathering_spot():
    _m, menu = _city()
    tips = getattr(menu.arena, "fishing_spots", [])
    assert tips, "kaupungissa on kalastuspaikka"
    tip = tips[0]
    near = [s for s in menu.gathering_spots
            if abs(s[0] - tip[0]) <= 90 and abs(s[1] - tip[1]) <= 90]
    assert near, "laiturin nokka on kokoontumispaikka"


def test_prospects_spawn_from_recruit_pool():
    m, menu = _city()
    assert 1 <= len(menu.prospects) <= 2
    for p in menu.prospects:
        assert p in m.recruit_options
        assert getattr(p, "is_prospect", False)
        assert p in menu.npcs
        assert p.ai_controller is None, "taisteluäly parkissa kadulla"
        assert hasattr(p, "_combat_ai_backup")


def test_prospect_interaction_opens_recruit_dialogue():
    m, menu = _city()
    prospect = menu.prospects[0]
    # Siirrä kohtaaminen tyhjään kohtaan: satunnainen spawni voi osua
    # esim. torikojun eteen, jolloin E avaisi kaupan ennen NPC:tä
    free = (menu.arena.width // 2, menu.arena.height - 200)
    prospect.rect.center = free
    menu.player.rect.center = free
    ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)
    menu.handle_event(ev)
    assert menu.next_state == "dialogue_active"
    dlg = m.pending_dialogue_menu
    assert dlg is not None
    assert dlg.npc.unit is prospect
    assert dlg.return_state == "muckford_city"


def test_hired_prospect_leaves_the_street():
    m, menu = _city()
    prospect = menu.prospects[0]
    cost = prospect.cost
    assert m.hire_unit_by_reference(prospect, cost)
    menu.update()
    assert prospect not in menu.npcs
    assert prospect not in menu.prospects
    assert prospect in m.my_team
    assert prospect.ai_controller is not None, "taisteluäly palautui"
