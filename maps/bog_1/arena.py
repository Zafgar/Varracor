import pygame
import random
from settings import *
from assets.tiles.bog_floors import BogFloor
from assets.tiles.bog_objects import BogTree, BogReed, MudPool
# Importataan uudet resurssit
from crafting.swamp.nightcap_fungus import NightcapFungus
from crafting.swamp.void_iron_node import VoidIronNode
from crafting.swamp.scrap_pile import ScrapPile
from crafting.swamp.swamp_tree import SwampTree

class Arena:
    def __init__(self):
        self.width = int(SCREEN_WIDTH * 4.0) # 2x suurempi (oli 2.0)
        self.height = int(SCREEN_HEIGHT * 4.0)
        self.obstacles = []
        self.props = [] 
        self.floor_props = [] # UUSI: Lattiaobjektit (MudPool)
        self.spawn_points = [(200, 200), (self.width - 200, self.height - 200)]
        
        self.floor = BogFloor(self.width, self.height)
        self._init_layout()
        
    def _init_layout(self):
        w, h = self.width, self.height
        
        # 1. Reunaesteet (Puita)
        for x in range(0, w, 80):
            self._add_prop(BogTree(x, -50))
            self._add_prop(BogTree(x, h - 100))
            
        for y in range(0, h, 120):
            self._add_prop(BogTree(-40, y))
            self._add_prop(BogTree(w - 60, y))
            
        # 2. Mutalammikot (Hidasteet) - Paljon näitä!
        for _ in range(60): # Lisää lammikoita isolle kartalle
            mx = random.randint(100, w - 100)
            my = random.randint(100, h - 100)
            self._add_prop(MudPool(mx, my))
            
        # 3. Puusaarekkeet (Esteet)
        for _ in range(15):
            tx = random.randint(200, w - 200)
            ty = random.randint(200, h - 200)
            self._add_prop(BogTree(tx, ty))
            
        # 4. Kaislikot (Koristeet)
        for _ in range(40):
            rx = random.randint(100, w - 100)
            ry = random.randint(100, h - 100)
            self._add_prop(BogReed(rx, ry))
            
        # 5. RESURSSIT (UUSI)
        # Sieniä (Nightcap Fungus) - Yleinen
        for _ in range(12):
            fx = random.randint(100, w - 100)
            fy = random.randint(100, h - 100)
            self._add_prop(NightcapFungus(fx, fy))
            
        # Romua (Scrap Pile) - Yleinen
        for _ in range(8):
            sx = random.randint(100, w - 100)
            sy = random.randint(100, h - 100)
            self._add_prop(ScrapPile(sx, sy))
            
        # Void-Iron (Harvinainen)
        for _ in range(3):
            vx = random.randint(200, w - 200)
            vy = random.randint(200, h - 200)
            self._add_prop(VoidIronNode(vx, vy))
            
        # Hakattavia puita (Swamp Tree)
        for _ in range(6):
            tx = random.randint(100, w - 100)
            ty = random.randint(100, h - 100)
            self._add_prop(SwampTree(tx, ty))

    def _add_prop(self, prop):
        # Jos tyyppi on 'mud', lisätään se lattiaobjekteihin eikä props-listaan (joka menee Y-sorttaukseen)
        if getattr(prop, "type", "") == "mud":
            self.floor_props.append(prop)
            # KORJAUS: Lisätään itse olio obstacles-listaan, jotta AI tunnistaa tyypin "mud"
            # eikä luule sitä seinäksi (mikä tapahtuisi jos lisättäisiin pelkkä rect).
            self.obstacles.append(prop)
        else:
            self.props.append(prop)
            # Lisää obstacles-listaan vain jos se on oikea este
            if getattr(prop, "is_structure", False) and prop.rect.w > 0:
                self.obstacles.append(prop) # Käytetään oliota tässäkin johdonmukaisuuden vuoksi

    def update(self, all_units):
        pass

    def draw_background(self, screen, offset=(0, 0)):
        self.floor.draw(screen, offset)
        # Piirretään mutalammikot lattian päälle, mutta hahmojen alle
        for p in self.floor_props:
            p.draw(screen, offset)

    def draw_foreground(self, screen, offset=(0, 0)):
        pass
