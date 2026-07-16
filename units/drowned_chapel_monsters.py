"""Code-rendered Drowned Chapel enemies and the Bell-Drowned Pilgrim boss."""
from __future__ import annotations

import math
from typing import List

import pygame

from ai.tier0_monster_ai import (
    HeavyChargeAI,
    RangedKiteMonsterAI,
    SwarmMonsterAI,
    ToxicPulseAI,
)
from units.tier0_monsters import CodeMonster, MOVE_SCALE, _shade, _vfx_text


class ChapelMonster(CodeMonster):
    """Generated silhouettes shared by the drowned Saint Lumen enemies."""

    def _draw_water_risen(self, surface, body, accent, bob, stretch, state, frame):
        cy = 30 + bob
        pygame.draw.circle(surface, body, (31, cy - 13), 11)
        pygame.draw.ellipse(surface, body, (17 - stretch, cy - 5, 29 + stretch * 2, 34))
        pygame.draw.line(surface, body, (20, cy + 5), (5, cy + 20 + frame * 2), 7)
        pygame.draw.line(surface, body, (43, cy + 5), (58, cy + 18 - frame * 2), 7)
        pygame.draw.line(surface, body, (24, cy + 24), (18, 58), 7)
        pygame.draw.line(surface, body, (39, cy + 24), (46, 58), 7)
        pygame.draw.arc(surface, accent, (17, cy - 17, 29, 23), 0.1, math.pi - 0.1, 3)
        pygame.draw.line(surface, accent, (12, cy + 3), (49, cy + 14), 3)
        self._eyes(surface, ((27, cy - 15), (35, cy - 15)), state)

    def _draw_acolyte(self, surface, body, accent, bob, stretch, state, frame):
        cy = 31 + bob
        pygame.draw.polygon(surface, body, [(31, 7), (16, cy + 25), (48, cy + 25)])
        pygame.draw.circle(surface, _shade(body, 20), (31, cy - 12), 10)
        pygame.draw.arc(surface, accent, (20, cy - 20, 23, 22), 0, math.pi, 3)
        pygame.draw.line(surface, accent, (12, cy + 24), (55, cy + 24), 4)
        staff_x = 54 + stretch
        pygame.draw.line(surface, (104, 76, 48), (staff_x, 11), (staff_x, 58), 4)
        pygame.draw.circle(surface, (113, 187, 177), (staff_x, 10), 7, 2)
        pygame.draw.circle(surface, (63, 121, 128), (staff_x, 10), 3)
        self._eyes(surface, ((28, cy - 14), (35, cy - 14)), state)

    def _draw_bell_wraith(self, surface, body, accent, bob, stretch, state, frame):
        cy = 29 + bob
        pygame.draw.circle(surface, body, (32, cy - 14), 10)
        pygame.draw.polygon(
            surface,
            body,
            [(19 - stretch, cy - 5), (46 + stretch, cy - 5), (55, cy + 26),
             (45, cy + 20), (36, cy + 31), (27, cy + 20), (11, cy + 27)],
        )
        pygame.draw.arc(surface, accent, (14, cy - 22, 36, 34), 0.1, math.pi - 0.1, 3)
        pygame.draw.circle(surface, (171, 205, 190), (32, cy + 7), 8, 2)
        pygame.draw.line(surface, (170, 137, 72), (32, cy + 13), (32, cy + 23), 3)
        self._eyes(surface, ((28, cy - 16), (36, cy - 16)), state)

    def _draw_bell_pilgrim(self, surface, body, accent, bob, stretch, state, frame):
        cy = 52 + bob
        pygame.draw.polygon(
            surface,
            _shade(body, -20),
            [(37, 12), (17, cy + 25), (94, cy + 25), (76, 12)],
        )
        pygame.draw.ellipse(surface, body, (28 - stretch, cy - 30, 58 + stretch * 2, 58))
        pygame.draw.circle(surface, _shade(body, 25), (57, cy - 34), 15)
        pygame.draw.arc(surface, accent, (39, cy - 48, 37, 35), 0, math.pi, 4)

        # The drowned bell is fused into the pilgrim's chest.
        bell = pygame.Rect(42, cy - 10, 34 + stretch, 35)
        pygame.draw.arc(surface, (180, 145, 69), bell, math.pi, math.tau, 5)
        pygame.draw.line(surface, (180, 145, 69), (44, cy + 7), (78 + stretch, cy + 7), 5)
        pygame.draw.circle(surface, (116, 84, 43), (61 + stretch // 2, cy + 20), 5)
        pygame.draw.line(surface, accent, (30, cy - 4), (7, cy + 24 + frame * 3), 10)
        pygame.draw.line(surface, accent, (84, cy - 3), (107, cy + 23 - frame * 3), 10)
        for x in (49, 57, 65):
            pygame.draw.circle(surface, (35, 48, 45), (x, cy - 36), 4)
            pygame.draw.circle(
                surface,
                self.EYE if state != "dead" else (48, 44, 39),
                (x, cy - 36),
                2,
            )
        if getattr(self, "phase", 1) >= 2 and state != "dead":
            pygame.draw.circle(surface, (190, 232, 219), (61, cy + 7), 28, 2)
            pygame.draw.circle(surface, (132, 190, 183), (61, cy + 7), 38, 2)


class WaterRisenPilgrim(ChapelMonster):
    SPECIES = "Water-risen Pilgrim"
    THREAT_LEVEL = 3
    SHAPE = "water_risen"
    BODY = (69, 83, 78)
    ACCENT = (88, 133, 123)
    EYE = (151, 225, 213)
    VISUAL_SIZE = (64, 62)
    HITBOX_SIZE = (35, 27)
    HP, STR, DEX, DEFENSE = 230, 19, 6, 5
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 0.78, 47, 69
    STATUS_EFFECT = ("Slow", 100, 0)
    AI_CLASS = SwarmMonsterAI
    XP_REWARD, BOUNTY_VALUE = 20, 3


class FloodedAcolyte(ChapelMonster):
    SPECIES = "Flooded Acolyte"
    THREAT_LEVEL = 4
    SHAPE = "acolyte"
    BODY = (62, 73, 79)
    ACCENT = (110, 151, 139)
    EYE = (169, 235, 218)
    VISUAL_SIZE = (68, 64)
    HITBOX_SIZE = (36, 28)
    HP, STR, DEX, INT, DEFENSE = 270, 17, 8, 14, 6
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 0.72, 175, 76
    DAMAGE_TYPE = "Poison"
    STATUS_EFFECT = ("Poison", 150, 3)
    AI_CLASS = ToxicPulseAI
    XP_REWARD, BOUNTY_VALUE = 31, 5


class BellWraith(ChapelMonster):
    SPECIES = "Bell Wraith"
    THREAT_LEVEL = 5
    SHAPE = "bell_wraith"
    BODY = (67, 74, 91)
    ACCENT = (119, 151, 157)
    EYE = (188, 239, 227)
    VISUAL_SIZE = (66, 64)
    HITBOX_SIZE = (34, 24)
    HP, STR, DEX, INT, DEFENSE = 300, 20, 14, 16, 5
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.18, 205, 66
    DAMAGE_TYPE = "Magic"
    STATUS_EFFECT = ("Slow", 130, 0)
    AI_CLASS = RangedKiteMonsterAI
    XP_REWARD, BOUNTY_VALUE = 43, 7


class BellDrownedPilgrim(ChapelMonster):
    SPECIES = "Bell-Drowned Pilgrim"
    THREAT_LEVEL = 5
    SHAPE = "bell_pilgrim"
    BODY = (57, 69, 69)
    ACCENT = (104, 139, 126)
    EYE = (180, 235, 220)
    VISUAL_SIZE = (122, 104)
    HITBOX_SIZE = (72, 48)
    HP, STR, DEX, INT, DEFENSE = 720, 27, 7, 12, 8
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 0.65, 74, 82
    STATUS_EFFECT = ("Slow", 160, 0)
    AI_CLASS = HeavyChargeAI
    XP_REWARD, BOUNTY_VALUE = 130, 24

    def __init__(self, name, x, y, team_color):
        self.phase = 1
        super().__init__(name, x, y, team_color)
        self.is_boss = True
        self.boss_id = "bell_drowned_pilgrim"
        self.pending_spawn: List[CodeMonster] = []
        self.bell_pulse_cooldown = 150
        self.pulse_count = 0

    def _enter_second_phase(self, manager=None):
        if self.phase >= 2 or self.is_dead:
            return
        self.phase = 2
        self.walk_speed = 0.86 * MOVE_SCALE
        self.speed = self.walk_speed
        self.attack_speed = 62
        self.strength += 6
        self.defense += 2
        self.pending_spawn = [
            WaterRisenPilgrim(
                f"Bell-Risen {index + 1}",
                self.rect.centerx + (index - 1) * 82,
                self.rect.centery + 110,
                self.team_color,
            )
            for index in range(3)
        ]
        _vfx_text(manager, self, "THE DROWNED BELL TOLLS", (183, 229, 215))

    def release_bell_wave(self, manager=None) -> int:
        """Damage and slow nearby enemies; returns the number of targets hit."""
        if manager is None:
            return 0
        hit = 0
        for target in list(getattr(manager, "all_units", ())):
            if target is self or getattr(target, "is_dead", False):
                continue
            if getattr(target, "team_color", None) == self.team_color:
                continue
            distance = math.hypot(
                target.rect.centerx - self.rect.centerx,
                target.rect.centery - self.rect.centery,
            )
            if distance > (270 if self.phase >= 2 else 225):
                continue
            try:
                target.take_damage(
                    9 + self.phase * 4,
                    "Magic",
                    attacker=self,
                    manager=manager,
                )
                target.apply_status("Slow", 95 + self.phase * 25, 0)
                hit += 1
            except Exception:
                continue
        self.pulse_count += 1
        _vfx_text(manager, self, "BELL WAVE", (177, 222, 211))
        return hit

    def update(self, obstacles=None, manager=None):
        if not self.is_dead and self.current_hp <= self.max_hp * 0.58:
            self._enter_second_phase(manager)
        super().update(obstacles, manager)
        if self.is_dead:
            return
        self.bell_pulse_cooldown -= 1
        if self.bell_pulse_cooldown <= 0:
            self.release_bell_wave(manager)
            self.bell_pulse_cooldown = 95 if self.phase >= 2 else 150


DROWNED_CHAPEL_MONSTER_CLASSES = (
    WaterRisenPilgrim,
    FloodedAcolyte,
    BellWraith,
)

DROWNED_CHAPEL_LOOT = {
    "Water-risen Pilgrim": [
        {"item": "Waterlogged Cloth", "chance": 0.75, "min": 1, "max": 2},
        {"item": "Sanctified Wax", "chance": 0.18, "min": 1, "max": 1},
    ],
    "Flooded Acolyte": [
        {"item": "Grave-Lotus", "chance": 0.62, "min": 1, "max": 2},
        {"item": "Tainted Water Sample", "chance": 0.30, "min": 1, "max": 1},
    ],
    "Bell Wraith": [
        {"item": "Bell Shard", "chance": 0.58, "min": 1, "max": 2},
        {"item": "Sanctified Wax", "chance": 0.32, "min": 1, "max": 1},
    ],
    "Bell-Drowned Pilgrim": [
        {"item": "Drowned Bell Clapper", "chance": 1.0, "min": 1, "max": 1},
        {"item": "Saint Lumen Seal", "chance": 1.0, "min": 1, "max": 1},
    ],
}
