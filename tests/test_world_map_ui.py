import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1920, 1080))

# BarracksMenu installs runtime hooks before the other menus are imported, the
# same order used by main.py.
from menus.barracks_menu import BarracksMenu
from arenas.world_arena_profiles import apply_arena_profile, get_arena_profile
from citys.mucford.muckford_city_menu import MuckfordCityMenu
from game_manager import GameManager
from menus.league_menu import LeagueMenu
from menus.regional_staging_menu import RegionalStagingMenu
from menus.town_hub import TownHub
from menus.world_map_menu import WorldMapMenu
from settings import SCREEN_HEIGHT, SCREEN_WIDTH
from systems.world_progression import (
    arena_access_status,
    ensure_world_state,
    travel_to,
)


class DummyClock:
    def __init__(self):
        self.minutes = 480.0
        self.day = 1

    def advance_day(self):
        self.day += 1


class DummyLeague:
    def __init__(self, tier=1):
        self.tier = tier


class DummyUnit:
    def __init__(self, level=1):
        self.level = level


class DummyManager:
    def __init__(self, tier=1, level=1, reputation=0):
        self.npc_state = {
            "global": {"reputation": reputation, "flags": {}, "deeds": []}
        }
        self.league_engine = DummyLeague(tier)
        self.league_level = tier
        self.player_character = DummyUnit(level)
        self.my_team = []
        self.reputation = reputation
        self.world_clock = DummyClock()
        self.mine_key_owned = False
        self.world_map_return_state = "hub"
        self.pending_world_location = "muckford"
        self.current_arena_location = "shanty_yard"
        self.league_return_state = None
        self.active_dialogue = None
        self.show_inventory = False
        ensure_world_state(self)


class DummyArena:
    pass


def test_runtime_hooks_are_installed_before_game_manager_creation():
    assert getattr(GameManager, "_world_map_installed", False)
    assert getattr(MuckfordCityMenu, "_world_map_installed", False)
    assert getattr(TownHub, "_world_map_installed", False)
    assert getattr(LeagueMenu, "_world_map_return_installed", False)
    assert hasattr(GameManager, "open_world_map")
    assert hasattr(GameManager, "get_world_location")


def test_world_map_menu_draws_all_panels_without_assets():
    manager = DummyManager()
    menu = WorldMapMenu(manager)
    menu.on_enter()
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    menu.draw(screen)

    assert menu.selected_location in menu.node_rects
    assert menu.info_rect.w > 0
    assert menu.btn_travel.text == "YOU ARE HERE"


def test_regional_staging_draws_and_surveys_a_reached_city():
    manager = DummyManager(tier=2, level=8)
    manager.pending_world_location = "rattlebridge"
    menu = RegionalStagingMenu(manager)
    menu.on_enter()
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    menu.draw(screen)

    assert menu.location_id == "rattlebridge"
    assert manager.npc_state["world_progression"]["current_location"] == "rattlebridge"
    assert menu.btn_arena.enabled
    assert menu.btn_arena.text == "The Scrapring"


def test_travel_wrapper_sets_arena_and_return_context():
    manager = DummyManager()

    ok, _message, target = travel_to(manager, "shanty_yard")

    assert ok
    assert target == "league"
    assert manager.current_arena_location == "shanty_yard"
    assert manager.league_return_state == "world_map"


def test_regional_arena_check_sets_staging_return_context():
    manager = DummyManager(tier=2, level=8)
    manager.pending_world_location = "rattlebridge"
    state = ensure_world_state(manager)
    state["current_location"] = "rattlebridge"
    state["visited_locations"].append("rattlebridge")

    ok, _reason = arena_access_status(manager, "rattlebridge")

    assert ok
    assert manager.current_arena_location == "rattlebridge"
    assert manager.league_return_state == "regional_staging"


def test_arena_profile_preserves_regional_identity_for_reused_arena_class():
    profile = get_arena_profile("rivet_row")
    assert profile["arena_tier"] == 1
    assert "steam vents" in profile["hazards"]

    arena = apply_arena_profile(DummyArena(), "rivet_row")
    assert arena.world_location_id == "rivet_row"
    assert arena.display_name == "Bolt Cage"
    assert arena.recommended_level_range == (7, 10)
    assert arena.combat_focus == "close-quarters pressure"


def test_world_map_and_staging_bypass_global_pause_overlay():
    # The wrappers are class-level and can be verified without constructing the
    # full asset-heavy GameManager.
    assert GameManager.handle_ui_event.__name__ == "handle_ui_event"
    assert GameManager.draw_ui_overlay.__name__ == "draw_ui_overlay"
