# tests/test_commander_life_skills.py
"""
Commanderin elämäntaidot: uudet Animal Husbandry- ja Trade-haarat sekä
aiemmin kuolleet puun efektit (harvest_yield, harvest_quality, mining_speed,
chop_speed, wood_yield) todella vaikuttavat peliin.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from skills.commander_skills_data import COMMANDER_SKILL_TREE


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


def test_new_branches_exist_with_requirements():
    for sid in ("husbandry_1", "husbandry_2", "trade_1", "trade_2"):
        assert sid in COMMANDER_SKILL_TREE
    assert COMMANDER_SKILL_TREE["husbandry_2"]["requires"] == ["husbandry_1"]
    assert COMMANDER_SKILL_TREE["trade_2"]["requires"] == ["trade_1"]


def test_life_skill_effects_apply_and_do_not_stack_on_recalc():
    m = _manager()
    hero = m.player_character
    hero.unlocked_skills.update({
        "mining_2", "mining_3", "lumber_2", "lumber_3",
        "harvesting_2", "harvesting_3",
        "husbandry_1", "husbandry_2", "trade_1", "trade_2",
    })
    hero.calculate_final_stats()
    hero.calculate_final_stats()  # toinen kutsu EI saa tuplata
    assert hero.mining_speed == 0.1
    assert hero.mining_yield == 1
    assert hero.chop_speed == 0.1
    assert hero.wood_yield == 1
    assert hero.harvest_yield == 1
    assert hero.harvest_quality == 0.20
    assert hero.husbandry == 2
    assert hero.haggler == 2


def test_harvest_yield_and_quality_consumed():
    import random
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(m)
    city.on_enter()
    hero = m.player_character
    hero.unlocked_skills.update({"harvesting_1", "harvesting_2", "harvesting_3"})
    hero.calculate_final_stats()
    from items.tools.harvest_tools import GuildHarvestScythe
    hero.equipment["main_hand"] = GuildHarvestScythe()

    plot = city.arena.crop_plots[0]  # Carrot: yield 1-2, req level/tier 1
    plot.watered = True
    plot.growth_ticks = plot.data["growth_frames"]
    random.seed(7)
    assert plot.harvest(m, hero) is True
    got = m.inventory.get(plot.crop_name, 0)
    # perussato 1-2 + tool tier ylitys 2 + skill ylitys 2 + harvest_yield 1
    assert got >= 6, f"sadon pitää sisältää harvest_yield-bonus (sain {got})"


def test_haggler_lowers_shop_prices():
    m = _manager()
    hero = m.player_character
    m.pending_shop_id = "scrap_arms"
    from menus.district_shop_menu import DistrictShopMenu
    menu = DistrictShopMenu(m)
    entry = menu.shop["goods"][0]  # Scrap Blade 28
    base_price = menu._final_price(entry)   # rep 0 -> x1.15 -> 32
    hero.unlocked_skills.update({"trade_1", "trade_2"})
    hero.calculate_final_stats()
    discounted = menu._final_price(entry)   # kuin rep 20 -> x1.05 -> 29
    assert discounted < base_price
    assert menu._effective_rep() == 20


def test_husbandry_milking_gives_milk_material():
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from items.tools.bucket import BucketEmpty
    city = MuckfordCityMenu(m)
    city.on_enter()
    hero = m.player_character
    hero.unlocked_skills.update({"husbandry_1", "husbandry_2"})
    hero.calculate_final_stats()
    m.equipment_bag.append(BucketEmpty())

    class _FakeCow:
        milk_ready = True
        rect = pygame.Rect(100, 100, 60, 40)
    city._interact_cow(_FakeCow())
    assert m.inventory.get("Milk", 0) == 2, "husbandry 2 -> +2 Milk lypsystä"


def test_husbandry_speeds_up_egg_laying():
    m = _manager()
    from ai.farm_animal_ai import FarmAnimalAI
    from units.farm_animals import Chicken
    import random
    hen = Chicken(200, 200)
    ai = getattr(hen, "ai_controller", None) or FarmAnimalAI(hen)
    m.current_arena = type("A", (), {"props": []})()

    hero = m.player_character
    hero.husbandry = 0
    random.seed(3)
    ai._lay_egg(m)
    slow = ai.egg_timer

    hero.husbandry = 2
    random.seed(3)
    ai._lay_egg(m)
    fast = ai.egg_timer
    assert fast < slow
    assert fast == int(slow * 0.70)


def test_wood_yield_bonus_on_felling():
    m = _manager()
    from assets.tiles.muckford_objects import MuckfordTree

    class _Axe:
        tool_type = "axe"

    class _Chopper:
        current_weapon = _Axe()
        chop_speed = 0.0
        wood_yield = 2

    tree = MuckfordTree(300, 300)
    tree.current_hits = 1
    before = m.inventory.get(tree.resource_name, 0)
    chopper = _Chopper()
    tree.chop(chopper, chopper.current_weapon, m)
    gained = m.inventory.get(tree.resource_name, 0) - before
    assert gained >= 4, "kaadosta 2 + wood_yield 2 (+ mahdollinen osumadroppi)"
