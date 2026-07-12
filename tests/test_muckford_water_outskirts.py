import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1280, 720))

from systems.muckford_opening_integration import install_muckford_opening_integration
from systems.muckford_outskirts_integration import _patch_world_map_data
from systems.procedural_water import ProceduralWaterBody

install_muckford_opening_integration()

from citys.mucford.forest_excursion import (
    ForestExcursionArena,
    MarshBridge,
    outskirts_state,
)
from lore.world_map_data import LOCATIONS


class DummyManager:
    def __init__(self):
        self.npc_state = {"global": {"flags": {}, "deeds": []}}
        self.inventory = {}


def test_water_geometry_drives_collision_and_fishing_anchors():
    water = ProceduralWaterBody(
        pygame.Rect(100, 50, 620, 1100),
        seed=77,
        name="Test Channel",
        shore_variance=40,
    )

    left, right = water.bounds_at(500)
    assert water.contains_point(((left + right) / 2, 500))
    assert not water.contains_point((left - 100, 500))

    barriers = water.make_collision_barriers([(430, 560)])
    assert barriers
    assert all(not (430 <= barrier.rect.centery <= 560) for barrier in barriers)
    assert any(barrier.rect.centery < 430 for barrier in barriers)
    assert any(barrier.rect.centery > 560 for barrier in barriers)

    anchors = water.fishing_anchors(8, difficulty=2)
    assert len(anchors) == 8
    assert {anchor.bank for anchor in anchors} == {"left", "right"}
    assert all(anchor.water_name == "Test Channel" for anchor in anchors)
    assert all(anchor.difficulty == 2 for anchor in anchors)


def test_water_renderer_draws_without_texture_assets():
    water = ProceduralWaterBody(
        pygame.Rect(120, 80, 520, 900),
        seed=23,
        name="Render Test",
    )
    surface = pygame.Surface((900, 700))
    surface.fill((0, 0, 0))
    water.add_ripple((360, 330), now_ms=100)
    water.draw(surface, offset=(0, 0), now_ms=900)

    # Both water colour and moving detail should have altered the frame.
    assert surface.get_at((360, 330))[:3] != (0, 0, 0)
    assert surface.get_bounding_rect().width > 400


def test_whisper_marsh_builds_water_resources_and_future_fishing_points():
    manager = DummyManager()
    arena = ForestExcursionArena(manager)

    assert arena.width == 3600
    assert arena.height == 2400
    assert len(arena.waters) == 2
    assert len(arena.resources) >= 30
    assert len(arena.fishing_spots) == 12
    assert arena.water_obstacles
    assert len(arena.obstacles) > len(arena.land_obstacles)


def test_boardwalk_upgrade_opens_second_crossing_and_persists():
    manager = DummyManager()
    state = outskirts_state(manager)
    state["camp_stage"] = 0
    arena = ForestExcursionArena(manager)
    initial_barriers = len(arena.water_obstacles)
    initial_bridges = sum(isinstance(prop, MarshBridge) for prop in arena.props)

    state["camp_stage"] = 2
    arena.refresh_development(manager)
    upgraded_barriers = len(arena.water_obstacles)
    upgraded_bridges = sum(isinstance(prop, MarshBridge) for prop in arena.props)

    assert initial_bridges == 1
    assert upgraded_bridges == 2
    assert upgraded_barriers < initial_barriers
    assert outskirts_state(manager)["camp_stage"] == 2


def test_world_map_describes_playable_outskirts_resources():
    # The runtime installer also performs this update automatically. Calling the
    # pure data patch directly keeps this assertion independent of pytest module
    # collection order and verifies the canonical mutation itself.
    _patch_world_map_data()
    location = LOCATIONS["whisper_marsh"]
    assert location["content_state"] == "playable"
    assert "survey-post development" in location["services"]
    assert "River Reed" in location["materials"]
    assert "Driftwood" in location["materials"]
    assert "Clay" in location["materials"]
