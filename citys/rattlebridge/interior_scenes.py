"""Käsin koodilla maalatut Rattlebridgen sisätilakohtaukset.

Placeholder-taide kunnes oikeat kuvat valmistuvat, mutta tehty niin hyvin kuin
koodipiirrolla on järkevää: staattinen pohja renderöidään KERRAN muistiin ja
per-frame piirretään vain halvat animaatiokerrokset (takkatuli, höyry,
kynttilänliekit, valokeila). Hahmoissa käytetään samaa rotukieltä kuin
yksiköiden koodipiirroissa (kääpiön parta+kypärä, gnomen hattu+suojalasit,
örkin torahampaat), joten tyyli pysyy yhtenäisenä.
"""

from __future__ import annotations

import math
import random

import pygame

from settings import SCREEN_HEIGHT, SCREEN_WIDTH


# ----------------------------------------------------------------------
# Yhteiset apurit
# ----------------------------------------------------------------------
TIMBER_DARK = (54, 40, 30)
TIMBER = (78, 58, 42)
TIMBER_LIGHT = (102, 78, 56)
PLANK = (96, 74, 52)
PLANK_DARK = (72, 55, 39)
STONE = (126, 120, 108)
STONE_DARK = (96, 91, 82)
BRASS = (176, 136, 74)
COPPER = (168, 106, 62)
IRON = (70, 68, 64)
CANDLE = (255, 214, 130)

SKIN = {
    "human": (214, 178, 146),
    "dwarf": (206, 166, 134),
    "gnome": (222, 188, 158),
    "orc": (116, 146, 92),
    "elf": (226, 198, 168),
    "goblin": (128, 168, 84),
}


def _noise(surface, rng, amount, color_delta=14, alpha=18):
    w, h = surface.get_size()
    dots = pygame.Surface((w, h), pygame.SRCALPHA)
    for _ in range(amount):
        x = rng.randint(0, w - 1)
        y = rng.randint(0, h - 1)
        d = rng.randint(-color_delta, color_delta)
        c = (128 + d, 128 + d, 128 + d, alpha)
        dots.set_at((x, y), c)
    surface.blit(dots, (0, 0))


def _vignette(surface, strength=140):
    w, h = surface.get_size()
    shade = pygame.Surface((w, h), pygame.SRCALPHA)
    steps = 26
    for i in range(steps):
        a = int(strength * (i / steps) ** 2)
        pygame.draw.rect(shade, (8, 6, 4, a),
                         (i * 6, i * 6, w - i * 12, h - i * 12), 8)
    surface.blit(shade, (0, 0))


def _seated_figure(surface, x, y, race, rng, facing=1, scale=1.0):
    """Istuva hahmo penkillä: rotukohtaiset tunnusmerkit."""
    s = scale
    skin = SKIN.get(race, SKIN["human"])
    cloth = rng.choice(((92, 74, 96), (74, 96, 84), (110, 84, 60),
                        (84, 88, 110), (120, 96, 62)))
    # Vartalo (istuva torso)
    body = pygame.Rect(x - int(26 * s), y - int(52 * s),
                       int(52 * s), int(56 * s))
    pygame.draw.rect(surface, cloth, body, border_radius=int(14 * s))
    pygame.draw.rect(surface, tuple(max(0, c - 26) for c in cloth), body,
                     2, border_radius=int(14 * s))
    # Pää
    head_r = int((15 if race != "gnome" else 13) * s)
    hx = x + int(4 * s * facing)
    hy = y - int(62 * s)
    pygame.draw.circle(surface, skin, (hx, hy), head_r)
    # Käsi + tuoppi pöydällä
    pygame.draw.line(surface, cloth, (x + int(10 * s * facing), y - int(34 * s)),
                     (x + int(34 * s * facing), y - int(20 * s)), int(9 * s))
    mug = pygame.Rect(x + int(28 * s * facing) - int(7 * s), y - int(30 * s),
                      int(15 * s), int(15 * s))
    pygame.draw.rect(surface, (168, 150, 118), mug, border_radius=3)
    pygame.draw.rect(surface, (120, 104, 78), mug, 2, border_radius=3)

    if race == "dwarf":
        pygame.draw.polygon(surface, (162, 116, 64),
                            [(hx - head_r + 3, hy + 3), (hx + head_r - 3, hy + 3),
                             (hx + int(6 * s), hy + int(30 * s)),
                             (hx - int(6 * s), hy + int(30 * s))])
        pygame.draw.rect(surface, (128, 128, 138),
                         (hx - head_r, hy - head_r - 2, head_r * 2, int(9 * s)),
                         border_radius=4)
    elif race == "gnome":
        pygame.draw.polygon(surface, (150, 108, 58),
                            [(hx, hy - head_r - int(20 * s)),
                             (hx + head_r + 2, hy - head_r + 5),
                             (hx - head_r - 2, hy - head_r + 5)])
        pygame.draw.circle(surface, (96, 134, 150), (hx - 5, hy - 2), 4)
        pygame.draw.circle(surface, (96, 134, 150), (hx + 5, hy - 2), 4)
    elif race == "orc":
        pygame.draw.line(surface, (232, 226, 210),
                         (hx - 6, hy + head_r - 4), (hx - 8, hy + head_r + 4), 3)
        pygame.draw.line(surface, (232, 226, 210),
                         (hx + 6, hy + head_r - 4), (hx + 8, hy + head_r + 4), 3)
    elif race == "elf":
        pygame.draw.polygon(surface, skin,
                            [(hx - head_r, hy - 4), (hx - head_r - 8, hy - 8),
                             (hx - head_r + 2, hy + 2)])
        pygame.draw.polygon(surface, skin,
                            [(hx + head_r, hy - 4), (hx + head_r + 8, hy - 8),
                             (hx + head_r - 2, hy + 2)])
    elif race == "goblin":
        pygame.draw.polygon(surface, skin,
                            [(hx - head_r, hy - 6), (hx - head_r - 10, hy - 14),
                             (hx - head_r + 3, hy)])
        pygame.draw.polygon(surface, skin,
                            [(hx + head_r, hy - 6), (hx + head_r + 10, hy - 14),
                             (hx + head_r - 3, hy)])
    # Silmät
    pygame.draw.circle(surface, (30, 26, 24), (hx - int(5 * s), hy - 2), 2)
    pygame.draw.circle(surface, (30, 26, 24), (hx + int(5 * s), hy - 2), 2)


def _standing_figure(surface, x, y, race, cloth, *, apron=False, coif=False,
                     robe=False, height=118, rng=None):
    """Seisova hahmo (baarimikko, priori, sisaret)."""
    rng = rng or random
    skin = SKIN.get(race, SKIN["human"])
    w = 56
    body = pygame.Rect(x - w // 2, y - height, w, height - 12)
    if robe:
        pygame.draw.polygon(surface, cloth,
                            [(body.left + 6, body.top),
                             (body.right - 6, body.top),
                             (body.right + 6, body.bottom + 10),
                             (body.left - 6, body.bottom + 10)])
    else:
        pygame.draw.rect(surface, cloth, body, border_radius=14)
    pygame.draw.rect(surface, tuple(max(0, c - 30) for c in cloth),
                     body.inflate(6, 6), 2, border_radius=14)
    if apron:
        ap = pygame.Rect(body.left + 10, body.top + 24, body.w - 20, body.h - 30)
        pygame.draw.rect(surface, (196, 182, 158), ap, border_radius=8)
        pygame.draw.line(surface, (150, 138, 118), (ap.left, ap.top + 12),
                         (ap.right, ap.top + 12), 2)
    hy = y - height - 14
    pygame.draw.circle(surface, skin, (x, hy), 17)
    if coif:
        pygame.draw.arc(surface, (232, 228, 218), (x - 20, hy - 22, 40, 40),
                        0.4, 2.75, 8)
    if race == "dwarf":
        pygame.draw.polygon(surface, (150, 150, 160),
                            [(x - 17, hy + 4), (x + 17, hy + 4),
                             (x + 7, hy + 36), (x - 7, hy + 36)])
    pygame.draw.circle(surface, (30, 26, 24), (x - 6, hy - 2), 2)
    pygame.draw.circle(surface, (30, 26, 24), (x + 6, hy - 2), 2)


class _Flame:
    """Kevyt liekki: piirretään suoraan ruudulle joka frame."""

    def __init__(self, x, y, size=1.0, hue=(255, 168, 60)):
        self.x = x
        self.y = y
        self.size = size
        self.hue = hue
        self.phase = random.uniform(0, 6.28)

    def draw(self, screen, tick):
        t = tick * 0.006 + self.phase
        h = (14 + math.sin(t * 3.1) * 4 + math.sin(t * 7.7) * 2) * self.size
        w = (7 + math.sin(t * 5.3) * 2) * self.size
        sway = math.sin(t * 2.2) * 2 * self.size
        base = (self.x + sway, self.y)
        pygame.draw.polygon(screen, self.hue,
                            [(base[0] - w, self.y),
                             (base[0] + w, self.y),
                             (base[0] + sway, self.y - h * 1.9)])
        pygame.draw.polygon(screen, (255, 226, 140),
                            [(base[0] - w * 0.45, self.y),
                             (base[0] + w * 0.45, self.y),
                             (base[0] + sway * 0.6, self.y - h)])


# ----------------------------------------------------------------------
# The Span - Boil-Cider Housen tupa
# ----------------------------------------------------------------------
class SpanTaproomScene:
    """Ironspan Unionin kantapaikka: höyryävä siiderikattila, takka,
    kansityöläisiä kaikista Rattlebridgen roduista."""

    def __init__(self, seed=771201):
        rng = random.Random(seed)
        self.base = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._paint_static(rng)
        # Animoidut pisteet
        self.hearth_flames = [
            _Flame(238 + i * 26, 668, size=1.9 - i * 0.18) for i in range(4)
        ]
        self.candle_flames = [
            _Flame(x, y, size=0.62, hue=(255, 196, 96))
            for x, y in ((700, 505), (988, 505), (1274, 505))
        ]
        self.boiler_xy = (1636, 470)
        self.steam_phase = rng.uniform(0, 6.28)

    # -- staattinen pohja -------------------------------------------------
    def _paint_static(self, rng):
        s = self.base
        w, h = s.get_size()

        # Takaseinä hirsipaneleina
        s.fill(TIMBER_DARK)
        for x in range(0, w, 132):
            pygame.draw.rect(s, TIMBER, (x + 5, 0, 122, 560))
            pygame.draw.line(s, TIMBER_DARK, (x + 5, 0), (x + 5, 560), 4)
        pygame.draw.rect(s, TIMBER_LIGHT, (0, 118, w, 26))   # vaakahirsi
        pygame.draw.rect(s, TIMBER_LIGHT, (0, 546, w, 22))
        for x in range(60, w, 132):                          # tapit
            pygame.draw.circle(s, TIMBER_DARK, (x, 131), 5)

        # Ikkunat: yösilta, sumu ja lyhtypisteet
        for wx in (160, 1180):
            win = pygame.Rect(wx, 190, 300, 240)
            pygame.draw.rect(s, (24, 36, 48), win)
            pygame.draw.line(s, (44, 62, 74), (win.left, win.bottom - 70),
                             (win.right, win.bottom - 96), 5)   # kaide
            for i in range(4):
                lx = win.left + 40 + i * 72
                pygame.draw.circle(s, (232, 186, 96), (lx, win.bottom - 84 - i * 4), 4)
                pygame.draw.circle(s, (120, 100, 60), (lx, win.bottom - 84 - i * 4), 7, 1)
            fog = pygame.Surface((win.w, 66), pygame.SRCALPHA)
            for i in range(3):
                pygame.draw.ellipse(fog, (188, 196, 198, 40 - i * 9),
                                    (i * 26, i * 14, win.w - i * 40, 52 - i * 8))
            s.blit(fog, (win.left, win.bottom - 66))
            pygame.draw.rect(s, TIMBER_LIGHT, win.inflate(22, 22), 11)
            pygame.draw.line(s, TIMBER_LIGHT, (win.centerx, win.top),
                             (win.centerx, win.bottom), 7)

        # Lattia: perspektiivilankut
        pygame.draw.rect(s, PLANK, (0, 568, w, h - 568))
        for i, y in enumerate(range(568, h, 46)):
            pygame.draw.line(s, PLANK_DARK, (0, y), (w, y), 3)
            step = 190 - i * 9
            offset = (i % 2) * step // 2
            for x in range(-offset, w, max(60, step)):
                pygame.draw.line(s, PLANK_DARK, (x, y), (x, min(h, y + 46)), 2)
        floor_shade = pygame.Surface((w, h - 568), pygame.SRCALPHA)
        for i in range(10):
            pygame.draw.rect(floor_shade, (20, 12, 8, 5 + i * 3),
                             (0, (h - 568) * i // 10, w, (h - 568) // 10 + 2))
        s.blit(floor_shade, (0, 568))

        # Takka vasemmalla
        hearth = pygame.Rect(120, 430, 300, 250)
        pygame.draw.rect(s, STONE_DARK, hearth.inflate(36, 30), border_radius=10)
        for row in range(5):
            for col in range(5):
                bx = hearth.left - 14 + col * 66 + (row % 2) * 22
                by = hearth.top - 12 + row * 52
                pygame.draw.rect(s, STONE, (bx, by, 60, 46), border_radius=6)
                pygame.draw.rect(s, STONE_DARK, (bx, by, 60, 46), 2, border_radius=6)
        opening = pygame.Rect(hearth.left + 50, hearth.top + 90, 200, 150)
        pygame.draw.rect(s, (16, 10, 8), opening, border_top_left_radius=90,
                         border_top_right_radius=90)
        pygame.draw.rect(s, (30, 22, 16), opening.inflate(14, 10), 6,
                         border_top_left_radius=98, border_top_right_radius=98)
        pygame.draw.ellipse(s, (52, 34, 22), (opening.left + 30,
                            opening.bottom - 42, 60, 22))  # halko
        pygame.draw.ellipse(s, (52, 34, 22), (opening.left + 90,
                            opening.bottom - 34, 70, 20))
        pygame.draw.rect(s, TIMBER_LIGHT, (hearth.left - 20, hearth.top - 36,
                         hearth.w + 40, 24), border_radius=6)  # hyllypalkki
        for mx in range(hearth.left, hearth.right, 70):
            mug = pygame.Rect(mx, hearth.top - 58, 22, 24)
            pygame.draw.rect(s, (150, 132, 100), mug, border_radius=4)

        # Baaritiski oikealla + KUPARINEN SIIDERIKATTILA (talon sydän)
        bar = pygame.Rect(1210, 560, 620, 66)
        pygame.draw.rect(s, TIMBER_LIGHT, bar, border_radius=10)
        pygame.draw.rect(s, TIMBER_DARK, bar, 4, border_radius=10)
        pygame.draw.line(s, BRASS, (bar.left + 8, bar.top + 10),
                         (bar.right - 8, bar.top + 10), 4)
        front = pygame.Rect(bar.left, bar.bottom, bar.w, 130)
        pygame.draw.rect(s, TIMBER, front)
        for px in range(front.left + 16, front.right, 88):
            pygame.draw.rect(s, TIMBER_DARK, (px, front.top + 10, 66, 108),
                             3, border_radius=8)
        # Tynnyrit tiskin alla
        for bx in (front.left + 60, front.left + 240, front.left + 430):
            keg = pygame.Rect(bx, front.top + 26, 84, 92)
            pygame.draw.ellipse(s, (124, 92, 58), keg)
            pygame.draw.ellipse(s, (86, 62, 40), keg, 4)
            pygame.draw.line(s, IRON, (keg.left, keg.centery - 16),
                             (keg.right, keg.centery - 16), 5)
            pygame.draw.line(s, IRON, (keg.left, keg.centery + 16),
                             (keg.right, keg.centery + 16), 5)
        # Pullohylly tiskin takana
        shelf = pygame.Rect(1240, 330, 400, 190)
        pygame.draw.rect(s, TIMBER_DARK, shelf, border_radius=8)
        for row in range(2):
            sy = shelf.top + 42 + row * 88
            pygame.draw.line(s, TIMBER_LIGHT, (shelf.left + 10, sy + 34),
                             (shelf.right - 10, sy + 34), 8)
            for i in range(7):
                bx = shelf.left + 30 + i * 52
                color = rng.choice(((104, 74, 44), (74, 96, 70), (120, 100, 52),
                                    (96, 70, 88)))
                pygame.draw.rect(s, color, (bx, sy - 6, 20, 40), border_radius=6)
                pygame.draw.rect(s, (208, 190, 150), (bx + 6, sy - 14, 8, 10))
        # Siiderikattila: iso kuparipata, putket, painemittari
        boiler = pygame.Rect(1560, 350, 150, 210)
        pygame.draw.ellipse(s, COPPER, boiler)
        pygame.draw.ellipse(s, (120, 74, 44), boiler, 5)
        shine = pygame.Surface(boiler.size, pygame.SRCALPHA)
        pygame.draw.ellipse(shine, (255, 220, 180, 60),
                            (18, 14, boiler.w // 3, boiler.h - 60))
        s.blit(shine, boiler.topleft)
        for ry in range(boiler.top + 34, boiler.bottom - 24, 44):
            pygame.draw.line(s, (128, 80, 48), (boiler.left + 12, ry),
                             (boiler.right - 12, ry), 3)
            for rx in range(boiler.left + 22, boiler.right - 14, 26):
                pygame.draw.circle(s, (108, 66, 40), (rx, ry), 3)
        pipe = pygame.Rect(boiler.centerx - 12, boiler.top - 60, 24, 66)
        pygame.draw.rect(s, COPPER, pipe, border_radius=6)
        pygame.draw.rect(s, (120, 74, 44), pipe, 3, border_radius=6)
        pygame.draw.circle(s, BRASS, (boiler.left - 6, boiler.top + 60), 17)
        pygame.draw.circle(s, (40, 34, 28), (boiler.left - 6, boiler.top + 60), 17, 3)
        pygame.draw.line(s, (40, 34, 28), (boiler.left - 6, boiler.top + 60),
                         (boiler.left - 14, boiler.top + 48), 3)
        tap = pygame.Rect(boiler.left + 30, boiler.bottom - 14, 90, 12)
        pygame.draw.rect(s, BRASS, tap, border_radius=5)

        # Union-ilmoitustaulu ovella
        board = pygame.Rect(620, 200, 330, 230)
        pygame.draw.rect(s, (88, 64, 40), board, border_radius=8)
        pygame.draw.rect(s, (188, 168, 120), board.inflate(-16, -16), 3)
        for _ in range(7):
            px = rng.randint(board.left + 24, board.right - 84)
            py = rng.randint(board.top + 26, board.bottom - 84)
            paper = pygame.Rect(px, py, rng.randint(48, 66), rng.randint(52, 70))
            pygame.draw.rect(s, (214, 202, 172), paper)
            pygame.draw.circle(s, (170, 60, 50), (paper.centerx, paper.top + 5), 3)
            for ly in range(paper.top + 14, paper.bottom - 6, 9):
                pygame.draw.line(s, (150, 140, 118), (paper.left + 6, ly),
                                 (paper.right - 6, ly), 1)
        title_plate = pygame.Rect(board.centerx - 90, board.top - 26, 180, 30)
        pygame.draw.rect(s, IRON, title_plate, border_radius=6)
        pygame.draw.rect(s, BRASS, title_plate, 2, border_radius=6)

        # Pöydät + asiakkaat (kaikki Rattlebridgen rodut edustettuina)
        tables = ((560, 812), (940, 830), (1310, 866), (330, 900))
        patrons = (
            ("dwarf", "human"), ("gnome", "orc"),
            ("human", "dwarf"), ("goblin", "elf"),
        )
        for (tx, ty), (race_a, race_b) in zip(tables, patrons):
            shadow = pygame.Surface((260, 60), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (10, 8, 6, 90), shadow.get_rect())
            s.blit(shadow, (tx - 130, ty - 18))
            _seated_figure(s, tx - 96, ty - 8, race_a, rng, facing=1)
            _seated_figure(s, tx + 96, ty - 8, race_b, rng, facing=-1)
            top = pygame.Rect(tx - 86, ty - 46, 172, 40)
            pygame.draw.ellipse(s, TIMBER_LIGHT, top)
            pygame.draw.ellipse(s, TIMBER_DARK, top, 4)
            pygame.draw.rect(s, TIMBER_DARK, (tx - 10, ty - 10, 20, 46))
            for mx in (tx - 40, tx + 24):
                pygame.draw.rect(s, (172, 152, 118), (mx, ty - 44, 16, 18),
                                 border_radius=3)

        # Hendrik Ironspan tiskin takana
        _standing_figure(s, 1408, 560, "human", (86, 66, 48), apron=True,
                         height=130, rng=rng)
        # Kattolyhdyt ketjuissa
        for lx in (700, 988, 1274):
            pygame.draw.line(s, IRON, (lx, 0), (lx, 470), 3)
            lamp = pygame.Rect(lx - 22, 470, 44, 52)
            pygame.draw.rect(s, IRON, lamp, 3, border_radius=8)
            pygame.draw.rect(s, (255, 214, 130), lamp.inflate(-14, -16),
                             border_radius=6)

        _noise(s, rng, 2600)
        _vignette(s, 150)

    # -- animaatio ---------------------------------------------------------
    def draw(self, screen, tick=None):
        if tick is None:
            tick = pygame.time.get_ticks()
        screen.blit(self.base, (0, 0))

        # Takkatuli + lämmin hehku
        for flame in self.hearth_flames:
            flame.draw(screen, tick)
        glow_a = 26 + int(math.sin(tick * 0.004) * 9)
        glow = pygame.Surface((560, 420), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (255, 150, 60, glow_a), glow.get_rect())
        screen.blit(glow, (20, 430))

        # Kynttilät ja lyhtyjen hehku
        for flame in self.candle_flames:
            flame.draw(screen, tick)

        # Siiderikattilan höyry
        bx, by = self.boiler_xy
        t = tick * 0.0016 + self.steam_phase
        for i in range(4):
            phase = t + i * 1.4
            py = by - 130 - (phase % 2.4) * 70
            px = bx + math.sin(phase * 2.1) * 16
            radius = 10 + int((phase % 2.4) * 9)
            alpha = max(0, 66 - int((phase % 2.4) * 26))
            puff = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(puff, (226, 228, 224, alpha), (radius, radius), radius)
            screen.blit(puff, (px - radius, py - radius))


# ----------------------------------------------------------------------
# Bridgeward Chapel-Hospital
# ----------------------------------------------------------------------
class BridgewardChapelScene:
    """Kappelisairaala: aurinkoikkuna, kynttilärivit, vuoteet potilaineen ja
    karanteeniverho - Radiant Synodin valoa ja Prior Vossin kirjanpitoa."""

    def __init__(self, seed=442087):
        rng = random.Random(seed)
        self.base = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._paint_static(rng)
        self.candle_flames = [
            _Flame(x, y, size=0.62, hue=(255, 206, 110))
            for x, y in ((330, 396), (394, 380), (362, 356),
                         (1532, 396), (1596, 380), (1564, 356))
        ]
        self.sun_center = (SCREEN_WIDTH // 2, 190)

    def _paint_static(self, rng):
        s = self.base
        w, h = s.get_size()

        # Kiviseinä
        s.fill((104, 99, 90))
        for row in range(11):
            for col in range(16):
                bx = col * 126 + (row % 2) * 60 - 40
                by = row * 56
                pygame.draw.rect(s, STONE, (bx, by, 118, 50), border_radius=4)
                pygame.draw.rect(s, STONE_DARK, (bx, by, 118, 50), 2, border_radius=4)
        # Holvikaaret + pylväät
        for px in (250, 960, 1670):
            pygame.draw.rect(s, STONE_DARK, (px - 34, 90, 68, 500))
            pygame.draw.rect(s, STONE, (px - 26, 90, 52, 500))
            pygame.draw.rect(s, STONE_DARK, (px - 44, 60, 88, 34), border_radius=6)
            pygame.draw.rect(s, STONE_DARK, (px - 44, 560, 88, 30), border_radius=6)
        pygame.draw.arc(s, STONE_DARK, (250, -60, 720, 340), 0, math.pi, 22)
        pygame.draw.arc(s, STONE_DARK, (950, -60, 720, 340), 0, math.pi, 22)

        # Aurinkoikkuna (Radiant Synod)
        cx, cy = w // 2, 190
        pygame.draw.circle(s, (60, 56, 50), (cx, cy), 128)
        pygame.draw.circle(s, (238, 212, 130), (cx, cy), 112)
        pygame.draw.circle(s, (255, 236, 176), (cx, cy), 58)
        for k in range(12):
            a = k * math.tau / 12
            pygame.draw.line(s, (150, 122, 60),
                             (cx + math.cos(a) * 30, cy + math.sin(a) * 30),
                             (cx + math.cos(a) * 108, cy + math.sin(a) * 108), 7)
        pygame.draw.circle(s, (96, 78, 44), (cx, cy), 112, 8)
        pygame.draw.circle(s, (96, 78, 44), (cx, cy), 58, 5)

        # Lattia: kivilaatta
        pygame.draw.rect(s, (134, 126, 112), (0, 590, w, h - 590))
        for i, y in enumerate(range(590, h, 58)):
            pygame.draw.line(s, (108, 101, 90), (0, y), (w, y), 3)
            step = 210 - i * 12
            offset = (i % 2) * step // 2
            for x in range(-offset, w, max(80, step)):
                pygame.draw.line(s, (108, 101, 90), (x, y), (x, min(h, y + 58)), 2)
        runner = pygame.Rect(cx - 80, 640, 160, h - 640)
        pygame.draw.rect(s, (112, 78, 70), runner)
        pygame.draw.rect(s, (146, 116, 78), runner, 5)
        for ry in range(runner.top + 26, h, 60):
            pygame.draw.line(s, (96, 66, 60), (runner.left + 14, ry),
                             (runner.right - 14, ry), 2)

        # Alttari + lahjoitusarkku + Prior Voss
        altar = pygame.Rect(cx - 130, 470, 260, 110)
        pygame.draw.rect(s, STONE, altar, border_radius=8)
        pygame.draw.rect(s, STONE_DARK, altar, 4, border_radius=8)
        pygame.draw.rect(s, (222, 214, 196), (altar.left + 10, altar.top - 10,
                         altar.w - 20, 16), border_radius=4)
        chest = pygame.Rect(cx + 160, 520, 96, 64)
        pygame.draw.rect(s, (96, 68, 40), chest, border_radius=8)
        pygame.draw.rect(s, BRASS, chest, 3, border_radius=8)
        pygame.draw.rect(s, BRASS, (chest.centerx - 8, chest.top + 22, 16, 22),
                         border_radius=4)
        _standing_figure(s, cx - 210, 590, "human", (206, 190, 150), robe=True,
                         height=140, rng=rng)
        # Kultareunus priorin kaapuun + kirjanpitokirja
        pygame.draw.line(s, BRASS, (cx - 236, 470), (cx - 236, 580), 3)
        pygame.draw.line(s, BRASS, (cx - 184, 470), (cx - 184, 580), 3)
        pygame.draw.rect(s, (120, 44, 40), (cx - 196, 508, 34, 24), border_radius=3)
        pygame.draw.rect(s, (222, 210, 180), (cx - 192, 512, 26, 16))

        # Vuoderivit potilaineen
        self._cots(s, rng, y=700, xs=(180, 460, 740), quarantine=False)
        self._cots(s, rng, y=700, xs=(1160, 1440, 1720), quarantine=True)
        self._cots(s, rng, y=930, xs=(300, 620), quarantine=False)
        self._cots(s, rng, y=930, xs=(1300, 1620), quarantine=True)

        # Karanteeniverho oikealla
        pygame.draw.line(s, IRON, (1000, 620), (w, 620), 5)
        for vx in range(1020, w, 130):
            pygame.draw.polygon(s, (150, 60, 54),
                                [(vx, 622), (vx + 104, 622),
                                 (vx + 92, 700), (vx + 12, 700)])
            pygame.draw.polygon(s, (108, 42, 38),
                                [(vx, 622), (vx + 104, 622),
                                 (vx + 92, 700), (vx + 12, 700)], 3)
        sign = pygame.Rect(1050, 636, 150, 48)
        pygame.draw.rect(s, (222, 210, 180), sign, border_radius=6)
        pygame.draw.line(s, (150, 46, 40), (sign.left + 14, sign.top + 10),
                         (sign.left + 40, sign.bottom - 10), 6)
        pygame.draw.line(s, (150, 46, 40), (sign.left + 40, sign.top + 10),
                         (sign.left + 14, sign.bottom - 10), 6)

        # Kynttiläkandelaaberit
        for base_x in (362, 1564):
            pygame.draw.line(s, IRON, (base_x, 590), (base_x, 400), 6)
            pygame.draw.line(s, IRON, (base_x - 36, 404), (base_x + 36, 404), 6)
            for cxx in (base_x - 32, base_x, base_x + 32):
                pygame.draw.rect(s, (232, 224, 204),
                                 (cxx - 5, 372 + (0 if cxx == base_x else 24),
                                  10, 26))

        # Sisaret hoitamassa
        _standing_figure(s, 560, 660, "human", (120, 116, 128), coif=True,
                         height=112, rng=rng)
        _standing_figure(s, 1390, 880, "human", (120, 116, 128), coif=True,
                         height=112, rng=rng)

        # Yrttihylly
        shelf = pygame.Rect(40, 300, 180, 260)
        pygame.draw.rect(s, TIMBER_DARK, shelf, border_radius=8)
        for row in range(3):
            sy = shelf.top + 40 + row * 78
            pygame.draw.line(s, TIMBER_LIGHT, (shelf.left + 8, sy + 30),
                             (shelf.right - 8, sy + 30), 7)
            for i in range(3):
                jx = shelf.left + 26 + i * 52
                color = rng.choice(((96, 122, 74), (140, 110, 60), (110, 90, 120)))
                pygame.draw.rect(s, color, (jx, sy - 4, 28, 34), border_radius=6)
                pygame.draw.rect(s, (208, 196, 168), (jx + 4, sy - 12, 20, 10))

        _noise(s, rng, 2200)
        _vignette(s, 120)

    def _cots(self, s, rng, y, xs, quarantine):
        for x in xs:
            shadow = pygame.Surface((250, 44), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (10, 8, 6, 80), shadow.get_rect())
            s.blit(shadow, (x - 10, y + 20))
            frame = pygame.Rect(x, y - 36, 230, 66)
            pygame.draw.rect(s, (110, 84, 56), frame, border_radius=10)
            pygame.draw.rect(s, (78, 60, 42), frame, 4, border_radius=10)
            pygame.draw.rect(s, (86, 66, 46), (frame.left - 8, frame.top - 14,
                             14, 80), border_radius=5)
            blanket = pygame.Rect(frame.left + 46, frame.top + 8,
                                  frame.w - 56, frame.h - 20)
            color = (150, 60, 54) if quarantine else (96, 110, 128)
            pygame.draw.rect(s, color, blanket, border_radius=8)
            pygame.draw.line(s, tuple(max(0, c - 26) for c in color),
                             (blanket.left, blanket.top + 14),
                             (blanket.right, blanket.top + 14), 3)
            # Potilaan pää tyynyllä; karanteenissa kuumeinen poski
            pygame.draw.ellipse(s, (226, 220, 204),
                                (frame.left + 8, frame.top + 6, 44, 30))
            head = (frame.left + 30, frame.top + 20)
            pygame.draw.circle(s, SKIN["human"], head, 13)
            if quarantine:
                pygame.draw.circle(s, (208, 108, 92), (head[0] - 5, head[1] + 3), 4)
                pygame.draw.circle(s, (208, 108, 92), (head[0] + 5, head[1] + 3), 4)
                pygame.draw.rect(s, (226, 220, 208),
                                 (head[0] - 12, head[1] - 13, 24, 8),
                                 border_radius=3)  # otsaliina
            pygame.draw.line(s, (30, 26, 24), (head[0] - 6, head[1] - 2),
                             (head[0] - 2, head[1] - 2), 2)
            pygame.draw.line(s, (30, 26, 24), (head[0] + 2, head[1] - 2),
                             (head[0] + 6, head[1] - 2), 2)

    def draw(self, screen, tick=None):
        if tick is None:
            tick = pygame.time.get_ticks()
        screen.blit(self.base, (0, 0))

        # Valokeila aurinkoikkunasta alttarille (hidas pulssi)
        cx, cy = self.sun_center
        pulse = 30 + int(math.sin(tick * 0.0012) * 10)
        shaft = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(shaft, (255, 232, 160, pulse),
                            [(cx - 66, cy + 60), (cx + 66, cy + 60),
                             (cx + 250, 620), (cx - 250, 620)])
        screen.blit(shaft, (0, 0))

        for flame in self.candle_flames:
            flame.draw(screen, tick)


_SCENES = {}


def get_scene(name):
    """Jaettu välimuisti: kohtaus maalataan kerran per prosessi."""
    if name not in _SCENES:
        if name == "span":
            _SCENES[name] = SpanTaproomScene()
        elif name == "chapel":
            _SCENES[name] = BridgewardChapelScene()
        elif name == "scrapring":
            _SCENES[name] = ScrapringOverlookScene()
        else:
            raise KeyError(f"unknown interior scene '{name}'")
    return _SCENES[name]


# ----------------------------------------------------------------------
# Scrapring - Seran parveke areenan ylla
# ----------------------------------------------------------------------
class ScrapringOverlookScene:
    """Sera Quenchin toimistoparveke: alla areenakulho jossa OIKEAT vaarat
    (murskaavat rattaat, hoyryventtiilit, magneettilaatat), katsomot yleisoineen
    ja sponsoriviirit - sponsorien varit suoraan systems.sponsors-datasta."""

    def __init__(self, seed=553311):
        rng = random.Random(seed)
        self.base = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        try:
            from systems.sponsors import SPONSORS
            self.sponsor_colors = [s["banner"] for s in SPONSORS.values()]
        except Exception:
            self.sponsor_colors = [(100, 120, 140), (170, 90, 120),
                                   (120, 150, 90), (150, 130, 70)]
        self.arena_rect = pygame.Rect(360, 300, 1200, 560)
        self._paint_static(rng)
        self.gears = ((640, 520, 66, 0.35), (1290, 640, 78, -0.28))
        self.vents = ((960, 470), (860, 700), (1120, 690))
        self.pennant_y = 176

    def _paint_static(self, rng):
        s = self.base
        w, h = s.get_size()
        # Iltatäivas ja kaupungin siluetti
        for i in range(14):
            t = i / 13
            color = (int(30 + 26 * t), int(30 + 20 * t), int(44 + 26 * t))
            pygame.draw.rect(s, color, (0, i * 26, w, 28))
        pygame.draw.rect(s, (24, 26, 34), (0, 330, w, h - 330))
        for bx in range(-40, w, 120):
            bh = rng.randint(60, 190)
            pygame.draw.rect(s, (34, 36, 46), (bx, 364 - bh, 96, bh))
            for wy in range(374 - bh, 350, 26):
                if rng.random() < 0.5:
                    pygame.draw.rect(s, (222, 186, 100), (bx + rng.randint(8, 74), wy, 8, 10))
        # Areenakulho
        bowl = self.arena_rect
        pygame.draw.ellipse(s, (52, 50, 48), bowl.inflate(220, 150))
        # Katsomoportaat
        for ring in range(4):
            band = bowl.inflate(200 - ring * 44, 132 - ring * 30)
            pygame.draw.ellipse(s, (66 + ring * 7, 62 + ring * 6, 58 + ring * 6), band)
        # Yleiso pistein
        crowd = pygame.Surface((w, h), pygame.SRCALPHA)
        for _ in range(2600):
            a = rng.uniform(0, math.tau)
            ring = rng.uniform(0.56, 0.96)
            cxp = bowl.centerx + math.cos(a) * bowl.w * 0.5 * (1 + (1 - ring) * 0.36) * ring / ring
            px = bowl.centerx + math.cos(a) * (bowl.w * 0.52 + rng.uniform(6, 96))
            py = bowl.centery + math.sin(a) * (bowl.h * 0.52 + rng.uniform(4, 62))
            color = rng.choice(((198, 178, 150), (150, 128, 104), (120, 140, 160),
                                (170, 120, 110), (110, 150, 120)))
            pygame.draw.circle(crowd, (*color, 190), (int(px), int(py)), 3)
        s.blit(crowd, (0, 0))
        # Hiekkapohja + kaistamaalaukset
        pygame.draw.ellipse(s, (150, 128, 96), bowl)
        pygame.draw.ellipse(s, (120, 100, 76), bowl, 6)
        pygame.draw.ellipse(s, (168, 146, 112), bowl.inflate(-260, -180), 3)
        # Magneettilaatat (siniset) kuten oikeassa areenassa
        for mx, my in ((bowl.centerx - 70, bowl.centery - 40),
                       (bowl.left + 170, bowl.centery + 60),
                       (bowl.right - 300, bowl.centery + 30)):
            plate = pygame.Rect(mx, my, 140, 92)
            pygame.draw.rect(s, (44, 60, 82), plate, border_radius=8)
            pygame.draw.rect(s, (70, 100, 140), plate, 3, border_radius=8)
            for gx in range(plate.left + 14, plate.right - 8, 22):
                pygame.draw.line(s, (60, 84, 116), (gx, plate.top + 6),
                                 (gx, plate.bottom - 6), 1)
        # Parvekekaide etualalla
        rail_y = h - 210
        pygame.draw.rect(s, (58, 52, 44), (0, rail_y, w, 26))
        pygame.draw.rect(s, BRASS, (0, rail_y, w, 6))
        for px in range(40, w, 130):
            pygame.draw.rect(s, (58, 52, 44), (px, rail_y + 20, 18, 190))
        # Seran tyopoyta oikealla: sopimuksia, sinettivaha, mustepullo
        desk = pygame.Rect(w - 620, h - 190, 560, 190)
        pygame.draw.rect(s, (86, 62, 42), desk, border_top_left_radius=18)
        pygame.draw.rect(s, (60, 44, 32), desk, 5, border_top_left_radius=18)
        for i in range(3):
            paper = pygame.Rect(desk.left + 40 + i * 150, desk.top + 26, 110, 76)
            pygame.draw.rect(s, (216, 204, 174), paper)
            pygame.draw.rect(s, (150, 140, 118), paper, 2)
            for ly in range(paper.top + 14, paper.bottom - 8, 12):
                pygame.draw.line(s, (150, 140, 118), (paper.left + 10, ly),
                                 (paper.right - 10, ly), 1)
            pygame.draw.circle(s, (150, 46, 44), (paper.right - 18, paper.bottom - 14), 9)
        pygame.draw.rect(s, (40, 36, 34), (desk.right - 90, desk.top + 20, 34, 46),
                         border_radius=6)
        # Sera itse parvekkeella (terava siluetti, viininpunainen takki)
        _standing_figure(s, w - 700, h - 66, "human", (122, 52, 64), height=150)
        pygame.draw.rect(s, BRASS, (w - 712, h - 210, 24, 6))
        _noise(s, rng, 2000)
        _vignette(s, 130)

    def draw(self, screen, tick=None):
        if tick is None:
            tick = pygame.time.get_ticks()
        screen.blit(self.base, (0, 0))
        # Pyorivat rattaat areenassa
        for gx, gy, radius, speed in self.gears:
            angle = tick * 0.001 * speed
            pygame.draw.circle(screen, (74, 72, 68), (gx, gy), radius)
            pygame.draw.circle(screen, (40, 40, 38), (gx, gy), radius, 5)
            for k in range(8):
                a = angle + k * (math.tau / 8)
                pygame.draw.circle(screen, (74, 72, 68),
                                   (gx + int(math.cos(a) * (radius + 9)),
                                    gy + int(math.sin(a) * (radius + 9))),
                                   max(6, radius // 7))
            pygame.draw.circle(screen, BRASS, (gx, gy), max(8, radius // 5))
        # Hoyryventtiilien purkaukset sykleissa
        for i, (vx, vy) in enumerate(self.vents):
            phase = (tick * 0.0011 + i * 0.83) % 2.2
            pygame.draw.circle(screen, (70, 70, 78), (vx, vy), 15)
            pygame.draw.circle(screen, (44, 44, 50), (vx, vy), 15, 3)
            if phase < 0.9:
                for k in range(3):
                    r = 8 + int(phase * 26) + k * 7
                    alpha = max(0, 90 - int(phase * 90) - k * 18)
                    puff = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(puff, (228, 230, 226, alpha), (r, r), r)
                    screen.blit(puff, (vx - r, vy - r - k * 16 - int(phase * 30)))
        # Sponsoriviirit heiluvat ylhaalla
        sway = math.sin(tick * 0.0016)
        n = max(1, len(self.sponsor_colors))
        for i, color in enumerate(self.sponsor_colors):
            px = 200 + i * (SCREEN_WIDTH - 400) // n
            top = self.pennant_y + int(math.sin(tick * 0.0016 + i) * 5)
            pygame.draw.line(screen, (50, 48, 44), (px, top - 40), (px, top), 3)
            pygame.draw.polygon(screen, color,
                                [(px, top - 36), (px + 46 + sway * 6, top - 22),
                                 (px, top - 8)])
        pygame.draw.line(screen, (60, 58, 52), (140, self.pennant_y - 40),
                         (SCREEN_WIDTH - 140, self.pennant_y - 40), 2)


# ----------------------------------------------------------------------
# Canalworks - kanaalitunnelit (maalataan pelialueen layoutista)
# ----------------------------------------------------------------------
class CanalworksScene:
    """Alakannen kanaalit: kavelykaistat, ritilat, putket ja pesapaikat
    maalataan SUORAAN pelialueen layout-datasta, joten grafiikka vastaa
    aina tormayksia ja spawneja."""

    def __init__(self, walkable, blockers, nest_points, boss_point, exit_rect,
                 seed=664422):
        rng = random.Random(seed)
        self.base = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.nest_points = tuple(nest_points)
        self.boss_point = tuple(boss_point)
        self._paint_static(rng, walkable, blockers, exit_rect)
        self.drips = [(rng.randint(60, SCREEN_WIDTH - 60),
                       rng.randint(90, SCREEN_HEIGHT - 90),
                       rng.uniform(0, 6.28)) for _ in range(9)]

    def _paint_static(self, rng, walkable, blockers, exit_rect):
        s = self.base
        w, h = s.get_size()
        # Pohja: tumma kanaalivesi
        s.fill((16, 30, 36))
        for y in range(0, h, 34):
            pygame.draw.line(s, (26, 44, 50), (0, y), (w, y), 2)
        # Levaa ja limaa veden pinnassa
        for _ in range(46):
            gx = rng.randint(0, w - 80)
            gy = rng.randint(0, h - 30)
            pygame.draw.ellipse(s, (30, 52, 42),
                                (gx, gy, rng.randint(30, 90), rng.randint(8, 18)))
        # Kavelykaistat kivilaattoina
        for lane in walkable:
            pygame.draw.rect(s, (30, 32, 34), lane.inflate(18, 18), border_radius=8)
            pygame.draw.rect(s, (84, 82, 76), lane, border_radius=6)
            pygame.draw.rect(s, (54, 54, 52), lane, 5, border_radius=6)
            if lane.w >= lane.h:  # vaakakaista
                for x in range(lane.left + 40, lane.right, 90):
                    pygame.draw.line(s, (66, 64, 60), (x, lane.top + 6),
                                     (x, lane.bottom - 6), 2)
            else:
                for y in range(lane.top + 40, lane.bottom, 90):
                    pygame.draw.line(s, (66, 64, 60), (lane.left + 6, y),
                                     (lane.right - 6, y), 2)
        # Viemariritilat kaistojen risteyksissa
        for lane in walkable[:3]:
            for gx in range(lane.left + 150, lane.right - 60, 420):
                grate = pygame.Rect(gx, lane.centery - 20, 66, 40)
                pygame.draw.rect(s, (36, 36, 38), grate, border_radius=6)
                for bar_x in range(grate.left + 8, grate.right - 4, 10):
                    pygame.draw.line(s, (70, 70, 72), (bar_x, grate.top + 5),
                                     (bar_x, grate.bottom - 5), 3)
        # Seinaputket ylareunassa + venttiilipyorat
        for px in range(80, w, 300):
            pygame.draw.line(s, (74, 64, 52), (px, 0), (px, 60), 14)
            pygame.draw.circle(s, (120, 96, 60), (px, 46), 13, 4)
        pygame.draw.line(s, (74, 64, 52), (0, 26), (w, 26), 10)
        # Esteet: romukasat ja kaatuneet tynnyrit
        for rect in blockers:
            pygame.draw.rect(s, (24, 22, 20), rect.move(5, 7), border_radius=8)
            pygame.draw.rect(s, (88, 66, 44), rect, border_radius=8)
            pygame.draw.rect(s, (52, 40, 30), rect, 3, border_radius=8)
            pygame.draw.line(s, (110, 84, 56), rect.topleft, rect.bottomright, 3)
            pygame.draw.line(s, (110, 84, 56), rect.bottomleft, rect.topright, 3)
        # Pesapaikkojen limarenkaat (itse pesat piirtaa pelilogiikka)
        for nx, ny in self.nest_points:
            ring = pygame.Surface((190, 120), pygame.SRCALPHA)
            for k in range(3):
                pygame.draw.ellipse(ring, (66, 120, 66, 60 - k * 16),
                                    (k * 16, k * 10, 190 - k * 32, 120 - k * 20), 6)
            s.blit(ring, (nx - 95, ny - 60))
        bx, by = self.boss_point
        ring = pygame.Surface((240, 150), pygame.SRCALPHA)
        for k in range(3):
            pygame.draw.ellipse(ring, (140, 66, 88, 56 - k * 14),
                                (k * 18, k * 12, 240 - k * 36, 150 - k * 24), 7)
        s.blit(ring, (bx - 120, by - 75))
        # Ulosjohtavat portaat exit-kohdassa
        pygame.draw.rect(s, (70, 68, 62), exit_rect.inflate(16, 16), border_radius=8)
        for step in range(4):
            sy = exit_rect.top + 12 + step * 18
            pygame.draw.rect(s, (110 + step * 8, 106 + step * 8, 98 + step * 8),
                             (exit_rect.left + 8, sy, exit_rect.w - 16, 14),
                             border_radius=4)
        # Riippuvat kettingit
        for cx in (rng.randint(200, w - 200) for _ in range(5)):
            length = rng.randint(60, 150)
            for ly in range(0, length, 12):
                pygame.draw.circle(s, (60, 60, 62), (cx, ly), 4, 2)
        _noise(s, rng, 2400)
        _vignette(s, 170)

    def draw(self, screen, tick=None):
        if tick is None:
            tick = pygame.time.get_ticks()
        screen.blit(self.base, (0, 0))
        # Tippuva vesi: pisara + rengas
        for dx, dy, phase in self.drips:
            t = (tick * 0.0013 + phase) % 1.6
            if t < 0.8:
                pygame.draw.line(screen, (150, 190, 196),
                                 (dx, dy - 40 + int(t * 56)),
                                 (dx, dy - 30 + int(t * 56)), 2)
            else:
                r = int((t - 0.8) * 34)
                if r > 1:
                    pygame.draw.ellipse(screen, (120, 170, 176),
                                        (dx - r, dy - r // 3, r * 2, r // 2), 1)
        # Pesien hidas mataneva hehku
        pulse = 30 + int(math.sin(tick * 0.002) * 16)
        for nx, ny in self.nest_points:
            glow = pygame.Surface((150, 90), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (90, 160, 80, pulse), glow.get_rect())
            screen.blit(glow, (nx - 75, ny - 45))
