import pygame
from assets.tiles.house_floors import HouseFloor
from assets.tiles.prop import Prop

class TestArena:
    def __init__(self):
        self.width = 2000
        self.height = 1500
        self.floor = HouseFloor(self.width, self.height)
        self.props = []
        self.floor_props = []
        self.obstacles = []
        self.enemies = [] # Lista vihollisille (jos spawnataan editorilla)
        self.vfx = None # Asetetaan menussa

    def update(self, manager=None):
        # Päivitä propit (esim. animaatiot)
        for p in self.props:
            if hasattr(p, "update"):
                p.update(manager=manager)
        
        # Päivitä MapVFX (sade, sumu yms) jos asetettu
        if self.vfx:
            if hasattr(self.vfx, "update"):
                try: self.vfx.update(manager)
                except: self.vfx.update()

    def draw_background(self, screen, offset):
        self.floor.draw(screen, offset)
        # Piirrä lattiaobjektit (Ground tiles)
        for p in self.floor_props:
            p.draw(screen, offset)

    def draw_foreground(self, screen, offset):
        if self.vfx:
            if hasattr(self.vfx, "draw_top"):
                self.vfx.draw_top(screen, offset)
            elif hasattr(self.vfx, "draw"):
                self.vfx.draw(screen, offset)