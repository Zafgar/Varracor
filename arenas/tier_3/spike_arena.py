import pygame
import random
from settings import *
from arenas.base_arena import BaseArena, ArenaObstacle
from vfx import spawn_floating_text

class SpikeArena(BaseArena):
    def __init__(self):
        super().__init__("Spike Pit")
        self.floor_color = (60, 30, 30) # Ruosteinen lattia
        
        # Piikkejä
        coords = [(400, 300), (600, 300), (500, 450), (300, 200), (700, 200)]
        for x, y in coords:
            self.obstacles.add(ArenaObstacle(x, y, 40, 40, 'spike'))

    def update(self, all_units):
        # Tarkista osuuko joku piikkeihin
        spikes = [o for o in self.obstacles if o.type == 'spike']
        
        for unit in all_units:
            if unit.is_dead: continue
            
            # Osuuko piikkiin?
            hit_list = pygame.sprite.spritecollide(unit, spikes, False)
            for spike in hit_list:
                # Ota vahinkoa (mutta vain harvoin, ettei sula heti)
                if random.random() < 0.05: 
                    unit.take_damage(2, 'Physical')