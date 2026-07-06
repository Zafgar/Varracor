import pygame
import os
from gladiator import Gladiator
from settings import *

class Bard(Gladiator):
    def __init__(self, name, race, x, y, team_color):
        race = race.capitalize()
        super().__init__(name, race, x, y, team_color)
        
        # Hitbox (Jalat)
        self.rect = pygame.Rect(x, y, 36, 24)
        
        # Stats
        self.max_hp = 60
        self.current_hp = 60
        self.strength = 4
        self.dexterity = 8
        self.intelligence = 12
        self.speed = 1.1
        self.cost = 100
        
        # Graphics
        self.sprites = {}
        self._load_bard_sprites(race)
        
        # Default image
        if "idle" in self.sprites:
            self.image = self.sprites["idle"]
        else:
            self.image = pygame.Surface((36, 60))
            self.image.fill((100, 100, 200))

        # Portrait
        if not getattr(self, "big_image", None):
             if self.image:
                # Käytetään kuvan kokoa skaalaukseen, ei hitboxia (joka on vain jalat)
                w, h = self.image.get_size()
                self.big_image = pygame.transform.smoothscale(self.image, (w * 3, h * 3))

    def _load_bard_sprites(self, race):
        base_path = os.path.join("assets", "races", race.lower())
        
        # Naming convention: bard_{race}_{state}_1.png
        r_lower = race.lower()
        mapping = {
            "idle": f"bard_{r_lower}_idle_1.png",
            "run": f"bard_{r_lower}_walk_1.png",
            "attack": f"bard_{r_lower}_attack_1.png",
            "hurt": f"bard_{r_lower}_hurt_1.png",
            "sing": f"bard_{r_lower}_sing_1.png"
        }

        for state, fname in mapping.items():
            path = os.path.join(base_path, fname)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.smoothscale(img, (36, 60))
                    self.sprites[state] = scaled
                    
                    if state == "idle":
                        self.big_image = pygame.transform.smoothscale(img, (108, 180))
                except Exception: pass

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        
        # Force sing animation if performing
        if self.ai_controller and getattr(self.ai_controller, "state", "") == "performing":
            if "sing" in self.sprites:
                self.image = self.sprites["sing"]
                if not self.facing_right:
                    self.image = pygame.transform.flip(self.image, True, False)