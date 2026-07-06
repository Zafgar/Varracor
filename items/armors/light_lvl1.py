import pygame
from items.base_armor import BaseArmor

class PaddedVest(BaseArmor):
    def __init__(self):
        super().__init__()
        self.name = "Padded Vest"
        self.rarity = "Common"
        self.description = "Layers of thick cloth and thin leather. Offers basic protection."
        self.cost = 40
        
        # Vaatimukset
        self.level_required = 1
        self.armor_group = "light" # (Tai "cloth", riippuen miten haluat skillit)
        
        # Stats (Mekaniikka)
        self.defense = 1 
        self.health_bonus = 20
        self.speed_bonus = 0.0 
        
        # --- UI STATS (Tooltipiä varten) ---
        self.stats = {
            "Defense": 1,
            "Max HP": 20
        }
        
        # Visuaalinen väri (Ruskehtava)
        self.color = (139, 69, 19) 
        self.stitch_color = (160, 100, 50) # Vaaleampi tikkausväri

    def draw_card_icon(self, surface, x, y, size):
        """Piirtää tikatun liivin markettiin/inventaarioon."""
        pad = size * 0.15
        w = size - pad * 2
        h = size - pad * 2
        
        cx = x + size // 2
        top_y = y + pad
        
        # 1. Liivin muoto (Hihaton, avoin kaula)
        # Jaetaan vasempaan ja oikeaan puoliskoon
        
        # Vasen puoli
        left_poly = [
            (cx - 2, top_y + h),      # Ala-keski
            (x + pad, top_y + h),     # Ala-vasen
            (x + pad, top_y),         # Ylä-vasen (olka)
            (cx - 6, top_y),          # Kaula-aukko alku
            (cx - 2, top_y + h*0.3)   # Rinta-aukko
        ]
        
        # Oikea puoli
        right_poly = [
            (cx + 2, top_y + h),
            (x + size - pad, top_y + h),
            (x + size - pad, top_y),
            (cx + 6, top_y),
            (cx + 2, top_y + h*0.3)
        ]
        
        pygame.draw.polygon(surface, self.color, left_poly)
        pygame.draw.polygon(surface, self.color, right_poly)
        
        # 2. Tikkaukset (Vaakaviivat luomaan "padded" efekti)
        for i in range(1, 4):
            ly = top_y + (h * 0.25 * i)
            # Vasen tikkaus
            pygame.draw.line(surface, self.stitch_color, (x+pad+2, ly), (cx-3, ly), 1)
            # Oikea tikkaus
            pygame.draw.line(surface, self.stitch_color, (cx+3, ly), (x+size-pad-2, ly), 1)
            
        # 3. Reunaviivat
        shade = (100, 50, 10)
        pygame.draw.polygon(surface, shade, left_poly, 1)
        pygame.draw.polygon(surface, shade, right_poly, 1)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_timer):
        """Piirtää liivin hahmon päälle."""
        
        # Liivi on lyhyempi kuin kaapu
        body_rect = pygame.Rect(
            unit_rect.x + 7, 
            unit_rect.y + 18, 
            18, 
            18  # Lyhyt helma
        )
        
        # Piirrä liivi
        pygame.draw.rect(surface, self.color, body_rect, border_radius=2)
        
        # Keskiviiva (napitus)
        pygame.draw.line(surface, (80, 40, 10), (body_rect.centerx, body_rect.top), (body_rect.centerx, body_rect.bottom), 1)