# units/human.py
import pygame
import os
import math
import random

from settings import *
from gladiator import Gladiator

from ai.base_ai import BaseAI

class Human(Gladiator):
    def __init__(self, name, x, y, team_color, quality="Common"):
        self.quality = quality

        super().__init__(name, "Human", x, y, team_color)

        # --- Stats ---
        self.level = 1
        mult = 1.0
        self.cost = 50

        # Traits & cost by quality
        if not hasattr(self, "traits") or self.traits is None:
            self.traits = []

        if quality == "Veteran":
            mult = 1.3
            if "Strong" not in self.traits:
                self.traits.append("Strong")
            self.cost = 150
        elif quality == "Elite":
            mult = 1.6
            for t in ("Quick", "Tank"):
                if t not in self.traits:
                    self.traits.append(t)
            self.cost = 300

        self.upgrade_cost = max(100, int(self.cost))

        # Base attributes update
        if hasattr(self, "base_attributes") and isinstance(self.base_attributes, dict):
            for k in ("str", "dex", "hp"):
                if k in self.base_attributes:
                    self.base_attributes[k] = int(self.base_attributes[k] * mult)
            if "hp" in self.base_attributes:
                self.base_attributes["max_hp"] = self.base_attributes["hp"]

        # Feet Hitbox (Physics)
        self.rect = pygame.Rect(x, y + 44, 30, 20)

        # Grafiikat
        self.show_main_hand = True
        self.show_off_hand = True
        self.sprites = {}
        self.hurt_timer = 0
        self.last_pos = self.rect.topleft
        
        self._load_sprites()
        # Ladataan spritet vain jos niitä ei ole vielä ladattu (esim. aliluokan load_assets toimesta)
        if not self.sprites:
            self._load_sprites()
            
        self.image = self.sprites.get("idle", pygame.Surface((36, 64)))
        if not self.sprites:
            self.image.fill((200, 180, 150))
        
        # Portrait UI:ta varten
        if not getattr(self, "big_image", None):
            self.big_image = pygame.transform.smoothscale(self.image, (self.rect.w * 3, self.rect.h * 3))

        # Stats
        self.calculate_final_stats()
        self.current_hp = self.max_hp
        
        # Käytä älykkäämpää AI:ta
        self.ai_controller = BaseAI(self)

    def load_assets(self):
        return True

    def _load_sprites(self):
        base_path = "assets/races/human/human"
        actions = ["idle", "run", "attack", "hurt", "cast"]
        target_w, target_h = 36, 64 # Visuaalinen koko (ei hitbox)
        
        for act in actions:
            path = f"{base_path}_{act}_1.png"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    
                    if act == "idle":
                        self.big_image = img

                    scaled = pygame.transform.smoothscale(img, (target_w, target_h))
                    self.sprites[act] = scaled
                except Exception: pass
        
        if not self.sprites:
            s = pygame.Surface((target_w, target_h))
            s.fill((200, 180, 150)) 
            self.sprites["idle"] = s

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        dmg = super().take_damage(amount, damage_type, attacker, manager)
        if dmg > 0:
            self.hurt_timer = 15
        return dmg

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        if self.is_dead: return

        state = "idle"
        
        if self.hurt_timer > 0:
            self.hurt_timer -= 1
            state = "hurt"
        elif self.attack_cooldown > 30:
            state = "attack"
        else:
            is_casting = False
            for slot, cd in self.spell_cooldowns.items():
                spell = self.equipment.get(slot)
                if spell:
                    max_cd = getattr(spell, "cooldown_max", 0)
                    if max_cd > 0 and cd > max_cd * 0.8:
                        is_casting = True
                        break
            if is_casting:
                state = "cast"
            elif self.rect.topleft != self.last_pos:
                state = "run"
        
        if state in self.sprites:
            self.image = self.sprites[state]

        self.last_pos = self.rect.topleft
