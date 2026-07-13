# tests/test_rattlebridge_ambient.py
"""
Rattlebridgen ambient-elämä: Bridgeguard-partiot kiertävät reittejään,
rahtikärryt kulkevat kansia, ja uudet nimetyt NPC:t (Yorik Sparkspanner,
Corwin Hale, Brasslight) ovat paikoillaan dialogeineen.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))


def _menu():
    from game_manager import GameManager
    from citys.rattlebridge.rattlebridge_city_menu import RattlebridgeCityMenu
    m = GameManager()
    menu = RattlebridgeCityMenu(m)
    menu.on_enter()
    return menu


def test_new_named_npcs_have_rich_dialogue():
    from citys.rattlebridge.rattlebridge_data import NAMED_NPCS
    for npc_id, race in (("yorik_sparkspanner", "Gnome"),
                         ("corwin_hale", "Human"),
                         ("brasslight_tout", "Goblin")):
        data = NAMED_NPCS[npc_id]
        assert data["race"] == race
        assert len(data["dialogue"]) >= 6, f"{npc_id} dialogue too short"


def test_patrols_walk_their_routes():
    menu = _menu()
    guards = [n for n in menu.npcs
              if getattr(n, "rattle_role", "") == "Bridgeguard Patrol"]
    assert len(guards) == 4
    start = [g.rect.center for g in guards]
    for _ in range(300):
        menu._update_population()
    moved = sum(1 for g, p in zip(guards, start) if g.rect.center != p)
    assert moved == len(guards), "partioiden pitää liikkua reittejään"


def test_freight_carts_move_and_wrap():
    menu = _menu()
    assert len(menu.carts) >= 3
    cart = menu.carts[0]
    assert cart.direction > 0
    cart.rect.left = cart.world_width + 90  # wrap-rajan yli
    cart.update()
    assert cart.rect.right <= 0, "kärryn pitää kiertää takaisin alkuun"
    # Piirto ei kaadu kameran ulkopuolella eikä sisällä
    surf = pygame.Surface((1920, 1080))
    cart.draw(surf, (0, 0))
    cart.draw(surf, (99999, 0))


def test_city_draw_includes_ambient_life():
    menu = _menu()
    surf = pygame.Surface((1920, 1080))
    for _ in range(30):
        menu.update()
    menu.draw(surf)  # renderables-lajittelu kärryineen ei saa heittää
