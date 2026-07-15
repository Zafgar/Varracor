# tests/test_playtest30_fixes.py
"""Pelitestikierros 30: yhtenäinen quest tracker.
1) Erillinen "FOUND AN ARENA TEAM" -paneeli korvattu journal-questilla
2) Areenatiimin perustus on main-quest, aktiivinen kylään saavuttaessa
3) Tavoitteiden valmius lasketaan elävästi (velka/maine/voitot/maksu)
4) Rekisteröinnin jälkeen quest siirtyy DONE-välilehdelle
5) HUD-tracker on siirrettävissä ja sijainti säilyy
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


def _arrive(m):
    from systems.muckford_opening_core import _opening, sync_arena_team_quest
    _opening(m)["intro_complete"] = True
    sync_arena_team_quest(m)


# ----------------------------------------------------------------------
# 1) + 2) Quest olemassa, aktivoituu kylään saavuttaessa
# ----------------------------------------------------------------------

def test_arena_team_quest_active_on_arrival():
    from quest_system import quest_manager
    m = _manager()
    q = quest_manager.get_quest("found_arena_team")
    assert q is not None
    assert q.category == "main"
    assert q.giver == "Bram Mudhand"
    assert len(q.objectives) == 5
    _arrive(m)
    assert q.status == "active"
    assert quest_manager.is_tracked("found_arena_team")


# ----------------------------------------------------------------------
# 3) Elävät tavoitetilat
# ----------------------------------------------------------------------

def test_objective_states_reflect_live_progress():
    from quest_system import quest_manager
    from systems.muckford_opening_core import (
        _opening, arena_team_objective_states)
    m = _manager()
    _arrive(m)
    m.innkeeper_debt = 25
    m.reputation = 0
    m.gold = 0
    _opening(m)["creature_wins"] = 0
    assert arena_team_objective_states(m) == [False, False, False, False, False]
    # Täytä vaatimukset
    m.innkeeper_debt = 0
    m.reputation = 8
    _opening(m)["creature_wins"] = 3
    m.gold = 30
    assert arena_team_objective_states(m) == [True, True, True, True, False]

    q = quest_manager.get_quest("found_arena_team")
    # HUD näyttää ensimmäisen keskeneräisen (tässä rekisteröinti)
    assert "Register" in m._quest_current_objective(q)


# ----------------------------------------------------------------------
# 4) Rekisteröinti -> DONE
# ----------------------------------------------------------------------

def test_registration_completes_and_moves_to_done():
    from quest_system import quest_manager
    from systems.muckford_opening_core import _opening, sync_arena_team_quest
    m = _manager()
    _arrive(m)
    _opening(m)["team_registered"] = True
    sync_arena_team_quest(m)
    q = quest_manager.get_quest("found_arena_team")
    assert q.status == "completed" and q.is_finished
    done = [x.id for x in m._journal_quests_for_tab("completed")]
    assert "found_arena_team" in done
    assert "found_arena_team" not in \
        [x.id for x in m._journal_quests_for_tab("main")]


def test_journal_draws_arena_team_objectives():
    m = _manager()
    _arrive(m)
    m.show_full_journal = True
    m.journal_tab = "main"
    m.journal_selected = "found_arena_team"
    surf = pygame.Surface((1920, 1080))
    m._draw_full_journal(surf)  # ei kaadu; piirtää tavoiteruudukon
    assert any(qid == "found_arena_team"
               for _, qid in m._journal_ui["rows"])


# ----------------------------------------------------------------------
# 5) Siirrettävä HUD-tracker + persistenssi
# ----------------------------------------------------------------------

def test_hud_tracker_is_draggable_and_persists(tmp_path, monkeypatch):
    import systems.ui_prefs as ui_prefs
    opts = tmp_path / "options.json"
    monkeypatch.setattr(ui_prefs, "OPTIONS_FILE", str(opts))
    m = _manager()
    _arrive(m)
    m.show_quest_journal = True
    surf = pygame.Surface((1920, 1080))
    m._draw_quest_journal(surf)
    handle = m._journal_drag_handle
    assert handle is not None
    start = handle.center
    m.handle_ui_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, pos=start, button=1), "muckford_city")
    m.handle_ui_event(pygame.event.Event(
        pygame.MOUSEMOTION, pos=(start[0] - 300, start[1] + 200)),
        "muckford_city")
    m.handle_ui_event(pygame.event.Event(
        pygame.MOUSEBUTTONUP, pos=(start[0] - 300, start[1] + 200),
        button=1), "muckford_city")
    assert not m._journal_dragging
    assert m.journal_tracker_pos is not None
    # Sijainti tallentui optioihin
    assert ui_prefs.get_quest_tracker_pos() == tuple(m.journal_tracker_pos)


def test_eye_button_still_toggles_after_drag_handle_added():
    m = _manager()
    _arrive(m)
    m.show_quest_journal = True
    surf = pygame.Surface((1920, 1080))
    m._draw_quest_journal(surf)
    eye = m._journal_toggle_rect
    before = m.show_quest_journal
    res = m.handle_ui_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, pos=eye.center, button=1), "muckford_city")
    assert res is True and m.show_quest_journal != before
