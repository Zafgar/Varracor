import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1280, 720))

from systems.muckford_opening_integration import install_muckford_opening_integration

install_muckford_opening_integration()

from citys.mucford.drowned_chapel import (
    CHAPEL_HEIGHT,
    CHAPEL_WIDTH,
    ChapelStone,
    DrownedChapelArena,
    DrownedChapelMenu,
    chapel_objective,
    drowned_chapel_state,
    sync_drowned_chapel_story,
)
from lore.world_map_data import LOCATIONS, get_route
from loot_data import LOOT_DROPS
from menus.regional_staging_menu import RegionalStagingMenu
from settings import ENEMY_TEAM, PLAYER_TEAM
from systems.drowned_chapel_integration import _patch_world_map_data
from systems.tier0_world_tracker import tier0_area_advice
from units.drowned_chapel_monsters import (
    BellDrownedPilgrim,
    BellWraith,
    DROWNED_CHAPEL_MONSTER_CLASSES,
    FloodedAcolyte,
    WaterRisenPilgrim,
)
from units.human import Human


class DummyClock:
    def __init__(self):
        self.year = 3
        self.day = 1
        self.minutes = 8 * 60.0
        self.weather = "rain"


class DummyVFX:
    def show_damage(self, *_args, **_kwargs):
        pass

    def create_impact_sparks(self, *_args, **_kwargs):
        pass


class DummyManager:
    def __init__(self):
        self.npc_state = {"global": {"flags": {}, "deeds": []}}
        self.inventory = {}
        self.city_storage = {}
        self.gold = 0
        self.reputation = 0
        self.world_clock = DummyClock()
        self.player_character = Human("Commander", 120, 120, PLAYER_TEAM, "Common")
        self.player_character.ai_controller = None
        self.player_character.level = 1
        self.pending_local_area = None
        self.pending_world_location = None
        self.chapel_return = False
        self.paused = False
        self.match_in_progress = False
        self.current_arena = None
        self.all_units = pygame.sprite.Group()
        self.vfx = DummyVFX()
        self.camera_x = 0
        self.camera_y = 0
        self.events = []

    def record_tier0_event(self, event_type, event_id):
        self.events.append((event_type, event_id))


class PulseTarget:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.team_color = PLAYER_TEAM
        self.is_dead = False
        self.current_hp = 200
        self.statuses = []

    def take_damage(self, amount, *_args, **_kwargs):
        self.current_hp -= amount
        return amount

    def apply_status(self, name, duration, damage):
        self.statuses.append((name, duration, damage))


def test_drowned_chapel_story_progresses_through_all_field_objectives():
    manager = DummyManager()
    state = drowned_chapel_state(manager)

    assert chapel_objective(manager).startswith("Speak with Sister-Medic")
    state["quest_stage"] = 1
    state["medicine_chest_recovered"] = True
    assert sync_drowned_chapel_story(manager) is True
    assert state["quest_stage"] == 2

    state["rescued_pilgrims"] = ["pilgrim_senn", "pilgrim_orla", "pilgrim_cal"]
    assert sync_drowned_chapel_story(manager) is True
    assert state["quest_stage"] == 3

    state["water_samples"] = ["nave_north", "nave_south", "grave_pool"]
    assert sync_drowned_chapel_story(manager) is True
    assert state["quest_stage"] == 4
    assert manager.inventory["Sanctified Wax"] == 3

    state["lit_wards"] = ["camp_ward", "nave_ward", "tower_ward"]
    assert sync_drowned_chapel_story(manager) is True
    assert state["quest_stage"] == 5
    assert state["boss_unlocked"] is True

    state["boss_defeated"] = True
    assert sync_drowned_chapel_story(manager) is True
    assert state["quest_stage"] == 6
    assert state["completed"] is True


def test_area_contains_flooded_chapel_graveyard_camp_resources_and_collisions():
    manager = DummyManager()
    arena = DrownedChapelArena(manager)

    assert arena.width == CHAPEL_WIDTH == 3300
    assert arena.height == CHAPEL_HEIGHT == 2200
    assert len(arena.waters) == 2
    assert len(arena.resources) == 29
    assert arena.water_obstacles
    assert arena.land_obstacles
    assert arena.quarantine_zone.collidepoint((350, 1000))
    assert arena.bell_zone.collidepoint((2600, 450))
    # Submerged graves are represented by Gravewater itself. Sixteen readable
    # headstones remain on dry islands and the graveyard rim.
    assert sum(
        isinstance(prop, ChapelStone) and prop.style == "grave"
        for prop in arena.props
    ) >= 16
    assert any(
        isinstance(prop, ChapelStone) and prop.style == "tower"
        for prop in arena.props
    )

    surface = pygame.Surface((1280, 720))
    arena.draw_background(surface, (900, 500))
    arena.draw_foreground(surface, (900, 500))
    assert surface.get_bounding_rect().width == 1280


def test_chapel_resources_persist_for_the_current_world_day_and_reset_next_day():
    manager = DummyManager()
    arena = DrownedChapelArena(manager)
    node = arena.resources[0]

    assert node.harvest(manager)
    assert node.harvested is True
    assert manager.inventory[node.resource_name] >= 1

    rebuilt = DrownedChapelArena(manager)
    rebuilt_node = next(item for item in rebuilt.resources if item.node_id == node.node_id)
    assert rebuilt_node.harvested is True

    manager.world_clock.day += 1
    next_day = DrownedChapelArena(manager)
    refreshed = next(item for item in next_day.resources if item.node_id == node.node_id)
    assert refreshed.harvested is False


def test_story_props_show_rhea_trapped_pilgrims_samples_and_wards_by_stage():
    manager = DummyManager()
    menu = DrownedChapelMenu(manager)
    state = drowned_chapel_state(manager)

    state["quest_stage"] = 2
    menu._refresh_story_props()
    names = {npc.name for npc in menu.chapel_npcs}
    assert "Sister-Medic Rhea Ashford" in names
    assert {"Pilgrim Senn", "Pilgrim Orla", "Brother Cal"}.issubset(names)

    state["rescued_pilgrims"] = ["pilgrim_senn", "pilgrim_orla", "pilgrim_cal"]
    state["quest_stage"] = 3
    menu._refresh_story_props()
    assert {marker.marker_id for marker in menu.chapel_markers} == {
        "nave_north",
        "nave_south",
        "grave_pool",
    }

    state["quest_stage"] = 4
    menu._refresh_story_props()
    assert {marker.marker_id for marker in menu.chapel_markers} == {
        "camp_ward",
        "nave_ward",
        "tower_ward",
    }


def test_tainted_water_builds_exposure_and_quarantine_camp_clears_it():
    manager = DummyManager()
    menu = DrownedChapelMenu(manager)
    state = drowned_chapel_state(manager)

    menu.player.rect.center = (1700, 1000)
    state["infection"] = 50.0
    infected = menu._infection_step()
    assert infected > 50.0

    menu.player.rect.center = manager.player_character.rect.center = (350, 1000)
    state["infection"] = 50.0
    recovering = menu._infection_step()
    assert recovering < 50.0


def test_new_monsters_have_generated_art_ai_levels_and_registered_loot():
    assert [monster.THREAT_LEVEL for monster in DROWNED_CHAPEL_MONSTER_CLASSES] == [3, 4, 5]
    for index, monster_class in enumerate(DROWNED_CHAPEL_MONSTER_CLASSES):
        monster = monster_class(monster_class.SPECIES, 200 + index * 50, 200, ENEMY_TEAM)
        assert monster.ai_controller is not None
        assert monster.level == monster_class.THREAT_LEVEL
        assert set(monster._generated_frames) == {"idle", "run", "attack", "hurt", "dead"}
        assert monster.image.get_bounding_rect().width > 15
        assert monster_class.SPECIES in LOOT_DROPS
    assert WaterRisenPilgrim.SPECIES != FloodedAcolyte.SPECIES != BellWraith.SPECIES


def test_bell_drowned_pilgrim_second_phase_summons_and_bell_wave_hits_targets():
    manager = DummyManager()
    boss = BellDrownedPilgrim("The Bell-Drowned Pilgrim", 500, 500, ENEMY_TEAM)
    target = PulseTarget(boss.rect.centerx + 40, boss.rect.centery)
    # PulseTarget is intentionally a minimal non-Sprite combat target.
    manager.all_units = [boss, target]

    assert boss.is_boss is True
    assert boss.max_hp == 720
    assert boss.image.get_size() == (122, 104)
    boss.current_hp = int(boss.max_hp * 0.5)
    boss._enter_second_phase(manager)
    assert boss.phase == 2
    assert len(boss.pending_spawn) == 3
    assert all(spawn.SPECIES == "Water-risen Pilgrim" for spawn in boss.pending_spawn)

    hp_before = target.current_hp
    assert boss.release_bell_wave(manager) == 1
    assert target.current_hp < hp_before
    assert any(status[0] == "Slow" for status in target.statuses)
    assert "Bell-Drowned Pilgrim" in LOOT_DROPS


def test_world_map_route_is_open_risk_and_factory_builds_playable_menu():
    # Focused tests share the mutable world registry. Reapply the pure patch so
    # this assertion is independent of pytest collection and import order.
    _patch_world_map_data()
    manager = DummyManager()
    location = LOCATIONS["drowned_chapel"]
    route = get_route("whisper_marsh", "drowned_chapel")

    assert location["content_state"] == "playable"
    assert location["level_range"] == (3, 5)
    assert location["boss"] == "The Bell-Drowned Pilgrim"
    assert route["danger"] == 4

    advice = tier0_area_advice(manager, "drowned_chapel")
    assert advice["access_policy"] == "open_with_warning"
    assert advice["blocked_by_policy"] is False

    manager.pending_local_area = "drowned_chapel"
    manager.pending_world_location = "drowned_chapel"
    menu = RegionalStagingMenu(manager)
    assert isinstance(menu, DrownedChapelMenu)
    assert manager.pending_local_area is None
