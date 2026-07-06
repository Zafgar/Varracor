import pygame
import random
from assets.tiles.prop import Prop

class HouseWall(Prop):
    """
    Perusseinä majataloon.
    """
    def __init__(self, x, y):
        # User requested 1/3 size of previous (100x100) -> approx 40x40
        w, h = 40, 40
        
        # Hitbox täyttää koko kuvan alueen
        coll_rect = pygame.Rect(x, y, w, h)
        
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/wall_inn_1.png",
            collision_rect=coll_rect,
            color=(100, 80, 60) # Fallback ruskea
        )
        self.has_shadow = False # Seinillä ei blob-varjoa

class HouseDoor(Prop):
    """
    Ovi, jonka voi avata ja sulkea.
    """
    def __init__(self, x, y, orientation="horizontal"):
        self.orientation = orientation
        self.is_open = False
        
        if orientation == "horizontal":
            w, h = 40, 40
            img_path = "assets/tiles/houses/door_1.png"
            coll_rect = pygame.Rect(x, y, w, h)
        else:
            w, h = 20, 80 # Pystysuora ovi (Täyttää 2x40px aukon)
            img_path = "assets/tiles/houses/door_up_1.png"
            coll_rect = pygame.Rect(x, y, w, h)

        super().__init__(x, y, w, h, img_path=img_path, collision_rect=coll_rect, color=(100, 50, 0))
        self.original_image = self.image
        self.original_rect = self.rect.copy()
        self.interaction_rect = self.rect.inflate(60, 60) # Alue josta voi avata
        self.name = "Door"
        self.has_shadow = False

    def toggle(self):
        self.is_open = not self.is_open
        if self.is_open:
            self.image = None # Piilota kuva
            self.rect = pygame.Rect(self.image_pos[0], self.image_pos[1], 0, 0) # Poista törmäys
        else:
            self.image = self.original_image
            self.rect = self.original_rect.copy()

class InnFireplace(Prop):
    """
    Tulisija, joka luo tunnelmaa.
    """
    def __init__(self, x, y):
        # Pienennetty (oli 260x140) -> 180x100
        w, h = 180, 100
        # Hitbox yläosassa (seinää vasten), alaosa vapaana overlapille
        coll_rect = pygame.Rect(x, y, w, 60)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/fireplace_inn_1.png",
            collision_rect=coll_rect,
            color=(80, 40, 30)
        )
        
    def update(self, obstacles=None, manager=None, **kwargs):
        if manager and hasattr(manager, "vfx"):
            # Savua
            if random.random() < 0.15:
                manager.vfx.create_smoke(self.rect.centerx + random.randint(-15, 15), self.rect.top + 20)
            
            # Tulta/Kipinöitä
            if random.random() < 0.25:
                manager.vfx.create_fireplace_ember(self.rect.centerx + random.randint(-20, 20), self.rect.bottom - 20)

class InnCounter(Prop):
    """
    Majatalon tiski.
    """
    def __init__(self, x, y):
        # Scaled down slightly (was 400x142)
        w, h = 300, 100
        
        # Hitbox yläosassa (Top-heavy)
        # Jätetään alaosa vapaaksi overlapille
        coll_h = 50
        coll_rect = pygame.Rect(x, y + 10, w, coll_h)
        
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/counter_inn_1.png",
            collision_rect=coll_rect,
            color=(120, 90, 50)
        )

class InnTable(Prop):
    """
    Pöytä.
    """
    def __init__(self, x, y):
        w, h = 100, 100
        # Hitbox alhaalla
        coll_rect = pygame.Rect(x + 10, y + 20, w - 20, h - 25)
        
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/table_inn_1.png",
            collision_rect=coll_rect,
            color=(110, 80, 40)
        )

class InnTable2(Prop):
    """
    Toinen pöytävariaatio.
    """
    def __init__(self, x, y):
        w, h = 120, 120
        coll_rect = pygame.Rect(x + 10, y + 25, w - 20, h - 30)
        
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/table_inn_2.png",
            collision_rect=coll_rect,
            color=(110, 80, 40)
        )

class InnBed(Prop):
    """
    Yhden hengen sänky.
    """
    def __init__(self, x, y):
        # Scaled up 30% (was 48x80) -> approx 62x104
        w, h = 62, 104
        
        # Hitbox yläpäädyssä
        coll_rect = pygame.Rect(x, y, w, 35)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/bed_1.png",
            color=(100, 50, 50)
        )
        self.occupied_by = None # Kuka nukkuu tässä

class InnDoubleBed(Prop):
    """
    Parisänky.
    """
    def __init__(self, x, y):
        # Scaled up 30% (was 80x90) -> approx 104x117
        w, h = 104, 117
        
        coll_rect = pygame.Rect(x, y, w, 40)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/bed_double_2.png",
            color=(100, 50, 50)
        )
        self.occupied_by = None # Kuka nukkuu tässä

class BearRug(Prop):
    """
    Karhuntalja lattialla. Ei estä liikkumista.
    """
    def __init__(self, x, y):
        # Scaled down (was 140x100)
        w, h = 110, 80
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/rug_bear_1.png",
            color=(80, 60, 40)
        )
        # Poistetaan törmäys
        self.rect = pygame.Rect(x, y, 0, 0)
        self.is_structure = True # Ei ole este, mutta ei myöskään hyökkäyksen kohde
        self.has_shadow = False # Matto on litteä

class InnConsumable(Prop):
    """Perusluokka kannettaville esineille (ruoka/juoma)."""
    def __init__(self, x, y, img_path, color):
        super().__init__(x, y, 24, 24, img_path=img_path, color=color)
        self.rect = pygame.Rect(x, y, 0, 0) # Ei törmäystä
        self.is_structure = True
        self.has_shadow = False
        self.z_offset = 0 # Korkeus maasta

    def update_position(self, owner):
        """Päivittää sijainnin omistajan mukaan."""
        # Hieman sivulle ja ylös (käden kohdalle)
        offset_x = 10 if owner.facing_right else -10
        self.image_pos = (owner.rect.centerx + offset_x - 12, owner.rect.centery - 10)
        
        # PÄIVITYS: Siirretään rect omistajan jalkojen juureen (tai hieman alemmas),
        # jotta Y-sort (renderables.sort) piirtää esineen hahmon JÄLKEEN (päälle).
        # Hahmon rect.bottom on jalkojen taso.
        self.rect.x = self.image_pos[0]
        self.rect.y = owner.rect.bottom + 1 # +1 varmistaa että piirretään hahmon jälkeen
        self.rect.w = 0
        self.rect.h = 0

class InnFood(InnConsumable):
    def __init__(self, x, y, variant=1):
        paths = {
            1: "assets/tiles/inn_objects/food_stew.png",
            2: "assets/tiles/inn_objects/food_meat.png",
            3: "assets/tiles/inn_objects/food_bread.png"
        }
        colors = {
            1: (100, 50, 20), # Ruskea (Stew)
            2: (150, 60, 60), # Punainen (Meat)
            3: (200, 180, 100) # Kellertävä (Bread)
        }
        path = paths.get(variant, paths[1])
        col = colors.get(variant, colors[1])
        super().__init__(x, y, path, col)
        self.variant = variant

class InnDrink(InnConsumable):
    def __init__(self, x, y, variant=1):
        paths = {
            1: "assets/tiles/inn_objects/drink_ale.png",
            2: "assets/tiles/inn_objects/drink_wine.png",
            3: "assets/tiles/inn_objects/drink_water.png"
        }
        colors = {
            1: (200, 150, 50), # Keltainen (Ale)
            2: (100, 20, 40),  # Tummanpunainen (Wine)
            3: (100, 200, 255) # Sininen (Water)
        }
        path = paths.get(variant, paths[1])
        col = colors.get(variant, colors[1])
        super().__init__(x, y, path, col)
        self.variant = variant

class SmallRoomTable(Prop):
    """
    Yöpöytä (alkup. 600x700). Skaalataan pieneksi makuuhuoneeseen.
    """
    def __init__(self, x, y):
        w, h = 40, 50
        coll_rect = pygame.Rect(x, y + 15, w, 35)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/small_room_table_1.png",
            collision_rect=coll_rect,
            color=(90, 70, 50)
        )
        self.is_structure = True

class Vase(Prop):
    """
    Koristevaasi (vase_1.png).
    """
    def __init__(self, x, y):
        w, h = 40, 60
        coll_rect = pygame.Rect(x + 10, y + 40, 20, 20)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/vase_1.png",
            collision_rect=coll_rect,
            color=(100, 100, 120)
        )
        self.is_structure = True

class Cauldron(Prop):
    """
    Iso pata (cauldron_1.png).
    Alkup: 388x360. Skaalattu n. 25%.
    """
    def __init__(self, x, y):
        scale = 0.25
        w, h = int(388 * scale), int(360 * scale) # ~97x90
        
        # Hitbox: Alareuna 250, sivuilta 70 (alkuperäisessä)
        # Skaalattuna: Bottom ~63, Side margin ~18
        coll_w = w - int(140 * scale) # 388 - 70 - 70 = 248 -> ~62
        coll_x = int(70 * scale)      # ~18
        coll_bottom = int(250 * scale) # ~63
        coll_h = 30 # Arvioitu korkeus hitboxille
        
        coll_rect = pygame.Rect(x + coll_x, y + coll_bottom - coll_h, coll_w, coll_h)
        
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/cauldron_1.png",
            collision_rect=coll_rect,
            color=(40, 40, 50)
        )
        self.is_structure = True
        self.soup_y = int(95 * scale) # Sopan kohta (höyryä varten)

    def update(self, obstacles=None, manager=None, **kwargs):
        if manager and random.random() < 0.1:
            # Höyryä sopan pinnasta
            sx = self.rect.centerx + random.randint(-10, 10)
            sy = self.image_pos[1] + self.soup_y
            manager.vfx.create_steam(sx, sy)

class CookingTable(Prop):
    """
    Ruokapöytä (cooking_table_1.png).
    Alkup: 1330x820. Skaalattu n. 22%.
    """
    def __init__(self, x, y):
        scale = 0.22
        w, h = int(1330 * scale), int(820 * scale) # ~292x180
        
        # Pöytätaso: Ylä 153, Ala 554 (alkuperäisessä)
        t_top = int(153 * scale)
        t_bot = int(554 * scale)
        
        coll_rect = pygame.Rect(x + 10, y + t_top, w - 20, t_bot - t_top)
        
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/cooking_table_1.png",
            collision_rect=coll_rect,
            color=(110, 90, 60)
        )
        self.is_structure = True
