import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from menus.barracks_menu import BarracksMenu
from lore.materials import MATERIALS
from quests.village_tasks import VILLAGE_TASKS


def _task(task_id):
    return next(task for task in VILLAGE_TASKS if task["id"] == task_id)


def test_marsh_smith_uses_iron_tier_material_not_endgame_void_iron():
    task = _task("marsh_smith")
    collect = [stage for stage in task["stages"]
               if stage.get("kind") == "collect"]
    assert collect == [{
        "kind": "collect",
        "item": "Iron Ingot",
        "count": 2,
        "hint": "Smelt Iron Ore with Coal at Muckford's Smeltery.",
    }]
    assert task["recommended_level"] == (6, 10)
    assert "Void-Iron" not in task["summary"]


def test_starter_material_tasks_do_not_require_materials_above_their_range():
    for task in VILLAGE_TASKS:
        level_range = task.get("recommended_level")
        if not level_range:
            continue
        maximum = level_range[1]
        if maximum is None:
            continue
        for stage in task.get("stages", []):
            material = MATERIALS.get(stage.get("item"))
            if material is not None:
                assert material["level_min"] <= maximum, (
                    task["id"],
                    stage["item"],
                    material["level_min"],
                    maximum,
                )


def test_hospice_quest_uses_bitterleaf_name_and_lore_family():
    task = _task("forest_herbs")
    assert task["title"] == "Hospice Bitterleaf"
    assert task["material_family"] == "Herbs, Alchemy & Potions"
    collect = next(stage for stage in task["stages"]
                   if stage.get("kind") == "collect")
    assert collect["item"] == "Bitterleaf"
    assert "Bogwort" not in task["summary"]
