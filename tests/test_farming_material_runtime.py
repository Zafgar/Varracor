import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from menus.barracks_menu import BarracksMenu
from assets.tiles.muckford_objects import MuckfordTree, Smeltery
from systems.material_integration_hardening import sync_material_discovery


class DummyVFX:
    def show_damage(self, *args, **kwargs):
        pass


class DummyManager:
    def __init__(self):
        self.inventory = {}
        self.city_storage = {}
        self.loot_gained = {}
        self.npc_state = {"global": {"reputation": 0, "flags": {}}}
        self.vfx = DummyVFX()
        self.dialogue = None

    def start_dialogue(self, speaker, text, options):
        self.dialogue = (speaker, text, options)


def test_muckford_tree_uses_canonical_name_in_harvest_text():
    assert getattr(BarracksMenu, "_tiered_stations_installed", False)
    tree = MuckfordTree(0, 0)
    assert tree.resource_name == "Rough Timber"


def test_smeltery_dialogue_uses_canonical_recipe_names():
    manager = DummyManager()
    smeltery = Smeltery(0, 0)
    smeltery.interact_cooldown = 0

    smeltery.interact(manager)

    assert manager.dialogue is not None
    _speaker, status, options = manager.dialogue
    option_text = [option["text"] for option in options]
    assert "Rough Timber" in status
    assert any("Iron Ingot" in text for text in option_text)
    assert not any("Iron Bar" in text for text in option_text)
    assert not any("Swamp Wood" in text for text in option_text)


def test_smeltery_creates_canonical_iron_ingot(monkeypatch):
    manager = DummyManager()
    manager.inventory = {"Iron Ore": 2, "Coal": 1}
    smeltery = Smeltery(0, 0)
    monkeypatch.setattr("systems.material_integration_hardening.sound_system.play_sound",
                        lambda *_args, **_kwargs: None)

    smeltery.handle_menu_action("smelter_iron", manager)

    assert smeltery.current_job["output"] == "Iron Ingot"
    assert manager.inventory["Iron Ore"] == 0
    assert manager.inventory["Coal"] == 0


def test_existing_materials_are_registered_in_discovery_codex():
    manager = DummyManager()
    manager.inventory = {"Iron Ingot": 2, "Carrot": 3}
    manager.city_storage = {"Moondew Petals": 1, "Bandage Roll": 2}
    manager.loot_gained = {"Void-Iron": 1}

    sync_material_discovery(manager)

    discovered = manager.npc_state["material_codex"]["discovered"]
    assert discovered == sorted([
        "Bandage Roll",
        "Iron Ingot",
        "Moondew Petals",
        "Void-Iron",
    ])
    assert "Carrot" not in discovered
