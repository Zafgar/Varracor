from spells.lvl_8.sun_ray_vfx import SunRayBeam

class SunRay:
    def __init__(self):
        self.name = "Sun Ray"
        self.tier = 8
        self.mana_cost = 80
        self.cooldown_max = 600 # 10 sekuntia (mutta kanavointi vie osan tästä)
        self.range = 600        # Pitkä kantama
        self.description = "Channel a massive beam of solar energy. Deals massive damage but immobilizes you."
        self.cost = 3500        # Kallis endgame item
        self.rarity = "Legendary"
        self.type = "spell"
        self.slot_type = "spell" # Voi mennä mihin tahansa spell slottiin
        # Aurinko/valo-teema kuuluu Radiant Synodiin (Holy), ei Pure-magiaan
        # -> siirretty pois Prismin satunnaispoolista.
        self.school = "holy"
        # Yhteensopivuus koulukaupan listan kanssa (data-vetoiset kentät)
        self.tier = 8
        self.damage_type = "Holy"
        self.archetype = "channel"

    def cast(self, caster, target, manager):
        # Tarkistetaan onko kohde olemassa
        if not target:
            return False
            
        # Luodaan efekti (joka hoitaa myös vahingon ja casterin lukituksen)
        # Välitetään target-olio, jotta säde voi seurata sitä
        
        beam = SunRayBeam(manager, caster, target, duration=300) # 5 sekuntia (oli 180)
        manager.vfx.add_effect(beam)
        
        return True

    def draw_card_icon(self, surface, x, y, size):
        # Piirretään ikoni UI:ta varten
        import pygame
        rect = pygame.Rect(x, y, size, size)
        
        # Tausta (Kulta/Oranssi)
        pygame.draw.rect(surface, (255, 140, 0), rect, border_radius=8)
        pygame.draw.rect(surface, (255, 215, 0), rect, 2, border_radius=8)
        
        # Säde symboli
        cx, cy = x + size//2, y + size//2
        pygame.draw.line(surface, (255, 255, 200), (cx, y+5), (cx, y+size-5), 6)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 8)
        
        # Säteet
        for i in range(0, 360, 45):
            import math
            rad = math.radians(i)
            ex = cx + math.cos(rad) * (size//2 - 5)
            ey = cy + math.sin(rad) * (size//2 - 5)
            pygame.draw.line(surface, (255, 200, 50), (cx, cy), (ex, ey), 2)
