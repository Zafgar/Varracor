# units/rattlebridge_threats.py
"""
Rattlebridgen uhat (Tier 1). Grafiikka piirretaan koodilla kunnes spritet
lisataan (assets/races/...), samalla viittaustavalla kuin muilla.

- Hush-Mantle      : Rank C/B -boss. Abyssal Echo joka luo akustisen tyhjion:
                     vaimentaa aanet -> Silence + Slow lahella (salamurhaajien
                     suosikki). Ei pakene.
- Gutter Vermin    : Gutter Swarm -parvi. Nopea, hauras; saastunut lima+rotta
                     tartuttaa myrkyn (fever) lahitaistelussa.
- Red Lantern Cadaver : Slummien epakuollut, kantaa tarttuvaa kuumetta (Poison).
                     Heikko tulelle (polta riepu, sanoo Captain Mara).
"""
import pygame
import os
import math
import random

from settings import *
from gladiator import Gladiator
from ai.base_ai import BaseAI


class _ThreatAI(BaseAI):
    def __init__(self, unit, no_retreat=False):
        super().__init__(unit)
        self.no_retreat = no_retreat


def _enemies_near(unit, manager, radius):
    cx, cy = unit.rect.center
    out = []
    for u in list(getattr(manager, "all_units", []) or []):
        if getattr(u, "is_dead", False) or u is unit:
            continue
        if getattr(u, "team_color", None) == unit.team_color:
            continue
        if math.hypot(u.rect.centerx - cx, u.rect.centery - cy) < radius:
            out.append(u)
    return out


class HushMantle(Gladiator):
    """Akustinen tyhjio-boss: vaimentaa aanet ymparillaan."""
    def __init__(self, name="Hush-Mantle", x=0, y=0, team_color=None):
        if team_color is None:
            team_color = ENEMY_TEAM
        super().__init__(name, "Corrupted", x, y, team_color)
        self.rect = pygame.Rect(x, y, 60, 84)
        self.base_attributes["str"] = 18
        self.base_attributes["dex"] = 9
        self.base_attributes["hp"] = 560
        self.base_attributes["def_flat"] = 4
        self.calculate_final_stats()
        self.max_hp = 560
        self.current_hp = self.max_hp
        self.speed = self.walk_speed = 0.9 * 1.85  # uusi liikeskaala (pelitesti 28); pelkka .speed ylikirjoittui updatessa
        self.attack_range = 52
        self.attack_speed = 80
        self.defense = 4
        self.is_boss = True
        self._hush_tick = 0
        self.show_main_hand = False
        self.sprites = {}
        self.image = self._fallback()
        self.big_image = pygame.transform.smoothscale(self.image, (self.rect.w * 2, self.rect.h * 2))
        self.ai_controller = _ThreatAI(self, no_retreat=True)

    def load_assets(self):
        return True

    def _fallback(self):
        s = pygame.Surface((60, 84), pygame.SRCALPHA)
        # Sumukehat
        for r, a in ((34, 55), (26, 85), (18, 120)):
            pygame.draw.circle(s, (150, 150, 162, a), (30, 40), r)
        # Kaapu
        pygame.draw.polygon(s, (70, 70, 82), [(30, 8), (50, 42), (44, 80), (16, 80), (10, 42)])
        # Tumma huppuontelo (kasvoton)
        pygame.draw.ellipse(s, (18, 18, 24), (20, 20, 20, 28))
        return s

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        if self.is_dead or not manager:
            return
        self._hush_tick += 1
        if self._hush_tick >= 90:   # 1.5s valein
            self._hush_tick = 0
            hit = _enemies_near(self, manager, 220)
            for u in hit:
                u.apply_status("Silence", 150)
                u.apply_status("Slow", 90)
            if hit:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 30,
                                        "...silence...", color=(150, 150, 162))


class GutterVermin(Gladiator):
    """Gutter Swarm -parvi: nopea, hauras, tartuttaa myrkyn lahitaistelussa."""
    def __init__(self, name="Gutter Vermin", x=0, y=0, team_color=None):
        if team_color is None:
            team_color = ENEMY_TEAM
        super().__init__(name, "Rat", x, y, team_color)
        self.rect = pygame.Rect(x, y, 30, 22)
        self.base_attributes["str"] = 6
        self.base_attributes["dex"] = 14
        self.base_attributes["hp"] = 44
        self.calculate_final_stats()
        self.max_hp = 44
        self.current_hp = self.max_hp
        self.speed = self.walk_speed = 1.7 * 1.85  # uusi liikeskaala (pelitesti 28); pelkka .speed ylikirjoittui updatessa
        self.attack_range = 30
        self.attack_speed = 45
        self.defense = 0
        self._tox_tick = random.randint(0, 40)
        self.show_main_hand = False
        self.sprites = {}
        self.image = self._fallback()
        self.big_image = pygame.transform.smoothscale(self.image, (self.rect.w * 3, self.rect.h * 3))
        self.ai_controller = _ThreatAI(self)

    def load_assets(self):
        return True

    def _fallback(self):
        s = pygame.Surface((30, 22), pygame.SRCALPHA)
        body = (90, 110, 70)
        pygame.draw.ellipse(s, body, (4, 6, 20, 12))
        pygame.draw.circle(s, (110, 130, 85), (24, 10), 5)      # paa
        pygame.draw.line(s, (70, 90, 55), (4, 12), (0, 18), 2)  # hanta
        pygame.draw.circle(s, (200, 60, 60), (25, 9), 1)        # silma
        # limatippa
        pygame.draw.circle(s, (120, 160, 90), (12, 18), 2)
        return s

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        if self.is_dead or not manager:
            return
        self._tox_tick += 1
        if self._tox_tick >= 60:
            self._tox_tick = 0
            for u in _enemies_near(self, manager, self.attack_range + 28):
                u.apply_status("Poison", 120, 4)


class RedLanternCadaver(Gladiator):
    """Slummien epakuollut: tarttuva kuume (Poison), heikko tulelle."""
    def __init__(self, name="Red Lantern Cadaver", x=0, y=0, team_color=None):
        if team_color is None:
            team_color = ENEMY_TEAM
        super().__init__(name, "Undead", x, y, team_color)
        self.rect = pygame.Rect(x, y, 32, 44)
        self.base_attributes["str"] = 11
        self.base_attributes["dex"] = 5
        self.base_attributes["hp"] = 260  # pelitesti 28: tier 1 -alueen mitoitus
        self.calculate_final_stats()
        self.max_hp = 260
        self.current_hp = self.max_hp
        self.speed = self.walk_speed = 0.85 * 1.85  # uusi liikeskaala (pelitesti 28); pelkka .speed ylikirjoittui updatessa
        self.attack_range = 34
        self.attack_speed = 70
        self.defense = 1
        self._fever_tick = random.randint(0, 45)
        self.show_main_hand = False
        self.sprites = {}
        self.image = self._fallback()
        self.big_image = pygame.transform.smoothscale(self.image, (self.rect.w * 3, self.rect.h * 3))
        self.ai_controller = _ThreatAI(self)

    def load_assets(self):
        return True

    def _fallback(self):
        s = pygame.Surface((32, 44), pygame.SRCALPHA)
        flesh = (120, 130, 110)
        pygame.draw.rect(s, flesh, (9, 16, 14, 20), border_radius=3)
        pygame.draw.circle(s, (135, 145, 120), (16, 12), 6)     # paa
        # punainen lyhty (nimikko)
        pygame.draw.rect(s, (60, 40, 40), (2, 18, 6, 8), border_radius=1)
        pygame.draw.circle(s, (220, 70, 60), (5, 22), 3)
        # kuumeen silmat
        pygame.draw.circle(s, (230, 90, 70), (14, 12), 1)
        pygame.draw.circle(s, (230, 90, 70), (18, 12), 1)
        return s

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        if self.is_dead or not manager:
            return
        self._fever_tick += 1
        if self._fever_tick >= 70:
            self._fever_tick = 0
            for u in _enemies_near(self, manager, self.attack_range + 24):
                u.apply_status("Poison", 150, 5)
