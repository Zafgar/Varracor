import pygame
import math
import random
from assets.tiles.prop import Prop
from sound_manager import sound_system

class ForestBush(Prop):
    """
    Iso pensas (bush_large_1).
    """
    def __init__(self, x, y):
        w, h = 90, 70
        # Pieni törmäyslaatikko keskellä alhaalla
        coll_rect = pygame.Rect(x + 15, y + 40, 60, 20)
        super().__init__(
            x, y, w, h, 
            img_path="assets/tiles/forest/bush_large_1.png", 
            collision_rect=coll_rect, 
            color=(30, 60, 30)
        )
        self.is_structure = True # Estää liikkumisen
        
        # Wind sway
        self.sway_timer = random.uniform(0, 100)
        self.base_image = self.image
        self.origin_pos = (x, y)

    def update(self, obstacles=None, manager=None, **kwargs):
        # Wind sway animation (Subtle)
        self.sway_timer += 0.03
        angle = math.sin(self.sway_timer) * 1.5 # +/- 1.5 degrees
        self.image = pygame.transform.rotate(self.base_image, angle)
        
        # Pivot at bottom center
        w, h = self.base_image.get_size()
        rw, rh = self.image.get_size()
        ox, oy = self.origin_pos
        self.image_pos = (ox + (w - rw) // 2, oy + (h - rh))

class ForestRockBig(Prop):
    """
    Iso kivi (rock_big).
    Alkuperäinen 970x700 -> Skaalataan n. 180x130 (2x pelaajan korkeus).
    """
    def __init__(self, x, y):
        w, h = 180, 130
        # Hitbox alaosassa
        coll_rect = pygame.Rect(x + 20, y + h - 50, w - 40, 40)
        super().__init__(
            x, y, w, h, 
            img_path="assets/tiles/forest/rock_big.png", 
            collision_rect=coll_rect, 
            color=(80, 80, 90)
        )
        self.is_structure = True

class ForestCart(Prop):
    """
    Metsäkärryt (forest_cart_1).
    """
    def __init__(self, x, y):
        w, h = 110, 70
        coll_rect = pygame.Rect(x + 10, y + 20, 90, 40)
        super().__init__(
            x, y, w, h, 
            img_path="assets/tiles/forest/forest_cart_1.png", 
            collision_rect=coll_rect, 
            color=(100, 80, 50)
        )
        self.is_structure = True

class ForestCrates(Prop):
    """
    Laatikoita (forest_crates_1).
    """
    def __init__(self, x, y):
        w, h = 50, 50
        coll_rect = pygame.Rect(x + 5, y + 15, 40, 30)
        super().__init__(
            x, y, w, h, 
            img_path="assets/tiles/forest/forest_crates_1.png", 
            collision_rect=coll_rect, 
            color=(110, 90, 60)
        )
        self.is_structure = True

class ForestGrass(Prop):
    """
    Keskikokoinen ruoho (grass_medium_1).
    Ei estä liikkumista.
    """
    def __init__(self, x, y):
        w, h = 80, 40 # Levennetty 2x (oli 40)
        super().__init__(
            x, y, w, h, 
            img_path="assets/tiles/forest/grass_medium_1.png", 
            color=(40, 80, 40)
        )
        self.rect = pygame.Rect(x, y, 0, 0) # Ei törmäystä
        self.is_structure = True
        self.has_shadow = False
        
        # Wind sway
        self.sway_timer = random.uniform(0, 100)
        self.base_image = self.image
        self.origin_pos = (x, y)
        self.sound_timer = random.randint(0, 2000) # Satunnainen aloitus

    def update(self, obstacles=None, manager=None, **kwargs):
        # Wind sway animation
        self.sway_timer += 0.03 # Hitaampi
        angle = math.sin(self.sway_timer) * 1.5 # +/- 1.5 degrees (hienovaraisempi)
        self.image = pygame.transform.rotate(self.base_image, angle)
        
        # Pivot at bottom center
        w, h = self.base_image.get_size()
        rw, rh = self.image.get_size()
        ox, oy = self.origin_pos
        self.image_pos = (ox + (w - rw) // 2, oy + (h - rh))

        # Positional Audio: Satunnainen kahina
        if manager and manager.player_character:
            self.sound_timer -= 1
            if self.sound_timer <= 0:
                self.sound_timer = random.randint(1500, 4000) # 25-60 sekuntia (harvakseltaan)
                sound_name = f"grass_moving_loop_{random.randint(1, 4)}"
                sound_system.play_positional(sound_name, self.rect.center, manager.player_character.rect.center, max_dist=500)