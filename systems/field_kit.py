# systems/field_kit.py
"""Kenttätyökalupakki: YKSI järjestelmä jolla kentät rakennetaan.

Kaikki avoimen maailman kentät ja missiokartat rakennetaan näillä
palasilla samalla mekaniikalla (pelitesti 30):

- FieldResourceNode: kerättävä resurssi (E) - yhteinen runko, joka
  aiemmin oli kopioitu neljään karttaan (Marsh/Chapel/Ford/Toll).
  Tyylipiirtäjät (PAINTERS) kattavat yleiset ulkoasut; kartta voi
  lisätä omiaan. _after_harvest-koukku hoitaa karttakohtaisen
  tilakirjanpidon.
- GateZone: SELVÄ sisäänkäynti/uloskäynti (holvikaari, kyltti, tikkaat,
  ritilä, portaali) - pelaaja näkee mistä tullaan ja mistä lähdetään.
- WallSegment + FloorPatch + build_dungeon: käytävä/kammio-luolastot
  (krypta ym.) - EI isoja tyhjiä neliöitä vaan oikeita käytäviä.
  Seinät generoituvat kuorena kuljettavan alueen ympärille, joten
  esteitä ei synny tuhansittain.
- spread_points: siisti hajautus resursseille/propeille.

Vesi tulee assets/tiles/water.py:stä (WaterBody + fishing_anchors) ja
monsterit units/monster_registry.py:stä - tämä moduuli ei duplikoi niitä.
"""
from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import pygame

from assets.tiles.prop import Prop


def _safe_sound(name: str):
    try:
        from sound_manager import sound_system
        sound_system.play_sound(name)
    except Exception:
        pass


# ---------------------------------------------------------------------
# RESURSSINODET
# ---------------------------------------------------------------------
def _paint_herb(image, s):
    for dx in (-9, -3, 4, 10):
        pygame.draw.line(image, (65, 130, 80), (s // 2, s - 6), (s // 2 + dx, 15), 3)
    for x, y in ((s // 3, 16), (s // 2, 11), (2 * s // 3, 18)):
        pygame.draw.circle(image, (205, 195, 110), (x, y), 4)


def _paint_reeds(image, s):
    for index, x in enumerate(range(8, s - 6, 7)):
        height = 24 + (index % 3) * 7
        pygame.draw.line(image, (80, 126, 72), (x, s - 4), (x + index % 2, s - 4 - height), 3)
        pygame.draw.line(image, (160, 126, 64), (x, s - 4 - height), (x + 4, s - 9 - height), 3)


def _paint_driftwood(image, s):
    pygame.draw.line(image, (104, 77, 49), (6, s - 14), (s - 8, 17), 9)
    pygame.draw.line(image, (139, 104, 65), (9, s - 18), (s - 9, 16), 3)
    pygame.draw.line(image, (91, 66, 44), (s // 2, s // 2), (s // 3, 12), 5)


def _paint_clay(image, s):
    pygame.draw.ellipse(image, (104, 74, 55), (4, s // 2, s - 10, s // 2 - 6))
    pygame.draw.ellipse(image, (148, 96, 67), (10, s // 2 - 6, s - 22, s // 2 - 12))


def _paint_ore(image, s):
    pygame.draw.polygon(image, (88, 90, 96), [(6, s - 8), (s // 3, s // 3), (s // 2, s - 10)])
    pygame.draw.polygon(image, (72, 74, 82), [(s // 2 - 4, s - 8), (2 * s // 3, s // 4), (s - 6, s - 8)])
    for x, y in ((s // 3, s // 2), (2 * s // 3, s // 2 + 4), (s // 2, 2 * s // 3)):
        pygame.draw.circle(image, (196, 172, 96), (x, y), 3)


def _paint_crystal(image, s):
    for x, tip, col in ((s // 4, 12, (150, 120, 210)), (s // 2, 6, (170, 140, 230)),
                        (3 * s // 4, 14, (140, 110, 200))):
        pygame.draw.polygon(image, col, [(x - 7, s - 8), (x, tip), (x + 7, s - 8)])
        pygame.draw.line(image, (220, 205, 245), (x, tip + 4), (x - 2, s - 12), 1)


def _paint_mushroom(image, s):
    for x, r in ((s // 3, 9), (2 * s // 3, 12), (s // 2, 7)):
        pygame.draw.rect(image, (196, 186, 160), (x - 3, s - 10 - r, 6, r + 4))
        pygame.draw.ellipse(image, (151, 80, 92), (x - r, s - 16 - r, r * 2, r))
        pygame.draw.circle(image, (222, 200, 205), (x - r // 2, s - 13 - r), 2)


def _paint_bone(image, s):
    pygame.draw.line(image, (214, 206, 184), (10, s - 12), (s - 12, 18), 6)
    for x, y in ((10, s - 12), (s - 12, 18)):
        pygame.draw.circle(image, (214, 206, 184), (x - 3, y - 3), 5)
        pygame.draw.circle(image, (214, 206, 184), (x + 3, y + 3), 5)
    pygame.draw.circle(image, (196, 186, 162), (s // 2 + 6, s - 14), 7)


def _paint_scrap(image, s):
    pygame.draw.polygon(image, (111, 113, 108), [(5, s - 8), (s // 3, 15), (s // 2 + 4, s - 11)])
    pygame.draw.rect(image, (75, 80, 78), (s // 2 - 4, s // 2 - 4, s // 2 - 4, s // 3), border_radius=3)
    pygame.draw.circle(image, (143, 118, 73), (2 * s // 3, s // 3), 8, 3)


def _paint_wood(image, s):
    for i, y in enumerate((s - 16, s - 24, s - 32)):
        pygame.draw.line(image, (117, 85, 52), (8 + i * 3, y), (s - 8 - i * 3, y), 7)
        pygame.draw.circle(image, (156, 121, 76), (s - 10 - i * 3, y), 4)


DEFAULT_PAINTERS: Dict[str, Callable] = {
    "herb": _paint_herb,
    "reeds": _paint_reeds,
    "driftwood": _paint_driftwood,
    "clay": _paint_clay,
    "ore": _paint_ore,
    "crystal": _paint_crystal,
    "mushroom": _paint_mushroom,
    "bone": _paint_bone,
    "scrap": _paint_scrap,
    "wood": _paint_wood,
}


class FieldResourceNode(Prop):
    """Kerättävä resurssi - yhteinen runko kaikille kentille.

    Alaluokat voivat ylikirjoittaa PAINTERS-piirtäjiä (karttakohtainen
    ulkoasu) ja _after_harvest-koukun (karttakohtainen tilakirjanpito).
    """

    SIZE = 54
    PAINTERS: Dict[str, Callable] = DEFAULT_PAINTERS

    def __init__(self, node_id, x, y, resource, style="herb",
                 amount: Tuple[int, int] = (1, 2), harvested=False):
        s = self.SIZE
        super().__init__(x, y, s, s, color=(0, 0, 0))
        self.node_id = str(node_id)
        self.resource_name = str(resource)
        self.style = str(style)
        self.min_amount, self.max_amount = int(amount[0]), int(amount[1])
        self.harvested = bool(harvested)
        self.image_pos = (x, y)
        # Matala hitbox jalkoihin, jotta noden taakse voi kävellä
        self.rect = pygame.Rect(x + 5, y + s // 2, s - 10, s // 2 - 4)
        self.blocks_projectiles = False
        self.is_structure = False
        self.has_shadow = self.style not in {"reeds", "herb", "clay"}
        self.interaction_range = 74
        self.interaction_label = f"Gather {self.resource_name}"
        self.type = "resource"
        self._redraw()

    def serialize_extra(self):
        return {"node_id": self.node_id, "resource": self.resource_name,
                "style": self.style,
                "amount": [self.min_amount, self.max_amount]}

    def _redraw(self):
        s = self.SIZE
        image = pygame.Surface((s, s), pygame.SRCALPHA)
        if self.harvested:
            # Tyhjä kuoppa/kanto: näkyy että tästä on jo kerätty
            pygame.draw.ellipse(image, (62, 56, 45, 100),
                                (8, s - 12, s - 16, 8))
        else:
            painter = self.PAINTERS.get(self.style, _paint_herb)
            painter(image, s)
        self.image = image

    def _after_harvest(self, manager, amount: int):
        """Karttakohtainen koukku (esim. harvested_nodes-listan päivitys)."""

    def harvest(self, manager) -> Optional[str]:
        if self.harvested:
            return None
        amount = random.randint(self.min_amount, self.max_amount)
        manager.inventory[self.resource_name] = (
            int(manager.inventory.get(self.resource_name, 0)) + amount)
        self.harvested = True
        self._after_harvest(manager, amount)
        self._redraw()
        _safe_sound("recruit")
        return f"+{amount} {self.resource_name}"


# ---------------------------------------------------------------------
# PORTIT: selvä sisään ja ulos
# ---------------------------------------------------------------------
class GateZone(Prop):
    """Sisään-/uloskäyntimerkki. kind: arch|sign|ladder|grate|portal.

    Piirtyy näkyvänä rakenteena + suuntanuolena, jotta pelaaja näkee
    heti mistä kenttään tullaan ja mistä lähdetään. Menut käyttävät
    rectiä siirtymän laukaisuun (interaction tai kosketus)."""

    def __init__(self, x, y, w=140, h=90, *, kind="arch", label="EXIT",
                 target=None, facing="down"):
        super().__init__(x, y, w, h, color=(0, 0, 0))
        self.kind = str(kind)
        self.label = str(label)
        self.target = target
        self.facing = str(facing)   # nuolen suunta: up/down/left/right
        self.is_gate = True
        self.is_structure = False
        self.blocks_projectiles = False
        self.has_shadow = False
        self.interaction_label = self.label
        self.image_pos = (x, y)
        self.rect = pygame.Rect(x, y, w, h)
        self.image = self._paint()

    def serialize_extra(self):
        return {"w": self.rect.w, "h": self.rect.h, "kind": self.kind,
                "label": self.label, "facing": self.facing}

    def _paint(self) -> pygame.Surface:
        w, h = self.rect.w, self.rect.h
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        if self.kind == "arch":
            # Kiviholvi: pielet + kaari + tumma aukko
            pygame.draw.rect(s, (30, 26, 32), (10, 14, w - 20, h - 18))
            for px in (0, w - 16):
                pygame.draw.rect(s, (108, 104, 112), (px, 8, 16, h - 8))
                pygame.draw.rect(s, (78, 74, 84), (px, 8, 16, h - 8), 2)
            pygame.draw.rect(s, (118, 114, 124), (0, 0, w, 16), border_radius=6)
            pygame.draw.rect(s, (84, 80, 92), (0, 0, w, 16), 2, border_radius=6)
        elif self.kind == "sign":
            # Tienviitta: tolppa + lautakyltti
            pygame.draw.rect(s, (96, 70, 44), (w // 2 - 4, 18, 8, h - 20))
            pygame.draw.rect(s, (140, 104, 62), (w // 2 - 46, 8, 92, 26), border_radius=4)
            pygame.draw.rect(s, (92, 66, 40), (w // 2 - 46, 8, 92, 26), 2, border_radius=4)
        elif self.kind == "ladder":
            for px in (w // 2 - 14, w // 2 + 10):
                pygame.draw.rect(s, (120, 92, 56), (px, 4, 5, h - 8))
            for py in range(10, h - 8, 12):
                pygame.draw.rect(s, (146, 112, 68), (w // 2 - 14, py, 29, 4))
        elif self.kind == "grate":
            pygame.draw.ellipse(s, (24, 22, 26), (4, 4, w - 8, h - 8))
            pygame.draw.ellipse(s, (96, 96, 104), (4, 4, w - 8, h - 8), 3)
            for i in range(1, 5):
                px = 4 + (w - 8) * i // 5
                pygame.draw.line(s, (96, 96, 104), (px, 8), (px, h - 8), 2)
        else:  # portal
            pygame.draw.ellipse(s, (60, 30, 90), (6, 4, w - 12, h - 8))
            pygame.draw.ellipse(s, (150, 90, 210), (6, 4, w - 12, h - 8), 3)
            pygame.draw.ellipse(s, (110, 70, 170), (w // 4, h // 4, w // 2, h // 2), 2)
        self._paint_arrow(s, w, h)
        return s

    def _paint_arrow(self, s, w, h):
        cx, cy = w // 2, h // 2
        size = 10
        col = (235, 210, 120)
        if self.facing == "down":
            pts = [(cx - size, h - 18), (cx + size, h - 18), (cx, h - 4)]
        elif self.facing == "up":
            pts = [(cx - size, 14), (cx + size, 14), (cx, 0)]
        elif self.facing == "left":
            pts = [(14, cy - size), (14, cy + size), (0, cy)]
        else:
            pts = [(w - 14, cy - size), (w - 14, cy + size), (w, cy)]
        pygame.draw.polygon(s, col, pts)

    def draw_on_screen(self, screen, offset=(0, 0)):
        super().draw_on_screen(screen, offset)
        # Nimilappu portin ylle - "mistä tullaan / minne mennään"
        try:
            from ui_kit import draw_text, font_small
            draw_text(self.label, font_small, (235, 220, 160), screen,
                      self.rect.centerx - offset[0] - 4 * len(self.label),
                      self.rect.top - offset[1] - 20)
        except Exception:
            pass


# ---------------------------------------------------------------------
# LUOLASTOT: seinät, lattiat ja käytävät
# ---------------------------------------------------------------------
_WALL_STYLES = {
    "crypt": ((66, 62, 74), (46, 42, 54), (92, 88, 102)),
    "rock": ((70, 62, 54), (50, 44, 38), (96, 86, 74)),
    "sewer": ((58, 64, 60), (40, 46, 42), (84, 92, 86)),
}

_FLOOR_STYLES = {
    "crypt": ((38, 36, 44), (46, 44, 54)),
    "rock": ((44, 39, 33), (52, 46, 39)),
    "sewer": ((40, 44, 42), (48, 53, 50)),
    "dirt": ((52, 44, 34), (60, 51, 40)),
}


class WallSegment(Prop):
    """Kiinteä seinäpala (estää kulun JA ammukset)."""

    def __init__(self, x, y, w, h, style="crypt"):
        super().__init__(x, y, w, h, color=(0, 0, 0))
        self.style = str(style)
        self.is_structure = True
        self.blocks_projectiles = True
        self.has_shadow = False
        self.image_pos = (x, y)
        self.rect = pygame.Rect(x, y, w, h)
        base, dark, light = _WALL_STYLES.get(self.style, _WALL_STYLES["crypt"])
        s = pygame.Surface((w, h))
        s.fill(base)
        rng = random.Random((x * 7919 + y * 104729) & 0xFFFF)
        # Tiiliriveittäin: joka toinen rivi puolikkaan sivussa
        bh = 22
        bw = 46
        for row, py in enumerate(range(0, h, bh)):
            off = (bw // 2) if row % 2 else 0
            for px in range(-off, w, bw):
                shade = rng.randint(-8, 8)
                col = tuple(max(0, min(255, c + shade)) for c in base)
                pygame.draw.rect(s, col, (px, py, bw - 2, bh - 2))
                pygame.draw.rect(s, dark, (px, py, bw - 2, bh - 2), 1)
        pygame.draw.rect(s, light, (0, 0, w, h), 2)
        self.image = s

    def serialize_extra(self):
        return {"w": self.rect.w, "h": self.rect.h, "style": self.style}


class FloorPatch(Prop):
    """Lattialaatta kammioon/käytävään (lattiakerros, ei este)."""

    def __init__(self, x, y, w, h, style="crypt"):
        super().__init__(x, y, w, h, color=(0, 0, 0))
        self.style = str(style)
        self.is_structure = False
        self.is_floor = True
        self.blocks_projectiles = False
        self.has_shadow = False
        self.image_pos = (x, y)
        self.rect = pygame.Rect(x, y, 0, 0)   # ei törmäystä
        base, alt = _FLOOR_STYLES.get(self.style, _FLOOR_STYLES["crypt"])
        s = pygame.Surface((w, h))
        s.fill(base)
        rng = random.Random((x * 31 + y * 17) & 0xFFFF)
        tile = 64
        for py in range(0, h, tile):
            for px in range(0, w, tile):
                if rng.random() < 0.5:
                    pygame.draw.rect(s, alt, (px, py, tile - 2, tile - 2))
                pygame.draw.rect(s, tuple(max(0, c - 8) for c in base),
                                 (px, py, tile, tile), 1)
        self.image = s
        self._w, self._h = w, h

    def serialize_extra(self):
        return {"w": self._w, "h": self._h, "style": self.style}

    def draw(self, screen, offset=(0, 0)):
        screen.blit(self.image, (self.image_pos[0] - offset[0],
                                 self.image_pos[1] - offset[1]))


def build_dungeon(walkables: Sequence[pygame.Rect], width: int, height: int,
                  *, cell: int = 40, wall_style: str = "crypt",
                  floor_style: str = "crypt",
                  shell: int = 2) -> Tuple[List[WallSegment], List[FloorPatch]]:
    """Rakentaa luolaston seinät kammio-/käytäväsuorakulmioista.

    walkables = huoneet + käytävät suorakulmioina. Seinäpalat syntyvät
    KUORENA kuljettavan alueen ympärille (shell x cell paksuus), joten
    kaukainen umpikallio ei tuota esteitä. Palauttaa (seinät, lattiat).
    """
    cols = max(1, int(math.ceil(width / cell)))
    rows = max(1, int(math.ceil(height / cell)))
    walk = [[False] * cols for _ in range(rows)]
    for rect in walkables:
        c0 = max(0, rect.left // cell)
        c1 = min(cols - 1, (rect.right - 1) // cell)
        r0 = max(0, rect.top // cell)
        r1 = min(rows - 1, (rect.bottom - 1) // cell)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                walk[r][c] = True

    def near_walkable(r, c):
        for dr in range(-shell, shell + 1):
            for dc in range(-shell, shell + 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < rows and 0 <= cc < cols and walk[rr][cc]:
                    return True
        return False

    wall_cells = [[(not walk[r][c]) and near_walkable(r, c)
                   for c in range(cols)] for r in range(rows)]

    # Yhdistä seinäsolut suorakulmioiksi: vaakajonot + identtisten
    # jonojen pystysuuntainen yhdistäminen (pitää estemäärän pienenä)
    runs_by_row: List[List[Tuple[int, int]]] = []
    for r in range(rows):
        runs = []
        c = 0
        while c < cols:
            if wall_cells[r][c]:
                start = c
                while c < cols and wall_cells[r][c]:
                    c += 1
                runs.append((start, c))
            else:
                c += 1
        runs_by_row.append(runs)

    walls: List[WallSegment] = []
    consumed = [set() for _ in range(rows)]
    for r in range(rows):
        for run in runs_by_row[r]:
            if run in consumed[r]:
                continue
            r2 = r
            while r2 + 1 < rows and run in runs_by_row[r2 + 1] \
                    and run not in consumed[r2 + 1]:
                r2 += 1
            for rr in range(r, r2 + 1):
                consumed[rr].add(run)
            x = run[0] * cell
            y = r * cell
            w = (run[1] - run[0]) * cell
            h = (r2 - r + 1) * cell
            walls.append(WallSegment(x, y, min(w, width - x),
                                     min(h, height - y), style=wall_style))

    floors = [FloorPatch(rect.x, rect.y, rect.w, rect.h, style=floor_style)
              for rect in walkables]
    return walls, floors


# ---------------------------------------------------------------------
# HAJAUTUS
# ---------------------------------------------------------------------
def spread_points(rng: random.Random, area: pygame.Rect, count: int,
                  min_dist: int = 90,
                  avoid: Sequence[pygame.Rect] = ()) -> List[Tuple[int, int]]:
    """Arpoo pisteitä alueelle niin, etteivät ne kasaudu päällekkäin
    eivätkä osu vältettäviin alueisiin (vesi, tiet, rakennukset)."""
    points: List[Tuple[int, int]] = []
    for _ in range(count * 40):
        if len(points) >= count:
            break
        x = rng.randint(area.left, max(area.left, area.right - 1))
        y = rng.randint(area.top, max(area.top, area.bottom - 1))
        if any(rect.collidepoint(x, y) for rect in avoid):
            continue
        if any(math.hypot(x - px, y - py) < min_dist for px, py in points):
            continue
        points.append((x, y))
    return points
