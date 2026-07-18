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
        self.props = []
        # Putkien suut pohjoisseinällä: näistä valuu limaa ja niistä
        # vyöryy rottia (Rat Kingin summon + monsterijahdin spawnit)
        self.pipe_points = [(520, 300), (self.width // 2, 260),
                            (self.width - 520, 300)]
        self.spawn_points = list(self.pipe_points)
        # Lavastuspisteet (pelitesti 22): pelaajien sisäänkäynti lännessä,
        # Rat Kingin roskavaltaistuin idässä
        self.entry_pos = (320, self.height // 2)
        self.entrance_point = self.entry_pos
        self.throne_pos = (self.width - 460, self.height // 2)

        # SELVÄ sisäänkäynti: viemäriritilä lännessä (pelitesti 30) +
        # kerättävää viemärin nurkissa (E kerää, sama järjestelmä)
        from systems.field_kit import FieldResourceNode, GateZone
        self.props.append(GateZone(140, self.height // 2 - 70, 150, 100,
                                   kind="grate", label="MUCKFORD SEWERS",
                                   facing="left"))
        for node_id, x, y, resource, style in (
                ("sewer_scrap_1", 700, 480, "Rusty Scrap", "scrap"),
                ("sewer_scrap_2", 1650, 1050, "Rusty Scrap", "scrap"),
                ("sewer_bone_1", 1150, 1150, "Bone Shard", "bone"),
                ("sewer_moss_1", 1900, 500, "Crypt Moss", "mushroom")):
            self.props.append(FieldResourceNode(node_id, x, y, resource,
                                                style, (1, 2)))

        # --- TUNNELMA (sovitettu käyttäjän bosses/-paketin lairista) ---
        # Viemärivesi virtaa etelälaidalla; kuplia, ajopuita ja putkista
        # tippuvaa limaa
        self.water_top = self.height - 190
        self.bubbles = [[random.randint(40, self.width - 40),
                         random.randint(self.water_top + 20, self.height - 50),
                         random.randint(2, 5), random.uniform(0.5, 1.5)]
                        for _ in range(24)]
        self.debris = [{'x': random.randint(0, self.width),
                        'w': random.randint(20, 60),
                        'offset': random.uniform(0, 6.28)}
                       for _ in range(10)]
        self.drips = []
        self._tick = 0
        
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
                    except Exception: pass
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
                    except Exception: pass

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

    def update(self, all_units=None):
        """Elävöittää viemärin: kuplat nousevat, lima tippuu putkista."""
        self._tick += 1
        for b in self.bubbles:
            b[1] -= b[3]
            if b[1] < self.water_top + 10:
                b[1] = self.height - 50
                b[0] = random.randint(40, self.width - 40)
        if random.random() < 0.08:
            px, py = random.choice(self.pipe_points)
            self.drips.append([px + random.randint(-30, 30), py + 30,
                               random.uniform(4, 7)])
        for d in self.drips:
            d[1] += d[2]
        self.drips = [d for d in self.drips if d[1] < self.height - 60]

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

        # --- 5. VIEMÄRITUNNELMA (pelitesti 22) ---
        self._draw_pipes(screen, offset)
        self._draw_throne(screen, offset)
        self._draw_water(screen, offset)
        # Putkista tippuva lima
        for dx, dy, _spd in self.drips:
            sx, sy = int(dx - offset[0]), int(dy - offset[1])
            if -20 < sx < SCREEN_WIDTH + 20 and -20 < sy < SCREEN_HEIGHT + 20:
                pygame.draw.line(screen, (50, 200, 50), (sx, sy - 10),
                                 (sx, sy), 3)
                pygame.draw.circle(screen, (100, 255, 100), (sx, sy), 4)

    def _draw_pipes(self, screen, offset):
        """Putkien suut pohjoisseinällä: keskellä ritilä, sivuilla aukot."""
        for i, (px, py) in enumerate(self.pipe_points):
            sx, sy = px - offset[0], py - offset[1]
            if not (-200 < sx < SCREEN_WIDTH + 200 and
                    -200 < sy < SCREEN_HEIGHT + 200):
                continue
            if i == 1:
                # Iso ritiläluukku
                pygame.draw.rect(screen, (5, 5, 5), (sx - 60, sy - 40, 120, 80))
                for k in range(0, 120, 20):
                    pygame.draw.line(screen, (50, 40, 40),
                                     (sx - 60 + k, sy - 40),
                                     (sx - 60 + k, sy + 40), 4)
                pygame.draw.rect(screen, (60, 50, 50),
                                 (sx - 60, sy - 40, 120, 80), 4)
            else:
                pygame.draw.circle(screen, (50, 50, 55), (sx, sy), 54)
                pygame.draw.circle(screen, (0, 0, 0), (sx, sy), 44)
                pygame.draw.arc(screen, (20, 20, 20),
                                (sx - 44, sy - 44, 88, 88), 0, 3.14, 4)

    def _draw_throne(self, screen, offset):
        """Rat Kingin roskavaltaistuin: romukasa + luita."""
        tx, ty = self.throne_pos
        sx, sy = tx - offset[0], ty - offset[1]
        if not (-300 < sx < SCREEN_WIDTH + 300 and
                -300 < sy < SCREEN_HEIGHT + 300):
            return
        # Romukumpu
        pygame.draw.ellipse(screen, (45, 38, 30), (sx - 130, sy - 20, 260, 110))
        pygame.draw.ellipse(screen, (60, 50, 38), (sx - 110, sy - 40, 220, 100))
        # "Istuin" laatikoista
        pygame.draw.rect(screen, (70, 55, 35), (sx - 45, sy - 90, 90, 70))
        pygame.draw.rect(screen, (50, 40, 25), (sx - 45, sy - 90, 90, 70), 3)
        pygame.draw.rect(screen, (80, 64, 40), (sx - 62, sy - 55, 124, 40))
        # Luita ja kalloja koristeeksi
        for bx, by in ((-90, 30), (75, 45), (-40, 60), (100, 10)):
            pygame.draw.circle(screen, (200, 195, 180),
                               (sx + bx, sy + by), 7)
            pygame.draw.line(screen, (185, 180, 165),
                             (sx + bx - 10, sy + by + 6),
                             (sx + bx + 12, sy + by + 2), 4)

    def _draw_water(self, screen, offset):
        """Etelälaidan viemärivirta: aaltoileva pinta, ajopuut ja kuplat."""
        top = self.water_top - offset[1]
        if top > SCREEN_HEIGHT:
            return
        time = pygame.time.get_ticks() * 0.002
        x0 = max(0, int(offset[0] // 20) * 20 - 20)
        points = [(0, SCREEN_HEIGHT), (0, top)]
        for wx in range(x0, x0 + SCREEN_WIDTH + 60, 20):
            y_off = math.sin(time + wx * 0.015) * 6 + \
                math.sin(time * 2 + wx * 0.03) * 3
            points.append((wx - offset[0], top + y_off))
        points.append((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.draw.polygon(screen, (20, 60, 20), points)
        pygame.draw.lines(screen, (80, 160, 80), False, points[1:-1], 3)
        for deb in self.debris:
            dy = self.water_top + 24 + math.sin(time + deb['offset']) * 8
            pygame.draw.rect(screen, (50, 30, 10),
                             (deb['x'] - offset[0], dy - offset[1],
                              deb['w'], 6))
        for bx, by, size, _spd in self.bubbles:
            sx, sy = int(bx - offset[0]), int(by - offset[1])
            if 0 <= sx <= SCREEN_WIDTH and 0 <= sy <= SCREEN_HEIGHT:
                pygame.draw.circle(screen, (100, 220, 100), (sx, sy), size)

    def draw_foreground(self, screen, offset=(0, 0)):
        # Viemärin hämäryys: tummat reunat ylä- ja alalaidassa
        if not hasattr(self, "_dark_overlay"):
            ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT),
                                pygame.SRCALPHA)
            pygame.draw.rect(ov, (0, 0, 0, 140), (0, 0, SCREEN_WIDTH, 110))
            pygame.draw.rect(ov, (0, 0, 0, 110),
                             (0, SCREEN_HEIGHT - 70, SCREEN_WIDTH, 70))
            self._dark_overlay = ov
        screen.blit(self._dark_overlay, (0, 0))

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
