import pygame
import random
from settings import *
from arenas.base_arena import BaseArena, ArenaObstacle
from vfx import spawn_floating_text

class StormArena(BaseArena):
    def __init__(self):
        super().__init__("Storm Plains")
        self.floor_color = (40, 50, 40) # Tumma ruoho
        
        # Vettä
        self.obstacles.add(ArenaObstacle(300, 300, 150, 100, 'water'))
        self.obstacles.add(ArenaObstacle(600, 500, 150, 100, 'water'))
        
        # Salama-ajastin
        self.lightning_timer = random.randint(300, 600) # 5-10 sekuntia
        self.flash_alpha = 0

    def update(self, all_units):
        # Salama logiikka
        self.lightning_timer -= 1
        if self.lightning_timer <= 0:
            self.trigger_lightning(all_units)
            self.lightning_timer = random.randint(300, 600)

        if self.flash_alpha > 0:
            self.flash_alpha -= 10

    def trigger_lightning(self, all_units):
        self.flash_alpha = 150 # Välähdys
        
        # Valitse satunnainen uhri
        living_units = [u for u in all_units if not u.is_dead]
        if living_units:
            target = random.choice(living_units)
            dmg = 20
            target.take_damage(dmg, 'Magic')
            spawn_floating_text(target.rect.centerx, target.rect.top - 20, "ZAP!", (255, 255, 0))

    def draw_foreground(self, screen):
        super().draw_foreground(screen)
        
        # Sade
        for _ in range(50):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(60, SCREEN_HEIGHT-80)
            pygame.draw.line(screen, (100, 100, 200), (x, y), (x-2, y+10), 1)

        # Salama välähdys (koko ruutu)
        if self.flash_alpha > 0:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash.fill((255, 255, 255))
            flash.set_alpha(self.flash_alpha)
            screen.blit(flash, (0, 0))