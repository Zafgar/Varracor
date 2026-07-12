# tests/test_scout_report.py
"""
Tiedusteluraportti (scout) heijastaa vastustajan todellista identiteettia:
tyyli, kokoonpano, uhka-arvio ja maine — ei enaa vakioplaceholderia.
"""
import pytest


def _engine():
    from leagues.league_engine import LeagueEngine
    le = LeagueEngine()
    le._ensure_initialized()
    return le


def test_scout_report_is_not_placeholder():
    le = _engine()
    opp = le.get_next_opponent("5v5")
    report = "\n".join(le.get_scout_report(opp))
    assert "Style: Standard" not in report
    assert "Threat: Medium" not in report


def test_scout_report_has_squad_and_threat():
    le = _engine()
    opp = le.get_next_opponent("5v5")
    lines = le.get_scout_report(opp)
    joined = "\n".join(lines)
    assert any(l.startswith("Opponent:") for l in lines)
    assert "Squad:" in joined
    assert "Threat:" in joined


def test_scout_report_shows_reputation():
    le = _engine()
    opp = le.get_next_opponent("3v3")
    # Kaikilla Tier 0 -premadeilla on reputation-teksti
    report = "\n".join(le.get_scout_report(opp))
    assert '"' in report  # maine lainausmerkeissa


def test_scout_report_handles_no_opponent():
    le = _engine()
    assert le.get_scout_report(None) == ["No opponent."]
