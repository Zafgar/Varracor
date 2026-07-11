import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

# Barracks import installs the station hardening layer and finalized costs.
from menus.barracks_menu import BarracksMenu
import citys.mucford.farming_stations as stations


def test_master_workbench_has_no_precision_component_cycle():
    assert getattr(BarracksMenu, "_tiered_stations_installed", False)
    materials = stations.STATION_DEFINITIONS["workbench"]["tiers"][3]["materials"]
    assert "Precision Components" not in materials
    assert materials["Leather Straps"] >= 1
    assert materials["Reinforced Cloth"] >= 1


def test_workbench_upgrade_chain_only_uses_outputs_from_lower_tiers():
    output_tiers = {
        recipe["output"]["name"]: int(recipe["tier"])
        for recipe in stations.WORKBENCH_RECIPES.values()
    }
    for target_tier in (1, 2, 3):
        materials = stations.STATION_DEFINITIONS["workbench"]["tiers"][target_tier]["materials"]
        for material in materials:
            producer_tier = output_tiers.get(material)
            if producer_tier is not None:
                assert producer_tier < target_tier, (
                    material,
                    producer_tier,
                    target_tier,
                )


def test_master_workbench_unlocks_components_for_other_master_stations():
    precision = stations.WORKBENCH_RECIPES["Precision Components"]
    assert precision["tier"] == 3
    for station_id in ("herbalist", "infirmary"):
        master_cost = stations.STATION_DEFINITIONS[station_id]["tiers"][3]["materials"]
        assert master_cost.get("Precision Components", 0) >= 1
