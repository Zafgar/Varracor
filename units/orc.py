# units/orc.py
import pygame
import os
import math
import random

from settings import *
from gladiator import Gladiator
from ai.base_ai import BaseAI

class Orc(Gladiator):
    def __init__(self, name, x, y, team_color):
        super().__init__(name, "Orc", x, y, team_color)

        # Isompi hitbox (Orc on suuri ja vahva)
        # Physics Rect (Jalat) - Pienempi korkeus parempaa syvyysvaikutelmaa varten
        self.rect = pygame.Rect(x, y, 42, 24)
        self.cost = 90

        # Grafiikat
        self.show_main_hand = True
        self.show_off_hand = True
        self.sprites = {}
        self.hurt_timer = 0
        self.last_pos = self.rect.topleft
        
        self._load_sprites()
        self.image = self.sprites.get("idle", pygame.Surface((42, 72)))
        if not self.sprites:
            self.image.fill((50, 100, 50)) # Örkinkaltainen vihreä fallback
        
        # Portrait UI:ta varten
        if not getattr(self, "big_image", None):
            # Käytetään kuvan kokoa skaalaukseen, ei hitboxia (joka on vain jalat)
            w, h = self.image.get_size()
            self.big_image = pygame.transform.smoothscale(self.image, (w * 3, h * 3))

        # AI
        self.ai_controller = BaseAI(self)

        # Varmistetaan statsit (HP mult 1.4, STR mult 1.2)
        self.calculate_final_stats()
        self.current_hp = self.max_hp

    def load_assets(self):
        return True

    def _load_sprites(self):
        base_path = "assets/races/orc/orc"
        actions = ["idle", "run", "attack", "hurt", "cast"]
        # Visuaalinen koko (pidetään alkuperäinen korkeus 72px, vaikka hitbox on matalampi)
        target_w, target_h = 42, 72
        
        for act in actions:
            path = f"{base_path}_{act}_1.png"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    
                    if act == "idle":
                        self.big_image = img

                    scaled = pygame.transform.smoothscale(img, (target_w, target_h))
                    self.sprites[act] = scaled
                except: pass
        
        if not self.sprites:
            s = pygame.Surface((target_w, target_h))
            s.fill((50, 100, 50)) # Örkinkaltainen vihreä fallback
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