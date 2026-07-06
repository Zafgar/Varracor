import pygame
from items.base_armor import BaseArmor

class BaseHelmet(BaseArmor):
    def __init__(self):
        super().__init__()
        # TÄRKEÄÄ: Tämä määrittää slotin (head vs body)
        self.slot_type = "head"
        
        # Oletukset
        self.armor_group = "cloth"
        self.level_required = 1
        self.color = (100, 100, 100)

    def draw_card_icon(self, surface, x, y, size):
        # Piirretään geneerinen kypäräikoni
        pad = size * 0.2
        rect = pygame.Rect(x + pad, y + pad, size - pad*2, size - pad*2)
        # Kupu
        pygame.draw.arc(surface, self.color, rect, 0, 3.14, 4)
        # Alareuna
        pygame.draw.line(surface, self.color, (rect.left, rect.centery), (rect.right, rect.centery), 4)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_timer):
        # Oletuspiirto: värillinen "pipo" pään päällä
        head_x = unit_rect.x + 8
        head_y = unit_rect.y + 2
        pygame.draw.rect(surface, self.color, (head_x, head_y, 16, 6))