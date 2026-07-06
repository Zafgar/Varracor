import pygame
import random
from assets.tiles.prop import Prop

class BogTree(Prop):
    """
    Käyrä suopuu. Estää liikkumisen.
    """
    def __init__(self, x, y):
        w, h = 220, 340 # Suurempi koko
        # Törmäyslaatikko vain juuressa
        coll_h = 40
        coll_rect = pygame.Rect(x + 85, y + h - 70, w - 170, coll_h)
        
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/bog_objects/bog_tree.png",
            collision_rect=coll_rect,
            color=(40, 50, 40) # Tumma harmaa/vihreä fallback
        )

class BogReed(Prop):
    """
    Kaislikko. Ei estä liikkumista, mutta peittää näkyvyyttä (visuaalisesti).
    """
    def __init__(self, x, y):
        w, h = 70, 100 # Suurempi koko
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/bog_objects/reed.png",
            color=(60, 80, 40)
        )
        self.blocks_projectiles = False
        self.is_structure = True # TÄRKEÄ: True, jotta AI ei hyökkää tähän
        self.rect = pygame.Rect(x, y, 0, 0) # Ei törmäystä
        self.has_shadow = False

class MudPool(Prop):
    """
    Muta-allas. Hidastaa liikkumista (BaseAI tunnistaa tyypin 'mud').
    """
    def __init__(self, x, y):
        w, h = 200, 130 # Suurempi koko
        
        # Pienempi hitbox, jotta slow ei vaikuta kuvan ulkopuolella
        cw, ch = 140, 70
        coll_rect = pygame.Rect(x + (w - cw)//2, y + (h - ch)//2, cw, ch)

        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/bog_objects/mud_pool.png",
            color=(50, 40, 30),
            collision_rect=coll_rect
        )
        self.type = "mud" # TÄRKEÄ: AI tunnistaa tämän
        self.blocks_projectiles = False
        self.is_structure = True # TÄRKEÄ: True, jotta AI ei hyökkää tähän
        self.has_shadow = False
        
        self.bubble_timer = random.randint(0, 100)

    def update(self, obstacles=None, manager=None):
        self.bubble_timer -= 1
        if self.bubble_timer <= 0:
            self.bubble_timer = random.randint(40, 120) # 0.7s - 2s välein
            if manager and hasattr(manager, "vfx"):
                # Satunnainen kohta lammikon keskellä
                off_x = random.randint(-40, 40)
                off_y = random.randint(-20, 20)
                manager.vfx.create_mud_bubble(self.rect.centerx + off_x, self.rect.centery + off_y)
