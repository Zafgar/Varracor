import pygame
from items.base_helmet import BaseHelmet

class VikingHelm(BaseHelmet):
    def __init__(self):
        super().__init__()
        self.name = "Viking Helmet"
        self.rarity = "Rare"
        self.description = "Horned helmet. Grants +2 Strength."
        self.cost = 150
        
        # Vaatimukset
        self.level_required = 1
        self.armor_group = "medium" # Tai "heavy", riippuen miten haluat tasapainottaa
        
        # Statsit
        self.defense = 3
        self.health_bonus = 25
        self.speed_bonus = 0.0 # Ei hidasta
        
        # --- ERIKOISUUS: VOIMABONUS ---
        # Tämä toimii nyt, koska gladiator.py lukee passive_bonuses kaikista esineistä!
        self.passive_bonuses = {
            "str": 2
        }
        
        self.color = (170, 170, 180) # Teräksen harmaa

    def draw_equipped(self, surface, unit_rect, facing_right, attack_timer):
        # Pään sijainti (vakio 32x48 hahmolle)
        head_x = unit_rect.x + 7
        head_y = unit_rect.y + 2
        
        # 1. Kypärän kupu (Pyöreä metalli)
        pygame.draw.circle(surface, self.color, (head_x + 9, head_y + 7), 9)
        # Reunaviiva
        pygame.draw.circle(surface, (50, 50, 60), (head_x + 9, head_y + 7), 9, 1) 
        
        # 2. Sarvet (Horns)
        horn_col = (240, 230, 200) # Luun värinen
        
        # Vasen sarvi
        start_l = (head_x + 2, head_y + 6)
        end_l = (head_x - 4, head_y - 2)
        pygame.draw.line(surface, horn_col, start_l, end_l, 3)
        
        # Oikea sarvi
        start_r = (head_x + 16, head_y + 6)
        end_r = (head_x + 22, head_y - 2)
        pygame.draw.line(surface, horn_col, start_r, end_r, 3)
        
        # 3. Nenäsuoja (Nose guard) - pieni yksityiskohta
        nose_x = head_x + 9
        if facing_right: nose_x += 2 
        else: nose_x -= 2
            
        pygame.draw.line(surface, (100, 110, 120), (nose_x, head_y + 7), (nose_x, head_y + 12), 2)