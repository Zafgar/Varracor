# tests/test_school_shops.py
"""Pelitesti 35: koulukohtaiset loitsukaupat (necro-mallin pohjalta).
Näyttävät katalogin loitsut kouluittain, rikas selite, toimiva osto
equipment_bagiin. Bases (koulujen sijainnit) eivät vielä kytketty
navigointiin - testataan menu suoraan.
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


def _shops(m):
    from menus.school_spell_shop import (
        make_radiant_synod, make_verdant_covenant, make_ashen_catalog,
        make_prism_catalog)
    return {
        "holy": make_radiant_synod(m),
        "druidism": make_verdant_covenant(m),
        "necromancy": make_ashen_catalog(m),
        "pure": make_prism_catalog(m),
    }


def test_each_shop_lists_only_its_school():
    m = _manager()
    for school, shop in _shops(m).items():
        assert shop.spells, f"{school} tarjoaa loitsuja"
        for sp in shop.spells:
            # Holy-kauppa sisältää myös Sun Ray (school='holy')
            assert getattr(sp, "school", None) == school, \
                f"{sp.name} ei kuulu kouluun {school}"


def test_shops_draw_without_crash():
    m = _manager()
    surf = pygame.Surface((1920, 1080))
    for shop in _shops(m).values():
        shop.draw(surf)


def test_buy_adds_spell_to_equipment_bag():
    m = _manager()
    m.gold = 100000
    shop = _shops(m)["holy"]
    shop.selected = 0
    surf = pygame.Surface((1920, 1080))
    shop.draw(surf)  # täyttää _buy_rect
    target = shop.spells[0]
    n0 = len(m.equipment_bag)
    gold0 = m.gold
    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                               pos=shop._buy_rect.center)
    shop.handle_event(click)
    assert len(m.equipment_bag) == n0 + 1
    assert any(getattr(it, "name", None) == target.name
               for it in m.equipment_bag)
    assert m.gold == gold0 - int(target.cost)


def test_cannot_buy_twice_or_without_funds():
    m = _manager()
    shop = _shops(m)["pure"]
    shop.selected = 0
    sp = shop.spells[0]
    # Ei varaa
    m.gold = 0
    surf = pygame.Surface((1920, 1080))
    shop.draw(surf)
    shop.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                         pos=shop._buy_rect.center))
    assert not any(getattr(it, "name", None) == sp.name
                   for it in m.equipment_bag), "ei osteta ilman rahaa"
    # Varaa -> osto onnistuu, toinen osto estyy (jo omistettu)
    m.gold = 100000
    shop.draw(surf)
    shop.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                         pos=shop._buy_rect.center))
    owned_after = sum(1 for it in m.equipment_bag
                      if getattr(it, "name", None) == sp.name)
    assert owned_after == 1
    gold_after = m.gold
    shop.draw(surf)
    shop.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                         pos=shop._buy_rect.center))
    assert m.gold == gold_after, "jo omistettua ei osteta uudelleen"


def test_row_click_selects_spell():
    m = _manager()
    shop = _shops(m)["pure"]
    surf = pygame.Surface((1920, 1080))
    shop.draw(surf)
    assert len(shop._row_rects) >= 2
    rect, idx = shop._row_rects[1]
    shop.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                         pos=rect.center))
    assert shop.selected == idx


def test_bought_spell_is_castable():
    # Ostettu loitsu equipment_bagissa on oikea castattava olio
    m = _manager()
    m.gold = 100000
    shop = _shops(m)["pure"]
    shop.selected = 0
    surf = pygame.Surface((1920, 1080))
    shop.draw(surf)
    shop.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                         pos=shop._buy_rect.center))
    spell = m.equipment_bag[-1]
    assert hasattr(spell, "cast") and hasattr(spell, "describe")


# ----------------------------------------------------------------------
# Testipääsy: magic_school-valikko reitittää koulukauppoihin
# ----------------------------------------------------------------------

def test_magic_school_routes_to_catalog_shops(monkeypatch):
    import pygame as pg
    from menus.magic_school_menu import MagicSchoolMenu
    m = _manager()
    menu = MagicSchoolMenu(m)
    routes = {}
    for rect, school in menu.school_buttons:
        menu.next_state = None
        monkeypatch.setattr(pg.mouse, "get_pos", lambda r=rect: r.center)
        menu.handle_event(pg.event.Event(pg.MOUSEBUTTONDOWN,
                                         pos=rect.center, button=1))
        routes[school["id"]] = menu.next_state
    assert routes["pure"] == "school_pure"
    assert routes["holy"] == "school_holy"      # test-pääsy vaikka lukittu
    assert routes["necro"] == "school_necro"
    assert routes["druid"] == "school_druid"


def test_school_shop_factories_build_all_four():
    from menus.school_spell_shop import (
        make_prism_catalog, make_radiant_synod, make_ashen_catalog,
        make_verdant_covenant)
    m = _manager()
    for fac, school in ((make_prism_catalog, "pure"),
                        (make_radiant_synod, "holy"),
                        (make_ashen_catalog, "necromancy"),
                        (make_verdant_covenant, "druidism")):
        shop = fac(m)
        assert shop.spells, f"{school} tarjoaa loitsuja"
        assert shop.back_state == "magic_school"
