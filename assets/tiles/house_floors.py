import pygame
import os

class HouseFloor:
    def __init__(self, width, height):
        self.image = pygame.Surface((width, height))
        self._generate_floor(width, height)

    def _generate_floor(self, w, h):
        tile_path = "assets/tiles/houses/floor_brick_1.png"
        
        tile_surf = None
        if os.path.exists(tile_path):
            try:
                raw = pygame.image.load(tile_path).convert()
                # Skaalaus: Jos seinä on n. 60px leveä ja 4 seinää mahtuu yhdelle lattialle,
                # lattian pitäisi olla n. 240px leveä.
                tile_surf = pygame.transform.scale(raw, (240, 240))
            except Exception: pass
            
        if not tile_surf:
            tile_surf = pygame.Surface((240, 240))
            tile_surf.fill((60, 40, 30)) # Tumma puu/tiili
            pygame.draw.rect(tile_surf, (50, 30, 20), (0, 0, 240, 240), 2)

        # Tiilitetään
        tile_w = tile_surf.get_width()
        tile_h = tile_surf.get_height()
        
        for y in range(0, h, tile_h):
            for x in range(0, w, tile_w):
                self.image.blit(tile_surf, (x, y))

    def draw(self, screen, offset=(0,0)):
        screen.blit(self.image, (-offset[0], -offset[1]))

class BlacksmithFloor:
    def __init__(self, width, height):
        self.image = pygame.Surface((width, height))
        self._generate_floor(width, height)

    def _generate_floor(self, w, h):
        tile_path = "assets/tiles/floors/tile_floor_1.png"
        
        tile_surf = None
        if os.path.exists(tile_path):
            try:
                tile_surf = pygame.image.load(tile_path).convert()
                # Scale down to ensure ~8x8 grid (Arena is 1000x800, so 100x100 tiles)
                tile_surf = pygame.transform.scale(tile_surf, (100, 100))
            except Exception: pass
            
        if not tile_surf:
            tile_surf = pygame.Surface((64, 64))
            tile_surf.fill((40, 40, 45))
            pygame.draw.rect(tile_surf, (30, 30, 35), (0, 0, 64, 64), 1)

        tile_w = tile_surf.get_width()
        tile_h = tile_surf.get_height()
        
        for y in range(0, h, tile_h):
            for x in range(0, w, tile_w):
                self.image.blit(tile_surf, (x, y))

    def draw(self, screen, offset=(0,0)):
        screen.blit(self.image, (-offset[0], -offset[1]))
