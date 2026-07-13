# arenas/tier_1/grand_slam_arena.py
"""Grand Slam -finaalin stadion: ruutua ISOMPI areena katsomoineen.

- Taistelumonttu (pit) on ~1880x1060 - tilaa taktiikoille, dashille ja
  liikekyvyille. Kamera seuraa Commanderia (game_manager clampaa).
- Katsomot neljällä sivulla: animoitu yleisö, liput, viirit, soihdut.
  Yleisössä tuttuja muckfordilaisia jotka huutavat kannustuksia.
- Kierroskohtaiset "jujut" (set_twist):
    1 = puhdas mittelö
    2 = CROWD DEBRIS - yleisö paiskoo romua kehään (varoitusrinki -> isku)
    3 = FIRE RING - sudden death, tulirengas kutistuu keskustaa kohti

Kaikki grafiikka piirretään koodilla (ei kuvatiedostoja); staattinen
pohja välimuistitetaan yhteen pintaan.
"""

import math
import random

import pygame

from arenas.base_arena import BaseArena, ArenaObstacle
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from sound_manager import sound_system

ARENA_W, ARENA_H = 3000, 1900
PIT = pygame.Rect(300, 250, ARENA_W - 600, ARENA_H - 500)

# Tutut kasvot katsomossa + mitä he huutavat
CROWD_SHOUTS = [
    ("Marda", "Win and the first round's free!"),
    ("Marda", "I've got money on you, mudlark!"),
    ("Hamo", "Break their knees! Sell me the boots!"),
    ("Hamo", "Tails and glory! TAILS AND GLORY!"),
    ("Gus", "Show 'em Muckford grit!"),
    ("Bram", "Keep your shield UP, rookie!"),
    ("Sister Rhea", "Try not to bleed too much!"),
    (None, "MUCK-FORD! MUCK-FORD!"),
    (None, "For the Shanty Yard!"),
    (None, "I can't watch... tell me what happens!"),
    (None, "TWO FALLS! TAKE TWO FALLS!"),
    (None, "That's my neighbor down there!"),
]


class GrandSlamArena(BaseArena):
    def __init__(self, seed=77):
        super().__init__("Shanty Yard Grand Stage")
        self.width = ARENA_W
        self.height = ARENA_H
        self.floor_color = (36, 32, 30)
        self.rng = random.Random(seed)
        self.timer = 0

        # Montun seinät (aukot porteille itä/länsi-keskellä)
        gate_h = 150
        gy = PIT.centery - gate_h // 2
        walls = [
            (PIT.x - 20, PIT.y - 20, PIT.w + 40, 20),                    # ylä
            (PIT.x - 20, PIT.bottom, PIT.w + 40, 20),                    # ala
            (PIT.x - 20, PIT.y, 20, gy - PIT.y),                         # vasen ylä
            (PIT.x - 20, gy + gate_h, 20, PIT.bottom - gy - gate_h),     # vasen ala
            (PIT.right, PIT.y, 20, gy - PIT.y),                          # oikea ylä
            (PIT.right, gy + gate_h, 20, PIT.bottom - gy - gate_h),      # oikea ala
        ]
        for wx, wy, ww, wh in walls:
            self.obstacles.add(ArenaObstacle(wx, wy, ww, wh, 'wall'))

        # Joukkueiden spawn-pisteet (game_manager._position_units käyttää)
        self.spawn_points = {
            "left": (PIT.x + 90, PIT.centery - 150),
            "right": (PIT.right - 160, PIT.centery - 150),
        }
        # Porttien sisäänkäynnit walk-in-cinematiikkaa varten
        self.gate_left = (PIT.x - 60, PIT.centery)
        self.gate_right = (PIT.right + 60, PIT.centery)

        # Yleisön istumapaikat (deterministinen)
        self._seats = self._build_seats()
        self._base = None  # staattinen pohja (laiska)

        # Huudot: (teksti, x, y, ttl, väri)
        self.crowd_bubbles = []
        self._next_shout = 200

        # --- KIERROSTEN JUJUT ---
        self.twist = "none"
        self._debris = []          # {"x","y","timer","hit"}
        self._next_debris = 300
        self.fire_radius = 0.0     # 0 = ei rengasta
        self._fire_tick = 0
        self.flash_alpha = 0

    # ------------------------------------------------------------------
    def set_twist(self, round_no: int):
        self.twist = {1: "none", 2: "debris"}.get(int(round_no), "fire_ring")
        self._debris = []
        self._next_debris = 240
        if self.twist == "fire_ring":
            self.fire_radius = 720.0
        else:
            self.fire_radius = 0.0

    # ------------------------------------------------------------------
    def _build_seats(self):
        seats = []
        rng = random.Random(4242)
        # Ylä- ja alakatsomot: 3 porrasriviä
        for row in range(3):
            y_top = 190 - row * 52
            y_bot = PIT.bottom + 84 + row * 52
            for x in range(PIT.x - 100, PIT.right + 100, 34):
                if rng.random() < 0.86:
                    seats.append((x + rng.randint(-6, 6), y_top, row))
                if rng.random() < 0.86:
                    seats.append((x + rng.randint(-6, 6), y_bot, row))
        # Sivukatsomot
        for row in range(2):
            x_l = 170 - row * 60
            x_r = PIT.right + 150 + row * 60
            for y in range(PIT.y - 40, PIT.bottom + 40, 40):
                if rng.random() < 0.82:
                    seats.append((x_l, y + rng.randint(-6, 6), row))
                if rng.random() < 0.82:
                    seats.append((x_r, y + rng.randint(-6, 6), row))
        return seats

    def _build_base(self):
        base = pygame.Surface((self.width, self.height))
        base.fill((30, 27, 26))
        rng = random.Random(11)

        # Katsomoportaat (terassit)
        for i, shade in enumerate(((52, 44, 38), (60, 51, 43), (68, 58, 48))):
            m = 210 - i * 60
            pygame.draw.rect(base, shade, (PIT.x - m, PIT.y - m,
                                           PIT.w + m * 2, PIT.h + m * 2),
                             border_radius=40)
        # Montun reunamuuri
        pygame.draw.rect(base, (78, 66, 52), PIT.inflate(80, 80),
                         border_radius=26)
        pygame.draw.rect(base, (48, 40, 34), PIT.inflate(44, 44),
                         border_radius=20)

        # Hiekkalattia + tekstuuri
        pygame.draw.rect(base, (150, 126, 92), PIT, border_radius=14)
        for _ in range(900):
            x = rng.randint(PIT.x, PIT.right - 2)
            y = rng.randint(PIT.y, PIT.bottom - 2)
            c = rng.choice(((162, 138, 102), (140, 116, 84), (156, 132, 96)))
            base.fill(c, (x, y, rng.randint(2, 5), rng.randint(2, 4)))
        # Tummempaa kulunutta hiekkaa keskellä
        pygame.draw.ellipse(base, (142, 118, 86),
                            (PIT.centerx - 420, PIT.centery - 260, 840, 520))

        # Maalatut kehäviivat
        line = (216, 200, 168)
        pygame.draw.circle(base, line, PIT.center, 300, 3)
        pygame.draw.circle(base, line, PIT.center, 120, 2)
        pygame.draw.line(base, line, (PIT.centerx, PIT.y + 30),
                         (PIT.centerx, PIT.bottom - 30), 2)
        # Kulmamerkit
        for cx, cy in (PIT.topleft, PIT.topright, PIT.bottomleft,
                       PIT.bottomright):
            pygame.draw.circle(base, (128, 46, 40),
                               (cx + (30 if cx == PIT.x else -30),
                                cy + (30 if cy == PIT.y else -30)), 10)

        # Portit (itä/länsi): tummat käytävät + kehykset
        for gx, side in ((PIT.x - 90, 1), (PIT.right + 90, -1)):
            corridor = pygame.Rect(0, 0, 120, 170)
            corridor.center = (gx, PIT.centery)
            pygame.draw.rect(base, (20, 18, 18), corridor, border_radius=8)
            pygame.draw.rect(base, (96, 76, 52), corridor, 4, border_radius=8)

        # Lipputangot + viirit katsomoiden kulmiin ja keskikohtiin
        flag_cols = ((168, 52, 44), (206, 168, 84), (86, 118, 92))
        poles = [(PIT.x - 140, PIT.y - 150), (PIT.right + 140, PIT.y - 150),
                 (PIT.x - 140, PIT.bottom + 130),
                 (PIT.right + 140, PIT.bottom + 130),
                 (PIT.centerx, PIT.y - 190), (PIT.centerx, PIT.bottom + 170)]
        for i, (px, py) in enumerate(poles):
            pygame.draw.line(base, (70, 58, 44), (px, py), (px, py - 110), 6)
            col = flag_cols[i % len(flag_cols)]
            pygame.draw.polygon(base, col, [(px, py - 110), (px + 64, py - 96),
                                            (px, py - 82)])
            pygame.draw.polygon(base, (30, 24, 22),
                                [(px, py - 110), (px + 64, py - 96),
                                 (px, py - 82)], 1)
        # Suuri finaalibanneri yläkatsomon takana
        banner = pygame.Rect(PIT.centerx - 330, 8, 660, 64)
        pygame.draw.rect(base, (110, 38, 34), banner, border_radius=10)
        pygame.draw.rect(base, (206, 168, 84), banner, 3, border_radius=10)
        try:
            from ui_kit import font_main
            txt = font_main.render("GRAND SLAM FINAL - TIER 1 CHARTER",
                                   True, (238, 218, 160))
            base.blit(txt, (banner.centerx - txt.get_width() // 2,
                            banner.centery - txt.get_height() // 2))
        except Exception:
            pass
        return base

    # ------------------------------------------------------------------
    def update(self, all_units):
        self.timer += 1
        if self.flash_alpha > 0:
            self.flash_alpha -= 8

        # Yleisön huudot
        self._next_shout -= 1
        if self._next_shout <= 0:
            self._next_shout = self.rng.randint(170, 320)
            who, text = self.rng.choice(CROWD_SHOUTS)
            seat = self.rng.choice(self._seats)
            label = f"{who}: {text}" if who else text
            self.crowd_bubbles.append(
                [label, seat[0], seat[1] - 26, 170,
                 (250, 226, 160) if who else (222, 222, 226)])
            if self.rng.random() < 0.35:
                sound_system.play_sound(
                    f"cheering_{self.rng.randint(1, 4)}", volume=0.35)
        for b in self.crowd_bubbles:
            b[3] -= 1
        self.crowd_bubbles = [b for b in self.crowd_bubbles if b[3] > 0]

        # --- TWIST: CROWD DEBRIS ---
        if self.twist == "debris":
            self._next_debris -= 1
            if self._next_debris <= 0:
                self._next_debris = self.rng.randint(200, 330)
                self._debris.append({
                    "x": self.rng.randint(PIT.x + 90, PIT.right - 90),
                    "y": self.rng.randint(PIT.y + 90, PIT.bottom - 90),
                    "timer": 55, "hit": False,
                })
            for d in self._debris:
                d["timer"] -= 1
                if d["timer"] <= 0 and not d["hit"]:
                    d["hit"] = True
                    d["timer"] = -30  # raato näkyy hetken
                    sound_system.play_sound("mining_break", volume=0.7)
                    for u in all_units:
                        if getattr(u, "is_dead", False):
                            continue
                        dist = math.hypot(u.rect.centerx - d["x"],
                                          u.rect.centery - d["y"])
                        if dist < 80:
                            u.take_damage(12, "Physical")
            self._debris = [d for d in self._debris if d["timer"] > -30]

        # --- TWIST: FIRE RING (sudden death) ---
        if self.twist == "fire_ring" and self.fire_radius > 0:
            # Kutistuu ~3600 framessa (60 s) 720 -> 240
            self.fire_radius = max(240.0, self.fire_radius - 0.135)
            self._fire_tick += 1
            if self._fire_tick >= 30:
                self._fire_tick = 0
                for u in all_units:
                    if getattr(u, "is_dead", False):
                        continue
                    dist = math.hypot(u.rect.centerx - PIT.centerx,
                                      u.rect.centery - PIT.centery)
                    if dist > self.fire_radius:
                        u.take_damage(4, "Fire")

    def cheer(self, big=False):
        """Yleisö räjähtää (kutsutaan mm. kierroksen ratketessa)."""
        for _ in range(3 if big else 1):
            sound_system.play_sound(
                f"cheering_{self.rng.randint(1, 4)}",
                volume=0.8 if big else 0.5)
        if big:
            sound_system.play_sound("loop_clapping_1", volume=0.6)

    # ------------------------------------------------------------------
    def draw_background(self, screen, offset=(0, 0)):
        if self._base is None:
            self._base = self._build_base()
        ox, oy = int(offset[0]), int(offset[1])
        screen.blit(self._base, (-ox, -oy))

        # Animoitu yleisö (vain näkyvät istuimet)
        sw, sh = screen.get_size()
        t = self.timer * 0.08
        for i, (x, y, row) in enumerate(self._seats):
            sx, sy = x - ox, y - oy
            if not (-30 < sx < sw + 30 and -40 < sy < sh + 40):
                continue
            bob = math.sin(t + i * 0.7) * (2 + row)
            c = 46 + (i * 13) % 34
            col = (c + 14, c, c - 6)
            pygame.draw.rect(screen, col, (sx - 7, sy - 10 + bob, 14, 20),
                             border_radius=4)
            skin = (188 - (i * 7) % 60, 152 - (i * 5) % 50, 118)
            pygame.draw.circle(screen, skin, (int(sx), int(sy - 16 + bob)), 6)
            # Osa heiluttaa käsiä
            if i % 5 == 0:
                wave = math.sin(t * 1.6 + i) * 8
                pygame.draw.line(screen, col, (sx + 6, sy - 8 + bob),
                                 (sx + 13, sy - 20 + bob - wave), 3)

    def draw_foreground(self, screen, offset=(0, 0)):
        ox, oy = int(offset[0]), int(offset[1])

        # Soihdut montun reunamuurilla
        for fx in range(PIT.x, PIT.right + 1, 380):
            for fy in (PIT.y - 46, PIT.bottom + 44):
                sx, sy = fx - ox, fy - oy
                flick = math.sin(self.timer * 0.21 + fx * 0.01) * 3
                pygame.draw.line(screen, (70, 56, 42), (sx, sy + 18),
                                 (sx, sy - 6), 5)
                pygame.draw.circle(screen, (222, 116, 44),
                                   (sx, int(sy - 14 + flick)), 9)
                pygame.draw.circle(screen, (250, 190, 80),
                                   (sx, int(sy - 17 + flick)), 5)

        # --- DEBRIS: varoitusrinki + putoava laatikko ---
        for d in self._debris:
            sx, sy = d["x"] - ox, d["y"] - oy
            if d["timer"] > 0:
                pct = d["timer"] / 55.0
                r = 60
                ring = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(ring, (255, 80, 60, 90), (r, r), r, 3)
                pygame.draw.circle(ring, (255, 80, 60, 40), (r, r),
                                   int(r * (1 - pct)))
                screen.blit(ring, (sx - r, sy - r))
                # laatikko putoaa
                drop_y = sy - int(pct * 420)
                pygame.draw.rect(screen, (108, 82, 54),
                                 (sx - 16, drop_y - 16, 32, 32))
                pygame.draw.rect(screen, (60, 44, 30),
                                 (sx - 16, drop_y - 16, 32, 32), 2)
            else:
                # sirpaleet
                pygame.draw.circle(screen, (96, 74, 50), (sx, sy), 14)
                pygame.draw.circle(screen, (70, 54, 38), (sx, sy), 14, 2)

        # --- FIRE RING ---
        if self.twist == "fire_ring" and self.fire_radius > 0:
            r = int(self.fire_radius)
            cx, cy = PIT.centerx - ox, PIT.centery - oy
            pts = 64
            for k in range(pts):
                a = k * math.tau / pts + self.timer * 0.01
                fx = cx + math.cos(a) * r
                fy = cy + math.sin(a) * r
                h = 8 + math.sin(self.timer * 0.3 + k) * 5
                pygame.draw.line(screen, (232, 110, 40), (fx, fy),
                                 (fx, fy - h), 3)
                pygame.draw.line(screen, (255, 190, 90), (fx, fy),
                                 (fx, fy - h * 0.55), 1)

        # Yleisön huudot
        try:
            from ui_kit import font_small
            for text, x, y, ttl, col in self.crowd_bubbles:
                sx, sy = x - ox, y - oy
                if -220 < sx < screen.get_width() + 40 and -40 < sy < screen.get_height() + 40:
                    alpha_col = col if ttl > 30 else (140, 140, 140)
                    surf = font_small.render(text, True, alpha_col)
                    bg = pygame.Surface((surf.get_width() + 10,
                                         surf.get_height() + 4),
                                        pygame.SRCALPHA)
                    bg.fill((12, 12, 16, 150))
                    screen.blit(bg, (sx - 5, sy - 2))
                    screen.blit(surf, (sx, sy))
        except Exception:
            pass

        if self.flash_alpha > 0:
            flash = pygame.Surface(screen.get_size())
            flash.fill((255, 244, 214))
            flash.set_alpha(self.flash_alpha)
            screen.blit(flash, (0, 0))
