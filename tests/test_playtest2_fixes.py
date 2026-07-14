# tests/test_playtest2_fixes.py
"""Pelitestikierros 2: maatilan portti, peltojen piirtojärjestys,
sprintin stamina, kartta, promptit ja quest-paneelin piilotus."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
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


def test_crop_plots_are_flat_and_drawn_under_units():
    m, menu = _city()
    plots = getattr(menu.arena, "crop_plots", [])
    assert plots, "palstat löytyvät"
    for p in plots:
        assert getattr(p, "is_flat", False), "palsta on lattiatasoa"
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)  # lattiapassi + y-sort ilman virheitä


def test_farm_gate_navigation_is_two_stage():
    m, menu = _city()
    from ai.villager_ai import VillagerAI
    arena = menu.arena
    farm = arena.farm_area
    gate = arena.farm_gate_pos
    # Portti on YLÄaidan aukon kohdalla (kaupungin puolella)
    assert abs(gate[1] - farm.y) < 5, "portti yläreunassa (kaupungin suunta)"
    assert gate[0] == farm.x + 640, "portti aukon keskellä (segmentti i==2)"

    npc = next(n for n in menu.npcs
               if isinstance(getattr(n, "ai_controller", None), VillagerAI))
    ai = npc.ai_controller
    target_inside = (farm.centerx, farm.centery)

    # Kaukana portista kaupungin puolella -> ensin oman puolen porttipiste
    npc.rect.center = (farm.x + 1500, farm.y - 400)
    step = ai._get_nav_target(target_inside, m)
    assert step[0] == gate[0], "kohdistetaan aukon x-linjalle"
    assert step[1] < farm.y, "pysytään omalla puolella kunnes aukon kohdalla"

    # Aukon kohdalla -> seuraava piste on aidan SISÄpuolella
    npc.rect.center = (gate[0], farm.y - 60)
    step = ai._get_nav_target(target_inside, m)
    assert step[1] > farm.y, "astutaan aukosta sisään"

    # Sisällä oleva menossa sisäkohteeseen -> suoraan kohteeseen
    npc.rect.center = (farm.centerx, farm.centery + 50)
    assert ai._get_nav_target(target_inside, m) == target_inside


def test_sprint_does_not_drain_stamina_standing_still(monkeypatch):
    m, menu = _city()
    player = menu.player
    player.current_stamina = player.max_stamina

    class _FKShift:
        def __getitem__(self, c):
            return c == pygame.K_LSHIFT

    # SHIFT pohjassa, hiiri pelaajan päällä (kuollut alue) -> ei liikettä
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: _FKShift())
    monkeypatch.setattr(pygame.mouse, "get_pressed", lambda: (False,) * 3)
    px = player.rect.centerx - menu.camera_x
    py = player.rect.centery - menu.camera_y
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (px, py))

    stam0 = player.current_stamina
    pos0 = player.rect.center
    for _ in range(60):
        menu.update()
    assert player.rect.center == pos0, "ei liikettä kuolleella alueella"
    assert player.current_stamina >= stam0 - 0.01, \
        "paikallaan seisominen ei kuluta staminaa shiftillä"

    # SHIFT + hiiri kauas -> juoksee hiiren suuntaan
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (px + 400, py))
    for _ in range(30):
        menu.update()
    assert player.rect.centerx > pos0[0], "shift+hiiri liikuttaa hahmoa"


def test_only_nearest_prompt_is_drawn():
    m, menu = _city()
    calls = []
    orig = m._draw_floating_prompt
    m._draw_floating_prompt = lambda *a, **k: calls.append(a)
    try:
        # Pelaaja tavernan oven ETEEN (lähellä myös NPC:itä/proppeja)
        th = menu.tavern_house
        menu.player.rect.centerx = th.rect.centerx
        menu.player.rect.bottom = th.rect.bottom + 40
        # Tuo NPC viereen, jotta ehdokkaita on varmasti useita
        if menu.npcs:
            menu.npcs[0].rect.center = menu.player.rect.center
        surf = pygame.Surface((1920, 1080))
        menu.draw(surf)
    finally:
        m._draw_floating_prompt = orig
    assert len(calls) <= 1, f"vain lähin prompti piirretään (oli {len(calls)})"
    assert len(calls) == 1, "yksi prompti löytyi"


def test_tracker_hidden_when_map_open():
    m, menu = _city()
    calls = []
    orig = menu._draw_muckford_opening_tracker
    menu._draw_muckford_opening_tracker = lambda s: calls.append(1)
    try:
        surf = pygame.Surface((1920, 1080))
        menu.show_map = False
        menu.draw(surf)
        drawn_normal = len(calls)
        menu.show_map = True
        menu.draw(surf)
        drawn_with_map = len(calls) - drawn_normal
    finally:
        menu._draw_muckford_opening_tracker = orig
        menu.show_map = False
    assert drawn_normal == 1, "paneeli näkyy normaalisti"
    assert drawn_with_map == 0, "paneeli piilossa kartan aikana"


def test_city_map_draws_with_icons():
    m, menu = _city()
    menu.show_map = True
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)
    menu.show_map = False
