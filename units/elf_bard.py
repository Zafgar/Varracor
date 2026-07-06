import pygame
import os
from units.elf import Elf
from settings import *

class ElfBard(Elf):
    def __init__(self, name, x, y, team_color):
        super().__init__(name, x, y, team_color)
        self.race_name = "Elf"
        
        # Ladataan Bardin omat kuvat
        self._load_bard_sprites()
        
        # Asetetaan oletuskuva
        if "idle" in self.sprites:
            self.image = self.sprites["idle"]

    def _load_bard_sprites(self):
        base_path = "assets/races/elf"
        
        # Kartta tiloista tiedostonimiin
        mapping = {
            "idle": "bard_elf_idle_1.png",
            "run": "bard_elf_walk_1.png",
            "attack": "bard_elf_attack_1.png",
            "hurt": "bard_elf_hurt_1.png",
            "sing": "bard_elf_sing_1.png"
        }
        
        for state, fname in mapping.items():
            path = os.path.join(base_path, fname)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    # Skaalataan Elf-kokoon (40x64)
                    scaled = pygame.transform.smoothscale(img, (40, 64))
                    self.sprites[state] = scaled
                    
                    if state == "idle":
                        self.big_image = pygame.transform.smoothscale(img, (120, 192))
                except Exception: pass

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        
        # Pakota laulukuva jos esiintyy
        if self.ai_controller and getattr(self.ai_controller, "state", "") == "performing":
            if "sing" in self.sprites:
                self.image = self.sprites["sing"]
                if not self.facing_right:
                    self.image = pygame.transform.flip(self.image, True, False)