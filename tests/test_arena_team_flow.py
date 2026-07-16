# tests/test_arena_team_flow.py
"""
Areena + rekrytointi + tiiminhallinta pelivirtana: prepare-valikon
kortticlickit osuvat oikeisiin hahmoihin, liigasta palataan liigaan,
rekrytointi aukeaa tiimitilasta ja palaa sinne, ja tiimitilassa voi
avata jäsenen skillipuun sekä erottaa jäsenen (tuplaklikkauksella).
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))


def _manager_with_team():
    import main  # noqa: F401
    from game_manager import GameManager
    m = GameManager()
    m.gold = 1000
    assert m.hire_recruit(0) and m.hire_recruit(1)
    return m


def test_prepare_card_clicks_hit_drawn_cards():
    """Klikkihitboxien PITÄÄ vastata piirrettyjä kortteja (320/90/100).

    FLAKE-KORJAUS: vastustajageneraatio on siemenetön - siemen tekee
    ajosta toistettavan (sama kuin league-flow'n kovennus)."""
    import random
    random.seed(88)
    m = _manager_with_team()
    m.mode = "League"
    m.match_mode = "3v3"
    m.battle_size = 3
    m.current_enemy_team = m.league_engine.get_next_opponent("3v3")
    from menus.prepare_menu import PrepareMenu
    pm = PrepareMenu(m)
    pm.selected_units = []  # tyhjennä autovalinta testiksi

    # Toisen rivin kortti (indeksi 1) piirtyy kohtaan y=150+1*100
    target = list(m.my_team)[0]
    click = (50 + 160, 150 + 1 * 100 + 45)
    pm.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                       pos=click, button=1))
    assert target in pm.selected_units, "klikkaus osui piirretyn kortin kohtaan"

    # Kolmas kortti (indeksi 2)
    target2 = list(m.my_team)[1]
    click2 = (50 + 160, 150 + 2 * 100 + 45)
    pm.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                       pos=click2, button=1))
    assert target2 in pm.selected_units


def test_prepare_back_returns_to_league_in_league_mode():
    m = _manager_with_team()
    m.mode = "League"
    m.match_mode = "1v1"
    m.current_enemy_team = m.league_engine.get_next_opponent("1v1")
    from menus.prepare_menu import PrepareMenu
    pm = PrepareMenu(m)
    pm.btn_back.update = lambda: True
    pm.btn_fight.update = lambda: False
    pm.update()
    assert pm.next_state == "league", "liigasta EI palata hubiin"


def test_recruit_menu_returns_where_opened():
    m = _manager_with_team()
    from menus.recruit_menu import RecruitMenu
    m.recruit_return_state = "barracks"
    rm = RecruitMenu(m)
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                            pos=rm.btn_back.rect.center, button=1)
    old = pygame.mouse.get_pos
    try:
        pygame.mouse.get_pos = lambda: rm.btn_back.rect.center
        rm.handle_event(ev)
    finally:
        pygame.mouse.get_pos = old
    assert rm.next_state == "barracks"


def test_barracks_recruit_button_and_skill_actions():
    m = _manager_with_team()
    from menus.barracks_menu import BarracksMenu
    b = BarracksMenu(m)
    surf = pygame.Surface((1920, 1080))
    b.update()
    b.draw(surf)  # rakentaa card_rects + action_rects

    # RECRUIT FIGHTERS -> recruit, paluu barracksiin
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                            pos=b.btn_recruits.rect.center, button=1)
    b.handle_event(ev)
    assert b.next_state == "recruit"
    assert m.recruit_return_state == "barracks"

    # Jäsenen SKILLS -> skill_tree valitulla hahmolla
    b.next_state = None
    member = list(m.my_team)[0]
    skills_rect = next(r for r, a, u in b.action_rects
                       if a == "skills" and u is member)
    b.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                      pos=skills_rect.center, button=1))
    assert b.next_state == "skill_tree"
    assert m.selected_hero is member
    assert m.skill_tree_return_state == "barracks"

    # Commanderin SKILLS -> commander_skills
    b.next_state = None
    hero_rect = next(r for r, a, u in b.action_rects
                     if a == "skills" and u is m.player_character)
    b.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                      pos=hero_rect.center, button=1))
    assert b.next_state == "commander_skills"


def test_barracks_dismiss_requires_double_click():
    m = _manager_with_team()
    from menus.barracks_menu import BarracksMenu
    b = BarracksMenu(m)
    surf = pygame.Surface((1920, 1080))
    b.update()
    b.draw(surf)
    member = list(m.my_team)[0]
    team_size = len(m.my_team.sprites())
    dis_rect = next(r for r, a, u in b.action_rects
                    if a == "dismiss" and u is member)
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=dis_rect.center,
                            button=1)
    b.handle_event(ev)
    assert len(m.my_team.sprites()) == team_size, "1. klikkaus vain varmistaa"
    assert b.pending_dismiss is member
    b.handle_event(ev)
    assert len(m.my_team.sprites()) == team_size - 1, "2. klikkaus erottaa"
    assert member not in m.my_team
    # Commanderille ei ole DISMISS-nappia
    assert not any(a == "dismiss" and u is m.player_character
                   for _r, a, u in b.action_rects)


def test_full_league_match_flow_with_recruits():
    """Rekrytoi -> valitse prepare-valikossa -> matsi käyntiin ja loppuun.

    FLAKE-KORJAUS: matsisimulaatio on siemenetön ja saattoi harvoin venyä
    yli framekaton (kaksi kitettäjää). Siemen tekee ajosta toistettavan ja
    katto on väljä - testin pointti on että FLOW valmistuu, ei tasapaino."""
    import random
    random.seed(77)
    m = _manager_with_team()
    from menus.tier0_team_intro import mark_tier0_team_intro_seen
    from menus.league_menu import LeagueMenu
    from menus.prepare_menu import PrepareMenu
    mark_tier0_team_intro_seen(m)
    lm = LeagueMenu(m)
    lm.selected_mode = "3v3"
    lm._start_next_match()
    assert lm.next_state == "prepare"
    pm = PrepareMenu(m)
    assert pm.team_limit == 3
    assert len(pm.selected_units) == 3, "koko elävä rosteri autovalittu"
    m.start_match(pm.selected_units, pm.team_limit)
    assert m.match_in_progress is True
    assert len(list(m.enemy_team)) == 3
    frames = 0
    while m.match_in_progress and frames < 40000:
        m.update_match()
        frames += 1
    assert m.match_over is True
    assert m.match_result in ("VICTORY", "DEFEAT")
