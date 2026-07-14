"""Playable Muckford Warrens beneath the Tier 0 city.

The area is deliberately code-rendered so its map, NPCs, quests, collision,
persistence and boss mechanics can be tuned before final painted assets exist.
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
from ui_kit import draw_text, font_main, font_small
from units.muckford_warrens_monsters import (
    RatRider,
    SewerRatSwarm,
    VioletEyedRat,
    WarrensRatKing,
    WasteGnawer,
)
from units.villager import Villager
from vfx import VFXManager


WARRENS_WIDTH = 3600
WARRENS_HEIGHT = 2400
WARRENS_SEED = 91377
TRACE_COUNT = 4
CACHE_COUNT = 4
NEST_COUNT = 4
RATCATCHER_COUNT = 3

WARRENS_OBJECTIVES = {
    0: "Speak with Hamo or Old Rinna Net at the cellar hatch.",
    1: "Trace the four violet-eyed rat trails through the old sewers.",
    2: "Recover the four stolen Muckford food caches.",
    3: "Destroy the four Vortex-waste nests.",
    4: "Find and rescue the three missing Muckford Ratcatchers.",
    5: "Enter the Royal Cistern and defeat the Rat King.",
    6: "Report the Rat King's death to Hamo or Old Rinna Net.",
    7: "The Warrens are secured. Rat raids against Muckford have ended.",
}

RATCATCHERS = (
    ("ratcatcher_tessa", "Tessa Trapwire", "Human", 1480, 430),
    ("ratcatcher_brin", "Brin Sootsnare", "Goblin", 2220, 1830),
    ("ratcatcher_dorrik", "Dorrik Two-Nails", "Dwarf", 2780, 690),
)


def _safe_sound(name: str) -> None:
    try:
        sound_system.play_sound(name)
    except Exception:
        pass


def warrens_state(manager) -> dict:
    global_data = manager.npc_state.setdefault("global", {})
    state = global_data.setdefault("muckford_warrens", {})
    state.setdefault("visits", 0)
    state.setdefault("quest_stage", 0)
    state.setdefault("traced_signs", [])
    state.setdefault("recovered_caches", [])
    state.setdefault("destroyed_nests", [])
    state.setdefault("rescued_ratcatchers", [])
    state.setdefault("boss_unlocked", False)
    state.setdefault("boss_defeated", False)
    state.setdefault("boss_reward_claimed", False)
    state.setdefault("report_reward_claimed", False)
    state.setdefault("city_raids_ended", False)
    state.setdefault("completed", False)
    state.setdefault("waste_exposure", 0)
    state.setdefault("deep_drain_open", False)
    return state


def sync_warrens_story(manager) -> bool:
    state = warrens_state(manager)
    changed = False
    while True:
        stage = int(state.get("quest_stage", 0))
        if stage == 1 and len(set(state.get("traced_signs", ()))) >= TRACE_COUNT:
            state["quest_stage"] = 2
        elif stage == 2 and len(set(state.get("recovered_caches", ()))) >= CACHE_COUNT:
            state["quest_stage"] = 3
        elif stage == 3 and len(set(state.get("destroyed_nests", ()))) >= NEST_COUNT:
            state["quest_stage"] = 4
            state["deep_drain_open"] = True
        elif stage == 4 and len(set(state.get("rescued_ratcatchers", ()))) >= RATCATCHER_COUNT:
            state["quest_stage"] = 5
            state["boss_unlocked"] = True
        elif state.get("boss_defeated") and stage < 6:
            state["quest_stage"] = 6
            state["city_raids_ended"] = True
        elif state.get("completed") and stage < 7:
            state["quest_stage"] = 7
        else:
            break
        changed = True
    return changed


def warrens_objective(manager) -> str:
    sync_warrens_story(manager)
    stage = int(warrens_state(manager).get("quest_stage", 0))
    return WARRENS_OBJECTIVES.get(stage, WARRENS_OBJECTIVES[7])


class RectObstacle:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.blocks_projectiles = True
        self.is_structure = True
        self.name = "Sewer Wall"


class WarrensProp(Prop):
    def __init__(self, x: int, y: int, width: int, height: int, style: str, blocking=False):
        super().__init__(x, y, width, height, color=(0, 0, 0))
        self.style = str(style)
        self.image_pos = (x, y)
        self.is_structure = bool(blocking)
        self.blocks_projectiles = bool(blocking)
        self.has_shadow = style not in {"bridge", "pipe", "grate", "water_marker"}
        self._redraw()

    def _redraw(self):
        w, h = self.rect.size
        image = pygame.Surface((w, h), pygame.SRCALPHA)
        if self.style == "brick_wall":
            image.fill((47, 43, 42))
            for y in range(0, h, 28):
                offset = 20 if (y // 28) % 2 else 0
                for x in range(-offset, w, 40):
                    pygame.draw.rect(image, (67, 61, 58), (x + 2, y + 2, 36, 23), 2)
            pygame.draw.line(image, (26, 24, 24), (0, h - 5), (w, h - 5), 6)
        elif self.style == "pipe":
            pygame.draw.rect(image, (73, 73, 68), (0, h // 2 - 9, w, 18), border_radius=8)
            pygame.draw.line(image, (126, 118, 98), (3, h // 2 - 4), (w - 3, h // 2 - 4), 3)
            for x in range(18, w, 65):
                pygame.draw.rect(image, (47, 47, 45), (x, h // 2 - 14, 10, 28), 3)
        elif self.style == "bridge":
            pygame.draw.rect(image, (72, 61, 50), (0, 5, w, h - 10), border_radius=5)
            for x in range(4, w, 24):
                pygame.draw.rect(image, (119, 84, 48), (x, 8, 18, h - 16), border_radius=2)
                pygame.draw.line(image, (166, 123, 72), (x + 3, 12), (x + 14, 12), 2)
            pygame.draw.line(image, (48, 38, 32), (0, 7), (w, 7), 4)
            pygame.draw.line(image, (48, 38, 32), (0, h - 7), (w, h - 7), 4)
        elif self.style == "crate":
            pygame.draw.rect(image, (90, 61, 38), (4, 5, w - 8, h - 10), border_radius=4)
            pygame.draw.rect(image, (143, 101, 58), (4, 5, w - 8, h - 10), 4, border_radius=4)
            pygame.draw.line(image, (60, 43, 31), (10, 10), (w - 10, h - 10), 6)
            pygame.draw.line(image, (60, 43, 31), (w - 10, 10), (10, h - 10), 6)
        elif self.style == "bar_gate":
            for x in range(5, w, 14):
                pygame.draw.rect(image, (87, 82, 76), (x, 0, 7, h))
                pygame.draw.line(image, (139, 129, 111), (x + 2, 0), (x + 2, h), 2)
            for y in (20, h - 26):
                pygame.draw.rect(image, (55, 52, 49), (0, y, w, 12))
        elif self.style == "throne":
            pygame.draw.ellipse(image, (45, 36, 38), (5, h - 32, w - 10, 28))
            pygame.draw.rect(image, (84, 64, 54), (18, 32, w - 36, h - 54), border_radius=9)
            pygame.draw.polygon(image, (130, 94, 45), [(15, 38), (31, 4), (48, 30), (w // 2, 0), (w - 48, 30), (w - 31, 4), (w - 15, 38)])
            for x in range(28, w - 20, 24):
                pygame.draw.circle(image, (151, 65, 167), (x, 57), 5)
        elif self.style == "drain":
            pygame.draw.ellipse(image, (40, 38, 37), (2, 2, w - 4, h - 4))
            pygame.draw.ellipse(image, (102, 96, 85), (5, 5, w - 10, h - 10), 5)
            for x in range(16, w - 10, 18):
                pygame.draw.line(image, (78, 74, 68), (x, 9), (x, h - 9), 5)
        self.image = image


class CitySewerHatch(Prop):
    """Visible Muckford-side entrance added beside Hamo at runtime."""

    def __init__(self, x: int, y: int, cleared=False):
        super().__init__(x, y, 104, 72, color=(0, 0, 0))
        self.rect = pygame.Rect(x + 7, y + 32, 90, 34)
        self.image_pos = (x, y)
        self.has_shadow = False
        self.blocks_projectiles = False
        self.is_structure = False
        self.cleared = bool(cleared)
        self._redraw()

    def _redraw(self):
        image = pygame.Surface((104, 72), pygame.SRCALPHA)
        pygame.draw.ellipse(image, (43, 39, 37), (3, 22, 98, 43))
        pygame.draw.ellipse(image, (104, 95, 79), (7, 18, 90, 43), 5)
        for x in range(20, 91, 15):
            pygame.draw.line(image, (78, 72, 64), (x, 25), (x, 56), 5)
        color = (103, 178, 118) if self.cleared else (168, 86, 191)
        pygame.draw.circle(image, color, (86, 18), 6)
        self.image = image


class TrailMark(Prop):
    def __init__(self, mark_id: str, x: int, y: int, traced=False):
        super().__init__(x, y, 72, 62, color=(0, 0, 0))
        self.mark_id = str(mark_id)
        self.traced = bool(traced)
        self.rect = pygame.Rect(x + 8, y + 28, 56, 28)
        self.image_pos = (x, y)
        self.has_shadow = False
        self.blocks_projectiles = False
        self.is_structure = False
        self._redraw()

    def _redraw(self):
        image = pygame.Surface((72, 62), pygame.SRCALPHA)
        if self.traced:
            pygame.draw.line(image, (84, 130, 94), (11, 45), (61, 45), 4)
            pygame.draw.circle(image, (84, 130, 94), (36, 35), 9, 3)
        else:
            for x, y, angle in ((16, 42, -1), (31, 30, 1), (47, 44, -1), (57, 25, 1)):
                pygame.draw.ellipse(image, (173, 79, 202), (x, y, 11, 7))
                pygame.draw.circle(image, (219, 127, 234), (x + 6, y + 3), 2)
        self.image = image


class FoodCache(Prop):
    def __init__(self, cache_id: str, x: int, y: int, recovered=False):
        super().__init__(x, y, 98, 82, color=(0, 0, 0))
        self.cache_id = str(cache_id)
        self.recovered = bool(recovered)
        self.rect = pygame.Rect(x + 8, y + 39, 82, 36)
        self.image_pos = (x, y)
        self.blocks_projectiles = False
        self.is_structure = False
        self._redraw()

    def _redraw(self):
        image = pygame.Surface((98, 82), pygame.SRCALPHA)
        if self.recovered:
            pygame.draw.rect(image, (65, 52, 40), (8, 56, 82, 12), border_radius=4)
            pygame.draw.line(image, (121, 91, 53), (14, 57), (84, 64), 3)
        else:
            pygame.draw.rect(image, (93, 64, 39), (10, 25, 78, 48), border_radius=4)
            pygame.draw.rect(image, (152, 107, 59), (10, 25, 78, 48), 4, border_radius=4)
            for x in (23, 45, 67):
                pygame.draw.ellipse(image, (186, 153, 78), (x, 12, 23, 33))
                pygame.draw.line(image, (113, 82, 43), (x + 5, 17), (x + 18, 36), 3)
            pygame.draw.circle(image, (184, 80, 204), (81, 27), 4)
        self.image = image


class WasteNest(Prop):
    def __init__(self, nest_id: str, x: int, y: int, destroyed=False):
        super().__init__(x, y, 104, 96, color=(0, 0, 0))
        self.nest_id = str(nest_id)
        self.destroyed = bool(destroyed)
        self.rect = pygame.Rect(x + 8, y + 48, 88, 38)
        self.image_pos = (x, y)
        self.blocks_projectiles = False
        self.is_structure = False
        self.pulse = random.randint(0, 120)
        self._redraw()

    def _redraw(self):
        image = pygame.Surface((104, 96), pygame.SRCALPHA)
        if self.destroyed:
            pygame.draw.ellipse(image, (73, 50, 67, 130), (7, 70, 90, 17))
            pygame.draw.line(image, (134, 69, 151), (18, 68), (87, 83), 3)
        else:
            pygame.draw.ellipse(image, (71, 49, 66), (5, 44, 94, 42))
            pygame.draw.ellipse(image, (114, 56, 127), (18, 27, 68, 50))
            for x, y, r in ((29, 41, 8), (48, 28, 10), (68, 45, 9), (53, 58, 7)):
                pygame.draw.circle(image, (154, 70, 174), (x, y), r)
                pygame.draw.circle(image, (217, 113, 228), (x - 2, y - 2), max(2, r - 5))
            for x in (18, 39, 61, 83):
                pygame.draw.line(image, (56, 45, 50), (52, 62), (x, 91), 4)
        self.image = image

    def update(self, *args, **kwargs):
        self.pulse = (self.pulse + 1) % 120


class MuckfordWarrensArena:
    def __init__(self, manager):
        self.manager = manager
        self.width = WARRENS_WIDTH
        self.height = WARRENS_HEIGHT
        self.props: List[object] = []
        self.floor_props: List[object] = []
        self.obstacles: List[object] = []
        self.trail_marks: List[TrailMark] = []
        self.food_caches: List[FoodCache] = []
        self.waste_nests: List[WasteNest] = []
        self.bridges: List[pygame.Rect] = []
        self.tainted_channels: List[pygame.Rect] = []
        self.vfx = VFXManager()
        self.rng = random.Random(WARRENS_SEED)
        self.floor_image = pygame.Surface((self.width, self.height))
        self.flow_offset = 0
        self.fumes = []
        self.boss_gate: Optional[WarrensProp] = None
        self.city_exit = pygame.Rect(0, 300, 74, 500)
        self.low_fields_exit = pygame.Rect(0, self.height - 680, 74, 520)
        self.royal_cistern = pygame.Rect(2980, 230, 520, 1900)
        self._generate_floor()
        self._build_level()
        self.refresh_persistent(manager)

    def _generate_floor(self):
        self.floor_image.fill((38, 35, 35))
        for _ in range(1900):
            x = self.rng.randrange(self.width)
            y = self.rng.randrange(self.height)
            shade = self.rng.randint(-7, 11)
            pygame.draw.circle(
                self.floor_image,
                (38 + shade, 35 + shade, 35 + shade),
                (x, y),
                self.rng.randint(5, 31),
            )
        # Old cellar lanes and brick service roads.
        pygame.draw.line(self.floor_image, (59, 52, 48), (90, 560), (3370, 560), 150)
        pygame.draw.line(self.floor_image, (56, 49, 46), (180, 1870), (3290, 1870), 170)
        pygame.draw.line(self.floor_image, (53, 47, 45), (820, 560), (820, 1900), 135)
        pygame.draw.line(self.floor_image, (53, 47, 45), (1760, 520), (1760, 1930), 135)
        pygame.draw.line(self.floor_image, (53, 47, 45), (2660, 540), (2660, 1910), 135)
        # Sewer channels: movement is allowed, but wading applies danger.
        channels = (
            pygame.Rect(470, 1060, 2970, 250),
            pygame.Rect(1510, 250, 260, 1880),
            pygame.Rect(2470, 300, 250, 1830),
        )
        self.tainted_channels = [pygame.Rect(rect) for rect in channels]
        for rect in channels:
            pygame.draw.rect(self.floor_image, (34, 61, 54), rect, border_radius=16)
            pygame.draw.rect(self.floor_image, (62, 79, 65), rect, 9, border_radius=16)
            pygame.draw.line(self.floor_image, (93, 102, 76), rect.topleft, rect.topright, 4)
            pygame.draw.line(self.floor_image, (25, 38, 36), rect.bottomleft, rect.bottomright, 6)
        pygame.draw.ellipse(self.floor_image, (47, 39, 42), self.royal_cistern)
        pygame.draw.ellipse(self.floor_image, (83, 57, 86), self.royal_cistern, 14)

    def _add(self, prop, blocking=False):
        self.props.append(prop)
        if blocking or getattr(prop, "is_structure", False):
            self.obstacles.append(prop)

    def _build_level(self):
        w, h = self.width, self.height
        self.obstacles.extend(
            [
                RectObstacle((0, -40, w, 40)),
                RectObstacle((0, h, w, 40)),
                RectObstacle((-40, 0, 40, h)),
                RectObstacle((w, 0, 40, h)),
            ]
        )
        wall_specs = (
            (520, 70, 130, 700), (520, 1470, 130, 830),
            (1120, 70, 130, 560), (1120, 1550, 130, 750),
            (2020, 70, 140, 660), (2020, 1510, 140, 790),
            (2890, 70, 130, 720), (2890, 1540, 130, 760),
        )
        for spec in wall_specs:
            self._add(WarrensProp(*spec, "brick_wall", blocking=True), blocking=True)
        for x, y, length in (
            (260, 330, 420), (900, 850, 480), (1910, 350, 430),
            (2250, 2060, 510), (2830, 920, 480),
        ):
            self.props.append(WarrensProp(x, y, length, 44, "pipe", blocking=False))
        bridge_specs = (
            (710, 1020, 180, 330), (1690, 980, 190, 410),
            (2580, 990, 190, 390), (3180, 1020, 190, 330),
        )
        for spec in bridge_specs:
            bridge = WarrensProp(*spec, "bridge", blocking=False)
            self.bridges.append(pygame.Rect(spec))
            self.props.append(bridge)
        for x, y in ((430, 470), (970, 1770), (1870, 520), (2320, 1770), (2780, 520)):
            self._add(WarrensProp(x, y, 115, 85, "crate", blocking=True), blocking=True)
        self.city_drain = WarrensProp(105, 430, 130, 110, "drain", blocking=False)
        self.low_fields_drain = WarrensProp(105, self.height - 520, 130, 110, "drain", blocking=False)
        self.props.extend((self.city_drain, self.low_fields_drain))
        self.throne = WarrensProp(3240, 1050, 190, 220, "throne", blocking=True)
        self._add(self.throne, blocking=True)

        state = warrens_state(self.manager)
        traced = set(state.get("traced_signs", ()))
        for mark_id, x, y in (
            ("trail_1", 780, 760), ("trail_2", 1340, 1710),
            ("trail_3", 2140, 760), ("trail_4", 2760, 1750),
        ):
            mark = TrailMark(mark_id, x, y, mark_id in traced)
            self.trail_marks.append(mark)
            self.props.append(mark)

        recovered = set(state.get("recovered_caches", ()))
        for cache_id, x, y in (
            ("cache_1", 930, 390), ("cache_2", 1430, 1950),
            ("cache_3", 2240, 420), ("cache_4", 2750, 1940),
        ):
            cache = FoodCache(cache_id, x, y, cache_id in recovered)
            self.food_caches.append(cache)
            self.props.append(cache)

        destroyed = set(state.get("destroyed_nests", ()))
        for nest_id, x, y in (
            ("nest_1", 1260, 750), ("nest_2", 1880, 1780),
            ("nest_3", 2350, 760), ("nest_4", 2810, 1510),
        ):
            nest = WasteNest(nest_id, x, y, nest_id in destroyed)
            self.waste_nests.append(nest)
            self.props.append(nest)

        self.set_boss_gate(int(state.get("quest_stage", 0)) < 5 and not state.get("boss_defeated"))

    def set_boss_gate(self, active: bool):
        if active and self.boss_gate is None:
            self.boss_gate = WarrensProp(2960, 650, 66, 1160, "bar_gate", blocking=True)
            self._add(self.boss_gate, blocking=True)
        elif not active and self.boss_gate is not None:
            if self.boss_gate in self.props:
                self.props.remove(self.boss_gate)
            if self.boss_gate in self.obstacles:
                self.obstacles.remove(self.boss_gate)
            self.boss_gate = None

    def refresh_persistent(self, manager):
        state = warrens_state(manager)
        traced = set(state.get("traced_signs", ()))
        for mark in self.trail_marks:
            mark.traced = mark.mark_id in traced
            mark._redraw()
        recovered = set(state.get("recovered_caches", ()))
        for cache in self.food_caches:
            cache.recovered = cache.cache_id in recovered
            cache._redraw()
        destroyed = set(state.get("destroyed_nests", ()))
        for nest in self.waste_nests:
            nest.destroyed = nest.nest_id in destroyed
            nest._redraw()
        self.set_boss_gate(int(state.get("quest_stage", 0)) < 5 and not state.get("boss_defeated"))

    def player_is_wading(self, point: Tuple[int, int]) -> bool:
        if any(bridge.collidepoint(point) for bridge in self.bridges):
            return False
        return any(channel.collidepoint(point) for channel in self.tainted_channels)

    def update(self, manager=None):
        self.flow_offset = (self.flow_offset + 1) % 44
        self.vfx.update(manager)
        for prop in self.props:
            if hasattr(prop, "update"):
                try:
                    prop.update(manager=manager)
                except TypeError:
                    prop.update()
        if random.random() < 0.12:
            self.fumes.append(
                {
                    "x": random.randint(650, self.width - 180),
                    "y": random.choice((1070, 1210, 1540, 1840)),
                    "life": random.randint(70, 160),
                    "size": random.randint(4, 10),
                }
            )
        for fume in self.fumes:
            fume["life"] -= 1
            fume["y"] -= 0.18
        self.fumes = [fume for fume in self.fumes if fume["life"] > 0]

    def draw_background(self, screen, offset=(0, 0)):
        screen.blit(self.floor_image, (-int(offset[0]), -int(offset[1])))

    def draw_foreground(self, screen, offset=(0, 0)):
        ox, oy = int(offset[0]), int(offset[1])
        for channel in self.tainted_channels:
            visible = channel.move(-ox, -oy)
            clipped = visible.clip(screen.get_rect())
            if clipped.w <= 0 or clipped.h <= 0:
                continue
            horizontal = channel.w > channel.h
            if horizontal:
                for x in range(channel.left - self.flow_offset, channel.right, 44):
                    sx = x - ox
                    sy = channel.centery - oy
                    pygame.draw.line(screen, (66, 101, 82), (sx, sy - 34), (sx + 20, sy - 29), 3)
                    pygame.draw.line(screen, (39, 72, 62), (sx + 8, sy + 37), (sx + 30, sy + 31), 2)
            else:
                for y in range(channel.top - self.flow_offset, channel.bottom, 44):
                    sx = channel.centerx - ox
                    sy = y - oy
                    pygame.draw.line(screen, (66, 101, 82), (sx - 33, sy), (sx - 27, sy + 20), 3)
                    pygame.draw.line(screen, (39, 72, 62), (sx + 34, sy + 8), (sx + 28, sy + 30), 2)
        for fume in self.fumes:
            x, y = int(fume["x"] - ox), int(fume["y"] - oy)
            if -20 < x < screen.get_width() + 20 and -20 < y < screen.get_height() + 20:
                pygame.draw.circle(screen, (137, 67, 151), (x, y), fume["size"], 2)
        self.vfx.draw_top(screen, offset)


class MuckfordWarrensMenu(GameplayScreen):
    def __init__(self, manager):
        super().__init__(manager)
        self.arena = MuckfordWarrensArena(manager)
        self.monsters = pygame.sprite.Group()
        self.warrens_npcs: List[Villager] = []
        self.dynamic_props: List[object] = []
        self.boss: Optional[WarrensRatKing] = None
        self.feedback = ""
        self.feedback_timer = 0
        self.warning = ""
        self.warning_timer = 0
        self.dialogue_active = False
        self.dialogue_name = ""
        self.dialogue_pages: List[str] = []
        self.dialogue_index = 0
        self.dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.wade_tick = 0
        self.boss_wave_timer = 0

    def on_enter(self):
        super().on_enter()
        self.manager.current_arena = self.arena
        self.manager.current_map_vfx = self.arena.vfx
        self.player = self.manager.player_character
        entry = getattr(self.manager, "warrens_entry", None) or "muckford"
        self.manager.warrens_entry = None
        if entry == "low_fields":
            self.player.rect.center = (190, self.arena.height - 410)
            self.player.facing_right = True
        else:
            self.player.rect.center = (190, 570)
            self.player.facing_right = True
        self.player.is_dead = False
        self.player.current_hp = max(1, self.player.current_hp)
        state = warrens_state(self.manager)
        state["visits"] = int(state.get("visits", 0)) + 1
        sync_warrens_story(self.manager)
        self.arena.refresh_persistent(self.manager)
        self.monsters.empty()
        self._spawn_population()
        self._refresh_npcs()
        self._spawn_boss_if_needed()
        self._update_camera()
        try:
            advice = self.manager.get_tier0_area_advice("muckford_warrens")
            self.warning = advice.get("warning", "Recommended Lv 4-6")
            self.warning_timer = 420
        except Exception:
            self.warning = "OPEN RISK — recommended Lv 4-6"
            self.warning_timer = 420
        try:
            from systems.world_progression import mark_location_visited
            mark_location_visited(self.manager, "muckford_warrens", set_current=True)
        except Exception:
            pass
        try:
            self.manager.record_tier0_event("visit", "muckford_warrens")
            self.manager.record_tier0_event("risk_seen", "muckford_warrens")
        except Exception:
            pass
        _safe_sound("click")

    @staticmethod
    def _npc(name: str, race: str, x: int, y: int, role: str):
        npc = Villager(name, race, x, y, team_color=GREEN)
        npc.ai_controller = None
        npc.name = str(name)
        npc.warrens_role = str(role)
        npc.animation_state = "idle"
        return npc

    def _refresh_npcs(self):
        for prop in list(self.dynamic_props):
            if prop in self.arena.props:
                self.arena.props.remove(prop)
        self.dynamic_props = []
        self.warrens_npcs = []
        state = warrens_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        self.warrens_npcs.append(self._npc("Hamo", "Goblin", 290, 520, "hamo"))
        self.warrens_npcs.append(self._npc("Old Rinna Net", "Human", 390, 650, "rinna"))
        rescued = set(state.get("rescued_ratcatchers", ()))
        if stage == 4:
            for ratcatcher_id, name, race, x, y in RATCATCHERS:
                if ratcatcher_id not in rescued:
                    self.warrens_npcs.append(self._npc(name, race, x, y, f"rescue:{ratcatcher_id}"))
        for index, ratcatcher_id in enumerate(sorted(rescued)):
            names = {entry[0]: entry[1] for entry in RATCATCHERS}
            races = {entry[0]: entry[2] for entry in RATCATCHERS}
            self.warrens_npcs.append(
                self._npc(
                    names.get(ratcatcher_id, "Muckford Ratcatcher"),
                    races.get(ratcatcher_id, "Human"),
                    520 + index * 100,
                    700,
                    "rescued",
                )
            )
        self.dynamic_props = list(self.warrens_npcs)
        self.arena.props.extend(self.dynamic_props)

    def _spawn_population(self):
        state = warrens_state(self.manager)
        cleared = bool(state.get("boss_defeated"))
        placements = [
            (SewerRatSwarm, 760, 470), (SewerRatSwarm, 990, 1420),
            (SewerRatSwarm, 1370, 820), (SewerRatSwarm, 1990, 1880),
            (SewerRatSwarm, 2500, 520), (SewerRatSwarm, 2830, 1830),
            (VioletEyedRat, 1100, 410), (VioletEyedRat, 1460, 1670),
            (VioletEyedRat, 1900, 720), (VioletEyedRat, 2260, 1450),
            (VioletEyedRat, 2690, 650), (VioletEyedRat, 2870, 1710),
            (RatRider, 1310, 1930), (RatRider, 2140, 420), (RatRider, 2750, 1420),
            (WasteGnawer, 1600, 870), (WasteGnawer, 2410, 1870), (WasteGnawer, 2800, 430),
        ]
        if cleared:
            placements = placements[::2]
        for index, (monster_class, x, y) in enumerate(placements):
            monster = monster_class(f"{monster_class.SPECIES} {index + 1}", x, y, ENEMY_TEAM)
            self.monsters.add(monster)

    def _spawn_boss_if_needed(self):
        state = warrens_state(self.manager)
        self.boss = None
        if not state.get("boss_unlocked") or state.get("boss_defeated"):
            return
        self.arena.set_boss_gate(False)
        self.boss = WarrensRatKing("The Rat King of Muckford", 3280, 1200, ENEMY_TEAM)
        self.monsters.add(self.boss)
        self._flash("The Rat King rises from the Royal Cistern.", 320)

    def _near(self, rect: pygame.Rect, inflate=76) -> bool:
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
        self.dialogue_active = True
        self.dialogue_name = str(name)
        self.dialogue_pages = [str(page) for page in pages]
        self.dialogue_index = 0
        _safe_sound("click")

    def _start_story(self):
        state = warrens_state(self.manager)
        if int(state.get("quest_stage", 0)) == 0:
            state["quest_stage"] = 1
            try:
                self.manager.record_tier0_event("flag", "muckford_warrens_started")
            except Exception:
                pass
        self._open_dialogue(
            "Hamo",
            (
                "Purple eyes were a warning. Now the rats are moving grain, scrap and Vortex waste like an army with quartermasters.",
                "Old Rinna marked four trails. Trace them first. We need to know where the Rat King is feeding his soldiers.",
                "The hatch is open at any level, Commander. That does not make the Warrens safe. These tunnels are Lv 4-6 work.",
            ),
        )

    def _hamo_dialogue(self):
        state = warrens_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        if stage == 0:
            self._start_story()
            return
        if stage == 1:
            pages = (f"Follow the violet tracks before they wash away. Trails traced: {len(set(state.get('traced_signs', ())))}/{TRACE_COUNT}.",)
        elif stage == 2:
            pages = (f"Those sacks belong above ground. Food caches recovered: {len(set(state.get('recovered_caches', ())))}/{CACHE_COUNT}.",)
        elif stage == 3:
            pages = (f"Burn out the purple nests. Vortex-waste nests destroyed: {len(set(state.get('destroyed_nests', ())))}/{NEST_COUNT}.",)
        elif stage == 4:
            pages = (f"Rinna's Ratcatchers are still alive. Rescued: {len(set(state.get('rescued_ratcatchers', ())))}/{RATCATCHER_COUNT}.",)
        elif stage == 5:
            pages = ("The Royal Cistern gate is open. Kill the Rat King and the surface raids end with him.",)
        elif stage == 6:
            self._complete_report("Hamo")
            return
        else:
            pages = (
                "No more raid schedules, no more purple eyes at the granary. Hamo calls that a profitable peace.",
                "Rat tails still buy coin, but the Warrens no longer decide whether Muckford eats.",
            )
        self._open_dialogue("Hamo", pages)

    def _rinna_dialogue(self):
        state = warrens_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        if stage == 0:
            state["quest_stage"] = 1
            try:
                self.manager.record_tier0_event("flag", "muckford_warrens_started")
            except Exception:
                pass
            pages = (
                "Name's Rinna Net. I trained every ratcatcher fool enough to climb down here twice.",
                "Four violet trails lead away from the cellar. Trace all four, then we take back the food stores one tunnel at a time.",
            )
        elif stage == 1:
            pages = ("Purple prints shine brightest where the sewer brick is dry. Mark every trail before chasing the rats.",)
        elif stage == 2:
            pages = ("Recover the stolen sacks. Muckford loses more people to empty bowls than to rat teeth.",)
        elif stage == 3:
            pages = ("Those waste nests are why the eyes glow. Break all four before searching for my crew.",)
        elif stage == 4:
            pages = ("Tessa, Brin and Dorrik know how to stay alive. Find them before the King moves his guard.",)
        elif stage == 5:
            pages = ("You hear that crown scraping brick? Royal Cistern. End it clean.",)
        elif stage == 6:
            self._complete_report("Old Rinna Net")
            return
        else:
            pages = ("My crew is alive and the city sleeps without raid bells. That is enough glory for one sewer.",)
        self._open_dialogue("Old Rinna Net", pages)

    def _complete_report(self, speaker: str):
        state = warrens_state(self.manager)
        if not state.get("report_reward_claimed"):
            self.manager.gold += 140
            self.manager.reputation = int(getattr(self.manager, "reputation", 0)) + 10
            self.manager.city_storage["Recovered Grain"] = int(self.manager.city_storage.get("Recovered Grain", 0)) + 8
            self.manager.city_storage["Scrap Iron"] = int(self.manager.city_storage.get("Scrap Iron", 0)) + 4
            state["report_reward_claimed"] = True
        state["completed"] = True
        state["city_raids_ended"] = True
        sync_warrens_story(self.manager)
        try:
            self.manager.record_tier0_event("quest", "muckford_warrens_cleared")
            self.manager.record_tier0_event("flag", "muckford_rat_raids_ended")
        except Exception:
            pass
        self._open_dialogue(
            speaker,
            (
                "The Rat King is dead. The Warrens still have teeth, but they no longer have orders.",
                "Muckford receives the recovered grain and scrap. +140 SP, +10 reputation. Rat raids have ended permanently.",
            ),
        )
        self._flash("Muckford Warrens secured. Surface rat raids ended permanently.", 420)

    def _try_npc(self) -> bool:
        for npc in self.warrens_npcs:
            if not self._near(npc.rect, 74):
                continue
            role = getattr(npc, "warrens_role", "")
            if role == "hamo":
                self._hamo_dialogue()
            elif role == "rinna":
                self._rinna_dialogue()
            elif role.startswith("rescue:"):
                ratcatcher_id = role.split(":", 1)[1]
                state = warrens_state(self.manager)
                rescued = state.setdefault("rescued_ratcatchers", [])
                if ratcatcher_id not in rescued:
                    rescued.append(ratcatcher_id)
                    self.manager.reputation = int(getattr(self.manager, "reputation", 0)) + 1
                    self._flash(f"Rescued {npc.name}. +1 reputation")
                    _safe_sound("recruit")
                    if sync_warrens_story(self.manager):
                        self.arena.refresh_persistent(self.manager)
                        self._flash("All Ratcatchers rescued. The Royal Cistern gate opens.", 320)
                        self._spawn_boss_if_needed()
                    self._refresh_npcs()
            else:
                self._open_dialogue(npc.name, ("We mark every side tunnel now. No more disappearing alone into the dark.",))
            return True
        return False

    def _try_trace(self) -> bool:
        state = warrens_state(self.manager)
        if int(state.get("quest_stage", 0)) != 1:
            return False
        for mark in self.arena.trail_marks:
            if mark.traced or not self._near(mark.rect, 74):
                continue
            traced = state.setdefault("traced_signs", [])
            if mark.mark_id not in traced:
                traced.append(mark.mark_id)
            mark.traced = True
            mark._redraw()
            for index in range(2):
                self.monsters.add(
                    VioletEyedRat(
                        f"Trail Guard {len(traced)}-{index + 1}",
                        mark.rect.centerx + index * 70 - 35,
                        mark.rect.centery + 80,
                        ENEMY_TEAM,
                    )
                )
            self._flash(f"Violet trail traced: {len(set(traced))}/{TRACE_COUNT}")
            if sync_warrens_story(self.manager):
                self._flash("The trails converge on Muckford's stolen food stores.", 300)
            return True
        return False

    def _try_cache(self) -> bool:
        state = warrens_state(self.manager)
        if int(state.get("quest_stage", 0)) != 2:
            return False
        for cache in self.arena.food_caches:
            if cache.recovered or not self._near(cache.rect, 78):
                continue
            recovered = state.setdefault("recovered_caches", [])
            if cache.cache_id not in recovered:
                recovered.append(cache.cache_id)
            cache.recovered = True
            cache._redraw()
            self.manager.city_storage["Recovered Grain"] = int(self.manager.city_storage.get("Recovered Grain", 0)) + 2
            self.manager.inventory["Scrap Iron"] = int(self.manager.inventory.get("Scrap Iron", 0)) + 1
            self._flash(f"Food caches recovered: {len(set(recovered))}/{CACHE_COUNT}. +2 city grain, +1 Scrap Iron")
            _safe_sound("recruit")
            if sync_warrens_story(self.manager):
                self._flash("The food stores are safe. Destroy the Vortex-waste nests.", 300)
            return True
        return False

    def _try_nest(self) -> bool:
        state = warrens_state(self.manager)
        if int(state.get("quest_stage", 0)) != 3:
            return False
        for nest in self.arena.waste_nests:
            if nest.destroyed or not self._near(nest.rect, 80):
                continue
            destroyed = state.setdefault("destroyed_nests", [])
            if nest.nest_id not in destroyed:
                destroyed.append(nest.nest_id)
            nest.destroyed = True
            nest._redraw()
            self.manager.inventory["Vortex Residue"] = int(self.manager.inventory.get("Vortex Residue", 0)) + 1
            self.monsters.add(WasteGnawer(f"Nest Gnawer {len(destroyed)}", nest.rect.centerx, nest.rect.centery + 100, ENEMY_TEAM))
            self.monsters.add(SewerRatSwarm(f"Nest Swarm {len(destroyed)}", nest.rect.centerx + 90, nest.rect.centery + 70, ENEMY_TEAM))
            self._flash(f"Waste nests destroyed: {len(set(destroyed))}/{NEST_COUNT}. +1 Vortex Residue")
            _safe_sound("mining_break")
            if sync_warrens_story(self.manager):
                self._flash("Waste nests destroyed. Find Rinna's three Ratcatchers.", 320)
                self.arena.refresh_persistent(self.manager)
                self._refresh_npcs()
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
            if self._try_npc():
                return
            if self._try_trace() or self._try_cache() or self._try_nest():
                return

    def _transfer_loot(self):
        loot = self.manager.round_rewards.get("loot")
        if not loot:
            return
        for name, amount in list(loot.items()):
            self.manager.inventory[name] = int(self.manager.inventory.get(name, 0)) + int(amount)
        self.manager.round_rewards["loot"] = {}

    def _apply_sewer_hazard(self):
        if not self.arena.player_is_wading(self.player.rect.center):
            self.wade_tick = 0
            return
        self.wade_tick += 1
        if self.wade_tick % 45 != 0:
            return
        state = warrens_state(self.manager)
        destroyed = len(set(state.get("destroyed_nests", ())))
        exposure_gain = max(1, 5 - destroyed)
        state["waste_exposure"] = min(100, int(state.get("waste_exposure", 0)) + exposure_gain)
        try:
            self.player.apply_status("Slow", 55, 0)
        except Exception:
            pass
        if int(state.get("waste_exposure", 0)) >= 60 and destroyed < NEST_COUNT:
            try:
                self.player.take_damage(4, "Poison", manager=self.manager)
                self.player.apply_status("Poison", 90, 2)
            except Exception:
                self.player.current_hp = max(1, self.player.current_hp - 4)
            self._flash("Vortex waste burns through the sewer water.", 90)
        elif self.wade_tick % 135 == 0:
            self._flash("Sewer current slows movement. Bridges avoid the waste.", 90)

    def _process_boss(self):
        if self.boss is None:
            return
        if self.boss.pending_spawn:
            for monster in list(self.boss.pending_spawn):
                self.monsters.add(monster)
            self.boss.pending_spawn = []
            self._flash("The Rat King calls another regiment from the tunnels.")
        if self.boss.pending_screech:
            self.boss.pending_screech = False
            self.boss.release_royal_screech([self.player], self.manager)
        while self.boss.pending_waste_wave > 0:
            self.boss.pending_waste_wave -= 1
            distance = math.hypot(
                self.player.rect.centerx - self.boss.rect.centerx,
                self.player.rect.centery - self.boss.rect.centery,
            )
            if distance < 520:
                try:
                    self.player.take_damage(12, "Poison", attacker=self.boss, manager=self.manager)
                    self.player.apply_status("Poison", 120, 3)
                except Exception:
                    self.player.current_hp = max(1, self.player.current_hp - 12)
            self._flash("The Royal Cistern erupts with Vortex-waste water!", 120)
            try:
                self.manager.vfx.create_shockwave(self.boss.rect.centerx, self.boss.rect.bottom, color=(144, 67, 166), max_radius=180)
            except Exception:
                pass
        if not self.boss.is_dead:
            return
        state = warrens_state(self.manager)
        if state.get("boss_defeated"):
            return
        state["boss_defeated"] = True
        state["city_raids_ended"] = True
        state["boss_unlocked"] = False
        state["quest_stage"] = 6
        if not state.get("boss_reward_claimed"):
            self.manager.gold += 100
            self.manager.reputation = int(getattr(self.manager, "reputation", 0)) + 6
            self.manager.inventory["Gnawed Crown"] = int(self.manager.inventory.get("Gnawed Crown", 0)) + 1
            self.manager.inventory["Vortex Residue"] = int(self.manager.inventory.get("Vortex Residue", 0)) + 3
            state["boss_reward_claimed"] = True
        try:
            self.manager.record_tier0_event("boss", "rat_king")
            self.manager.record_tier0_event("flag", "muckford_rat_raids_ended")
        except Exception:
            pass
        try:
            self.manager.record_deed("rat_king", "slew the Rat King beneath Muckford and ended the sewer raids")
        except Exception:
            pass
        try:
            from quest_system import quest_manager
            if quest_manager:
                quest = quest_manager.quests.get("hunt_01")
                if quest:
                    quest.completed = True
                    quest.status = "completed"
        except Exception:
            pass
        self.manager.next_raid_day = 10 ** 9
        self.arena.set_boss_gate(False)
        self._flash("Rat King slain. +100 SP, +6 reputation. Report to Hamo or Rinna.", 420)
        self._refresh_npcs()

    def update(self):
        if self.dialogue_active or self.manager.paused:
            if self.feedback_timer > 0:
                self.feedback_timer -= 1
            return
        living = [monster for monster in self.monsters if not monster.is_dead]
        all_units = [self.player] + living
        self._update_gameplay(all_units)
        self._transfer_loot()
        self._apply_sewer_hazard()
        self._process_boss()

        if self.player.is_dead:
            self.player.is_dead = False
            self.player.current_hp = max(1, int(self.player.max_hp * 0.3))
            self.manager.city_spawn_point = "warrens_hatch"
            self.next_state = "muckford_city"
            return

        if self.player.rect.colliderect(self.arena.city_exit):
            self.manager.match_in_progress = False
            self.manager.city_spawn_point = "warrens_hatch"
            self.next_state = "muckford_city"
            return
        if self.player.rect.colliderect(self.arena.low_fields_exit):
            self.manager.match_in_progress = False
            self.manager.pending_local_area = "low_fields"
            self.manager.pending_world_location = "low_fields"
            self.manager.low_fields_entry = "warrens"
            self.next_state = "regional_staging"
            return

        if self.feedback_timer > 0:
            self.feedback_timer -= 1
        if self.warning_timer > 0:
            self.warning_timer -= 1

    def _nearest_prompt(self):
        for npc in self.warrens_npcs:
            if self._near(npc.rect, 74):
                role = str(getattr(npc, "warrens_role", ""))
                if role.startswith("rescue:"):
                    return npc.rect, f"Rescue {npc.name}"
                return npc.rect, f"Talk to {npc.name}"
        state = warrens_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        if stage == 1:
            for mark in self.arena.trail_marks:
                if not mark.traced and self._near(mark.rect, 74):
                    return mark.rect, "Trace violet-eyed rat trail"
        if stage == 2:
            for cache in self.arena.food_caches:
                if not cache.recovered and self._near(cache.rect, 78):
                    return cache.rect, "Recover stolen food cache"
        if stage == 3:
            for nest in self.arena.waste_nests:
                if not nest.destroyed and self._near(nest.rect, 80):
                    return nest.rect, "Destroy Vortex-waste nest"
        return None

    def _draw_darkness(self, screen):
        self.dark_overlay.fill((5, 4, 8, 218))
        lights = [((self.player.rect.centerx, self.player.rect.centery), 335)]
        for x, y in ((350, 540), (910, 560), (1820, 560), (2690, 560), (3320, 1190)):
            lights.append(((x, y), 150))
        for nest in self.arena.waste_nests:
            if not nest.destroyed:
                lights.append((nest.rect.center, 95))
        if self.boss is not None and not self.boss.is_dead:
            lights.append((self.boss.rect.center, 180 + self.boss.phase * 25))
        for (world_x, world_y), radius in lights:
            x = int(world_x - self.camera_x)
            y = int(world_y - self.camera_y)
            flicker = random.randint(-5, 5)
            for r, alpha in ((radius + flicker, 155), (int(radius * 0.68), 82), (int(radius * 0.38), 28), (54, 0)):
                pygame.draw.circle(self.dark_overlay, (5, 4, 8, alpha), (x, y), max(4, r))
        screen.blit(self.dark_overlay, (0, 0))

    def _draw_dialogue(self, screen):
        # Yhtenäinen Muckford-tyylinen dialogi (puhuja esiin + nimikilpi)
        from systems.area_dialogue import draw_area_dialogue
        if draw_area_dialogue(self, screen):
            return
        if not self.dialogue_active or not self.dialogue_pages:
            return
        panel = pygame.Rect(165, SCREEN_HEIGHT - 260, SCREEN_WIDTH - 330, 205)
        overlay = pygame.Surface(panel.size, pygame.SRCALPHA)
        overlay.fill((20, 17, 22, 244))
        screen.blit(overlay, panel.topleft)
        pygame.draw.rect(screen, (153, 91, 169), panel, 3, border_radius=9)
        draw_text(self.dialogue_name, font_main, GOLD_COLOR, screen, panel.x + 24, panel.y + 18)
        y = panel.y + 60
        page = self.dialogue_pages[self.dialogue_index]
        for line in self._wrap(page, font_main, panel.w - 48)[:4]:
            draw_text(line, font_main, WHITE, screen, panel.x + 24, y)
            y += 29
        draw_text("[E / Enter] continue    [Esc] close", font_small, GRAY, screen, panel.right - 355, panel.bottom - 27)

    def draw(self, screen):
        living = [monster for monster in self.monsters if not monster.is_dead]
        all_units = [self.player] + living
        self._draw_gameplay(screen, all_units)
        self._draw_darkness(screen)
        # HUD piirretään pimeyden PÄÄLLE - muuten HP/mana-pallot ja
        # palkit himmenevät lukukelvottomiksi (pelaajapalaute)
        if getattr(self, "player", None):
            self.player.draw_hud(screen)
        prompt = None if self.dialogue_active else self._nearest_prompt()
        if prompt:
            rect, label = prompt
            try:
                self.manager._draw_floating_prompt(
                    screen,
                    rect.centerx,
                    rect.top - 16,
                    "E",
                    (self.camera_x, self.camera_y),
                    label,
                )
            except Exception:
                pass
        state = warrens_state(self.manager)
        draw_text("MUCKFORD WARRENS — OPEN RISK Lv 4-6", font_small, WHITE, screen, 34, 32)
        draw_text(f"CRISIS: {warrens_objective(self.manager)}", font_small, (219, 184, 121), screen, 34, 58)
        draw_text(
            f"Threats: {len(living)}   Trails: {len(set(state.get('traced_signs', ())))}/4   "
            f"Caches: {len(set(state.get('recovered_caches', ())))}/4   "
            f"Nests: {len(set(state.get('destroyed_nests', ())))}/4",
            font_small,
            GRAY,
            screen,
            34,
            84,
        )
        draw_text(
            "Upper west drain: Muckford   Lower west drain: Low Fields   Sewer water slows and carries Vortex waste.",
            font_small,
            GRAY,
            screen,
            34,
            108,
        )
        if self.warning_timer > 0:
            surface = font_main.render(self.warning, True, (237, 153, 92))
            screen.blit(surface, (SCREEN_WIDTH // 2 - surface.get_width() // 2, 136))
        if self.feedback_timer > 0:
            surface = font_main.render(self.feedback, True, GOLD_COLOR)
            screen.blit(surface, (SCREEN_WIDTH // 2 - surface.get_width() // 2, 170))
        self._draw_dialogue(screen)
