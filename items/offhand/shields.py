import pygame
from items.base_item import Armor

class Shield(Armor):
    def __init__(self):
        super().__init__()
        self.slot_type = "off_hand"
        self.type = "Shield"
        
        # Oletusarvot (nämä ylikirjoitetaan alaluokissa)
        self.block_chance = 0.15        # Passiivinen torjunta %
        self.stamina_efficiency = 1.0   # 1.0 = normaali kulutus aktiivisessa torjunnassa
        
        # UUSI: Nopeusrangaistus (painava kilpi hidastaa)
        # -0.10 tarkoittaa 10% hitaampaa kävelyä
        self.speed_bonus = -0.10

        # Visuaaliset värit (oletus = puu)
        self.color = (100, 80, 50)
        self.border_color = (60, 50, 30)

    def draw_card_icon(self, surface, x, y, size):
        # UI-ikoni (yksinkertainen kilpi)
        pygame.draw.rect(surface, self.color, (x+size*0.2, y+size*0.2, size*0.6, size*0.6), border_radius=5)
        pygame.draw.rect(surface, self.border_color, (x+size*0.2, y+size*0.2, size*0.6, size*0.6), 2, border_radius=5)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_timer):
        """
        Piirretään kilpi hahmon eteen tai taakse riippuen suunnasta.
        Tätä kutsutaan unit.draw_on_screen() funktiosta.
        """
        # Hahmon keskipiste
        cx, cy = unit_rect.centerx, unit_rect.centery
        
        # Kilven offset (sivulle ja hieman alas)
        offset_x = 10 
        if not facing_right:
            offset_x = -10
            
        shield_x = cx + offset_x
        shield_y = cy + 5
        
        # Kilven koko pikseleinä
        w, h = 12, 18
        
        rect = pygame.Rect(shield_x - w//2, shield_y - h//2, w, h)
        
        # Piirretään kilpi
        pygame.draw.rect(surface, self.color, rect, border_radius=3)
        pygame.draw.rect(surface, self.border_color, rect, 2, border_radius=3)
        
        # "Kahva" tai yksityiskohta keskelle
        pygame.draw.circle(surface, self.border_color, (shield_x, shield_y), 2)


class WoodenShield(Shield):
    def __init__(self):
        super().__init__()
        self.name = "Wooden Shield"
        self.defense = 2
        self.block_chance = 0.15  # 15% block
        self.cost = 60
        self.rarity = "Common"
        self.description = "A sturdy wooden shield. 15% Block chance."
        
        # UUSI: Raskas peruskilpi hidastaa enemmän
        self.speed_bonus = -0.15 # -15% vauhtia
        
        # Pidetään oletusvärit (ruskea)

class SlimeShield(Shield):
    def __init__(self):
        super().__init__()
        self.name = "Slime Shield"
        self.defense = 4
        self.health_bonus = 20
        self.block_chance = 0.25  # 25% block
        self.cost = 100
        self.rarity = "Rare"
        self.description = "Sticky but effective. 25% Block chance."
        
        # UUSI: Kevyempi kilpi hidastaa vähemmän
        self.speed_bonus = -0.05 # -5% vauhtia
        
        # Vihreä limaväri
        self.color = (100, 200, 100) 
        self.border_color = (50, 150, 50)