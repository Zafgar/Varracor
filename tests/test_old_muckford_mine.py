import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1280, 720))

from systems.muckford_opening_integration import install_muckford_opening_integration

install_muckford_opening_integration()

from citys.mucford.mine_cave_menu import MineCaveMenu
from citys.mucford.mine_road_menu import MineRoadMenu
from citys.mucford.old_muckford_mine import (
    MINE_HEIGHT,
    MINE_WIDTH,
    PRODUCTION_COST,
    DeepCaveBroodmother,
    OldMuckfordMineArena,
    OldMuckfordMineMenu,
    mine_objective,
    old_mine_state,
    sync_old_mine_story,
)
from lore.world_map_data import LOCATIONS
from loot_data import LOOT_DROPS
from settings import ENEMY_TEAM, PLAYER_TEAM
from systems.old_muckford_mine_integration import (
    _patch_world_map_data,
    apply_daily_mine_production,
)
from systems.tier0_world_tracker import tier0_area_advice
from units.human import Human
from units.old_muckford_mine_monsters import (
    BroodGuard,
    CrystalHusk,
    GravePickman,
    OLD_MINE_MONSTER_CLASSES,
    RailWraith,
    WebCrawler,
)


class DummyClock:
    def __init__(self):
        self.year = 3
        self.day = 1
        self.minutes = 8 * 60.0
        self.weather = "clear"


class DummyVFX:
    def show_damage(self, *_args, **_kwargs):
        pass

    def create_impact_sparks(self, *_args, **_kwargs):
        pass

    def create_spawn_fog(self, *_args, **_kwargs):
        pass

    def create_ore_glimmer(self, *_args, **_kwargs):
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
        self.player_character.level = 3
        self.player_character.unlocked_skills = {"mining_1"}
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
        self.mine_key_owned = False
        self.pending_local_area = None
        self.pending_world_location = None
        self.events = []
        self.deeds = []

    def record_tier0_event(self, event_type, event_id):
        self.events.append((event_type, event_id))

    def record_deed(self, deed_id, description):
        self.deeds.append((deed_id, description))
        global_state = self.npc_state.setdefault("global", {})
        deeds = global_state.setdefault("deeds", [])
        if deed_id not in deeds:
            deeds.append(deed_id)

    def has_deed(self, deed_id):
        return deed_id in self.npc_state.get("global", {}).get("deeds", [])

    def add_material(self, name, amount):
        self.round_rewards.setdefault("loot", {})[name] = (
            int(self.round_rewards.setdefault("loot", {}).get(name, 0))
            + int(amount)
        )

    def grant_hero_xp(self, *_args, **_kwargs):
        pass

    def _draw_floating_prompt(self, *_args, **_kwargs):
        pass


class CombatTarget:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 34, 34)
        self.team_color = PLAYER_TEAM
        self.is_dead = False
        self.current_hp = 300
        self.statuses = []

    def take_damage(self, amount, *_args, **_kwargs):
        self.current_hp -= amount
        return amount

    def apply_status(self, name, duration, damage):
        self.statuses.append((name, duration, damage))


class FakeRoadMenu:
    def __init__(self, manager):
        self.manager = manager
        self.undead = []


def test_old_mine_story_progresses_through_restoration_chain():
    manager = DummyManager()
    state = old_mine_state(manager)

    assert mine_objective(manager).startswith("Speak with Foreman Torra")
    state["quest_stage"] = 1
    state["lanterns_lit"] = ["entrance_lamp", "rail_lamp", "deep_lamp"]
    assert sync_old_mine_story(manager) is True
    assert state["quest_stage"] == 2

    state["rescued_miners"] = ["miner_durn", "miner_pell", "miner_sava"]
    assert sync_old_mine_story(manager) is True
    assert state["quest_stage"] == 3

    state["cleared_collapses"] = ["north_fall", "rail_fall", "deep_fall"]
    assert sync_old_mine_story(manager) is True
    assert state["quest_stage"] == 4

    state["egg_sacs_destroyed"] = ["sac_1", "sac_2", "sac_3", "sac_4"]
    assert sync_old_mine_story(manager) is True
    assert state["quest_stage"] == 5
    assert state["boss_unlocked"] is True

    state["boss_defeated"] = True
    assert sync_old_mine_story(manager) is True
    assert state["quest_stage"] == 6

    state["production_restarted"] = True
    assert sync_old_mine_story(manager) is True
    assert state["quest_stage"] == 7
    assert state["completed"] is True


def test_expanded_mine_has_four_chambers_restoration_props_and_resources():
    manager = DummyManager()
    arena = OldMuckfordMineArena(manager)

    assert arena.width == MINE_WIDTH == 3800
    assert arena.height == MINE_HEIGHT == 2400
    assert len(arena.lanterns) == 3
    assert len(arena.collapses) == 3
    assert len(arena.egg_sacs) == 4
    assert len(arena.ore_nodes) == 18
    assert arena.web_gate is not None
    assert arena.land_obstacles if hasattr(arena, "land_obstacles") else arena.obstacles
    assert arena.production_winch in arena.props
    assert {node.resource_name for node in arena.ore_nodes} >= {
        "Iron Ore",
        "Coal",
        "Stone",
        "Chipped Ruby",
        "Silver Ore",
    }

    surface = pygame.Surface((1280, 720))
    arena.draw_background(surface, (1200, 700))
    arena.draw_foreground(surface, (1200, 700))
    assert surface.get_bounding_rect().width == 1280


def test_daily_ore_depletion_persists_and_resets_on_next_world_day():
    manager = DummyManager()
    state = old_mine_state(manager)
    state["depleted_ores"] = ["iron_1", "ruby_1"]

    same_day = OldMuckfordMineArena(manager)
    iron = next(node for node in same_day.ore_nodes if node.node_id == "iron_1")
    ruby = next(node for node in same_day.ore_nodes if node.node_id == "ruby_1")
    assert iron.is_empty is True
    assert ruby.is_empty is True

    manager.world_clock.day += 1
    next_day = OldMuckfordMineArena(manager)
    refreshed_iron = next(node for node in next_day.ore_nodes if node.node_id == "iron_1")
    refreshed_ruby = next(node for node in next_day.ore_nodes if node.node_id == "ruby_1")
    assert refreshed_iron.is_empty is False
    assert refreshed_ruby.is_empty is False
    assert old_mine_state(manager)["depleted_ores"] == []


def test_new_mine_monsters_have_generated_art_ai_levels_and_loot():
    expected_levels = [3, 4, 4, 5, 6]
    assert [monster.THREAT_LEVEL for monster in OLD_MINE_MONSTER_CLASSES] == expected_levels

    for index, monster_class in enumerate(OLD_MINE_MONSTER_CLASSES):
        monster = monster_class(monster_class.SPECIES, 250 + index * 70, 260, ENEMY_TEAM)
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

    assert GravePickman.SPECIES != RailWraith.SPECIES
    assert WebCrawler.SPECIES != CrystalHusk.SPECIES
    assert BroodGuard.THREAT_LEVEL == 6


def test_deep_broodmother_has_three_phases_summons_and_web_burst():
    manager = DummyManager()
    boss = DeepCaveBroodmother("Cave Broodmother", 700, 700, ENEMY_TEAM)
    target = CombatTarget(boss.rect.centerx + 50, boss.rect.centery)
    manager.all_units = [boss, target]

    assert boss.is_boss is True
    assert boss.level == 7
    assert boss.max_hp == 1080
    assert boss.image.get_size() == (154, 124)
    assert boss.phase == 1

    boss.current_hp = int(boss.max_hp * 0.60)
    boss._phase_two(manager)
    assert boss.phase == 2
    assert len(boss.pending_spawn) == 3
    assert all(spawn.SPECIES == "Web Crawler" for spawn in boss.pending_spawn)
    assert boss.pending_collapse_wave == 1

    boss.pending_spawn = []
    boss.current_hp = int(boss.max_hp * 0.30)
    boss._phase_three(manager)
    assert boss.phase == 3
    assert len(boss.pending_spawn) == 2
    assert all(spawn.SPECIES == "Brood Guard" for spawn in boss.pending_spawn)
    assert boss.pending_collapse_wave == 3

    before = target.current_hp
    assert boss.release_web_burst(manager) == 1
    assert target.current_hp < before
    assert any(status[0] == "Web" for status in target.statuses)
    assert "Cave Broodmother" in LOOT_DROPS


def test_mine_cave_factory_returns_expanded_menu_and_stable_npcs():
    manager = DummyManager()
    menu = MineCaveMenu(manager)

    assert isinstance(menu, OldMuckfordMineMenu)
    state = old_mine_state(manager)
    state["quest_stage"] = 2
    menu._refresh_npcs()
    names = {npc.name for npc in menu.mine_npcs}
    assert names >= {
        "Foreman Torra Flintvein",
        "Durn Coalhand",
        "Pell Rook",
        "Sava Brasspin",
    }


def test_restored_mine_delivers_only_one_production_share_per_world_day():
    manager = DummyManager()
    state = old_mine_state(manager)
    state["production_restarted"] = True

    assert apply_daily_mine_production(manager) is True
    assert manager.city_storage == {"Iron Ore": 2, "Coal": 1}
    assert apply_daily_mine_production(manager) is False
    assert manager.city_storage == {"Iron Ore": 2, "Coal": 1}

    manager.world_clock.day += 1
    assert apply_daily_mine_production(manager) is True
    assert manager.city_storage == {"Iron Ore": 4, "Coal": 2}


def test_secured_mine_road_does_not_respawn_daily_undead_blockade():
    manager = DummyManager()
    state = old_mine_state(manager)
    state["road_secured"] = True
    fake = FakeRoadMenu(manager)

    MineRoadMenu._spawn_undead(fake)

    assert fake.undead == []


def test_world_map_and_tier0_gate_keep_mardas_key_as_physical_requirement():
    _patch_world_map_data()
    manager = DummyManager()
    location = LOCATIONS["old_mine_road"]

    assert location["content_state"] == "playable"
    assert location["boss"] == "Cave Broodmother"
    assert "mine restoration" in location["services"]
    assert "Silver Ore" in location["materials"]

    advice = tier0_area_advice(manager, "old_muckford_mine")
    assert advice["access_policy"] == "physical_gate"
    assert advice["blocked_by_policy"] is True
    assert "mine key" in advice["reason"].lower()

    manager.mine_key_owned = True
    advice = tier0_area_advice(manager, "old_muckford_mine")
    assert advice["blocked_by_policy"] is False


def test_production_cost_is_meaningful_and_uses_existing_economy_materials():
    assert PRODUCTION_COST == {
        "Iron Ore": 8,
        "Coal": 5,
        "Softwood": 4,
    }
