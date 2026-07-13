"""Sponsor-objectivet Tier 1 -liigamatseihin (The Scrapring).

Sera myy tarinoita: voitto maksaa palkkion, mutta ESITYS rakentaa brändin.
Jokaiseen Rattlebridgen liigamatsiin arvotaan kiertävä sponsoritavoite.
Tavoitteen täyttäminen voitossa maksaa bonuksen, antaa mainetta ja
kasvattaa KAIKKIEN allekirjoitettujen sponsorien kärsivällisyyttä
("presentation builds the brand").

Kaikki logiikka on UI-vapaata ja testattavaa. Tila:
  manager.current_match_objective  - aktiivinen tavoite (dict) tai None
  manager.last_objective_result    - viimeisin tulos (dict) tai None
  npc_state['rattlebridge']['objective_history'] - viimeiset 20 tulosta
"""

from __future__ import annotations

import random

OBJECTIVE_GOLD = 40
OBJECTIVE_REP = 3


def _check_clean_sweep(ctx):
    return not any(f.get("dead") for f in ctx["fighters"])


def _check_crowd_pleaser(ctx):
    return any(f.get("kills", 0) >= 2 for f in ctx["fighters"])


def _check_hazard_dance(ctx):
    return int(ctx.get("hazard_hits", 0)) == 0


def _check_iron_discipline(ctx):
    fighters = ctx["fighters"]
    if not fighters:
        return False
    strong = sum(1 for f in fighters if f.get("hp_ratio", 0.0) >= 0.5)
    return strong * 2 >= len(fighters)


OBJECTIVES = {
    "clean_sweep": {
        "name": "Clean Sweep",
        "desc": "Win without losing a single fighter.",
        "sponsor_line": "Bridgeward Alms loves an unbloodied banner.",
        "check": _check_clean_sweep,
    },
    "crowd_pleaser": {
        "name": "Crowd Pleaser",
        "desc": "One fighter scores 2+ takedowns.",
        "sponsor_line": "Quench Promotions wants a face for the poster.",
        "check": _check_crowd_pleaser,
    },
    "hazard_dance": {
        "name": "Hazard Dance",
        "desc": "Win without any fighter hit by arena hazards.",
        "sponsor_line": "The Cog Wardens judge your footwork around their gears.",
        "check": _check_hazard_dance,
    },
    "iron_discipline": {
        "name": "Iron Discipline",
        "desc": "Finish with at least half the team above 50% HP.",
        "sponsor_line": "The Ironspan Union pays for shifts, not stretchers.",
        "check": _check_iron_discipline,
    },
}


def _lore_tier(manager) -> int:
    engine = getattr(manager, "league_engine", None)
    tier = getattr(engine, "tier", None)
    if tier is None:
        tier = getattr(manager, "league_level", 1)
    return max(0, int(tier) - 1)


def roll_match_objective(manager, rng=None):
    """Arpoo tavoitteen Rattlebridgen Tier 1+ -liigamatsiin (muuten None)."""
    manager.current_match_objective = None
    if getattr(manager, "mode", None) != "League":
        return None
    if getattr(manager, "current_arena_location", None) != "rattlebridge":
        return None
    if _lore_tier(manager) < 1:
        return None
    rng = rng or random
    objective_id = rng.choice(sorted(OBJECTIVES))
    data = OBJECTIVES[objective_id]
    manager.current_match_objective = {
        "id": objective_id,
        "name": data["name"],
        "desc": data["desc"],
        "sponsor_line": data["sponsor_line"],
    }
    return manager.current_match_objective


def build_context(manager, won, fighters):
    """Kokoaa arviointidatan matsin lopputilasta."""
    rows = []
    stats = {}
    try:
        for row in (getattr(manager, "last_match_stats", None) or {}).get("fighters", []):
            stats[row.get("name")] = int(row.get("kills", 0))
    except Exception:
        pass
    for unit in fighters or []:
        if unit is None:
            continue
        max_hp = max(1, int(getattr(unit, "max_hp", 1)))
        kills = int(getattr(unit, "stats", {}).get("kills", stats.get(getattr(unit, "name", ""), 0)))
        rows.append({
            "name": getattr(unit, "name", "?"),
            "dead": bool(getattr(unit, "is_dead", False)),
            "hp_ratio": max(0.0, int(getattr(unit, "current_hp", 0)) / max_hp),
            "kills": kills,
        })
    arena = getattr(manager, "current_arena", None)
    return {
        "won": bool(won),
        "fighters": rows,
        "hazard_hits": int(getattr(arena, "player_hazard_hits", 0) or 0),
    }


def evaluate_match_objective(manager, won, fighters):
    """Arvioi aktiivisen tavoitteen, maksaa palkkiot ja kirjaa tuloksen.

    Palauttaa tulosdictin tai None jos tavoitetta ei ollut.
    """
    objective = getattr(manager, "current_match_objective", None)
    manager.current_match_objective = None
    if not objective:
        manager.last_objective_result = None
        return None
    data = OBJECTIVES.get(objective["id"])
    ctx = build_context(manager, won, fighters)
    completed = bool(won and data and data["check"](ctx))
    result = {
        "id": objective["id"],
        "name": objective["name"],
        "completed": completed,
        "gold": OBJECTIVE_GOLD if completed else 0,
        "reputation": OBJECTIVE_REP if completed else 0,
    }
    if completed:
        manager.gold = int(getattr(manager, "gold", 0)) + OBJECTIVE_GOLD
        try:
            manager.reputation = int(getattr(manager, "reputation", 0)) + OBJECTIVE_REP
        except Exception:
            g = manager.npc_state.setdefault("global", {})
            g["reputation"] = int(g.get("reputation", 0)) + OBJECTIVE_REP
        # Esitys rakentaa brandin: kaikki sponsorit +1 karsivallisyys.
        try:
            from systems import sponsors
            state = sponsors.ensure_sponsor_state(manager)
            for record in state["signed"].values():
                record["patience"] = min(sponsors.MAX_PATIENCE,
                                         int(record.get("patience", 0)) + 1)
        except Exception:
            pass
    try:
        root = manager.npc_state.setdefault("rattlebridge", {})
        history = root.setdefault("objective_history", [])
        history.append(dict(result))
        root["objective_history"] = history[-20:]
    except Exception:
        pass
    manager.last_objective_result = result
    return result
