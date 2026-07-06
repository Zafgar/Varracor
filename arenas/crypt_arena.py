import pygame
import random
from settings import *

class CryptArena:
    def __init__(self):
        self.name = "Crypt of the Undead"
        self.width = 3000  # Isompi kartta
        self.height = 2000
        self.obstacles = []
        self._init_obstacles()
        
        # Visuals
        self.bg_color = (15, 12, 18) # Dark purple/black
        self.floor_tiles = []
        
        # Generate floor pattern (stone slabs)
        rows = 12
        cols = 20
        w = self.width // cols
        h = self.height // rows
        for r in range(rows):
            for c in range(cols):
                color_var = random.randint(-5, 5)
                base_c = 30
                col = (base_c + color_var, base_c + color_var, base_c + color_var + 5)
                rect = pygame.Rect(c * w, r * h, w, h)
                self.floor_tiles.append((rect, col))

    def _init_obstacles(self):
        # 1. Central Sarcophagus
        cx, cy = self.width // 2, self.height // 2
        self.obstacles.append(pygame.Rect(cx - 80, cy - 50, 160, 100))
        
        # 2. Pillars near corners (for cover)
        margin_x = 250
        margin_y = 200
        size = 60
        
        self.obstacles.append(pygame.Rect(margin_x, margin_y, size, size))
        self.obstacles.append(pygame.Rect(self.width - margin_x - size, margin_y, size, size))
        self.obstacles.append(pygame.Rect(margin_x, self.height - margin_y - size, size, size))
        self.obstacles.append(pygame.Rect(self.width - margin_x - size, self.height - margin_y - size, size, size))

        # 3. Boundary walls (invisible)
        thickness = 50
        self.obstacles.append(pygame.Rect(0, -thickness, self.width, thickness)) # Top
        self.obstacles.append(pygame.Rect(0, self.height, self.width, thickness)) # Bottom
        self.obstacles.append(pygame.Rect(-thickness, 0, thickness, self.height)) # Left
        self.obstacles.append(pygame.Rect(self.width, 0, thickness, self.height)) # Right

    def update(self, all_units):
        pass

    def draw_background(self, screen, offset=(0, 0)):
        screen.fill(self.bg_color)
        
        # Floor
        for rect, col in self.floor_tiles:
            draw_rect = rect.move(-offset[0], -offset[1])
            # Piirrä vain jos ruudulla
            if screen.get_rect().colliderect(draw_rect):
                pygame.draw.rect(screen, col, draw_rect)
                pygame.draw.rect(screen, (10, 8, 12), draw_rect, 1)

        # Obstacles (Tombs/Pillars)
        for obs in self.obstacles:
            draw_obs = obs.move(-offset[0], -offset[1])
            if not screen.get_rect().colliderect(draw_obs): continue

            # Shadow
            shadow_rect = draw_obs.copy()
            shadow_rect.y += 10
            pygame.draw.rect(screen, (5, 5, 8), shadow_rect)
            
            # Main block
            pygame.draw.rect(screen, (50, 50, 60), draw_obs)
            # Top face highlight
            pygame.draw.rect(screen, (70, 70, 80), draw_obs.inflate(-10, -10))
            
            # Cracks/Details
            pygame.draw.line(screen, (30, 30, 40), (draw_obs.centerx - 10, draw_obs.centery), (draw_obs.centerx + 10, draw_obs.centery), 2)
            pygame.draw.line(screen, (30, 30, 40), (draw_obs.centerx, draw_obs.centery - 10), (draw_obs.centerx, draw_obs.centery + 10), 2)