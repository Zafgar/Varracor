"""Runtime integration hooks for the Varrakor world map.

Installed during menu imports before GameManager is instantiated. The hooks are
kept here to avoid invasive edits to Muckford's large city module and to remain
compatible with older saves.
"""

from __future__ import annotations

import pygame

from arenas.world_arena_profiles import apply_arena_profile
from lore.world_map_data import LOCATIONS
from sound_manager import sound_system
from systems.world_progression import (
    current_location_id,
    ensure_world_state,
    mark_location_visited,
    refresh_world_progression,
)


_INSTALLED = False


def _patch_progression_context():
    """Attach travel destinations to the existing menu/league state machine."""
    import systems.world_progression as progression

    if getattr(progression, "_world_map_context_installed", False):
        return

    previous_travel = progression.travel_to
    previous_arena_access = progression.arena_access_status

    def travel_to(manager, location_id):
        result = previous_travel(manager, location_id)
        ok, _message, target_state = result
        if not ok:
            return result

        manager.pending_world_location = str(location_id)
        if target_state == "league":
            manager.current_arena_location = str(location_id)
            manager.league_return_state = "world_map"
        elif target_state == "regional_staging":
            manager.world_map_return_state = "regional_staging"
        return result

    def arena_access_status(manager, location_id):
        ok, reason = previous_arena_access(manager, location_id)
        if ok:
            manager.current_arena_location = str(location_id)
            manager.league_return_state = "regional_staging"
        return ok, reason

    progression.travel_to = travel_to
    progression.arena_access_status = arena_access_status
    progression._world_map_context_installed = True


def _patch_game_manager():
    from game_manager import GameManager

    if getattr(GameManager, "_world_map_installed", False):
        return

    previous_init = GameManager.__init__
    previous_start_match = GameManager.start_match
    previous_handle_ui = GameManager.handle_ui_event
    previous_draw_ui = GameManager.draw_ui_overlay

    def __init__(self, *args, **kwargs):
        previous_init(self, *args, **kwargs)
        self.world_map_return_state = "hub"
        self.pending_world_location = "muckford"
        self.current_arena_location = "shanty_yard"
        self.league_return_state = None
        ensure_world_state(self)
        refresh_world_progression(self)

    def start_match(self, selected_units, battle_size_limit=None):
        result = previous_start_match(
            self, selected_units, battle_size_limit=battle_size_limit)
        if getattr(self, "mode", None) == "League" and self.current_arena:
            location_id = getattr(self, "current_arena_location", None)
            if location_id not in LOCATIONS:
                location_id = "shanty_yard"
            apply_arena_profile(self.current_arena, location_id)
        return result

    def handle_ui_event(self, event, current_state_key):
        if current_state_key in ("world_map", "regional_staging"):
            return None
        return previous_handle_ui(self, event, current_state_key)

    def draw_ui_overlay(self, screen, current_state_key):
        if current_state_key in ("world_map", "regional_staging"):
            return None
        return previous_draw_ui(self, screen, current_state_key)

    def open_world_map(self, return_state="hub"):
        self.world_map_return_state = return_state
        return "world_map"

    def get_world_location(self):
        return current_location_id(self)

    GameManager.__init__ = __init__
    GameManager.start_match = start_match
    GameManager.handle_ui_event = handle_ui_event
    GameManager.draw_ui_overlay = draw_ui_overlay
    GameManager.open_world_map = open_world_map
    GameManager.get_world_location = get_world_location
    GameManager._world_map_installed = True


def _patch_save_load():
    try:
        import save_manager
    except Exception:
        return
    if getattr(save_manager, "_world_map_installed", False):
        return

    previous_load = save_manager.load_game

    def load_game(manager, *args, **kwargs):
        result = previous_load(manager, *args, **kwargs)
        if result:
            ensure_world_state(manager)
            refresh_world_progression(manager)
            manager.pending_world_location = current_location_id(manager)
        return result

    save_manager.load_game = load_game
    save_manager._world_map_installed = True


def _patch_muckford():
    try:
        from citys.mucford.muckford_city_menu import MuckfordCityMenu
        from ui_kit import draw_text, font_small
    except Exception:
        return
    if getattr(MuckfordCityMenu, "_world_map_installed", False):
        return

    previous_enter = MuckfordCityMenu.on_enter
    previous_event = MuckfordCityMenu.handle_event
    previous_map_draw = MuckfordCityMenu._draw_city_map

    def on_enter(self):
        result = previous_enter(self)
        mark_location_visited(self.manager, "muckford", set_current=True)
        self.manager.pending_world_location = "muckford"
        return result

    def handle_event(self, event):
        blocked = (
            getattr(self, "show_pause_menu", False)
            or getattr(self, "show_map", False)
            or bool(getattr(self.manager, "active_dialogue", None))
            or bool(getattr(self.manager, "show_inventory", False))
        )
        if (event.type == pygame.KEYDOWN and event.key == pygame.K_TAB
                and not blocked):
            self.manager.world_map_return_state = "muckford_city"
            self.next_state = "world_map"
            sound_system.play_sound("click")
            return
        return previous_event(self, event)

    def _draw_city_map(self, screen):
        result = previous_map_draw(self, screen)
        draw_text("[TAB] continent map", font_small, (190, 175, 145),
                  screen, 430, 958)
        return result

    MuckfordCityMenu.on_enter = on_enter
    MuckfordCityMenu.handle_event = handle_event
    MuckfordCityMenu._draw_city_map = _draw_city_map
    MuckfordCityMenu._world_map_installed = True


def _patch_town_hub():
    try:
        from menus.town_hub import TownHub
        from settings import SCREEN_HEIGHT, SCREEN_WIDTH
        from ui_kit import UIButton
    except Exception:
        return
    if getattr(TownHub, "_world_map_installed", False):
        return

    previous_init = TownHub.__init__
    previous_event = TownHub.handle_event
    previous_update = TownHub.update
    previous_draw = TownHub.draw

    def __init__(self, manager):
        previous_init(self, manager)
        self.btn_world_map = UIButton(
            SCREEN_WIDTH // 2 - 180,
            SCREEN_HEIGHT - 205,
            360,
            58,
            "VARRAKOR WORLD MAP",
            None,
            (175, 145, 85),
        )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_m, pygame.K_TAB):
            self.manager.world_map_return_state = "hub"
            self.next_state = "world_map"
            sound_system.play_sound("click")
            return
        if self.btn_world_map.is_clicked(event):
            self.manager.world_map_return_state = "hub"
            self.next_state = "world_map"
            sound_system.play_sound("click")
            return
        return previous_event(self, event)

    def update(self):
        self.btn_world_map.update_hover(pygame.mouse.get_pos())
        return previous_update(self)

    def draw(self, screen):
        result = previous_draw(self, screen)
        self.btn_world_map.draw(screen)
        return result

    TownHub.__init__ = __init__
    TownHub.handle_event = handle_event
    TownHub.update = update
    TownHub.draw = draw
    TownHub._world_map_installed = True


def _patch_league_return():
    try:
        from menus.league_menu import LeagueMenu
    except Exception:
        return
    if getattr(LeagueMenu, "_world_map_return_installed", False):
        return

    previous_event = LeagueMenu.handle_event

    def handle_event(self, event):
        return_state = getattr(self.manager, "league_return_state", None)
        if return_state and self.btn_back.is_clicked(event):
            self.next_state = return_state
            self.manager.league_return_state = None
            sound_system.play_sound("click")
            return
        return previous_event(self, event)

    LeagueMenu.handle_event = handle_event
    LeagueMenu._world_map_return_installed = True


def install_world_map_integration():
    global _INSTALLED
    if _INSTALLED:
        return
    _patch_progression_context()
    _patch_game_manager()
    _patch_save_load()
    _patch_muckford()
    _patch_town_hub()
    _patch_league_return()
    _INSTALLED = True
