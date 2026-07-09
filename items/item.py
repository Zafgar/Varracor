import pygame
import os

class Item:
    def __init__(self, name, type, cost, description=""):
        self.name = name
        self.type = type # Esim. "Weapon", "Armor", "Tool", "Material"
        self.cost = cost
        self.description = description
        
        self.rarity = "Common"
        self.slot_type = "main_hand"
        self.stackable = False
        self.count = 1
        
        self.image_path = None
        self.image = None
        
        # Stats
        self.damage = 0
        self.defense = 0
        self.stats = {} # Bonus stats like {"str": 1}

    def get_color(self):
        if self.rarity == "Common": return (220, 220, 220)
        if self.rarity == "Rare": return (100, 150, 255)
        if self.rarity == "Epic": return (200, 100, 255)
        if self.rarity == "Legendary": return (255, 215, 0)
        return (255, 255, 255)

    def draw_card_icon(self, surface, x, y, size):
        if self.image_path and not self.image:
            if os.path.exists(self.image_path):
                try:
                    raw = pygame.image.load(self.image_path).convert_alpha()
                    self.image = pygame.transform.smoothscale(raw, (size, size))
                except Exception: pass
        
        if self.image:
            # Skaalaa tarvittaessa
            if self.image.get_width() != size:
                 self.image = pygame.transform.smoothscale(self.image, (size, size))
            surface.blit(self.image, (x, y))
        else:
            # Placeholder
            pygame.draw.rect(surface, (60, 60, 60), (x, y, size, size))
            pygame.draw.rect(surface, (100, 100, 100), (x, y, size, size), 1)

    def draw_equipped(self, surface, rect, facing_right, timer=0, attack_speed=60):
        pass
