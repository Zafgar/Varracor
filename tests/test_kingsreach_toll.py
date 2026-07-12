import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1280, 720))

from systems.muckford_opening_integration import install_muckford_opening_integration

install_muckford_opening_integration()

from citys.mucford.kingsreach_toll import (
    MAP_HEIGHT,
    MAP_WIDTH,
    OFFICIAL_EVIDENCE,
    SERVICE_COST,
    SERVICE_ESCAPEES,
    SMUGGLER_FEE,
    TOLL_FEE,
    KingsreachTollArena,
    KingsreachTollMenu,
    kingsreach_objective,
    kingsreach_state,
    sync_kingsreach_story,
)
from lore.world_map_data import LOCATIONS, get_route
from loot_data import LOOT_DROPS
from menus.regional_staging_menu import RegionalStagingMenu
from settings import ENEMY_TEAM, PLAYER_TEAM
from systems.kingsreach_toll_integration import _patch_world_map_data
from systems.tier0_world_tracker import ensure_tier0_state, tier0_phase
from units.human import Human
from units.kingsreach_toll_monsters import (
    CausewayBandit,
    CrownTollEnforcer,
    FeveredEscapee,
    KINGSREACH_THREAT_CLASSES,
    TollmasterHadrikCrowl,
)


class DummyClock:
    def __init__(self):
        self.year = 3
        self.day = 13
        self.hour = 12
        self.minutes = 12 * 60.0
        self.weather = "clear"


class DummyLeague:
    def __init__(self, tier=1):
        self.tier = tier


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
    def __init__(self, level=7, tier=1):
        self.npc_state = {"global": {"flags": {}, "deeds": []}}
        self.inventory = {}
        self.city_storage = {}
        self.gold = 500
        self.reputation = 0
        self.reputations = {}
        self.world_clock = DummyClock()
        self.league_engine = DummyLeague(tier)
        self.player_character = Human("Commander", 120, 120, PLAYER_TEAM, "Common")
        self.player_character.ai_controller = None
        self.player_character.level = level
        self.paused = False
        self.world_paused = False
        self.match_in_progress = False
        self.current_arena = None
        self.current_map_vfx = None
        self.pending_local_area = None
        self.pending_world_location = None
        self.kingsreach_entry = None
        self.greywash_entry = None
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

    def modify_faction_rep(self, faction_id, amount):
        self.reputations[faction_id] = int(self.reputations.get(faction_id, 0)) + int(amount)

    def get_tier0_area_advice(self, area_id):
        from systems.tier0_world_tracker import tier0_area_advice

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
        self.rect = pygame.Rect(x, y, 42, 42)
        self.team_color = PLAYER_TEAM
        self.is_dead = False
        self.current_hp = 600
        self.statuses = []

    def take_damage(self, amount, *_args, **_kwargs):
        self.current_hp -= amount
        return amount

    def apply_status(self, name, duration, damage):
        self.statuses.append((name, duration, damage))


def _inspect(menu):
    state = kingsreach_state(menu.manager)
    state["quest_stage"] = 1
    menu._medic_dialogue()
    assert state["inspection_complete"] is True
    assert state["quest_stage"] == 2
    menu.dialogue_active = False


def test_kingsreach_story_requires_inspection_then_resolution_then_promotion():
    manager = DummyManager()
    state = kingsreach_state(manager)
    assert kingsreach_objective(manager).startswith("Speak with Toll Captain")

    state["quest_stage"] = 1
    state["inspection_complete"] = True
    assert sync_kingsreach_story(manager) is True
    assert state["quest_stage"] == 2

    state["quest_stage"] = 5
    state["pass_issued"] = True
    assert sync_kingsreach_story(manager) is True
    assert state["quest_stage"] == 6
    assert state["completed"] is True

    ensure_tier0_state(manager)["story_flags"]["tier1_promoted"] = True
    assert sync_kingsreach_story(manager) is True
    assert state["quest_stage"] == 7


def test_arena_contains_causeway_gate_quarantine_culvert_resources_and_exits():
    manager = DummyManager()
    arena = KingsreachTollArena(manager)

    assert arena.width == MAP_WIDTH == 3800
    assert arena.height == MAP_HEIGHT == 2300
    assert len(arena.resources) == 28
    assert arena.east_exit.centerx > arena.gate_rect.centerx
    assert arena.west_exit.centerx < arena.gate_rect.centerx
    assert arena.quarantine_rect.centerx > arena.gate_rect.centerx
    assert arena.smuggler_rect.centerx < arena.gate_rect.centerx
    assert arena.bandit_rect.centery < arena.gate_rect.centery
    assert arena.gatehouse in arena.props
    assert arena.east_booth in arena.obstacles
    assert arena.west_booth in arena.obstacles

    surface = pygame.Surface((1280, 720))
    arena.draw_background(surface, (1200, 650))
    arena.draw_foreground(surface, (1200, 650))
    assert surface.get_bounding_rect().width == 1280


def test_official_evidence_route_consumes_orders_and_seal_but_keeps_vale_signet():
    manager = DummyManager()
    menu = KingsreachTollMenu(manager)
    _inspect(menu)
    for name, amount in OFFICIAL_EVIDENCE.items():
        manager.inventory[name] = amount

    menu.choice_mode = "resolution"
    menu.choice_active = True
    menu._resolve_choice(0)

    state = kingsreach_state(manager)
    assert state["resolution"] == "official_evidence"
    assert state["quest_stage"] == 5
    assert manager.inventory["Vale's Broken Signet"] == 1
    assert "Torn Crown Orders" not in manager.inventory
    assert "Wax Seal" not in manager.inventory
    assert manager.reputations["crown_dominion"] == 8


def test_full_toll_payment_is_noncombat_resolution_and_costs_exact_amount():
    manager = DummyManager()
    menu = KingsreachTollMenu(manager)
    _inspect(menu)
    before = manager.gold

    menu.choice_mode = "resolution"
    menu.choice_active = True
    menu._resolve_choice(1)

    state = kingsreach_state(manager)
    assert state["resolution"] == "paid"
    assert state["toll_paid"] is True
    assert state["quest_stage"] == 5
    assert manager.gold == before - TOLL_FEE
    assert state["boss_unlocked"] is False
    assert manager.reputations["crown_dominion"] == 2


def test_quarantine_service_consumes_supplies_counts_escapees_and_grants_credit():
    manager = DummyManager()
    menu = KingsreachTollMenu(manager)
    _inspect(menu)

    menu.choice_mode = "resolution"
    menu.choice_active = True
    menu._resolve_choice(2)
    state = kingsreach_state(manager)
    assert state["quest_stage"] == 3
    assert state["service_started"] is True

    for name, amount in SERVICE_COST.items():
        manager.inventory[name] = amount
    state["service_escapees"] = SERVICE_ESCAPEES
    menu._medic_dialogue()

    assert state["service_complete"] is True
    assert state["quest_stage"] == 5
    assert manager.reputation == 5
    assert manager.reputations["crown_dominion"] == 10
    for name in SERVICE_COST:
        assert name not in manager.inventory


def test_smuggler_route_costs_less_but_unlocks_crowl_and_hurts_crown_rep():
    manager = DummyManager()
    menu = KingsreachTollMenu(manager)
    _inspect(menu)
    before = manager.gold

    menu.choice_mode = "smuggler"
    menu.choice_active = True
    menu._resolve_choice(0)

    state = kingsreach_state(manager)
    assert manager.gold == before - SMUGGLER_FEE
    assert state["resolution"] == "smuggling"
    assert state["quest_stage"] == 4
    assert state["boss_unlocked"] is True
    assert menu.boss is not None
    assert manager.reputations["crown_dominion"] == -5
    assert any(isinstance(monster, CrownTollEnforcer) for monster in menu.monsters)


def test_kingsreach_threats_have_generated_art_ai_loot_and_expected_levels():
    assert [threat.THREAT_LEVEL for threat in KINGSREACH_THREAT_CLASSES] == [6, 6, 7]
    for index, threat_class in enumerate(KINGSREACH_THREAT_CLASSES):
        threat = threat_class(threat_class.SPECIES, 250 + index * 130, 320, ENEMY_TEAM)
        assert threat.level == threat_class.THREAT_LEVEL
        assert threat.ai_controller is not None
        assert set(threat._generated_frames) == {"idle", "run", "attack", "hurt", "dead"}
        assert threat.image.get_bounding_rect().width > 20
        assert threat_class.SPECIES in LOOT_DROPS

    assert CrownTollEnforcer.SPECIES != FeveredEscapee.SPECIES
    assert CausewayBandit.THREAT_LEVEL == 7


def test_tollmaster_crowl_has_three_phases_collectors_knives_and_stamp_attack():
    manager = DummyManager()
    boss = TollmasterHadrikCrowl("Tollmaster Hadrik Crowl", 700, 700, ENEMY_TEAM)
    target = CombatTarget(boss.rect.centerx + 80, boss.rect.centery)

    assert boss.is_boss is True
    assert boss.level == 8
    assert boss.max_hp == 1640

    boss.current_hp = int(boss.max_hp * 0.60)
    boss._phase_two(manager)
    assert boss.phase == 2
    assert len(boss.pending_spawn) == 3
    assert all(spawn.SPECIES == "Crown Toll Enforcer" for spawn in boss.pending_spawn)
    assert boss.pending_stamp_shock is True

    boss.pending_spawn = []
    boss.current_hp = int(boss.max_hp * 0.25)
    boss._phase_three(manager)
    assert boss.phase == 3
    assert len(boss.pending_spawn) == 2
    assert all(spawn.SPECIES == "Causeway Bandit" for spawn in boss.pending_spawn)
    assert boss.pending_tax_shout is True

    before = target.current_hp
    assert boss.release_tax_shout([target], manager) == 1
    assert target.current_hp < before
    assert any(status[0] == "Slow" for status in target.statuses)
    assert any(status[0] == "Bleed" for status in target.statuses)
    assert "Tollmaster Hadrik Crowl" in LOOT_DROPS


def test_crowl_death_forces_pass_route_and_grants_ledger_rewards():
    manager = DummyManager()
    menu = KingsreachTollMenu(manager)
    state = kingsreach_state(manager)
    state["quest_stage"] = 4
    state["resolution"] = "smuggling"
    state["boss_unlocked"] = True
    menu._spawn_boss_if_needed()
    menu.boss.is_dead = True

    menu._process_boss()

    assert state["boss_defeated"] is True
    assert state["quest_stage"] == 5
    assert manager.inventory["Crowl's Black Ledger"] == 1
    assert manager.inventory["Crown Seal Token"] == 1
    assert manager.gold == 590
    assert manager.reputation == 6


def test_pass_issuance_sets_finale_flags_and_existing_league_promotion_opens_road():
    manager = DummyManager(tier=1)
    menu = KingsreachTollMenu(manager)
    state = kingsreach_state(manager)
    state["quest_stage"] = 5
    state["resolution"] = "official_evidence"

    menu._issue_pass()

    flags = ensure_tier0_state(manager)["story_flags"]
    assert state["quest_stage"] == 6
    assert state["completed"] is True
    assert flags["kingsreach_cleared"] is True
    assert flags["bram_recommendation_requested"] is True
    assert manager.inventory["Stamped Crown Travel Papers"] == 1
    assert manager.inventory["Crown Promotion Docket"] == 1
    assert tier0_phase(manager) == 7

    manager.league_engine.tier = 2
    menu.on_enter()
    flags = ensure_tier0_state(manager)["story_flags"]
    assert flags["tier1_promoted"] is True
    assert state["quest_stage"] == 7
    assert manager.inventory["Bram's Recommendation"] == 1
    assert "Crown Promotion Docket" not in manager.inventory
    assert tier0_phase(manager) == 8


def test_regional_factory_returns_kingsreach_menu_with_stable_named_npcs():
    manager = DummyManager()
    manager.pending_local_area = "kingsreach_toll"
    manager.pending_world_location = "kingsreach_toll"

    menu = RegionalStagingMenu(manager)

    assert isinstance(menu, KingsreachTollMenu)
    menu._refresh_npcs()
    assert {npc.name for npc in menu.npcs} == {
        "Toll Captain Elric Dorn",
        "Medic Vela Marrow",
        "Salla Quill",
        "Nix Quickreed",
    }


def test_world_map_metadata_and_western_causeway_routes_are_live():
    _patch_world_map_data()
    location = LOCATIONS["kingsreach_toll"]

    assert location["content_state"] == "playable"
    assert location["boss"] == "Tollmaster Hadrik Crowl"
    assert "Crown travel papers" in location["services"]
    assert "water-fever haze" in location["threats"]
    assert "official evidence" in location["formal_routes"]
    assert get_route("greywash_ford", "kingsreach_toll") is not None
    assert get_route("kingsreach_toll", "rattlebridge") is not None
