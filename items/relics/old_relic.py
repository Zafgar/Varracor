import pygame
from items.base_item import Item

class OldRelic(Item):
    def __init__(self):
        super().__init__()
        self.name = "Old Relic"
        self.rarity = "Common"
        self.description = "A faint magical glow warms your hand."
        self.cost = 60
        self.level_required = 1
        
        self.type = "relic"
        self.slot_type = "off_hand"
        # Ei weapon_groupia -> Kaikki voivat käyttää
        
        # --- PASSIIVISET BONUKSET ---
        # Gladiator.py lukee nämä automaattisesti off-handista
        self.passive_bonuses = {
            "max_mana": 15,
            "mana_regen": 0.05,
            "int": 1
        }

    def draw_card_icon(self, surface, x, y, size):
        # Hohtava pallo
        cx, cy = x + size//2, y + size//2
        pygame.draw.circle(surface, (100, 255, 200), (cx, cy), size*0.25)
        # Kehys
        pygame.draw.polygon(surface, (200, 180, 50), [
            (cx, cy-15), (cx+10, cy), (cx, cy+15), (cx-10, cy)
        ], 2)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_timer):
        # Pieni leijuva valo off-handissa
        x = unit_rect.centerx + (-12 if facing_right else 12) # Takakäsi
        y = unit_rect.centery
        
        import math
        pulse = math.sin(pygame.time.get_ticks() * 0.01) * 3
        
        # Hehku
        s = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(s, (100, 255, 200, 100), (10, 10), 6 + pulse)
        pygame.draw.circle(s, (255, 255, 255, 200), (10, 10), 3)
        
        surface.blit(s, (x-10, y-10))