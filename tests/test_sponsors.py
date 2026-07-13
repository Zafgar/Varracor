# tests/test_sponsors.py
"""
Rattlebridgen sponsorijärjestelmä: kelpoisuus (tier/rep), allekirjoitus +
signing bonus, slotit, per-matsi stipendit ja demand-ehdot (win/clean/
dominant/spectacle) sekä kärsivällisyyden loppuminen -> pudotus.
"""
import pytest
from systems import sponsors


class _Engine:
    def __init__(self, tier):
        self.tier = tier


class _Mgr:
    """Minimaalinen manageri: gold, reputation, npc_state, league_engine."""
    def __init__(self, engine_tier=2, reputation=100, gold=0):
        self.gold = gold
        self.reputation = reputation
        self.league_engine = _Engine(engine_tier)
        self.league_level = engine_tier
        self.npc_state = {"global": {"reputation": reputation}}


class _Unit:
    def __init__(self, dead=False):
        self.is_dead = dead


def test_tier0_player_has_no_sponsors():
    m = _Mgr(engine_tier=1, reputation=100)  # lore tier 0
    assert sponsors.available_sponsors(m) == []


def test_reputation_gates_sponsors():
    low = _Mgr(engine_tier=2, reputation=0)   # lore tier 1
    avail = sponsors.available_sponsors(low)
    assert "ironspan_union" in avail          # rep 0 ok
    assert "vane_concession" not in avail     # needs rep 40
    high = _Mgr(engine_tier=2, reputation=50)
    assert "vane_concession" in sponsors.available_sponsors(high)


def test_sign_pays_bonus_and_consumes_slot():
    m = _Mgr(engine_tier=2, reputation=100, gold=0)
    ok, _ = sponsors.sign_sponsor(m, "ironspan_union")
    assert ok
    assert m.gold == sponsors.SPONSORS["ironspan_union"]["signing_bonus"]
    assert sponsors.is_signed(m, "ironspan_union")
    assert sponsors.slots_used(m) == 1


def test_slot_limit_enforced():
    m = _Mgr(engine_tier=2, reputation=100)
    for sid in ("ironspan_union", "quench_promotions", "gutterlight_book"):
        assert sponsors.sign_sponsor(m, sid)[0]
    assert sponsors.slots_free(m) == 0
    ok, reason = sponsors.sign_sponsor(m, "bridgeward_alms")
    assert not ok and "slot" in reason.lower()


def test_win_pays_stipend_and_reputation():
    m = _Mgr(engine_tier=2, reputation=100, gold=0)
    sponsors.sign_sponsor(m, "ironspan_union")          # +60 bonus
    gold_after_sign = m.gold
    result = {"won": True, "any_ally_died": False,
              "ally_survivors": 3, "ally_total": 3, "enemies_defeated": 1}
    summ = sponsors.on_league_match_end(m, result)
    s = sponsors.SPONSORS["ironspan_union"]
    assert m.gold == gold_after_sign + s["stipend"]
    assert summ["gold"] == s["stipend"]
    assert "ironspan_union" in summ["satisfied"]


def test_clean_demand_fails_when_ally_dies():
    m = _Mgr(engine_tier=2, reputation=100)
    sponsors.sign_sponsor(m, "bridgeward_alms")  # demand "clean"
    result = {"won": True, "any_ally_died": True,
              "ally_survivors": 2, "ally_total": 3, "enemies_defeated": 1}
    summ = sponsors.on_league_match_end(m, result)
    assert "bridgeward_alms" in summ["failed"]
    assert summ["gold"] == 0


def test_patience_runs_out_and_crown_penalizes_on_drop():
    m = _Mgr(engine_tier=2, reputation=100)
    sponsors.sign_sponsor(m, "vane_concession")   # demand "clean", drop penalty 12
    rep0 = m.reputation
    dirty = {"won": True, "any_ally_died": True,
             "ally_survivors": 1, "ally_total": 3, "enemies_defeated": 1}
    # START_PATIENCE failures -> dropped on the last one
    last = {}
    for _ in range(sponsors.START_PATIENCE):
        last = sponsors.on_league_match_end(m, dirty)
    assert not sponsors.is_signed(m, "vane_concession")
    assert "vane_concession" in last["dropped"]
    assert m.reputation == rep0 - sponsors.SPONSORS["vane_concession"]["drop_rep_penalty"]


def test_dominant_demand_needs_majority_survivors():
    m = _Mgr(engine_tier=2, reputation=100)
    sponsors.sign_sponsor(m, "gutterlight_book")  # demand "dominant"
    scrape = {"won": True, "any_ally_died": True,
              "ally_survivors": 1, "ally_total": 3, "enemies_defeated": 1}
    assert "gutterlight_book" in sponsors.on_league_match_end(m, scrape)["failed"]
    m2 = _Mgr(engine_tier=2, reputation=100)
    sponsors.sign_sponsor(m2, "gutterlight_book")
    strong = {"won": True, "any_ally_died": False,
              "ally_survivors": 3, "ally_total": 3, "enemies_defeated": 2}
    assert "gutterlight_book" in sponsors.on_league_match_end(m2, strong)["satisfied"]


def test_loss_satisfies_nobody():
    m = _Mgr(engine_tier=2, reputation=100)
    sponsors.sign_sponsor(m, "ironspan_union")
    loss = {"won": False, "any_ally_died": True,
            "ally_survivors": 0, "ally_total": 3, "enemies_defeated": 0}
    summ = sponsors.on_league_match_end(m, loss)
    assert summ["satisfied"] == []
    assert "ironspan_union" in summ["failed"]


def test_build_match_result_from_fighters():
    r = sponsors.build_match_result(True, [_Unit(False), _Unit(True), None])
    assert r["won"] is True
    assert r["ally_total"] == 2
    assert r["ally_survivors"] == 1
    assert r["any_ally_died"] is True


def test_drop_sponsor_is_persisted_in_state():
    m = _Mgr(engine_tier=2, reputation=100)
    sponsors.sign_sponsor(m, "quench_promotions")
    rep0 = m.reputation
    ok, msg = sponsors.drop_sponsor(m, "quench_promotions")
    assert ok
    assert not sponsors.is_signed(m, "quench_promotions")
    # Quench applies a small drop penalty (5)
    assert m.reputation == rep0 - sponsors.SPONSORS["quench_promotions"]["drop_rep_penalty"]


# ----------------------------------------------------------------------
# Lore-laajennus: alignment, kuukausistipendit, Gutter Ledgerin velka
# ----------------------------------------------------------------------
class _Clock:
    def __init__(self, year=3, day=1):
        self.year = year
        self.day = day
        self.minutes = 8 * 60.0

    def advance_day(self):
        self.day += 1


def test_every_sponsor_has_lore_fields():
    for sid, s in sponsors.SPONSORS.items():
        assert s.get("alignment") in ("crown", "kharak", "lupine",
                                      "neutral", "underworld"), sid
        assert int(s.get("monthly", -1)) >= 0, sid
        assert int(s.get("tier", 0)) >= 1, sid


def test_monthly_stipends_accrue_by_calendar():
    m = _Mgr(engine_tier=2, reputation=100, gold=0)
    m.world_clock = _Clock(year=3, day=1)
    sponsors.sign_sponsor(m, "ironspan_union")   # monthly 25
    sponsors.sign_sponsor(m, "quench_promotions")  # monthly 40
    gold0 = m.gold
    # Alle kuukausi -> ei maksua
    m.world_clock.day = 20
    assert sponsors.collect_due_stipends(m)["gold"] == 0
    # Kaksi täyttä kuukautta (56 pv) -> 2 * (25+40)
    m.world_clock.day = 1 + 56
    paid = sponsors.collect_due_stipends(m)
    assert paid["months"] == 2
    assert paid["gold"] == 2 * (25 + 40)
    assert m.gold == gold0 + paid["gold"]
    # Uusi kutsu heti perään ei tuplamaksa
    assert sponsors.collect_due_stipends(m)["gold"] == 0


def test_gutter_ledger_open_to_broke_teams_and_records_debt():
    m = _Mgr(engine_tier=2, reputation=0, gold=0)
    assert "gutter_ledger" in sponsors.available_sponsors(m)
    ok, _ = sponsors.sign_sponsor(m, "gutter_ledger")
    assert ok
    win = {"won": True, "any_ally_died": False,
           "ally_survivors": 3, "ally_total": 3, "enemies_defeated": 1}
    sponsors.on_league_match_end(m, win)
    sponsors.on_league_match_end(m, win)
    state = sponsors.ensure_sponsor_state(m)
    assert state["ledger_debt"] == 2


def test_gutter_ledger_calls_in_debt_on_drop():
    m = _Mgr(engine_tier=2, reputation=50, gold=0)
    sponsors.sign_sponsor(m, "gutter_ledger")
    win = {"won": True, "any_ally_died": False,
           "ally_survivors": 3, "ally_total": 3, "enemies_defeated": 1}
    for _ in range(3):
        sponsors.on_league_match_end(m, win)
    rep0 = m.reputation
    ok, msg = sponsors.drop_sponsor(m, "gutter_ledger")
    assert ok and "debt" in msg.lower()
    assert m.reputation == rep0 - 3 * sponsors.LEDGER_DEBT_REP_PER_PAYOUT
    # Velka EI nollaudu - questline-koukku säilyy
    assert sponsors.ensure_sponsor_state(m)["ledger_debt"] == 3


def test_monthly_stipend_grows_ledger_debt():
    m = _Mgr(engine_tier=2, reputation=0, gold=0)
    m.world_clock = _Clock(year=3, day=1)
    sponsors.sign_sponsor(m, "gutter_ledger")
    m.world_clock.day = 1 + 28
    sponsors.collect_due_stipends(m)
    assert sponsors.ensure_sponsor_state(m)["ledger_debt"] == 1
