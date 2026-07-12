"""Rattlebridge sponsor system.

The Scrapring (Tier 1) is where gladiators stop being brawlers and start being
*brands*. Sera Quench sells stories; sponsors pay teams that can be marketed.
This is the mechanic that makes Rattlebridge deeper than Muckford:

- Each sponsor has tier/reputation gates, a signing bonus, a per-league-win
  stipend, and a per-match DEMAND ("what keeps them happy").
- You have a limited number of sponsor slots. Signing pays a bonus and steady
  stipends; failing a sponsor's demand burns their patience, and at zero
  patience they drop you (some, like the Crown concession, with a rep hit).

State lives in ``manager.npc_state['rattlebridge']['sponsors']`` so it persists
through the existing save system without a format break. All logic here is
pure-ish (operates on ``manager``) and UI-free so it can be unit tested.

Demand vocabulary (evaluated from an end-of-match result dict):
  win        - the match was won at all
  clean      - won and no signed fighter died
  dominant   - won with the majority of the team still standing
  spectacle  - won and at least one enemy was defeated (a "show")
"""

from __future__ import annotations

SPONSOR_SLOTS = 3
START_PATIENCE = 3
MAX_PATIENCE = 3


SPONSORS = {
    "ironspan_union": {
        "name": "Ironspan Union",
        "patron": "Hendrik Ironspan",
        "banner": (100, 120, 140),
        "required_tier": 1,
        "required_rep": 0,
        "signing_bonus": 60,
        "stipend": 40,
        "rep_per_win": 2,
        "demand": "win",
        "drop_rep_penalty": 0,
        "flavor": ("The bridge-workers' union backs teams that simply win and pay "
                   "their tab. Dull, reliable coin."),
    },
    "quench_promotions": {
        "name": "Quench Promotions",
        "patron": "Sera Quench",
        "banner": (170, 90, 120),
        "required_tier": 1,
        "required_rep": 20,
        "signing_bonus": 120,
        "stipend": 70,
        "rep_per_win": 4,
        "demand": "spectacle",
        "drop_rep_penalty": 5,
        "flavor": ("Sera sells stories. She pays well for wins that make a crowd "
                   "roar - and remembers teams that bore them."),
    },
    "gutterlight_book": {
        "name": "Gutterlight Book",
        "patron": "Hamo (via bookmakers)",
        "banner": (120, 150, 90),
        "required_tier": 1,
        "required_rep": 10,
        "signing_bonus": 40,
        "stipend": 90,
        "rep_per_win": 0,
        "demand": "dominant",
        "drop_rep_penalty": 0,
        "flavor": ("The bookmakers pay big on clean, dominant results they can set "
                   "odds around - and nothing when you scrape by."),
    },
    "vane_concession": {
        "name": "Vane Toll Concession",
        "patron": "Factor Ellis Vane",
        "banner": (150, 130, 70),
        "required_tier": 1,
        "required_rep": 40,
        "signing_bonus": 200,
        "stipend": 110,
        "rep_per_win": -1,
        "demand": "clean",
        "drop_rep_penalty": 12,
        "flavor": ("Crown money, Crown strings. Enormous stipends and a spotless "
                   "brand demand - and the Crown does not forget a team that walks "
                   "away."),
    },
    "bridgeward_alms": {
        "name": "Bridgeward Alms",
        "patron": "Prior Jannik Voss",
        "banner": (180, 170, 120),
        "required_tier": 1,
        "required_rep": 15,
        "signing_bonus": 50,
        "stipend": 30,
        "rep_per_win": 5,
        "demand": "clean",
        "drop_rep_penalty": 0,
        "flavor": ("The chapel-hospital pays modestly but launders a team's image: "
                   "win cleanly and the Prior calls you merciful."),
    },
}


# ----------------------------------------------------------------------
# State
# ----------------------------------------------------------------------
def ensure_sponsor_state(manager) -> dict:
    root = manager.npc_state.setdefault("rattlebridge", {})
    sponsors = root.setdefault("sponsors", {})
    sponsors.setdefault("signed", {})   # id -> {"patience": int, "wins": int}
    sponsors.setdefault("history", [])
    return sponsors


def _reputation(manager) -> int:
    rep = getattr(manager, "reputation", None)
    if isinstance(rep, (int, float)):
        return int(rep)
    return int(manager.npc_state.get("global", {}).get("reputation", 0))


def _add_reputation(manager, amount: int) -> None:
    if amount == 0:
        return
    try:
        manager.reputation = int(getattr(manager, "reputation", 0)) + int(amount)
    except Exception:
        g = manager.npc_state.setdefault("global", {})
        g["reputation"] = int(g.get("reputation", 0)) + int(amount)


def _add_gold(manager, amount: int) -> None:
    manager.gold = int(getattr(manager, "gold", 0)) + int(amount)


def _league_tier(manager) -> int:
    """Lore tier (engine tier - 1), matching the rest of the codebase."""
    engine = getattr(manager, "league_engine", None)
    tier = getattr(engine, "tier", None)
    if tier is None:
        tier = getattr(manager, "league_level", 1)
    return max(0, int(tier) - 1)


# ----------------------------------------------------------------------
# Queries
# ----------------------------------------------------------------------
def signed_ids(manager) -> list:
    return list(ensure_sponsor_state(manager)["signed"].keys())


def is_signed(manager, sponsor_id: str) -> bool:
    return sponsor_id in ensure_sponsor_state(manager)["signed"]


def slots_used(manager) -> int:
    return len(ensure_sponsor_state(manager)["signed"])


def slots_free(manager) -> int:
    return max(0, SPONSOR_SLOTS - slots_used(manager))


def meets_requirements(manager, sponsor_id: str) -> bool:
    s = SPONSORS.get(sponsor_id)
    if not s:
        return False
    return (_league_tier(manager) >= int(s["required_tier"])
            and _reputation(manager) >= int(s["required_rep"]))


def available_sponsors(manager) -> list:
    """Sponsor ids the player qualifies for and has not signed."""
    out = []
    for sid in SPONSORS:
        if not is_signed(manager, sid) and meets_requirements(manager, sid):
            out.append(sid)
    return out


def can_sign(manager, sponsor_id: str):
    """Return (ok, reason)."""
    s = SPONSORS.get(sponsor_id)
    if not s:
        return False, "Unknown sponsor."
    if is_signed(manager, sponsor_id):
        return False, "Already signed."
    if slots_free(manager) <= 0:
        return False, f"No free sponsor slots (max {SPONSOR_SLOTS})."
    if _league_tier(manager) < int(s["required_tier"]):
        return False, f"Requires Arena Tier {s['required_tier']}."
    if _reputation(manager) < int(s["required_rep"]):
        return False, f"Requires {s['required_rep']} reputation."
    return True, ""


# ----------------------------------------------------------------------
# Mutations
# ----------------------------------------------------------------------
def sign_sponsor(manager, sponsor_id: str):
    """Sign a sponsor: pays the signing bonus, opens a slot. (ok, message)."""
    ok, reason = can_sign(manager, sponsor_id)
    if not ok:
        return False, reason
    s = SPONSORS[sponsor_id]
    state = ensure_sponsor_state(manager)
    state["signed"][sponsor_id] = {"patience": START_PATIENCE, "wins": 0}
    _add_gold(manager, int(s["signing_bonus"]))
    state["history"].append({"event": "signed", "sponsor": sponsor_id})
    return True, f"Signed {s['name']} (+{s['signing_bonus']}g signing bonus)."


def drop_sponsor(manager, sponsor_id: str):
    """Player-initiated drop. Some sponsors (Crown) apply a rep penalty."""
    state = ensure_sponsor_state(manager)
    if sponsor_id not in state["signed"]:
        return False, "Not signed."
    s = SPONSORS[sponsor_id]
    penalty = int(s.get("drop_rep_penalty", 0))
    del state["signed"][sponsor_id]
    if penalty:
        _add_reputation(manager, -penalty)
    state["history"].append({"event": "dropped", "sponsor": sponsor_id})
    msg = f"Dropped {s['name']}."
    if penalty:
        msg += f" The Crown remembers (-{penalty} reputation)."
    return True, msg


# ----------------------------------------------------------------------
# Demand evaluation + per-match settlement
# ----------------------------------------------------------------------
def _demand_met(demand: str, result: dict) -> bool:
    won = bool(result.get("won"))
    if not won:
        return False
    if demand == "win":
        return True
    if demand == "clean":
        return not bool(result.get("any_ally_died", False))
    if demand == "dominant":
        survivors = int(result.get("ally_survivors", 0))
        total = int(result.get("ally_total", 0))
        return total > 0 and survivors * 2 > total
    if demand == "spectacle":
        return int(result.get("enemies_defeated", 0)) >= 1
    return won


def on_league_match_end(manager, result: dict) -> dict:
    """Settle all signed sponsors for a finished Tier 1 league match.

    ``result`` keys: won(bool), any_ally_died(bool), ally_survivors(int),
    ally_total(int), enemies_defeated(int).

    Returns a summary dict: {gold, reputation, satisfied[], failed[], dropped[]}.
    """
    state = ensure_sponsor_state(manager)
    summary = {"gold": 0, "reputation": 0,
               "satisfied": [], "failed": [], "dropped": []}
    if not state["signed"]:
        return summary

    for sid in list(state["signed"].keys()):
        s = SPONSORS.get(sid)
        if not s:
            del state["signed"][sid]
            continue
        rec = state["signed"][sid]
        if _demand_met(s["demand"], result):
            stipend = int(s["stipend"])
            rep = int(s["rep_per_win"])
            _add_gold(manager, stipend)
            _add_reputation(manager, rep)
            rec["patience"] = min(MAX_PATIENCE, rec.get("patience", START_PATIENCE) + 1)
            rec["wins"] = int(rec.get("wins", 0)) + 1
            summary["gold"] += stipend
            summary["reputation"] += rep
            summary["satisfied"].append(sid)
        else:
            rec["patience"] = rec.get("patience", START_PATIENCE) - 1
            summary["failed"].append(sid)
            if rec["patience"] <= 0:
                penalty = int(s.get("drop_rep_penalty", 0))
                del state["signed"][sid]
                if penalty:
                    _add_reputation(manager, -penalty)
                    summary["reputation"] -= penalty
                summary["dropped"].append(sid)
                state["history"].append({"event": "patience_dropped", "sponsor": sid})
    return summary


def build_match_result(won: bool, fighters) -> dict:
    """Build an on_league_match_end result dict from the player's fighters.

    ``fighters`` is an iterable of unit objects (may contain None). Uses
    ``is_dead`` to derive clean/dominant demands. Enemy-defeat count is
    approximated as 1 on a win (a defeated opponent = a show) unless the
    caller overrides it later.
    """
    units = [f for f in (fighters or []) if f is not None]
    total = len(units)
    dead = sum(1 for u in units if getattr(u, "is_dead", False))
    survivors = total - dead
    return {
        "won": bool(won),
        "any_ally_died": dead > 0,
        "ally_survivors": survivors,
        "ally_total": total,
        "enemies_defeated": 1 if won else 0,
    }
