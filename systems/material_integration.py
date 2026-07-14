"""Runtime integration for Varrakor's canonical material registry.

The project still contains older material names in saves, props and recipes.
This module keeps those builds compatible while moving active gameplay to the
canonical names defined in ``lore.materials``.
"""

from __future__ import annotations

import random
from collections import OrderedDict

import pygame

from lore.materials import (
    COMMON_MARKET_STOCK,
    CRAFTED_COMPONENTS,
    MATERIALS,
    RARITY_COLORS,
    canonical_material_name,
    get_material_or_component,
    material_names,
    resource_tiers_view,
)


_INSTALLED = False


def _canonical_dict_keys(data):
    if not isinstance(data, dict):
        return data
    merged = {}
    for key, value in list(data.items()):
        canonical = canonical_material_name(key)
        if isinstance(value, (int, float)) and isinstance(merged.get(canonical), (int, float)):
            merged[canonical] += value
        elif canonical in merged and isinstance(value, dict) and isinstance(merged[canonical], dict):
            merged[canonical].update(value)
        else:
            merged[canonical] = value
    data.clear()
    data.update(merged)
    return data


def migrate_manager_materials(manager):
    """Canonicalize material keys in live state and old saves."""
    for attr in ("inventory", "city_storage", "loot_gained"):
        container = getattr(manager, attr, None)
        if isinstance(container, dict):
            _canonical_dict_keys(container)

    rewards = getattr(manager, "round_rewards", None)
    if isinstance(rewards, dict) and isinstance(rewards.get("loot"), dict):
        _canonical_dict_keys(rewards["loot"])

    npc_state = getattr(manager, "npc_state", None)
    if not isinstance(npc_state, dict):
        return

    farming = npc_state.get("farming", {})
    plots = farming.get("plots", {}) if isinstance(farming, dict) else {}
    if isinstance(plots, dict):
        renamed = {}
        for plot_id, state in list(plots.items()):
            new_id = str(plot_id)
            new_id = new_id.replace("_sunleaf", "_sunblossom")
            new_id = new_id.replace("_moonpetal", "_moondew_petals")
            new_id = new_id.replace("_medicinal_herb", "_bitterleaf")
            if isinstance(state, dict) and state.get("crop"):
                state["crop"] = canonical_material_name(state["crop"])
            renamed[new_id] = state
        plots.clear()
        plots.update(renamed)

    for ledger_key in ("npc_harvest_totals", "player_harvest_totals"):
        ledger = farming.get(ledger_key) if isinstance(farming, dict) else None
        if isinstance(ledger, dict):
            _canonical_dict_keys(ledger)

    stations = npc_state.get("crafting_stations", {}).get("stations", {})
    if isinstance(stations, dict):
        for node in stations.values():
            job = node.get("job") if isinstance(node, dict) else None
            if isinstance(job, dict) and isinstance(job.get("consumed_materials"), dict):
                _canonical_dict_keys(job["consumed_materials"])


def _canonicalize_recipe(recipe):
    if not isinstance(recipe, dict):
        return
    for key in ("mats", "ingredients", "materials"):
        if isinstance(recipe.get(key), dict):
            _canonical_dict_keys(recipe[key])


def _sync_blueprints_and_loot():
    import loot_data

    for name, recipe in loot_data.BLUEPRINTS.items():
        _canonicalize_recipe(recipe)
        lower = name.lower()
        if lower.startswith("scrap "):
            recipe.setdefault("station", "blacksmith")
            recipe.setdefault("station_tier", 1)
            recipe.setdefault("craft_minutes", 35)
        elif lower.startswith(("weak ", "iron ")) or name == "Bent Spear":
            recipe.setdefault("station", "blacksmith")
            recipe.setdefault("station_tier", 2)
            recipe.setdefault("craft_minutes", 70)
        elif "poison" in lower or name == "Rat King Shield":
            recipe.setdefault("station", "blacksmith")
            recipe.setdefault("station_tier", 2)
            recipe.setdefault("craft_minutes", 95)
        elif name == "Wooden Shield":
            recipe.setdefault("station", "carpenter")
            recipe.setdefault("station_tier", 1)
            recipe.setdefault("craft_minutes", 45)
        else:
            recipe.setdefault("station", "workshop")
            recipe.setdefault("station_tier", 1)
            recipe.setdefault("craft_minutes", 45)
        recipe.setdefault("output_amount", 1)

    for drops in loot_data.LOOT_DROPS.values():
        drop_list = drops if isinstance(drops, list) else [drops]
        for drop in drop_list:
            if drop.get("item"):
                drop["item"] = canonical_material_name(drop["item"])
            if isinstance(drop.get("one_of"), list):
                drop["one_of"] = [canonical_material_name(name)
                                  for name in drop["one_of"]]


def _sync_world_and_market():
    import lore.world_data as world_data

    world_data.RESOURCE_TIERS.clear()
    world_data.RESOURCE_TIERS.update(resource_tiers_view())

    sell = world_data.MARKET_PRICES.setdefault("sell", {})
    for name, data in MATERIALS.items():
        sell[name] = int(data["sell_price"])
    for name, data in CRAFTED_COMPONENTS.items():
        sell[name] = int(data["sell_price"])

    buy = world_data.MARKET_PRICES.setdefault("buy", {})
    for name, price in COMMON_MARKET_STOCK.items():
        buy.setdefault(name, {
            "price": int(price),
            "kind": "material",
            "class": None,
        })


def _replace_layout(layout):
    return tuple((canonical_material_name(crop), col, row)
                 for crop, col, row in layout)


def _rename_mapping_key(mapping, old, new):
    if old not in mapping:
        return
    value = mapping.pop(old)
    mapping.setdefault(new, value)


def _sync_farming_and_stations():
    try:
        import citys.mucford.farming_expansion as farming
        import citys.mucford.farming_content as content
        import citys.mucford.farming_content_hardening as content_hardening
        import citys.mucford.farming_stations as stations
    except Exception:
        return

    for old in ("Medicinal Herb", "Sunleaf", "Moonpetal"):
        new = canonical_material_name(old)
        _rename_mapping_key(farming.CROP_DATA, old, new)
        _rename_mapping_key(content.HERB_DATA, old, new)

    farming.PLOT_LAYOUT = _replace_layout(farming.PLOT_LAYOUT)
    content.EXPANDED_PLOT_LAYOUT = _replace_layout(content.EXPANDED_PLOT_LAYOUT)
    content_hardening.SAFE_PLOT_LAYOUT = _replace_layout(
        content_hardening.SAFE_PLOT_LAYOUT)

    for recipe in farming.MEAL_RECIPES.values():
        _canonicalize_recipe(recipe)
    for recipe in content.POTION_RECIPES.values():
        _canonicalize_recipe(recipe)

    # Canonical potion reagent identities while preserving existing potion
    # classes and display names for save compatibility.
    potion_inputs = {
        "Bitterleaf Tonic": {"Bitterleaf": 2, "Resin": 1},
        "Marshmint Draught": {"Marsh Mint": 2, "Sunblossom": 1},
        "Siltroot Antidote": {"Nightcap Fungus": 2, "Bitterleaf": 1},
        "Moonpetal Elixir": {"Moondew Petals": 2, "Focus Powder": 1},
        "Sunleaf Restorative": {"Sunblossom": 2, "Bitterleaf": 1,
                               "Resin": 1},
        "Ironstem Fortifier": {"Ironstem": 2, "Bitterleaf": 1,
                               "Resin": 1},
    }
    for name, ingredients in potion_inputs.items():
        if name in content.POTION_RECIPES:
            content.POTION_RECIPES[name]["ingredients"] = ingredients

    # Current Barracks components use canonical world inputs. Outputs remain
    # crafted components, intentionally separate from gathered materials.
    workbench_inputs = {
        "Bandage Roll": {"Plant Fiber": 2, "Bitterleaf": 1},
        "Treated Timber": {"Rough Timber": 3, "Resin": 1},
        "Leather Straps": {"Leather": 1, "Refined Binding Kit": 1},
        "Reinforced Cloth": {"Plant Fiber": 3,
                             "Refined Binding Kit": 1},
        "Precision Components": {"Iron Ingot": 2,
                                 "Silver Filigree Wire": 1,
                                 "Focus Powder": 1},
    }
    for name, ingredients in workbench_inputs.items():
        if name in stations.WORKBENCH_RECIPES:
            stations.WORKBENCH_RECIPES[name]["ingredients"] = ingredients

    for definition in stations.STATION_DEFINITIONS.values():
        for tier in definition.get("tiers", {}).values():
            _canonicalize_recipe(tier)
    for recipe in stations.WORKBENCH_RECIPES.values():
        _canonicalize_recipe(recipe)
    for recipe in stations.RECOVERY_RECIPES.values():
        _canonicalize_recipe(recipe)

    # Replace the last non-canonical high-tier reagents in station upgrades.
    stations.STATION_DEFINITIONS["herbalist"]["tiers"][3]["materials"] = {
        "Iron Ingot": 5,
        "Precision Components": 2,
        "Focus Crystal Shard": 1,
    }
    stations.STATION_DEFINITIONS["workbench"]["tiers"][3]["materials"] = {
        "Iron Ingot": 6,
        "Reinforced Cloth": 2,
        "Leather Straps": 2,
        "Arcane Dust": 1,
    }
    stations.STATION_DEFINITIONS["infirmary"]["tiers"][3]["materials"] = {
        "Iron Ingot": 5,
        "Precision Components": 1,
        "Sanctified Ember": 1,
    }

    CropPlot = farming.CropPlot
    if not getattr(CropPlot, "_plant_fiber_yield_installed", False):
        previous_harvest = CropPlot.harvest

        def harvest(self, manager, harvester, to_storage=False, npc=False):
            succeeded = previous_harvest(
                self, manager, harvester, to_storage=to_storage, npc=npc)
            if not succeeded:
                return False
            # Every second completed harvest returns useful stalk and leaf fiber.
            if int(getattr(self, "harvest_count", 0)) % 2 == 0:
                destination = (manager.city_storage if to_storage
                               else manager.inventory)
                destination["Plant Fiber"] = destination.get("Plant Fiber", 0) + 1
            return True

        CropPlot.harvest = harvest
        CropPlot._plant_fiber_yield_installed = True


def _install_tasks():
    try:
        from quests.material_contracts import get_active_material_tasks
        from quests.village_tasks import VILLAGE_TASKS
    except Exception:
        return
    existing = {task.get("id") for task in VILLAGE_TASKS}
    for task in get_active_material_tasks():
        if task["id"] not in existing:
            VILLAGE_TASKS.append(task)
            existing.add(task["id"])
    # Canonicalize older task objectives and rewards (Bogwort, Void Iron, etc.).
    for task in VILLAGE_TASKS:
        for stage in task.get("stages", []):
            if stage.get("item"):
                stage["item"] = canonical_material_name(stage["item"])
        rewards = task.get("rewards", {})
        if isinstance(rewards.get("material"), dict):
            _canonical_dict_keys(rewards["material"])


def _patch_game_manager():
    from game_manager import GameManager

    if getattr(GameManager, "_material_registry_installed", False):
        return

    original_init = GameManager.__init__
    original_known = GameManager._build_known_material_set
    original_add_material = GameManager.add_material
    original_add_loot = GameManager.add_loot_name

    def __init__(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        migrate_manager_materials(self)
        self._known_materials.update(material_names())

    def _build_known_material_set(self):
        known = set(original_known(self))
        known.update(material_names())
        return known

    def add_material(self, name, count=1):
        return original_add_material(self, canonical_material_name(name), count)

    def add_loot_name(self, item_name, count=1):
        return original_add_loot(self, canonical_material_name(item_name), count)

    def get_material_info(self, name):
        return get_material_or_component(name)

    GameManager.__init__ = __init__
    GameManager._build_known_material_set = _build_known_material_set
    GameManager.add_material = add_material
    GameManager.add_loot_name = add_loot_name
    GameManager.get_material_info = get_material_info
    GameManager._material_registry_installed = True


def _patch_save_load():
    try:
        import save_manager
    except Exception:
        return
    if getattr(save_manager, "_material_migration_installed", False):
        return
    original_load = save_manager.load_game

    def load_game(manager, *args, **kwargs):
        result = original_load(manager, *args, **kwargs)
        if result:
            migrate_manager_materials(manager)
            try:
                manager._known_materials.update(material_names())
            except Exception:
                pass
        return result

    save_manager.load_game = load_game
    save_manager._material_migration_installed = True


def _patch_market_codex():
    try:
        from menus.market_menu import MarketMenu
        from settings import SCREEN_WIDTH
        from ui_kit import draw_text, font_small, font_main
    except Exception:
        return
    if getattr(MarketMenu, "_material_codex_installed", False):
        return
    previous_draw = MarketMenu.draw

    def draw(self, screen):
        result = previous_draw(self, screen)
        mouse = pygame.mouse.get_pos()
        hovered = None
        for rect, name in list(getattr(self, "sell_rects", [])):
            if rect.collidepoint(mouse):
                hovered = name
                break
        if hovered is None:
            for rect, name in list(getattr(self, "buy_rects", [])):
                if rect.collidepoint(mouse):
                    hovered = name
                    break
        info = get_material_or_component(hovered) if hovered else None
        if not info:
            return result

        panel = pygame.Surface((760, 84), pygame.SRCALPHA)
        panel.fill((18, 18, 24, 225))
        x = SCREEN_WIDTH // 2 - 380
        y = 82
        screen.blit(panel, (x, y))
        rarity = info.get("rarity", "Common")
        level_max = info.get("level_max")
        level_text = (f"Level {info.get('level_min', 1)}+" if level_max is None
                      else f"Level {info.get('level_min', 1)}-{level_max}")
        heading = f"{info['name']}  |  {rarity}  |  {level_text}"
        draw_text(heading, font_main, RARITY_COLORS.get(rarity, (220, 220, 220)),
                  screen, x + 14, y + 8)
        draw_text(str(info.get("lore", "")), font_small, (220, 215, 200),
                  screen, x + 14, y + 36)
        draw_text(f"Source: {info.get('source', 'Unknown')}   Station: {info.get('station', 'None')}",
                  font_small, (165, 175, 190), screen, x + 14, y + 59)
        return result

    MarketMenu.draw = draw
    MarketMenu._material_codex_installed = True


def _patch_muckford_props():
    try:
        from assets.tiles.muckford_objects import ScrapPileBig, Smeltery
    except Exception:
        return

    if not getattr(ScrapPileBig, "_canonical_materials_installed", False):
        previous_init = ScrapPileBig.__init__

        def __init__(self, *args, **kwargs):
            previous_init(self, *args, **kwargs)
            self.loot_table = [canonical_material_name(name)
                               for name in self.loot_table]

        ScrapPileBig.__init__ = __init__
        ScrapPileBig._canonical_materials_installed = True

    if not getattr(Smeltery, "_canonical_materials_installed", False):
        previous_handle = Smeltery.handle_menu_action

        def handle_menu_action(self, action, manager):
            inv = manager.inventory
            if action == "smelter_scrap":
                if inv.get("Scrap Iron", 0) >= 2 and inv.get("Rough Timber", 0) >= 1:
                    inv["Scrap Iron"] -= 2
                    inv["Rough Timber"] -= 1
                    self.current_job = {"output": "Scrap Metal Bar",
                                        "timer": 0, "max_time": 300}
                    return
                return previous_handle(self, action, manager)
            if action == "smelter_iron":
                if inv.get("Iron Ore", 0) >= 2 and inv.get("Coal", 0) >= 1:
                    inv["Iron Ore"] -= 2
                    inv["Coal"] -= 1
                    self.current_job = {"output": "Iron Ingot",
                                        "timer": 0, "max_time": 400}
                    return
                return previous_handle(self, action, manager)
            if action == "smelter_deposit":
                # The old implementation looks for Swamp Wood. Temporarily
                # expose the canonical timber count and merge the remainder back.
                rough = int(inv.get("Rough Timber", 0))
                inv["Swamp Wood"] = rough
                previous_handle(self, action, manager)
                remaining = int(inv.pop("Swamp Wood", 0))
                if remaining:
                    inv["Rough Timber"] = remaining
                else:
                    inv.pop("Rough Timber", None)
                return
            return previous_handle(self, action, manager)

        Smeltery.handle_menu_action = handle_menu_action
        Smeltery._canonical_materials_installed = True


def install_material_integration():
    global _INSTALLED
    if _INSTALLED:
        return
    _sync_blueprints_and_loot()
    _sync_world_and_market()
    _sync_farming_and_stations()
    _install_tasks()
    _patch_game_manager()
    _patch_save_load()
    _patch_market_codex()
    _patch_muckford_props()
    _INSTALLED = True
