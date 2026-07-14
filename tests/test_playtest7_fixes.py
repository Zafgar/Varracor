# tests/test_playtest7_fixes.py
"""Pelitestikierros 7 (jatkokehitys): mestaruus kirjautuu urotyöksi,
Arena Hallin vitriini näyttää saavutukset ja tienviitat avaavat
maailmankartan reitit pelikentältä."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1920, 1080))


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


def test_grand_slam_win_records_champion_deed():
    from systems.grand_slam_series import begin_series, get_series, \
        handle_promotion_result
    m = _manager()
    begin_series(m)
    series = get_series(m)
    series["wins"] = 1
    m.match_result = "VICTORY"
    m.last_fighters = []
    result = handle_promotion_result(m)
    assert result == "finale_show"
    assert get_series(m)["mode"] == "champion"
    deeds = m.get_deeds()
    assert any(str(d["id"]).endswith("_champion") for d in deeds), \
        "mestaruus kirjautuu urotyöksi"
    assert any("championship" in d["text"] for d in deeds)


def test_trophy_case_panel():
    m = _manager()
    m.record_deed("tier0_champion",
                  "won the Grand Slam and claimed the Tier 0 championship")
    m.record_deed("mine_broodmother",
                  "slew the Cave Broodmother and opened the deep mine")
    from citys.mucford.city_interiors import ArenaHallMenu
    hall = ArenaHallMenu(m)
    hall.on_enter()
    # E vitriinillä avaa paneelin
    hall.player.rect.center = (hall.trophy_case.rect.centerx,
                               hall.trophy_case.rect.bottom + 40)
    hall.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e,
                                         unicode="e"))
    assert hall.show_trophies is True
    assert hall.consumes_escape(), "paneeli haluaa ESC:n itselleen"
    surf = pygame.Surface((1920, 1080))
    hall.draw(surf)
    # ESC sulkee
    hall.handle_event(pygame.event.Event(pygame.KEYDOWN,
                                         key=pygame.K_ESCAPE))
    assert hall.show_trophies is False


def test_road_signposts_open_world_map():
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from assets.tiles.muckford_objects import RoadSignpost
    city = MuckfordCityMenu(m)
    city.on_enter()
    signs = [p for p in city.arena.props if isinstance(p, RoadSignpost)]
    assert len(signs) == 2, "viitta kadun molemmissa päissä"
    sign = signs[0]
    city.player.rect.center = sign.rect.center
    city.next_state = None
    assert city._try_interact_prop(sign, check_collision=True) is True
    assert city.next_state == "world_map", "viitta avaa maailmankartan"
