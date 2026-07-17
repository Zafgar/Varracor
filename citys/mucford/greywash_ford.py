"""Playable Greywash Ford crossing between Muckford and the Crown causeway."""
from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Sequence, Tuple

import pygame

from assets.tiles.prop import Prop
from menus.gameplay_screen import GameplayScreen
from settings import ENEMY_TEAM, GOLD_COLOR, GRAY, GREEN, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from assets.tiles.water import FishingAnchor, WaterBody
from ui_kit import draw_text, font_main, font_small
from units.greywash_ford_monsters import CaptainGarranVale, CrownDeserter, FordBrute, GreywashRiverjaw
from units.villager import Villager
from vfx import VFXManager


FORD_WIDTH = 3900
FORD_HEIGHT = 2500
FORD_SEED = 70113
SURVEY_COUNT = 3
DESERTER_TARGET = 6
CARAVAN_CHECKPOINTS = 5
BRIDGE_COST = {"Driftwood": 8, "Scrap Iron": 6, "River Reed": 4, "Clay": 3}

FORD_OBJECTIVES = {
    0: "Speak with Ferrykeeper Oswin Pike at the eastern camp.",
    1: "Survey the three marked ford lanes.",
    2: "Defeat six Crown deserters controlling the crossing.",
    3: "Repair the central bridge with local materials.",
    4: "Escort the Muckford caravan across five checkpoints.",
    5: "Search the abandoned Crown watchtower.",
    6: "Defeat Captain Garran Vale at the western causeway.",
    7: "Report the secured crossing to Oswin Pike.",
    8: "Greywash Ford is secured and the road toward Kingsreach is open.",
}


def _safe_sound(name: str) -> None:
    try:
        sound_system.play_sound(name)
    except Exception:
        pass


def _cost_text(cost: Dict[str, int]) -> str:
    return ", ".join(f"{amount} {name}" for name, amount in cost.items())


def ford_state(manager) -> dict:
    global_data = manager.npc_state.setdefault("global", {})
    state = global_data.setdefault("greywash_ford", {})
    state.setdefault("visits", 0)
    state.setdefault("quest_stage", 0)
    state.setdefault("surveyed_lanes", [])
    state.setdefault("deserters_defeated", 0)
    state.setdefault("bridge_repaired", False)
    state.setdefault("caravan_checkpoint", 0)
    state.setdefault("caravan_complete", False)
    state.setdefault("tower_searched", False)
    state.setdefault("boss_unlocked", False)
    state.setdefault("boss_defeated", False)
    state.setdefault("boss_reward_claimed", False)
    state.setdefault("report_reward_claimed", False)
    state.setdefault("completed", False)
    state.setdefault("resource_day", -1)
    state.setdefault("harvested_nodes", [])
    state.setdefault("fish_caught", 0)
    state.setdefault("catches", {})
    state.setdefault("flood_exposure", 0)
    return state


def sync_ford_story(manager) -> bool:
    state = ford_state(manager)
    changed = False
    while True:
        stage = int(state.get("quest_stage", 0))
        if stage == 1 and len(set(state.get("surveyed_lanes", ()))) >= SURVEY_COUNT:
            state["quest_stage"] = 2
        elif stage == 2 and int(state.get("deserters_defeated", 0)) >= DESERTER_TARGET:
            state["quest_stage"] = 3
        elif stage == 3 and state.get("bridge_repaired"):
            state["quest_stage"] = 4
        elif stage == 4 and state.get("caravan_complete"):
            state["quest_stage"] = 5
        elif stage == 5 and state.get("tower_searched"):
            state["quest_stage"] = 6
            state["boss_unlocked"] = True
        elif state.get("boss_defeated") and stage < 7:
            state["quest_stage"] = 7
        elif state.get("completed") and stage < 8:
            state["quest_stage"] = 8
        else:
            break
        changed = True
    return changed


def ford_objective(manager) -> str:
    sync_ford_story(manager)
    return FORD_OBJECTIVES.get(int(ford_state(manager).get("quest_stage", 0)), FORD_OBJECTIVES[8])


def _world_day(manager) -> int:
    clock = getattr(manager, "world_clock", None)
    return int(getattr(clock, "day", 0))


def _consume_cost(manager, cost: Dict[str, int]) -> bool:
    if any(int(manager.inventory.get(name, 0)) < amount for name, amount in cost.items()):
        return False
    for name, amount in cost.items():
        manager.inventory[name] = int(manager.inventory.get(name, 0)) - amount
        if manager.inventory[name] <= 0:
            manager.inventory.pop(name, None)
    return True


class RectObstacle:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.blocks_projectiles = True
        self.is_structure = True
        self.name = "Ford Boundary"


class FordProp(Prop):
    def __init__(self, x: int, y: int, width: int, height: int, style: str, blocking=False):
        super().__init__(x, y, width, height, color=(0, 0, 0))
        self.style = str(style)
        self.image_pos = (x, y)
        self.is_structure = bool(blocking)
        self.blocks_projectiles = bool(blocking)
        self.has_shadow = style not in {"ford_stones", "bridge", "road"}
        self._redraw()

    def _redraw(self):
        w, h = self.rect.size
        image = pygame.Surface((w, h), pygame.SRCALPHA)
        if self.style == "willow":
            pygame.draw.line(image, (80, 58, 38), (w // 2, h - 8), (w // 2, 36), 15)
            pygame.draw.line(image, (89, 65, 43), (w // 2, 62), (22, 30), 8)
            pygame.draw.line(image, (89, 65, 43), (w // 2, 58), (w - 20, 21), 8)
            for x, y, r in ((23, 29, 24), (48, 20, 29), (76, 31, 25), (38, 49, 27), (68, 51, 25)):
                pygame.draw.circle(image, (62, 103, 62), (x, y), r)
                pygame.draw.circle(image, (87, 126, 71), (x - 5, y - 5), max(8, r - 9))
        elif self.style == "boulder":
            pygame.draw.ellipse(image, (80, 82, 76), (4, 14, w - 8, h - 18))
            pygame.draw.polygon(image, (111, 111, 98), [(12, h - 20), (24, 12), (w - 18, 8), (w - 7, h - 23)])
            pygame.draw.line(image, (145, 142, 121), (26, 19), (w - 24, 16), 3)
        elif self.style == "ford_stones":
            for index, x in enumerate(range(5, w - 8, 39)):
                y = 8 + (index % 3) * 12
                pygame.draw.ellipse(image, (115, 113, 96), (x, y, 33, h - y - 8))
                pygame.draw.arc(image, (171, 164, 133), (x + 4, y + 3, 23, 15), 3.3, 5.9, 2)
        elif self.style == "bridge":
            pygame.draw.rect(image, (74, 58, 43), (0, 8, w, h - 16), border_radius=5)
            for x in range(4, w, 24):
                pygame.draw.rect(image, (137, 96, 54), (x, 11, 19, h - 22), border_radius=2)
                pygame.draw.line(image, (185, 139, 78), (x + 3, 15), (x + 15, 15), 2)
            pygame.draw.line(image, (51, 40, 31), (0, 10), (w, 10), 5)
            pygame.draw.line(image, (51, 40, 31), (0, h - 10), (w, h - 10), 5)
        elif self.style == "broken_bridge":
            pygame.draw.line(image, (76, 57, 40), (5, h // 2), (w // 3, h // 2 - 9), 15)
            pygame.draw.line(image, (76, 57, 40), (w - 5, h // 2), (w * 2 // 3, h // 2 + 8), 15)
            for x in (15, 45, w - 60, w - 30):
                pygame.draw.rect(image, (133, 92, 50), (x, 13, 20, h - 26), border_radius=2)
            pygame.draw.line(image, (59, 44, 34), (w // 3, 7), (w * 2 // 3, h - 6), 5)
        elif self.style == "watchtower":
            pygame.draw.rect(image, (88, 79, 65), (24, 46, w - 48, h - 56))
            pygame.draw.rect(image, (130, 115, 90), (24, 46, w - 48, h - 56), 5)
            for x in range(31, w - 28, 30):
                pygame.draw.line(image, (57, 53, 48), (x, 50), (x, h - 13), 4)
            pygame.draw.polygon(image, (71, 65, 57), [(9, 52), (w // 2, 6), (w - 9, 52)])
            pygame.draw.rect(image, (33, 31, 30), (w // 2 - 16, h - 54, 32, 44))
            pygame.draw.line(image, (135, 89, 49), (w // 2 + 3, 57), (w // 2 + 3, 17), 5)
            pygame.draw.polygon(image, (130, 53, 47), [(w // 2 + 3, 17), (w // 2 + 40, 28), (w // 2 + 3, 40)])
        elif self.style == "camp":
            pygame.draw.polygon(image, (85, 93, 68), [(10, h - 11), (w // 2, 18), (w - 10, h - 11)])
            pygame.draw.polygon(image, (146, 120, 70), [(17, h - 13), (w // 2, 33), (w - 17, h - 13)])
            pygame.draw.circle(image, (113, 50, 29), (w - 27, h - 20), 13)
            pygame.draw.circle(image, (237, 135, 45), (w - 27, h - 25), 8)
        self.image = image


class FordResourceNode(Prop):
    def __init__(self, node_id: str, x: int, y: int, resource: str, style: str, amount=(1, 2), harvested=False):
        super().__init__(x, y, 56, 56, color=(0, 0, 0))
        self.node_id = str(node_id)
        self.resource_name = str(resource)
        self.style = str(style)
        self.min_amount, self.max_amount = int(amount[0]), int(amount[1])
        self.harvested = bool(harvested)
        self.image_pos = (x, y)
        self.rect = pygame.Rect(x + 5, y + 24, 46, 28)
        self.has_shadow = style not in {"reeds", "clay"}
        self.blocks_projectiles = False
        self.is_structure = False
        self._redraw()

    def _redraw(self):
        image = pygame.Surface((56, 56), pygame.SRCALPHA)
        if self.harvested:
            pygame.draw.ellipse(image, (66, 58, 46, 100), (8, 43, 40, 8))
        elif self.style == "reeds":
            for index, x in enumerate((8, 15, 23, 31, 39, 47)):
                height = 25 + (index % 3) * 7
                pygame.draw.line(image, (73, 122, 70), (x, 52), (x + index % 2, 52 - height), 3)
                pygame.draw.line(image, (163, 128, 63), (x, 52 - height), (x + 4, 47 - height), 3)
        elif self.style == "clay":
            pygame.draw.ellipse(image, (104, 74, 55), (4, 28, 48, 23))
            pygame.draw.ellipse(image, (151, 99, 67), (10, 21, 35, 22))
        elif self.style == "scrap":
            pygame.draw.polygon(image, (111, 113, 108), [(5, 46), (19, 15), (31, 43)])
            pygame.draw.rect(image, (75, 80, 78), (23, 23, 28, 22), border_radius=3)
            pygame.draw.circle(image, (143, 118, 73), (38, 18), 8, 3)
        else:
            pygame.draw.line(image, (104, 75, 47), (6, 43), (50, 18), 10)
            pygame.draw.line(image, (151, 109, 63), (9, 39), (49, 17), 3)
            pygame.draw.line(image, (87, 62, 42), (26, 30), (17, 12), 5)
        self.image = image

    def harvest(self, manager) -> Optional[str]:
        if self.harvested:
            return None
        amount = random.randint(self.min_amount, self.max_amount)
        manager.inventory[self.resource_name] = int(manager.inventory.get(self.resource_name, 0)) + amount
        state = ford_state(manager)
        harvested = state.setdefault("harvested_nodes", [])
        if self.node_id not in harvested:
            harvested.append(self.node_id)
        self.harvested = True
        self._redraw()
        _safe_sound("recruit")
        return f"+{amount} {self.resource_name}"


class FordSurveyMarker(Prop):
    def __init__(self, marker_id: str, x: int, y: int, label: str, complete=False):
        super().__init__(x, y, 82, 92, color=(0, 0, 0))
        self.marker_id = str(marker_id)
        self.label = str(label)
        self.complete = bool(complete)
        self.rect = pygame.Rect(x + 13, y + 48, 56, 36)
        self.image_pos = (x, y)
        self.has_shadow = True
        self.blocks_projectiles = False
        self.is_structure = False
        self._redraw()

    def _redraw(self):
        image = pygame.Surface((82, 92), pygame.SRCALPHA)
        pygame.draw.line(image, (82, 59, 40), (40, 87), (40, 18), 6)
        pygame.draw.polygon(image, (126, 94, 54), [(40, 18), (76, 32), (40, 48)])
        pygame.draw.rect(image, (171, 145, 90), (11, 52, 61, 27), border_radius=4)
        color = (78, 177, 104) if self.complete else (235, 190, 77)
        pygame.draw.circle(image, color, (15, 15), 9, 3)
        if self.complete:
            pygame.draw.line(image, color, (10, 15), (14, 20), 3)
            pygame.draw.line(image, color, (14, 20), (23, 8), 3)
        self.image = image


class CaravanCart(Prop):
    def __init__(self, x: int, y: int):
        super().__init__(x, y, 154, 104, color=(0, 0, 0))
        self.image_pos = (x, y)
        self.rect = pygame.Rect(x + 8, y + 49, 138, 46)
        self.blocks_projectiles = False
        self.is_structure = False
        self._redraw()

    def move_to(self, x: int, y: int):
        self.image_pos = (int(x), int(y))
        self.rect.topleft = (int(x) + 8, int(y) + 49)

    def _redraw(self):
        image = pygame.Surface((154, 104), pygame.SRCALPHA)
        pygame.draw.rect(image, (105, 73, 44), (17, 31, 118, 52), border_radius=7)
        pygame.draw.rect(image, (159, 113, 63), (17, 31, 118, 52), 4, border_radius=7)
        for x in (32, 63, 94):
            pygame.draw.ellipse(image, (188, 151, 83), (x, 12, 34, 38))
            pygame.draw.line(image, (104, 73, 42), (x + 4, 18), (x + 28, 42), 3)
        pygame.draw.circle(image, (52, 47, 42), (36, 83), 17)
        pygame.draw.circle(image, (52, 47, 42), (119, 83), 17)
        pygame.draw.circle(image, (141, 127, 101), (36, 83), 7)
        pygame.draw.circle(image, (141, 127, 101), (119, 83), 7)
        self.image = image


class GreywashFordArena:
    def __init__(self, manager):
        self.manager = manager
        self.width = FORD_WIDTH
        self.height = FORD_HEIGHT
        self.props: List[object] = []
        self.floor_props: List[object] = []
        self.land_obstacles: List[object] = []
        self.water_obstacles: List[object] = []
        self.obstacles: List[object] = []
        self.resources: List[FordResourceNode] = []
        self.survey_markers: List[FordSurveyMarker] = []
        self.rng = random.Random(FORD_SEED)
        self.vfx = VFXManager()
        self.flow_spray = []
        self.floor_image = pygame.Surface((self.width, self.height))
        self.ford_bands = [(510, 700), (1110, 1305), (2070, 2255)]
        self.bridge_band = (1645, 1825)
        self.bridge_rect = pygame.Rect(1250, 1650, 1450, 170)
        self.muckford_exit = pygame.Rect(self.width - 76, 1450, 100, 620)
        self.whisper_exit = pygame.Rect(2860, self.height - 80, 850, 110)
        self.kingsreach_exit = pygame.Rect(-25, 280, 100, 570)
        self._generate_floor()
        self.river = WaterBody(
            pygame.Rect(1450, -40, 1000, self.height + 80),
            seed=FORD_SEED,
            name="Greywash Ford",
            style="river",
            flow=(0.20, 2.15),
            shore_variance=64,
            deep_margin=78,
            shallow_color=(72, 114, 116),
            mid_color=(40, 82, 99),
            deep_color=(16, 49, 72),
            foam_color=(198, 225, 216),
        )
        anchors = self.river.fishing_anchors(10, difficulty=3)
        self.fishing_spots = [
            FishingAnchor(a.x, a.y, a.bank, a.water_name, 3, "greywash_ford")
            for a in anchors
            if not any(start - 80 <= a.y <= end + 80 for start, end in self.ford_bands)
        ]
        self._build_landscape()
        self.refresh_persistent(manager)

    def _generate_floor(self):
        self.floor_image.fill((76, 83, 58))
        rng = random.Random(FORD_SEED + 3)
        for _ in range(2200):
            x = rng.randrange(self.width)
            y = rng.randrange(self.height)
            shade = rng.randint(-9, 12)
            color = (max(35, 76 + shade), max(39, 83 + shade), max(31, 58 + shade))
            pygame.draw.circle(self.floor_image, color, (x, y), rng.randint(5, 31))
        pygame.draw.line(self.floor_image, (123, 104, 70), (self.width - 40, 1770), (2500, 1770), 170)
        pygame.draw.line(self.floor_image, (113, 98, 69), (1400, 1770), (60, 570), 175)
        pygame.draw.line(self.floor_image, (132, 118, 89), (1300, 1760), (80, 560), 44)
        pygame.draw.rect(self.floor_image, (101, 88, 61), (120, 245, 900, 690), border_radius=32)

    def _add(self, prop, blocking=False):
        self.props.append(prop)
        if blocking or getattr(prop, "is_structure", False):
            self.land_obstacles.append(prop)

    def _build_landscape(self):
        self.land_obstacles.extend(
            [
                RectObstacle((0, -40, self.width, 40)),
                RectObstacle((0, self.height, self.width, 40)),
                RectObstacle((-40, 0, 40, self.height)),
                RectObstacle((self.width, 0, 40, self.height)),
            ]
        )
        for _ in range(38):
            side = self.rng.choice(("west", "east"))
            x = self.rng.randint(110, 1210) if side == "west" else self.rng.randint(2700, self.width - 130)
            y = self.rng.randint(120, self.height - 180)
            if self.rng.random() < 0.66:
                prop = FordProp(x, y, 102, 126, "willow", blocking=True)
            else:
                prop = FordProp(x, y, 88, 66, "boulder", blocking=True)
            self._add(prop, blocking=True)

        for start, end in self.ford_bands:
            y = (start + end) // 2 - 50
            left, right = self.river.bounds_at((start + end) // 2)
            self.props.append(FordProp(int(left) - 20, y, int(right - left) + 40, 105, "ford_stones"))

        self.broken_bridge = FordProp(self.bridge_rect.x, self.bridge_rect.y, self.bridge_rect.w, self.bridge_rect.h, "broken_bridge")
        self.props.append(self.broken_bridge)
        self.repaired_bridge: Optional[FordProp] = None
        self.watchtower = FordProp(335, 370, 210, 250, "watchtower", blocking=True)
        self._add(self.watchtower, blocking=True)
        self.east_camp = FordProp(3160, 1570, 180, 135, "camp")
        self.props.append(self.east_camp)

        state = ford_state(self.manager)
        surveyed = set(state.get("surveyed_lanes", ()))
        marker_data = (
            ("north_ford", 2510, 540, "Survey northern shallows"),
            ("mid_ford", 1260, 1160, "Survey broken causeway ford"),
            ("south_ford", 2520, 2120, "Survey southern ferry ford"),
        )
        for marker_id, x, y, label in marker_data:
            marker = FordSurveyMarker(marker_id, x, y, label, marker_id in surveyed)
            self.survey_markers.append(marker)
            self.props.append(marker)

        harvested = set(state.get("harvested_nodes", ()))
        specs = []
        for index, (resource, style, amount) in enumerate(
            [("River Reed", "reeds", (1, 3))] * 10
            + [("Clay", "clay", (1, 2))] * 7
            + [("Driftwood", "driftwood", (1, 3))] * 8
            + [("Scrap Iron", "scrap", (1, 2))] * 6
        ):
            side = "west" if index % 2 else "east"
            x = self.rng.randint(1050, 1340) if side == "west" else self.rng.randint(2555, 2830)
            y = self.rng.randint(120, self.height - 150)
            node_id = f"ford_node_{index + 1}"
            node = FordResourceNode(node_id, x, y, resource, style, amount, node_id in harvested)
            self.resources.append(node)
            self.props.append(node)

    def refresh_persistent(self, manager):
        state = ford_state(manager)
        repaired = bool(state.get("bridge_repaired"))
        if repaired and self.repaired_bridge is None:
            if self.broken_bridge in self.props:
                self.props.remove(self.broken_bridge)
            self.repaired_bridge = FordProp(self.bridge_rect.x, self.bridge_rect.y, self.bridge_rect.w, self.bridge_rect.h, "bridge")
            self.props.append(self.repaired_bridge)
        elif not repaired and self.repaired_bridge is not None:
            if self.repaired_bridge in self.props:
                self.props.remove(self.repaired_bridge)
            self.repaired_bridge = None
            if self.broken_bridge not in self.props:
                self.props.append(self.broken_bridge)
        surveyed = set(state.get("surveyed_lanes", ()))
        for marker in self.survey_markers:
            marker.complete = marker.marker_id in surveyed
            marker._redraw()
        harvested = set(state.get("harvested_nodes", ()))
        for node in self.resources:
            node.harvested = node.node_id in harvested
            node._redraw()
        self._rebuild_water_collision(repaired)

    def _rebuild_water_collision(self, bridge_repaired: bool):
        bands = list(self.ford_bands)
        if bridge_repaired:
            bands.append(self.bridge_band)
        self.water_obstacles = self.river.make_collision_barriers(bands, slice_height=52, inset=14)
        self.obstacles = list(self.land_obstacles) + list(self.water_obstacles)

    def is_safe_crossing(self, point: Tuple[int, int]) -> bool:
        x, y = point
        if not self.river.contains_point(point, inset=-5):
            return True
        if any(start <= y <= end for start, end in self.ford_bands):
            return True
        if ford_state(self.manager).get("bridge_repaired") and self.bridge_rect.collidepoint(x, y):
            return True
        return False

    def is_wading(self, point: Tuple[int, int]) -> bool:
        if not self.river.contains_point(point, inset=-5):
            return False
        if ford_state(self.manager).get("bridge_repaired") and self.bridge_rect.collidepoint(point):
            return False
        return any(start <= point[1] <= end for start, end in self.ford_bands)

    def flood_strength(self) -> int:
        weather = str(getattr(getattr(self.manager, "world_clock", None), "weather", "")).lower()
        return 3 if "storm" in weather else 2 if "rain" in weather else 1

    def update(self, manager=None):
        self.vfx.update(manager)
        if random.random() < 0.17:
            y = random.randint(40, self.height - 40)
            left, right = self.river.bounds_at(y)
            self.flow_spray.append({
                "x": random.randint(int(left + 30), int(right - 30)),
                "y": y,
                "life": random.randint(35, 90),
                "size": random.randint(2, 6),
            })
        for spray in self.flow_spray:
            spray["life"] -= 1
            spray["y"] += 0.8 * self.flood_strength()
        self.flow_spray = [spray for spray in self.flow_spray if spray["life"] > 0]
        if random.random() < 0.035:
            y = random.randint(60, self.height - 60)
            left, right = self.river.bounds_at(y)
            self.river.add_ripple((random.randint(int(left + 25), int(right - 25)), y))

    def draw_background(self, screen, offset=(0, 0)):
        screen.blit(self.floor_image, (-int(offset[0]), -int(offset[1])))
        self.river.draw(screen, offset)

    def draw_foreground(self, screen, offset=(0, 0)):
        ox, oy = int(offset[0]), int(offset[1])
        strength = self.flood_strength()
        for spray in self.flow_spray:
            x = int(spray["x"] - ox)
            y = int(spray["y"] - oy)
            if -10 < x < screen.get_width() + 10 and -10 < y < screen.get_height() + 10:
                pygame.draw.circle(screen, (205, 229, 223), (x, y), spray["size"], 1)
        if strength >= 2:
            flood = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            flood.fill((38, 76, 89, 12 if strength == 2 else 22))
            screen.blit(flood, (0, 0))
        self.vfx.draw_top(screen, offset)


class GreywashFordMenu(GameplayScreen):
    def __init__(self, manager):
        super().__init__(manager)
        self.arena = GreywashFordArena(manager)
        self.monsters = pygame.sprite.Group()
        self.ford_npcs: List[Villager] = []
        self.dynamic_props: List[object] = []
        self.boss: Optional[CaptainGarranVale] = None
        self.caravan: Optional[CaravanCart] = None
        self.feedback = ""
        self.feedback_timer = 0
        self.warning = ""
        self.warning_timer = 0
        self.dialogue_active = False
        self.dialogue_name = ""
        self.dialogue_pages: List[str] = []
        self.dialogue_index = 0
        self.wade_tick = 0

    def on_enter(self):
        super().on_enter()
        self.manager.current_arena = self.arena
        self.manager.current_map_vfx = self.arena.vfx
        self.player = self.manager.player_character
        entry = getattr(self.manager, "greywash_entry", None) or "muckford"
        self.manager.greywash_entry = None
        if entry == "whisper_marsh":
            self.player.rect.center = (3290, self.arena.height - 150)
        elif entry == "kingsreach":
            self.player.rect.center = (110, 560)
        else:
            self.player.rect.center = (3660, 1770)
        self.player.facing_right = entry == "kingsreach"
        self.player.is_dead = False
        self.player.current_hp = max(1, self.player.current_hp)

        state = ford_state(self.manager)
        today = _world_day(self.manager)
        if int(state.get("resource_day", -1)) != today:
            state["resource_day"] = today
            state["harvested_nodes"] = []
        state["visits"] = int(state.get("visits", 0)) + 1
        sync_ford_story(self.manager)
        self.arena.refresh_persistent(self.manager)
        self.manager.current_fishing_spots = list(self.arena.fishing_spots)
        self.monsters.empty()
        self._spawn_population()
        self._ensure_deserter_objective()
        self._refresh_npcs_and_caravan()
        self._spawn_boss_if_needed()
        self._update_camera()
        try:
            advice = self.manager.get_tier0_area_advice("greywash_ford")
            self.warning = advice.get("warning", "OPEN RISK — recommended Lv 5-7")
        except Exception:
            self.warning = "OPEN RISK — recommended Lv 5-7"
        self.warning_timer = 420
        try:
            from systems.world_progression import mark_location_visited
            mark_location_visited(self.manager, "greywash_ford", set_current=True, surveyed=True)
        except Exception:
            pass
        try:
            self.manager.record_tier0_event("visit", "greywash_ford")
            self.manager.record_tier0_event("risk_seen", "greywash_ford")
        except Exception:
            pass
        _safe_sound("water")

    @staticmethod
    def _npc(name: str, race: str, x: int, y: int, role: str):
        npc = Villager(name, race, x, y, team_color=GREEN)
        npc.ai_controller = None
        npc.name = str(name)
        npc.ford_role = str(role)
        npc.animation_state = "idle"
        return npc

    def _refresh_npcs_and_caravan(self):
        for prop in list(self.dynamic_props):
            if prop in self.arena.props:
                self.arena.props.remove(prop)
        self.dynamic_props = []
        self.ford_npcs = [
            self._npc("Ferrykeeper Oswin Pike", "Human", 3300, 1720, "oswin"),
            self._npc("Saint Mara Wold", "Human", 3170, 1820, "saint"),
            self._npc("Hobb Reed", "Goblin", 3435, 1840, "saint"),
        ]
        self.dynamic_props.extend(self.ford_npcs)
        state = ford_state(self.manager)
        self.caravan = None
        if int(state.get("quest_stage", 0)) == 4 and not state.get("caravan_complete"):
            route = self._caravan_route()
            index = max(0, min(len(route) - 1, int(state.get("caravan_checkpoint", 0))))
            x, y = route[index]
            self.caravan = CaravanCart(x, y)
            self.dynamic_props.append(self.caravan)
        self.arena.props.extend(self.dynamic_props)

    @staticmethod
    def _caravan_route():
        return (
            (3370, 1665),
            (2790, 1665),
            (2230, 1665),
            (1510, 1665),
            (930, 1180),
            (430, 690),
        )

    def _spawn_population(self):
        state = ford_state(self.manager)
        cleared = bool(state.get("boss_defeated"))
        placements = [
            (GreywashRiverjaw, 1580, 600), (GreywashRiverjaw, 2260, 1190),
            (GreywashRiverjaw, 1700, 2140), (GreywashRiverjaw, 2320, 2180),
            (CrownDeserter, 1050, 520), (CrownDeserter, 1180, 880),
            (CrownDeserter, 800, 1210), (CrownDeserter, 1110, 1540),
            (CrownDeserter, 720, 1940), (CrownDeserter, 980, 2220),
            (FordBrute, 570, 1030), (FordBrute, 780, 1760),
        ]
        if cleared:
            placements = placements[::3]
        for index, (monster_class, x, y) in enumerate(placements):
            monster = monster_class(f"{monster_class.SPECIES} {index + 1}", x, y, ENEMY_TEAM)
            monster.ford_counted = False
            if monster_class is CrownDeserter:
                monster.ford_quest_tag = "deserter"
            self.monsters.add(monster)

    def _ensure_deserter_objective(self):
        state = ford_state(self.manager)
        if int(state.get("quest_stage", 0)) != 2:
            return
        remaining = max(0, DESERTER_TARGET - int(state.get("deserters_defeated", 0)))
        living = [m for m in self.monsters if not m.is_dead and getattr(m, "ford_quest_tag", None) == "deserter"]
        for index in range(max(0, remaining - len(living))):
            deserter = CrownDeserter(f"Ford Occupier {index + 1}", 820 + index * 85, 930 + (index % 2) * 120, ENEMY_TEAM)
            deserter.ford_counted = False
            deserter.ford_quest_tag = "deserter"
            self.monsters.add(deserter)

    def _spawn_boss_if_needed(self):
        state = ford_state(self.manager)
        self.boss = None
        if not state.get("boss_unlocked") or state.get("boss_defeated"):
            return
        self.boss = CaptainGarranVale("Captain Garran Vale", 660, 650, ENEMY_TEAM)
        self.monsters.add(self.boss)
        self._flash("Captain Garran Vale blocks the Crown causeway.", 340)

    def _near(self, rect: pygame.Rect, inflate=78) -> bool:
        return self.player.rect.colliderect(rect.inflate(inflate, inflate))

    def _flash(self, message: str, duration=220):
        self.feedback = str(message)
        self.feedback_timer = int(duration)

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

    def _open_dialogue(self, name: str, pages: Sequence[str]):
        self.dialogue_name = str(name)
        self.dialogue_pages = [str(page) for page in pages]
        self.dialogue_index = 0
        self.dialogue_active = True
        _safe_sound("click")

    def _start_story(self):
        state = ford_state(self.manager)
        if int(state.get("quest_stage", 0)) == 0:
            state["quest_stage"] = 1
        try:
            self.manager.record_tier0_event("flag", "greywash_ford_started")
        except Exception:
            pass
        self._open_dialogue(
            "Ferrykeeper Oswin Pike",
            (
                "This is where Muckford mud meets the King's stone. Garran Vale's deserters tax the river without Crown law or shame.",
                "Mark the three ford lanes first. The rain moves the safe stones, and a bad route can drown a loaded cart before anyone draws steel.",
                "The crossing is open country, Commander. Lv 5-7 is a warning, not a wall.",
            ),
        )

    def _oswin_dialogue(self):
        state = ford_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        if stage == 0:
            self._start_story()
            return
        if stage == 1:
            pages = (f"Survey the north, middle and south lanes. Marked: {len(set(state.get('surveyed_lanes', ())))}/{SURVEY_COUNT}.",)
        elif stage == 2:
            pages = (f"Vale's deserters own the western bank. Defeated: {int(state.get('deserters_defeated', 0))}/{DESERTER_TARGET}.",)
        elif stage == 3:
            pages = (f"The central bridge can be rebuilt. It needs {_cost_text(BRIDGE_COST)}.",)
        elif stage == 4:
            pages = (f"Keep beside the grain cart and move it checkpoint by checkpoint. Progress: {int(state.get('caravan_checkpoint', 0))}/{CARAVAN_CHECKPOINTS}.",)
        elif stage == 5:
            pages = ("The caravan crossed. Vale fell back to the abandoned watchtower. Search it before he closes the road again.",)
        elif stage == 6:
            pages = ("Garran Vale is on the western causeway. He will use the flood and every deserter he has left.",)
        elif stage == 7:
            self._complete_report()
            return
        else:
            pages = (
                "The ford stones are marked, the bridge holds and Crown caravans can reach Muckford again.",
                "Kingsreach Toll is the next problem. At least now it is a road problem instead of a drowning problem.",
            )
        self._open_dialogue("Ferrykeeper Oswin Pike", pages)

    def _saint_dialogue(self, name: str):
        state = ford_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        if stage < 2:
            pages = (
                "The Shanty Yard Saints keep a rope on both banks. We save whoever the Crown forgets to count.",
                "Survey before fighting. A ford can kill a stronger team than any deserter.",
            )
        elif stage < 5:
            pages = (
                "Vale's people know every stone. Break their control, rebuild the bridge and keep the caravan moving.",
                "We will hold the eastern rope while you clear the west.",
            )
        else:
            pages = ("The Saints have the crossing. Finish Vale and we can keep the route open after you leave.",)
        self._open_dialogue(name, pages)

    def _complete_report(self):
        state = ford_state(self.manager)
        if not state.get("report_reward_claimed"):
            self.manager.gold += 175
            self.manager.reputation = int(getattr(self.manager, "reputation", 0)) + 12
            self.manager.city_storage["Ford Trade Goods"] = int(self.manager.city_storage.get("Ford Trade Goods", 0)) + 10
            self.manager.city_storage["Scrap Iron"] = int(self.manager.city_storage.get("Scrap Iron", 0)) + 5
            state["report_reward_claimed"] = True
        state["completed"] = True
        sync_ford_story(self.manager)
        try:
            self.manager.record_tier0_event("quest", "greywash_ford_secured")
            self.manager.record_tier0_event("flag", "kingsreach_access")
        except Exception:
            pass
        self._open_dialogue(
            "Ferrykeeper Oswin Pike",
            (
                "Greywash Ford is secured. The Saints hold the ropes, the bridge carries carts and Vale's levy is finished.",
                "Muckford receives trade goods and scrap. +175 SP, +12 reputation. The road to Kingsreach Toll is open.",
            ),
        )
        self._flash("Greywash Ford secured. Kingsreach road opened.", 420)

    def _try_npc(self) -> bool:
        for npc in self.ford_npcs:
            if not self._near(npc.rect, 76):
                continue
            if getattr(npc, "ford_role", "") == "oswin":
                self._oswin_dialogue()
            else:
                self._saint_dialogue(npc.name)
            return True
        return False

    def _try_survey(self) -> bool:
        state = ford_state(self.manager)
        if int(state.get("quest_stage", 0)) != 1:
            return False
        for marker in self.arena.survey_markers:
            if marker.complete or not self._near(marker.rect, 78):
                continue
            surveyed = state.setdefault("surveyed_lanes", [])
            if marker.marker_id not in surveyed:
                surveyed.append(marker.marker_id)
            marker.complete = True
            marker._redraw()
            self._flash(f"Ford lanes surveyed: {len(set(surveyed))}/{SURVEY_COUNT}")
            if sync_ford_story(self.manager):
                self._flash("All ford lanes marked. Clear Vale's deserters from the western bank.", 300)
                self._ensure_deserter_objective()
            return True
        return False

    def _try_bridge(self) -> bool:
        state = ford_state(self.manager)
        if int(state.get("quest_stage", 0)) != 3 or not self._near(self.arena.bridge_rect, 110):
            return False
        if not _consume_cost(self.manager, BRIDGE_COST):
            self._flash(f"Bridge repair needs: {_cost_text(BRIDGE_COST)}")
            _safe_sound("error")
            return True
        state["bridge_repaired"] = True
        sync_ford_story(self.manager)
        self.arena.refresh_persistent(self.manager)
        self._refresh_npcs_and_caravan()
        try:
            self.manager.record_tier0_event("project", "greywash_bridge")
        except Exception:
            pass
        self._flash("Central bridge repaired. The Muckford caravan is ready to cross.", 320)
        _safe_sound("recruit")
        return True

    def _try_caravan(self) -> bool:
        state = ford_state(self.manager)
        if int(state.get("quest_stage", 0)) != 4 or self.caravan is None or not self._near(self.caravan.rect, 100):
            return False
        checkpoint = int(state.get("caravan_checkpoint", 0)) + 1
        route = self._caravan_route()
        if checkpoint >= len(route):
            state["caravan_checkpoint"] = CARAVAN_CHECKPOINTS
            state["caravan_complete"] = True
            sync_ford_story(self.manager)
            self._refresh_npcs_and_caravan()
            self._flash("The caravan reached the western causeway. Search the abandoned watchtower.", 340)
            try:
                self.manager.record_tier0_event("quest", "greywash_caravan_escorted")
            except Exception:
                pass
            return True
        state["caravan_checkpoint"] = checkpoint
        x, y = route[checkpoint]
        self.caravan.move_to(x, y)
        ambushers = 2 + checkpoint // 2
        for index in range(ambushers):
            monster_class = FordBrute if checkpoint >= 4 and index == ambushers - 1 else CrownDeserter
            monster = monster_class(
                f"Caravan Ambusher {checkpoint}-{index + 1}",
                x - 160 + index * 90,
                y + 150,
                ENEMY_TEAM,
            )
            monster.ford_counted = True
            self.monsters.add(monster)
        self._flash(f"Caravan checkpoint {checkpoint}/{CARAVAN_CHECKPOINTS}. Ambush from the river road!")
        _safe_sound("click")
        return True

    def _try_tower(self) -> bool:
        state = ford_state(self.manager)
        if int(state.get("quest_stage", 0)) != 5 or not self._near(self.arena.watchtower.rect, 120):
            return False
        state["tower_searched"] = True
        state["boss_unlocked"] = True
        sync_ford_story(self.manager)
        self.manager.inventory["Wax Seal"] = int(self.manager.inventory.get("Wax Seal", 0)) + 1
        self.manager.inventory["Torn Crown Orders"] = int(self.manager.inventory.get("Torn Crown Orders", 0)) + 1
        self._flash("Vale's orders found. Captain Garran Vale takes the western causeway.", 340)
        self._spawn_boss_if_needed()
        return True

    def _nearest_fishing_anchor(self) -> Optional[FishingAnchor]:
        best = None
        best_distance = 99999.0
        for anchor in self.arena.fishing_spots:
            distance = math.hypot(self.player.rect.centerx - anchor.x, self.player.rect.centery - anchor.y)
            if distance < 92 and distance < best_distance:
                best, best_distance = anchor, distance
        return best

    def _try_fishing(self) -> bool:
        anchor = self._nearest_fishing_anchor()
        if anchor is None:
            return False
        self.manager.pending_fishing_anchor = anchor
        self.manager.fishing_return_state = "regional_staging"
        self.manager.pending_local_area = "marsh_fishing"
        self.manager.pending_world_location = "greywash_ford"
        self.next_state = "regional_staging"
        _safe_sound("click")
        return True

    def _try_gather(self) -> bool:
        for node in self.arena.resources:
            if node.harvested or not self._near(node.rect, 70):
                continue
            message = node.harvest(self.manager)
            if message:
                self._flash(message)
            return True
        return False

    def handle_event(self, event):
        if self.dialogue_active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.dialogue_active = False
                    return
                if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.dialogue_index += 1
                    if self.dialogue_index >= len(self.dialogue_pages):
                        self.dialogue_active = False
                    return
            return
        super().handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            if self._try_npc() or self._try_survey() or self._try_bridge() or self._try_caravan() or self._try_tower():
                return
            if self._try_fishing() or self._try_gather():
                return

    def _count_deserter_deaths(self):
        state = ford_state(self.manager)
        if int(state.get("quest_stage", 0)) != 2:
            return
        changed = False
        for monster in self.monsters:
            if not monster.is_dead or getattr(monster, "ford_counted", False):
                continue
            monster.ford_counted = True
            if getattr(monster, "ford_quest_tag", None) == "deserter":
                state["deserters_defeated"] = int(state.get("deserters_defeated", 0)) + 1
                changed = True
        if changed and sync_ford_story(self.manager):
            self._flash("Vale's western-bank patrol is broken. Repair the central bridge.", 330)

    def _transfer_loot(self):
        loot = self.manager.round_rewards.get("loot")
        if not loot:
            return
        for name, amount in list(loot.items()):
            self.manager.inventory[name] = int(self.manager.inventory.get(name, 0)) + int(amount)
        self.manager.round_rewards["loot"] = {}

    def _apply_current(self):
        if not self.arena.is_wading(self.player.rect.center):
            self.wade_tick = 0
            return
        self.wade_tick += 1
        strength = self.arena.flood_strength()
        self.player.rect.y += strength
        if self.wade_tick % 42 != 0:
            return
        state = ford_state(self.manager)
        state["flood_exposure"] = min(100, int(state.get("flood_exposure", 0)) + strength * 2)
        try:
            self.player.apply_status("Slow", 55 + strength * 15, 0)
        except Exception:
            pass
        if strength >= 2 and self.wade_tick % 84 == 0:
            damage = 3 + strength * 2
            try:
                self.player.take_damage(damage, "Physical", manager=self.manager)
            except Exception:
                self.player.current_hp = max(1, self.player.current_hp - damage)
            self._flash("The flooded Greywash drags at your footing.", 90)

    def _process_boss(self):
        if self.boss is None:
            return
        if self.boss.pending_spawn:
            for monster in list(self.boss.pending_spawn):
                self.monsters.add(monster)
            self.boss.pending_spawn = []
            self._flash("Vale calls deserters down from the watch road.")
        if self.boss.pending_command_shout:
            self.boss.pending_command_shout = False
            self.boss.release_command_shout([self.player], self.manager)
        while self.boss.pending_flood_pulses > 0:
            self.boss.pending_flood_pulses -= 1
            distance = math.hypot(
                self.player.rect.centerx - self.boss.rect.centerx,
                self.player.rect.centery - self.boss.rect.centery,
            )
            if distance < 560:
                try:
                    self.player.take_damage(14, "Physical", attacker=self.boss, manager=self.manager)
                    self.player.apply_status("Slow", 125, 0)
                except Exception:
                    self.player.current_hp = max(1, self.player.current_hp - 14)
                self.player.rect.y += 42
            self._flash("Vale releases the floodgate chain!", 120)
            try:
                self.manager.vfx.create_shockwave(self.boss.rect.centerx, self.boss.rect.bottom, color=(86, 151, 166), max_radius=210)
            except Exception:
                pass
        if not self.boss.is_dead:
            return
        state = ford_state(self.manager)
        if state.get("boss_defeated"):
            return
        state["boss_defeated"] = True
        state["boss_unlocked"] = False
        state["quest_stage"] = 7
        if not state.get("boss_reward_claimed"):
            self.manager.gold += 125
            self.manager.reputation = int(getattr(self.manager, "reputation", 0)) + 7
            self.manager.inventory["Vale's Broken Signet"] = int(self.manager.inventory.get("Vale's Broken Signet", 0)) + 1
            self.manager.inventory["Wax Seal"] = int(self.manager.inventory.get("Wax Seal", 0)) + 1
            state["boss_reward_claimed"] = True
        try:
            self.manager.record_tier0_event("boss", "greywash_deserter_captain")
            self.manager.record_tier0_event("flag", "greywash_captain_defeated")
            self.manager.record_deed("greywash_captain", "defeated Captain Garran Vale and reopened Greywash Ford")
        except Exception:
            pass
        self._flash("Captain Garran Vale defeated. Report to Oswin Pike.", 420)

    def update(self):
        if self.dialogue_active or self.manager.paused:
            if self.feedback_timer > 0:
                self.feedback_timer -= 1
            return
        living = [monster for monster in self.monsters if not monster.is_dead]
        self._update_gameplay([self.player] + living)
        self._count_deserter_deaths()
        self._transfer_loot()
        self._apply_current()
        self._process_boss()

        if self.player.is_dead:
            self.player.is_dead = False
            self.player.current_hp = max(1, int(self.player.max_hp * 0.3))
            self.manager.pending_local_area = "greywash_ford"
            self.manager.pending_world_location = "greywash_ford"
            self.manager.greywash_entry = "muckford"
            self.next_state = "regional_staging"
            return
        if self.player.rect.colliderect(self.arena.muckford_exit):
            self.manager.city_spawn_point = "greywash_gate"
            self.next_state = "muckford_city"
            return
        if self.player.rect.colliderect(self.arena.whisper_exit):
            self.manager.pending_local_area = "whisper_marsh"
            self.manager.pending_world_location = "whisper_marsh"
            self.manager.marsh_return_state = "greywash_ford"
            self.next_state = "forest_excursion"
            return
        if self.player.rect.colliderect(self.arena.kingsreach_exit):
            if ford_state(self.manager).get("completed"):
                self.manager.pending_local_area = None
                self.manager.pending_world_location = "kingsreach_toll"
                self.manager.greywash_entry = "kingsreach"
                self.next_state = "regional_staging"
            else:
                self.player.rect.left = 48
                self._flash("The western causeway remains controlled by Captain Garran Vale.", 140)
            return
        if self.feedback_timer > 0:
            self.feedback_timer -= 1
        if self.warning_timer > 0:
            self.warning_timer -= 1

    def _nearest_prompt(self):
        for npc in self.ford_npcs:
            if self._near(npc.rect, 76):
                return npc.rect, f"Talk to {npc.name}"
        state = ford_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        if stage == 1:
            for marker in self.arena.survey_markers:
                if not marker.complete and self._near(marker.rect, 78):
                    return marker.rect, marker.label
        if stage == 3 and self._near(self.arena.bridge_rect, 110):
            return self.arena.bridge_rect, f"Repair bridge: {_cost_text(BRIDGE_COST)}"
        if stage == 4 and self.caravan is not None and self._near(self.caravan.rect, 100):
            return self.caravan.rect, "Advance escorted caravan"
        if stage == 5 and self._near(self.arena.watchtower.rect, 120):
            return self.arena.watchtower.rect, "Search abandoned watchtower"
        anchor = self._nearest_fishing_anchor()
        if anchor is not None:
            return pygame.Rect(anchor.x - 16, anchor.y - 16, 32, 32), "Fish at Greywash Ford"
        for node in self.arena.resources:
            if not node.harvested and self._near(node.rect, 70):
                return node.rect, f"Gather {node.resource_name}"
        return None

    def _draw_dialogue(self, screen):
        # Yhtenäinen Muckford-tyylinen dialogi (puhuja esiin + nimikilpi)
        from systems.area_dialogue import draw_area_dialogue
        if draw_area_dialogue(self, screen):
            return
        if not self.dialogue_active or not self.dialogue_pages:
            return
        panel = pygame.Rect(165, SCREEN_HEIGHT - 260, SCREEN_WIDTH - 330, 205)
        overlay = pygame.Surface(panel.size, pygame.SRCALPHA)
        overlay.fill((22, 24, 23, 242))
        screen.blit(overlay, panel.topleft)
        pygame.draw.rect(screen, (170, 147, 88), panel, 3, border_radius=9)
        draw_text(self.dialogue_name, font_main, GOLD_COLOR, screen, panel.x + 24, panel.y + 18)
        y = panel.y + 60
        for line in self._wrap(self.dialogue_pages[self.dialogue_index], font_main, panel.w - 48)[:4]:
            draw_text(line, font_main, WHITE, screen, panel.x + 24, y)
            y += 29
        draw_text("[E / Enter] continue    [Esc] close", font_small, GRAY, screen, panel.right - 355, panel.bottom - 27)

    def draw(self, screen):
        living = [monster for monster in self.monsters if not monster.is_dead]
        self._draw_gameplay(screen, [self.player] + living)
        prompt = None if self.dialogue_active else self._nearest_prompt()
        if prompt:
            rect, label = prompt
            try:
                self.manager._draw_floating_prompt(screen, rect.centerx, rect.top - 17, "E", (self.camera_x, self.camera_y), label)
            except Exception:
                pass
        state = ford_state(self.manager)
        flood = self.arena.flood_strength()
        draw_text("GREYWASH FORD — OPEN RISK Lv 5-7", font_small, WHITE, screen, 34, 32)
        draw_text(f"CROSSING: {ford_objective(self.manager)}", font_small, (223, 199, 133), screen, 34, 58)
        draw_text(
            f"Threats: {len(living)}   Lanes: {len(set(state.get('surveyed_lanes', ())))}/3   "
            f"Deserters: {int(state.get('deserters_defeated', 0))}/6   "
            f"Bridge: {'READY' if state.get('bridge_repaired') else 'BROKEN'}",
            font_small,
            GRAY,
            screen,
            34,
            84,
        )
        draw_text(
            f"Current: {'STORM FLOOD' if flood == 3 else 'RAIN-SWOLLEN' if flood == 2 else 'NORMAL'}   "
            "East: Muckford   South-east: Whisper Marsh   West: Kingsreach Toll",
            font_small,
            (157, 202, 207),
            screen,
            34,
            108,
        )
        if self.warning_timer > 0:
            surface = font_main.render(self.warning, True, (239, 157, 88))
            screen.blit(surface, (SCREEN_WIDTH // 2 - surface.get_width() // 2, 138))
        if self.feedback_timer > 0:
            surface = font_main.render(self.feedback, True, GOLD_COLOR)
            screen.blit(surface, (SCREEN_WIDTH // 2 - surface.get_width() // 2, 172))
        self._draw_dialogue(screen)
