# tests/test_playtest27_fixes.py
"""Pelitestikierros 27: kunnollinen RPG-questijournal.
1) Questeilla kategoria (main/side), tavoitteet ja tehtävänantaja
2) Täysi journal: välilehdet MAIN / SIDE / DONE, tehtävätiedot
3) Seuranta: pelaaja voi valita mitkä questit näkyvät HUD-seurannassa
4) HUD-tracker näyttää VAIN seuratut; seuranta persistoi saveen
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
# 1) Kategoriat + metadata
# ----------------------------------------------------------------------

def test_quests_have_categories_and_metadata():
    from quest_system import quest_manager
    rk = quest_manager.quests["hunt_01"]
    assert rk.category == "main"
    assert rk.objectives, "main-questilla vaiheittaiset tavoitteet"
    assert rk.giver == "Griznak the Shifty"
    manure = quest_manager.quests["quest_manure_cleanup"]
    assert manure.category == "side"
    assert manure.giver == "Farmer Gus"


# ----------------------------------------------------------------------
# 2) Välilehtijaottelu
# ----------------------------------------------------------------------

def test_journal_tabs_split_main_side_completed():
    from quest_system import quest_manager
    m = _manager()
    quest_manager.accept_quest("hunt_01")
    quest_manager.accept_quest("quest_manure_cleanup")
    main = [q.id for q in m._journal_quests_for_tab("main")]
    side = [q.id for q in m._journal_quests_for_tab("side")]
    done = [q.id for q in m._journal_quests_for_tab("completed")]
    assert "hunt_01" in main
    assert "quest_manure_cleanup" in side
    assert "hunt_01" not in side
    # Kun quest on lunastettu -> siirtyy DONE-välilehdelle
    quest_manager.quests["quest_manure_cleanup"].status = "completed"
    quest_manager.quests["quest_manure_cleanup"].is_finished = True
    done = [q.id for q in m._journal_quests_for_tab("completed")]
    assert "quest_manure_cleanup" in done
    assert "quest_manure_cleanup" not in \
        [q.id for q in m._journal_quests_for_tab("side")]


def test_full_journal_opens_and_draws():
    from quest_system import quest_manager
    m = _manager()
    quest_manager.accept_quest("hunt_01")
    m.show_full_journal = True
    m._journal_sync_selection()
    assert m.journal_selected == "hunt_01"
    surf = pygame.Surface((1920, 1080))
    m._draw_full_journal(surf)
    assert len(m._journal_ui["tabs"]) == 3
    assert m._journal_ui["rows"], "main-välilehdellä on rivi"
    assert m._journal_ui["track_btn"] is not None


# ----------------------------------------------------------------------
# 3) Seuranta
# ----------------------------------------------------------------------

def test_tracking_toggle_and_hud_shows_only_tracked():
    from quest_system import quest_manager
    m = _manager()
    quest_manager.accept_quest("hunt_01")
    quest_manager.accept_quest("quest_manure_cleanup")
    assert quest_manager.is_tracked("hunt_01")
    quest_manager.set_tracked("quest_manure_cleanup", False)
    assert not quest_manager.is_tracked("quest_manure_cleanup")
    # HUD-tracker piirtyy näyttäen vain seuratut (ei kaadu)
    surf = pygame.Surface((1920, 1080))
    m.show_quest_journal = True
    m._draw_quest_journal(surf)


def test_journal_track_button_click_toggles():
    from quest_system import quest_manager
    m = _manager()
    quest_manager.accept_quest("hunt_01")
    m.show_full_journal = True
    m._journal_sync_selection()
    surf = pygame.Surface((1920, 1080))
    m._draw_full_journal(surf)   # täyttää _journal_ui
    btn = m._journal_ui["track_btn"]
    was = quest_manager.is_tracked("hunt_01")
    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                               pos=btn.center)
    m._handle_full_journal_event(click)
    assert quest_manager.is_tracked("hunt_01") != was


def test_journal_tab_and_close_keys():
    from quest_system import quest_manager
    m = _manager()
    quest_manager.accept_quest("hunt_01")
    m.show_full_journal = True
    m.journal_tab = "main"
    m._handle_full_journal_event(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB))
    assert m.journal_tab == "side"
    m._handle_full_journal_event(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert m.show_full_journal is False


# ----------------------------------------------------------------------
# 4) Persistenssi
# ----------------------------------------------------------------------

def test_tracking_persists_through_save_load(tmp_path):
    import save_manager
    from quest_system import quest_manager
    m = _manager()
    quest_manager.accept_quest("hunt_01")
    quest_manager.set_tracked("hunt_01", False)
    path = str(tmp_path / "journal_save.json")
    assert save_manager.save_game(m, path)
    quest_manager.untracked = set()
    m2 = _manager()
    assert save_manager.load_game(m2, path)
    assert "hunt_01" in quest_manager.untracked
    assert not quest_manager.is_tracked("hunt_01")
