# units/gnome.py
"""
Gnome - Rattlebridgen paja-nikkari (forge-tinker). Pieni, ketterä ja nokkela;
heikko voimissa mutta kipinaansat (Spark Snare -racial) hidastavat ja
polttavat vihollisia. Ironspan Unionin dwarfien tyokaverit Scrapringilla.
Grafiikka piirretaan koodilla kunnes spritet lisataan (assets/races/gnome/...),
samalla viittaustavalla kuin muut.
"""
import pygame
import os
from settings import *
from gladiator import Gladiator
from ai.base_ai import BaseAI


class Gnome(Gladiator):
    def __init__(self, name, x, y, team_color):
        super().__init__(name, "Gnome", x, y, team_color)
        self.rect = pygame.Rect(x, y + 24, 22, 16)

        self.level = 1
        self.upgrade_cost = 85
        self.cost = 45

        self.show_main_hand = True
        self.show_off_hand = True
        self.sprites = {}
        self.hurt_timer = 0
        self.last_pos = self.rect.topleft

        self._load_sprites()
        self.image = self.sprites.get("idle") or self._fallback()
        if not getattr(self, "big_image", None):
            self.big_image = pygame.transform.smoothscale(self.image, (30 * 3, 40 * 3))

        self.ai_controller = BaseAI(self)
        self.calculate_final_stats()
        self.current_hp = self.max_hp

    def load_assets(self):
        return True

    def _fallback(self):
        """Koodipiirretty gnomi: pieni vartalo, iso pyoreä paa, hattu ja rattaat."""
        w, h = 30, 40
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        skin = (225, 190, 160)
        cloth = tuple(min(255, c) for c in getattr(self, "team_color", (140, 120, 90)))
        # Vartalo (pieni)
        pygame.draw.rect(s, cloth, (10, 24, 12, 12), border_radius=3)
        # Jalat
        pygame.draw.rect(s, (70, 60, 50), (11, 34, 4, 6))
        pygame.draw.rect(s, (70, 60, 50), (17, 34, 4, 6))
        # Iso paa
        pygame.draw.circle(s, skin, (15, 18), 8)
        # Suippo nikkari-hattu
        pygame.draw.polygon(s, (150, 110, 60), [(15, 2), (23, 14), (7, 14)])
        pygame.draw.circle(s, (200, 170, 90), (15, 3), 2)  # topaasi
        # Suojalasit (nikkari)
        pygame.draw.circle(s, (90, 130, 150), (12, 18), 2)
        pygame.draw.circle(s, (90, 130, 150), (18, 18), 2)
        pygame.draw.line(s, (60, 60, 60), (14, 18), (16, 18), 1)
        # Pieni ratas olalla
        pygame.draw.circle(s, (150, 150, 160), (23, 24), 3, 1)
        return s

    def _load_sprites(self):
        base = "assets/races/gnome/gnome"
        for act in ("idle", "run", "attack", "hurt"):
            path = f"{base}_{act}_1.png"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    if act == "idle":
                        self.big_image = img
                    self.sprites[act] = pygame.transform.smoothscale(img, (30, 40))
                except Exception:
                    pass

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        dmg = super().take_damage(amount, damage_type, attacker, manager)
        if dmg > 0:
            self.hurt_timer = 15
        return dmg

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        if self.is_dead:
            return
        state = "idle"
        if self.hurt_timer > 0:
            self.hurt_timer -= 1
            state = "hurt"
        elif self.attack_cooldown > 30:
            state = "attack"
        elif self.rect.topleft != self.last_pos:
            state = "run"
        if state in self.sprites:
            self.image = self.sprites[state]
        self.last_pos = self.rect.topleft
