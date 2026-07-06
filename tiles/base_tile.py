import pygame
import os

class MapObject(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path, groups):
        super().__init__(groups)
        
        self.image = None
        
        # Yritetään ladata kuva
        if os.path.exists(image_path):
            try:
                loaded = pygame.image.load(image_path).convert_alpha()
                # Skaalataan 64x64 kokoon varmuuden vuoksi, jos kuva on eri kokoinen
                self.image = pygame.transform.scale(loaded, (64, 64))
            except Exception as e:
                print(f"Error loading tile {image_path}: {e}")
        else:
            print(f"MISSING ASSET: {image_path}")

        # Fallback: Jos kuvaa ei löytynyt, piirrä värikäs neliö
        if self.image is None:
            self.image = pygame.Surface((64, 64))
            self.image.fill((100, 0, 100)) # Violetti virheväri
            pygame.draw.rect(self.image, (0,0,0), (0,0,64,64), 1)

        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        
        # Ominaisuudet
        self.type = "prop"
        self.is_solid = False