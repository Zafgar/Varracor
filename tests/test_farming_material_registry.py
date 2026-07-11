import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

# Installs farming, stations and material integration like the real game.
from menus.barracks_menu import BarracksMenu
import citys.mucford.farming_expansion as farming
import citys.mucford.farming_content as farming_content
import citys.mucford.farming_stations as stations
from lore.materials import (
    CRAFTED_COMPONENTS,
    MATERIALS,
    RARITY_ORDER,
    canonical_material_name,
    get_material_or_component,
)
from lore.world_data import MARKET_PRICES, RESOURCE_TIERS
from loot_data import BLUEPRINTS, LOOT_DROPS
from quests.material_contracts import (
    ACTIVE_MATERIAL_TASKS,
    FUTURE_MATERIAL_CONTRACTS,
)
from quests.village_tasks import VILLAGE_TASKS
from systems.material_integration import migrate_manager_materials


class DummyManager:
    def __init__(self):
        self.inventory = {
            "Iron Bar": 2,
            "Iron Ingot": 1,
            "Swamp Wood": 4,
            "Sunleaf": 3,
            "Moonpetal": 2,
        }
        self.city_storage = {"Void Iron": 1, "Dragon Scale": 2}
        self.loot_gained = {"Bogwort": 2}
        self.round_rewards = {"loot": {"Stormsilver": 1}}
        self.npc_state = {
            "global": {"reputation": 0, "flags": {}},
            "farming": {
                "plots": {
                    "plot_1_sunleaf": {"crop": "Sunleaf"},
                    "plot_2_moonpetal": {"crop": "Moonpetal"},
                },
                "npc_harvest_totals": {"Medicinal Herb": 3},
            },
        }


def test_registry_contains_complete_canonical_material_set():
    assert len(MATERIALS) == 49
    for name, data in MATERIALS.items():
        assert name
        assert data["rarity"] in RARITY_ORDER
        assert data["category"]
        assert data["level_min"] >= 1
        assert data["level_max"] is None or data["level_max"] >= data["level_min"]
        assert data["source"]
        assert data["station"]
        assert data["uses"]
        assert data["lore"]
        assert data["sell_price"] > 0


def test_known_ambiguities_are_explicitly_resolved():
    echo = MATERIALS["Echo Shard"]
    assert echo["rarity"] == "Rare"
    assert echo["special_grade"] == "Epic"
    focus = MATERIALS["Focus Powder"]
    assert focus["rarity"] == "Uncommon"
    assert focus["special_grade"] == "Uncommon/Rare"


def test_legacy_aliases_resolve_to_canonical_names():
    expected = {
        "Iron Bar": "Iron Ingot",
        "Swamp Wood": "Rough Timber",
        "Void Iron": "Void-Iron",
        "Dragon Scale": "Drake Scale",
        "Sunleaf": "Sunblossom",
        "Moonpetal": "Moondew Petals",
        "Bogwort": "Bitterleaf",
    }
    for old, new in expected.items():
        assert canonical_material_name(old) == new
        assert get_material_or_component(old)["name"] == new


def test_old_save_materials_merge_without_losing_counts():
    manager = DummyManager()
    migrate_manager_materials(manager)

    assert manager.inventory["Iron Ingot"] == 3
    assert manager.inventory["Rough Timber"] == 4
    assert manager.inventory["Sunblossom"] == 3
    assert manager.inventory["Moondew Petals"] == 2
    assert "Iron Bar" not in manager.inventory
    assert "Swamp Wood" not in manager.inventory
    assert manager.city_storage == {"Void-Iron": 1, "Drake Scale": 2}
    assert manager.loot_gained == {"Bitterleaf": 2}
    assert manager.round_rewards["loot"] == {"Stormsilver Ore": 1}
    assert "plot_1_sunblossom" in manager.npc_state["farming"]["plots"]
    assert "plot_2_moondew_petals" in manager.npc_state["farming"]["plots"]
    assert manager.npc_state["farming"]["npc_harvest_totals"]["Bitterleaf"] == 3


def test_world_data_and_market_are_generated_from_registry():
    assert set(RESOURCE_TIERS) == set(RARITY_ORDER)
    for name, data in MATERIALS.items():
        assert name in RESOURCE_TIERS[data["rarity"]]["resources"]
        assert MARKET_PRICES["sell"][name] == data["sell_price"]
    for component in CRAFTED_COMPONENTS:
        assert component in MARKET_PRICES["sell"]
    for starter in ("Coal", "Plant Fiber", "Rough Timber", "Resin",
                    "Parchment Sheet", "Wax Seal"):
        assert MARKET_PRICES["buy"][starter]["kind"] == "material"


def test_blueprints_use_canonical_inputs_and_station_metadata():
    forbidden = {"Iron Bar", "Swamp Wood", "Sunleaf", "Moonpetal", "Void Iron"}
    for recipe in BLUEPRINTS.values():
        assert not forbidden.intersection(recipe.get("mats", {}))
        assert recipe["station"]
        assert recipe["station_tier"] >= 1
        assert recipe["craft_minutes"] > 0
        assert recipe["output_amount"] >= 1
    assert BLUEPRINTS["Iron Sword"]["mats"] == {
        "Iron Ingot": 2,
        "Rough Timber": 1,
    }
    dragon_drops = LOOT_DROPS["Dragon"]
    assert dragon_drops[0]["item"] == "Drake Scale"


def test_farming_and_station_recipes_use_canonical_world_materials():
    assert "Sunblossom" in farming.CROP_DATA
    assert "Moondew Petals" in farming.CROP_DATA
    assert "Sunleaf" not in farming.CROP_DATA
    assert "Moonpetal" not in farming.CROP_DATA

    moondew_recipe = farming_content.POTION_RECIPES["Moonpetal Elixir"]
    assert moondew_recipe["ingredients"] == {
        "Moondew Petals": 2,
        "Focus Powder": 1,
    }
    assert stations.WORKBENCH_RECIPES["Treated Timber"]["ingredients"] == {
        "Rough Timber": 3,
        "Resin": 1,
    }
    assert stations.WORKBENCH_RECIPES["Precision Components"]["ingredients"] == {
        "Iron Ingot": 2,
        "Silver Filigree Wire": 1,
        "Focus Powder": 1,
    }


def test_material_contracts_are_connected_and_future_hooks_exist():
    active_ids = {task["id"] for task in ACTIVE_MATERIAL_TASKS}
    installed_ids = {task["id"] for task in VILLAGE_TASKS}
    assert active_ids.issubset(installed_ids)
    assert len(ACTIVE_MATERIAL_TASKS) >= 6
    assert len(FUTURE_MATERIAL_CONTRACTS) >= 10

    active_items = {
        stage["item"]
        for task in ACTIVE_MATERIAL_TASKS
        for stage in task["stages"]
        if stage.get("item")
    }
    assert {"Coal", "Plant Fiber", "Iron Ore", "Bitterleaf",
            "Nightcap Fungus", "Parchment Sheet", "Wax Seal"}.issubset(active_items)

    future_items = {
        material
        for contract in FUTURE_MATERIAL_CONTRACTS
        for material in contract["materials"]
    }
    assert {"Blacksteel Ore", "Stormsilver Ore", "Sun-Gold Ore",
            "Void-Iron", "Heartcore Adamant", "Echo Heart",
            "Charter Seal Token"}.issubset(
                future_items | {
                    reward
                    for contract in FUTURE_MATERIAL_CONTRACTS
                    for reward in contract.get("reward_materials", {})
                }
            )
