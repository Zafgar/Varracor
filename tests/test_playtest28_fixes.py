# tests/test_playtest28_fixes.py
"""Pelitestikierros 28: Griznakin ja Saggan (rohtoteltta) paikat kartalle.
Pelaajapalaute: "map ei tainnut näkyä griznak tai sitä potion teltta
tyyppiä, joten heidän paikat pitää näkyä kartalla".
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


def _muckford():
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(_manager())
    city.on_enter()
    return city


def test_griznak_and_sagga_on_city_map():
    city = _muckford()
    markers = city._city_map_markers()
    labels = [lbl for _, _, _, lbl in markers]
    assert any("Griznak" in lbl for lbl in labels), \
        "Griznakin vankkuri näkyy kartalla"
    assert any("Herb Tent" in lbl for lbl in labels), \
        "Saggan rohtoteltta näkyy kartalla"
    # Molemmilla on omat ikonityyppinsä (ei pelkkä väripiste)
    kinds = {lbl: kind for _, kind, _, lbl in markers}
    griz = next(k for lbl, k in kinds.items() if "Griznak" in lbl)
    herb = next(k for lbl, k in kinds.items() if "Herb Tent" in lbl)
    assert griz == "wagon"
    assert herb == "herbs"


def test_city_map_draws_without_crash():
    city = _muckford()
    surf = pygame.Surface((1920, 1080))
    city._draw_city_map(surf)  # kokoaa merkit + piirtää pelaajan/raidit


def test_wagon_and_herbs_icons_render():
    city = _muckford()
    surf = pygame.Surface((200, 200))
    # Uudet ikonityypit piirtyvät ilman poikkeusta
    city._draw_map_icon(surf, 100, 100, "wagon", (210, 175, 95))
    city._draw_map_icon(surf, 60, 60, "herbs", (150, 210, 130))


def test_rattlebridge_shows_griznak_marker():
    from citys.rattlebridge.rattlebridge_city_menu import RattlebridgeCityMenu
    city = RattlebridgeCityMenu(_manager())
    city.on_enter()
    surf = pygame.Surface((1920, 1080))
    # Paikalliskartta piirtyy Griznak-merkinnän kanssa kaatumatta
    city._draw_local_map(surf)
