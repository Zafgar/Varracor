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
    assert set(prog.PATHS) == {"combat", "arcane", "fishing", "building",
                               "mining", "smithing", "forestry"}
    assert prog.PATHS["building"]["locked"] is True
    for path_id, spec in prog.PATHS.items():
        levels = [m[0] for m in spec["milestones"]]
        assert levels == sorted(levels), f"{path_id}: milestonet nousevassa"
        assert levels[-1] <= prog.MAX_LEVEL


def test_vortex_path_unlocks_spell_slots_behind_levels():
    """Spell slotit ja tierit ovat Vortex-polun tasovaatimusten takana:
    L1 = slot 1 + tier I, L8 = slot 2, L16 = slot 3, L30 = tier IV."""
    m = _manager()
    hero = m.player_character
    prog.apply_to_hero(m)

    class _Spell:
        slot_type = "spell"
        type = "spell"
        tier = 1
    assert 1 in hero.spell_slots_unlocked and hero.max_spell_tier >= 1
    ok, _ = hero.can_equip_item_to_slot("spell1", _Spell())
    assert ok, "First Sigil avaa slotin 1 heti"
    ok2, why = hero.can_equip_item_to_slot("spell2", _Spell())
    assert not ok2 and "locked" in why.lower()

    prog.get_path(m, "arcane")["level"] = 16
    prog.apply_to_hero(m)
    assert {1, 2, 3} <= hero.spell_slots_unlocked
    prog.get_path(m, "arcane")["level"] = 30
    prog.apply_to_hero(m)
    assert hero.max_spell_tier >= 4, "Abyssal Gate avaa tier IV:n"


def test_weapon_level_requirements_gate_commander():
    """Aseiden level_required koskee Commanderia kuten muitakin
    gladiaattoreita (ei-cheat)."""
    m = _manager()
    hero = m.player_character
    from items.swords.vortex_blade import VortexBlade
    ok, why = hero.can_equip_item_to_slot("main_hand", VortexBlade())
    assert not ok and "Level 30" in why
    hero.level = 30
    ok2, _ = hero.can_equip_item_to_slot("main_hand", VortexBlade())
    assert ok2


def test_craft_paths_gain_xp_from_doing():
    m = _manager()
    hero = m.player_character

    prog.on_ore_mined(m, hero, dropped=1)
    assert prog.get_path(m, "mining")["xp"] == 8
    prog.on_ore_mined(m, object(), dropped=1)  # muu kuin sankari
    assert prog.get_path(m, "mining")["xp"] == 8

    prog.on_tree_chopped(m, hero, felled=False)
    prog.on_tree_chopped(m, hero, felled=True)
    assert prog.get_path(m, "forestry")["xp"] == 8

    from loot_data import BLUEPRINTS
    name = next(iter(BLUEPRINTS))
    recipe = BLUEPRINTS[name]
    m.gold = 5000
    for mat, count in recipe["mats"].items():
        m.add_material(mat, count)
    assert m.craft_item(name, None) is True
    assert prog.get_path(m, "smithing")["xp"] > 0

    # Milestone-efektit valuvat elämäntaitoattribuutteihin
    prog.get_path(m, "mining")["level"] = 8
    prog.get_path(m, "forestry")["level"] = 9
    prog.apply_to_hero(m)
    assert hero.mining_yield >= 1
    assert hero.wood_yield >= 1


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


def test_tool_ladders_defined_and_resolvable():
    """Työkalutikkaat: uusi väline ~4 tason välein (1/5/9/14/19),
    kaikki työkalut löytyvät rekisteristä ja Paths-UI tietää seuraavan."""
    from items.item_registry import create_item
    m = _manager()
    for path_id in ("mining", "forestry", "fishing"):
        tools = prog.PATHS[path_id]["tools"]
        levels = [lvl for lvl, _ in tools]
        assert levels == [1, 5, 9, 14, 19], f"{path_id}: väärä tahti"
        gaps = [b - a for a, b in zip(levels, levels[1:])]
        assert all(3 <= g <= 5 for g in gaps), f"{path_id}: 3-5 tason välit"
        for _lvl, name in tools:
            assert create_item(name) is not None, f"{name} puuttuu rekisteristä"
    # next_tool kertoo seuraavan avauksen
    assert prog.next_tool(m, "mining") == (5, "Bogiron Pickaxe")
    prog.get_path(m, "mining")["level"] = 9
    assert prog.next_tool(m, "mining") == (14, "Duskforged Pickaxe")
    prog.get_path(m, "mining")["level"] = 30
    assert prog.next_tool(m, "mining") is None


def test_tool_level_gates_mining_and_forestry():
    """Liian vaativa hakku/kirves ei toimi sankarilla ennen tasoa -
    NPC:t saavat käyttää mitä vain."""
    from items.item_registry import create_item
    m = _manager()
    hero = m.player_character
    pick = create_item("SteelheadPickaxe")   # vaatii Vein 9
    ok, req = prog.tool_allowed(m, hero, pick, "mining",
                                "mining_level_required")
    assert not ok and req == 9
    prog.get_path(m, "mining")["level"] = 9
    ok2, _ = prog.tool_allowed(m, hero, pick, "mining",
                               "mining_level_required")
    assert ok2
    # NPC ohittaa
    ok3, _ = prog.tool_allowed(m, object(), pick, "mining",
                               "mining_level_required")
    assert ok3

    axe = create_item("VortexfellLumberAxe")  # vaatii Timber 19
    ok4, req4 = prog.tool_allowed(m, hero, axe, "forestry",
                                  "forestry_level_required")
    assert not ok4 and req4 == 19


def test_ore_and_tree_reject_too_advanced_tool_in_world():
    """Kenttätesti: malmi ja puu näyttävät vaatimuksen eivätkä anna
    resursseja liian vaativalla työkalulla."""
    import main  # noqa: F401
    from game_manager import GameManager
    from items.item_registry import create_item
    from crafting.ores.iron_ore import IronOre
    from assets.tiles.muckford_objects import MuckfordTree
    m = GameManager()
    hero = m.player_character

    ore = IronOre(0, 0)
    hits0 = ore.current_hits
    ore.take_hit(hero, create_item("VortexbitePickaxe"), m)
    assert ore.current_hits == hits0, "isku estyi tasovaatimukseen"
    ore.take_hit(hero, create_item("WeakPickaxe"), m)
    assert ore.current_hits == hits0 - 1, "perushakku toimii tasolla 1"

    tree = MuckfordTree(0, 0)
    th0 = tree.current_hits
    tree.chop(hero, create_item("DuskforgedLumberAxe"), m)
    assert tree.current_hits == th0, "hakkuu estyi tasovaatimukseen"


def test_chicken_petting_gives_feathers():
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from units.farm_animals import Chicken
    city = MuckfordCityMenu(m)
    city.on_enter()
    hen = Chicken(500, 500)
    hen._feather_cd = 0
    import random as _r
    _r.seed(1)
    got = 0
    for _ in range(20):
        hen._feather_cd = 0
        before = m.inventory.get("Feather", 0)
        city._pet_chicken(hen)
        got += m.inventory.get("Feather", 0) - before
    assert got >= 5, "silittäminen tuottaa höyheniä"
    from lore.world_data import MARKET_PRICES
    assert MARKET_PRICES["sell"]["Feather"] == 1


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
