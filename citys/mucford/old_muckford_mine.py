"""Expanded Old Muckford Mine with restoration, rescues and Webbed Depths.

This replaces the small cave interior at runtime while retaining the existing
Muckford mine road and key gate. All placeholder art is generated in pygame and
can later be replaced without changing quest, collision or save data.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Sequence, Tuple

import pygame

from assets.tiles.prop import Prop
from citys.mucford.mine_cave_arena import CoalDeposit, RubyVein, SilverVein
from crafting.ores.iron_ore import IronOre
from menus.gameplay_screen import GameplayScreen
from settings import ENEMY_TEAM, GOLD_COLOR, GRAY, GREEN, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from ui_kit import draw_text, font_main, font_small
from units.old_muckford_mine_monsters import (
    BroodGuard,
    CrystalHusk,
    DeepCaveBroodmother,
    GravePickman,
    RailWraith,
    WebCrawler,
)
from units.villager import Villager


MINE_WIDTH = 3800
MINE_HEIGHT = 2400
MINE_SEED = 44017
PRODUCTION_COST = {"Iron Ore": 8, "Coal": 5, "Softwood": 4}

MINE_OBJECTIVES = {
    0: "Speak with Foreman Torra Flintvein at the old mine entrance.",
    1: "Relight the three mine lantern stations using Coal.",
    2: "Find and rescue the three missing miners.",
    3: "Clear the three marked collapse piles with a pickaxe.",
    4: "Destroy the four Webbed Depths egg sacs.",
    5: "Defeat the Cave Broodmother in the deep chamber.",
    6: "Restart controlled ore production at the entrance winch.",
    7: "Old Muckford Mine restored. Continue mining or return to town.",
}


def _safe_sound(name: str) -> None:
    try:
        sound_system.play_sound(name)
    except Exception:
        pass


def _day_key(manager) -> str:
    clock = getattr(manager, "world_clock", None)
    return f"{int(getattr(clock, 'year', 0))}:{int(getattr(clock, 'day', 1))}"


def old_mine_state(manager) -> dict:
    global_data = manager.npc_state.setdefault("global", {})
    state = global_data.setdefault("old_muckford_mine", {})
    state.setdefault("visits", 0)
    state.setdefault("quest_stage", 0)
    state.setdefault("road_secured", False)
    state.setdefault("lanterns_lit", [])
    state.setdefault("rescued_miners", [])
    state.setdefault("cleared_collapses", [])
    state.setdefault("egg_sacs_destroyed", [])
    state.setdefault("boss_unlocked", False)
    state.setdefault("boss_defeated", False)
    state.setdefault("boss_reward_claimed", False)
    state.setdefault("production_restarted", False)
    state.setdefault("production_reward_claimed", False)
    state.setdefault("supplies_claimed", False)
    state.setdefault("completed", False)
    state.setdefault("ore_day", _day_key(manager))
    state.setdefault("depleted_ores", [])
    state.setdefault("collapse_hits", 0)
    if state["ore_day"] != _day_key(manager):
        state["ore_day"] = _day_key(manager)
        state["depleted_ores"] = []
    return state


def sync_old_mine_story(manager) -> bool:
    state = old_mine_state(manager)
    changed = False
    while True:
        stage = int(state.get("quest_stage", 0))
        if stage == 1 and len(set(state.get("lanterns_lit", ()))) >= 3:
            state["quest_stage"] = 2
        elif stage == 2 and len(set(state.get("rescued_miners", ()))) >= 3:
            state["quest_stage"] = 3
        elif stage == 3 and len(set(state.get("cleared_collapses", ()))) >= 3:
            state["quest_stage"] = 4
        elif stage == 4 and len(set(state.get("egg_sacs_destroyed", ()))) >= 4:
            state["quest_stage"] = 5
            state["boss_unlocked"] = True
        elif state.get("boss_defeated") and stage < 6:
            state["quest_stage"] = 6
        elif state.get("production_restarted") and stage < 7:
            state["quest_stage"] = 7
            state["completed"] = True
        else:
            break
        changed = True
    return changed


def mine_objective(manager) -> str:
    sync_old_mine_story(manager)
    stage = int(old_mine_state(manager).get("quest_stage", 0))
    return MINE_OBJECTIVES.get(stage, MINE_OBJECTIVES[7])


def _has_materials(manager, cost: Dict[str, int]) -> bool:
    return all(int(manager.inventory.get(name, 0)) >= amount for name, amount in cost.items())


def _consume_materials(manager, cost: Dict[str, int]) -> bool:
    if not _has_materials(manager, cost):
        return False
    for name, amount in cost.items():
        manager.inventory[name] = int(manager.inventory.get(name, 0)) - amount
        if manager.inventory[name] <= 0:
            manager.inventory.pop(name, None)
    return True


def _cost_text(cost: Dict[str, int]) -> str:
    return ", ".join(f"{amount} {name}" for name, amount in cost.items())


class MineProp(Prop):
    def __init__(self, x: int, y: int, width: int, height: int, style: str, blocking=False):
        super().__init__(x, y, width, height, color=(0, 0, 0))
        self.style = style
        self.image_pos = (x, y)
        self.is_structure = bool(blocking)
        self.blocks_projectiles = bool(blocking)
        self.has_shadow = style not in {"rail", "lantern", "marker"}
        self._draw()

    def _draw(self):
        w, h = self.rect.size
        image = pygame.Surface((w, h), pygame.SRCALPHA)
        if self.style == "rock":
            pygame.draw.polygon(image, (49, 46, 45), [(4, h - 8), (7, 25), (w // 3, 5), (w - 13, 12), (w - 3, h - 12)])
            pygame.draw.polygon(image, (72, 68, 63), [(w // 3, 5), (w - 13, 12), (w * 2 // 3, h // 2), (w // 4, h // 2)])
        elif self.style == "support":
            pygame.draw.rect(image, (85, 57, 35), (8, 7, 13, h - 12))
            pygame.draw.rect(image, (85, 57, 35), (w - 21, 7, 13, h - 12))
            pygame.draw.rect(image, (112, 77, 45), (3, 5, w - 6, 15))
            pygame.draw.line(image, (58, 42, 31), (20, h - 10), (w - 19, 18), 6)
        elif self.style == "rail":
            pygame.draw.line(image, (91, 80, 69), (3, 8), (w - 3, 8), 4)
            pygame.draw.line(image, (91, 80, 69), (3, h - 8), (w - 3, h - 8), 4)
            for x in range(8, w, 30):
                pygame.draw.line(image, (91, 60, 37), (x, 2), (x, h - 2), 6)
        elif self.style == "cart":
            pygame.draw.circle(image, (48, 43, 39), (20, h - 15), 13)
            pygame.draw.circle(image, (48, 43, 39), (w - 20, h - 15), 13)
            pygame.draw.polygon(image, (82, 68, 55), [(8, 16), (w - 8, 16), (w - 18, h - 18), (18, h - 18)])
            pygame.draw.line(image, (121, 97, 69), (15, 20), (w - 15, 20), 3)
        elif self.style == "winch":
            pygame.draw.line(image, (91, 62, 37), (20, h - 5), (20, 20), 8)
            pygame.draw.line(image, (91, 62, 37), (w - 20, h - 5), (w - 20, 20), 8)
            pygame.draw.line(image, (123, 87, 48), (15, 20), (w - 15, 20), 9)
            pygame.draw.circle(image, (78, 75, 69), (w // 2, h // 2), 24, 7)
            pygame.draw.line(image, (137, 116, 83), (w // 2, h // 2), (w // 2 + 37, h // 2 - 18), 5)
        elif self.style == "web_gate":
            for x in range(4, w, max(8, w // 4)):
                pygame.draw.line(image, (221, 219, 232, 210), (x, 0), (w - x, h), 2)
            for y in range(10, h, 32):
                pygame.draw.arc(image, (238, 237, 247, 160), (2, y - 14, w - 4, 28), 0, math.pi, 2)
        self.image = image


class LanternStation(Prop):
    def __init__(self, station_id: str, x: int, y: int, lit=False):
        super().__init__(x, y, 74, 104, color=(0, 0, 0))
        self.station_id = str(station_id)
        self.lit = bool(lit)
        self.rect = pygame.Rect(x + 20, y + 55, 34, 42)
        self.image_pos = (x, y)
        self.blocks_projectiles = False
        self.has_shadow = True
        self._redraw()

    def _redraw(self):
        image = pygame.Surface((74, 104), pygame.SRCALPHA)
        pygame.draw.line(image, (94, 65, 40), (37, 100), (37, 23), 6)
        pygame.draw.line(image, (94, 65, 40), (37, 25), (56, 25), 5)
        pygame.draw.rect(image, (95, 89, 73), (47, 26, 20, 31), 3, border_radius=4)
        pygame.draw.line(image, (65, 59, 51), (52, 30), (52, 53), 2)
        pygame.draw.line(image, (65, 59, 51), (62, 30), (62, 53), 2)
        if self.lit:
            pygame.draw.circle(image, (239, 171, 67), (57, 43), 9)
            pygame.draw.circle(image, (255, 224, 130), (57, 39), 5)
        else:
            pygame.draw.circle(image, (55, 52, 47), (57, 43), 7)
        self.image = image


class CollapsePile(Prop):
    def __init__(self, pile_id: str, x: int, y: int, cleared=False):
        super().__init__(x, y, 120, 82, color=(0, 0, 0))
        self.pile_id = str(pile_id)
        self.cleared = bool(cleared)
        self.rect = pygame.Rect(x + 5, y + 42, 110, 35)
        self.image_pos = (x, y)
        self.is_structure = not self.cleared
        self.blocks_projectiles = not self.cleared
        self._redraw()

    def _redraw(self):
        image = pygame.Surface((120, 82), pygame.SRCALPHA)
        if self.cleared:
            for x, y, r in ((20, 62, 8), (51, 67, 6), (87, 63, 7)):
                pygame.draw.circle(image, (66, 62, 58), (x, y), r)
        else:
            rocks = ((18, 55, 21), (43, 42, 27), (72, 51, 25), (99, 43, 20), (59, 24, 24))
            for x, y, r in rocks:
                pygame.draw.circle(image, (61, 58, 55), (x, y), r)
                pygame.draw.arc(image, (90, 84, 76), (x - r, y - r, r * 2, r * 2), 3.3, 5.8, 3)
        self.image = image


class EggSac(Prop):
    def __init__(self, sac_id: str, x: int, y: int, destroyed=False):
        super().__init__(x, y, 74, 84, color=(0, 0, 0))
        self.sac_id = str(sac_id)
        self.destroyed = bool(destroyed)
        self.rect = pygame.Rect(x + 11, y + 42, 52, 34)
        self.image_pos = (x, y)
        self.blocks_projectiles = False
        self._redraw()

    def _redraw(self):
        image = pygame.Surface((74, 84), pygame.SRCALPHA)
        if self.destroyed:
            pygame.draw.ellipse(image, (83, 57, 73, 120), (7, 62, 60, 12))
            pygame.draw.line(image, (214, 207, 222), (17, 60), (58, 74), 2)
        else:
            pygame.draw.ellipse(image, (176, 167, 184), (13, 18, 48, 58))
            pygame.draw.ellipse(image, (222, 216, 228), (20, 24, 33, 42), 3)
            for x, y in ((25, 34), (43, 28), (36, 49), (47, 58), (26, 61)):
                pygame.draw.circle(image, (118, 63, 102), (x, y), 4)
            pygame.draw.line(image, (224, 222, 235), (2, 15), (70, 78), 2)
            pygame.draw.line(image, (224, 222, 235), (70, 13), (4, 79), 2)
        self.image = image


class StoneDeposit(IronOre):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.name = "Stone Deposit"
        self.resource_name = "Stone"
        self.max_hits = random.randint(2, 4)
        self.current_hits = self.max_hits
        for key in ("full", "hit", "empty"):
            surface = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.polygon(surface, (79, 76, 72), [(5, 50), (9, 25), (24, 9), (46, 11), (56, 36), (47, 53)])
            if key != "empty":
                pygame.draw.polygon(surface, (115, 109, 99), [(24, 9), (46, 11), (35, 30), (17, 28)])
            self.sprites[key] = surface
        self.image = self.sprites["full"]


class OldMuckfordMineArena:
    def __init__(self, manager):
        self.manager = manager
        self.width = MINE_WIDTH
        self.height = MINE_HEIGHT
        self.props: List[object] = []
        self.floor_props: List[object] = []
        self.obstacles: List[object] = []
        self.ore_nodes: List[IronOre] = []
        self.lanterns: List[LanternStation] = []
        self.collapses: List[CollapsePile] = []
        self.egg_sacs: List[EggSac] = []
        self.web_gate: Optional[MineProp] = None
        self.rng = random.Random(MINE_SEED)
        self.floor_image = pygame.Surface((self.width, self.height))
        self.dust = []
        self.collapse_zones = {
            "north_fall": pygame.Rect(1180, 330, 520, 430),
            "rail_fall": pygame.Rect(1850, 1010, 560, 430),
            "deep_fall": pygame.Rect(2720, 1510, 430, 420),
        }
        self.entrance_zone = pygame.Rect(0, 760, 760, 900)
        self.deep_zone = pygame.Rect(2960, 180, 760, 2040)
        self._generate_floor()
        self._build_level()
        self.refresh_persistent(manager)

    def _generate_floor(self):
        self.floor_image.fill((34, 31, 30))
        for _ in range(1800):
            x = self.rng.randrange(self.width)
            y = self.rng.randrange(self.height)
            shade = self.rng.randint(-8, 12)
            pygame.draw.circle(self.floor_image, (34 + shade, 31 + shade, 30 + shade), (x, y), self.rng.randint(6, 34))
        # Main rail line and chamber loops.
        pygame.draw.line(self.floor_image, (58, 51, 43), (100, 1200), (3450, 1200), 150)
        pygame.draw.line(self.floor_image, (46, 42, 39), (930, 1200), (1350, 520), 120)
        pygame.draw.line(self.floor_image, (46, 42, 39), (2200, 1200), (2780, 500), 130)
        pygame.draw.ellipse(self.floor_image, (42, 37, 38), (2920, 260, 690, 1740))
        # Rails are part of floor art and remain nonblocking.
        for offset in (-32, 32):
            pygame.draw.line(self.floor_image, (89, 79, 67), (120, 1200 + offset), (3440, 1200 + offset), 5)
        for x in range(140, 3450, 42):
            pygame.draw.line(self.floor_image, (92, 61, 37), (x, 1155), (x, 1245), 7)

    def _add(self, prop, blocking=False):
        self.props.append(prop)
        if blocking or getattr(prop, "is_structure", False):
            self.obstacles.append(prop)

    def _build_level(self):
        w, h = self.width, self.height
        self.obstacles.extend([
            pygame.Rect(0, -40, w, 40), pygame.Rect(0, h, w, 40),
            pygame.Rect(-40, 0, 40, h), pygame.Rect(w, 0, 40, h),
        ])
        # Rock walls create four broad chambers while preserving the rail path.
        wall_specs = (
            (760, 80, 160, 850), (760, 1460, 160, 820),
            (1680, 80, 170, 720), (1680, 1540, 170, 740),
            (2500, 80, 170, 670), (2500, 1650, 170, 630),
            (2920, 80, 140, 520), (2920, 1860, 140, 420),
        )
        for spec in wall_specs:
            self._add(MineProp(*spec, "rock", blocking=True), blocking=True)
        for x in (480, 1080, 1500, 2050, 2440, 2860, 3330):
            self._add(MineProp(x, 1040, 115, 250, "support", blocking=True), blocking=True)
        for x in (520, 1380, 2310, 3150):
            self._add(MineProp(x, 1125, 210, 75, "cart", blocking=True), blocking=True)
        self.production_winch = MineProp(390, 820, 180, 180, "winch", blocking=True)
        self._add(self.production_winch, blocking=True)

        state = old_mine_state(self.manager)
        lit = set(state.get("lanterns_lit", ()))
        for station_id, x, y in (
            ("entrance_lamp", 720, 930),
            ("rail_lamp", 1910, 900),
            ("deep_lamp", 2760, 850),
        ):
            station = LanternStation(station_id, x, y, station_id in lit)
            self.lanterns.append(station)
            self.props.append(station)

        cleared = set(state.get("cleared_collapses", ()))
        for pile_id, x, y in (
            ("north_fall", 1380, 520),
            ("rail_fall", 2090, 1180),
            ("deep_fall", 2870, 1690),
        ):
            pile = CollapsePile(pile_id, x, y, pile_id in cleared)
            self.collapses.append(pile)
            self._add(pile, blocking=not pile.cleared)

        destroyed = set(state.get("egg_sacs_destroyed", ()))
        for sac_id, x, y in (
            ("sac_1", 2800, 510), ("sac_2", 3180, 470),
            ("sac_3", 2840, 1460), ("sac_4", 3330, 1580),
        ):
            sac = EggSac(sac_id, x, y, sac_id in destroyed)
            self.egg_sacs.append(sac)
            self.props.append(sac)

        self._spawn_ores()
        self.set_web_gate(int(state.get("quest_stage", 0)) < 5 and not state.get("boss_defeated"))

    def _spawn_ores(self):
        state = old_mine_state(self.manager)
        depleted = set(state.get("depleted_ores", ()))
        specs = (
            (IronOre, "iron_1", 980, 390), (IronOre, "iron_2", 1280, 850),
            (IronOre, "iron_3", 1510, 1760), (IronOre, "iron_4", 2200, 420),
            (IronOre, "iron_5", 2340, 1840), (IronOre, "iron_6", 3050, 330),
            (CoalDeposit, "coal_1", 850, 1740), (CoalDeposit, "coal_2", 1320, 330),
            (CoalDeposit, "coal_3", 2010, 650), (CoalDeposit, "coal_4", 2640, 1420),
            (StoneDeposit, "stone_1", 1120, 2010), (StoneDeposit, "stone_2", 1880, 1880),
            (StoneDeposit, "stone_3", 2450, 520), (StoneDeposit, "stone_4", 3420, 1910),
            (RubyVein, "ruby_1", 2740, 430), (RubyVein, "ruby_2", 3400, 640),
            (SilverVein, "silver_1", 3200, 1940), (SilverVein, "silver_2", 3480, 1040),
        )
        for cls, node_id, x, y in specs:
            node = cls(x, y)
            node.node_id = node_id
            if node_id in depleted:
                node.current_hits = 0
                node.is_empty = True
                if node.sprites.get("empty"):
                    node.image = node.sprites["empty"]
            self.ore_nodes.append(node)
            self.props.append(node)

    def refresh_persistent(self, manager):
        state = old_mine_state(manager)
        lit = set(state.get("lanterns_lit", ()))
        for lantern in self.lanterns:
            lantern.lit = lantern.station_id in lit
            lantern._redraw()
        cleared = set(state.get("cleared_collapses", ()))
        for pile in self.collapses:
            pile.cleared = pile.pile_id in cleared
            pile.is_structure = not pile.cleared
            pile.blocks_projectiles = not pile.cleared
            pile._redraw()
            if pile.cleared and pile in self.obstacles:
                self.obstacles.remove(pile)
            elif not pile.cleared and pile not in self.obstacles:
                self.obstacles.append(pile)
        destroyed = set(state.get("egg_sacs_destroyed", ()))
        for sac in self.egg_sacs:
            sac.destroyed = sac.sac_id in destroyed
            sac._redraw()
        self.set_web_gate(int(state.get("quest_stage", 0)) < 5 and not state.get("boss_defeated"))

    def set_web_gate(self, active: bool):
        if active and self.web_gate is None:
            self.web_gate = MineProp(2960, 580, 58, 1280, "web_gate", blocking=True)
            self._add(self.web_gate, blocking=True)
        elif not active and self.web_gate is not None:
            if self.web_gate in self.props:
                self.props.remove(self.web_gate)
            if self.web_gate in self.obstacles:
                self.obstacles.remove(self.web_gate)
            self.web_gate = None

    def update(self, manager=None):
        for prop in self.props:
            if hasattr(prop, "update"):
                try:
                    prop.update(manager=manager)
                except TypeError:
                    prop.update()
        if random.random() < 0.08:
            self.dust.append({
                "x": random.randint(100, self.width - 100),
                "y": random.randint(100, self.height - 100),
                "life": random.randint(45, 110),
                "size": random.randint(2, 5),
            })
        for mote in self.dust:
            mote["life"] -= 1
            mote["y"] -= 0.12
        self.dust = [mote for mote in self.dust if mote["life"] > 0]

    def draw_background(self, screen, offset=(0, 0)):
        screen.blit(self.floor_image, (-int(offset[0]), -int(offset[1])))

    def draw_foreground(self, screen, offset=(0, 0)):
        ox, oy = int(offset[0]), int(offset[1])
        for mote in self.dust:
            x, y = int(mote["x"] - ox), int(mote["y"] - oy)
            if -10 < x < screen.get_width() + 10 and -10 < y < screen.get_height() + 10:
                pygame.draw.circle(screen, (129, 118, 101), (x, y), mote["size"])


class OldMuckfordMineMenu(GameplayScreen):
    def __init__(self, manager):
        super().__init__(manager)
        self.arena = OldMuckfordMineArena(manager)
        self.monsters = pygame.sprite.Group()
        self.mine_npcs: List[Villager] = []
        self.dynamic_props: List[object] = []
        self.boss: Optional[DeepCaveBroodmother] = None
        self.feedback = ""
        self.feedback_timer = 0
        self.dialogue_active = False
        self.dialogue_name = ""
        self.dialogue_pages: List[str] = []
        self.dialogue_index = 0
        self.dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.hazard_timer = 0
        self.collapse_warning = None
        self.collapse_warning_timer = 0

    def on_enter(self):
        super().on_enter()
        self.manager.current_arena = self.arena
        self.player = self.manager.player_character
        self.player.rect.center = (180, self.arena.height // 2)
        self.player.facing_right = True
        self.player.is_dead = False
        self.player.current_hp = max(1, self.player.current_hp)
        state = old_mine_state(self.manager)
        state["visits"] = int(state.get("visits", 0)) + 1
        state["road_secured"] = True
        sync_old_mine_story(self.manager)
        self.arena.refresh_persistent(self.manager)
        self.monsters.empty()
        self._spawn_population()
        self._refresh_npcs()
        self._spawn_boss_if_needed()
        self._update_camera()
        try:
            from systems.world_progression import mark_location_visited
            mark_location_visited(self.manager, "old_mine_road", set_current=True)
        except Exception:
            pass
        _safe_sound("click")

    @staticmethod
    def _npc(name: str, race: str, x: int, y: int, role: str):
        npc = Villager(name, race, x, y, team_color=GREEN)
        npc.ai_controller = None
        npc.name = name
        npc.mine_role = role
        return npc

    def _refresh_npcs(self):
        for prop in list(self.dynamic_props):
            if prop in self.arena.props:
                self.arena.props.remove(prop)
        self.dynamic_props = []
        self.mine_npcs = []
        state = old_mine_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        foreman = self._npc("Foreman Torra Flintvein", "Dwarf", 270, 1150, "foreman")
        self.mine_npcs.append(foreman)
        rescued = set(state.get("rescued_miners", ()))
        miner_data = (
            ("miner_durn", "Durn Coalhand", "Dwarf", 1420, 510),
            ("miner_pell", "Pell Rook", "Human", 2200, 1740),
            ("miner_sava", "Sava Brasspin", "Goblin", 2790, 720),
        )
        if stage == 2:
            for miner_id, name, race, x, y in miner_data:
                if miner_id not in rescued:
                    self.mine_npcs.append(self._npc(name, race, x, y, f"rescue:{miner_id}"))
        for index, miner_id in enumerate(sorted(rescued)):
            name_map = {item[0]: item[1] for item in miner_data}
            race_map = {item[0]: item[2] for item in miner_data}
            self.mine_npcs.append(
                self._npc(name_map.get(miner_id, "Rescued Miner"), race_map.get(miner_id, "Human"), 380 + index * 100, 1360, "rescued")
            )
        self.dynamic_props = list(self.mine_npcs)
        self.arena.props.extend(self.dynamic_props)

    def _spawn_population(self):
        placements = (
            (GravePickman, 980, 920), (GravePickman, 1170, 1460),
            (GravePickman, 1510, 810), (GravePickman, 1740, 1830),
            (RailWraith, 1380, 380), (RailWraith, 2100, 720), (RailWraith, 2520, 1450),
            (WebCrawler, 2630, 480), (WebCrawler, 2800, 1110),
            (WebCrawler, 3240, 760), (WebCrawler, 3400, 1520),
            (CrystalHusk, 1960, 420), (CrystalHusk, 2400, 1920),
            (CrystalHusk, 3350, 2020), (BroodGuard, 3100, 470),
        )
        for index, (monster_class, x, y) in enumerate(placements):
            monster = monster_class(f"{monster_class.SPECIES} {index + 1}", x, y, ENEMY_TEAM)
            self.monsters.add(monster)

    def _spawn_boss_if_needed(self):
        state = old_mine_state(self.manager)
        self.boss = None
        if not state.get("boss_unlocked") or state.get("boss_defeated"):
            return
        self.arena.set_web_gate(False)
        self.boss = DeepCaveBroodmother("Cave Broodmother", 3340, 1160, ENEMY_TEAM)
        self.monsters.add(self.boss)
        self._flash("The Cave Broodmother descends from the Webbed Depths.", 300)

    def _near(self, rect: pygame.Rect, inflate=74) -> bool:
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

    def _foreman_dialogue(self):
        state = old_mine_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        if stage == 0:
            state["quest_stage"] = 1
            if not state.get("supplies_claimed"):
                self.manager.inventory["Coal"] = int(self.manager.inventory.get("Coal", 0)) + 3
                state["supplies_claimed"] = True
            pages = (
                "Marda's key opens the door. It does not make the mine safe. I am Torra Flintvein, last foreman foolish enough to come back.",
                "Relight the three lantern stations. Take three Coal from the emergency crate. Once we can see, we find my miners.",
                "The lower galleries are level 3-7 work. The key is a physical gate, not a promise that you are strong enough.",
            )
            try:
                self.manager.record_tier0_event("flag", "old_mine_restoration_started")
            except Exception:
                pass
        elif stage == 1:
            count = len(set(state.get("lanterns_lit", ())))
            pages = (f"Relight all three stations with one Coal each. Lanterns: {count}/3.",)
        elif stage == 2:
            count = len(set(state.get("rescued_miners", ())))
            pages = (f"Durn, Pell and Sava are still inside. Miners rescued: {count}/3.",)
        elif stage == 3:
            count = len(set(state.get("cleared_collapses", ())))
            pages = (f"Use a pickaxe on the three marked collapse piles. Cleared: {count}/3.",)
        elif stage == 4:
            count = len(set(state.get("egg_sacs_destroyed", ())))
            pages = (f"The Webbed Depths are breeding. Destroy every marked egg sac: {count}/4.",)
        elif stage == 5:
            pages = ("The deep web is open. Kill the Cave Broodmother before it seals the galleries again.",)
        elif stage == 6:
            pages = (
                f"The mine can work again, but the entrance winch needs {_cost_text(PRODUCTION_COST)}.",
                "Load the materials into the winch beside me. Controlled production will send a share to Muckford storage each day.",
            )
        else:
            pages = (
                "Lanterns burn, the rails are clear and my crew is alive. Old Muckford Mine is producing again.",
                "The Webbed Depths remain dangerous, but danger we can schedule is better than a sealed dark hole.",
            )
        self._open_dialogue("Foreman Torra Flintvein", pages)
        self._refresh_npcs()

    def _try_npc(self) -> bool:
        for npc in self.mine_npcs:
            if not self._near(npc.rect, 72):
                continue
            role = getattr(npc, "mine_role", "")
            if role == "foreman":
                self._foreman_dialogue()
            elif role.startswith("rescue:"):
                miner_id = role.split(":", 1)[1]
                state = old_mine_state(self.manager)
                rescued = state.setdefault("rescued_miners", [])
                if miner_id not in rescued:
                    rescued.append(miner_id)
                    self.manager.reputation = int(getattr(self.manager, "reputation", 0)) + 1
                    self._flash(f"Rescued {npc.name}. +1 reputation")
                    _safe_sound("recruit")
                    sync_old_mine_story(self.manager)
                    self._refresh_npcs()
            else:
                self._open_dialogue(npc.name, ("Torra has us counting supports twice. Nobody wants another sealed shift.",))
            return True
        return False

    def _try_lantern(self) -> bool:
        state = old_mine_state(self.manager)
        if int(state.get("quest_stage", 0)) != 1:
            return False
        for lantern in self.arena.lanterns:
            if lantern.lit or not self._near(lantern.rect, 82):
                continue
            if int(self.manager.inventory.get("Coal", 0)) < 1:
                self._flash("Lighting the station requires 1 Coal.")
                _safe_sound("error")
                return True
            self.manager.inventory["Coal"] -= 1
            if self.manager.inventory["Coal"] <= 0:
                self.manager.inventory.pop("Coal", None)
            state.setdefault("lanterns_lit", []).append(lantern.station_id)
            lantern.lit = True
            lantern._redraw()
            self._flash(f"Mine lanterns restored: {len(set(state['lanterns_lit']))}/3")
            _safe_sound("recruit")
            if sync_old_mine_story(self.manager):
                self._flash("The galleries are visible. Find Torra's three miners.", 300)
                self._refresh_npcs()
            return True
        return False

    def _try_collapse(self) -> bool:
        state = old_mine_state(self.manager)
        if int(state.get("quest_stage", 0)) != 3:
            return False
        for pile in self.arena.collapses:
            if pile.cleared or not self._near(pile.rect, 82):
                continue
            tool = getattr(self.player, "current_weapon", None)
            if getattr(tool, "tool_type", "") != "pickaxe":
                self._flash("Clearing the collapse requires an equipped pickaxe.")
                _safe_sound("error")
                return True
            cleared = state.setdefault("cleared_collapses", [])
            if pile.pile_id not in cleared:
                cleared.append(pile.pile_id)
            pile.cleared = True
            pile.is_structure = False
            pile.blocks_projectiles = False
            pile._redraw()
            if pile in self.arena.obstacles:
                self.arena.obstacles.remove(pile)
            self.manager.inventory["Stone"] = int(self.manager.inventory.get("Stone", 0)) + 2
            self._flash(f"Collapse cleared: {len(set(cleared))}/3. +2 Stone")
            _safe_sound("mining_break")
            if sync_old_mine_story(self.manager):
                self._flash("The lower rails are clear. Destroy the Webbed Depths egg sacs.", 300)
                self.arena.refresh_persistent(self.manager)
            return True
        return False

    def _try_egg_sac(self) -> bool:
        state = old_mine_state(self.manager)
        if int(state.get("quest_stage", 0)) != 4:
            return False
        for sac in self.arena.egg_sacs:
            if sac.destroyed or not self._near(sac.rect, 78):
                continue
            destroyed = state.setdefault("egg_sacs_destroyed", [])
            if sac.sac_id not in destroyed:
                destroyed.append(sac.sac_id)
            sac.destroyed = True
            sac._redraw()
            self.manager.inventory["Spider Silk"] = int(self.manager.inventory.get("Spider Silk", 0)) + 1
            # Each nest defends itself with fresh crawlers.
            for index in range(2):
                self.monsters.add(WebCrawler(f"Egg Crawler {len(destroyed)}-{index + 1}", sac.rect.centerx + (index * 70 - 35), sac.rect.centery + 75, ENEMY_TEAM))
            self._flash(f"Egg sacs destroyed: {len(set(destroyed))}/4. +1 Spider Silk")
            _safe_sound("mining_break")
            if sync_old_mine_story(self.manager):
                self.arena.refresh_persistent(self.manager)
                self._flash("The deep web tears open. The Cave Broodmother awakens.", 320)
                self._spawn_boss_if_needed()
            return True
        return False

    def _try_production_winch(self) -> bool:
        state = old_mine_state(self.manager)
        if int(state.get("quest_stage", 0)) != 6 or not self._near(self.arena.production_winch.rect, 105):
            return False
        if not _consume_materials(self.manager, PRODUCTION_COST):
            self._flash(f"Restarting the winch requires {_cost_text(PRODUCTION_COST)}.")
            _safe_sound("error")
            return True
        state["production_restarted"] = True
        sync_old_mine_story(self.manager)
        if not state.get("production_reward_claimed"):
            self.manager.gold += 120
            self.manager.reputation = int(getattr(self.manager, "reputation", 0)) + 8
            self.manager.city_storage["Iron Ore"] = int(self.manager.city_storage.get("Iron Ore", 0)) + 6
            self.manager.city_storage["Coal"] = int(self.manager.city_storage.get("Coal", 0)) + 4
            state["production_reward_claimed"] = True
        try:
            self.manager.record_tier0_event("project", "old_mine_production_restarted")
            self.manager.record_tier0_event("quest", "old_muckford_mine_restored")
        except Exception:
            pass
        self._flash("Old Mine production restarted. +120 SP, +8 reputation, first ore shipment.", 420)
        _safe_sound("recruit")
        return True

    def _try_ore_prompt(self) -> bool:
        # Mining itself remains attack-based. E only provides explicit feedback.
        for node in self.arena.ore_nodes:
            if not node.is_empty and self._near(node.rect, 62):
                tool = getattr(self.player, "current_weapon", None)
                if getattr(tool, "tool_type", "") == "pickaxe":
                    self._flash(f"Attack the {node.name} with your pickaxe to mine it.")
                else:
                    self._flash("Equip a pickaxe before mining this deposit.")
                    _safe_sound("error")
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
            if self._try_lantern() or self._try_collapse() or self._try_egg_sac():
                return
            if self._try_production_winch() or self._try_ore_prompt():
                return

    def _record_depleted_ores(self):
        state = old_mine_state(self.manager)
        depleted = state.setdefault("depleted_ores", [])
        for node in self.arena.ore_nodes:
            if node.is_empty and node.node_id not in depleted:
                depleted.append(node.node_id)

    def _transfer_loot(self):
        loot = self.manager.round_rewards.get("loot")
        if not loot:
            return
        for name, count in list(loot.items()):
            self.manager.inventory[name] = int(self.manager.inventory.get(name, 0)) + int(count)
        self.manager.round_rewards["loot"] = {}

    def _collapse_hazard_step(self):
        state = old_mine_state(self.manager)
        cleared = set(state.get("cleared_collapses", ()))
        active_zone = None
        for zone_id, rect in self.arena.collapse_zones.items():
            if zone_id not in cleared and rect.collidepoint(self.player.rect.center):
                active_zone = (zone_id, rect)
                break
        if active_zone is None:
            self.collapse_warning = None
            self.collapse_warning_timer = 0
            return
        zone_id, rect = active_zone
        if self.collapse_warning != zone_id:
            self.collapse_warning = zone_id
            self.collapse_warning_timer = 90
            self._flash("Loose stone shifts overhead — move or clear the collapse!", 120)
            return
        self.collapse_warning_timer -= 1
        if self.collapse_warning_timer <= 0:
            try:
                self.player.take_damage(10, "Physical", manager=self.manager)
                self.player.apply_status("Slow", 75, 0)
            except Exception:
                self.player.current_hp = max(1, self.player.current_hp - 10)
            state["collapse_hits"] = int(state.get("collapse_hits", 0)) + 1
            self.collapse_warning_timer = 120
            self._flash("Falling stone strikes the gallery!")
            try:
                self.manager.vfx.create_impact_sparks(self.player.rect.centerx, self.player.rect.centery, color=(135, 120, 97), count=8)
            except Exception:
                pass

    def _process_boss(self):
        if self.boss is None:
            return
        if self.boss.pending_spawn:
            for spawn in list(self.boss.pending_spawn):
                self.monsters.add(spawn)
            self.boss.pending_spawn = []
            self._flash("The Broodmother calls defenders from the web walls.")
        while self.boss.pending_collapse_wave > 0:
            self.boss.pending_collapse_wave -= 1
            self.collapse_warning = "boss_wave"
            self.collapse_warning_timer = 45
            self._flash("The Broodmother shakes loose the cavern roof!", 120)
        if not self.boss.is_dead:
            return
        state = old_mine_state(self.manager)
        if state.get("boss_defeated"):
            return
        state["boss_defeated"] = True
        state["boss_unlocked"] = False
        state["quest_stage"] = 6
        if not state.get("boss_reward_claimed"):
            self.manager.gold += 90
            self.manager.reputation = int(getattr(self.manager, "reputation", 0)) + 5
            self.manager.inventory["Broodmother Carapace"] = int(self.manager.inventory.get("Broodmother Carapace", 0)) + 1
            self.manager.inventory["Royal Venom Gland"] = int(self.manager.inventory.get("Royal Venom Gland", 0)) + 1
            state["boss_reward_claimed"] = True
        try:
            self.manager.record_tier0_event("boss", "cave_broodmother")
        except Exception:
            pass
        try:
            self.manager.record_deed("mine_broodmother", "slew the Cave Broodmother and opened the deep mine")
        except Exception:
            pass
        self.arena.set_web_gate(False)
        self._flash("Cave Broodmother slain. +90 SP, +5 reputation. Restart the entrance winch.", 420)
        self._refresh_npcs()

    def update(self):
        if self.dialogue_active:
            if self.feedback_timer > 0:
                self.feedback_timer -= 1
            return
        if self.manager.paused:
            return
        living = [monster for monster in self.monsters if not monster.is_dead]
        all_units = [self.player] + living + [node for node in self.arena.ore_nodes if not node.is_empty]
        self._update_gameplay(all_units)
        self._transfer_loot()
        self._record_depleted_ores()
        self._collapse_hazard_step()
        self._process_boss()
        if self.player.is_dead:
            self.player.is_dead = False
            self.player.current_hp = max(1, int(self.player.max_hp * 0.3))
            self.next_state = "mine_road"
            return
        if self.player.rect.left < 8:
            self.manager.match_in_progress = False
            self.next_state = "mine_road"
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    def _draw_darkness(self, screen):
        self.dark_overlay.fill((4, 4, 10, 236))
        lights = [(self.player.rect.center, 285)]
        for lantern in self.arena.lanterns:
            if lantern.lit:
                lights.append((lantern.rect.center, 235))
        if old_mine_state(self.manager).get("production_restarted"):
            lights.append((self.arena.production_winch.rect.center, 190))
        for (world_x, world_y), radius in lights:
            x = int(world_x - self.camera_x)
            y = int(world_y - self.camera_y)
            flicker = random.randint(-6, 6)
            for r, alpha in ((radius + flicker, 175), (int(radius * 0.72), 100), (int(radius * 0.43), 35), (70, 0)):
                pygame.draw.circle(self.dark_overlay, (4, 4, 10, alpha), (x, y), max(5, r))
        for node in self.arena.ore_nodes:
            if node.is_empty or node.resource_name not in {"Chipped Ruby", "Silver Ore"}:
                continue
            x, y = node.rect.centerx - self.camera_x, node.rect.centery - self.camera_y
            color = (52, 8, 25, 120) if node.resource_name == "Chipped Ruby" else (55, 60, 80, 135)
            pygame.draw.circle(self.dark_overlay, color, (int(x), int(y)), 65)
        screen.blit(self.dark_overlay, (0, 0))

    def _nearest_prompt(self):
        for npc in self.mine_npcs:
            if self._near(npc.rect, 72):
                label = f"Rescue {npc.name}" if str(getattr(npc, "mine_role", "")).startswith("rescue:") else f"Talk to {npc.name}"
                return npc.rect, label
        state = old_mine_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        if stage == 1:
            for lantern in self.arena.lanterns:
                if not lantern.lit and self._near(lantern.rect, 82):
                    return lantern.rect, "Relight station: 1 Coal"
        if stage == 3:
            for pile in self.arena.collapses:
                if not pile.cleared and self._near(pile.rect, 82):
                    return pile.rect, "Clear collapse with pickaxe"
        if stage == 4:
            for sac in self.arena.egg_sacs:
                if not sac.destroyed and self._near(sac.rect, 78):
                    return sac.rect, "Destroy egg sac"
        if stage == 6 and self._near(self.arena.production_winch.rect, 105):
            return self.arena.production_winch.rect, f"Restart production: {_cost_text(PRODUCTION_COST)}"
        for node in self.arena.ore_nodes:
            if not node.is_empty and self._near(node.rect, 62):
                return node.rect, f"Mine {node.name} with pickaxe attacks"
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
        overlay.fill((20, 19, 21, 242))
        screen.blit(overlay, panel.topleft)
        pygame.draw.rect(screen, (145, 116, 74), panel, 3, border_radius=9)
        draw_text(self.dialogue_name, font_main, GOLD_COLOR, screen, panel.x + 24, panel.y + 18)
        page = self.dialogue_pages[self.dialogue_index]
        y = panel.y + 60
        for line in self._wrap(page, font_main, panel.w - 48)[:4]:
            draw_text(line, font_main, WHITE, screen, panel.x + 24, y)
            y += 29
        draw_text("[E / Enter] continue    [Esc] close", font_small, GRAY, screen, panel.right - 355, panel.bottom - 27)

    def draw(self, screen):
        living = [monster for monster in self.monsters if not monster.is_dead]
        all_units = [self.player] + living + [node for node in self.arena.ore_nodes if not node.is_empty]
        self._draw_gameplay(screen, all_units)
        self._draw_darkness(screen)
        # HUD piirretään pimeyden PÄÄLLE - muuten HP/mana-pallot ja
        # palkit himmenevät lukukelvottomiksi (pelaajapalaute)
        if getattr(self, "player", None):
            self.player.draw_hud(screen)
        prompt = None if self.dialogue_active else self._nearest_prompt()
        if prompt:
            rect, label = prompt
            self.manager._draw_floating_prompt(screen, rect.centerx, rect.top - 18, "E", (self.camera_x, self.camera_y), label)
        state = old_mine_state(self.manager)
        ore_left = sum(1 for node in self.arena.ore_nodes if not node.is_empty)
        draw_text("OLD MUCKFORD MINE — PHYSICAL GATE: MARDA'S KEY — Lv 3-7", font_small, WHITE, screen, 34, 32)
        draw_text(f"MINE RESTORATION: {mine_objective(self.manager)}", font_small, (218, 195, 128), screen, 34, 58)
        draw_text(f"Threats: {len(living)}   Ore deposits: {ore_left}   Lanterns: {len(set(state.get('lanterns_lit', ())))}/3", font_small, GRAY, screen, 34, 84)
        draw_text("Exit west to Mine Road. Lit stations create permanent safe light.", font_small, GRAY, screen, 34, 108)
        if self.feedback_timer > 0:
            surface = font_main.render(self.feedback, True, GOLD_COLOR)
            screen.blit(surface, (SCREEN_WIDTH // 2 - surface.get_width() // 2, 136))
        self._draw_dialogue(screen)
