from ai.base_ai import BaseAI
import random
import pygame
import math
from sound_manager import sound_system

class LeechAI(BaseAI):
    """
    Bog Leech AI: Aggressiivinen laumahyökkääjä.
    """
    def execute_ai(self, all_units, obstacles=None, manager=None):
        # Reagoi nopeammin muutoksiin kuin perus AI
        self.rethink_timer -= 1
        if self.rethink_timer <= 0:
            self.current_target = self.find_best_target(all_units)
            self.rethink_timer = 15 # 0.25s välein uusi arvio
            
        super().execute_ai(all_units, obstacles, manager)

class FrogAI(BaseAI):
    """
    Giant Frog AI: Tankki, joka loikkii vihollisten päälle.
    """
    def __init__(self, unit):
        super().__init__(unit)
        self.leap_cooldown = 0

    def execute_ai(self, all_units, obstacles=None, manager=None):
        if self.unit.is_dead: return
        
        if self.leap_cooldown > 0:
            self.leap_cooldown -= 1
            
        target = self.current_target
        if not self._is_valid_target(target):
            self.current_target = self.find_best_target(all_units)
            target = self.current_target
            
        # Loikkaus-logiikka
        if target:
            dist = math.hypot(target.rect.centerx - self.unit.rect.centerx, 
                              target.rect.centery - self.unit.rect.centery)
            
            # Jos kohde on sopivan matkan päässä (ei ihan vieressä, mutta ei liian kaukana)
            if self.leap_cooldown <= 0 and 100 < dist < 280:
                dx = target.rect.centerx - self.unit.rect.centerx
                dy = target.rect.centery - self.unit.rect.centery
                
                # Käytetään dash-mekaniikkaa loikkana
                if self.unit.perform_dash(dx, dy):
                    self.leap_cooldown = 240 # 4s cooldown loikalle
                    sound_system.play_sound(random.choice([f'frog_jump_{i}' for i in range(1, 5)]))
                    if manager:
                        manager.vfx.show_damage(self.unit.rect.centerx, self.unit.rect.top - 20, "LEAP!", color=(50, 200, 50))
                    return # Loikka vie kontrollin täksi frameksi

        super().execute_ai(all_units, obstacles, manager)
