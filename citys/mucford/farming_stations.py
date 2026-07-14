"""Tiered, player-owned crafting stations for the Muckford Team Quarters.

The heavy production chain remains location based:

* the town Smeltery converts ore and scrap into bars;
* the Scrap Iron Smithy turns bars into weapons, shields and metal tools;
* the Team Quarters handles food, portable medicine, utility components and
  long-form roster recovery.

Station state and active jobs are JSON-safe and live in
``manager.npc_state['crafting_stations']``. Jobs use real elapsed time, so they
continue during battles and can finish while the game is closed.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Dict, Iterable, Optional, Tuple

import pygame

from settings import (
    GOLD_COLOR,
    GRAY,
    GREEN,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
)
from sound_manager import sound_system
from ui_kit import UIButton, draw_text, font_main, font_small, font_header, format_money


# One Varracor game day is approximately fifteen real minutes.
REAL_SECONDS_PER_GAME_MINUTE = 15.0 * 60.0 / 1440.0
MAX_STATION_TIER = 3


STATION_DEFINITIONS = OrderedDict({
    "kitchen": {
        "title": "Barracks Kitchen",
        "description": "Turns farm produce into roster healing and battle meals.",
        "legacy_level": 1,
        "tiers": {
            1: {
                "name": "Makeshift Hearth",
                "speed": 1.00,
                "minutes": 0,
                "gold": 0,
                "materials": {},
            },
            2: {
                "name": "Field Kitchen",
                "speed": 0.80,
                "minutes": 360,
                "gold": 160,
                "materials": {"Treated Timber": 4, "Scrap Metal Bar": 4},
            },
            3: {
                "name": "Guild Kitchen",
                "speed": 0.62,
                "minutes": 720,
                "gold": 480,
                "materials": {"Iron Bar": 5, "Reinforced Cloth": 3,
                              "Quality Produce": 3},
            },
        },
    },
    "herbalist": {
        "title": "Herbalist Station",
        "description": "Brews portable potions from named Muckford herbs.",
        "legacy_level": 1,
        "tiers": {
            1: {
                "name": "Makeshift Herb Table",
                "speed": 1.00,
                "minutes": 0,
                "gold": 0,
                "materials": {},
            },
            2: {
                "name": "Alchemy Bench",
                "speed": 0.78,
                "minutes": 420,
                "gold": 190,
                "materials": {"Treated Timber": 3, "Iron Bar": 2,
                              "Reinforced Cloth": 1},
            },
            3: {
                "name": "Guild Distillery",
                "speed": 0.58,
                "minutes": 780,
                "gold": 560,
                "materials": {"Iron Bar": 5, "Precision Components": 2,
                              "Spirit Essence": 1},
            },
        },
    },
    "workbench": {
        "title": "Quartermaster Workbench",
        "description": "Makes medical supplies and components for later upgrades.",
        "legacy_level": 0,
        "tiers": {
            1: {
                "name": "Salvage Table",
                "speed": 1.00,
                "minutes": 240,
                "gold": 100,
                "materials": {"Swamp Wood": 10, "Scrap Iron": 6},
            },
            2: {
                "name": "Quartermaster Bench",
                "speed": 0.78,
                "minutes": 480,
                "gold": 280,
                "materials": {"Scrap Metal Bar": 5, "Iron Bar": 2,
                              "Treated Timber": 2},
            },
            3: {
                "name": "Guild Artisan Bench",
                "speed": 0.58,
                "minutes": 840,
                "gold": 650,
                "materials": {"Iron Bar": 6, "Reinforced Cloth": 2,
                              "Spirit Essence": 1},
            },
        },
    },
    "infirmary": {
        "title": "Recovery Ward",
        "description": "Slow, efficient treatment for the entire arena roster.",
        "legacy_level": 0,
        "tiers": {
            1: {
                "name": "Recovery Cot",
                "speed": 1.00,
                "minutes": 300,
                "gold": 130,
                "materials": {"Treated Timber": 4, "Bandage Roll": 4},
            },
            2: {
                "name": "Field Infirmary",
                "speed": 0.78,
                "minutes": 540,
                "gold": 340,
                "materials": {"Iron Bar": 2, "Reinforced Cloth": 3,
                              "Bandage Roll": 4},
            },
            3: {
                "name": "Guild Recovery Ward",
                "speed": 0.60,
                "minutes": 900,
                "gold": 760,
                "materials": {"Iron Bar": 5, "Precision Components": 1,
                              "Spirit Essence": 2},
            },
        },
    },
})


ADDITIONAL_MEALS = OrderedDict({
    "Farmhand Breakfast": {
        "ingredients": {"Potato": 1, "Egg": 1, "Milk": 1},
        "description": "+15 maximum stamina for 2 battles; heals 15%.",
        "remaining_battles": 2,
        "effects": {"max_stamina": 15},
        "heal_pct": 0.15,
    },
    "Marshwarden Herb Pie": {
        "ingredients": {"Cabbage": 1, "Onion": 1, "Yarrow": 1, "Egg": 1},
        "description": "+1 DEX and +1 INT for 3 battles; heals 25%.",
        "remaining_battles": 3,
        "effects": {"dexterity": 1, "intelligence": 1},
        "heal_pct": 0.25,
    },
    "Champion's Banquet": {
        "ingredients": {"Quality Produce": 3, "Sunleaf": 1,
                        "Milk": 1, "Egg": 2},
        "description": "+3 STR and +2 DEF for 2 battles; heals 50%.",
        "remaining_battles": 2,
        "effects": {"strength": 3, "defense": 2},
        "heal_pct": 0.50,
    },
})


MEAL_TIERS = {
    "Muckford Root Stew": (1, 35),
    "Arena Farmer's Hash": (1, 40),
    "Farmhand Breakfast": (1, 30),
    "Rhea's Healer Broth": (2, 70),
    "Marshwarden Herb Pie": (2, 65),
    "Prime Guild Feast": (3, 110),
    "Champion's Banquet": (3, 120),
}

POTION_TIERS = {
    "Bitterleaf Tonic": (1, 25),
    "Marshmint Draught": (1, 25),
    "Siltroot Antidote": (2, 45),
    "Sunleaf Restorative": (2, 55),
    "Moonpetal Elixir": (3, 70),
    "Ironstem Fortifier": (3, 75),
}

WORKBENCH_RECIPES = OrderedDict({
    "Bandage Roll": {
        "tier": 1,
        "minutes": 35,
        "ingredients": {"Yarrow": 1, "Spider Silk": 1},
        "description": "Produces two clean dressings used by the Recovery Ward.",
        "output": {"kind": "material", "name": "Bandage Roll", "amount": 2},
    },
    "Treated Timber": {
        "tier": 1,
        "minutes": 45,
        "ingredients": {"Swamp Wood": 3, "Siltroot": 1},
        "description": "Stable construction timber for station upgrades.",
        "output": {"kind": "material", "name": "Treated Timber", "amount": 1},
    },
    "Leather Straps": {
        "tier": 2,
        "minutes": 65,
        "ingredients": {"Troll Hide": 1, "Siltroot": 1},
        "description": "Produces two durable straps for armor and equipment work.",
        "output": {"kind": "material", "name": "Leather Straps", "amount": 2},
    },
    "Reinforced Cloth": {
        "tier": 2,
        "minutes": 70,
        "ingredients": {"Spider Silk": 2, "Yarrow": 1},
        "description": "Strong cloth for advanced kitchens, wards and armor parts.",
        "output": {"kind": "material", "name": "Reinforced Cloth", "amount": 1},
    },
    "Precision Components": {
        "tier": 3,
        "minutes": 110,
        "ingredients": {"Iron Bar": 2, "Scrap Metal Bar": 2,
                        "Moonpetal": 1},
        "description": "Fine mechanisms for master-grade stations and devices.",
        "output": {"kind": "material", "name": "Precision Components", "amount": 1},
    },
})

RECOVERY_RECIPES = OrderedDict({
    "Dress Wounds": {
        "tier": 1,
        "minutes": 180,
        "ingredients": {"Bandage Roll": 2, "Bitterleaf": 1},
        "description": "Heals the roster by 35% and clears minor injuries.",
        "recovery": {"heal_pct": 0.35, "clear_minor": True},
    },
    "Healer's Recovery": {
        "tier": 2,
        "minutes": 300,
        "ingredients": {"Bandage Roll": 2, "Sunleaf": 1, "Milk": 1},
        "description": "Heals 65%; serious injuries become minor.",
        "recovery": {"heal_pct": 0.65, "clear_minor": True,
                     "serious_to_minor": True},
    },
    "Full Guild Recovery": {
        "tier": 3,
        "minutes": 480,
        "ingredients": {"Bandage Roll": 3, "Sunleaf": 2,
                        "Moonpetal": 1},
        "description": "Fully heals the roster and clears all injuries.",
        "recovery": {"heal_pct": 1.0, "clear_all": True},
    },
})


_INSTALLED = False


def _safe_sound(name: str):
    try:
        sound_system.play_sound(name)
    except Exception:
        pass


def _iter_roster(manager) -> Iterable:
    seen = set()
    commander = getattr(manager, "player_character", None)
    if commander is not None:
        seen.add(id(commander))
        yield commander
    for unit in list(getattr(manager, "my_team", [])):
        if id(unit) not in seen:
            seen.add(id(unit))
            yield unit


def _root_state(manager) -> dict:
    npc_state = getattr(manager, "npc_state", None)
    if not isinstance(npc_state, dict):
        manager.npc_state = {"global": {"reputation": 0, "flags": {}}}
    root = manager.npc_state.setdefault("crafting_stations", {})
    stations = root.setdefault("stations", {})
    for station_id, definition in STATION_DEFINITIONS.items():
        node = stations.setdefault(station_id, {})
        node.setdefault("level", int(definition["legacy_level"]))
        node.setdefault("job", None)
        node.setdefault("completed_jobs", 0)
    root.setdefault("crafting_xp", 0)
    root.setdefault("last_message", "")
    root.setdefault("last_message_time", 0.0)
    return root


def station_node(manager, station_id: str) -> dict:
    return _root_state(manager)["stations"][station_id]


def station_level(manager, station_id: str) -> int:
    return max(0, min(MAX_STATION_TIER,
                      int(station_node(manager, station_id).get("level", 0))))


def available_material(manager, name: str) -> int:
    return (int(getattr(manager, "inventory", {}).get(name, 0))
            + int(getattr(manager, "city_storage", {}).get(name, 0)))


def can_pay_materials(manager, materials: Dict[str, int]) -> bool:
    return all(available_material(manager, name) >= int(amount)
               for name, amount in materials.items())


def consume_materials(manager, materials: Dict[str, int]):
    if not can_pay_materials(manager, materials):
        raise ValueError("Missing materials")
    for name, requested in materials.items():
        remaining = int(requested)
        for container in (manager.inventory, manager.city_storage):
            take = min(remaining, int(container.get(name, 0)))
            if take:
                container[name] -= take
                remaining -= take
                if container[name] <= 0:
                    container.pop(name, None)
            if remaining <= 0:
                break


def _duration_seconds(game_minutes: float, station_tier: int) -> float:
    speed = STATION_DEFINITIONS[next(iter(STATION_DEFINITIONS))]["tiers"][1]["speed"]
    # The caller passes the actual station tier multiplier below; this fallback
    # simply keeps zero/invalid values safe.
    return max(1.0, float(game_minutes) * REAL_SECONDS_PER_GAME_MINUTE * speed)


def _station_speed(station_id: str, level: int) -> float:
    if level <= 0:
        return 1.0
    return float(STATION_DEFINITIONS[station_id]["tiers"][level]["speed"])


def _set_message(manager, text: str, now: Optional[float] = None):
    root = _root_state(manager)
    root["last_message"] = str(text)
    root["last_message_time"] = float(time.time() if now is None else now)


def _recipe_catalog(station_id: str) -> OrderedDict:
    if station_id == "kitchen":
        from citys.mucford.farming_expansion import MEAL_RECIPES
        recipes = OrderedDict()
        for name, recipe in MEAL_RECIPES.items():
            tier, minutes = MEAL_TIERS.get(name, (1, 45))
            data = dict(recipe)
            data.update({"tier": tier, "minutes": minutes,
                         "station_kind": "meal"})
            recipes[name] = data
        return recipes

    if station_id == "herbalist":
        from citys.mucford.farming_content import POTION_RECIPES
        recipes = OrderedDict()
        for name, recipe in POTION_RECIPES.items():
            tier, minutes = POTION_TIERS.get(name, (1, 35))
            data = dict(recipe)
            data.update({"tier": tier, "minutes": minutes,
                         "station_kind": "potion"})
            recipes[name] = data
        return recipes

    if station_id == "workbench":
        return OrderedDict((name, dict(recipe))
                           for name, recipe in WORKBENCH_RECIPES.items())
    if station_id == "infirmary":
        return OrderedDict((name, dict(recipe))
                           for name, recipe in RECOVERY_RECIPES.items())
    return OrderedDict()


def begin_station_upgrade(manager, station_id: str,
                          now: Optional[float] = None) -> Tuple[bool, str]:
    if station_id not in STATION_DEFINITIONS:
        return False, "Unknown station."
    node = station_node(manager, station_id)
    if node.get("job"):
        return False, "Station is already busy."
    level = station_level(manager, station_id)
    if level >= MAX_STATION_TIER:
        return False, "Station is already at maximum tier."

    target = level + 1
    tier_data = STATION_DEFINITIONS[station_id]["tiers"][target]
    materials = dict(tier_data.get("materials", {}))
    gold = int(tier_data.get("gold", 0))
    if int(getattr(manager, "gold", 0)) < gold:
        return False, "Not enough gold."
    if not can_pay_materials(manager, materials):
        return False, "Missing construction materials."

    manager.gold -= gold
    consume_materials(manager, materials)
    started = float(time.time() if now is None else now)
    seconds = max(1.0, float(tier_data.get("minutes", 1))
                  * REAL_SECONDS_PER_GAME_MINUTE)
    node["job"] = {
        "kind": "upgrade",
        "target_level": target,
        "display_name": tier_data["name"],
        "started_at": started,
        "finish_at": started + seconds,
        "duration_seconds": seconds,
    }
    _set_message(manager, f"Construction started: {tier_data['name']}.", started)
    return True, f"Building {tier_data['name']}."


def begin_station_recipe(manager, station_id: str, recipe_name: str,
                         now: Optional[float] = None) -> Tuple[bool, str]:
    if station_id not in STATION_DEFINITIONS:
        return False, "Unknown station."
    node = station_node(manager, station_id)
    if node.get("job"):
        return False, "Station is already busy."
    level = station_level(manager, station_id)
    if level <= 0:
        return False, "Build this station first."

    recipes = _recipe_catalog(station_id)
    recipe = recipes.get(recipe_name)
    if not recipe:
        return False, "Unknown recipe."
    required_tier = int(recipe.get("tier", 1))
    if level < required_tier:
        return False, f"Requires station tier {required_tier}."
    ingredients = dict(recipe.get("ingredients", {}))
    if not can_pay_materials(manager, ingredients):
        return False, "Missing ingredients."

    consume_materials(manager, ingredients)
    started = float(time.time() if now is None else now)
    speed = _station_speed(station_id, level)
    seconds = max(1.0, float(recipe.get("minutes", 30))
                  * REAL_SECONDS_PER_GAME_MINUTE * speed)
    node["job"] = {
        "kind": "craft",
        "recipe": recipe_name,
        "started_at": started,
        "finish_at": started + seconds,
        "duration_seconds": seconds,
    }
    _set_message(manager, f"Started: {recipe_name}.", started)
    return True, f"Crafting {recipe_name}."


def _apply_recovery(manager, data: dict):
    heal_pct = float(data.get("heal_pct", 0.0))
    clear_all = bool(data.get("clear_all", False))
    clear_minor = bool(data.get("clear_minor", False))
    serious_to_minor = bool(data.get("serious_to_minor", False))
    for unit in _iter_roster(manager):
        maximum = max(1, int(getattr(unit, "max_hp", 1)))
        current = float(getattr(unit, "current_hp", 0))
        unit.current_hp = min(maximum,
                              current + max(1, int(maximum * heal_pct)))
        severity = getattr(unit, "injury_severity", None)
        if clear_all:
            unit.injured = False
            unit.injury_severity = None
        elif severity == "Serious" and serious_to_minor:
            unit.injured = True
            unit.injury_severity = "Minor"
        elif severity in (None, "Minor") and clear_minor:
            unit.injured = False
            unit.injury_severity = None
        unit.is_dead = False


def _complete_recipe(manager, station_id: str, recipe_name: str):
    recipe = _recipe_catalog(station_id)[recipe_name]
    if station_id == "kitchen":
        from citys.mucford.farming_expansion import _apply_meal
        _apply_meal(manager, recipe_name, recipe)
        return f"Meal served: {recipe_name}."

    if station_id == "herbalist":
        potion = recipe["factory"]()
        manager.equipment_bag.append(potion)
        return f"Potion ready: {recipe_name}."

    if station_id == "workbench":
        output = dict(recipe.get("output", {}))
        name = output.get("name", recipe_name)
        amount = max(1, int(output.get("amount", 1)))
        manager.city_storage[name] = manager.city_storage.get(name, 0) + amount
        return f"Completed: {amount} x {name} sent to city storage."

    if station_id == "infirmary":
        _apply_recovery(manager, dict(recipe.get("recovery", {})))
        return f"Treatment completed: {recipe_name}."

    return f"Completed: {recipe_name}."


def process_station_jobs(manager, now: Optional[float] = None) -> list:
    current = float(time.time() if now is None else now)
    root = _root_state(manager)
    completed = []
    for station_id, node in root["stations"].items():
        job = node.get("job")
        if not job or current < float(job.get("finish_at", current + 1)):
            continue
        try:
            if job.get("kind") == "upgrade":
                target = int(job.get("target_level", node.get("level", 0)))
                node["level"] = max(0, min(MAX_STATION_TIER, target))
                message = f"Station completed: {job.get('display_name', 'upgrade')}."
            else:
                message = _complete_recipe(manager, station_id,
                                           str(job.get("recipe", "")))
            node["completed_jobs"] = int(node.get("completed_jobs", 0)) + 1
            root["crafting_xp"] = int(root.get("crafting_xp", 0)) + 5
        except Exception as exc:
            # Do not leave a station permanently locked because one output type
            # changed during development. Record a visible error and free it.
            message = f"{STATION_DEFINITIONS[station_id]['title']} job failed: {exc}"
        node["job"] = None
        completed.append(message)
        _set_message(manager, message, current)
    return completed


def job_progress(node: dict, now: Optional[float] = None) -> float:
    job = node.get("job")
    if not job:
        return 0.0
    current = float(time.time() if now is None else now)
    start = float(job.get("started_at", current))
    finish = float(job.get("finish_at", start + 1))
    return max(0.0, min(1.0, (current - start) / max(0.001, finish - start)))


def remaining_text(node: dict, now: Optional[float] = None) -> str:
    job = node.get("job")
    if not job:
        return "Idle"
    current = float(time.time() if now is None else now)
    seconds = max(0, int(float(job.get("finish_at", current)) - current))
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes:02d}:{seconds:02d} remaining"


def _cost_text(manager, materials: Dict[str, int], gold: int) -> str:
    parts = [f"{name} {available_material(manager, name)}/{amount}"
             for name, amount in materials.items()]
    if gold:
        parts.append(f"{format_money(gold)} (have "
                     f"{format_money(int(getattr(manager, 'gold', 0)))})")
    return "   ".join(parts) if parts else "No construction cost"


def _patch_barracks(BarracksMenu):
    if getattr(BarracksMenu, "_tiered_stations_installed", False):
        return

    original_init = BarracksMenu.__init__
    original_event = BarracksMenu.handle_event
    original_update = BarracksMenu.update
    original_draw = BarracksMenu.draw

    def __init__(self, manager):
        original_init(self, manager)
        _root_state(manager)
        process_station_jobs(manager)

        # The first farming pass exposed Kitchen and Herbalist as separate
        # buttons. Keep their logic installed for save compatibility, but route
        # all new interaction through one coherent station screen.
        for name in ("btn_kitchen", "btn_alchemy"):
            button = getattr(self, name, None)
            if button and hasattr(button, "rect"):
                button.rect.topleft = (-3000, -3000)
        self.show_kitchen = False
        self.show_alchemy = False

        cx = SCREEN_WIDTH // 2
        self.btn_stations = UIButton(cx - 150, SCREEN_HEIGHT - 195, 300, 55,
                                     "CRAFTING STATIONS", None, (92, 78, 56))
        self.show_station_hub = False
        self.station_detail = None
        self.station_card_rects = []
        self.station_recipe_rects = []
        self.station_upgrade_rect = pygame.Rect(0, 0, 0, 0)
        self.station_back_rect = pygame.Rect(0, 0, 0, 0)
        self.station_scroll = 0
        self.station_feedback = ""
        self.station_feedback_timer = 0

    def handle_event(self, event):
        if self.show_station_hub:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.station_detail:
                    self.station_detail = None
                    self.station_scroll = 0
                else:
                    self.show_station_hub = False
                _safe_sound("click")
                return

            if event.type == pygame.MOUSEWHEEL and self.station_detail:
                recipes = _recipe_catalog(self.station_detail)
                visible_h = SCREEN_HEIGHT - 355
                max_scroll = max(0, len(recipes) * 108 - visible_h)
                self.station_scroll = max(
                    0, min(max_scroll, self.station_scroll - event.y * 35))
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.station_detail:
                    if self.station_back_rect.collidepoint(event.pos):
                        self.station_detail = None
                        self.station_scroll = 0
                        _safe_sound("click")
                        return
                    if self.station_upgrade_rect.collidepoint(event.pos):
                        ok, message = begin_station_upgrade(
                            self.manager, self.station_detail)
                        self.station_feedback = message
                        self.station_feedback_timer = 180
                        _safe_sound("click" if ok else "error")
                        return
                    for rect, recipe_name in self.station_recipe_rects:
                        if rect.collidepoint(event.pos):
                            ok, message = begin_station_recipe(
                                self.manager, self.station_detail, recipe_name)
                            self.station_feedback = message
                            self.station_feedback_timer = 180
                            _safe_sound("click" if ok else "error")
                            return
                else:
                    for rect, station_id in self.station_card_rects:
                        if rect.collidepoint(event.pos):
                            self.station_detail = station_id
                            self.station_scroll = 0
                            _safe_sound("click")
                            return
            return

        if self.btn_stations.is_clicked(event):
            self.show_station_hub = True
            self.station_detail = None
            process_station_jobs(self.manager)
            _safe_sound("click")
            return
        return original_event(self, event)

    def update(self):
        result = original_update(self)
        messages = process_station_jobs(self.manager)
        if messages:
            self.station_feedback = messages[-1]
            self.station_feedback_timer = 240
            _safe_sound("recruit")
        if self.station_feedback_timer > 0:
            self.station_feedback_timer -= 1
        return result

    def draw(self, screen):
        result = original_draw(self, screen)
        if not self.show_station_hub:
            self.btn_stations.draw(screen)
            return result
        if self.station_detail:
            _draw_station_detail(self, screen, self.station_detail)
        else:
            _draw_station_hub(self, screen)
        return result

    def consumes_escape(self):
        # Crafting-hub auki -> ESC sulkee paneelin (ei pausea)
        return bool(getattr(self, "show_station_hub", False))

    BarracksMenu.__init__ = __init__
    BarracksMenu.handle_event = handle_event
    BarracksMenu.update = update
    BarracksMenu.draw = draw
    BarracksMenu.consumes_escape = consumes_escape
    BarracksMenu._tiered_stations_installed = True


def _draw_overlay_panel(screen, rect: pygame.Rect, title: str):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 226))
    screen.blit(overlay, (0, 0))
    pygame.draw.rect(screen, (36, 34, 31), rect, border_radius=14)
    pygame.draw.rect(screen, (128, 108, 75), rect, 3, border_radius=14)
    # font_header (30px) mahtuu paneelin yläpalkkiin - font_title (60px)
    # valui alaotsikoiden päälle
    draw_text(title, font_header, GOLD_COLOR, screen, rect.x + 35, rect.y + 24)


def _draw_job_bar(screen, rect: pygame.Rect, node: dict):
    progress = job_progress(node)
    pygame.draw.rect(screen, (28, 27, 25), rect, border_radius=4)
    fill = rect.copy()
    fill.w = int(rect.w * progress)
    if fill.w > 0:
        pygame.draw.rect(screen, (95, 165, 95), fill, border_radius=4)
    pygame.draw.rect(screen, (105, 100, 90), rect, 1, border_radius=4)


def _draw_station_hub(menu, screen):
    panel = pygame.Rect(145, 65, SCREEN_WIDTH - 290, SCREEN_HEIGHT - 130)
    _draw_overlay_panel(screen, panel, "TEAM QUARTERS CRAFTING STATIONS")
    draw_text("Build stations, upgrade them over time and run one job at each station in parallel.",
              font_small, GRAY, screen, panel.x + 35, panel.y + 68)
    draw_text("Heavy metal production remains at the town Smeltery and Scrap Iron Smithy.",
              font_small, (185, 175, 150), screen, panel.x + 35, panel.y + 92)
    draw_text("ESC closes", font_small, GRAY, screen, panel.right - 115, panel.y + 30)

    menu.station_card_rects = []
    mouse = pygame.mouse.get_pos()
    card_w = (panel.w - 95) // 2
    card_h = 330
    start_y = panel.y + 130
    for index, (station_id, definition) in enumerate(STATION_DEFINITIONS.items()):
        col = index % 2
        row = index // 2
        rect = pygame.Rect(panel.x + 30 + col * (card_w + 35),
                           start_y + row * (card_h + 30), card_w, card_h)
        node = station_node(menu.manager, station_id)
        level = station_level(menu.manager, station_id)
        hover = rect.collidepoint(mouse)
        bg = (57, 53, 47) if hover else (47, 44, 40)
        pygame.draw.rect(screen, bg, rect, border_radius=10)
        pygame.draw.rect(screen, GOLD_COLOR if hover else (98, 88, 70),
                         rect, 2, border_radius=10)
        draw_text(definition["title"], font_header, WHITE,
                  screen, rect.x + 20, rect.y + 18)
        if level > 0:
            tier_name = definition["tiers"][level]["name"]
            draw_text(f"Tier {level}: {tier_name}", font_main, GOLD_COLOR,
                      screen, rect.x + 20, rect.y + 60)
        else:
            draw_text("NOT BUILT", font_main, RED,
                      screen, rect.x + 20, rect.y + 60)
        draw_text(definition["description"], font_small, (205, 198, 180),
                  screen, rect.x + 20, rect.y + 100)

        job = node.get("job")
        if job:
            label = (job.get("display_name") if job.get("kind") == "upgrade"
                     else job.get("recipe", "Crafting"))
            draw_text(f"WORKING: {label}", font_main, GREEN,
                      screen, rect.x + 20, rect.y + 175)
            _draw_job_bar(screen, pygame.Rect(rect.x + 20, rect.y + 215,
                                              rect.w - 40, 16), node)
            draw_text(remaining_text(node), font_small, WHITE,
                      screen, rect.x + 20, rect.y + 240)
        else:
            draw_text("IDLE", font_main, GRAY,
                      screen, rect.x + 20, rect.y + 185)

        draw_text("OPEN STATION >", font_main, GOLD_COLOR,
                  screen, rect.right - 180, rect.bottom - 48)
        menu.station_card_rects.append((rect, station_id))

    root = _root_state(menu.manager)
    draw_text(f"Crafting experience: {root.get('crafting_xp', 0)}",
              font_small, GRAY, screen, panel.x + 35, panel.bottom - 28)
    if menu.station_feedback_timer > 0 and menu.station_feedback:
        draw_text(menu.station_feedback, font_main, GREEN,
                  screen, panel.centerx - 260, panel.bottom - 34)


def _draw_station_detail(menu, screen, station_id: str):
    definition = STATION_DEFINITIONS[station_id]
    panel = pygame.Rect(125, 55, SCREEN_WIDTH - 250, SCREEN_HEIGHT - 110)
    _draw_overlay_panel(screen, panel, definition["title"].upper())
    node = station_node(menu.manager, station_id)
    level = station_level(menu.manager, station_id)

    menu.station_back_rect = pygame.Rect(panel.right - 150, panel.y + 20, 115, 42)
    pygame.draw.rect(screen, (70, 66, 60), menu.station_back_rect, border_radius=6)
    draw_text("< BACK", font_main, WHITE, screen,
              menu.station_back_rect.x + 18, menu.station_back_rect.y + 10)

    if level > 0:
        tier_name = definition["tiers"][level]["name"]
        draw_text(f"Tier {level}: {tier_name}", font_main, GOLD_COLOR,
                  screen, panel.x + 35, panel.y + 68)
    else:
        draw_text("Not built", font_main, RED,
                  screen, panel.x + 35, panel.y + 68)
    draw_text(definition["description"], font_small, GRAY,
              screen, panel.x + 35, panel.y + 98)

    upgrade_panel = pygame.Rect(panel.x + 30, panel.y + 135, panel.w - 60, 120)
    pygame.draw.rect(screen, (46, 43, 39), upgrade_panel, border_radius=8)
    pygame.draw.rect(screen, (90, 80, 65), upgrade_panel, 2, border_radius=8)
    menu.station_upgrade_rect = pygame.Rect(upgrade_panel.right - 250,
                                            upgrade_panel.y + 30, 220, 58)
    job = node.get("job")
    if job:
        label = (job.get("display_name") if job.get("kind") == "upgrade"
                 else job.get("recipe", "Current job"))
        draw_text(f"CURRENT JOB: {label}", font_main, GREEN,
                  screen, upgrade_panel.x + 18, upgrade_panel.y + 18)
        _draw_job_bar(screen, pygame.Rect(upgrade_panel.x + 18,
                                          upgrade_panel.y + 58,
                                          upgrade_panel.w - 300, 16), node)
        draw_text(remaining_text(node), font_small, WHITE,
                  screen, upgrade_panel.x + 18, upgrade_panel.y + 82)
        pygame.draw.rect(screen, (65, 65, 65), menu.station_upgrade_rect,
                         border_radius=7)
        draw_text("STATION BUSY", font_main, GRAY,
                  screen, menu.station_upgrade_rect.x + 35,
                  menu.station_upgrade_rect.y + 17)
    elif level < MAX_STATION_TIER:
        target = level + 1
        tier_data = definition["tiers"][target]
        action = "BUILD" if level == 0 else "UPGRADE"
        draw_text(f"{action}: {tier_data['name']}", font_main, WHITE,
                  screen, upgrade_panel.x + 18, upgrade_panel.y + 16)
        draw_text(_cost_text(menu.manager, tier_data["materials"],
                             int(tier_data["gold"])),
                  font_small, GRAY, screen, upgrade_panel.x + 18,
                  upgrade_panel.y + 50)
        real_seconds = int(float(tier_data["minutes"])
                           * REAL_SECONDS_PER_GAME_MINUTE)
        draw_text(f"Construction time: {real_seconds // 60}m {real_seconds % 60}s",
                  font_small, (190, 180, 150), screen,
                  upgrade_panel.x + 18, upgrade_panel.y + 78)
        affordable = (int(getattr(menu.manager, "gold", 0)) >= int(tier_data["gold"])
                      and can_pay_materials(menu.manager,
                                            tier_data["materials"]))
        pygame.draw.rect(screen, (67, 118, 70) if affordable else (75, 65, 62),
                         menu.station_upgrade_rect, border_radius=7)
        draw_text(action, font_main, WHITE if affordable else GRAY,
                  screen, menu.station_upgrade_rect.x + 72,
                  menu.station_upgrade_rect.y + 17)
    else:
        draw_text("MAXIMUM TIER REACHED", font_main, GOLD_COLOR,
                  screen, upgrade_panel.x + 18, upgrade_panel.y + 42)
        menu.station_upgrade_rect = pygame.Rect(0, 0, 0, 0)

    recipes = _recipe_catalog(station_id)
    list_rect = pygame.Rect(panel.x + 30, panel.y + 280,
                            panel.w - 60, panel.h - 335)
    pygame.draw.rect(screen, (31, 30, 29), list_rect, border_radius=8)
    draw_text("RECIPES / SERVICES", font_main, GOLD_COLOR,
              screen, list_rect.x + 15, list_rect.y + 12)
    draw_text("Mouse wheel scrolls", font_small, GRAY,
              screen, list_rect.right - 155, list_rect.y + 15)

    menu.station_recipe_rects = []
    mouse = pygame.mouse.get_pos()
    previous_clip = screen.get_clip()
    clip = pygame.Rect(list_rect.x + 10, list_rect.y + 45,
                       list_rect.w - 20, list_rect.h - 55)
    screen.set_clip(clip)
    y = list_rect.y + 50 - menu.station_scroll
    for recipe_name, recipe in recipes.items():
        rect = pygame.Rect(list_rect.x + 15, y, list_rect.w - 30, 98)
        required = int(recipe.get("tier", 1))
        tier_ok = level >= required
        has_items = can_pay_materials(menu.manager,
                                      dict(recipe.get("ingredients", {})))
        can_start = tier_ok and has_items and not job and level > 0
        hover = rect.collidepoint(mouse)
        bg = (53, 70, 53) if hover and can_start else (44, 43, 41)
        if not tier_ok:
            bg = (48, 38, 38)
        elif not has_items:
            bg = (52, 43, 39)
        pygame.draw.rect(screen, bg, rect, border_radius=7)
        pygame.draw.rect(screen, (92, 123, 92) if can_start else (82, 71, 65),
                         rect, 2, border_radius=7)
        draw_text(recipe_name, font_main, WHITE if tier_ok else GRAY,
                  screen, rect.x + 14, rect.y + 10)
        draw_text(f"Tier {required}", font_small,
                  GOLD_COLOR if tier_ok else RED,
                  screen, rect.right - 75, rect.y + 13)
        draw_text(str(recipe.get("description", "")), font_small,
                  (204, 198, 185), screen, rect.x + 14, rect.y + 38)
        ingredients = "   ".join(
            f"{name} {available_material(menu.manager, name)}/{amount}"
            for name, amount in recipe.get("ingredients", {}).items())
        draw_text(ingredients, font_small, GREEN if has_items else RED,
                  screen, rect.x + 14, rect.y + 65)
        if can_start:
            draw_text("CLICK TO START", font_small, GOLD_COLOR,
                      screen, rect.right - 140, rect.y + 65)
        menu.station_recipe_rects.append((rect, recipe_name))
        y += 108
    screen.set_clip(previous_clip)

    if menu.station_feedback_timer > 0 and menu.station_feedback:
        draw_text(menu.station_feedback, font_main, GREEN,
                  screen, panel.centerx - 250, panel.bottom - 32)


def install_farming_stations():
    global _INSTALLED
    if _INSTALLED:
        return

    from citys.mucford.farming_expansion import MEAL_RECIPES
    from menus.barracks_menu import BarracksMenu

    for name, recipe in ADDITIONAL_MEALS.items():
        MEAL_RECIPES.setdefault(name, dict(recipe))

    _patch_barracks(BarracksMenu)
    _INSTALLED = True
