"""Final safety and presentation layer for canonical Varrakor materials."""

from __future__ import annotations

from lore.materials import canonical_material_name, get_material_or_component
from sound_manager import sound_system


_INSTALLED = False


def _mark_discovered(manager, name):
    canonical = canonical_material_name(name)
    if get_material_or_component(canonical) is None:
        return
    npc_state = getattr(manager, "npc_state", None)
    if not isinstance(npc_state, dict):
        manager.npc_state = {"global": {"reputation": 0, "flags": {}}}
        npc_state = manager.npc_state
    codex = npc_state.setdefault("material_codex", {})
    discovered = codex.setdefault("discovered", [])
    if canonical not in discovered:
        discovered.append(canonical)
        discovered.sort()


def sync_material_discovery(manager):
    """Mark existing inventory/storage materials as discovered after loading."""
    for attr in ("inventory", "city_storage", "loot_gained"):
        container = getattr(manager, attr, None)
        if not isinstance(container, dict):
            continue
        for name, amount in container.items():
            if int(amount) > 0:
                _mark_discovered(manager, name)


def _patch_game_manager_discovery():
    from game_manager import GameManager

    if getattr(GameManager, "_material_discovery_installed", False):
        return

    previous_init = GameManager.__init__
    previous_add_material = GameManager.add_material

    def __init__(self, *args, **kwargs):
        previous_init(self, *args, **kwargs)
        sync_material_discovery(self)

    def add_material(self, name, count=1):
        canonical = canonical_material_name(name)
        result = previous_add_material(self, canonical, count)
        if int(count) > 0:
            _mark_discovered(self, canonical)
        return result

    def get_discovered_materials(self):
        npc_state = getattr(self, "npc_state", {})
        names = npc_state.get("material_codex", {}).get("discovered", [])
        result = []
        for name in names:
            info = get_material_or_component(name)
            if info:
                result.append(info)
        return result

    GameManager.__init__ = __init__
    GameManager.add_material = add_material
    GameManager.get_discovered_materials = get_discovered_materials
    GameManager._material_discovery_installed = True


def _patch_save_discovery():
    try:
        import save_manager
    except Exception:
        return
    if getattr(save_manager, "_material_discovery_installed", False):
        return

    previous_load = save_manager.load_game

    def load_game(manager):
        result = previous_load(manager)
        if result:
            sync_material_discovery(manager)
        return result

    save_manager.load_game = load_game
    save_manager._material_discovery_installed = True


def _patch_muckford_gathering():
    try:
        from assets.tiles.muckford_objects import MuckfordTree, Smeltery
    except Exception:
        return

    if not getattr(MuckfordTree, "_rough_timber_installed", False):
        previous_tree_init = MuckfordTree.__init__

        def __init__(self, *args, **kwargs):
            previous_tree_init(self, *args, **kwargs)
            # This also fixes the floating harvest text, not just inventory keys.
            self.resource_name = "Rough Timber"

        MuckfordTree.__init__ = __init__
        MuckfordTree._rough_timber_installed = True

    if not getattr(Smeltery, "_canonical_labels_installed", False):
        previous_interact = Smeltery.interact
        previous_action = Smeltery.handle_menu_action

        def interact(self, manager):
            if self.interact_cooldown > 0:
                return

            if self.output_inventory:
                # Existing collection path already routes output through
                # GameManager.add_material, which canonicalizes and discovers it.
                return previous_interact(self, manager)

            status = (
                f"Storage: {self.scrap_stored} Scrap Iron, "
                f"{self.wood_stored} Rough Timber."
            )
            if self.current_job:
                timer = float(self.current_job.get("timer", 0))
                maximum = max(1.0, float(self.current_job.get("max_time", 1)))
                status += f" Working... ({int(timer / maximum * 100)}%)"

            options = [
                {"text": "Scrap Bar (2 Scrap Iron, 1 Rough Timber)",
                 "action": "smelter_scrap"},
                {"text": "Iron Ingot (2 Iron Ore, 1 Coal)",
                 "action": "smelter_iron"},
                {"text": "Deposit Resources", "action": "smelter_deposit"},
                {"text": "Cancel", "action": "close"},
            ]
            manager.start_dialogue(self, status, options)
            self.interact_cooldown = 20

        def handle_menu_action(self, action, manager):
            if self.current_job:
                return previous_action(self, action, manager)

            inventory = manager.inventory
            if action == "smelter_scrap":
                if (inventory.get("Scrap Iron", 0) >= 2
                        and inventory.get("Rough Timber", 0) >= 1):
                    inventory["Scrap Iron"] -= 2
                    inventory["Rough Timber"] -= 1
                    self.current_job = {
                        "output": "Scrap Metal Bar",
                        "timer": 0,
                        "max_time": 300,
                    }
                    sound_system.play_sound("click")
                    try:
                        manager.vfx.show_damage(
                            self.rect.centerx,
                            self.rect.top - 40,
                            "Smelting Scrap Bar...",
                            color=(200, 200, 200),
                        )
                    except Exception:
                        pass
                    return
            elif action == "smelter_iron":
                if (inventory.get("Iron Ore", 0) >= 2
                        and inventory.get("Coal", 0) >= 1):
                    inventory["Iron Ore"] -= 2
                    inventory["Coal"] -= 1
                    self.current_job = {
                        "output": "Iron Ingot",
                        "timer": 0,
                        "max_time": 400,
                    }
                    sound_system.play_sound("click")
                    try:
                        manager.vfx.show_damage(
                            self.rect.centerx,
                            self.rect.top - 40,
                            "Smelting Iron Ingot...",
                            color=(200, 200, 200),
                        )
                    except Exception:
                        pass
                    return

            return previous_action(self, action, manager)

        Smeltery.interact = interact
        Smeltery.handle_menu_action = handle_menu_action
        Smeltery._canonical_labels_installed = True


def install_material_integration_hardening():
    global _INSTALLED
    if _INSTALLED:
        return
    _patch_game_manager_discovery()
    _patch_save_discovery()
    _patch_muckford_gathering()
    _INSTALLED = True
