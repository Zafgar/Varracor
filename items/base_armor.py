import pygame
from items.base_item import Item

class BaseArmor(Item):
    def __init__(self):
        super().__init__()
        self.slot_type = "body"
        self.type = "armor"
        
        # Oletusarvot
        self.armor_group = "cloth" 
        self.level_required = 1
        
        self.health_bonus = 0
        self.mana_bonus = 0
        self.defense = 0
        self.speed_bonus = 0.0
        
        self.color = (150, 150, 150)
        self.trim_color = (50, 50, 50)

    def draw_card_icon(self, surface, x, y, size):
        """
        Oletuspiirto (Fallback).
        Tämä ajetaan VAIN jos lapsiluokka (esim. NoviceRobe) EI määrittele omaa piirtoa.
        """
        pad = size * 0.2
        rect = pygame.Rect(x + pad, y + pad, size - pad*2, size - pad*2)
        pygame.draw.rect(surface, self.color, rect, border_radius=4)
        # Kysymysmerkki tai simppeli kuvio
        pygame.draw.circle(surface, self.trim_color, rect.center, size * 0.1)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_timer):
        """
        Oletuspiirto hahmolle.
        Piirtää yksinkertaisen värillisen laatikon hahmon päälle.
        """
        body_rect = pygame.Rect(unit_rect.x + 8, unit_rect.y + 18, 16, 20)
        pygame.draw.rect(surface, self.color, body_rect, border_radius=3)