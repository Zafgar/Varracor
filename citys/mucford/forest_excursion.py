# citys/mucford/forest_excursion.py
"""Whisper Marsh outskirts south of Muckford.

This is a repeatable free-roam area for gathering, hunting and developing a
small survey post. Water is rendered entirely in code through
``ProceduralWaterBody`` so shore motion, foam and currents do not depend on a
large painted water image. Stable fishing anchors are exposed for the later
fishing minigame.
"""
from __future__ import annotations

import math
import random
from typing import Dict, Iterable, List, Optional, Tuple

import pygame

from assets.tiles.forest_objects import ForestBush, ForestGrass
from assets.tiles.muckford_floors import MuckfordFloor
from assets.tiles.muckford_objects import MuckfordTree
from assets.tiles.prop import Prop
from menus.gameplay_screen import GameplayScreen
from settings import (
    ENEMY_TEAM,
    GOLD_COLOR,
    GRAY,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
)
from sound_manager import sound_system
from systems.field_kit import FieldResourceNode
from assets.tiles.water import FishingAnchor, WaterBody
from ui_kit import draw_text, font_main, font_small, format_money
from units.corrupted_crow import CorruptedCrow
from units.rat import GiantRat


MAP_SEED = 44721
CAMP_UPGRADES = {
    0: ("Dry Shelter", {"Driftwood": 4, "River Reed": 3}),
    1: ("Raised Boardwalk", {"Driftwood": 4, "River Reed": 6, "Clay": 2}),
    2: ("Tackle Bench", {"Driftwood": 5, "River Reed": 5, "Bogwort": 2}),
}


def outskirts_state(manager) -> dict:
    global_data = manager.npc_state.setdefault("global", {})
    state = global_data.setdefault("muckford_outskirts", {})
    state.setdefault("visits", 0)
    state.setdefault("camp_stage", 0)
    state.setdefault("gathered_total", 0)
    state.setdefault("fishing_ready", False)
    return state


def _cost_text(cost: Dict[str, int]) -> str:
    return ", ".join(f"{amount} {name}" for name, amount in cost.items())


class MarshResourceNode(FieldResourceNode):
    """Suon keräysnode - runko tulee kenttäpakista (systems/field_kit),
    tässä vain suokohtaiset piirtotyylit ja tilastokoukku."""

    SIZE = 52

    def _paint_bogwort(image, s):
        for dx in (-9, -3, 4, 10):
            pygame.draw.line(image, (59, 132, 83), (26, 49), (26 + dx, 15), 3)
        pygame.draw.circle(image, (151, 106, 191), (17, 15), 4)
        pygame.draw.circle(image, (151, 106, 191), (30, 11), 4)
        pygame.draw.circle(image, (151, 106, 191), (38, 19), 3)

    # "herb" säilyttää suon violetin bogwort-ulkoasun (vanha else-haara)
    PAINTERS = {**FieldResourceNode.PAINTERS,
                "bogwort": _paint_bogwort, "herb": _paint_bogwort}

    def __init__(self, x, y, resource_name, style,
                 amount: Tuple[int, int] = (1, 2)):
        super().__init__("", x, y, resource_name, style, amount)

    def _after_harvest(self, manager, amount):
        state = outskirts_state(manager)
        state["gathered_total"] = int(state.get("gathered_total", 0)) + amount


class MarshBridge(Prop):
    def __init__(self, rect: pygame.Rect, *, reed: bool = False):
        super().__init__(rect.x, rect.y, rect.w, rect.h, color=(0, 0, 0))
        self.rect = pygame.Rect(rect)
        self.image_pos = self.rect.topleft
        self.has_shadow = False
        self.type = "bridge"
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        plank_color = (121, 88, 54) if not reed else (139, 119, 67)
        rope_color = (73, 58, 38)
        plank_w = 22 if not reed else 17
        for x in range(5, self.rect.w - 5, plank_w):
            wobble = ((x // plank_w) % 3) - 1
            pygame.draw.rect(
                surface,
                plank_color,
                pygame.Rect(x, 8 + wobble * 2, plank_w - 3, self.rect.h - 16),
                border_radius=2,
            )
            pygame.draw.line(
                surface,
                (164, 126, 77),
                (x + 3, 13 + wobble * 2),
                (x + plank_w - 6, 13 + wobble * 2),
                2,
            )
        pygame.draw.line(surface, rope_color, (3, 8), (self.rect.w - 3, 8), 4)
        pygame.draw.line(
            surface, rope_color, (3, self.rect.h - 8), (self.rect.w - 3, self.rect.h - 8), 4
        )
        self.image = surface


class SurveyPost(Prop):
    def __init__(self, x: int, y: int, stage: int):
        super().__init__(x, y, 150, 125, color=(0, 0, 0))
        self.rect = pygame.Rect(x + 12, y + 68, 126, 48)
        self.image_pos = (x, y)
        self.stage = int(stage)
        self.interaction_range = 115
        self.interaction_label = "Develop survey post"
        self.type = "camp"
        self._redraw()

    def set_stage(self, stage: int):
        self.stage = int(stage)
        self._redraw()

    def _redraw(self):
        surface = pygame.Surface((150, 125), pygame.SRCALPHA)
        # Raised platform
        pygame.draw.polygon(
            surface,
            (91, 65, 42),
            [(13, 96), (134, 96), (122, 116), (24, 116)],
        )
        for x in range(24, 126, 18):
            pygame.draw.line(surface, (132, 96, 57), (x, 97), (x - 4, 114), 4)

        # Marker and campfire exist from stage 0.
        pygame.draw.line(surface, (80, 60, 42), (27, 96), (27, 25), 5)
        pygame.draw.polygon(surface, (112, 78, 47), [(27, 25), (75, 39), (27, 52)])
        pygame.draw.circle(surface, (117, 53, 27), (103, 91), 13)
        pygame.draw.circle(surface, (236, 130, 45), (103, 86), 8)

        if self.stage >= 1:
            # Dry shelter
            pygame.draw.polygon(
                surface,
                (74, 84, 56),
                [(42, 74), (75, 31), (118, 76)],
            )
            pygame.draw.polygon(
                surface,
                (124, 105, 63),
                [(42, 74), (75, 44), (118, 76), (108, 92), (50, 92)],
            )
        if self.stage >= 2:
            # Survey crates and boardwalk plans
            pygame.draw.rect(surface, (105, 75, 45), (9, 79, 30, 22))
            pygame.draw.line(surface, (187, 163, 100), (12, 82), (36, 98), 2)
            pygame.draw.line(surface, (187, 163, 100), (36, 82), (12, 98), 2)
        if self.stage >= 3:
            # Tackle bench foundation for the later fishing system.
            pygame.draw.rect(surface, (100, 70, 42), (82, 61, 55, 9))
            pygame.draw.line(surface, (90, 61, 38), (89, 68), (86, 95), 4)
            pygame.draw.line(surface, (90, 61, 38), (130, 68), (133, 95), 4)
            pygame.draw.arc(surface, (178, 171, 130), (107, 52, 20, 18), 0, math.tau, 2)
        self.image = surface


class WhisperMarshArena:
    def __init__(self, manager):
        self.width = 3600
        self.height = 2400
        self.manager = manager
        self.floor = MuckfordFloor(self.width, self.height)
        self.props: List[object] = []
        self.floor_props: List[object] = []
        self.land_obstacles: List[object] = []
        self.water_obstacles: List[object] = []
        self.obstacles: List[object] = []
        self.resources: List[MarshResourceNode] = []
        self.development_props: List[object] = []
        self.rng = random.Random(MAP_SEED)

        self.greywash_channel = WaterBody(
            pygame.Rect(1510, -50, 820, self.height + 100),
            seed=MAP_SEED,
            name="Greywash Channel",
            style="river",
            flow=(0.25, 1.0),
            shore_variance=52,
            deep_margin=58,
            shallow_color=(67, 105, 104),
            mid_color=(39, 77, 91),
            deep_color=(18, 47, 67),
        )
        self.whisper_pool = WaterBody(
            pygame.Rect(2670, 1240, 610, 520),
            seed=MAP_SEED + 9,
            name="Whisper Pool",
            style="lake",
            flow=(0.8, 0.15),
            shore_variance=38,
            deep_margin=46,
            shallow_color=(69, 106, 94),
            mid_color=(40, 79, 82),
            deep_color=(21, 53, 67),
        )
        self.waters = [self.greywash_channel, self.whisper_pool]
        self.fishing_spots: List[FishingAnchor] = (
            self.greywash_channel.fishing_anchors(8, difficulty=1)
            + self.whisper_pool.fishing_anchors(4, difficulty=2)
        )
        self._build_landscape()
        self.refresh_development(manager)

    def _add(self, prop, blocking: bool = False):
        self.props.append(prop)
        if blocking:
            self.land_obstacles.append(prop)

    def _is_water(self, point: Tuple[int, int], inset: int = -15) -> bool:
        return any(water.contains_point(point, inset=inset) for water in self.waters)

    def random_land_point(self, margin: int = 120) -> Tuple[int, int]:
        for _ in range(500):
            point = (
                self.rng.randint(margin, self.width - margin),
                self.rng.randint(margin, self.height - margin),
            )
            if self._is_water(point, inset=-30):
                continue
            if point[1] < 330 and 250 < point[0] < 900:
                continue
            return point
        return (500, 700)

    def _build_landscape(self):
        # Ground clutter gives the wetland shape without relying on a background image.
        for _ in range(115):
            x, y = self.random_land_point(45)
            if self.rng.random() < 0.58:
                self._add(ForestGrass(x, y))
            else:
                self._add(ForestBush(x, y))

        # Trees are concentrated away from the entrance and shore approaches.
        for _ in range(68):
            x, y = self.random_land_point(100)
            if 1300 < x < 2450 and (300 < y < 650 or 1320 < y < 1660):
                continue
            self._add(MuckfordTree(x, y), blocking=True)

        # Resource distribution: reeds hug banks, clay sits in exposed banks,
        # driftwood is washed farther inland and Bogwort grows in wet shade.
        for index in range(14):
            y = 260 + index * 135 + self.rng.randint(-40, 40)
            left, right = self.greywash_channel.bounds_at(y)
            x = int(left - self.rng.randint(45, 80)) if index % 2 == 0 else int(right + self.rng.randint(18, 48))
            self._add_resource(MarshResourceNode(x, y, "River Reed", "reeds", (1, 2)))

        for _ in range(8):
            x, y = self.random_land_point(100)
            self._add_resource(MarshResourceNode(x, y, "Driftwood", "driftwood", (1, 2)))
        for index in range(6):
            y = 450 + index * 280 + self.rng.randint(-50, 50)
            left, right = self.greywash_channel.bounds_at(y)
            x = int(left - 78) if index % 2 == 0 else int(right + 28)
            self._add_resource(MarshResourceNode(x, y, "Clay", "clay", (1, 2)))
        for _ in range(10):
            x, y = self.random_land_point(100)
            self._add_resource(MarshResourceNode(x, y, "Bogwort", "herb", (1, 2)))

    def _add_resource(self, node: MarshResourceNode):
        self.resources.append(node)
        self._add(node)

    def refresh_development(self, manager):
        for prop in self.development_props:
            if prop in self.props:
                self.props.remove(prop)
        self.development_props = []
        state = outskirts_state(manager)
        stage = int(state.get("camp_stage", 0))

        self.survey_post = SurveyPost(360, 270, stage)
        self.development_props.append(self.survey_post)
        self.props.append(self.survey_post)

        old_crossing = self.greywash_channel.span_rect(475, height=94, padding=28)
        old_bridge = MarshBridge(old_crossing, reed=False)
        self.development_props.append(old_bridge)
        self.props.append(old_bridge)

        crossings = [(410, 545)]
        if stage >= 2:
            boardwalk_rect = self.greywash_channel.span_rect(1490, height=86, padding=30)
            boardwalk = MarshBridge(boardwalk_rect, reed=True)
            self.development_props.append(boardwalk)
            self.props.append(boardwalk)
            crossings.append((1425, 1560))

        self.water_obstacles = self.greywash_channel.make_collision_barriers(crossings)
        self.water_obstacles += self.whisper_pool.make_collision_barriers(())
        self.obstacles = list(self.land_obstacles) + list(self.water_obstacles)

    def update(self, manager):
        # Rain and marsh creatures constantly disturb the water surface.
        if random.random() < 0.035:
            water = random.choice(self.waters)
            local_y = random.randint(20, max(20, water.rect.height - 20))
            left, right = water._local_bounds_at(local_y)
            x = random.randint(int(left + 20), max(int(left + 21), int(right - 20)))
            water.add_ripple((water.rect.left + x, water.rect.top + local_y))

    def draw_background(self, screen, offset=(0, 0)):
        self.floor.draw(screen, offset)
        for water in self.waters:
            water.draw(screen, offset)

    def draw_foreground(self, screen, offset=(0, 0)):
        # A faint low fog along water surfaces makes depth readable while keeping
        # collision and actors visible.
        for water in self.waters:
            visible = water.rect.move(-int(offset[0]), -int(offset[1]))
            clipped = visible.clip(screen.get_rect())
            if clipped.width <= 0 or clipped.height <= 0:
                continue
            fog = pygame.Surface((clipped.width, clipped.height), pygame.SRCALPHA)
            fog.fill((178, 196, 185, 12))
            screen.blit(fog, clipped.topleft)


# Backwards-compatible name used by external imports and tests.
ForestExcursionArena = WhisperMarshArena


class ForestExcursionMenu(GameplayScreen):
    """Repeatable gathering, combat and survey-post development area."""

    def __init__(self, manager):
        super().__init__(manager)
        self.arena = WhisperMarshArena(manager)
        self.monsters = pygame.sprite.Group()
        self.feedback = ""
        self.feedback_timer = 0
        self.event_banner = ""
        self.event_banner_timer = 0
        self.lost_traveler_pos = None
        self.lost_traveler_found = True
        self.troll = None

    def on_enter(self):
        super().on_enter()
        self.manager.current_arena = self.arena
        state = outskirts_state(self.manager)
        state["visits"] = int(state.get("visits", 0)) + 1
        self.arena.refresh_development(self.manager)

        # Muckford lies north of this map. The player walks south into the marsh
        # and returns by stepping back over the northern boundary.
        self.player.rect.center = (520, 175)
        self.player.current_hp = max(1, self.player.current_hp)
        self.player.is_dead = False
        self.monsters.empty()
        rng = random.Random()
        for index in range(7):
            mx, my = self.arena.random_land_point(210)
            if rng.random() < 0.62:
                monster = GiantRat(f"Marsh Rat {index + 1}", mx, my, ENEMY_TEAM)
            else:
                monster = CorruptedCrow(f"Drowned Crow {index + 1}", mx, my, ENEMY_TEAM)
            self.monsters.add(monster)
        self._roll_event(rng)
        self._update_camera()

        try:
            from systems.world_progression import mark_location_visited
            mark_location_visited(self.manager, "whisper_marsh", set_current=True)
        except Exception:
            pass

    def _roll_event(self, rng):
        self.lost_traveler_pos = None
        self.lost_traveler_found = True
        self.troll = None
        roll = rng.random()
        if roll < 0.16:
            from units.troll import Troll

            tx, ty = self.arena.random_land_point(350)
            self.troll = Troll("Greywash Troll", tx, ty, ENEMY_TEAM)
            self.monsters.add(self.troll)
            self._set_event("A GREYWASH TROLL has crawled from beneath the old bridge!")
        elif roll < 0.34:
            for _ in range(5):
                x, y = self.arena.random_land_point(120)
                node = MarshResourceNode(x, y, "Bogwort", "herb", (1, 2))
                self.arena.resources.append(node)
                self.arena.props.append(node)
            self._set_event("The flood has fed a thick new Bogwort bloom.")
        elif roll < 0.50:
            self.lost_traveler_pos = self.arena.random_land_point(240)
            self.lost_traveler_found = False
            self._set_event("A ferryman's bell rings somewhere beyond the reeds...")
        elif roll < 0.68:
            for index in range(4):
                x, y = self.arena.random_land_point(210)
                self.monsters.add(GiantRat(f"Flood Rat {index + 1}", x, y, ENEMY_TEAM))
            self._set_event("Fresh flood tracks lead straight toward an ambush.")
        elif roll < 0.84:
            for _ in range(4):
                x, y = self.arena.random_land_point(100)
                node = MarshResourceNode(x, y, "Driftwood", "driftwood", (1, 3))
                self.arena.resources.append(node)
                self.arena.props.append(node)
            self._set_event("Last night's current washed useful timber onto the banks.")
        else:
            self._set_event("The Whisper Marsh is quiet enough to hear the water answer itself.")

    def _set_event(self, text: str):
        self.event_banner = text
        self.event_banner_timer = 360

    def _flash(self, message: str):
        self.feedback = str(message)
        self.feedback_timer = 180

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            if self._try_survey_post():
                return
            self._try_gather()

    def _near(self, rect: pygame.Rect, inflate: int = 70) -> bool:
        return self.player.rect.colliderect(rect.inflate(inflate, inflate))

    def _try_gather(self) -> bool:
        for node in self.arena.resources:
            if node.harvested or not self._near(node.rect, 70):
                continue
            message = node.harvest(self.manager)
            if message:
                self._flash(message)
                village_tasks = getattr(self.manager, "village_tasks", None)
                if village_tasks and node.resource_name == "Bogwort":
                    village_tasks.notify_collect(self.manager, "forest_herbs")
            return True
        return False

    def _try_survey_post(self) -> bool:
        post = self.arena.survey_post
        if not self._near(post.rect, 100):
            return False
        state = outskirts_state(self.manager)
        stage = int(state.get("camp_stage", 0))
        if stage >= 3:
            self.player.current_hp = self.player.max_hp
            self.player.current_mana = self.player.max_mana
            self.player.current_stamina = self.player.max_stamina
            self._flash("Rested at the completed survey post. Fishing foundation is ready.")
            return True

        upgrade_name, cost = CAMP_UPGRADES[stage]
        missing = [
            f"{amount - int(self.manager.inventory.get(name, 0))} {name}"
            for name, amount in cost.items()
            if int(self.manager.inventory.get(name, 0)) < amount
        ]
        if missing:
            self._flash(f"{upgrade_name} needs: {_cost_text(cost)}")
            try:
                sound_system.play_sound("error")
            except Exception:
                pass
            return True

        for name, amount in cost.items():
            self.manager.inventory[name] = int(self.manager.inventory.get(name, 0)) - amount
            if self.manager.inventory[name] <= 0:
                self.manager.inventory.pop(name, None)
        state["camp_stage"] = stage + 1
        if stage + 1 >= 3:
            state["fishing_ready"] = True
        self.arena.refresh_development(self.manager)
        if hasattr(self.manager, "record_deed"):
            self.manager.record_deed(
                f"whisper_marsh_camp_{stage + 1}",
                f"built the {upgrade_name} at the Whisper Marsh survey post",
            )
        try:
            sound_system.play_sound("recruit")
        except Exception:
            pass
        benefit = {
            1: "The shelter can now restore you between expeditions.",
            2: "A second boardwalk now crosses the Greywash channel.",
            3: "The tackle bench exposes fishing anchors for the future minigame.",
        }[stage + 1]
        self._flash(f"Built {upgrade_name}. {benefit}")
        return True

    def update(self):
        if self.manager.paused:
            return
        all_units = [self.player] + [monster for monster in self.monsters if not monster.is_dead]
        self._update_gameplay(all_units)

        if self.lost_traveler_pos and not self.lost_traveler_found:
            distance = math.hypot(
                self.player.rect.centerx - self.lost_traveler_pos[0],
                self.player.rect.centery - self.lost_traveler_pos[1],
            )
            if distance < 85:
                self.lost_traveler_found = True
                self.manager.gold += 30
                if hasattr(self.manager, "record_deed"):
                    self.manager.record_deed(
                        "forest_lost_traveler",
                        "guided a lost ferryman home from the Whisper Marsh",
                    )
                self._flash(f"Found the ferryman! +{format_money(30)}")

        # Return through the northern trail to Muckford.
        if self.player.rect.top < 8:
            self.manager.match_in_progress = False
            self.manager.city_spawn_point = "forest_gate"
            self.next_state = "muckford_city"

        if self.feedback_timer > 0:
            self.feedback_timer -= 1
        if self.event_banner_timer > 0:
            self.event_banner_timer -= 1

    def _nearest_prompt(self):
        if self._near(self.arena.survey_post.rect, 100):
            stage = int(outskirts_state(self.manager).get("camp_stage", 0))
            if stage >= 3:
                return self.arena.survey_post.rect, "Rest at completed survey post"
            name, cost = CAMP_UPGRADES[stage]
            return self.arena.survey_post.rect, f"Build {name}: {_cost_text(cost)}"
        for node in self.arena.resources:
            if not node.harvested and self._near(node.rect, 70):
                return node.rect, node.interaction_label
        return None

    def draw(self, screen):
        all_units = [self.player] + [monster for monster in self.monsters if not monster.is_dead]
        self._draw_gameplay(screen, all_units)
        offset = (self.camera_x, self.camera_y)

        prompt = self._nearest_prompt()
        if prompt:
            rect, label = prompt
            self.manager._draw_floating_prompt(
                screen,
                rect.centerx,
                rect.top - 18,
                "E",
                offset,
                label,
            )

        remaining = sum(1 for node in self.arena.resources if not node.harvested)
        alive = sum(1 for monster in self.monsters if not monster.is_dead)
        stage = int(outskirts_state(self.manager).get("camp_stage", 0))
        draw_text(
            f"WHISPER MARSH OUTSKIRTS   Resources: {remaining}   Threats: {alive}   Survey post: {stage}/3",
            font_small,
            WHITE,
            screen,
            36,
            34,
        )
        draw_text(
            "Return north to Muckford. Old bridge: upper channel. Boardwalk unlock: lower channel.",
            font_small,
            GRAY,
            screen,
            36,
            60,
        )
        draw_text(
            "Water: procedural current, shore foam, glints and ripple simulation.",
            font_small,
            (144, 190, 195),
            screen,
            36,
            84,
        )

        if self.lost_traveler_pos and not self.lost_traveler_found:
            tx = self.lost_traveler_pos[0] - offset[0]
            ty = self.lost_traveler_pos[1] - offset[1]
            if 0 < tx < SCREEN_WIDTH and 0 < ty < SCREEN_HEIGHT:
                draw_text("?", font_main, (255, 220, 120), screen, tx, ty - 40)

        if self.event_banner_timer > 0:
            surface = font_main.render(self.event_banner, True, (255, 210, 130))
            screen.blit(surface, (SCREEN_WIDTH // 2 - surface.get_width() // 2, 124))
        if self.feedback_timer > 0:
            surface = font_main.render(self.feedback, True, GOLD_COLOR)
            screen.blit(surface, (SCREEN_WIDTH // 2 - surface.get_width() // 2, 94))
