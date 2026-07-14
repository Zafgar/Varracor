import pygame
import random
import os
from assets.tiles.prop import Prop
from assets.tiles.farm_vfx import FarmVFX
from sound_manager import sound_system

class GrassPatch(Prop):
    """
    Ruoho, jota lehmät syövät.
    """
    def __init__(self, x, y):
        super().__init__(x, y, 32, 32, color=(50, 150, 50))
        self.is_eaten = False
        self.regrow_timer = 0
        self.regrow_time = 3600 # 60 sekuntia
        
        # Ladataan kuvat
        self.img_full = self._load_img("assets/tiles/farm/grass_full.png")
        self.img_eaten = self._load_img("assets/tiles/farm/grass_eaten.png")
        
        self._update_image()
        
        # Ei estä liikkumista
        self.rect = pygame.Rect(x, y, 32, 32)
        self.is_structure = True
        self.has_shadow = False
        self.sound_timer = random.randint(0, 2000)

    def _load_img(self, path):
        if os.path.exists(path):
            try:
                return pygame.transform.smoothscale(pygame.image.load(path).convert_alpha(), (32, 32))
            except Exception: pass
        return None

    def _update_image(self):
        if self.is_eaten:
            if self.img_eaten:
                self.image = self.img_eaten
            else:
                self.image.fill((100, 100, 50)) # Fallback ruskea
        else:
            if self.img_full:
                self.image = self.img_full
            else:
                self.image.fill((50, 180, 50)) # Fallback vihreä

    def eat(self):
        if not self.is_eaten:
            self.is_eaten = True
            self.regrow_timer = self.regrow_time
            self._update_image()
            return True
        return False

    def update(self, obstacles=None, manager=None, *args):
        if self.is_eaten:
            self.regrow_timer -= 1
            if self.regrow_timer <= 0:
                self.is_eaten = False
                self._update_image()
        
        # Positional Audio: Satunnainen kahina (vain jos ei syöty)
        if not self.is_eaten and manager and manager.player_character:
            self.sound_timer -= 1
            if self.sound_timer <= 0:
                self.sound_timer = random.randint(1500, 4000)
                sound_system.play_positional(
                    f"grass_moving_loop_{random.randint(1, 4)}", 
                    self.rect.center, 
                    manager.player_character.rect.center, 
                    max_dist=500
                )

class Manure(Prop):
    """
    Lehmän kakka. Pelaaja voi kerätä.
    """
    def __init__(self, x, y):
        super().__init__(x, y, 24, 24, img_path="assets/tiles/farm/manure.png", color=(80, 60, 20))
        self.loot_item = "Manure" # Tunniste keräykselle
        self.rect = pygame.Rect(x, y, 24, 24)
        self.is_structure = True
        self.has_shadow = False

    def update(self, obstacles=None, manager=None):
        if manager:
            FarmVFX.process_object(self, manager)

class ManurePile(Prop):
    """
    Kasa, johon lanta viedään.
    """
    def __init__(self, x, y):
        # Suurennettu koko (alkuperäinen 80x60 -> nyt 260x140)
        w, h = 260, 140
        # Hitbox vain yläosassa (takaseinä), jotta "karsinaan" voi kävellä sisään
        coll_rect = pygame.Rect(x, y, w, 40)
        super().__init__(x, y, w, h, img_path="assets/tiles/farm/manure_pile.png", color=(60, 50, 30), collision_rect=coll_rect)
        self.is_structure = True

    def update(self, obstacles=None, manager=None):
        if manager:
            FarmVFX.process_object(self, manager)

class Barn(Prop):
    """
    Iso lato.
    """
    def __init__(self, x, y):
        w, h = 300, 240
        # Hitbox alareunassa
        coll_rect = pygame.Rect(x + 20, y + h - 80, w - 40, 60) # Nostettu 20px (oli h-60)
        super().__init__(x, y, w, h, img_path="assets/tiles/farm/barn.png", color=(100, 50, 50), collision_rect=coll_rect)
        self.is_structure = True

class FarmField(Prop):
    """
    Viljelyspalsta (uusi).
    """
    def __init__(self, x, y):
        w, h = 300, 200
        super().__init__(x, y, w, h, img_path="assets/tiles/farm/field.png", color=(80, 70, 40))
        self.rect = pygame.Rect(x, y, 0, 0) # Ei estä liikkumista
        self.is_structure = False
        self.has_shadow = False

class PastureFloor(Prop):
    """
    Laidunalueen tausta.
    """
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, img_path="assets/tiles/farm/pasture.png", color=(40, 100, 40))
        self.rect = pygame.Rect(x, y, 0, 0) # Lattia
        self.is_structure = False
        self.has_shadow = False
        self.is_flat = True
        
        # Jos kuva löytyy, tiilitetään se koko alueelle
        path = "assets/tiles/farm/pasture.png"
        if os.path.exists(path):
             self._tile_image(w, h, path)

    def _tile_image(self, w, h, path):
        try:
            tile = pygame.image.load(path).convert()
            self.image = pygame.Surface((w, h))
            tw, th = tile.get_size()
            for r in range(0, h, th):
                for c in range(0, w, tw):
                    self.image.blit(tile, (c, r))
        except Exception: pass

class FarmFenceHorizontal(Prop):
    def __init__(self, x, y):
        # Alkuperäinen 1280x230 -> 1/5 koko = 256x46
        w, h = 256, 46
        # Hitbox skaalattu: y+100 -> y+20, korkeus 30 -> 6
        coll_rect = pygame.Rect(x, y + 20, w, 6)
        super().__init__(x, y, w, h, img_path="assets/tiles/farm/fence_horizontal.png", collision_rect=coll_rect)
        self.has_shadow = False

class FarmFenceVertical(Prop):
    def __init__(self, x, y):
        # Alkuperäinen 260x1330 -> 1/5 koko = 52x266
        w, h = 52, 266
        # Hitbox skaalattu: x+110 -> x+22, leveys 40 -> 8
        coll_rect = pygame.Rect(x + 22, y, 8, h)
        super().__init__(x, y, w, h, img_path="assets/tiles/farm/fence_vertical.png", collision_rect=coll_rect)
        self.has_shadow = False

class FarmStorage(Prop):
    """
    Varastorakennus / Farm Shop.
    """
    def __init__(self, x, y):
        w, h = 400, 220 # Pienennetty (oli 540x290)
        # Hitbox alareunassa
        coll_rect = pygame.Rect(x + 30, y + h - 90, w - 60, 50)
        super().__init__(x, y, w, h, img_path="assets/tiles/farm/storage.png", color=(100, 80, 60), collision_rect=coll_rect)
        self.is_structure = True
        self.name = "Farm Storage"

class Apple(Prop):
    """
    Maahan pudonnut omena.
    """
    def __init__(self, x, y):
        super().__init__(x, y, 16, 16, color=(200, 50, 50))
        self.loot_item = "Apple"
        self.rect = pygame.Rect(x, y, 16, 16)
        self.is_structure = True
        self.interaction_range = 50
        self.interaction_label = "Pickup"
        self.has_shadow = False
        # Piirrä punainen ympyrä jos kuvaa ei ole
        pygame.draw.circle(self.image, (220, 40, 40), (8, 8), 6)

class Egg(Prop):
    """
    Maahan munittu muna.
    """
    def __init__(self, x, y):
        super().__init__(x, y, 12, 14, color=(240, 230, 200))
        self.loot_item = "Egg"
        self.rect = pygame.Rect(x, y, 12, 14)
        self.is_structure = True
        self.interaction_range = 50
        self.interaction_label = "Pickup"
        self.has_shadow = False
        pygame.draw.ellipse(self.image, (250, 245, 220), (0, 0, 12, 14))
