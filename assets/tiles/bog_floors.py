import pygame
import random
import os

class BogFloor:
    """
    Procedural swamp floor generator.
    """
    def __init__(self, width, height):
        self.image = pygame.Surface((width, height))
        self._generate_floor(width, height)

    def _generate_floor(self, w, h):
        # 1. Yritetään ladata taustakuva (swamp_floor.png)
        tile_path = "assets/tiles/floors/swamp_floor.png"
        if os.path.exists(tile_path):
            try:
                tile = pygame.image.load(tile_path).convert()
                
                # Skaalataan kuva paljon pienemmäksi (25% alkuperäisestä), jotta tekstuuri on tiheämpi
                new_w = int(tile.get_width() * 0.25)
                new_h = int(tile.get_height() * 0.25)
                tile = pygame.transform.scale(tile, (new_w, new_h))

                # Tiilitetään kuva koko alueelle
                for y in range(0, h, tile.get_height()):
                    for x in range(0, w, tile.get_width()):
                        self.image.blit(tile, (x, y))
                return # Lopetetaan, jos kuva löytyi ja latautui
            except: pass

        # 2. Fallback: Procedural generation (jos kuvaa ei ole)
        # Pohjaväri: Tumma oliivinvihreä / muta
        self.image.fill((30, 35, 20))
        
        # Lisätään tekstuuria (muta-alueita ja ruoholaikkuja)
        for _ in range(400):
            x = random.randint(0, w)
            y = random.randint(0, h)
            radius = random.randint(20, 60)
            
            # 50/50 Muta tai Tumma ruoho
            if random.random() < 0.5:
                color = (40, 30, 20) # Muta (ruskea)
            else:
                color = (25, 40, 25) # Ruoho (vihreä)
                
            pygame.draw.circle(self.image, color, (x, y), radius)

    def draw(self, screen, offset):
        screen.blit(self.image, (-offset[0], -offset[1]))
