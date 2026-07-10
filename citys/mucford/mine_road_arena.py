# citys/mucford/mine_road_arena.py
"""
Kaivostie: kivinen polku Muckfordista itään vanhalle kaivokselle.
Epäkuolleet ovat vallanneet tien - reitti pitää raivata päästäkseen
louhimaan. Malmit ja epäkuolleet palautuvat päivittäin (WorldClock).
"""
import random
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from vfx import VFXManager
from crafting.ores.iron_ore import IronOre


class _Rock(pygame.sprite.Sprite):
    """Yksinkertainen kivipaasi (este)."""

    def __init__(self, x, y, size):
        super().__init__()
        self.is_structure = True
        self.type = "wall"
        self.name = "Structure"
        self.has_shadow = False
        s = int(size)
        self.image = pygame.Surface((s, s), pygame.SRCALPHA)
        base = random.randint(70, 95)
        col = (base, base - 5, base - 10)
        pygame.draw.polygon(self.image, col, [
            (s * 0.1, s * 0.8), (s * 0.05, s * 0.45), (s * 0.3, s * 0.15),
            (s * 0.7, s * 0.1), (s * 0.95, s * 0.5), (s * 0.85, s * 0.85),
        ])
        pygame.draw.polygon(self.image, (base + 25, base + 20, base + 15), [
            (s * 0.3, s * 0.15), (s * 0.7, s * 0.1), (s * 0.6, s * 0.4),
            (s * 0.35, s * 0.45),
        ])
        # Törmäys vain kiven "jalkoihin"
        self.rect = pygame.Rect(x, y + s * 0.55, s * 0.9, s * 0.4)
        self.image_pos = (x, y)

    def draw_on_screen(self, surface, offset=(0, 0)):
        surface.blit(self.image, (self.image_pos[0] - offset[0],
                                  self.image_pos[1] - offset[1]))


class MineRoadArena:
    def __init__(self):
        self.width = 2600
        self.height = 1100
        self.props = []
        self.obstacles = []
        self.floor_props = []
        self.vfx = VFXManager()
        self.ore_nodes = []

        self.floor_image = pygame.Surface((self.width, self.height))
        self._generate_floor()
        self._build_level()

    def _generate_floor(self):
        # Kivinen, kulunut tie: ruskeanharmaa pohja + tummempia laikkuja
        self.floor_image.fill((88, 78, 64))
        for _ in range(900):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            r = random.randint(6, 40)
            shade = random.randint(-14, 10)
            col = (88 + shade, 78 + shade, 64 + shade)
            pygame.draw.circle(self.floor_image, col, (x, y), r)
        # Polku keskellä (vaaleampi ura vasemmalta oikealle)
        path_y = self.height // 2
        for x in range(0, self.width, 8):
            wob = int(40 * random.uniform(-1, 1))
            pygame.draw.circle(self.floor_image, (112, 100, 80),
                               (x, path_y + wob), random.randint(28, 44))
        # Kaivoksen suuaukko oikeaan päähän (tumma aukko + kehys)
        mouth_x = self.width - 220
        mouth_y = path_y
        pygame.draw.ellipse(self.floor_image, (25, 22, 20),
                            (mouth_x - 80, mouth_y - 140, 260, 280))
        pygame.draw.ellipse(self.floor_image, (55, 48, 42),
                            (mouth_x - 90, mouth_y - 150, 280, 300), 12)

    def _build_level(self):
        w, h = self.width, self.height

        # Reunat (näkymättömät seinät raakoina Rect-esteinä)
        self.obstacles.append(pygame.Rect(0, -40, w, 40))        # ylä
        self.obstacles.append(pygame.Rect(0, h, w, 40))          # ala
        self.obstacles.append(pygame.Rect(-40, 0, 40, h))        # vasen
        self.obstacles.append(pygame.Rect(w, 0, 40, h))          # oikea

        # Kivipaasia tien varrelle (ei polun päälle)
        path_y = h // 2
        for _ in range(26):
            x = random.randint(100, w - 300)
            y = random.choice([random.randint(40, path_y - 220),
                               random.randint(path_y + 160, h - 120)])
            rock = _Rock(x, y, random.randint(50, 130))
            self._add_prop(rock)

        # Malmiesiintymät kaivoksen suulle ja rinteille
        self.spawn_ores()

    def spawn_ores(self):
        """Luo (tai palauttaa) malmit. Kutsutaan päivän vaihtuessa."""
        # Poista vanhat
        for node in self.ore_nodes:
            if node in self.props:
                self.props.remove(node)
        self.ore_nodes = []

        path_y = self.height // 2
        mouth_x = self.width - 260
        spots = [
            (mouth_x - 120, path_y - 200), (mouth_x + 40, path_y - 160),
            (mouth_x - 60, path_y + 140), (mouth_x + 60, path_y + 190),
            (mouth_x - 220, path_y + 60), (mouth_x - 320, path_y - 120),
        ]
        for sx, sy in spots:
            node = IronOre(sx + random.randint(-20, 20), sy + random.randint(-15, 15))
            self.ore_nodes.append(node)
            self.props.append(node)

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
