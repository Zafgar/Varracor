import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1280, 720))

from systems.muckford_opening_integration import install_muckford_opening_integration

install_muckford_opening_integration()

from citys.mucford.low_fields import (
    FIELD_HEIGHT,
    FIELD_WIDTH,
    FieldBridge,
    LowFieldsArena,
    LowFieldsMenu,
    PROJECT_COSTS,
    low_fields_state,
)
from lore.world_map_data import LOCATIONS, get_route
from settings import PLAYER_TEAM
from systems.muckford_low_fields_integration import _patch_world_map_data
from units.human import Human


class DummyClock:
    def __init__(self, year=3, day=1):
        self.year = year
        self.day = day
        self.minutes = 8 * 60.0
        self.weather = "clear"


class DummyManager:
    def __init__(self):
        self.npc_state = {"global": {"flags": {}, "deeds": []}}
        self.inventory = {}
        self.city_storage = {}
        self.world_clock = DummyClock()
        self.player_character = Human("Commander", 400, 200, PLAYER_TEAM, "Common")
        self.player_character.ai_controller = None
        self.paused = False
        self.match_in_progress = False
        self.current_arena = None
        self.all_units = pygame.sprite.Group()
        self.camera_x = 0
        self.camera_y = 0
        self.gold = 0
        self.reputation = 0
        self.active_dialogue = None
        self.low_fields_entry = None
        self.marsh_return_state = None
        self.pending_local_area = None
        self.pending_world_location = None



def test_low_fields_resources_respawn_only_on_a_new_world_day():
    manager = DummyManager()
    state = low_fields_state(manager)
    state["harvested_nodes"] = ["carrot_0", "reed_0"]

    same_day = low_fields_state(manager)
    assert same_day["harvested_nodes"] == ["carrot_0", "reed_0"]

    manager.world_clock.day += 1
    next_day = low_fields_state(manager)
    assert next_day["harvested_nodes"] == []
    assert next_day["resource_day"] == "3:2"



def test_low_fields_builds_code_rendered_fields_water_resources_and_projects():
    manager = DummyManager()
    arena = LowFieldsArena(manager)

    assert arena.width == FIELD_WIDTH == 3200
    assert arena.height == FIELD_HEIGHT == 2200
    assert len(arena.field_rects) == 4
    assert len(arena.waters) == 1
    assert len(arena.resources) == 40
    assert arena.water_obstacles
    assert len(arena.burrows) == 3
    assert arena.irrigation_marker.project_id == "irrigation"
    assert arena.bridge_marker.project_id == "footbridge"

    surface = pygame.Surface((1280, 720))
    arena.draw_background(surface, (900, 600))
    arena.draw_foreground(surface, (900, 600))
    assert surface.get_bounding_rect().width == 1280



def test_daily_resource_harvest_is_persistent_and_not_repeatable():
    manager = DummyManager()
    arena = LowFieldsArena(manager)
    node = arena.resources[0]

    result = node.harvest(manager, random.Random(4))
    assert result
    assert manager.inventory[node.resource_name] >= 1
    assert node.harvested
    before = dict(manager.inventory)

    assert node.harvest(manager, random.Random(4)) is None
    assert manager.inventory == before

    rebuilt_arena = LowFieldsArena(manager)
    rebuilt = next(item for item in rebuilt_arena.resources if item.node_id == node.node_id)
    assert rebuilt.harvested



def test_footbridge_project_opens_a_second_irrigation_crossing():
    manager = DummyManager()
    state = low_fields_state(manager)
    arena = LowFieldsArena(manager)
    initial_barriers = len(arena.water_obstacles)
    initial_bridges = sum(isinstance(prop, FieldBridge) for prop in arena.props)

    state["projects"].append("footbridge")
    arena.refresh_persistent_props(manager)

    assert sum(isinstance(prop, FieldBridge) for prop in arena.props) == initial_bridges + 1
    assert len(arena.water_obstacles) < initial_barriers
    assert "footbridge" in low_fields_state(manager)["projects"]



def test_burrows_require_clay_and_remain_sealed_after_rebuilding_area():
    manager = DummyManager()
    arena = LowFieldsArena(manager)
    burrow = arena.burrows[0]

    assert burrow.seal(manager) is False
    manager.inventory["Clay"] = 1
    assert burrow.seal(manager) is True
    assert manager.inventory.get("Clay", 0) == 0

    rebuilt_arena = LowFieldsArena(manager)
    rebuilt = next(item for item in rebuilt_arena.burrows if item.burrow_id == burrow.burrow_id)
    assert rebuilt.sealed



def test_low_fields_menu_has_stable_npcs_monsters_and_open_risk_entry():
    manager = DummyManager()
    menu = LowFieldsMenu(manager)
    menu.on_enter()

    assert manager.current_arena is menu.arena
    assert menu.player.rect.center == (470, 155)
    assert len(menu.npcs) == 5
    assert {npc.name for npc in menu.npcs} >= {
        "Farmer Gus",
        "Lysa Reedrunner",
        "Orin Ditchhand",
    }
    assert len(menu.monsters) == 10
    assert low_fields_state(manager)["visits"] == 1



def test_low_fields_world_node_and_routes_are_registered():
    _patch_world_map_data()
    location = LOCATIONS["low_fields"]

    assert location["content_state"] == "playable"
    assert location["level_range"] == (1, 3)
    assert "field work" in location["services"]
    assert "Softwood" in location["materials"]
    assert get_route("muckford", "low_fields")["danger"] == 1
    assert get_route("low_fields", "whisper_marsh")["danger"] == 2



def test_project_costs_match_the_planned_restoration_chain():
    assert PROJECT_COSTS["irrigation"] == {"Clay": 5, "River Reed": 4}
    assert PROJECT_COSTS["footbridge"] == {
        "Softwood": 6,
        "River Reed": 5,
        "Clay": 2,
    }
