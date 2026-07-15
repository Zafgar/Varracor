# tests/test_playtest29_fixes.py
"""Pelitestikierros 29: syöte- ja sijaintibugit.
1) Griznakin vankkuri ei saa piirtyä talon (rakennuspropin) päälle
2) Save-nimeä kirjoittaessa 'i' (tai muu pikanäppäin) ei avaa inventorya
3) Save-nimeä kirjoittaessa backspace pyyhkii puskurista
4) Kun pause-valikko on auki, hiiriklikkaus EI valu pelimaailman
   combat-käsittelyyn (hahmo ei lyö LMB:llä)
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


def _muckford(m):
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(m)
    city.on_enter()
    return city


# ----------------------------------------------------------------------
# 1) Griznakin vankkuri ei rakennuksen päällä
# ----------------------------------------------------------------------

def test_griznak_wagon_not_on_top_of_a_building():
    from systems.griznak_caravan import GriznakWagon
    city = _muckford(_manager())
    wagon = city.griznak_wagon
    assert wagon is not None
    for prop in city.arena.props:
        if prop is wagon or isinstance(prop, GriznakWagon):
            continue
        if getattr(prop, "is_structure", False):
            assert not prop.rect.colliderect(wagon.rect), \
                f"vankkuri piirtyy {type(prop).__name__}:n päälle"


# ----------------------------------------------------------------------
# 2) + 3) Nimen kirjoitus kaappaa näppäimet (ei inventorya, backspace toimii)
# ----------------------------------------------------------------------

def test_typing_save_name_does_not_trigger_global_hotkeys():
    m = _manager()
    m.paused = True
    m.pause_panel_mode = "save"
    m.pause_name_slot = 1
    m.pause_name_buffer = "Te"
    inv_before = m.show_inventory
    # 'i' pitää mennä nimeen, EI avata inventorya
    res = m.handle_ui_event(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_i, unicode="i"),
        "muckford_city")
    assert res is True
    assert m.show_inventory == inv_before, "inventory ei saa aueta kirjoittaessa"
    assert m.pause_name_buffer == "Tei"


def test_backspace_erases_save_name_buffer():
    m = _manager()
    m.paused = True
    m.pause_panel_mode = "save"
    m.pause_name_slot = 1
    m.pause_name_buffer = "Test"
    m.handle_ui_event(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE),
        "muckford_city")
    assert m.pause_name_buffer == "Tes"


# ----------------------------------------------------------------------
# 4) Pause: hiiriklikkaus ei valu combattiin
# ----------------------------------------------------------------------

def test_paused_consumes_mouse_clicks():
    m = _manager()
    m.paused = True
    for button in (1, 3):
        down = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                  pos=(700, 430), button=button)
        up = pygame.event.Event(pygame.MOUSEBUTTONUP,
                                pos=(700, 430), button=button)
        assert m.handle_ui_event(down, "muckford_city") is True
        assert m.handle_ui_event(up, "muckford_city") is True


def test_unpaused_does_not_swallow_events():
    m = _manager()
    m.paused = False
    # Kun ei olla paussissa eikä dialogissa, tuntematon näppäin valuu läpi
    res = m.handle_ui_event(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F13),
        "muckford_city")
    assert res in (None, False)
