# tests/test_command_flow.py
"""
Toimintavalikko pelin sisällä: C-näppäin avaa Commander-valikon kaupungista
ja SIELTÄ PALATAAN KAUPUNKIIN (ei vanhaan hubiin). Liigamatsin jälkeen
palataan liigavalikkoon, ja liigavalikosta sinne mistä tultiin.
Kauppasivun hover näyttää varusteen infokortin.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))


def _manager():
    import main  # noqa: F401  (rekisteröi integraatiot)
    from game_manager import GameManager
    return GameManager()


def _click(button):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                              pos=button.rect.center, button=1)


def test_c_key_opens_commander_menu_from_muckford():
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(m)
    city.on_enter()
    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c))
    assert city.next_state == "manager_menu"
    assert m.manager_return_state == "muckford_city"


def test_c_key_opens_commander_menu_from_rattlebridge():
    m = _manager()
    from citys.rattlebridge.rattlebridge_city_menu import RattlebridgeCityMenu
    rb = RattlebridgeCityMenu(m)
    rb.on_enter()
    rb.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c))
    assert rb.next_state == "manager_menu"
    assert m.manager_return_state == "rattlebridge_city"


def test_manager_menu_back_returns_to_live_map():
    m = _manager()
    from menus.manager_menu import ManagerMenu
    m.manager_return_state = "muckford_city"
    menu = ManagerMenu(m)
    old_get_pos = pygame.mouse.get_pos
    try:
        pygame.mouse.get_pos = lambda: menu.btn_back.rect.center
        menu.handle_event(_click(menu.btn_back))
    finally:
        pygame.mouse.get_pos = old_get_pos
    assert menu.next_state == "muckford_city"


def test_manager_menu_team_button_roundtrip():
    """TEAM avaa tiimitilan ja tiimitilasta palataan Commander-valikkoon;
    kaupungin ovesta tullessa palataan kaupunkiin."""
    m = _manager()
    from menus.manager_menu import ManagerMenu
    from menus.barracks_menu import BarracksMenu
    menu = ManagerMenu(m)
    old_get_pos = pygame.mouse.get_pos
    try:
        pygame.mouse.get_pos = lambda: menu.btn_team.rect.center
        menu.handle_event(_click(menu.btn_team))
    finally:
        pygame.mouse.get_pos = old_get_pos
    assert menu.next_state == "barracks"
    assert m.barracks_return_state == "manager_menu"

    b = BarracksMenu(m)
    b.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert b.next_state == "manager_menu"

    # Kaupungin rakennuksesta tullessa takaisin kaupunkiin
    m.barracks_return_state = "muckford_city"
    b2 = BarracksMenu(m)
    b2.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert b2.next_state == "muckford_city"


def test_league_match_returns_to_league_not_hub():
    m = _manager()
    from menus.post_battle_menu import LootScreenMenu
    m.gold = 500
    m.mode = "League"
    m.match_mode = "1v1"
    m.match_result = "VICTORY"
    m.is_game_over = False
    ls = LootScreenMenu(m)
    ls.handle_event(_click(ls.btn_claim))
    assert ls.next_state == "league"

    # Muut moodit säilyttävät vanhan reitin
    m.mode = "Arena"
    ls2 = LootScreenMenu(m)
    ls2.handle_event(_click(ls2.btn_claim))
    assert ls2.next_state == "hub"


def test_league_menu_back_honors_entry_point():
    m = _manager()
    from menus.league_menu import LeagueMenu
    from menus.tier0_team_intro import mark_tier0_team_intro_seen
    mark_tier0_team_intro_seen(m)
    m.league_return_state = "muckford_city"
    menu = LeagueMenu(m)
    menu.handle_event(_click(menu.btn_back))
    assert menu.next_state == "muckford_city"


def test_shanty_yard_gate_sets_league_return():
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(m)
    city.on_enter()
    gate = city.arena_gate
    assert gate is not None
    city.player.rect.centerx = gate.rect.centerx
    city.player.rect.bottom = gate.rect.bottom + 20
    city.next_state = None
    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    assert city.next_state == "league"
    assert m.league_return_state == "muckford_city"


def test_shop_hover_previews_built():
    """Jokaiselle varusteelle on esikatselukappale infokorttia varten."""
    m = _manager()
    m.pending_shop_id = "mudguard_armory"
    from menus.district_shop_menu import DistrictShopMenu
    menu = DistrictShopMenu(m)
    items = [e for e in menu.shop["goods"] if e["kind"] == "item"]
    assert items, "panssarikaupassa on varusteita"
    for entry in items:
        assert menu._previews.get(entry["name"]) is not None
    surf = pygame.Surface((1920, 1080))
    menu.update()
    menu.draw(surf)  # hover-polku ei kaada piirtoa
