"""Muckford farming expansion.

This module is deliberately installed as a small runtime extension instead of
making the already large ``muckford_city_menu.py`` even larger.  It adds:

* six persistent crop plots with watering and growth stages;
* a three-rank Harvesting skill and tiered harvest tools;
* farmer NPC work for watering and harvesting excess crops;
* quality produce and market prices;
* a Team Quarters kitchen with healing meals and temporary battle buffs;
* light-weight post-battle injuries that food or normal healing can clear.

The extension is installed from ``menus.barracks_menu`` after the relevant
classes have been imported.  All persistent farming data is stored inside
``manager.npc_state['farming']``, which is already covered by save_manager.
"""

from __future__ import annotations

import math
import random
from typing import Dict, Iterable, Optional

import pygame

from assets.tiles.prop import Prop
from items.tools.bucket import BucketEmpty, BucketWater
from items.tools.harvest_tools import (
    CrudeHarvestSickle,
    GuildHarvestScythe,
    IronHarvestSickle,
)
from settings import GOLD_COLOR, GRAY, GREEN, RED, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from ui_kit import UIButton, draw_text, font_main, font_small, font_title


CROP_DATA = {
    "Carrot": {
        "required_level": 1,
        "required_tool_tier": 1,
        "growth_frames": 2400,
        "yield": (1, 2),
        "leaf": (65, 150, 75),
        "crop": (230, 115, 35),
    },
    "Potato": {
        "required_level": 1,
        "required_tool_tier": 1,
        "growth_frames": 2800,
        "yield": (1, 3),
        "leaf": (75, 135, 65),
        "crop": (176, 133, 72),
    },
    "Onion": {
        "required_level": 1,
        "required_tool_tier": 1,
        "growth_frames": 2600,
        "yield": (1, 2),
        "leaf": (80, 160, 95),
        "crop": (225, 215, 165),
    },
    "Cabbage": {
        "required_level": 2,
        "required_tool_tier": 2,
        "growth_frames": 3600,
        "yield": (1, 2),
        "leaf": (55, 135, 65),
        "crop": (80, 165, 85),
    },
    "Turnip": {
        "required_level": 2,
        "required_tool_tier": 2,
        "growth_frames": 3400,
        "yield": (1, 2),
        "leaf": (65, 150, 78),
        "crop": (205, 188, 210),
    },
    "Medicinal Herb": {
        "required_level": 3,
        "required_tool_tier": 3,
        "growth_frames": 4400,
        "yield": (1, 2),
        "leaf": (55, 175, 125),
        "crop": (120, 225, 175),
    },
}

PLOT_LAYOUT = (
    ("Carrot", 0, 0),
    ("Potato", 1, 0),
    ("Onion", 2, 0),
    ("Cabbage", 0, 1),
    ("Turnip", 1, 1),
    ("Medicinal Herb", 2, 1),
)

MEAL_RECIPES = {
    "Muckford Root Stew": {
        "ingredients": {"Carrot": 2, "Potato": 2, "Onion": 1},
        "description": "+10% max HP and +1 DEF for 3 battles.",
        "remaining_battles": 3,
        "effects": {"max_hp_pct": 0.10, "defense": 1},
        "heal_pct": 0.20,
    },
    "Arena Farmer's Hash": {
        "ingredients": {"Potato": 2, "Cabbage": 1, "Egg": 1},
        "description": "+2 STR and +1 DEX for 2 battles.",
        "remaining_battles": 2,
        "effects": {"strength": 2, "dexterity": 1},
        "heal_pct": 0.10,
    },
    "Rhea's Healer Broth": {
        "ingredients": {"Medicinal Herb": 1, "Carrot": 1, "Milk": 1},
        "description": "Heals the whole roster and removes injuries.",
        "remaining_battles": 0,
        "effects": {},
        "heal_pct": 1.0,
        "clear_injuries": True,
    },
    "Mudwater Fish Stew": {
        "ingredients": {"Mudfin": 2, "Bogwort": 1, "Onion": 1},
        "description": "+15 max stamina and +1 DEF for 2 battles.",
        "remaining_battles": 2,
        "effects": {"max_stamina": 15, "defense": 1},
        "heal_pct": 0.25,
    },
    "Smoked Bog Perch": {
        "ingredients": {"Bog Perch": 2, "Swamp Wood": 1},
        "description": "+1 STR and +1 DEX for 2 battles.",
        "remaining_battles": 2,
        "effects": {"strength": 1, "dexterity": 1},
        "heal_pct": 0.15,
    },
    "Pike Roast": {
        "ingredients": {"Marsh Pike": 1, "Carrot": 1, "Medicinal Herb": 1},
        "description": "+10% max HP and +2 STR for 3 battles.",
        "remaining_battles": 3,
        "effects": {"max_hp_pct": 0.10, "strength": 2},
        "heal_pct": 0.30,
    },
    "Prime Guild Feast": {
        "ingredients": {"Quality Produce": 3, "Milk": 1, "Egg": 2},
        "description": "+2 STR, DEX and INT for 3 battles.",
        "remaining_battles": 3,
        "effects": {"strength": 2, "dexterity": 2, "intelligence": 2},
        "heal_pct": 0.35,
    },
}

_INSTALLED = False
_ORIGINAL_CALCULATE_FINAL_STATS = None


def harvesting_level(unit) -> int:
    """Return the highest unlocked Commander harvesting rank."""
    skills = set(getattr(unit, "unlocked_skills", set()) or set())
    if "harvesting_3" in skills:
        return 3
    if "harvesting_2" in skills:
        return 2
    if "harvesting_1" in skills:
        return 1
    return 0


def equipped_harvest_tool(unit):
    item = getattr(unit, "equipment", {}).get("main_hand")
    return item if getattr(item, "tool_type", "") == "harvest" else None


def _safe_sound(name: str):
    try:
        sound_system.play_sound(name)
    except Exception:
        pass


def _show(manager, x, y, text, color=WHITE):
    try:
        manager.vfx.show_damage(x, y, text, color=color)
    except Exception:
        pass


def _iter_team(manager) -> Iterable:
    seen = set()
    commander = getattr(manager, "player_character", None)
    if commander is not None:
        seen.add(id(commander))
        yield commander
    for unit in list(getattr(manager, "my_team", [])):
        if id(unit) not in seen:
            seen.add(id(unit))
            yield unit


class CropPlot(Prop):
    """One automatically replanted Muckford crop plot."""

    WIDTH = 220
    HEIGHT = 138

    def __init__(self, x: int, y: int, crop_name: str, state: dict, plot_id: str):
        super().__init__(x, y, self.WIDTH, self.HEIGHT, color=(92, 68, 42))
        self.crop_name = crop_name
        self.data = CROP_DATA[crop_name]
        self.plot_id = plot_id
        self.state = state
        self.is_structure = False
        self.blocks_projectiles = False
        self.has_shadow = False
        self.is_flat = True  # piirretään lattiapassissa - ei koskaan heron päälle
        self.name = f"{crop_name} Plot"
        self.interaction_range = 75
        self.interaction_label = "Farm"
        self.being_worked_on = False
        self._last_visual_key = None
        self._load_state()
        self._redraw(force=True)

    def _load_state(self):
        self.growth_ticks = int(self.state.get("growth_ticks", 0))
        self.watered = bool(self.state.get("watered", False))
        self.harvest_count = int(self.state.get("harvest_count", 0))
        self._save_state()

    def rebind_state(self, state: dict):
        self.state = state
        self._load_state()
        self._redraw(force=True)

    def _save_state(self):
        self.state["crop"] = self.crop_name
        self.state["growth_ticks"] = int(self.growth_ticks)
        self.state["watered"] = bool(self.watered)
        self.state["harvest_count"] = int(self.harvest_count)

    @property
    def ready(self) -> bool:
        return self.growth_ticks >= self.data["growth_frames"]

    @property
    def growth_pct(self) -> float:
        return min(1.0, self.growth_ticks / max(1, self.data["growth_frames"]))

    def update(self, obstacles=None, manager=None, *args, **kwargs):
        # Rain waters the fields automatically when the clock exposes weather.
        if manager and not self.watered and not self.ready:
            weather = str(getattr(getattr(manager, "world_clock", None), "weather", "")).lower()
            if "rain" in weather:
                self.watered = True

        if self.watered and not self.ready:
            self.growth_ticks += 1
            if self.ready:
                self.growth_ticks = self.data["growth_frames"]
                _show(manager, self.rect.centerx, self.rect.top - 10,
                      f"{self.crop_name} ready!", GOLD_COLOR)
        self._save_state()
        self._redraw()

    def water(self, manager=None, worker=None, consume_bucket=False) -> bool:
        if self.ready or self.watered:
            return False
        if consume_bucket and not _consume_water_bucket(worker, manager):
            _show(manager, self.rect.centerx, self.rect.top - 10,
                  "Need a Bucket of Water", RED)
            _safe_sound("error")
            return False
        self.watered = True
        self._save_state()
        self._redraw(force=True)
        _safe_sound("water")
        _show(manager, self.rect.centerx, self.rect.top - 10,
              f"Watered {self.crop_name}", (100, 180, 255))
        return True

    def harvest(self, manager, harvester, to_storage=False, npc=False) -> bool:
        if not self.ready:
            return False

        tool = equipped_harvest_tool(harvester)
        tool_tier = int(getattr(tool, "tool_tier", 1 if npc else 0))
        skill_level = 3 if npc else harvesting_level(harvester)
        required_level = int(self.data["required_level"])
        required_tier = int(self.data["required_tool_tier"])

        if skill_level < required_level:
            _show(manager, self.rect.centerx, self.rect.top - 10,
                  f"Requires Harvesting {required_level}", RED)
            _safe_sound("error")
            return False
        if tool_tier < required_tier:
            _show(manager, self.rect.centerx, self.rect.top - 10,
                  f"Requires Tier {required_tier} harvest tool", RED)
            _safe_sound("error")
            return False

        low, high = self.data["yield"]
        amount = random.randint(low, high)
        amount += max(0, tool_tier - required_tier)
        amount += max(0, skill_level - required_level)
        # Commander-puun harvest_yield (Harvesting II) - ei koske NPC:itä
        amount += int(getattr(harvester, "harvest_yield", 0))

        destination = manager.city_storage if to_storage else manager.inventory
        destination[self.crop_name] = destination.get(self.crop_name, 0) + amount

        quality_chance = max(0.0, 0.12 * (tool_tier - 1) + 0.08 * (skill_level - 1))
        # Master Harvesterin harvest_quality kasvattaa laatusadon mahdollisuutta
        quality_chance += float(getattr(harvester, "harvest_quality", 0.0))
        quality = 1 if random.random() < quality_chance else 0
        if quality:
            destination["Quality Produce"] = destination.get("Quality Produce", 0) + quality

        self.harvest_count += 1
        self.growth_ticks = 0
        self.watered = False
        self._save_state()
        self._redraw(force=True)

        suffix = " + Quality Produce" if quality else ""
        _show(manager, self.rect.centerx, self.rect.top - 10,
              f"+{amount} {self.crop_name}{suffix}", GREEN)
        _safe_sound("grass_pickup")
        return True

    def interaction_text(self) -> str:
        if self.ready:
            return f"Harvest {self.crop_name}"
        if not self.watered:
            return f"Water {self.crop_name}"
        return f"Growing {int(self.growth_pct * 100)}%"

    def _redraw(self, force=False):
        stage = 4 if self.ready else int(self.growth_pct * 4)
        key = (stage, self.watered, self.ready)
        if not force and key == self._last_visual_key:
            return
        self._last_visual_key = key

        self.image = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (76, 54, 34), (0, 0, self.WIDTH, self.HEIGHT), border_radius=8)
        pygame.draw.rect(self.image, (132, 101, 61), (0, 0, self.WIDTH, self.HEIGHT), 3, border_radius=8)

        # Furrows.
        for row in range(4):
            y = 24 + row * 28
            pygame.draw.line(self.image, (57, 40, 26), (12, y + 9), (self.WIDTH - 12, y + 9), 5)
            for col in range(7):
                x = 24 + col * 28
                if stage <= 0:
                    pygame.draw.circle(self.image, (47, 34, 24), (x, y), 2)
                    continue
                stem_h = 3 + stage * 3
                pygame.draw.line(self.image, self.data["leaf"], (x, y + 4), (x, y - stem_h), 2)
                radius = 2 + stage
                pygame.draw.circle(self.image, self.data["crop"], (x, y), radius)
                if stage >= 3:
                    pygame.draw.line(self.image, self.data["leaf"], (x, y - stem_h),
                                     (x - 4, y - stem_h - 4), 2)
                    pygame.draw.line(self.image, self.data["leaf"], (x, y - stem_h),
                                     (x + 4, y - stem_h - 3), 2)

        if self.watered and not self.ready:
            water = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
            water.fill((60, 120, 190, 25))
            self.image.blit(water, (0, 0))

    def draw_on_screen(self, screen, offset):
        super().draw_on_screen(screen, offset)
        x = self.rect.x - offset[0]
        y = self.rect.y - offset[1]
        bar = pygame.Rect(x + 12, y + self.HEIGHT - 12, self.WIDTH - 24, 6)
        pygame.draw.rect(screen, (35, 28, 22), bar, border_radius=3)
        fill = bar.copy()
        fill.w = int(bar.w * self.growth_pct)
        if fill.w > 0:
            pygame.draw.rect(screen, (85, 180, 90) if self.ready else (110, 155, 80),
                             fill, border_radius=3)


def _consume_water_bucket(worker, manager) -> bool:
    if worker is None:
        return False
    equipped = getattr(worker, "equipment", {}).get("main_hand")
    if isinstance(equipped, BucketWater):
        worker.equipment["main_hand"] = BucketEmpty()
        worker.primary_weapon = worker.equipment["main_hand"]
        worker.current_weapon = worker.primary_weapon
        return True

    bag = getattr(manager, "equipment_bag", []) if manager else []
    for index, item in enumerate(list(bag)):
        if isinstance(item, BucketWater):
            bag[index] = BucketEmpty()
            return True
    return False


class FarmingSystem:
    def __init__(self, city_menu):
        self.city = city_menu
        self.manager = city_menu.manager
        self.plots = []
        self._create_plots()
        self._equip_farmer_npcs()
        _restore_meal_buff(self.manager)

    def _state_root(self):
        npc_state = getattr(self.manager, "npc_state", None)
        if npc_state is None:
            self.manager.npc_state = {"global": {"reputation": 0, "flags": {}}}
            npc_state = self.manager.npc_state
        return npc_state.setdefault("farming", {})

    def _create_plots(self):
        arena = self.city.arena
        if getattr(arena, "crop_plots", None):
            self.plots = list(arena.crop_plots)
            self.rebind_state()
            return
        farm = getattr(arena, "farm_area", None)
        if farm is None:
            return

        state_root = self._state_root().setdefault("plots", {})
        start_x = farm.x + 1240
        start_y = farm.y + 130
        gap_x = CropPlot.WIDTH + 28
        gap_y = CropPlot.HEIGHT + 32

        for index, (crop, col, row) in enumerate(PLOT_LAYOUT):
            plot_id = f"plot_{index}_{crop.lower().replace(' ', '_')}"
            state = state_root.setdefault(plot_id, {
                "crop": crop,
                "growth_ticks": random.randint(0, CROP_DATA[crop]["growth_frames"] // 3),
                "watered": False,
                "harvest_count": 0,
            })
            plot = CropPlot(start_x + col * gap_x, start_y + row * gap_y,
                            crop, state, plot_id)
            arena.props.append(plot)
            self.plots.append(plot)

        arena.crop_plots = self.plots
        # BUGIKORJAUS: portti oli alareunan sisäpuolella, mutta kyläläiset
        # tulevat kaupungista POHJOISESTA - he jumittivat yläaitaan.
        # Yläaidan aukko on segmentissä i==2 (256 px segmentit) ->
        # aukon keskikohta x + 640.
        arena.farm_gate_pos = (farm.x + 640, farm.y)

    def rebind_state(self):
        root = self._state_root().setdefault("plots", {})
        for plot in self.plots:
            state = root.setdefault(plot.plot_id, {
                "crop": plot.crop_name,
                "growth_ticks": 0,
                "watered": False,
                "harvest_count": 0,
            })
            plot.rebind_state(state)
        _restore_meal_buff(self.manager)

    def _equip_farmer_npcs(self):
        for npc in getattr(self.city, "npcs", []):
            ai = getattr(npc, "ai_controller", None)
            if getattr(ai, "job", None) != "Farmer":
                continue
            inventory = getattr(npc, "inventory", None)
            if inventory is None:
                npc.inventory = []
                inventory = npc.inventory
            if not any(getattr(i, "tool_type", "") == "harvest" for i in inventory):
                inventory.append(CrudeHarvestSickle())

    def nearest_plot(self, radius=85) -> Optional[CropPlot]:
        player = self.city.player
        best = None
        best_dist = radius
        for plot in self.plots:
            dist = math.hypot(player.rect.centerx - plot.rect.centerx,
                              player.rect.centery - plot.rect.centery)
            if dist < best_dist:
                best = plot
                best_dist = dist
        return best

    def handle_event(self, event) -> bool:
        if event.type != pygame.KEYDOWN or event.key != pygame.K_e:
            return False
        if (getattr(self.city, "show_pause_menu", False)
                or getattr(self.manager, "show_inventory", False)
                or getattr(self.manager, "active_dialogue", None)
                or getattr(self.city, "show_map", False)):
            return False

        plot = self.nearest_plot()
        if plot is None:
            return False

        if plot.ready:
            plot.harvest(self.manager, self.city.player, to_storage=False, npc=False)
        elif not plot.watered:
            plot.water(self.manager, self.city.player, consume_bucket=True)
        else:
            _show(self.manager, plot.rect.centerx, plot.rect.top - 10,
                  f"{plot.crop_name}: {int(plot.growth_pct * 100)}%", WHITE)
        return True

    def draw(self, screen):
        if not self.plots:
            return
        offset = (self.city.camera_x, self.city.camera_y)
        player = self.city.player

        for plot in self.plots:
            dist = math.hypot(player.rect.centerx - plot.rect.centerx,
                              player.rect.centery - plot.rect.centery)
            if dist < 105:
                self.manager._draw_floating_prompt(
                    screen, plot.rect.centerx, plot.rect.top - 12,
                    "E", offset, plot.interaction_text())

        farm = getattr(self.city.arena, "farm_area", None)
        if farm and farm.collidepoint(player.rect.center):
            level = harvesting_level(player)
            tool = equipped_harvest_tool(player)
            tier = int(getattr(tool, "tool_tier", 0))
            panel = pygame.Surface((340, 72), pygame.SRCALPHA)
            panel.fill((20, 24, 20, 190))
            screen.blit(panel, (20, 95))
            draw_text("MUCKFORD FARM", font_main, GOLD_COLOR, screen, 34, 104)
            draw_text(f"Harvesting {level}/3   Tool tier {tier}/3",
                      font_small, WHITE, screen, 34, 132)
            draw_text("Water with a Bucket of Water; harvest with a sickle.",
                      font_small, GRAY, screen, 34, 150)


# ---------------------------------------------------------------------------
# Meal and injury helpers
# ---------------------------------------------------------------------------

def _farming_state(manager):
    return manager.npc_state.setdefault("farming", {})


def _available_material(manager, name: str) -> int:
    return int(manager.inventory.get(name, 0)) + int(manager.city_storage.get(name, 0))


def _consume_material(manager, name: str, amount: int):
    remaining = amount
    take = min(remaining, int(manager.inventory.get(name, 0)))
    if take:
        manager.inventory[name] -= take
        remaining -= take
        if manager.inventory[name] <= 0:
            manager.inventory.pop(name, None)
    if remaining:
        take = min(remaining, int(manager.city_storage.get(name, 0)))
        manager.city_storage[name] -= take
        remaining -= take
        if manager.city_storage[name] <= 0:
            manager.city_storage.pop(name, None)
    if remaining:
        raise ValueError(f"Not enough {name}")


def _can_cook(manager, recipe: dict) -> bool:
    return all(_available_material(manager, name) >= amount
               for name, amount in recipe["ingredients"].items())


def _restore_meal_buff(manager):
    data = _farming_state(manager).get("meal_buff")
    effects = dict(data.get("effects", {})) if data and data.get("remaining_battles", 0) > 0 else {}
    for unit in _iter_team(manager):
        unit._farming_meal_effects = effects
        try:
            unit.calculate_final_stats()
            unit.current_hp = min(unit.current_hp, unit.max_hp)
        except Exception:
            pass


def _apply_meal(manager, name: str, recipe: dict):
    heal_pct = float(recipe.get("heal_pct", 0.0))
    clear_injuries = bool(recipe.get("clear_injuries", False))
    for unit in _iter_team(manager):
        if heal_pct:
            unit.current_hp = min(unit.max_hp,
                                  unit.current_hp + max(1, int(unit.max_hp * heal_pct)))
        if clear_injuries or unit.current_hp >= unit.max_hp * 0.90:
            unit.injured = False
            unit.injury_severity = None

    remaining = int(recipe.get("remaining_battles", 0))
    effects = dict(recipe.get("effects", {}))
    if remaining > 0 and effects:
        _farming_state(manager)["meal_buff"] = {
            "name": name,
            "remaining_battles": remaining,
            "effects": effects,
        }
    else:
        _farming_state(manager).pop("meal_buff", None)
    _restore_meal_buff(manager)


def _advance_meal_buff(manager):
    state = _farming_state(manager)
    data = state.get("meal_buff")
    if not data:
        return
    data["remaining_battles"] = int(data.get("remaining_battles", 0)) - 1
    if data["remaining_battles"] <= 0:
        state.pop("meal_buff", None)
    _restore_meal_buff(manager)


def _apply_post_battle_injuries(manager):
    defeat = str(getattr(manager, "match_result", "")).upper() == "DEFEAT"
    threshold = 0.60 if defeat else 0.28
    for unit in _iter_team(manager):
        hp_pct = unit.current_hp / max(1, unit.max_hp)
        dead = bool(getattr(unit, "is_dead", False)) or unit.current_hp <= 0
        if dead or hp_pct <= threshold:
            unit.injured = True
            unit.injury_severity = "Serious" if dead or hp_pct <= 0.20 else "Minor"
            if unit.current_hp <= 0:
                unit.current_hp = max(1, int(unit.max_hp * 0.15))


# ---------------------------------------------------------------------------
# Monkey-patch installers
# ---------------------------------------------------------------------------

def _patch_city(MuckfordCityMenu):
    if getattr(MuckfordCityMenu, "_farming_expansion_installed", False):
        return

    original_init = MuckfordCityMenu.__init__
    original_event = MuckfordCityMenu.handle_event
    original_draw = MuckfordCityMenu.draw
    original_on_enter = MuckfordCityMenu.on_enter

    def __init__(self, manager):
        original_init(self, manager)
        self.farming_system = FarmingSystem(self)

    def handle_event(self, event):
        system = getattr(self, "farming_system", None)
        if system and system.handle_event(event):
            return
        return original_event(self, event)

    def draw(self, screen):
        result = original_draw(self, screen)
        system = getattr(self, "farming_system", None)
        if system:
            system.draw(screen)
        return result

    def on_enter(self):
        result = original_on_enter(self)
        system = getattr(self, "farming_system", None)
        if system:
            system.manager = self.manager
            system.rebind_state()
            system._equip_farmer_npcs()
        return result

    MuckfordCityMenu.__init__ = __init__
    MuckfordCityMenu.handle_event = handle_event
    MuckfordCityMenu.draw = draw
    MuckfordCityMenu.on_enter = on_enter
    MuckfordCityMenu._farming_expansion_installed = True


def _patch_villager_ai(VillagerAI):
    if getattr(VillagerAI, "_crop_work_installed", False):
        return
    original_find = VillagerAI._find_farm_work
    original_finish = VillagerAI._finish_work

    def _find_farm_work(self, all_units, manager):
        if self.job == "Farmer" and manager and getattr(manager, "current_arena", None):
            plots = [p for p in getattr(manager.current_arena, "crop_plots", [])
                     if isinstance(p, CropPlot) and not p.being_worked_on]
            ripe = [p for p in plots if p.ready]
            dry = [p for p in plots if not p.ready and not p.watered]

            # Leave one ripe plot for the player whenever possible.
            if len(ripe) >= 2:
                self.work_target = random.choice(ripe)
                self.work_target.being_worked_on = True
                self.work_type = "harvest_crop"
                self._equip_tool("harvest")
                self.state_timer = random.randint(180, 300)
                return True
            if dry:
                self.work_target = random.choice(dry)
                self.work_target.being_worked_on = True
                self.work_type = "water_crop"
                self._equip_tool("bucket")
                self.state_timer = random.randint(120, 240)
                return True
        return original_find(self, all_units, manager)

    def _finish_work(self, manager):
        if isinstance(self.work_target, CropPlot):
            if self.work_type == "water_crop":
                self.work_target.water(manager, self.unit, consume_bucket=False)
            elif self.work_type == "harvest_crop":
                self.work_target.harvest(manager, self.unit, to_storage=True, npc=True)
            return
        return original_finish(self, manager)

    VillagerAI._find_farm_work = _find_farm_work
    VillagerAI._finish_work = _finish_work
    VillagerAI._crop_work_installed = True


def _patch_gladiator(Gladiator):
    global _ORIGINAL_CALCULATE_FINAL_STATS
    if getattr(Gladiator, "_meal_effects_installed", False):
        return

    _ORIGINAL_CALCULATE_FINAL_STATS = Gladiator.calculate_final_stats

    def calculate_final_stats(self):
        result = _ORIGINAL_CALCULATE_FINAL_STATS(self)
        effects = dict(getattr(self, "_farming_meal_effects", {}) or {})
        self.strength += effects.get("strength", 0)
        self.dexterity += effects.get("dexterity", 0)
        self.intelligence += effects.get("intelligence", 0)
        self.defense += effects.get("defense", 0)
        self.max_stamina += effects.get("max_stamina", 0)
        if effects.get("max_hp_pct"):
            self.max_hp = max(1, int(self.max_hp * (1.0 + effects["max_hp_pct"])))
        if effects.get("max_hp"):
            self.max_hp += int(effects["max_hp"])
        return result

    Gladiator.calculate_final_stats = calculate_final_stats

    original_heal = getattr(Gladiator, "heal", None)
    if original_heal:
        def heal(self, *args, **kwargs):
            result = original_heal(self, *args, **kwargs)
            if self.current_hp >= self.max_hp * 0.90:
                self.injured = False
                self.injury_severity = None
            return result
        Gladiator.heal = heal

    Gladiator._meal_effects_installed = True


def _patch_game_manager(GameManager):
    if getattr(GameManager, "_farming_battle_hooks_installed", False):
        return
    original_update_match = GameManager.update_match

    def update_match(self, *args, **kwargs):
        was_over = bool(getattr(self, "match_over", False))
        result = original_update_match(self, *args, **kwargs)
        if not was_over and bool(getattr(self, "match_over", False)):
            _apply_post_battle_injuries(self)
            _advance_meal_buff(self)
        return result

    GameManager.update_match = update_match
    GameManager._farming_battle_hooks_installed = True


def _patch_save_manager():
    try:
        import save_manager
    except Exception:
        return
    if getattr(save_manager, "_farming_save_installed", False):
        return

    original_serialize = save_manager._serialize_unit
    original_apply = save_manager._apply_unit_state

    def _serialize_unit(unit):
        data = original_serialize(unit)
        data["current_hp"] = float(getattr(unit, "current_hp", 0))
        data["injured"] = bool(getattr(unit, "injured", False))
        data["injury_severity"] = getattr(unit, "injury_severity", None)
        return data

    def _apply_unit_state(unit, data):
        result = original_apply(unit, data)
        unit.current_hp = max(1, min(unit.max_hp, float(data.get("current_hp", unit.max_hp))))
        unit.injured = bool(data.get("injured", False))
        unit.injury_severity = data.get("injury_severity")
        return result

    save_manager._serialize_unit = _serialize_unit
    save_manager._apply_unit_state = _apply_unit_state
    save_manager._farming_save_installed = True


def _patch_barracks(BarracksMenu):
    if getattr(BarracksMenu, "_kitchen_installed", False):
        return

    original_init = BarracksMenu.__init__
    original_event = BarracksMenu.handle_event
    original_draw = BarracksMenu.draw

    def __init__(self, manager):
        original_init(self, manager)
        cx = SCREEN_WIDTH // 2
        self.btn_kitchen = UIButton(cx - 150, SCREEN_HEIGHT - 195, 300, 55,
                                    "KITCHEN & MEALS", None, (115, 82, 45))
        self.show_kitchen = False
        self.kitchen_recipe_rects = []
        self.kitchen_feedback = ""
        self.kitchen_feedback_timer = 0
        _restore_meal_buff(manager)

    def handle_event(self, event):
        if self.show_kitchen:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.show_kitchen = False
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, recipe_name in self.kitchen_recipe_rects:
                    if rect.collidepoint(event.pos):
                        recipe = MEAL_RECIPES[recipe_name]
                        if not _can_cook(self.manager, recipe):
                            self.kitchen_feedback = "Missing ingredients. Check inventory and city storage."
                            self.kitchen_feedback_timer = 150
                            _safe_sound("error")
                            return
                        try:
                            for material, amount in recipe["ingredients"].items():
                                _consume_material(self.manager, material, amount)
                            _apply_meal(self.manager, recipe_name, recipe)
                            self.kitchen_feedback = f"Served {recipe_name}."
                            self.kitchen_feedback_timer = 180
                            _safe_sound("heal")
                        except ValueError:
                            self.kitchen_feedback = "The ingredients changed before the meal was cooked."
                            self.kitchen_feedback_timer = 150
                        return
            return

        if self.btn_kitchen.is_clicked(event):
            self.show_kitchen = True
            _safe_sound("click")
            return
        return original_event(self, event)

    def draw(self, screen):
        result = original_draw(self, screen)
        self.btn_kitchen.draw(screen)

        # Injury labels on roster cards.
        for rect, unit in getattr(self, "card_rects", []):
            if getattr(unit, "injured", False):
                severity = getattr(unit, "injury_severity", "Minor") or "Minor"
                pygame.draw.rect(screen, (105, 25, 25),
                                 (rect.x + 8, rect.bottom - 48, rect.w - 16, 24),
                                 border_radius=4)
                draw_text(f"INJURED: {severity}", font_small, WHITE,
                          screen, rect.x + 18, rect.bottom - 45)

        if self.kitchen_feedback_timer > 0:
            self.kitchen_feedback_timer -= 1

        if not self.show_kitchen:
            return result

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))
        panel = pygame.Rect(180, 90, SCREEN_WIDTH - 360, SCREEN_HEIGHT - 180)
        pygame.draw.rect(screen, (45, 35, 27), panel, border_radius=12)
        pygame.draw.rect(screen, (145, 110, 65), panel, 3, border_radius=12)
        draw_text("TEAM QUARTERS KITCHEN", font_title, GOLD_COLOR,
                  screen, panel.x + 35, panel.y + 24)
        draw_text("Ingredients are taken from your inventory first, then Muckford city storage.",
                  font_small, GRAY, screen, panel.x + 35, panel.y + 68)

        self.kitchen_recipe_rects = []
        mouse = pygame.mouse.get_pos()
        y = panel.y + 110
        for name, recipe in MEAL_RECIPES.items():
            rect = pygame.Rect(panel.x + 30, y, panel.w - 60, 118)
            can_cook = _can_cook(self.manager, recipe)
            hover = rect.collidepoint(mouse)
            bg = (70, 58, 40) if hover and can_cook else (54, 45, 36)
            if not can_cook:
                bg = (52, 36, 34)
            pygame.draw.rect(screen, bg, rect, border_radius=8)
            pygame.draw.rect(screen, (135, 105, 65) if can_cook else (95, 65, 60),
                             rect, 2, border_radius=8)
            draw_text(name, font_main, WHITE if can_cook else GRAY,
                      screen, rect.x + 16, rect.y + 12)
            draw_text(recipe["description"], font_small, (215, 205, 185),
                      screen, rect.x + 16, rect.y + 42)
            ingredient_text = "   ".join(
                f"{ingredient} { _available_material(self.manager, ingredient) }/{amount}"
                for ingredient, amount in recipe["ingredients"].items())
            draw_text(ingredient_text, font_small, GREEN if can_cook else RED,
                      screen, rect.x + 16, rect.y + 76)
            draw_text("CLICK TO COOK", font_small, GOLD_COLOR if can_cook else GRAY,
                      screen, rect.right - 145, rect.y + 12)
            self.kitchen_recipe_rects.append((rect, name))
            y += 132

        buff = _farming_state(self.manager).get("meal_buff")
        if buff:
            draw_text(f"Active meal: {buff.get('name')} ({buff.get('remaining_battles', 0)} battles)",
                      font_main, GOLD_COLOR, screen, panel.x + 35, panel.bottom - 58)
        if self.kitchen_feedback_timer > 0:
            draw_text(self.kitchen_feedback, font_main, GREEN,
                      screen, panel.centerx - 220, panel.bottom - 30)
        draw_text("ESC closes kitchen", font_small, GRAY,
                  screen, panel.right - 150, panel.y + 30)
        return result

    BarracksMenu.__init__ = __init__
    BarracksMenu.handle_event = handle_event
    BarracksMenu.draw = draw
    BarracksMenu._kitchen_installed = True


def _extend_market_prices():
    try:
        from lore.world_data import MARKET_PRICES
    except Exception:
        return
    sell = MARKET_PRICES.setdefault("sell", {})
    sell.update({
        "Carrot": 3,
        "Potato": 3,
        "Onion": 4,
        "Cabbage": 6,
        "Turnip": 6,
        "Medicinal Herb": 12,
        "Quality Produce": 15,
    })
    buy = MARKET_PRICES.setdefault("buy", {})
    buy.setdefault("Crude Harvest Sickle", {
        "price": 35, "kind": "gear", "class": "CrudeHarvestSickle"})
    buy.setdefault("Iron Harvest Sickle", {
        "price": 140, "kind": "gear", "class": "IronHarvestSickle"})
    buy.setdefault("Guild Harvest Scythe", {
        "price": 420, "kind": "gear", "class": "GuildHarvestScythe"})


def install_farming_expansion():
    """Install the expansion exactly once for the current Python process."""
    global _INSTALLED
    if _INSTALLED:
        return

    from ai.villager_ai import VillagerAI
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from game_manager import GameManager
    from gladiator import Gladiator
    from menus.barracks_menu import BarracksMenu

    _patch_gladiator(Gladiator)
    _patch_game_manager(GameManager)
    _patch_save_manager()
    _patch_villager_ai(VillagerAI)
    _patch_city(MuckfordCityMenu)
    _patch_barracks(BarracksMenu)
    _extend_market_prices()
    _INSTALLED = True
