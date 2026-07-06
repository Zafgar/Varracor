import pygame
import math
from items.base_item import Item

class Relic(Item):
    def __init__(self):
        super().__init__()
        self.slot_type = "off_hand"
        self.type = "Relic"
        self.rarity = "Rare"
        # Sanakirja bonuksista: {'int': 5, 'mana_regen': 0.1, ...}
        self.passive_bonuses = {} 

    def draw_card_icon(self, surface, x, y, size):
        # Piirretään "kirja" tai "orb"
        pygame.draw.circle(surface, (100, 0, 200), (x + size//2, y + size//2), size//2 - 5)
        pygame.draw.circle(surface, (150, 50, 250), (x + size//2, y + size//2), size//3)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_timer):
        # Relic leijuu hahmon vieressä
        cx, cy = unit_rect.centerx, unit_rect.centery
        off_x = -20 if facing_right else 20
        
        # Pieni "hyllyvä" liike
        time_shift = pygame.time.get_ticks() * 0.005
        hover_y = math.sin(time_shift) * 5
        
        # Hehkuva pallo
        pygame.draw.circle(surface, (150, 50, 250), (int(cx + off_x), int(cy + hover_y)), 6)
        pygame.draw.circle(surface, (200, 100, 255), (int(cx + off_x), int(cy + hover_y)), 3)

# --- KONKREETTISET RELICIT ---

class TomeOfKnowledge(Relic):
    def __init__(self):
        super().__init__()
        self.name = "Tome of Knowledge"
        self.cost = 300
        self.rarity = "Epic"
        self.description = "+5 INT, +20 Mana. A magical book."
        self.passive_bonuses = {'int': 5, 'mana': 20}

class HolySymbol(Relic):
    def __init__(self):
        super().__init__()
        self.name = "Holy Symbol"
        self.cost = 250
        self.rarity = "Rare"
        self.description = "+30 HP, +20 Stamina."
        self.passive_bonuses = {'hp': 30, 'stamina': 20}