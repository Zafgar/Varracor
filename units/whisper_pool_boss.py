"""Code-rendered Whisper Pool boss for the Tier 0 marsh climax."""
from __future__ import annotations

import math

import pygame

from ai.tier0_monster_ai import HeavyChargeAI
from units.tier0_monsters import CodeMonster, MOVE_SCALE, MireLurkerSpawn, _shade, _vfx_text


class WhisperPoolMaw(CodeMonster):
    """Ancient mire predator disturbed by the Survey Post and fishing lines.

    The placeholder silhouette is generated entirely with pygame primitives.
    At half health the Maw enters a violent second phase and calls three spawn
    from the pool edge. The menu owns adding those spawn to its monster group;
    this unit exposes them through ``pending_spawn`` to keep combat integration
    explicit and testable.
    """

    SPECIES = "Whisper Pool Maw"
    THREAT_LEVEL = 5
    SHAPE = "pool_maw"
    BODY = (37, 82, 73)
    ACCENT = (91, 145, 105)
    EYE = (176, 238, 204)
    VISUAL_SIZE = (118, 88)
    HITBOX_SIZE = (72, 43)
    HP, STR, DEX, INT, DEFENSE = 520, 24, 7, 8, 7
    MOVE_SPEED, ATTACK_RANGE, ATTACK_SPEED = 0.72, 68, 78
    STATUS_EFFECT = ("Slow", 140, 0)
    AI_CLASS = HeavyChargeAI
    XP_REWARD, BOUNTY_VALUE = 95, 16

    def __init__(self, name, x, y, team_color):
        # CodeMonster generates animation frames inside super().__init__, so the
        # phase must already exist when the custom frame drawer is called.
        self.phase = 1
        super().__init__(name, x, y, team_color)
        self.is_boss = True
        self.pending_spawn = []
        self.pool_ripple_timer = 0
        self.boss_id = "whisper_pool_maw"

    def _draw_pool_maw(self, surface, body, accent, bob, stretch, state, frame):
        cy = 49 + bob
        pygame.draw.polygon(
            surface,
            _shade(body, -18),
            [(34, cy + 4), (7, cy + 19), (15, cy - 4), (4, cy - 22), (42, cy - 10)],
        )
        pygame.draw.ellipse(surface, body, (26 - stretch, cy - 25, 66 + stretch * 2, 47))
        pygame.draw.ellipse(surface, accent, (61, cy - 28, 49 + stretch, 39))

        for index, x in enumerate((37, 52, 67, 82)):
            height = 14 + index % 2 * 6
            pygame.draw.polygon(
                surface,
                _shade(accent, 18),
                [(x, cy - 18), (x + 7, cy - 18 - height), (x + 13, cy - 15)],
            )

        kick = 7 if state == "attack" and frame else 0
        pygame.draw.line(surface, body, (53, cy + 10), (39 - kick, cy + 32), 10)
        pygame.draw.line(surface, body, (84, cy + 10), (96 + kick, cy + 31), 10)
        pygame.draw.arc(surface, accent, (25 - kick, cy + 23, 24, 18), 0.2, math.pi * 1.25, 4)
        pygame.draw.arc(surface, accent, (91 + kick, cy + 22, 22, 18), math.pi * 0.1, math.pi * 1.2, 4)

        mouth = pygame.Rect(75, cy - 5, 34 + stretch, 22)
        pygame.draw.ellipse(surface, (24, 38, 35), mouth)
        pygame.draw.arc(surface, (157, 214, 181), mouth, 0, math.pi, 3)
        for x, y in ((72, cy - 17), (82, cy - 20), (94, cy - 18), (103, cy - 14)):
            pygame.draw.circle(surface, (28, 45, 40), (x, y), 5)
            pygame.draw.circle(surface, self.EYE if state != "dead" else (45, 42, 38), (x, y), 2)

        if getattr(self, "phase", 1) >= 2 and state != "dead":
            pygame.draw.arc(surface, (162, 236, 221), (31, cy - 30, 75, 59), 0.2, 2.9, 2)

    def _enter_second_phase(self, manager=None):
        if self.phase >= 2 or self.is_dead:
            return
        self.phase = 2
        self.walk_speed = 0.94 * MOVE_SCALE
        self.speed = self.walk_speed
        self.attack_speed = 61
        self.strength += 5
        self.defense += 2
        self.pending_spawn = [
            MireLurkerSpawn(
                f"Pool Spawn {index + 1}",
                self.rect.centerx + (index - 1) * 70,
                self.rect.centery + 95,
                self.team_color,
            )
            for index in range(3)
        ]
        _vfx_text(manager, self, "THE POOL ANSWERS", (150, 235, 221))

    def update(self, obstacles=None, manager=None):
        if not self.is_dead and self.current_hp <= self.max_hp * 0.5:
            self._enter_second_phase(manager)
        super().update(obstacles, manager)

        self.pool_ripple_timer -= 1
        if self.pool_ripple_timer <= 0 and manager is not None:
            arena = getattr(manager, "current_arena", None)
            pool = getattr(arena, "whisper_pool", None)
            if pool is not None:
                pool.add_ripple(self.rect.center)
            self.pool_ripple_timer = 26 if self.phase >= 2 else 48
