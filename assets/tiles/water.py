# assets/tiles/water.py
"""Koodipiirretty vesi: lampi/joki ilman kuvatiedostoja.

Pohja renderöidään KERRAN (syvyysliukuma, mutarannat, kaislikot,
lumpeenlehdet, pohjakivet) ja päälle piirretään joka frame kevyet
animoidut kerrokset: kulkevat aallonharjat, kimaltavat valopilkut,
rantavaahto ja satunnaiset laajenevat väreilyrenkaat. Piirto rajataan
näkyvään osaan, joten iso allas ei maksa ruudun ulkopuolella mitään.

Vesi lisätään arena.floor_props-listaan (draw(screen, offset) +
update(manager=...)) ja kulku estetään erillisillä WaterBlocker-
esteillä, jotta laiturille jää aukko.
"""

from __future__ import annotations

import math
import random

import pygame

DEEP = (24, 52, 58)
SHALLOW = (52, 96, 92)
BANK_MUD = (74, 58, 40)
BANK_MUD_DARK = (56, 44, 30)
FOAM = (168, 196, 188)
GLINT = (190, 225, 215)
REED = (74, 108, 58)
REED_DARK = (52, 82, 44)
LILY = (66, 118, 66)


class WaterBlocker:
    """Näkymätön este veden päälle (kulku + ammukset eivät kulje).

    Yhteensopiva obstacles-listan kanssa: .rect, .blocks_projectiles,
    .is_structure. Ei kuvaa - itse vesi piirretään WaterBodyssä.
    """

    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(int(x), int(y), int(w), int(h))
        self.blocks_projectiles = False   # nuoli voi lentää veden yli
        self.is_structure = True
        self.is_water = True
        self.type = "water"
        self.name = "Water"


class WaterBody:
    """Animoitu vesialue lattiakerrokseen."""

    def __init__(self, x, y, w=400, h=300, seed=7):
        self.rect = pygame.Rect(int(x), int(y), int(w), int(h))
        self.seed = seed
        self._t = random.random() * 100.0
        rng = random.Random(seed)
        self.base = self._paint_base(rng)
        self.image = self.base   # editorin ghost-esikatselulle

        # Kimalluspisteet: (rx, ry, vaihe, nopeus) suhteessa altaan kulmaan
        self.glints = []
        for _ in range(max(10, (w * h) // 22000)):
            self.glints.append((rng.randint(14, w - 14),
                                rng.randint(14, h - 14),
                                rng.random() * math.tau,
                                0.7 + rng.random() * 1.2))

        # Aktiiviset väreilyrenkaat: [x, y, sade, max]
        self.ripples = []
        self._ripple_timer = rng.randint(40, 120)
        self._rng = random.Random(seed * 31 + 1)

        # Ajelehtivat pinnan pilkut (vaahtoa/lehtiä virtauksessa)
        self.drifters = []
        for _ in range(max(4, (w * h) // 60000)):
            self.drifters.append((rng.randint(10, h - 10),
                                  rng.random(),
                                  8 + rng.random() * 18))

    # Karttaeditorin serialisointi (save/load project)
    @property
    def image_pos(self):
        return self.rect.topleft

    def serialize_extra(self):
        return {"w": self.rect.w, "h": self.rect.h, "seed": self.seed}

    # ------------------------------------------------------------- pohja
    def _paint_base(self, rng) -> pygame.Surface:
        w, h = self.rect.w, self.rect.h
        s = pygame.Surface((w, h), pygame.SRCALPHA)

        # Syvyysliukuma: reunoilta matalaa (vaaleampaa), keskeltä syvää
        for row in range(h):
            edge = min(row, h - 1 - row) / max(1, h // 2)
            t = min(1.0, edge * 1.6)
            color = tuple(int(SHALLOW[i] + (DEEP[i] - SHALLOW[i]) * t)
                          for i in range(3))
            pygame.draw.line(s, color, (0, row), (w, row))
        # Vaakasuuntainen tummennus keskelle (syvänne)
        depth = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(depth, (10, 24, 30, 90),
                            (w // 6, h // 5, w * 2 // 3, h * 3 // 5))
        s.blit(depth, (0, 0))

        # Pyöristetyt kulmat: maski leikkaa altaan luonnollisemmaksi
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        mask.fill((255, 255, 255, 0))
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h),
                         border_radius=26)
        s.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # Mutaranta reunoille + vaalea vesiraja rannan sisäpuolelle
        pygame.draw.rect(s, BANK_MUD, (0, 0, w, h), 7, border_radius=26)
        pygame.draw.rect(s, BANK_MUD_DARK, (0, 0, w, h), 3, border_radius=26)
        pygame.draw.rect(s, (96, 148, 138), (6, 6, w - 12, h - 12), 2,
                         border_radius=20)

        # Pohjakivet matalikossa
        for _ in range(w * h // 60000 + 4):
            rx = rng.randint(12, w - 20)
            ry = rng.choice((rng.randint(8, 22), h - rng.randint(14, 26)))
            rr = rng.randint(3, 7)
            pygame.draw.ellipse(s, (66, 84, 82), (rx, ry, rr * 2, rr))
            pygame.draw.ellipse(s, (88, 108, 104), (rx + 1, ry + 1, rr, rr // 2 + 1))

        # Kaislikot rannoille (tupsuina)
        for _ in range(w // 90 + 3):
            cx = rng.randint(16, w - 16)
            cy = rng.choice((rng.randint(2, 10), h - rng.randint(4, 12)))
            for k in range(rng.randint(3, 6)):
                bx = cx + rng.randint(-10, 10)
                tip_x = bx + rng.randint(-4, 4)
                tall = rng.randint(12, 26)
                col = REED if k % 2 else REED_DARK
                pygame.draw.line(s, col, (bx, cy), (tip_x, cy - tall), 2)
                pygame.draw.ellipse(s, col, (tip_x - 2, cy - tall - 5, 4, 7))

        # Lumpeenlehdet
        for _ in range(max(2, w * h // 140000)):
            lx = rng.randint(w // 6, w * 5 // 6)
            ly = rng.randint(h // 5, h * 4 // 5)
            lw = rng.randint(14, 26)
            pygame.draw.ellipse(s, LILY, (lx, ly, lw, lw * 2 // 3))
            pygame.draw.ellipse(s, (44, 88, 48), (lx, ly, lw, lw * 2 // 3), 2)
            pygame.draw.polygon(s, DEEP, [(lx + lw // 2, ly + lw // 3),
                                          (lx + lw, ly),
                                          (lx + lw, ly + lw // 3)])
        return s

    # ------------------------------------------------------------- elo
    def splash(self, world_x, world_y):
        """Ulkoinen roiske (esim. koho tipahtaa) -> väreilyrengas."""
        self.ripples.append([world_x - self.rect.x, world_y - self.rect.y,
                             2.0, 26])

    def update(self, obstacles=None, manager=None, **kwargs):
        self._t += 1.0 / 60.0
        self._ripple_timer -= 1
        if self._ripple_timer <= 0:
            self._ripple_timer = self._rng.randint(50, 160)
            self.ripples.append([self._rng.randint(20, self.rect.w - 20),
                                 self._rng.randint(16, self.rect.h - 16),
                                 2.0, self._rng.randint(14, 24)])
        for r in self.ripples:
            r[2] += 0.45
        self.ripples = [r for r in self.ripples if r[2] < r[3]]

    def draw(self, screen, offset=(0, 0)):
        # Näkyvä osa ruudulla
        view = screen.get_rect().move(offset)
        vis = self.rect.clip(view)
        if vis.w <= 0 or vis.h <= 0:
            return
        sub = self.base.subsurface((vis.x - self.rect.x, vis.y - self.rect.y,
                                    vis.w, vis.h))
        dx, dy = vis.x - offset[0], vis.y - offset[1]
        screen.blit(sub, (dx, dy))

        t = self._t

        # Kulkevat aallonharjat: katkoviivamaiset vaaleat kaaret
        local_top = vis.y - self.rect.y
        for band in range(3):
            base_y = (self.rect.h * (band + 1)) // 4
            phase = t * (18 + band * 7)
            for seg_x in range(0, vis.w, 46):
                wx = vis.x - self.rect.x + seg_x
                wy = base_y + math.sin((wx + phase * 8) * 0.02 + band) * 6
                if not (local_top - 8 <= wy <= local_top + vis.h + 8):
                    continue
                sy = int(wy - local_top)
                alpha_seg = pygame.Surface((26, 2), pygame.SRCALPHA)
                shade = 40 + int(24 * math.sin(t * 2 + wx * 0.05 + band))
                alpha_seg.fill((FOAM[0], FOAM[1], FOAM[2], max(16, shade)))
                screen.blit(alpha_seg, (dx + seg_x + int(math.sin(t + band) * 6),
                                        dy + sy))

        # Kimalluspilkut (sykkivä koko/alfa)
        for gx, gy, ph, spd in self.glints:
            if not (vis.x - self.rect.x <= gx <= vis.x - self.rect.x + vis.w):
                continue
            if not (vis.y - self.rect.y <= gy <= vis.y - self.rect.y + vis.h):
                continue
            pulse = (math.sin(t * spd * 3 + ph) + 1) / 2
            if pulse < 0.55:
                continue
            size = 1 + int(pulse * 2)
            gsurf = pygame.Surface((size * 2 + 2, size + 2), pygame.SRCALPHA)
            gsurf.fill((GLINT[0], GLINT[1], GLINT[2], int(90 * pulse)))
            screen.blit(gsurf, (dx + gx - (vis.x - self.rect.x),
                                dy + gy - (vis.y - self.rect.y)))

        # Rantavaahto ylä- ja alareunaan (wiggle)
        for edge_y, direction in ((3, 1), (self.rect.h - 5, -1)):
            if not (vis.y - self.rect.y - 6 <= edge_y <=
                    vis.y - self.rect.y + vis.h + 6):
                continue
            sy = dy + edge_y - (vis.y - self.rect.y)
            for seg_x in range(0, vis.w, 30):
                wig = math.sin(t * 3 + (vis.x + seg_x) * 0.04) * 2
                foam = pygame.Surface((16, 2), pygame.SRCALPHA)
                foam.fill((FOAM[0], FOAM[1], FOAM[2], 70))
                screen.blit(foam, (dx + seg_x, sy + int(wig) * direction))

        # Ajelehtivat pilkut: kulkevat hitaasti oikealle (virtauksen tuntu)
        for drift_y, phase, speed in self.drifters:
            wx = (phase * self.rect.w + t * speed) % self.rect.w
            wy = drift_y + math.sin(t * 0.8 + phase * 9) * 4
            if not (vis.x - self.rect.x <= wx <= vis.x - self.rect.x + vis.w):
                continue
            if not (vis.y - self.rect.y <= wy <= vis.y - self.rect.y + vis.h):
                continue
            speck = pygame.Surface((5, 3), pygame.SRCALPHA)
            speck.fill((FOAM[0], FOAM[1], FOAM[2], 60))
            screen.blit(speck, (dx + wx - (vis.x - self.rect.x),
                                dy + wy - (vis.y - self.rect.y)))

        # Väreilyrenkaat
        for rx, ry, radius, max_r in self.ripples:
            if not (vis.x - self.rect.x - 30 <= rx <=
                    vis.x - self.rect.x + vis.w + 30):
                continue
            fade = max(0, 1.0 - radius / max_r)
            ring = pygame.Surface((int(radius * 2) + 4, int(radius * 2) + 4),
                                  pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (GLINT[0], GLINT[1], GLINT[2],
                                       int(110 * fade)),
                                (2, 2 + radius // 3, radius * 2,
                                 radius * 2 * 2 // 3), 1)
            screen.blit(ring, (dx + rx - radius - (vis.x - self.rect.x),
                               dy + ry - radius - (vis.y - self.rect.y)))


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
    siirretään (karttaeditori). Asettaa arena.fishing_spots-listan
    (+ fishing_pond/jetty/spot yhteensopivuusaliakset).
    """
    arena.obstacles[:] = [o for o in arena.obstacles
                          if not getattr(o, "is_water", False)]
    waters = [p for p in arena.floor_props if isinstance(p, WaterBody)]
    jetties = [p for p in arena.floor_props if isinstance(p, FishingJetty)]

    spots = []
    for water in waters:
        pieces = [pygame.Rect(water.rect)]
        for jetty in jetties:
            if jetty.rect.colliderect(water.rect):
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


def carve_water(arena, rect, seed=11):
    """Upottaa vesialueen areenaan: siivoaa alle jäävät propit, lisää
    WaterBodyn lattiakerrokseen ja laskee esteet. Palauttaa WaterBodyn."""
    area = pygame.Rect(rect)
    clear = area.inflate(60, 60)
    for prop in list(arena.props):
        if clear.colliderect(prop.rect):
            arena.props.remove(prop)
            if prop in arena.obstacles:
                arena.obstacles.remove(prop)
    water = WaterBody(area.x, area.y, area.w, area.h, seed=seed)
    arena.floor_props.append(water)
    rebuild_water_blockers(arena)
    return water


def carve_pond(arena, pond_rect, jetty_side="left", seed=11):
    """Lampi + laituri länsirannalta. Palauttaa (water, jetty)."""
    pond = pygame.Rect(pond_rect)
    water = carve_water(arena, pond, seed=seed)
    jw, jh = 170, 64
    jetty = FishingJetty(pond.x - 26, pond.centery - jh // 2, jw, jh,
                         seed=seed + 1)
    arena.floor_props.append(jetty)
    rebuild_water_blockers(arena)
    return water, jetty
