import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1280, 720))

from systems.muckford_opening_integration import install_muckford_opening_integration

install_muckford_opening_integration()

from citys.mucford.greywash_ford import (
    BRIDGE_COST,
    CARAVAN_CHECKPOINTS,
    DESERTER_TARGET,
    FORD_HEIGHT,
    FORD_WIDTH,
    SURVEY_COUNT,
    GreywashFordArena,
    GreywashFordMenu,
    ford_objective,
    ford_state,
    sync_ford_story,
)
from lore.world_map_data import LOCATIONS, get_route
from loot_data import LOOT_DROPS
from menus.regional_staging_menu import RegionalStagingMenu
from minigames.marsh_fishing import FISH_TABLES, MarshFishingMenu, choose_fish
from settings import ENEMY_TEAM, PLAYER_TEAM
from systems.greywash_ford_integration import _patch_world_map_data
from systems.procedural_water import FishingAnchor
from systems.tier0_world_tracker import tier0_area_advice, tier0_phase
from systems.whisper_marsh_story import whisper_marsh_story_state
from units.greywash_ford_monsters import (
    CaptainGarranVale,
    CrownDeserter,
    FordBrute,
    GREYWASH_MONSTER_CLASSES,
    GreywashRiverjaw,
)
from units.human import Human


class DummyClock:
    def __init__(self, weather="rain"):
        self.year = 3
        self.day = 12
        self.hour = 14
        self.minutes = 14 * 60.0
        self.weather = weather


class DummyVFX:
    def show_damage(self, *_args, **_kwargs):
        pass

    def create_impact_sparks(self, *_args, **_kwargs):
        pass

    def create_spawn_fog(self, *_args, **_kwargs):
        pass

    def create_shockwave(self, *_args, **_kwargs):
        pass

    def create_acid_puddle(self, *_args, **_kwargs):
        pass

    def update(self, *_args, **_kwargs):
        pass

    def draw_floor(self, *_args, **_kwargs):
        pass

    def draw_top(self, *_args, **_kwargs):
        pass


class DummyManager:
    def __init__(self, level=6, weather="rain"):
        self.npc_state = {"global": {"flags": {}, "deeds": []}}
        self.inventory = {}
        self.city_storage = {}
        self.gold = 0
        self.reputation = 0
        self.world_clock = DummyClock(weather)
        self.player_character = Human("Commander", 120, 120, PLAYER_TEAM, "Common")
        self.player_character.ai_controller = None
        self.player_character.level = level
        self.paused = False
        self.world_paused = False
        self.match_in_progress = False
        self.current_arena = None
        self.current_map_vfx = None
        self.current_fishing_spots = []
        self.pending_fishing_anchor = None
        self.fishing_return_state = "forest_excursion"
        self.pending_local_area = None
        self.pending_world_location = None
        self.greywash_entry = None
        self.marsh_entry = None
        self.city_spawn_point = None
        self.active_dialogue = None
        self.all_units = pygame.sprite.Group()
        self.enemy_team = pygame.sprite.Group()
        self.round_rewards = {"loot": {}}
        self.vfx = DummyVFX()
        self.camera_x = 0
        self.camera_y = 0
        self.events = []
        self.deeds = []

    def record_tier0_event(self, event_type, event_id, amount=1):
        from systems.tier0_world_tracker import mark_tier0_event

        self.events.append((event_type, event_id))
        return mark_tier0_event(self, event_type, event_id, amount=amount)

    def record_deed(self, deed_id, description):
        self.deeds.append((deed_id, description))
        deeds = self.npc_state.setdefault("global", {}).setdefault("deeds", [])
        if deed_id not in deeds:
            deeds.append(deed_id)

    def get_tier0_area_advice(self, area_id):
        return tier0_area_advice(self, area_id)

    def add_material(self, name, amount):
        loot = self.round_rewards.setdefault("loot", {})
        loot[name] = int(loot.get(name, 0)) + int(amount)

    def grant_hero_xp(self, *_args, **_kwargs):
        pass

    def _draw_floating_prompt(self, *_args, **_kwargs):
        pass


class CombatTarget:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 38, 38)
        self.team_color = PLAYER_TEAM
        self.is_dead = False
        self.current_hp = 500
        self.statuses = []

    def take_damage(self, amount, *_args, **_kwargs):
        self.current_hp -= amount
        return amount

    def apply_status(self, name, duration, damage):
        self.statuses.append((name, duration, damage))


def test_ford_story_progresses_from_survey_to_kingsreach_road():
    manager = DummyManager()
    state = ford_state(manager)

    assert ford_objective(manager).startswith("Speak with Ferrykeeper")
    state["quest_stage"] = 1
    state["surveyed_lanes"] = ["north_ford", "mid_ford", "south_ford"]
    assert sync_ford_story(manager) is True
    assert state["quest_stage"] == 2

    state["deserters_defeated"] = DESERTER_TARGET
    assert sync_ford_story(manager) is True
    assert state["quest_stage"] == 3

    state["bridge_repaired"] = True
    assert sync_ford_story(manager) is True
    assert state["quest_stage"] == 4

    state["caravan_complete"] = True
    assert sync_ford_story(manager) is True
    assert state["quest_stage"] == 5

    state["tower_searched"] = True
    assert sync_ford_story(manager) is True
    assert state["quest_stage"] == 6
    assert state["boss_unlocked"] is True

    state["boss_defeated"] = True
    assert sync_ford_story(manager) is True
    assert state["quest_stage"] == 7

    state["completed"] = True
    assert sync_ford_story(manager) is True
    assert state["quest_stage"] == 8


def test_ford_arena_has_wide_river_three_lanes_bridge_routes_and_fishing():
    manager = DummyManager(weather="storm")
    arena = GreywashFordArena(manager)

    assert arena.width == FORD_WIDTH == 3900
    assert arena.height == FORD_HEIGHT == 2500
    assert len(arena.ford_bands) == SURVEY_COUNT == 3
    assert len(arena.survey_markers) == 3
    assert len(arena.resources) == 31
    assert len(arena.fishing_spots) >= 3
    assert arena.flood_strength() == 3
    assert arena.muckford_exit.centerx > arena.river.rect.right
    assert arena.kingsreach_exit.centerx < arena.river.rect.left
    assert arena.whisper_exit.centery > arena.river.rect.centery

    ford_point = (arena.river.rect.centerx, sum(arena.ford_bands[0]) // 2)
    assert arena.is_wading(ford_point) is True
    assert not any(barrier.rect.collidepoint(ford_point) for barrier in arena.water_obstacles)

    bridge_point = arena.bridge_rect.center
    assert any(barrier.rect.collidepoint(bridge_point) for barrier in arena.water_obstacles)
    state = ford_state(manager)
    state["bridge_repaired"] = True
    arena.refresh_persistent(manager)
    assert arena.repaired_bridge is not None
    assert not any(barrier.rect.collidepoint(bridge_point) for barrier in arena.water_obstacles)
    assert arena.is_wading(bridge_point) is False

    surface = pygame.Surface((1280, 720))
    arena.draw_background(surface, (1250, 900))
    arena.draw_foreground(surface, (1250, 900))
    assert surface.get_bounding_rect().width == 1280


def test_ford_monsters_have_distinct_generated_art_ai_loot_and_levels():
    assert [monster.THREAT_LEVEL for monster in GREYWASH_MONSTER_CLASSES] == [5, 5, 6]
    for index, monster_class in enumerate(GREYWASH_MONSTER_CLASSES):
        monster = monster_class(monster_class.SPECIES, 250 + index * 120, 320, ENEMY_TEAM)
        assert monster.level == monster_class.THREAT_LEVEL
        assert monster.ai_controller is not None
        assert set(monster._generated_frames) == {"idle", "run", "attack", "hurt", "dead"}
        assert monster.image.get_bounding_rect().width > 20
        assert monster_class.SPECIES in LOOT_DROPS

    assert GreywashRiverjaw.SPECIES != CrownDeserter.SPECIES
    assert FordBrute.THREAT_LEVEL == 6


def test_garran_vale_has_three_phases_reinforcements_floods_and_command_shout():
    manager = DummyManager()
    boss = CaptainGarranVale("Captain Garran Vale", 700, 700, ENEMY_TEAM)
    target = CombatTarget(boss.rect.centerx + 70, boss.rect.centery)

    assert boss.is_boss is True
    assert boss.level == 7
    assert boss.max_hp == 1380
    assert boss.phase == 1

    boss.current_hp = int(boss.max_hp * 0.60)
    boss._phase_two(manager)
    assert boss.phase == 2
    assert len(boss.pending_spawn) == 3
    assert all(spawn.SPECIES == "Crown Deserter" for spawn in boss.pending_spawn)
    assert boss.pending_flood_pulses == 1

    boss.pending_spawn = []
    boss.current_hp = int(boss.max_hp * 0.25)
    boss._phase_three(manager)
    assert boss.phase == 3
    assert len(boss.pending_spawn) == 2
    assert all(spawn.SPECIES == "Ford Brute" for spawn in boss.pending_spawn)
    assert boss.pending_flood_pulses == 3
    assert boss.pending_command_shout is True

    before = target.current_hp
    assert boss.release_command_shout([target], manager) == 1
    assert target.current_hp < before
    assert any(status[0] == "Slow" for status in target.statuses)
    assert any(status[0] == "Bleed" for status in target.statuses)
    assert "Captain Garran Vale" in LOOT_DROPS


def test_regional_factory_returns_ford_menu_with_named_stable_npcs():
    manager = DummyManager()
    manager.pending_local_area = "greywash_ford"
    manager.pending_world_location = "greywash_ford"

    menu = RegionalStagingMenu(manager)

    assert isinstance(menu, GreywashFordMenu)
    menu._refresh_npcs_and_caravan()
    assert {npc.name for npc in menu.ford_npcs} == {
        "Ferrykeeper Oswin Pike",
        "Saint Mara Wold",
        "Hobb Reed",
    }


def test_bridge_repair_and_five_caravan_checkpoints_advance_without_extra_step():
    manager = DummyManager()
    menu = GreywashFordMenu(manager)
    state = ford_state(manager)
    state["quest_stage"] = 3
    for name, amount in BRIDGE_COST.items():
        manager.inventory[name] = amount
    menu.player.rect.center = menu.arena.bridge_rect.center

    assert menu._try_bridge() is True
    assert state["bridge_repaired"] is True
    assert state["quest_stage"] == 4
    assert menu.caravan is not None

    for expected in range(1, CARAVAN_CHECKPOINTS + 1):
        menu.player.rect.center = menu.caravan.rect.center
        assert menu._try_caravan() is True
        assert int(state.get("caravan_checkpoint", 0)) == expected
        if expected < CARAVAN_CHECKPOINTS:
            assert menu.caravan is not None

    assert state["caravan_complete"] is True
    assert state["quest_stage"] == 5
    assert menu.caravan is None


def test_ford_fishing_uses_own_table_and_does_not_advance_whisper_marsh_story():
    manager = DummyManager()
    anchor = FishingAnchor(100, 100, "east", "Greywash Ford", 3, "greywash_ford")
    menu = MarshFishingMenu(manager)
    menu.anchor = anchor
    menu.rng = random.Random(77)
    menu.current_fish = choose_fish(anchor, menu.rng)
    whisper_before = dict(whisper_marsh_story_state(manager))

    menu._award_catch()

    state = ford_state(manager)
    assert state["fish_caught"] == 1
    assert state["catches"][menu.current_fish.name] == 1
    assert manager.inventory[menu.current_fish.name] == 1
    assert whisper_marsh_story_state(manager) == whisper_before
    assert "Greywash Ford" in FISH_TABLES["greywash_ford"]


def test_boss_death_and_oswin_report_open_kingsreach_and_advance_tier0():
    manager = DummyManager()
    state = ford_state(manager)
    state["quest_stage"] = 6
    state["boss_unlocked"] = True
    menu = GreywashFordMenu(manager)
    menu._spawn_boss_if_needed()
    assert menu.boss is not None

    menu.boss.is_dead = True
    menu._process_boss()
    assert state["boss_defeated"] is True
    assert state["quest_stage"] == 7
    assert manager.inventory["Vale's Broken Signet"] == 1

    menu._complete_report()
    assert state["completed"] is True
    assert state["quest_stage"] == 8
    assert manager.gold == 300
    assert manager.reputation == 19
    assert manager.city_storage["Ford Trade Goods"] == 10
    assert manager.city_storage["Scrap Iron"] == 5
    assert ("flag", "kingsreach_access") in manager.events
    assert tier0_phase(manager) == 6


def test_world_map_routes_and_open_risk_advice_are_live():
    _patch_world_map_data()
    manager = DummyManager(level=1)
    location = LOCATIONS["greywash_ford"]

    assert location["content_state"] == "playable"
    assert location["boss"] == "Captain Garran Vale"
    assert "river fishing" in location["services"]
    assert "flood current" in location["threats"]
    assert get_route("muckford", "greywash_ford") is not None
    assert get_route("whisper_marsh", "greywash_ford") is not None
    assert get_route("greywash_ford", "kingsreach_toll") is not None

    advice = tier0_area_advice(manager, "greywash_ford")
    assert advice["access_policy"] == "open_with_warning"
    assert advice["blocked_by_policy"] is False
    assert advice["risk"] == "SEVERE"
    assert "recommended Lv 5-7" in advice["warning"]
