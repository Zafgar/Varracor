import pygame
import random
from settings import *

class RatSewerArena:
    def __init__(self):
        self.name = "Rat Sewer"
        self.width = 2400
        self.height = 1600
        self.obstacles = []
        self._init_obstacles()
        
        # Kiinteät spawn-pisteet (Viemäriaukot)
        self.spawn_points = [
            (300, 300), 
            (self.width - 300, self.height - 300)
        ]
        
        self.bg_color = (25, 20, 15) # Muddy brown

    def _init_obstacles(self):
        # Satunnaisia pylväitä
        for _ in range(10):
            x = random.randint(200, self.width - 200)
            y = random.randint(200, self.height - 200)
            self.obstacles.append(pygame.Rect(x, y, 60, 60))

    def get_spawn_point(self):
        """Palauttaa satunnaisen kiinteän spawn-pisteen"""
        return random.choice(self.spawn_points)

    def update(self, all_units):
        pass

    def draw_background(self, screen, offset=(0, 0)):
        screen.fill(self.bg_color)
        
        # Piirretään spawn-pisteet (Ritilät)
        for sp in self.spawn_points:
            x, y = sp
            draw_x = x - offset[0]
            draw_y = y - offset[1]
            
            pygame.draw.circle(screen, (10, 10, 15), (draw_x, draw_y), 30)
            pygame.draw.circle(screen, (60, 60, 70), (draw_x, draw_y), 30, 4)
            pygame.draw.line(screen, (50, 50, 60), (draw_x - 20, draw_y), (draw_x + 20, draw_y), 3)
            pygame.draw.line(screen, (50, 50, 60), (draw_x, draw_y - 20), (draw_x, draw_y + 20), 3)

        # Piirretään esteet
        for obs in self.obstacles:
            r = obs.move(-offset[0], -offset[1])
            if screen.get_rect().colliderect(r):
                pygame.draw.rect(screen, (40, 35, 30), r)
                pygame.draw.rect(screen, (30, 25, 20), r, 2)

    def draw_foreground(self, screen, offset=(0, 0)):
        pass