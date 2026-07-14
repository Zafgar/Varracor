# citys/mucford/barracks_interior_arena.py
"""Team Barracksin sisätila: pelaajan ja gladiaattorien koti.

Taso 1 on ränsistynyt parakki (romua, halkeamia, kylmä takka, 6 punkkaa).
Kehittyy pelaajan panostuksella: taso 2 (8 punkkaa, palava takka, matto),
taso 3 (10 punkkaa, liput, palkintohylly, harjoittelunukke).

Grafiikka on koodipiirrettyä placeholderia; oikeat kuvat pudotetaan
assets-polkuihin (ks. MISSING_ASSETS.md) ja Prop lataa ne jos löytyvät.
"""
import random

import pygame

from assets.tiles.prop import Prop
from vfx import VFXManager

# Makuupaikat tasoittain: rajaa myös tiimin koon (Commander vie yhden punkan)
BUNKS_PER_LEVEL = {1: 6, 2: 8, 3: 10}

# Seuraavan tason hinta: kulta (SP) + materiaalit reppuun kerättynä
UPGRADE_COSTS = {
    2: {"gold": 400, "Swamp Wood": 15, "Stone": 10},
    3: {"gold": 1200, "Swamp Wood": 30, "Iron Bar": 8},
}

LEVEL_NAMES = {1: "Leaky Shack", 2: "Proper Quarters", 3: "Champions' Hall"}

WALL = 48          # seinän paksuus
DOOR_W = 160       # oviaukon leveys alaseinässä


class _Furniture(Prop):
    """Sisäkaluste: piirretään koodilla, kuva voi korvata polusta."""

    def __init__(self, x, y, w, h, img_path=None, collision_rect=None):
        super().__init__(x, y, w, h, img_path=img_path,
                         collision_rect=collision_rect)
        self.has_shadow = False


class Bunk(_Furniture):
    """Punkka. quality: 1 = risainen, 2 = siisti, 3 = komea."""

    def __init__(self, x, y, quality=1, occupied_name=""):
        super().__init__(x, y, 84, 150,
                         img_path=f"assets/tiles/barracks/bunk_q{quality}.png",
                         collision_rect=pygame.Rect(x, y + 40, 84, 110))
        self.quality = quality
        self.occupant_name = occupied_name
        self.interaction_range = 90
        self.interaction_label = "Sleep"
        # Placeholder vain jos oikeaa kuvaa ei löytynyt (Prop täyttää harmaalla)
        if self.image.get_at((0, 0)) == (100, 100, 100, 255):
            self._draw_placeholder(quality)

    def _draw_placeholder(self, q):
        s = pygame.Surface((84, 150), pygame.SRCALPHA)
        frame = (86, 64, 40) if q == 1 else (110, 80, 48) if q == 2 else (128, 96, 52)
        blanket = (96, 78, 66) if q == 1 else (86, 104, 66) if q == 2 else (120, 84, 96)
        # Runko
        pygame.draw.rect(s, frame, (0, 6, 84, 138), border_radius=8)
        pygame.draw.rect(s, (30, 22, 16), (0, 6, 84, 138), 3, border_radius=8)
        # Patja + peitto
        pygame.draw.rect(s, (172, 158, 128), (8, 14, 68, 122), border_radius=6)
        pygame.draw.rect(s, blanket, (8, 62, 68, 74), border_radius=6)
        # Tyyny
        pygame.draw.ellipse(s, (214, 206, 182), (18, 20, 48, 30))
        if q == 1:
            # Paikatut reiät + oljenkorsia
            pygame.draw.circle(s, (70, 58, 50), (30, 92), 7)
            pygame.draw.circle(s, (70, 58, 50), (58, 116), 6)
            for i in range(4):
                pygame.draw.line(s, (150, 130, 70), (10 + i * 6, 140),
                                 (14 + i * 6, 148), 2)
        elif q == 3:
            # Koristereunus
            pygame.draw.rect(s, (196, 164, 90), (8, 62, 68, 74), 2,
                             border_radius=6)
        self.image = s


class LongTable(_Furniture):
    def __init__(self, x, y, quality=1):
        super().__init__(x, y, 320, 130,
                         img_path="assets/tiles/barracks/long_table.png",
                         collision_rect=pygame.Rect(x + 10, y + 40, 300, 70))
        if self.image.get_at((0, 0)) == (100, 100, 100, 255):
            s = pygame.Surface((320, 130), pygame.SRCALPHA)
            top = (118, 88, 54) if quality > 1 else (98, 76, 50)
            pygame.draw.rect(s, top, (10, 34, 300, 62), border_radius=10)
            pygame.draw.rect(s, (40, 28, 18), (10, 34, 300, 62), 3, border_radius=10)
            for lx in (30, 286):
                pygame.draw.rect(s, (60, 44, 28), (lx, 92, 14, 34))
            # Penkit ylä + ala
            for by in (8, 104):
                pygame.draw.rect(s, (88, 66, 42), (40, by, 240, 18), border_radius=6)
            if quality > 1:
                # Kynttilä + muki
                pygame.draw.rect(s, (220, 210, 170), (150, 24, 8, 14))
                pygame.draw.circle(s, (255, 200, 90), (154, 20), 5)
                pygame.draw.rect(s, (150, 150, 160), (200, 40, 16, 14), border_radius=3)
            self.image = s


class Hearth(_Furniture):
    """Takka länsiseinällä. Palaa vain tasolla 2+."""

    def __init__(self, x, y, lit=False):
        super().__init__(x, y, 120, 150,
                         img_path="assets/tiles/barracks/hearth.png",
                         collision_rect=pygame.Rect(x, y + 60, 120, 90))
        self.lit = lit
        self._flame_seed = random.random() * 10
        if self.image.get_at((0, 0)) == (100, 100, 100, 255):
            s = pygame.Surface((120, 150), pygame.SRCALPHA)
            pygame.draw.rect(s, (92, 88, 84), (0, 20, 120, 130), border_radius=6)
            pygame.draw.rect(s, (60, 56, 54), (0, 20, 120, 130), 4, border_radius=6)
            # Kivikuvio
            for row in range(4):
                for col in range(3):
                    rx = 8 + col * 36 + (18 if row % 2 else 0)
                    pygame.draw.rect(s, (78, 74, 70),
                                     (rx % 104, 30 + row * 28, 32, 22),
                                     1, border_radius=4)
            # Pesä
            pygame.draw.rect(s, (24, 20, 18), (26, 76, 68, 62), border_radius=8)
            if not lit:
                # Kylmä tuhka
                pygame.draw.ellipse(s, (70, 66, 62), (36, 116, 48, 16))
            self.image = s

    def flame_rect(self):
        return pygame.Rect(self.image_pos[0] + 26, self.image_pos[1] + 76, 68, 62)


class CommanderDesk(_Furniture):
    """Komentajan pöytä: avaa tiiminhallinnan (roster/varusteet)."""

    def __init__(self, x, y):
        super().__init__(x, y, 170, 120,
                         img_path="assets/tiles/barracks/desk.png",
                         collision_rect=pygame.Rect(x, y + 34, 170, 80))
        self.interaction_range = 110
        self.interaction_label = "Team ledger"
        if self.image.get_at((0, 0)) == (100, 100, 100, 255):
            s = pygame.Surface((170, 120), pygame.SRCALPHA)
            pygame.draw.rect(s, (104, 78, 48), (0, 30, 170, 70), border_radius=8)
            pygame.draw.rect(s, (44, 32, 20), (0, 30, 170, 70), 3, border_radius=8)
            # Paperit + kynä + kirja
            pygame.draw.rect(s, (222, 214, 190), (16, 42, 52, 36))
            pygame.draw.rect(s, (210, 200, 170), (24, 38, 52, 36))
            pygame.draw.line(s, (60, 50, 40), (34, 48), (64, 60), 2)
            pygame.draw.rect(s, (110, 46, 40), (100, 44, 46, 30), border_radius=4)
            pygame.draw.rect(s, (196, 164, 90), (100, 44, 46, 30), 2, border_radius=4)
            self.image = s


class PlansBoard(_Furniture):
    """Rakennussuunnitelmat: barracksin kehityspaneeli."""

    def __init__(self, x, y):
        super().__init__(x, y, 110, 130,
                         img_path="assets/tiles/barracks/plans_board.png",
                         collision_rect=pygame.Rect(x + 10, y + 90, 90, 36))
        self.interaction_range = 110
        self.interaction_label = "Upgrade plans"
        if self.image.get_at((0, 0)) == (100, 100, 100, 255):
            s = pygame.Surface((110, 130), pygame.SRCALPHA)
            # Jalusta + taulu
            pygame.draw.rect(s, (80, 60, 40), (50, 90, 10, 40))
            pygame.draw.rect(s, (96, 74, 48), (5, 8, 100, 86), border_radius=6)
            pygame.draw.rect(s, (216, 206, 180), (13, 16, 84, 70))
            # Pohjapiirros
            pygame.draw.rect(s, (90, 90, 120), (20, 24, 44, 30), 2)
            pygame.draw.rect(s, (90, 90, 120), (52, 40, 36, 36), 2)
            pygame.draw.line(s, (160, 60, 50), (24, 66), (88, 30), 2)
            self.image = s


class TrainingDummy(_Furniture):
    """Harjoittelunukke (taso 3)."""

    def __init__(self, x, y):
        super().__init__(x, y, 70, 120,
                         img_path="assets/tiles/barracks/training_dummy.png",
                         collision_rect=pygame.Rect(x + 15, y + 70, 40, 46))
        if self.image.get_at((0, 0)) == (100, 100, 100, 255):
            s = pygame.Surface((70, 120), pygame.SRCALPHA)
            pygame.draw.rect(s, (96, 74, 46), (31, 40, 8, 76))
            pygame.draw.ellipse(s, (176, 150, 104), (17, 30, 36, 46))
            pygame.draw.circle(s, (176, 150, 104), (35, 20), 14)
            pygame.draw.line(s, (96, 74, 46), (5, 52), (65, 52), 6)
            # Viiltoja
            pygame.draw.line(s, (120, 90, 60), (24, 44), (40, 60), 2)
            pygame.draw.line(s, (120, 90, 60), (44, 40), (30, 66), 2)
            self.image = s


class TrophyShelf(_Furniture):
    """Palkintohylly (taso 3): muistoja voitoista."""

    def __init__(self, x, y):
        super().__init__(x, y, 180, 110,
                         img_path="assets/tiles/barracks/trophy_shelf.png",
                         collision_rect=pygame.Rect(x, y + 70, 180, 36))
        if self.image.get_at((0, 0)) == (100, 100, 100, 255):
            s = pygame.Surface((180, 110), pygame.SRCALPHA)
            pygame.draw.rect(s, (92, 70, 44), (0, 20, 180, 90), border_radius=6)
            pygame.draw.rect(s, (40, 30, 20), (0, 20, 180, 90), 3, border_radius=6)
            for shelf_y in (48, 80):
                pygame.draw.line(s, (60, 46, 30), (8, shelf_y), (172, shelf_y), 4)
            # Pysti, kypärä, kilpi
            pygame.draw.polygon(s, (222, 186, 92), [(28, 44), (44, 44), (40, 30), (32, 30)])
            pygame.draw.circle(s, (150, 150, 165), (86, 38), 9)
            pygame.draw.circle(s, (170, 120, 70), (136, 38), 10)
            pygame.draw.circle(s, (222, 186, 92), (136, 38), 10, 2)
            self.image = s


class FlatDecor(Prop):
    """Lattiatason koriste (matto, romu, halkeama) - ei törmäystä."""

    def __init__(self, x, y, kind):
        w, h = (260, 160) if kind == "rug" else (90, 60)
        super().__init__(x, y, w, h)
        self.is_flat = True
        self.has_shadow = False
        self.rect = pygame.Rect(x, y, 0, 0)  # ei törmäystä
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        if kind == "rug":
            pygame.draw.ellipse(s, (110, 60, 54), (0, 0, w, h))
            pygame.draw.ellipse(s, (150, 92, 66), (18, 12, w - 36, h - 24), 4)
            pygame.draw.ellipse(s, (196, 164, 90), (52, 34, w - 104, h - 68), 2)
        elif kind == "debris":
            for _ in range(7):
                px, py = random.randint(4, w - 10), random.randint(4, h - 8)
                pygame.draw.rect(s, random.choice([(96, 82, 60), (76, 66, 52)]),
                                 (px, py, random.randint(5, 14), random.randint(3, 8)))
        else:  # crack
            pts = [(6, h - 6)]
            for i in range(4):
                pts.append((10 + i * (w // 5) + random.randint(-6, 6),
                            h - 12 - i * (h // 6) + random.randint(-5, 5)))
            pygame.draw.lines(s, (44, 40, 36), False, pts, 3)
        self.image = s
        self.image_pos = (x, y)


class _Wall(Prop):
    """Näkymätön törmäysseinä; itse seinät piirretään taustaan."""

    def __init__(self, x, y, w, h):
        super().__init__(x, y, max(1, w), max(1, h))
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.image_pos = (x, y)
        self.rect = pygame.Rect(x, y, w, h)
        self.has_shadow = False


class BarracksInteriorArena:
    """Sisätila-areena GameplayScreen-rajapinnalla (width/height/obstacles/
    props/vfx/draw_background). Rakennetaan uudelleen tason vaihtuessa."""

    def __init__(self, level=1):
        self.level = max(1, min(3, int(level)))
        self.width = 2200
        self.height = 1300
        self.vfx = VFXManager()
        self.props = []
        self.obstacles = []
        self.bunks = []
        self.hearth = None
        self.desk = None
        self.plans_board = None
        self.door_rect = pygame.Rect(self.width // 2 - DOOR_W // 2,
                                     self.height - WALL - 10, DOOR_W, WALL + 20)
        self._background = None
        self._build()

    # ------------------------------------------------------------------
    def _build(self):
        lvl = self.level
        w, h = self.width, self.height
        self.props = []
        self.bunks = []

        # Törmäysseinät (oviaukko alaseinän keskellä)
        door = self.door_rect
        walls = [
            _Wall(0, 0, w, WALL + 60),                # yläseinä (korkea, punkkien takana)
            _Wall(0, 0, WALL, h),                     # vasen
            _Wall(w - WALL, 0, WALL, h),              # oikea
            _Wall(0, h - WALL, door.left, WALL),      # ala vasen
            _Wall(door.right, h - WALL, w - door.right, WALL),  # ala oikea
        ]
        self.props.extend(walls)

        # Punkat yläseinälle riviin
        count = BUNKS_PER_LEVEL[lvl]
        gap = (w - 2 * WALL - 200) // count
        start_x = WALL + 100 + (gap - 84) // 2
        for i in range(count):
            self.bunks.append(Bunk(start_x + i * gap, WALL + 40, quality=lvl))
        self.props.extend(self.bunks)

        # Pitkä pöytä keskelle
        self.table = LongTable(w // 2 - 160, h // 2 - 40, quality=lvl)
        self.props.append(self.table)

        # Takka länsiseinällä; palaa tasolla 2+
        self.hearth = Hearth(WALL + 20, h // 2 - 140, lit=(lvl >= 2))
        self.props.append(self.hearth)

        # Komentajan pöytä + suunnitelmataulu itäseinälle
        self.desk = CommanderDesk(w - WALL - 220, h // 2 - 160)
        self.plans_board = PlansBoard(w - WALL - 160, h // 2 + 60)
        self.props.extend([self.desk, self.plans_board])

        if lvl == 1:
            # Ränsistynyt: romua ja halkeamia lattialla
            for pos in [(w * 0.3, h * 0.72), (w * 0.62, h * 0.3),
                        (w * 0.75, h * 0.68), (w * 0.42, h * 0.36)]:
                self.props.append(FlatDecor(int(pos[0]), int(pos[1]), "debris"))
            for pos in [(w * 0.2, h * 0.5), (w * 0.55, h * 0.78)]:
                self.props.append(FlatDecor(int(pos[0]), int(pos[1]), "crack"))
        if lvl >= 2:
            self.props.append(FlatDecor(w // 2 - 130, h // 2 + 140, "rug"))
        if lvl >= 3:
            self.props.append(TrainingDummy(int(w * 0.72), int(h * 0.72)))
            self.props.append(TrophyShelf(int(w * 0.3), WALL + 210))

        self.obstacles = [p for p in self.props if p.rect.w > 0]
        self._background = None  # pakota uudelleenpiirto

    # ------------------------------------------------------------------
    def _render_background(self):
        lvl = self.level
        w, h = self.width, self.height
        bg = pygame.Surface((w, h))
        # Lattialankut
        plank = (74, 58, 40) if lvl == 1 else (88, 68, 46)
        alt = (66, 52, 36) if lvl == 1 else (80, 62, 42)
        bg.fill(plank)
        rng = random.Random(42 + lvl)
        line = (plank[0] - 12, plank[1] - 10, plank[2] - 8)
        for py in range(0, h, 46):
            offset = (py // 46) % 2 * 110
            pygame.draw.line(bg, line, (0, py), (w, py), 1)
            for px in range(-offset, w, 220):
                pygame.draw.line(bg, line, (px, py), (px, py + 46), 1)
            # Vaihtelevan sävyisiä lankkuja + puun syitä
            for _ in range(3):
                sx = rng.randint(0, w - 220)
                pygame.draw.rect(bg, alt, (sx, py + 1, rng.randint(80, 200), 44))
            for _ in range(4):
                gx = rng.randint(10, w - 90)
                gy = py + rng.randint(8, 38)
                pygame.draw.line(bg, line, (gx, gy), (gx + rng.randint(24, 70), gy), 1)
        if lvl == 1:
            # Kosteusläikkiä
            for _ in range(14):
                px, py = rng.randint(60, w - 120), rng.randint(120, h - 120)
                pygame.draw.ellipse(bg, (58, 48, 36),
                                    (px, py, rng.randint(40, 110), rng.randint(20, 50)))

        # Seinät
        wall_col = (96, 82, 66) if lvl == 1 else (112, 94, 72)
        pygame.draw.rect(bg, wall_col, (0, 0, w, WALL + 60))
        pygame.draw.rect(bg, wall_col, (0, 0, WALL, h))
        pygame.draw.rect(bg, wall_col, (w - WALL, 0, WALL, h))
        pygame.draw.rect(bg, wall_col, (0, h - WALL, w, WALL))
        pygame.draw.rect(bg, (36, 28, 22), (0, 0, w, h), 6)
        # Hirsisaumat yläseinään
        for px in range(0, w, 90):
            pygame.draw.line(bg, (70, 58, 46), (px, 0), (px, WALL + 60), 2)
        if lvl == 1:
            # Laudoitettu ikkuna + halkeamia seinässä
            pygame.draw.rect(bg, (30, 24, 20), (int(w * 0.62), 18, 110, 62))
            for i in range(3):
                pygame.draw.line(bg, (108, 88, 60),
                                 (int(w * 0.62) - 6, 26 + i * 18),
                                 (int(w * 0.62) + 116, 34 + i * 18), 7)
        if lvl >= 3:
            # Liput yläseinälle
            for i, fx in enumerate(range(int(w * 0.18), int(w * 0.85), 260)):
                col = (140, 44, 44) if i % 2 == 0 else (196, 164, 90)
                pygame.draw.polygon(bg, col, [(fx, 8), (fx + 56, 8), (fx + 28, 92)])
                pygame.draw.polygon(bg, (40, 30, 22), [(fx, 8), (fx + 56, 8), (fx + 28, 92)], 2)

        # Oviaukko alaseinään
        door = self.door_rect
        pygame.draw.rect(bg, (30, 24, 18), (door.x, h - WALL, door.w, WALL))
        pygame.draw.rect(bg, (120, 100, 70), (door.x, h - WALL, door.w, 8))
        self._background = bg

    def draw_background(self, screen, offset=(0, 0)):
        if self._background is None:
            self._render_background()
        screen.blit(self._background, (-offset[0], -offset[1]))

    def update(self, manager=None):
        # Takan liekki-VFX hoidetaan menun draw-vaiheessa (kevyt flicker)
        pass
