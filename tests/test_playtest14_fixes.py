# tests/test_playtest14_fixes.py
"""Pelitestikierros 14:
1) BUGI: UIButton laukesi DOWN+UP -> kaupan BUY osti KAHDESTI
   ("fishing rod antaa niitä kaksi")
2) Muckford Market: myynti/osto vaatii vahvistuksen ja määrän valinnan
3) torin bardi käyttää tavernan bardin spritejä (Elf) eikä ole neliö
4) kävelysuunnan pehmennys (villagerit eivät tärise)
5) quest journal -paneeli (J / silmänappi piilottaa)
6) sää: pilvinen päivä; taivaalla lintuja päivisin ja lepakoita öisin;
   kadulla nokkivia lintuja
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


# ----------------------------------------------------------------------
# 1) Nappi laukeaa vain kerran per klikkaus
# ----------------------------------------------------------------------

def test_uibutton_fires_only_on_mousedown():
    from ui_kit import UIButton
    btn = UIButton(100, 100, 200, 60, "BUY", None, (65, 135, 80))
    surf = pygame.Surface((1920, 1080))
    btn.draw(surf)
    pos = btn._last_draw_rect.center
    down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1)
    up = pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=1)
    assert btn.is_clicked(down) is True
    assert btn.is_clicked(up) is False, "UP ei saa laukaista uudestaan"


def test_district_shop_buy_gives_exactly_one(monkeypatch):
    m = _manager()
    m.gold = 1000
    m.pending_shop_id = "oddments"
    from menus.district_shop_menu import DistrictShopMenu
    shop = DistrictShopMenu(m)
    surf = pygame.Surface((1920, 1080))
    shop.draw(surf)
    entry = next(e for e in shop.shop["goods"] if e["kind"] == "item")
    shop.selected_entry = entry
    n0 = len(m.equipment_bag)
    pos = shop.btn_buy._last_draw_rect.center
    shop.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                         pos=pos, button=1))
    shop.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP,
                                         pos=pos, button=1))
    assert len(m.equipment_bag) == n0 + 1, \
        "yksi klikkaus = tasan yksi ostos (ei tuplavapaa)"


# ----------------------------------------------------------------------
# 2) Market: vahvistus + määrä
# ----------------------------------------------------------------------

def test_market_sell_requires_confirm_and_respects_qty():
    m = _manager()
    m.inventory["Egg"] = 5
    gold0 = m.gold = 100
    from menus.market_menu import MarketMenu
    menu = MarketMenu(m)
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)
    row, name = next((r, n) for r, n in menu.sell_rects if n == "Egg")
    menu.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                         pos=row.center, button=1))
    assert menu.pending == {"side": "sell", "key": "Egg", "qty": 1}
    assert m.gold == gold0, "pelkkä klikkaus ei vielä myy"
    assert m.inventory["Egg"] == 5
    # Määrä 3 ja vahvistus
    menu.pending["qty"] = 3
    menu._confirm_pending()
    assert m.inventory["Egg"] == 2
    assert m.gold == gold0 + 3 * 2, "Egg myyntihinta 2 SP/kpl"


def test_market_buy_quantity_and_funds_check():
    m = _manager()
    m.gold = 100
    from menus.market_menu import MarketMenu
    menu = MarketMenu(m)
    menu.pending = {"side": "buy", "key": "Apple", "qty": 5}
    menu._confirm_pending()
    assert m.inventory.get("Apple", 0) >= 5
    assert m.gold == 100 - 5 * 4, "5 omenaa a 4 SP"
    # Ei varaa -> kauppa ei toteudu
    m.gold = 3
    menu.pending = {"side": "buy", "key": "Apple", "qty": 1}
    apples = m.inventory.get("Apple", 0)
    menu._confirm_pending()
    assert m.gold == 3 and m.inventory.get("Apple", 0) == apples


def test_market_confirm_bar_buttons():
    m = _manager()
    m.inventory["Egg"] = 9
    from menus.market_menu import MarketMenu
    menu = MarketMenu(m)
    menu.pending = {"side": "sell", "key": "Egg", "qty": 1}
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)  # täyttää _confirm_rects
    plus = menu._confirm_rects["plus"].center
    menu.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                         pos=plus, button=1))
    assert menu.pending["qty"] == 2
    mx = menu._confirm_rects["max"].center
    menu.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                         pos=mx, button=1))
    assert menu.pending["qty"] == 9
    cancel = menu._confirm_rects["cancel"].center
    menu.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                         pos=cancel, button=1))
    assert menu.pending is None
    assert m.inventory["Egg"] == 9, "peruutus ei myy mitään"


# ----------------------------------------------------------------------
# 3) Torin bardi
# ----------------------------------------------------------------------

def test_market_bard_is_elf_with_real_sprite():
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(m)
    city.on_enter()
    city._update_ambient_event()  # alustaa event-kentät
    city._start_bard_performance(city.stage)
    bard = city._event_bard
    assert bard is not None
    # Ei tasavärinen neliö: proseduraalisessa bardissa on läpinäkyvyyttä
    corner = bard.image.get_at((0, 0))
    assert corner != (100, 100, 200, 255), "bardi ei ole sininen laatikko"
    city._end_bard_performance()


def test_bard_procedural_fallback_has_transparency():
    import main  # noqa: F401
    from units.bard import Bard
    from settings import GREEN
    b = Bard("Testi", "Human", 0, 0, GREEN)
    # Ilman sprite-tiedostoja piirretään hahmo läpinäkyvälle pinnalle
    assert b.image.get_at((0, 0)).a == 0 or b.image.get_at((0, 0))[:3] != \
        (100, 100, 200)


# ----------------------------------------------------------------------
# 4) Liikkeen pehmennys
# ----------------------------------------------------------------------

def test_move_towards_smooths_heading():
    import main  # noqa: F401
    from units.villager import Villager
    m = _manager()
    v = Villager("Kulkija", "Human", 500, 500)
    ai = v.ai_controller
    # Ensin itään
    ai._move_towards(100, 0, 100, [], [], manager=m)
    d1 = pygame.math.Vector2(ai._smooth_dir)
    assert d1.x > 0.9
    # Sitten jyrkästi etelään - suunta EI käänny kerralla (pehmennys)
    ai._move_towards(0, 100, 100, [], [], manager=m)
    d2 = ai._smooth_dir
    assert d2.x > 0.2, "vanha suunta painaa yhä (ei tärinäkäännöstä)"
    assert d2.y > 0.2, "uusi suunta alkaa vaikuttaa"


# ----------------------------------------------------------------------
# 5) Quest journal
# ----------------------------------------------------------------------

def test_quest_journal_draws_and_toggles():
    # Pelitesti 27: J avaa TÄYDEN journalin; silmänappi piilottaa
    # HUD-seurantapaneelin
    from quest_system import quest_manager
    m = _manager()
    q = quest_manager.get_quest("quest_krads_crate")
    q.status = "active"
    q.progress = 0
    assert m.show_quest_journal is True
    surf = pygame.Surface((1920, 1080))
    m._draw_quest_journal(surf)
    assert m._journal_toggle_rect is not None
    # J-näppäin avaa täyden journalin
    handled = m.handle_ui_event(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_j), "muckford_city")
    assert handled is True and m.show_full_journal is True
    # J sulkee sen taas (modaalinen)
    handled = m.handle_ui_event(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_j), "muckford_city")
    assert handled is True and m.show_full_journal is False
    # Silmänappi piilottaa HUD-trackerin
    m._draw_quest_journal(surf)
    eye = m._journal_toggle_rect
    handled = m.handle_ui_event(
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=eye.center,
                           button=1), "muckford_city")
    assert handled is True and m.show_quest_journal is False
    q.status = "available"


def test_quest_journal_key_ignored_in_battle():
    m = _manager()
    m.show_quest_journal = True
    res = m.handle_ui_event(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_j), "battle")
    assert m.show_quest_journal is True, "taistelussa J ei kuulu journalille"
    assert res is None


# ----------------------------------------------------------------------
# 6) Sää ja ambient-elämä
# ----------------------------------------------------------------------

def test_cloudy_weather_exists_and_draws():
    from world_clock import WorldClock, WEATHER_TYPES
    assert "cloudy" in WEATHER_TYPES
    clock = WorldClock()
    clock.weather = "cloudy"
    surf = pygame.Surface((1920, 1080))
    clock.draw_overlays(surf)  # pilvivarjot + himmennys kaatumatta
    assert clock._clouds, "pilvivarjot alustuvat"


def test_sky_life_birds_by_day_bats_by_night():
    from world_clock import WorldClock
    clock = WorldClock()
    surf = pygame.Surface((1920, 1080))
    clock.minutes = 12 * 60.0  # keskipäivä
    clock.weather = "clear"
    clock._next_flock = 0
    clock._draw_sky_life(surf)
    assert clock._sky_life and not clock._sky_life[0]["bat"], \
        "päivällä taivaalla lintuja"
    clock._sky_life = []
    clock.minutes = 23 * 60.0  # yö
    clock._next_flock = 0
    clock._draw_sky_life(surf)
    assert clock._sky_life and clock._sky_life[0]["bat"], \
        "yöllä lepakoita"


def test_ground_birds_spawn_and_flee_player():
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(m)
    city.on_enter()
    m.world_clock.minutes = 12 * 60.0
    m.world_clock.weather = "clear"
    city._update_ground_birds()      # alustaa
    city._next_ground_bird = 0
    city._update_ground_birds()
    assert city._ground_birds, "lintu laskeutuu kadulle"
    bird = city._ground_birds[0]
    # Laskeutuminen maahan
    for _ in range(200):
        city._update_ground_birds()
        if bird["state"] == "ground":
            break
    assert bird["state"] == "ground"
    # Pelaaja viereen -> lintu lähtee lentoon
    city.player.rect.center = (int(bird["x"]), int(bird["y"]))
    city._update_ground_birds()
    assert bird["state"] == "flying", "lähestyminen ajaa linnun siivilleen"
    surf = pygame.Surface((1920, 1080))
    city._draw_ground_birds(surf, (0, 0))
