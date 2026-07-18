# maps/bog_1/arena.py
"""Suokenttä: rakenteellinen räme, EI satunnaisripottelua (pelitesti 30).

Aiemmin jättikartta (7680x4320) oli lähes tyhjä eikä SUOLLA ollut edes
vettä. Nyt kenttäpakilla + yhtenäisellä vesimallilla:

- Neljä isoa suolampea (lake-vesi) ja niiden väliin jäävät KANNAKSET -
  kulku kanavoituu luonnollisesti, kiertoreitit kiertävät vedet.
- SISÄÄN lounaasta (porttikyltti 'MUCKFORD'), peikon pesä koillisessa:
  luita, savua ja Void-Iron-louhinta - selvä määränpää.
- Saarekkeet ja tiheät puustovyöt esteinä; mutalammikot hidasteina
  polkujen varsilla (type='mud' - AI ymmärtää hidasteeksi).
- Kerättävää: Nightcap Fungus, Scrap Pile, Void Iron, hakattavat puut
  (vanhat crafting-nodet) + kenttäpakin Bogwort/Driftwood-nodet.
- Kalastuslaituri eteläisellä lammella.
- Tulikärpäsiä ja sumua tunnelmaksi.

Mission-logiikka lukee: entrance_point, spawn_zones (aallot nousevat
maastosta - ei satunnaisesti pelaajan niskaan).
"""
import random

import pygame

from settings import *
from assets.tiles.bog_floors import BogFloor
from assets.tiles.bog_objects import BogReed, BogTree, MudPool
from assets.tiles.effect_emitters import FireflySwarm, FogPatch, SmokeEmitter
from assets.tiles.water import FishingJetty, WaterBody
from crafting.swamp.nightcap_fungus import NightcapFungus
from crafting.swamp.scrap_pile import ScrapPile
from crafting.swamp.swamp_tree import SwampTree
from crafting.swamp.void_iron_node import VoidIronNode
from systems.field_kit import FieldResourceNode, GateZone, spread_points

BOG_W, BOG_H = 5200, 3400
BOG_SEED = 77121


class Arena:
    def __init__(self):
        self.width = BOG_W
        self.height = BOG_H
        self.map_name = "Rotmire Bog"
        self.obstacles = []
        self.props = []
        self.floor_props = []
        self.waters = []
        rng = random.Random(BOG_SEED)

        self.floor = BogFloor(self.width, self.height)

        # ---------------- VESI: neljä lampea, väliin kannakset --------
        pool_rects = [
            pygame.Rect(1100, 500, 1150, 800),     # luoteinen
            pygame.Rect(3000, 350, 1000, 750),     # koillinen (pesän etuvesi)
            pygame.Rect(800, 2100, 1250, 850),     # eteläinen (kalastus)
            pygame.Rect(2900, 1900, 1050, 800),    # kaakkoinen
        ]
        for index, rect in enumerate(pool_rects):
            water = WaterBody(rect, seed=BOG_SEED + index,
                              name=f"Rotmire Pool {index + 1}", style="lake")
            self.waters.append(water)
            self.floor_props.append(water)
            self.obstacles.extend(water.make_collision_barriers(()))

        # Kalastuslaituri eteläisen lammen länsirannalle
        jetty = FishingJetty(pool_rects[2].left - 30,
                             pool_rects[2].centery - 32, seed=5)
        self.floor_props.append(jetty)
        self.fishing_spots = [(jetty.rect.right + 46, jetty.rect.centery)]

        # ---------------- KIINTOPISTEET -------------------------------
        self.entrance_point = (350, self.height - 420)
        lair = pygame.Rect(4150, 550, 800, 700)
        self.lair_rect = lair
        gate = GateZone(180, self.height - 360, 170, 110, kind="sign",
                        label="MUCKFORD (RETREAT)", facing="left")
        self.props.append(gate)

        # Aallot nousevat maastosta: lampien takamaat + pesän edusta
        self.spawn_zones = [
            pygame.Rect(400, 300, 600, 700),          # luoteiskulma
            pygame.Rect(2350, 200, 500, 600),         # pohjoiskannas
            pygame.Rect(4100, 1400, 700, 700),        # pesän edusta
            pygame.Rect(2200, 2500, 500, 700),        # eteläkannas
            pygame.Rect(4100, 2500, 700, 700),        # kaakkoiskulma
        ]
        self.spawn_points = [self.entrance_point]

        # Kuljettavina pidettävät kannakset (ei esteripottelua näihin)
        travel_lanes = [
            pygame.Rect(0, self.height - 600, self.width, 380),   # etelätie
            pygame.Rect(2350, 0, 500, self.height),               # keskikannas
            pygame.Rect(0, 1400, self.width, 420),                # keskitie
        ]
        avoid = travel_lanes + [w.rect.inflate(100, 100) for w in self.waters]

        # ---------------- PEIKON PESÄ ---------------------------------
        for x, y in spread_points(rng, lair.inflate(-120, -120), 5,
                                  min_dist=130):
            self.props.append(FieldResourceNode(
                f"bog_lair_bone_{x}", x, y, "Ancient Bone", "bone", (1, 2)))
        self.props.append(SmokeEmitter(lair.centerx, lair.centery,
                                       variant=2))
        for _ in range(2):
            vx, vy = rng.randint(lair.left, lair.right - 60), \
                rng.randint(lair.top, lair.bottom - 60)
            node = VoidIronNode(vx, vy)
            self.props.append(node)
            self.obstacles.append(node)

        # ---------------- PUUSTOVYÖT JA SAAREKKEET --------------------
        area = pygame.Rect(150, 150, self.width - 300, self.height - 300)
        for x, y in spread_points(rng, area, 90, min_dist=160,
                                  avoid=avoid + [lair.inflate(150, 150)]):
            tree = BogTree(x, y)
            self.props.append(tree)
            self.obstacles.append(tree)

        # Kaislikot rantojen tuntumaan
        for water in self.waters:
            ring = water.rect.inflate(220, 220)
            for x, y in spread_points(rng, ring, 8, min_dist=120,
                                      avoid=[water.rect]):
                if 0 < x < self.width and 0 < y < self.height:
                    self.props.append(BogReed(x, y))

        # Mutalammikot polkujen varsille (hidaste, ei este)
        for lane in travel_lanes[:2]:
            for x, y in spread_points(rng, lane, 8, min_dist=350):
                mud = MudPool(x, y)
                self.floor_props.append(mud)
                self.obstacles.append(mud)   # type='mud' -> AI hidastuu

        # ---------------- KERÄTTÄVÄT ----------------------------------
        for x, y in spread_points(rng, area, 12, min_dist=300, avoid=avoid):
            self.props.append(NightcapFungus(x, y))
        for x, y in spread_points(rng, area, 7, min_dist=380, avoid=avoid):
            self.props.append(ScrapPile(x, y))
        for x, y in spread_points(rng, area, 6, min_dist=420, avoid=avoid):
            tree = SwampTree(x, y)
            self.props.append(tree)
            self.obstacles.append(tree)
        node_index = 0
        for resource, style, count in (("Bogwort", "herb", 5),
                                       ("Driftwood", "wood", 4)):
            for x, y in spread_points(rng, area, count, min_dist=340,
                                      avoid=avoid):
                self.props.append(FieldResourceNode(
                    f"bog_{node_index}", x, y, resource, style))
                node_index += 1

        # ---------------- TUNNELMA ------------------------------------
        for water in self.waters[:2]:
            self.props.append(FireflySwarm(water.rect.centerx,
                                           water.rect.top - 100, variant=2))
        for water in self.waters[2:]:
            self.props.append(FogPatch(water.rect.centerx,
                                       water.rect.bottom + 80, variant=3))

    def _add_prop(self, prop):
        # Yhteensopivuus: mud lattiaan+obstacles, muut props(+obstacles)
        if getattr(prop, "type", "") == "mud":
            self.floor_props.append(prop)
            self.obstacles.append(prop)
        else:
            self.props.append(prop)
            if getattr(prop, "is_structure", False) and prop.rect.w > 0:
                self.obstacles.append(prop)

    def get_spawn_point(self):
        return self.entrance_point

    def update(self, all_units):
        for p in self.props:
            if getattr(p, "is_effect", False):
                p.update(None, None)
        for water in self.waters:
            water.update(None, None)

    def draw_background(self, screen, offset=(0, 0)):
        self.floor.draw(screen, offset)
        for p in self.floor_props:
            p.draw(screen, offset)

    def draw_foreground(self, screen, offset=(0, 0)):
        pass
