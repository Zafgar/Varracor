import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

# Importing BarracksMenu installs all farming/material layers like main.py.
from menus.barracks_menu import BarracksMenu
import citys.mucford.farming_expansion as farming
from citys.mucford.farming_content import HERB_DATA, POTION_RECIPES
from items.farm_potions import (
    BitterleafTonic,
    IronstemFortifier,
    MoonpetalElixir,
)
from items.item_registry import create_item
from items.tools.harvest_tools import GuildHarvestScythe
from lore.world_data import MARKET_PRICES
from settings import SCREEN_HEIGHT, SCREEN_WIDTH


class DummyVFX:
    def show_damage(self, *args, **kwargs):
        pass

    def create_falling_leaves(self, *args, **kwargs):
        pass


class DummyClock:
    weather = "clear"


class DummyManager:
    def __init__(self):
        self.inventory = {}
        self.city_storage = {}
        self.equipment_bag = []
        self.npc_state = {"global": {"reputation": 0, "flags": {}}}
        self.vfx = DummyVFX()
        self.world_clock = DummyClock()


class DummyHarvester:
    def __init__(self, tool):
        self.unlocked_skills = {"harvesting_1", "harvesting_2", "harvesting_3"}
        self.equipment = {"main_hand": tool}
        self.primary_weapon = tool
        self.current_weapon = tool


class DummyAI:
    job = "Farmer"


class DummyFarmer:
    def __init__(self, name):
        self.name = name
        self.ai_controller = DummyAI()
        self.inventory = []
        self.weapon_masteries = set()


class DummyFighter:
    def __init__(self):
        self.max_hp = 100
        self.current_hp = 20
        self.max_mana = 80
        self.current_mana = 10
        self.max_stamina = 100
        self.current_stamina = 15
        self.injured = True
        self.injury_severity = "Minor"
        self.equipment = {"usable": None, "usable2": None}


def test_expanded_layout_has_twenty_valid_plots_and_named_herbs():
    assert getattr(BarracksMenu, "_farm_alchemy_installed", False)
    assert len(farming.PLOT_LAYOUT) == 20
    assert len(HERB_DATA) == 7
    assert len({(col, row) for _crop, col, row in farming.PLOT_LAYOUT}) == 20
    assert max(col for _crop, col, _row in farming.PLOT_LAYOUT) == 3
    assert max(row for _crop, _col, row in farming.PLOT_LAYOUT) == 4
    assert "Sunblossom" in HERB_DATA
    assert "Moondew Petals" in HERB_DATA
    assert "Sunleaf" not in HERB_DATA
    assert "Moonpetal" not in HERB_DATA
    for crop_name, _col, _row in farming.PLOT_LAYOUT:
        assert crop_name in farming.CROP_DATA
    for herb_name, herb in HERB_DATA.items():
        assert herb_name in farming.CROP_DATA
        assert herb["kind"] == "herb"
        assert herb["potion_use"]


def test_plot_grid_fits_farm_and_leaves_eastern_apple_corridor():
    world_w = int(SCREEN_WIDTH * 3.0)
    world_h = int(SCREEN_HEIGHT * 3.0)
    street_bottom = world_h // 2 + 200
    farm = pygame.Rect(
        100,
        street_bottom + 50,
        world_w // 2 - 200,
        world_h - street_bottom - 150,
    )
    max_col = max(col for _crop, col, _row in farming.PLOT_LAYOUT)
    max_row = max(row for _crop, _col, row in farming.PLOT_LAYOUT)
    grid_right = farm.x + 1240 + max_col * (farming.CropPlot.WIDTH + 28) + farming.CropPlot.WIDTH
    grid_bottom = farm.y + 130 + max_row * (farming.CropPlot.HEIGHT + 32) + farming.CropPlot.HEIGHT

    assert grid_right <= farm.right - 300
    assert grid_bottom <= farm.bottom


def test_market_contains_all_harvest_tools_and_water():
    expected = {
        "Bucket of Water": "BucketWater",
        "Crude Harvest Sickle": "CrudeHarvestSickle",
        "Iron Harvest Sickle": "IronHarvestSickle",
        "Guild Harvest Scythe": "GuildHarvestScythe",
    }
    for shop_name, class_name in expected.items():
        assert MARKET_PRICES["buy"][shop_name]["class"] == class_name
    for herb_name in HERB_DATA:
        assert herb_name in MARKET_PRICES["sell"]


def test_item_registry_creates_shop_tools_and_brewed_potions():
    for name in (
        "BucketWater",
        "CrudeHarvestSickle",
        "IronHarvestSickle",
        "GuildHarvestScythe",
        "Bitterleaf Tonic",
        "Ironstem Fortifier",
    ):
        assert create_item(name) is not None, name


def test_npc_harvest_places_canonical_product_in_city_storage_and_ledger():
    manager = DummyManager()
    state = {"growth_ticks": 0, "watered": True, "harvest_count": 0}
    plot = farming.CropPlot(
        0, 0, "Moondew Petals", state, "moondew_petals_test")
    plot.growth_ticks = plot.data["growth_frames"]
    worker = DummyHarvester(GuildHarvestScythe())

    assert plot.harvest(manager, worker, to_storage=True, npc=True)
    assert manager.city_storage["Moondew Petals"] >= 1
    assert manager.npc_state["farming"]["npc_harvest_totals"]["Moondew Petals"] >= 1
    assert plot.growth_ticks == 0
    assert plot.watered is False


def test_farmer_roster_gets_all_required_tool_tiers():
    manager = DummyManager()
    farmers = [DummyFarmer(f"Farmer {index}") for index in range(5)]
    system = object.__new__(farming.FarmingSystem)
    system.manager = manager
    system.city = type("City", (), {"npcs": farmers})()

    system._equip_farmer_npcs()

    tiers = []
    for farmer in farmers:
        tools = [item for item in farmer.inventory
                 if getattr(item, "tool_type", "") == "harvest"]
        assert len(tools) == 1
        tiers.append(tools[0].tool_tier)
        assert "harvest_tool" in farmer.weapon_masteries
    assert sorted(tiers, reverse=True) == [3, 2, 2, 1, 1]


def test_farm_potions_apply_effects_and_are_consumed_from_slot():
    fighter = DummyFighter()
    tonic = BitterleafTonic()
    fighter.equipment["usable"] = tonic
    assert tonic.cast(fighter)
    assert fighter.current_hp == 45
    assert fighter.equipment["usable"] is None

    elixir = MoonpetalElixir()
    fighter.equipment["usable2"] = elixir
    assert elixir.cast(fighter)
    assert fighter.current_mana == 46
    assert fighter.equipment["usable2"] is None

    fortifier = IronstemFortifier()
    fighter.equipment["usable"] = fortifier
    hp_before = fighter.current_hp
    stamina_before = fighter.current_stamina
    assert fortifier.cast(fighter)
    assert fighter.current_hp > hp_before
    assert fighter.current_stamina > stamina_before
    assert fighter.equipment["usable"] is None


def test_alchemy_uses_canonical_world_reagents():
    used_ingredients = {
        ingredient
        for recipe in POTION_RECIPES.values()
        for ingredient in recipe["ingredients"]
    }
    assert "Bitterleaf" in used_ingredients
    assert "Sunblossom" in used_ingredients
    assert "Nightcap Fungus" in used_ingredients
    assert "Moondew Petals" in used_ingredients
    assert "Resin" in used_ingredients
    assert "Focus Powder" in used_ingredients
    assert "Sunleaf" not in used_ingredients
    assert "Moonpetal" not in used_ingredients


def test_every_alchemy_recipe_builds_a_concrete_potion():
    assert len(POTION_RECIPES) >= 6
    for recipe in POTION_RECIPES.values():
        potion = recipe["factory"]()
        assert potion.type == "potion"
        assert potion.slot_type == "usable"
        assert recipe["ingredients"]
