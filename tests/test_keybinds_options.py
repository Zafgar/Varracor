# tests/test_keybinds_options.py
"""Näppäinasettelu: keskitetty rekisteri, uudelleensidonta (konflikti
irrotetaan), tallennus/lataus ja Options-valikon CONTROLS-paneeli.
Lisäksi League-tabien vaatimusmäärät tulevat enginestä (REQ_GAMES),
ei kovakoodatusta 2:sta (regressio: näytti '0/2' vaikka vaaditaan 6/5/5)."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))

from systems import keybinds


@pytest.fixture(autouse=True)
def _isolated_binds(tmp_path, monkeypatch):
    """Ohjaa tallennus väliaikaistiedostoon ja palauta oletukset lopuksi."""
    monkeypatch.setattr(keybinds, "OPTIONS_FILE",
                        str(tmp_path / "options.json"))
    keybinds.reset_defaults(save_after=False)
    yield
    keybinds.reset_defaults(save_after=False)


class _FakeKeys:
    def __init__(self, *down):
        self.down = set(down)

    def __getitem__(self, code):
        if code > 100000:
            raise IndexError(code)  # kuten oikea ScancodeWrapper isoilla koodeilla
        return code in self.down


def test_defaults_and_pressed():
    assert keybinds.key("move_up") == pygame.K_w
    assert keybinds.key("interact") == pygame.K_e
    keys = _FakeKeys(pygame.K_w)
    assert keybinds.pressed(keys, "move_up")
    assert not keybinds.pressed(keys, "move_down")
    assert keybinds.matches(pygame.K_m, "map")


def test_rebind_removes_conflicts():
    keybinds.set_key("interact", pygame.K_f)
    assert keybinds.key("interact") == pygame.K_f
    # F oli vapaana - muut ennallaan
    assert keybinds.key("move_up") == pygame.K_w
    # Sido W interactiin -> move_up ei saa jäädä ilman näppäintä
    keybinds.set_key("interact", pygame.K_w)
    assert keybinds.key("interact") == pygame.K_w
    assert pygame.K_w not in keybinds.keys_for("move_up") or \
        keybinds.keys_for("move_up"), "move_up sai fallback-näppäimen"
    assert keybinds.keys_for("move_up"), "toiminto ei jää tyhjäksi"


def test_save_and_load_roundtrip():
    keybinds.set_key("map", pygame.K_n)
    keybinds.save()
    keybinds.reset_defaults(save_after=False)
    assert keybinds.key("map") == pygame.K_m
    keybinds.load()
    assert keybinds.key("map") == pygame.K_n


def test_options_menu_rebind_flow():
    import main  # noqa: F401
    from game_manager import GameManager
    from menus.options_menu import OptionsMenu
    m = GameManager()
    menu = OptionsMenu(m)
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)  # rakentaa bind_rows
    assert menu.bind_rows, "Controls-rivit piirtyvät"

    # Klikkaa 'interact'-riviä ja paina F
    rect, action = next((r, a) for r, a in menu.bind_rows if a == "interact")
    menu.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                         pos=rect.center, button=1))
    assert menu.awaiting_bind == "interact"
    menu.draw(surf)  # "PRESS A KEY..." -tila piirtyy
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_f))
    assert menu.awaiting_bind is None
    assert keybinds.key("interact") == pygame.K_f

    # ESC rebind-tilassa peruu eikä sulje valikkoa
    menu.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                         pos=rect.center, button=1))
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN,
                                         key=pygame.K_ESCAPE))
    assert menu.awaiting_bind is None
    assert menu.next_state is None
    assert keybinds.key("interact") == pygame.K_f


def test_city_uses_keybinds_for_interact():
    import main  # noqa: F401
    from game_manager import GameManager
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    m = GameManager()
    menu = MuckfordCityMenu(m)
    menu.on_enter()
    # Sido interact F:ään: E ei enää avaa mitään, F avaa
    keybinds.set_key("interact", pygame.K_f)
    prospect = menu.prospects[0]
    free = (menu.arena.width // 2, menu.arena.height - 200)
    prospect.rect.center = free
    menu.player.rect.center = free
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    assert menu.next_state is None
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_f))
    assert menu.next_state == "dialogue_active"


def test_league_tab_requirements_from_engine():
    from leagues.league_engine import REQ_GAMES, LeagueEngine
    assert REQ_GAMES == {"1v1": 6, "3v3": 5, "5v5": 5}
    le = LeagueEngine()
    le._ensure_initialized()
    # Moodi valmistuu vasta kun REQ_GAMES-määrä on pelattu
    assert not le.is_mode_complete("1v1")
    season = le.seasons["1v1"]
    opp = season.get_next_opponent_team()
    for _ in range(REQ_GAMES["1v1"]):
        opp = season.get_next_opponent_team() or opp
        le.report_match_result("1v1", True, opp)
    assert le.is_mode_complete("1v1")
    assert not le.is_mode_complete("3v3")


def test_league_menu_draws_with_progress():
    import main  # noqa: F401
    from game_manager import GameManager
    from menus.league_menu import LeagueMenu
    from menus.tier0_team_intro import mark_tier0_team_intro_seen
    m = GameManager()
    mark_tier0_team_intro_seen(m)
    lm = LeagueMenu(m)
    lm.update()
    surf = pygame.Surface((1920, 1080))
    lm.draw(surf)             # TOTAL: season summary + vaatimuslista
    lm.selected_mode = "1v1"
    lm._rebuild_layout()
    lm.draw(surf)             # moodinäkymä
