"""Persistent discovery, travel and level-gating logic for Varrakor's map.

State is stored inside ``manager.npc_state['world_progression']`` so the
existing save system persists it without a save-format break.
"""

from __future__ import annotations

from typing import Iterable

from lore.world_map_data import (
    ARENA_CIRCUITS,
    LOCATIONS,
    ROUTES,
    STARTING_DISCOVERED_LOCATIONS,
    get_location,
    get_neighbors,
    get_route,
)


WORLD_STATE_VERSION = 2
WORLD_STATE_KEY = "world_progression"


def _append_unique(values: list, value) -> bool:
    if value in values:
        return False
    values.append(value)
    return True


def route_key(a: str, b: str) -> str:
    """Return a stable JSON-safe identifier for an undirected route."""
    return "|".join(sorted((str(a), str(b))))


VALID_ROUTE_KEYS = {
    route_key(route["a"], route["b"])
    for route in ROUTES
}


def _normalise_id_list(value: Iterable | None) -> list[str]:
    out = []
    for item in value or ():
        item = str(item)
        if item in LOCATIONS and item not in out:
            out.append(item)
    return out


def _normalise_route_list(value: Iterable | None) -> list[str]:
    out = []
    for item in value or ():
        item = str(item)
        if item in VALID_ROUTE_KEYS and item not in out:
            out.append(item)
    return out


def ensure_world_state(manager) -> dict:
    npc_state = getattr(manager, "npc_state", None)
    if not isinstance(npc_state, dict):
        manager.npc_state = {
            "global": {"reputation": 0, "flags": {}, "deeds": []}
        }
        npc_state = manager.npc_state

    state = npc_state.setdefault(WORLD_STATE_KEY, {})
    if not isinstance(state, dict):
        state = {}
        npc_state[WORLD_STATE_KEY] = state

    current = str(state.get("current_location", "muckford"))
    if current not in LOCATIONS:
        current = "muckford"

    discovered = _normalise_id_list(state.get("discovered_locations"))
    visited = _normalise_id_list(state.get("visited_locations"))
    surveyed = _normalise_id_list(state.get("surveyed_locations"))
    discovered_routes = _normalise_route_list(state.get("discovered_routes"))

    if not discovered:
        discovered = list(STARTING_DISCOVERED_LOCATIONS)
    else:
        for location_id in STARTING_DISCOVERED_LOCATIONS:
            _append_unique(discovered, location_id)

    _append_unique(discovered, current)
    if not visited:
        visited = ["muckford"]
    _append_unique(visited, current)

    # Bram, Hamo and Muckford's caravan brokers provide the first local map.
    if not surveyed:
        surveyed = ["muckford"]
    else:
        _append_unique(surveyed, "muckford")

    state["version"] = WORLD_STATE_VERSION
    state["current_location"] = current
    state["discovered_locations"] = discovered
    state["visited_locations"] = visited
    state["surveyed_locations"] = surveyed
    state["discovered_routes"] = discovered_routes

    history = state.get("travel_history")
    state["travel_history"] = history if isinstance(history, list) else []
    notices = state.get("unlock_notices")
    state["unlock_notices"] = notices if isinstance(notices, list) else []
    links = state.get("fast_travel_links")
    state["fast_travel_links"] = links if isinstance(links, list) else []
    return state


# ----------------------------------------------------------------------
# Fast travel
# ----------------------------------------------------------------------
# Ensivierailu kaupunkiin avaa pysyvän nopean reitin (lore: paikallinen
# sponsori/liitto operoi linjaa). Data-ohjattu tulevia kaupunkeja varten.
FAST_TRAVEL_UNLOCKS = {
    "rattlebridge": {
        "between": ("muckford", "rattlebridge"),
        "label": "Ironspan Union freight wagon",
        "hours": 6,
        "notice": ("The Ironspan Union opens its freight line: fast travel "
                   "between Muckford and Rattlebridge."),
    },
}


def has_fast_travel(manager, a: str, b: str) -> bool:
    state = ensure_world_state(manager)
    return route_key(a, b) in state["fast_travel_links"]


def unlock_fast_travel(manager, a: str, b: str) -> bool:
    """Avaa pysyvän fast travel -linkin. True jos linkki oli uusi."""
    state = ensure_world_state(manager)
    return _append_unique(state["fast_travel_links"], route_key(a, b))


def _fast_travel_route(manager, current: str, location_id: str):
    """Synteettinen reitti fast travel -linkille (tai None)."""
    if not has_fast_travel(manager, current, location_id):
        return None
    for spec in FAST_TRAVEL_UNLOCKS.values():
        if {current, location_id} == set(spec["between"]):
            return {"a": current, "b": location_id,
                    "hours": int(spec.get("hours", 6)), "danger": 1,
                    "label": spec["label"]}
    return {"a": current, "b": location_id, "hours": 6, "danger": 1,
            "label": "fast caravan"}


def league_lore_tier(manager) -> int:
    engine = getattr(manager, "league_engine", None)
    game_tier = getattr(engine, "tier", None)
    if game_tier is None:
        game_tier = getattr(manager, "league_level", 1)
    return max(0, min(5, int(game_tier or 1) - 1))


def party_level(manager) -> int:
    units = []
    commander = getattr(manager, "player_character", None)
    if commander is not None:
        units.append(commander)
    try:
        units.extend(list(getattr(manager, "my_team", ())))
    except Exception:
        pass

    levels = sorted(
        (
            max(1, int(getattr(unit, "level", 1) or 1))
            for unit in units
            if unit
        ),
        reverse=True,
    )
    if not levels:
        return 1
    active = levels[:5]
    return max(1, int(round(sum(active) / len(active))))


def _reputation(manager) -> int:
    return int(getattr(manager, "reputation", 0) or 0)


def _requirement_attr_met(manager, requirement) -> bool:
    if not requirement:
        return True
    attr, expected = requirement
    return getattr(manager, str(attr), None) == expected


def _route_reveal_allowed(manager, destination_id: str) -> bool:
    destination = LOCATIONS[destination_id]
    return int(destination.get("reveal_tier", 0)) <= league_lore_tier(manager) + 1


def refresh_world_progression(manager) -> dict:
    """Reveal circuit goals and roads from locations the player surveyed."""
    state = ensure_world_state(manager)
    tier = league_lore_tier(manager)
    discovered = state["discovered_locations"]
    surveyed = state["surveyed_locations"]
    discovered_routes = state["discovered_routes"]

    before_locations = set(discovered)
    before_routes = set(discovered_routes)

    # Promotion reveals arena-city names as rumors, but not their roads.
    for circuit_tier in range(0, min(5, tier) + 1):
        for location_id in ARENA_CIRCUITS[circuit_tier]["locations"]:
            _append_unique(discovered, location_id)

    # Major landmarks may also be known by rumor before a safe route exists.
    for location_id, location in LOCATIONS.items():
        if (
            location.get("landmark")
            and int(location.get("reveal_tier", 0)) <= tier
        ):
            _append_unique(discovered, location_id)

    # Surveying opens physical roads. A road may lead to a destination one tier
    # ahead so the next progression goal can be seen while remaining gated.
    for origin in list(dict.fromkeys(surveyed)):
        for neighbor in get_neighbors(origin):
            if not _route_reveal_allowed(manager, neighbor):
                continue
            _append_unique(discovered, neighbor)
            _append_unique(discovered_routes, route_key(origin, neighbor))

    newly_revealed_locations = [
        location_id
        for location_id in discovered
        if location_id not in before_locations
    ]
    newly_revealed_routes = [
        key
        for key in discovered_routes
        if key not in before_routes
    ]
    if newly_revealed_locations or newly_revealed_routes:
        state["unlock_notices"].append({
            "tier": tier,
            "locations": newly_revealed_locations,
            "routes": newly_revealed_routes,
        })
        state["unlock_notices"] = state["unlock_notices"][-20:]
    return state


def current_location_id(manager) -> str:
    return str(refresh_world_progression(manager)["current_location"])


def mark_location_visited(
    manager,
    location_id: str,
    *,
    set_current=True,
    surveyed=False,
) -> dict:
    location_id = str(location_id)
    if location_id not in LOCATIONS:
        raise KeyError(f"Unknown world location: {location_id}")
    state = ensure_world_state(manager)
    first_visit = location_id not in state["visited_locations"]
    _append_unique(state["discovered_locations"], location_id)
    _append_unique(state["visited_locations"], location_id)
    if surveyed:
        _append_unique(state["surveyed_locations"], location_id)
    if set_current:
        state["current_location"] = location_id
    # Ensivierailu avaa kaupungin fast travel -linjan (sponsorin operoima).
    spec = FAST_TRAVEL_UNLOCKS.get(location_id)
    if spec and first_visit:
        if unlock_fast_travel(manager, *spec["between"]):
            manager.pending_fast_travel_notice = spec["notice"]
    return refresh_world_progression(manager)


def survey_location(manager, location_id: str) -> list[str]:
    """Survey a reached node and return destinations whose roads were opened."""
    location_id = str(location_id)
    state = ensure_world_state(manager)
    before_routes = set(state["discovered_routes"])

    state = mark_location_visited(
        manager,
        location_id,
        set_current=True,
        surveyed=True,
    )

    opened = []
    for neighbor in get_neighbors(location_id):
        key = route_key(location_id, neighbor)
        if key in state["discovered_routes"] and key not in before_routes:
            opened.append(neighbor)
    return opened


def is_route_discovered(manager, a: str, b: str) -> bool:
    state = refresh_world_progression(manager)
    return route_key(a, b) in state["discovered_routes"]


def location_status(manager, location_id: str) -> dict:
    state = refresh_world_progression(manager)
    location_id = str(location_id)
    location = get_location(location_id)
    if not location:
        return {
            "discovered": False,
            "can_travel": False,
            "reason": "Unknown location.",
            "warning": "",
            "route": None,
            "route_discovered": False,
        }

    discovered = location_id in state["discovered_locations"]
    current = state["current_location"]
    route = get_route(current, location_id)
    route_discovered = bool(
        route and route_key(current, location_id) in state["discovered_routes"]
    )
    if route is None:
        # Avattu fast travel -linja korvaa puuttuvan suoran tien.
        fast = _fast_travel_route(manager, current, location_id)
        if fast is not None:
            route = fast
            route_discovered = True
    tier = league_lore_tier(manager)
    rep = _reputation(manager)
    level = party_level(manager)
    low, high = location["level_range"]

    warning = ""
    if level < low:
        warning = (
            f"Danger: party average Lv {level}; recommended Lv {low}-{high}."
        )
    elif level > high + 5:
        warning = f"Low-level region for your Lv {level} party."

    result = {
        "discovered": discovered,
        "visited": location_id in state["visited_locations"],
        "surveyed": location_id in state["surveyed_locations"],
        "current": location_id == current,
        "can_travel": False,
        "reason": "",
        "warning": warning,
        "route": route,
        "route_discovered": route_discovered,
        "party_level": level,
        "league_tier": tier,
    }

    if not discovered:
        result["reason"] = (
            "The location has not been discovered. Survey connected areas first."
        )
        return result
    if location_id == current:
        result["reason"] = "Your expedition is currently here."
        return result
    if route is None:
        result["reason"] = (
            "No direct route from your current location. Travel node by node."
        )
        return result
    if not route_discovered:
        result["reason"] = (
            "The destination is known, but this road has not been surveyed."
        )
        return result
    if location.get("content_state") == "future":
        result["reason"] = (
            "This region is mapped in the world foundation but its local "
            "playable area is not secured yet."
        )
        return result

    required_tier = int(location.get("required_tier", 0))
    if tier < required_tier:
        result["reason"] = (
            f"Requires Arena Tier {required_tier}; current tier is {tier}."
        )
        return result

    required_rep = int(location.get("required_rep", 0))
    if rep < required_rep:
        result["reason"] = (
            f"Requires {required_rep} reputation; current reputation is {rep}."
        )
        return result

    if not _requirement_attr_met(
        manager,
        location.get("requires_manager_attr"),
    ):
        attr, expected = location["requires_manager_attr"]
        if attr == "mine_key_owned":
            result["reason"] = (
                "The mine road is locked. Marda holds the key until the debt "
                "is settled."
            )
        else:
            result["reason"] = f"Requires {attr} = {expected}."
        return result

    missing = [
        requirement
        for requirement in location.get("requires_visited", ())
        if requirement not in state["visited_locations"]
    ]
    if missing:
        names = ", ".join(LOCATIONS[item]["name"] for item in missing)
        result["reason"] = f"Reach and survey {names} first."
        return result

    result["can_travel"] = True
    if warning:
        result["reason"] = warning
    else:
        result["reason"] = (
            f"Direct route: {route['label']} ({route['hours']} travel hours)."
        )
    return result


def _advance_travel_time(manager, hours: int) -> None:
    clock = getattr(manager, "world_clock", None)
    if clock is None:
        return
    clock.minutes += float(hours) * 60.0
    while clock.minutes >= 1440.0:
        clock.minutes -= 1440.0
        clock.advance_day()


def travel_to(manager, location_id: str):
    """Attempt travel and return ``(ok, message, target_state)``."""
    location_id = str(location_id)
    status = location_status(manager, location_id)
    if not status["can_travel"]:
        return False, status["reason"], None

    state = ensure_world_state(manager)
    origin = state["current_location"]
    route = status["route"]
    _advance_travel_time(manager, route["hours"])

    state["current_location"] = location_id
    _append_unique(state["discovered_locations"], location_id)
    _append_unique(state["visited_locations"], location_id)
    state["travel_history"].append({
        "from": origin,
        "to": location_id,
        "hours": int(route["hours"]),
        "danger": int(route["danger"]),
        "route": route["label"],
    })
    state["travel_history"] = state["travel_history"][-50:]
    manager.pending_world_location = location_id
    refresh_world_progression(manager)

    location = LOCATIONS[location_id]
    target_state = location.get("target_state") or "regional_staging"
    return True, (
        f"Travelled to {location['name']} by {route['label']} "
        f"({route['hours']} hours)."
    ), target_state


def arena_access_status(manager, location_id: str) -> tuple[bool, str]:
    location = get_location(location_id)
    if not location or location.get("arena_tier") is None:
        return False, "No registered arena circuit at this location."
    current_tier = league_lore_tier(manager)
    arena_tier = int(location["arena_tier"])
    if current_tier != arena_tier:
        return False, (
            f"This arena hosts Tier {arena_tier}; your registered circuit is "
            f"Tier {current_tier}."
        )
    return True, f"Enter {location['arena_name']}."


def world_progress_summary(manager) -> dict:
    state = refresh_world_progression(manager)
    return {
        "current_location": state["current_location"],
        "discovered": len(state["discovered_locations"]),
        "visited": len(state["visited_locations"]),
        "surveyed": len(state["surveyed_locations"]),
        "discovered_routes": len(state["discovered_routes"]),
        "total_locations": len(LOCATIONS),
        "total_routes": len(ROUTES),
        "party_level": party_level(manager),
        "league_tier": league_lore_tier(manager),
        "reputation": _reputation(manager),
    }
