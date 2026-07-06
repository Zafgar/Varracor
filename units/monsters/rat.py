# units/monsters/rat.py
import pygame
import random
from gladiator import Gladiator
from settings import *

class Rat(Gladiator):
    def __init__(self, name, x, y, team_color):
        # Kutsutaan perusluokkaa rodulla "Giant Rat"
        super().__init__(name, "Giant Rat", x, y, team_color)
        
        # --- ROTAN OMAT STATSIT (TIER 1) ---
        self.max_hp = 30
        self.current_hp = self.max_hp
        self.strength = 4
        self.defense = 0
        
        # Asetetaan nopeus suoraan (nopeampi kuin muut)
        self.walk_speed = 4.0
        self.speed = 4.0
        
        # Aseet (Rotta puree)
        self.primary_weapon = 'Fists' 
        self.attack_range = 30 
        
        # Pienempi koko
        self.rect = pygame.Rect(x, y, 40, 25) 
        self.image = pygame.Surface((40, 25)).convert_alpha()
        
        self.draw_procedural()

    def draw_procedural(self):
        """ Piirtää rotan koodilla """
        self.image.fill((0,0,0,0))
        
        # Vartalo (Harmaa)
        pygame.draw.ellipse(self.image, (100, 100, 100), (5, 5, 30, 20))
        
        # Pää 
        pygame.draw.circle(self.image, (110, 110, 110), (10, 15), 8)
        
        # Nenä (Pinkki)
        pygame.draw.circle(self.image, (255, 150, 150), (4, 15), 3)
        
        # Korvat
        pygame.draw.circle(self.image, (120, 120, 120), (10, 8), 4)
        
        # Häntä (Viiva)
        pygame.draw.line(self.image, (200, 150, 150), (30, 15), (38, 12), 3)
        
        # Tiimiväri
        pygame.draw.rect(self.image, self.team_color, (15, 5, 5, 20))
        
        # Käännä kuva jos vihollinen (vihollinen katsoo vasemmalle)
        if self.team_color == RED:
             self.image = pygame.transform.flip(self.image, True, False)