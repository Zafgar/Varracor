import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from lore.tier0_world_plan import (
    CONTENT_DOMAINS,
    CURRENT_FOCUS,
    TIER0_AREAS,
    completion_ratio,
    next_development_batch,
    validate_plan,
)
from systems.tier0_world_tracker import (
    ensure_tier0_state,
    mark_tier0_event,
    next_player_objectives,
    tier0_area_advice,
    tier0_phase,
)


class Commander:
    def __init__(self, level=1):
        self.level = level


class DummyManager:
    def __init__(self, level=1):
        self.npc_state = {"global": {"flags": {}, "deeds": []}}
        self.player_character = Commander(level)
        self.mine_key_owned = False


def test_plan_is_complete_structurally_and_acyclic():
    assert validate_plan() == []
    assert CURRENT_FOCUS == "whisper_marsh"
    assert list(TIER0_AREAS) == [
        "muckford",
        "low_fields",
        "whisper_marsh",
        "drowned_chapel",
        "old_muckford_mine",
        "muckford_warrens",
        "greywash_ford",
        "kingsreach_toll",
        "tier0_finale",
        "rattlebridge_handoff",
    ]
    for area in TIER0_AREAS.values():
        assert set(area["deliverables"]) == set(CONTENT_DOMAINS)
        assert area["graphics"]
        assert area["vfx"]


def test_development_queue_advances_to_whisper_marsh_and_keeps_partial_work_visible():
    queue = next_development_batch(20)
    assert queue
    assert queue[0]["area_id"] == "whisper_marsh"
    assert queue[0]["domain"] in {"npcs", "dialogue"}
    assert any(task["state"] == "partial" for task in queue)
    assert completion_ratio("muckford") == 1.0
    assert completion_ratio("low_fields") > 0.8
    assert 0.0 < completion_ratio("whisper_marsh") < 1.0


def test_open_risk_area_warns_but_does_not_block_entry():
    manager = DummyManager(level=1)
    advice = tier0_area_advice(manager, "greywash_ford")
    assert advice["risk"] == "SEVERE"
    assert "recommended Lv 5-7" in advice["warning"]
    assert advice["blocked_by_policy"] is False
    assert advice["access_policy"] == "open_with_warning"


def test_physical_and_formal_gates_are_explicit_and_state_driven():
    manager = DummyManager(level=5)

    mine = tier0_area_advice(manager, "old_muckford_mine")
    assert mine["blocked_by_policy"] is True
    assert "mine key" in mine["reason"].lower()

    manager.mine_key_owned = True
    mine = tier0_area_advice(manager, "old_muckford_mine")
    assert mine["blocked_by_policy"] is False

    toll = tier0_area_advice(manager, "kingsreach_toll")
    assert toll["blocked_by_policy"] is True
    mark_tier0_event(manager, "flag", "kingsreach_access")
    toll = tier0_area_advice(manager, "kingsreach_toll")
    assert toll["blocked_by_policy"] is False

    bridge = tier0_area_advice(manager, "rattlebridge_handoff")
    assert bridge["blocked_by_policy"] is True
    mark_tier0_event(manager, "flag", "tier1_promoted")
    bridge = tier0_area_advice(manager, "rattlebridge_handoff")
    assert bridge["blocked_by_policy"] is False


def test_tracker_migrates_existing_muckford_and_whisper_marsh_progress():
    manager = DummyManager(level=3)
    manager.npc_state["global"]["muckford_opening"] = {
        "team_registered": True,
        "intro_complete": True,
    }
    manager.npc_state["global"]["muckford_outskirts"] = {
        "visits": 4,
        "camp_stage": 2,
        "fishing_ready": True,
    }
    manager.mine_key_owned = True

    state = ensure_tier0_state(manager)
    assert state["story_flags"]["team_registered"] is True
    assert state["story_flags"]["forest_road_complete"] is True
    assert state["story_flags"]["whisper_marsh_fishing_ready"] is True
    assert state["story_flags"]["mine_key_owned"] is True
    assert "whisper_marsh" in state["visited_areas"]
    assert "survey_post_stage_1" in state["built_projects"]
    assert "survey_post_stage_2" in state["built_projects"]
    assert tier0_phase(manager) == 2


def test_player_phase_and_objectives_advance_without_optional_area_locks():
    manager = DummyManager(level=5)
    assert tier0_phase(manager) == 0
    assert "Register" in " ".join(next_player_objectives(manager))

    mark_tier0_event(manager, "flag", "team_registered")
    assert tier0_phase(manager) == 1

    mark_tier0_event(manager, "project", "survey_post_stage_1")
    assert tier0_phase(manager) == 2

    mark_tier0_event(manager, "boss", "bell_drowned_pilgrim")
    assert tier0_phase(manager) == 3

    mark_tier0_event(manager, "boss", "cave_broodmother")
    assert tier0_phase(manager) == 4

    mark_tier0_event(manager, "boss", "rat_king")
    assert tier0_phase(manager) == 5

    mark_tier0_event(manager, "quest", "greywash_ford_secured")
    assert tier0_phase(manager) == 6

    mark_tier0_event(manager, "flag", "kingsreach_cleared")
    assert tier0_phase(manager) == 7

    mark_tier0_event(manager, "flag", "tier1_promoted")
    assert tier0_phase(manager) == 8

    mark_tier0_event(manager, "flag", "rattlebridge_arrived")
    assert tier0_phase(manager) == 9
