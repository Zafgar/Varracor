"""Playable farms and wet fields immediately outside Muckford.

The Low Fields are the first complete Tier 0 production area after the city.
They deliberately reuse the existing farming, monster, water and save systems
while keeping all local art replaceable: fields, fences, carts, bridges,
resources and project markers are drawn with pygame primitives.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Sequence, Tuple

import pygame

from assets.tiles.prop import Prop
from menus.gameplay_screen import GameplayScreen
from settings import ENEMY_TEAM, GOLD_COLOR, GRAY, GREEN, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from systems.procedural_water import ProceduralWaterBody
from ui_kit import draw_text, font_main, font_small
from units.rat import GiantRat
from units.tier0_monsters import MudMite, ReedSkitter
from units.villager import Villager


MAP_SEED = 70113
FIELD_WIDTH = 3200
FIELD_HEIGHT = 2200

PROJECT_COSTS = {
    "irrigation": {"Clay": 5, "River Reed": 4},
    "grain_cart": {"Softwood": 4, "Clay": 2},
    "footbridge": {"Softwood": 6, "River Reed": 5, "Clay": 2},
}


def _current_day_key(manager) -> str:
    clock = getattr(manager, "world_clock", None)
    if clock is None:
        return "timeless"
    return f"{int(getattr(clock, 'year', 0))}:{int(getattr(clock, 'day', 1))}"


def low_fields_state(manager) -> dict:
    global_data = manager.npc_state.setdefault("global", {})
    state = global_data.setdefault("muckford_low_fields", {})
    state.setdefault("visits", 0)
    state.setdefault("quest_stage", 0)
    state.setdefault("projects", [])
    state.setdefault("sealed_burrows", [])
    state.setdefault("grain_raiders_defeated", 0)
    state.setdefault("grain_raid_resolved", False)
    state.setdefault("supply_claimed", False)
    state.setdefault("harvested_nodes", [])
    state.setdefault("resource_day", _current_day_key(manager))
    state.setdefault("completed", False)

    day_key = _current_day_key(manager)
    if state.get("resource_day") != day_key:
        state["resource_day"] = day_key
        state["harvested_nodes"] = []
    return state


def _cost_text(cost: Dict[str, int]) -> str:
    return ", ".join(f"{amount} {name}" for name, amount in cost.items())


def _has_cost(manager, cost: Dict[str, int]) -> bool:
    return all(int(manager.inventory.get(name, 0)) >= amount for name, amount in cost.items())


def _consume_cost(manager, cost: Dict[str, int]) -> bool:
    if not _has_cost(manager, cost):
        return False
    for name, amount in cost.items():
        manager.inventory[name] = int(manager.inventory.get(name, 0)) - amount
        if manager.inventory[name] <= 0:
            manager.inventory.pop(name, None)
    return True


def _safe_sound(name: str) -> None:
    try:
        sound_system.play_sound(name)
    except Exception:
        pass


class RectObstacle:
    def __init__(self, rect: pygame.Rect):
        self.rect = pygame.Rect(rect)
        self.blocks_projectiles = True


class FieldResourceNode(Prop):
    """Daily renewable, deterministic resource node."""

    def __init__(
        self,
        node_id: str,
        x: int,
        y: int,
        resource_name: str,
        style: str,
        amount: Tuple[int, int],
        state: dict,
    ):
        super().__init__(x, y, 54, 54, color=(0, 0, 0))
        self.node_id = str(node_id)
        self.resource_name = str(resource_name)
        self.style = str(style)
        self.amount = (int(amount[0]), int(amount[1]))
        self.state = state
        self.type = "resource"
        self.has_shadow = style not in {"reed", "produce"}
        self.blocks_projectiles = False
        self.interaction_label = f"Gather {self.resource_name}"
        self._redraw()

    @property
    def harvested(self) -> bool:
        return self.node_id in self.state.get("harvested_nodes", ())

    def _redraw(self) -> None:
        image = pygame.Surface((54, 54), pygame.SRCALPHA)
        if self.harvested:
            pygame.draw.ellipse(image, (67, 55, 39, 90), (7, 42, 40, 7))
            self.image = image
            self.image_pos = self.rect.topleft
            return

        if self.style == "reed":
            for index, x in enumerate((8, 15, 22, 30, 38, 45)):
                height = 25 + (index % 3) * 6
                pygame.draw.line(image, (68, 132, 74), (x, 50), (x + index % 2, 50 - height), 3)
                pygame.draw.line(image, (174, 139, 67), (x, 50 - height), (x + 4, 45 - height), 3)
        elif self.style == "clay":
            pygame.draw.ellipse(image, (105, 72, 51), (4, 27, 46, 22))
            pygame.draw.ellipse(image, (151, 99, 68), (11, 20, 30, 19))
            pygame.draw.arc(image, (73, 51, 39), (13, 25, 25, 14), 0.2, 2.7, 2)
        elif self.style == "wood":
            pygame.draw.line(image, (102, 72, 44), (6, 42), (47, 18), 10)
            pygame.draw.line(image, (149, 110, 66), (9, 38), (45, 19), 3)
            pygame.draw.line(image, (88, 62, 39), (27, 29), (19, 12), 5)
        else:
            crop_color = {
                "Carrot": (224, 111, 35),
                "Potato": (171, 128, 70),
                "Onion": (220, 211, 169),
            }.get(self.resource_name, (174, 147, 76))
            pygame.draw.ellipse(image, (91, 65, 39), (5, 34, 44, 15))
            for index, x in enumerate((14, 26, 38)):
                pygame.draw.circle(image, crop_color, (x, 35 + index % 2 * 3), 7)
                pygame.draw.line(image, (64, 137, 69), (x, 30), (x - 3, 18), 3)
                pygame.draw.line(image, (64, 137, 69), (x, 25), (x + 5, 17), 2)
        self.image = image
        self.image_pos = self.rect.topleft

    def harvest(self, manager, rng: random.Random) -> Optional[str]:
        if self.harvested:
            return None
        amount = rng.randint(*self.amount)
        manager.inventory[self.resource_name] = int(manager.inventory.get(self.resource_name, 0)) + amount
        harvested = self.state.setdefault("harvested_nodes", [])
        if self.node_id not in harvested:
            harvested.append(self.node_id)
        self._redraw()
        _safe_sound("grass_pickup")
        return f"+{amount} {self.resource_name}"


class FieldFence(Prop):
    def __init__(self, rect: pygame.Rect, horizontal: bool = True):
        super().__init__(rect.x, rect.y, rect.w, rect.h, color=(0, 0, 0))
        self.rect = pygame.Rect(rect)
        self.image_pos = self.rect.topleft
        self.has_shadow = True
        self.blocks_projectiles = True
        image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        if horizontal:
            y = self.rect.h // 2
            pygame.draw.line(image, (91, 65, 39), (0, y - 7), (self.rect.w, y - 7), 5)
            pygame.draw.line(image, (126, 88, 50), (0, y + 7), (self.rect.w, y + 7), 5)
            for x in range(8, self.rect.w, 44):
                pygame.draw.line(image, (74, 52, 34), (x, 0), (x, self.rect.h), 7)
        else:
            x = self.rect.w // 2
            pygame.draw.line(image, (91, 65, 39), (x - 7, 0), (x - 7, self.rect.h), 5)
            pygame.draw.line(image, (126, 88, 50), (x + 7, 0), (x + 7, self.rect.h), 5)
            for y in range(8, self.rect.h, 44):
                pygame.draw.line(image, (74, 52, 34), (0, y), (self.rect.w, y), 7)
        self.image = image


class FieldCart(Prop):
    def __init__(self, x: int, y: int, repaired: bool):
        super().__init__(x, y, 120, 82, color=(0, 0, 0))
        self.rect = pygame.Rect(x + 8, y + 38, 104, 38)
        self.image_pos = (x, y)
        self.has_shadow = True
        self.blocks_projectiles = True
        image = pygame.Surface((120, 82), pygame.SRCALPHA)
        pygame.draw.circle(image, (61, 47, 35), (25, 67), 14)
        pygame.draw.circle(image, (61, 47, 35), (94, 67), 14)
        pygame.draw.circle(image, (143, 105, 61), (25, 67), 7)
        pygame.draw.circle(image, (143, 105, 61), (94, 67), 7)
        pygame.draw.polygon(image, (105, 73, 43), [(12, 30), (105, 30), (97, 65), (20, 65)])
        pygame.draw.line(image, (161, 117, 68), (17, 34), (101, 34), 3)
        if repaired:
            for x2 in (28, 47, 66, 85):
                pygame.draw.ellipse(image, (185, 155, 77), (x2, 17, 20, 26))
        else:
            pygame.draw.line(image, (62, 46, 34), (35, 31), (63, 60), 5)
            pygame.draw.line(image, (62, 46, 34), (73, 31), (57, 61), 5)
        self.image = image


class FieldBridge(Prop):
    def __init__(self, rect: pygame.Rect, sturdy: bool):
        super().__init__(rect.x, rect.y, rect.w, rect.h, color=(0, 0, 0))
        self.rect = pygame.Rect(rect)
        self.image_pos = self.rect.topleft
        self.has_shadow = False
        self.blocks_projectiles = False
        image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        plank = (135, 97, 55) if sturdy else (103, 76, 49)
        for x in range(4, self.rect.w - 4, 23):
            wobble = (x // 23) % 3 - 1
            pygame.draw.rect(image, plank, (x, 8 + wobble * 2, 19, self.rect.h - 16), border_radius=2)
            pygame.draw.line(image, (177, 132, 78), (x + 3, 13), (x + 15, 13), 2)
        pygame.draw.line(image, (70, 52, 37), (3, 8), (self.rect.w - 3, 8), 4)
        pygame.draw.line(image, (70, 52, 37), (3, self.rect.h - 8), (self.rect.w - 3, self.rect.h - 8), 4)
        self.image = image


class FieldProjectMarker(Prop):
    def __init__(self, project_id: str, x: int, y: int, label: str, completed: bool):
        super().__init__(x, y, 86, 94, color=(0, 0, 0))
        self.project_id = project_id
        self.label = label
        self.completed = bool(completed)
        self.rect = pygame.Rect(x + 15, y + 42, 56, 46)
        self.image_pos = (x, y)
        self.has_shadow = True
        self.blocks_projectiles = False
        self._redraw()

    def _redraw(self):
        image = pygame.Surface((86, 94), pygame.SRCALPHA)
        pygame.draw.line(image, (80, 58, 38), (43, 90), (43, 18), 7)
        pygame.draw.rect(image, (139, 103, 62), (8, 8, 70, 45), border_radius=4)
        pygame.draw.rect(image, (190, 155, 95), (8, 8, 70, 45), 3, border_radius=4)
        color = (78, 164, 91) if self.completed else (210, 170, 76)
        pygame.draw.circle(image, color, (43, 30), 11, 3)
        if self.completed:
            pygame.draw.line(image, color, (36, 30), (41, 36), 3)
            pygame.draw.line(image, color, (41, 36), (52, 22), 3)
        else:
            pygame.draw.line(image, color, (43, 18), (43, 35), 3)
            pygame.draw.circle(image, color, (43, 43), 2)
        self.image = image


class BurrowMound(Prop):
    def __init__(self, burrow_id: str, x: int, y: int, state: dict):
        super().__init__(x, y, 92, 62, color=(0, 0, 0))
        self.burrow_id = burrow_id
        self.state = state
        self.rect = pygame.Rect(x + 8, y + 24, 76, 32)
        self.image_pos = (x, y)
        self.has_shadow = False
        self.blocks_projectiles = False
        self._redraw()

    @property
    def sealed(self) -> bool:
        return self.burrow_id in self.state.get("sealed_burrows", ())

    def _redraw(self):
        image = pygame.Surface((92, 62), pygame.SRCALPHA)
        pygame.draw.ellipse(image, (83, 59, 40), (5, 25, 82, 32))
        pygame.draw.ellipse(image, (117, 83, 52), (15, 18, 62, 30))
        if self.sealed:
            pygame.draw.line(image, (154, 116, 71), (25, 25), (67, 48), 8)
            pygame.draw.line(image, (154, 116, 71), (67, 25), (25, 48), 8)
            pygame.draw.circle(image, (77, 122, 69), (46, 36), 7, 2)
        else:
            pygame.draw.ellipse(image, (30, 23, 20), (27, 27, 40, 23))
            pygame.draw.circle(image, (142, 101, 61), (18, 45), 4)
            pygame.draw.circle(image, (142, 101, 61), (73, 43), 3)
        self.image = image

    def seal(self, manager) -> bool:
        if self.sealed:
            return False
        if int(manager.inventory.get("Clay", 0)) < 1:
            return False
        manager.inventory["Clay"] -= 1
        if manager.inventory["Clay"] <= 0:
            manager.inventory.pop("Clay", None)
        self.state.setdefault("sealed_burrows", []).append(self.burrow_id)
        self._redraw()
        return True


class LowFieldsArena:
    def __init__(self, manager):
        self.width = FIELD_WIDTH
        self.height = FIELD_HEIGHT
        self.manager = manager
        self.rng = random.Random(MAP_SEED)
        self.props: List[object] = []
        self.floor_props: List[object] = []
        self.land_obstacles: List[object] = []
        self.water_obstacles: List[object] = []
        self.obstacles: List[object] = []
        self.resources: List[FieldResourceNode] = []
        self.project_props: List[object] = []
        self.field_rects = (
            pygame.Rect(420, 360, 860, 590),
            pygame.Rect(1880, 330, 870, 650),
            pygame.Rect(390, 1250, 810, 540),
            pygame.Rect(1940, 1260, 760, 520),
        )
        self.path_rects = (
            pygame.Rect(340, 0, 250, self.height),
            pygame.Rect(340, 910, 2470, 210),
        )
        self.irrigation = ProceduralWaterBody(
            pygame.Rect(1465, 220, 285, 1750),
            seed=MAP_SEED + 2,
            name="Low Fields Irrigation",
            flow=(0.18, 0.95),
            shore_variance=18,
            deep_margin=24,
            shallow_color=(83, 113, 95),
            mid_color=(55, 86, 83),
            deep_color=(31, 60, 68),
        )
        self.waters = [self.irrigation]
        self.motes: List[dict] = []
        self._build_static_landscape()
        self.refresh_persistent_props(manager)

    def _add(self, prop, blocking=False):
        self.props.append(prop)
        if blocking:
            self.land_obstacles.append(prop)

    def _build_static_landscape(self):
        # Fence segments leave roads and field gates open.
        fence_specs = [
            (pygame.Rect(410, 340, 880, 28), True),
            (pygame.Rect(410, 940, 880, 28), True),
            (pygame.Rect(390, 1230, 830, 28), True),
            (pygame.Rect(390, 1780, 830, 28), True),
            (pygame.Rect(1870, 310, 900, 28), True),
            (pygame.Rect(1870, 970, 900, 28), True),
            (pygame.Rect(1930, 1240, 790, 28), True),
            (pygame.Rect(1930, 1780, 790, 28), True),
        ]
        for rect, horizontal in fence_specs:
            self._add(FieldFence(rect, horizontal), blocking=True)

        state = low_fields_state(self.manager)
        resource_specs = []
        for index in range(6):
            resource_specs.append((f"carrot_{index}", 540 + index * 105, 560 + index % 2 * 90, "Carrot", "produce", (1, 2)))
        for index in range(5):
            resource_specs.append((f"potato_{index}", 2020 + index * 125, 520 + index % 2 * 105, "Potato", "produce", (1, 3)))
        for index in range(5):
            resource_specs.append((f"onion_{index}", 520 + index * 130, 1420 + index % 2 * 100, "Onion", "produce", (1, 2)))
        for index in range(10):
            y = 330 + index * 150
            left, right = self.irrigation.bounds_at(y)
            x = int(left - 52) if index % 2 == 0 else int(right + 12)
            resource_specs.append((f"reed_{index}", x, y, "River Reed", "reed", (1, 2)))
        for index in range(6):
            y = 430 + index * 245
            left, right = self.irrigation.bounds_at(y)
            x = int(left - 76) if index % 2 == 0 else int(right + 30)
            resource_specs.append((f"clay_{index}", x, y, "Clay", "clay", (1, 2)))
        for index in range(8):
            resource_specs.append((f"wood_{index}", 2780 + index % 2 * 95, 390 + index * 190, "Softwood", "wood", (1, 2)))

        for spec in resource_specs:
            node = FieldResourceNode(*spec, state)
            self.resources.append(node)
            self._add(node)

    def refresh_persistent_props(self, manager):
        for prop in list(self.project_props):
            if prop in self.props:
                self.props.remove(prop)
            if prop in self.land_obstacles:
                self.land_obstacles.remove(prop)
        self.project_props = []

        state = low_fields_state(manager)
        projects = set(state.get("projects", ()))

        cart = FieldCart(920, 1015, "grain_cart" in projects)
        self.project_props.append(cart)
        self._add(cart, blocking=True)

        irrigation_marker = FieldProjectMarker(
            "irrigation", 1330, 520, "Repair irrigation", "irrigation" in projects
        )
        cart_marker = FieldProjectMarker(
            "grain_cart", 980, 930, "Repair grain cart", "grain_cart" in projects
        )
        bridge_marker = FieldProjectMarker(
            "footbridge", 1390, 1430, "Build field bridge", "footbridge" in projects
        )
        for marker in (irrigation_marker, cart_marker, bridge_marker):
            self.project_props.append(marker)
            self._add(marker)

        self.irrigation_marker = irrigation_marker
        self.cart_marker = cart_marker
        self.bridge_marker = bridge_marker

        self.burrows = [
            BurrowMound("burrow_1", 2360, 1390, state),
            BurrowMound("burrow_2", 2640, 1530, state),
            BurrowMound("burrow_3", 2240, 1710, state),
        ]
        for burrow in self.burrows:
            self.project_props.append(burrow)
            self._add(burrow)

        upper = self.irrigation.span_rect(710, height=86, padding=25)
        upper_bridge = FieldBridge(upper, sturdy=False)
        self.project_props.append(upper_bridge)
        self._add(upper_bridge)
        crossings = [(650, 780)]

        if "footbridge" in projects:
            lower = self.irrigation.span_rect(1500, height=92, padding=28)
            lower_bridge = FieldBridge(lower, sturdy=True)
            self.project_props.append(lower_bridge)
            self._add(lower_bridge)
            crossings.append((1435, 1570))

        self.water_obstacles = self.irrigation.make_collision_barriers(crossings)
        self.obstacles = list(self.land_obstacles) + list(self.water_obstacles)

    def random_spawn_point(self, zone="any", margin=130) -> Tuple[int, int]:
        zones = {
            "west": pygame.Rect(260, 260, 980, 1650),
            "east": pygame.Rect(1830, 250, 1120, 1650),
            "south_east": pygame.Rect(2050, 1250, 850, 650),
            "any": pygame.Rect(margin, margin, self.width - margin * 2, self.height - margin * 2),
        }
        area = zones.get(zone, zones["any"])
        for _ in range(400):
            point = (self.rng.randint(area.left, area.right), self.rng.randint(area.top, area.bottom))
            if self.irrigation.contains_point(point, inset=-20):
                continue
            if point[1] < 250 and point[0] < 900:
                continue
            if any(obstacle.rect.inflate(24, 24).collidepoint(point) for obstacle in self.land_obstacles):
                continue
            return point
        return (650, 700)

    def update(self, manager):
        if random.random() < 0.025:
            local_y = random.randint(20, self.irrigation.rect.height - 20)
            left, right = self.irrigation._local_bounds_at(local_y)
            x = random.randint(int(left + 15), max(int(left + 16), int(right - 15)))
            self.irrigation.add_ripple((self.irrigation.rect.left + x, self.irrigation.rect.top + local_y))
        if random.random() < 0.045:
            self.motes.append({
                "x": random.randint(200, self.width - 200),
                "y": random.randint(250, self.height - 150),
                "life": random.randint(80, 150),
                "kind": random.choice(("seed", "fly", "mist")),
            })
        for mote in self.motes:
            mote["life"] -= 1
            mote["x"] += 0.18 if mote["kind"] != "fly" else math.sin(mote["life"] * 0.18) * 0.7
            mote["y"] -= 0.08 if mote["kind"] == "seed" else 0
        self.motes = [mote for mote in self.motes if mote["life"] > 0]

    def draw_background(self, screen, offset=(0, 0)):
        screen.fill((70, 78, 49))
        ox, oy = int(offset[0]), int(offset[1])
        visible = pygame.Rect(ox, oy, screen.get_width(), screen.get_height())

        # Subtle alternating ground strips avoid a flat single-colour map.
        start_y = (visible.top // 96) * 96
        for world_y in range(start_y, visible.bottom + 96, 96):
            shade = (76, 83, 52) if (world_y // 96) % 2 == 0 else (66, 75, 47)
            pygame.draw.rect(screen, shade, (0, world_y - oy, screen.get_width(), 96))

        for rect in self.path_rects:
            draw_rect = rect.move(-ox, -oy)
            pygame.draw.rect(screen, (105, 86, 57), draw_rect, border_radius=18)
            pygame.draw.rect(screen, (126, 102, 66), draw_rect, 3, border_radius=18)
            for x in range(draw_rect.left + 28, draw_rect.right, 76):
                if -20 <= x <= screen.get_width() + 20:
                    pygame.draw.ellipse(screen, (86, 70, 49), (x, draw_rect.centery - 8, 22, 9), 2)

        crop_palettes = (
            ((94, 78, 48), (68, 113, 57)),
            ((87, 72, 45), (80, 125, 61)),
            ((96, 76, 48), (92, 132, 66)),
            ((82, 70, 47), (75, 112, 55)),
        )
        for field_index, rect in enumerate(self.field_rects):
            draw_rect = rect.move(-ox, -oy)
            if not draw_rect.colliderect(screen.get_rect()):
                continue
            soil, crop = crop_palettes[field_index]
            pygame.draw.rect(screen, soil, draw_rect, border_radius=9)
            pygame.draw.rect(screen, (139, 111, 68), draw_rect, 3, border_radius=9)
            start = max(rect.top + 30, visible.top - 40)
            for world_y in range(start, min(rect.bottom, visible.bottom + 40), 38):
                y = world_y - oy
                pygame.draw.line(screen, (59, 47, 34), (draw_rect.left + 14, y + 7), (draw_rect.right - 14, y + 7), 4)
                for world_x in range(rect.left + 26, rect.right - 14, 46):
                    x = world_x - ox
                    if -20 <= x <= screen.get_width() + 20:
                        pygame.draw.line(screen, crop, (x, y + 4), (x, y - 8), 2)
                        pygame.draw.circle(screen, crop, (x - 3, y - 7), 3)
                        pygame.draw.circle(screen, crop, (x + 3, y - 5), 3)

        self.irrigation.draw(screen, offset)

    def draw_foreground(self, screen, offset=(0, 0)):
        ox, oy = int(offset[0]), int(offset[1])
        for mote in self.motes:
            x = int(mote["x"] - ox)
            y = int(mote["y"] - oy)
            if not (-10 < x < screen.get_width() + 10 and -10 < y < screen.get_height() + 10):
                continue
            alpha = min(150, mote["life"] * 2)
            if mote["kind"] == "seed":
                pygame.draw.circle(screen, (218, 207, 151, alpha), (x, y), 2)
            elif mote["kind"] == "fly":
                pygame.draw.circle(screen, (32, 31, 25), (x, y), 2)
            else:
                mist = pygame.Surface((30, 8), pygame.SRCALPHA)
                pygame.draw.ellipse(mist, (190, 196, 171, min(40, alpha)), mist.get_rect())
                screen.blit(mist, (x - 15, y - 4))


class LowFieldsMenu(GameplayScreen):
    def __init__(self, manager):
        super().__init__(manager)
        self.arena = LowFieldsArena(manager)
        self.monsters = pygame.sprite.Group()
        self.npcs: List[object] = []
        self.feedback = ""
        self.feedback_timer = 0
        self.warning = ""
        self.warning_timer = 0
        self.dialogue_pages: List[str] = []
        self.dialogue_index = 0
        self.dialogue_name = ""
        self.dialogue_active = False
        self._spawn_npcs()

    def _spawn_npcs(self):
        gus = Villager("Farmer Gus", "Dwarf", 690, 1020, team_color=GREEN)
        gus.ai_controller = None
        gus.name = "Farmer Gus"
        gus.low_fields_role = "gus"
        self.gus = gus

        runner = Villager("Lysa Reedrunner", "Human", 1130, 1040, team_color=GREEN)
        runner.ai_controller = None
        runner.name = "Lysa Reedrunner"
        runner.low_fields_role = "supply"
        self.supply_runner = runner

        worker_data = (
            ("Orin Ditchhand", "Goblin", 780, 610),
            ("Mela Root", "Human", 2180, 760),
            ("Tarn Wick", "Dwarf", 650, 1500),
        )
        workers = []
        for name, race, x, y in worker_data:
            worker = Villager(name, race, x, y, team_color=GREEN)
            worker.ai_controller = None
            worker.name = name
            worker.low_fields_role = "worker"
            workers.append(worker)
        self.npcs = [gus, runner] + workers

    def on_enter(self):
        super().on_enter()
        self.manager.current_arena = self.arena
        self.player = self.manager.player_character
        state = low_fields_state(self.manager)
        state["visits"] = int(state.get("visits", 0)) + 1
        self.arena.refresh_persistent_props(self.manager)

        entry = getattr(self.manager, "low_fields_entry", "muckford")
        self.manager.low_fields_entry = None
        if entry == "whisper_marsh":
            self.player.rect.center = (2500, self.arena.height - 130)
        else:
            self.player.rect.center = (470, 155)
        self.player.is_dead = False
        self.player.current_hp = max(1, self.player.current_hp)

        self.monsters.empty()
        self._spawn_population(state)
        self._sync_quest_encounter(state)
        self._update_camera()

        try:
            self.manager.record_tier0_event("visit", "low_fields")
            advice = self.manager.get_tier0_area_advice("low_fields")
            self.warning = advice["warning"]
            self.warning_timer = 360
        except Exception:
            self.warning = "Recommended danger band: Lv 1-3."
            self.warning_timer = 300

        try:
            from systems.world_progression import mark_location_visited
            mark_location_visited(self.manager, "low_fields", set_current=True, surveyed=True)
        except Exception:
            pass

    def _spawn_population(self, state):
        rng = random.Random(MAP_SEED + int(state.get("visits", 0)) * 17)
        for index in range(5):
            x, y = self.arena.random_spawn_point("east")
            monster = MudMite(f"Field Mud Mite {index + 1}", x, y, ENEMY_TEAM)
            monster.low_fields_counted = False
            self.monsters.add(monster)
        for index in range(3):
            x, y = self.arena.random_spawn_point("west")
            monster = ReedSkitter(f"Reed Skitter {index + 1}", x, y, ENEMY_TEAM)
            monster.low_fields_counted = False
            self.monsters.add(monster)
        for index in range(2):
            x, y = self.arena.random_spawn_point("south_east")
            monster = GiantRat(f"Field Rat {index + 1}", x, y, ENEMY_TEAM)
            monster.low_fields_counted = False
            self.monsters.add(monster)

    def _sync_quest_encounter(self, state):
        if int(state.get("quest_stage", 0)) != 2 or state.get("grain_raid_resolved"):
            return
        existing = [m for m in self.monsters if getattr(m, "low_fields_quest_tag", None) == "grain_raider"]
        needed = max(0, 4 - int(state.get("grain_raiders_defeated", 0)) - len(existing))
        for index in range(needed):
            x = 1040 + (index % 2) * 90
            y = 1040 + (index // 2) * 85
            raider = ReedSkitter(f"Grain Cart Skitter {index + 1}", x, y, ENEMY_TEAM)
            raider.low_fields_quest_tag = "grain_raider"
            raider.low_fields_counted = False
            self.monsters.add(raider)
        if needed:
            self._flash("Reed Skitters are tearing into the grain cart!")

    def _near(self, rect: pygame.Rect, inflate=75) -> bool:
        return self.player.rect.colliderect(rect.inflate(inflate, inflate))

    def _flash(self, message: str, duration=210):
        self.feedback = str(message)
        self.feedback_timer = int(duration)

    def handle_event(self, event):
        if self.dialogue_active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.dialogue_active = False
                    return
                if event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.dialogue_index += 1
                    if self.dialogue_index >= len(self.dialogue_pages):
                        self.dialogue_active = False
                    return
            return

        super().handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            if self._try_npc_dialogue():
                return
            if self._try_project():
                return
            if self._try_burrow():
                return
            self._try_gather()

    def _try_npc_dialogue(self) -> bool:
        for npc in self.npcs:
            if not self._near(npc.rect, 70):
                continue
            role = getattr(npc, "low_fields_role", "worker")
            if role == "gus":
                self._open_gus_dialogue()
            elif role == "supply":
                self._open_supply_dialogue()
            else:
                lines = [
                    "The fields feed Muckford before the arena ever pays a purse.",
                    "Watch the ditch banks. Mud Mites come up after every hard rain.",
                    "Greywash water grows crops well enough, if it stays inside the channel.",
                ]
                self._open_dialogue(npc.name, [random.choice(lines)])
            return True
        return False

    def _open_dialogue(self, name: str, pages: Sequence[str]):
        self.dialogue_name = str(name)
        self.dialogue_pages = [str(page) for page in pages]
        self.dialogue_index = 0
        self.dialogue_active = True
        _safe_sound("click")

    def _open_gus_dialogue(self):
        state = low_fields_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        if stage == 0:
            state["quest_stage"] = 1
            pages = (
                "City folk call these the Low Fields because the river stands higher than our roofs. We call them breakfast.",
                "The sluice is leaking. Bring 5 Clay and 4 River Reed to the marked irrigation post. Fix that, and we can save the roots.",
                "The road is open, Commander, but the eastern plots are still wild. Do not mistake farmland for safety.",
            )
            try:
                self.manager.record_tier0_event("flag", "low_fields_started")
            except Exception:
                pass
        elif stage == 1:
            pages = (f"The irrigation post still needs {_cost_text(PROJECT_COSTS['irrigation'])}.",)
        elif stage == 2:
            defeated = int(state.get("grain_raiders_defeated", 0))
            pages = (f"Protect the grain cart. Reed Skitters defeated: {defeated}/4.",)
        elif stage == 3:
            sealed = len(state.get("sealed_burrows", ()))
            pages = (f"The grain is safe. Seal the three Mud Mite burrows with Clay: {sealed}/3.",)
        elif stage == 4:
            pages = (f"One last job: build the lower footbridge. It needs {_cost_text(PROJECT_COSTS['footbridge'])}.",)
        else:
            pages = (
                "The channels hold, the carts move and both sides of the fields are connected. Muckford will notice this harvest.",
                "There is always more work, but now it is honest work instead of disaster.",
            )
        self._open_dialogue("Farmer Gus", pages)

    def _open_supply_dialogue(self):
        state = low_fields_state(self.manager)
        if not state.get("supply_claimed") and int(state.get("quest_stage", 0)) >= 1:
            package = {"Clay": 2, "River Reed": 2, "Softwood": 1}
            for name, amount in package.items():
                self.manager.inventory[name] = int(self.manager.inventory.get(name, 0)) + amount
            state["supply_claimed"] = True
            pages = (
                "Rhea sent what the hospice could spare: two Clay, two River Reed and one Softwood.",
                "It will not finish Gus's work, but it should keep you from starting empty-handed.",
            )
        elif int(state.get("quest_stage", 0)) == 0:
            pages = ("Talk to Farmer Gus. He knows which repair will keep the food road open.",)
        else:
            pages = ("The next supply cart comes when the old one can cross without losing a wheel.",)
        self._open_dialogue("Lysa Reedrunner", pages)

    def _try_project(self) -> bool:
        state = low_fields_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        project = None
        marker = None
        if stage == 1 and self._near(self.arena.irrigation_marker.rect, 90):
            project, marker = "irrigation", self.arena.irrigation_marker
        elif stage == 4 and self._near(self.arena.bridge_marker.rect, 90):
            project, marker = "footbridge", self.arena.bridge_marker
        elif self._near(self.arena.cart_marker.rect, 90) and "grain_cart" not in state.get("projects", ()):
            project, marker = "grain_cart", self.arena.cart_marker
        if not project:
            return False

        cost = PROJECT_COSTS[project]
        if not _consume_cost(self.manager, cost):
            self._flash(f"{marker.label} needs: {_cost_text(cost)}")
            _safe_sound("error")
            return True

        projects = state.setdefault("projects", [])
        if project not in projects:
            projects.append(project)
        if project == "irrigation":
            state["quest_stage"] = 2
            # The repaired sluice also stabilises the damaged cart road.
            if "grain_cart" not in projects:
                projects.append("grain_cart")
            self._flash("Irrigation repaired. Defend the grain cart from Reed Skitters.")
            self._sync_quest_encounter(state)
        elif project == "footbridge":
            state["quest_stage"] = 5
            state["completed"] = True
            self.manager.gold += 35
            self.manager.reputation = int(getattr(self.manager, "reputation", 0)) + 3
            self._flash("Low Fields restored. +35 SP, +3 reputation.", 300)
            try:
                self.manager.record_tier0_event("project", "low_fields_footbridge")
                self.manager.record_tier0_event("quest", "low_fields_restored")
            except Exception:
                pass
        self.arena.refresh_persistent_props(self.manager)
        try:
            self.manager.record_tier0_event("project", f"low_fields_{project}")
        except Exception:
            pass
        _safe_sound("recruit")
        return True

    def _try_burrow(self) -> bool:
        state = low_fields_state(self.manager)
        if int(state.get("quest_stage", 0)) != 3:
            return False
        for burrow in self.arena.burrows:
            if burrow.sealed or not self._near(burrow.rect, 75):
                continue
            if not burrow.seal(self.manager):
                self._flash("Sealing a burrow needs 1 Clay.")
                _safe_sound("error")
                return True
            sealed = len(state.get("sealed_burrows", ()))
            self._flash(f"Burrow sealed: {sealed}/3")
            _safe_sound("recruit")
            if sealed >= 3:
                state["quest_stage"] = 4
                self._flash("All burrows sealed. Farmer Gus needs the lower footbridge rebuilt.", 300)
                try:
                    self.manager.record_tier0_event("project", "low_fields_burrows_sealed")
                except Exception:
                    pass
            return True
        return False

    def _try_gather(self) -> bool:
        state = low_fields_state(self.manager)
        rng = random.Random(MAP_SEED + int(state.get("visits", 0)) * 37 + len(state.get("harvested_nodes", ())))
        for node in self.arena.resources:
            if node.harvested or not self._near(node.rect, 68):
                continue
            message = node.harvest(self.manager, rng)
            if message:
                self._flash(message)
            return True
        return False

    def _count_quest_deaths(self):
        state = low_fields_state(self.manager)
        changed = False
        for monster in self.monsters:
            if not monster.is_dead or getattr(monster, "low_fields_counted", False):
                continue
            monster.low_fields_counted = True
            if getattr(monster, "low_fields_quest_tag", None) == "grain_raider":
                state["grain_raiders_defeated"] = int(state.get("grain_raiders_defeated", 0)) + 1
                changed = True
        if changed and int(state.get("grain_raiders_defeated", 0)) >= 4:
            state["grain_raid_resolved"] = True
            state["quest_stage"] = 3
            self.manager.gold += 8
            self._flash("The grain cart is safe. +8 SP. Gus wants the mite burrows sealed.", 300)
            try:
                self.manager.record_tier0_event("quest", "low_fields_grain_cart_defended")
            except Exception:
                pass

    def update(self):
        if self.manager.paused or self.dialogue_active:
            if self.feedback_timer > 0:
                self.feedback_timer -= 1
            return
        self._count_quest_deaths()
        alive_monsters = [monster for monster in self.monsters if not monster.is_dead]
        all_units = [self.player] + self.npcs + alive_monsters
        self._update_gameplay(all_units)

        if self.player.rect.top < 6:
            self.manager.match_in_progress = False
            self.manager.city_spawn_point = "low_fields_gate"
            try:
                from systems.world_progression import mark_location_visited
                mark_location_visited(self.manager, "muckford", set_current=True)
            except Exception:
                pass
            self.next_state = "muckford_city"
        elif self.player.rect.bottom > self.arena.height - 5 and self.player.rect.centerx > 2050:
            self.manager.match_in_progress = False
            self.manager.marsh_return_state = "low_fields"
            self.next_state = "forest_excursion"

        if self.feedback_timer > 0:
            self.feedback_timer -= 1
        if self.warning_timer > 0:
            self.warning_timer -= 1

    def _nearest_prompt(self):
        for npc in self.npcs:
            if self._near(npc.rect, 70):
                return npc.rect, f"Talk to {npc.name}"
        state = low_fields_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        if stage == 1 and self._near(self.arena.irrigation_marker.rect, 90):
            return self.arena.irrigation_marker.rect, f"Repair irrigation: {_cost_text(PROJECT_COSTS['irrigation'])}"
        if stage == 4 and self._near(self.arena.bridge_marker.rect, 90):
            return self.arena.bridge_marker.rect, f"Build footbridge: {_cost_text(PROJECT_COSTS['footbridge'])}"
        if stage == 3:
            for burrow in self.arena.burrows:
                if not burrow.sealed and self._near(burrow.rect, 75):
                    return burrow.rect, "Seal burrow: 1 Clay"
        for node in self.arena.resources:
            if not node.harvested and self._near(node.rect, 68):
                return node.rect, node.interaction_label
        return None

    @staticmethod
    def _wrap(text: str, font, width: int) -> List[str]:
        lines = []
        current = ""
        for word in str(text).split():
            trial = word if not current else f"{current} {word}"
            if font.size(trial)[0] <= width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def _draw_dialogue(self, screen):
        # Yhtenäinen Muckford-tyylinen dialogi (puhuja esiin + nimikilpi)
        from systems.area_dialogue import draw_area_dialogue
        if draw_area_dialogue(self, screen):
            return
        if not self.dialogue_active or not self.dialogue_pages:
            return
        panel = pygame.Rect(190, SCREEN_HEIGHT - 245, SCREEN_WIDTH - 380, 190)
        overlay = pygame.Surface(panel.size, pygame.SRCALPHA)
        overlay.fill((27, 24, 20, 235))
        screen.blit(overlay, panel.topleft)
        pygame.draw.rect(screen, (181, 145, 86), panel, 3, border_radius=8)
        draw_text(self.dialogue_name, font_main, GOLD_COLOR, screen, panel.x + 24, panel.y + 18)
        y = panel.y + 60
        for line in self._wrap(self.dialogue_pages[self.dialogue_index], font_main, panel.w - 48)[:4]:
            draw_text(line, font_main, WHITE, screen, panel.x + 24, y)
            y += 30
        draw_text("[E / Enter] continue    [Esc] close", font_small, GRAY, screen, panel.right - 360, panel.bottom - 28)

    def draw(self, screen):
        alive_monsters = [monster for monster in self.monsters if not monster.is_dead]
        all_units = [self.player] + self.npcs + alive_monsters
        self._draw_gameplay(screen, all_units)
        offset = (self.camera_x, self.camera_y)

        prompt = None if self.dialogue_active else self._nearest_prompt()
        if prompt:
            rect, label = prompt
            try:
                self.manager._draw_floating_prompt(screen, rect.centerx, rect.top - 15, "E", offset, label)
            except Exception:
                pass

        state = low_fields_state(self.manager)
        remaining = sum(1 for node in self.arena.resources if not node.harvested)
        threats = len(alive_monsters)
        draw_text(
            f"MUCKFORD LOW FIELDS   Resources: {remaining}   Threats: {threats}   Restoration: {int(state.get('quest_stage', 0))}/5",
            font_small,
            WHITE,
            screen,
            34,
            32,
        )
        draw_text(
            "North: Muckford   South-east: Whisper Marsh   Recommended Lv 1-3",
            font_small,
            (195, 190, 155),
            screen,
            34,
            58,
        )
        if self.warning_timer > 0:
            surface = font_main.render(self.warning, True, (245, 169, 90))
            screen.blit(surface, (SCREEN_WIDTH // 2 - surface.get_width() // 2, 92))
        if self.feedback_timer > 0:
            surface = font_main.render(self.feedback, True, GOLD_COLOR)
            screen.blit(surface, (SCREEN_WIDTH // 2 - surface.get_width() // 2, 124))
        self._draw_dialogue(screen)
