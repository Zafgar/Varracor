# tests/test_forest_tutorial_regression.py
"""Regressio: metsäpolun tutoriaali kaatui heti ensimmäiseen updateen
('ForestRoadMenu' object has no attribute '_update_stage'), koska
monkeypatch asensi apumetodit vain pitkillä _tutorial_-nimillä mutta
kutsui lyhyitä. Tämä testi ajaa saman polun kuin pelaaja: uusi peli ->
metsäpolku -> update/draw -frameja -> stage etenee."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))


def test_forest_road_tutorial_updates_without_crash():
    import main  # noqa: F401  (asentaa runtime-laajennukset)
    from game_manager import GameManager
    from citys.mucford.forest_road_menu import ForestRoadMenu

    assert getattr(ForestRoadMenu, "_muckford_opening_installed", False), \
        "tutoriaali-integraation pitää olla asennettuna"
    # Kaikki patchatun updaten kutsumat metodit ovat olemassa
    for name in ("_update_stage", "_spawn_stage", "_stage_enemies_dead",
                 "_repeat_stage", "_advance_stage", "_draw_tutorial_panel"):
        assert hasattr(ForestRoadMenu, name), f"{name} puuttuu"

    m = GameManager()
    menu = ForestRoadMenu(m)
    menu.on_enter()
    surf = pygame.Surface((1920, 1080))

    # Sama kohta kuin pelaajan kaatuminen: update() heti sisääntulon jälkeen
    for _ in range(30):
        menu.update()
    menu.draw(surf)

    # Stage 0 -> 1 kun pelaaja kävelee portille (x >= 760)
    assert menu.tutorial_stage == 0
    menu.player.rect.centerx = 800
    for _ in range(10):
        menu.update()
    assert menu.tutorial_stage >= 1, "tutoriaali etenee portin yli"

    # Stage 1: viholliset spawnaavat kun pelaaja lähestyy
    from systems.muckford_forest_tutorial import _tutorial_stage_data
    data = _tutorial_stage_data(menu.tutorial_stage)
    menu.player.rect.centerx = int(data["spawn_x"]) - 100
    for _ in range(30):
        menu.update()
    assert menu.tutorial_enemies, "stage-viholliset spawnaavat"
    menu.draw(surf)
