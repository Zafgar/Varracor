"""Distinct low-level monster behaviours for Muckford and Whisper Marsh.

These controllers deliberately reuse BaseAI targeting and pathfinding. Each
archetype only overrides the decision that makes the creature recognizable:
swarming, lateral skittering, pouncing, burrow ambushes, toxic support, ranged
kiting or a heavy charge.
"""
from __future__ import annotations

import math
import random

from ai.base_ai import BaseAI


def _distance(a, b) -> float:
    return math.hypot(
        b.rect.centerx - a.rect.centerx,
        b.rect.centery - a.rect.centery,
    )


def _valid_enemies(unit, all_units):
    return [
        other
        for other in list(all_units or [])
        if other is not unit
        and not getattr(other, "is_dead", False)
        and not unit.is_ally(other)
    ]


class SwarmMonsterAI(BaseAI):
    """Fast pressure AI that becomes more confident beside its own species."""

    def __init__(self, unit):
        super().__init__(unit)
        self.no_retreat = True

    def execute_ai(self, all_units, obstacles=None, manager=None):
        allies = 0
        for other in list(all_units or []):
            if other is self.unit or getattr(other, "is_dead", False):
                continue
            if getattr(other, "race_name", None) != self.unit.race_name:
                continue
            if _distance(self.unit, other) < 125:
                allies += 1
        if allies:
            self.unit.temp_speed_mult = 1.0 + min(0.24, allies * 0.06)
        super().execute_ai(all_units, obstacles, manager)


class SkitterMonsterAI(BaseAI):
    """Circles at close range and occasionally dashes across the target."""

    def __init__(self, unit):
        super().__init__(unit)
        self.skitter_cooldown = random.randint(70, 130)

    def execute_ai(self, all_units, obstacles=None, manager=None):
        self.skitter_cooldown -= 1
        if not self._is_valid_target(self.current_target):
            self.current_target = self.find_best_target(all_units, manager)
        target = self.current_target
        if target:
            dx = target.rect.centerx - self.unit.rect.centerx
            dy = target.rect.centery - self.unit.rect.centery
            dist = math.hypot(dx, dy)
            if self.skitter_cooldown <= 0 and 45 < dist < 150:
                side = random.choice((-1, 1))
                if self.unit.perform_dash(-dy * side, dx * side):
                    self.skitter_cooldown = random.randint(120, 210)
                    self.state = "skitter"
                    return
        super().execute_ai(all_units, obstacles, manager)


class PounceMonsterAI(BaseAI):
    """Waits for medium range, then leaps into melee with impact damage."""

    def __init__(self, unit):
        super().__init__(unit)
        self.pounce_cooldown = random.randint(80, 160)
        self.no_retreat = True

    def execute_ai(self, all_units, obstacles=None, manager=None):
        self.pounce_cooldown -= 1
        if not self._is_valid_target(self.current_target):
            self.current_target = self.find_best_target(all_units, manager)
        target = self.current_target
        if target:
            dx = target.rect.centerx - self.unit.rect.centerx
            dy = target.rect.centery - self.unit.rect.centery
            dist = math.hypot(dx, dy)
            if self.pounce_cooldown <= 0 and 105 < dist < 315:
                if self.unit.perform_dash(dx, dy):
                    self.unit.dash_damage = max(4, int(self.unit.strength * 0.8))
                    self.pounce_cooldown = random.randint(210, 310)
                    self.state = "pounce"
                    self.unit.animation_state = "attack"
                    self.unit.animation_timer = 22
                    return
        super().execute_ai(all_units, obstacles, manager)


class BurrowAmbushAI(BaseAI):
    """Remains concealed until prey approaches, then lunges with bonus damage."""

    def __init__(self, unit):
        super().__init__(unit)
        self.hidden = True
        self.rehide_timer = 0
        self.no_retreat = True

    def _set_hidden(self, value: bool):
        self.hidden = bool(value)
        self.unit.burrowed = self.hidden
        if getattr(self.unit, "image", None):
            self.unit.image.set_alpha(75 if self.hidden else 255)

    def execute_ai(self, all_units, obstacles=None, manager=None):
        enemies = _valid_enemies(self.unit, all_units)
        nearest = min(enemies, key=lambda enemy: _distance(self.unit, enemy), default=None)
        if self.hidden:
            self.state = "burrowed"
            self.unit.temp_speed_mult = 0.0
            if nearest is None or _distance(self.unit, nearest) > 175:
                return
            self.current_target = nearest
            self._set_hidden(False)
            self.unit.ambush_ready = True
            dx = nearest.rect.centerx - self.unit.rect.centerx
            dy = nearest.rect.centery - self.unit.rect.centery
            if self.unit.perform_dash(dx, dy):
                self.unit.dash_damage = max(5, int(self.unit.strength * 0.6))
            self.rehide_timer = 420
            return

        self.rehide_timer -= 1
        if self.rehide_timer <= 0 and nearest and _distance(self.unit, nearest) > 360:
            self._set_hidden(True)
            return
        super().execute_ai(all_units, obstacles, manager)


class ToxicPulseAI(BaseAI):
    """Approaches the fight and periodically poisons nearby enemies."""

    def __init__(self, unit):
        super().__init__(unit)
        self.pulse_cooldown = random.randint(120, 230)

    def execute_ai(self, all_units, obstacles=None, manager=None):
        self.pulse_cooldown -= 1
        enemies = _valid_enemies(self.unit, all_units)
        nearby = [enemy for enemy in enemies if _distance(self.unit, enemy) <= 115]
        if nearby and self.pulse_cooldown <= 0:
            if hasattr(self.unit, "release_spores"):
                self.unit.release_spores(nearby, manager)
            self.pulse_cooldown = random.randint(300, 430)
            self.state = "spore_burst"
            return
        super().execute_ai(all_units, obstacles, manager)


class RangedKiteMonsterAI(BaseAI):
    """Uses a direct ranged attack and retreats when prey reaches melee range."""

    def __init__(self, unit):
        super().__init__(unit)
        self.kite_cooldown = 0

    def execute_ai(self, all_units, obstacles=None, manager=None):
        if self.kite_cooldown > 0:
            self.kite_cooldown -= 1
        if not self._is_valid_target(self.current_target):
            self.current_target = self.find_best_target(all_units, manager)
        target = self.current_target
        if target:
            dx = target.rect.centerx - self.unit.rect.centerx
            dy = target.rect.centery - self.unit.rect.centery
            dist = math.hypot(dx, dy)
            if dist < 82 and self.kite_cooldown <= 0:
                if self.unit.perform_dash(-dx, -dy):
                    self.kite_cooldown = 180
                    self.state = "kite"
                    return
        super().execute_ai(all_units, obstacles, manager)


class HeavyChargeAI(BaseAI):
    """Slow tank that commits to a damaging straight-line charge."""

    def __init__(self, unit):
        super().__init__(unit)
        self.charge_cooldown = random.randint(120, 220)
        self.no_retreat = True

    def execute_ai(self, all_units, obstacles=None, manager=None):
        self.charge_cooldown -= 1
        if not self._is_valid_target(self.current_target):
            self.current_target = self.find_best_target(all_units, manager)
        target = self.current_target
        if target:
            dx = target.rect.centerx - self.unit.rect.centerx
            dy = target.rect.centery - self.unit.rect.centery
            dist = math.hypot(dx, dy)
            if self.charge_cooldown <= 0 and 130 < dist < 390:
                if self.unit.perform_dash(dx, dy):
                    self.unit.dash_timer = 22
                    self.unit.dash_speed_mult = 4.0
                    self.unit.dash_damage = max(10, int(self.unit.strength * 1.15))
                    self.charge_cooldown = random.randint(330, 460)
                    self.state = "charge"
                    self.unit.animation_state = "attack"
                    self.unit.animation_timer = 28
                    return
        super().execute_ai(all_units, obstacles, manager)
