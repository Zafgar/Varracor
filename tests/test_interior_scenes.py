# tests/test_interior_scenes.py
"""
Koodilla maalatut sisätilat: The Span -tupa ja Bridgewardin kappelisali.
Staattinen pohja maalataan kerran, animaatiokerrokset ovat halpoja, ja
valikot toimivat kohtausten päällä.
"""
import os
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))


def test_scenes_build_and_are_cached():
    from citys.rattlebridge.interior_scenes import get_scene
    a = get_scene("span")
    b = get_scene("span")
    assert a is b, "kohtaus maalataan vain kerran per prosessi"
    assert get_scene("chapel") is get_scene("chapel")


def test_scene_draw_is_fast_enough_for_60fps():
    from citys.rattlebridge.interior_scenes import get_scene
    surf = pygame.Surface((1920, 1080))
    for name in ("span", "chapel"):
        scene = get_scene(name)
        t0 = time.perf_counter()
        for i in range(60):
            scene.draw(surf, tick=i * 16)
        avg_ms = (time.perf_counter() - t0) / 60 * 1000
        assert avg_ms < 8.0, f"{name} liian hidas: {avg_ms:.2f} ms/frame"


def test_span_menu_uses_scene_and_modals_toggle():
    from game_manager import GameManager
    from citys.rattlebridge.the_span_menu import TheSpanMenu
    m = GameManager()
    menu = TheSpanMenu(m)
    menu.on_enter()
    assert hasattr(menu, "scene")
    surf = pygame.Surface((1920, 1080))
    menu.update()
    menu.draw(surf)
    menu.show_teams = True
    menu.draw(surf)   # Arena talk -modaali piirtyy
    menu.show_teams = False
    menu.show_rumors = True
    menu.draw(surf)
    # ESC sulkee modaalin, ei poistu
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert menu.show_rumors is False
    assert menu.next_state is None


def test_hospital_menu_uses_scene_and_treats():
    from game_manager import GameManager
    from citys.rattlebridge.bridgeward_hospital_menu import BridgewardHospitalMenu
    m = GameManager()
    m.gold = 500
    menu = BridgewardHospitalMenu(m)
    menu.on_enter()
    assert hasattr(menu, "scene")
    surf = pygame.Surface((1920, 1080))
    menu.update()
    menu.draw(surf)
    hero = m.player_character
    hero.current_hp = 1
    menu.selected = "full"
    menu._treat()
    assert hero.current_hp == hero.max_hp
    assert m.gold == 500 - menu.SERVICES["full"]["cost"]
