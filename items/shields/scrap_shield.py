import pygame
import os
from items.base_item import Item

class ScrapShield(Item):
    def __init__(self):
        super().__init__()
        self.name = "Pot Lid"
        self.rarity = "Common"
        self.cost = 15
        self.description = "Better than nothing, but not by much."
        
        self.type = "shield"
        self.slot_type = "off_hand"
        self.armor_group = "shield"
        self.level_required = 1
        
        self.defense = 1
        self.block_chance = 0.10 # 10% chance
        self.shield_tier = 1  # 1=perus, 2=Tower Discipline
        self.speed_bonus = -0.02
        
        self.image = None
        self._load_image()

    def _load_image(self):
        path = "assets/gear/shields/scrap_shield.png"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (24, 28))
                self.big_image = img
            except Exception: pass

    def draw_card_icon(self, surface, x, y, size):
        img = getattr(self, "big_image", self.image)
        if img:
            ratio = img.get_width() / img.get_height()
            new_h = size
            new_w = int(new_h * ratio)
            scaled = pygame.transform.smoothscale(img, (new_w, new_h))
            surface.blit(scaled, (x + (size - new_w) // 2, y))

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown):
        from items.shields.weak_shield import WeakShield
        WeakShield.draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown)