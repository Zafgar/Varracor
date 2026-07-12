# tests/test_sponsor_menu.py
"""
Sponsorigalleria-valikon perussmoketesti: rakentuu, listaa kaikki sponsorit
ja allekirjoitusnappi vaihtaa SIGN/DROP tilan mukaan. (Logiikka testataan
erikseen test_sponsors.py:ssä.)
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from systems import sponsors


def _menu_and_manager():
    from citys.rattlebridge.sponsor_gallery_menu import SponsorGalleryMenu
    from game_manager import GameManager
    m = GameManager()
    m.gold = 500
    try:
        m.reputation = 60
    except Exception:
        m.npc_state.setdefault("global", {})["reputation"] = 60
    m.league_engine.tier = 2  # lore tier 1
    return SponsorGalleryMenu(m), m


def test_menu_lists_all_sponsors():
    menu, _ = _menu_and_manager()
    ids = {b.data_id for b in menu.list_buttons}
    assert ids == set(sponsors.SPONSORS)


def test_menu_draws_without_error():
    menu, _ = _menu_and_manager()
    menu.on_enter()
    surf = pygame.Surface((1920, 1080))
    menu.update()
    menu.draw(surf)  # ei saa heittää


def test_menu_action_signs_and_then_offers_drop():
    menu, m = _menu_and_manager()
    menu.on_enter()
    menu.selected_id = "ironspan_union"
    menu._act()  # SIGN
    assert sponsors.is_signed(m, "ironspan_union")
    # Uudelleen piirto päivittää napin DROP-tilaan
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)
    assert "DROP" in menu.btn_action.text.upper()
