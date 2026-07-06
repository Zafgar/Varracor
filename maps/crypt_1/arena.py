import pygame
import random
from settings import *
from assets.tiles.prop import Prop
from assets.tiles.crypt_walls import CryptBackWall, CryptSideWall, CryptPillar
from assets.tiles.crypt_floors import CryptFloor
from assets.tiles.crypt_objects import CryptGrass, CryptBigPillar, CryptRock, CryptCoffin, BrokenPillar, CryptTree
from crafting.ores.iron_ore import IronOre

class Arena:
    def __init__(self):
        self.width = int(SCREEN_WIDTH * 2.2)
        self.height = int(SCREEN_HEIGHT * 2.2)
        self.obstacles = []
        self.props = [] # Objects that need Y-sorting (Walls, Pillars)
        self.spawn_points = [(300, 300), (self.width - 300, self.height - 300)]
        
        self.floor = CryptFloor(self.width, self.height)
        self._init_walls()
        self._init_decorations()
        
    def _init_walls(self):
        w, h = self.width, self.height
        
        # --- 1. BACK WALLS (Top) ---
        bw_w = 400 
        for x in range(0, w, bw_w):
            prop = CryptBackWall(x, 0)
            self.props.append(prop)
            self.obstacles.append(prop.rect)

        # --- 2. SIDE WALLS ---
        sw_h = 300 
        sw_w = 80  
        
        for y in range(0, h, sw_h):
            p_left = CryptSideWall(0, y)
            self.props.append(p_left)
            self.obstacles.append(p_left.rect)
            
            p_right = CryptSideWall(w - sw_w, y)
            self.props.append(p_right)
            self.obstacles.append(p_right.rect)
            
        # Bottom boundary
        self.obstacles.append(pygame.Rect(0, h - 50, w, 50))

    def _init_decorations(self):
        w, h = self.width, self.height
        cx, cy = w // 2, h // 2
        
        # --- 3. PILLARS (Symmetriset) ---
        offset_x = 500
        offset_y = 350
        
        for px, py in [
            (cx - offset_x, cy - offset_y),
            (cx + offset_x, cy - offset_y),
            (cx - offset_x, cy + offset_y),
            (cx + offset_x, cy + offset_y)
        ]:
            p = CryptBigPillar(px, py)
            self.props.append(p)
            self.obstacles.append(p.rect)

        # --- 4. RANDOM SCATTER (Paljon enemmän) ---
        # Lisätään runsaasti objekteja (40 kpl)
        for _ in range(40):
            rx = random.randint(200, w - 200)
            ry = random.randint(200, h - 200)
            
            # Vältä aivan keskustaa (spawn point)
            if abs(rx - cx) < 250 and abs(ry - cy) < 150: continue
            
            # Arvotaan objekti (painotetaan kiviä ja ruohoa)
            choice = random.choice([CryptGrass, CryptRock, CryptCoffin, CryptPillar, CryptGrass, CryptRock, BrokenPillar, CryptTree])
            prop = choice(rx, ry)
            self.props.append(prop)
            self.obstacles.append(prop.rect)
            
        # --- 5. ORES (Iron Ore) ---
        for _ in range(6):
            ox = random.randint(200, w - 200)
            oy = random.randint(200, h - 200)
            ore = IronOre(ox, oy)
            self.props.append(ore)
            self.obstacles.append(ore.rect)

    def get_spawn_point(self):
        return random.choice(self.spawn_points)

    def update(self, all_units):
        pass

    def draw_background(self, screen, offset=(0, 0)):
        self.floor.draw(screen, offset)

    def draw_foreground(self, screen, offset=(0, 0)):
        pass