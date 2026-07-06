import pygame
import random
import math
from assets.tiles.prop import Prop

class InnDrinksTable(Prop):
    """
    Pieni taso (253x191) jossa ruokaa/juomaa ja tynnyri.
    """
    def __init__(self, x, y):
        w, h = 100, 75
        # Törmäyslaatikko alaosassa
        coll_rect = pygame.Rect(x + 10, y + h - 30, w - 20, 25)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/inn_object_drinks.png",
            collision_rect=coll_rect,
            color=(100, 80, 60) # Ruskea fallback
        )
        self.is_structure = True

class FoodBucket(Prop):
    """
    Ämpäri (130x126) jossa pulloja ja ruokaa.
    """
    def __init__(self, x, y):
        w, h = 40, 40
        coll_rect = pygame.Rect(x + 5, y + h - 15, w - 10, 10)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/object_bucket_1.png",
            collision_rect=coll_rect,
            color=(80, 70, 50)
        )
        self.is_structure = True # Voi olla koristeena

class GroundFoodPile(Prop):
    """
    Kasa laatikoita ja säkkejä (317x252).
    """
    def __init__(self, x, y):
        w, h = 110, 90
        coll_rect = pygame.Rect(x + 10, y + h - 40, w - 20, 35)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/object_ground_foods.png",
            collision_rect=coll_rect,
            color=(90, 80, 60)
        )
        self.is_structure = True

class BarDrinksTable(Prop):
    """
    Iso juomapöytä (511x211), sopii tiskin taakse.
    """
    def __init__(self, x, y):
        w, h = 220, 90
        # Hitbox alhaalla (hyllymäinen). Marda (y=100 -> bottom=148) piirtyy yhä eteen (Table bottom ~120).
        coll_rect = pygame.Rect(x + 10, y + h - 25, w - 20, 20)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/table_drinks_1.png",
            collision_rect=coll_rect,
            color=(70, 50, 30)
        )
        self.is_structure = True

class BathTub(Prop):
    """
    Kylpyamme (351x190). Tuottaa höyryä.
    """
    def __init__(self, x, y):
        w, h = 140, 80
        coll_rect = pygame.Rect(x + 10, y + h - 30, w - 20, 25)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/bath_tub.png",
            collision_rect=coll_rect,
            color=(200, 200, 220) # Vaalea amme
        )
        self.is_structure = True
        self.steam_timer = 0

    def update(self, obstacles=None, manager=None, **kwargs):
        # Höyryefekti
        if manager:
            self.steam_timer += 1
            if self.steam_timer > 10: # Joka 10. frame (n. 6 kertaa sekunnissa)
                self.steam_timer = 0
                if random.random() < 0.4: # 40% mahdollisuus
                    # Höyryä nousee ammeen keskeltä/pinnalta
                    # Ammeen "vesi" on noin puolivälissä kuvaa pystysuunnassa
                    sx = self.rect.x + random.randint(60, self.rect.width - 60)
                    sy = self.rect.y + random.randint(40, 80)
                    manager.vfx.create_steam(sx, sy)

class BookshelfHorizontal(Prop):
    """
    Iso kirjahylly (alkup. 1246x1161). Skaalataan sopivaksi.
    """
    def __init__(self, x, y):
        w, h = 120, 110
        coll_rect = pygame.Rect(x + 10, y + h - 30, w - 20, 25)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/hylly_kirja_horizontal_1.png",
            collision_rect=coll_rect,
            color=(100, 60, 40)
        )
        self.is_structure = True

class WardrobeCloth(Prop):
    """
    Vaatekaappi (alkup. 257x280).
    """
    def __init__(self, x, y):
        w, h = 100, 110 # Suurennettu (oli 60x70)
        coll_rect = pygame.Rect(x + 5, y + h - 30, w - 10, 25)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/closet_cloth_1.png",
            collision_rect=coll_rect,
            color=(90, 70, 50)
        )
        self.is_structure = True

class BarrelGroup(Prop):
    """
    Tynnyreitä ja romua (alkup. 311x187).
    """
    def __init__(self, x, y):
        w, h = 90, 60
        coll_rect = pygame.Rect(x + 5, y + h - 25, w - 10, 20)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/object_barrels_1.png",
            collision_rect=coll_rect,
            color=(100, 80, 60)
        )
        self.is_structure = True

class WorkTable(Prop):
    """
    Työpöytä (alkup. 307x201).
    """
    def __init__(self, x, y):
        w, h = 90, 60
        coll_rect = pygame.Rect(x + 5, y + h - 30, w - 10, 25)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/table_working_horizontal.png",
            collision_rect=coll_rect,
            color=(110, 90, 60)
        )
        self.is_structure = True

class CabinetHorizontal(Prop):
    """
    Kaappi (alkup. 256x287).
    """
    def __init__(self, x, y):
        w, h = 100, 110 # Suurennettu (oli 60x70)
        coll_rect = pygame.Rect(x + 5, y + h - 30, w - 10, 25)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/kaappi_horizontal_2.png",
            collision_rect=coll_rect,
            color=(100, 70, 50)
        )
        self.is_structure = True

class GamblersTable(Prop):
    """
    Iso uhkapelipöytä (alkup. gamblers_table_1.png).
    """
    def __init__(self, x, y):
        w, h = 180, 140
        coll_rect = pygame.Rect(x + 10, y + 40, w - 20, h - 40)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/gamblers_table_1.png",
            collision_rect=coll_rect,
            color=(40, 100, 40)
        )
        self.is_structure = True
        self.interaction_label = "Play (E)"
        self.interaction_range = 100

class MagicCrystal(Prop):
    """
    Hohtava kristalli salahuoneeseen. (Pixel Art Style)
    """
    def __init__(self, x, y):
        w, h = 40, 60
        coll_rect = pygame.Rect(x + 10, y + 40, 20, 20)
        super().__init__(x, y, w, h, color=(0,0,0,0), collision_rect=coll_rect)
        self.is_structure = True
        self.timer = 0
        
    def update(self, obstacles=None, manager=None, **kwargs):
        self.timer += 0.05
        if manager and random.random() < 0.05:
            manager.vfx.create_void_particles(self.rect.centerx, self.rect.centery - 20)

    def draw_on_screen(self, screen, offset):
        pulse = (math.sin(self.timer) + 1) * 0.5
        cx = self.rect.centerx - offset[0]
        cy = self.rect.centery - 20 - offset[1]
        
        # Glow
        radius = 20 + pulse * 10
        s = pygame.Surface((int(radius*2), int(radius*2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (100, 0, 200, 50), (int(radius), int(radius)), int(radius))
        screen.blit(s, (cx - radius, cy - radius))
        
        # Crystal shape
        pts = [(cx, cy - 30), (cx + 15, cy), (cx, cy + 30), (cx - 15, cy)]
        col = (150 + int(pulse*50), 50, 200 + int(pulse*55))
        pygame.draw.polygon(screen, col, pts)
        pygame.draw.polygon(screen, (255, 255, 255), pts, 2)

class StagePlatform(Prop):
    """Koroke esiintyjille. (Pixel Art Style)"""
    def __init__(self, x, y, w=200, h=120):
        super().__init__(x, y, w, h, color=(0,0,0,0))
        self.rect = pygame.Rect(x, y, w, h)
        self.is_structure = False
        self.image = pygame.Surface((w, h))
        self.image.fill((80, 50, 30))
        for i in range(0, w, 20):
            pygame.draw.line(self.image, (60, 40, 20), (i, 0), (i, h), 2)
        pygame.draw.rect(self.image, (100, 70, 40), (0, 0, w, h), 4)
