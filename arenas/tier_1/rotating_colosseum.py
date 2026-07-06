import pygame
import random
import math
from settings import *
from arenas.base_arena import BaseArena, ArenaObstacle


class RotatingColosseum(BaseArena):
    """
    Tier 1: Jungle Arena (ei enää pyörimistä).
    - Viidakko-areena: vihreä reunus, sammal/maa, valonsäteet latvuksesta
    - Lehtiä ilmassa (kevyet VFX)
    - “apinasiluetteja” oksilla (pelkkä taustakoriste)
    - Gameplay: 4 pylvästä kuten ennen
    - Reuna-collisionit (seinät)
    - FAILSAFE: bounds clamp (palauttaa unitit sisään jos clippaa)
    """

    def __init__(self):
        super().__init__("Jungle Arena")
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT

        # --- Paletti ---
        self.soil_dark = (38, 34, 26)
        self.soil_mid = (64, 56, 40)
        self.soil_light = (92, 80, 55)

        self.moss_dark = (20, 60, 35)
        self.moss_mid = (35, 95, 55)
        self.moss_light = (70, 135, 85)

        self.stone_dark = (40, 42, 45)
        self.stone_mid = (78, 82, 88)
        self.stone_light = (130, 135, 140)

        self.crowd_base = (40, 55, 45)

        # --- Layout skaalaus ---
        self.ring_thick = max(52, int(min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.05))
        self.inner_pad = self.ring_thick + max(10, int(min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.012))

        self.play_rect = pygame.Rect(
            self.inner_pad + 40,
            self.inner_pad + 60,
            SCREEN_WIDTH - (self.inner_pad + 40) * 2,
            SCREEN_HEIGHT - (self.inner_pad + 60) * 2,
        )

        # --- FAILSAFE BOUNDS (uusi) ---
        # “sallittu” sisäalue, jonka sisällä unitit pidetään vaikka clippaa.
        bounds_margin = 6
        self.bounds_rect = pygame.Rect(
            self.inner_pad + bounds_margin,
            self.inner_pad + bounds_margin,
            SCREEN_WIDTH - (self.inner_pad + bounds_margin) * 2,
            SCREEN_HEIGHT - (self.inner_pad + bounds_margin) * 2,
        )

        # --- Obstacles ---
        self.obstacles.empty()

        # --- KORJAUS: LISÄTÄÄN SEINÄT (REUNAT) ---
        wall_thick = 100

        # Yläreuna
        self.obstacles.add(ArenaObstacle(
            -wall_thick, -wall_thick,
            SCREEN_WIDTH + wall_thick * 2, self.inner_pad + wall_thick,
            "wall"
        ))
        # Alareuna
        self.obstacles.add(ArenaObstacle(
            -wall_thick, SCREEN_HEIGHT - self.inner_pad,
            SCREEN_WIDTH + wall_thick * 2, self.inner_pad + wall_thick,
            "wall"
        ))
        # Vasen reuna
        self.obstacles.add(ArenaObstacle(
            -wall_thick, 0,
            self.inner_pad + wall_thick, SCREEN_HEIGHT,
            "wall"
        ))
        # Oikea reuna
        self.obstacles.add(ArenaObstacle(
            SCREEN_WIDTH - self.inner_pad, 0,
            self.inner_pad + wall_thick, SCREEN_HEIGHT,
            "wall"
        ))
        # ------------------------------------------

        # 4 pylvästä
        pillar_size = max(56, int(min(self.play_rect.w, self.play_rect.h) * 0.09))
        px1 = self.play_rect.x + int(self.play_rect.w * 0.28)
        px2 = self.play_rect.x + int(self.play_rect.w * 0.72)
        py1 = self.play_rect.y + int(self.play_rect.h * 0.30)
        py2 = self.play_rect.y + int(self.play_rect.h * 0.70)

        cols = [(px1, py1), (px2, py1), (px1, py2), (px2, py2)]
        for x, y in cols:
            self.obstacles.add(ArenaObstacle(x - pillar_size // 2, y - pillar_size // 2, pillar_size, pillar_size, "wall"))

        # --- Static caches ---
        self._bg_cache = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._fg_cache = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._build_static_bg()
        self._build_static_fg()

        # --- Light rays phase ---
        self.rays_phase = 0.0

        # --- Leaves VFX (cached sprites) ---
        self.leaves = []  # [x,y,vx,vy,rot,rot_spd,life,scale,variant]
        self._leaf_sprites = self._build_leaf_sprites()

        target = 46 if SCREEN_WIDTH >= 1600 else 34
        for _ in range(target):
            self._spawn_leaf(initial=True)

        # kevyt “humid haze”
        self.haze = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    # ---------------------------
    # FAILSAFE (uusi)
    # ---------------------------
    def enforce_bounds(self, all_units):
        """Public wrapper: voit kutsua myös GameManagerista loopin lopussa."""
        self._failsafe_keep_units_in_bounds(all_units)

    def _failsafe_keep_units_in_bounds(self, all_units):
        """
        Turvaverkko:
          - clamp unit.rect bounds_rect sisään
          - sync mahdolliset float-pos attribuutit (x/y/pos)
          - katkaisee AI:n escape/panic jos se jäi hakkaamaan seinää
        """
        if not all_units:
            return

        br = self.bounds_rect
        if br.w <= 0 or br.h <= 0:
            return

        for u in all_units:
            if not hasattr(u, "rect"):
                continue

            before = u.rect.topleft
            u.rect.clamp_ip(br)

            if u.rect.topleft != before:
                # synkkaa mahdolliset float-pos kentät (jos sun Gladiator käyttää niitä)
                if hasattr(u, "x"):
                    u.x = float(u.rect.x)
                if hasattr(u, "y"):
                    u.y = float(u.rect.y)
                if hasattr(u, "pos"):
                    try:
                        u.pos.x = float(u.rect.x)
                        u.pos.y = float(u.rect.y)
                    except Exception:
                        pass

                # nollaa “pakoon juoksu” jos se jäi seinään jumiin
                ai = getattr(u, "ai_controller", None)
                if ai and hasattr(ai, "escape_mode"):
                    ai.escape_mode = False
                    if hasattr(ai, "escape_timer"):
                        ai.escape_timer = 0

    # ---------- build ----------
    def _build_static_bg(self):
        bg = self._bg_cache
        bg.fill((0, 0, 0, 0))

        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

        # 1) Maa / soil gradient
        max_r = int(math.hypot(cx, cy))
        step = max(14, int(min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.012))
        for r in range(max_r, 0, -step):
            p = r / max_r
            col = (
                int(self.soil_light[0] * (1 - p) + self.soil_dark[0] * p),
                int(self.soil_light[1] * (1 - p) + self.soil_dark[1] * p),
                int(self.soil_light[2] * (1 - p) + self.soil_dark[2] * p),
            )
            pygame.draw.circle(bg, col, (cx, cy), r)

        # 2) Sammal “reunus”
        moss_band = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ip = self.inner_pad + 10
        rect = pygame.Rect(ip, ip, SCREEN_WIDTH - ip * 2, SCREEN_HEIGHT - ip * 2)
        pygame.draw.rect(moss_band, (*self.moss_mid, 75), rect, border_radius=26)
        pygame.draw.rect(moss_band, (*self.moss_dark, 85), rect, 10, border_radius=26)
        bg.blit(moss_band, (0, 0))

        # 3) “Soil specks”
        grains = int((SCREEN_WIDTH * SCREEN_HEIGHT) * 0.00085)
        for _ in range(grains):
            x = random.randint(0, SCREEN_WIDTH - 1)
            y = random.randint(self.ring_thick + 8, SCREEN_HEIGHT - self.ring_thick - 8)
            c = random.choice([(75, 66, 48), (90, 78, 55), (55, 48, 36), (35, 80, 50)])
            bg.set_at((x, y), c)

        # 4) Kivikehä (reuna “kivi”)
        rt = self.ring_thick
        pygame.draw.rect(bg, self.stone_dark, (0, 0, SCREEN_WIDTH, rt))
        pygame.draw.rect(bg, self.stone_dark, (0, SCREEN_HEIGHT - rt, SCREEN_WIDTH, rt))
        pygame.draw.rect(bg, self.stone_dark, (0, 0, rt, SCREEN_HEIGHT))
        pygame.draw.rect(bg, self.stone_dark, (SCREEN_WIDTH - rt, 0, rt, SCREEN_HEIGHT))

        edge = max(6, int(rt * 0.12))
        ip = self.inner_pad
        pygame.draw.rect(bg, self.stone_mid, (ip, ip, SCREEN_WIDTH - ip * 2, edge))
        pygame.draw.rect(bg, self.stone_mid, (ip, SCREEN_HEIGHT - ip - edge, SCREEN_WIDTH - ip * 2, edge))
        pygame.draw.rect(bg, self.stone_mid, (ip, ip, edge, SCREEN_HEIGHT - ip * 2))
        pygame.draw.rect(bg, self.stone_mid, (SCREEN_WIDTH - ip - edge, ip, edge, SCREEN_HEIGHT - ip * 2))

        # 5) Puut sivuille
        self._draw_trees(bg)

        # 6) “Apinat oksilla”
        self._draw_monkeys(bg)

        # 7) Vinjetti
        vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        steps = 92
        step2 = 9
        for i in range(0, steps, step2):
            a = int(150 * (i / steps))
            pygame.draw.rect(vignette, (0, 0, 0, a),
                             (i, i, SCREEN_WIDTH - 2 * i, SCREEN_HEIGHT - 2 * i), 10)
        bg.blit(vignette, (0, 0))

    def _build_static_fg(self):
        fg = self._fg_cache
        fg.fill((0, 0, 0, 0))

        # Obstacle shadow
        for obs in self.obstacles:
            if getattr(obs, "type", "") != "wall":
                continue

            # Ei piirretä varjoja reunaesteille
            if obs.rect.w > 300 or obs.rect.h > 300:
                continue

            shadow = pygame.Surface((obs.rect.w + 34, obs.rect.h + 34), pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 85), (18, 18, obs.rect.w, obs.rect.h), border_radius=12)
            fg.blit(shadow, (obs.rect.x - 10, obs.rect.y - 10))

    def _draw_trees(self, surf):
        left_x = self.ring_thick - 10
        right_x = SCREEN_WIDTH - self.ring_thick - 30
        for k in range(4):
            y = 120 + k * int((SCREEN_HEIGHT - 240) / 4)
            w = 40 + random.randint(-6, 12)
            h = 220 + random.randint(-30, 60)
            bark = (40, 30, 20)
            pygame.draw.rect(surf, bark, (left_x, y, w, h), border_radius=14)
            pygame.draw.rect(surf, bark, (right_x, y - 30, w, h + 40), border_radius=14)

            for i in range(5):
                rx = left_x + random.randint(-40, 80)
                ry = y - 40 + random.randint(-70, 40)
                rr = 60 + random.randint(-10, 20)
                col = (25, 90 + random.randint(-10, 20), 55 + random.randint(-10, 20))
                pygame.draw.circle(surf, col, (rx, ry), rr)

                rx2 = right_x + random.randint(-40, 80)
                ry2 = (y - 40) + random.randint(-70, 40)
                rr2 = 60 + random.randint(-10, 20)
                col2 = (25, 90 + random.randint(-10, 20), 55 + random.randint(-10, 20))
                pygame.draw.circle(surf, col2, (rx2, ry2), rr2)

    def _draw_monkeys(self, surf):
        top_y = self.ring_thick + 30
        for bx in (int(SCREEN_WIDTH * 0.18), int(SCREEN_WIDTH * 0.45), int(SCREEN_WIDTH * 0.72)):
            pygame.draw.line(surf, (30, 25, 20), (bx - 120, top_y), (bx + 160, top_y + 25), 8)
            mx = bx + random.randint(-20, 40)
            my = top_y - 18 + random.randint(-6, 6)
            pygame.draw.circle(surf, (10, 10, 10), (mx, my), 14)
            pygame.draw.ellipse(surf, (10, 10, 10), (mx - 16, my + 10, 34, 22))
            pygame.draw.arc(surf, (10, 10, 10), (mx + 8, my + 8, 32, 26), 0.6, 4.6, 4)

    def _build_leaf_sprites(self):
        sprites = []
        variants = [
            (55, 150, 80),
            (85, 170, 90),
            (120, 145, 70),
            (170, 140, 60),
        ]
        for col in variants:
            base = pygame.Surface((18, 10), pygame.SRCALPHA)
            pygame.draw.ellipse(base, (*col, 210), (0, 0, 18, 10))
            pygame.draw.line(base, (30, 50, 30, 140), (3, 5), (15, 5), 2)
            sprites.append(base)
        return sprites

    # ---------- VFX ----------
    def _spawn_leaf(self, initial=False):
        if initial:
            x = random.uniform(0, SCREEN_WIDTH)
            y = random.uniform(self.ring_thick + 40, SCREEN_HEIGHT - self.ring_thick - 40)
        else:
            edge = random.random()
            if edge < 0.5:
                x = random.uniform(-40, SCREEN_WIDTH + 40)
                y = random.uniform(-40, 0)
            else:
                x = random.uniform(-40, 0)
                y = random.uniform(self.ring_thick + 60, SCREEN_HEIGHT - self.ring_thick - 60)

        vx = random.uniform(0.8, 2.2)
        vy = random.uniform(0.6, 1.8)
        rot = random.uniform(0, 360)
        rot_spd = random.uniform(-2.6, 2.6)
        life = random.randint(140, 260)
        scale = random.uniform(0.85, 1.35)
        variant = random.randint(0, len(self._leaf_sprites) - 1)
        self.leaves.append([x, y, vx, vy, rot, rot_spd, life, scale, variant])

    # ---------- loop ----------
    def update(self, all_units):
        self.rays_phase += 0.012

        for L in self.leaves:
            L[0] += L[2] + math.sin((L[1] + self.rays_phase * 80) * 0.01) * 0.35
            L[1] += L[3] + math.sin((L[0] + self.rays_phase * 50) * 0.008) * 0.25
            L[4] = (L[4] + L[5]) % 360.0
            L[6] -= 1

        self.leaves = [L for L in self.leaves if L[6] > 0 and L[1] < SCREEN_HEIGHT + 80 and L[0] < SCREEN_WIDTH + 120]

        target = 46 if SCREEN_WIDTH >= 1600 else 34
        while len(self.leaves) < target:
            self._spawn_leaf(initial=False)

        # --- FAILSAFE (uusi) ---
        # Jos sun peliloopissa arena.update() ajetaan ennen unitien liikettä,
        # siirrä tämä GameManagerin loopin loppuun:
        # manager.arena.enforce_bounds(all_units)
        self._failsafe_keep_units_in_bounds(all_units)

    def draw_background(self, screen):
        screen.blit(self._bg_cache, (0, 0))
        self._draw_light_rays(screen)

        a = 10 + int(6 * (0.5 + 0.5 * math.sin(self.rays_phase * 2.1)))
        self.haze.fill((140, 200, 170, a))
        screen.blit(self.haze, (0, 0))

    def _draw_light_rays(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        cx = int(SCREEN_WIDTH * 0.55)
        top = self.ring_thick + 10

        for k in range(5):
            ang = (self.rays_phase * 0.7) + k * 0.85
            spread = 0.18 + 0.03 * math.sin(self.rays_phase + k)
            length = int(min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.65)

            p0 = (cx + int(math.sin(ang) * 120), top)
            p1 = (p0[0] - int(length * spread), top + length)
            p2 = (p0[0] + int(length * spread), top + length)

            alpha = 18 + int(10 * (0.5 + 0.5 * math.sin(self.rays_phase * 2.2 + k)))
            pygame.draw.polygon(overlay, (255, 245, 210, alpha), [p0, p1, p2])

        screen.blit(overlay, (0, 0))

    def draw_foreground(self, screen):
        screen.blit(self._fg_cache, (0, 0))

        for obs in self.obstacles:
            if getattr(obs, "type", "") != "wall":
                continue

            if obs.rect.w > 300 or obs.rect.h > 300:
                continue

            self._draw_mossy_pillar(screen, obs.rect)

        for x, y, vx, vy, rot, rot_spd, life, scale, variant in self.leaves:
            spr = self._leaf_sprites[variant]
            if abs(scale - 1.0) > 0.08:
                spr2 = pygame.transform.smoothscale(
                    spr,
                    (max(8, int(spr.get_width() * scale)), max(6, int(spr.get_height() * scale)))
                )
            else:
                spr2 = spr

            spr3 = pygame.transform.rotate(spr2, rot)
            screen.blit(spr3, (int(x), int(y)))

    def _draw_mossy_pillar(self, screen, r):
        pygame.draw.rect(screen, self.stone_mid, r, border_radius=12)
        pygame.draw.rect(screen, self.stone_dark, r, 3, border_radius=12)

        top = pygame.Rect(r.x + 4, r.y + 4, r.w - 8, max(8, int(r.h * 0.18)))
        pygame.draw.rect(screen, self.moss_mid, top, border_radius=10)
        pygame.draw.rect(screen, self.moss_dark, top, 2, border_radius=10)

        hl = pygame.Rect(r.x + 6, r.y + 7, 9, r.h - 14)
        pygame.draw.rect(screen, self.stone_light, hl, border_radius=8)

        pygame.draw.line(screen, (65, 65, 70), (r.x + 12, r.y + 18), (r.x + r.w - 18, r.y + 12), 2)
        pygame.draw.line(screen, (65, 65, 70), (r.x + 18, r.y + r.h - 20), (r.x + r.w - 14, r.y + r.h - 30), 2)
