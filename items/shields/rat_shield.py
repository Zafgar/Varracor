import pygame
import math
from settings import *

class RatKingShield:
    def __init__(self):
        self.name = "Rat King Shield"
        self.type = "shield"
        self.slot_type = "off_hand"
        self.defense = 5
        self.block_chance = 0.30
        self.rarity = "Epic"
        self.description = "A heavy shield made of sewer scrap. High block chance."
        self.cost = 600
        self.health_bonus = 50
        self.weapon_group = "shield"
        self.level_required = 2
        self.in_shop = False

    def draw_card_icon(self, surface, x, y, size):
        pygame.draw.rect(surface, (40, 30, 30), (x, y, size, size), border_radius=5)
        pygame.draw.rect(surface, (180, 60, 180), (x, y, size, size), 2, border_radius=5)
        
        cx, cy = x + size//2, y + size//2
        s = size
        
        # Kilven runko (Ruosteinen metalli)
        pygame.draw.circle(surface, (90, 70, 60), (cx, cy), s*0.35)
        pygame.draw.circle(surface, (60, 50, 40), (cx, cy), s*0.35, 3)
        
        # Rotta-symboli (Vihreä)
        pygame.draw.circle(surface, (60, 100, 60), (cx, cy - 2), s*0.15)
        pygame.draw.circle(surface, (255, 50, 50), (cx - 3, cy - 4), 2) # Silmä
        pygame.draw.circle(surface, (255, 50, 50), (cx + 3, cy - 4), 2) # Silmä
        
        # Piikit reunoilla
        for i in range(0, 360, 45):
            rad = math.radians(i)
            ex = cx + math.cos(rad) * (s*0.35 + 4)
            ey = cy + math.sin(rad) * (s*0.35 + 4)
            pygame.draw.line(surface, (160, 160, 160), (cx + math.cos(rad)*s*0.3, cy + math.sin(rad)*s*0.3), (ex, ey), 2)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_timer):
        offset_x = 8 if facing_right else -8
        center_x = unit_rect.centerx + offset_x
        center_y = unit_rect.centery + 2
        
        # Poison Glow
        pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.5
        glow_radius = 12 + int(pulse * 2)
        pygame.draw.circle(surface, (40, 200, 40), (center_x, center_y), glow_radius)

        # Kilven runko
        pygame.draw.circle(surface, (90, 70, 60), (center_x, center_y), 10)
        pygame.draw.circle(surface, (60, 50, 40), (center_x, center_y), 10, 2)
        # Rotta-symboli
        pygame.draw.circle(surface, (60, 100, 60), (center_x, center_y - 1), 4)
