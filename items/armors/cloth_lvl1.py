import pygame
from items.base_armor import BaseArmor

class NoviceRobe(BaseArmor):
    def __init__(self):
        super().__init__()
        self.name = "Novice Robe"
        self.rarity = "Common"
        # Tämä teksti näkyy nyt kortissa!
        self.description = "A thin cloth robe worn by apprentice mages. Allows for easy movement and mana flow."
        self.cost = 50
        
        self.level_required = 1
        self.armor_group = "cloth"
        
        # --- TEKNISET BONUKSET (Peliä varten) ---
        self.health_bonus = 15
        self.mana_bonus = 10
        self.defense = 0
        self.speed_bonus = 0.05 # 5% nopeampi liikkuminen
        
        # --- UI BONUKSET (Korttia varten) ---
        # Lisää tänne kaikki mitä haluat näyttää pelaajalle
        self.stats = {
            "Max HP": 15,
            "Max Mana": 10,
            "Speed": "+5%" # Voidaan kirjoittaa tekstinä
        }
        
        # Ulkonäkö
        self.color = (200, 190, 170)
        self.trim_color = (100, 80, 60)

    def draw_card_icon(self, surface, x, y, size):
        # ... (Sama hieno piirto kuin aiemmin) ...
        pad = size * 0.15
        w = size - pad * 2
        h = size - pad * 2
        cx = x + size // 2
        top_y = y + pad
        shade = (max(0, self.color[0]-40), max(0, self.color[1]-40), max(0, self.color[2]-40))

        shoulder_pts = [(cx, top_y), (x + size - pad, top_y + h*0.4), (x + size - pad - 5, top_y + h*0.5), (x + pad + 5, top_y + h*0.5), (x + pad, top_y + h*0.4)]
        pygame.draw.polygon(surface, self.color, shoulder_pts)
        
        body_pts = [(x + pad + 5, top_y + h*0.5), (x + pad, y + size - pad), (x + size - pad, y + size - pad), (x + size - pad - 5, top_y + h*0.5)]
        pygame.draw.polygon(surface, self.color, body_pts)
        
        belt_y = top_y + h * 0.6
        pygame.draw.line(surface, self.trim_color, (x+pad+2, belt_y), (x+size-pad-2, belt_y), 3)
        
        pygame.draw.polygon(surface, shade, shoulder_pts, 2)
        pygame.draw.polygon(surface, shade, body_pts, 2)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_timer):
        # ... (Sama piirto kuin aiemmin) ...
        body_rect = pygame.Rect(unit_rect.x + 6, unit_rect.y + 18, 20, 22)
        pygame.draw.rect(surface, self.color, body_rect, border_radius=4)
        belt_y = body_rect.y + 12
        pygame.draw.line(surface, self.trim_color, (body_rect.left, belt_y), (body_rect.right, belt_y), 2)
        pygame.draw.line(surface, (0,0,0,50), (body_rect.centerx, belt_y), (body_rect.centerx, body_rect.bottom), 1)