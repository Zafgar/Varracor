import pygame
from assets.tiles.prop import Prop

class CryptBackWall(Prop):
    """
    Takaseinä (Skaalattu: 400x150).
    """
    def __init__(self, x, y):
        w, h = 400, 150
        # Törmäyslaatikko on vain alaosassa (n. 70px)
        coll_rect = pygame.Rect(x, y + 80, w, 70)
        
        super().__init__(
            x, y, w, h, 
            img_path="assets/tiles/walls/crypt_back_wall.png", 
            collision_rect=coll_rect,
            color=(90, 80, 100)
        )

class CryptSideWall(Prop):
    """
    Sivuseinä (Skaalattu: 80x300).
    """
    def __init__(self, x, y):
        w, h = 80, 300
        super().__init__(
            x, y, w, h, 
            img_path="assets/tiles/walls/crypt_side_wall.png",
            color=(80, 70, 90)
        )

class CryptPillar(Prop):
    """
    Pylväs (48x48).
    """
    def __init__(self, x, y):
        super().__init__(x, y, 48, 48, color=(120, 110, 130))

class CryptCoffin(Prop):
    """
    Hauta-arkku (80x50).
    """
    def __init__(self, x, y):
        super().__init__(x, y, 80, 50, color=(100, 80, 90))