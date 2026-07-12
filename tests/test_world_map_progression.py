import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from lore.world_map_data import (
    ARENA_CIRCUITS,
    ARENA_LEVEL_BANDS,
    LOCATIONS,
    REGIONS,
    ROUTES,
    get_neighbors,
    get_route,
)
from systems.world_progression import (
    arena_access_status,
    ensure_world_state,
    league_lore_tier,
    location_status,
    party_level,
    survey_location,
    travel_to,
    world_progress_summary,
)


class DummyClock:
    def __init__(self):
        self.minutes = 8 * 60.0
        self.day = 1
        self.year = 3

    def advance_day(self):
        self.day += 1


class DummyLeague:
    def __init__(self, tier=1):
        self.tier = tier


class DummyUnit:
    def __init__(self, level):
        self.level = level


class DummyManager:
    def __init__(self, *, league_tier=1, level=1, reputation=0):
        self.npc_state = {
            "global": {"reputation": reputation, "flags": {}, "deeds": []}
        }
        self.league_engine = DummyLeague(league_tier)
        self.league_level = league_tier
        self.player_character = DummyUnit(level)
        self.my_team = []
        self.reputation = reputation
        self.world_clock = DummyClock()
        self.mine_key_owned = False
        self.pending_world_location = None


def test_level_bands_cover_levels_one_to_thirty_without_gaps():
    assert set(ARENA_LEVEL_BANDS) == set(range(6))
    expected_start = 1
    for tier in range(6):
        low, high = ARENA_LEVEL_BANDS[tier]
        assert low == expected_start
        assert high == low + 4
        expected_start = high + 1
    assert expected_start == 31


def test_world_graph_has_regions_locations_and_valid_route_endpoints():
    assert set(REGIONS) == {
        "sundered_heartlands",
        "crownlands",
        "sunscar_expanse",
        "wyrdwood",
        "aegis_peaks",
    }
    assert len(LOCATIONS) == 36
    assert len(ROUTES) >= 35

    for location_id, location in LOCATIONS.items():
        assert location["region"] in REGIONS
        assert len(location["map_pos"]) == 2
        assert location["content_state"] in {"playable", "survey", "future"}
        low, high = location["level_range"]
        assert 1 <= low <= high <= 30
        assert location["summary"]
        assert location["lore"]

    seen_edges = set()
    for route in ROUTES:
        assert route["a"] in LOCATIONS
        assert route["b"] in LOCATIONS
        assert route["a"] != route["b"]
        edge = frozenset((route["a"], route["b"]))
        assert edge not in seen_edges
        seen_edges.add(edge)
        assert route["hours"] > 0
        assert 1 <= route["danger"] <= 10


def test_every_world_node_is_connected_to_muckford():
    reached = {"muckford"}
    frontier = ["muckford"]
    while frontier:
        current = frontier.pop()
        for neighbor in get_neighbors(current):
            if neighbor not in reached:
                reached.add(neighbor)
                frontier.append(neighbor)
    assert reached == set(LOCATIONS)


def test_arena_circuits_match_level_bands_and_location_tiers():
    assert set(ARENA_CIRCUITS) == set(range(6))
    for tier, circuit in ARENA_CIRCUITS.items():
        assert tuple(circuit["level_range"]) == ARENA_LEVEL_BANDS[tier]
        assert circuit["locations"]
        for location_id in circuit["locations"]:
            location = LOCATIONS[location_id]
            assert location["arena_tier"] == tier
            assert location["arena_name"]


def test_new_world_state_starts_in_muckford_with_known_rumor_routes():
    manager = DummyManager()
    state = ensure_world_state(manager)

    assert state["current_location"] == "muckford"
    assert state["visited_locations"] == ["muckford"]
    assert "muckford" in state["surveyed_locations"]
    assert {"shanty_yard", "whisper_marsh", "old_mine_road",
            "rattlebridge", "saffron_oasis", "vinehollow",
            "timbercross"}.issubset(state["discovered_locations"])
    json.dumps(manager.npc_state)


def test_league_tier_and_party_level_use_current_game_structures():
    manager = DummyManager(league_tier=4, level=18)
    manager.my_team = [DummyUnit(20), DummyUnit(17), DummyUnit(16),
                       DummyUnit(15), DummyUnit(2), DummyUnit(30)]

    assert league_lore_tier(manager) == 3
    # Top five levels are 30, 20, 18, 17 and 16.
    assert party_level(manager) == 20


def test_local_travel_advances_world_clock_and_writes_history():
    manager = DummyManager(level=1)
    status = location_status(manager, "whisper_marsh")
    assert status["can_travel"]

    ok, message, target = travel_to(manager, "whisper_marsh")

    assert ok
    assert target == "forest_excursion"
    assert "Whisper Marsh" in message
    assert manager.world_clock.minutes == 12 * 60
    state = manager.npc_state["world_progression"]
    assert state["current_location"] == "whisper_marsh"
    assert state["visited_locations"][-1] == "whisper_marsh"
    assert state["travel_history"][-1] == {
        "from": "muckford",
        "to": "whisper_marsh",
        "hours": 4,
        "danger": 2,
        "route": "Whisper track",
    }


def test_level_is_a_warning_but_arena_tier_is_a_hard_gate():
    manager = DummyManager(league_tier=1, level=1)
    locked = location_status(manager, "rattlebridge")
    assert not locked["can_travel"]
    assert "Requires Arena Tier 1" in locked["reason"]

    manager.league_engine.tier = 2
    unlocked = location_status(manager, "rattlebridge")
    assert unlocked["can_travel"]
    assert "Danger:" in unlocked["warning"]
    assert "Danger:" in unlocked["reason"]


def test_reputation_and_story_keys_gate_routes():
    manager = DummyManager(reputation=0)

    oasis = location_status(manager, "saffron_oasis")
    assert not oasis["can_travel"]
    assert "Requires 10 reputation" in oasis["reason"]
    manager.reputation = 10
    assert location_status(manager, "saffron_oasis")["can_travel"]

    mine = location_status(manager, "old_mine_road")
    assert not mine["can_travel"]
    assert "Marda" in mine["reason"]
    manager.mine_key_owned = True
    assert location_status(manager, "old_mine_road")["can_travel"]


def test_surveying_reveals_connected_next_step_routes():
    manager = DummyManager(league_tier=2, level=8)
    ok, _message, target = travel_to(manager, "rattlebridge")
    assert ok and target == "regional_staging"

    state = manager.npc_state["world_progression"]
    assert "rivet_row" not in state["discovered_locations"]
    revealed = survey_location(manager, "rattlebridge")

    assert "rivet_row" in revealed
    assert "giltgate" in revealed
    assert "sanctum_marches" in revealed
    assert "rattlebridge" in state["surveyed_locations"]


def test_travel_is_node_by_node_not_global_teleportation():
    manager = DummyManager(league_tier=5, level=24, reputation=200)
    direct = location_status(manager, "crownhold")
    assert not direct["can_travel"]
    assert direct["route"] is None
    assert "node by node" in direct["reason"]
    assert get_route("muckford", "crownhold") is None


def test_future_and_vortex_nodes_cannot_skip_content_order():
    manager = DummyManager(league_tier=6, level=30, reputation=500)
    state = ensure_world_state(manager)
    state["current_location"] = "sundered_ruins"
    state["discovered_locations"].extend(
        location_id for location_id in (
            "outer_shatterbelt", "spiral_scar", "the_throat", "the_eye"
        ) if location_id not in state["discovered_locations"]
    )

    outer = location_status(manager, "outer_shatterbelt")
    assert outer["can_travel"]

    # The deeper rings exist in the graph, but are explicitly future content
    # and also require visiting the preceding ring.
    spiral = location_status(manager, "spiral_scar")
    assert not spiral["can_travel"]
    assert "not secured yet" in spiral["reason"]


def test_arena_access_requires_exact_registered_circuit():
    manager = DummyManager(league_tier=2, level=8)
    ok, reason = arena_access_status(manager, "rattlebridge")
    assert ok
    assert "Scrapring" in reason

    ok, reason = arena_access_status(manager, "giltgate")
    assert not ok
    assert "hosts Tier 2" in reason


def test_world_progress_summary_is_save_safe():
    manager = DummyManager(league_tier=3, level=13, reputation=44)
    summary = world_progress_summary(manager)
    assert summary["current_location"] == "muckford"
    assert summary["total_locations"] == 36
    assert summary["league_tier"] == 2
    assert summary["party_level"] == 13
    assert summary["reputation"] == 44
    json.dumps(summary)
    json.dumps(manager.npc_state)
