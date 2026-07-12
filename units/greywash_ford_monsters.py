"""Code-rendered level 5-7 creatures for Greywash Ford."""
from __future__ import annotations

import math
from typing import Iterable, List

import pygame

from ai.tier0_monster_ai import HeavyChargeAI, PounceMonsterAI, SkitterMonsterAI, SwarmMonsterAI
from units.tier0_monsters import CodeMonster, _shade, _vfx_text


class GreywashMonster(CodeMonster):
    def _draw_riverjaw(self, surface, body, accent, bob, stretch, state, frame):
        cy = 34 + bob
        pygame.draw.polygon(surface, accent, [(11, cy), (1, cy - 9), (4, cy + 8), (24, cy + 5)])
        pygame.draw.ellipse(surface, body, (11, cy - 14, 48 + stretch, 27))
        pygame.draw.polygon(surface, _shade(body, 18), [(47, cy - 12), (76 + stretch, cy - 9), (76 + stretch, cy + 6), (47, cy + 7)])
        for x in (21, 33, 46):
            pygame.draw.polygon(surface, accent, [(x, cy - 10), (x + 5, cy - 23), (x + 10, cy - 9)])
        for x in (23, 54):
            kick = 4 if frame else -3
            pygame.draw.line(surface, body, (x, cy + 8), (x - 8 + kick, cy + 20), 6)
        eye = (40, 28, 23) if state == "dead" else self.EYE
        pygame.draw.circle(surface, eye, (66 + stretch, cy - 7), 3)
        pygame.draw.line(surface, (217, 205, 150), (70 + stretch, cy + 2), (79 + stretch, cy + 1), 2)

    def _draw_deserter(self, surface, body, accent, bob, stretch, state, frame):
        cx, cy = 39, 42 + bob
        cloak = _shade(body, -18)
        skin = (132, 102, 80)
        metal = (121, 126, 123)
        pygame.draw.ellipse(surface, (20, 19, 18, 80), (16, 65, 48, 12))
        pygame.draw.line(surface, body, (cx - 10, cy + 11), (cx - 15 + (4 if frame else -2), 69), 8)
        pygame.draw.line(surface, body, (cx + 8, cy + 11), (cx + 14 + (-4 if frame else 2), 69), 8)
        pygame.draw.polygon(surface, cloak, [(cx - 21, cy - 18), (cx + 18, cy - 16), (cx + 25, cy + 21), (cx - 25, cy + 22)])
        pygame.draw.rect(surface, body, (cx - 14, cy - 14, 28, 34), border_radius=5)
        pygame.draw.circle(surface, skin, (cx, cy - 25), 11)
        pygame.draw.polygon(surface, metal, [(cx - 15, cy - 31), (cx + 15, cy - 31), (cx + 10, cy - 18), (cx - 10, cy - 18)])
        pygame.draw.line(surface, accent, (cx - 11, cy + 1), (cx + 21 + stretch, cy - 17), 5)
        pygame.draw.polygon(surface, metal, [(cx + 18 + stretch, cy - 21), (cx + 31 + stretch, cy - 18), (cx + 19 + stretch, cy - 13)])
        eye = (42, 33, 28) if state == "dead" else self.EYE
        pygame.draw.circle(surface, eye, (cx + 4, cy - 27), 2)
        pygame.draw.line(surface, (92, 40, 37), (cx - 12, cy - 21), (cx + 11, cy - 22), 3)

    def _draw_ford_brute(self, surface, body, accent, bob, stretch, state, frame):
        cx, cy = 48, 53 + bob
        skin = (117, 92, 73)
        pygame.draw.ellipse(surface, (22, 20, 18, 90), (14, 81, 74, 15))
        pygame.draw.line(surface, body, (cx - 18, cy + 19), (cx - 25 + (4 if frame else -3), 91), 13)
        pygame.draw.line(surface, body, (cx + 17, cy + 19), (cx + 25 + (-4 if frame else 3), 91), 13)
        pygame.draw.ellipse(surface, body, (cx - 34, cy - 29, 68 + stretch, 59))
        pygame.draw.circle(surface, skin, (cx + 5 + stretch, cy - 38), 17)
        pygame.draw.polygon(surface, accent, [(cx - 34, cy - 22), (cx - 10, cy - 42), (cx + 3, cy - 18)])
        pygame.draw.polygon(surface, accent, [(cx + 4, cy - 18), (cx + 29, cy - 42), (cx + 38, cy - 15)])
        pygame.draw.line(surface, (82, 60, 42), (cx - 28, cy + 1), (cx + 45 + stretch, cy - 14), 9)
        pygame.draw.circle(surface, (111, 116, 112), (cx + 45 + stretch, cy - 14), 12)
        eye = (40, 31, 27) if state == "dead" else self.EYE
        pygame.draw.circle(surface, eye, (cx + 11 + stretch, cy - 41), 3)

    def _draw_captain(self, surface, body, accent, bob, stretch, state, frame):
        cx, cy = 61, 68 + bob
        skin = (139, 104, 79)
        metal = (132, 139, 140)
        phase = int(getattr(self, "phase", 1))
        pygame.draw.ellipse(surface, (19, 19, 20, 100), (18, 103, 94, 18))
        pygame.draw.line(surface, body, (cx - 18, cy + 23), (cx - 24 + (5 if frame else -3), 115), 14)
        pygame.draw.line(surface, body, (cx + 17, cy + 23), (cx + 25 + (-5 if frame else 3), 115), 14)
        pygame.draw.polygon(surface, _shade(body, -18), [(cx - 43, cy - 28), (cx + 38, cy - 26), (cx + 47, cy + 33), (cx - 50, cy + 32)])
        pygame.draw.rect(surface, body, (cx - 28, cy - 25, 56, 55), border_radius=8)
        pygame.draw.circle(surface, skin, (cx + 5, cy - 44), 19)
        pygame.draw.polygon(surface, metal, [(cx - 20, cy - 52), (cx + 30, cy - 52), (cx + 22, cy - 34), (cx - 14, cy - 34)])
        pygame.draw.line(surface, (92, 49, 44), (cx - 20, cy - 43), (cx + 27, cy - 45), 5)
        pygame.draw.line(surface, accent, (cx - 25, cy - 4), (cx + 48 + stretch, cy - 34), 8)
        pygame.draw.polygon(surface, metal, [(cx + 42 + stretch, cy - 42), (cx + 62 + stretch, cy - 36), (cx + 45 + stretch, cy - 26)])
        eye = (45, 34, 28) if state == "dead" else self.EYE
        pygame.draw.circle(surface, eye, (cx + 12, cy - 47), 4)
        if phase >= 2 and state != "dead":
            pygame.draw.arc(surface, (87, 151, 166), (cx - 54, cy - 62, 112, 112), 0.2, 3.0, 4)
        if phase >= 3 and state != "dead":
            for x in (cx - 31, cx, cx + 31):
                pygame.draw.line(surface, (187, 219, 218), (x, cy + 35), (x + 7, cy - 58), 3)


class GreywashRiverjaw(GreywashMonster):
    SPECIES = "Greywash Riverjaw"
    THREAT_LEVEL = 5
    SHAPE = "riverjaw"
    BODY = (65, 91, 75)
    ACCENT = (104, 123, 84)
    EYE = (229, 193, 77)
    VISUAL_SIZE = (84, 59)
    HITBOX_SIZE = (49, 28)
    HP, STR, DEX, DEFENSE = 255, 23, 15, 7
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.18, 55, 58
    STATUS_EFFECT = ("Bleed", 120, 3)
    AI_CLASS = PounceMonsterAI
    XP_REWARD, BOUNTY_VALUE = 61, 9


class CrownDeserter(GreywashMonster):
    SPECIES = "Crown Deserter"
    THREAT_LEVEL = 5
    SHAPE = "deserter"
    BODY = (66, 73, 69)
    ACCENT = (128, 91, 53)
    EYE = (225, 178, 87)
    VISUAL_SIZE = (84, 78)
    HITBOX_SIZE = (42, 31)
    HP, STR, DEX, DEFENSE = 238, 21, 18, 8
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.16, 63, 56
    STATUS_EFFECT = ("Bleed", 100, 2)
    AI_CLASS = SkitterMonsterAI
    XP_REWARD, BOUNTY_VALUE = 64, 10


class FordBrute(GreywashMonster):
    SPECIES = "Ford Brute"
    THREAT_LEVEL = 6
    SHAPE = "ford_brute"
    BODY = (77, 74, 68)
    ACCENT = (97, 85, 68)
    EYE = (222, 157, 69)
    VISUAL_SIZE = (100, 99)
    HITBOX_SIZE = (61, 43)
    HP, STR, DEX, DEFENSE = 430, 34, 9, 15
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 0.86, 79, 76
    STATUS_EFFECT = ("Stun", 45, 0)
    AI_CLASS = HeavyChargeAI
    XP_REWARD, BOUNTY_VALUE = 95, 16


class CaptainGarranVale(GreywashMonster):
    SPECIES = "Captain Garran Vale"
    THREAT_LEVEL = 7
    SHAPE = "captain"
    BODY = (57, 67, 69)
    ACCENT = (126, 80, 48)
    EYE = (232, 178, 91)
    VISUAL_SIZE = (132, 124)
    HITBOX_SIZE = (72, 54)
    HP, STR, DEX, INT, DEFENSE = 1380, 40, 16, 12, 17
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.02, 91, 64
    DAMAGE_TYPE = "Physical"
    STATUS_EFFECT = ("Bleed", 150, 4)
    AI_CLASS = HeavyChargeAI
    XP_REWARD, BOUNTY_VALUE = 260, 46

    def __init__(self, name, x, y, team_color):
        self.phase = 1
        super().__init__(name, x, y, team_color)
        self.is_boss = True
        self.boss_id = "greywash_deserter_captain"
        self.pending_spawn: List[CodeMonster] = []
        self.pending_flood_pulses = 0
        self.pending_command_shout = False
        self.shout_cooldown = 190
        self.phase_two_triggered = False
        self.phase_three_triggered = False

    def _phase_two(self, manager=None):
        if self.phase_two_triggered or self.is_dead:
            return
        self.phase_two_triggered = True
        self.phase = 2
        self.speed = self.walk_speed = 1.18
        self.attack_speed = 55
        self.pending_spawn = [
            CrownDeserter(
                f"Vale's Rearguard {index + 1}",
                self.rect.centerx + (index - 1) * 95,
                self.rect.centery + 130,
                self.team_color,
            )
            for index in range(3)
        ]
        self.pending_flood_pulses += 1
        _vfx_text(manager, self, "HOLD THE FORD", (222, 177, 89))

    def _phase_three(self, manager=None):
        if self.phase_three_triggered or self.is_dead:
            return
        self.phase_three_triggered = True
        self.phase = 3
        self.speed = self.walk_speed = 1.31
        self.attack_speed = 46
        self.strength += 10
        self.defense += 5
        self.pending_spawn.extend(
            [
                FordBrute("Vale's Ford Brute One", self.rect.centerx - 170, self.rect.centery + 140, self.team_color),
                FordBrute("Vale's Ford Brute Two", self.rect.centerx + 170, self.rect.centery + 140, self.team_color),
            ]
        )
        self.pending_flood_pulses += 2
        self.pending_command_shout = True
        _vfx_text(manager, self, "CROWN ROAD OR GRAVE", (227, 97, 76))

    def release_command_shout(self, targets: Iterable, manager=None) -> int:
        hit = 0
        radius = 300 if self.phase >= 3 else 235
        for target in list(targets or ()):
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
                target.take_damage(13 + self.phase * 4, "Physical", attacker=self, manager=manager)
                target.apply_status("Slow", 80 + self.phase * 25, 0)
                if self.phase >= 3:
                    target.apply_status("Bleed", 120, 3)
                hit += 1
            except Exception:
                continue
        _vfx_text(manager, self, "DESERTER'S COMMAND", (230, 178, 100))
        return hit

    def update(self, obstacles=None, manager=None):
        if not self.is_dead and self.current_hp <= self.max_hp * 0.66:
            self._phase_two(manager)
        if not self.is_dead and self.current_hp <= self.max_hp * 0.30:
            self._phase_three(manager)
        super().update(obstacles, manager)
        if self.is_dead:
            return
        self.shout_cooldown -= 1
        if self.shout_cooldown <= 0:
            self.pending_command_shout = True
            self.shout_cooldown = 115 if self.phase >= 3 else 165


GREYWASH_MONSTER_CLASSES = (GreywashRiverjaw, CrownDeserter, FordBrute)

GREYWASH_LOOT = {
    "Greywash Riverjaw": [
        {"item": "Riverjaw Hide", "chance": 0.68, "min": 1, "max": 2},
        {"item": "River Meat", "chance": 0.74, "min": 1, "max": 2},
    ],
    "Crown Deserter": [
        {"item": "Scrap Iron", "chance": 0.72, "min": 1, "max": 2},
        {"item": "Torn Crown Tabard", "chance": 0.24, "min": 1, "max": 1},
    ],
    "Ford Brute": [
        {"item": "Scrap Iron", "chance": 0.82, "min": 2, "max": 4},
        {"item": "Driftwood", "chance": 0.55, "min": 1, "max": 3},
    ],
    "Captain Garran Vale": [
        {"item": "Vale's Broken Signet", "chance": 1.0, "min": 1, "max": 1},
        {"item": "Scrap Iron", "chance": 1.0, "min": 5, "max": 8},
        {"item": "Wax Seal", "chance": 1.0, "min": 1, "max": 2},
    ],
}
