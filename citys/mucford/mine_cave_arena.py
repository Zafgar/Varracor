# citys/mucford/mine_cave_arena.py
"""
Kaivoksen sisäosa: pimeä luola, jossa enemmän rautaa, hiiltä ja
syvemmällä rubiinisuoni. Grafiikka on proseduraalista placeholderia -
viralliset kuvat korvaavat ne kun ne lisätään (ks. MISSING_ASSETS.md).
"""
import random
import pygame

from vfx import VFXManager
from crafting.ores.iron_ore import IronOre


class CoalDeposit(IronOre):
    """Hiiliesiintymä: sama louhintalogiikka, eri resurssi ja ulkonäkö."""

    def __init__(self, x, y):
        super().__init__(x, y)
        self.name = "Coal Deposit"
        self.resource_name = "Coal"
        self.max_hits = random.randint(2, 4)
        self.current_hits = self.max_hits
        self._make_images((30, 28, 26), (60, 58, 55))

    def _make_images(self, dark, light):
        # Proseduraalinen kivi + kiiltävät sirut
        for key in ("full", "hit", "empty"):
            s = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.polygon(s, dark, [
                (8, 48), (4, 26), (18, 10), (42, 8), (56, 30), (50, 50)])
            if key != "empty":
                for _ in range(6):
                    px, py = random.randint(14, 46), random.randint(16, 42)
                    pygame.draw.circle(s, light, (px, py), 3)
            if key == "hit":
                pygame.draw.polygon(s, (255, 240, 200), [
                    (8, 48), (4, 26), (18, 10)], 2)
            self.sprites[key] = s
        self.image = self.sprites["full"]


class RubyVein(IronOre):
    """Rubiinisuoni syvällä luolassa: vähän osumia, arvokas droppi."""

    def __init__(self, x, y):
        super().__init__(x, y)
        self.name = "Ruby Vein"
        self.resource_name = "Chipped Ruby"
        self.max_hits = 2
        self.current_hits = self.max_hits
        self._make_images()

    def _make_images(self):
        for key in ("full", "hit", "empty"):
            s = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.polygon(s, (70, 60, 65), [
                (8, 50), (4, 28), (20, 10), (44, 8), (56, 32), (48, 52)])
            if key != "empty":
                # Hehkuvat rubiinikiteet
                for cx, cy, r in [(24, 30, 6), (38, 24, 5), (32, 42, 4)]:
                    pygame.draw.polygon(s, (200, 40, 60), [
                        (cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)])
                    pygame.draw.polygon(s, (255, 120, 140), [
                        (cx, cy - r), (cx + r, cy), (cx, cy)], 0)
            self.sprites[key] = s
        self.image = self.sprites["full"]


class _CavePillar(pygame.sprite.Sprite):
    """Luolan kivipylväs (este)."""

    def __init__(self, x, y):
        super().__init__()
        self.is_structure = True
        self.type = "wall"
        self.name = "Structure"
        self.has_shadow = False
        w, h = random.randint(60, 100), random.randint(90, 150)
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        base = random.randint(45, 60)
        pygame.draw.ellipse(self.image, (base, base - 4, base - 8), (0, h - 40, w, 40))
        pygame.draw.rect(self.image, (base + 8, base + 3, base - 2),
                         (w * 0.15, 10, w * 0.7, h - 35), border_radius=12)
        pygame.draw.ellipse(self.image, (base + 16, base + 10, base + 4), (w * 0.1, 0, w * 0.8, 30))
        self.rect = pygame.Rect(x, y + h - 35, w * 0.8, 30)
        self.image_pos = (x, y)

    def draw_on_screen(self, surface, offset=(0, 0)):
        surface.blit(self.image, (self.image_pos[0] - offset[0],
                                  self.image_pos[1] - offset[1]))


class MineCaveArena:
    def __init__(self):
        self.width = 2200
        self.height = 1300
        self.props = []
        self.obstacles = []
        self.floor_props = []
        self.vfx = VFXManager()
        self.ore_nodes = []

        self.floor_image = pygame.Surface((self.width, self.height))
        self._generate_floor()
        self._build_level()

    def _generate_floor(self):
        # Tumma luolan lattia
        self.floor_image.fill((38, 34, 32))
        for _ in range(700):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            shade = random.randint(-8, 10)
            pygame.draw.circle(self.floor_image,
                               (38 + shade, 34 + shade, 32 + shade),
                               (x, y), random.randint(8, 34))
        # Sisäänkäynnin valo vasemmalla
        for r in range(200, 40, -20):
            a = int(90 * (1 - r / 200))
            pygame.draw.circle(self.floor_image, (60 + a // 2, 56 + a // 2, 50 + a // 3),
                               (60, self.height // 2), r)

    def _build_level(self):
        w, h = self.width, self.height
        self.obstacles.append(pygame.Rect(0, -40, w, 40))
        self.obstacles.append(pygame.Rect(0, h, w, 40))
        self.obstacles.append(pygame.Rect(-40, 0, 40, h))
        self.obstacles.append(pygame.Rect(w, 0, 40, h))

        for _ in range(14):
            x = random.randint(200, w - 300)
            y = random.randint(80, h - 200)
            # Jätä kulkuväylä keskelle sisäänkäynniltä
            if abs(y - h // 2) < 130 and x < 700:
                continue
            self._add_prop(_CavePillar(x, y))

        self.spawn_ores()

    def spawn_ores(self):
        for node in self.ore_nodes:
            if node in self.props:
                self.props.remove(node)
        self.ore_nodes = []

        w, h = self.width, self.height

        def place(cls, count, x_min, x_max):
            for _ in range(count):
                for _attempt in range(12):
                    x = random.randint(x_min, x_max)
                    y = random.randint(120, h - 160)
                    if all(abs(x - n.rect.x) > 90 or abs(y - n.rect.y) > 90
                           for n in self.ore_nodes):
                        break
                node = cls(x, y)
                self.ore_nodes.append(node)
                self.props.append(node)

        place(IronOre, 8, 400, w - 500)       # rautaa ympäri luolaa
        place(CoalDeposit, 4, 500, w - 400)   # hiiltä sulattoa varten
        place(RubyVein, 2, w - 450, w - 150)  # rubiinit syvimmällä

    def _add_prop(self, prop):
        self.props.append(prop)
        if getattr(prop, "is_structure", False):
            self.obstacles.append(prop)

    def update(self, manager=None):
        self.vfx.update(manager)
        for p in self.props:
            if hasattr(p, "update"):
                p.update(manager=manager)

    def draw_background(self, screen, offset=(0, 0)):
        screen.blit(self.floor_image, (-offset[0], -offset[1]))

    def draw_foreground(self, screen, offset=(0, 0)):
        self.vfx.draw_top(screen, offset)
