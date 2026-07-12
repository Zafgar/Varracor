"""Procedural animated water for outdoor maps.

The renderer intentionally avoids large water texture assets. A deterministic
shore profile is generated once, while waves, foam, current streaks, glints and
ripples are drawn from code every frame. The same body also exposes collision
barriers and fishing anchors so rendering and gameplay share one shoreline.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import pygame


Color = Tuple[int, int, int]
Point = Tuple[int, int]


@dataclass(frozen=True)
class FishingAnchor:
    """Stable world-space point for a future fishing minigame."""

    x: int
    y: int
    bank: str
    water_name: str
    difficulty: int = 1
    fish_table: str = "muckford_marsh"


class WaterBarrier:
    """Invisible collision slice generated from the visible shoreline."""

    def __init__(self, rect: pygame.Rect):
        self.rect = pygame.Rect(rect)
        self.image_pos = self.rect.topleft
        self.image = None
        self.type = "water"
        self.name = "Deep Water"
        self.is_structure = True
        self.is_dead = False
        self.blocks_projectiles = False
        self.team_color = "Neutral"

    def draw_on_screen(self, *_args, **_kwargs):
        return None


class ProceduralWaterBody:
    """Animated river, channel or pond with deterministic irregular shores."""

    def __init__(
        self,
        rect: pygame.Rect | Sequence[int],
        *,
        seed: int = 1,
        name: str = "water",
        flow: Tuple[float, float] = (0.35, 1.0),
        shore_variance: int = 34,
        deep_margin: int = 42,
        shallow_color: Color = (58, 105, 111),
        mid_color: Color = (35, 78, 94),
        deep_color: Color = (20, 50, 70),
        foam_color: Color = (185, 215, 207),
    ):
        self.rect = pygame.Rect(rect)
        self.seed = int(seed)
        self.name = str(name)
        self.flow = flow
        self.shore_variance = max(0, int(shore_variance))
        self.deep_margin = max(12, int(deep_margin))
        self.shallow_color = shallow_color
        self.mid_color = mid_color
        self.deep_color = deep_color
        self.foam_color = foam_color
        self._sample_step = 48
        self._profile = self._build_profile()
        self._static_surface = self._build_static_surface()
        self._glints = self._build_glints()
        self._ripples: List[Tuple[int, int, int]] = []

    # ------------------------------------------------------------------
    # Geometry shared by rendering, collision and fishing
    # ------------------------------------------------------------------
    def _build_profile(self) -> List[Tuple[int, int, int]]:
        rng = random.Random(self.seed)
        samples: List[Tuple[int, int, int]] = []
        left_noise = rng.randint(-self.shore_variance, self.shore_variance)
        right_noise = rng.randint(-self.shore_variance, self.shore_variance)
        y = 0
        while y <= self.rect.height + self._sample_step:
            left_noise = int(left_noise * 0.62 + rng.randint(-18, 18))
            right_noise = int(right_noise * 0.62 + rng.randint(-18, 18))
            left_noise = max(-self.shore_variance, min(self.shore_variance, left_noise))
            right_noise = max(-self.shore_variance, min(self.shore_variance, right_noise))
            left = 18 + left_noise
            right = self.rect.width - 18 + right_noise
            if right - left < 120:
                right = left + 120
            samples.append((y, left, right))
            y += self._sample_step
        return samples

    def _local_bounds_at(self, local_y: float) -> Tuple[float, float]:
        y = max(0.0, min(float(local_y), float(self.rect.height)))
        index = min(int(y // self._sample_step), len(self._profile) - 2)
        y0, left0, right0 = self._profile[index]
        y1, left1, right1 = self._profile[index + 1]
        span = max(1.0, float(y1 - y0))
        t = (y - y0) / span
        left = left0 + (left1 - left0) * t
        right = right0 + (right1 - right0) * t
        return left, right

    def bounds_at(self, world_y: float) -> Tuple[float, float]:
        left, right = self._local_bounds_at(world_y - self.rect.top)
        return self.rect.left + left, self.rect.left + right

    def contains_point(self, point: Sequence[float], inset: int = 0) -> bool:
        x, y = float(point[0]), float(point[1])
        if not (self.rect.top <= y <= self.rect.bottom):
            return False
        left, right = self.bounds_at(y)
        return left + inset <= x <= right - inset

    def span_rect(self, world_y: int, height: int = 86, padding: int = 36) -> pygame.Rect:
        left, right = self.bounds_at(world_y)
        return pygame.Rect(
            int(left - padding),
            int(world_y - height // 2),
            int((right - left) + padding * 2),
            int(height),
        )

    def make_collision_barriers(
        self,
        crossing_bands: Iterable[Tuple[int, int]] = (),
        *,
        slice_height: int = 58,
        inset: int = 10,
    ) -> List[WaterBarrier]:
        """Generate shoreline-following blockers, leaving bridge bands open."""
        bands = [(int(a), int(b)) for a, b in crossing_bands]
        barriers: List[WaterBarrier] = []
        y = self.rect.top
        while y < self.rect.bottom:
            h = min(slice_height, self.rect.bottom - y)
            center_y = y + h // 2
            if any(start <= center_y <= end for start, end in bands):
                y += h
                continue
            left, right = self.bounds_at(center_y)
            width = max(8, int(right - left) - inset * 2)
            barriers.append(
                WaterBarrier(pygame.Rect(int(left) + inset, y, width, h + 1))
            )
            y += h
        return barriers

    def fishing_anchors(self, count: int = 6, difficulty: int = 1) -> List[FishingAnchor]:
        """Return deterministic bank positions suitable for later fishing UI."""
        rng = random.Random(self.seed + 913)
        anchors: List[FishingAnchor] = []
        margin = 150
        usable = max(1, self.rect.height - margin * 2)
        for index in range(max(1, int(count))):
            local_y = margin + int((index + 0.5) * usable / max(1, count))
            local_y += rng.randint(-55, 55)
            world_y = self.rect.top + local_y
            left, right = self.bounds_at(world_y)
            bank = "left" if index % 2 == 0 else "right"
            x = int(left - 30) if bank == "left" else int(right + 30)
            anchors.append(
                FishingAnchor(
                    x=x,
                    y=int(world_y),
                    bank=bank,
                    water_name=self.name,
                    difficulty=int(difficulty),
                )
            )
        return anchors

    # ------------------------------------------------------------------
    # Static water color and animated detail
    # ------------------------------------------------------------------
    def _polygon(self, inset: int = 0) -> List[Point]:
        left_points: List[Point] = []
        right_points: List[Point] = []
        for y, left, right in self._profile:
            py = min(y, self.rect.height)
            left_points.append((int(left + inset), int(py)))
            right_points.append((int(right - inset), int(py)))
        return left_points + list(reversed(right_points))

    def _build_static_surface(self) -> pygame.Surface:
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.polygon(surface, (*self.shallow_color, 255), self._polygon(0))
        pygame.draw.polygon(
            surface,
            (*self.mid_color, 255),
            self._polygon(max(14, self.deep_margin // 2)),
        )
        pygame.draw.polygon(
            surface,
            (*self.deep_color, 255),
            self._polygon(self.deep_margin),
        )

        # Static submerged mottling gives depth without a texture asset.
        rng = random.Random(self.seed + 77)
        for _ in range(max(20, self.rect.height // 22)):
            local_y = rng.randrange(0, max(1, self.rect.height))
            left, right = self._local_bounds_at(local_y)
            if right - left < self.deep_margin * 2 + 20:
                continue
            x = rng.randint(int(left + self.deep_margin), int(right - self.deep_margin))
            radius = rng.randint(8, 28)
            color = (12, 42, 59, rng.randint(15, 34))
            pygame.draw.ellipse(
                surface,
                color,
                pygame.Rect(x - radius, local_y - radius // 3, radius * 2, radius),
            )
        return surface

    def _build_glints(self):
        rng = random.Random(self.seed + 311)
        glints = []
        count = max(18, self.rect.height // 70)
        for _ in range(count):
            local_y = rng.randint(25, max(25, self.rect.height - 25))
            left, right = self._local_bounds_at(local_y)
            u = rng.random()
            x = int(left + (right - left) * u)
            glints.append((x, local_y, rng.random() * math.tau, rng.randint(6, 22)))
        return glints

    def add_ripple(self, world_pos: Sequence[int], now_ms: int | None = None) -> None:
        if not self.contains_point(world_pos):
            return
        timestamp = pygame.time.get_ticks() if now_ms is None else int(now_ms)
        self._ripples.append((int(world_pos[0]), int(world_pos[1]), timestamp))

    def draw(self, screen: pygame.Surface, offset=(0, 0), now_ms: int | None = None) -> None:
        now = pygame.time.get_ticks() if now_ms is None else int(now_ms)
        ox, oy = int(offset[0]), int(offset[1])
        screen.blit(self._static_surface, (self.rect.x - ox, self.rect.y - oy))

        view_top = max(self.rect.top, oy - 40)
        view_bottom = min(self.rect.bottom, oy + screen.get_height() + 40)
        if view_bottom <= view_top:
            return

        t = now * 0.001
        flow_x, flow_y = self.flow

        # Moving current bands across the visible water.
        start_y = int(view_top // 30) * 30
        for world_y in range(start_y, int(view_bottom) + 1, 30):
            left, right = self.bounds_at(world_y)
            width = right - left
            if width < 70:
                continue
            points = []
            for step in range(6):
                u = step / 5.0
                x = left + 24 + (width - 48) * u
                y = world_y + math.sin(t * 1.7 + u * 5.5 + world_y * 0.026) * 3.2
                x += math.sin(t * 0.65 + world_y * 0.012) * flow_x * 8
                y += math.sin(t * 0.55) * flow_y * 1.8
                points.append((int(x - ox), int(y - oy)))
            pygame.draw.aalines(screen, (75, 132, 145), False, points)

        # Foam curls along both banks. The phase travels with the current.
        foam_start = int(view_top // 18) * 18
        for world_y in range(foam_start, int(view_bottom) + 1, 18):
            left, right = self.bounds_at(world_y)
            wobble = math.sin(t * 2.4 + world_y * 0.052) * 5.5
            alpha_color = self.foam_color
            lx = int(left + 8 + wobble - ox)
            rx = int(right - 8 - wobble - ox)
            sy = int(world_y - oy)
            length = 6 + int((math.sin(t * 1.9 + world_y) + 1.0) * 3)
            pygame.draw.line(screen, alpha_color, (lx, sy), (lx + length, sy + 2), 2)
            pygame.draw.line(screen, alpha_color, (rx, sy), (rx - length, sy + 2), 2)
            if (world_y // 18) % 3 == 0:
                pygame.draw.circle(screen, (215, 232, 222), (lx + 2, sy - 2), 2)
                pygame.draw.circle(screen, (215, 232, 222), (rx - 2, sy - 2), 2)

        # Sun/sky glints pulse independently and move a little with the current.
        for gx, gy, phase, length in self._glints:
            world_y = self.rect.top + gy
            if not (view_top <= world_y <= view_bottom):
                continue
            pulse = (math.sin(t * 2.2 + phase) + 1.0) * 0.5
            if pulse < 0.42:
                continue
            drift = math.sin(t * 0.8 + phase) * 5 * flow_x
            sx = int(self.rect.left + gx + drift - ox)
            sy = int(world_y + math.sin(t + phase) * 2 - oy)
            draw_len = max(3, int(length * pulse))
            pygame.draw.line(screen, (150, 190, 190), (sx, sy), (sx + draw_len, sy), 1)

        # Expanding rings are useful for rain, creatures and future fishing casts.
        alive_ripples: List[Tuple[int, int, int]] = []
        for x, y, started in self._ripples:
            age = now - started
            if age >= 1800:
                continue
            alive_ripples.append((x, y, started))
            radius = 4 + int(age * 0.026)
            fade = max(40, 170 - int(age * 0.075))
            layer = pygame.Surface((radius * 2 + 6, radius + 8), pygame.SRCALPHA)
            pygame.draw.ellipse(
                layer,
                (175, 218, 218, fade),
                pygame.Rect(3, 3, radius * 2, max(4, radius // 2)),
                1,
            )
            screen.blit(layer, (x - radius - ox, y - radius // 3 - oy))
        self._ripples = alive_ripples
