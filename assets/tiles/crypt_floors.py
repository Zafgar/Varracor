import pygame
import os

class CryptFloor:
    """
    Hoitaa lattian piirtämisen ja tiilittämisen (Tiling).
    """
    def __init__(self, width, height):
        self.image = pygame.Surface((width, height))
        self._generate_floor(width, height)

    def _generate_floor(self, w, h):
        # Ladataan tile (1500x1000)
        tile_w, tile_h = 1500, 1000
        tile_path = "assets/tiles/floors/crypt_floor.png"
        
        tile_surf = pygame.Surface((tile_w, tile_h))
        tile_surf.fill((20, 18, 22)) # Fallback tumma
        
        if os.path.exists(tile_path):
            try:
                loaded = pygame.image.load(tile_path).convert()
                tile_surf = pygame.transform.scale(loaded, (tile_w, tile_h))
            except Exception: pass
        
        # Tiilitetään koko alueelle
        for y in range(0, h, tile_h):
            for x in range(0, w, tile_w):
                self.image.blit(tile_surf, (x, y))

    def draw(self, screen, offset):
        screen.blit(self.image, (-offset[0], -offset[1]))