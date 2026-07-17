"""Playable Drowned Chapel ruin east of Whisper Marsh.

The area is open with a level 3-5 danger warning. It uses procedural water and
pygame-drawn placeholder art for the flooded chapel, graveyard, quarantine camp,
quest markers, resources and enemies so gameplay does not wait for painted art.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Sequence, Tuple

import pygame

from assets.tiles.forest_objects import ForestBush, ForestGrass
from assets.tiles.muckford_floors import MuckfordFloor
from assets.tiles.prop import Prop
from menus.gameplay_screen import GameplayScreen
from systems.field_kit import FieldResourceNode
from settings import ENEMY_TEAM, GOLD_COLOR, GRAY, GREEN, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from assets.tiles.water import WaterBody
from ui_kit import draw_text, font_main, font_small
from units.drowned_chapel_monsters import (
    BellDrownedPilgrim,
    BellWraith,
    FloodedAcolyte,
    WaterRisenPilgrim,
)
from units.tier0_monsters import BogTick, DrownedMudling, WhisperMoth
from units.villager import Villager


CHAPEL_WIDTH = 3300
CHAPEL_HEIGHT = 2200
CHAPEL_SEED = 91837
CHAPEL_REWARD_SP = 80
CHAPEL_REWARD_REPUTATION = 7

CHAPEL_OBJECTIVES = {
    0: "Speak with Sister-Medic Rhea Ashford at the quarantine camp.",
    1: "Recover the Saint Lumen medicine chest from the flooded chapel.",
    2: "Rescue the three trapped pilgrims.",
    3: "Collect samples from all three tainted-water sites.",
    4: "Light the three Saint Lumen ward braziers with Sanctified Wax.",
    5: "Silence the Bell-Drowned Pilgrim at the bell tower.",
    6: "Drowned Chapel secured. Return to Rhea or continue exploring.",
}


def _safe_sound(name: str) -> None:
    try:
        sound_system.play_sound(name)
    except Exception:
        pass


def _world_day_key(manager) -> str:
    clock = getattr(manager, "world_clock", None)
    return f"{int(getattr(clock, 'year', 0))}:{int(getattr(clock, 'day', 1))}"


def drowned_chapel_state(manager) -> dict:
    global_data = manager.npc_state.setdefault("global", {})
    state = global_data.setdefault("drowned_chapel", {})
    state.setdefault("visits", 0)
    state.setdefault("quest_stage", 0)
    state.setdefault("medicine_chest_recovered", False)
    state.setdefault("rescued_pilgrims", [])
    state.setdefault("water_samples", [])
    state.setdefault("lit_wards", [])
    state.setdefault("wax_issued", False)
    state.setdefault("boss_unlocked", False)
    state.setdefault("boss_defeated", False)
    state.setdefault("boss_reward_claimed", False)
    state.setdefault("infection", 0.0)
    state.setdefault("completed", False)
    state.setdefault("resource_day", _world_day_key(manager))
    state.setdefault("harvested_nodes", [])
    if state["resource_day"] != _world_day_key(manager):
        state["resource_day"] = _world_day_key(manager)
        state["harvested_nodes"] = []
    return state


def sync_drowned_chapel_story(manager) -> bool:
    state = drowned_chapel_state(manager)
    changed = False
    while True:
        stage = int(state.get("quest_stage", 0))
        if stage == 1 and state.get("medicine_chest_recovered"):
            state["quest_stage"] = 2
        elif stage == 2 and len(set(state.get("rescued_pilgrims", ()))) >= 3:
            state["quest_stage"] = 3
        elif stage == 3 and len(set(state.get("water_samples", ()))) >= 3:
            state["quest_stage"] = 4
            if not state.get("wax_issued"):
                manager.inventory["Sanctified Wax"] = int(manager.inventory.get("Sanctified Wax", 0)) + 3
                state["wax_issued"] = True
        elif stage == 4 and len(set(state.get("lit_wards", ()))) >= 3:
            state["quest_stage"] = 5
            state["boss_unlocked"] = True
        elif state.get("boss_defeated") and stage < 6:
            state["quest_stage"] = 6
            state["completed"] = True
        else:
            break
        changed = True
    return changed


def chapel_objective(manager) -> str:
    sync_drowned_chapel_story(manager)
    stage = int(drowned_chapel_state(manager).get("quest_stage", 0))
    return CHAPEL_OBJECTIVES.get(stage, CHAPEL_OBJECTIVES[6])


class ChapelStone(Prop):
    """Generated chapel wall, grave, tent, brazier or bell-tower landmark."""

    def __init__(self, x: int, y: int, width: int, height: int, style: str, blocking=True):
        super().__init__(x, y, width, height, color=(0, 0, 0))
        self.style = style
        self.image_pos = (x, y)
        self.has_shadow = style not in {"grave", "brazier"}
        self.is_structure = bool(blocking)
        self.blocks_projectiles = bool(blocking)
        self._draw()

    def _draw(self):
        w, h = self.rect.size
        image = pygame.Surface((w, h), pygame.SRCALPHA)
        if self.style == "wall":
            pygame.draw.rect(image, (73, 77, 76), (0, 8, w, h - 8), border_radius=4)
            pygame.draw.rect(image, (116, 118, 109), (0, 8, w, h - 8), 3, border_radius=4)
            for y in range(18, h - 5, 22):
                pygame.draw.line(image, (52, 58, 59), (3, y), (w - 3, y), 2)
                offset = 18 if (y // 22) % 2 else 4
                for x in range(offset, w, 36):
                    pygame.draw.line(image, (52, 58, 59), (x, y - 9), (x, y + 9), 2)
            for x in range(12, w, 44):
                pygame.draw.line(image, (50, 82, 68), (x, h - 8), (x + 7, h - 28), 3)
        elif self.style == "grave":
            pygame.draw.ellipse(image, (46, 50, 47, 120), (5, h - 13, w - 10, 10))
            pygame.draw.rect(image, (86, 91, 87), (w // 2 - 10, 17, 20, h - 25), border_radius=5)
            pygame.draw.arc(image, (128, 131, 120), (w // 2 - 10, 8, 20, 20), math.pi, math.tau, 3)
            pygame.draw.line(image, (57, 72, 62), (w // 2, h - 13), (w // 2 - 12, h - 30), 2)
        elif self.style == "tent":
            pygame.draw.polygon(image, (165, 157, 129), [(5, h - 8), (w // 2, 8), (w - 5, h - 8)])
            pygame.draw.polygon(image, (103, 111, 92), [(w // 2, 8), (w - 5, h - 8), (w // 2 + 8, h - 8)])
            pygame.draw.line(image, (89, 68, 43), (w // 2, 7), (w // 2, h - 5), 4)
            pygame.draw.rect(image, (50, 47, 39), (w // 2 - 10, h - 35, 20, 27))
        elif self.style == "brazier":
            pygame.draw.line(image, (104, 82, 52), (w // 2, h - 5), (w // 2, 28), 5)
            pygame.draw.arc(image, (141, 112, 64), (8, 19, w - 16, 24), 0, math.pi, 4)
            pygame.draw.circle(image, (206, 103, 45), (w // 2, 22), 10)
            pygame.draw.circle(image, (244, 188, 70), (w // 2, 18), 6)
        elif self.style == "tower":
            pygame.draw.rect(image, (69, 74, 74), (12, 20, w - 24, h - 25), border_radius=5)
            pygame.draw.rect(image, (116, 117, 107), (12, 20, w - 24, h - 25), 4, border_radius=5)
            pygame.draw.polygon(image, (55, 63, 67), [(4, 24), (w // 2, 0), (w - 4, 24)])
            pygame.draw.arc(image, (184, 146, 70), (w // 2 - 24, 40, 48, 48), math.pi, math.tau, 7)
            pygame.draw.line(image, (184, 146, 70), (w // 2 - 22, 65), (w // 2 + 22, 65), 6)
            pygame.draw.circle(image, (113, 80, 38), (w // 2, 84), 7)
            for y in range(108, h - 20, 34):
                pygame.draw.line(image, (50, 57, 58), (18, y), (w - 18, y), 2)
        self.image = image


class ChapelMarker(Prop):
    def __init__(self, marker_id: str, x: int, y: int, label: str, style: str, complete=False):
        super().__init__(x, y, 70, 78, color=(0, 0, 0))
        self.marker_id = str(marker_id)
        self.label = str(label)
        self.style = style
        self.complete = bool(complete)
        self.rect = pygame.Rect(x + 10, y + 42, 50, 30)
        self.image_pos = (x, y)
        self.has_shadow = True
        self.blocks_projectiles = False
        self._redraw()

    def _redraw(self):
        image = pygame.Surface((70, 78), pygame.SRCALPHA)
        if self.style == "chest":
            pygame.draw.rect(image, (92, 62, 37), (8, 35, 54, 31), border_radius=5)
            pygame.draw.arc(image, (146, 111, 64), (8, 16, 54, 38), math.pi, math.tau, 5)
            pygame.draw.rect(image, (183, 146, 73), (31, 39, 9, 13))
            pygame.draw.line(image, (210, 208, 178), (17, 52), (54, 52), 3)
        elif self.style == "sample":
            pygame.draw.line(image, (100, 79, 49), (35, 70), (35, 16), 5)
            pygame.draw.circle(image, (66, 121, 127), (35, 50), 15, 3)
            pygame.draw.circle(image, (113, 184, 176), (35, 48), 8)
            pygame.draw.circle(image, (183, 222, 210), (42, 38), 3)
        else:  # ward
            pygame.draw.line(image, (89, 69, 44), (35, 72), (35, 27), 5)
            pygame.draw.arc(image, (150, 118, 65), (10, 21, 50, 27), 0, math.pi, 4)
            flame = (108, 192, 158) if self.complete else (80, 74, 65)
            pygame.draw.circle(image, flame, (35, 20), 11)
            if self.complete:
                pygame.draw.circle(image, (202, 236, 205), (35, 15), 6)
        status = (77, 181, 104) if self.complete else (230, 187, 76)
        pygame.draw.circle(image, status, (10, 10), 8, 3)
        self.image = image


class ChapelResourceNode(FieldResourceNode):
    """Kappelin keräysnode - runko kenttäpakista, tässä vain kappelin
    omat piirtotyylit (lotus, wax) ja harvested_nodes-kirjanpito."""

    SIZE = 50
    DATA = {
        "Medicinal Herb": ("herb", (1, 2)),
        "Grave-Lotus": ("lotus", (1, 2)),
        "Sanctified Wax": ("wax", (1, 1)),
        "River Clay": ("clay", (1, 2)),
    }

    def _paint_lotus(image, s):
        pygame.draw.ellipse(image, (55, 95, 75), (7, 29, 36, 15))
        for angle in range(0, 360, 60):
            rad = math.radians(angle)
            cx = 25 + int(math.cos(rad) * 9)
            cy = 25 + int(math.sin(rad) * 7)
            pygame.draw.ellipse(image, (184, 160, 194), (cx - 6, cy - 4, 12, 8))
        pygame.draw.circle(image, (228, 209, 127), (25, 25), 4)

    def _paint_wax(image, s):
        pygame.draw.rect(image, (209, 194, 137), (15, 17, 20, 29), border_radius=5)
        pygame.draw.line(image, (75, 64, 48), (25, 17), (25, 9), 2)
        pygame.draw.circle(image, (235, 163, 61), (25, 7), 5)

    PAINTERS = {**FieldResourceNode.PAINTERS,
                "lotus": _paint_lotus, "wax": _paint_wax}

    def __init__(self, node_id: str, x: int, y: int, resource_name: str,
                 harvested=False):
        style, amount = self.DATA[resource_name]
        super().__init__(node_id, x, y, resource_name, style, amount,
                         harvested=harvested)

    def _after_harvest(self, manager, amount):
        state = drowned_chapel_state(manager)
        harvested = state.setdefault("harvested_nodes", [])
        if self.node_id not in harvested:
            harvested.append(self.node_id)


class DrownedChapelArena:
    def __init__(self, manager):
        self.manager = manager
        self.width = CHAPEL_WIDTH
        self.height = CHAPEL_HEIGHT
        self.floor = MuckfordFloor(self.width, self.height)
        self.props: List[object] = []
        self.land_obstacles: List[object] = []
        self.water_obstacles: List[object] = []
        self.obstacles: List[object] = []
        self.resources: List[ChapelResourceNode] = []
        self.story_props: List[object] = []
        self.rng = random.Random(CHAPEL_SEED)

        self.nave_flood = WaterBody(
            pygame.Rect(1370, 250, 760, 1900),
            seed=CHAPEL_SEED,
            name="Flooded Nave",
            style="lake",
            flow=(0.15, 0.55),
            shore_variance=34,
            deep_margin=52,
            shallow_color=(58, 96, 93),
            mid_color=(34, 70, 78),
            deep_color=(18, 43, 57),
        )
        self.gravewater = WaterBody(
            pygame.Rect(2500, 1190, 540, 520),
            seed=CHAPEL_SEED + 8,
            name="Sunken Graveyard",
            style="lake",
            flow=(0.45, 0.1),
            shore_variance=28,
            deep_margin=40,
            shallow_color=(65, 99, 88),
            mid_color=(41, 73, 75),
            deep_color=(23, 49, 58),
        )
        self.waters = [self.nave_flood, self.gravewater]
        self.quarantine_zone = pygame.Rect(120, 720, 760, 620)
        self.bell_zone = pygame.Rect(2310, 220, 690, 650)
        self._build_environment()
        self._build_resources(manager)
        self.refresh_collisions()

    def _add(self, prop, blocking=False):
        self.props.append(prop)
        if blocking:
            self.land_obstacles.append(prop)

    def _is_water(self, point: Tuple[int, int], inset=-15) -> bool:
        return any(water.contains_point(point, inset=inset) for water in self.waters)

    def is_tainted(self, point: Tuple[int, int]) -> bool:
        if self.quarantine_zone.collidepoint(point):
            return False
        return any(water.contains_point(point, inset=-30) for water in self.waters)

    def random_land_point(self, margin=100) -> Tuple[int, int]:
        for _ in range(600):
            point = (
                self.rng.randint(margin, self.width - margin),
                self.rng.randint(margin, self.height - margin),
            )
            if self._is_water(point, inset=-35):
                continue
            if self.quarantine_zone.inflate(120, 120).collidepoint(point):
                continue
            return point
        return (950, 1700)

    def _build_environment(self):
        # Quarantine camp and safe holy fire.
        self._add(ChapelStone(220, 830, 170, 120, "tent", blocking=False))
        self._add(ChapelStone(430, 850, 170, 120, "tent", blocking=False))
        self.quarantine_brazier = ChapelStone(625, 920, 56, 76, "brazier", blocking=False)
        self._add(self.quarantine_brazier)

        # Ruined chapel walls flank the flooded nave and leave two causeways.
        wall_specs = (
            (1110, 260, 210, 110), (2180, 260, 220, 110),
            (1080, 420, 150, 390), (1080, 940, 150, 390), (1080, 1480, 150, 470),
            (2260, 420, 150, 390), (2260, 940, 150, 390), (2260, 1480, 150, 470),
            (1110, 2020, 1290, 105),
        )
        for spec in wall_specs:
            self._add(ChapelStone(*spec, "wall", blocking=True), blocking=True)

        # Bell tower and eastern graveyard.
        self.bell_tower = ChapelStone(2520, 300, 220, 330, "tower", blocking=True)
        self._add(self.bell_tower, blocking=True)
        for row in range(5):
            for col in range(7):
                x = 2470 + col * 92 + (row % 2) * 25
                y = 930 + row * 190
                if self.gravewater.rect.inflate(50, 50).collidepoint((x, y)):
                    continue
                self._add(ChapelStone(x, y, 48, 68, "grave", blocking=False))

        for _ in range(68):
            x, y = self.random_land_point(45)
            self._add(ForestGrass(x, y) if self.rng.random() < 0.65 else ForestBush(x, y))

    def _build_resources(self, manager):
        state = drowned_chapel_state(manager)
        harvested = set(state.get("harvested_nodes", ()))
        specs = []
        for index in range(9):
            specs.append((f"herb_{index}", "Medicinal Herb"))
        for index in range(8):
            specs.append((f"lotus_{index}", "Grave-Lotus"))
        for index in range(5):
            specs.append((f"wax_{index}", "Sanctified Wax"))
        for index in range(7):
            specs.append((f"clay_{index}", "River Clay"))
        for node_id, resource in specs:
            x, y = self.random_land_point(90)
            node = ChapelResourceNode(node_id, x, y, resource, node_id in harvested)
            self.resources.append(node)
            self.props.append(node)

    def refresh_collisions(self):
        # Two broken stone causeways cross the flooded nave. Gravewater remains deep.
        self.water_obstacles = self.nave_flood.make_collision_barriers(
            ((590, 735), (1760, 1885)),
            slice_height=58,
        )
        self.water_obstacles += self.gravewater.make_collision_barriers(())
        self.obstacles = list(self.land_obstacles) + list(self.water_obstacles)

    def update(self, manager):
        if random.random() < 0.05:
            water = random.choice(self.waters)
            local_y = random.randint(20, max(20, water.rect.height - 20))
            left, right = water._local_bounds_at(local_y)
            x = random.randint(int(left + 20), max(int(left + 21), int(right - 20)))
            water.add_ripple((water.rect.left + x, water.rect.top + local_y))

    def draw_background(self, screen, offset=(0, 0)):
        self.floor.draw(screen, offset)
        for water in self.waters:
            water.draw(screen, offset)
        # Pale stone causeways are drawn directly over the water geometry.
        for world_y in (665, 1820):
            rect = self.nave_flood.span_rect(world_y, height=78, padding=20)
            draw_rect = rect.move(-int(offset[0]), -int(offset[1]))
            pygame.draw.rect(screen, (91, 91, 84), draw_rect, border_radius=5)
            for x in range(draw_rect.x + 8, draw_rect.right - 6, 34):
                pygame.draw.line(screen, (58, 63, 63), (x, draw_rect.top + 4), (x - 5, draw_rect.bottom - 4), 2)

    def draw_foreground(self, screen, offset=(0, 0)):
        for water in self.waters:
            visible = water.rect.move(-int(offset[0]), -int(offset[1])).clip(screen.get_rect())
            if visible.width <= 0 or visible.height <= 0:
                continue
            haze = pygame.Surface(visible.size, pygame.SRCALPHA)
            haze.fill((145, 188, 176, 18))
            screen.blit(haze, visible.topleft)


class DrownedChapelMenu(GameplayScreen):
    def __init__(self, manager):
        super().__init__(manager)
        self.arena = DrownedChapelArena(manager)
        self.monsters = pygame.sprite.Group()
        self.chapel_npcs: List[Villager] = []
        self.chapel_markers: List[ChapelMarker] = []
        self.dynamic_props: List[object] = []
        self.boss: Optional[BellDrownedPilgrim] = None
        self.feedback = ""
        self.feedback_timer = 0
        self.dialogue_active = False
        self.dialogue_name = ""
        self.dialogue_pages: List[str] = []
        self.dialogue_index = 0
        self.hazard_tick = 0

    def on_enter(self):
        super().on_enter()
        self.manager.current_arena = self.arena
        state = drowned_chapel_state(self.manager)
        state["visits"] = int(state.get("visits", 0)) + 1
        sync_drowned_chapel_story(self.manager)
        self.player.rect.center = (250, 1080)
        self.player.current_hp = max(1, self.player.current_hp)
        self.player.is_dead = False
        self.monsters.empty()
        self._spawn_population()
        self._refresh_story_props()
        self._spawn_boss_if_needed()
        self._update_camera()
        try:
            from systems.world_progression import mark_location_visited
            mark_location_visited(self.manager, "drowned_chapel", set_current=True)
        except Exception:
            pass

    def _spawn_population(self):
        placements = (
            (WaterRisenPilgrim, 980, 470), (WaterRisenPilgrim, 980, 1280),
            (WaterRisenPilgrim, 900, 1830), (WaterRisenPilgrim, 2430, 1040),
            (WaterRisenPilgrim, 3060, 1010), (WaterRisenPilgrim, 3020, 1840),
            (FloodedAcolyte, 2300, 720), (FloodedAcolyte, 2440, 1500),
            (FloodedAcolyte, 3150, 720), (BellWraith, 2850, 760),
            (BellWraith, 3140, 1960), (DrownedMudling, 980, 2050),
            (BogTick, 2380, 1950), (WhisperMoth, 3000, 1120),
        )
        for index, (monster_class, x, y) in enumerate(placements):
            self.monsters.add(monster_class(f"{monster_class.SPECIES} {index + 1}", x, y, ENEMY_TEAM))

    @staticmethod
    def _npc(name, x, y, role):
        npc = Villager(name, "Human", x, y, team_color=GREEN)
        npc.ai_controller = None
        npc.chapel_role = role
        return npc

    def _refresh_story_props(self):
        for prop in list(self.dynamic_props):
            if prop in self.arena.props:
                self.arena.props.remove(prop)
        self.dynamic_props = []
        self.chapel_npcs = []
        self.chapel_markers = []
        state = drowned_chapel_state(self.manager)
        stage = int(state.get("quest_stage", 0))

        rhea = self._npc("Sister-Medic Rhea Ashford", 330, 1030, "rhea")
        volunteer = self._npc("Brother Iven", 535, 1115, "iven")
        self.chapel_npcs.extend((rhea, volunteer))

        if stage == 1 and not state.get("medicine_chest_recovered"):
            self.chapel_markers.append(ChapelMarker("medicine_chest", 2260, 610, "Recover medicine chest", "chest"))

        pilgrim_data = (
            ("pilgrim_senn", "Pilgrim Senn", 2460, 940),
            ("pilgrim_orla", "Pilgrim Orla", 3100, 1420),
            ("pilgrim_cal", "Brother Cal", 2450, 1930),
        )
        rescued = set(state.get("rescued_pilgrims", ()))
        if stage == 2:
            for pilgrim_id, name, x, y in pilgrim_data:
                if pilgrim_id not in rescued:
                    self.chapel_npcs.append(self._npc(name, x, y, f"rescue:{pilgrim_id}"))
        for index, pilgrim_id in enumerate(sorted(rescued)):
            label = dict((pid, name) for pid, name, _x, _y in pilgrim_data).get(pilgrim_id, "Rescued Pilgrim")
            self.chapel_npcs.append(self._npc(label, 260 + index * 95, 1220, "rescued"))

        if stage == 3:
            samples = set(state.get("water_samples", ()))
            sample_data = (
                ("nave_north", 1280, 520, "Sample northern nave water"),
                ("nave_south", 2190, 1800, "Sample southern nave water"),
                ("grave_pool", 3050, 1450, "Sample graveyard water"),
            )
            for marker_id, x, y, label in sample_data:
                self.chapel_markers.append(ChapelMarker(marker_id, x, y, label, "sample", marker_id in samples))

        if stage == 4:
            lit = set(state.get("lit_wards", ()))
            ward_data = (
                ("camp_ward", 760, 980, "Light quarantine ward"),
                ("nave_ward", 2280, 1130, "Light chapel ward"),
                ("tower_ward", 2830, 710, "Light bell-tower ward"),
            )
            for marker_id, x, y, label in ward_data:
                self.chapel_markers.append(ChapelMarker(marker_id, x, y, label, "ward", marker_id in lit))

        self.dynamic_props = list(self.chapel_npcs) + list(self.chapel_markers)
        self.arena.props.extend(self.dynamic_props)

    def _spawn_boss_if_needed(self):
        state = drowned_chapel_state(self.manager)
        self.boss = None
        if not state.get("boss_unlocked") or state.get("boss_defeated"):
            return
        self.boss = BellDrownedPilgrim("The Bell-Drowned Pilgrim", 2760, 690, ENEMY_TEAM)
        self.monsters.add(self.boss)
        self._flash("The drowned bell answers from the tower.", 300)

    def _near(self, rect: pygame.Rect, inflate=72) -> bool:
        return self.player.rect.colliderect(rect.inflate(inflate, inflate))

    @staticmethod
    def _wrap(text: str, font, width: int) -> List[str]:
        lines, current = [], ""
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

    def _rhea_dialogue(self):
        state = drowned_chapel_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        state["infection"] = 0.0
        if stage == 0:
            state["quest_stage"] = 1
            pages = (
                "This was Saint Lumen's roadside chapel before the flood carried the dead back through its doors.",
                "Recover my medicine chest from the eastern apse. After that we rescue the living, test the water and silence the bell.",
                "The road is open, but this is a level 3-5 quarantine zone. I will not pretend a warning is a wall.",
            )
            try:
                self.manager.record_tier0_event("flag", "drowned_chapel_started")
            except Exception:
                pass
        elif stage == 1:
            pages = ("The medicine chest lies beyond the northern causeway, against the dry eastern wall of the flooded nave.",)
        elif stage == 2:
            count = len(set(state.get("rescued_pilgrims", ())))
            pages = (f"Three pilgrims are still trapped among the graves and ruined walls. Rescued: {count}/3.",)
        elif stage == 3:
            count = len(set(state.get("water_samples", ())))
            pages = (f"Take samples from the marked nave and graveyard sites. Samples: {count}/3.",)
        elif stage == 4:
            count = len(set(state.get("lit_wards", ())))
            pages = (
                f"The samples carry Vortex residue. Light all three wards with the wax I issued. Wards: {count}/3.",
                "The wards will force whatever rings that bell to take solid form.",
            )
        elif stage == 5:
            pages = ("The Bell-Drowned Pilgrim is corporeal now. Break the bell fused into its chest before another toll raises the graves.",)
        else:
            pages = (
                "The bell is silent and the quarantine line can become a hospice outpost.",
                "The chapel is not clean, but it is ours to heal instead of theirs to haunt.",
            )
        self._open_dialogue("Sister-Medic Rhea Ashford", pages)
        self._refresh_story_props()

    def _iven_dialogue(self):
        state = drowned_chapel_state(self.manager)
        infection = int(state.get("infection", 0))
        pages = (
            f"Your taint exposure reads {infection}%. Stay near the green brazier or speak with Rhea to clear it.",
            "Water-risen drag their victims into the flood. Acolytes poison the ground. Bell Wraiths punish anyone who stands still.",
        )
        self._open_dialogue("Brother Iven", pages)

    def _rescue_pilgrim(self, npc):
        state = drowned_chapel_state(self.manager)
        pilgrim_id = str(npc.chapel_role).split(":", 1)[1]
        rescued = state.setdefault("rescued_pilgrims", [])
        if pilgrim_id not in rescued:
            rescued.append(pilgrim_id)
            self.manager.reputation = int(getattr(self.manager, "reputation", 0)) + 1
            self._flash(f"Rescued {npc.name}. +1 reputation")
            _safe_sound("recruit")
            sync_drowned_chapel_story(self.manager)
            self._refresh_story_props()
        return True

    def _try_npc(self) -> bool:
        for npc in self.chapel_npcs:
            if not self._near(npc.rect, 72):
                continue
            role = getattr(npc, "chapel_role", "")
            if role == "rhea":
                self._rhea_dialogue()
            elif role == "iven":
                self._iven_dialogue()
            elif role.startswith("rescue:"):
                self._rescue_pilgrim(npc)
            else:
                self._open_dialogue(npc.name, ("Rhea got us behind the quarantine line. The bell still rings in my sleep.",))
            return True
        return False

    def _try_marker(self) -> bool:
        state = drowned_chapel_state(self.manager)
        for marker in self.chapel_markers:
            if marker.complete or not self._near(marker.rect, 76):
                continue
            if marker.style == "chest":
                state["medicine_chest_recovered"] = True
                self.manager.inventory["Saint Lumen Medicine Chest"] = int(self.manager.inventory.get("Saint Lumen Medicine Chest", 0)) + 1
                self._flash("Recovered the Saint Lumen medicine chest.")
            elif marker.style == "sample":
                samples = state.setdefault("water_samples", [])
                if marker.marker_id not in samples:
                    samples.append(marker.marker_id)
                    self.manager.inventory["Tainted Water Sample"] = int(self.manager.inventory.get("Tainted Water Sample", 0)) + 1
                    self._flash(f"Tainted-water samples: {len(set(samples))}/3")
            elif marker.style == "ward":
                if int(self.manager.inventory.get("Sanctified Wax", 0)) < 1:
                    self._flash("The ward requires 1 Sanctified Wax.")
                    _safe_sound("error")
                    return True
                self.manager.inventory["Sanctified Wax"] -= 1
                if self.manager.inventory["Sanctified Wax"] <= 0:
                    self.manager.inventory.pop("Sanctified Wax", None)
                wards = state.setdefault("lit_wards", [])
                if marker.marker_id not in wards:
                    wards.append(marker.marker_id)
                self._flash(f"Saint Lumen wards lit: {len(set(wards))}/3")
            marker.complete = True
            marker._redraw()
            _safe_sound("recruit")
            old_stage = int(state.get("quest_stage", 0))
            changed = sync_drowned_chapel_story(self.manager)
            new_stage = int(state.get("quest_stage", 0))
            if changed:
                self._refresh_story_props()
                if old_stage == 3 and new_stage == 4:
                    self._flash("Water source identified. Rhea issued 3 Sanctified Wax.", 300)
                elif old_stage == 4 and new_stage == 5:
                    self._flash("All wards lit. The Bell-Drowned Pilgrim has taken form.", 300)
                    self._spawn_boss_if_needed()
            return True
        return False

    def _try_resource(self) -> bool:
        for node in self.arena.resources:
            if node.harvested or not self._near(node.rect, 68):
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
            if self._try_npc() or self._try_marker() or self._try_resource():
                return
            if self._near(self.arena.quarantine_brazier.rect, 100):
                state = drowned_chapel_state(self.manager)
                state["infection"] = 0.0
                self.player.current_hp = min(self.player.max_hp, self.player.current_hp + max(1, int(self.player.max_hp * 0.25)))
                self._flash("Rested at the quarantine brazier. Taint exposure cleared.")

    def _infection_step(self):
        state = drowned_chapel_state(self.manager)
        infection = float(state.get("infection", 0.0))
        if self.arena.quarantine_zone.collidepoint(self.player.rect.center):
            infection = max(0.0, infection - 2.5)
        elif self.arena.is_tainted(self.player.rect.center):
            infection = min(100.0, infection + 2.1)
        else:
            infection = max(0.0, infection - 0.18)
        if infection >= 100.0:
            try:
                self.player.take_damage(6, "Poison", manager=self.manager)
                self.player.apply_status("Slow", 120, 0)
            except Exception:
                self.player.current_hp = max(1, self.player.current_hp - 6)
            infection = 74.0
            self._flash("Vortex-tainted fever surges through you.")
        state["infection"] = infection
        return infection

    def _process_boss(self):
        if self.boss is None:
            return
        if self.boss.pending_spawn:
            for spawn in list(self.boss.pending_spawn):
                self.monsters.add(spawn)
            self.boss.pending_spawn = []
            self._flash("The drowned bell raises three Water-risen Pilgrims.")
        if not self.boss.is_dead:
            return
        state = drowned_chapel_state(self.manager)
        if state.get("boss_defeated"):
            return
        state["boss_defeated"] = True
        state["boss_unlocked"] = False
        state["quest_stage"] = 6
        state["completed"] = True
        if not state.get("boss_reward_claimed"):
            self.manager.gold += CHAPEL_REWARD_SP
            self.manager.reputation = int(getattr(self.manager, "reputation", 0)) + CHAPEL_REWARD_REPUTATION
            self.manager.inventory["Saint Lumen Seal"] = int(self.manager.inventory.get("Saint Lumen Seal", 0)) + 1
            self.manager.inventory["Drowned Bell Clapper"] = int(self.manager.inventory.get("Drowned Bell Clapper", 0)) + 1
            state["boss_reward_claimed"] = True
        try:
            self.manager.record_tier0_event("boss", "bell_drowned_pilgrim")
            self.manager.record_tier0_event("quest", "drowned_chapel_secured")
        except Exception:
            pass
        self._flash("Drowned Chapel secured. +80 SP, +7 reputation, Saint Lumen Seal.", 420)
        self._refresh_story_props()

    def update(self):
        if self.dialogue_active:
            if self.feedback_timer > 0:
                self.feedback_timer -= 1
            return
        if self.manager.paused:
            return
        all_units = [self.player] + [monster for monster in self.monsters if not monster.is_dead]
        self._update_gameplay(all_units)
        self.hazard_tick += 1
        if self.hazard_tick % 24 == 0:
            self._infection_step()
        self._process_boss()
        if self.player.rect.left < 8:
            self.manager.match_in_progress = False
            self.manager.pending_local_area = "whisper_marsh"
            self.manager.pending_world_location = "whisper_marsh"
            self.manager.chapel_return = True
            self.next_state = "regional_staging"
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    def _flash(self, message: str, duration=180):
        self.feedback = str(message)
        self.feedback_timer = int(duration)

    def _nearest_prompt(self):
        for npc in self.chapel_npcs:
            if self._near(npc.rect, 72):
                role = getattr(npc, "chapel_role", "")
                label = f"Rescue {npc.name}" if role.startswith("rescue:") else f"Talk to {npc.name}"
                return npc.rect, label
        for marker in self.chapel_markers:
            if not marker.complete and self._near(marker.rect, 76):
                return marker.rect, marker.label
        for node in self.arena.resources:
            if not node.harvested and self._near(node.rect, 68):
                return node.rect, f"Gather {node.resource_name}"
        if self._near(self.arena.quarantine_brazier.rect, 100):
            return self.arena.quarantine_brazier.rect, "Rest and clear taint exposure"
        return None

    def _draw_dialogue(self, screen):
        # Yhtenäinen Muckford-tyylinen dialogi (puhuja esiin + nimikilpi)
        from systems.area_dialogue import draw_area_dialogue
        if draw_area_dialogue(self, screen):
            return
        if not self.dialogue_active:
            return
        panel = pygame.Rect(165, SCREEN_HEIGHT - 260, SCREEN_WIDTH - 330, 205)
        overlay = pygame.Surface(panel.size, pygame.SRCALPHA)
        overlay.fill((20, 25, 24, 240))
        screen.blit(overlay, panel.topleft)
        pygame.draw.rect(screen, (166, 148, 86), panel, 3, border_radius=9)
        draw_text(self.dialogue_name, font_main, GOLD_COLOR, screen, panel.x + 24, panel.y + 18)
        page = self.dialogue_pages[self.dialogue_index]
        y = panel.y + 60
        for line in self._wrap(page, font_main, panel.w - 48)[:4]:
            draw_text(line, font_main, WHITE, screen, panel.x + 24, y)
            y += 29
        draw_text("[E / Enter] continue    [Esc] close", font_small, GRAY, screen, panel.right - 355, panel.bottom - 27)

    def draw(self, screen):
        all_units = [self.player] + [monster for monster in self.monsters if not monster.is_dead]
        self._draw_gameplay(screen, all_units)
        offset = (self.camera_x, self.camera_y)
        prompt = self._nearest_prompt()
        if prompt and not self.dialogue_active:
            rect, label = prompt
            self.manager._draw_floating_prompt(screen, rect.centerx, rect.top - 18, "E", offset, label)

        state = drowned_chapel_state(self.manager)
        alive = sum(1 for monster in self.monsters if not monster.is_dead)
        remaining = sum(1 for node in self.arena.resources if not node.harvested)
        draw_text(
            f"DROWNED CHAPEL — OPEN RISK Lv 3-5   Threats: {alive}   Resources: {remaining}",
            font_small, WHITE, screen, 36, 34,
        )
        draw_text(f"CHAPEL OBJECTIVE: {chapel_objective(self.manager)}", font_small, (221, 203, 137), screen, 36, 60)
        infection = int(state.get("infection", 0))
        draw_text(f"TAINT EXPOSURE: {infection}%", font_small, (225, 104, 91) if infection >= 70 else (145, 210, 182), screen, 36, 86)
        draw_text("Return west to Whisper Marsh. Green quarantine brazier clears exposure.", font_small, GRAY, screen, 36, 110)
        if self.feedback_timer > 0:
            surface = font_main.render(self.feedback, True, GOLD_COLOR)
            screen.blit(surface, (SCREEN_WIDTH // 2 - surface.get_width() // 2, 135))
        self._draw_dialogue(screen)
