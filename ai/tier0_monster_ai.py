"""Distinct low-level monster behaviours for Muckford and Whisper Marsh.

Controllers reuse BaseAI targeting/pathfinding, but enforce a local aggro radius
so deep-marsh level 4-5 creatures do not cross the whole map to attack a new
player standing at Muckford's entrance.
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


class LocalMonsterAI(BaseAI):
    """BaseAI wrapper with aggro, leash and spawn-home awareness."""

    def __init__(self, unit):
        super().__init__(unit)
        self.home = tuple(unit.rect.center)
        self.aggro_radius = float(getattr(unit, "aggro_radius", 430))
        self.leash_radius = float(getattr(unit, "leash_radius", 680))

    def _distance_from_home(self) -> float:
        return math.hypot(
            self.unit.rect.centerx - self.home[0],
            self.unit.rect.centery - self.home[1],
        )

    def _local_units(self, all_units):
        units = [self.unit]
        for other in list(all_units or []):
            if other is self.unit or getattr(other, "is_dead", False):
                continue
            distance = _distance(self.unit, other)
            if self.current_target is other:
                if distance <= self.leash_radius:
                    units.append(other)
            elif distance <= self.aggro_radius:
                units.append(other)
        return units

    def _prepare(self, all_units, obstacles=None, manager=None):
        if self._distance_from_home() > self.leash_radius:
            self.current_target = None
            self.state = "return"
            self.navigate_to(self.home, obstacles, all_units, manager)
            return None
        local = self._local_units(all_units)
        enemies = _valid_enemies(self.unit, local)
        if not enemies and self.current_target is None:
            self.state = "idle"
            return None
        return local

    def execute_ai(self, all_units, obstacles=None, manager=None):
        local = self._prepare(all_units, obstacles, manager)
        if local is None:
            return
        super().execute_ai(local, obstacles, manager)


class SwarmMonsterAI(LocalMonsterAI):
    """Fast pressure AI that becomes stronger beside its own species."""

    def __init__(self, unit):
        super().__init__(unit)
        self.no_retreat = True

    def execute_ai(self, all_units, obstacles=None, manager=None):
        local = self._prepare(all_units, obstacles, manager)
        if local is None:
            return
        allies = sum(
            1
            for other in local
            if other is not self.unit
            and getattr(other, "race_name", None) == self.unit.race_name
            and _distance(self.unit, other) < 125
        )
        if allies:
            self.unit.temp_speed_mult = 1.0 + min(0.24, allies * 0.06)
        BaseAI.execute_ai(self, local, obstacles, manager)


class SkitterMonsterAI(LocalMonsterAI):
    """Circles at close range and dashes sideways across the target."""

    def __init__(self, unit):
        super().__init__(unit)
        self.skitter_cooldown = random.randint(70, 130)

    def execute_ai(self, all_units, obstacles=None, manager=None):
        local = self._prepare(all_units, obstacles, manager)
        if local is None:
            return
        self.skitter_cooldown -= 1
        if not self._is_valid_target(self.current_target):
            self.current_target = self.find_best_target(local, manager)
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
        BaseAI.execute_ai(self, local, obstacles, manager)


class PounceMonsterAI(LocalMonsterAI):
    """Waits for medium range, then leaps into melee with impact damage."""

    def __init__(self, unit):
        super().__init__(unit)
        self.pounce_cooldown = random.randint(80, 160)
        self.no_retreat = True

    def execute_ai(self, all_units, obstacles=None, manager=None):
        local = self._prepare(all_units, obstacles, manager)
        if local is None:
            return
        self.pounce_cooldown -= 1
        if not self._is_valid_target(self.current_target):
            self.current_target = self.find_best_target(local, manager)
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
        BaseAI.execute_ai(self, local, obstacles, manager)


class BurrowAmbushAI(LocalMonsterAI):
    """Stays concealed until prey approaches, then lunges for bonus damage."""

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
        local = self._prepare(all_units, obstacles, manager)
        if local is None:
            return
        enemies = _valid_enemies(self.unit, local)
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
        BaseAI.execute_ai(self, local, obstacles, manager)


class ToxicPulseAI(LocalMonsterAI):
    """Approaches the fight and periodically poisons nearby enemies."""

    def __init__(self, unit):
        super().__init__(unit)
        self.pulse_cooldown = random.randint(120, 230)

    def execute_ai(self, all_units, obstacles=None, manager=None):
        local = self._prepare(all_units, obstacles, manager)
        if local is None:
            return
        self.pulse_cooldown -= 1
        enemies = _valid_enemies(self.unit, local)
        nearby = [enemy for enemy in enemies if _distance(self.unit, enemy) <= 115]
        if nearby and self.pulse_cooldown <= 0:
            self.unit.release_spores(nearby, manager)
            self.pulse_cooldown = random.randint(300, 430)
            self.state = "spore_burst"
            return
        BaseAI.execute_ai(self, local, obstacles, manager)


class RangedKiteMonsterAI(LocalMonsterAI):
    """Uses a ranged attack and retreats when prey reaches melee distance."""

    def __init__(self, unit):
        super().__init__(unit)
        self.kite_cooldown = 0

    def execute_ai(self, all_units, obstacles=None, manager=None):
        local = self._prepare(all_units, obstacles, manager)
        if local is None:
            return
        self.kite_cooldown = max(0, self.kite_cooldown - 1)
        if not self._is_valid_target(self.current_target):
            self.current_target = self.find_best_target(local, manager)
        target = self.current_target
        if target:
            dx = target.rect.centerx - self.unit.rect.centerx
            dy = target.rect.centery - self.unit.rect.centery
            if math.hypot(dx, dy) < 82 and self.kite_cooldown <= 0:
                if self.unit.perform_dash(-dx, -dy):
                    self.kite_cooldown = 180
                    self.state = "kite"
                    return
        BaseAI.execute_ai(self, local, obstacles, manager)


class HeavyChargeAI(LocalMonsterAI):
    """Slow tank that commits to a damaging straight-line charge."""

    def __init__(self, unit):
        super().__init__(unit)
        self.charge_cooldown = random.randint(120, 220)
        self.no_retreat = True

    def execute_ai(self, all_units, obstacles=None, manager=None):
        local = self._prepare(all_units, obstacles, manager)
        if local is None:
            return
        self.charge_cooldown -= 1
        if not self._is_valid_target(self.current_target):
            self.current_target = self.find_best_target(local, manager)
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
        BaseAI.execute_ai(self, local, obstacles, manager)
