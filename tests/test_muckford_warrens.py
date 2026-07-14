import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1280, 720))

from systems.muckford_opening_integration import install_muckford_opening_integration

install_muckford_opening_integration()

from citys.mucford.muckford_city_menu import MuckfordCityMenu
from citys.mucford.muckford_warrens import (
    CACHE_COUNT,
    NEST_COUNT,
    RATCATCHER_COUNT,
    TRACE_COUNT,
    WARRENS_HEIGHT,
    WARRENS_WIDTH,
    CitySewerHatch,
    MuckfordWarrensArena,
    MuckfordWarrensMenu,
    sync_warrens_story,
    warrens_objective,
    warrens_state,
)
from lore.world_map_data import LOCATIONS, get_route
from loot_data import LOOT_DROPS
from menus.regional_staging_menu import RegionalStagingMenu
from settings import ENEMY_TEAM, PLAYER_TEAM
from systems.muckford_warrens_integration import _patch_world_map_data
from systems.tier0_world_tracker import tier0_area_advice, tier0_phase
from units.human import Human
from units.muckford_warrens_monsters import (
    RatRider,
    SewerRatSwarm,
    VioletEyedRat,
    WARRENS_MONSTER_CLASSES,
    WarrensRatKing,
    WasteGnawer,
)


class DummyClock:
    def __init__(self):
        self.year = 3
        self.day = 8
        self.hour = 12
        self.minutes = 12 * 60.0
        self.weather = "rain"


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
    def __init__(self, level=5):
        self.npc_state = {"global": {"flags": {}, "deeds": []}}
        self.inventory = {}
        self.city_storage = {}
        self.gold = 0
        self.reputation = 0
        self.world_clock = DummyClock()
        self.player_character = Human("Commander", 120, 120, PLAYER_TEAM, "Common")
        self.player_character.ai_controller = None
        self.player_character.level = level
        self.paused = False
        self.world_paused = False
        self.match_in_progress = False
        self.current_arena = None
        self.current_map_vfx = None
        self.all_units = pygame.sprite.Group()
        self.enemy_team = pygame.sprite.Group()
        self.round_rewards = {"loot": {}}
        self.vfx = DummyVFX()
        self.camera_x = 0
        self.camera_y = 0
        self.pending_local_area = None
        self.pending_world_location = None
        self.warrens_entry = None
        self.low_fields_entry = None
        self.city_spawn_point = None
        self.active_dialogue = None
        self.next_raid_day = 9
        self.events = []
        self.deeds = []

    def record_tier0_event(self, event_type, event_id, amount=1):
        from systems.tier0_world_tracker import mark_tier0_event

        self.events.append((event_type, event_id))
        return mark_tier0_event(self, event_type, event_id, amount=amount)

    def record_deed(self, deed_id, description):
        self.deeds.append((deed_id, description))
        global_state = self.npc_state.setdefault("global", {})
        deeds = global_state.setdefault("deeds", [])
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
        self.rect = pygame.Rect(x, y, 36, 36)
        self.team_color = PLAYER_TEAM
        self.is_dead = False
        self.current_hp = 400
        self.statuses = []

    def take_damage(self, amount, *_args, **_kwargs):
        self.current_hp -= amount
        return amount

    def apply_status(self, name, duration, damage):
        self.statuses.append((name, duration, damage))


class FakeRaidRat(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.rect = self.image.get_rect()
        self.is_dead = False


class FakeCityMenu:
    def __init__(self, manager):
        self.manager = manager
        self.raid_rats = [FakeRaidRat(), FakeRaidRat()]
        self.raid_state = "active"
        self.raid_result_timer = 0
        self._warrens_peace_announced = False
        manager.all_units.add(self.raid_rats)


def test_warrens_story_progresses_through_every_city_crisis_stage():
    manager = DummyManager()
    state = warrens_state(manager)

    assert warrens_objective(manager).startswith("Speak with Hamo")
    state["quest_stage"] = 1
    state["traced_signs"] = [f"trail_{index}" for index in range(1, TRACE_COUNT + 1)]
    assert sync_warrens_story(manager) is True
    assert state["quest_stage"] == 2

    state["recovered_caches"] = [f"cache_{index}" for index in range(1, CACHE_COUNT + 1)]
    assert sync_warrens_story(manager) is True
    assert state["quest_stage"] == 3

    state["destroyed_nests"] = [f"nest_{index}" for index in range(1, NEST_COUNT + 1)]
    assert sync_warrens_story(manager) is True
    assert state["quest_stage"] == 4
    assert state["deep_drain_open"] is True

    state["rescued_ratcatchers"] = [
        "ratcatcher_tessa",
        "ratcatcher_brin",
        "ratcatcher_dorrik",
    ]
    assert sync_warrens_story(manager) is True
    assert state["quest_stage"] == 5
    # Pelitesti 24: boss ei enää avaudu automaattisesti vaiheessa 5 -
    # Royal Cistern -portti kammetään auki sepän Cistern Gate Crankilla
    assert state["boss_unlocked"] is False

    state["boss_defeated"] = True
    assert sync_warrens_story(manager) is True
    assert state["quest_stage"] == 6
    assert state["city_raids_ended"] is True

    state["completed"] = True
    assert sync_warrens_story(manager) is True
    assert state["quest_stage"] == 7


def test_warrens_arena_contains_routes_objectives_channels_and_royal_gate():
    manager = DummyManager()
    arena = MuckfordWarrensArena(manager)

    assert arena.width == WARRENS_WIDTH == 3600
    assert arena.height == WARRENS_HEIGHT == 2400
    assert len(arena.trail_marks) == TRACE_COUNT == 4
    assert len(arena.food_caches) == CACHE_COUNT == 4
    assert len(arena.waste_nests) == NEST_COUNT == 4
    assert len(arena.bridges) == 4
    assert len(arena.tainted_channels) == 3
    assert arena.boss_gate is not None
    assert arena.city_exit.centery < arena.low_fields_exit.centery
    assert arena.throne in arena.props

    channel_point = arena.tainted_channels[0].center
    assert arena.player_is_wading(channel_point) is True
    bridge_point = arena.bridges[0].center
    assert arena.player_is_wading(bridge_point) is False

    surface = pygame.Surface((1280, 720))
    arena.draw_background(surface, (1100, 700))
    arena.draw_foreground(surface, (1100, 700))
    assert surface.get_bounding_rect().width == 1280


def test_warrens_monsters_have_distinct_levels_generated_art_ai_and_loot():
    assert [monster.THREAT_LEVEL for monster in WARRENS_MONSTER_CLASSES] == [4, 4, 5, 5]

    for index, monster_class in enumerate(WARRENS_MONSTER_CLASSES):
        monster = monster_class(monster_class.SPECIES, 220 + index * 100, 300, ENEMY_TEAM)
        assert monster.level == monster_class.THREAT_LEVEL
        assert monster.ai_controller is not None
        assert set(monster._generated_frames) == {
            "idle",
            "run",
            "attack",
            "hurt",
            "dead",
        }
        assert monster.image.get_bounding_rect().width > 18
        assert monster_class.SPECIES in LOOT_DROPS

    assert SewerRatSwarm.SPECIES != VioletEyedRat.SPECIES
    assert RatRider.THREAT_LEVEL == WasteGnawer.THREAT_LEVEL == 5


def test_rat_king_has_three_phases_regiments_waste_waves_and_screech():
    manager = DummyManager()
    boss = WarrensRatKing("The Rat King of Muckford", 700, 700, ENEMY_TEAM)
    target = CombatTarget(boss.rect.centerx + 60, boss.rect.centery)

    assert boss.is_boss is True
    assert boss.level == 6
    assert boss.max_hp == 1120
    assert boss.image.get_size() == (164, 126)
    assert boss.phase == 1

    boss.current_hp = int(boss.max_hp * 0.60)
    boss._phase_two(manager)
    assert boss.phase == 2
    assert len(boss.pending_spawn) == 4
    assert all(spawn.SPECIES == "Violet-Eyed Rat" for spawn in boss.pending_spawn)
    assert boss.pending_waste_wave == 1

    boss.pending_spawn = []
    boss.current_hp = int(boss.max_hp * 0.30)
    boss._phase_three(manager)
    assert boss.phase == 3
    assert len(boss.pending_spawn) == 4
    assert {spawn.SPECIES for spawn in boss.pending_spawn} == {"Rat Rider", "Waste Gnawer"}
    assert boss.pending_waste_wave == 3
    assert boss.pending_screech is True

    before = target.current_hp
    assert boss.release_royal_screech([target], manager) == 1
    assert target.current_hp < before
    assert any(status[0] == "Slow" for status in target.statuses)
    assert any(status[0] == "Poison" for status in target.statuses)
    assert "Rat King" in LOOT_DROPS


def test_regional_factory_returns_warrens_menu_and_stable_story_npcs():
    manager = DummyManager()
    manager.pending_local_area = "muckford_warrens"
    manager.pending_world_location = "muckford_warrens"

    menu = RegionalStagingMenu(manager)

    assert isinstance(menu, MuckfordWarrensMenu)
    state = warrens_state(manager)
    state["quest_stage"] = 4
    menu._refresh_npcs()
    names = {npc.name for npc in menu.warrens_npcs}
    assert names >= {
        "Hamo",
        "Old Rinna Net",
        "Tessa Trapwire",
        "Brin Sootsnare",
        "Dorrik Two-Nails",
    }


def test_rat_king_death_marks_tier0_phase_and_permanently_ends_city_raids():
    manager = DummyManager()
    state = warrens_state(manager)
    state["quest_stage"] = 5
    state["boss_unlocked"] = True
    menu = MuckfordWarrensMenu(manager)
    menu._spawn_boss_if_needed()
    assert menu.boss is not None

    menu.boss.is_dead = True
    menu._process_boss()

    assert state["boss_defeated"] is True
    assert state["city_raids_ended"] is True
    assert state["quest_stage"] == 6
    assert manager.next_raid_day == 10 ** 9
    assert manager.inventory["Gnawed Crown"] == 1
    assert tier0_phase(manager) == 5

    fake_city = FakeCityMenu(manager)
    assert MuckfordCityMenu._rat_king_defeated(fake_city) is True
    MuckfordCityMenu._update_raids(fake_city)
    assert fake_city.raid_rats == []
    assert fake_city.raid_state == "idle"
    assert len(manager.all_units) == 0


def test_reporting_crisis_recovery_rewards_city_and_sets_completion_flags_once():
    manager = DummyManager()
    state = warrens_state(manager)
    state["quest_stage"] = 6
    state["boss_defeated"] = True
    state["city_raids_ended"] = True
    menu = MuckfordWarrensMenu(manager)

    menu._complete_report("Hamo")
    first_gold = manager.gold
    first_rep = manager.reputation
    first_storage = dict(manager.city_storage)

    assert state["completed"] is True
    assert state["quest_stage"] == 7
    assert manager.gold == 140
    assert manager.reputation == 10
    assert manager.city_storage["Recovered Grain"] == 8
    assert manager.city_storage["Scrap Iron"] == 4

    menu._complete_report("Old Rinna Net")
    assert manager.gold == first_gold
    assert manager.reputation == first_rep
    assert manager.city_storage == first_storage


def test_world_map_routes_and_advice_keep_warrens_open_with_severe_warning():
    _patch_world_map_data()
    manager = DummyManager(level=1)
    location = LOCATIONS["muckford_warrens"]

    assert location["content_state"] == "playable"
    assert location["boss"] == "The Rat King of Muckford"
    assert "food recovery" in location["services"]
    assert "Vortex Residue" in location["materials"]
    assert get_route("muckford", "muckford_warrens") is not None
    assert get_route("low_fields", "muckford_warrens") is not None

    advice = tier0_area_advice(manager, "muckford_warrens")
    assert advice["access_policy"] == "open_with_warning"
    assert advice["blocked_by_policy"] is False
    assert advice["risk"] == "SEVERE"
    assert "recommended Lv 4-6" in advice["warning"]


def test_city_hatch_has_distinct_cleared_visual_state():
    hatch = CitySewerHatch(100, 100, cleared=False)
    uncleared = hatch.image.copy()
    hatch.cleared = True
    hatch._redraw()

    assert hatch.is_structure is False
    assert hatch.blocks_projectiles is False
    assert pygame.image.tostring(uncleared, "RGBA") != pygame.image.tostring(hatch.image, "RGBA")
