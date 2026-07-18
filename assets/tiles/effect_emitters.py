# assets/tiles/effect_emitters.py
"""Koodipiirretyt efektiemitterit karttoihin (pelitesti 29).

Editorissa sijoiteltavia tunnelmaefektejä: savu, sumu, kipinät ja
tulikärpäset. Ei asset-tiedostoja - partikkelit piirretään joka frame.
Emitterit EIVÄT ole esteitä (is_effect=True) eivätkä heitä varjoa;
ne kulkevat normaalissa props-listassa, joten z-järjestys, raahaus,
poisto ja serialisointi toimivat editorissa suoraan.

Variant säätää voimakkuutta/sädettä ([ ja ] editorissa).
"""
from __future__ import annotations

import math
import random

import pygame


class EffectEmitter(pygame.sprite.Sprite):
    """Yhteinen pohja: pieni lähdeglyyfi + partikkelipäivitys.

    Sprite-kantaluokka, jotta missiokarttojen setup voi lisätä propit
    all_units-ryhmään kaatumatta."""

    GLYPH_COLOR = (200, 200, 200)

    def __init__(self, x, y, variant=1):
        super().__init__()
        self.variant = max(1, int(variant))
        self.rect = pygame.Rect(int(x), int(y), 24, 24)
        self.is_structure = False
        self.is_effect = True
        self.is_floor = False
        self.has_shadow = False
        self.blocks_projectiles = False
        self.angle = 0
        self.particles = []          # [x, y, vx, vy, ikä, max_ikä, koko]
        self._spawn_timer = 0
        self._rng = random.Random(id(self) & 0xFFFF)
        # Editorin poiminta/ghost tarvitsee kuvan: lähdeglyyfi
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (*self.GLYPH_COLOR, 90), (12, 12), 10, 2)
        pygame.draw.circle(self.image, (*self.GLYPH_COLOR, 140), (12, 12), 3)

    @property
    def image_pos(self):
        return self.rect.topleft

    @image_pos.setter
    def image_pos(self, pos):
        self.rect.topleft = (int(pos[0]), int(pos[1]))

    def serialize_extra(self):
        return {"variant": self.variant}

    # ------------------------------------------------------------ elo
    def update(self, obstacles=None, manager=None, **kwargs):
        self._spawn_timer -= 1
        if self._spawn_timer <= 0:
            self._spawn_timer = self._spawn_interval()
            for _ in range(self._spawn_count()):
                self.particles.append(self._new_particle())
        alive = []
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[4] += 1
            self._advance(p)
            if p[4] < p[5]:
                alive.append(p)
        self.particles = alive

    # Alaluokat toteuttavat nämä
    def _spawn_interval(self):
        return 10

    def _spawn_count(self):
        return 1

    def _new_particle(self):
        raise NotImplementedError

    def _advance(self, p):
        pass

    def _particle_color(self, p):
        raise NotImplementedError

    def draw_on_screen(self, screen, offset=(0, 0)):
        ox, oy = offset
        cx, cy = self.rect.center
        for p in self.particles:
            color = self._particle_color(p)
            if color is None:
                continue
            size = max(1, int(p[6]))
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (size, size), size)
            screen.blit(surf, (int(cx + p[0]) - size - ox,
                               int(cy + p[1]) - size - oy))

    # Yhteensopivuus floor_props-piirtopolun kanssa
    def draw(self, screen, offset=(0, 0)):
        self.draw_on_screen(screen, offset)


class SmokeEmitter(EffectEmitter):
    """Nouseva savu (savupiiput, nuotiot, rauniot). Variant = tiheys."""

    GLYPH_COLOR = (170, 170, 175)

    def _spawn_interval(self):
        return max(3, 9 - self.variant * 2)

    def _new_particle(self):
        r = self._rng
        return [r.uniform(-4, 4), 0.0,
                r.uniform(-0.15, 0.15), r.uniform(-0.7, -0.4),
                0, r.randint(70, 120), r.uniform(3, 5)]

    def _advance(self, p):
        p[2] += self._rng.uniform(-0.03, 0.03)   # tuulen huojunta
        p[6] += 0.06                              # puffi kasvaa noustessa

    def _particle_color(self, p):
        fade = 1.0 - p[4] / p[5]
        alpha = int(90 * fade)
        shade = 150 + int(40 * fade)
        return (shade, shade, shade + 5, alpha)


class FogPatch(EffectEmitter):
    """Matala ajelehtiva sumu (suot, hautausmaat). Variant = säde."""

    GLYPH_COLOR = (160, 175, 175)

    def _radius(self):
        return 60 + self.variant * 40

    def _spawn_interval(self):
        return 14

    def _new_particle(self):
        r = self._rng
        rad = self._radius()
        return [r.uniform(-rad, rad), r.uniform(-rad * 0.4, rad * 0.4),
                r.uniform(-0.12, 0.12), r.uniform(-0.03, 0.03),
                0, r.randint(160, 260), r.uniform(14, 26)]

    def _advance(self, p):
        # Pysy alueella: käänny takaisin reunalta
        rad = self._radius()
        if abs(p[0]) > rad:
            p[2] *= -1
        p[6] += 0.02

    def _particle_color(self, p):
        life = p[4] / p[5]
        alpha = int(38 * math.sin(life * math.pi))  # häivy sisään ja ulos
        return (168, 182, 180, max(0, alpha))


class EmberEmitter(EffectEmitter):
    """Nousevat kipinät ja hehku (ahjot, roihut, riftit). Variant = määrä."""

    GLYPH_COLOR = (235, 140, 60)

    def _spawn_interval(self):
        return max(2, 7 - self.variant * 2)

    def _new_particle(self):
        r = self._rng
        return [r.uniform(-6, 6), 0.0,
                r.uniform(-0.2, 0.2), r.uniform(-1.4, -0.7),
                0, r.randint(35, 70), r.uniform(1.5, 2.5)]

    def _advance(self, p):
        p[2] += self._rng.uniform(-0.05, 0.05)
        p[3] *= 0.98

    def _particle_color(self, p):
        fade = 1.0 - p[4] / p[5]
        if self._rng.random() < 0.08:
            return None                           # välkyntä
        return (235, 120 + int(90 * fade), 40, int(200 * fade))


class FireflySwarm(EffectEmitter):
    """Vaeltavat hohtavat pisteet (yö, metsä, lampi). Variant = parvi."""

    GLYPH_COLOR = (190, 230, 120)

    def _spawn_interval(self):
        return 20

    def _spawn_count(self):
        # Pidä parven koko: max ~6 x variant kärpästä
        return 1 if len(self.particles) < 6 * self.variant else 0

    def _new_particle(self):
        r = self._rng
        rad = 50 + self.variant * 25
        return [r.uniform(-rad, rad), r.uniform(-rad * 0.6, rad * 0.6),
                r.uniform(-0.4, 0.4), r.uniform(-0.3, 0.3),
                0, r.randint(300, 600), r.uniform(1.5, 2.2)]

    def _advance(self, p):
        p[2] += self._rng.uniform(-0.08, 0.08)
        p[3] += self._rng.uniform(-0.06, 0.06)
        p[2] = max(-0.5, min(0.5, p[2]))
        p[3] = max(-0.4, min(0.4, p[3]))

    def _particle_color(self, p):
        pulse = (math.sin(p[4] * 0.15) + 1) / 2
        if pulse < 0.3:
            return None
        return (190, 235, 110, int(190 * pulse))


EFFECT_CLASSES = (SmokeEmitter, FogPatch, EmberEmitter, FireflySwarm)
