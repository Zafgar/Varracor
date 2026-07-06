import pygame
import os

class Lute:
    def __init__(self):
        self.name = "Bard's Lute"
        self.slot_type = "main_hand"
        self.rarity = "Common"
        self.cost = 50
        self.description = "A finely crafted instrument."
        
        # Stats (ei taisteluun, mutta estää crashit)
        self.damage = 2
        self.speed_bonus = 0
        self.range = 0
        self.type = "tool"
        
        # Kuva
        self.image = None
        path = "assets/gear/tools/lute.png"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                # Skaalataan sopivaksi käteen
                self.image = pygame.transform.smoothscale(img, (24, 24))
            except: pass
            
        if not self.image:
            self.image = pygame.Surface((10, 20))
            self.image.fill((139, 69, 19)) # Ruskea fallback

    def draw_equipped(self, surface, rect, facing_right, attack_timer, attack_speed=60):
        if not self.image: return

        # Sijainti (Kädessä)
        offset_x = 10 if facing_right else 2
        offset_y = 15
        
        # Soittoanimaatio (heiluu vähän)
        import math
        bob = math.sin(pygame.time.get_ticks() * 0.01) * 2
        
        img = self.image
        if not facing_right:
            img = pygame.transform.flip(img, True, False)
            
        # Käännetään hieman soittoasentoon
        angle = 30 if facing_right else -30
        img = pygame.transform.rotate(img, angle + bob)
        
        draw_x = rect.x + offset_x
        draw_y = rect.y + offset_y + bob
        
        surface.blit(img, (draw_x, draw_y))