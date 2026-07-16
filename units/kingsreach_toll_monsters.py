"""Code-rendered level 6-8 threats for Kingsreach Toll."""
from __future__ import annotations

import math
from typing import Iterable, List

import pygame

from ai.tier0_monster_ai import HeavyChargeAI, RangedKiteMonsterAI, SkitterMonsterAI, ToxicPulseAI
from units.tier0_monsters import CodeMonster, MOVE_SCALE, _shade, _vfx_text


class KingsreachThreat(CodeMonster):
    def _draw_enforcer(self, surface, body, accent, bob, stretch, state, frame):
        cx, cy = 42, 48 + bob
        skin = (139, 104, 80)
        steel = (134, 143, 145)
        pygame.draw.ellipse(surface, (24, 23, 22, 95), (15, 72, 56, 13))
        pygame.draw.line(surface, body, (cx - 10, cy + 17), (cx - 14 + (4 if frame else -3), 80), 9)
        pygame.draw.line(surface, body, (cx + 10, cy + 17), (cx + 15 + (-4 if frame else 3), 80), 9)
        pygame.draw.polygon(surface, _shade(body, -12), [(cx - 28, cy - 21), (cx + 26, cy - 20), (cx + 29, cy + 24), (cx - 31, cy + 25)])
        pygame.draw.rect(surface, body, (cx - 18, cy - 17, 36, 39), border_radius=6)
        pygame.draw.circle(surface, skin, (cx, cy - 30), 13)
        pygame.draw.polygon(surface, steel, [(cx - 17, cy - 38), (cx + 17, cy - 38), (cx + 12, cy - 24), (cx - 12, cy - 24)])
        pygame.draw.line(surface, accent, (cx - 15, cy + 1), (cx + 31 + stretch, cy - 22), 6)
        pygame.draw.polygon(surface, steel, [(cx + 27 + stretch, cy - 29), (cx + 43 + stretch, cy - 24), (cx + 29 + stretch, cy - 17)])
        pygame.draw.rect(surface, (128, 48, 42), (cx - 24, cy - 12, 9, 32))
        eye = (38, 31, 27) if state == "dead" else self.EYE
        pygame.draw.circle(surface, eye, (cx + 5, cy - 32), 2)

    def _draw_escapee(self, surface, body, accent, bob, stretch, state, frame):
        cx, cy = 35, 42 + bob
        skin = (125, 105, 83)
        pygame.draw.ellipse(surface, (21, 21, 20, 80), (11, 65, 49, 12))
        pygame.draw.line(surface, body, (cx - 8, cy + 14), (cx - 15 + (5 if frame else -3), 72), 7)
        pygame.draw.line(surface, body, (cx + 8, cy + 14), (cx + 14 + (-5 if frame else 3), 72), 7)
        pygame.draw.polygon(surface, body, [(cx - 22, cy - 17), (cx + 20, cy - 16), (cx + 24, cy + 20), (cx - 25, cy + 21)])
        pygame.draw.circle(surface, skin, (cx + stretch, cy - 27), 11)
        pygame.draw.line(surface, accent, (cx - 18, cy - 8), (cx + 19, cy + 14), 5)
        for x, y in ((cx - 8, cy - 4), (cx + 6, cy + 6), (cx + 15, cy - 9)):
            pygame.draw.circle(surface, (116, 74, 54), (x, y), 3)
        eye = (44, 38, 31) if state == "dead" else self.EYE
        pygame.draw.circle(surface, eye, (cx + 4 + stretch, cy - 29), 2)
        if state != "dead":
            pygame.draw.arc(surface, (119, 151, 104), (cx - 31, cy - 38, 62, 58), 0.2, 2.8, 2)

    def _draw_bandit(self, surface, body, accent, bob, stretch, state, frame):
        cx, cy = 40, 46 + bob
        skin = (135, 98, 73)
        pygame.draw.ellipse(surface, (22, 20, 19, 90), (13, 70, 55, 13))
        pygame.draw.line(surface, body, (cx - 10, cy + 16), (cx - 16 + (5 if frame else -4), 78), 8)
        pygame.draw.line(surface, body, (cx + 10, cy + 16), (cx + 16 + (-5 if frame else 4), 78), 8)
        pygame.draw.polygon(surface, _shade(body, -18), [(cx - 27, cy - 18), (cx + 24, cy - 18), (cx + 30, cy + 23), (cx - 30, cy + 23)])
        pygame.draw.circle(surface, skin, (cx, cy - 29), 12)
        pygame.draw.polygon(surface, accent, [(cx - 15, cy - 36), (cx + 15, cy - 36), (cx + 21, cy - 25), (cx - 18, cy - 23)])
        pygame.draw.line(surface, (93, 64, 41), (cx - 19, cy + 4), (cx + 34 + stretch, cy - 15), 6)
        pygame.draw.line(surface, (174, 178, 163), (cx + 30 + stretch, cy - 20), (cx + 47 + stretch, cy - 18), 4)
        eye = (38, 30, 26) if state == "dead" else self.EYE
        pygame.draw.circle(surface, eye, (cx + 5, cy - 31), 2)

    def _draw_tollmaster(self, surface, body, accent, bob, stretch, state, frame):
        cx, cy = 62, 68 + bob
        skin = (148, 105, 77)
        steel = (145, 151, 151)
        phase = int(getattr(self, "phase", 1))
        pygame.draw.ellipse(surface, (17, 17, 18, 110), (17, 105, 96, 18))
        pygame.draw.line(surface, body, (cx - 19, cy + 24), (cx - 26 + (5 if frame else -3), 117), 15)
        pygame.draw.line(surface, body, (cx + 18, cy + 24), (cx + 26 + (-5 if frame else 3), 117), 15)
        pygame.draw.polygon(surface, _shade(body, -18), [(cx - 48, cy - 31), (cx + 43, cy - 29), (cx + 51, cy + 35), (cx - 53, cy + 36)])
        pygame.draw.rect(surface, body, (cx - 31, cy - 27, 62, 61), border_radius=9)
        pygame.draw.circle(surface, skin, (cx + 4, cy - 47), 20)
        pygame.draw.polygon(surface, steel, [(cx - 22, cy - 57), (cx + 31, cy - 57), (cx + 24, cy - 38), (cx - 16, cy - 38)])
        pygame.draw.line(surface, accent, (cx - 26, cy - 5), (cx + 52 + stretch, cy - 37), 9)
        pygame.draw.polygon(surface, steel, [(cx + 46 + stretch, cy - 47), (cx + 68 + stretch, cy - 40), (cx + 49 + stretch, cy - 29)])
        pygame.draw.rect(surface, (137, 48, 42), (cx - 41, cy - 18, 13, 49))
        pygame.draw.circle(surface, (205, 168, 77), (cx - 35, cy + 5), 9, 3)
        eye = (43, 33, 27) if state == "dead" else self.EYE
        pygame.draw.circle(surface, eye, (cx + 12, cy - 50), 4)
        if phase >= 2 and state != "dead":
            for x in (cx - 38, cx, cx + 38):
                pygame.draw.line(surface, (196, 160, 76), (x, cy + 39), (x + 5, cy - 61), 3)
        if phase >= 3 and state != "dead":
            pygame.draw.arc(surface, (171, 66, 56), (cx - 62, cy - 69, 124, 126), 0.2, 3.0, 5)


class CrownTollEnforcer(KingsreachThreat):
    SPECIES = "Crown Toll Enforcer"
    THREAT_LEVEL = 6
    SHAPE = "enforcer"
    BODY = (68, 75, 76)
    ACCENT = (151, 104, 52)
    EYE = (228, 190, 93)
    VISUAL_SIZE = (88, 86)
    HITBOX_SIZE = (45, 33)
    HP, STR, DEX, DEFENSE = 325, 27, 17, 12
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.08, 70, 59
    STATUS_EFFECT = ("Slow", 75, 0)
    AI_CLASS = SkitterMonsterAI
    XP_REWARD, BOUNTY_VALUE = 80, 13


class FeveredEscapee(KingsreachThreat):
    SPECIES = "Fevered Escapee"
    THREAT_LEVEL = 6
    SHAPE = "escapee"
    BODY = (96, 90, 69)
    ACCENT = (135, 109, 78)
    EYE = (194, 224, 129)
    VISUAL_SIZE = (72, 79)
    HITBOX_SIZE = (39, 31)
    HP, STR, DEX, DEFENSE = 285, 22, 18, 5
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.28, 48, 52
    DAMAGE_TYPE = "Poison"
    STATUS_EFFECT = ("Poison", 115, 3)
    AI_CLASS = ToxicPulseAI
    XP_REWARD, BOUNTY_VALUE = 76, 10


class CausewayBandit(KingsreachThreat):
    SPECIES = "Causeway Bandit"
    THREAT_LEVEL = 7
    SHAPE = "bandit"
    BODY = (72, 61, 50)
    ACCENT = (91, 91, 76)
    EYE = (229, 164, 79)
    VISUAL_SIZE = (86, 84)
    HITBOX_SIZE = (44, 31)
    HP, STR, DEX, DEFENSE = 365, 29, 22, 8
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.22, 145, 57
    STATUS_EFFECT = ("Bleed", 110, 3)
    AI_CLASS = RangedKiteMonsterAI
    XP_REWARD, BOUNTY_VALUE = 96, 16


class TollmasterHadrikCrowl(KingsreachThreat):
    SPECIES = "Tollmaster Hadrik Crowl"
    THREAT_LEVEL = 8
    SHAPE = "tollmaster"
    BODY = (59, 67, 70)
    ACCENT = (157, 101, 48)
    EYE = (239, 186, 82)
    VISUAL_SIZE = (136, 128)
    HITBOX_SIZE = (76, 56)
    HP, STR, DEX, INT, DEFENSE = 1640, 35, 17, 11, 20
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.00, 96, 66
    STATUS_EFFECT = ("Bleed", 150, 4)
    AI_CLASS = HeavyChargeAI
    XP_REWARD, BOUNTY_VALUE = 310, 62

    def __init__(self, name, x, y, team_color):
        self.phase = 1
        super().__init__(name, x, y, team_color)
        self.is_boss = True
        self.boss_id = "tollmaster_hadrik_crowl"
        self.pending_spawn: List[CodeMonster] = []
        self.pending_stamp_shock = False
        self.pending_tax_shout = False
        self.phase_two_triggered = False
        self.phase_three_triggered = False
        self.tax_shout_cooldown = 185

    def _phase_two(self, manager=None):
        if self.phase_two_triggered or self.is_dead:
            return
        self.phase_two_triggered = True
        self.phase = 2
        self.speed = self.walk_speed = 1.16 * MOVE_SCALE
        self.attack_speed = 55
        self.pending_spawn = [
            CrownTollEnforcer(
                f"Crowl's Collector {index + 1}",
                self.rect.centerx + (index - 1) * 105,
                self.rect.centery + 145,
                self.team_color,
            )
            for index in range(3)
        ]
        self.pending_stamp_shock = True
        _vfx_text(manager, self, "SEIZE THEIR PAPERS", (228, 184, 91))

    def _phase_three(self, manager=None):
        if self.phase_three_triggered or self.is_dead:
            return
        self.phase_three_triggered = True
        self.phase = 3
        self.speed = self.walk_speed = 1.31 * MOVE_SCALE
        self.attack_speed = 46
        self.strength += 11
        self.defense += 6
        self.pending_spawn.extend(
            [
                CausewayBandit("Crowl's Paid Knife One", self.rect.centerx - 190, self.rect.centery + 150, self.team_color),
                CausewayBandit("Crowl's Paid Knife Two", self.rect.centerx + 190, self.rect.centery + 150, self.team_color),
            ]
        )
        self.pending_stamp_shock = True
        self.pending_tax_shout = True
        _vfx_text(manager, self, "THE ROAD OWES ME", (229, 90, 74))

    def release_tax_shout(self, targets: Iterable, manager=None) -> int:
        hit = 0
        radius = 325 if self.phase >= 3 else 245
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
                target.take_damage(15 + self.phase * 5, "Physical", attacker=self, manager=manager)
                target.apply_status("Slow", 90 + self.phase * 25, 0)
                if self.phase >= 3:
                    target.apply_status("Bleed", 130, 4)
                hit += 1
            except Exception:
                continue
        _vfx_text(manager, self, "COLLECTION DUE", (235, 172, 88))
        return hit

    def update(self, obstacles=None, manager=None):
        if not self.is_dead and self.current_hp <= self.max_hp * 0.67:
            self._phase_two(manager)
        if not self.is_dead and self.current_hp <= self.max_hp * 0.31:
            self._phase_three(manager)
        super().update(obstacles, manager)
        if self.is_dead:
            return
        self.tax_shout_cooldown -= 1
        if self.tax_shout_cooldown <= 0:
            self.pending_tax_shout = True
            self.tax_shout_cooldown = 120 if self.phase >= 3 else 170


KINGSREACH_THREAT_CLASSES = (CrownTollEnforcer, FeveredEscapee, CausewayBandit)

KINGSREACH_LOOT = {
    "Crown Toll Enforcer": [
        {"item": "Wax Seal", "chance": 0.48, "min": 1, "max": 1},
        {"item": "Scrap Iron", "chance": 0.70, "min": 1, "max": 2},
    ],
    "Fevered Escapee": [
        {"item": "Feverfew", "chance": 0.64, "min": 1, "max": 2},
        {"item": "Torn Bandage", "chance": 0.52, "min": 1, "max": 2},
    ],
    "Causeway Bandit": [
        {"item": "Parchment Sheet", "chance": 0.42, "min": 1, "max": 1},
        {"item": "Silver Cache", "chance": 0.28, "min": 1, "max": 1},
    ],
    "Tollmaster Hadrik Crowl": [
        {"item": "Crowl's Black Ledger", "chance": 1.0, "min": 1, "max": 1},
        {"item": "Crown Seal Token", "chance": 1.0, "min": 1, "max": 1},
        {"item": "Wax Seal", "chance": 1.0, "min": 2, "max": 3},
    ],
}
