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

from citys.mucford.forest_excursion import ForestExcursionArena, outskirts_state
from lore.world_map_data import LOCATIONS
from menus.regional_staging_menu import RegionalStagingMenu
from minigames.marsh_fishing import MarshFishingMenu, choose_fish
from settings import ENEMY_TEAM
from assets.tiles.water import FishingAnchor
from systems.whisper_marsh_story import (
    _patch_world_map_metadata,
    _refresh_story_props,
    marsh_objective,
    sync_whisper_marsh_story,
    whisper_marsh_story_state,
)
from units.whisper_pool_boss import WhisperPoolMaw


class DummyManager:
    def __init__(self):
        self.npc_state = {"global": {"flags": {}, "deeds": []}}
        self.inventory = {}
        self.gold = 0
        self.reputation = 0
        self.pending_fishing_anchor = None
        self.fishing_return_state = "forest_excursion"
        self.pending_local_area = None
        self.pending_world_location = None
        self.events = []

    def record_tier0_event(self, event_type, event_id):
        self.events.append((event_type, event_id))


class FakeMarshMenu:
    def __init__(self, manager):
        self.manager = manager
        self.arena = ForestExcursionArena(manager)
        self.marsh_story_props = []
        self.marsh_npcs = []
        self.marsh_markers = []


def test_story_progression_tracks_camp_ferryman_map_fishing_and_boss_gate():
    manager = DummyManager()
    state = whisper_marsh_story_state(manager)
    camp = outskirts_state(manager)

    state["quest_stage"] = 1
    camp["camp_stage"] = 1
    assert sync_whisper_marsh_story(manager) is True
    assert state["quest_stage"] == 2
    assert "Ferryman Noll" in marsh_objective(manager)

    state["ferryman_rescued"] = True
    state["quest_stage"] = 3
    camp["camp_stage"] = 2
    assert sync_whisper_marsh_story(manager) is True
    assert state["quest_stage"] == 4

    state["mapped_points"] = ["pool_west", "pool_east", "pool_south"]
    assert sync_whisper_marsh_story(manager) is True
    assert state["quest_stage"] == 5

    camp["camp_stage"] = 3
    assert sync_whisper_marsh_story(manager) is True
    assert state["quest_stage"] == 6

    state["first_fish_caught"] = True
    assert sync_whisper_marsh_story(manager) is True
    assert state["quest_stage"] == 7
    assert state["boss_unlocked"] is True

    state["boss_defeated"] = True
    assert sync_whisper_marsh_story(manager) is True
    assert state["quest_stage"] == 8
    assert state["completed"] is True


def test_named_marsh_npcs_and_pool_survey_markers_are_stable_props():
    manager = DummyManager()
    state = whisper_marsh_story_state(manager)
    menu = FakeMarshMenu(manager)

    state["quest_stage"] = 2
    _refresh_story_props(menu)
    names = {npc.name for npc in menu.marsh_npcs}
    assert names == {
        "Surveyor Kessa Fenmark",
        "Brik Sealrunner",
        "Ferryman Noll",
    }
    assert any(marker.style == "ferryman" for marker in menu.marsh_markers)
    assert all(prop in menu.arena.props for prop in menu.marsh_story_props)

    state["ferryman_rescued"] = True
    state["quest_stage"] = 4
    _refresh_story_props(menu)
    assert len([marker for marker in menu.marsh_markers if marker.style == "survey"]) == 3
    assert {marker.marker_id for marker in menu.marsh_markers} == {
        "pool_west",
        "pool_east",
        "pool_south",
    }


def test_fish_tables_are_different_for_channel_and_whisper_pool():
    channel = FishingAnchor(10, 10, "left", "Greywash Channel", 1)
    pool = FishingAnchor(20, 20, "right", "Whisper Pool", 2)

    channel_names = {choose_fish(channel, random.Random(seed)).name for seed in range(80)}
    pool_names = {choose_fish(pool, random.Random(seed)).name for seed in range(80)}

    assert "Mudfin" in channel_names
    assert "Greywash Perch" in channel_names
    assert "Whisper Koi" in pool_names
    assert "Echo Eel" in pool_names
    assert channel_names.isdisjoint(pool_names)


def test_successful_reel_awards_fish_and_unlocks_pool_boss():
    manager = DummyManager()
    state = whisper_marsh_story_state(manager)
    state["quest_stage"] = 6
    anchor = FishingAnchor(2500, 1400, "left", "Whisper Pool", 2)
    manager.pending_fishing_anchor = anchor

    menu = MarshFishingMenu(manager)
    menu.on_enter()
    menu.current_fish = choose_fish(anchor, random.Random(2))
    menu.phase = "reel"
    menu.cast_power = 1.0
    menu.tension = 40.0
    menu.fish_stamina_max = 100.0
    menu.fish_stamina = 0.2
    menu.reel_timer = 100
    menu.frame = 12
    menu.rng = random.Random(5)

    menu._update_reel(True)

    assert menu.phase == "result"
    assert menu.result_success is True
    assert manager.inventory[menu.current_fish.name] == 1
    assert state["fish_caught"] == 1
    assert state["first_fish_caught"] is True
    assert state["quest_stage"] == 7
    assert state["boss_unlocked"] is True


def test_over_tension_breaks_the_line_without_awarding_inventory():
    manager = DummyManager()
    anchor = FishingAnchor(100, 100, "left", "Greywash Channel", 1)
    menu = MarshFishingMenu(manager)
    menu.anchor = anchor
    menu.current_fish = choose_fish(anchor, random.Random(1))
    menu.phase = "reel"
    menu.tension = 99.8
    menu.fish_stamina_max = 100.0
    menu.fish_stamina = 70.0
    menu.reel_timer = 100
    menu.rng = random.Random(1)

    menu._update_reel(True)

    assert menu.phase == "result"
    assert menu.result_success is False
    assert "snapped" in menu.result_text.lower()
    assert manager.inventory == {}


def test_regional_staging_factory_opens_fishing_without_a_new_main_state():
    manager = DummyManager()
    manager.pending_local_area = "marsh_fishing"
    manager.pending_fishing_anchor = FishingAnchor(1, 2, "left", "Greywash Channel", 1)

    menu = RegionalStagingMenu(manager)

    assert isinstance(menu, MarshFishingMenu)
    assert manager.pending_local_area is None


def test_whisper_pool_maw_has_generated_boss_art_and_second_phase_spawn():
    boss = WhisperPoolMaw("Whisper Pool Maw", 400, 500, ENEMY_TEAM)

    assert boss.is_boss is True
    assert boss.max_hp == 520
    assert boss.image.get_width() == 118
    assert boss.image.get_height() == 88
    assert boss.phase == 1

    boss.current_hp = boss.max_hp // 2
    boss._enter_second_phase(None)

    assert boss.phase == 2
    assert len(boss.pending_spawn) == 3
    assert all(spawn.SPECIES == "Mire-Lurker Spawn" for spawn in boss.pending_spawn)


def test_world_map_exposes_fishing_story_and_named_pool_boss():
    # Other focused world-map tests intentionally mutate the shared registry.
    # Reapply the pure story metadata patch so this assertion verifies the current
    # canonical mutation instead of depending on pytest collection order.
    _patch_world_map_metadata()
    location = LOCATIONS["whisper_marsh"]

    assert "fishing" in location["services"]
    assert location["boss"] == "Whisper Pool Maw"
    assert location["story_state"] == "playable quest chain"
