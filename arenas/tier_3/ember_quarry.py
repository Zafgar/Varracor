import pygame
import random
import math
from settings import *
from arenas.base_arena import BaseArena, ArenaObstacle


class EmberQuarry(BaseArena):
    """Hehkulouhos (Tier 3): laavakanavat jakavat kentän kaistoihin ja
    louhoskivet antavat suojaa (estävät myös ammukset). Laava vahingoittaa
    päällä seisovaa, mutta nuolet lentävät sen yli - asemointi ratkaisee."""

    def __init__(self):
        super().__init__("Ember Quarry")
        self.floor_color = (44, 38, 40)
        pad = 60
        t = 100
        self.obstacles.add(ArenaObstacle(-t, -t, SCREEN_WIDTH + t * 2, pad + t, "wall"))
        self.obstacles.add(ArenaObstacle(-t, SCREEN_HEIGHT - pad, SCREEN_WIDTH + t * 2, pad + t, "wall"))
        self.obstacles.add(ArenaObstacle(-t, 0, pad + t, SCREEN_HEIGHT, "wall"))
        self.obstacles.add(ArenaObstacle(SCREEN_WIDTH - pad, 0, pad + t, SCREEN_HEIGHT, "wall"))

        # Laavakanavat: kaksi railoa aukkoineen (kulkureitit jäävät)
        self.lava = [
            pygame.Rect(int(SCREEN_WIDTH * 0.36), 60, 70, int(SCREEN_HEIGHT * 0.34)),
            pygame.Rect(int(SCREEN_WIDTH * 0.36), int(SCREEN_HEIGHT * 0.62), 70,
                        SCREEN_HEIGHT - 60 - int(SCREEN_HEIGHT * 0.62)),
            pygame.Rect(int(SCREEN_WIDTH * 0.62), int(SCREEN_HEIGHT * 0.28), 70,
                        int(SCREEN_HEIGHT * 0.44)),
        ]
        for r in self.lava:
            self.obstacles.add(ArenaObstacle(r.x, r.y, r.w, r.h, "lava"))

        # SUOJAT: louhoskivet
        self.cover = [
            pygame.Rect(int(SCREEN_WIDTH * 0.18), int(SCREEN_HEIGHT * 0.42), 92, 78),
            pygame.Rect(int(SCREEN_WIDTH * 0.50), int(SCREEN_HEIGHT * 0.16), 92, 78),
            pygame.Rect(int(SCREEN_WIDTH * 0.50), int(SCREEN_HEIGHT * 0.74), 92, 78),
            pygame.Rect(int(SCREEN_WIDTH * 0.80), int(SCREEN_HEIGHT * 0.44), 92, 78),
        ]
        for r in self.cover:
            self.obstacles.add(ArenaObstacle(r.x, r.y, r.w, r.h, "wall"))

        self.embers = [[random.uniform(0, SCREEN_WIDTH),
                        random.uniform(0, SCREEN_HEIGHT),
                        random.uniform(-0.4, 0.4),
                        random.uniform(-1.4, -0.5),
                        random.randint(40, 120)] for _ in range(60)]
        self._bg = None
        self._tick = 0

    def _build_bg(self):
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.fill(self.floor_color)
        rng = random.Random(23)
        for _ in range(340):
            x, y = rng.randint(0, SCREEN_WIDTH), rng.randint(0, SCREEN_HEIGHT)
            c = rng.choice(((52, 44, 46), (38, 32, 36), (58, 48, 44)))
            bg.fill(c, (x, y, rng.randint(10, 34), rng.randint(6, 16)))
        # Louhitut porrasjäljet
        for _ in range(26):
            x, y = rng.randint(80, SCREEN_WIDTH - 160), rng.randint(80, SCREEN_HEIGHT - 120)
            pygame.draw.rect(bg, (36, 30, 32), (x, y, rng.randint(60, 140), 8))
        # Reunakalliot
        pygame.draw.rect(bg, (58, 50, 50), (0, 0, SCREEN_WIDTH, 60))
        pygame.draw.rect(bg, (58, 50, 50), (0, SCREEN_HEIGHT - 60, SCREEN_WIDTH, 60))
        pygame.draw.rect(bg, (58, 50, 50), (0, 0, 60, SCREEN_HEIGHT))
        pygame.draw.rect(bg, (58, 50, 50), (SCREEN_WIDTH - 60, 0, 60, SCREEN_HEIGHT))
        return bg

    def update(self, all_units):
        self._tick += 1
        # Laava polttaa päällä seisovia (tasainen, väisteltävä)
        if self._tick % 20 == 0:
            for u in all_units:
                if getattr(u, "is_dead", False):
                    continue
                for r in self.lava:
                    if u.rect.colliderect(r):
                        u.take_damage(6, "Fire")
                        break
        # Kekäleet leijuvat
        for e in self.embers:
            e[0] += e[2]
            e[1] += e[3]
            e[4] -= 1
            if e[4] <= 0 or e[1] < -10:
                lava = random.choice(self.lava)
                e[0] = random.uniform(lava.x, lava.right)
                e[1] = random.uniform(lava.y, lava.bottom)
                e[2] = random.uniform(-0.4, 0.4)
                e[3] = random.uniform(-1.6, -0.6)
                e[4] = random.randint(40, 120)

    def draw_background(self, screen):
        if self._bg is None:
            self._bg = self._build_bg()
        screen.blit(self._bg, (0, 0))
        # Laava: sykkivä hehku
        pulse = 0.5 + 0.5 * math.sin(self._tick * 0.05)
        for r in self.lava:
            pygame.draw.rect(screen, (150, 52, 20), r, border_radius=8)
            inner = r.inflate(-14, -14)
            if inner.w > 0 and inner.h > 0:
                col = (216 + int(20 * pulse), 96 + int(30 * pulse), 26)
                pygame.draw.rect(screen, col, inner, border_radius=8)
            # Tummat laattakuviot virtaavassa laavassa
            for i in range(3):
                y = r.y + 18 + ((self._tick // 3 + i * 40) % max(1, r.h - 30))
                pygame.draw.ellipse(screen, (120, 40, 16),
                                    (r.x + 12, r.y + min(y - r.y, r.h - 24), r.w - 24, 12))
            pygame.draw.rect(screen, (70, 30, 20), r, 3, border_radius=8)

    def draw_foreground(self, screen):
        # Louhoskivet (suojat)
        for r in self.cover:
            pygame.draw.rect(screen, (24, 20, 22), r.move(4, 5), border_radius=10)
            pygame.draw.rect(screen, (94, 84, 82), r, border_radius=10)
            pygame.draw.rect(screen, (54, 46, 48), r, 3, border_radius=10)
            pygame.draw.line(screen, (120, 104, 96), (r.x + 10, r.y + 12),
                             (r.x + r.w - 24, r.y + 26), 2)
        # Kekäleet
        for x, y, _vx, _vy, life in self.embers:
            col = (255, 170, 70) if life > 50 else (200, 90, 40)
            pygame.draw.circle(screen, col, (int(x), int(y)), 2)
