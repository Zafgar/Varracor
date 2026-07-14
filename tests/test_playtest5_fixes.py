# tests/test_playtest5_fixes.py
"""Pelitestikierros 5: päävalikon load-paneeli + savejen poisto, NPC-sadon-
korjuun lukkiutumiskorjaus, barracks-paluun sijainti, Arena Hall ja Town
Hall -sisätilat, vedonlyönti ja kanan klikkauskaatuma."""
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


# ----------------------------------------------------------------------
# Save-slotit: poisto + päävalikon paneeli
# ----------------------------------------------------------------------

def test_delete_slot_removes_file(tmp_saves):
    m = _manager()
    assert tmp_saves.save_to_slot(m, 2, "Roskiin")
    assert os.path.exists(tmp_saves.slot_path(2))
    assert tmp_saves.delete_slot(2)
    assert not os.path.exists(tmp_saves.slot_path(2))
    rows = {r["slot"]: r for r in tmp_saves.list_slots()}
    assert not rows[2]["exists"]


def test_main_menu_load_panel_and_delete(tmp_saves):
    m = _manager()
    m.gold = 4242
    tmp_saves.save_to_slot(m, 1, "Paneelitesti")
    from menus.main_menu import MainMenu
    menu = MainMenu(m)
    menu.show_load_panel = True
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)
    assert menu.load_slot_rects, "tallennusrivit näkyvät"
    assert menu.delete_rects, "poistonapit näkyvät"

    # Poisto vaatii kaksi klikkausta
    del_rect, slot = menu.delete_rects[0]
    menu.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, pos=del_rect.center, button=1))
    assert menu.delete_armed == slot
    assert os.path.exists(tmp_saves.slot_path(slot)), "1. klikkaus vain varmistaa"
    menu.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, pos=del_rect.center, button=1))
    assert not os.path.exists(tmp_saves.slot_path(slot)), "2. klikkaus poistaa"

    # Lataus vie pelimaailmaan
    tmp_saves.save_to_slot(m, 1, "Ladattava")
    m2 = _manager()
    menu2 = MainMenu(m2)
    menu2.show_load_panel = True
    menu2.draw(surf)
    rect, slot = next((r, s) for r, s in menu2.load_slot_rects if s == 1)
    menu2.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, pos=rect.center, button=1))
    assert menu2.next_state == "muckford_city"
    assert m2.gold == 4242


# ----------------------------------------------------------------------
# NPC-sadonkorjuu: varausten vapautus
# ----------------------------------------------------------------------

def test_crop_plot_reservation_expires():
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from citys.mucford.farming_expansion import CropPlot
    city = MuckfordCityMenu(m)
    city.on_enter()
    m.world_clock.minutes = 10 * 60.0
    plots = [p for p in city.arena.crop_plots if isinstance(p, CropPlot)]
    assert plots
    # Simuloi vuotanut varaus: kaikki lukossa ilman työntekijää
    for p in plots:
        p.being_worked_on = True
        p._work_ttl = 5
    for _ in range(10):
        city.update()
    assert all(not p.being_worked_on for p in plots), \
        "roikkuvat varaukset raukeavat ajastimella"


def test_stuck_villager_releases_work_target():
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from citys.mucford.farming_expansion import CropPlot
    from ai.villager_ai import VillagerAI
    city = MuckfordCityMenu(m)
    city.on_enter()
    npc = next(n for n in city.npcs
               if isinstance(getattr(n, "ai_controller", None), VillagerAI))
    ai = npc.ai_controller
    plot = next(p for p in city.arena.crop_plots if isinstance(p, CropPlot))
    plot.being_worked_on = True
    ai.work_target = plot
    ai._clear_work_target()
    assert plot.being_worked_on is False
    assert ai.work_target is None


# ----------------------------------------------------------------------
# Kaupungin klikkaukset ja paluusijainti
# ----------------------------------------------------------------------

def test_chicken_click_does_not_crash():
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from units.farm_animals import Chicken
    city = MuckfordCityMenu(m)
    city.on_enter()
    hen = next((a for a in city.animals if isinstance(a, Chicken)), None)
    assert hen is not None
    # Klikkaa kanaa pelaajan vierestä (ennen: AttributeError milk_ready)
    city.player.rect.center = (hen.rect.centerx + 30, hen.rect.centery)
    screen_pos = (hen.rect.centerx - city.camera_x,
                  hen.rect.centery - city.camera_y)
    city._handle_click(screen_pos)


def test_barracks_exit_restores_city_position():
    m = _manager()
    from citys.mucford.barracks_interior_menu import BarracksInteriorMenu
    menu = BarracksInteriorMenu(m)
    city_pos = (3100, 1700)
    m.player_character.rect.center = city_pos
    menu.on_enter()
    assert menu.player.rect.center != city_pos, "sisällä ovella"
    # Kävele ovelle ja poistu
    menu.player.rect.centerx = menu.arena.door_rect.centerx
    menu.player.rect.bottom = menu.arena.door_rect.top - 5
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e,
                                         unicode="e"))
    assert menu.next_state == "muckford_city"
    assert menu.player.rect.center == city_pos, \
        "paluu kaupunkiin samaan kohtaan josta tultiin"


# ----------------------------------------------------------------------
# Arena Hall & Town Hall
# ----------------------------------------------------------------------

def test_city_gate_leads_to_arena_hall():
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(m)
    city.on_enter()
    gate = city.arena_gate
    assert gate is not None
    city.player.rect.centerx = gate.rect.centerx
    city.player.rect.bottom = gate.rect.bottom + 10
    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e,
                                         unicode="e"))
    assert city.next_state == "arena_hall"


def test_arena_hall_npcs_and_league_desk():
    m = _manager()
    from citys.mucford.city_interiors import ArenaHallMenu
    hall = ArenaHallMenu(m)
    hall.on_enter()
    kinds = [k for _u, k in hall.hall_npcs]
    assert "bookie" in kinds
    assert kinds.count("guard") == 2
    assert "rival" in kinds, "kilpailijatiimien edustajia loungessa"
    for _ in range(60):
        hall.update()
    surf = pygame.Surface((1920, 1080))
    hall.draw(surf)
    # Liigatiski avaa liigan
    hall.player.rect.center = (hall.league_desk.rect.centerx,
                               hall.league_desk.rect.bottom + 40)
    hall.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e,
                                         unicode="e"))
    assert hall.next_state == "league"


def test_arena_hall_betting_flow(tmp_saves):
    m = _manager()
    from citys.mucford.city_interiors import ArenaHallMenu, BET_PAYOUT
    hall = ArenaHallMenu(m)
    hall.on_enter()
    m.gold = 100
    hall._open_bet_dialogue()
    assert m.active_dialogue is not None
    hall._on_bet_action("hall_bet_20")
    assert m.gold == 80
    assert m.active_bet == {"amount": 20}
    # Voitto liigamatsissa maksaa panoksen kaksinkertaisena
    m.mode = "League"
    m.current_enemy_team = None
    m.end_match(True)
    assert m.gold == 80 + int(20 * BET_PAYOUT)
    assert m.active_bet is None


def test_town_hall_desks():
    m = _manager()
    from citys.mucford.city_interiors import TownHallMenu
    hall = TownHallMenu(m)
    hall.on_enter()
    hall.player.rect.center = (hall.clerk_desk.rect.centerx,
                               hall.clerk_desk.rect.bottom + 40)
    hall.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e,
                                         unicode="e"))
    assert hall.next_state == "sponsors"
    hall.next_state = None
    hall.player.rect.center = (hall.ledger_board.rect.centerx,
                               hall.ledger_board.rect.bottom + 40)
    hall.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e,
                                         unicode="e"))
    assert hall.next_state == "reputation"


def test_clock_hud_drawn_indoors():
    m = _manager()
    surf = pygame.Surface((1920, 1080))
    for state in ("barracks_interior", "tavern_sunk_cask", "arena_hall"):
        m.draw_ui_overlay(surf, state)  # ei saa kaatua; kello piirtyy
