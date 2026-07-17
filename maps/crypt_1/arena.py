# maps/crypt_1/arena.py
"""Krypta: OIKEA luolasto käytävineen ja kammioineen (pelitesti 30).

Aiemmin tämä oli yksi iso avoin sali, johon aallot spawnasivat joka
suunnalta. Nyt pohja on rakennettu kenttäpakilla (systems/field_kit):

- SISÄÄN etelästä (holvikaariportti "MUCKFORD"), sisääntulohalli.
- Keskussanktuaari, jota puolustetaan - EI iso neliö vaan kammio,
  johon johtaa NELJÄ kapeaa käytävää = puolustettavat kuristuskohdat.
- Ulkokammiot (länsi/itä/pohjoinen + kaksi galleriaa), joiden
  Vortex-portaaleista aallot vyöryvät käytäviä pitkin.
- Perimmäinen holvi (vault) pohjoisessa: kristalli- ja luulöytöjä
  rohkeille, jotka työntyvät ulos aaltojen välissä.
- Kerättävät resurssit kammioissa (Grave Dust, Crypt Moss, Ancient
  Bone, rautamalmi) + savu/sumu/kipinäemitterit tunnelmaan.

Mission-logiikka lukee: entrance_point (pelaajan aloitus),
defend_point (sanktuaarin keskus), portal_points (aaltoportaalit).
"""
import random

import pygame

from settings import *
from assets.tiles.crypt_floors import CryptFloor
from assets.tiles.crypt_walls import CryptPillar
from assets.tiles.crypt_objects import (
    BrokenPillar, CryptBigPillar, CryptCoffin, CryptGrass, CryptRock,
)
from assets.tiles.effect_emitters import EmberEmitter, FogPatch
from crafting.ores.iron_ore import IronOre
from systems.field_kit import (
    FieldResourceNode, GateZone, build_dungeon, spread_points,
)

CRYPT_W, CRYPT_H = 4800, 3200
CRYPT_SEED = 40913


class Arena:
    def __init__(self):
        self.width = CRYPT_W
        self.height = CRYPT_H
        self.map_name = "Crypt of the Grave-Tide"
        self.obstacles = []
        self.props = []
        self.floor_props = []
        rng = random.Random(CRYPT_SEED)

        # ---------------- POHJARATKAISU: kammiot + käytävät ----------
        entry_hall = pygame.Rect(2050, 2660, 700, 480)
        sanctum = pygame.Rect(1800, 1300, 1200, 900)
        west_room = pygame.Rect(400, 1350, 800, 700)
        east_room = pygame.Rect(3600, 1350, 800, 700)
        north_room = pygame.Rect(2000, 300, 800, 600)
        nw_gallery = pygame.Rect(700, 300, 900, 600)
        ne_gallery = pygame.Rect(3200, 300, 900, 600)
        vault = pygame.Rect(2150, 40, 500, 220)

        corridors = [
            pygame.Rect(2320, 2200, 160, 480),   # sisääntulo -> sanktuaari
            pygame.Rect(1200, 1620, 600, 160),   # länsi -> sanktuaari
            pygame.Rect(3000, 1620, 600, 160),   # itä -> sanktuaari
            pygame.Rect(2320, 900, 160, 400),    # pohjoinen -> sanktuaari
            pygame.Rect(1000, 900, 160, 450),    # NW-galleria -> länsi
            pygame.Rect(3640, 900, 160, 450),    # NE-galleria -> itä
            pygame.Rect(1600, 520, 400, 160),    # NW-galleria -> pohjoinen
            pygame.Rect(2800, 520, 400, 160),    # pohjoinen -> NE-galleria
            pygame.Rect(2320, 220, 160, 120),    # pohjoinen -> holvi
        ]
        rooms = [entry_hall, sanctum, west_room, east_room, north_room,
                 nw_gallery, ne_gallery, vault]
        self.rooms = {"entry": entry_hall, "sanctum": sanctum,
                      "west": west_room, "east": east_room,
                      "north": north_room, "nw": nw_gallery,
                      "ne": ne_gallery, "vault": vault}

        self.floor = CryptFloor(self.width, self.height)
        walls, floors = build_dungeon(rooms + corridors, self.width,
                                      self.height, wall_style="crypt",
                                      floor_style="crypt")
        for wall in walls:
            self.props.append(wall)
            self.obstacles.append(wall)
        self.floor_props.extend(floors)

        # ---------------- MISSION-LOGIIKAN KIINTOPISTEET --------------
        # Pelaaja astuu sisään etelästä, puolustaa sanktuaaria; aallot
        # vyöryvät ulkokammioiden portaaleista käytäviä pitkin.
        self.entrance_point = (entry_hall.centerx, entry_hall.centery + 60)
        self.defend_point = sanctum.center
        self.portal_points = [west_room.center, east_room.center,
                              north_room.center, nw_gallery.center,
                              ne_gallery.center]
        self.spawn_points = [self.entrance_point]

        # ---------------- PORTIT: selvä sisään ja ulos ----------------
        gate = GateZone(entry_hall.centerx - 90, entry_hall.bottom - 40,
                        180, 100, kind="arch", label="MUCKFORD (RETREAT)",
                        facing="down")
        self.props.append(gate)
        vault_gate = GateZone(vault.centerx - 70, vault.top - 6, 140, 80,
                              kind="portal", label="SEALED VAULT",
                              facing="up")
        self.props.append(vault_gate)

        # ---------------- SISUSTUS ------------------------------------
        # Sanktuaarin pilarit: suojaa pelaajalle, ei tukkeeksi käytäviin
        for px, py in [(sanctum.left + 220, sanctum.top + 200),
                       (sanctum.right - 300, sanctum.top + 200),
                       (sanctum.left + 220, sanctum.bottom - 280),
                       (sanctum.right - 300, sanctum.bottom - 280)]:
            pillar = CryptBigPillar(px, py)
            self.props.append(pillar)
            self.obstacles.append(pillar)

        # Arkut gallerioihin ja pohjoiskammioon riveiksi
        for room in (nw_gallery, ne_gallery, north_room):
            for i in range(3):
                cx = room.left + 120 + i * (room.w - 220) // 2
                coffin = CryptCoffin(cx, room.top + 80)
                self.props.append(coffin)
                self.obstacles.append(coffin)

        # Hajasälä kammioihin (EI käytäville - ne pysyvät kuljettavina)
        scatter_rooms = [west_room, east_room, nw_gallery, ne_gallery,
                         north_room]
        for room in scatter_rooms:
            for x, y in spread_points(rng, room.inflate(-160, -160), 4,
                                      min_dist=140):
                cls = rng.choice((CryptGrass, CryptRock, BrokenPillar,
                                  CryptPillar, CryptGrass))
                prop = cls(x, y)
                self.props.append(prop)
                self.obstacles.append(prop)

        # ---------------- TEKEMISTÄ: resurssit ------------------------
        node_table = [
            ("Grave Dust", "bone", west_room),
            ("Crypt Moss", "mushroom", east_room),
            ("Ancient Bone", "bone", nw_gallery),
            ("Crypt Moss", "mushroom", ne_gallery),
            ("Grave Dust", "bone", north_room),
        ]
        for idx, (resource, style, room) in enumerate(node_table):
            for jdx, (x, y) in enumerate(spread_points(
                    rng, room.inflate(-200, -200), 2, min_dist=180)):
                self.props.append(FieldResourceNode(
                    f"crypt_{idx}_{jdx}", x, y, resource, style, (1, 2)))
        # Rautamalmia sivukammioissa (hakattava)
        for room in (west_room, east_room):
            for x, y in spread_points(rng, room.inflate(-240, -240), 2,
                                      min_dist=200):
                ore = IronOre(x, y)
                self.props.append(ore)
                self.obstacles.append(ore)
        # Holvin aarteet: kristalleja perimmäisessä kammiossa
        for jdx, (x, y) in enumerate(spread_points(
                rng, vault.inflate(-120, -80), 3, min_dist=110)):
            self.props.append(FieldResourceNode(
                f"crypt_vault_{jdx}", x, y, "Vortex Shard", "crystal",
                (1, 1)))

        # ---------------- TUNNELMA ------------------------------------
        # Roihut sanktuaarin kulmissa + sisäänkäynnillä, sumu kammioissa
        for px, py in [(sanctum.left + 120, sanctum.top + 120),
                       (sanctum.right - 140, sanctum.top + 120),
                       (entry_hall.left + 90, entry_hall.top + 70),
                       (entry_hall.right - 110, entry_hall.top + 70),
                       (vault.centerx, vault.centery)]:
            self.props.append(EmberEmitter(px, py, variant=1))
        for room in (nw_gallery, ne_gallery, west_room, east_room):
            fog = FogPatch(room.centerx, room.centery, variant=3)
            self.props.append(fog)

    def get_spawn_point(self):
        return self.entrance_point

    def update(self, all_units):
        # Efektiemitterit elävät (kombattitila ei päivitä propeja itse)
        for p in self.props:
            if getattr(p, "is_effect", False):
                p.update(None, None)

    def draw_background(self, screen, offset=(0, 0)):
        self.floor.draw(screen, offset)
        for p in self.floor_props:
            p.draw(screen, offset)

    def draw_foreground(self, screen, offset=(0, 0)):
        pass
