import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1280, 720))

from systems.muckford_opening_integration import install_muckford_opening_integration

install_muckford_opening_integration()

from menus.promotion_menu import PromotionMenu
from npc.dwarf_league_manager import DwarfLeagueManager
from systems.muckford_low_fields_integration import _patch_world_map_data as _patch_low_fields_world_map
from systems.tier0_finale import (
    FINAL_REWARD_SP,
    complete_ceremony,
    ensure_finale_state,
    farewell_pages,
    finale_requirements,
    mark_promotion_victory,
    promotion_lock_reason,
    requirement_lines,
    return_docket_to_bram,
)
from systems.tier0_world_tracker import ensure_tier0_state, mark_tier0_event, tier0_phase
from systems.world_progression import ensure_world_state, location_status, route_key


class DummyLeague:
    def __init__(self, tier=1, eligible=True):
        self.tier = tier
        self.eligible = eligible
        self.promotions = 0

    def check_promotion_eligibility(self):
        if self.eligible:
            return True, "PROMOTION MATCH READY!", object()
        return False, "Play more: 5v5 (1/2)", None

    def promote_player(self):
        self.promotions += 1
        self.tier = min(6, self.tier + 1)
        return True


class DummyPlayer:
    def __init__(self):
        self.rect = pygame.Rect(100, 100, 40, 50)
        self.level = 7


class DummyVFX:
    def show_damage(self, *_args, **_kwargs):
        pass


class DummyManager:
    def __init__(self, tier=1, eligible=True):
        self.npc_state = {"global": {"flags": {}, "deeds": []}}
        self.inventory = {}
        self.gold = 100
        self.reputation = 20
        self.reputations = {}
        self.league_engine = DummyLeague(tier, eligible)
        self.player_character = DummyPlayer()
        self.vfx = DummyVFX()
        self.match_mode = "PROMOTION"
        self.match_result = "VICTORY"
        self.is_game_over = False
        self.pending_local_area = None
        self.pending_world_location = None
        self.kingsreach_entry = None
        self.events = []
        self.deeds = []

    def record_tier0_event(self, event_type, value, amount=1):
        self.events.append((event_type, value))
        return mark_tier0_event(self, event_type, value, amount=amount)

    def record_deed(self, deed_id, text):
        self.deeds.append((deed_id, text))

    def apply_rewards(self):
        pass


def ready_manager(tier=1):
    manager = DummyManager(tier=tier, eligible=True)
    state = ensure_tier0_state(manager)
    state["story_flags"]["kingsreach_cleared"] = True
    state["defeated_bosses"].append("rat_king")
    manager.npc_state["global"]["kingsreach_toll"] = {
        "completed": True,
        "pass_issued": True,
        "quest_stage": 6,
        "resolution": "quarantine_service",
    }
    manager.inventory["Stamped Crown Travel Papers"] = 1
    manager.inventory["Crown Promotion Docket"] = 1
    return manager


def test_docket_requires_kingsreach_then_is_consumed_exactly_once():
    manager = DummyManager()
    manager.inventory["Crown Promotion Docket"] = 1

    ok, reason = return_docket_to_bram(manager)
    assert ok is False
    assert "Kingsreach" in reason
    assert manager.inventory["Crown Promotion Docket"] == 1

    ensure_tier0_state(manager)["story_flags"]["kingsreach_cleared"] = True
    ok, reason = return_docket_to_bram(manager)
    assert ok is True
    assert "ledger" in reason
    assert "Crown Promotion Docket" not in manager.inventory
    assert ensure_finale_state(manager)["docket_returned"] is True

    ok, _reason = return_docket_to_bram(manager)
    assert ok is True
    assert "Crown Promotion Docket" not in manager.inventory


def test_finale_requirements_combine_crown_papers_crisis_docket_and_league_rank():
    manager = ready_manager()
    status = finale_requirements(manager)
    assert status["ready"] is False
    assert status["requirements"]["docket_returned"] is False
    assert "Speak with Bram" in promotion_lock_reason(manager)

    assert return_docket_to_bram(manager)[0] is True
    status = finale_requirements(manager)
    assert status["ready"] is True
    assert status["major_crisis"] == "Rat King of Muckford"
    assert all("YES" in line for line in requirement_lines(manager))


def test_unfinished_rookie_dust_season_remains_locked_after_world_work():
    manager = ready_manager()
    manager.league_engine.eligible = False
    assert return_docket_to_bram(manager)[0] is True

    status = finale_requirements(manager)
    assert status["ready"] is False
    assert status["requirements"]["league_qualified"] is False
    assert "5v5" in promotion_lock_reason(manager)


def test_bram_dialogue_prioritizes_docket_and_waiting_states():
    manager = ready_manager()
    bram = DwarfLeagueManager()
    context = {
        "memory": manager.npc_state,
        "inventory": manager.inventory,
        "league_engine": manager.league_engine,
        "player_roster": [],
        "reputation": 0,
        "completed_quests": [],
        "player": {"team_name": "Mudlarks"},
    }

    assert bram.get_dialogue_root(context) == "tier0_docket"
    assert return_docket_to_bram(manager)[0] is True
    assert bram.get_dialogue_root(context) == "tier0_waiting"

    ensure_tier0_state(manager)["story_flags"]["tier1_promoted"] = True
    assert bram.get_dialogue_root(context) == "tier0_promoted"


def test_promotion_rewards_are_idempotent_and_never_raise_tier_again():
    manager = ready_manager(tier=2)
    assert return_docket_to_bram(manager)[0] is True
    before_gold = manager.gold
    before_tier = manager.league_engine.tier

    state = mark_promotion_victory(manager)
    assert state["promotion_won"] is True
    assert manager.gold == before_gold + FINAL_REWARD_SP
    assert manager.reputation == 30
    assert manager.inventory["Bram's Recommendation"] == 1
    assert manager.inventory["Tier 1 Charter"] == 1
    assert manager.inventory["Sera Quench Sponsor Letter"] == 1
    assert manager.league_engine.tier == before_tier == 2

    mark_promotion_victory(manager)
    assert manager.gold == before_gold + FINAL_REWARD_SP
    assert manager.inventory["Tier 1 Charter"] == 1
    assert manager.league_engine.promotions == 0


def test_farewell_dialogue_is_branch_aware_for_crisis_and_kingsreach_route():
    manager = ready_manager(tier=2)
    return_docket_to_bram(manager)
    mark_promotion_victory(manager)
    pages = farewell_pages(manager)
    combined = " ".join(page["text"] for page in pages)

    assert len(pages) == 7
    assert "Rat King" in combined
    assert "quarantine tents" in combined
    assert "Rattlebridge" in combined
    assert {page["speaker"] for page in pages} >= {
        "Bram 'Mudhand' Carrow",
        "Marda Shant",
        "Hamo",
        "Sera Quench's Representative",
    }


def test_ceremony_draws_code_graphics_and_opens_departure_after_last_page():
    manager = ready_manager(tier=2)
    return_docket_to_bram(manager)
    menu = PromotionMenu(manager)
    menu.on_enter()

    assert len(menu.pages) == 7
    assert ensure_finale_state(manager)["rewards_claimed"] is True
    surface = pygame.Surface((1280, 720))
    menu.draw(surface)
    assert surface.get_bounding_rect().width == 1280

    for _ in range(len(menu.pages)):
        menu._advance()

    state = ensure_finale_state(manager)
    flags = ensure_tier0_state(manager)["story_flags"]
    assert state["ceremony_complete"] is True
    assert state["departure_ready"] is True
    assert flags["tier0_finale_complete"] is True
    assert flags["rattlebridge_road_open"] is True
    assert menu.next_state == "regional_staging"
    assert manager.pending_local_area == "kingsreach_toll"
    assert manager.pending_world_location == "kingsreach_toll"
    assert tier0_phase(manager) == 8


def test_complete_ceremony_is_safe_for_loaded_promoted_save():
    manager = ready_manager(tier=2)
    return_docket_to_bram(manager)
    complete_ceremony(manager)
    gold = manager.gold
    complete_ceremony(manager)

    assert manager.gold == gold
    assert ensure_finale_state(manager)["ceremony_complete"] is True
    assert manager.inventory["Bram's Recommendation"] == 1


def test_world_map_cannot_bypass_papers_promotion_or_farewell_to_rattlebridge():
    # Other tests may reload lore.world_map_data. Restore runtime-only local nodes
    # before world progression rebuilds its surveyed route graph.
    _patch_low_fields_world_map()
    manager = ready_manager(tier=2)
    world = ensure_world_state(manager)
    world["current_location"] = "kingsreach_toll"
    for location_id in ("kingsreach_toll", "rattlebridge"):
        if location_id not in world["discovered_locations"]:
            world["discovered_locations"].append(location_id)
    key = route_key("kingsreach_toll", "rattlebridge")
    if key not in world["discovered_routes"]:
        world["discovered_routes"].append(key)

    status = location_status(manager, "rattlebridge")
    assert status["can_travel"] is False
    assert "promotion" in status["reason"]

    return_docket_to_bram(manager)
    mark_promotion_victory(manager)
    status = location_status(manager, "rattlebridge")
    assert status["can_travel"] is False
    assert "farewell" in status["reason"]

    complete_ceremony(manager)
    status = location_status(manager, "rattlebridge")
    assert status["can_travel"] is True
