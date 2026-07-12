# units/dwarf.py
"""
Dwarf - sitka, hidas ja panssaroitunut. Rotu oli jo RACESissa (Stoneform-
racial: -50% vahinko + puhdistaa stunit/statukset), mutta omaa yksikkoluokkaa
ei ollut. Grafiikka piirretaan koodilla kunnes spritet lisataan
(assets/races/dwarf/...), samalla viittaustavalla kuin muut.
"""
import pygame
import os
from settings import *
from gladiator import Gladiator
from ai.base_ai import BaseAI


class Dwarf(Gladiator):
    def __init__(self, name, x, y, team_color):
        super().__init__(name, "Dwarf", x, y, team_color)
        self.rect = pygame.Rect(x, y + 22, 26, 18)

        self.level = 1
        self.upgrade_cost = 95
        self.cost = 55

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
        """Koodipiirretty kaapio: matala, tukeva, iso parta ja kypara."""
        w, h = 30, 40
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        skin = (210, 170, 140)
        cloth = tuple(min(255, c) for c in getattr(self, "team_color", (120, 110, 100)))
        beard = (170, 120, 60)
        # Vartalo (leveä)
        pygame.draw.rect(s, cloth, (6, 20, 18, 16), border_radius=4)
        # Jalat
        pygame.draw.rect(s, (80, 70, 60), (9, 34, 5, 6))
        pygame.draw.rect(s, (80, 70, 60), (16, 34, 5, 6))
        # Paa
        pygame.draw.circle(s, skin, (15, 15), 7)
        # Kypara
        pygame.draw.rect(s, (130, 130, 140), (7, 8, 16, 6), border_radius=3)
        pygame.draw.rect(s, (150, 150, 160), (13, 4, 4, 6))  # piikki
        # Parta
        pygame.draw.polygon(s, beard, [(9, 18), (21, 18), (18, 30), (12, 30)])
        # Silmat
        pygame.draw.circle(s, (40, 40, 40), (13, 15), 1)
        pygame.draw.circle(s, (40, 40, 40), (17, 15), 1)
        return s

    def _load_sprites(self):
        base = "assets/races/dwarf/dwarf"
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
