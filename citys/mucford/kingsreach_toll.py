"""Playable Crown checkpoint between Greywash Ford and Rattlebridge."""
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
from units.kingsreach_toll_monsters import (
    CausewayBandit,
    CrownTollEnforcer,
    FeveredEscapee,
    TollmasterHadrikCrowl,
)
from units.villager import Villager
from vfx import VFXManager


MAP_WIDTH = 3800
MAP_HEIGHT = 2300
MAP_SEED = 91277
TOLL_FEE = 140
SMUGGLER_FEE = 35
SERVICE_ESCAPEES = 4
SERVICE_COST = {"Feverfew": 6, "Clean Bandage": 4, "Charcoal": 3}
OFFICIAL_EVIDENCE = {"Vale's Broken Signet": 1, "Torn Crown Orders": 1, "Wax Seal": 1}

OBJECTIVES = {
    0: "Speak with Toll Captain Elric Dorn at the east gate.",
    1: "Complete quarantine inspection with Medic Vela Marrow.",
    2: "Choose papers, payment, quarantine service or the smuggler route.",
    3: "Gather quarantine supplies and contain four Fevered Escapees.",
    4: "Use Nix Quickreed's culvert and defeat Tollmaster Hadrik Crowl.",
    5: "Collect stamped Crown travel papers from Captain Dorn.",
    6: "Return the Crown Promotion Docket to Bram for his recommendation.",
    7: "Tier 1 promotion secured. Take the western road to Rattlebridge.",
}


def _safe_sound(name: str) -> None:
    try:
        sound_system.play_sound(name)
    except Exception:
        pass


def _cost_text(cost: Dict[str, int]) -> str:
    return ", ".join(f"{amount} {name}" for name, amount in cost.items())


def kingsreach_state(manager) -> dict:
    global_data = manager.npc_state.setdefault("global", {})
    state = global_data.setdefault("kingsreach_toll", {})
    state.setdefault("visits", 0)
    state.setdefault("quest_stage", 0)
    state.setdefault("inspection_complete", False)
    state.setdefault("resolution", "")
    state.setdefault("toll_paid", False)
    state.setdefault("service_started", False)
    state.setdefault("service_escapees", 0)
    state.setdefault("service_complete", False)
    state.setdefault("smuggler_paid", False)
    state.setdefault("boss_unlocked", False)
    state.setdefault("boss_defeated", False)
    state.setdefault("boss_reward_claimed", False)
    state.setdefault("pass_issued", False)
    state.setdefault("completed", False)
    state.setdefault("resource_day", -1)
    state.setdefault("harvested_nodes", [])
    state.setdefault("merchant_purchases", 0)
    state.setdefault("quarantine_exposure", 0)
    state.setdefault("crown_rep_delta", 0)
    return state


def _tier0_flags(manager) -> dict:
    try:
        from systems.tier0_world_tracker import ensure_tier0_state

        return ensure_tier0_state(manager)["story_flags"]
    except Exception:
        return manager.npc_state.setdefault("tier0_world", {}).setdefault("story_flags", {})


def sync_kingsreach_story(manager) -> bool:
    state = kingsreach_state(manager)
    changed = False
    while True:
        stage = int(state.get("quest_stage", 0))
        if stage == 1 and state.get("inspection_complete"):
            state["quest_stage"] = 2
        elif stage == 3 and state.get("service_complete"):
            state["quest_stage"] = 5
        elif stage == 4 and state.get("boss_defeated"):
            state["quest_stage"] = 5
        elif stage == 5 and state.get("pass_issued"):
            state["quest_stage"] = 6
            state["completed"] = True
        elif stage == 6 and _tier0_flags(manager).get("tier1_promoted"):
            state["quest_stage"] = 7
        else:
            break
        changed = True
    return changed


def kingsreach_objective(manager) -> str:
    sync_kingsreach_story(manager)
    stage = int(kingsreach_state(manager).get("quest_stage", 0))
    return OBJECTIVES.get(stage, OBJECTIVES[7])


def _world_day(manager) -> int:
    return int(getattr(getattr(manager, "world_clock", None), "day", 0))


def _has_cost(manager, cost: Dict[str, int]) -> bool:
    return all(int(manager.inventory.get(name, 0)) >= amount for name, amount in cost.items())


def _consume_cost(manager, cost: Dict[str, int], *, keep=()) -> bool:
    if not _has_cost(manager, cost):
        return False
    keep = set(keep)
    for name, amount in cost.items():
        if name in keep:
            continue
        manager.inventory[name] = int(manager.inventory.get(name, 0)) - amount
        if manager.inventory[name] <= 0:
            manager.inventory.pop(name, None)
    return True


def _modify_crown_rep(manager, amount: int) -> None:
    amount = int(amount)
    try:
        manager.modify_faction_rep("crown_dominion", amount)
    except Exception:
        reps = getattr(manager, "reputations", None)
        if not isinstance(reps, dict):
            manager.reputations = {}
            reps = manager.reputations
        reps["crown_dominion"] = int(reps.get("crown_dominion", 0)) + amount
    state = kingsreach_state(manager)
    state["crown_rep_delta"] = int(state.get("crown_rep_delta", 0)) + amount


class RectObstacle:
    def __init__(self, rect, name="Crown wall"):
        self.rect = pygame.Rect(rect)
        self.blocks_projectiles = True
        self.is_structure = True
        self.name = str(name)


class TollProp(Prop):
    def __init__(self, x, y, width, height, style, blocking=False):
        super().__init__(x, y, width, height, color=(0, 0, 0))
        self.style = str(style)
        self.image_pos = (x, y)
        self.is_structure = bool(blocking)
        self.blocks_projectiles = bool(blocking)
        self.has_shadow = style not in {"road_mark", "culvert"}
        self._redraw()

    def _redraw(self):
        w, h = self.rect.size
        image = pygame.Surface((w, h), pygame.SRCALPHA)
        if self.style == "gatehouse":
            stone = (111, 109, 99)
            dark = (73, 72, 68)
            pygame.draw.rect(image, dark, (7, 42, w - 14, h - 48), border_radius=5)
            pygame.draw.rect(image, stone, (12, 46, w - 24, h - 57), border_radius=4)
            pygame.draw.polygon(image, dark, [(0, 52), (w // 2, 3), (w, 52)])
            pygame.draw.rect(image, (39, 38, 37), (w // 2 - 34, h - 94, 68, 84))
            pygame.draw.arc(image, (149, 143, 123), (w // 2 - 35, h - 112, 70, 54), 0, math.pi, 5)
            for x in range(20, w - 18, 52):
                pygame.draw.rect(image, (82, 82, 77), (x, 56, 24, 18))
        elif self.style == "wall":
            pygame.draw.rect(image, (79, 79, 75), (0, 8, w, h - 8))
            for y in range(12, h, 26):
                offset = 18 if (y // 26) % 2 else 0
                for x in range(-offset, w, 40):
                    pygame.draw.rect(image, (119, 116, 105), (x, y, 36, 21), border_radius=2)
                    pygame.draw.rect(image, (76, 74, 69), (x, y, 36, 21), 2, border_radius=2)
        elif self.style == "booth":
            pygame.draw.rect(image, (92, 73, 52), (11, 32, w - 22, h - 38), border_radius=4)
            pygame.draw.polygon(image, (126, 55, 46), [(2, 40), (w // 2, 5), (w - 2, 40)])
            pygame.draw.rect(image, (35, 31, 28), (w // 2 - 18, h - 55, 36, 49))
            pygame.draw.rect(image, (188, 162, 98), (18, 48, w - 36, 25), border_radius=3)
            pygame.draw.line(image, (91, 58, 37), (25, 52), (w - 25, 68), 3)
        elif self.style == "tent":
            pygame.draw.polygon(image, (146, 132, 96), [(7, h - 8), (w // 2, 9), (w - 7, h - 8)])
            pygame.draw.polygon(image, (103, 119, 91), [(18, h - 10), (w // 2, 29), (w - 18, h - 10)])
            pygame.draw.line(image, (78, 61, 43), (w // 2, 12), (w // 2, h - 7), 4)
            pygame.draw.circle(image, (153, 51, 46), (w // 2, 42), 12, 3)
            pygame.draw.line(image, (153, 51, 46), (w // 2 - 8, 42), (w // 2 + 8, 42), 3)
            pygame.draw.line(image, (153, 51, 46), (w // 2, 34), (w // 2, 50), 3)
        elif self.style == "cart":
            pygame.draw.rect(image, (111, 76, 45), (11, 31, w - 22, h - 47), border_radius=6)
            pygame.draw.rect(image, (168, 119, 67), (11, 31, w - 22, h - 47), 4, border_radius=6)
            for x in range(24, w - 25, 43):
                pygame.draw.ellipse(image, (192, 155, 88), (x, 10, 34, 37))
            pygame.draw.circle(image, (52, 48, 43), (31, h - 18), 16)
            pygame.draw.circle(image, (52, 48, 43), (w - 31, h - 18), 16)
        elif self.style == "brazier":
            pygame.draw.line(image, (68, 61, 52), (w // 2, h - 5), (w // 2, 37), 8)
            pygame.draw.polygon(image, (91, 79, 63), [(15, 35), (w - 15, 35), (w - 24, 58), (24, 58)])
            pygame.draw.circle(image, (225, 102, 38), (w // 2, 29), 15)
            pygame.draw.circle(image, (249, 176, 56), (w // 2, 24), 9)
        elif self.style == "banner":
            pygame.draw.line(image, (72, 56, 40), (18, h - 3), (18, 7), 6)
            pygame.draw.polygon(image, (140, 46, 42), [(21, 11), (w - 5, 22), (21, 56)])
            pygame.draw.circle(image, (205, 168, 70), (43, 31), 10, 3)
        elif self.style == "culvert":
            pygame.draw.arc(image, (72, 71, 68), (4, 4, w - 8, h - 2), math.pi, math.tau, 12)
            pygame.draw.rect(image, (43, 45, 44), (9, h // 2 - 2, w - 18, h // 2))
            for x in range(20, w - 18, 22):
                pygame.draw.line(image, (82, 76, 64), (x, h // 2 - 5), (x, h - 5), 5)
        elif self.style == "bandit_camp":
            pygame.draw.polygon(image, (82, 72, 57), [(8, h - 8), (w // 2, 17), (w - 8, h - 8)])
            pygame.draw.polygon(image, (115, 79, 54), [(18, h - 10), (w // 2, 34), (w - 18, h - 10)])
            pygame.draw.circle(image, (112, 49, 29), (w - 31, h - 21), 14)
            pygame.draw.circle(image, (232, 126, 44), (w - 31, h - 26), 8)
        elif self.style == "stone":
            pygame.draw.ellipse(image, (86, 86, 79), (4, 13, w - 8, h - 16))
            pygame.draw.polygon(image, (121, 119, 106), [(12, h - 18), (23, 8), (w - 17, 7), (w - 7, h - 21)])
        self.image = image


class TollResourceNode(Prop):
    def __init__(self, node_id, x, y, resource, style, amount=(1, 2), harvested=False):
        super().__init__(x, y, 54, 54, color=(0, 0, 0))
        self.node_id = str(node_id)
        self.resource_name = str(resource)
        self.style = str(style)
        self.min_amount, self.max_amount = int(amount[0]), int(amount[1])
        self.harvested = bool(harvested)
        self.image_pos = (x, y)
        self.rect = pygame.Rect(x + 5, y + 25, 44, 25)
        self.blocks_projectiles = False
        self.is_structure = False
        self.has_shadow = style not in {"herb", "paper"}
        self._redraw()

    def _redraw(self):
        image = pygame.Surface((54, 54), pygame.SRCALPHA)
        if self.harvested:
            pygame.draw.ellipse(image, (67, 62, 50, 95), (7, 43, 40, 8))
        elif self.style == "herb":
            for dx in (-10, -4, 3, 9):
                pygame.draw.line(image, (65, 123, 74), (27, 50), (27 + dx, 15), 3)
            for x, y in ((16, 16), (28, 12), (38, 18)):
                pygame.draw.circle(image, (213, 192, 93), (x, y), 4)
        elif self.style == "bandage":
            pygame.draw.rect(image, (206, 194, 157), (6, 24, 42, 19), border_radius=5)
            pygame.draw.line(image, (154, 76, 66), (12, 27), (42, 39), 3)
            pygame.draw.line(image, (154, 76, 66), (42, 27), (12, 39), 3)
        elif self.style == "charcoal":
            for x, y, r in ((14, 35, 10), (29, 28, 13), (42, 38, 9)):
                pygame.draw.circle(image, (38, 39, 38), (x, y), r)
                pygame.draw.arc(image, (89, 82, 69), (x - r + 3, y - r + 3, r * 2 - 6, r * 2 - 6), 3.3, 5.8, 2)
        else:
            pygame.draw.polygon(image, (210, 194, 143), [(7, 15), (45, 10), (48, 42), (10, 47)])
            pygame.draw.line(image, (115, 83, 59), (15, 22), (39, 19), 2)
            pygame.draw.line(image, (115, 83, 59), (14, 30), (40, 28), 2)
            pygame.draw.line(image, (115, 83, 59), (14, 38), (34, 36), 2)
        self.image = image

    def harvest(self, manager) -> Optional[str]:
        if self.harvested:
            return None
        amount = random.randint(self.min_amount, self.max_amount)
        manager.inventory[self.resource_name] = int(manager.inventory.get(self.resource_name, 0)) + amount
        state = kingsreach_state(manager)
        harvested = state.setdefault("harvested_nodes", [])
        if self.node_id not in harvested:
            harvested.append(self.node_id)
        self.harvested = True
        self._redraw()
        _safe_sound("recruit")
        return f"+{amount} {self.resource_name}"


class KingsreachTollArena:
    def __init__(self, manager):
        self.manager = manager
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        self.props: List[object] = []
        self.floor_props: List[object] = []
        self.land_obstacles: List[object] = []
        self.obstacles: List[object] = []
        self.resources: List[TollResourceNode] = []
        self.vfx = VFXManager()
        self.rng = random.Random(MAP_SEED)
        self.floor_image = pygame.Surface((self.width, self.height))
        self.dust = []
        self.haze = []
        self.east_exit = pygame.Rect(self.width - 75, 820, 105, 720)
        self.west_exit = pygame.Rect(-30, 820, 105, 720)
        self.quarantine_rect = pygame.Rect(2580, 1420, 980, 700)
        self.smuggler_rect = pygame.Rect(520, 1590, 940, 610)
        self.bandit_rect = pygame.Rect(260, 180, 1050, 650)
        self.gate_rect = pygame.Rect(1660, 650, 520, 990)
        self._generate_floor()
        self._build_landscape()
        self.refresh_persistent(manager)

    def _generate_floor(self):
        self.floor_image.fill((87, 83, 69))
        rng = random.Random(MAP_SEED + 5)
        for _ in range(1800):
            x = rng.randrange(self.width)
            y = rng.randrange(self.height)
            shade = rng.randint(-10, 12)
            color = (max(42, 87 + shade), max(41, 83 + shade), max(36, 69 + shade))
            pygame.draw.circle(self.floor_image, color, (x, y), rng.randint(5, 28))
        road = pygame.Rect(0, 865, self.width, 590)
        pygame.draw.rect(self.floor_image, (123, 119, 104), road)
        for x in range(-30, self.width, 82):
            for y in range(885, 1435, 58):
                wobble = ((x // 82 + y // 58) % 3) * 4
                pygame.draw.rect(self.floor_image, (151, 146, 126), (x + wobble, y, 74, 50), border_radius=5)
                pygame.draw.rect(self.floor_image, (91, 90, 84), (x + wobble, y, 74, 50), 2, border_radius=5)
        pygame.draw.line(self.floor_image, (185, 162, 101), (0, 1157), (self.width, 1157), 8)
        pygame.draw.rect(self.floor_image, (103, 96, 76), self.quarantine_rect, border_radius=20)
        pygame.draw.rect(self.floor_image, (72, 70, 61), self.smuggler_rect, border_radius=30)
        pygame.draw.rect(self.floor_image, (79, 70, 58), self.bandit_rect, border_radius=30)

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
        wall_specs = (
            (1640, 80, 120, 720),
            (1640, 1520, 120, 700),
            (2100, 80, 120, 720),
            (2100, 1520, 120, 700),
        )
        for x, y, w, h in wall_specs:
            wall = TollProp(x, y, w, h, "wall", blocking=True)
            self._add(wall, blocking=True)
        self.gatehouse = TollProp(1695, 585, 430, 305, "gatehouse", blocking=True)
        self._add(self.gatehouse, blocking=True)
        self.east_booth = TollProp(2250, 900, 180, 185, "booth", blocking=True)
        self.west_booth = TollProp(1430, 1230, 180, 185, "booth", blocking=True)
        self._add(self.east_booth, blocking=True)
        self._add(self.west_booth, blocking=True)

        for x in (1575, 2185):
            self.props.append(TollProp(x, 875, 70, 112, "banner"))
            self.props.append(TollProp(x, 1340, 70, 112, "banner"))
        for x, y in ((1525, 1030), (2250, 1030), (1525, 1260), (2250, 1260), (2760, 1530), (3300, 1530)):
            self.props.append(TollProp(x, y, 75, 98, "brazier"))

        for x, y in ((2760, 1590), (3020, 1690), (3290, 1585), (2890, 1900), (3260, 1920)):
            self.props.append(TollProp(x, y, 205, 135, "tent"))
        for x, y in ((2730, 380), (3000, 450), (3290, 350), (2850, 690)):
            self.props.append(TollProp(x, y, 175, 112, "cart"))
        self.culvert = TollProp(740, 1770, 250, 175, "culvert")
        self.props.append(self.culvert)
        self.bandit_camp = TollProp(540, 355, 230, 155, "bandit_camp")
        self.props.append(self.bandit_camp)

        for _ in range(28):
            x = self.rng.choice((self.rng.randint(100, 1350), self.rng.randint(2420, self.width - 120)))
            y = self.rng.randint(90, self.height - 120)
            if pygame.Rect(x, y, 82, 65).colliderect(self.quarantine_rect.inflate(100, 100)):
                continue
            self._add(TollProp(x, y, 82, 62, "stone", blocking=True), blocking=True)

        state = kingsreach_state(self.manager)
        harvested = set(state.get("harvested_nodes", ()))
        specs = (
            [("Feverfew", "herb", (1, 2))] * 10
            + [("Clean Bandage", "bandage", (1, 2))] * 7
            + [("Charcoal", "charcoal", (1, 2))] * 6
            + [("Parchment Sheet", "paper", (1, 1))] * 5
        )
        for index, (resource, style, amount) in enumerate(specs):
            if resource in {"Feverfew", "Clean Bandage"}:
                x = self.rng.randint(self.quarantine_rect.left + 55, self.quarantine_rect.right - 80)
                y = self.rng.randint(self.quarantine_rect.top + 55, self.quarantine_rect.bottom - 80)
            elif resource == "Parchment Sheet":
                x = self.rng.randint(2280, 3550)
                y = self.rng.randint(250, 790)
            else:
                x = self.rng.randint(250, 1450)
                y = self.rng.randint(1500, 2150)
            node_id = f"kingsreach_node_{index + 1}"
            node = TollResourceNode(node_id, x, y, resource, style, amount, node_id in harvested)
            self.resources.append(node)
            self.props.append(node)
        self.obstacles = list(self.land_obstacles)

    def refresh_persistent(self, manager):
        harvested = set(kingsreach_state(manager).get("harvested_nodes", ()))
        for node in self.resources:
            node.harvested = node.node_id in harvested
            node._redraw()
        self.obstacles = list(self.land_obstacles)

    def update(self, manager=None):
        self.vfx.update(manager)
        if random.random() < 0.22:
            self.dust.append({
                "x": random.randint(0, self.width),
                "y": random.randint(900, 1400),
                "life": random.randint(45, 110),
                "size": random.randint(3, 10),
            })
        for dust in self.dust:
            dust["x"] += 0.7
            dust["y"] -= 0.08
            dust["life"] -= 1
        self.dust = [dust for dust in self.dust if dust["life"] > 0]
        if random.random() < 0.12:
            self.haze.append({
                "x": random.randint(self.quarantine_rect.left, self.quarantine_rect.right),
                "y": random.randint(self.quarantine_rect.top, self.quarantine_rect.bottom),
                "life": random.randint(50, 120),
                "size": random.randint(12, 28),
            })
        for haze in self.haze:
            haze["y"] -= 0.18
            haze["life"] -= 1
        self.haze = [haze for haze in self.haze if haze["life"] > 0]

    def draw_background(self, screen, offset=(0, 0)):
        screen.blit(self.floor_image, (-int(offset[0]), -int(offset[1])))

    def draw_foreground(self, screen, offset=(0, 0)):
        ox, oy = int(offset[0]), int(offset[1])
        for dust in self.dust:
            x, y = int(dust["x"] - ox), int(dust["y"] - oy)
            if -20 < x < screen.get_width() + 20 and -20 < y < screen.get_height() + 20:
                pygame.draw.circle(screen, (185, 170, 132), (x, y), dust["size"], 1)
        haze_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        for haze in self.haze:
            x, y = int(haze["x"] - ox), int(haze["y"] - oy)
            if -40 < x < screen.get_width() + 40 and -40 < y < screen.get_height() + 40:
                pygame.draw.circle(haze_surface, (123, 145, 104, 24), (x, y), haze["size"])
        screen.blit(haze_surface, (0, 0))
        self.vfx.draw_top(screen, offset)


class KingsreachTollMenu(GameplayScreen):
    def __init__(self, manager):
        super().__init__(manager)
        self.arena = KingsreachTollArena(manager)
        self.monsters = pygame.sprite.Group()
        self.npcs: List[Villager] = []
        self.dynamic_props: List[object] = []
        self.boss: Optional[TollmasterHadrikCrowl] = None
        self.feedback = ""
        self.feedback_timer = 0
        self.warning = ""
        self.warning_timer = 0
        self.dialogue_active = False
        self.dialogue_name = ""
        self.dialogue_pages: List[str] = []
        self.dialogue_index = 0
        self.choice_active = False
        self.choice_mode = ""
        self.choice_title = ""
        self.choice_options: List[str] = []
        self.quarantine_tick = 0

    def on_enter(self):
        super().on_enter()
        self.manager.current_arena = self.arena
        self.manager.current_map_vfx = self.arena.vfx
        self.player = self.manager.player_character
        entry = getattr(self.manager, "kingsreach_entry", None) or "greywash_ford"
        self.manager.kingsreach_entry = None
        if entry == "rattlebridge":
            self.player.rect.center = (120, 1150)
            self.player.facing_right = True
        else:
            self.player.rect.center = (3650, 1150)
            self.player.facing_right = False
        self.player.is_dead = False
        self.player.current_hp = max(1, self.player.current_hp)

        state = kingsreach_state(self.manager)
        today = _world_day(self.manager)
        if int(state.get("resource_day", -1)) != today:
            state["resource_day"] = today
            state["harvested_nodes"] = []
        state["visits"] = int(state.get("visits", 0)) + 1
        sync_kingsreach_story(self.manager)
        self.arena.refresh_persistent(self.manager)
        self.monsters.empty()
        self._spawn_baseline_threats()
        self._ensure_story_threats()
        self._refresh_npcs()
        self._spawn_boss_if_needed()
        self._update_camera()
        try:
            advice = self.manager.get_tier0_area_advice("kingsreach_toll")
            self.warning = advice.get("warning", "CROWN CHECKPOINT — recommended Lv 6-8")
        except Exception:
            self.warning = "CROWN CHECKPOINT — recommended Lv 6-8"
        self.warning_timer = 420
        try:
            from systems.world_progression import mark_location_visited

            mark_location_visited(self.manager, "kingsreach_toll", set_current=True, surveyed=True)
        except Exception:
            pass
        try:
            self.manager.record_tier0_event("visit", "kingsreach_toll")
            self.manager.record_tier0_event("risk_seen", "kingsreach_toll")
        except Exception:
            pass

    @staticmethod
    def _npc(name, race, x, y, role):
        npc = Villager(name, race, x, y, team_color=GREEN)
        npc.ai_controller = None
        npc.name = str(name)
        npc.kingsreach_role = str(role)
        npc.animation_state = "idle"
        return npc

    def _refresh_npcs(self):
        for prop in list(self.dynamic_props):
            if prop in self.arena.props:
                self.arena.props.remove(prop)
        self.npcs = [
            self._npc("Toll Captain Elric Dorn", "Human", 2350, 1120, "captain"),
            self._npc("Medic Vela Marrow", "Human", 2910, 1770, "medic"),
            self._npc("Salla Quill", "Dwarf", 3010, 650, "merchant"),
            self._npc("Nix Quickreed", "Goblin", 980, 1860, "smuggler"),
        ]
        self.dynamic_props = list(self.npcs)
        self.arena.props.extend(self.dynamic_props)

    def _spawn_baseline_threats(self):
        state = kingsreach_state(self.manager)
        cleared = bool(state.get("completed"))
        bandits = 2 if cleared else 5
        escapees = 1 if cleared else 4
        for index in range(bandits):
            monster = CausewayBandit(
                f"Causeway Bandit {index + 1}",
                440 + (index % 3) * 180,
                360 + (index // 3) * 180,
                ENEMY_TEAM,
            )
            monster.kingsreach_counted = True
            self.monsters.add(monster)
        for index in range(escapees):
            monster = FeveredEscapee(
                f"Fevered Escapee {index + 1}",
                2780 + (index % 2) * 260,
                1640 + (index // 2) * 230,
                ENEMY_TEAM,
            )
            monster.kingsreach_counted = False
            monster.kingsreach_quest_tag = "escapee"
            self.monsters.add(monster)

    def _ensure_story_threats(self):
        state = kingsreach_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        if stage == 3:
            remaining = max(0, SERVICE_ESCAPEES - int(state.get("service_escapees", 0)))
            living = [m for m in self.monsters if not m.is_dead and getattr(m, "kingsreach_quest_tag", "") == "escapee"]
            for index in range(max(0, remaining - len(living))):
                monster = FeveredEscapee(
                    f"Quarantine Escapee {index + 1}",
                    2870 + index * 110,
                    1840 + (index % 2) * 100,
                    ENEMY_TEAM,
                )
                monster.kingsreach_counted = False
                monster.kingsreach_quest_tag = "escapee"
                self.monsters.add(monster)
        elif stage == 4:
            living_enforcers = [m for m in self.monsters if not m.is_dead and isinstance(m, CrownTollEnforcer)]
            for index in range(max(0, 4 - len(living_enforcers))):
                monster = CrownTollEnforcer(
                    f"Culvert Enforcer {index + 1}",
                    1040 + (index % 2) * 190,
                    1570 + (index // 2) * 170,
                    ENEMY_TEAM,
                )
                monster.kingsreach_counted = True
                self.monsters.add(monster)

    def _spawn_boss_if_needed(self):
        state = kingsreach_state(self.manager)
        self.boss = None
        if not state.get("boss_unlocked") or state.get("boss_defeated"):
            return
        self.boss = TollmasterHadrikCrowl("Tollmaster Hadrik Crowl", 720, 1210, ENEMY_TEAM)
        self.monsters.add(self.boss)
        self._flash("Tollmaster Crowl seals the smuggler culvert behind you.", 330)

    def _near(self, rect, inflate=78):
        return self.player.rect.colliderect(pygame.Rect(rect).inflate(inflate, inflate))

    def _flash(self, message, duration=220):
        self.feedback = str(message)
        self.feedback_timer = int(duration)

    @staticmethod
    def _wrap(text, font, width):
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

    def _open_dialogue(self, name, pages: Sequence[str]):
        self.dialogue_name = str(name)
        self.dialogue_pages = [str(page) for page in pages]
        self.dialogue_index = 0
        self.dialogue_active = True
        _safe_sound("click")

    def _open_choice(self, mode):
        self.choice_mode = str(mode)
        self.choice_active = True
        if mode == "resolution":
            self.choice_title = "Choose how to clear Kingsreach Toll"
            self.choice_options = [
                "Present Vale evidence and request official papers",
                f"Pay the full Crown toll — {TOLL_FEE} SP",
                "Volunteer for quarantine service",
                "Leave and seek another route",
            ]
        elif mode == "smuggler":
            self.choice_title = "Nix Quickreed's culvert route"
            self.choice_options = [
                f"Pay {SMUGGLER_FEE} SP and enter the culvert",
                "Decline the smuggler route",
            ]
        elif mode == "merchant":
            self.choice_title = "Salla Quill's checkpoint stock"
            self.choice_options = [
                "Buy Parchment Sheet — 18 SP",
                "Buy Wax Seal — 28 SP",
                "Buy Clean Bandage — 12 SP",
                "Close trade",
            ]
        _safe_sound("click")

    def _resolve_choice(self, index):
        index = int(index)
        mode = self.choice_mode
        self.choice_active = False
        state = kingsreach_state(self.manager)
        if mode == "resolution":
            if index == 0:
                if not _consume_cost(self.manager, OFFICIAL_EVIDENCE, keep=("Vale's Broken Signet",)):
                    self._flash(f"Official evidence requires: {_cost_text(OFFICIAL_EVIDENCE)}", 280)
                    _safe_sound("error")
                    return
                state["resolution"] = "official_evidence"
                state["quest_stage"] = 5
                _modify_crown_rep(self.manager, 8)
                self._flash("Vale's evidence accepted. Captain Dorn can issue the travel papers.", 300)
            elif index == 1:
                if int(self.manager.gold) < TOLL_FEE:
                    self._flash(f"The full Crown toll is {TOLL_FEE} SP.")
                    _safe_sound("error")
                    return
                self.manager.gold -= TOLL_FEE
                state["toll_paid"] = True
                state["resolution"] = "paid"
                state["quest_stage"] = 5
                _modify_crown_rep(self.manager, 2)
                self._flash("Toll paid. Captain Dorn can stamp the travel papers.", 280)
            elif index == 2:
                state["service_started"] = True
                state["resolution"] = "quarantine_service"
                state["quest_stage"] = 3
                self._ensure_story_threats()
                self._flash(f"Service accepted: {_cost_text(SERVICE_COST)} and {SERVICE_ESCAPEES} escapees.", 320)
            else:
                self._flash("Nix Quickreed waits beside the south-west culvert.")
        elif mode == "smuggler":
            if index == 0:
                if int(self.manager.gold) < SMUGGLER_FEE:
                    self._flash(f"Nix requires {SMUGGLER_FEE} SP before opening the grate.")
                    _safe_sound("error")
                    return
                self.manager.gold -= SMUGGLER_FEE
                state["smuggler_paid"] = True
                state["resolution"] = "smuggling"
                state["quest_stage"] = 4
                state["boss_unlocked"] = True
                _modify_crown_rep(self.manager, -5)
                self._ensure_story_threats()
                self._spawn_boss_if_needed()
                self._flash("The culvert opens. Crowl's collectors move to intercept you.", 320)
            else:
                self._flash("Nix closes the grate and pockets the key.")
        elif mode == "merchant":
            offers = (("Parchment Sheet", 18), ("Wax Seal", 28), ("Clean Bandage", 12))
            if 0 <= index < len(offers):
                item, price = offers[index]
                if int(self.manager.gold) < price:
                    self._flash(f"{item} costs {price} SP.")
                    _safe_sound("error")
                    return
                self.manager.gold -= price
                self.manager.inventory[item] = int(self.manager.inventory.get(item, 0)) + 1
                state["merchant_purchases"] = int(state.get("merchant_purchases", 0)) + 1
                self._flash(f"Purchased {item} for {price} SP.")
            else:
                self._flash("Trade closed.")

    def _captain_dialogue(self):
        state = kingsreach_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        if stage == 0:
            state["quest_stage"] = 1
            self._open_dialogue(
                "Toll Captain Elric Dorn",
                (
                    "Greywash is open again, but the King's road is counted stone. Nobody crosses this gate without inspection and a lawful reason.",
                    "Report to Medic Vela Marrow. After quarantine clearance you may present papers, pay the toll, serve the checkpoint or find a route I will not recommend.",
                    "Captain Garran Vale's signet and orders would be strong evidence if you recovered them at the ford.",
                ),
            )
        elif stage == 1:
            self._open_dialogue("Toll Captain Elric Dorn", ("Quarantine inspection comes first. Medic Vela Marrow is in the south-east camp.",))
        elif stage == 2:
            self._open_choice("resolution")
        elif stage in (3, 4):
            route = "quarantine service" if stage == 3 else "the south-west culvert"
            self._open_dialogue("Toll Captain Elric Dorn", (f"You selected {route}. Finish what you started before asking for a stamp.",))
        elif stage == 5:
            self._issue_pass()
        elif stage == 6:
            self._open_dialogue(
                "Toll Captain Elric Dorn",
                (
                    "Your road papers are valid, but Rattlebridge only accepts promoted Tier 1 teams through the professional gate.",
                    "Take the Crown Promotion Docket to Bram Carrow. His recommendation completes the legal chain.",
                ),
            )
        else:
            self._open_dialogue("Toll Captain Elric Dorn", ("Your papers and promotion are both valid. The western gate is open to Rattlebridge.",))

    def _medic_dialogue(self):
        state = kingsreach_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        if stage == 1:
            state["inspection_complete"] = True
            sync_kingsreach_story(self.manager)
            self._open_dialogue(
                "Medic Vela Marrow",
                (
                    "No active water-fever in your eyes. The marsh has marked you, but not enough for isolation.",
                    "Inspection cleared. Dorn will now offer the legal routes. I can also sponsor passage if you complete quarantine service.",
                ),
            )
        elif stage == 3:
            escapees = int(state.get("service_escapees", 0))
            if escapees < SERVICE_ESCAPEES or not _has_cost(self.manager, SERVICE_COST):
                self._open_dialogue(
                    "Medic Vela Marrow",
                    (f"We still need {_cost_text(SERVICE_COST)} and {SERVICE_ESCAPEES} contained escapees. Current containment: {escapees}/{SERVICE_ESCAPEES}.",),
                )
                return
            _consume_cost(self.manager, SERVICE_COST)
            state["service_complete"] = True
            sync_kingsreach_story(self.manager)
            _modify_crown_rep(self.manager, 10)
            self.manager.reputation = int(getattr(self.manager, "reputation", 0)) + 5
            self._open_dialogue(
                "Medic Vela Marrow",
                (
                    "The tents are supplied and the escapees are contained. I have signed your service waiver.",
                    "Dorn can now issue your stamped travel papers. +5 reputation and strong Crown service credit.",
                ),
            )
            self._flash("Quarantine service complete. Return to Captain Dorn.", 300)
        else:
            self._open_dialogue("Medic Vela Marrow", ("The quarantine line is holding. Feverfew and clean bandages remain useful trade goods here.",))

    def _merchant_dialogue(self):
        self._open_choice("merchant")

    def _smuggler_dialogue(self):
        state = kingsreach_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        if stage == 2:
            self._open_choice("smuggler")
        elif stage == 4:
            self._open_dialogue(
                "Nix Quickreed",
                (
                    "Crowl knew the grate was being used. His collectors are between you and the western road now.",
                    "Beat Crowl and his black ledger becomes better paperwork than any forged pass.",
                ),
            )
        elif state.get("boss_defeated"):
            self._open_dialogue("Nix Quickreed", ("Crowl is gone and the ledger is yours. Dorn cannot ignore proof that large.",))
        else:
            self._open_dialogue("Nix Quickreed", ("No need for a culvert when your papers are already stamped. Unless you enjoy wet boots.",))

    def _issue_pass(self):
        state = kingsreach_state(self.manager)
        if state.get("pass_issued"):
            sync_kingsreach_story(self.manager)
            return
        state["pass_issued"] = True
        state["completed"] = True
        self.manager.inventory["Stamped Crown Travel Papers"] = int(self.manager.inventory.get("Stamped Crown Travel Papers", 0)) + 1
        self.manager.inventory["Crown Promotion Docket"] = int(self.manager.inventory.get("Crown Promotion Docket", 0)) + 1
        reward = 0
        if state.get("resolution") == "quarantine_service":
            reward = 35
        elif state.get("resolution") == "official_evidence":
            reward = 20
        elif state.get("resolution") == "smuggling":
            reward = 55
        self.manager.gold += reward
        sync_kingsreach_story(self.manager)
        try:
            self.manager.record_tier0_event("quest", "kingsreach_toll_cleared")
            self.manager.record_tier0_event("flag", "kingsreach_cleared")
            self.manager.record_tier0_event("flag", "bram_recommendation_requested")
            self.manager.record_deed("kingsreach_toll", f"cleared Kingsreach Toll through {state.get('resolution') or 'checkpoint service'}")
        except Exception:
            pass
        self._open_dialogue(
            "Toll Captain Elric Dorn",
            (
                "Kingsreach Toll is cleared in your name. These stamped travel papers are valid on the counted Crown road.",
                f"Take the Crown Promotion Docket to Bram Carrow. Reward: {reward} SP. His recommendation is the final Tier 0 requirement.",
            ),
        )
        self._flash("Kingsreach cleared. Return the Promotion Docket to Bram.", 420)

    def _try_npc(self):
        for npc in self.npcs:
            if not self._near(npc.rect, 78):
                continue
            role = getattr(npc, "kingsreach_role", "")
            if role == "captain":
                self._captain_dialogue()
            elif role == "medic":
                self._medic_dialogue()
            elif role == "merchant":
                self._merchant_dialogue()
            else:
                self._smuggler_dialogue()
            return True
        return False

    def _try_gather(self):
        for node in self.arena.resources:
            if node.harvested or not self._near(node.rect, 72):
                continue
            message = node.harvest(self.manager)
            if message:
                self._flash(message)
            return True
        return False

    def handle_event(self, event):
        if self.choice_active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.choice_active = False
                    return
                keys = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4)
                if event.key in keys:
                    index = keys.index(event.key)
                    if index < len(self.choice_options):
                        self._resolve_choice(index)
                    return
            return
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
            if self._try_npc() or self._try_gather():
                return

    def _count_service_escapees(self):
        state = kingsreach_state(self.manager)
        if int(state.get("quest_stage", 0)) != 3:
            return
        changed = False
        for monster in self.monsters:
            if not monster.is_dead or getattr(monster, "kingsreach_counted", False):
                continue
            monster.kingsreach_counted = True
            if getattr(monster, "kingsreach_quest_tag", "") == "escapee":
                state["service_escapees"] = min(
                    SERVICE_ESCAPEES,
                    int(state.get("service_escapees", 0)) + 1,
                )
                changed = True
        if changed:
            self._flash(f"Fevered Escapees contained: {int(state.get('service_escapees', 0))}/{SERVICE_ESCAPEES}")

    def _transfer_loot(self):
        loot = self.manager.round_rewards.get("loot")
        if not loot:
            return
        for name, amount in list(loot.items()):
            self.manager.inventory[name] = int(self.manager.inventory.get(name, 0)) + int(amount)
        self.manager.round_rewards["loot"] = {}

    def _apply_quarantine_hazard(self):
        if not self.arena.quarantine_rect.collidepoint(self.player.rect.center):
            self.quarantine_tick = 0
            return
        self.quarantine_tick += 1
        if self.quarantine_tick % 90 != 0:
            return
        state = kingsreach_state(self.manager)
        state["quarantine_exposure"] = min(100, int(state.get("quarantine_exposure", 0)) + 3)
        try:
            self.player.apply_status("Slow", 65, 0)
        except Exception:
            pass
        if int(state.get("quarantine_exposure", 0)) % 18 == 0:
            try:
                self.player.take_damage(4, "Poison", manager=self.manager)
            except Exception:
                self.player.current_hp = max(1, self.player.current_hp - 4)
            self._flash("Water-fever haze weakens you inside the quarantine line.", 100)

    def _process_boss(self):
        if self.boss is None:
            return
        if self.boss.pending_spawn:
            for monster in list(self.boss.pending_spawn):
                self.monsters.add(monster)
            self.boss.pending_spawn = []
            self._flash("Crowl calls collectors and paid knives into the culvert yard.")
        if self.boss.pending_tax_shout:
            self.boss.pending_tax_shout = False
            self.boss.release_tax_shout([self.player], self.manager)
        if self.boss.pending_stamp_shock:
            self.boss.pending_stamp_shock = False
            distance = math.hypot(
                self.player.rect.centerx - self.boss.rect.centerx,
                self.player.rect.centery - self.boss.rect.centery,
            )
            if distance < 470:
                try:
                    self.player.take_damage(18, "Physical", attacker=self.boss, manager=self.manager)
                    self.player.apply_status("Slow", 120, 0)
                except Exception:
                    self.player.current_hp = max(1, self.player.current_hp - 18)
            try:
                self.manager.vfx.create_shockwave(self.boss.rect.centerx, self.boss.rect.bottom, color=(196, 156, 71), max_radius=205)
            except Exception:
                pass
            self._flash("Crowl slams the Crown stamp into the causeway.", 120)
        if not self.boss.is_dead:
            return
        state = kingsreach_state(self.manager)
        if state.get("boss_defeated"):
            return
        state["boss_defeated"] = True
        state["boss_unlocked"] = False
        if not state.get("boss_reward_claimed"):
            self.manager.gold += 90
            self.manager.reputation = int(getattr(self.manager, "reputation", 0)) + 6
            self.manager.inventory["Crowl's Black Ledger"] = int(self.manager.inventory.get("Crowl's Black Ledger", 0)) + 1
            self.manager.inventory["Crown Seal Token"] = int(self.manager.inventory.get("Crown Seal Token", 0)) + 1
            state["boss_reward_claimed"] = True
        sync_kingsreach_story(self.manager)
        try:
            self.manager.record_tier0_event("boss", "tollmaster_hadrik_crowl")
            self.manager.record_tier0_event("flag", "kingsreach_corruption_exposed")
        except Exception:
            pass
        self._flash("Tollmaster Crowl defeated. His ledger forces Captain Dorn to issue papers.", 420)

    def update(self):
        if self.choice_active or self.dialogue_active or self.manager.paused:
            if self.feedback_timer > 0:
                self.feedback_timer -= 1
            return
        living = [monster for monster in self.monsters if not monster.is_dead]
        self._update_gameplay([self.player] + living)
        self._count_service_escapees()
        self._transfer_loot()
        self._apply_quarantine_hazard()
        self._process_boss()
        sync_kingsreach_story(self.manager)

        if self.player.is_dead:
            self.player.is_dead = False
            self.player.current_hp = max(1, int(self.player.max_hp * 0.3))
            self.manager.pending_local_area = "kingsreach_toll"
            self.manager.pending_world_location = "kingsreach_toll"
            self.manager.kingsreach_entry = "greywash_ford"
            self.next_state = "regional_staging"
            return
        if self.player.rect.colliderect(self.arena.east_exit):
            self.manager.pending_local_area = "greywash_ford"
            self.manager.pending_world_location = "greywash_ford"
            self.manager.greywash_entry = "kingsreach"
            self.next_state = "regional_staging"
            return
        if self.player.rect.colliderect(self.arena.west_exit):
            state = kingsreach_state(self.manager)
            if int(state.get("quest_stage", 0)) >= 7:
                self.manager.pending_world_location = "rattlebridge"
                self.manager.kingsreach_entry = "rattlebridge"
                try:
                    self.manager.record_tier0_event("flag", "rattlebridge_arrived")
                except Exception:
                    pass
                self.next_state = "rattlebridge_city"
            elif state.get("completed"):
                self.player.rect.left = 48
                self._flash("Rattlebridge requires Bram's Tier 1 recommendation and formal promotion.", 180)
            else:
                self.player.rect.left = 48
                self._flash("The Crown gate remains closed until Kingsreach Toll is resolved.", 180)
            return
        if self.feedback_timer > 0:
            self.feedback_timer -= 1
        if self.warning_timer > 0:
            self.warning_timer -= 1

    def _nearest_prompt(self):
        for npc in self.npcs:
            if self._near(npc.rect, 78):
                return npc.rect, f"Talk to {npc.name}"
        for node in self.arena.resources:
            if not node.harvested and self._near(node.rect, 72):
                return node.rect, f"Gather {node.resource_name}"
        return None

    def _draw_dialogue(self, screen):
        if not self.dialogue_active or not self.dialogue_pages:
            return
        panel = pygame.Rect(165, SCREEN_HEIGHT - 260, SCREEN_WIDTH - 330, 205)
        overlay = pygame.Surface(panel.size, pygame.SRCALPHA)
        overlay.fill((22, 24, 24, 243))
        screen.blit(overlay, panel.topleft)
        pygame.draw.rect(screen, (174, 145, 78), panel, 3, border_radius=9)
        draw_text(self.dialogue_name, font_main, GOLD_COLOR, screen, panel.x + 24, panel.y + 18)
        y = panel.y + 60
        for line in self._wrap(self.dialogue_pages[self.dialogue_index], font_main, panel.w - 48)[:4]:
            draw_text(line, font_main, WHITE, screen, panel.x + 24, y)
            y += 29
        draw_text("[E / Enter] continue    [Esc] close", font_small, GRAY, screen, panel.right - 355, panel.bottom - 27)

    def _draw_choice(self, screen):
        if not self.choice_active:
            return
        panel = pygame.Rect(310, 205, SCREEN_WIDTH - 620, 430)
        overlay = pygame.Surface(panel.size, pygame.SRCALPHA)
        overlay.fill((21, 23, 24, 246))
        screen.blit(overlay, panel.topleft)
        pygame.draw.rect(screen, (185, 151, 80), panel, 3, border_radius=12)
        draw_text(self.choice_title, font_main, GOLD_COLOR, screen, panel.x + 30, panel.y + 28)
        y = panel.y + 88
        for index, option in enumerate(self.choice_options):
            color = WHITE if index < 3 else GRAY
            draw_text(f"[{index + 1}] {option}", font_main, color, screen, panel.x + 44, y)
            y += 67
        draw_text("Esc: close", font_small, GRAY, screen, panel.right - 120, panel.bottom - 32)

    def draw(self, screen):
        living = [monster for monster in self.monsters if not monster.is_dead]
        self._draw_gameplay(screen, [self.player] + living)
        if not self.choice_active and not self.dialogue_active:
            prompt = self._nearest_prompt()
            if prompt:
                rect, label = prompt
                try:
                    self.manager._draw_floating_prompt(screen, rect.centerx, rect.top - 17, "E", (self.camera_x, self.camera_y), label)
                except Exception:
                    pass
        state = kingsreach_state(self.manager)
        draw_text("KINGSREACH TOLL — CROWN CHECKPOINT Lv 6-8", font_small, WHITE, screen, 34, 32)
        draw_text(f"CHECKPOINT: {kingsreach_objective(self.manager)}", font_small, (224, 197, 126), screen, 34, 58)
        draw_text(
            f"Route: {state.get('resolution') or 'UNDECIDED'}   Exposure: {int(state.get('quarantine_exposure', 0))}%   "
            f"Escapees: {int(state.get('service_escapees', 0))}/{SERVICE_ESCAPEES}   Pass: {'STAMPED' if state.get('pass_issued') else 'NONE'}",
            font_small,
            GRAY,
            screen,
            34,
            84,
        )
        draw_text(
            "East: Greywash Ford   West: Rattlebridge — Tier 1 promotion required after checkpoint clearance",
            font_small,
            (157, 192, 204),
            screen,
            34,
            108,
        )
        if self.warning_timer > 0:
            surface = font_main.render(self.warning, True, (237, 157, 87))
            screen.blit(surface, (SCREEN_WIDTH // 2 - surface.get_width() // 2, 138))
        if self.feedback_timer > 0:
            surface = font_main.render(self.feedback, True, GOLD_COLOR)
            screen.blit(surface, (SCREEN_WIDTH // 2 - surface.get_width() // 2, 172))
        self._draw_dialogue(screen)
        self._draw_choice(screen)
