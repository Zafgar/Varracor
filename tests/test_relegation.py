# tests/test_relegation.py
"""
Ylennys/putoamis-sykli: paras Tier 0 -tiimi (pelaaja) nousee Tier 1:een,
mutta jos ei pysy mukana, tippuu takaisin. Testaa relegaatiomekaniikan.
"""
import pytest


def _engine():
    from leagues.league_engine import LeagueEngine
    le = LeagueEngine()
    le._ensure_initialized()
    return le


def test_promote_then_relegate_roundtrip():
    le = _engine()
    assert le.tier == 1  # lore Tier 0 = pohja
    le.promote_player()
    assert le.tier == 2  # lore Tier 1
    le.relegate_player()
    assert le.tier == 1  # takaisin lore Tier 0:aan


def test_relegation_never_below_floor():
    le = _engine()
    assert le.tier == 1
    le.relegate_player()
    assert le.tier == 1  # ei koskaan alle 1


def test_promotion_capped():
    le = _engine()
    for _ in range(10):
        le.promote_player()
    assert le.tier == 6  # katto


def test_fail_season_stays_at_tier0():
    """Tier 1 (lore Tier 0) on pohja: epäonnistuminen ei pudota alle."""
    le = _engine()
    assert le.tier == 1
    le.fail_season()
    assert le.tier == 1
