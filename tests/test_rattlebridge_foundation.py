import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

# This matches main.py's import order and installs runtime integrations.
from menus.barracks_menu import BarracksMenu
from citys.rattlebridge import rattlebridge_art
from citys.rattlebridge.rattlebridge_data import (
    DISTRICTS,
    LANDMARKS,
    LOCAL_TEAMS,
    NAMED_NPCS,
    RATTLEBRIDGE_CONTRACTS,
    SCRAPRING_HAZARDS,
)
from citys.rattlebridge.rattlebridge_map import RattlebridgeCityMap
from lore.world_map_data import LOCATIONS
from settings import SCREEN_HEIGHT, SCREEN_WIDTH


def test_runtime_install_turns_rattlebridge_into_playable_world_location():
    assert getattr(BarracksMenu, "_tiered_stations_installed", False)
    location = LOCATIONS["rattlebridge"]
    assert location["target_state"] == "rattlebridge_city"
    assert location["content_state"] == "playable"
    assert location["level_range"] == (6, 10)
    assert location["arena_tier"] == 1
    assert location["arena_name"] == "The Scrapring"
    assert "Gutter Swarm" in location["threats"]
    assert "Hush-Mantle" in location["threats"]


def test_city_map_is_larger_and_more_structured_than_muckford_foundation():
    city = RattlebridgeCityMap()

    assert city.width == int(SCREEN_WIDTH * 4.5)
    assert city.height == int(SCREEN_HEIGHT * 3.4)
    assert city.width > int(SCREEN_WIDTH * 3.0)
    assert city.height > int(SCREEN_HEIGHT * 3.0)
    assert len(city.districts) == 8
    assert set(city.districts) == set(DISTRICTS)
    assert len(city.landmarks) == len(LANDMARKS) == 12
    assert len(city.walkable_zones) == 5
    assert len(city.obstacles) > len(city.landmarks)
    assert len(city.steam_vents) >= 30
    assert len(city.cranes) >= 6
    assert len(city.market_stalls) == 15
    assert len(city.enemy_spawns) == 6


def test_starting_spawn_and_landmark_interaction_points_are_reachable():
    city = RattlebridgeCityMap()
    spawn_x, spawn_y = city.spawn_points[0]
    spawn_rect = pygame.Rect(spawn_x - 16, spawn_y - 24, 32, 24)
    assert city.is_walkable(spawn_rect)

    for landmark_id in (
        "world_gate",
        "union_market",
        "the_span",
        "scrapring_gate",
        "bridgeward_hospital",
        "freight_warehouse",
        "canalworks_lift",
        "east_gate",
    ):
        landmark = city.landmarks[landmark_id]
        x, y = landmark.interaction_point
        interaction_rect = pygame.Rect(x - 16, y - 24, 32, 24)
        assert any(zone.collidepoint(interaction_rect.center)
                   for zone in city.walkable_zones), landmark_id


def test_canonical_city_content_is_present():
    assert set(NAMED_NPCS) == {
        "sera_quench",
        "hendrik_ironspan",
        "prior_jannik_voss",
        "captain_mara_chain",
        "factor_ellis_vane",
        # Ambient-laajennus: uudet nimetyt hahmot
        "yorik_sparkspanner",
        "corwin_hale",
        "brasslight_tout",
    }
    assert set(LOCAL_TEAMS) == {
        "rattlebridge_runners",
        "bridgeguard_five",
    }
    assert set(SCRAPRING_HAZARDS) == {
        "crushing_gears",
        "steam_bursts",
        "magnet_plates",
    }
    assert len(RATTLEBRIDGE_CONTRACTS) == 4
    assert {contract["objective"] for contract in RATTLEBRIDGE_CONTRACTS} == {
        "survey_freight_deck",
        "gutter_swarm_patrol",
        "scrapring_sponsor_trial",
        "hush_mantle_rumors",
    }


def test_placeholder_pipeline_generates_all_replaceable_assets(tmp_path, monkeypatch):
    monkeypatch.setattr(rattlebridge_art, "ASSET_DIR", tmp_path)
    rattlebridge_art.clear_rattlebridge_asset_cache()

    paths = rattlebridge_art.generate_placeholder_assets(force=True)

    assert set(paths) == set(rattlebridge_art.CANONICAL_ASSETS)
    for key, path in paths.items():
        assert Path(path).exists(), key
        image = pygame.image.load(str(path))
        assert image.get_width() >= 1500
        assert image.get_height() >= 850

    loaded = rattlebridge_art.load_rattlebridge_image(
        "city_map", (640, 360)
    )
    assert loaded.get_size() == (640, 360)


def test_final_asset_name_overrides_generated_placeholder(tmp_path, monkeypatch):
    monkeypatch.setattr(rattlebridge_art, "ASSET_DIR", tmp_path)
    rattlebridge_art.clear_rattlebridge_asset_cache()
    rattlebridge_art.generate_placeholder_assets(force=True)

    final_path = tmp_path / "city_map_final.png"
    final = pygame.Surface((80, 60))
    final.fill((12, 34, 56))
    pygame.image.save(final, str(final_path))

    resolved = rattlebridge_art.resolve_asset_path("city_map")
    # The explicit final version should be preferred when a user adds it.
    assert resolved == final_path
