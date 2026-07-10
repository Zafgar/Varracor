import pygame
import os
from items.base_item import Item

class WeakShield(Item):
    def __init__(self):
        super().__init__()
        self.name = "Wooden Buckler"
        self.rarity = "Common"
        self.cost = 35
        self.description = "A simple shield. Blocks some attacks."
        
        self.type = "shield"
        self.slot_type = "off_hand"
        self.armor_group = "shield"
        
        self.defense = 2
        self.block_chance = 0.20 # 20% chance to block completely
        self.speed_bonus = -0.05
        
        self.image = None
        self._load_image()

    def _load_image(self):
        path = "assets/gear/shields/weak_shield.png"
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
        else:
            pygame.draw.circle(surface, (100, 80, 40), (x+size/2, y+size/2), size*0.3)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown):
        if not self.image: return

        # Kilpi on off-handissa, eli "takana" jos katsotaan oikealle, "edessä" jos vasemmalle?
        # Yleensä off-hand piirretään ennen tai jälkeen riippuen suunnasta.
        # Tässä yksinkertaistettu:
        offset_x = -5 if facing_right else 5
        hand_x = unit_rect.centerx + offset_x
        hand_y = unit_rect.centery + 5
        
        img_to_draw = self.image
        if not facing_right:
            img_to_draw = pygame.transform.flip(self.image, True, False)
            
        rect = img_to_draw.get_rect(center=(hand_x, hand_y))
        surface.blit(img_to_draw, rect)
