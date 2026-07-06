import pygame
from spells.lvl_2.life_drain_vfx import LifeDrainBeam

class LifeDrain:
    def __init__(self):
        self.name = "Life Drain"
        self.tier = 2
        self.mana_cost = 10 # Aloituskustannus
        self.cooldown_max = 60 # Lyhyt cooldown lopetuksen jälkeen
        self.range = 350       # Keskipitkä kantama
        self.description = "Channels a necrotic beam that drains HP from the enemy to heal you. Consumes mana continuously."
        self.cost = 450        # Hinta kaupassa
        self.rarity = "Rare"
        self.type = "spell"
        self.slot_type = "spell"

    def cast(self, caster, target, manager):
        if not target: return False
        
        # Luodaan efekti (joka hoitaa logiikan)
        beam = LifeDrainBeam(manager, caster, target)
        manager.vfx.add_effect(beam)
        
        return True

    def draw_card_icon(self, surface, x, y, size):
        # Ikonin piirto (Vihreä kallo/säde)
        rect = pygame.Rect(x, y, size, size)
        
        # Tausta
        pygame.draw.rect(surface, (20, 0, 20), rect, border_radius=8)
        pygame.draw.rect(surface, (100, 255, 100), rect, 2, border_radius=8)
        
        cx, cy = x + size//2, y + size//2
        
        # Kallo-mainen muoto
        pygame.draw.circle(surface, (200, 255, 200), (cx, cy - 5), 10)
        pygame.draw.rect(surface, (200, 255, 200), (cx - 6, cy, 12, 12))
        
        # Silmät
        pygame.draw.circle(surface, (0, 0, 0), (cx - 3, cy - 5), 3)
        pygame.draw.circle(surface, (0, 0, 0), (cx + 3, cy - 5), 3)
        
        # Säde
        pygame.draw.line(surface, (50, 255, 50), (cx, cy+10), (cx, y+size-5), 3)
