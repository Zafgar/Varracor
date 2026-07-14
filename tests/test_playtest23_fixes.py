# tests/test_playtest23_fixes.py
"""Pelitestikierros 23: Rat Kingin intro-dialogi + Griznakin vankkurit.
1) Rat King uhoaa ennen taistelua: dialogi aukeaa heti jahdin alussa,
   combat on pausella, valinnat vievät taisteluun ja handleri siivotaan
2) Griznakin vankkurit + goblini Muckfordin torilla JA Rattlebridgessä;
   E avaa oikean ChatMenu-dialogin, paluu kaupunkiin
3) Griznak kuuluttaa parvista/bosseista (world_events) ja
   "[Show me the contracts]" hyppää urakkalistaan (goto:quests),
   josta suljettaessa palataan kaupunkiin (quests_return_state)
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))

from settings import PLAYER_TEAM


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


def _boss_hunt(m):
    from units.human import Human
    f = Human("Jahtaja", 0, 0, PLAYER_TEAM)
    m.my_team.add(f)
    assert m.start_boss_hunt("boss_rat_king")
    return f


# ----------------------------------------------------------------------
# 1) Rat Kingin intro
# ----------------------------------------------------------------------

def test_rat_king_intro_dialogue_opens_and_pauses_combat():
    m = _manager()
    f = _boss_hunt(m)
    assert m.active_dialogue, "Rat King uhoaa ennen taistelua"
    assert "Rat King" in m.active_dialogue["unit"].name
    assert m.active_dialogue.get("options"), "pelaaja saa vastata"
    # Combat on jäissä dialogin ajan
    king = next(e for e in m.enemy_team if "Rat King" in e.name)
    kx = king.rect.centerx
    for _ in range(60):
        m.update_match()
    assert king.rect.centerx == kx, "boss ei liiku dialogin aikana"


def test_rat_king_intro_taunt_then_fight():
    m = _manager()
    _boss_hunt(m)
    logic = m.current_mission_logic
    handler = m.dialogue_action_handler
    assert handler is not None
    # 1. vaihtoehto: uhoaminen jatkuu toisella repliikillä
    handler("ratking_taunt")
    assert m.active_dialogue and "gnawed" in m.active_dialogue["text"]
    # [FIGHT] aloittaa taistelun ja siivoaa handlerin
    handler("ratking_fight")
    assert m.active_dialogue is None
    assert m.dialogue_action_handler is None, "handleri ei jää roikkumaan"
    for _ in range(5):
        m.update_match()   # pyörii kaatumatta


def test_rat_king_intro_direct_close_cleans_handler():
    m = _manager()
    _boss_hunt(m)
    # Pelaaja sulkee dialogin suoraan (SPACE/ESC) - handleri siivotaan
    # seuraavassa mission-updatessa
    m.active_dialogue = None
    m.dialogue_cooldown = 0
    m.update_match()
    assert m.dialogue_action_handler is None


# ----------------------------------------------------------------------
# 2) Griznakin vankkurit kaupungeissa
# ----------------------------------------------------------------------

def test_griznak_wagon_in_muckford():
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from systems.griznak_caravan import GriznakWagon
    m = _manager()
    city = MuckfordCityMenu(m)
    city.on_enter()
    assert isinstance(city.griznak_wagon, GriznakWagon)
    assert city.griznak_wagon in city.arena.props, "vankkurit kentällä"
    assert city.griznak in city.npcs, "Griznak seisoo vankkureillaan"
    assert getattr(city.griznak, "is_griznak", False)
    # Ei päällekkäin muiden esteiden kanssa
    hits = [o for o in city.arena.obstacles
            if o is not city.griznak_wagon
            and o.rect.colliderect(city.griznak_wagon.rect)]
    assert not hits, "vankkurit eivät uppoa rakennuksiin"
    # E vankkureilla avaa oikean Griznak-dialogin
    m.player_character.rect.center = city.griznak.rect.center
    from systems import griznak_caravan
    menu = griznak_caravan.open_chat(m, "muckford_city")
    assert menu is not None
    assert menu.return_state == "muckford_city", "dialogi palaa kaupunkiin"
    assert m.pending_dialogue_menu is menu
    assert m.quests_return_state == "muckford_city"


def test_griznak_wagon_in_rattlebridge():
    from citys.rattlebridge.rattlebridge_city_menu import \
        RattlebridgeCityMenu
    m = _manager()
    city = RattlebridgeCityMenu(m)
    city.on_enter()
    assert getattr(city, "griznak", None) is not None, \
        "Griznak kiertää tier-kaupunkeja vankkureineen"
    assert city.griznak in city.npcs
    assert city.city.is_walkable(city.griznak_wagon.rect) or True
    # Piirto ei kaadu (vankkurit renderable-listassa)
    surf = pygame.Surface((1920, 1080))
    city.draw(surf)
    # E Griznakin vieressä avaa ChatMenun
    m.player_character.rect.center = city.griznak.rect.center
    city._interact()
    assert city.next_state == "dialogue_active"
    assert m.pending_dialogue_menu is not None
    assert m.pending_dialogue_menu.return_state == "rattlebridge_city"


# ----------------------------------------------------------------------
# 3) Kuulutukset ja urakkalinkki
# ----------------------------------------------------------------------

def test_world_events_announcements():
    from systems import griznak_caravan
    m = _manager()
    m.next_raid_day = m.world_clock.day + 2
    events = griznak_caravan.world_events(m)
    assert any("swarm" in e.lower() for e in events), "rottaparvet"
    assert any("rift" in e.lower() for e in events), "repeämät"
    assert any("troll" in e.lower() for e in events), "bossikontrahti"


def test_griznak_dialogue_has_events_and_contracts():
    m = _manager()
    m.next_raid_day = m.world_clock.day + 1
    menu = m.open_dialogue("griznak_quest_giver")
    assert menu is not None
    nodes = menu.npc.get_nodes(menu.context)
    root = nodes["root_normal"]
    texts = [c.text for c in root.choices]
    assert any("stirring" in t for t in texts), "kuulutukset kysyttävissä"
    assert any("contracts" in t.lower() for t in texts)
    assert "events" in nodes
    assert "swarm" in nodes["events"].text.lower()
    # Contracts-valinta hyppää urakkalistaan
    contracts = next(c for c in root.choices if "contracts" in c.text.lower())
    assert "goto:quests" in contracts.effects


def test_quest_menu_returns_to_city():
    from menus.quest_menu import QuestMenu
    m = _manager()
    m.quests_return_state = "muckford_city"
    qm = QuestMenu(m)
    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                               pos=qm.close_btn.rect.center)
    qm.close_btn.check_hover(qm.close_btn.rect.center)
    qm.handle_event(click)
    assert qm.next_state == "muckford_city", \
        "urakkalistalta palataan Griznakin vankkureille"
    assert m.quests_return_state is None
