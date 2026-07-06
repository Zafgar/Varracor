import pygame
from items.base_item import Item
from sound_manager import sound_system

class Potion(Item):
    def __init__(self, name="Potion", heal_amount=0):
        super().__init__()
        self.name = name
        self.slot_type = "usable"
        self.type = "Usable"
        self.heal_amount = heal_amount

    def draw_card_icon(self, surface, x, y, size):
        # Pieni pullo
        pygame.draw.rect(surface, (200, 200, 200), (x+size*0.4, y+size*0.2, size*0.2, size*0.1))
        pygame.draw.circle(surface, (255, 50, 50), (x+size*0.5, y+size*0.6), size*0.3)

class WeakHealthPotion(Potion):
    def __init__(self):
        super().__init__("Weak Health Potion", heal_amount=30)
        self.cost = 20
        self.rarity = "Common"
        self.description = "Restores 30 HP."