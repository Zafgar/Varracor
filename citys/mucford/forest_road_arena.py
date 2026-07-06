import pygame
import random
import os
import math
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from assets.tiles.prop import Prop
from assets.tiles.muckford_objects import MuckfordTree, ScrapPileBig
from assets.tiles.forest_objects import ForestBush, ForestGrass, ForestCart, ForestRockBig
from assets.tiles.muckford_floors import MuckfordFloor
from assets.tiles.vfx import MapVFX, RainDrop

class ForestRoadArena:
    def __init__(self):
        # Pitkä ja kapea kartta (polku)
        self.width = 3000
        self.height = 1200
        
        # Käytetään ForestFloor-logiikkaa (tai MuckfordFloor muokattuna)
        # Tässä tapauksessa luodaan lattia suoraan tässä
        self.floor_image = pygame.Surface((self.width, self.height))
        self._generate_floor()
        
        self.vfx = MapVFX()
        
        self.props = []
        self.obstacles = []
        self.floor_props = []
        
        self._build_level()

    def _generate_floor(self):
        # Ladataan muckford_forest.png
        tile_path = "assets/tiles/floors/muckford_forest.png"
        if os.path.exists(tile_path):
            try:
                tile = pygame.image.load(tile_path).convert()
                # Tiilitetään
                for y in range(0, self.height, tile.get_height()):
                    for x in range(0, self.width, tile.get_width()):
                        self.floor_image.blit(tile, (x, y))
                return
            except: pass
            
        # Fallback
        self.floor_image.fill((20, 30, 20))

    def _build_level(self):
        w, h = self.width, self.height
        
        # --- TIE (Road) ---
        road_y = h // 2
        road_h = 200
        
        # Ladataan tiekuva
        road_img = None
        road_path = "assets/tiles/floors/road_brick_horizontal.png"
        if os.path.exists(road_path):
            try:
                road_img = pygame.image.load(road_path).convert_alpha()
                # Skaalataan sopivaksi
                road_img = pygame.transform.scale(road_img, (256, road_h))
            except: pass
            
        # Piirretään tie suoraan lattiaan (tai luodaan propseja)
        # Koska MuckfordFloor on jo luotu, piirretään sen päälle
        if road_img:
            # Piirretään tie suorana
            for x in range(0, w, 250):
                self.floor_image.blit(road_img, (x, road_y - road_h//2))
        else:
            # Fallback tie
            pygame.draw.rect(self.floor_image, (80, 70, 60), (0, road_y - road_h//2, w, road_h))

        # --- METSÄ (Forest) ---
        # Lisätään puita vain tien ulkopuolelle.
        # Huomioidaan puiden korkeus (n. 280px), jotta ne eivät peitä tietä ylhäältä.
        # Tie on välillä [road_y - 100, road_y + 100] (korkeus 200)
        
        # Yläpuoli (Top Forest)
        # Puiden y-koordinaatti on kuvan yläreuna. Puun juuri on n. y + 250.
        # Jotta juuri ei ole tiellä (y > 500), puun y pitää olla < 250.
        for _ in range(60):
            x = random.randint(0, w)
            y = random.randint(0, road_y - 350) 
            self._add_random_forest_prop(x, y)
            
        # Alapuoli (Bottom Forest)
        # Puun y pitää olla tien alapuolella.
        for _ in range(60):
            x = random.randint(0, w)
            y = random.randint(road_y + 150, h - 100)
            self._add_random_forest_prop(x, y)
            
        # --- YKSITYISKOHDAT (Details) ---
        # Kärryt tien varressa (Yläpuolella)
        self._add_prop(ForestCart(800, road_y - 250))
        
        # Romukasa
        self._add_prop(ScrapPileBig(1500, road_y + 120))
        
        # Ruohoa tien reunoille
        for x in range(0, w, 50):
            if random.random() < 0.6:
                self._add_prop(ForestGrass(x, road_y - 110))
            if random.random() < 0.6:
                self._add_prop(ForestGrass(x, road_y + 110))

    def _add_random_forest_prop(self, x, y):
        r = random.random()
        if r < 0.4:
            self._add_prop(MuckfordTree(x, y))
        elif r < 0.6:
            self._add_prop(ForestBush(x, y))
        elif r < 0.7:
            self._add_prop(ForestRockBig(x, y))
        else:
            self._add_prop(ForestGrass(x, y))

    def _add_prop(self, prop):
        self.props.append(prop)
        if prop.rect.w > 0 and prop.rect.h > 0 and getattr(prop, "is_structure", False):
            self.obstacles.append(prop)
        elif isinstance(prop, ForestGrass):
            self.floor_props.append(prop)

    def update(self, manager=None):
        # Luo sadetta (jos manager on annettu, käytä kameraa, muuten satunnainen)
        if manager:
            cx, cy = manager.camera_x, manager.camera_y
            for _ in range(8): # Sateen tiheys
                rx = random.randint(int(cx), int(cx + SCREEN_WIDTH))
                ry = random.randint(int(cy) - 50, int(cy + SCREEN_HEIGHT))
                if hasattr(self.vfx, "add_effect"):
                    self.vfx.add_effect(RainDrop(rx, ry))
                elif hasattr(self.vfx, "particles"):
                    self.vfx.particles.add(RainDrop(rx, ry))

        self.vfx.update(manager)
        for p in self.props:
            if hasattr(p, "update"): p.update(manager=manager)

    def draw_background(self, screen, offset=(0,0)):
        screen.blit(self.floor_image, (-offset[0], -offset[1]))
        
    def draw_foreground(self, screen, offset=(0,0)):
        self.vfx.draw_top(screen, offset)