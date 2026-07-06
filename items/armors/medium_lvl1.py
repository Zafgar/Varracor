import pygame
from items.base_armor import BaseArmor

class BronzeBreastplate(BaseArmor):
    def __init__(self):
        super().__init__()
        self.name = "Bronze Breastplate"
        self.rarity = "Common"
        self.description = "A solid metal plate protecting the chest. Offers good protection but restricts movement slightly."
        self.cost = 70
        
        # Vaatimukset
        self.level_required = 1
        self.armor_group = "medium" # Vaatii taidon (Medium Armor)
        
        # Stats (Mekaniikka)
        self.defense = 2       
        self.health_bonus = 30
        self.speed_bonus = -0.05 # 5% hidastus
        
        # --- UI STATS (Tooltipiä varten) ---
        self.stats = {
            "Defense": 2,
            "Max HP": 30,
            "Speed": "-5%" # Näytetään selkeästi miinuksena
        }
        
        # Visuaaliset värit
        self.color = (205, 127, 50)     # Pronssi
        self.shade = (139, 69, 19)      # Tummempi varjo
        self.highlight = (235, 177, 100) # Kiilto

    def draw_card_icon(self, surface, x, y, size):
        """Piirtää rintapanssarin markettiin/inventaarioon."""
        pad = size * 0.15
        w = size - pad * 2
        h = size - pad * 2
        
        cx = x + size // 2
        top_y = y + pad
        
        # --- PANSSARIN MUOTO (Cuirass) ---
        # Leveät hartiat, kapenee vyötärölle
        
        points = [
            (x + pad, top_y),               # Vasen olka
            (cx, top_y + 5),                # Kaula-aukko (pieni dippi)
            (x + size - pad, top_y),        # Oikea olka
            (x + size - pad - 2, top_y + h * 0.6), # Oikea kylki
            (x + size - pad, y + size - pad), # Oikea helma (levenee hieman)
            (x + pad, y + size - pad),      # Vasen helma
            (x + pad + 2, top_y + h * 0.6)  # Vasen kylki
        ]
        
        # Piirrä pohja (Varjo)
        pygame.draw.polygon(surface, self.shade, points)
        
        # Piirrä itse panssari (hieman pienempi, jotta varjo jää reunoille)
        inner_points = [(p[0], p[1]+1) for p in points] # Shiftataan alas
        # Kutistetaan hieman leveydestä
        pygame.draw.polygon(surface, self.color, points)
        
        # --- YKSITYISKOHDAT ---
        
        # Keskiviiva (Harjanne)
        pygame.draw.line(surface, self.shade, (cx, top_y + 5), (cx, y + size - pad), 2)
        
        # Kiilto (Highlight) - Vasempaan yläkulmaan "metallinen" heijastus
        shine_pts = [
            (x + pad + 5, top_y + 10),
            (cx - 5, top_y + 10),
            (cx - 5, top_y + 25),
            (x + pad + 8, top_y + 25)
        ]
        pygame.draw.polygon(surface, self.highlight, shine_pts)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_timer):
        """Piirtää panssarin hahmon päälle."""
        
        # Breastplate on jäykkä ja peittää koko torson
        body_rect = pygame.Rect(
            unit_rect.x + 6, 
            unit_rect.y + 18, 
            20, 
            20 
        )
        
        # Pohja
        pygame.draw.rect(surface, self.color, body_rect, border_radius=3)
        
        # Reuna (Outline) jotta erottuu ihosta
        pygame.draw.rect(surface, self.shade, body_rect, 1, border_radius=3)
        
        # Kiilto (Metalli-efekti)
        # Piirretään vaalea viiva vasempaan yläkulmaan
        pygame.draw.line(surface, self.highlight, 
                         (body_rect.left + 3, body_rect.top + 3), 
                         (body_rect.left + 3, body_rect.bottom - 5), 2)