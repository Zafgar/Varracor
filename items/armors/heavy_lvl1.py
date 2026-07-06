import pygame
from items.base_armor import BaseArmor

class RustyMail(BaseArmor):
    def __init__(self):
        super().__init__()
        self.name = "Rusty Mail"
        self.rarity = "Common"
        self.description = "Old, heavy chainmail covered in rust. Better than nothing, but it slows you down."
        self.cost = 80
        
        # Requirements
        self.level_required = 1
        self.armor_group = "heavy" # Vaatii Heavy Armor skillin
        
        # Stats
        self.health_bonus = 30
        self.defense = 2       # Merkittävä etu alussa (damage -2)
        self.speed_bonus = -0.10 # Hidastaa 10%
        
        # --- UI STATS (Tooltipiä varten) ---
        self.stats = {
            "Defense": 2,
            "Max HP": 30,
            "Speed": "-10%" # Negatiivinen nopeus
        }
        
        # Visuaaliset värit
        self.color = (100, 70, 50)  # Ruosteinen ruskea pohja
        self.link_color = (130, 100, 80) # Hieman vaaleammat renkaat
        self.rust_dark = (60, 40, 30) # Syvä ruoste/varjo

    def draw_card_icon(self, surface, x, y, size):
        """Piirtää rengaspanssarin (Chainmail) tekstuurilla."""
        pad = size * 0.15
        w = size - pad * 2
        h = size - pad * 2
        
        cx = x + size // 2
        top_y = y + pad
        
        # --- MUOTO (T-paita tyylinen) ---
        points = [
            (x + pad, top_y),                # Vasen olka
            (cx, top_y + 5),                 # Kaula
            (x + size - pad, top_y),         # Oikea olka
            (x + size - pad, top_y + h * 0.4), # Oikea hiha
            (x + size - pad - 5, top_y + h * 0.5), # Oikea kainalo
            (x + size - pad - 5, y + size - pad),  # Oikea helma
            (x + pad + 5, y + size - pad),   # Vasen helma
            (x + pad + 5, top_y + h * 0.5),  # Vasen kainalo
            (x + pad, top_y + h * 0.4)       # Vasen hiha
        ]
        
        # 1. Piirrä pohjaväri (Tumma ruoste)
        pygame.draw.polygon(surface, self.rust_dark, points)
        
        # 2. Piirrä "renkaat" (Pistekuviointi polygonin sisään)
        # Teemme yksinkertaisen maskin tai piirrämme vain bounding boxin alueelle ja leikkaamme (tai piirrämme päälle)
        # Yksinkertaisuuden vuoksi piirretään pisteitä riveittäin panssarin alueelle.
        
        step = 4 # Pisteiden väli
        for row_y in range(int(top_y), int(y + size - pad), step):
            # Vuorotteleva offset (tiiliseinä-efekti)
            offset = (row_y // step) % 2 * 2
            
            for col_x in range(int(x + pad), int(x + size - pad), step):
                # Tarkistetaan karkeasti onko piste "paidan" alueella (X-koordinaateilla)
                draw_x = col_x + offset
                
                # Yksinkertaistettu rajaus:
                if (x + pad + 2 < draw_x < x + size - pad - 2):
                    # Piirretään rengas/piste
                    pygame.draw.circle(surface, self.link_color, (draw_x, row_y), 1)

        # 3. Reunaviiva (Outline)
        pygame.draw.polygon(surface, (40, 30, 20), points, 2)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_timer):
        """Piirtää ruosteisen panssarin hahmon päälle."""
        
        body_rect = pygame.Rect(
            unit_rect.x + 6, 
            unit_rect.y + 18, 
            20, 
            20 
        )
        
        # Pohja
        pygame.draw.rect(surface, self.color, body_rect, border_radius=2)
        
        # Tekstuuri (Muutama piste kuvaamaan renkaita)
        for i in range(0, 20, 4):
            for j in range(0, 20, 4):
                if (i + j) % 3 == 0:
                    px = body_rect.x + i
                    py = body_rect.y + j
                    pygame.draw.circle(surface, self.link_color, (px, py), 1)
        
        # Reunaviiva
        pygame.draw.rect(surface, self.rust_dark, body_rect, 1, border_radius=2)