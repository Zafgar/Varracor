"""Tier 0 finale state, requirements and branch-aware farewell content."""
from __future__ import annotations

from typing import Dict, List, Tuple


STATE_KEY = "tier0_finale"
FINAL_REWARD_SP = 250
MAJOR_CRISIS_BOSSES = (
    "rat_king",
    "cave_broodmother",
    "bell_drowned_pilgrim",
    "whisper_pool_maw",
)


def ensure_finale_state(manager) -> dict:
    global_data = manager.npc_state.setdefault("global", {})
    state = global_data.setdefault(STATE_KEY, {})
    state.setdefault("docket_returned", False)
    state.setdefault("docket_return_dialogue_seen", False)
    state.setdefault("promotion_match_unlocked", False)
    state.setdefault("promotion_won", False)
    state.setdefault("ceremony_started", False)
    state.setdefault("ceremony_complete", False)
    state.setdefault("farewell_pages_seen", 0)
    state.setdefault("rewards_claimed", False)
    state.setdefault("departure_ready", False)
    state.setdefault("major_crisis", "")
    state.setdefault("kingsreach_resolution", "")
    state.setdefault("reward_sp", 0)
    return state


def finale_state_from_memory(memory: dict) -> dict:
    global_data = (memory or {}).setdefault("global", {})
    state = global_data.setdefault(STATE_KEY, {})
    defaults = {
        "docket_returned": False,
        "docket_return_dialogue_seen": False,
        "promotion_match_unlocked": False,
        "promotion_won": False,
        "ceremony_started": False,
        "ceremony_complete": False,
        "farewell_pages_seen": 0,
        "rewards_claimed": False,
        "departure_ready": False,
        "major_crisis": "",
        "kingsreach_resolution": "",
        "reward_sp": 0,
    }
    for key, value in defaults.items():
        state.setdefault(key, value)
    return state


def _tier0_state(manager) -> dict:
    try:
        from systems.tier0_world_tracker import ensure_tier0_state

        return ensure_tier0_state(manager)
    except Exception:
        state = manager.npc_state.setdefault("tier0_world", {})
        state.setdefault("story_flags", {})
        state.setdefault("completed_quests", [])
        state.setdefault("defeated_bosses", [])
        state.setdefault("built_projects", [])
        return state


def _kingsreach_state(manager) -> dict:
    return manager.npc_state.setdefault("global", {}).setdefault("kingsreach_toll", {})


def major_crisis(manager) -> str:
    defeated = set(_tier0_state(manager).get("defeated_bosses", ()))
    aliases = {
        "rat_king": "Rat King of Muckford",
        "cave_broodmother": "Cave Broodmother",
        "bell_drowned_pilgrim": "Bell-Drowned Pilgrim",
        "whisper_pool_maw": "Whisper Pool Maw",
    }
    for boss_id in MAJOR_CRISIS_BOSSES:
        if boss_id in defeated:
            return aliases[boss_id]
    # Existing saves may retain boss completion in area-local state only.
    global_data = manager.npc_state.setdefault("global", {})
    local_checks = (
        ("muckford_warrens", "boss_defeated", "Rat King of Muckford"),
        ("old_muckford_mine", "boss_defeated", "Cave Broodmother"),
        ("drowned_chapel", "boss_defeated", "Bell-Drowned Pilgrim"),
        ("whisper_marsh_story", "boss_defeated", "Whisper Pool Maw"),
    )
    for key, flag, label in local_checks:
        if bool((global_data.get(key) or {}).get(flag)):
            return label
    return ""


def kingsreach_cleared(manager) -> bool:
    flags = _tier0_state(manager).get("story_flags", {})
    state = _kingsreach_state(manager)
    return bool(flags.get("kingsreach_cleared") or state.get("completed") or state.get("pass_issued"))


def has_crown_papers(manager) -> bool:
    return int(getattr(manager, "inventory", {}).get("Stamped Crown Travel Papers", 0)) > 0


def league_promotion_status(manager) -> Tuple[bool, str, object | None]:
    engine = getattr(manager, "league_engine", None)
    if not engine:
        return False, "Bram's league ledger is unavailable.", None
    if int(getattr(engine, "tier", 1)) >= 2:
        return True, "Rookie Dust promotion already won.", None
    try:
        return engine.check_promotion_eligibility()
    except Exception:
        return False, "Complete the Rookie Dust 1v1, 3v3 and 5v5 standings.", None


def finale_requirements(manager) -> dict:
    state = ensure_finale_state(manager)
    crisis = major_crisis(manager)
    league_ok, league_reason, opponent = league_promotion_status(manager)
    requirements = {
        "kingsreach": kingsreach_cleared(manager),
        "crown_papers": has_crown_papers(manager),
        "docket_returned": bool(state.get("docket_returned")),
        "major_crisis": bool(crisis),
        "league_qualified": bool(league_ok),
    }
    state["major_crisis"] = crisis
    state["kingsreach_resolution"] = str(_kingsreach_state(manager).get("resolution", ""))
    state["promotion_match_unlocked"] = all(requirements.values())
    return {
        "requirements": requirements,
        "major_crisis": crisis,
        "league_reason": league_reason,
        "opponent": opponent,
        "ready": bool(state["promotion_match_unlocked"]),
    }


def requirement_lines(manager) -> List[str]:
    status = finale_requirements(manager)
    req = status["requirements"]
    crisis = status["major_crisis"] or "none"
    return [
        f"Kingsreach Toll cleared: {'YES' if req['kingsreach'] else 'NO'}",
        f"Stamped Crown papers: {'YES' if req['crown_papers'] else 'NO'}",
        f"Promotion Docket returned to Bram: {'YES' if req['docket_returned'] else 'NO'}",
        f"Major Muckford crisis resolved: {'YES — ' + crisis if req['major_crisis'] else 'NO'}",
        f"Rookie Dust Top 2 qualification: {'YES' if req['league_qualified'] else 'NO'}",
    ]


def promotion_lock_reason(manager) -> str:
    status = finale_requirements(manager)
    req = status["requirements"]
    if not req["kingsreach"]:
        return "Secure Greywash Ford and clear Kingsreach Toll first."
    if not req["crown_papers"]:
        return "Captain Dorn's stamped Crown travel papers are required."
    if not req["docket_returned"]:
        if int(getattr(manager, "inventory", {}).get("Crown Promotion Docket", 0)) > 0:
            return "Speak with Bram and return the Crown Promotion Docket."
        return "Obtain the Crown Promotion Docket at Kingsreach Toll."
    if not req["major_crisis"]:
        return "Resolve one major Muckford crisis before Bram risks his name."
    if not req["league_qualified"]:
        return status["league_reason"] or "Finish the Rookie Dust season in the Top 2."
    return "Promotion match ready."


def return_docket_to_bram(manager) -> Tuple[bool, str]:
    state = ensure_finale_state(manager)
    if state.get("docket_returned"):
        return True, "Bram already entered the Crown docket in his ledger."
    if not kingsreach_cleared(manager):
        return False, "Bram will not sign anything until Kingsreach Toll is cleared."
    inventory = getattr(manager, "inventory", {})
    if int(inventory.get("Crown Promotion Docket", 0)) <= 0:
        return False, "Bring Bram the Crown Promotion Docket from Captain Dorn."
    inventory["Crown Promotion Docket"] = int(inventory.get("Crown Promotion Docket", 0)) - 1
    if inventory["Crown Promotion Docket"] <= 0:
        inventory.pop("Crown Promotion Docket", None)
    state["docket_returned"] = True
    state["docket_return_dialogue_seen"] = True
    finale_requirements(manager)
    try:
        manager.record_tier0_event("flag", "bram_docket_returned")
        manager.record_deed("bram_docket", "returned Captain Dorn's Crown Promotion Docket to Bram Carrow")
    except Exception:
        pass
    return True, "Bram stamps the docket into his ledger. The final promotion conditions are now recorded."


def mark_promotion_victory(manager) -> dict:
    state = ensure_finale_state(manager)
    state["promotion_won"] = True
    state["ceremony_started"] = True
    flags = _tier0_state(manager).setdefault("story_flags", {})
    flags["tier1_promoted"] = True
    try:
        manager.record_tier0_event("flag", "tier1_promoted")
        manager.record_tier0_event("quest", "tier0_finale_won")
    except Exception:
        pass
    if not state.get("rewards_claimed"):
        inventory = getattr(manager, "inventory", {})
        inventory["Bram's Recommendation"] = max(1, int(inventory.get("Bram's Recommendation", 0)))
        inventory["Tier 1 Charter"] = max(1, int(inventory.get("Tier 1 Charter", 0)))
        inventory["Sera Quench Sponsor Letter"] = max(1, int(inventory.get("Sera Quench Sponsor Letter", 0)))
        manager.gold = int(getattr(manager, "gold", 0)) + FINAL_REWARD_SP
        manager.reputation = int(getattr(manager, "reputation", 0)) + 10
        state["reward_sp"] = FINAL_REWARD_SP
        state["rewards_claimed"] = True
        try:
            manager.record_deed(
                "tier0_promotion",
                "won the Rookie Dust promotion match and earned Bram Carrow's Tier 1 recommendation",
            )
        except Exception:
            pass
    # Keep Kingsreach's own progression synchronized.
    kingsreach = _kingsreach_state(manager)
    if int(kingsreach.get("quest_stage", 0)) < 7:
        kingsreach["quest_stage"] = 7
    return state


def farewell_pages(manager) -> List[Dict[str, str]]:
    state = ensure_finale_state(manager)
    crisis = state.get("major_crisis") or major_crisis(manager) or "the dangers around Muckford"
    route = state.get("kingsreach_resolution") or str(_kingsreach_state(manager).get("resolution", ""))
    route_lines = {
        "official_evidence": "Dorn accepted Garran Vale's own evidence. Even Crown ink had to admit what you uncovered.",
        "paid": "You paid Crown law in silver and kept the road clean. Expensive, but difficult to dispute.",
        "quarantine_service": "You earned the road by serving the quarantine tents. The checkpoint remembers that.",
        "smuggling": "You crawled through Nix's culvert and broke Crowl's private toll ring. Crown officials will argue about it for years.",
    }
    pages = [
        {
            "speaker": "Bram 'Mudhand' Carrow",
            "text": "The ledger is closed. You came to me owing mud, blood and silver. Now the Rookie Dust Circuit owes you a road upward.",
        },
        {
            "speaker": "Bram 'Mudhand' Carrow",
            "text": f"You survived {crisis}, cleared Kingsreach and won when the whole Yard was counting. My recommendation is not charity. You earned every line.",
        },
        {
            "speaker": "Marda Shant",
            "text": "I dragged you in half-dead and put the cost in my book. Look at you now. Rattlebridge charges more for a bed, so try not to arrive unconscious.",
        },
        {
            "speaker": "Hamo",
            "text": "Big bridge, bigger bounties, shinier seals. Do not forget who taught you that every monster has a price if you keep the useful pieces.",
        },
        {
            "speaker": "Sera Quench's Representative",
            "text": route_lines.get(route, "Your Crown papers are valid and Bram's recommendation is recognized. The Scrapring Circuit will receive your team."),
        },
        {
            "speaker": "Muckford Crowd",
            "text": "Mudhand's team! Mudhand's team! Bring the bridge-city a little Muckford dirt!",
        },
        {
            "speaker": "Bram 'Mudhand' Carrow",
            "text": f"Take the Tier 1 Charter, the sponsor letter and {FINAL_REWARD_SP} SP. The western road is open. Next stop: Rattlebridge.",
        },
    ]
    return pages


def complete_ceremony(manager) -> dict:
    state = mark_promotion_victory(manager)
    state["ceremony_complete"] = True
    state["departure_ready"] = True
    flags = _tier0_state(manager).setdefault("story_flags", {})
    flags["tier0_finale_complete"] = True
    flags["rattlebridge_road_open"] = True
    try:
        manager.record_tier0_event("flag", "tier0_finale_complete")
        manager.record_tier0_event("flag", "rattlebridge_road_open")
    except Exception:
        pass
    return state
