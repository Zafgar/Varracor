import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from assets.tiles.house_objects import HouseWall, HouseDoor, InnCounter, InnTable, InnTable2, InnBed, InnDoubleBed, BearRug, InnFireplace, Cauldron, CookingTable, Vase
from assets.tiles.house_floors import HouseFloor
from assets.tiles.house_vfx import HouseVFX
from assets.tiles.tavern_objects import WorkTable, MagicCrystal, StagePlatform, BarrelGroup
from assets.tiles.blacksmith_objects import Forge
from assets.tiles.muckford_objects import ScrapPileBig, ScrapBarrel

class HouseArena:
    def __init__(self):
        # Määritellään huoneen koko (Vielä suurempi: Keittiö + Salahuone)
        self.width = 2800 # Laajennettu kellarille
        self.height = 1600
        
        self.floor = HouseFloor(self.width, self.height)
        self.vfx = HouseVFX(self.width, self.height)
        
        self.props = []
        self.obstacles = []
        
        self._build_room()

    def _build_room(self):
        w, h = self.width, self.height
        wall_s = 40 # New smaller wall size
        
        # --- SEINÄT ---
        # Yläseinä
        for x in range(0, w, wall_s):
            self._add_prop(HouseWall(x, 0))
            
        # Alaseinä (Jätetään oviaukko keskelle)
        door_x = w // 2
        door_width = 120 # Oviaukon leveys
        for x in range(0, w, wall_s):
            if not (door_x - door_width//2 <= x < door_x + door_width//2):
                self._add_prop(HouseWall(x, h - wall_s))
                
        # Vasen seinä
        for y in range(wall_s, h - wall_s, wall_s):
            self._add_prop(HouseWall(0, y))
            
        # Oikea seinä
        for y in range(wall_s, h - wall_s, wall_s):
            self._add_prop(HouseWall(w - wall_s, y))

        # --- HUONEET (Vasemmalla laidalla) ---
        # Tehdään 4 erillistä huonetta vasemmalle seinustalle
        room_w = 400
        room_h = 300
        corridor_x = room_w # Pystyseinän X-koordinaatti
        
        # Pystyseinä erottamaan huoneet pääsalista
        for y in range(wall_s, h - wall_s, wall_s):
            # Jätetään oviaukot jokaiseen huoneeseen
            # Huoneiden keskikohdat: 150, 450, 750, 1050, 1400
            is_door = False
            # Oviaukot: 120, 440, 720, 1040, 1360 (vastaa ovien sijaintia)
            for r_y in [120, 440, 720, 1040, 1360]:
                if r_y - 20 < y < r_y + 60: 
                    is_door = True
            
            if not is_door:
                self._add_prop(HouseWall(corridor_x, y))
        
        # Lisätään ovet aukkoihin (Pystysuorat ovet)
        # Keskitetään ovi seinän sisään (+10px) ja asetetaan oikeaan Y-kohtaan
        self._add_prop(HouseDoor(corridor_x + 10, 120, "vertical"))
        self._add_prop(HouseDoor(corridor_x + 10, 440, "vertical"))
        self._add_prop(HouseDoor(corridor_x + 10, 720, "vertical"))
        self._add_prop(HouseDoor(corridor_x + 10, 1040, "vertical"))
        self._add_prop(HouseDoor(corridor_x + 10, 1360, "vertical"))
            
        # Vaakaseinät huoneiden väliin
        for y in [300, 600, 900, 1200]:
            for x in range(wall_s, corridor_x, wall_s):
                self._add_prop(HouseWall(x, y))

        # --- KEITTIÖ (Oikea yläkulma) ---
        kitchen_x = w - 700
        kitchen_y = 600
        
        # Keittiön seinät
        for x in range(kitchen_x, w, wall_s):
            # Jätetään leveä oviaukko keittiöön
            if x < w - 250: 
                self._add_prop(HouseWall(x, kitchen_y))
        
        for y in range(0, kitchen_y, wall_s):
            self._add_prop(HouseWall(kitchen_x, y))

        # --- SALAHUONE (Oikea alakulma) ---
        secret_x = w - 500
        secret_y = h - 500
        
        # Salahuoneen seinät
        for x in range(secret_x, w, wall_s):
            # Jätetään aukko kirjahyllylle (salaovi)
            if not (secret_x + 80 < x < secret_x + 220):
                self._add_prop(HouseWall(x, secret_y))
        
        for y in range(secret_y, h, wall_s):
            self._add_prop(HouseWall(secret_x, y))

        # --- KELLARI (Keittiön oikealla puolella) ---
        cellar_x = 2400
        # Seinä keittiön ja kellarin väliin
        for y in range(0, 600, wall_s):
            if not (200 < y < 300): # Oviaukko
                self._add_prop(HouseWall(cellar_x, y))
        
        # Kellarin sisältö
        self._add_prop(ScrapPileBig(2500, 100))
        self._add_prop(BarrelGroup(2600, 400))
        self._add_prop(ScrapBarrel(2450, 500))

        # --- HUONEKALUT ---
        
        # Tiski (Keittiön eteen)
        # Siirretään tiskiä hieman alemmas ja vasemmalle, jotta sen taakse mahtuu
        self._add_prop(InnCounter(1700, 250))
        
        # Tulisija (Yläseinä, keskellä)
        # Keskitetään pääsaliin (x=400...2100 -> center ~1250)
        fp_x = 1250
        fp_y = 40 # Kiinni yläseinässä
        self._add_prop(InnFireplace(fp_x, fp_y))
        self.vfx.add_fireplace(fp_x + 90, fp_y + 70) # VFX keskelle tulisijaa (leveys 180)
        
        # Matto takan eteen
        self._add_prop(BearRug(fp_x + 35, fp_y + 80)) # Matto takan eteen
        self._add_prop(BearRug(1150, 550)) # Keskelle pitkän pöydän alle
        self._add_prop(BearRug(650, 850)) # Alapöydän alle
        
        # Keittiön varustus
        # Liesi (Forge)
        stove_x = w - 400
        self._add_prop(Forge(stove_x, 40))
        self.vfx.add_fireplace(stove_x + 150, 140, spread=30)
        self.vfx.add_steam(stove_x + 100, 100)
        self.vfx.add_steam(stove_x + 200, 100)
        
        # Pata (Cauldron)
        self._add_prop(Cauldron(w - 600, 80))
        
        # --- LAVA (Stage) ---
        # Oikealle takasta, lähelle tiskiä
        stage_x = 1500
        self._add_prop(StagePlatform(stage_x, 100, w=240, h=140))
        
        # Pöytiä (Pääsalissa) - Lisätty ja järjestelty
        
        # Yläosa (Takan lähellä)
        self._add_prop(InnTable2(1050, 250)) # Pitkä pöytä vasemmalla
        self._add_prop(InnTable(1450, 250))  # Neliö oikealla
        
        # Keski-vasen
        self._add_prop(InnTable(750, 550))
        
        # Keskellä iso ryhmä
        self._add_prop(InnTable2(1100, 600)) 
        self._add_prop(InnTable(1400, 600))
        
        # Oikea laita (Tiskin edusta)
        self._add_prop(InnTable(1800, 500))
        
        # Alaosa (Oven molemmin puolin)
        self._add_prop(InnTable2(650, 850))
        self._add_prop(InnTable(1000, 900))
        self._add_prop(InnTable2(1350, 850))
        self._add_prop(InnTable(1750, 900))
        
        # Sänkyjä (Makuuhuoneissa) - Siirretty kiinni vasempaan seinään (x=50)
        # Huone 1 (Ylin)
        self._add_prop(InnDoubleBed(50, 150)) # Jätetään tilaa ylös ammeelle/hyllylle
        # Huone 2
        self._add_prop(InnDoubleBed(50, 450))
        # Huone 3 (Gambling) - Ei sänkyä (TavernMenu poistaa pöydät jos niitä on)
        # Huone 4 (Gambling extension) - Ei sänkyä
        # Huone 5 (Alin)
        self._add_prop(InnDoubleBed(50, 1350))
        
        # --- SALAHUONEEN KRISTALLI ---
        self._add_prop(MagicCrystal(w - 150, h - 150))
        
        # --- LISÄTÄÄN KYNTTILÖITÄ PÖYDILLE ---
        for p in self.props:
            if "Table" in p.__class__.__name__:
                # Keskelle pöytää (visuaalisesti)
                cx = p.image_pos[0] + p.image.get_width() // 2
                cy = p.image_pos[1] + p.image.get_height() // 2 - 15
                self.vfx.add_candle(cx, cy)
            elif "Counter" in p.__class__.__name__:
                # Tiskille yksi kynttilä
                cx = p.image_pos[0] + 60
                cy = p.image_pos[1] + 30
                self.vfx.add_candle(cx, cy)

    def _add_prop(self, prop):
        self.props.append(prop)
        if getattr(prop, "is_structure", False) and prop.rect.w > 0 and prop.rect.h > 0:
            self.obstacles.append(prop)

    def update(self, all_units=None):
        self.vfx.update()

    def draw_background(self, screen, offset=(0,0)):
        self.floor.draw(screen, offset)
        
    def draw_props(self, screen, offset=(0,0)):
        # Järjestä Y-koordinaatin mukaan (syvyys)
        sorted_props = sorted(self.props, key=lambda p: p.rect.bottom)
        for p in sorted_props:
            p.draw_on_screen(screen, offset)
            
    def draw_foreground(self, screen, offset=(0,0)):
        self.vfx.draw(screen, offset)
