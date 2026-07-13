"""Code-rendered level 1-5 monsters for Muckford and Whisper Marsh.

The art in this module is deliberately generated with pygame primitives. Each
species has a readable silhouette and several lightweight animation frames, so
it is immediately playable while final painted assets are produced later.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Sequence, Tuple, Type

import pygame

from ai.tier0_monster_ai import (
    BurrowAmbushAI,
    HeavyChargeAI,
    PounceMonsterAI,
    RangedKiteMonsterAI,
    SkitterMonsterAI,
    SwarmMonsterAI,
    ToxicPulseAI,
)
from gladiator import Gladiator


Color = Tuple[int, int, int]


def _clamp_channel(value: float) -> int:
    return max(0, min(255, int(value)))


def _shade(color: Color, amount: int) -> Color:
    return tuple(_clamp_channel(channel + amount) for channel in color)


def _vfx_text(manager, unit, text: str, color=(180, 220, 180)) -> None:
    if manager is None or not hasattr(manager, "vfx"):
        return
    try:
        manager.vfx.show_damage(
            unit.rect.centerx,
            unit.rect.top - 24,
            text,
            color=color,
        )
    except Exception:
        pass


class CodeMonster(Gladiator):
    """Shared stat, attack and generated-sprite implementation."""

    SPECIES = "Code Monster"
    THREAT_LEVEL = 1
    SHAPE = "mite"
    BODY: Color = (100, 100, 100)
    ACCENT: Color = (170, 170, 170)
    EYE: Color = (240, 220, 120)
    VISUAL_SIZE = (62, 48)
    HITBOX_SIZE = (34, 24)
    HP = 50
    STR = 6
    DEX = 8
    INT = 1
    DEFENSE = 0
    MOVE_SPEED = 1.0
    ATTACK_RANGE = 38
    ATTACK_SPEED = 58
    DAMAGE_TYPE = "Physical"
    STATUS_EFFECT = None  # (name, duration, damage)
    STAMINA_DRAIN = 0
    LIFESTEAL = 0.0
    AI_CLASS: Type = SwarmMonsterAI
    XP_REWARD = 8
    BOUNTY_VALUE = 2

    def load_assets(self):
        # Prevent Gladiator from filling a fallback rectangle during super init.
        return True

    def __init__(self, name, x, y, team_color):
        super().__init__(name, self.SPECIES, x, y, team_color)
        center = self.rect.center
        self.level = int(self.THREAT_LEVEL)
        self.threat_level = int(self.THREAT_LEVEL)
        self.xp_reward = int(self.XP_REWARD)
        self.bounty_value = int(self.BOUNTY_VALUE)
        self.show_main_hand = False
        self.show_off_hand = False
        self.base_attributes.update(
            {
                "str": int(self.STR),
                "dex": int(self.DEX),
                "int": int(self.INT),
                "hp": int(self.HP),
                "max_hp": int(self.HP),
                "mana": 0,
                "def_flat": int(self.DEFENSE),
            }
        )
        self.calculate_final_stats()
        self.max_hp = int(self.HP)
        self.current_hp = self.max_hp
        self.max_mana = 0
        self.current_mana = 0
        self.walk_speed = float(self.MOVE_SPEED)
        self.speed = self.walk_speed
        self.attack_range = int(self.ATTACK_RANGE)
        self.attack_speed = int(self.ATTACK_SPEED)
        self.weapon_type = "ranged" if self.attack_range >= 120 else "melee"
        self.mud_immune = True
        self.rect = pygame.Rect(0, 0, *self.HITBOX_SIZE)
        self.rect.center = center
        self._frame_counter = random.randint(0, 29)
        self._generated_frames = self._build_animation_frames()
        self.sprites = {
            state: frames[0] for state, frames in self._generated_frames.items()
        }
        self.image = self._generated_frames["idle"][0]
        self.use_sprites = True
        self.ai_controller = self.AI_CLASS(self)
        self.ambush_ready = False
        self.burrowed = False
        self.jump_height = 0

    # ------------------------------------------------------------------
    # Generated placeholder graphics
    # ------------------------------------------------------------------
    def _build_animation_frames(self) -> Dict[str, List[pygame.Surface]]:
        return {
            "idle": [self._draw_frame("idle", 0), self._draw_frame("idle", 1)],
            "run": [self._draw_frame("run", 0), self._draw_frame("run", 1)],
            "attack": [self._draw_frame("attack", 0), self._draw_frame("attack", 1)],
            "hurt": [self._draw_frame("hurt", 0)],
            "dead": [self._draw_frame("dead", 0)],
        }

    def _draw_frame(self, state: str, frame: int) -> pygame.Surface:
        width, height = self.VISUAL_SIZE
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        bob = 0
        stretch = 0
        if state == "idle":
            bob = -1 if frame else 1
        elif state == "run":
            bob = -2 if frame else 2
        elif state == "attack":
            stretch = 5 if frame else 1
            bob = -2
        elif state == "hurt":
            bob = 2
        body = self.BODY if state != "hurt" else _shade(self.BODY, 65)
        accent = self.ACCENT if state != "hurt" else _shade(self.ACCENT, 55)

        drawer = getattr(self, f"_draw_{self.SHAPE}", self._draw_mite)
        drawer(surface, body, accent, bob, stretch, state, frame)
        if state == "dead":
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((35, 28, 25, 125))
            surface.blit(overlay, (0, 0))
            pygame.draw.line(
                surface,
                (30, 25, 22),
                (width // 2 - 5, height // 2 - 3),
                (width // 2 + 5, height // 2 + 3),
                2,
            )
        return surface

    def _eyes(self, surface, points: Sequence[Tuple[int, int]], state: str):
        color = (40, 25, 20) if state == "dead" else self.EYE
        for point in points:
            pygame.draw.circle(surface, color, point, 2)

    def _draw_mite(self, s, body, accent, bob, stretch, state, frame):
        cy = 27 + bob
        for index, dy in enumerate((-9, -3, 4, 10)):
            pygame.draw.line(s, accent, (24, cy + dy), (7, cy + dy + (-5 if index % 2 else 5)), 3)
            pygame.draw.line(s, accent, (38, cy + dy), (55, cy + dy + (5 if index % 2 else -5)), 3)
        pygame.draw.ellipse(s, body, (15 - stretch // 2, cy - 14, 34 + stretch, 27))
        pygame.draw.ellipse(s, accent, (21, cy - 11, 22 + stretch, 18), 2)
        self._eyes(s, ((21, cy - 4), (26, cy - 5)), state)

    def _draw_skitter(self, s, body, accent, bob, stretch, state, frame):
        cy = 29 + bob
        for side in (-1, 1):
            base_x = 18 if side < 0 else 44
            for index in range(3):
                y = cy - 8 + index * 8
                pygame.draw.line(s, accent, (base_x, y), (base_x + side * 15, y + (index - 1) * 4), 3)
            claw_x = 5 if side < 0 else 57
            pygame.draw.circle(s, body, (claw_x, cy - 9 - stretch), 7, 3)
        pygame.draw.ellipse(s, body, (16, cy - 13, 30 + stretch, 24))
        pygame.draw.arc(s, _shade(body, 35), (19, cy - 10, 24, 18), 0, math.pi, 2)
        self._eyes(s, ((24, cy - 7), (37, cy - 7)), state)

    def _draw_tick(self, s, body, accent, bob, stretch, state, frame):
        cy = 28 + bob
        for index in range(4):
            y = cy - 10 + index * 7
            pygame.draw.line(s, accent, (23, y), (7, y + (index % 2) * 5 - 2), 3)
            pygame.draw.line(s, accent, (39, y), (55, y - (index % 2) * 5 + 2), 3)
        pygame.draw.ellipse(s, body, (17 - stretch, cy - 16, 34 + stretch * 2, 31))
        pygame.draw.circle(s, accent, (31, cy - 2), 8)
        self._eyes(s, ((25, cy - 10), (31, cy - 11)), state)

    def _draw_toad(self, s, body, accent, bob, stretch, state, frame):
        cy = 31 + bob
        pygame.draw.ellipse(s, _shade(body, -20), (8, cy + 4, 18, 11))
        pygame.draw.ellipse(s, _shade(body, -20), (39, cy + 4, 18, 11))
        pygame.draw.ellipse(s, body, (12 - stretch, cy - 16, 42 + stretch * 2, 29))
        pygame.draw.circle(s, accent, (22, cy - 14), 8)
        pygame.draw.circle(s, accent, (44, cy - 14), 8)
        pygame.draw.circle(s, _shade(body, 45), (31, cy - 5), 4)
        pygame.draw.circle(s, _shade(body, 45), (42, cy + 1), 3)
        self._eyes(s, ((22, cy - 15), (44, cy - 15)), state)

    def _draw_lurker(self, s, body, accent, bob, stretch, state, frame):
        cy = 29 + bob
        pygame.draw.polygon(s, accent, [(12, cy), (2, cy - 8), (4, cy + 6), (19, cy + 4)])
        pygame.draw.ellipse(s, body, (14, cy - 14, 37 + stretch, 26))
        pygame.draw.ellipse(s, accent, (35, cy - 17, 23 + stretch, 20))
        for x in (20, 32, 43):
            pygame.draw.polygon(s, _shade(body, 30), [(x, cy - 12), (x + 4, cy - 21), (x + 8, cy - 11)])
        pygame.draw.line(s, body, (19, cy + 7), (10, cy + 16), 5)
        pygame.draw.line(s, body, (45, cy + 7), (54, cy + 16), 5)
        self._eyes(s, ((48, cy - 10), (54, cy - 9)), state)

    def _draw_mudling(self, s, body, accent, bob, stretch, state, frame):
        cy = 28 + bob
        pygame.draw.line(s, accent, (28, cy - 14), (23, 5), 3)
        pygame.draw.line(s, accent, (34, cy - 14), (39, 7), 3)
        pygame.draw.circle(s, body, (31, cy - 10), 11 + stretch // 2)
        pygame.draw.ellipse(s, body, (17 - stretch, cy - 2, 29 + stretch * 2, 27))
        pygame.draw.line(s, body, (20, cy + 8), (7, cy + 18), 6)
        pygame.draw.line(s, body, (43, cy + 8), (57, cy + 17), 6)
        pygame.draw.line(s, body, (25, cy + 20), (20, 47), 7)
        pygame.draw.line(s, body, (38, cy + 20), (44, 47), 7)
        self._eyes(s, ((27, cy - 12), (35, cy - 12)), state)

    def _draw_stalker(self, s, body, accent, bob, stretch, state, frame):
        cy = 29 + bob
        pygame.draw.polygon(s, accent, [(17, cy), (2, cy + 9), (7, cy - 2), (19, cy - 6)])
        pygame.draw.ellipse(s, body, (14, cy - 12, 36 + stretch, 22))
        pygame.draw.polygon(s, body, [(43, cy - 10), (58 + stretch, cy - 15), (55 + stretch, cy + 4), (42, cy + 3)])
        for x in (21, 43):
            kick = 4 if frame else -2
            pygame.draw.line(s, body, (x, cy + 6), (x - 5 + kick, cy + 18), 5)
        self._eyes(s, ((51 + stretch, cy - 10), (56 + stretch, cy - 9)), state)

    def _draw_rotcap(self, s, body, accent, bob, stretch, state, frame):
        cy = 29 + bob
        pygame.draw.ellipse(s, body, (20, cy - 7, 25 + stretch, 31))
        pygame.draw.line(s, body, (24, cy + 12), (15, 48), 7)
        pygame.draw.line(s, body, (42, cy + 12), (50, 48), 7)
        pygame.draw.line(s, body, (23, cy + 1), (8, cy + 13), 6)
        pygame.draw.line(s, body, (44, cy + 1), (58, cy + 12), 6)
        pygame.draw.ellipse(s, accent, (8 - stretch, 5 + bob, 49 + stretch * 2, 23))
        for point in ((18, 12 + bob), (31, 8 + bob), (45, 14 + bob)):
            pygame.draw.circle(s, _shade(accent, 55), point, 3)
        self._eyes(s, ((29, cy), (37, cy)), state)

    def _draw_marshback(self, s, body, accent, bob, stretch, state, frame):
        cy = 31 + bob
        pygame.draw.ellipse(s, body, (8 - stretch, cy - 13, 49 + stretch * 2, 27))
        pygame.draw.ellipse(s, accent, (13, cy - 17, 38, 24))
        pygame.draw.arc(s, _shade(accent, 45), (17, cy - 13, 30, 18), 0, math.tau, 3)
        pygame.draw.polygon(s, body, [(51, cy - 7), (62, cy - 4), (59, cy + 8), (49, cy + 7)])
        for x in (16, 44):
            pygame.draw.line(s, body, (x, cy + 8), (x - 3, cy + 18), 7)
        self._eyes(s, ((57, cy - 3),), state)

    def _draw_moth(self, s, body, accent, bob, stretch, state, frame):
        cy = 25 + bob
        wing = 4 if frame else -3
        pygame.draw.polygon(s, accent, [(29, cy), (8, cy - 15 - wing), (4, cy + 12), (26, cy + 8)])
        pygame.draw.polygon(s, accent, [(35, cy), (56, cy - 15 - wing), (60, cy + 12), (38, cy + 8)])
        pygame.draw.ellipse(s, body, (25, cy - 13, 14 + stretch, 31))
        pygame.draw.circle(s, body, (32, cy - 12), 8)
        pygame.draw.line(s, body, (29, cy - 17), (22, cy - 27), 2)
        pygame.draw.line(s, body, (35, cy - 17), (42, cy - 27), 2)
        for point in ((14, cy - 5), (50, cy - 5)):
            pygame.draw.circle(s, _shade(accent, 50), point, 4)
        self._eyes(s, ((29, cy - 13), (35, cy - 13)), state)

    # ------------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------------
    def perform_attack(
        self,
        target=None,
        manager=None,
        damage_mult=1.0,
        range_override=None,
        target_pos=None,
    ):
        if self.is_dead or self.stun_timer > 0 or self.attack_cooldown > 0:
            return False
        if target is None or getattr(target, "is_dead", False):
            return False
        attack_range = int(range_override or self.attack_range)
        distance = math.hypot(
            target.rect.centerx - self.rect.centerx,
            target.rect.centery - self.rect.centery,
        )
        if distance > attack_range:
            return False
        if (
            self.weapon_type == "ranged"
            and manager is not None
            and getattr(manager, "current_arena", None) is not None
            and not self.has_line_of_sight(
                target,
                getattr(manager.current_arena, "obstacles", []),
            )
        ):
            return False

        self.facing_right = target.rect.centerx >= self.rect.centerx
        self.attack_vector = (
            target.rect.centerx - self.rect.centerx,
            target.rect.centery - self.rect.centery,
        )
        self.attack_cooldown = self.attack_speed
        self.animation_state = "attack"
        self.animation_timer = 18
        self.current_stamina = max(0, self.current_stamina - 5)
        multiplier = float(damage_mult)
        if self.ambush_ready:
            multiplier *= 1.75
            self.ambush_ready = False
            _vfx_text(manager, self, "AMBUSH", (220, 235, 150))
        damage = max(1, int(self.strength * multiplier))
        dealt = target.take_damage(
            damage,
            self.DAMAGE_TYPE,
            attacker=self,
            manager=manager,
        )
        self.stats["damage"] += int(dealt or 0)
        # HUOM: tappo kirjataan take_damagessa (tuplakirjauksen esto)
        if self.STATUS_EFFECT and not getattr(target, "is_dead", False):
            effect_name, duration, effect_damage = self.STATUS_EFFECT
            target.apply_status(effect_name, duration, effect_damage)
            _vfx_text(manager, target, effect_name.upper(), (145, 210, 125))
        if self.STAMINA_DRAIN and hasattr(target, "current_stamina"):
            target.current_stamina = max(
                0,
                target.current_stamina - int(self.STAMINA_DRAIN),
            )
            _vfx_text(manager, target, "DRAIN", (155, 120, 190))
        if self.LIFESTEAL and dealt:
            self.current_hp = min(
                self.max_hp,
                self.current_hp + max(1, int(dealt * self.LIFESTEAL)),
            )
        return True

    def release_spores(self, targets, manager=None):
        self.animation_state = "attack"
        self.animation_timer = 30
        for target in targets:
            if getattr(target, "is_dead", False):
                continue
            target.apply_status("Poison", 180, max(1, self.level))
            target.apply_status("Slow", 90, 0)
            target.take_damage(
                max(2, self.strength // 3),
                "Poison",
                attacker=self,
                manager=manager,
            )
        _vfx_text(manager, self, "SPORE BURST", (165, 210, 110))

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        dealt = super().take_damage(amount, damage_type, attacker, manager)
        if dealt > 0 and not self.is_dead:
            self.animation_state = "hurt"
            self.animation_timer = 14
        if self.is_dead:
            self.image = self._generated_frames["dead"][0]
        return dealt

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        self._frame_counter += 1
        if self.is_dead:
            state = "dead"
        elif self.animation_state in self._generated_frames:
            state = self.animation_state
        elif self.is_dashing:
            state = "run"
        else:
            state = "idle"
        frames = self._generated_frames.get(state, self._generated_frames["idle"])
        index = (self._frame_counter // 10) % len(frames)
        self.image = frames[index]
        if self.burrowed:
            self.image.set_alpha(75)
        else:
            self.image.set_alpha(255)
        if self.is_dashing and self.SHAPE in ("lurker", "toad", "stalker"):
            total = max(1, 15)
            progress = (total - min(total, self.dash_timer)) / total
            self.jump_height = 42 * 4 * progress * (1.0 - progress)
        else:
            self.jump_height = 0


class MudMite(CodeMonster):
    SPECIES = "Mud Mite"
    THREAT_LEVEL = 1
    SHAPE = "mite"
    BODY = (91, 72, 52)
    ACCENT = (133, 107, 70)
    EYE = (236, 188, 76)
    VISUAL_SIZE = (62, 48)
    HITBOX_SIZE = (29, 18)
    HP, STR, DEX, DEFENSE = 34, 5, 12, 0
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.35, 34, 42
    AI_CLASS = SwarmMonsterAI
    XP_REWARD, BOUNTY_VALUE = 5, 1


class ReedSkitter(CodeMonster):
    SPECIES = "Reed Skitter"
    THREAT_LEVEL = 1
    SHAPE = "skitter"
    BODY = (76, 112, 76)
    ACCENT = (150, 128, 73)
    EYE = (228, 233, 150)
    HP, STR, DEX, DEFENSE = 44, 6, 11, 1
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.15, 40, 50
    STATUS_EFFECT = ("Slow", 45, 0)
    AI_CLASS = SkitterMonsterAI
    XP_REWARD, BOUNTY_VALUE = 6, 1


class BogTick(CodeMonster):
    SPECIES = "Bog Tick"
    THREAT_LEVEL = 2
    SHAPE = "tick"
    BODY = (82, 49, 69)
    ACCENT = (123, 77, 103)
    EYE = (239, 139, 93)
    HP, STR, DEX, DEFENSE = 62, 8, 10, 1
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.05, 36, 54
    STAMINA_DRAIN = 10
    LIFESTEAL = 0.25
    AI_CLASS = BurrowAmbushAI
    XP_REWARD, BOUNTY_VALUE = 10, 2


class SporeToad(CodeMonster):
    SPECIES = "Spore Toad"
    THREAT_LEVEL = 2
    SHAPE = "toad"
    BODY = (63, 111, 67)
    ACCENT = (138, 92, 151)
    EYE = (226, 224, 124)
    VISUAL_SIZE = (68, 56)
    HITBOX_SIZE = (42, 28)
    HP, STR, DEX, INT, DEFENSE = 76, 7, 7, 4, 1
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 0.82, 52, 68
    STATUS_EFFECT = ("Poison", 120, 2)
    AI_CLASS = ToxicPulseAI
    XP_REWARD, BOUNTY_VALUE = 12, 2


class MireLurkerSpawn(CodeMonster):
    SPECIES = "Mire-Lurker Spawn"
    THREAT_LEVEL = 3
    SHAPE = "lurker"
    BODY = (43, 101, 78)
    ACCENT = (102, 157, 96)
    EYE = (195, 244, 137)
    VISUAL_SIZE = (70, 55)
    HITBOX_SIZE = (44, 27)
    HP, STR, DEX, DEFENSE = 94, 11, 12, 2
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.18, 47, 54
    STATUS_EFFECT = ("Slow", 80, 0)
    AI_CLASS = PounceMonsterAI
    XP_REWARD, BOUNTY_VALUE = 17, 3


class DrownedMudling(CodeMonster):
    SPECIES = "Drowned Mudling"
    THREAT_LEVEL = 3
    SHAPE = "mudling"
    BODY = (73, 83, 70)
    ACCENT = (90, 126, 88)
    EYE = (148, 211, 200)
    VISUAL_SIZE = (66, 58)
    HITBOX_SIZE = (34, 27)
    HP, STR, DEX, DEFENSE = 112, 12, 6, 3
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 0.76, 45, 72
    STATUS_EFFECT = ("Slow", 105, 0)
    AI_CLASS = SwarmMonsterAI
    XP_REWARD, BOUNTY_VALUE = 18, 3


class FenStalker(CodeMonster):
    SPECIES = "Fen Stalker"
    THREAT_LEVEL = 4
    SHAPE = "stalker"
    BODY = (47, 83, 63)
    ACCENT = (94, 129, 79)
    EYE = (222, 239, 112)
    VISUAL_SIZE = (68, 52)
    HITBOX_SIZE = (43, 24)
    HP, STR, DEX, DEFENSE = 132, 15, 15, 3
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.42, 50, 45
    STATUS_EFFECT = ("Poison", 105, 2)
    AI_CLASS = BurrowAmbushAI
    XP_REWARD, BOUNTY_VALUE = 25, 4


class RotcapShambler(CodeMonster):
    SPECIES = "Rotcap Shambler"
    THREAT_LEVEL = 4
    SHAPE = "rotcap"
    BODY = (84, 94, 61)
    ACCENT = (151, 68, 82)
    EYE = (225, 213, 131)
    VISUAL_SIZE = (68, 62)
    HITBOX_SIZE = (38, 30)
    HP, STR, DEX, INT, DEFENSE = 158, 13, 5, 8, 4
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 0.67, 52, 78
    STATUS_EFFECT = ("Poison", 150, 3)
    AI_CLASS = ToxicPulseAI
    XP_REWARD, BOUNTY_VALUE = 28, 4


class MarshbackBrute(CodeMonster):
    SPECIES = "Marshback Brute"
    THREAT_LEVEL = 5
    SHAPE = "marshback"
    BODY = (55, 84, 64)
    ACCENT = (107, 118, 76)
    EYE = (236, 172, 82)
    VISUAL_SIZE = (74, 56)
    HITBOX_SIZE = (54, 31)
    HP, STR, DEX, DEFENSE = 235, 20, 5, 6
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 0.72, 58, 82
    STATUS_EFFECT = ("Slow", 120, 0)
    AI_CLASS = HeavyChargeAI
    XP_REWARD, BOUNTY_VALUE = 42, 7


class WhisperMoth(CodeMonster):
    SPECIES = "Whisper Moth"
    THREAT_LEVEL = 5
    SHAPE = "moth"
    BODY = (78, 74, 105)
    ACCENT = (134, 119, 163)
    EYE = (177, 239, 230)
    VISUAL_SIZE = (66, 58)
    HITBOX_SIZE = (34, 22)
    HP, STR, DEX, INT, DEFENSE = 168, 15, 14, 12, 2
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 1.22, 190, 72
    DAMAGE_TYPE = "Poison"
    STATUS_EFFECT = ("Poison", 180, 4)
    AI_CLASS = RangedKiteMonsterAI
    XP_REWARD, BOUNTY_VALUE = 38, 6


TIER0_MONSTER_CLASSES = (
    MudMite,
    ReedSkitter,
    BogTick,
    SporeToad,
    MireLurkerSpawn,
    DrownedMudling,
    FenStalker,
    RotcapShambler,
    MarshbackBrute,
    WhisperMoth,
)

TIER0_MONSTER_BY_SPECIES = {
    monster_class.SPECIES: monster_class for monster_class in TIER0_MONSTER_CLASSES
}
