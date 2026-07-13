# tests/test_league_qa_and_hof.py
"""
Liigan QA: seuraava vastustaja lukittu kunnes pelattu, moodit pelattavissa
missä järjestyksessä vain, vajaa joukkue sallittu (League 3v3/5v5) -
sekä all-time Hall of Fame -kronikka ja vastustajan scout-raportti.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from leagues import league_engine as le


class _Stub:
    def __init__(self):
        self.npc_state = {"global": {}}
        self.my_team = []


def _engine():
    eng = le.LeagueEngine()
    eng.manager = _Stub()
    eng._ensure_initialized()
    return eng


def test_next_opponent_is_locked_until_played():
    eng = _engine()
    a = eng.get_next_opponent("1v1")
    b = eng.get_next_opponent("1v1")
    assert a is b, "vastustaja ei saa vaihtua kyselyjen välillä"
    # Standings-kysely kesken kierroksen ei saa vaihtaa vastustajaa
    eng.get_standings("1v1")
    assert eng.get_next_opponent("1v1") is a
    # Pelattu -> kierros etenee -> uusi pari
    eng.report_match_result("1v1", True, a)
    round_after = eng.seasons["1v1"].current_round
    eng.get_next_opponent("1v1")  # resolvaa taustaparit + advance
    assert eng.seasons["1v1"].current_round >= 1 or round_after >= 1


def test_modes_progress_independently_any_order():
    eng = _engine()
    # Pelaa 5v5 ensin, sitten 1v1, sitten taas 5v5 - kukin kausi omillaan
    for mode in ("5v5", "1v1", "5v5", "3v3", "1v1"):
        opp = eng.get_next_opponent(mode)
        assert opp is not None, f"{mode}: vastustaja puuttuu"
        eng.report_match_result(mode, True, opp)
        eng.get_standings(mode)
    games = eng.get_grand_score(le.PLAYER_ID)["games"]
    assert games == {"1v1": 2, "3v3": 1, "5v5": 2}


def test_understrength_league_start_allowed():
    """Pelaaja voi aloittaa 5v5:n yhdellä hahmolla - vihollinen saa täydet 5."""
    import main  # noqa: F401  (rekisteröi integraatiot)
    from game_manager import GameManager
    m = GameManager()
    m.mode = "League"
    m.match_mode = "5v5"
    m.battle_size = 5
    m.current_enemy_team = m.league_engine.get_next_opponent("5v5")
    hero = m.player_character
    m.start_match([hero], 5)
    assert m.match_in_progress is True
    assert len(list(m.enemy_team)) == 5, "vihollisrosteri täytetään kokoon"
    allies = [u for u in m.all_units if getattr(u, "team_color", None) == hero.team_color]
    assert len(allies) == 1, "pelaaja sai aloittaa vajaalla"


def test_chronicle_records_seasons_and_promotions_persistently():
    eng = _engine()
    opp = eng.get_next_opponent("1v1")
    eng.report_match_result("1v1", True, opp)
    entry = eng.record_chronicle("season", note="test season wrap")
    assert entry["tier"] == eng.tier and entry["season"] == 1
    assert entry["champion"]
    old_tier = eng.tier
    eng.promote_player()
    log = eng.manager.npc_state["global"]["hall_of_fame"]
    kinds = [e["type"] for e in log]
    assert "season" in kinds and "promotion" in kinds
    assert eng.tier == old_tier + 1
    assert eng.season_number == 2
    import json
    json.dumps(eng.manager.npc_state)  # tallentuu saveen sellaisenaan
    assert eng.get_chronicle(5)[0]["type"] == "promotion"  # uusin ensin


def test_scout_report_exposes_roster_and_gear_but_locks_tactics():
    eng = _engine()
    report = eng.build_scout_report("5v5")
    assert report is not None
    assert report["team_name"]
    assert len(report["roster"]) >= 3
    row = report["roster"][0]
    assert set(row) == {"name", "race", "level", "weapon", "armor"}
    assert row["weapon"], "varusteet näkyvät raportissa"
    assert "Commander" in report["locked_info"], "taktiikat lukossa tulevalle kyvylle"


def test_hall_of_fame_menu_tabs_draw():
    import main  # noqa: F401
    from game_manager import GameManager
    from menus.hall_of_fame_menu import HallOfFameMenu
    m = GameManager()
    m.league_engine.record_chronicle("season", note="smoke")
    menu = HallOfFameMenu(m)
    surf = pygame.Surface((1920, 1080))
    for tab in menu.TABS:
        menu.tab = tab
        menu.draw(surf)


def test_league_menu_scout_modal_draws():
    import main  # noqa: F401
    from game_manager import GameManager
    from menus.league_menu import LeagueMenu
    m = GameManager()
    from menus.tier0_team_intro import mark_tier0_team_intro_seen
    mark_tier0_team_intro_seen(m)  # Tier 0 -potrettiesittely nähdyksi
    menu = LeagueMenu(m)
    menu.selected_mode = "5v5"
    menu.show_scout = True
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)  # scout-raportti piirtyy ilman virheitä
    # ESC sulkee modaalin poistumatta
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert menu.show_scout is False
