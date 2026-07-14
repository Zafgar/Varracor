# tests/test_playtest8_fixes.py
"""Pelitestikierros 8: liigan tila tallentuu, sim-matsien tapot Hall of
Fameen, Farmer Gus portilla ja quest tarjolla, questien karttamerkit sekä
uudet maine-questit (First Swing + Krad's Missing Crate)."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))


@pytest.fixture
def tmp_saves(tmp_path, monkeypatch):
    import save_manager
    monkeypatch.setattr(save_manager, "SAVE_DIR", str(tmp_path))
    monkeypatch.setattr(save_manager, "SAVE_FILE",
                        str(tmp_path / "savegame.json"))
    return save_manager


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


def _reset_quests():
    from quest_system import quest_manager
    for qid in ("quest_manure_cleanup", "quest_first_swing",
                "quest_krads_crate"):
        q = quest_manager.get_quest(qid)
        if q:
            q.status = "available"
            q.is_finished = False
            q.progress = 0


# ----------------------------------------------------------------------
# Liigan persistenssi + sim-tapot
# ----------------------------------------------------------------------

def test_league_state_survives_save_load(tmp_saves):
    m = _manager()
    eng = m.league_engine
    eng._ensure_initialized()
    season = eng.seasons["1v1"]
    # Simuloi kierroksia: taulukkoon syntyy tuloksia
    for _ in range(3):
        season._pending_matches = list(season._current_pairings)
        season._pending_advance = True
        season.resolve_pending()
    wins_before = {tid: r.wins for tid, r in season.records.items()}
    round_before = season.current_round
    assert sum(wins_before.values()) > 0, "simulaatio tuotti tuloksia"

    assert tmp_saves.save_game(m)
    m2 = _manager()
    assert tmp_saves.load_game(m2)
    season2 = m2.league_engine.seasons["1v1"]
    assert season2.current_round == round_before, "kierros säilyy"
    for tid, wins in wins_before.items():
        assert season2.records[tid].wins == wins, f"{tid} voitot säilyvät"
    assert season2.hof_kills, "HoF-tapot säilyvät savessa"


def test_simulated_matches_feed_hall_of_fame():
    m = _manager()
    eng = m.league_engine
    eng._ensure_initialized()
    season = eng.seasons["3v3"]
    season._pending_matches = list(season._current_pairings)
    season.resolve_pending()
    assert season.hof_kills, ("simuloitujen matsien taistelijat saavat "
                              "tappoja Hall of Fameen")
    assert all(isinstance(v, int) and v > 0
               for v in season.hof_kills.values())


# ----------------------------------------------------------------------
# Farmer Gus + questinantajat
# ----------------------------------------------------------------------

def test_gus_at_gate_with_clean_name_and_quest():
    m = _manager()
    _reset_quests()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(m)
    city.on_enter()
    gus = city.farmer_gus
    assert gus.name == "Farmer Gus", "job-liite rikkoi questihaun"
    gate = city.arena.farm_gate_pos
    assert abs(gus.rect.centerx - gate[0]) < 220
    assert gus.rect.centery < city.arena.farm_area.y, \
        "Gus on portin luona kaupungin puolella, ei farmin alla"
    # Quest-dialogi löytyy nyt nimellä
    from quest_system import quest_manager
    assert quest_manager.get_npc_dialogue_override("Farmer Gus"), \
        "lantaquest tarjolla Gusilta"


def test_new_quests_registered_and_dialogues():
    import main  # noqa: F401
    _reset_quests()
    from quest_system import quest_manager
    assert quest_manager.get_quest_status("quest_first_swing") == "available"
    assert quest_manager.get_quest_status("quest_krads_crate") == "available"
    from quest_registry import get_quest_def
    timber = get_quest_def("quest_first_swing")
    nodes = timber.get_dialogue_for_npc("Woodsman Alder", "available")
    assert nodes and "start" in nodes
    effects = []
    for choice in nodes["start"].choices:
        effects.extend(choice.effects or [])
    assert "give_item:WeakLumberAxe" in effects, "eka kirves annetaan"
    crate = get_quest_def("quest_krads_crate")
    assert crate.get_dialogue_for_npc("Krad", "available")
    assert crate.get_dialogue_for_npc("Farmer Gus", "available") is None


def test_timber_quest_progress_on_felled_trees():
    m = _manager()
    _reset_quests()
    from quest_system import quest_manager
    from systems import commander_progression as prog
    quest_manager.accept_quest("quest_first_swing")
    hero = m.player_character
    q = quest_manager.get_quest("quest_first_swing")
    for _ in range(q.definition.required_amount):
        prog.on_tree_chopped(m, hero, felled=True)
    assert q.status == "completed", "kaadot etenevät questia"


def test_crate_quest_lifecycle():
    m = _manager()
    _reset_quests()
    from quest_system import quest_manager
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from assets.tiles.muckford_objects import QuestCrate
    city = MuckfordCityMenu(m)
    city.on_enter()
    assert city._quest_crate is None
    quest_manager.accept_quest("quest_krads_crate")
    city._update_quest_crate()
    crate = city._quest_crate
    assert isinstance(crate, QuestCrate), "laatikko ilmestyy hökkelille"
    assert crate in city.arena.props
    # Poiminta E:llä -> completed ja laatikko pois
    city.player.rect.center = crate.rect.center
    assert city._try_interact_prop(crate, check_collision=True) is True
    assert quest_manager.get_quest_status("quest_krads_crate") == "completed"
    assert city._quest_crate is None


def test_map_shows_quest_markers():
    m = _manager()
    _reset_quests()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(m)
    city.on_enter()
    city.show_map = True
    surf = pygame.Surface((1920, 1080))
    city.draw(surf)  # quest-glyyfit piirtyvät kaatumatta
    city.show_map = False
    assert getattr(city, "woodsman_alder", None) is not None
    assert city.woodsman_alder.name == "Woodsman Alder"


def test_give_item_effect_creates_axe():
    import main  # noqa: F401
    from items.item_registry import create_item
    axe = create_item("WeakLumberAxe")
    assert axe is not None, "registry löytää ekan kirveen luokkanimellä"
    assert getattr(axe, "weapon_group", "") == "lumber_axe" or \
        getattr(axe, "tool_type", "") == "lumber_axe"
