import pygame
from settings import *

class ArenaObstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, type):
        super().__init__()
        self.type = type # 'wall', 'water', 'mud', 'spike', 'lava'
        self.rect = pygame.Rect(x, y, w, h)
        
        # Värit debuggausta varten (jos kuvaa ei ole)
        if self.type == 'wall': self.color = (80, 80, 80)
        elif self.type == 'lava': self.color = (200, 50, 0)
        elif self.type == 'mud': self.color = (100, 80, 40)
        elif self.type == 'water': self.color = (0, 100, 200)
        elif self.type == 'spike': self.color = (100, 20, 20)
        else: self.color = (150, 150, 150)

class BaseArena:
    def __init__(self, name):
        self.name = name
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.obstacles = pygame.sprite.Group()
        self.hazards = [] # Lista asioista jotka tekevät vahinkoa (esim. salama)
        self.floor_color = (40, 40, 40)
        
    def update(self, all_units):
        """ Päivittää areenan dynaamiset efektit (sää, ansat) """
        pass

    def draw_background(self, screen):
        """ Piirtää lattian (hahmojen alle) """
        # Piirretään koko ruudun kokoinen tausta
        pygame.draw.rect(screen, self.floor_color, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

    def draw_foreground(self, screen):
        """ Piirtää esteet ja sääefektit (hahmojen päälle tai alle) """
        for obs in self.obstacles:
            pygame.draw.rect(screen, obs.color, obs.rect)
            # Reunus selkeyden vuoksi
            pygame.draw.rect(screen, (0,0,0), obs.rect, 2)