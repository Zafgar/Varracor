# units/tortle.py
"""
Tortle (kilpikonna-humanoidi) - hidas, sitkea muuri. Racial: Shell Guard
(use_racial_ability) - vetaytyy kilpeen: -75% vahinko useaksi sekunniksi,
mutta juurtuu paikalleen (ei liiku). Heikko magialle. Grafiikka koodilla
kunnes spritet lisataan (assets/races/tortle/...).
"""
import pygame
import os
from settings import *
from gladiator import Gladiator
from ai.base_ai import BaseAI


class Tortle(Gladiator):
    def __init__(self, name, x, y, team_color):
        super().__init__(name, "Tortle", x, y, team_color)
        self.rect = pygame.Rect(x, y + 24, 30, 18)

        self.level = 1
        self.upgrade_cost = 120
        self.cost = 65

        self.show_main_hand = True
        self.show_off_hand = True
        self.sprites = {}
        self.hurt_timer = 0
        self.last_pos = self.rect.topleft

        self._load_sprites()
        self.image = self.sprites.get("idle") or self._fallback()
        if not getattr(self, "big_image", None):
            self.big_image = pygame.transform.smoothscale(self.image, (34 * 3, 42 * 3))

        self.ai_controller = BaseAI(self)
        self.calculate_final_stats()
        self.current_hp = self.max_hp

    def load_assets(self):
        return True

    def _fallback(self):
        """Koodipiirretty kilpikonna-humanoidi: kupolikilpi, pieni paa, tukevat jalat."""
        w, h = 34, 42
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        skin = (90, 150, 95)
        shell = (95, 70, 45)
        shell_hi = (135, 100, 65)
        # Jalat
        pygame.draw.rect(s, skin, (9, 33, 6, 8))
        pygame.draw.rect(s, skin, (19, 33, 6, 8))
        # Kilpi (kupoli)
        pygame.draw.ellipse(s, shell, (5, 14, 24, 22))
        pygame.draw.ellipse(s, shell_hi, (9, 17, 16, 13), 2)
        # Kilven ruudut
        pygame.draw.line(s, shell_hi, (17, 15), (17, 34), 1)
        pygame.draw.line(s, shell_hi, (8, 25), (26, 25), 1)
        # Paa
        pygame.draw.circle(s, skin, (17, 11), 6)
        pygame.draw.circle(s, (20, 30, 20), (15, 10), 1)
        pygame.draw.circle(s, (20, 30, 20), (19, 10), 1)
        # Kadet
        pygame.draw.line(s, skin, (6, 24), (2, 30), 3)
        pygame.draw.line(s, skin, (28, 24), (32, 30), 3)
        return s

    def _load_sprites(self):
        base = "assets/races/tortle/tortle"
        for act in ("idle", "run", "attack", "hurt"):
            path = f"{base}_{act}_1.png"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    if act == "idle":
                        self.big_image = img
                    self.sprites[act] = pygame.transform.smoothscale(img, (34, 42))
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
        if getattr(self, "shell_timer", 0) > 0:
            state = "hurt"  # kilpiasento (kayta hurt/idle-ruutua kunnes oma sprite)
        elif self.hurt_timer > 0:
            self.hurt_timer -= 1
            state = "hurt"
        elif self.attack_cooldown > 30:
            state = "attack"
        elif self.rect.topleft != self.last_pos:
            state = "run"
        if state in self.sprites:
            self.image = self.sprites[state]
        self.last_pos = self.rect.topleft
