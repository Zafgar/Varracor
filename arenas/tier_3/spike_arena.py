import pygame
import random
import math
from settings import *
from arenas.base_arena import BaseArena, ArenaObstacle


class SpikeArena(BaseArena):
    """Ruosteinen piikkimonttu (Tier 3): rautaharkot antavat suojaa
    (myös ammuksilta), ja piikkiansat nousevat lattiasta TELEGRAAFILLA -
    raot tärisevät hetken ennen laukeamista, joten ne voi väistää.

    BUGIKORJAUS: vanha versio ei koskaan latautunut (rikkinäinen
    vfx-import) ja piikit vahingoittivat ilman varoitusta."""

    def __init__(self):
        super().__init__("Rustyard Spike Pit")
        self.floor_color = (58, 44, 38)
        pad = 60
        t = 100
        self.obstacles.add(ArenaObstacle(-t, -t, SCREEN_WIDTH + t * 2, pad + t, "wall"))
        self.obstacles.add(ArenaObstacle(-t, SCREEN_HEIGHT - pad, SCREEN_WIDTH + t * 2, pad + t, "wall"))
        self.obstacles.add(ArenaObstacle(-t, 0, pad + t, SCREEN_HEIGHT, "wall"))
        self.obstacles.add(ArenaObstacle(SCREEN_WIDTH - pad, 0, pad + t, SCREEN_HEIGHT, "wall"))

        # SUOJAT: ruostuneet rautaharkot
        self.cover = [
            pygame.Rect(int(SCREEN_WIDTH * 0.26), int(SCREEN_HEIGHT * 0.30), 84, 84),
            pygame.Rect(int(SCREEN_WIDTH * 0.70), int(SCREEN_HEIGHT * 0.30), 84, 84),
            pygame.Rect(int(SCREEN_WIDTH * 0.26), int(SCREEN_HEIGHT * 0.64), 84, 84),
            pygame.Rect(int(SCREEN_WIDTH * 0.70), int(SCREEN_HEIGHT * 0.64), 84, 84),
            pygame.Rect(int(SCREEN_WIDTH * 0.48), int(SCREEN_HEIGHT * 0.20), 150, 44),
            pygame.Rect(int(SCREEN_WIDTH * 0.48), int(SCREEN_HEIGHT * 0.76), 150, 44),
        ]
        for r in self.cover:
            self.obstacles.add(ArenaObstacle(r.x, r.y, r.w, r.h, "wall"))

        # Piikkiraot: {"rect", "state": idle/warn/out, "timer"}
        rng = random.Random(19)
        self.traps = []
        spots = [(0.38, 0.46), (0.60, 0.46), (0.49, 0.60), (0.34, 0.72),
                 (0.64, 0.24)]
        for fx, fy in spots:
            r = pygame.Rect(int(SCREEN_WIDTH * fx), int(SCREEN_HEIGHT * fy), 90, 42)
            self.traps.append({"rect": r, "state": "idle",
                               "timer": rng.randint(180, 480)})

        self.sparks = []
        self._bg = None

    # ------------------------------------------------------------------
    def _build_bg(self):
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.fill(self.floor_color)
        rng = random.Random(5)
        for _ in range(320):
            x, y = rng.randint(0, SCREEN_WIDTH), rng.randint(0, SCREEN_HEIGHT)
            c = rng.choice(((66, 50, 42), (50, 38, 34), (74, 52, 40)))
            bg.fill(c, (x, y, rng.randint(8, 30), rng.randint(4, 14)))
        # Ruosteläikät
        for _ in range(40):
            x, y = rng.randint(60, SCREEN_WIDTH - 60), rng.randint(60, SCREEN_HEIGHT - 60)
            pygame.draw.ellipse(bg, (96, 58, 34), (x, y, rng.randint(20, 60), rng.randint(10, 26)))
        # Reunat: niitatut rautalevyt
        pygame.draw.rect(bg, (64, 58, 54), (0, 0, SCREEN_WIDTH, 60))
        pygame.draw.rect(bg, (64, 58, 54), (0, SCREEN_HEIGHT - 60, SCREEN_WIDTH, 60))
        pygame.draw.rect(bg, (64, 58, 54), (0, 0, 60, SCREEN_HEIGHT))
        pygame.draw.rect(bg, (64, 58, 54), (SCREEN_WIDTH - 60, 0, 60, SCREEN_HEIGHT))
        for x in range(30, SCREEN_WIDTH, 90):
            pygame.draw.circle(bg, (40, 36, 34), (x, 30), 5)
            pygame.draw.circle(bg, (40, 36, 34), (x, SCREEN_HEIGHT - 30), 5)
        # Piikkirakojen pohjat
        for trap in self.traps:
            r = trap["rect"]
            pygame.draw.rect(bg, (28, 24, 22), r, border_radius=6)
            pygame.draw.rect(bg, (80, 62, 48), r, 2, border_radius=6)
        return bg

    # ------------------------------------------------------------------
    def update(self, all_units):
        for trap in self.traps:
            trap["timer"] -= 1
            if trap["state"] == "idle" and trap["timer"] <= 0:
                trap["state"] = "warn"          # rako tärisee 50 framea
                trap["timer"] = 50
            elif trap["state"] == "warn" and trap["timer"] <= 0:
                trap["state"] = "out"           # piikit ylhäällä 90 framea
                trap["timer"] = 90
                for _ in range(8):
                    self.sparks.append([trap["rect"].centerx + random.randint(-40, 40),
                                        trap["rect"].centery,
                                        random.uniform(-1.5, 1.5),
                                        random.uniform(-3.5, -1.0), 26])
            elif trap["state"] == "out":
                if trap["timer"] % 12 == 0:
                    for u in all_units:
                        if getattr(u, "is_dead", False):
                            continue
                        if u.rect.colliderect(trap["rect"]):
                            u.take_damage(8, "Physical")
                if trap["timer"] <= 0:
                    trap["state"] = "idle"
                    trap["timer"] = random.randint(240, 600)

        for s in self.sparks:
            s[0] += s[2]; s[1] += s[3]; s[3] += 0.15; s[4] -= 1
        self.sparks = [s for s in self.sparks if s[4] > 0]

    # ------------------------------------------------------------------
    def draw_background(self, screen):
        if self._bg is None:
            self._bg = self._build_bg()
        screen.blit(self._bg, (0, 0))

    def draw_foreground(self, screen):
        # Rautaharkot (suojat)
        for r in self.cover:
            pygame.draw.rect(screen, (22, 20, 18), r.move(4, 5), border_radius=6)
            pygame.draw.rect(screen, (88, 74, 62), r, border_radius=6)
            pygame.draw.rect(screen, (48, 40, 36), r, 3, border_radius=6)
            pygame.draw.line(screen, (120, 92, 66), (r.x + 6, r.y + 8),
                             (r.x + 6, r.bottom - 8), 3)

        # Piikkiansat
        tick = pygame.time.get_ticks()
        for trap in self.traps:
            r = trap["rect"]
            if trap["state"] == "warn":
                # Tärisevä varoitus: rako hehkuu punaisena
                jitter = random.randint(-2, 2)
                warn = pygame.Surface((r.w + 12, r.h + 12), pygame.SRCALPHA)
                pygame.draw.rect(warn, (255, 90, 60, 110), warn.get_rect(), 3,
                                 border_radius=8)
                screen.blit(warn, (r.x - 6 + jitter, r.y - 6))
            elif trap["state"] == "out":
                # Piikit ylhäällä
                n = max(4, r.w // 18)
                for i in range(n):
                    px = r.x + 6 + i * (r.w - 12) // max(1, n - 1)
                    pygame.draw.polygon(screen, (168, 158, 148),
                                        [(px - 6, r.bottom - 4),
                                         (px, r.y - 16),
                                         (px + 6, r.bottom - 4)])
                    pygame.draw.polygon(screen, (90, 82, 76),
                                        [(px - 6, r.bottom - 4),
                                         (px, r.y - 16),
                                         (px + 6, r.bottom - 4)], 1)

        # Kipinät
        for x, y, _vx, _vy, life in self.sparks:
            col = (255, 200, 90) if life > 12 else (200, 110, 60)
            pygame.draw.circle(screen, col, (int(x), int(y)), 2)
