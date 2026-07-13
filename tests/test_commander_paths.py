# tests/test_commander_paths.py
"""
Commander Paths: jokainen tekeminen on oma kykypuunsa omalla XP:llä.
Combat-XP tapoista/voitoista, arcane-XP loitsuista, fishing-XP saaliista.
Milestone-perkit vaikuttavat sankarin statseihin ja palautuvat latauksessa.
"""
import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from systems import commander_progression as prog
from systems import fishing as fs


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


def test_paths_defined_with_milestones():
    assert set(prog.PATHS) == {"combat", "arcane", "fishing", "building"}
    assert prog.PATHS["building"]["locked"] is True
    for path_id, spec in prog.PATHS.items():
        levels = [m[0] for m in spec["milestones"]]
        assert levels == sorted(levels), f"{path_id}: milestonet nousevassa"
        assert levels[-1] <= prog.MAX_LEVEL


def test_xp_levels_and_milestone_effects_apply_to_hero():
    import json
    m = _manager()
    hero = m.player_character
    hero.calculate_final_stats()
    base_hp = hero.max_hp
    # Nosta combat taso 3:een -> Arena Footing (+10 max HP)
    total = prog.xp_needed("combat", 1) + prog.xp_needed("combat", 2)
    assert prog.grant_xp(m, "combat", total) is True
    assert prog.get_path(m, "combat")["level"] == 3
    assert prog.has_perk(m, "combat", "arena_footing")
    assert hero.max_hp == base_hp + 10, "milestone näkyy statseissa heti"
    json.dumps(m.npc_state)  # tallentuu saveen

    # Efektit eivät tuplaannu uudelleenlaskennassa
    hero.calculate_final_stats()
    assert hero.max_hp == base_hp + 10

    # Lukittu polku ei ota XP:tä
    assert prog.grant_xp(m, "building", 999) is False
    assert prog.get_path(m, "building")["level"] == 1


def test_combat_xp_from_match_end():
    m = _manager()
    hero = m.player_character
    m.last_fighters = [hero]
    hero.stats["kills"] = 3
    before = prog.get_path(m, "combat")["xp"]
    prog.on_match_end(m, win=True)
    assert prog.get_path(m, "combat")["xp"] == before + 3 * 8 + 12

    # Ilman sankaria kentällä ei XP:tä
    m.last_fighters = []
    xp_now = prog.get_path(m, "combat")["xp"]
    prog.on_match_end(m, win=True)
    assert prog.get_path(m, "combat")["xp"] == xp_now


def test_arcane_xp_from_spell_cast():
    m = _manager()

    class _Spell:
        mana_cost = 12
    before = prog.get_path(m, "arcane")["xp"]
    prog.on_player_spell_cast(m, _Spell())
    assert prog.get_path(m, "arcane")["xp"] == before + 6


def test_fishing_path_migration_and_shared_level():
    m = _manager()
    # Vanha tallennusmuoto migratoituu Path of the Lineen
    m.npc_state["fishing"] = {"level": 9, "xp": 5}
    m.npc_state.pop("paths", None)
    st = fs.get_progress(m)
    assert st["level"] == 9 and st["xp"] == 5
    assert "fishing" not in m.npc_state, "vanha avain siivottu"
    assert prog.get_path(m, "fishing") is st


def test_treasures_and_double_catch_perks():
    m = _manager()
    # Perustaso: aarremahdollisuus 8 %, sharp_hook (lvl 10) tuplaa
    assert abs(fs.treasure_chance(m) - fs.TREASURE_CHANCE) < 1e-9
    prog.get_path(m, "fishing")["level"] = 10
    assert abs(fs.treasure_chance(m) - fs.TREASURE_CHANCE * 2) < 1e-9
    assert fs.double_catch(m) is False
    prog.get_path(m, "fishing")["level"] = 18
    assert fs.double_catch(m) is True
    # Aarrepooli arpoutuu ja kaikilla on myyntihinta
    from lore.world_data import MARKET_PRICES
    rng = random.Random(2)
    names = {fs.roll_treasure(rng)["name"] for _ in range(500)}
    assert "Waterlogged Boot" in names
    for t in fs.TREASURES:
        assert MARKET_PRICES["sell"].get(t["name"]) == t["price"], t["name"]


def test_fish_recipes_in_kitchen():
    from citys.mucford.farming_expansion import MEAL_RECIPES
    for recipe in ("Mudwater Fish Stew", "Smoked Bog Perch", "Pike Roast"):
        assert recipe in MEAL_RECIPES
    assert "Marsh Pike" in MEAL_RECIPES["Pike Roast"]["ingredients"]


def test_paths_menu_draws_and_registered():
    import inspect
    import main
    m = _manager()
    prog.grant_xp(m, "combat", 200)
    from menus.paths_menu import PathsMenu
    menu = PathsMenu(m)
    surf = pygame.Surface((1920, 1080))
    menu.update()
    menu.draw(surf)
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert menu.next_state == "manager_menu"
    src = inspect.getsource(main.main)
    assert '"paths": PathsMenu' in src


def test_progression_reapplied_on_save_load():
    import save_manager
    m = _manager()
    prog.grant_xp(m, "combat",
                  prog.xp_needed("combat", 1) + prog.xp_needed("combat", 2))
    hero = m.player_character
    boosted = hero.max_hp
    save_manager.save_game(m)

    m2 = _manager()
    assert save_manager.load_game(m2) is True
    assert prog.get_path(m2, "combat")["level"] == 3
    m2.player_character.calculate_final_stats()
    assert m2.player_character.max_hp == boosted, \
        "milestone-statsit palautuvat latauksessa"
