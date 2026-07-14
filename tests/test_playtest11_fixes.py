# tests/test_playtest11_fixes.py
"""Pelitestikierros 11:
1) taistelun efektit (ammukset, AoE, tekstit) eivät saa vuotaa seuraavaan
   matsiin/mappiin ("isku siirtyy toiseen map?")
2) liigamoottorin lämmitys loading-ruudussa -> Shanty Yardin ensiavaus
   ei enää jäädy ("tuntui crashilta")
3) sisätilojen in-game dialogi piirretään ("place wagers ei tee mitään",
   "NPC:lle ei voi puhua")
4) vedonlyönnin tierikohtaiset maksimipanokset + dominanssikertoimet
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))


def _manager():
    import main  # noqa: F401 - asentaa integraatiot
    from game_manager import GameManager
    return GameManager()


def _dummy_sprite():
    s = pygame.sprite.Sprite()
    s.image = pygame.Surface((4, 4))
    s.rect = s.image.get_rect()
    return s


# ----------------------------------------------------------------------
# 1) VFX ei vuoda taistelusta toiseen
# ----------------------------------------------------------------------

def test_start_match_clears_leftover_vfx():
    m = _manager()
    m.vfx.particles.add(_dummy_sprite())
    m.vfx.floor_particles.add(_dummy_sprite())
    m.vfx.texts.add(_dummy_sprite())
    m.mode = "Arena"
    m.start_match([m.player_character], 1)
    assert len(m.vfx.particles) == 0, "ammukset/efektit tyhjennetty"
    assert len(m.vfx.floor_particles) == 0, "lattiaefektit tyhjennetty"
    assert len(m.vfx.texts) == 0, "leijuvat tekstit tyhjennetty"


# ----------------------------------------------------------------------
# 2) Liigan lämmitys askel kerrallaan (loading-ruutu)
# ----------------------------------------------------------------------

def test_league_warm_up_steps():
    from leagues.league_engine import LeagueEngine
    eng = LeagueEngine()
    assert not eng._initialized
    assert eng.warm_up_step() is False, "1. askel: yksi kausi"
    assert len(eng.seasons) == 1
    assert eng.warm_up_step() is False, "2. askel: toinen kausi"
    assert eng.warm_up_step() is True, "3. askel: valmis"
    assert set(eng.seasons) == {"1v1", "3v3", "5v5"}
    # Valmiin moottorin askel on no-op
    assert eng.warm_up_step() is True
    assert len(eng.seasons) == 3


def test_loading_screen_prewarms_league():
    from menus.loading_screen import LoadingScreen
    m = _manager()
    m.league_engine._initialized = False
    m.league_engine.seasons.clear()
    m.loading_target_state = "arena_hall"
    screen = LoadingScreen(m)
    for _ in range(160):
        screen.update()
    assert m.league_engine._initialized, "loading-ruutu lämmitti liigan"
    assert screen.next_state == "arena_hall"


# ----------------------------------------------------------------------
# 3) Sisätilan dialogi piirretään (näkymätön dialogi söi syötteet)
# ----------------------------------------------------------------------

def test_interior_draws_active_dialogue():
    from citys.mucford.city_interiors import ArenaHallMenu
    m = _manager()
    hall = ArenaHallMenu(m)
    hall.on_enter()
    called = {"n": 0}
    orig = m._draw_in_game_dialogue
    m._draw_in_game_dialogue = lambda s: called.__setitem__("n", called["n"] + 1)
    surf = pygame.Surface((1920, 1080))
    hall.draw(surf)
    assert called["n"] == 0, "ei dialogia -> ei piirtoa"
    hall._open_bet_dialogue()
    assert m.active_dialogue is not None
    hall.draw(surf)
    assert called["n"] == 1, "aktiivinen dialogi piirretään sisätilassa"
    m._draw_in_game_dialogue = orig
    # Oikea piirtokin toimii kaatumatta
    hall.draw(surf)
    m.active_dialogue = None


def test_interior_guard_talk_opens_visible_dialogue():
    from citys.mucford.city_interiors import ArenaHallMenu
    m = _manager()
    hall = ArenaHallMenu(m)
    hall.on_enter()
    guard = next(u for u, k in hall.hall_npcs if k == "guard")
    hall.player.rect.center = (guard.rect.centerx, guard.rect.bottom + 40)
    hall.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e,
                                         unicode="e"))
    assert m.active_dialogue is not None, "E avaa vartijan dialogin"
    surf = pygame.Surface((1920, 1080))
    hall.draw(surf)  # dialogi piirtyy kaatumatta
    m.active_dialogue = None


# ----------------------------------------------------------------------
# 4) Vedonlyönnin rajat ja kertoimet
# ----------------------------------------------------------------------

def test_wager_odds_clamped_by_dominance():
    from citys.mucford.city_interiors import wager_odds
    m = _manager()
    # Alle 3 matsia -> neutraali 50 % -> x1.5
    m.season_wins, m.season_losses = 1, 0
    assert wager_odds(m) == 1.5
    # Tasainen kausi -> x1.5
    m.season_wins, m.season_losses = 5, 5
    assert wager_odds(m) == 1.5
    # Dominoiva suosikki -> pohjakerroin
    m.season_wins, m.season_losses = 12, 0
    assert wager_odds(m) == pytest.approx(1.15)
    # Altavastaaja -> katto
    m.season_wins, m.season_losses = 0, 12
    assert wager_odds(m) == pytest.approx(2.4)


def test_tier1_table_limit_filters_big_bets():
    from citys.mucford.city_interiors import (ArenaHallMenu,
                                              WAGER_MAX_BY_TIER)
    assert WAGER_MAX_BY_TIER[1] == 50, "Shanty Yardissa ei liiku isot rahat"
    m = _manager()
    m.league_engine.tier = 1
    m.gold = 1000
    hall = ArenaHallMenu(m)
    hall.on_enter()
    hall._open_bet_dialogue()
    actions = [o.get("action", "") for o in m.active_dialogue["options"]]
    assert "hall_bet_20" in actions
    assert "hall_bet_50" in actions
    assert "hall_bet_100" not in actions, "100 SP ylittää tierin 1 katon"
    m.active_dialogue = None
    m.dialogue_action_handler = None


def test_bet_stores_odds_and_pays_by_multiplier():
    from citys.mucford.city_interiors import ArenaHallMenu, wager_odds
    m = _manager()
    m.gold = 100
    # Dominoiva joukkue saa laihan kertoimen
    m.season_wins, m.season_losses = 12, 0
    mult = wager_odds(m)
    hall = ArenaHallMenu(m)
    hall.on_enter()
    hall._open_bet_dialogue()
    hall._on_bet_action("hall_bet_20")
    assert m.gold == 80
    assert m.active_bet == {"amount": 20, "mult": mult}
    m.mode = "League"
    m.current_enemy_team = None
    m.end_match(True)
    assert m.gold == 80 + int(20 * mult), "voitto maksaa panos*kerroin"
    assert m.active_bet is None


def test_lost_league_bet_is_kept_by_house():
    from citys.mucford.city_interiors import ArenaHallMenu
    m = _manager()
    m.gold = 100
    hall = ArenaHallMenu(m)
    hall.on_enter()
    hall._open_bet_dialogue()
    hall._on_bet_action("hall_bet_20")
    assert m.gold == 80
    m.mode = "League"
    m.current_enemy_team = None
    m.end_match(False)
    assert m.gold == 80, "hävitty panos jää talolle"
    assert m.active_bet is None
