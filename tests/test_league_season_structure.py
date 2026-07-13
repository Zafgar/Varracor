# tests/test_league_season_structure.py
"""
Kausirakenne: kierrospohjainen (EI kalenteripäiviä), moodikiintiöt per kausi,
5v5 painavin pistemoodi, promo aina 5v5, ja muiden parien matsit simuloituvat
taustalla samalla kierroksella kuin pelaajan matsi.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from leagues import league_engine as le


def test_points_ladder_and_promo_size():
    assert le.POINTS_PER_WIN["5v5"] > le.POINTS_PER_WIN["3v3"] > le.POINTS_PER_WIN["1v1"]
    assert le.PROMOTION_BATTLE_SIZE == 5


def test_season_quotas_are_real_not_test_values():
    # Kausi vaatii oikean määrän matseja (ei 2/2/2-testijäännettä)
    assert le.REQ_GAMES == {"1v1": 6, "3v3": 5, "5v5": 5}
    assert sum(le.REQ_GAMES.values()) >= 15, "tarpeeksi monta taistelua per kausi"


def test_engine_has_no_calendar_coupling():
    # Kello tikittää vapaasti (fast travel ym.) - liigan eteneminen on
    # kierrospohjaista eikä saa lukea maailmankelloa/päiviä.
    src = open("leagues/league_engine.py").read()
    for forbidden in ("world_clock", "advance_day", "DAYS_PER"):
        assert forbidden not in src, f"league_engine ei saa sitoutua kelloon: {forbidden}"


def test_background_pairings_resolve_with_player_round():
    season = le.LeagueSeason(tier=1)
    # Pelaajan vastustaja tältä kierrokselta
    opponent = season.get_next_opponent_team()
    assert opponent is not None
    season.report_player_result(True, opponent)
    assert season.has_pending_results(), "muiden parien matsit jonoutuvat"
    standings = season.get_standings_sorted()
    assert not season.has_pending_results(), "kysely ratkaisee taustamatsit"
    # Kaikki kierroksen parit pelasivat: jokaisella osallistujalla played>=1
    played = sum(1 for r in standings if r.played >= 1)
    assert played >= 4, "kierroksen kaikkien parien pitää pelata samaan aikaan"


def test_standings_are_fresh_not_stale():
    season = le.LeagueSeason(tier=1)
    opponent = season.get_next_opponent_team()
    season.report_player_result(True, opponent)
    # ENSIMMÄINEN standings-kutsu heijastaa jo ratkaistut taustamatsit
    standings = season.get_standings_sorted()
    total_played = sum(r.played for r in standings)
    assert total_played >= 6, f"lajittelun pitää tapahtua resolvauksen jälkeen ({total_played})"


def test_season_not_complete_before_quotas():
    class _Eng(le.LeagueEngine):
        pass
    eng = le.LeagueEngine()
    eng._ensure_initialized()
    assert eng.is_season_complete() is False
    ok, reason, _ = eng.check_promotion_eligibility()
    assert ok is False
    assert "5v5" in reason and "1v1" in reason
