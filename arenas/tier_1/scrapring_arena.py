"""The Scrapring - Rattlebridgen Tier 1 -areena (The Scrapring Circuit).

Sera Quenchin näytösareena rakennettu vanhan sillan koneistoon. Kolme
lore-vaaraa, jotka tekevät Tier 1:stä mekaanisesti erilaisen kuin Tier 0:

- Crushing Gears  : jättirattaat jotka telegrafoivat ja sitten iskeytyvät
                    kiinni - raskas fyysinen isku + lyhyt stun ruudussa.
- Steam Bursts    : höyryventtiilit sihisevät ja purkautuvat - vahinko +
                    Burn venttiilin päällä seisoville.
- Magnet Plates   : magneettilaatat hidastavat metallihaarniskaa (heavy)
                    kantavia - Slow niin kauan kuin seisot laatalla.

Kaikki vaaramekaniikka ajetaan update(all_units):ssa (headless-testattava);
piirto on erillään eikä vaikuta logiikkaan.
"""
import math
import pygame
import random
from settings import *
from arenas.base_arena import BaseArena, ArenaObstacle


# Vaiheiden kestot (frameina, 60 fps)
_GEAR_OPEN = 150       # rattaat auki (turvallista)
_GEAR_WARN = 45        # varoitus (telegraph) ennen iskua
_GEAR_SLAM = 24        # isku aktiivinen
_STEAM_IDLE = 130      # venttiili lepää
_STEAM_HISS = 40       # sihinä (telegraph)
_STEAM_BURST = 30      # purkaus aktiivinen


class _Gear:
    def __init__(self, x, y, r):
        self.rect = pygame.Rect(x - r, y - r, r * 2, r * 2)
        self.cx, self.cy, self.r = x, y, r
        self.timer = random.randint(0, _GEAR_OPEN)
        self.phase = "open"
        self.angle = random.uniform(0, 360)

    @property
    def slamming(self):
        return self.phase == "slam"

    def step(self):
        self.angle = (self.angle + 3) % 360
        self.timer -= 1
        if self.timer <= 0:
            if self.phase == "open":
                self.phase, self.timer = "warn", _GEAR_WARN
            elif self.phase == "warn":
                self.phase, self.timer = "slam", _GEAR_SLAM
            else:
                self.phase, self.timer = "open", _GEAR_OPEN


class _Steam:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.timer = random.randint(0, _STEAM_IDLE)
        self.phase = "idle"

    @property
    def bursting(self):
        return self.phase == "burst"

    def step(self):
        self.timer -= 1
        if self.timer <= 0:
            if self.phase == "idle":
                self.phase, self.timer = "hiss", _STEAM_HISS
            elif self.phase == "hiss":
                self.phase, self.timer = "burst", _STEAM_BURST
            else:
                self.phase, self.timer = "idle", _STEAM_IDLE


class ScrapringArena(BaseArena):
    def __init__(self):
        super().__init__("The Scrapring")
        self.floor_color = (46, 42, 38)  # öljyinen metallilattia
        self.player_hazard_hits = 0     # sponsor-objectivet seuraavat tätä
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT

        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

        # --- Crushing Gears (kaksi paria sivuilla) ---
        gr = max(46, int(min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.05))
        self.gears = [
            _Gear(int(SCREEN_WIDTH * 0.28), int(SCREEN_HEIGHT * 0.32), gr),
            _Gear(int(SCREEN_WIDTH * 0.72), int(SCREEN_HEIGHT * 0.68), gr),
            _Gear(int(SCREEN_WIDTH * 0.72), int(SCREEN_HEIGHT * 0.32), gr),
            _Gear(int(SCREEN_WIDTH * 0.28), int(SCREEN_HEIGHT * 0.68), gr),
        ]

        # --- Steam Bursts (keskilinjan venttiilit) ---
        sw, sh = 70, 70
        self.steam_vents = [
            _Steam(cx - sw // 2, int(SCREEN_HEIGHT * 0.22), sw, sh),
            _Steam(cx - sw // 2, int(SCREEN_HEIGHT * 0.70), sw, sh),
        ]

        # --- Magnet Plates (metallia hidastavat laatat) ---
        pw, ph = 150, 110
        self.magnet_plates = [
            pygame.Rect(cx - pw // 2, cy - ph // 2, pw, ph),
            pygame.Rect(int(SCREEN_WIDTH * 0.16), cy - ph // 2, pw, ph),
            pygame.Rect(int(SCREEN_WIDTH * 0.84) - pw, cy - ph // 2, pw, ph),
        ]

        # --- Scrap-kasat (SUOJAT: estävät myös ammukset) ---
        # Hazard-areenakin tarvitsee katveita, jotta ranged ei dominoi.
        self.scrap_cover = [
            pygame.Rect(int(SCREEN_WIDTH * 0.42), int(SCREEN_HEIGHT * 0.30), 110, 64),
            pygame.Rect(int(SCREEN_WIDTH * 0.52), int(SCREEN_HEIGHT * 0.62), 110, 64),
            pygame.Rect(int(SCREEN_WIDTH * 0.14), int(SCREEN_HEIGHT * 0.24), 80, 60),
            pygame.Rect(int(SCREEN_WIDTH * 0.82), int(SCREEN_HEIGHT * 0.70), 80, 60),
        ]
        for r in self.scrap_cover:
            self.obstacles.add(ArenaObstacle(r.x, r.y, r.w, r.h, "wall"))

        self._build_walls()

    def _build_walls(self):
        wall_thick = 100
        pad = 60
        self.obstacles.add(ArenaObstacle(-wall_thick, -wall_thick,
                                         SCREEN_WIDTH + wall_thick * 2, pad + wall_thick, "wall"))
        self.obstacles.add(ArenaObstacle(-wall_thick, SCREEN_HEIGHT - pad,
                                         SCREEN_WIDTH + wall_thick * 2, pad + wall_thick, "wall"))
        self.obstacles.add(ArenaObstacle(-wall_thick, 0, pad + wall_thick, SCREEN_HEIGHT, "wall"))
        self.obstacles.add(ArenaObstacle(SCREEN_WIDTH - pad, 0, pad + wall_thick, SCREEN_HEIGHT, "wall"))

    # ---------------------------------------------------------------
    # HAZARD LOGIC (headless-testattava)
    # ---------------------------------------------------------------
    @staticmethod
    def _is_metal_armored(unit):
        """Kantaako yksikkö raskasta (metalli)haarniskaa?"""
        armor = getattr(unit, "armor", None)
        if armor is None:
            return False
        fn = getattr(unit, "_armor_group_from_item", None)
        if callable(fn):
            try:
                return fn(armor) == "heavy"
            except Exception:
                pass
        return "heavy" in str(getattr(armor, "armor_group", "")).lower()

    def _count_hazard_hit(self, unit):
        """Sponsor-objectivet (Hazard Dance) laskevat pelaajan osumat."""
        if getattr(unit, "team_color", None) == PLAYER_TEAM:
            self.player_hazard_hits = getattr(self, "player_hazard_hits", 0) + 1

    def _sidestep(self, unit, cx, cy, speed=3.4):
        """Siirtää yksikköä poispäin vaaran keskipisteestä (esteet väistäen).

        Arena Instincts -kyvyn (hazard_sense) väistörefleksi: AI-ohjatut
        taistelijat lukevat telegraph-vaiheen ja astuvat sivuun ilman
        pelaajan mikroa - automaattimatsit (1v1/3v3/5v5) hyötyvät samasta
        kehityksestä kuin sankarilla pelatut.
        """
        dx = unit.rect.centerx - cx
        dy = unit.rect.centery - cy
        distance = math.hypot(dx, dy)
        if distance < 1:
            dx, dy, distance = 1.0, 0.0, 1.0
        step_x = int(round(dx / distance * speed)) or (1 if dx >= 0 else -1)
        step_y = int(round(dy / distance * speed))
        moved = unit.rect.move(step_x, step_y)
        for obstacle in self.obstacles:
            rect = getattr(obstacle, "rect", obstacle)
            if moved.colliderect(rect):
                return
        unit.rect = moved

    def _apply_hazard_awareness(self, units):
        """Hazard sense -yksiköt väistävät telegraphattuja vaaroja."""
        for u in units:
            sense = int(getattr(u, "hazard_sense", 0))
            if sense <= 0:
                continue
            for g in self.gears:
                if g.phase in ("warn", "slam") and u.rect.colliderect(g.rect.inflate(34, 34)):
                    self._sidestep(u, g.cx, g.cy)
            for s in self.steam_vents:
                if s.phase in ("hiss", "burst") and u.rect.colliderect(s.rect.inflate(24, 24)):
                    self._sidestep(u, s.rect.centerx, s.rect.centery)
            if sense >= 2 and self._is_metal_armored(u):
                for plate in self.magnet_plates:
                    if u.rect.colliderect(plate):
                        self._sidestep(u, plate.centerx, plate.centery, speed=1.6)

    def update(self, all_units):
        for g in self.gears:
            g.step()
        for s in self.steam_vents:
            s.step()

        units = [u for u in (all_units or []) if not getattr(u, "is_dead", False)]
        self._apply_hazard_awareness(units)

        # Crushing gears: iskun aikana ruudussa olevat murskautuvat
        for g in self.gears:
            if not g.slamming:
                continue
            for u in units:
                if u.rect.colliderect(g.rect):
                    u.take_damage(14, "Physical")
                    if getattr(u, "stun_timer", 0) < 20:
                        u.stun_timer = 20
                    self._count_hazard_hit(u)

        # Steam bursts: purkauksen aikana venttiilin päällä palaa
        for s in self.steam_vents:
            if not s.bursting:
                continue
            for u in units:
                if u.rect.colliderect(s.rect):
                    u.take_damage(6, "Fire")
                    u.apply_status("Burn", 90, 2)
                    self._count_hazard_hit(u)

        # Magnet plates: metallihaarniska juuttuu (Slow niin kauan kuin päällä)
        for plate in self.magnet_plates:
            for u in units:
                if u.rect.colliderect(plate) and self._is_metal_armored(u):
                    u.apply_status("Slow", 40)

    # ---------------------------------------------------------------
    # DRAW
    # ---------------------------------------------------------------
    def draw_background(self, screen):
        pygame.draw.rect(screen, self.floor_color, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        # Magneettilaatat (himmeät siniset)
        for plate in self.magnet_plates:
            pygame.draw.rect(screen, (44, 60, 82), plate, border_radius=8)
            pygame.draw.rect(screen, (70, 100, 140), plate, 3, border_radius=8)
            for gx in range(plate.left + 14, plate.right - 8, 22):
                pygame.draw.line(screen, (60, 84, 116), (gx, plate.top + 6), (gx, plate.bottom - 6), 1)
        # Öljytahroja
        for _ in range(3):
            x = random.randint(80, SCREEN_WIDTH - 80)
            y = random.randint(80, SCREEN_HEIGHT - 80)
            pygame.draw.circle(screen, (34, 32, 30), (x, y), random.randint(8, 20))

    def draw_foreground(self, screen):
        super().draw_foreground(screen)
        # Scrap-kasat (suojat): ruosteinen romuröykkiö
        for r in getattr(self, "scrap_cover", []):
            pygame.draw.rect(screen, (26, 24, 22), r.move(3, 4), border_radius=8)
            pygame.draw.rect(screen, (86, 72, 58), r, border_radius=8)
            pygame.draw.rect(screen, (48, 42, 38), r, 3, border_radius=8)
            rng = random.Random(r.x)
            for _ in range(5):
                px = rng.randint(r.x + 8, r.right - 20)
                py = rng.randint(r.y + 6, r.bottom - 16)
                pygame.draw.rect(screen, rng.choice(((108, 84, 52), (70, 64, 60), (120, 96, 64))),
                                 (px, py, rng.randint(10, 20), rng.randint(6, 12)),
                                 border_radius=3)
        # Steam-venttiilit
        for s in self.steam_vents:
            base = (70, 70, 78)
            pygame.draw.rect(screen, base, s.rect, border_radius=6)
            pygame.draw.rect(screen, (40, 40, 46), s.rect, 3, border_radius=6)
            if s.phase == "hiss":
                pygame.draw.rect(screen, (200, 200, 210), s.rect, 2, border_radius=6)
            elif s.bursting:
                steam = pygame.Surface((s.rect.w, s.rect.h + 60), pygame.SRCALPHA)
                for _ in range(18):
                    sx = random.randint(0, s.rect.w)
                    sy = random.randint(0, s.rect.h + 50)
                    pygame.draw.circle(steam, (230, 230, 235, 120), (sx, sy), random.randint(4, 10))
                screen.blit(steam, (s.rect.x, s.rect.y - 50))
        # Rattaat
        for g in self.gears:
            self._draw_gear(screen, g)

    def _draw_gear(self, screen, g):
        if g.phase == "warn":
            col = (150, 110, 60)
        elif g.slamming:
            col = (200, 70, 50)
        else:
            col = (90, 90, 100)
        pygame.draw.circle(screen, col, (g.cx, g.cy), g.r)
        pygame.draw.circle(screen, (40, 40, 46), (g.cx, g.cy), g.r, 4)
        # Hampaat
        for k in range(8):
            a = math.radians(g.angle + k * 45)
            tx = g.cx + int(math.cos(a) * (g.r + 6))
            ty = g.cy + int(math.sin(a) * (g.r + 6))
            pygame.draw.circle(screen, col, (tx, ty), 6)
        pygame.draw.circle(screen, (30, 30, 34), (g.cx, g.cy), max(6, g.r // 4))
