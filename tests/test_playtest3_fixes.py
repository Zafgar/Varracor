# tests/test_playtest3_fixes.py
"""Pelitestikierros 3: nimetyt save-slotit + pause-paneeli, raidin AI
(kyläläiset pelkäävät, vartijat puolustavat), bardi näkyy lavalla,
portin/barracksin uudet paikat."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))


@pytest.fixture
def tmp_saves(tmp_path, monkeypatch):
    import save_manager
    monkeypatch.setattr(save_manager, "SAVE_DIR", str(tmp_path))
    monkeypatch.setattr(save_manager, "SAVE_FILE",
                        str(tmp_path / "savegame.json"))
    return save_manager


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


def test_named_save_slots_roundtrip(tmp_saves):
    m = _manager()
    m.gold = 777
    assert tmp_saves.save_to_slot(m, 2, "Ennen finaalia")
    rows = {r["slot"]: r for r in tmp_saves.list_slots()}
    assert rows[2]["exists"]
    assert rows[2]["name"] == "Ennen finaalia"
    assert "Thaw" in rows[2]["game_date"], "pelin päiväys mukana"
    assert not rows[3]["exists"]

    m2 = _manager()
    assert tmp_saves.load_from_slot(m2, 2)
    assert m2.gold == 777


def test_pause_panel_save_flow(tmp_saves):
    m = _manager()
    m.gold = 1234
    m.paused = True
    m.pause_panel_mode = "save"
    screen = pygame.Surface((1920, 1080))
    m._draw_pause_panel(screen)
    assert m.pause_slot_rects, "slottirivit piirtyvät"
    # Quicksave-rivi EI näy save-tilassa (slot 0 puuttuu)
    assert all(slot != 0 for _r, slot in m.pause_slot_rects)

    # Klikkaa slottia 1 -> nimeäminen alkaa oletusnimellä
    rect, slot = m.pause_slot_rects[0]
    r = m._handle_pause_panel_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, pos=rect.center, button=1))
    assert r is True
    assert m.pause_name_slot == slot
    assert m.pause_name_buffer, "oletusnimi pelipäivästä"

    # Kirjoita oma nimi ja ENTER
    m.pause_name_buffer = ""
    for ch in "Oma savi":
        m._handle_pause_panel_event(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_a, unicode=ch))
    m._handle_pause_panel_event(pygame.event.Event(
        pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r"))
    rows = {r2["slot"]: r2 for r2 in tmp_saves.list_slots()}
    assert rows[slot]["exists"] and rows[slot]["name"] == "Oma savi"
    assert m.pause_panel_mode is None, "paneeli sulkeutuu tallennukseen"


def test_pause_panel_load_returns_to_city(tmp_saves):
    m = _manager()
    m.gold = 55
    tmp_saves.save_to_slot(m, 1, "T")
    m.paused = True
    m.pause_panel_mode = "load"
    screen = pygame.Surface((1920, 1080))
    m._draw_pause_panel(screen)
    rect, slot = next((r, s) for r, s in m.pause_slot_rects if s == 1)
    r = m._handle_pause_panel_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, pos=rect.center, button=1))
    assert r == "muckford_city", "lataus vie pelimaailmaan, ei hubiin"
    assert m.paused is False


def test_raid_rats_frighten_villagers_and_guards_fight():
    import main  # noqa: F401
    from game_manager import GameManager
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from ai.villager_ai import VillagerAI
    m = GameManager()
    menu = MuckfordCityMenu(m)
    menu.on_enter()
    m.world_clock.minutes = 10 * 60.0
    m.next_raid_day = m.world_clock.day
    for _ in range(1500):
        menu.update()
        if menu.raid_state == "active":
            break
    assert menu.raid_state == "active"
    rat = next(r for r in menu.raid_rats if not r.is_dead)

    # Siirrä rotta kyläläisen viereen -> kyläläinen panikoi
    villager = next(n for n in menu.npcs
                    if isinstance(getattr(n, "ai_controller", None), VillagerAI))
    rat.rect.center = (villager.rect.centerx + 80, villager.rect.centery)
    panicked = False
    for _ in range(90):
        menu.update()
        rat.rect.center = (villager.rect.centerx + 80, villager.rect.centery)
        if villager.ai_controller.panic_mode:
            panicked = True
            break
    assert panicked, "kyläläinen pelkää raid-rottaa"

    # Vartija (combat-AI) vahingoittaa rottaa kun se on lähellä
    guard = next((n for n in menu.npcs
                  if not isinstance(getattr(n, "ai_controller", None),
                                    VillagerAI)
                  and getattr(n, "ai_controller", None) is not None
                  and hasattr(n, "perform_attack")), None)
    assert guard is not None, "vartijoita on kaupungissa"
    hp0 = rat.current_hp
    for _ in range(600):
        rat.rect.center = (guard.rect.centerx + 50, guard.rect.centery)
        rat.current_stamina = rat.max_stamina
        menu.update()
        if rat.current_hp < hp0 or rat.is_dead:
            break
    assert rat.is_dead or rat.current_hp < hp0, "vartija puolustautuu"


def test_bard_stays_on_stage_and_is_visible():
    import main  # noqa: F401
    from game_manager import GameManager
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    m = GameManager()
    menu = MuckfordCityMenu(m)
    menu.on_enter()
    stage = getattr(menu, "stage", None)
    assert stage is not None
    menu._update_ambient_event()          # alustaa event-tilan
    menu._start_bard_performance(stage)
    bard = menu._event_bard
    assert bard is not None
    assert bard.sim_state == "PERFORMING"
    pos0 = bard.rect.center
    for _ in range(120):
        menu.update()
    assert bard.sim_state == "PERFORMING"
    dx = abs(bard.rect.centerx - pos0[0])
    dy = abs(bard.rect.centery - pos0[1])
    assert dx < 30 and dy < 30, "bardi pysyy lavalla (AI ei vie töihin)"
    # Bardi piirtyy (ei INSIDE-tilassa)
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)


def test_gate_and_barracks_relocated_apart():
    import main  # noqa: F401
    from assets.tiles.arena import Arena
    from assets.tiles.muckford_objects import ShantyYardGate, TeamBarracks, ShantyHouse
    a = Arena()
    gate = next(p for p in a.props if isinstance(p, ShantyYardGate))
    barr = next(p for p in a.props if isinstance(p, TeamBarracks))
    street_top = a.height // 2 - 200
    street_bottom = a.height // 2 + 200
    # Portti kadun eteläpuolella, barracks lännessä - selvästi erillään
    assert gate.rect.y > street_top, "portti ei enää talokorttelissa"
    assert barr.rect.x < 800, "barracks kadun länsipäässä"
    assert abs(gate.rect.centerx - barr.rect.centerx) > 1500

    # Taloja ei generoidu niiden päälle
    for p in a.props:
        if isinstance(p, ShantyHouse):
            for target in (gate, barr):
                t = pygame.Rect(target.image_pos[0], target.image_pos[1],
                                target.image.get_width(),
                                target.image.get_height())
                h = pygame.Rect(p.image_pos[0], p.image_pos[1],
                                p.image.get_width(), p.image.get_height())
                assert not t.colliderect(h), "talo ei peitä porttia/barracksia"
