import pygame
import random
import os

class MuckfordFloor:
    """
    Mutainen ja kivetty katu.
    """
    def __init__(self, w, h):
        self.image = pygame.Surface((w, h))
        self._generate_floor(w, h)

    def _generate_floor(self, w, h):
        # 1. Yritetään ladata kuva
        tile_path = "assets/tiles/floors/muckford_floor.png"
        if os.path.exists(tile_path):
            try:
                tile = pygame.image.load(tile_path).convert()
                # Skaalataan pienemmäksi (tiheämpi tekstuuri)
                tile = pygame.transform.scale(tile, (256, 256))
                # Tiilitetään kuva koko alueelle
                for y in range(0, h, tile.get_height()):
                    for x in range(0, w, tile.get_width()):
                        self.image.blit(tile, (x, y))
                return # Lopetetaan jos kuva löytyi
            except Exception: pass

        # 2. Fallback: Generoidaan koodilla jos kuvaa ei ole
        self.image.fill((60, 50, 40)) # Muta
        
        # Piirretään "kivetystä" tai lankkuja
        for _ in range(500):
            x = random.randint(0, w)
            y = random.randint(0, h)
            rw = random.randint(20, 60)
            rh = random.randint(10, 30)
            col = (70, 60, 50)
            pygame.draw.rect(self.image, col, (x, y, rw, rh))

    def draw(self, screen, offset):
        screen.blit(self.image, (-offset[0], -offset[1]))