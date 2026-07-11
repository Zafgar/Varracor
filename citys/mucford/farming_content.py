"""Second content pass for Muckford farming.

This module extends the original farming system before the city instance is
created.  It keeps procedural art as a robust fallback while exposing stable
asset paths for future hand-painted crop stages.
"""

from __future__ import annotations

import math
import os
from collections import OrderedDict

import pygame

from items.farm_potions import (
    BitterleafTonic,
    MarshmintDraught,
    MoonpetalElixir,
    SiltrootAntidote,
    SunleafRestorative,
)
from items.tools.bucket import BucketEmpty
from items.tools.harvest_tools import (
    CrudeHarvestSickle,
    GuildHarvestScythe,
    IronHarvestSickle,
)
from settings import GOLD_COLOR, GRAY, GREEN, RED, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from ui_kit import UIButton, draw_text, font_main, font_small, font_title


HERB_DATA = {
    "Bitterleaf": {
        "required_level": 1,
        "required_tool_tier": 1,
        "growth_frames": 3000,
        "yield": (1, 3),
        "leaf": (68, 133, 62),
        "crop": (105, 160, 78),
        "flower": (184, 212, 112),
        "kind": "herb",
        "potion_use": "Health tonic base",
    },
    "Marsh Mint": {
        "required_level": 1,
        "required_tool_tier": 1,
        "growth_frames": 2800,
        "yield": (1, 3),
        "leaf": (48, 157, 126),
        "crop": (75, 192, 157),
        "flower": (174, 238, 222),
        "kind": "herb",
        "potion_use": "Stamina draught",
    },
    "Yarrow": {
        "required_level": 1,
        "required_tool_tier": 1,
        "growth_frames": 3200,
        "yield": (1, 2),
        "leaf": (94, 145, 72),
        "crop": (160, 176, 108),
        "flower": (235, 226, 174),
        "kind": "herb",
        "potion_use": "Wound binding and restorative mixtures",
    },
    "Siltroot": {
        "required_level": 2,
        "required_tool_tier": 2,
        "growth_frames": 3800,
        "yield": (1, 2),
        "leaf": (85, 115, 69),
        "crop": (154, 116, 62),
        "flower": (211, 173, 92),
        "kind": "herb",
        "potion_use": "Antidote base",
    },
    "Sunleaf": {
        "required_level": 2,
        "required_tool_tier": 2,
        "growth_frames": 4100,
        "yield": (1, 2),
        "leaf": (142, 157, 57),
        "crop": (211, 176, 61),
        "flower": (255, 221, 105),
        "kind": "herb",
        "potion_use": "Strong restorative",
    },
    "Moonpetal": {
        "required_level": 3,
        "required_tool_tier": 3,
        "growth_frames": 5000,
        "yield": (1, 2),
        "leaf": (76, 105, 145),
        "crop": (121, 118, 205),
        "flower": (192, 199, 255),
        "kind": "herb",
        "potion_use": "Mana elixir",
    },
    "Ironstem": {
        "required_level": 3,
        "required_tool_tier": 3,
        "growth_frames": 5200,
        "yield": (1, 2),
        "leaf": (77, 103, 79),
        "crop": (113, 126, 113),
        "flower": (184, 171, 138),
        "kind": "herb",
        "potion_use": "Fortifying brew ingredient",
    },
}

# Twenty real plots: repeated staple vegetables plus a dedicated herb quarter.
EXPANDED_PLOT_LAYOUT = (
    ("Carrot", 0, 0),
    ("Potato", 1, 0),
    ("Onion", 2, 0),
    ("Carrot", 3, 0),
    ("Potato", 4, 0),
    ("Cabbage", 0, 1),
    ("Turnip", 1, 1),
    ("Onion", 2, 1),
    ("Cabbage", 3, 1),
    ("Turnip", 4, 1),
    ("Bitterleaf", 0, 2),
    ("Marsh Mint", 1, 2),
    ("Yarrow", 2, 2),
    ("Siltroot", 3, 2),
    ("Sunleaf", 4, 2),
    ("Moonpetal", 0, 3),
    ("Ironstem", 1, 3),
    ("Bitterleaf", 2, 3),
    ("Marsh Mint", 3, 3),
    ("Yarrow", 4, 3),
)

POTION_RECIPES = OrderedDict({
    "Bitterleaf Tonic": {
        "ingredients": {"Bitterleaf": 2, "Marsh Mint": 1},
        "description": "Restores 25% maximum health.",
        "factory": BitterleafTonic,
    },
    "Marshmint Draught": {
        "ingredients": {"Marsh Mint": 2, "Potato": 1},
        "description": "Restores 55% maximum stamina.",
        "factory": MarshmintDraught,
    },
    "Siltroot Antidote": {
        "ingredients": {"Siltroot": 2, "Yarrow": 1},
        "description": "Clears poison-like effects and restores some health.",
        "factory": SiltrootAntidote,
    },
    "Moonpetal Elixir": {
        "ingredients": {"Moonpetal": 2, "Bitterleaf": 1},
        "description": "Restores 45% maximum mana.",
        "factory": MoonpetalElixir,
    },
    "Sunleaf Restorative": {
        "ingredients": {"Sunleaf": 2, "Yarrow": 1, "Quality Produce": 1},
        "description": "Strong healing and minor-injury treatment.",
        "factory": SunleafRestorative,
    },
})

_INSTALLED = False


def _safe_sound(name):
    try:
        sound_system.play_sound(name)
    except Exception:
        pass


def _asset_slug(name):
    return name.lower().replace(" ", "_").replace("'", "")


def _plot_asset(plot, stage):
    cache = getattr(plot, "_crop_asset_cache", None)
    if cache is None:
        plot._crop_asset_cache = {}
        cache = plot._crop_asset_cache
    if stage in cache:
        return cache[stage]

    slug = plot.data.get("asset_slug", _asset_slug(plot.crop_name))
    path = f"assets/tiles/farm/crops/{slug}_stage_{stage}.png"
    image = None
    if os.path.exists(path):
        try:
            raw = pygame.image.load(path)
            if pygame.display.get_surface():
                raw = raw.convert_alpha()
            image = pygame.transform.smoothscale(raw, (plot.WIDTH, plot.HEIGHT))
        except Exception:
            image = None
    cache[stage] = image
    return image


def _draw_crop_animation(plot, screen, offset):
    sx = plot.rect.x - offset[0]
    sy = plot.rect.y - offset[1]
    if sx > SCREEN_WIDTH or sy > SCREEN_HEIGHT or sx + plot.WIDTH < 0 or sy + plot.HEIGHT < 0:
        return

    stage = 4 if plot.ready else int(plot.growth_pct * 4)
    official = _plot_asset(plot, stage)
    if official:
        screen.blit(official, (sx, sy))
        return
    if stage <= 0:
        return

    now = pygame.time.get_ticks() * 0.003
    weather = str(getattr(getattr(getattr(plot, "_manager", None),
                                  "world_clock", None), "weather", "clear"))
    wind = 2.0 if weather in ("wind", "storm") else 1.0
    seed = getattr(plot, "_visual_seed", 0)
    leaf = plot.data["leaf"]
    flower = plot.data.get("flower")
    kind = plot.data.get("kind", "vegetable")

    # Animated representative sprouts over the static fallback crop rows.
    for index in range(10):
        col = (index * 3 + seed) % 7
        row = (index * 5 + seed // 7) % 4
        px = sx + 24 + col * 28
        ground_y = sy + 24 + row * 28
        stem_h = 4 + stage * 4
        sway = math.sin(now * wind + index * 0.83 + seed * 0.01) * (1.0 + stage * 0.8)
        top = (int(px + sway), int(ground_y - stem_h))
        pygame.draw.line(screen, leaf, (px, ground_y + 3), top, 2)
        leaf_w = 3 + stage
        pygame.draw.ellipse(screen, leaf,
                            (top[0] - leaf_w - 1, top[1] - 2, leaf_w + 2, 4))
        pygame.draw.ellipse(screen, leaf,
                            (top[0], top[1] + 1, leaf_w + 2, 4))
        if kind == "herb" and flower and stage >= 3:
            pygame.draw.circle(screen, flower, (top[0], top[1] - 2), 2 + stage // 2)

    # A few wind-carried leaves/pollen motes make ready fields feel alive.
    if stage >= 3:
        cycle = int(now * 18 + seed) % 240
        for particle in range(2):
            travel = (cycle + particle * 91) % 240
            px = sx + (travel / 240.0) * plot.WIDTH
            py = sy + 18 + ((seed + particle * 37) % 80) + math.sin(now + particle) * 5
            color = plot.data.get("flower", leaf) if kind == "herb" else leaf
            pygame.draw.ellipse(screen, color, (int(px), int(py), 4, 2))

    if plot.watered and not plot.ready:
        sparkle = int(now * 25 + seed) % 180
        for i in range(2):
            px = sx + 20 + ((sparkle * 3 + i * 79) % max(1, plot.WIDTH - 40))
            py = sy + plot.HEIGHT - 28 - i * 7
            pygame.draw.circle(screen, (145, 195, 235), (int(px), int(py)), 1)


def _migrate_legacy_herbs(manager):
    state = manager.npc_state.setdefault("farming", {})
    if state.get("named_herb_migration_done"):
        return
    for container_name in ("inventory", "city_storage"):
        container = getattr(manager, container_name, None)
        if not isinstance(container, dict):
            continue
        amount = int(container.pop("Medicinal Herb", 0))
        if amount:
            container["Bitterleaf"] = container.get("Bitterleaf", 0) + amount
    state["named_herb_migration_done"] = True


def _available(manager, name):
    return int(manager.inventory.get(name, 0)) + int(manager.city_storage.get(name, 0))


def _can_brew(manager, recipe):
    return all(_available(manager, name) >= amount
               for name, amount in recipe["ingredients"].items())


def _consume(manager, name, amount):
    remaining = int(amount)
    for container in (manager.inventory, manager.city_storage):
        take = min(remaining, int(container.get(name, 0)))
        if take:
            container[name] -= take
            remaining -= take
            if container[name] <= 0:
                container.pop(name, None)
        if remaining <= 0:
            return
    raise ValueError(f"Missing {name}")


def _patch_crop_plots(fe):
    CropPlot = fe.CropPlot
    if getattr(CropPlot, "_content_pass_installed", False):
        return

    previous_init = CropPlot.__init__
    previous_draw = CropPlot.draw_on_screen
    previous_harvest = CropPlot.harvest

    def __init__(self, x, y, crop_name, state, plot_id):
        previous_init(self, x, y, crop_name, state, plot_id)
        self._visual_seed = sum(ord(c) for c in plot_id) + x * 3 + y * 5
        self._crop_asset_cache = {}
        self._manager = None

    def update(self, obstacles=None, manager=None, *args, **kwargs):
        self._manager = manager
        return CropPlot._content_previous_update(self, obstacles, manager, *args, **kwargs)

    def draw_on_screen(self, screen, offset):
        previous_draw(self, screen, offset)
        _draw_crop_animation(self, screen, offset)

    def harvest(self, manager, harvester, to_storage=False, npc=False):
        destination = manager.city_storage if to_storage else manager.inventory
        before = int(destination.get(self.crop_name, 0))
        quality_before = int(destination.get("Quality Produce", 0))
        succeeded = previous_harvest(self, manager, harvester, to_storage, npc)
        if not succeeded:
            return False

        amount = int(destination.get(self.crop_name, 0)) - before
        quality = int(destination.get("Quality Produce", 0)) - quality_before
        farm_state = manager.npc_state.setdefault("farming", {})
        key = "npc_harvest_totals" if npc else "player_harvest_totals"
        totals = farm_state.setdefault(key, {})
        totals[self.crop_name] = totals.get(self.crop_name, 0) + max(0, amount)
        if quality:
            totals["Quality Produce"] = totals.get("Quality Produce", 0) + quality
        farm_state["total_harvest_actions"] = farm_state.get("total_harvest_actions", 0) + 1
        try:
            manager.vfx.create_falling_leaves(self.rect.centerx, self.rect.centery)
        except Exception:
            pass
        return True

    CropPlot._content_previous_update = CropPlot.update
    CropPlot.__init__ = __init__
    CropPlot.update = update
    CropPlot.draw_on_screen = draw_on_screen
    CropPlot.harvest = harvest
    CropPlot._content_pass_installed = True


def _patch_farming_system(fe):
    FarmingSystem = fe.FarmingSystem
    if getattr(FarmingSystem, "_content_pass_installed", False):
        return

    previous_init = FarmingSystem.__init__
    previous_equip = FarmingSystem._equip_farmer_npcs
    previous_draw = FarmingSystem.draw

    def __init__(self, city_menu):
        previous_init(self, city_menu)
        _migrate_legacy_herbs(self.manager)
        self._equip_farmer_npcs()

    def _equip_farmer_npcs(self):
        previous_equip(self)
        farmers = []
        for npc in getattr(self.city, "npcs", []):
            ai = getattr(npc, "ai_controller", None)
            if getattr(ai, "job", None) == "Farmer":
                farmers.append(npc)
        farmers.sort(key=lambda unit: getattr(unit, "name", ""))

        for index, npc in enumerate(farmers):
            if index == 0:
                tool = GuildHarvestScythe()
                skill = 3
            elif index <= 2:
                tool = IronHarvestSickle()
                skill = 2
            else:
                tool = CrudeHarvestSickle()
                skill = 1
            inventory = list(getattr(npc, "inventory", []) or [])
            inventory = [item for item in inventory
                         if getattr(item, "tool_type", "") != "harvest"]
            inventory.append(tool)
            if not any(isinstance(item, BucketEmpty) for item in inventory):
                inventory.append(BucketEmpty())
            npc.inventory = inventory
            npc.harvesting_skill = skill
            if hasattr(npc, "weapon_masteries"):
                npc.weapon_masteries.add("harvest_tool")

    def draw(self, screen):
        result = previous_draw(self, screen)
        farm = getattr(self.city.arena, "farm_area", None)
        player = self.city.player
        if not farm or not farm.collidepoint(player.rect.center):
            return result
        state = self.manager.npc_state.setdefault("farming", {})
        npc_total = sum(int(v) for v in state.get("npc_harvest_totals", {}).values())
        ready = sum(1 for plot in self.plots if plot.ready)
        growing = sum(1 for plot in self.plots if plot.watered and not plot.ready)
        panel = pygame.Surface((340, 58), pygame.SRCALPHA)
        panel.fill((20, 24, 20, 190))
        screen.blit(panel, (20, 172))
        draw_text(f"Fields: {len(self.plots)}   Ready: {ready}   Growing: {growing}",
                  font_small, WHITE, screen, 34, 181)
        draw_text(f"NPC produce stored: {npc_total}", font_small, GREEN,
                  screen, 34, 205)
        return result

    FarmingSystem.__init__ = __init__
    FarmingSystem._equip_farmer_npcs = _equip_farmer_npcs
    FarmingSystem.draw = draw
    FarmingSystem._content_pass_installed = True


def _patch_city_and_worker_ai():
    from ai.villager_ai import STATE_IDLE, VillagerAI
    from citys.mucford.muckford_city_menu import MuckfordCityMenu

    if not getattr(MuckfordCityMenu, "_farming_worker_fix_installed", False):
        previous_spawn_guards = MuckfordCityMenu._spawn_guards
        previous_simulation = MuckfordCityMenu._update_simulation

        def _spawn_guards(self):
            # _spawn_population already calls this; __init__ calls it once more.
            if getattr(self, "_guards_spawned_once", False):
                return
            self._guards_spawned_once = True
            return previous_spawn_guards(self)

        def _update_simulation(self):
            # City ambience must not overwrite movement owned by VillagerAI.
            all_npcs = self.npcs
            idle_npcs = []
            for npc in all_npcs:
                ai = getattr(npc, "ai_controller", None)
                working = isinstance(ai, VillagerAI) and (
                    getattr(ai, "state", STATE_IDLE) != STATE_IDLE
                    or getattr(ai, "work_target", None) is not None
                )
                if not working:
                    idle_npcs.append(npc)
            self.npcs = idle_npcs
            try:
                return previous_simulation(self)
            finally:
                self.npcs = all_npcs

        MuckfordCityMenu._spawn_guards = _spawn_guards
        MuckfordCityMenu._update_simulation = _update_simulation
        MuckfordCityMenu._farming_worker_fix_installed = True

    if not getattr(VillagerAI, "_farming_animation_installed", False):
        previous_handle_work = VillagerAI._handle_work

        def _handle_work(self, obstacles, all_units, manager):
            target = getattr(self, "work_target", None)
            if target and self.work_type in ("water_crop", "harvest_crop"):
                distance = math.hypot(target.rect.centerx - self.unit.rect.centerx,
                                      target.rect.centery - self.unit.rect.centery)
                if distance < 70:
                    if self.work_type == "harvest_crop":
                        self.unit.animation_state = "attack"
                        if self.state_timer % 55 == 0:
                            _safe_sound("grass_pickup")
                            try:
                                manager.vfx.create_falling_leaves(target.rect.centerx,
                                                                  target.rect.centery)
                            except Exception:
                                pass
                    else:
                        self.unit.animation_state = "working"
                        if self.state_timer % 70 == 0:
                            _safe_sound("water")
            return previous_handle_work(self, obstacles, all_units, manager)

        VillagerAI._handle_work = _handle_work
        VillagerAI._farming_animation_installed = True


def _patch_market():
    from lore.world_data import MARKET_PRICES
    from menus.market_menu import MarketMenu

    MARKET_PRICES["sell"].update({
        "Carrot": 3,
        "Potato": 3,
        "Onion": 4,
        "Cabbage": 6,
        "Turnip": 6,
        "Bitterleaf": 7,
        "Marsh Mint": 7,
        "Yarrow": 8,
        "Siltroot": 12,
        "Sunleaf": 15,
        "Moonpetal": 24,
        "Ironstem": 22,
        "Quality Produce": 15,
    })
    MARKET_PRICES["buy"].update({
        "Bucket of Water": {"price": 8, "kind": "item", "class": "BucketWater"},
        "Crude Harvest Sickle": {"price": 35, "kind": "item", "class": "CrudeHarvestSickle"},
        "Iron Harvest Sickle": {"price": 140, "kind": "item", "class": "IronHarvestSickle"},
        "Guild Harvest Scythe": {"price": 420, "kind": "item", "class": "GuildHarvestScythe"},
    })

    if getattr(MarketMenu, "_farming_scroll_installed", False):
        return
    previous_init = MarketMenu.__init__
    previous_sellable = MarketMenu._sellable_items
    previous_handle = MarketMenu.handle_event
    previous_draw = MarketMenu.draw
    visible_rows = 13

    def __init__(self, manager):
        previous_init(self, manager)
        self.sell_scroll = 0
        self.buy_scroll = 0

    def _sellable_items(self):
        all_items = previous_sellable(self)
        max_scroll = max(0, len(all_items) - visible_rows)
        self.sell_scroll = max(0, min(self.sell_scroll, max_scroll))
        return all_items[self.sell_scroll:self.sell_scroll + visible_rows]

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            mx, _ = pygame.mouse.get_pos()
            if mx < SCREEN_WIDTH // 2:
                count = len(previous_sellable(self))
                self.sell_scroll = max(0, min(
                    self.sell_scroll - event.y,
                    max(0, count - visible_rows)))
            else:
                count = len(MARKET_PRICES["buy"])
                self.buy_scroll = max(0, min(
                    self.buy_scroll - event.y,
                    max(0, count - visible_rows)))
            return
        return previous_handle(self, event)

    def draw(self, screen):
        full_buy = MARKET_PRICES["buy"]
        buy_items = list(full_buy.items())
        self.buy_scroll = max(0, min(
            self.buy_scroll, max(0, len(buy_items) - visible_rows)))
        MARKET_PRICES["buy"] = OrderedDict(
            buy_items[self.buy_scroll:self.buy_scroll + visible_rows])
        try:
            result = previous_draw(self, screen)
        finally:
            MARKET_PRICES["buy"] = full_buy
        if len(previous_sellable(self)) > visible_rows:
            draw_text("Mouse wheel: scroll goods", font_small, GRAY,
                      screen, SCREEN_WIDTH // 2 - 600, 820)
        if len(buy_items) > visible_rows:
            draw_text("Mouse wheel: scroll shop", font_small, GRAY,
                      screen, SCREEN_WIDTH // 2 + 60, 820)
        return result

    MarketMenu.__init__ = __init__
    MarketMenu._sellable_items = _sellable_items
    MarketMenu.handle_event = handle_event
    MarketMenu.draw = draw
    MarketMenu._farming_scroll_installed = True


def _patch_barracks_alchemy():
    from menus.barracks_menu import BarracksMenu

    if getattr(BarracksMenu, "_farm_alchemy_installed", False):
        return
    previous_init = BarracksMenu.__init__
    previous_handle = BarracksMenu.handle_event
    previous_draw = BarracksMenu.draw

    def __init__(self, manager):
        previous_init(self, manager)
        cx = SCREEN_WIDTH // 2
        self.btn_alchemy = UIButton(cx + 170, SCREEN_HEIGHT - 195, 300, 55,
                                    "HERBALIST BENCH", None, (73, 105, 74))
        self.show_alchemy = False
        self.alchemy_recipe_rects = []
        self.alchemy_feedback = ""
        self.alchemy_feedback_timer = 0

    def handle_event(self, event):
        if self.show_alchemy:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.show_alchemy = False
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, recipe_name in self.alchemy_recipe_rects:
                    if not rect.collidepoint(event.pos):
                        continue
                    recipe = POTION_RECIPES[recipe_name]
                    if not _can_brew(self.manager, recipe):
                        self.alchemy_feedback = "Missing herbs or produce."
                        self.alchemy_feedback_timer = 150
                        _safe_sound("error")
                        return
                    try:
                        for ingredient, amount in recipe["ingredients"].items():
                            _consume(self.manager, ingredient, amount)
                        potion = recipe["factory"]()
                        self.manager.equipment_bag.append(potion)
                        state = self.manager.npc_state.setdefault("farming", {})
                        brewed = state.setdefault("potions_brewed", {})
                        brewed[recipe_name] = brewed.get(recipe_name, 0) + 1
                        self.alchemy_feedback = f"Brewed {recipe_name}."
                        self.alchemy_feedback_timer = 180
                        _safe_sound("heal")
                    except ValueError:
                        self.alchemy_feedback = "Ingredients changed before brewing completed."
                        self.alchemy_feedback_timer = 150
                    return
            return

        if not getattr(self, "show_kitchen", False) and self.btn_alchemy.is_clicked(event):
            self.show_alchemy = True
            _safe_sound("click")
            return
        return previous_handle(self, event)

    def draw(self, screen):
        result = previous_draw(self, screen)
        if not getattr(self, "show_kitchen", False) and not self.show_alchemy:
            self.btn_alchemy.draw(screen)
        if self.alchemy_feedback_timer > 0:
            self.alchemy_feedback_timer -= 1
        if not self.show_alchemy:
            return result

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 225))
        screen.blit(overlay, (0, 0))
        panel = pygame.Rect(190, 85, SCREEN_WIDTH - 380, SCREEN_HEIGHT - 170)
        pygame.draw.rect(screen, (31, 45, 34), panel, border_radius=12)
        pygame.draw.rect(screen, (100, 145, 95), panel, 3, border_radius=12)
        draw_text("MUCKFORD HERBALIST BENCH", font_title, GOLD_COLOR,
                  screen, panel.x + 35, panel.y + 24)
        draw_text("Farm herbs become usable potions in the equipment bag.",
                  font_small, GRAY, screen, panel.x + 35, panel.y + 67)
        draw_text("ESC closes the bench", font_small, GRAY,
                  screen, panel.right - 170, panel.y + 30)

        self.alchemy_recipe_rects = []
        mouse = pygame.mouse.get_pos()
        y = panel.y + 105
        for name, recipe in POTION_RECIPES.items():
            rect = pygame.Rect(panel.x + 30, y, panel.w - 60, 112)
            can_brew = _can_brew(self.manager, recipe)
            hover = rect.collidepoint(mouse)
            bg = (55, 78, 55) if hover and can_brew else (43, 58, 44)
            if not can_brew:
                bg = (53, 40, 39)
            pygame.draw.rect(screen, bg, rect, border_radius=8)
            pygame.draw.rect(screen, (105, 151, 99) if can_brew else (95, 65, 60),
                             rect, 2, border_radius=8)
            draw_text(name, font_main, WHITE if can_brew else GRAY,
                      screen, rect.x + 16, rect.y + 12)
            draw_text(recipe["description"], font_small, (211, 220, 202),
                      screen, rect.x + 16, rect.y + 41)
            ingredients = "   ".join(
                f"{ingredient} {_available(self.manager, ingredient)}/{amount}"
                for ingredient, amount in recipe["ingredients"].items())
            draw_text(ingredients, font_small, GREEN if can_brew else RED,
                      screen, rect.x + 16, rect.y + 72)
            draw_text("CLICK TO BREW", font_small, GOLD_COLOR if can_brew else GRAY,
                      screen, rect.right - 145, rect.y + 12)
            self.alchemy_recipe_rects.append((rect, name))
            y += 124

        if self.alchemy_feedback_timer > 0:
            draw_text(self.alchemy_feedback, font_main, GREEN,
                      screen, panel.centerx - 190, panel.bottom - 35)
        return result

    BarracksMenu.__init__ = __init__
    BarracksMenu.handle_event = handle_event
    BarracksMenu.draw = draw
    BarracksMenu._farm_alchemy_installed = True


def install_farming_content():
    global _INSTALLED
    if _INSTALLED:
        return

    import citys.mucford.farming_expansion as fe

    # Expand the original data in place before any MuckfordCityMenu instance is built.
    for crop_name, data in HERB_DATA.items():
        data = dict(data)
        data["asset_slug"] = _asset_slug(crop_name)
        fe.CROP_DATA[crop_name] = data
    for crop_name, data in fe.CROP_DATA.items():
        data.setdefault("kind", "vegetable")
        data.setdefault("asset_slug", _asset_slug(crop_name))
    fe.PLOT_LAYOUT = EXPANDED_PLOT_LAYOUT

    # Named herb replaces the generic first-pass material in new saves/content.
    if "Rhea's Healer Broth" in fe.MEAL_RECIPES:
        fe.MEAL_RECIPES["Rhea's Healer Broth"]["ingredients"] = {
            "Bitterleaf": 1,
            "Carrot": 1,
            "Milk": 1,
        }

    _patch_crop_plots(fe)
    _patch_farming_system(fe)
    _patch_city_and_worker_ai()
    _patch_market()
    _patch_barracks_alchemy()
    _INSTALLED = True
