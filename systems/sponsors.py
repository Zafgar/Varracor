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

Lore model (docs/LORE.md + sponsor brief):
- Sponsors are organizations, alliances or realm agents. They pay a MONTHLY
  stipend (28-day calendar month) plus per-win bonuses; in exchange they get
  fame, information and political leverage.
- ``alignment`` records whose interests a sponsor ultimately serves:
  "crown" / "kharak" / "lupine" / "neutral" / "underworld". Teams are neutral
  by default but drift toward their backers' politics.
- The Gutter Ledger is the underworld backer: big dirty cash at every tier,
  but every payout is DEBT that is eventually called in.
"""

from __future__ import annotations

SPONSOR_SLOTS = 3
START_PATIENCE = 3
MAX_PATIENCE = 3
# Kalenterikuukausi = yksi vuodenaika-kuukausi (world_clock: 28 pv).
STIPEND_PERIOD_DAYS = 28
# Gutter Ledgerin velka peritään maineena kun suhde katkeaa.
LEDGER_DEBT_REP_PER_PAYOUT = 2
LEDGER_DEBT_REP_CAP = 30


SPONSORS = {
    "ironspan_union": {
        "name": "Ironspan Union",
        "patron": "Hendrik Ironspan",
        "banner": (100, 120, 140),
        "tier": 1,
        "alignment": "crown",
        "required_tier": 1,
        "required_rep": 0,
        "signing_bonus": 60,
        "monthly": 25,
        "stipend": 40,
        "rep_per_win": 2,
        "demand": "win",
        "drop_rep_penalty": 0,
        "flavor": ("The bridge-workers' union backs teams that simply win and pay "
                   "their tab. Dull, reliable coin - and their freight wagons run "
                   "the causeway to Muckford daily."),
    },
    "quench_promotions": {
        "name": "Quench Promotions",
        "patron": "Sera Quench",
        "banner": (170, 90, 120),
        "tier": 1,
        "alignment": "neutral",
        "required_tier": 1,
        "required_rep": 20,
        "signing_bonus": 120,
        "monthly": 40,
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
        "tier": 1,
        "alignment": "neutral",
        "required_tier": 1,
        "required_rep": 10,
        "signing_bonus": 40,
        "monthly": 30,
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
        "tier": 1,
        "alignment": "crown",
        "required_tier": 1,
        "required_rep": 40,
        "signing_bonus": 200,
        "monthly": 80,
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
        "tier": 1,
        "alignment": "crown",
        "required_tier": 1,
        "required_rep": 15,
        "signing_bonus": 50,
        "monthly": 20,
        "stipend": 30,
        "rep_per_win": 5,
        "demand": "clean",
        "drop_rep_penalty": 0,
        "flavor": ("The chapel-hospital pays modestly but launders a team's image: "
                   "win cleanly and the Prior calls you merciful."),
    },
    "gutter_ledger": {
        "name": "The Gutter Ledger",
        "patron": "A voice behind a lantern",
        "banner": (90, 60, 90),
        "tier": 1,
        "alignment": "underworld",
        "required_tier": 1,
        "required_rep": 0,
        "signing_bonus": 150,
        "monthly": 60,
        "stipend": 120,
        "rep_per_win": 0,
        "demand": "win",
        "drop_rep_penalty": 0,   # velka peritään erikseen (ks. debt)
        "debt_per_payout": True,
        "flavor": ("Shadow money from Giltgate's and Rattlebridge's underside. "
                   "No questions, huge purses - and every payout is entered in a "
                   "ledger you never get to read. Debts are always called in."),
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
    # Gutter Ledgerin kirjattu velka (peritään maineena, questline-koukku)
    sponsors.setdefault("ledger_debt", 0)
    # Kuukausistipendien viimeisin maksettu absoluuttipäivä
    sponsors.setdefault("last_stipend_absday", None)
    return sponsors


def _absolute_day(manager):
    """Maailmankellon absoluuttinen päivä (vuosi*vuoden pituus + päivä)."""
    clock = getattr(manager, "world_clock", None)
    if clock is None:
        return None
    try:
        from world_clock import DAYS_PER_YEAR
    except Exception:
        DAYS_PER_YEAR = 112
    return int(getattr(clock, "year", 0)) * DAYS_PER_YEAR + int(getattr(clock, "day", 1))


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
    if state.get("last_stipend_absday") is None:
        # Kuukausilaskuri alkaa ensimmäisestä sopimuksesta.
        state["last_stipend_absday"] = _absolute_day(manager)
    state["history"].append({"event": "signed", "sponsor": sponsor_id})
    return True, f"Signed {s['name']} (+{s['signing_bonus']}g signing bonus)."


def _call_in_ledger_debt(manager, state) -> int:
    """Perii Gutter Ledgerin velan maineena kun suhde katkeaa.

    Velka EI nollaudu - alamaailma muistaa, ja kirjattu velka jää
    tulevan questlinen koukuksi (state['ledger_debt'])."""
    debt = int(state.get("ledger_debt", 0))
    if debt <= 0:
        return 0
    hit = min(LEDGER_DEBT_REP_CAP, debt * LEDGER_DEBT_REP_PER_PAYOUT)
    _add_reputation(manager, -hit)
    state["history"].append({"event": "ledger_debt_called", "debt": debt, "rep": hit})
    return hit


def drop_sponsor(manager, sponsor_id: str):
    """Player-initiated drop. Some sponsors (Crown) apply a rep penalty;
    the Gutter Ledger calls in its recorded debt instead."""
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
    if s.get("debt_per_payout"):
        hit = _call_in_ledger_debt(manager, state)
        if hit:
            msg += f" The Ledger calls in its debt (-{hit} reputation)."
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
            if s.get("debt_per_payout"):
                state["ledger_debt"] = int(state.get("ledger_debt", 0)) + 1
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
                if s.get("debt_per_payout"):
                    hit = _call_in_ledger_debt(manager, state)
                    summary["reputation"] -= hit
                summary["dropped"].append(sid)
                state["history"].append({"event": "patience_dropped", "sponsor": sid})
    return summary


def collect_due_stipends(manager) -> dict:
    """Maksaa erääntyneet kuukausistipendit (28 pv jakso) kaikilta
    allekirjoitetuilta sponsoreilta. Kutsutaan hubeissa/matsien jälkeen -
    laskuri perustuu maailmankellon absoluuttipäivään, joten kutsutiheys
    ei vaikuta summiin. Gutter Ledgerin kuukausiraha kasvattaa velkaa.

    Palauttaa {"gold": int, "months": int}.
    """
    state = ensure_sponsor_state(manager)
    summary = {"gold": 0, "months": 0}
    if not state["signed"]:
        return summary
    today = _absolute_day(manager)
    last = state.get("last_stipend_absday")
    if today is None:
        return summary
    if last is None:
        state["last_stipend_absday"] = today
        return summary
    months = max(0, (int(today) - int(last)) // STIPEND_PERIOD_DAYS)
    if months <= 0:
        return summary
    total = 0
    for sid in state["signed"]:
        s = SPONSORS.get(sid)
        if not s:
            continue
        total += int(s.get("monthly", 0)) * months
        if s.get("debt_per_payout"):
            state["ledger_debt"] = int(state.get("ledger_debt", 0)) + months
    if total:
        _add_gold(manager, total)
        state["history"].append({"event": "monthly_stipends",
                                 "months": months, "gold": total})
    state["last_stipend_absday"] = int(last) + months * STIPEND_PERIOD_DAYS
    summary["gold"] = total
    summary["months"] = months
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
