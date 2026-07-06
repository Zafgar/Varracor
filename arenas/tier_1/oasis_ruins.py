import pygame
import random
import math
from settings import *
from arenas.base_arena import BaseArena, ArenaObstacle


class OasisRuins(BaseArena):
    """
    Tier 1: Oasis/ruins - areena
    - Oasis-vedet ylä/ala reunoilla (shimmer + kevyt aallotus)
    - Palmun varjojen “heiluminen”
    - Lämpöhuntu
    - Hiekkapöly + satunnaiset tuulenpuuskat (gust)
    - 3 rauniokiveä (collision), skaalautuvilla koordinaateilla
    - Reuna-collisionit (seinät)
    - FAILSAFE: bounds clamp (palauttaa unitit sisään jos clippaa)
    """

    def __init__(self):
        super().__init__("Oasis Ruins")
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT

        # --- Paletti ---
        self.sand = (198, 182, 132)
        self.sand_dark = (170, 155, 110)
        self.sand_light = (225, 210, 160)

        self.stone_mid = (95, 95, 105)
        self.stone_dark = (55, 55, 65)
        self.stone_light = (135, 135, 150)

        self.water_deep = (25, 90, 110)
        self.water_mid = (40, 120, 140)
        self.water_light = (120, 220, 240)

        # --- Layout ---
        self.ring_thick = max(52, int(min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.05))
        self.inner_pad = self.ring_thick + max(10, int(min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.012))

        self.play_rect = pygame.Rect(
            self.inner_pad + 40,
            self.inner_pad + 60,
            SCREEN_WIDTH - (self.inner_pad + 40) * 2,
            SCREEN_HEIGHT - (self.inner_pad + 60) * 2,
        )

        # --- FAILSAFE BOUNDS (uusi) ---
        # Tämän sisällä unitit "pakotetaan" pysymään vaikka ne joskus clippaa.
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
        # Estää hahmoja juoksemasta veteen tai ruudun ulkopuolelle
        wall_thick = 100

        # Yläreuna (Vesi)
        self.obstacles.add(ArenaObstacle(
            -wall_thick, -wall_thick,
            SCREEN_WIDTH + wall_thick * 2, self.inner_pad + wall_thick,
            "wall"
        ))
        # Alareuna (Vesi)
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

        # --- 3 rauniokiveä (rocks) ---
        rock_w = max(68, int(min(self.play_rect.w, self.play_rect.h) * 0.11))
        rock_h = max(50, int(rock_w * 0.78))

        rx1 = self.play_rect.x + int(self.play_rect.w * 0.40)
        ry1 = self.play_rect.y + int(self.play_rect.h * 0.34)

        rx2 = self.play_rect.x + int(self.play_rect.w * 0.58)
        ry2 = self.play_rect.y + int(self.play_rect.h * 0.55)

        rx3 = self.play_rect.x + int(self.play_rect.w * 0.48)
        ry3 = self.play_rect.y + int(self.play_rect.h * 0.70)

        rocks = [(rx1, ry1), (rx2, ry2), (rx3, ry3)]
        for x, y in rocks:
            self.obstacles.add(ArenaObstacle(x - rock_w // 2, y - rock_h // 2, rock_w, rock_h, "wall"))

        # --- caches ---
        self._bg_cache = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._fg_cache = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._build_bg()
        self._build_fg()

        # --- anim phases ---
        self.phase = 0.0
        self.heat_phase = 0.0

        # --- dust ---
        self.dust = []  # [x,y,vx,vy,life,scale]
        target = 34 if SCREEN_WIDTH >= 1600 else 26
        for _ in range(target):
            self._spawn_dust(initial=True)

        # cached dust sprites
        self._dust_sprites = []
        for a in range(0, 136, 16):
            s = pygame.Surface((12, 7), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (215, 200, 150, a), (0, 0, 12, 7))
            self._dust_sprites.append(s)

        # gusts (sand swirl)
        self.gusts = []  # [x,y,vx,vy,life,maxlife,scale]
        self._gust_timer = 0

        # overlays
        self.heat = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.haze = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    # ---------------------------
    # FAILSAFE (uusi)
    # ---------------------------
    def enforce_bounds(self, all_units):
        """Public wrapper: voit kutsua tätä myös GameManagerista loopin lopussa."""
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
    def _build_bg(self):
        bg = self._bg_cache
        bg.fill((0, 0, 0, 0))

        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        max_r = int(math.hypot(cx, cy))
        step = max(14, int(min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.012))

        # sand radial
        for r in range(max_r, 0, -step):
            p = r / max_r
            col = (
                int(self.sand_light[0] * (1 - p) + self.sand_dark[0] * p),
                int(self.sand_light[1] * (1 - p) + self.sand_dark[1] * p),
                int(self.sand_light[2] * (1 - p) + self.sand_dark[2] * p),
            )
            pygame.draw.circle(bg, col, (cx, cy), r)

        # grain (scaled)
        grains = int((SCREEN_WIDTH * SCREEN_HEIGHT) * 0.0010)
        for _ in range(grains):
            x = random.randint(0, SCREEN_WIDTH - 1)
            y = random.randint(self.ring_thick + 8, SCREEN_HEIGHT - self.ring_thick - 8)
            c = random.choice([(210, 195, 145), (175, 160, 115), (200, 185, 135), (190, 175, 125)])
            bg.set_at((x, y), c)

        # oasis water bands (top/bottom)
        band_h = max(62, int(SCREEN_HEIGHT * 0.055))
        top = pygame.Rect(0, 0, SCREEN_WIDTH, band_h)
        bot = pygame.Rect(0, SCREEN_HEIGHT - band_h, SCREEN_WIDTH, band_h)

        pygame.draw.rect(bg, self.water_deep, top)
        pygame.draw.rect(bg, self.water_deep, bot)

        # water inner edge highlight
        edge_h = max(10, int(band_h * 0.16))
        pygame.draw.rect(bg, self.water_mid, (0, band_h - edge_h, SCREEN_WIDTH, edge_h))
        pygame.draw.rect(bg, self.water_mid, (0, SCREEN_HEIGHT - band_h, SCREEN_WIDTH, edge_h))

        # stone lip between sand & water
        lip_h = max(10, int(SCREEN_HEIGHT * 0.010))
        pygame.draw.rect(bg, self.stone_dark, (0, band_h, SCREEN_WIDTH, lip_h))
        pygame.draw.rect(bg, self.stone_dark, (0, SCREEN_HEIGHT - band_h - lip_h, SCREEN_WIDTH, lip_h))

        pygame.draw.rect(bg, (0, 0, 0), top, 3)
        pygame.draw.rect(bg, (0, 0, 0), bot, 3)

        # small stones on sand
        for _ in range(80 if SCREEN_WIDTH >= 1600 else 60):
            x = random.randint(self.ring_thick + 40, SCREEN_WIDTH - self.ring_thick - 40)
            y = random.randint(band_h + 40, SCREEN_HEIGHT - band_h - 40)
            pygame.draw.circle(bg, (155, 145, 110), (x, y), random.randint(1, 3))

        # subtle vignette
        vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        steps = 90
        step2 = 9
        for i in range(0, steps, step2):
            a = int(140 * (i / steps))
            pygame.draw.rect(vignette, (0, 0, 0, a),
                             (i, i, SCREEN_WIDTH - 2 * i, SCREEN_HEIGHT - 2 * i), 10)
        bg.blit(vignette, (0, 0))

    def _build_fg(self):
        fg = self._fg_cache
        fg.fill((0, 0, 0, 0))

        # obstacle shadows
        for obs in self.obstacles:
            if getattr(obs, "type", "") != "wall":
                continue

            # Ei piirretä varjoja reunaesteille (ovat ruudun ulkopuolella)
            if obs.rect.w > 300 or obs.rect.h > 300:
                continue

            sh = pygame.Surface((obs.rect.w + 34, obs.rect.h + 34), pygame.SRCALPHA)
            pygame.draw.rect(sh, (0, 0, 0, 80), (18, 18, obs.rect.w, obs.rect.h), border_radius=12)
            fg.blit(sh, (obs.rect.x - 10, obs.rect.y - 10))

    # ---------- VFX ----------
    def _spawn_dust(self, initial=False):
        if initial:
            x = random.uniform(0, SCREEN_WIDTH)
        else:
            x = random.uniform(-60, 0)

        band_h = max(62, int(SCREEN_HEIGHT * 0.055))
        y = random.uniform(band_h + 40, SCREEN_HEIGHT - band_h - 40)

        vx = random.uniform(1.0, 2.8)
        vy = random.uniform(-0.22, 0.22)
        life = random.randint(44, 95)
        scale = random.uniform(0.85, 1.35)
        self.dust.append([x, y, vx, vy, life, scale])

    def _maybe_spawn_gust(self):
        self._gust_timer -= 1
        if self._gust_timer > 0:
            return
        self._gust_timer = random.randint(50, 110)

        band_h = max(62, int(SCREEN_HEIGHT * 0.055))
        x = random.uniform(-40, 0)
        y = random.uniform(band_h + 80, SCREEN_HEIGHT - band_h - 80)
        vx = random.uniform(3.2, 5.4)
        vy = random.uniform(-0.25, 0.25)
        life = random.randint(26, 42)
        scale = random.uniform(1.0, 1.7)
        self.gusts.append([x, y, vx, vy, life, life, scale])

    # ---------- loop ----------
    def update(self, all_units):
        self.phase += 0.02
        self.heat_phase += 0.018

        # dust
        for p in self.dust:
            p[0] += p[2]
            p[1] += p[3] + math.sin(p[0] * 0.02 + self.phase) * 0.10
            p[4] -= 1

        self.dust = [p for p in self.dust if p[4] > 0 and p[0] < SCREEN_WIDTH + 80]
        target = 34 if SCREEN_WIDTH >= 1600 else 26
        while len(self.dust) < target:
            self._spawn_dust(initial=False)

        # gusts
        self._maybe_spawn_gust()
        for g in self.gusts:
            g[0] += g[2]
            g[1] += g[3] + math.sin((g[0] * 0.03) + self.phase * 2.0) * 0.20
            g[4] -= 1
        self.gusts = [g for g in self.gusts if g[4] > 0 and g[0] < SCREEN_WIDTH + 120]

        # --- FAILSAFE (uusi) ---
        # Tämä kannattaa ajaa liikkeen jälkeen. Jos sun peliloopissa arena.update()
        # tapahtuu ennen unitien liikepäivitystä, siirrä kutsu GameManagerin loopin loppuun:
        # manager.arena.enforce_bounds(all_units)
        self._failsafe_keep_units_in_bounds(all_units)

    def draw_background(self, screen):
        screen.blit(self._bg_cache, (0, 0))

        band_h = max(62, int(SCREEN_HEIGHT * 0.055))

        # water shimmer (top+bottom)
        shimmer = pygame.Surface((SCREEN_WIDTH, band_h), pygame.SRCALPHA)
        for i in range(0, SCREEN_WIDTH, 22):
            a = 30 + int(22 * math.sin(self.phase * 2.1 + i * 0.05))
            pygame.draw.rect(shimmer, (*self.water_light, max(0, min(70, a))),
                             (i, int(band_h * 0.25), 16, 4), border_radius=3)
        screen.blit(shimmer, (0, 0))
        screen.blit(shimmer, (0, SCREEN_HEIGHT - band_h))

        # palm shadows (gentle sway)
        shadow = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        sx = int(140 + 35 * math.sin(self.phase * 0.9))
        base_y = band_h + int(0.10 * SCREEN_HEIGHT)

        count = max(6, SCREEN_WIDTH // 280)
        step = SCREEN_WIDTH // (count + 1)
        for k in range(1, count + 1):
            x = sx + k * step - 120
            y = base_y + int(14 * math.sin(self.phase + k * 0.7))
            pygame.draw.ellipse(shadow, (0, 0, 0, 16), (x, y, 240, 88))
        screen.blit(shadow, (0, 0))

        # heat + humid haze
        heat_a = 12 + int(7 * (0.5 + 0.5 * math.sin(self.heat_phase)))
        self.heat.fill((255, 175, 90, heat_a))
        screen.blit(self.heat, (0, 0))

        haze_a = 10 + int(6 * (0.5 + 0.5 * math.sin(self.heat_phase * 1.4)))
        self.haze.fill((235, 220, 180, haze_a))
        screen.blit(self.haze, (0, 0))

    def draw_foreground(self, screen):
        super().draw_foreground(screen)
        screen.blit(self._fg_cache, (0, 0))

        # rocks
        for obs in self.obstacles:
            if getattr(obs, "type", "") != "wall":
                continue

            # Piirretään vain kivet, ei reunoja
            if obs.rect.w > 300 or obs.rect.h > 300:
                continue

            self._draw_ruin_rock(screen, obs.rect)

        # gust rings
        for x, y, vx, vy, life, maxlife, scale in self.gusts:
            t = life / maxlife
            a = int(70 * t)
            r = int((18 + (1 - t) * 26) * scale)
            s = pygame.Surface((r * 2 + 6, r * 2 + 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (235, 220, 175, a),
                               (s.get_width() // 2, s.get_height() // 2), r, 2)
            screen.blit(s, (int(x - s.get_width() // 2), int(y - s.get_height() // 2)))

        # dust cached
        for x, y, vx, vy, life, scale in self.dust:
            idx = max(0, min(len(self._dust_sprites) - 1,
                             int((life / 95) * (len(self._dust_sprites) - 1))))
            spr = self._dust_sprites[idx]
            if abs(scale - 1.0) < 0.08:
                screen.blit(spr, (int(x), int(y)))
            else:
                w = max(6, int(spr.get_width() * scale))
                h = max(4, int(spr.get_height() * scale))
                screen.blit(pygame.transform.smoothscale(spr, (w, h)), (int(x), int(y)))

    def _draw_ruin_rock(self, screen, r):
        pygame.draw.rect(screen, self.stone_mid, r, border_radius=10)
        pygame.draw.rect(screen, self.stone_dark, r, 3, border_radius=10)

        # highlight
        hl_w = max(8, r.w // 6)
        hl = pygame.Rect(r.x + 6, r.y + 7, hl_w, r.h - 14)
        pygame.draw.rect(screen, self.stone_light, hl, border_radius=8)

        # tiny cracks
        pygame.draw.line(screen, (70, 70, 78), (r.x + 12, r.y + 16), (r.x + r.w - 16, r.y + 10), 2)
        pygame.draw.line(screen, (70, 70, 78), (r.x + 18, r.y + r.h - 18), (r.x + r.w - 12, r.y + r.h - 28), 2)
