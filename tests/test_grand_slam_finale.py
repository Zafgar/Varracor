# tests/test_grand_slam_finale.py
"""Grand Slam -finaali: iso stadionareena jujuineen, cinematic-juonto,
best-of-3 -sarja (promotio vasta 2 voitosta) ja mestaruusjuhla."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from settings import SCREEN_WIDTH, SCREEN_HEIGHT


def _promotion_manager():
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


def test_grand_slam_arena_is_big_with_stands_and_walls():
    from arenas.tier_1.grand_slam_arena import GrandSlamArena, PIT
    a = GrandSlamArena()
    assert a.width > SCREEN_WIDTH and a.height > SCREEN_HEIGHT
    assert len(a._seats) > 200, "katsomoissa on yleisöä"
    assert len(a.obstacles) >= 6, "montun seinät estävät karkaamisen"
    assert a.spawn_points["left"][0] < PIT.centerx < a.spawn_points["right"][0]
    surf = pygame.Surface((1920, 1080))
    a.draw_background(surf, (200, 150))
    a.draw_foreground(surf, (200, 150))


def test_fire_ring_twist_damages_outside_ring():
    import main  # noqa: F401
    from arenas.tier_1.grand_slam_arena import GrandSlamArena, PIT
    from units.human import Human
    from settings import GREEN
    a = GrandSlamArena()
    a.set_twist(3)
    assert a.twist == "fire_ring" and a.fire_radius > 0
    inside = Human("In", 0, 0, GREEN, "Common")
    outside = Human("Out", 0, 0, GREEN, "Common")
    inside.rect.center = PIT.center
    outside.rect.center = (PIT.centerx + 900, PIT.centery)
    hp_in, hp_out = inside.current_hp, outside.current_hp
    for _ in range(120):
        a.update([inside, outside])
    assert inside.current_hp == hp_in, "renkaan sisällä on turvassa"
    assert outside.current_hp < hp_out, "renkaan ulkopuolella palaa"


def test_debris_twist_spawns_and_hits():
    import main  # noqa: F401
    from arenas.tier_1.grand_slam_arena import GrandSlamArena, PIT
    from units.human import Human
    from settings import GREEN
    import random
    a = GrandSlamArena()
    a.set_twist(2)
    a.rng = random.Random(3)
    dummy = Human("Dummy", 0, 0, GREEN, "Common")
    hp0 = dummy.current_hp
    hit = False
    for _ in range(4000):
        if a._debris and not a._debris[0]["hit"]:
            dummy.rect.center = (a._debris[0]["x"], a._debris[0]["y"])
        a.update([dummy])
        if dummy.current_hp < hp0:
            hit = True
            break
    assert hit, "romu osuu varoitusringin kohdalle"


def test_promotion_uses_grand_slam_arena_and_spawns():
    m = _promotion_manager()
    from arenas.tier_1.grand_slam_arena import GrandSlamArena
    assert isinstance(m.current_arena, GrandSlamArena)
    assert m.current_arena.twist == "none"  # kierros 1 = puhdas mittelö
    # Yksiköt spawnaavat montun sisään, eivät ruutukoordinaatteihin
    for u in m.active_player_units:
        assert u.rect.x > 200


def test_finale_show_phases_intro_to_battle():
    m = _promotion_manager()
    from menus.finale_show_menu import FinaleShowMenu
    show = FinaleShowMenu(m)
    assert show.phase == "announce"
    assert any("GRAND SLAM" in line for line in show.script)
    surf = pygame.Surface((1920, 1080))
    show.update(); show.draw(surf)
    # Klikkaile juonto läpi
    ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)
    for _ in range(len(show.script)):
        show.handle_event(ev)
    assert show.phase == "walkin"
    show.draw(surf)
    # Skippaa kävely, sitten splash pyörii loppuun
    show.handle_event(ev)
    for _ in range(400):
        show.update()
        if show.next_state:
            break
    assert show.next_state == "battle"
    assert m.camera_locked is True, "kamera palautuu taisteluun"


def test_best_of_three_series_resolution():
    m = _promotion_manager()
    from systems.grand_slam_series import handle_promotion_result, get_series
    tier0 = m.league_engine.tier

    # Kierros 1: voitto -> uusi kierros käynnistyy, EI promootiota vielä
    m.match_result = "VICTORY"
    nxt = handle_promotion_result(m)
    assert nxt == "finale_show"
    assert get_series(m)["round"] == 2
    assert m.league_engine.tier == tier0, "1 voitto ei vielä promotoi"
    assert m.current_arena.twist == "debris", "kierroksella 2 on juju"
    for u in m.active_player_units:
        assert not u.is_dead and u.current_hp == u.max_hp, "revive kierrosten välillä"

    # Kierros 2: voitto -> sarja 2-0, promootio + mestaruusjuhla
    m.match_result = "VICTORY"
    nxt = handle_promotion_result(m)
    assert nxt == "finale_show"
    assert get_series(m)["mode"] == "champion"
    assert m.league_engine.tier == tier0 + 1, "promootio vasta 2 voitosta"

    # Champion-vaihe ohjaa seremoniaan
    from menus.finale_show_menu import FinaleShowMenu
    show = FinaleShowMenu(m)
    assert show.phase == "champion"
    surf = pygame.Surface((1920, 1080))
    show.update(); show.draw(surf)
    show.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    assert show.next_state == "promotion_ceremony"


def test_series_lost_returns_to_league():
    m = _promotion_manager()
    from systems.grand_slam_series import handle_promotion_result
    m.match_result = "DEFEAT"
    assert handle_promotion_result(m) == "finale_show"  # 0-1, jatkuu
    m.match_result = "DEFEAT"
    assert handle_promotion_result(m) == "league"       # 0-2, sarja ohi
    assert m.finale_series is None
