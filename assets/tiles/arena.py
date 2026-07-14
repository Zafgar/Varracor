import pygame
import random
from settings import *
from assets.tiles.muckford_objects import (
    ShantyHouse, ScrapBarrel, SewerGrate, StreetLamp, TavernBuilding, 
    ScrapIronBuilding, TownHall, Smeltery, ChickenCoop, Well, AppleTree, 
    MuckfordTree, MuckfordField, ForestFloor, ScrapPileBig,
    MuckfordStall, MuckfordStage
)
from assets.tiles.muckford_floors import MuckfordFloor
from crafting.swamp.scrap_pile import ScrapPile
from assets.tiles.farm_objects import Barn, PastureFloor, FarmFenceHorizontal, FarmFenceVertical, FarmStorage, ManurePile
from assets.tiles.forest_objects import ForestBush, ForestCart, ForestCrates, ForestGrass

class Arena:
    def __init__(self):
        # Iso kartta: 3x leveys, 3x korkeus
        self.width = int(SCREEN_WIDTH * 3.0)
        self.height = int(SCREEN_HEIGHT * 3.0)
        
        self.obstacles = []
        self.props = [] 
        self.floor_props = []
        self.spawn_points = [] # Pelaajan spawnit
        self.enemy_spawns = [] # Viemärit
        
        self.floor = MuckfordFloor(self.width, self.height)
        self._init_city_layout()
        
    def _init_city_layout(self):
        w, h = self.width, self.height
        
        # --- ZONES ---
        # Katu jakaa kartan ylä- ja alaosaan
        street_y = h // 2
        street_width = 400
        street_top = street_y - street_width // 2
        street_bottom = street_y + street_width // 2
        
        # 1. FARM AREA (Bottom Left)
        # Määritellään alue eläimille (MuckfordCityMenu käyttää tätä)
        self.farm_area = pygame.Rect(100, street_bottom + 50, w // 2 - 200, h - street_bottom - 150)
        
        # Lattia (Pasture)
        self._add_prop(PastureFloor(self.farm_area.x, self.farm_area.y, self.farm_area.w, self.farm_area.h))
        
        # Rakennukset
        self._add_prop(Barn(self.farm_area.x + 50, self.farm_area.y + 50))
        self._add_prop(ChickenCoop(self.farm_area.x + 400, self.farm_area.y + 100))
        self._add_prop(Well(self.farm_area.x + 600, self.farm_area.y + 200))
        # Farm Shop (varasto) ja komposti (lantaquestin palautuspiste).
        # HUOM: Nämä puuttuivat aiemmin kartalta kokonaan, jolloin lantaquestia
        # ei voinut suorittaa (ei paikkaa mihin dumpata).
        self._add_prop(FarmStorage(self.farm_area.x + 750, self.farm_area.y + 50))
        self._add_prop(ManurePile(self.farm_area.x + 850, self.farm_area.bottom - 220))
        
        # Pellot (Fields)
        self._add_prop(MuckfordField(self.farm_area.x + 100, self.farm_area.bottom - 250))
        self._add_prop(MuckfordField(self.farm_area.x + 450, self.farm_area.bottom - 250))
        
        # Omenapuut
        self._add_prop(AppleTree(self.farm_area.right - 200, self.farm_area.y + 100))
        self._add_prop(AppleTree(self.farm_area.right - 100, self.farm_area.y + 250))
        
        # Aidat (Yksinkertainen aitaus)
        # Yläreuna
        for i, fx in enumerate(range(self.farm_area.x, self.farm_area.right, 256)):
            if i != 2: # Jätä aukko
                self._add_prop(FarmFenceHorizontal(fx, self.farm_area.y))
        # Alareuna
        for i, fx in enumerate(range(self.farm_area.x, self.farm_area.right, 256)):
            if i != 3: # Jätä aukko
                self._add_prop(FarmFenceHorizontal(fx, self.farm_area.bottom))
        # Vasen reuna
        for i, fy in enumerate(range(self.farm_area.y, self.farm_area.bottom, 266)):
            if i != 1: # Jätä aukko
                self._add_prop(FarmFenceVertical(self.farm_area.x, fy))
        # Oikea reuna
        for i, fy in enumerate(range(self.farm_area.y, self.farm_area.bottom, 266)):
            if i != 1: # Jätä aukko
                self._add_prop(FarmFenceVertical(self.farm_area.right, fy))

        # 2. FOREST / SLUMS (Bottom Right)
        forest_x = w // 2 + 100
        forest_y = street_bottom + 50
        forest_w = w - forest_x - 50
        forest_h = h - forest_y - 50
        
        # Metsän pohja
        self._add_prop(ForestFloor(forest_x, forest_y, forest_w, forest_h))
        
        # Ruohoa (Grass) - Ripotellaan ympäriinsä
        for _ in range(60):
            gx = random.randint(forest_x, forest_x + forest_w - 40)
            gy = random.randint(forest_y, forest_y + forest_h - 40)
            self._add_prop(ForestGrass(gx, gy))
        
        # Tiheä metsä (Puut ja Pensaat)
        for _ in range(40):
            tx = random.randint(forest_x, forest_x + forest_w - 100)
            ty = random.randint(forest_y, forest_y + forest_h - 100)
            
            # 70% Puu, 30% Pensas
            if random.random() < 0.7:
                self._add_prop(MuckfordTree(tx, ty))
            else:
                self._add_prop(ForestBush(tx, ty + 150)) # Pensaat hieman alemmas visuaalisesti
            
        # Romukasat metsässä
        for _ in range(10):
            sx = random.randint(forest_x, forest_x + forest_w - 100)
            sy = random.randint(forest_y, forest_y + forest_h - 100)
            self._add_prop(ScrapPileBig(sx, sy))
            
        # Hökkelit metsän reunassa
        self._add_prop(ShantyHouse(forest_x + 100, forest_y + 100, variant=3))
        # Lisätään kärryt ja laatikoita talon viereen
        self._add_prop(ForestCart(forest_x + 80, forest_y + 350))
        self._add_prop(ForestCrates(forest_x + 200, forest_y + 380))
        
        self._add_prop(ShantyHouse(forest_x + 500, forest_y + 200, variant=3))
        # Lisätään laatikoita toisen talon viereen
        self._add_prop(ForestCrates(forest_x + 480, forest_y + 450))

        # 3. CITY PROPER (Top Side)
        
        # Taverna (Vasen ylä)
        self._add_prop(TavernBuilding(200, 100))
        
        # Town Hall (Keskellä ylhäällä)
        self._add_prop(TownHall(w // 2 - 350, 50))
        
        # Shanty Yard -areenan portti: kadun ETELÄreunalla hökkelimetsän
        # rajalla - portti johtaa slummien kehälle (ei enää talojen keskellä)
        from assets.tiles.muckford_objects import ShantyYardGate
        gate = ShantyYardGate(w // 2 + 260, street_bottom - 160)
        self._clear_overlapping(gate)
        self._add_prop(gate)

        # Pelaajan tiimitila (Team Barracks): kadun varrella lännessä
        # tavernan alapuolella - erillään areenaportista
        from assets.tiles.muckford_objects import TeamBarracks
        barracks = TeamBarracks(260, street_top - 340)
        self._clear_overlapping(barracks)
        self._add_prop(barracks)

        # Blacksmith & Smeltery (Oikea ylä)
        self._add_prop(ScrapIronBuilding(w - 700, 100))
        self._add_prop(Smeltery(w - 800, 450)) # Lähellä katua
        
        # Asuinalueet (Täytetään tyhjät tilat ylhäällä)
        # Vasen kortteli (Tavernan ja Town Hallin välissä)
        # Taverna (x=200, w=800) loppuu kohtaan 1000. Aloitetaan talot kohdasta 1100.
        # Jätetään keskelle enemmän tilaa torille (w // 2 - 1000), jotta talot eivät mene kojujen päälle.
        self._generate_block(1100, 150, w // 2 - 1000, street_top)
        
        # Oikea kortteli (Town Hallin ja Blacksmithin välissä)
        # Aloitetaan torin toiselta puolelta (w // 2 + 600).
        self._generate_block(w // 2 + 600, 150, w - 800, street_top)

        # --- MARKET SQUARE ---
        market_x = w // 2
        # Town Hall on y=50, korkeus 460 -> bottom 510.
        # Laitetaan lava selkeästi sen eteen.
        stage_y = 600 
        
        # Stage (Keskellä ylhäällä, Town Hallin portaiden edessä)
        self._add_prop(MuckfordStage(market_x - 250, stage_y)) # Keskitetty (500w / 2)

        # Ilmoitustaulu torilla (kylätehtävät) - lavan oikealla puolella
        from assets.tiles.muckford_objects import NoticeBoard
        self._add_prop(NoticeBoard(market_x + 320, stage_y + 40))
        
        # Kojut (Stalls) - Torin laidoilla
        # Vasen puoli (Lava on 500 leveä. Kojut kauemmas)
        self._add_prop(MuckfordStall(market_x - 500, stage_y + 50, variant=1)) # Kristallit
        self._add_prop(MuckfordStall(market_x - 500, stage_y + 250, variant=2)) # Ruoka
        
        # Oikea puoli
        self._add_prop(MuckfordStall(market_x + 300, stage_y + 50, variant=2)) # Ruoka
        self._add_prop(MuckfordStall(market_x + 300, stage_y + 250, variant=1)) # Kristallit

        # 4. STREET PROPS
        # Katuvalot
        for x in range(200, w - 200, 500):
            self._add_prop(StreetLamp(x, street_top + 20))
            self._add_prop(StreetLamp(x + 250, street_bottom - 40))
            
        # Viemärit
        for _ in range(8):
            vx = random.randint(300, w - 300)
            vy = random.randint(street_top + 50, street_bottom - 50)
            self._add_prop(SewerGrate(vx, vy))
            self.enemy_spawns.append((vx + 30, vy + 20))
            
        # Romutynnyrit
        for _ in range(20):
            bx = random.randint(100, w - 100)
            by = random.randint(street_top, street_bottom)
            self._add_prop(ScrapBarrel(bx, by))

        # 5. MUDWATER POND (metsäaukiolla, kaakko)
        # Koodipiirretty suolampi laitureineen - kalastuspaikka. carve_pond
        # siivoaa alle jääneet puut ja lisää kulkuesteet (laituri jää auki).
        from assets.tiles.water import carve_pond
        pond_w, pond_h = 760, 460
        pond_x = forest_x + forest_w // 2 - pond_w // 2
        pond_y = forest_y + forest_h // 2 - pond_h // 2 + 60
        carve_pond(self, (pond_x, pond_y, pond_w, pond_h), seed=17)

    def _generate_block(self, x1, y1, x2, y2):
        """Generoi taloja tiheään rypäkseen, jättäen kujia."""
        # Päivitetty vastaamaan uusia isompia taloja (480x280 - 640x400)
        grid_w = 550 
        grid_h = 400
        
        for y in range(y1, y2, grid_h): 
            for x in range(x1, x2, grid_w): 
                # 80% todennäköisyys talolle, 20% aukko/kuja
                if random.random() < 0.8:
                    variant = random.randint(1, 3)
                    # Tarkistetaan mahtuuko levein talo (Variant 3 on 640px)
                    if variant == 3 and (x + 550 > x2): # Päivitetty koko (520 + margin)
                        variant = 1 # Fallback pienempään
                        
                    self._add_prop(ShantyHouse(x, y, variant))
                else:
                    # Jos aukko, laitetaan romua
                    self._add_prop(ScrapBarrel(x + 100, y + 100))

    def _clear_overlapping(self, prop, pad=60):
        """Raivaa aiemmin generoidut propit (puut, romut, talot) uuden
        rakennuksen alta, ettei se huku niiden sekaan."""
        area = pygame.Rect(prop.image_pos[0], prop.image_pos[1],
                           prop.image.get_width() if prop.image else prop.rect.w,
                           prop.image.get_height() if prop.image else prop.rect.h)
        area = area.inflate(pad, pad)
        for other in list(self.props):
            # Lattiat (pelto, laidun, metsäpohja) ja litteät jätetään:
            # niiden rect on 0-kokoinen mutta kuva valtava
            if getattr(other, "is_flat", False) or other.rect.w == 0:
                continue
            orect = pygame.Rect(
                other.image_pos[0], other.image_pos[1],
                other.image.get_width() if other.image else max(other.rect.w, 1),
                other.image.get_height() if other.image else max(other.rect.h, 1))
            if area.colliderect(orect):
                self.props.remove(other)
                if other in self.obstacles:
                    self.obstacles.remove(other)

    def _add_prop(self, prop):
        self.props.append(prop)
        # Lisää esteisiin vain jos se on rakenne (is_structure=True) ja sillä on kokoa
        if getattr(prop, "is_structure", False) and prop.rect.w > 0:
            self.obstacles.append(prop)

    def update(self, all_units):
        pass

    def draw_background(self, screen, offset=(0, 0)):
        self.floor.draw(screen, offset)
        # Lattiaobjektit (jos olisi)
        for p in self.floor_props:
            p.draw(screen, offset)

    def draw_foreground(self, screen, offset=(0, 0)):
        pass