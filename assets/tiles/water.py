# assets/tiles/water.py
"""YKSI koodipiirretty vesimalli koko peliin (pelitesti 29).

Aiemmin vesiä oli KAKSI rinnakkaista toteutusta: tämä (suorakulmainen
lampi editorille) ja systems/procedural_water.py (orgaaniset rannat
retkikartoille). Ne on nyt yhdistetty: WaterBody kattaa molemmat.

- Orgaaninen rantaprofiili: per-rivi (vasen, oikea) -rajat kohinalla,
  sama geometria ajaa renderöinnin, törmäyksen JA kalastuksen.
- style="pond": profiili kapenee ylä-/alapäissä -> lampimainen möykky,
  ja pohjaan maalataan kaislat/lumpeet/pohjakivet.
- style="river": profiili kulkee koko matkan -> joki/kanava, pinnalle
  piirretään virtausraidat.
- style="lake": seisova avovesi ilman virtausraitoja ja taperia
  (tulva-altaat, suolammikot, isot poolit).
- style="auto" (oletus): river jos korkeus >= 1.6 x leveys.

Rajapinta (sama joka paikassa - kaupunki, retkikartat, editori):
  contains_point, bounds_at, span_rect, make_collision_barriers
  (ylityskaistoilla silloille/kahluupaikoille), fishing_anchors,
  add_ripple/splash, update, draw, serialize_extra.

Editori: carve_water upottaa altaan areenaan, rebuild_water_blockers
laskee esteet laituriaukkoineen. Kulkuesteet ovat WaterBlocker-
palasia (alias WaterBarrier vanhoille kutsujille).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import pygame

Color = Tuple[int, int, int]

DEEP = (24, 52, 58)
SHALLOW = (52, 96, 92)
MID = (36, 74, 76)
BANK_MUD = (74, 58, 40)
BANK_MUD_DARK = (56, 44, 30)
FOAM = (168, 196, 188)
GLINT = (190, 225, 215)
REED = (74, 108, 58)
REED_DARK = (52, 82, 44)
LILY = (66, 118, 66)


@dataclass(frozen=True)
class FishingAnchor:
    """Pysyvä maailmankoordinaattipiste kalastusta varten."""

    x: int
    y: int
    bank: str
    water_name: str
    difficulty: int = 1
    fish_table: str = "muckford_marsh"


class WaterBlocker:
    """Näkymätön este veden päälle (kulku estyy, ammukset lentävät yli).

    Yhteensopiva obstacles-listojen kanssa: .rect, .blocks_projectiles,
    .is_structure jne. Ei kuvaa - itse vesi piirretään WaterBodyssä.
    Hyväksyy WaterBlocker(x, y, w, h) TAI WaterBlocker(rect).
    """

    def __init__(self, x, y=None, w=None, h=None):
        if y is None:
            self.rect = pygame.Rect(x)
        else:
            self.rect = pygame.Rect(int(x), int(y), int(w), int(h))
        self.image_pos = self.rect.topleft
        self.image = None
        self.blocks_projectiles = False
        self.is_structure = True
        self.is_water = True
        self.is_dead = False
        self.type = "water"
        self.name = "Water"
        self.team_color = "Neutral"

    def draw_on_screen(self, *_args, **_kwargs):
        return None


# Vanha nimi retkikartoille (systems/procedural_water.py poistettu)
WaterBarrier = WaterBlocker


def _rect_from_args(x, y, w, h):
    """Tukee sekä WaterBody(x, y, w, h) että WaterBody(rect)."""
    if y is None:
        return pygame.Rect(x)
    return pygame.Rect(int(x), int(y), int(w), int(h))


class WaterBody:
    """Animoitu vesialue: lampi TAI joki, sama luokka joka kartalle."""

    def __init__(self, x, y=None, w=400, h=300, seed=7, *,
                 name="water",
                 style="auto",
                 flow: Tuple[float, float] = (0.35, 1.0),
                 shore_variance=None,
                 deep_margin=42,
                 shallow_color: Color = SHALLOW,
                 mid_color: Color = MID,
                 deep_color: Color = DEEP,
                 foam_color: Color = FOAM):
        self.rect = _rect_from_args(x, y, w, h)
        self.seed = int(seed)
        self.name = str(name)
        self.flow = flow
        if style == "auto":
            style = "river" if self.rect.h >= self.rect.w * 1.6 else "pond"
        self.style = style
        if shore_variance is None:
            shore_variance = max(12, min(40, self.rect.w // 12))
        self.shore_variance = max(0, int(shore_variance))
        self.deep_margin = max(12, int(deep_margin))
        self.shallow_color = shallow_color
        self.mid_color = mid_color
        self.deep_color = deep_color
        self.foam_color = foam_color

        self._sample_step = 48
        self._profile = self._build_profile()
        self.base = self._build_static_surface()
        self._glints = self._build_glints()
        self._ripples: List[Tuple[int, int, int]] = []
        self._ripple_timer = random.Random(seed * 31 + 1).randint(40, 120)
        self._rng = random.Random(seed * 31 + 1)

    # Karttaeditorin serialisointi + ghost-esikatselu
    @property
    def image(self):
        return self.base

    @property
    def image_pos(self):
        return self.rect.topleft

    @image_pos.setter
    def image_pos(self, pos):
        self.rect.topleft = (int(pos[0]), int(pos[1]))

    def serialize_extra(self):
        return {"w": self.rect.w, "h": self.rect.h, "seed": self.seed,
                "name": self.name, "style": self.style}

    # ------------------------------------------------------ geometria
    def _build_profile(self) -> List[Tuple[int, int, int]]:
        """Per-rivi (y, vasen, oikea) -rajat. Sama profiili ajaa piirron,
        törmäyksen ja kalastuksen - ranta ei voi erota pelattavuudesta."""
        rng = random.Random(self.seed)
        samples: List[Tuple[int, int, int]] = []
        left_noise = rng.randint(-self.shore_variance, self.shore_variance)
        right_noise = rng.randint(-self.shore_variance, self.shore_variance)
        height = self.rect.height
        y = 0
        while y <= height + self._sample_step:
            left_noise = int(left_noise * 0.62 + rng.randint(-18, 18))
            right_noise = int(right_noise * 0.62 + rng.randint(-18, 18))
            left_noise = max(-self.shore_variance,
                             min(self.shore_variance, left_noise))
            right_noise = max(-self.shore_variance,
                              min(self.shore_variance, right_noise))
            left = 18 + left_noise
            right = self.rect.width - 18 + right_noise

            if self.style == "pond":
                # Lampi: kavenna profiilia ylä- ja alapäissä (möykky)
                py = min(y, height)
                edge = min(py, height - py) / max(1.0, height * 0.5)
                taper = 1.0 - min(1.0, edge * 2.6)   # 1 reunalla, 0 keskellä
                pinch = taper * self.rect.width * 0.34
                left += pinch
                right -= pinch

            if right - left < 40:
                mid = (left + right) / 2
                left, right = mid - 20, mid + 20
            samples.append((y, int(left), int(right)))
            y += self._sample_step
        return samples

    def _local_bounds_at(self, local_y: float) -> Tuple[float, float]:
        y = max(0.0, min(float(local_y), float(self.rect.height)))
        index = min(int(y // self._sample_step), len(self._profile) - 2)
        y0, left0, right0 = self._profile[index]
        y1, left1, right1 = self._profile[index + 1]
        span = max(1.0, float(y1 - y0))
        t = (y - y0) / span
        return (left0 + (left1 - left0) * t,
                right0 + (right1 - right0) * t)

    def bounds_at(self, world_y: float) -> Tuple[float, float]:
        left, right = self._local_bounds_at(world_y - self.rect.top)
        return self.rect.left + left, self.rect.left + right

    def contains_point(self, point: Sequence[float], inset: int = 0) -> bool:
        x, y = float(point[0]), float(point[1])
        if not (self.rect.top <= y <= self.rect.bottom):
            return False
        left, right = self.bounds_at(y)
        return left + inset <= x <= right - inset

    def span_rect(self, world_y: int, height: int = 86,
                  padding: int = 36) -> pygame.Rect:
        left, right = self.bounds_at(world_y)
        return pygame.Rect(int(left - padding), int(world_y - height // 2),
                           int((right - left) + padding * 2), int(height))

    def make_collision_barriers(
        self,
        crossing_bands: Iterable[Tuple[int, int]] = (),
        *,
        slice_height: int = 58,
        inset: int = 10,
    ) -> List[WaterBlocker]:
        """Rantaviivaa seuraavat esteet; ylityskaistat jäävät auki
        (sillat, kahluupaikat, laiturit)."""
        bands = [(int(a), int(b)) for a, b in crossing_bands]
        barriers: List[WaterBlocker] = []
        y = self.rect.top
        while y < self.rect.bottom:
            h = min(slice_height, self.rect.bottom - y)
            center_y = y + h // 2
            if any(start <= center_y <= end for start, end in bands):
                y += h
                continue
            left, right = self.bounds_at(center_y)
            width = max(8, int(right - left) - inset * 2)
            barriers.append(WaterBlocker(int(left) + inset, y, width, h + 1))
            y += h
        return barriers

    def fishing_anchors(self, count: int = 6,
                        difficulty: int = 1) -> List[FishingAnchor]:
        """Deterministiset rantapisteet kalastusta varten."""
        rng = random.Random(self.seed + 913)
        anchors: List[FishingAnchor] = []
        margin = min(150, self.rect.height // 4)
        usable = max(1, self.rect.height - margin * 2)
        for index in range(max(1, int(count))):
            local_y = margin + int((index + 0.5) * usable / max(1, count))
            local_y += rng.randint(-55, 55)
            local_y = max(10, min(self.rect.height - 10, local_y))
            world_y = self.rect.top + local_y
            left, right = self.bounds_at(world_y)
            bank = "left" if index % 2 == 0 else "right"
            x = int(left - 30) if bank == "left" else int(right + 30)
            anchors.append(FishingAnchor(x=x, y=int(world_y), bank=bank,
                                         water_name=self.name,
                                         difficulty=int(difficulty)))
        return anchors

    # ------------------------------------------------------ pohjapinta
    def _polygon(self, inset: int = 0) -> List[Tuple[int, int]]:
        left_points = []
        right_points = []
        for y, left, right in self._profile:
            py = min(y, self.rect.height)
            if right - inset <= left + inset:
                mid = (left + right) // 2
                left_points.append((int(mid - 2), int(py)))
                right_points.append((int(mid + 2), int(py)))
            else:
                left_points.append((int(left + inset), int(py)))
                right_points.append((int(right - inset), int(py)))
        return left_points + list(reversed(right_points))

    def _build_static_surface(self) -> pygame.Surface:
        s = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        poly = self._polygon(0)
        pygame.draw.polygon(s, (*self.shallow_color, 255), poly)
        pygame.draw.polygon(s, (*self.mid_color, 255),
                            self._polygon(max(14, self.deep_margin // 2)))
        pygame.draw.polygon(s, (*self.deep_color, 255),
                            self._polygon(self.deep_margin))

        # Mutaranta polygonin reunaan + vaalea vesiraja
        pygame.draw.polygon(s, BANK_MUD, poly, 6)
        pygame.draw.polygon(s, BANK_MUD_DARK, poly, 2)
        pygame.draw.polygon(s, (96, 148, 138), self._polygon(7), 2)

        rng = random.Random(self.seed + 77)

        # Upoksissa oleva laikutus antaa syvyyttä ilman tekstuuria
        for _ in range(max(12, self.rect.height // 22)):
            local_y = rng.randrange(0, max(1, self.rect.height))
            left, right = self._local_bounds_at(local_y)
            if right - left < self.deep_margin * 2 + 20:
                continue
            x = rng.randint(int(left + self.deep_margin),
                            int(right - self.deep_margin))
            radius = rng.randint(8, 28)
            pygame.draw.ellipse(
                s, (12, 42, 59, rng.randint(15, 34)),
                pygame.Rect(x - radius, local_y - radius // 3,
                            radius * 2, radius))

        if self.style == "pond":
            self._paint_pond_decor(s, rng)
        return s

    def _paint_pond_decor(self, s, rng):
        """Lammen koristeet: pohjakivet matalikossa, kaislatupsut
        rannoilla, lumpeenlehdet keskialueella."""
        w, h = self.rect.size
        # Pohjakivet ylä-/alarannan matalikkoon
        for _ in range(w * h // 60000 + 4):
            local_y = rng.choice((rng.randint(10, 26), h - rng.randint(14, 30)))
            left, right = self._local_bounds_at(local_y)
            if right - left < 40:
                continue
            rx = rng.randint(int(left + 8), int(right - 16))
            rr = rng.randint(3, 7)
            pygame.draw.ellipse(s, (66, 84, 82), (rx, local_y, rr * 2, rr))
            pygame.draw.ellipse(s, (88, 108, 104),
                                (rx + 1, local_y + 1, rr, rr // 2 + 1))
        # Kaislatupsut rantaviivalle
        for _ in range(w // 90 + 3):
            local_y = rng.choice((rng.randint(4, 16), h - rng.randint(8, 20)))
            left, right = self._local_bounds_at(local_y)
            if right - left < 30:
                continue
            cx = rng.randint(int(left + 6), int(right - 6))
            for k in range(rng.randint(3, 6)):
                bx = cx + rng.randint(-10, 10)
                tip_x = bx + rng.randint(-4, 4)
                tall = rng.randint(12, 26)
                col = REED if k % 2 else REED_DARK
                pygame.draw.line(s, col, (bx, local_y), (tip_x, local_y - tall), 2)
                pygame.draw.ellipse(s, col, (tip_x - 2, local_y - tall - 5, 4, 7))
        # Lumpeenlehdet
        for _ in range(max(2, w * h // 140000)):
            ly = rng.randint(h // 5, h * 4 // 5)
            left, right = self._local_bounds_at(ly)
            if right - left < 70:
                continue
            lx = rng.randint(int(left + 20), int(right - 40))
            lw = rng.randint(14, 26)
            pygame.draw.ellipse(s, LILY, (lx, ly, lw, lw * 2 // 3))
            pygame.draw.ellipse(s, (44, 88, 48), (lx, ly, lw, lw * 2 // 3), 2)
            pygame.draw.polygon(s, self.deep_color,
                                [(lx + lw // 2, ly + lw // 3),
                                 (lx + lw, ly), (lx + lw, ly + lw // 3)])

    def _build_glints(self):
        rng = random.Random(self.seed + 311)
        glints = []
        count = max(12, self.rect.height // 70 + self.rect.width // 120)
        for _ in range(count):
            local_y = rng.randint(25, max(26, self.rect.height - 25))
            left, right = self._local_bounds_at(local_y)
            if right - left < 40:
                continue
            u = rng.random()
            x = int(left + (right - left) * u)
            glints.append((x, local_y, rng.random() * math.tau,
                           rng.randint(6, 22)))
        return glints

    @property
    def ripples(self):
        """Aktiiviset väreilyrenkaat (julkinen lukurajapinta testeille)."""
        return self._ripples

    # ------------------------------------------------------ elo
    def add_ripple(self, world_pos: Sequence[int], now_ms=None) -> None:
        if not self.contains_point(world_pos):
            return
        timestamp = pygame.time.get_ticks() if now_ms is None else int(now_ms)
        self._ripples.append((int(world_pos[0]), int(world_pos[1]), timestamp))

    def splash(self, world_x, world_y):
        """Ulkoinen roiske (esim. kalastuskoho) -> väreilyrengas."""
        self.add_ripple((world_x, world_y))

    def update(self, obstacles=None, manager=None, **kwargs):
        """Spontaanit väreet (lattiakerroksen update-polku editorissa ja
        kaupungissa). Retkikartat voivat kutsua add_ripple itse."""
        self._ripple_timer -= 1
        if self._ripple_timer <= 0:
            self._ripple_timer = self._rng.randint(50, 160)
            local_y = self._rng.randint(16, max(17, self.rect.height - 16))
            left, right = self._local_bounds_at(local_y)
            if right - left > 40:
                x = self._rng.randint(int(left + 15), int(right - 15))
                self.add_ripple((self.rect.left + x, self.rect.top + local_y))

    def draw(self, screen: pygame.Surface, offset=(0, 0), now_ms=None) -> None:
        ox, oy = int(offset[0]), int(offset[1])
        # Piirrä vain näkyvä osa (iso allas ei maksa ruudun ulkopuolella)
        view = screen.get_rect().move(ox, oy)
        vis = self.rect.clip(view)
        if vis.w <= 0 or vis.h <= 0:
            return
        sub = self.base.subsurface((vis.x - self.rect.x, vis.y - self.rect.y,
                                    vis.w, vis.h))
        screen.blit(sub, (vis.x - ox, vis.y - oy))

        now = pygame.time.get_ticks() if now_ms is None else int(now_ms)
        t = now * 0.001
        flow_x, flow_y = self.flow
        view_top = max(self.rect.top, oy - 40)
        view_bottom = min(self.rect.bottom, oy + screen.get_height() + 40)
        if view_bottom <= view_top:
            return

        # Virtausraidat (vain joet - lammessa vesi seisoo)
        if self.style == "river":
            start_y = int(view_top // 30) * 30
            for world_y in range(start_y, int(view_bottom) + 1, 30):
                left, right = self.bounds_at(world_y)
                width = right - left
                if width < 70:
                    continue
                points = []
                for step in range(6):
                    u = step / 5.0
                    x = left + 24 + (width - 48) * u
                    y = world_y + math.sin(t * 1.7 + u * 5.5
                                           + world_y * 0.026) * 3.2
                    x += math.sin(t * 0.65 + world_y * 0.012) * flow_x * 8
                    y += math.sin(t * 0.55) * flow_y * 1.8
                    points.append((int(x - ox), int(y - oy)))
                pygame.draw.aalines(screen, (75, 132, 145), False, points)

        # Rantavaahto molemmille rannoille (kulkee virtauksen mukana)
        foam_start = int(view_top // 18) * 18
        for world_y in range(foam_start, int(view_bottom) + 1, 18):
            left, right = self.bounds_at(world_y)
            if right - left < 30:
                continue
            wobble = math.sin(t * 2.4 + world_y * 0.052) * 5.5
            lx = int(left + 8 + wobble - ox)
            rx = int(right - 8 - wobble - ox)
            sy = int(world_y - oy)
            length = 6 + int((math.sin(t * 1.9 + world_y) + 1.0) * 3)
            pygame.draw.line(screen, self.foam_color, (lx, sy),
                             (lx + length, sy + 2), 2)
            pygame.draw.line(screen, self.foam_color, (rx, sy),
                             (rx - length, sy + 2), 2)
            if (world_y // 18) % 3 == 0:
                pygame.draw.circle(screen, (215, 232, 222), (lx + 2, sy - 2), 2)
                pygame.draw.circle(screen, (215, 232, 222), (rx - 2, sy - 2), 2)

        # Kimalluspilkut (sykkivät, ajelehtivat virtauksessa)
        for gx, gy, phase, length in self._glints:
            world_y = self.rect.top + gy
            if not (view_top <= world_y <= view_bottom):
                continue
            pulse = (math.sin(t * 2.2 + phase) + 1.0) * 0.5
            if pulse < 0.42:
                continue
            drift = math.sin(t * 0.8 + phase) * 5 * flow_x
            sx = int(self.rect.left + gx + drift - ox)
            sy = int(world_y + math.sin(t + phase) * 2 - oy)
            draw_len = max(3, int(length * pulse))
            pygame.draw.line(screen, (150, 190, 190), (sx, sy),
                             (sx + draw_len, sy), 1)

        # Laajenevat väreilyrenkaat (sade, olennot, kalastus)
        alive: List[Tuple[int, int, int]] = []
        for x, y, started in self._ripples:
            age = now - started
            if age >= 1800:
                continue
            alive.append((x, y, started))
            radius = 4 + int(age * 0.026)
            fade = max(40, 170 - int(age * 0.075))
            layer = pygame.Surface((radius * 2 + 6, radius + 8),
                                   pygame.SRCALPHA)
            pygame.draw.ellipse(layer, (175, 218, 218, fade),
                                pygame.Rect(3, 3, radius * 2,
                                            max(4, radius // 2)), 1)
            screen.blit(layer, (x - radius - ox, y - radius // 3 - oy))
        self._ripples = alive


# Vanha nimi: retkikartat loivat "ProceduralWaterBody(rect, ...)" -
# sama luokka, polymorfinen konstruktori hoitaa rect-muodon.
ProceduralWaterBody = WaterBody


class FishingJetty:
    """Puinen laituri joka ulottuu veteen - lattiakerros, kävelykelpoinen."""

    def __init__(self, x, y, w=170, h=64, seed=3):
        self.rect = pygame.Rect(int(x), int(y), int(w), int(h))
        self.seed = seed
        rng = random.Random(seed)
        s = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        plank_h = 12
        for py in range(0, self.rect.h, plank_h):
            shade = rng.randint(-10, 10)
            col = (110 + shade, 82 + shade, 52 + shade)
            pygame.draw.rect(s, col, (0, py, self.rect.w, plank_h - 2))
            pygame.draw.line(s, (70, 52, 34), (0, py + plank_h - 2),
                             (self.rect.w, py + plank_h - 2), 2)
        # Reunapaalut
        for px in (2, self.rect.w - 8):
            for py in (2, self.rect.h - 10):
                pygame.draw.rect(s, (78, 58, 38), (px, py, 6, 8))
                pygame.draw.rect(s, (52, 40, 26), (px, py, 6, 8), 1)
        self.image = s

    def update(self, *args, **kwargs):
        pass

    @property
    def image_pos(self):
        return self.rect.topleft

    @image_pos.setter
    def image_pos(self, pos):
        self.rect.topleft = (int(pos[0]), int(pos[1]))

    def serialize_extra(self):
        return {"w": self.rect.w, "h": self.rect.h, "seed": self.seed}

    def draw(self, screen, offset=(0, 0)):
        screen.blit(self.image, (self.rect.x - offset[0],
                                 self.rect.y - offset[1]))


def _subtract_rect(pieces, hole):
    """Vähentää holen jokaisesta palasta (max 4 uutta palaa/pala).
    Näin joessa voi olla monta laituria/siltakaistaa."""
    result = []
    for r in pieces:
        cut = r.clip(hole)
        if cut.w <= 0 or cut.h <= 0:
            result.append(r)
            continue
        if cut.top > r.top:
            result.append(pygame.Rect(r.x, r.y, r.w, cut.top - r.top))
        if cut.bottom < r.bottom:
            result.append(pygame.Rect(r.x, cut.bottom, r.w,
                                      r.bottom - cut.bottom))
        if cut.left > r.left:
            result.append(pygame.Rect(r.x, cut.top, cut.left - r.left, cut.h))
        if cut.right < r.right:
            result.append(pygame.Rect(cut.right, cut.top,
                                      r.right - cut.right, cut.h))
    return [p for p in result if p.w > 0 and p.h > 0]


def _jetty_tip(jetty_rect, water_rect):
    """Kalastuspiste laiturin kärjen edessä (kärki = veden keskustaa
    lähinnä oleva pää)."""
    j = jetty_rect
    dx = water_rect.centerx - j.centerx
    dy = water_rect.centery - j.centery
    if abs(dx) >= abs(dy):
        return (j.right + 46, j.centery) if dx >= 0 else (j.left - 46, j.centery)
    return (j.centerx, j.bottom + 46) if dy >= 0 else (j.centerx, j.top - 46)


def rebuild_water_blockers(arena):
    """Laskee kaikkien vesien kulkuesteet uudelleen laituriaukkoineen.

    Kutsutaan aina kun vesiä/laitureita lisätään, poistetaan tai
    siirretään (karttaeditori). Esteet seuraavat rantaviivaa
    (make_collision_barriers) ja laiturit leikkaavat niihin aukot.
    Asettaa arena.fishing_spots-listan (+ vanhat aliakset).
    """
    arena.obstacles[:] = [o for o in arena.obstacles
                          if not getattr(o, "is_water", False)]
    waters = [p for p in arena.floor_props if isinstance(p, WaterBody)]
    jetties = [p for p in arena.floor_props if isinstance(p, FishingJetty)]

    spots = []
    for water in waters:
        for barrier in water.make_collision_barriers(()):
            pieces = [pygame.Rect(barrier.rect)]
            for jetty in jetties:
                if jetty.rect.colliderect(barrier.rect):
                    pieces = _subtract_rect(pieces, jetty.rect.inflate(4, 4))
            for piece in pieces:
                arena.obstacles.append(WaterBlocker(piece.x, piece.y,
                                                    piece.w, piece.h))
    for jetty in jetties:
        touching = [w for w in waters if jetty.rect.colliderect(
            w.rect.inflate(80, 80))]
        if touching:
            spots.append(_jetty_tip(jetty.rect, touching[0].rect))

    arena.fishing_spots = spots
    # Yhteensopivuus: vanha yhden lammen rajapinta
    arena.fishing_pond = pygame.Rect(waters[0].rect) if waters else None
    arena.fishing_jetty = pygame.Rect(jetties[0].rect) if jetties else None
    arena.fishing_spot = spots[0] if spots else None


def carve_water(arena, rect, seed=11, name="water", style="auto"):
    """Upottaa vesialueen areenaan: siivoaa alle jäävät propit, lisää
    WaterBodyn lattiakerrokseen ja laskee esteet. Palauttaa WaterBodyn."""
    area = pygame.Rect(rect)
    clear = area.inflate(60, 60)
    for prop in list(arena.props):
        if clear.colliderect(prop.rect):
            arena.props.remove(prop)
            if prop in arena.obstacles:
                arena.obstacles.remove(prop)
    water = WaterBody(area.x, area.y, area.w, area.h, seed=seed,
                      name=name, style=style)
    arena.floor_props.append(water)
    rebuild_water_blockers(arena)
    return water


def carve_pond(arena, pond_rect, jetty_side="left", seed=11):
    """Lampi + laituri länsirannalta. Palauttaa (water, jetty)."""
    pond = pygame.Rect(pond_rect)
    water = carve_water(arena, pond, seed=seed, style="pond")
    jw, jh = 170, 64
    jetty = FishingJetty(pond.x - 26, pond.centery - jh // 2, jw, jh,
                         seed=seed + 1)
    arena.floor_props.append(jetty)
    rebuild_water_blockers(arena)
    return water, jetty
