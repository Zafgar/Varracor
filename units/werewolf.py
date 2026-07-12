# units/werewolf.py
"""
Werewolf (ihmissusi) - nopea, kova ja janoinen lahitaistelija. Racial:
Bloodmoon Frenzy (use_racial_ability) - hetkellinen nopeus, +vahinko ja
elamanimu. Heikko tulelle. Grafiikka piirretaan koodilla kunnes spritet
lisataan (assets/races/werewolf/...), samalla viittaustavalla kuin muut.
"""
import pygame
import os
from settings import *
from gladiator import Gladiator
from ai.base_ai import BaseAI


class Werewolf(Gladiator):
    def __init__(self, name, x, y, team_color):
        super().__init__(name, "Werewolf", x, y, team_color)
        self.rect = pygame.Rect(x, y + 22, 26, 18)

        self.level = 1
        self.upgrade_cost = 110
        self.cost = 60

        self.show_main_hand = True
        self.show_off_hand = True
        self.sprites = {}
        self.hurt_timer = 0
        self.last_pos = self.rect.topleft

        self._load_sprites()
        self.image = self.sprites.get("idle") or self._fallback()
        if not getattr(self, "big_image", None):
            self.big_image = pygame.transform.smoothscale(self.image, (32 * 3, 46 * 3))

        self.ai_controller = BaseAI(self)
        self.calculate_final_stats()
        self.current_hp = self.max_hp

    def load_assets(self):
        return True

    def _fallback(self):
        """Koodipiirretty ihmissusi: tumma karvainen biped, korvat, punasilmat."""
        w, h = 32, 46
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        fur = (70, 62, 58)
        fur_hi = (100, 90, 84)
        # Vartalo
        pygame.draw.ellipse(s, fur, (7, 16, 18, 24))
        # Jalat
        pygame.draw.rect(s, fur, (10, 36, 5, 9))
        pygame.draw.rect(s, fur, (18, 36, 5, 9))
        # Kadet/kynnet
        pygame.draw.line(s, fur_hi, (8, 22), (2, 30), 3)
        pygame.draw.line(s, fur_hi, (24, 22), (30, 30), 3)
        for cx in (1, 3):
            pygame.draw.line(s, (220, 220, 210), (cx, 30), (cx - 1, 34), 1)
        # Paa + kuono
        pygame.draw.circle(s, fur_hi, (16, 12), 8)
        pygame.draw.polygon(s, fur_hi, [(16, 12), (26, 14), (18, 18)])  # kuono
        # Korvat
        pygame.draw.polygon(s, fur, [(10, 5), (13, 12), (8, 11)])
        pygame.draw.polygon(s, fur, [(22, 5), (19, 12), (24, 11)])
        # Punasilmat
        pygame.draw.circle(s, (230, 40, 40), (13, 11), 2)
        pygame.draw.circle(s, (230, 40, 40), (19, 11), 2)
        return s

    def _load_sprites(self):
        base = "assets/races/werewolf/werewolf"
        for act in ("idle", "run", "attack", "hurt"):
            path = f"{base}_{act}_1.png"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    if act == "idle":
                        self.big_image = img
                    self.sprites[act] = pygame.transform.smoothscale(img, (32, 46))
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
