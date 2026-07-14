"""Code-rendered level 4-6 rat ecology for the Muckford Warrens."""
from __future__ import annotations

import math
from typing import Iterable, List

import pygame

from ai.tier0_monster_ai import (
    HeavyChargeAI,
    PounceMonsterAI,
    SkitterMonsterAI,
    SwarmMonsterAI,
    ToxicPulseAI,
)
from units.tier0_monsters import CodeMonster, _shade, _vfx_text


class WarrensMonster(CodeMonster):
    """Generated silhouettes shared by the sewer and cellar rat army."""

    def _draw_rat_swarm(self, surface, body, accent, bob, stretch, state, frame):
        offsets = ((15, 30), (34, 23), (56, 31), (43, 39))
        for index, (cx, cy) in enumerate(offsets):
            cy += bob + (frame if index % 2 else -frame)
            length = 18 + (stretch if state == "attack" and index == 1 else 0)
            pygame.draw.ellipse(surface, body, (cx - 8, cy - 6, length, 12))
            pygame.draw.circle(surface, _shade(body, 18), (cx + 8, cy - 2), 5)
            pygame.draw.circle(surface, accent, (cx + 10, cy - 4), 2)
            pygame.draw.arc(surface, accent, (cx - 18, cy - 4, 22, 16), 0.0, 2.4, 2)

    def _draw_violet_rat(self, surface, body, accent, bob, stretch, state, frame):
        cy = 31 + bob
        pygame.draw.arc(surface, accent, (0, cy - 4, 31, 24), 0.1, 2.7, 3)
        pygame.draw.ellipse(surface, body, (13 - stretch, cy - 13, 42 + stretch * 2, 26))
        pygame.draw.circle(surface, _shade(body, 18), (52 + stretch, cy - 7), 10)
        pygame.draw.polygon(surface, accent, [(48, cy - 14), (51, cy - 25), (57, cy - 14)])
        pygame.draw.polygon(surface, accent, [(56, cy - 14), (62, cy - 23), (63, cy - 10)])
        pygame.draw.line(surface, body, (22, cy + 8), (15, 47), 5)
        pygame.draw.line(surface, body, (44, cy + 8), (51, 47), 5)
        eye = self.EYE if state != "dead" else (45, 34, 51)
        pygame.draw.circle(surface, eye, (56 + stretch, cy - 8), 3)
        pygame.draw.circle(surface, _shade(eye, 55), (56 + stretch, cy - 8), 1)

    def _draw_rat_rider(self, surface, body, accent, bob, stretch, state, frame):
        cy = 44 + bob
        pygame.draw.arc(surface, accent, (0, cy - 2, 39, 27), 0.1, 2.7, 3)
        pygame.draw.ellipse(surface, body, (14 - stretch, cy - 16, 57 + stretch * 2, 31))
        pygame.draw.circle(surface, _shade(body, 16), (69 + stretch, cy - 9), 12)
        pygame.draw.line(surface, body, (28, cy + 8), (20, 65), 6)
        pygame.draw.line(surface, body, (55, cy + 8), (64, 65), 6)
        pygame.draw.circle(surface, self.EYE if state != "dead" else (45, 34, 51), (74 + stretch, cy - 10), 3)
        rider_y = cy - 29 - (2 if frame else 0)
        pygame.draw.circle(surface, (111, 91, 73), (43, rider_y - 8), 7)
        pygame.draw.rect(surface, (91, 76, 65), (36, rider_y - 2, 16, 20), border_radius=4)
        pygame.draw.polygon(surface, (137, 118, 91), [(35, rider_y - 15), (43, rider_y - 23), (51, rider_y - 15)])
        pygame.draw.line(surface, (120, 83, 46), (48, rider_y + 3), (77 + stretch, rider_y - 10), 4)
        pygame.draw.polygon(surface, (164, 149, 118), [(75 + stretch, rider_y - 13), (86 + stretch, rider_y - 10), (76 + stretch, rider_y - 6)])

    def _draw_waste_gnawer(self, surface, body, accent, bob, stretch, state, frame):
        cy = 43 + bob
        pygame.draw.arc(surface, accent, (0, cy + 1, 37, 31), 0.1, 2.8, 4)
        pygame.draw.ellipse(surface, body, (11 - stretch, cy - 23, 66 + stretch * 2, 45))
        pygame.draw.circle(surface, _shade(body, 17), (76 + stretch, cy - 12), 15)
        pygame.draw.line(surface, body, (27, cy + 12), (20, 69), 8)
        pygame.draw.line(surface, body, (59, cy + 12), (68, 69), 8)
        for x, height in ((24, 18), (38, 27), (53, 21), (66, 16)):
            pygame.draw.polygon(
                surface,
                accent,
                [(x - 5, cy - 14), (x, cy - 14 - height), (x + 7, cy - 11)],
            )
            pygame.draw.line(surface, _shade(accent, 55), (x, cy - 13 - height), (x + 4, cy - 12), 2)
        pygame.draw.circle(surface, self.EYE if state != "dead" else (46, 34, 49), (82 + stretch, cy - 14), 4)
        pygame.draw.line(surface, (207, 198, 120), (83 + stretch, cy - 4), (91 + stretch, cy - 2), 3)

    def _draw_hulk_rat(self, surface, body, accent, bob, stretch, state, frame):
        """Valtava lihaskimppurotta: leveä kroppa, kyhmyinen selkä ja
        raskas etukäpälä. Isompi ja uhkaavampi kuin Waste Gnawer."""
        cy = 58 + bob
        # Häntä
        pygame.draw.arc(surface, accent, (0, cy - 4, 44, 40), 0.1, 2.8, 6)
        # Kroppa (leveä pisara)
        pygame.draw.ellipse(surface, body, (16 - stretch, cy - 30, 88 + stretch * 2, 60))
        # Selän kyhmyt (lihakset)
        for hx in (34, 52, 70):
            pygame.draw.circle(surface, _shade(body, 14), (hx, cy - 22), 11)
        # Pää
        pygame.draw.circle(surface, _shade(body, 18), (104 + stretch, cy - 16), 22)
        # Raskaat etukäpälät
        pygame.draw.ellipse(surface, _shade(body, -10), (86 + stretch, cy + 12, 26, 20))
        pygame.draw.ellipse(surface, _shade(body, -10), (58, cy + 16, 24, 18))
        # Takajalat
        pygame.draw.line(surface, body, (34, cy + 16), (24, cy + 42), 11)
        pygame.draw.line(surface, body, (62, cy + 18), (72, cy + 44), 11)
        # Korvat + kuono
        pygame.draw.polygon(surface, accent, [(96, cy - 34), (102, cy - 50), (112, cy - 33)])
        pygame.draw.polygon(surface, accent, [(112, cy - 33), (122, cy - 48), (128, cy - 30)])
        pygame.draw.polygon(surface, _shade(body, 22), [(118 + stretch, cy - 20), (140 + stretch, cy - 14), (118 + stretch, cy - 6)])
        # Torahampaat
        pygame.draw.polygon(surface, (222, 214, 190), [(120 + stretch, cy - 8), (124 + stretch, cy + 4), (128 + stretch, cy - 7)])
        # Silmä
        eye = self.EYE if state != "dead" else (46, 34, 49)
        pygame.draw.circle(surface, eye, (110 + stretch, cy - 20), 5)
        pygame.draw.circle(surface, _shade(eye, 60), (110 + stretch, cy - 20), 2)

    def _draw_rat_king(self, surface, body, accent, bob, stretch, state, frame):
        cy = 75 + bob
        pygame.draw.arc(surface, accent, (0, cy - 7, 63, 46), 0.1, 2.9, 7)
        pygame.draw.ellipse(surface, body, (27 - stretch, cy - 42, 94 + stretch * 2, 76))
        pygame.draw.circle(surface, _shade(body, 20), (118 + stretch, cy - 28), 29)
        pygame.draw.line(surface, body, (48, cy + 19), (36, 116), 13)
        pygame.draw.line(surface, body, (91, cy + 19), (105, 116), 13)
        crown = (178, 139, 55)
        pygame.draw.polygon(
            surface,
            crown,
            [(94, cy - 52), (99, cy - 82), (108, cy - 60),
             (120, cy - 91), (128, cy - 59), (141, cy - 78),
             (146, cy - 48)],
        )
        pygame.draw.line(surface, _shade(crown, 52), (97, cy - 51), (145, cy - 48), 4)
        pygame.draw.polygon(surface, (88, 76, 69), [(40, cy - 35), (64, cy - 58), (78, cy - 31)])
        pygame.draw.polygon(surface, (88, 76, 69), [(78, cy - 31), (97, cy - 57), (113, cy - 28)])
        phase = int(getattr(self, "phase", 1))
        eye = self.EYE if state != "dead" else (50, 37, 51)
        eye = _shade(eye, min(65, (phase - 1) * 25))
        pygame.draw.circle(surface, eye, (124 + stretch, cy - 33), 6)
        pygame.draw.circle(surface, eye, (140 + stretch, cy - 29), 5)
        if phase >= 2 and state != "dead":
            pygame.draw.arc(surface, (160, 82, 186), (21, cy - 51, 119, 91), 0.2, 3.0, 4)
        if phase >= 3 and state != "dead":
            for x in (47, 70, 91):
                pygame.draw.polygon(surface, (137, 65, 164), [(x - 6, cy - 34), (x, cy - 70), (x + 8, cy - 31)])


class SewerRatSwarm(WarrensMonster):
    SPECIES = "Sewer Rat Swarm"
    THREAT_LEVEL = 4
    SHAPE = "rat_swarm"
    BODY = (91, 78, 67)
    ACCENT = (53, 42, 36)
    EYE = (185, 73, 205)
    VISUAL_SIZE = (76, 55)
    HITBOX_SIZE = (44, 27)
    HP, STR, DEX, DEFENSE = 155, 14, 18, 2
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.48, 43, 47
    STATUS_EFFECT = ("Bleed", 90, 2)
    AI_CLASS = SwarmMonsterAI
    XP_REWARD, BOUNTY_VALUE = 34, 5


class VioletEyedRat(WarrensMonster):
    SPECIES = "Violet-Eyed Rat"
    THREAT_LEVEL = 4
    SHAPE = "violet_rat"
    BODY = (79, 67, 65)
    ACCENT = (44, 35, 39)
    EYE = (191, 72, 228)
    VISUAL_SIZE = (70, 52)
    HITBOX_SIZE = (40, 26)
    HP, STR, DEX, DEFENSE = 176, 16, 18, 3
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.42, 46, 50
    DAMAGE_TYPE = "Poison"
    STATUS_EFFECT = ("Poison", 120, 2)
    AI_CLASS = SkitterMonsterAI
    XP_REWARD, BOUNTY_VALUE = 39, 6


class RatRider(WarrensMonster):
    SPECIES = "Rat Rider"
    THREAT_LEVEL = 5
    SHAPE = "rat_rider"
    BODY = (84, 67, 62)
    ACCENT = (48, 36, 34)
    EYE = (202, 76, 232)
    VISUAL_SIZE = (92, 72)
    HITBOX_SIZE = (54, 32)
    HP, STR, DEX, DEFENSE = 242, 22, 17, 6
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.33, 62, 57
    STATUS_EFFECT = ("Bleed", 120, 3)
    AI_CLASS = PounceMonsterAI
    XP_REWARD, BOUNTY_VALUE = 58, 9


class WasteGnawer(WarrensMonster):
    SPECIES = "Waste Gnawer"
    THREAT_LEVEL = 5
    SHAPE = "waste_gnawer"
    BODY = (79, 71, 68)
    ACCENT = (123, 59, 147)
    EYE = (224, 94, 238)
    VISUAL_SIZE = (96, 76)
    HITBOX_SIZE = (58, 38)
    HP, STR, DEX, INT, DEFENSE = 310, 24, 8, 12, 9
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 0.78, 68, 75
    DAMAGE_TYPE = "Poison"
    STATUS_EFFECT = ("Poison", 165, 4)
    AI_CLASS = ToxicPulseAI
    XP_REWARD, BOUNTY_VALUE = 68, 11

    def release_spores(self, targets: Iterable, manager=None):
        for target in list(targets or ()):
            if getattr(target, "is_dead", False):
                continue
            try:
                target.take_damage(9, "Poison", attacker=self, manager=manager)
                target.apply_status("Poison", 135, 3)
            except Exception:
                continue
        _vfx_text(manager, self, "WASTE FUME", (180, 85, 205))


class HulkRat(WarrensMonster):
    """Valtava lihasrotta: hidas mutta tuhoisa panssarimurskaaja. Kuhisevien
    tunnelien raskas isku - kannattaa maalittaa yhdessä (pelitesti 24)."""
    SPECIES = "Hulk Rat"
    THREAT_LEVEL = 6
    SHAPE = "hulk_rat"
    BODY = (96, 82, 70)
    ACCENT = (54, 42, 36)
    EYE = (216, 92, 236)
    VISUAL_SIZE = (148, 108)
    HITBOX_SIZE = (84, 52)
    HP, STR, DEX, DEFENSE = 620, 30, 8, 14
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 0.72, 78, 88
    STATUS_EFFECT = ("Bleed", 150, 4)
    AI_CLASS = HeavyChargeAI
    XP_REWARD, BOUNTY_VALUE = 120, 20


class WarrensRatKing(WarrensMonster):
    SPECIES = "Rat King"
    THREAT_LEVEL = 6
    SHAPE = "rat_king"
    BODY = (80, 65, 63)
    ACCENT = (45, 34, 37)
    EYE = (211, 76, 239)
    VISUAL_SIZE = (164, 126)
    HITBOX_SIZE = (96, 61)
    HP, STR, DEX, INT, DEFENSE = 1120, 34, 13, 16, 13
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 0.93, 83, 70
    DAMAGE_TYPE = "Poison"
    STATUS_EFFECT = ("Poison", 180, 4)
    AI_CLASS = HeavyChargeAI
    XP_REWARD, BOUNTY_VALUE = 210, 38

    def __init__(self, name, x, y, team_color):
        self.phase = 1
        super().__init__(name, x, y, team_color)
        self.is_boss = True
        self.boss_id = "rat_king"
        self.pending_spawn: List[CodeMonster] = []
        self.pending_waste_wave = 0
        self.pending_screech = False
        self.screech_cooldown = 180
        self.phase_two_triggered = False
        self.phase_three_triggered = False

    def _phase_two(self, manager=None):
        if self.phase_two_triggered or self.is_dead:
            return
        self.phase_two_triggered = True
        self.phase = 2
        self.speed = self.walk_speed = 1.12
        self.attack_speed = 58
        self.pending_spawn = [
            VioletEyedRat(
                f"Royal Violet Rat {index + 1}",
                self.rect.centerx + int((index - 1.5) * 82),
                self.rect.centery + 115,
                self.team_color,
            )
            for index in range(4)
        ]
        self.pending_waste_wave += 1
        _vfx_text(manager, self, "THE WARRENS ANSWER", (211, 133, 232))

    def _phase_three(self, manager=None):
        if self.phase_three_triggered or self.is_dead:
            return
        self.phase_three_triggered = True
        self.phase = 3
        self.speed = self.walk_speed = 1.29
        self.attack_speed = 48
        self.strength += 9
        self.defense += 4
        self.pending_spawn.extend(
            [
                RatRider("Royal Rat Rider One", self.rect.centerx - 150, self.rect.centery + 145, self.team_color),
                RatRider("Royal Rat Rider Two", self.rect.centerx + 150, self.rect.centery + 145, self.team_color),
                WasteGnawer("Crown Waste Gnawer One", self.rect.centerx - 210, self.rect.centery - 90, self.team_color),
                WasteGnawer("Crown Waste Gnawer Two", self.rect.centerx + 210, self.rect.centery - 90, self.team_color),
            ]
        )
        self.pending_waste_wave += 2
        self.pending_screech = True
        _vfx_text(manager, self, "THE GNAWED CROWN BREAKS", (239, 89, 149))

    def release_royal_screech(self, targets: Iterable, manager=None) -> int:
        hit = 0
        radius = 285 if self.phase >= 3 else 225
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
                target.take_damage(11 + self.phase * 4, "Magic", attacker=self, manager=manager)
                target.apply_status("Slow", 95 + self.phase * 25, 0)
                if self.phase >= 3:
                    target.apply_status("Poison", 120, 3)
                hit += 1
            except Exception:
                continue
        _vfx_text(manager, self, "ROYAL SCREECH", (222, 173, 235))
        return hit

    def update(self, obstacles=None, manager=None):
        if not self.is_dead and self.current_hp <= self.max_hp * 0.66:
            self._phase_two(manager)
        if not self.is_dead and self.current_hp <= self.max_hp * 0.33:
            self._phase_three(manager)
        super().update(obstacles, manager)
        if self.is_dead:
            return
        self.screech_cooldown -= 1
        if self.screech_cooldown <= 0:
            self.pending_screech = True
            self.screech_cooldown = 105 if self.phase >= 3 else 150


WARRENS_MONSTER_CLASSES = (
    SewerRatSwarm,
    VioletEyedRat,
    RatRider,
    WasteGnawer,
)

WARRENS_LOOT = {
    "Sewer Rat Swarm": [
        {"item": "Rat Tail", "chance": 0.72, "min": 1, "max": 2},
        {"item": "Rotten Flesh", "chance": 0.46, "min": 1, "max": 2},
    ],
    "Violet-Eyed Rat": [
        {"item": "Rat Tail", "chance": 0.85, "min": 1, "max": 2},
        {"item": "Vortex Residue", "chance": 0.27, "min": 1, "max": 1},
    ],
    "Rat Rider": [
        {"item": "Rat Tail", "chance": 0.78, "min": 1, "max": 2},
        {"item": "Scrap Iron", "chance": 0.63, "min": 1, "max": 2},
    ],
    "Waste Gnawer": [
        {"item": "Rotten Flesh", "chance": 0.72, "min": 1, "max": 3},
        {"item": "Vortex Residue", "chance": 0.52, "min": 1, "max": 2},
    ],
    "Hulk Rat": [
        {"item": "Rotten Flesh", "chance": 0.9, "min": 2, "max": 4},
        {"item": "Scrap Iron", "chance": 0.7, "min": 1, "max": 3},
        {"item": "Rusted Sluice Cog", "chance": 0.35, "min": 1, "max": 1},
    ],
    "Rat King": [
        {"item": "Gnawed Crown", "chance": 1.0, "min": 1, "max": 1},
        {"item": "Vortex Residue", "chance": 1.0, "min": 3, "max": 5},
        {"item": "Rat Tail", "chance": 1.0, "min": 6, "max": 10},
    ],
}
