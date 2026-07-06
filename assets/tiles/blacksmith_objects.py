import pygame
import random
from assets.tiles.prop import Prop

class BlacksmithWall(Prop):
    """
    Kiviseinä, josta rakennetaan huone.
    """
    def __init__(self, x, y):
        w, h = 40, 40
        # Hitbox yläreunassa
        coll_rect = pygame.Rect(x, y, w, 25)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/wall_stone.png", # Oletetaan tämä nimi
            collision_rect=coll_rect,
            color=(80, 80, 90) # Tummanharmaa kivi
        )
        self.has_shadow = False

class Anvil(Prop):
    """
    Alasin. Toimii crafting-pisteenä.
    """
    def __init__(self, x, y):
        w, h = 50, 40
        coll_rect = pygame.Rect(x, y + 10, w, 30)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/anvil.png",
            collision_rect=coll_rect,
            color=(40, 40, 50)
        )
        self.is_structure = True
        self.interaction_label = "Craft"
        self.interaction_range = 80
        self.glimmer_timer = random.randint(0, 100)

    def update(self, obstacles=None, manager=None, **kwargs):
        self.glimmer_timer += 1
        if self.glimmer_timer > 150:
            self.glimmer_timer = 0
            if manager and hasattr(manager, "vfx"):
                manager.vfx.create_ore_glimmer(self.rect.centerx, self.rect.top)

class Forge(Prop):
    """
    Ahjo. Tähän lisätään VFX (tuli/savu).
    """
    def __init__(self, x, y):
        w, h = 300, 150
        coll_rect = pygame.Rect(x, y + 40, w, 80)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/forge.png",
            collision_rect=coll_rect,
            color=(60, 30, 30)
        )
        self.is_structure = True

class WeaponRack(Prop):
    """
    Aseteline.
    """
    def __init__(self, x, y):
        w, h = 100, 70
        coll_rect = pygame.Rect(x, y + 20, w, 40)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/weapon_rack.png",
            collision_rect=coll_rect,
            color=(100, 70, 40)
        )
        self.is_structure = True

class EquipmentTable(Prop):
    """
    Varustepöytä.
    """
    def __init__(self, x, y):
        w, h = 180, 90
        coll_rect = pygame.Rect(x, y + 10, w, 50)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/houses/table_equip.png",
            collision_rect=coll_rect,
            color=(110, 80, 40)
        )
        self.is_structure = True
