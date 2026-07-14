# tests/test_playtest6_fixes.py
"""Pelitestikierros 6: torin iltashow (aikataulutettu, oikea bardi, yleisö,
oluttarjoilu), Bramin kuulutukset reaktioineen, ilmoitustaulun paikka ja
district-kauppojen osta/myy-layout."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))


def _city():
    import main  # noqa: F401
    from game_manager import GameManager
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    m = GameManager()
    menu = MuckfordCityMenu(m)
    menu.on_enter()
    return m, menu


# ----------------------------------------------------------------------
# Iltashow
# ----------------------------------------------------------------------

def test_bard_show_starts_in_evening_not_midday():
    from units.bard import Bard
    m, menu = _city()
    m.world_clock.minutes = 12 * 60.0
    menu._update_ambient_event()          # alustaa aikataulun
    for _ in range(30):
        menu._update_ambient_event()
    assert menu._event_state == "idle", "keskipäivällä ei showta"

    # Ilta: show alkaa aikataulun tunnilla
    m.world_clock.minutes = (menu._show_hour + 0.5) * 60.0
    menu._update_ambient_event()
    assert menu._event_state == "bard"
    assert isinstance(menu._event_bard, Bard), "oikea bardihahmo lavalla"
    assert menu._event_bard.name == "Wren Reedpipe"
    assert menu._event_bard in menu.npcs
    assert menu._event_timer > 3000, "esitys kestää pitkään (~2 pelituntia)"
    assert menu._event_watchers, "yleisöä kerääntyy"
    assert all(n.sim_state == "WATCHING" for n in menu._event_watchers)
    assert menu._event_server is not None, "Petra tarjoilee olutta"
    assert menu._event_server in menu.npcs

    # Lopetus siivoaa kaiken ja siirtää seuraavan showhun huomiseen
    day = m.world_clock.day
    menu._end_bard_performance()
    assert menu._event_bard is None
    assert menu._event_server is None
    assert not menu._event_watchers
    assert menu._next_show_day == day + 1, "vain yksi show päivässä"


def test_watchers_walk_to_stage_and_stay():
    m, menu = _city()
    menu._update_ambient_event()
    menu._start_bard_performance(menu.stage)
    watchers = list(menu._event_watchers)
    assert watchers
    for _ in range(600):
        menu.update()
        if menu._event_state != "bard":
            break
    import math
    near = sum(1 for n in watchers
               if math.hypot(n._watch_spot[0] - n.rect.centerx,
                             n._watch_spot[1] - n.rect.centery) < 80)
    assert near >= len(watchers) // 2, "yleisö kävelee lavan eteen"


# ----------------------------------------------------------------------
# Bramin kuulutus
# ----------------------------------------------------------------------

def test_bram_announcement_flow():
    m, menu = _city()
    menu._update_ambient_event()
    assert menu.bram is not None
    m.world_clock.minutes = 11 * 60.0
    menu._next_news_day = m.world_clock.day
    menu._news_hour = 11
    menu._update_ambient_event()
    assert menu._event_state == "announce"
    assert menu._event_news is not None
    assert "Bram" in menu._event_banner_text
    assert menu._event_watchers, "väki kokoontuu kuuntelemaan"
    # Bram on lavalla
    stage = menu.stage
    assert abs(menu.bram.rect.centerx - stage.rect.centerx) < 10
    return_pos = menu._bram_return_pos
    # Reaktio ei kaada
    menu._crowd_reaction(menu._event_news[1])
    menu._end_announcement()
    assert menu.bram.rect.center == return_pos, "Bram palaa paikalleen"
    assert menu._next_news_day > m.world_clock.day, "kuulutus parin päivän välein"


# ----------------------------------------------------------------------
# Ilmoitustaulu ja kaupat
# ----------------------------------------------------------------------

def test_notice_board_clear_of_stalls():
    import main  # noqa: F401
    from assets.tiles.arena import Arena
    from assets.tiles.muckford_objects import NoticeBoard, MuckfordStall
    a = Arena()
    board = next(p for p in a.props if isinstance(p, NoticeBoard))
    b_rect = pygame.Rect(board.image_pos[0], board.image_pos[1],
                         board.image.get_width(), board.image.get_height())
    for stall in (p for p in a.props if isinstance(p, MuckfordStall)):
        s_rect = pygame.Rect(stall.image_pos[0], stall.image_pos[1],
                             stall.image.get_width(),
                             stall.image.get_height())
        assert not b_rect.colliderect(s_rect), "taulu ei ole kojun edessä"


def test_district_shop_sell_panel():
    import main  # noqa: F401
    from game_manager import GameManager
    from citys.mucford.market_data import MARKET_SHOPS
    for shop in MARKET_SHOPS.values():
        assert shop.get("buys"), f"{shop['name']} ei osta mitään"

    m = GameManager()
    m.gold = 100
    m.inventory.update({"Bitterleaf": 5})
    m.pending_shop_id = "bittersip"
    from menus.district_shop_menu import DistrictShopMenu
    menu = DistrictShopMenu(m)
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)
    assert menu.sell_rects, "myyntirivit piirtyvät"
    rect, name = menu.sell_rects[0]
    assert name == "Bitterleaf"
    # Pelitesti 14: 1. klikkaus VALITSEE (ei myy), 2. klikkaus myy yhden
    g0 = m.gold
    menu.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, pos=rect.center, button=1))
    assert m.gold == g0, "eka klikkaus vain valitsee rivin"
    assert menu.selected_sell == "Bitterleaf"
    menu.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, pos=rect.center, button=1))
    assert m.gold > g0
    assert m.inventory["Bitterleaf"] == 4


def test_no_buy_sell_money_loop():
    """Takaisinostohinta ei saa ylittää liikkeen omaa myyntihintaa."""
    import main  # noqa: F401
    from game_manager import GameManager
    m = GameManager()
    m.pending_shop_id = "bittersip"
    from menus.district_shop_menu import DistrictShopMenu
    menu = DistrictShopMenu(m)
    for entry in menu.shop["goods"]:
        if entry["name"] in menu.shop.get("buys", ()):
            sell = menu._sell_price(entry["name"])
            buy = menu._final_price(entry)
            assert sell < buy, (f"{entry['name']}: myynti {sell} >= "
                                f"osto {buy} -> rahasilmukka")
