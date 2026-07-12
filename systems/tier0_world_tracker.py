"""Persistent player-facing progress for Muckford's Tier 0 world.

Development state lives in ``lore.tier0_world_plan``. This module stores only
what the player has done: visited areas, completed quests, defeated bosses,
constructed projects and acknowledged danger warnings. It is deliberately
save-compatible by using manager.npc_state.
"""
from __future__ import annotations

from typing import Iterable

from lore.tier0_world_plan import TIER0_AREAS


STATE_KEY = "tier0_world"
STATE_VERSION = 1


def _unique_strings(values: Iterable | None) -> list[str]:
    result = []
    for value in values or ():
        value = str(value)
        if value not in result:
            result.append(value)
    return result


def ensure_tier0_state(manager) -> dict:
    npc_state = getattr(manager, "npc_state", None)
    if not isinstance(npc_state, dict):
        manager.npc_state = {"global": {"reputation": 0, "flags": {}, "deeds": []}}
        npc_state = manager.npc_state

    state = npc_state.setdefault(STATE_KEY, {})
    if not isinstance(state, dict):
        state = {}
        npc_state[STATE_KEY] = state

    state["version"] = STATE_VERSION
    state["visited_areas"] = _unique_strings(state.get("visited_areas"))
    state["completed_quests"] = _unique_strings(state.get("completed_quests"))
    state["defeated_bosses"] = _unique_strings(state.get("defeated_bosses"))
    state["built_projects"] = _unique_strings(state.get("built_projects"))
    state["risk_warnings_seen"] = _unique_strings(state.get("risk_warnings_seen"))
    state["story_flags"] = dict(state.get("story_flags") or {})
    state["area_counters"] = dict(state.get("area_counters") or {})
    if "muckford" not in state["visited_areas"]:
        state["visited_areas"].append("muckford")
    return state


def mark_tier0_event(manager, event_type: str, value: str, *, amount: int = 1) -> dict:
    state = ensure_tier0_state(manager)
    value = str(value)
    mapping = {
        "visit": "visited_areas",
        "quest": "completed_quests",
        "boss": "defeated_bosses",
        "project": "built_projects",
        "risk_seen": "risk_warnings_seen",
    }
    if event_type in mapping:
        bucket = state[mapping[event_type]]
        if value not in bucket:
            bucket.append(value)
    elif event_type == "flag":
        state["story_flags"][value] = True
    elif event_type == "counter":
        counters = state["area_counters"]
        counters[value] = int(counters.get(value, 0)) + int(amount)
    else:
        raise ValueError(f"Unknown Tier 0 event type: {event_type}")
    return state


def tier0_area_advice(manager, area_id: str) -> dict:
    area_id = str(area_id)
    if area_id not in TIER0_AREAS:
        raise KeyError(f"Unknown Tier 0 area: {area_id}")
    area = TIER0_AREAS[area_id]
    commander = getattr(manager, "player_character", None)
    level = max(1, int(getattr(commander, "level", 1) or 1))
    low, high = area["level_range"]

    warning = ""
    risk = "LOW"
    if level < low:
        risk = "SEVERE"
        warning = (
            f"Open route, severe risk: Commander Lv {level}; "
            f"recommended Lv {low}-{high}."
        )
    elif level == low:
        risk = "HIGH"
        warning = f"Open route, high risk at the lower edge of Lv {low}-{high}."
    elif level <= high:
        risk = "MATCHED"
        warning = f"Recommended danger band: Lv {low}-{high}."
    else:
        warning = f"Below your current level; recommended Lv {low}-{high}."

    blocked = False
    reason = warning
    policy = area["access_policy"]
    if policy in {"physical_gate", "formal_gate", "tier1_gate"}:
        blocked = True
        reason = area["physical_gate"] or "A specific progression obstacle blocks entry."

    return {
        "area_id": area_id,
        "name": area["name"],
        "recommended_level": area["level_range"],
        "access_policy": policy,
        "risk": risk,
        "warning": warning,
        "blocked_by_policy": blocked,
        "reason": reason,
    }


def tier0_phase(manager) -> int:
    """Return a broad player phase without hard-locking optional areas."""
    state = ensure_tier0_state(manager)
    quests = set(state["completed_quests"])
    bosses = set(state["defeated_bosses"])
    flags = state["story_flags"]

    if flags.get("rattlebridge_arrived"):
        return 9
    if flags.get("tier1_promoted"):
        return 8
    if flags.get("kingsreach_cleared"):
        return 7
    if "greywash_ford_secured" in quests:
        return 6
    if "rat_king" in bosses:
        return 5
    if "cave_broodmother" in bosses:
        return 4
    if "bell_drowned_pilgrim" in bosses:
        return 3
    if "survey_post_stage_1" in state["built_projects"]:
        return 2
    if flags.get("team_registered"):
        return 1
    return 0


def next_player_objectives(manager, limit: int = 4) -> list[str]:
    state = ensure_tier0_state(manager)
    phase = tier0_phase(manager)
    objectives = {
        0: (
            "Pay Marda's debt and earn local reputation.",
            "Help Farmer Gus and gather supplies around Muckford.",
            "Register and name the first official arena team.",
        ),
        1: (
            "Work in the Low Fields and repair the first local projects.",
            "Explore Whisper Marsh and build the Survey Post shelter.",
            "Begin Rookie Dust Circuit matches at Shanty Yard.",
        ),
        2: (
            "Complete the Whisper Marsh survey and investigate the Drowned Chapel.",
            "Gather materials for the Survey Post boardwalk and tackle bench.",
            "Prepare for the Old Muckford Mine and deeper Tier 0 hunts.",
        ),
        3: (
            "Resolve the Drowned Chapel crisis with Sister-Medic Rhea.",
            "Enter the Old Muckford Mine after obtaining Marda's key.",
        ),
        4: (
            "Clear the Webbed Depths and begin restoring the mine.",
            "Follow Hamo's reports of violet-eyed rats beneath Muckford.",
        ),
        5: (
            "Secure Greywash Ford and prepare the western causeway.",
            "Finish the Rookie Dust Circuit and earn Bram's recommendation.",
        ),
        6: (
            "Escort a caravan across Greywash Ford.",
            "Reach Kingsreach Toll and obtain valid Crown travel papers.",
        ),
        7: (
            "Complete the Tier 0 finale and receive formal promotion.",
            "Meet Sera Quench's representative for the Scrapring Circuit.",
        ),
        8: ("Travel through Kingsreach Toll and enter Rattlebridge.",),
        9: ("Register with the Tier 1 Scrapring Circuit.",),
    }
    completed = set(state["completed_quests"])
    result = []
    for objective in objectives.get(phase, ()):
        key = objective.lower().replace(" ", "_")
        if key not in completed:
            result.append(objective)
    return result[:max(0, int(limit))]
