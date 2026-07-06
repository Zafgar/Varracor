import pygame
import math
import random
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

class MapVFX:
    def __init__(self):
        self.fog_scroll = 0.0
        # Luodaan muutama usvapilvi
        self.clouds = []
        for _ in range(12):
            self.clouds.append({
                'x': random.randint(0, 3000),
                'y': random.randint(0, 2000),
                'size': random.randint(200, 500),
                'speed': random.uniform(0.2, 0.8),
                'alpha': random.randint(30, 70)
            })

    def update(self, manager):
        self.fog_scroll += 0.5
        for c in self.clouds:
            c['x'] += c['speed']
            if c['x'] > 3000: c['x'] = -c['size']

    def draw_floor(self, screen, offset):
        pass

    def draw_top(self, screen, offset):
        # Piirretään vihertävää usvaa hahmojen päälle
        for c in self.clouds:
            dx = c['x'] - offset[0]
            dy = c['y'] - offset[1]
            
            # Piirretään vain jos on ruudulla
            if -c['size'] < dx < SCREEN_WIDTH and -c['size'] < dy < SCREEN_HEIGHT:
                s = pygame.Surface((c['size'], c['size']), pygame.SRCALPHA)
                pygame.draw.circle(s, (40, 80, 40, c['alpha']), (c['size']//2, c['size']//2), c['size']//2)
                screen.blit(s, (dx, dy))
