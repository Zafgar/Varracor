# tests/test_playtest15_fixes.py
"""Pelitestikierros 15:
1) Vintin vedonlyöntitoimisto: kertoimet ELO:sta, kuponki mistä tahansa
   tiimistä, useita avoimia vetoja, laiska ratkaisu kierroksen tuloksista
2) BUGI: dialogin jälkeen E lakkasi toimimasta sisätiloissa
   (dialogue_cooldown ei koskaan vähentynyt)
3) BUGI: lataus heitti aina Sunk Caskin ovelle - kaupunkisijainti
   tallentuu ja palautuu
4) etäisyysvaimennettu ääni (play_sound_at)
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
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


# ----------------------------------------------------------------------
# 1) Vedonlyöntitoimisto
# ----------------------------------------------------------------------

def test_odds_favor_underdog():
    from systems import betting
    m = _manager()
    m.league_engine._ensure_initialized()
    season = m.league_engine.seasons["3v3"]
    a, b = betting.fixtures(season)[0]
    # Vääristä ELOa: a on ylivoimainen suosikki
    season.records[a].elo = 1400
    season.records[b].elo = 1000
    fav = betting.odds_multiplier(season, a, b)
    dog = betting.odds_multiplier(season, b, a)
    assert fav < dog, "altavastaajalle isompi kerroin"
    assert 1.05 <= fav < 1.5
    assert dog > 2.0


def test_can_bet_on_other_teams_and_sim_resolves():
    from systems import betting
    m = _manager()
    m.gold = 200
    m.league_engine._ensure_initialized()
    season = m.league_engine.seasons["5v5"]
    # Valitse pari jossa pelaaja EI pelaa
    pair = next(p for p in betting.fixtures(season) if "PLAYER" not in p)
    tid = pair[0]
    ok, msg = betting.place_bet(m, "5v5", tid, 30)
    assert ok, msg
    assert m.gold == 170
    assert len(m.open_bets) == 1
    # Sama tiimi samalle kierrokselle ei kelpaa toista kertaa
    ok2, msg2 = betting.place_bet(m, "5v5", tid, 10)
    assert not ok2 and "already" in msg2.lower()
    # Simuloi kierros -> kuponki ratkeaa suuntaan tai toiseen
    season._pending_matches = list(season._current_pairings)
    season.resolve_pending()
    gold_before = m.gold
    msgs = betting.check_open_bets(m)
    assert msgs, "pelattu kierros ratkaisee kupongin"
    assert m.open_bets == []
    b_won = m.gold > gold_before
    assert b_won or m.gold == gold_before, "voitto maksaa, häviö ei palauta"


def test_open_bets_cap_and_persistence(tmp_path, monkeypatch):
    import save_manager
    monkeypatch.setattr(save_manager, "SAVE_DIR", str(tmp_path))
    monkeypatch.setattr(save_manager, "SAVE_FILE",
                        str(tmp_path / "savegame.json"))
    from systems import betting
    m = _manager()
    m.gold = 10000
    m.league_engine._ensure_initialized()
    placed = 0
    for mode in betting.MODES:
        season = m.league_engine.seasons[mode]
        for a, b in betting.fixtures(season):
            for tid in (a, b):
                ok, _ = betting.place_bet(m, mode, tid, 5)
                if ok:
                    placed += 1
    assert placed == betting.MAX_OPEN_BETS, "avoimien kuponkien katto"
    # Kupongit säilyvät savessa
    assert save_manager.save_game(m)
    m2 = _manager()
    assert save_manager.load_game(m2)
    assert len(m2.open_bets) == betting.MAX_OPEN_BETS
    assert m2.open_bets[0]["team_name"]


def test_betting_office_menu_flow():
    from menus.betting_menu import BettingOfficeMenu
    m = _manager()
    m.gold = 500
    m.league_engine._ensure_initialized()
    menu = BettingOfficeMenu(m)
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)
    assert menu.tab_rects and menu.team_rects, "ottelurivit piirtyvät"
    # Klikkaa ensimmäistä tiimiä -> kuponki auki
    cell, tid, oid = menu.team_rects[0]
    menu.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                         pos=cell.center, button=1))
    assert menu.selected == (menu.mode, tid, oid)
    menu.draw(surf)
    assert "place" in menu.btn_rects
    # PLACE BET
    menu.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, pos=menu.btn_rects["place"].center,
        button=1))
    assert len(m.open_bets) == 1
    assert m.gold == 500 - m.open_bets[0]["amount"]
    menu.draw(surf)  # MY TICKETS -paneeli piirtyy
    # ESC palaa halliin
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN,
                                         key=pygame.K_ESCAPE))
    assert menu.next_state == "arena_hall"


# ----------------------------------------------------------------------
# 2) E toimii dialogin jälkeen sisätiloissa
# ----------------------------------------------------------------------

def test_interior_interact_works_after_dialogue():
    from citys.mucford.city_interiors import ArenaHallMenu
    m = _manager()
    hall = ArenaHallMenu(m)
    hall.on_enter()
    guard = next(u for u, k in hall.hall_npcs if k == "guard")
    hall.player.rect.center = (guard.rect.centerx, guard.rect.bottom + 40)
    e_key = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e, unicode="e")
    hall.handle_event(e_key)
    assert m.active_dialogue is not None
    # Sulje dialogi E:llä (handle_dialogue_event asettaa cooldownin 20)
    assert m.handle_dialogue_event(e_key)
    assert m.active_dialogue is None
    assert m.dialogue_cooldown > 0
    # REGRESSIO: cooldown hupenee sisätilan updatessa
    for _ in range(60):
        hall.update()
    assert m.dialogue_cooldown == 0, "cooldown ei jää jumiin"
    hall.handle_event(e_key)
    assert m.active_dialogue is not None, "E toimii taas dialogin jälkeen"
    m.active_dialogue = None
    m.dialogue_cooldown = 0


# ----------------------------------------------------------------------
# 3) Kaupunkisijainti savessa
# ----------------------------------------------------------------------

def test_city_position_saved_and_restored(tmp_path, monkeypatch):
    import save_manager
    monkeypatch.setattr(save_manager, "SAVE_DIR", str(tmp_path))
    monkeypatch.setattr(save_manager, "SAVE_FILE",
                        str(tmp_path / "savegame.json"))
    m = _manager()
    m.last_city_pos = (2345, 1678)
    assert save_manager.save_game(m)
    m2 = _manager()
    assert save_manager.load_game(m2)
    assert m2.city_spawn_point == ("pos", (2345, 1678))
    # Kaupungin on_enter kunnioittaa sijaintia (ei tavernan ovea)
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(m2)
    city.on_enter()
    assert city.player.rect.center == (2345, 1678), \
        "lataus palauttaa tallennettuun kohtaan, ei Sunk Caskin eteen"


def test_city_on_enter_without_saved_pos_uses_tavern():
    m = _manager()
    m.city_spawn_point = None
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(m)
    city.on_enter()  # oletusspawn (taverna) toimii yhä kaatumatta


# ----------------------------------------------------------------------
# 4) Etäisyysvaimennettu ääni
# ----------------------------------------------------------------------

def test_play_sound_at_attenuates_with_distance():
    from sound_manager import sound_system
    m = _manager()
    m.player_character.rect.center = (500, 500)

    class _FakeChannel:
        def __init__(self):
            self.volume = None

        def set_volume(self, v):
            self.volume = v

    class _FakeSound:
        def __init__(self):
            self.ch = None

        def play(self, loops=0):
            self.ch = _FakeChannel()
            return self.ch

    fake = _FakeSound()
    old_enabled = sound_system.sound_enabled
    sound_system.sound_enabled = True
    sound_system.sounds["_test_axe"] = fake
    try:
        near = sound_system.play_sound_at("_test_axe", 560, 500, m)
        v_near = near.volume
        far = sound_system.play_sound_at("_test_axe", 1400, 500, m)
        v_far = far.volume
        gone = sound_system.play_sound_at("_test_axe", 5000, 500, m)
        assert v_near > v_far > 0, "lähellä kovempaa kuin kaukana"
        assert gone is None, "kantaman ulkopuolella ei soi lainkaan"
    finally:
        sound_system.sounds.pop("_test_axe", None)
        sound_system.sound_enabled = old_enabled
