# tests/test_playtest13_fixes.py
"""Pelitestikierros 13 (Grand Slam -finaali):
1) BUGI: sarjan 2. matsiin ei spawnannut ketään ja tuli automaattinen
   DEFEAT - apply_rewards tyhjensi rosterin kesken PROMOTION-sarjan
2) Bram saapuu kävellen yläkatsomosta ja juonto on ChatMenu-tyylinen
   (iso elekuva, emotiot, ääniraidat)
3) yleisö on oikeita kyläläisspritejä ja huudot ovat puhekuplia;
   laidalla yleisö kommentoi sarjatilannetta joukkueiden nimillä
4) monttuun lisätty suojaesteitä (pilarit, barrikadit, laatikot)
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))


def _promotion_manager(tmp_path=None):
    import main  # noqa: F401
    from game_manager import GameManager
    from systems.grand_slam_series import begin_series
    from leagues.league_engine import PROMOTION_BATTLE_SIZE
    m = GameManager()
    m.gold = 5000
    m.hire_recruit(0); m.hire_recruit(1)
    m.mode = "League"
    m.match_mode = "PROMOTION"
    m.league_engine._ensure_initialized()
    m.current_enemy_team = m.league_engine.get_next_opponent("5v5")
    m.battle_size = PROMOTION_BATTLE_SIZE
    begin_series(m)
    fighters = [m.player_character] + list(m.my_team)
    m.start_match(fighters, PROMOTION_BATTLE_SIZE)
    return m


# ----------------------------------------------------------------------
# 1) Sarjan 2. matsi spawnaa molemmat joukkueet
# ----------------------------------------------------------------------

def test_series_round2_spawns_both_teams(tmp_path, monkeypatch):
    import save_manager
    monkeypatch.setattr(save_manager, "SAVE_DIR", str(tmp_path))
    monkeypatch.setattr(save_manager, "SAVE_FILE",
                        str(tmp_path / "savegame.json"))
    from systems.grand_slam_series import handle_promotion_result
    m = _promotion_manager()
    assert len(m.active_player_units) > 0
    n_players = len(m.active_player_units)

    # Kierros 1 päättyy voittoon; loot-ruutu kutsuu apply_rewards +
    # handle_promotion_result TÄSSÄ järjestyksessä (post_battle_menu)
    for e in m.enemy_team:
        e.is_dead = True
    m.end_match(True)
    m.apply_rewards()
    nxt = handle_promotion_result(m)
    assert nxt == "finale_show"
    assert m.finale_series["round"] == 2

    # REGRESSIO: 2. kierroksella molemmat puolet ovat kentällä hengissä
    assert len(m.active_player_units) == n_players, \
        "pelaajan rosteri ei katoa kierrosten välillä"
    assert len(m.enemy_team) > 0, "vastustaja spawnaa 2. kierrokseen"
    my_alive = any(not u.is_dead for u in m.active_player_units)
    enemies_alive = any(not u.is_dead for u in m.enemy_team)
    assert my_alive and enemies_alive, "ei automaattista DEFEATia"
    # check_match_status ei saa päättää matsia heti
    m.check_match_status()
    assert not m.match_over


def test_normal_league_match_still_clears_roster(tmp_path, monkeypatch):
    import save_manager
    monkeypatch.setattr(save_manager, "SAVE_DIR", str(tmp_path))
    monkeypatch.setattr(save_manager, "SAVE_FILE",
                        str(tmp_path / "savegame.json"))
    import main  # noqa: F401
    from game_manager import GameManager
    m = GameManager()
    m.mode = "Arena"
    m.match_mode = ""
    m.start_match([m.player_character], 1)
    for e in m.enemy_team:
        e.is_dead = True
    m.end_match(True)
    m.apply_rewards()
    assert m.last_fighters == [], "tavallinen matsi siivoaa rosterin"


# ----------------------------------------------------------------------
# 2) Bramin sisääntulo + ChatMenu-tyylinen juonto
# ----------------------------------------------------------------------

def test_finale_bram_walk_and_portrait_dialogue():
    m = _promotion_manager()
    from menus.finale_show_menu import FinaleShowMenu
    show = FinaleShowMenu(m)
    assert show.phase == "bram_walk"
    assert show._bram_unit is not None, "Bramilla on kenttäsprite"
    assert show._announcer is not None, "portrait/voice-kansiot Bramilta"
    # Kävely etenee ja kamera seuraa
    y0 = show._bram_pos[1]
    for _ in range(40):
        show.update()
    assert show._bram_pos[1] > y0, "Bram kävelee alaspäin kohti monttua"
    surf = pygame.Surface((1920, 1080))
    show.draw(surf)
    # Loppuun -> juonto, rivit ovat (emotion, teksti) -pareja
    show.bram_t = 1.0
    show.update()
    assert show.phase == "announce"
    emotions = {emo for emo, _t in show.script}
    assert emotions & {"serious", "encouraging", "frustrated"}, \
        "juonto käyttää elekuvia (emotion per rivi)"
    assert show._portrait_for("serious") is not None, \
        "iso elekuva piirretään (fallback spriteen ilman assetteja)"
    show.draw(surf)


def test_finale_round_talk_also_walks_in():
    m = _promotion_manager()
    m.finale_series = {"round": 2, "wins": 1, "losses": 0, "mode": "round"}
    from menus.finale_show_menu import FinaleShowMenu
    show = FinaleShowMenu(m)
    assert show.phase == "bram_walk"
    show.bram_t = 1.0
    show.update()
    assert show.phase == "round_talk"
    assert any("1 - 0" in text for _e, text in show.script)


# ----------------------------------------------------------------------
# 3) Yleisö: kyläläisspritet, puhekuplat ja reunahuutelu
# ----------------------------------------------------------------------

def test_crowd_uses_villager_sprites():
    import main  # noqa: F401
    from arenas.tier_1.grand_slam_arena import GrandSlamArena
    a = GrandSlamArena()
    sprites = a._build_crowd_sprites()
    assert sprites and len(sprites) >= 10, \
        "katsomo rakentuu oikeista Villager-spriteistä"
    surf = pygame.Surface((1920, 1080))
    a.draw_background(surf, (200, 150))  # blittaa spritet kaatumatta
    assert a._crowd_sprites, "spritepankki välimuistittuu"


def test_edge_taunt_names_leading_team():
    m = _promotion_manager()
    from arenas.tier_1.grand_slam_arena import GrandSlamArena, PIT
    a = m.current_arena
    assert isinstance(a, GrandSlamArena)
    a.manager = m
    m.finale_series = {"round": 2, "wins": 1, "losses": 0, "mode": "round"}
    pc = m.player_character
    pc.rect.center = (PIT.x + 60, PIT.centery)  # aivan laidassa
    a._next_taunt = 0
    n0 = len(a.crowd_bubbles)
    a._update_edge_taunt([pc])
    assert len(a.crowd_bubbles) == n0 + 1, "laidalla yleisö huutelee"
    assert a._next_taunt > 0, "huutelulla on cooldown"
    # Kaukana keskellä ei huudella
    a._next_taunt = 0
    pc.rect.center = PIT.center
    a._update_edge_taunt([pc])
    assert len(a.crowd_bubbles) == n0 + 1, "keskellä ei reunahuutelua"


def test_crowd_bubbles_render_as_speech_bubbles():
    import main  # noqa: F401
    from arenas.tier_1.grand_slam_arena import GrandSlamArena
    a = GrandSlamArena()
    a.crowd_bubbles.append(["MUCK-FORD!", 700, 300, 100, (250, 226, 160)])
    surf = pygame.Surface((1920, 1080))
    a.draw_foreground(surf, (0, 0))  # kupla + häntä piirtyvät kaatumatta


# ----------------------------------------------------------------------
# 4) Suojaesteet montussa
# ----------------------------------------------------------------------

def test_pit_has_cover_obstacles():
    from arenas.tier_1.grand_slam_arena import GrandSlamArena, PIT
    a = GrandSlamArena()
    assert len(a._cover) >= 6, "monttu ei ole enää paljas"
    kinds = {k for _r, k in a._cover}
    assert kinds == {"pillar", "barricade", "crates"}
    for rect, _k in a._cover:
        assert PIT.contains(rect), "esteet ovat montun sisällä"
        # Spawn-kaistat (porttien edustat) pysyvät vapaina
        assert rect.right < PIT.right - 120 and rect.x > PIT.x + 120
    # Seinät + esteet törmäysryhmässä
    assert len(a.obstacles) >= 12
    surf = pygame.Surface((1920, 1080))
    a.draw_background(surf, (600, 400))  # esteiden visuaalit pohjassa
