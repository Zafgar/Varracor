import pygame
import os
import math
import random
from gladiator import Gladiator
from ai.rat_ai import RatAI
from settings import *

class RatRider(Gladiator):
    def __init__(self, name, x, y, team_color=(200, 50, 50)):
        super().__init__(name, "Rat", x, y, team_color)
        
        self.rect = pygame.Rect(x, y, 96, 96)
        
        # Stats (Fast, Hit & Run)
        self.max_hp = 240
        self.current_hp = 240
        self.strength = 32
        self.dexterity = 15
        self.speed = 2.0
        self.attack_speed = 45
        self.cost = 120
        
        # Abilities
        self.charge_cooldown = 0
        self.throw_cooldown = 0
        self.charge_phase = 0 # 0: None, 1: Windup, 2: Dash, 3: Impact
        self.charge_timer = 0
        
        self.sprites = {}
        self._load_sprites()
        self.image = self.sprites.get("idle", pygame.Surface((96, 96)))
        
        # Portrait
        if not getattr(self, "big_image", None):
            self.big_image = pygame.transform.smoothscale(self.image, (self.rect.w * 3, self.rect.h * 3))

        self.facing_right = True
        self.ai_controller = RatAI(self)

    def load_assets(self):
        return True

    def _load_sprites(self):
        base_path = os.path.join("assets", "races", "rat")
        # Filenames based on user description
        files = {
            "idle": "rat_rider_idle.png",
            "run": "rat_rider_run.png",
            "charge_1": "rat_rider_charge_1.png", # Windup
            "charge_2": "rat_rider_charge_2.png", # Impact
            "throw": "rat_rider_throw.png",
            "hurt": "rat_rider_hurt.png"
        }
        
        for key, fname in files.items():
            path = os.path.join(base_path, fname)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.sprites[key] = pygame.transform.smoothscale(img, (128, 128))
                except: pass
        
        if "idle" not in self.sprites:
            s = pygame.Surface((96, 96))
            s.fill((150, 50, 50))
            self.sprites["idle"] = s
            self.sprites["run"] = s

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        
        if self.charge_cooldown > 0: self.charge_cooldown -= 1
        if self.throw_cooldown > 0: self.throw_cooldown -= 1
        
        # Sprite State Machine
        state = "idle"
        if self.charge_phase == 1: state = "charge_1"
        elif self.charge_phase == 2: state = "run"
        elif self.charge_phase == 3: state = "charge_2"
        elif self.animation_state == "throw": state = "throw"
        elif self.animation_state == "hurt": state = "hurt"
        elif self.rect.topleft != getattr(self, "last_pos", self.rect.topleft): state = "run"
        
        img = self.sprites.get(state, self.sprites.get("idle"))
        if img:
            self.image = img
            if not self.facing_right:
                self.image = pygame.transform.flip(self.image, True, False)
        
        self.last_pos = self.rect.topleft

    def start_charge(self):
        if self.charge_cooldown <= 0:
            self.charge_phase = 1
            self.charge_timer = 40 # Windup time
            self.charge_cooldown = 300
            return True
        return False

    def perform_throw(self, target, manager):
        if self.throw_cooldown <= 0:
            self.throw_cooldown = 240
            self.animation_state = "throw"
            self.animation_timer = 30
            if manager:
                manager.vfx.create_firebomb(self.rect.center, target.rect.center, self, manager)
            return True
        return False