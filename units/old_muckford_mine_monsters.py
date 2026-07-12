"""Code-rendered level 3-7 monsters for Old Muckford Mine."""
from __future__ import annotations

import math
from typing import List

import pygame

from ai.tier0_monster_ai import (
    HeavyChargeAI,
    PounceMonsterAI,
    RangedKiteMonsterAI,
    SkitterMonsterAI,
    SwarmMonsterAI,
)
from units.tier0_monsters import CodeMonster, _shade, _vfx_text


class MineMonster(CodeMonster):
    """Generated mine silhouettes shared by the new underground ecology."""

    def _draw_pickman(self, surface, body, accent, bob, stretch, state, frame):
        cy = 31 + bob
        pygame.draw.circle(surface, _shade(body, 18), (31, cy - 15), 10)
        pygame.draw.rect(surface, body, (20 - stretch, cy - 6, 23 + stretch * 2, 29), border_radius=5)
        pygame.draw.line(surface, body, (22, cy + 3), (8, cy + 19 + frame * 2), 7)
        pygame.draw.line(surface, body, (41, cy + 3), (54, cy + 17 - frame * 2), 7)
        pygame.draw.line(surface, body, (25, cy + 20), (20, 58), 7)
        pygame.draw.line(surface, body, (38, cy + 20), (44, 58), 7)
        # Rusted pickaxe silhouette.
        pygame.draw.line(surface, (109, 74, 43), (47, cy - 3), (58, cy + 27), 4)
        pygame.draw.arc(surface, accent, (39, cy - 13, 25, 19), math.pi, math.tau, 4)
        pygame.draw.line(surface, accent, (19, cy - 18), (44, cy - 18), 3)
        self._eyes(surface, ((27, cy - 16), (35, cy - 16)), state)

    def _draw_rail_wraith(self, surface, body, accent, bob, stretch, state, frame):
        cy = 30 + bob
        pygame.draw.circle(surface, body, (32, cy - 15), 10)
        pygame.draw.polygon(
            surface,
            body,
            [(20 - stretch, cy - 6), (45 + stretch, cy - 6), (54, cy + 29),
             (43, cy + 22), (34, cy + 33), (24, cy + 22), (10, cy + 30)],
        )
        pygame.draw.line(surface, accent, (14, cy + 12), (3, cy + 25), 4)
        pygame.draw.line(surface, accent, (49, cy + 12), (62, cy + 25), 4)
        # Mine lantern held inside the chest.
        pygame.draw.rect(surface, (135, 102, 57), (25, cy - 1, 15, 18), 2)
        glow = (222, 183, 91) if state != "dead" else (70, 65, 54)
        pygame.draw.circle(surface, glow, (32, cy + 6), 5)
        self._eyes(surface, ((28, cy - 17), (36, cy - 17)), state)

    def _draw_web_crawler(self, surface, body, accent, bob, stretch, state, frame):
        cy = 33 + bob
        for side in (-1, 1):
            root = 26 if side < 0 else 42
            for index, dy in enumerate((-12, -5, 3, 11)):
                reach = 23 + (stretch if state == "attack" else 0)
                kick = 4 if frame and index % 2 else -3
                pygame.draw.line(
                    surface,
                    accent,
                    (root, cy + dy),
                    (root + side * reach, cy + dy + kick),
                    4,
                )
        pygame.draw.ellipse(surface, body, (22 - stretch, cy - 17, 38 + stretch * 2, 33))
        pygame.draw.circle(surface, _shade(body, 20), (37, cy - 14), 12)
        for ex in (31, 35, 39, 43):
            pygame.draw.circle(surface, self.EYE if state != "dead" else (45, 37, 39), (ex, cy - 16), 2)
        pygame.draw.line(surface, (221, 220, 232), (16, cy + 12), (7, cy + 22), 2)
        pygame.draw.line(surface, (221, 220, 232), (56, cy + 12), (65, cy + 22), 2)

    def _draw_crystal_husk(self, surface, body, accent, bob, stretch, state, frame):
        cy = 34 + bob
        pygame.draw.rect(surface, body, (21 - stretch, cy - 18, 42 + stretch * 2, 37), border_radius=9)
        pygame.draw.circle(surface, _shade(body, 18), (42, cy - 24), 13)
        pygame.draw.line(surface, body, (24, cy + 3), (6, cy + 24), 10)
        pygame.draw.line(surface, body, (60, cy + 3), (78, cy + 23), 10)
        pygame.draw.line(surface, body, (31, cy + 15), (26, 67), 11)
        pygame.draw.line(surface, body, (54, cy + 15), (60, 67), 11)
        for x, height in ((25, 18), (38, 26), (52, 21), (63, 15)):
            pygame.draw.polygon(
                surface,
                accent,
                [(x - 5, cy - 11), (x, cy - 11 - height), (x + 6, cy - 8)],
            )
            pygame.draw.line(surface, _shade(accent, 55), (x, cy - 10 - height), (x + 4, cy - 9), 2)
        self._eyes(surface, ((38, cy - 26), (47, cy - 26)), state)

    def _draw_brood_guard(self, surface, body, accent, bob, stretch, state, frame):
        cy = 40 + bob
        for side in (-1, 1):
            root = 38 if side < 0 else 70
            for index, dy in enumerate((-18, -7, 6, 18)):
                reach = 34 + stretch * 2
                kick = 7 if frame and index % 2 else -5
                pygame.draw.line(surface, accent, (root, cy + dy), (root + side * reach, cy + dy + kick), 6)
        pygame.draw.ellipse(surface, body, (29 - stretch, cy - 24, 52 + stretch * 2, 48))
        pygame.draw.circle(surface, _shade(body, 22), (63, cy - 19), 18)
        pygame.draw.polygon(surface, _shade(accent, 20), [(31, cy - 21), (19, cy - 38), (44, cy - 27)])
        for ex in (54, 60, 66, 72):
            pygame.draw.circle(surface, self.EYE if state != "dead" else (42, 35, 38), (ex, cy - 22), 2)

    def _draw_deep_broodmother(self, surface, body, accent, bob, stretch, state, frame):
        cy = 58 + bob
        for side in (-1, 1):
            root = 57 if side < 0 else 91
            for index, dy in enumerate((-28, -14, 1, 17)):
                reach = 50 + stretch * 2
                kick = 10 if frame and index % 2 else -7
                pygame.draw.line(surface, accent, (root, cy + dy), (root + side * reach, cy + dy + kick), 8)
        pygame.draw.ellipse(surface, body, (37 - stretch, cy - 34, 78 + stretch * 2, 67))
        pygame.draw.ellipse(surface, _shade(body, 22), (77, cy - 39, 55 + stretch, 48))
        # Egg-armoured abdomen and crown spines.
        pygame.draw.arc(surface, _shade(accent, 18), (40, cy - 31, 70, 57), 0.1, 3.0, 4)
        for x, height in ((51, 24), (69, 34), (88, 39), (108, 29)):
            pygame.draw.polygon(surface, accent, [(x - 6, cy - 28), (x, cy - 28 - height), (x + 8, cy - 24)])
        for ex in (91, 98, 105, 112, 119, 126):
            pygame.draw.circle(surface, self.EYE if state != "dead" else (40, 32, 36), (ex, cy - 30), 3)
        if getattr(self, "phase", 1) >= 2 and state != "dead":
            pygame.draw.arc(surface, (216, 204, 232), (35, cy - 43, 103, 85), 0.1, 3.0, 3)
        if getattr(self, "phase", 1) >= 3 and state != "dead":
            pygame.draw.circle(surface, (153, 76, 178), (86, cy - 4), 24, 3)


class GravePickman(MineMonster):
    SPECIES = "Grave Pickman"
    THREAT_LEVEL = 3
    SHAPE = "pickman"
    BODY = (74, 77, 72)
    ACCENT = (139, 105, 68)
    EYE = (164, 220, 182)
    VISUAL_SIZE = (66, 64)
    HITBOX_SIZE = (36, 28)
    HP, STR, DEX, DEFENSE = 145, 15, 7, 4
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 0.82, 52, 72
    STATUS_EFFECT = ("Slow", 90, 0)
    AI_CLASS = SwarmMonsterAI
    XP_REWARD, BOUNTY_VALUE = 24, 4


class RailWraith(MineMonster):
    SPECIES = "Rail Wraith"
    THREAT_LEVEL = 4
    SHAPE = "rail_wraith"
    BODY = (64, 71, 83)
    ACCENT = (111, 132, 144)
    EYE = (186, 231, 218)
    VISUAL_SIZE = (66, 68)
    HITBOX_SIZE = (34, 24)
    HP, STR, DEX, INT, DEFENSE = 172, 13, 13, 14, 3
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.08, 210, 68
    DAMAGE_TYPE = "Magic"
    STATUS_EFFECT = ("Slow", 120, 0)
    AI_CLASS = RangedKiteMonsterAI
    XP_REWARD, BOUNTY_VALUE = 37, 6


class WebCrawler(MineMonster):
    SPECIES = "Web Crawler"
    THREAT_LEVEL = 4
    SHAPE = "web_crawler"
    BODY = (82, 63, 92)
    ACCENT = (46, 36, 52)
    EYE = (229, 77, 103)
    VISUAL_SIZE = (76, 66)
    HITBOX_SIZE = (42, 28)
    HP, STR, DEX, DEFENSE = 164, 16, 16, 3
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.42, 45, 53
    STATUS_EFFECT = ("Web", 120, 0)
    AI_CLASS = PounceMonsterAI
    XP_REWARD, BOUNTY_VALUE = 39, 6


class CrystalHusk(MineMonster):
    SPECIES = "Crystal Husk"
    THREAT_LEVEL = 5
    SHAPE = "crystal_husk"
    BODY = (75, 75, 81)
    ACCENT = (151, 73, 101)
    EYE = (240, 166, 191)
    VISUAL_SIZE = (86, 76)
    HITBOX_SIZE = (50, 34)
    HP, STR, DEX, INT, DEFENSE = 255, 21, 6, 8, 8
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 0.72, 63, 82
    DAMAGE_TYPE = "Physical"
    STATUS_EFFECT = ("Slow", 110, 0)
    AI_CLASS = HeavyChargeAI
    XP_REWARD, BOUNTY_VALUE = 56, 9


class BroodGuard(MineMonster):
    SPECIES = "Brood Guard"
    THREAT_LEVEL = 6
    SHAPE = "brood_guard"
    BODY = (71, 49, 82)
    ACCENT = (38, 29, 44)
    EYE = (235, 63, 102)
    VISUAL_SIZE = (116, 92)
    HITBOX_SIZE = (62, 40)
    HP, STR, DEX, DEFENSE = 340, 24, 12, 9
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.02, 61, 64
    STATUS_EFFECT = ("Poison", 150, 3)
    AI_CLASS = SkitterMonsterAI
    XP_REWARD, BOUNTY_VALUE = 76, 12


class DeepCaveBroodmother(MineMonster):
    SPECIES = "Cave Broodmother"
    THREAT_LEVEL = 7
    SHAPE = "deep_broodmother"
    BODY = (69, 47, 81)
    ACCENT = (35, 27, 41)
    EYE = (242, 60, 103)
    VISUAL_SIZE = (154, 124)
    HITBOX_SIZE = (88, 58)
    HP, STR, DEX, INT, DEFENSE = 1080, 31, 12, 14, 11
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 0.86, 78, 76
    STATUS_EFFECT = ("Poison", 180, 4)
    AI_CLASS = HeavyChargeAI
    XP_REWARD, BOUNTY_VALUE = 185, 32

    def __init__(self, name, x, y, team_color):
        self.phase = 1
        super().__init__(name, x, y, team_color)
        self.is_boss = True
        self.boss_id = "cave_broodmother"
        self.pending_spawn: List[CodeMonster] = []
        self.pending_collapse_wave = 0
        self.web_burst_cooldown = 165
        self.phase_two_triggered = False
        self.phase_three_triggered = False

    def _phase_two(self, manager=None):
        if self.phase_two_triggered or self.is_dead:
            return
        self.phase_two_triggered = True
        self.phase = 2
        self.speed = self.walk_speed = 1.05
        self.attack_speed = 62
        self.pending_spawn = [
            WebCrawler(
                f"Brood Crawler {index + 1}",
                self.rect.centerx + (index - 1) * 90,
                self.rect.centery + 110,
                self.team_color,
            )
            for index in range(3)
        ]
        self.pending_collapse_wave += 1
        _vfx_text(manager, self, "THE WEBBED DEPTHS STIR", (218, 191, 232))

    def _phase_three(self, manager=None):
        if self.phase_three_triggered or self.is_dead:
            return
        self.phase_three_triggered = True
        self.phase = 3
        self.speed = self.walk_speed = 1.22
        self.attack_speed = 52
        self.strength += 7
        self.defense += 3
        self.pending_spawn.extend(
            [
                BroodGuard("Brood Guard Alpha", self.rect.centerx - 120, self.rect.centery + 125, self.team_color),
                BroodGuard("Brood Guard Beta", self.rect.centerx + 120, self.rect.centery + 125, self.team_color),
            ]
        )
        self.pending_collapse_wave += 2
        _vfx_text(manager, self, "BROOD CROWN BREAKS", (236, 103, 151))

    def release_web_burst(self, manager=None) -> int:
        if manager is None:
            return 0
        hit = 0
        radius = 250 if self.phase >= 3 else 205
        for target in list(getattr(manager, "all_units", ())):
            if target is self or getattr(target, "is_dead", False):
                continue
            if getattr(target, "team_color", None) == self.team_color:
                continue
            distance = math.hypot(
                target.rect.centerx - self.rect.centerx,
                target.rect.centery - self.rect.centery,
            )
            if distance > radius:
                continue
            try:
                target.take_damage(10 + self.phase * 3, "Poison", attacker=self, manager=manager)
                target.apply_status("Web", 105 + self.phase * 25, 0)
                hit += 1
            except Exception:
                continue
        _vfx_text(manager, self, "WEB BURST", (221, 211, 236))
        return hit

    def update(self, obstacles=None, manager=None):
        if not self.is_dead and self.current_hp <= self.max_hp * 0.66:
            self._phase_two(manager)
        if not self.is_dead and self.current_hp <= self.max_hp * 0.33:
            self._phase_three(manager)
        super().update(obstacles, manager)
        if self.is_dead:
            return
        self.web_burst_cooldown -= 1
        if self.web_burst_cooldown <= 0:
            self.release_web_burst(manager)
            self.web_burst_cooldown = 105 if self.phase >= 3 else 145


OLD_MINE_MONSTER_CLASSES = (
    GravePickman,
    RailWraith,
    WebCrawler,
    CrystalHusk,
    BroodGuard,
)

OLD_MINE_LOOT = {
    "Grave Pickman": [
        {"item": "Rusty Mine Tag", "chance": 0.52, "min": 1, "max": 1},
        {"item": "Coal", "chance": 0.38, "min": 1, "max": 2},
    ],
    "Rail Wraith": [
        {"item": "Wraith Lantern Shard", "chance": 0.48, "min": 1, "max": 1},
        {"item": "Scrap Iron", "chance": 0.55, "min": 1, "max": 2},
    ],
    "Web Crawler": [
        {"item": "Spider Silk", "chance": 0.72, "min": 1, "max": 2},
        {"item": "Venom Gland", "chance": 0.24, "min": 1, "max": 1},
    ],
    "Crystal Husk": [
        {"item": "Stone", "chance": 0.72, "min": 1, "max": 3},
        {"item": "Chipped Ruby", "chance": 0.28, "min": 1, "max": 1},
    ],
    "Brood Guard": [
        {"item": "Thick Spider Silk", "chance": 0.68, "min": 1, "max": 2},
        {"item": "Venom Gland", "chance": 0.42, "min": 1, "max": 1},
    ],
    "Cave Broodmother": [
        {"item": "Broodmother Carapace", "chance": 1.0, "min": 1, "max": 1},
        {"item": "Royal Venom Gland", "chance": 1.0, "min": 1, "max": 1},
        {"item": "Thick Spider Silk", "chance": 1.0, "min": 3, "max": 5},
    ],
}
