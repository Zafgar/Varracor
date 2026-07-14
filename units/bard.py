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
        
        # Rotukohtaisten kuvien puuttuessa käytetään elf-bardin kuvia
        # (sama hahmo kuin tavernassa) - ei sinistä neliötä lavalle
        if not self.sprites and race.lower() != "elf":
            self._load_bard_sprites("Elf")

        # Default image
        if "idle" in self.sprites:
            self.image = self.sprites["idle"]
        else:
            # Proseduraalinen bardi (repossa ei ole kuva-assetteja):
            # hahmo luutun kanssa tasavärisen laatikon sijaan
            self.image = self._draw_procedural_bard()

        # Portrait
        if not getattr(self, "big_image", None):
             if self.image:
                # Käytetään kuvan kokoa skaalaukseen, ei hitboxia (joka on vain jalat)
                w, h = self.image.get_size()
                self.big_image = pygame.transform.smoothscale(self.image, (w * 3, h * 3))

    def _draw_procedural_bard(self):
        """Koodipiirretty bardi: tunika, hilkka ja luuttu."""
        surf = pygame.Surface((36, 60), pygame.SRCALPHA)
        # Jalat + saappaat
        pygame.draw.rect(surf, (74, 52, 36), (10, 46, 6, 12))
        pygame.draw.rect(surf, (74, 52, 36), (20, 46, 6, 12))
        # Tunika (viininpunainen)
        pygame.draw.rect(surf, (128, 52, 64), (8, 24, 20, 24),
                         border_radius=4)
        pygame.draw.rect(surf, (96, 38, 48), (8, 24, 20, 24), 1,
                         border_radius=4)
        # Pää + hilkka sulalla
        pygame.draw.circle(surf, (214, 176, 140), (18, 16), 8)
        pygame.draw.polygon(surf, (60, 96, 70),
                            [(9, 14), (27, 14), (24, 6), (12, 6)])
        pygame.draw.line(surf, (226, 212, 120), (25, 8), (31, 2), 2)
        # Luuttu (rungon soikio + kaula)
        pygame.draw.ellipse(surf, (150, 108, 62), (18, 32, 14, 18))
        pygame.draw.line(surf, (110, 78, 44), (24, 34), (33, 22), 3)
        pygame.draw.line(surf, (230, 224, 200), (23, 44), (32, 24), 1)
        return surf

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