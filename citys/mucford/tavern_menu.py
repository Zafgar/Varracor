import pygame
import math
import random
import os
from settings import *
from ui_kit import UIButton, draw_text, font_title, font_main, font_small, draw_panel, GOLD_COLOR, WHITE, GRAY, GREEN, RED, format_money
from menus.base_menu import BaseMenu
from sound_manager import sound_system
from assets.tiles.house_arena import HouseArena
from assets.tiles.house_objects import (
    HouseWall, HouseDoor, InnCounter, InnTable, InnTable2, InnBed, InnDoubleBed, 
    BearRug, InnFireplace, Cauldron, CookingTable, Vase, InnDrink, InnFood, SmallRoomTable
)
from assets.tiles.prop import Prop
from ai.tavern_ai import TavernAI
from ai.gambler_ai import GamblerAI
from units.villager import Villager
from races import get_random_name
from items.tools.bard_instrument import Lute
from units.bard import Bard
from items.daggers.scrap_dagger import ScrapDagger
from units.marda_shant import MardaShant
from assets.tiles.muckford_objects import ScrapBarrel, ScrapPileBig
from assets.tiles.tavern_objects import (
    InnDrinksTable, FoodBucket, GroundFoodPile, BarDrinksTable, BathTub,
    BookshelfHorizontal, WardrobeCloth, BarrelGroup, WorkTable, CabinetHorizontal, 
    GamblersTable, MagicCrystal, StagePlatform
)

class TavernMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.tavern_name = "The Sunk Cask"
        self.keeper_name = "Marda Shant"
        
        self.MAX_PATRONS = 8
        
        # Initialize Arena (Map)
        self.arena = HouseArena()
        # TÄRKEÄÄ: Kerrotaan managerille että olemme tässä areenassa, jotta AI osaa lisätä propit (ruoat) tänne
        self.manager.current_arena = self.arena
        
        # Helper to add props correctly to both lists (visuals & collisions)
        def add_prop(p):
            self.arena.props.append(p)
            if p.rect.w > 0 and p.rect.h > 0:
                self.arena.obstacles.append(p)
        
        # --- CUSTOM FLOOR OVERRIDE ---
        self._override_tavern_floor()
        
        # --- FIX: Poista sänkyjen hitboxit ---
        # Estää pelaajan jumiutumisen herätessä sängystä
        for p in self.arena.props:
            if "Bed" in p.__class__.__name__:
                if p in self.arena.obstacles:
                    self.arena.obstacles.remove(p)
        
        # --- FIX: Poista sänky VIP-huoneesta (Top Left) ---
        # Jotta kylpyamme mahtuu sinne ilman päällekkäisyyttä.
        # Etsitään sänky huoneesta 1 (x < 400, y < 300)
        for p in self.arena.props[:]:
            if "Bed" in p.__class__.__name__ and p.rect.x < 400 and p.rect.y < 300:
                self.arena.props.remove(p)
                if p in self.arena.obstacles: self.arena.obstacles.remove(p)
                break
        
        # --- EXPAND GAMBLING ROOM (Merge Room 3 & 4: Y=600...1200) ---
        # Poistetaan seinä (Y=900, X<400) ja huonekalut näistä huoneista
        props_to_remove = []
        for p in self.arena.props:
            # Seinä huoneiden välissä
            if "Wall" in p.__class__.__name__ and p.rect.y == 900 and p.rect.x < 400:
                props_to_remove.append(p)
            # Huonekalut huoneissa 3 ja 4 (600 < Y < 1200, X < 400)
            elif p.rect.x < 400 and 600 < p.rect.y < 1200:
                if "Bed" in p.__class__.__name__ or "Table" in p.__class__.__name__:
                    props_to_remove.append(p)
        
        for p in props_to_remove:
            if p in self.arena.props: self.arena.props.remove(p)
            if p in self.arena.obstacles: self.arena.obstacles.remove(p)
        
        # --- CLUTTER (Lisää romua nurkkiin) ---
        # Lisätään tynnyreitä satunnaisesti seinien viereen
        for _ in range(8):
            rx = random.randint(50, self.arena.width - 50)
            ry = random.randint(50, self.arena.height - 50)
            dummy = pygame.Rect(rx, ry, 40, 40)
            # Tarkista ettei osu olemassa oleviin esteisiin (seinät, pöydät)
            if not any(o.rect.colliderect(dummy) for o in self.arena.obstacles):
                # Lisää vain jos lähellä seinää (yksinkertainen heuristiikka: reunoilla)
                # KORJAUS: Älä laita vasemmalle (rx < 420), koska siellä on makuuhuoneet
                # Logic: (Oikea seinä TAI Alaseinä TAI Yläseinä mutta ei vasemmalla)
                is_right = rx > self.arena.width - 150
                is_bottom = ry > self.arena.height - 150
                is_top = ry < 150
                is_safe_x = rx > 420 # Makuuhuoneiden raja
                
                if is_right or is_bottom or (is_top and is_safe_x):
                    add_prop(ScrapBarrel(rx, ry))
        
        # Lisää tynnyri oven viereen (sisäänkäynnin koriste)
        add_prop(ScrapBarrel(self.arena.width // 2 - 100, self.arena.height - 80))
        add_prop(ScrapBarrel(self.arena.width // 2 + 100, self.arena.height - 80))

        # --- NEW PROPS (Sisustus) ---
        
        # 1. Iso juomapöytä tiskin taakse
        # Tiski on x=1700, y=250. Pöytä taakse x=1750, y=100.
        add_prop(BarDrinksTable(1750, 100))

        # 2. Kylpyamme (Vasempaan yläkulmaan, "VIP-alue")
        # Room 1: y=0..300. Amme ylös oikealle nurkkaan.
        add_prop(BathTub(220, 50))

        # 3. Ruokakasa (Keittiöön)
        add_prop(GroundFoodPile(2200, 400))
        add_prop(GroundFoodPile(2500, 400))

        # 4. Juomataso ja ämpäri (Satunnaisesti lattialle koristeeksi)
        add_prop(InnDrinksTable(550, 200)) # Käytävälle, hieman oikealle
        add_prop(FoodBucket(1650, 220)) # Tiskin päähän

        # 5. Kirjahylly (VIP-alueen viereen)
        # Room 1 yläseinälle
        add_prop(BookshelfHorizontal(50, 40))
        
        # 6. Vaatekaappi (Oikeaan yläkulmaan)
        # Room 2 yläseinälle (y=300 alkaa huone, +40 seinä)
        add_prop(WardrobeCloth(250, 340))
        
        # 7. Tynnyriryhmä (Varastoon alas)
        add_prop(BarrelGroup(2600, 1400))
        
        # 8. Työpöytä (Alimpaan huoneeseen)
        # Room 5 yläseinälle (y=1200)
        add_prop(WorkTable(250, 1240))
        # Työpöytä keittiöön
        add_prop(WorkTable(2300, 300))
        
        # 9. Kaappi (Tiskin lähelle)
        # Room 3 (Gambling) yläseinälle (y=600)
        add_prop(CabinetHorizontal(250, 640))
        
        # 10. UUSI Uhkapelipöytä (Laajennettuun huoneeseen, keskitetty Y~900)
        # Room 3+4 yhdistetty (600...1200). Keskikohta 900.
        gambling_table = GamblersTable(100, 850)
        add_prop(gambling_table)
        
        # 11. Yöpöydät makuuhuoneisiin (Room 1 & 2)
        # Room 1 (Ylin)
        add_prop(SmallRoomTable(160, 160))
        # Room 2
        add_prop(SmallRoomTable(160, 460))
        # Room 5 (Alin)
        add_prop(SmallRoomTable(160, 1360))
        
        # --- SALAHUONEEN OVI JA LOOT ---
        # Kirjahylly, joka toimii ovena (koordinaatit HouseArenan aukon mukaan)
        # HouseArena: secret_x = w - 500, secret_y = h - 500. Aukko x+80..x+220.
        secret_x = self.arena.width - 500
        secret_y = self.arena.height - 500
        
        self.secret_door = BookshelfHorizontal(secret_x + 90, secret_y - 20)
        self.secret_door.interaction_label = "Inspect (E)"
        self.secret_door.interaction_range = 100
        add_prop(self.secret_door)
        
        # Loot salahuoneeseen
        add_prop(ScrapPileBig(self.arena.width - 250, self.arena.height - 250))
        add_prop(BarrelGroup(self.arena.width - 400, self.arena.height - 150))
        add_prop(ScrapBarrel(self.arena.width - 100, self.arena.height - 400))

        # --- PRE-POPULATE TABLES (Lisää elämää pöytiin) ---
        # Käydään läpi kaikki pöydät ja lisätään satunnaisesti juomia/ruokaa
        for p in self.arena.props:
            if isinstance(p, (InnTable, InnTable2)):
                # Älä laita uhkapelipöytään lisää (se hoidettiin jo)
                if p == gambling_table: continue
                
                if random.random() < 0.5:
                    # Lisää juoma
                    dx = p.rect.centerx + random.randint(-15, 15)
                    dy = p.rect.centery - 20
                    # Varmista että InnDrink on importattu
                    drink = InnDrink(dx, dy, variant=random.randint(1, 3))
                    drink.rect.bottom = p.rect.bottom + 1 # Varmista piirto pöydän päälle
                    self.arena.props.append(drink)
                
                if random.random() < 0.3:
                    # Lisää ruoka
                    fx = p.rect.centerx + random.randint(-15, 15)
                    fy = p.rect.centery - 10
                    food = InnFood(fx, fy, variant=random.randint(1, 3))
                    food.rect.bottom = p.rect.bottom + 1 # Varmista piirto pöydän päälle
                    self.arena.props.append(food)
        
        # --------------------------------------------------

        # Player setup for this scene
        self.player = self.manager.player_character
        
        # Check spawn point
        spawn_point = getattr(self.manager, "city_spawn_point", None)
        self.manager.city_spawn_point = None # Reset
        
        self.fade_alpha = 0
        if spawn_point == "bed":
            self.fade_alpha = 255 # Aloita mustasta ruudusta
            # Etsi sänky (InnBed)
            beds = [p for p in self.arena.props if "Bed" in p.__class__.__name__]
            if beds:
                target_bed = beds[0] # Ota ensimmäinen sänky
                self.player.rect.center = target_bed.rect.center
                self.manager.start_dialogue(self.player, "My head... what happened? And where is my sword?", options=[{"text": "Get up", "action": "close_dialogue"}])
        else:
            # Set initial position (Doorway at bottom center of the arena)
            self.player.rect.centerx = self.arena.width // 2
            self.player.rect.bottom = self.arena.height - 120
            
        self.player.facing_right = False # Face into the room
        
        # Camera centering
        self.map_offset_x = (SCREEN_WIDTH - self.arena.width) // 2
        self.map_offset_y = (SCREEN_HEIGHT - self.arena.height) // 2
        self.camera_offset = (-self.map_offset_x, -self.map_offset_y)
        
        # Keeper setup (Behind the counter)
        # HouseArena counters are at Y=150. Keeper should be slightly behind/above them visually.
        # KORVATTU: Käytetään MardaShant-yksikköä
        self.keeper = MardaShant(1850, 180) # Tiskin takana (Tiski y=250)
        # Lisätään keeper propseihin jotta se piirtyy oikein (GladiatorRenderer hoitaa piirron)
        self.arena.props.append(self.keeper)

        # Mardan puheajastin
        self.marda_talk_timer = random.randint(1200, 2400) # Aloitetaan hiljaisemmin (20-40s)

        # Exit Zone (Doorway at bottom)
        self.exit_rect = pygame.Rect(self.arena.width // 2 - 60, self.arena.height - 100, 120, 100)

        # UI
        self.btn_back = UIButton(30, 30, 120, 50, "LEAVE", None, GRAY)
        
        # Recruit UI state
        self.show_recruit_list = False
        
        # UUSI: Chat Overlay (Moderni dialogijärjestelmä)
        self.chat_overlay = None
        
        # Generate recruits if needed
        if not self.manager.recruit_options:
            self.manager.generate_recruits()
            
        # --- SPAWN RECRUITS INTO ARENA ---
        for unit in self.manager.recruit_options:
            if unit:
                # Arvo sijainti pääsalista (vältä huoneita ja keittiötä)
                for _ in range(20):
                    rx = random.randint(450, 2000)
                    ry = random.randint(200, 1400)
                    dummy = pygame.Rect(rx, ry, 32, 24) # Jalkojen koko
                    if not any(o.rect.colliderect(dummy) for o in self.arena.obstacles):
                        unit.rect.topleft = (rx, ry)
                        break

                # Varmuuskopioi alkuperäinen AI (Combat AI), jos sitä ei ole jo tehty
                # Varmistetaan myös, ettei varmuuskopioida TavernAI:ta itseään
                if not hasattr(unit, "_combat_ai_backup") or unit._combat_ai_backup is None:
                    if not isinstance(unit.ai_controller, TavernAI):
                        unit._combat_ai_backup = unit.ai_controller
                
                # Aseta TavernAI
                unit.ai_controller = TavernAI(unit)
                self.arena.props.append(unit) # Lisää piirrettäviin (mutta ei obstacles)

        # --- SPAWN VILLAGERS (Patrons) ---
        # Lisätään ei-rekrytoitavia asiakkaita tunnelman vuoksi
        self.patrons = []
        for _ in range(5): # Aloitetaan viidellä
            self._spawn_patron()
        
        # --- SPECIAL NPCS ---
        # 1. Gambler (Istuu aina uhkapelipöydässä)
        # Käytetään uutta GamblerAI:ta ja erotetaan patrons-listasta omaksi muuttujaksi
        self.gambler = Villager("Sly Gix", "Goblin", 220, 970, team_color=(150, 150, 150))
        self.gambler.ai_controller = GamblerAI(self.gambler)
        self.gambler.ai_controller.target_obj = gambling_table
        # Lisätään props-listaan piirtoa varten, mutta EI patrons-listaan (jotta ei sotkeudu geneeriseen logiikkaan)
        self.arena.props.append(self.gambler)
        
        # 2. Old Drunk (Nukkuu lattialla)
        # Siirretty alimpaan huoneeseen (Room 5)
        drunk = Villager("Old Drunk", "Human", 200, 1450, team_color=(150, 150, 150))
        drunk.ai_controller = TavernAI(drunk)
        drunk.ai_controller.state = "sleeping" # Pakota nukkumaan
        drunk.ai_controller.state_timer = 99999
        self.patrons.append(drunk)
        self.arena.props.append(drunk)
            
        # --- SPAWN BARD ---
        self._spawn_bard()

    def _spawn_patron(self, at_door=False, pos=None):
        race = random.choice(["Human", "Goblin", "Dwarf", "Elf"])
        name = get_random_name(race)
        
        if pos:
            rx, ry = pos
        elif at_door:
            rx, ry = self.arena.width // 2, self.arena.height - 50 # Ovelta
        else:
            # Arvo turvallinen paikka pääsalista
            for _ in range(20):
                rx = random.randint(450, 2000)
                ry = random.randint(200, 1400)
                dummy = pygame.Rect(rx, ry, 32, 24)
                if not any(o.rect.colliderect(dummy) for o in self.arena.obstacles):
                    break
        
        v = Villager(name, race, rx, ry, team_color=(150, 150, 150))
        v.ai_controller = TavernAI(v)
        
        self.patrons.append(v)
        self.arena.props.append(v)

    def _spawn_bard(self):
        # Bard on pysyvä asukas
        # Siirretään lavalle (Stage on x=1000, y=150)
        self.bard = Bard("Bard", "Elf", 1620, 150, team_color=(100, 100, 200))
        self.bard.ai_controller = TavernAI(self.bard)
        # Anna luuttu käteen
        self.bard.equip_item(Lute())
        # Lisätään suoraan propseihin, mutta ei patrons-listaan (ettei poistu)
        self.arena.props.append(self.bard)

        # --- AUDIO SETUP ---
        sound_system.stop_music() # Pysäytä Hub-musiikki
        
        # Soita ambient loop
        self.ambient_channel = sound_system.play_sound('tavern_ambient', loops=-1, volume=0.4)
        
        self.fireplace_channel = None
        self.fireplace_obj = None
        
        # Etsi takka ja soita loop
        for p in self.arena.props:
            if "Fireplace" in p.__class__.__name__:
                self.fireplace_obj = p
                self.fireplace_channel = sound_system.play_sound('fireplace_loop', loops=-1, volume=0.0)
                break
        
        # Lighting Overlay Surface
        self.darkness_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.light_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    def _override_tavern_floor(self):
        """Vaihtaa lattian floor_wood_poor.png -kuvaan (10x10 tiiltä)."""
        if hasattr(self.arena, "floor") and hasattr(self.arena.floor, "image"):
            path = "assets/tiles/houses/floor_wood_poor.png"
            if os.path.exists(path):
                try:
                    tile_raw = pygame.image.load(path).convert()
                    aw = self.arena.width
                    ah = self.arena.height
                    # 10x10 grid
                    tw = int(aw / 10) + 1
                    th = int(ah / 10) + 1
                    tile_scaled = pygame.transform.smoothscale(tile_raw, (tw, th))
                    
                    new_surface = pygame.Surface((aw, ah))
                    for y in range(0, ah, th):
                        for x in range(0, aw, tw):
                            new_surface.blit(tile_scaled, (x, y))
                    self.arena.floor.image = new_surface
                except Exception as e:
                    print(f"Error updating tavern floor: {e}")

    def _stop_sounds(self):
        if self.ambient_channel: 
            self.ambient_channel.stop()
            self.ambient_channel = None
        if self.fireplace_channel: 
            self.fireplace_channel.stop()
            self.fireplace_channel = None
            
        # Stop Bard music
        if hasattr(self, "bard") and hasattr(self.bard, "ai_controller"):
            if hasattr(self.bard.ai_controller, "stop_music"):
                self.bard.ai_controller.stop_music()

    def _handle_local_dialogue_action(self, action):
        """Käsittelee tavernan sisäiset dialogivalinnat (Legacy + New)."""
        if action == "give_scrap_dagger":
            # Anna ase
            self.player.equip_item(ScrapDagger())
            self.manager.vfx.show_damage(self.player.rect.centerx, self.player.rect.top - 40, "Received Scrap Dagger!", color=GOLD_COLOR)
            sound_system.play_sound('recruit')
        elif action == "start_minigame:crown_knives":
            # Vähennä rahat (hoidettu dialogissa pay_gold:lla, mutta varmistus ei haittaa)
            
            # Stop Bard music specifically (keep ambient)
            if hasattr(self, "bard") and hasattr(self.bard, "ai_controller"):
                if hasattr(self.bard.ai_controller, "stop_music"):
                    self.bard.ai_controller.stop_music()
            
            self.next_state = "crown_knives"
            sound_system.play_sound('click')
        elif action == "open_recruit_menu":
            self.show_recruit_list = True
        else:
             # Välitä managerille (close_chat yms.)
             self.manager._handle_dialogue_action(action)

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        # --- UNIVERSAL MAP EDITOR ---
        if self.handle_editor_event(event):
            return

        # 1. Chat Overlay Input (Uusi järjestelmä)
        if self.chat_overlay:
            self.chat_overlay.handle_event(event)
            return

        if self.show_recruit_list:
            # Handle recruit UI events
            if event.type == pygame.MOUSEBUTTONDOWN:
                # UI Constants
                card_w, card_h = 290, 360
                gap_x, gap_y = 30, 30
                start_x = (SCREEN_WIDTH - (3 * card_w + 2 * gap_x)) // 2
                start_y = 150
                
                for i, unit in enumerate(self.manager.recruit_options):
                    if unit is None: continue
                    row, col = i//3, i%3
                    x = start_x + col * (card_w + gap_x)
                    y = start_y + row * (card_h + gap_y)
                    
                    if pygame.Rect(x, y, card_w, card_h).collidepoint(mouse_pos):
                        if self.manager.hire_recruit(i): 
                            # Palauta alkuperäinen AI (Combat AI) jos sellainen oli tallessa
                            if hasattr(unit, "_combat_ai_backup") and unit._combat_ai_backup:
                                unit.ai_controller = unit._combat_ai_backup
                                
                            sound_system.play_sound('recruit')
                        else:
                            sound_system.play_sound('error')
                
                # Close on back button
                if self.btn_back.is_clicked(event): 
                    self.show_recruit_list = False
                    sound_system.play_sound('click')
                    return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.show_recruit_list = False

        # --- DIALOGUE INPUT HANDLING (Lisätty) ---
        elif self.manager.active_dialogue:
            if event.type == pygame.KEYDOWN:
                opts = self.manager.active_dialogue.get("options", [])
                if event.key == pygame.K_1 and len(opts) >= 1:
                    self._handle_local_dialogue_action(opts[0]["action"])
                elif event.key == pygame.K_2 and len(opts) >= 2:
                    self._handle_local_dialogue_action(opts[1]["action"])
                elif event.key in (pygame.K_SPACE, pygame.K_ESCAPE):
                    # Jos ei ole valintoja, sulje
                    if not opts: self.manager.active_dialogue = None
            
            elif event.type == pygame.MOUSEWHEEL:
                self.manager.handle_dialogue_scroll(event.y)
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Hiiren klikkaus dialogin nappeihin
                box_w, box_h = 800, 200
                box_x = (SCREEN_WIDTH - box_w) // 2
                box_y = (SCREEN_HEIGHT - box_h) // 2
                opts = self.manager.active_dialogue.get("options", [])
                if opts:
                    view_y = box_y + 130
                    view_h = 70
                    oy = view_y - self.manager.dialogue_scroll
                    for opt in opts:
                        if box_x + 220 <= mouse_pos[0] <= box_x + 700 and oy <= mouse_pos[1] <= oy + 25 and view_y <= mouse_pos[1] <= view_y + view_h:
                            self._handle_local_dialogue_action(opt["action"])
                            return
                        oy += 30
            return # Estä muu liike dialogin aikana

        else:
            # Handle walking mode events
            if self.btn_back.is_clicked(event):
                self._stop_sounds()
                self.next_state = "recruit" # Palaa rekrytointivalikkoon (Town Hub)
                sound_system.play_sound('click')
                return
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p and CHEAT_MODE:
                    self.manager.world_paused = not self.manager.world_paused

                if event.key == pygame.K_e:
                    # Check interaction
                    # Keeperin rect on maailmakoordinaateissa
                    if self.player.rect.colliderect(self.keeper.rect.inflate(150, 250)):
                        # Käytetään aina dialogijärjestelmää.
                        # Se hoitaa intron (jos ei tavattu) tai avaa hubin (josta pääsee rekrytoimaan).
                        self.chat_overlay = self.manager.open_dialogue("marda_shant")
                        if self.chat_overlay:
                            self.chat_overlay.return_state = "tavern_sunk_cask"
                        return
                    
                    # Check Gambler Interaction
                    if self.player.rect.colliderect(self.gambler.rect.inflate(150, 250)):
                        self.chat_overlay = self.manager.open_dialogue("gambler")
                        if self.chat_overlay:
                            self.chat_overlay.return_state = "tavern_sunk_cask"
                        return
                    
                    # Check Recruit Interaction
                    # Etsitään lähin rekrytoitava
                    for unit in self.manager.recruit_options:
                        if unit and unit in self.arena.props: # Varmistetaan että on kentällä
                            if self.player.rect.colliderect(unit.rect.inflate(140, 140)):
                                self.manager.open_recruit_dialogue(unit)
                                self.next_state = "dialogue_active"
                                return
                    
                    # Check Bard Interaction
                    if hasattr(self, "bard") and self.player.rect.colliderect(self.bard.rect.inflate(140, 140)):
                        self.manager.open_bard_dialogue(self.bard)
                        self.next_state = "dialogue_active"
                        return
                    
                    # Check Patron Interaction (Villagers)
                    for unit in self.patrons:
                        if self.player.rect.colliderect(unit.rect.inflate(140, 140)):
                            # Jos nukkuu -> Herätä ja suutu
                            ai = getattr(unit, "ai_controller", None)
                            if ai and ai.state == "sleeping":
                                ai._wake_up()
                                ai.state = "idle"
                                shout = random.choice(["Hey!", "I'm sleeping!", "Get out!", "Rude!", "Private room!"])
                                self.manager.vfx.create_speech_bubble(unit, shout, duration=90)
                                sound_system.play_sound("error")
                                return

                            self.manager.open_patron_dialogue(unit)
                            self.next_state = "dialogue_active"
                            return

                    # Check Door Interaction
                    for prop in self.arena.props:
                        if isinstance(prop, HouseDoor) and prop.interaction_rect.colliderect(self.player.rect):
                            prop.toggle()
                            sound_system.play_sound('click')
                            return
                    
                    # Check Exit
                    if self.player.rect.colliderect(self.exit_rect):
                        self._stop_sounds()
                        self.manager.city_spawn_point = "tavern"
                        self.next_state = "muckford_city" # Mene kaupunkiin
                        sound_system.play_sound('click')

                    # Check Secret Door
                    if self.player.rect.colliderect(self.secret_door.rect.inflate(60, 60)):
                        # Siirrä hylly sivuun
                        self.secret_door.rect.x += 100
                        sound_system.play_sound('click') # "Slide" ääni

                # --- COMBAT CONTROLS ---
                if event.key == pygame.K_SPACE:
                    mx, my = pygame.mouse.get_pos()
                    wx = mx + self.camera_offset[0]
                    wy = my + self.camera_offset[1]
                    dx = wx - self.player.rect.centerx
                    dy = wy - self.player.rect.centery
                    self.player.perform_dash(dx, dy)

    def update(self):
        super().update() # Calls base update (editor)
        
        if self.show_recruit_list:
            return # Pause movement when menu is open

        # Chat Overlay Update
        if self.chat_overlay:
            self.manager.is_in_dialogue = True
            self.chat_overlay.update()
            # Jos dialogi asettaa next_staten (esim. minipeliin siirtyminen)
            if self.chat_overlay.next_state:
                # Jos tila on eri kuin paluutila (esim. "crown_knives"), vaihda siihen
                if self.chat_overlay.next_state != self.chat_overlay.return_state:
                    
                    # Stop Bard music if entering minigame
                    if self.chat_overlay.next_state == "crown_knives":
                        if hasattr(self, "bard") and hasattr(self.bard, "ai_controller"):
                            if hasattr(self.bard.ai_controller, "stop_music"):
                                self.bard.ai_controller.stop_music()

                    self.next_state = self.chat_overlay.next_state
                self.chat_overlay = None
                self.manager.is_in_dialogue = False
            return
        else:
            self.manager.is_in_dialogue = False

        # Fade In Update
        if self.fade_alpha > 0:
            self.fade_alpha -= 2 # Hidas fade (n. 2 sekuntia)
            if self.fade_alpha < 0: self.fade_alpha = 0

        # Remove hired units from arena props (visuals)
        for prop in self.arena.props[:]:
            if prop in self.manager.my_team and prop != self.player:
                self.arena.props.remove(prop)

        # --- POPULATION CONTROL ---
        # 1. Poista lähteneet
        for p in self.patrons[:]:
            ai = getattr(p, "ai_controller", None)
            # Jos AI on tilassa 'gone' (jumissa tai poistunut)
            if ai and ai.state == "gone":
                self.patrons.remove(p)
                if p in self.arena.props: self.arena.props.remove(p)
                continue
            
            # Jos AI on tilassa 'leaving' ja lähellä ovea TAI 'gone'
            if ai and ai.state == "leaving":
                dist_to_exit = math.hypot(p.rect.centerx - self.arena.width//2, p.rect.centery - (self.arena.height-50))
                if dist_to_exit < 100:
                    self.patrons.remove(p)
                    if p in self.arena.props: self.arena.props.remove(p)
        
        # 2. Lisää uusia (jos tilaa on)
        if len(self.patrons) < self.MAX_PATRONS:
            if random.random() < 0.005: # Harvakseen (n. kerran 3 sekunnissa check)
                self._spawn_patron(at_door=True)

        # Update Arena & Units
        # TavernAI tarvitsee listan muista yksiköistä (brawl targetointiin)
        all_tavern_units = [u for u in self.manager.recruit_options if u]
        all_tavern_units.append(self.player)
        all_tavern_units.extend(self.patrons)
        if hasattr(self, "bard"): all_tavern_units.append(self.bard)
        all_tavern_units.append(self.keeper) # LISÄTTY: Marda mukaan AI-looppiin
        all_tavern_units.append(self.gambler) # LISÄTTY: Gambler mukaan
        
        self.arena.update(all_tavern_units)
        self.manager.vfx.update()

        # --- UPDATE RECRUITS ---
        obstacles = self.arena.obstacles
        for unit in all_tavern_units:
            if unit == self.player: continue
            if self.manager.world_paused: continue
            
            if hasattr(unit, "run_combat_ai"):
                unit.run_combat_ai(all_tavern_units, obstacles, manager=self.manager)
            if hasattr(unit, "update"):
                unit.update(obstacles, manager=self.manager)

        # --- MARDA AMBIENT TALK ---
        self.marda_talk_timer -= 1
        if self.marda_talk_timer <= 0:
            self.marda_talk_timer = random.randint(2000, 4000) # 30-60 sekuntia (paljon harvemmin)
            lines = [
                "Wipe your feet!",
                "No fighting inside!",
                "Ale's fresh. Bread's stale.",
                "Pay up or get out.",
                "I've got my eye on you lot.",
                "Someone clean up that spill!",
                "Business is business."
            ]
            self.manager.vfx.create_speech_bubble(self.keeper, random.choice(lines), duration=120)
            
            # Soita satunnainen ääni
            voice = random.choice(['marda_casual', 'marda_rude', 'marda_shouting', 'marda_annoyed'])
            sound_system.play_sound(voice)
            
        # --- ATMOSPHERE PARTICLES ---
        if random.random() < 0.3: # Jatkuva pöly
            dx = random.randint(int(self.camera_offset[0]), int(self.camera_offset[0] + SCREEN_WIDTH))
            dy = random.randint(int(self.camera_offset[1]), int(self.camera_offset[1] + SCREEN_HEIGHT))
            self.manager.vfx.create_tavern_dust(dx, dy)

        # --- UPDATE PATRONS (Varmistus, jos eivät ole all_tavern_units listassa oikein) ---
        # Huom: yllä oleva loop hoitaa jo patronsit koska ne lisättiin all_tavern_unitsiin,
        # mutta varmistetaan ettei tule tuplapäivitystä.
        # Poistetaan tämä erillinen looppi ja luotetaan yllä olevaan.
        pass

        # Simple Movement Logic
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        speed = 5
        
        # Block
        # self.player.set_blocking(keys[pygame.K_LSHIFT]) # Ei blockia tavernassa
        
        if not self.player.is_dashing:
            if keys[pygame.K_w]: dy = -speed
            if keys[pygame.K_s]: dy = speed
            if keys[pygame.K_a]: dx = -speed
            if keys[pygame.K_d]: dx = speed
        
        # Commander seuraa aina hiirtä
        mx, my = pygame.mouse.get_pos()
        wx = mx + self.camera_offset[0]
        self.player.facing_right = (wx >= self.player.rect.centerx)

        if dx != 0 or dy != 0:
            # Tallenna vanha sijainti törmäystarkistusta varten
            old_rect = self.player.rect.copy()
            
            # X-liike
            self.player.rect.x += dx
            # Tarkista seinät
            for obs in self.arena.obstacles:
                if self.player.rect.colliderect(obs.rect):
                    if dx > 0: self.player.rect.right = obs.rect.left
                    if dx < 0: self.player.rect.left = obs.rect.right

            # Y-liike
            self.player.rect.y += dy
            # Tarkista seinät
            for obs in self.arena.obstacles:
                if self.player.rect.colliderect(obs.rect):
                    if dy > 0: self.player.rect.bottom = obs.rect.top
                    if dy < 0: self.player.rect.top = obs.rect.bottom
            
            self.player.animation_state = "run"
            
            # Clamp to arena bounds (varmuuden vuoksi)
            if self.player.rect.left < 0: self.player.rect.left = 0
            if self.player.rect.right > self.arena.width: self.player.rect.right = self.arena.width
            if self.player.rect.top < 0: self.player.rect.top = 0
            if self.player.rect.bottom > self.arena.height: self.player.rect.bottom = self.arena.height
            
        else:
            self.player.animation_state = "idle"
            
        # Update player animation
        self.player.update(self.arena.obstacles, self.manager)
        
        # --- CAMERA FOLLOW ---
        # Target: Player center is at Screen center
        target_x = self.player.rect.centerx - SCREEN_WIDTH // 2
        target_y = self.player.rect.centery - SCREEN_HEIGHT // 2

        # Clamp X (Center if smaller than screen, clamp if larger)
        if self.arena.width <= SCREEN_WIDTH:
            cam_x = -(SCREEN_WIDTH - self.arena.width) // 2
        else:
            cam_x = max(0, min(target_x, self.arena.width - SCREEN_WIDTH))

        # Clamp Y
        if self.arena.height <= SCREEN_HEIGHT:
            cam_y = -(SCREEN_HEIGHT - self.arena.height) // 2
        else:
            cam_y = max(0, min(target_y, self.arena.height - SCREEN_HEIGHT))
            
        self.camera_offset = (cam_x, cam_y)
        
        # Sync to manager (for HUD transparency logic)
        self.manager.camera_x = cam_x
        self.manager.camera_y = cam_y

        # --- UPDATE AUDIO (Fireplace Distance) ---
        if self.fireplace_channel and self.fireplace_obj:
            # Laske etäisyys pelaajaan
            dist = math.hypot(self.player.rect.centerx - self.fireplace_obj.rect.centerx,
                              self.player.rect.centery - self.fireplace_obj.rect.centery)
            
            # Äänenvoimakkuuden vaimennus
            # Täysi voimakkuus 150px sisällä, 0 kun > 900px
            max_dist = 900
            min_dist = 150
            if dist < min_dist:
                vol = 0.6
            elif dist > max_dist:
                vol = 0.0
            else:
                vol = 0.6 * (1.0 - (dist - min_dist) / (max_dist - min_dist))
            
            self.fireplace_channel.set_volume(vol)

    def _draw_atmosphere(self, screen):
        """Piirtää varjot, valot ja 'tunkkaisuuden'."""
        # 1. Tumma yleissävy (Darkness)
        self.darkness_surf.fill((15, 10, 5, 90)) # Vähemmän peittävä (oli 120 alpha)
        
        # 2. Valonlähteet (Leikataan reikiä pimeyteen)
        # Käytetään BLEND_RGBA_SUB (vähentää alphaa) tai piirretään valoa ADD-moodilla toiseen pintaan
        
        # Tapa B: Piirretään valot erilliselle pinnalle ja yhdistetään
        self.light_surf.fill((0, 0, 0, 0))
        
        offset = self.camera_offset
        
        # Helper valon piirtoon
        def draw_light(x, y, radius, color, flicker=0):
            r = int(radius + random.randint(-flicker, flicker))
            
            # KORJAUS: Värit ovat nyt ERITTÄIN himmeitä (vain hento sävy)
            # Glow (iso)
            glow_col = (max(1, int(color[0] * 0.05)), max(1, int(color[1] * 0.05)), max(1, int(color[2] * 0.05)))
            pygame.draw.circle(self.light_surf, glow_col, (x, y), int(r * 1.2))
            
            # Core (pieni)
            core_col = (max(1, int(color[0] * 0.1)), max(1, int(color[1] * 0.1)), max(1, int(color[2] * 0.1)))
            pygame.draw.circle(self.light_surf, core_col, (x, y), int(r * 0.6))

        # Takka
        if self.fireplace_obj:
            # Sidotaan takan sijaintiin (objekti + kamera offset)
            fx = self.fireplace_obj.rect.centerx - offset[0]
            fy = self.fireplace_obj.rect.centery - offset[1] + 20
            draw_light(fx, fy, 160, (255, 140, 40), flicker=3)

        # Yhdistä valot pimeyteen (Light 'syö' pimeyttä tai lisätään päälle)
        # Yksinkertainen tapa: Piirrä pimeys, sitten valot ADD-moodilla
        screen.blit(self.darkness_surf, (0, 0))
        screen.blit(self.light_surf, (0, 0), special_flags=pygame.BLEND_ADD)
        
        # 3. Vinjetti (Reunat tummemmat)
        # (Voi lisätä jos haluaa vielä synkemmän)

    def _use_player_ability(self, slot_name):
        """Käyttää kykyä hiiren osoittamaan kohtaan/kohteeseen."""
        item = self.player.equipment.get(slot_name)
        if not item: return

        if self.player.spell_cooldowns.get(slot_name, 0) > 0:
            sound_system.play_sound("error")
            return

        mx, my = pygame.mouse.get_pos()
        wx = mx + self.camera_offset[0]
        wy = my + self.camera_offset[1]
        mouse_rect = pygame.Rect(wx - 5, wy - 5, 10, 10)
        
        # Käänny kohti kohdetta
        if wx > self.player.rect.centerx:
            self.player.facing_right = True
        else:
            self.player.facing_right = False

        target = None
        for u in self.arena.props:
            if hasattr(u, "rect") and u.rect.colliderect(mouse_rect):
                target = u
                break
        
        if not target:
            class DummyTarget:
                def __init__(self, x, y): self.rect = pygame.Rect(x, y, 1, 1); self.is_dead = False
            target = DummyTarget(wx, wy)

        if hasattr(item, "cast"):
            if item.cast(self.player, target, self.manager):
                cd = getattr(item, "cooldown_max", 60)
                self.player.spell_cooldowns[slot_name] = cd
                self.player.animation_state = "attack"
                self.player.attack_cooldown = 20

    def _handle_combat_click(self, pos):
        mx, my = pos
        wx = mx + self.camera_offset[0]
        wy = my + self.camera_offset[1]
        
        # Käänny kohti kohdetta
        if wx > self.player.rect.centerx:
            self.player.facing_right = True
        else:
            self.player.facing_right = False
        
        self.player.perform_attack(None, self.manager, target_pos=(wx, wy))

    def draw(self, screen):
        # 1. Background (Interior)
        screen.fill((10, 10, 12)) # Black void outside the house
        
        offset = self.camera_offset
        
        # 2. Arena Floor
        self.arena.draw_background(screen, offset)
        
        # 3. Props & Characters (Y-Sort)
        renderables = list(self.arena.props)
        renderables.append(self.player)
        
        renderables.sort(key=lambda x: x.rect.bottom)
        
        for obj in renderables:
            if hasattr(obj, "draw_on_screen"):
                obj.draw_on_screen(screen, offset)

        # 4. Arena Foreground (VFX / Dust)
        self.arena.draw_foreground(screen, offset)
        self.manager.vfx.draw_top(screen, offset)
        
        # 5. Atmosphere Overlay (Tunkkaisuus)
        self._draw_atmosphere(screen)
        
        # --- UNIVERSAL EDITOR UI ---
        self.draw_editor(screen)

        # Dialogue Overlay (Jos aktiivinen)
        if self.manager.active_dialogue:
            self.manager._draw_in_game_dialogue(screen)

        # Interaction Prompt
        if self.player.rect.colliderect(self.keeper.rect.inflate(150, 250)):
            p_screen_x = self.player.rect.centerx - offset[0]
            p_screen_y = self.player.rect.top - offset[1]
            draw_text("Press E to Talk", font_main, WHITE, screen, p_screen_x - 60, p_screen_y - 40)
            
        # Gambler Prompt
        if self.player.rect.colliderect(self.gambler.rect.inflate(150, 250)):
            ux = self.gambler.rect.centerx - offset[0]
            uy = self.gambler.rect.top - offset[1]
            draw_text("Gamble (E)", font_small, GOLD_COLOR, screen, ux - 30, uy - 30)

        # Recruit Prompts
        for unit in self.manager.recruit_options:
            if unit and unit in self.arena.props:
                if self.player.rect.colliderect(unit.rect.inflate(140, 140)):
                    ux = unit.rect.centerx - offset[0]
                    uy = unit.rect.top - offset[1]
                    draw_text("Talk (E)", font_small, GOLD_COLOR, screen, ux - 30, uy - 30)

        # Bard Prompt
        if hasattr(self, "bard") and self.player.rect.colliderect(self.bard.rect.inflate(140, 140)):
            ux = self.bard.rect.centerx - offset[0]
            uy = self.bard.rect.top - offset[1]
            draw_text("Request Song (E)", font_small, (150, 150, 255), screen, ux - 50, uy - 30)

        # Patron Prompts
        for unit in self.patrons:
            if self.player.rect.colliderect(unit.rect.inflate(140, 140)):
                ux = unit.rect.centerx - offset[0]
                uy = unit.rect.top - offset[1]
                draw_text("Chat (E)", font_small, (200, 200, 200), screen, ux - 30, uy - 30)

        # Door Prompts
        for prop in self.arena.props:
            if isinstance(prop, HouseDoor) and prop.interaction_rect.colliderect(self.player.rect):
                dx = prop.interaction_rect.centerx - offset[0]
                dy = prop.interaction_rect.top - offset[1]
                draw_text("Open/Close (E)", font_small, WHITE, screen, dx - 40, dy - 20)

        # Exit Prompt
        if self.player.rect.colliderect(self.exit_rect):
            p_screen_x = self.player.rect.centerx - offset[0]
            p_screen_y = self.player.rect.top - offset[1]
            draw_text("Press E to Leave", font_main, WHITE, screen, p_screen_x - 60, p_screen_y - 40)
            
        # Secret Door Prompt
        if self.player.rect.colliderect(self.secret_door.rect.inflate(60, 60)):
            dx = self.secret_door.rect.centerx - offset[0]
            dy = self.secret_door.rect.top - offset[1]
            draw_text("Inspect (E)", font_small, GOLD_COLOR, screen, dx - 30, dy - 20)

        # UI
        if not self.show_recruit_list:
            self.btn_back.draw(screen)
            draw_text(self.tavern_name.upper(), font_title, GOLD_COLOR, screen, 200, 50)
        
        # Recruit Overlay
        if self.show_recruit_list:
            self._draw_recruit_overlay(screen)
            
        # Chat Overlay (Uusi) - Piirretään kaiken muun päälle
        if self.chat_overlay:
            self.chat_overlay.draw(screen)

    def _draw_recruit_overlay(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(220)
        overlay.fill((10, 10, 15))
        screen.blit(overlay, (0,0))
        
        draw_text(f"{self.keeper_name}'s Contracts", font_title, GOLD_COLOR, screen, SCREEN_WIDTH//2 - 150, 50)
        draw_text(f"Funds: {format_money(self.manager.gold)}", font_title, WHITE, screen, 50, 100)
        
        self.btn_back.draw(screen)
        
        # Cards
        card_w, card_h = 290, 360
        gap_x, gap_y = 30, 30
        total_w = 3 * card_w + 2 * gap_x
        start_x = (SCREEN_WIDTH - total_w) // 2
        start_y = 150
        
        mouse_pos = pygame.mouse.get_pos()
        
        for i, unit in enumerate(self.manager.recruit_options):
            row, col = i//3, i%3
            x = start_x + col * (card_w + gap_x)
            y = start_y + row * (card_h + gap_y)

            if unit is None: 
                pygame.draw.rect(screen, (30, 30, 35), (x, y, card_w, card_h), border_radius=8)
                draw_text("HIRED", font_main, (60,60,60), screen, x+110, y+160)
                continue
            
            can_afford = self.manager.gold >= unit.cost
            is_hover = pygame.Rect(x, y, card_w, card_h).collidepoint(mouse_pos)
            
            unit.draw_info_card(screen, x, y, w=card_w, h=card_h, show_cost=True, hover=is_hover, can_afford=can_afford)
            
        # Fade Overlay (Herääminen)
        if self.fade_alpha > 0:
            f = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            f.fill((0, 0, 0))
            f.set_alpha(self.fade_alpha)
            screen.blit(f, (0, 0))