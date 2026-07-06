import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from assets.tiles.blacksmith_objects import BlacksmithWall, Anvil, Forge, WeaponRack, EquipmentTable
from assets.tiles.house_objects import BearRug
from assets.tiles.house_floors import BlacksmithFloor
from assets.tiles.house_vfx import HouseVFX

class BlacksmithArena:
    def __init__(self):
        # Huoneen koko
        self.width = 1000
        self.height = 800
        
        # Käytetään samaa lattiaa kuin taloissa
        self.floor = BlacksmithFloor(self.width, self.height)
        self.vfx = HouseVFX(self.width, self.height)
        
        self.props = []
        self.obstacles = []
        
        self._build_room()

    def _build_room(self):
        w, h = self.width, self.height
        wall_s = 40
        
        # --- SEINÄT ---
        # Yläseinä
        for x in range(0, w, wall_s):
            self._add_prop(BlacksmithWall(x, 0))
            
        # Alaseinä (Oviaukko keskellä)
        door_x = w // 2
        door_width = 120
        for x in range(0, w, wall_s):
            if not (door_x - door_width//2 <= x < door_x + door_width//2):
                self._add_prop(BlacksmithWall(x, h - wall_s))
                
        # Vasen seinä
        for y in range(wall_s, h - wall_s, wall_s):
            self._add_prop(BlacksmithWall(0, y))
            
        # Oikea seinä
        for y in range(wall_s, h - wall_s, wall_s):
            self._add_prop(BlacksmithWall(w - wall_s, y))

        # --- SISUSTUS ---
        
        # Ahjo (Forge) - Takaseinälle
        forge_w = 300
        forge_x = w // 2 - forge_w // 2 # Keskitetty
        forge_y = 40
        self._add_prop(Forge(forge_x, forge_y))
        
        # Lisätään KAKSI tuli-efektiä kattamaan leveä ahjo
        self.vfx.add_fireplace(forge_x + 80, forge_y + 100, spread=40, speed_y=-2.8)
        self.vfx.add_fireplace(forge_x + 220, forge_y + 100, spread=40, speed_y=-2.8)
        
        # Lisätään tunnelmaa (höyryä/savua)
        self.vfx.add_steam(forge_x + 150, forge_y + 20)
        self.vfx.add_steam(forge_x + 50, forge_y + 50)

        # Alasin (Anvil) - Ahjon eteen
        anvil_w = 50 # Levennetty (oli 32)
        self._add_prop(Anvil(w // 2 - anvil_w // 2, 300))
        
        # Matto (Bear Rug) - Lattialle
        self._add_prop(BearRug(w // 2 - 55, 400))

        # Asetelineet (Weapon Racks) - Vasemmalle seinustalle
        self._add_prop(WeaponRack(50, 200))
        self._add_prop(WeaponRack(50, 320))
        
        # Varustepöydät (Equipment Tables) - Oikealle seinustalle
        table_w = 180
        self._add_prop(EquipmentTable(w - table_w - 50, 200))
        self._add_prop(EquipmentTable(w - table_w - 50, 400))

    def _add_prop(self, prop):
        self.props.append(prop)
        if getattr(prop, "is_structure", False) and prop.rect.w > 0 and prop.rect.h > 0:
            self.obstacles.append(prop)

    def update(self, manager=None):
        self.vfx.update()
        for p in self.props:
            if hasattr(p, "update"):
                p.update(manager=manager)

    def draw_background(self, screen, offset=(0,0)):
        self.floor.draw(screen, offset)
        
    def draw_foreground(self, screen, offset=(0,0)):
        self.vfx.draw(screen, offset)