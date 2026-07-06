import pygame
import random
import os
import math
from settings import *

class Arena:
    def __init__(self):
        self.name = "Rat Sewer"
        self.width, self.height = 2400, 1600
        self.tile_size = 128 # Oletetaan 128x128 laatat
        
        self.obstacles = []
        self.spawn_points = [(300, 300), (self.width - 300, self.height - 300)]
        
        # --- ASSETS ---
        self.floor_tiles = []
        self.wall_tiles = {}
        self.object_tiles = []
        self.map_data = [] # 2D grid
        self.visual_walls = [] # Pilarit
        self.visual_objects = [] # Objektit
        
        self.load_assets()
        self.generate_map()

    def load_assets(self):
        # 1. FLOORS
        # Kokeillaan ensin sewer_floors, sitten yleinen floors
        paths_to_check = [
            os.path.join("assets", "tiles", "sewer_floors"),
            os.path.join("assets", "tiles", "floors")
        ]
        
        floor_names = ["dungeon_floor_1.png", "dungeon_floor_2.png"]
        
        for p in paths_to_check:
            for fname in floor_names:
                fpath = os.path.join(p, fname)
                if os.path.exists(fpath):
                    try:
                        img = pygame.image.load(fpath).convert()
                        img = pygame.transform.scale(img, (self.tile_size, self.tile_size))
                        self.floor_tiles.append(img)
                    except: pass
            if self.floor_tiles: break # Jos löydettiin laatat, lopetetaan etsintä

        # Fallback floor
        if not self.floor_tiles:
            s = pygame.Surface((self.tile_size, self.tile_size))
            s.fill((30, 25, 20))
            pygame.draw.rect(s, (40, 35, 30), (0,0,self.tile_size,self.tile_size), 1)
            self.floor_tiles.append(s)

        # 2. WALLS
        # Kokeillaan sewer_walls, sitten walls
        wall_paths = [
            os.path.join("assets", "tiles", "sewer_walls"),
            os.path.join("assets", "tiles", "walls")
        ]
        
        for p in wall_paths:
            top_path = os.path.join(p, "sewer_wall_top.png")
            side_path = os.path.join(p, "sewer_wall_side.png")
            
            if os.path.exists(top_path) and "top" not in self.wall_tiles:
                img = pygame.image.load(top_path).convert_alpha()
                # Skaalataan leveys tile_sizeen, korkeus suhteessa
                scale = self.tile_size / img.get_width()
                new_h = int(img.get_height() * scale)
                self.wall_tiles["top"] = pygame.transform.smoothscale(img, (self.tile_size, new_h))

            if os.path.exists(side_path) and "side" not in self.wall_tiles:
                img = pygame.image.load(side_path).convert_alpha()
                # Sivuseinä voi olla kapeampi tai tile_size
                scale = self.tile_size / img.get_width() # Oletetaan neliömäinen tile-logiikka
                new_h = int(img.get_height() * scale)
                self.wall_tiles["side"] = pygame.transform.smoothscale(img, (self.tile_size, new_h))
        
        # 3. OBJECTS (Sewer Products)
        obj_path = os.path.join("assets", "tiles", "sewer_objects")
        if os.path.exists(obj_path):
            for fname in os.listdir(obj_path):
                if fname.lower().endswith(".png"):
                    try:
                        img = pygame.image.load(os.path.join(obj_path, fname)).convert_alpha()
                        self.object_tiles.append(img)
                    except: pass

    def generate_map(self):
        cols = (self.width // self.tile_size) + 1
        rows = (self.height // self.tile_size) + 1
        
        self.map_data = []
        for r in range(rows):
            row_data = []
            for c in range(cols):
                row_data.append(random.choice(self.floor_tiles))
            self.map_data.append(row_data)
            
        # --- ESTEET JA OBJEKTIT ---
        self.obstacles = []
        self.visual_walls = []
        self.visual_objects = []

        # 1. Reunaesteet (Boundaries)
        thickness = 80
        self.obstacles.append(pygame.Rect(0, -thickness, self.width, thickness + 60)) # Top
        self.obstacles.append(pygame.Rect(0, self.height - 40, self.width, thickness)) # Bottom
        self.obstacles.append(pygame.Rect(-thickness, 0, thickness + 40, self.height)) # Left
        self.obstacles.append(pygame.Rect(self.width - 40, 0, thickness, self.height)) # Right

        # 2. Sisäiset seinät (Pillars) - Käytetään sewer_wall_top grafiikkaa
        w_top = self.wall_tiles.get("top")
        if w_top:
            for _ in range(10): # Luodaan 10 satunnaista pilaria
                c = random.randint(2, cols - 3)
                r = random.randint(2, rows - 3)
                x, y = c * self.tile_size, r * self.tile_size
                
                # Collision box (Seinän "jalat", eli alaosa on este)
                rect = pygame.Rect(x + 20, y + 40, self.tile_size - 40, self.tile_size - 40)
                
                # Tarkistetaan ettei spawnin päällä
                if any(math.hypot(sp[0]-rect.centerx, sp[1]-rect.centery) < 250 for sp in self.spawn_points):
                    continue

                self.obstacles.append(rect)
                vis_y = (y + self.tile_size) - w_top.get_height()
                self.visual_walls.append((w_top, x, vis_y))

        # 3. Objektit (Sewer Objects)
        if self.object_tiles:
            for _ in range(15): # Luodaan 15 satunnaista objektia
                img = random.choice(self.object_tiles)
                x = random.randint(100, self.width - 100)
                y = random.randint(100, self.height - 100)
                w, h = img.get_size()
                
                # Oletetaan että objektit ovat esteitä (esim. tynnyrit)
                rect = pygame.Rect(x + w*0.1, y + h*0.5, w*0.8, h*0.4)
                
                if any(math.hypot(sp[0]-rect.centerx, sp[1]-rect.centery) < 200 for sp in self.spawn_points):
                    continue
                if any(rect.colliderect(o) for o in self.obstacles):
                    continue
                    
                self.obstacles.append(rect)
                self.visual_objects.append((img, x, y))

    def get_spawn_point(self):
        return random.choice(self.spawn_points)

    def update(self, all_units):
        pass

    def draw_background(self, screen, offset=(0, 0)):
        # Lasketaan näkyvä alue optimointia varten
        start_col = max(0, int(offset[0] // self.tile_size))
        end_col = min(len(self.map_data[0]), int((offset[0] + SCREEN_WIDTH) // self.tile_size) + 1)
        start_row = max(0, int(offset[1] // self.tile_size))
        end_row = min(len(self.map_data), int((offset[1] + SCREEN_HEIGHT) // self.tile_size) + 1)

        # 1. Lattia
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                x = c * self.tile_size - offset[0]
                y = r * self.tile_size - offset[1]
                screen.blit(self.map_data[r][c], (x, y))

        # 2. Seinät (Yläreuna ja Sivut)
        # Yläseinä
        w_top = self.wall_tiles.get("top")
        if w_top:
            # Piirretään yläreunaan rivi seiniä
            # Huom: Seinän "jalat" ovat kohdassa y=0, joten kuva piirretään ylemmäs
            wall_h = w_top.get_height()
            for c in range(start_col, end_col):
                x = c * self.tile_size - offset[0]
                y = -wall_h + 40 - offset[1] # +40 jotta seinä on hieman pelialueen päällä
                screen.blit(w_top, (x, y))

        # Sivuseinät
        w_side = self.wall_tiles.get("side")
        if w_side:
            # Vasen reuna
            for r in range(start_row, end_row):
                x = -40 - offset[0]
                y = r * self.tile_size - offset[1] - 40
                screen.blit(w_side, (x, y))
            
            # Oikea reuna
            for r in range(start_row, end_row):
                x = self.width - 40 - offset[0]
                y = r * self.tile_size - offset[1] - 40
                screen.blit(w_side, (x, y))

        # 3. Sisäiset seinät (Pillars)
        for img, x, y in self.visual_walls:
            if -200 < x - offset[0] < SCREEN_WIDTH and -200 < y - offset[1] < SCREEN_HEIGHT:
                screen.blit(img, (x - offset[0], y - offset[1]))

        # 4. Objektit
        for img, x, y in self.visual_objects:
            if -200 < x - offset[0] < SCREEN_WIDTH and -200 < y - offset[1] < SCREEN_HEIGHT:
                screen.blit(img, (x - offset[0], y - offset[1]))

    def draw_foreground(self, screen, offset=(0, 0)):
        # 3. Alareunan seinä (Peittää hahmot, luo syvyyttä)
        w_top = self.wall_tiles.get("top")
        if w_top:
            start_col = max(0, int(offset[0] // self.tile_size))
            end_col = min(len(self.map_data[0]), int((offset[0] + SCREEN_WIDTH) // self.tile_size) + 1)
            
            wall_h = w_top.get_height()
            y = self.height - wall_h + 60 - offset[1] # Alareunassa
            
            for c in range(start_col, end_col):
                x = c * self.tile_size - offset[0]
                screen.blit(w_top, (x, y))
