import pygame
import random
import math
from settings import *
from menus.base_menu import BaseMenu
from ui_kit import draw_text, font_main, font_small, font_title, UIButton, draw_panel, draw_item_slot_background, draw_item_tooltip, WHITE, GOLD_COLOR, GREEN, RED, GRAY
from sound_manager import sound_system

# Kartta ja objektit
from assets.tiles.arena import Arena as MuckfordArena
from assets.tiles.vfx import MapVFX
from units.villager import Villager
from units.human import Human
from ai.villager_ai import VillagerAI
from races import get_random_name
from units.farm_animals import Cow, Chicken
from items.tools.bucket import BucketEmpty, BucketMilk, BucketWater
from items.tools.weak_pickaxe import WeakPickaxe
from items.tools.weak_lumberaxe import WeakLumberAxe
from items.swords.weak_sword import WeakSword
from items.shields.weak_shield import WeakShield
from assets.tiles.farm_objects import Manure, ManurePile, FarmStorage, Apple, Egg, GrassPatch
from settings import ENEMY_TEAM
from assets.tiles.muckford_objects import MuckfordTree, ScrapPileBig, TavernBuilding, TownHall, AppleTree, Smeltery, Well, ChickenCoop, ScrapIronBuilding, MuckfordStage, MuckfordStall
from crafting.swamp.scrap_pile import ScrapPile
from quest_system import quest_manager
from ai.life_ai import DIALOGUE_TOPICS
from citys.mucford.market_stalls import MarketStall, build_market_row
from assets.tiles.water import WaterBody
from systems import fishing as fishing_system

class MuckfordCityMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        
        # Käytetään seediä myös asukkaille, jotta ne ovat aina samoilla paikoilla alussa
        self.rng = random.Random(54321)
        
        # 1. Alusta kartta
        self.arena = MuckfordArena()
        self.manager.current_arena = self.arena
        self.vfx = MapVFX()
        self.manager.current_map_vfx = self.vfx
        
        # Rekisteröi callback manageriin jotta Coop voi kutsua sitä
        self.manager.spawn_chicken = self.spawn_chicken
        
        # 2. Pelaaja
        self.player = self.manager.player_character
        # Aseta pelaaja oletuksena keskelle, tai tavernan ovelle jos tullaan sieltä
        # Etsitään taverna (ensimmäinen talo)
        self.tavern_house = None
        for p in self.arena.props:
            if isinstance(p, TavernBuilding):
                self.tavern_house = p
                break
        
        self.blacksmith_house = None
        for p in self.arena.props:
            if isinstance(p, ScrapIronBuilding):
                self.blacksmith_house = p
                break
        
        # Etsitään kaikki talot (NPC-simulaatiota varten)
        self.buildings = []
        for p in self.arena.props:
            if "House" in p.__class__.__name__:
                # Tallenna oven sijainti (alareuna keskellä)
                self.buildings.append((p.rect.centerx, p.rect.bottom - 20))
        
        if self.tavern_house:
            # Spawnataan tavernan ovelle
            # Ovi on vasemmalla alhaalla (offset määritelty luokassa)
            base_x, base_y = self.tavern_house.image_pos
            door_off = getattr(self.tavern_house, "door_offset", (self.tavern_house.rect.w//2, self.tavern_house.rect.h))
            self.player.rect.centerx = base_x + door_off[0]
            self.player.rect.bottom = base_y + door_off[1] + 50
        else:
            self.player.rect.center = (self.arena.width//2, self.arena.height//2)
            
        self.player.facing_right = True
        
        # 3. Kamera
        self.camera_x = 0
        self.camera_y = 0
        self._update_camera()
        
        # 4. NPC:t (50 kpl)
        self.npcs = []
        self._spawn_population()
        self._spawn_guards()
        
        # 5. Eläimet (Lehmät)
        self.animals = []

        # --- KARTTA (M-näppäin) ---
        self.show_map = False

        # Siivoa kartan ulkopuolelle jääneet propit (esim. reunan yli
        # generoidut puut) - muuten AI voi valita ne työkohteiksi ja
        # jäädä kävelemään seinää päin
        self._remove_out_of_bounds_props()

        # --- MARKET ROW ---
        # Nimetyt liikkeet market-aukiolle (lavan eteläpuoli, kadun pohjois-
        # puolella). Jokaisesta aukeaa oma kauppasivu (district_shop) ja
        # jokaisella on oma maine-faktio joka vaikuttaa hintoihin.
        self.market_stalls = build_market_row(
            self.arena.width // 2 - 50, 1150, spacing=270)
        for stall in self.market_stalls:
            self.arena.props.append(stall)

        # --- KALASTUS (Mudwater Pond + editorilla lisätyt vedet) ---
        self.fishing_session = None
        self.fishing_flash = 0     # "!"-huomio nykäisyn ajan
        self.active_fishing_spot = None
        self._pond_water = next((p for p in self.arena.floor_props
                                 if isinstance(p, WaterBody)), None)

        # --- RAT RAID -JÄRJESTELMÄ ---
        # Rat King lähettää parvia kylään kunnes hänet kukistetaan (quest hunt_01)
        self.raid_rats = []
        self.raid_state = "idle"   # idle / warning / active
        self.raid_banner_timer = 0
        self.raid_result_timer = 0
        self._raid_player_kills_start = 0
        self._spawn_animals()

        # 6. Tehtävät & Tehtävänantajat
        self.farmer_gus = None
        self._spawn_quest_givers()
        
        # Audio
        sound_system.play_music('assets/music/swamp_theme.mp3')
        
        # --- PAUSE MENU ---
        self.show_pause_menu = False
        self.pause_buttons = []
        
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        btn_w = 250
        btn_h = 50
        gap = 20
        start_y = cy - 100
        
        self.btn_resume = UIButton(cx - btn_w//2, start_y, btn_w, btn_h, "RESUME", None, GRAY)
        self.btn_hub = UIButton(cx - btn_w//2, start_y + (btn_h+gap), btn_w, btn_h, "BACK TO HUB", None, GRAY)
        self.btn_save = UIButton(cx - btn_w//2, start_y + (btn_h+gap)*2, btn_w, btn_h, "SAVE GAME", None, GRAY)
        self.btn_load = UIButton(cx - btn_w//2, start_y + (btn_h+gap)*3, btn_w, btn_h, "LOAD GAME", None, GRAY)
        self.btn_options = UIButton(cx - btn_w//2, start_y + (btn_h+gap)*4, btn_w, btn_h, "OPTIONS", None, GRAY)
        self.btn_exit = UIButton(cx - btn_w//2, start_y + (btn_h+gap)*5, btn_w, btn_h, "EXIT GAME", None, (200, 60, 60))
        
        self.pause_buttons = [self.btn_resume, self.btn_hub, self.btn_save, self.btn_load, self.btn_options, self.btn_exit]
        
        # --- SMELTERY UI ---
        self.active_smeltery = None
        self.smelter_buttons = []

    def on_enter(self):
        """Kutsutaan aina kun tähän valikkoon tullaan."""
        # Varmistetaan, että manager tietää meidän olevan tässä kartassa (eikä esim. tavernassa)
        self.manager.current_arena = self.arena
        self.manager.current_map_vfx = self.vfx
        
        # PÄIVITYS: Varmistetaan että pelaaja-referenssi on tuore
        self.player = self.manager.player_character

        # Varmistetaan referenssit (jos Arena on generoitu uudelleen tai initin jälkeen)
        if not self.tavern_house:
            for p in self.arena.props:
                if isinstance(p, TavernBuilding): self.tavern_house = p; break
        
        if not self.blacksmith_house:
            for p in self.arena.props:
                if isinstance(p, ScrapIronBuilding): self.blacksmith_house = p; break

        # --- SPAWN LOGIC ---
        spawn_target = getattr(self.manager, "city_spawn_point", None)
        self.manager.city_spawn_point = None # Nollaa heti käytön jälkeen
        
        spawned = False

        # 0. "keep": säilytä pelaajan nykyinen sijainti (esim. paluu
        # options-valikosta pause-menun kautta)
        if spawn_target == "keep":
            spawned = True

        # 1. Blacksmith Spawn
        if spawn_target == "blacksmith" and self.blacksmith_house:
            base_x, base_y = self.blacksmith_house.image_pos
            door_off = getattr(self.blacksmith_house, "door_offset", (self.blacksmith_house.rect.w//2, self.blacksmith_house.rect.h))
            self.player.rect.centerx = base_x + door_off[0]
            self.player.rect.bottom = base_y + door_off[1] + 50
            spawned = True

        # 2. Tavern Spawn (Oletus)
        if not spawned and self.tavern_house:
            base_x, base_y = self.tavern_house.image_pos
            door_off = getattr(self.tavern_house, "door_offset", (self.tavern_house.rect.w//2, self.tavern_house.rect.h))
            self.player.rect.centerx = base_x + door_off[0]
            self.player.rect.bottom = base_y + door_off[1] + 50
            spawned = True
            
        # 3. Fallback (Keskelle)
        if not spawned:
            self.player.rect.center = (self.arena.width//2, self.arena.height//2)
            
        # Kerää kokoontumispaikat (Gathering Spots)
        self.gathering_spots = []
        for p in self.arena.props:
            if isinstance(p, (Well, TownHall, Smeltery, TavernBuilding, ScrapIronBuilding)):
                 # Lisää pisteitä rakennuksen eteen
                 base_y = p.rect.bottom + 30
                 self.gathering_spots.append((p.rect.centerx, base_y))
                 self.gathering_spots.append((p.rect.centerx + 50, base_y))
                 self.gathering_spots.append((p.rect.centerx - 50, base_y))
            
            elif isinstance(p, MuckfordStage):
                 # Lavan eteen "yleisömeri"
                 # Lavan hitbox on yläreunassa (y), kuva on korkea (h).
                 # Haluamme pisteet kuvan alareunan eteen.
                 base_y = p.image_pos[1] + p.image.get_height() + 40
                 for ox in range(-200, 201, 50): # Leveämpi alue isommalle lavalle
                     self.gathering_spots.append((p.rect.centerx + ox, base_y + random.randint(-20, 40)))
                 self.stage = p  # Talteen ambient-bardieventtiä varten
            
            elif isinstance(p, (MuckfordStall, MarketStall)):
                 # Kojun eteen
                 self.gathering_spots.append((p.rect.centerx, p.rect.bottom + 40))

        # Kalastuslaituri on suosittu juttelupaikka (laiturin nokan ranta)
        for tip in getattr(self.arena, "fishing_spots", []):
            self.gathering_spots.append((tip[0] - 70, tip[1] + 50))
            self.gathering_spots.append((tip[0] + 70, tip[1] + 70))

        self._update_camera()
        self._spawn_prospects()

    def _spawn_prospects(self):
        """Rekryprospektit kaupungilla: 1-2 Sunk Caskin vapaata taistelijaa
        haahuilee kokoontumispaikoilla. E avaa saman palkkausdialogin kuin
        tavernassa - katu on löytöpaikka, taverna varma paikka.
        Idempotentti: on_enter voi kutsua useita kertoja."""
        for old in list(getattr(self, "prospects", [])):
            if old in self.npcs:
                self.npcs.remove(old)
        self.prospects = []
        pool = [u for u in getattr(self.manager, "recruit_options", [])
                if u is not None]
        if not pool or not self.gathering_spots:
            return
        count = min(2, len(pool))
        picks = self.rng.sample(pool, count)
        for unit in picks:
            spot = self.rng.choice(self.gathering_spots)
            unit.rect.center = (int(spot[0]) + self.rng.randint(-40, 40),
                                int(spot[1]) + self.rng.randint(-20, 20))
            unit.sim_state = "IDLE"
            unit.sim_timer = self.rng.randint(30, 120)
            unit.is_prospect = True
            # Taisteluäly talteen kadun ajaksi (sama malli kuin tavernassa;
            # hire_unit_by_reference -> _restore_unit_ai palauttaa sen)
            if unit.ai_controller and not hasattr(unit, "_combat_ai_backup"):
                unit._combat_ai_backup = unit.ai_controller
                unit.ai_controller = None
            self.npcs.append(unit)
            self.prospects.append(unit)

    def _cleanup_hired_prospects(self):
        """Palkattu prospekti poistuu kadulta (siirtyi tiimiin)."""
        for unit in list(getattr(self, "prospects", [])):
            if unit in self.manager.my_team or unit not in self.manager.recruit_options:
                unit.is_prospect = False
                if unit in self.npcs:
                    self.npcs.remove(unit)
                self.prospects.remove(unit)

    def _spawn_population(self):
        self._spawn_guards()
        for _ in range(50):
            # Arvo sijainti kadulta (vältä talojen sisustaa)
            # Yksinkertainen tapa: Arvo kunnes ei törmää esteeseen
            for attempt in range(10):
                rx = self.rng.randint(100, self.arena.width - 100)
                ry = self.rng.randint(100, self.arena.height - 100)
                dummy_rect = pygame.Rect(rx, ry, 32, 48)
                
                collision = False
                for obs in self.arena.obstacles:
                    if dummy_rect.colliderect(obs.rect):
                        collision = True
                        break
                
                # Tarkista myös propit (puut, kivet, romukasat)
                if not collision:
                    for prop in self.arena.props:
                        if dummy_rect.colliderect(prop.rect):
                            collision = True
                            break

                # Tarkista muut jo luodut NPC:t (ettei synny päällekkäin)
                if not collision:
                    for npc in self.npcs:
                        if dummy_rect.colliderect(npc.rect):
                            collision = True
                            break
                
                if not collision:
                    race = self.rng.choice(["Human", "Goblin", "Dwarf", "Elf"])
                    name = get_random_name(race)
                    
                    # Käytetään GREEN (sama kuin pelaaja), jotta eivät pelkää toisiaan tai pelaajaa
                    v = Villager(name, race, rx, ry, team_color=GREEN)
                    
                    # Alustetaan sim_state, jotta kaupunkisimulaatio (kävely, juttelu) toimii
                    v.sim_state = "IDLE"
                    v.sim_timer = self.rng.randint(0, 60)
                    
                    # Estetään VillagerAI:n oma satunnainen haahuilu, jotta CityMenu saa ohjata idle-liikettä
                    if hasattr(v, "ai_controller") and isinstance(v.ai_controller, VillagerAI):
                        v.ai_controller.allow_idle_wander = False
                    
                    # Varmistetaan työkalut (vaikka Villager-luokka tekee tämän, varmistus ei haittaa)
                    if not hasattr(v, "inventory") or v.inventory is None:
                        v.inventory = []

                    # Siivotaan mahdolliset None-arvot (jos Villager-luokan create_item epäonnistui)
                    v.inventory = [i for i in v.inventory if i is not None]

                    if len(v.inventory) == 0:
                        v.inventory.append(WeakPickaxe())
                        v.inventory.append(WeakLumberAxe())
                        v.inventory.append(BucketEmpty())

                    self.npcs.append(v)
                    break

    def _pet_chicken(self, hen):
        """Kanan silitys: joskus irtoaa höyhen (cooldown per kana)."""
        import random as _random
        cd = int(getattr(hen, "_feather_cd", 0))
        if cd <= 0 and _random.random() < 0.5:
            hen._feather_cd = 1800  # ~30 s ennen seuraavaa
            self.manager.add_material("Feather", 1)
            self.manager.vfx.show_damage(hen.rect.centerx, hen.rect.top - 16,
                                         "+1 Feather", color=(235, 235, 220))
            self.manager.grant_hero_xp(1, hen.rect.centerx, hen.rect.top)
        else:
            hen._feather_cd = max(0, cd)
            self.manager.vfx.show_damage(hen.rect.centerx, hen.rect.top - 16,
                                         "Cluck!", color=(220, 220, 200))
        sound_system.play_sound('hover')

    def _resolve_catch(self, fish, spot):
        """Saaliin ratkaisu: aarre koukussa? tuplasaalis? XP + tason nousu."""
        rng = self.fishing_session.rng if self.fishing_session else None
        import random as _random
        rng = rng or _random.Random()

        # Joskus koukkuun tarttuu jotain muuta kuin kala
        if rng.random() < fishing_system.treasure_chance(self.manager):
            fish = fishing_system.roll_treasure(rng)

        count = 1
        if not fish.get("treasure") and fishing_system.double_catch(self.manager) \
                and rng.random() < 0.25:
            count = 2
        self.manager.add_material(fish["name"], count)

        color = (255, 200, 120) if fish.get("treasure") else (150, 220, 255)
        prefix = "Snagged" if fish.get("treasure") else "Caught"
        suffix = " x2!" if count == 2 else "!"
        self.manager.vfx.show_damage(
            self.player.rect.centerx, self.player.rect.top - 30,
            f"{prefix} {fish['name']}{suffix}", color=color)
        self.manager.grant_hero_xp(3, self.player.rect.centerx,
                                   self.player.rect.top)
        if fishing_system.grant_catch_xp(self.manager, fish):
            lvl = fishing_system.get_progress(self.manager)["level"]
            self.manager.vfx.show_damage(
                self.player.rect.centerx, self.player.rect.top - 60,
                f"Path of the Line {lvl}!", color=(255, 215, 0))
            sound_system.play_sound('win')
        sound_system.play_sound('coin')
        water = self._water_at(spot)
        if water and spot:
            water.splash(*spot)

    def _water_at(self, point):
        """Vesialue jossa piste on (roiskeet oikeaan altaaseen)."""
        if point:
            for p in self.arena.floor_props:
                if isinstance(p, WaterBody) and \
                        p.rect.inflate(120, 120).collidepoint(point):
                    return p
        return self._pond_water

    def _nearest_fishing_spot(self, max_dist=170):
        """Lähin kalastuspaikka (laitureita voi olla useita)."""
        spots = getattr(self.arena, "fishing_spots", None) or \
            ([self.arena.fishing_spot]
             if getattr(self.arena, "fishing_spot", None) else [])
        best, best_d = None, max_dist
        for spot in spots:
            d = math.hypot(self.player.rect.centerx - spot[0],
                           self.player.rect.centery - spot[1])
            if d < best_d:
                best, best_d = spot, d
        return best

    def _remove_out_of_bounds_props(self):
        bounds = pygame.Rect(0, 0, self.arena.width, self.arena.height)
        removed = 0
        for prop in list(self.arena.props):
            if not bounds.colliderect(prop.rect):
                self.arena.props.remove(prop)
                if prop in self.arena.obstacles:
                    self.arena.obstacles.remove(prop)
                removed += 1
        if removed:
            print(f"[City] Removed {removed} out-of-bounds props")

    @staticmethod
    def _draw_map_icon(screen, x, y, kind, col):
        """Pieni koodilla piirretty ikoni karttamerkille (tuoppi, alasin...)."""
        badge = pygame.Rect(x - 12, y - 12, 24, 24)
        pygame.draw.rect(screen, (32, 28, 24), badge, border_radius=6)
        pygame.draw.rect(screen, col, badge, 2, border_radius=6)
        c = col
        if kind == "tavern":       # tuoppi + korva
            pygame.draw.rect(screen, c, (x - 6, y - 6, 9, 12), border_radius=2)
            pygame.draw.rect(screen, c, (x - 6, y - 6, 9, 3))
            pygame.draw.arc(screen, c, (x + 2, y - 4, 8, 8), -1.6, 1.6, 2)
        elif kind == "anvil":      # alasin
            pygame.draw.rect(screen, c, (x - 7, y - 4, 14, 4))
            pygame.draw.rect(screen, c, (x - 3, y, 6, 4))
            pygame.draw.rect(screen, c, (x - 5, y + 4, 10, 2))
        elif kind == "market":     # kojukatos
            pygame.draw.polygon(screen, c, [(x - 8, y - 2), (x, y - 8), (x + 8, y - 2)])
            pygame.draw.rect(screen, c, (x - 6, y - 1, 12, 7), 1)
        elif kind == "hall":       # torni + lippu
            pygame.draw.rect(screen, c, (x - 4, y - 6, 8, 13), 1)
            pygame.draw.line(screen, c, (x, y - 6), (x, y - 10), 1)
            pygame.draw.polygon(screen, c, [(x, y - 10), (x + 6, y - 8), (x, y - 6)])
        elif kind == "smeltery":   # uuni + liekki
            pygame.draw.rect(screen, c, (x - 6, y - 2, 12, 8), 1)
            pygame.draw.circle(screen, (240, 140, 60), (x, y + 2), 3)
        elif kind == "well":       # kaivon rengas
            pygame.draw.circle(screen, c, (x, y), 6, 2)
            pygame.draw.line(screen, c, (x - 6, y - 6), (x + 6, y - 6), 2)
        elif kind == "coop":       # muna
            pygame.draw.ellipse(screen, c, (x - 4, y - 6, 8, 12))
        elif kind == "storage":    # laatikko
            pygame.draw.rect(screen, c, (x - 6, y - 5, 12, 10), 1)
            pygame.draw.line(screen, c, (x - 6, y), (x + 6, y), 1)
        elif kind == "compost":    # kasa
            pygame.draw.polygon(screen, c, [(x - 7, y + 5), (x, y - 5), (x + 7, y + 5)])
        elif kind == "league":     # ristikkäiset miekat
            pygame.draw.line(screen, c, (x - 6, y + 6), (x + 6, y - 6), 2)
            pygame.draw.line(screen, c, (x - 6, y - 6), (x + 6, y + 6), 2)
        elif kind == "quarters":   # kilpi
            pygame.draw.polygon(screen, c, [(x - 6, y - 5), (x + 6, y - 5),
                                            (x + 5, y + 2), (x, y + 7), (x - 5, y + 2)], 1)
        elif kind == "board":      # ilmoitus
            pygame.draw.rect(screen, c, (x - 5, y - 6, 10, 12), 1)
            pygame.draw.line(screen, c, (x - 3, y - 2), (x + 3, y - 2), 1)
            pygame.draw.line(screen, c, (x - 3, y + 1), (x + 3, y + 1), 1)
        elif kind == "mine":       # hakku
            pygame.draw.line(screen, c, (x - 5, y + 6), (x + 4, y - 4), 2)
            pygame.draw.arc(screen, c, (x - 3, y - 9, 14, 10), 2.0, 4.4, 2)
        elif kind == "forest":     # puu
            pygame.draw.polygon(screen, c, [(x - 6, y + 2), (x, y - 8), (x + 6, y + 2)])
            pygame.draw.rect(screen, c, (x - 1, y + 2, 3, 5))
        else:
            pygame.draw.circle(screen, c, (x, y), 5)

    def _draw_city_map(self, screen):
        """Muckfordin kartta: maastovyöhykkeet, ikonit + nimet suoraan
        kartalla (ei enää pelkkiä väripisteitä ja erillistä legendaa)."""
        from ui_kit import get_fullscreen_overlay
        screen.blit(get_fullscreen_overlay((0, 0, 0, 190)), (0, 0))

        # Karttapaneeli keskelle
        map_w, map_h = 1240, 800
        panel = pygame.Rect((SCREEN_WIDTH - map_w) // 2, (SCREEN_HEIGHT - map_h) // 2 - 20, map_w, map_h)
        pygame.draw.rect(screen, (58, 50, 40), panel, border_radius=12)
        pygame.draw.rect(screen, (150, 130, 95), panel, 3, border_radius=12)
        draw_text("MUCKFORD", font_title, GOLD_COLOR, screen, panel.centerx - 110, panel.y + 10)

        # Skaalaus maailmasta kartalle
        inner = panel.inflate(-50, -120)
        inner.y += 40
        sx = inner.w / self.arena.width
        sy = inner.h / self.arena.height

        def to_map(wx, wy):
            return (int(inner.x + wx * sx), int(inner.y + wy * sy))

        def to_rect(r):
            return pygame.Rect(*to_map(r.x, r.y),
                               max(4, int(r.w * sx)), max(4, int(r.h * sy)))

        # --- MAASTO ---
        # Pohja: kuiva maa
        pygame.draw.rect(screen, (96, 82, 62), inner, border_radius=8)
        # Katu (vaakavyöhyke keskellä)
        street_y = self.arena.height // 2
        street = pygame.Rect(0, street_y - 200, self.arena.width, 400)
        pygame.draw.rect(screen, (128, 114, 92), to_rect(street))
        # Maatila (vihreä)
        farm = getattr(self.arena, "farm_area", None)
        if farm:
            fr = to_rect(farm)
            pygame.draw.rect(screen, (88, 116, 66), fr, border_radius=4)
            pygame.draw.rect(screen, (120, 150, 92), fr, 2, border_radius=4)
        # Metsä (oikea alakulma)
        forest = pygame.Rect(self.arena.width // 2 + 100, street_y + 250,
                             self.arena.width // 2 - 150,
                             self.arena.height - street_y - 300)
        pygame.draw.rect(screen, (62, 88, 56), to_rect(forest), border_radius=6)
        # Vesialueet
        for p in getattr(self.arena, "floor_props", []):
            if getattr(p, "is_water", False) or type(p).__name__ == "WaterBody":
                pygame.draw.ellipse(screen, (74, 112, 142), to_rect(p.rect))
        # Puut pieninä täplinä
        from assets.tiles.muckford_objects import MuckfordTree
        for p in self.arena.props:
            if isinstance(p, MuckfordTree):
                tx, ty = to_map(p.rect.centerx, p.rect.centery)
                pygame.draw.circle(screen, (52, 74, 48), (tx, ty), 3)
        # Talot (rakennukset harmaanruskeina laattoina)
        for p in self.arena.props:
            if getattr(p, "is_structure", False) and p.rect.w > 100 and not getattr(p, "is_flat", False):
                hr = to_rect(p.rect)
                pygame.draw.rect(screen, (118, 100, 78), hr, border_radius=3)
                pygame.draw.rect(screen, (76, 64, 50), hr, 1, border_radius=3)

        # --- KOHTEET: ikoni + nimi suoraan kartalle ---
        from assets.tiles.muckford_objects import TownHall, MuckfordStall, Smeltery, Well, ChickenCoop, ShantyYardGate, TeamBarracks, NoticeBoard
        from assets.tiles.farm_objects import FarmStorage, ManurePile
        markers = []
        if getattr(self, "tavern_house", None):
            markers.append((self.tavern_house.rect, "tavern", (240, 200, 110), "Sunk Cask"))
        if getattr(self, "blacksmith_house", None):
            markers.append((self.blacksmith_house.rect, "anvil", (235, 150, 80), "Blacksmith"))
        seen = set()
        for prop in self.arena.props:
            for cls, kind, col, label in (
                    (TownHall, "hall", (130, 165, 235), "Town Hall"),
                    (MuckfordStall, "market", (130, 215, 120), "Market"),
                    (Smeltery, "smeltery", (230, 110, 80), "Smeltery"),
                    (Well, "well", (120, 205, 225), "Well"),
                    (ChickenCoop, "coop", (225, 200, 140), "Coop"),
                    (FarmStorage, "storage", (190, 160, 105), "Storage"),
                    (ManurePile, "compost", (150, 125, 85), "Compost"),
                    (ShantyYardGate, "league", (225, 90, 80), "Shanty Yard"),
                    (TeamBarracks, "quarters", (110, 200, 120), "Team Quarters"),
                    (NoticeBoard, "board", (235, 215, 165), "Notices")):
                if isinstance(prop, cls) and label not in seen:
                    seen.add(label)
                    markers.append((prop.rect, kind, col, label))

        mine_owned = getattr(self.manager, "mine_key_owned", False)
        markers.append((self._mine_gate_rect(), "mine",
                        (215, 215, 225) if mine_owned else (140, 140, 150),
                        "Mine Road" if mine_owned else "Mine (locked)"))
        markers.append((self._forest_gate_rect(), "forest",
                        (140, 200, 130), "Forest Trail"))

        for rect, kind, col, label in markers:
            mx, my = to_map(rect.centerx, rect.centery)
            self._draw_map_icon(screen, mx, my, kind, col)
            # Nimi ikonin viereen; oikeassa laidassa teksti vasemmalle
            lbl = font_small.render(label, True, (240, 235, 220))
            bg = pygame.Surface((lbl.get_width() + 8, lbl.get_height() + 2),
                                pygame.SRCALPHA)
            bg.fill((20, 16, 12, 165))
            if mx > inner.right - 150:
                lx = mx - 16 - lbl.get_width() - 8
            else:
                lx = mx + 16
            screen.blit(bg, (lx - 4, my - 9))
            screen.blit(lbl, (lx, my - 8))

        # Raid-viholliset punaisina sykkivinä pisteinä
        rat_pulse = 2 + int(2 * abs(math.sin(pygame.time.get_ticks() * 0.008)))
        for rat in self.raid_rats:
            if getattr(rat, "is_dead", False):
                continue
            rx, ry = to_map(rat.rect.centerx, rat.rect.centery)
            pygame.draw.circle(screen, (230, 60, 50), (rx, ry), 4 + rat_pulse, 2)
            pygame.draw.circle(screen, (255, 90, 70), (rx, ry), 3)
        if any(not getattr(r, "is_dead", False) for r in self.raid_rats):
            draw_text("RAID! Red marks = rats", font_small, (255, 110, 90),
                      screen, panel.x + 24, panel.bottom - 30)

        # Pelaaja (sykkivä merkki)
        px, py = to_map(self.player.rect.centerx, self.player.rect.centery)
        pulse = 3 + int(2 * abs(math.sin(pygame.time.get_ticks() * 0.005)))
        pygame.draw.circle(screen, (255, 250, 220), (px, py), 6 + pulse, 2)
        pygame.draw.circle(screen, (255, 255, 255), (px, py), 5)
        pygame.draw.circle(screen, (60, 40, 20), (px, py), 5, 1)
        draw_text("YOU", font_small, WHITE, screen, px + 10, py - 8)

        draw_text("[M] / [ESC] close", font_small, (190, 185, 170), screen,
                  panel.right - 170, panel.y + 18)

    def _mine_gate_rect(self):
        """Kaivostien portti kaupungin itäreunalla."""
        return pygame.Rect(self.arena.width - 70, self.arena.height // 2 - 120, 70, 240)

    def _forest_gate_rect(self):
        """Metsäpolun aukko kartan eteläreunalla (metsävyöhykkeen alapuolella)."""
        gx = int(self.arena.width * 0.72)
        return pygame.Rect(gx, self.arena.height - 70, 260, 70)

    def _spawn_guards(self):
        """Lisää vartijat (Human) jotka käyttävät Combat AI:ta (eivät pelkää)."""
        for i in range(6):
            for attempt in range(10):
                rx = self.rng.randint(100, self.arena.width - 100)
                ry = self.rng.randint(100, self.arena.height - 100)
                dummy_rect = pygame.Rect(rx, ry, 32, 48)
                
                collision = False
                for obs in self.arena.obstacles:
                    if dummy_rect.colliderect(obs.rect):
                        collision = True
                        break
                
                if not collision:
                    # Vartijat ovat Human-luokkaa (Gladiator), joten ne käyttävät HumanAI:ta (Combat)
                    # Eivätkä VillagerAI:ta (Työt/Pako)
                    guard = Human(f"City Guard", rx, ry, GREEN, "Guard")
                    guard.equip_item(WeakSword())
                    guard.equip_item(WeakShield())
                    
                    self.npcs.append(guard)
                    break

    def _spawn_animals(self):
        # Jos areenalla on farm_area, spawnataan lehmät sinne
        if hasattr(self.arena, "farm_area"):
            area = self.arena.farm_area
            for i in range(3):
                # Yritä löytää vapaa paikka (ei ladon tai aidan sisällä)
                for _ in range(10):
                    x = self.rng.randint(area.left + 50, area.right - 50)
                    y = self.rng.randint(area.top + 50, area.bottom - 50)
                    dummy = pygame.Rect(x, y, 64, 48)
                    
                    collision = False
                    for obs in self.arena.obstacles:
                        if dummy.colliderect(obs.rect):
                            collision = True
                            break
                    
                    # Tarkista propit ja muut eläimet
                    if not collision:
                        for prop in self.arena.props:
                            if dummy.colliderect(prop.rect):
                                collision = True
                                break
                        for other_cow in self.animals:
                            if dummy.colliderect(other_cow.rect):
                                collision = True
                                break
                    
                    if not collision:
                        cow = Cow(x, y, team_color=GREEN) # Vihreä tiimi = ei vihollinen
                        cow.farm_rect = area # Aseta rajaus AI:lle
                        if i == 0: cow.milk_ready = True
                        self.animals.append(cow)
                        break
            
            # Ruoho (Lehmät tarvitsevat tätä tuottaakseen maitoa)
            for _ in range(20):
                gx = self.rng.randint(area.left, area.right)
                gy = self.rng.randint(area.top, area.bottom)
                # Lisätään floor_props listaan (jos arena tukee), muuten props
                self.arena.floor_props.append(GrassPatch(gx, gy))

            # Kanat
            for _ in range(5):
                for _ in range(10):
                    cx, cy = self.rng.randint(area.left, area.right), self.rng.randint(area.top, area.bottom)
                    dummy = pygame.Rect(cx, cy, 20, 20)
                    collision = False
                    
                    # Tarkista esteet kanoillekin
                    for obs in self.arena.obstacles:
                        if dummy.colliderect(obs.rect): collision = True; break
                    for prop in self.arena.props:
                        if dummy.colliderect(prop.rect): collision = True; break
                        
                    if not collision:
                        c = Chicken(cx, cy, team_color=GREEN)
                        c.facing_right = True # Alustetaan puuttuva attribuutti
                        self.animals.append(c)
                        break

    def spawn_chicken(self, x, y):
        """Callback jota ChickenCoop kutsuu."""
        c = Chicken(x, y, team_color=GREEN)
        c.facing_right = True # Alustetaan puuttuva attribuutti
        self.animals.append(c)
        self.manager.vfx.show_damage(x, y - 20, "Hatched!", color=GREEN)

    def _spawn_quest_givers(self):
        # Sijoitetaan Farmer Gus maatilan portin lähelle
        if hasattr(self.arena, "farm_area"):
            farm_gate_x = self.arena.farm_area.centerx
            farm_gate_y = self.arena.farm_area.bottom + 50
            
            gus = Villager("Farmer Gus", "Dwarf", farm_gate_x, farm_gate_y, team_color=GREEN)
            # Estetään häntä liikkumasta
            gus.ai_controller = None 
            gus.animation_state = "idle"
            
            self.farmer_gus = gus
            self.npcs.append(gus) # Lisätään piirrettäviin ja päivitettäviin

        # Hamo (goblin bounty broker) - kadun varrella, areenan liepeillä
        hamo_x = self.arena.width // 2 + 200
        hamo_y = self.arena.height // 2 + 120
        hamo = Villager("Hamo", "Goblin", hamo_x, hamo_y, team_color=GREEN)
        hamo.ai_controller = None  # Pysyy paikallaan kuten Gus
        hamo.name = "Hamo"  # VillagerAI ehti lisätä job-liitteen; palautetaan
        hamo.animation_state = "idle"
        self.hamo = hamo
        self.npcs.append(hamo)

        # Bram "Mudhand" Carrow - Tier 0 -verkoston manageri areenaportilla
        self.arena_gate = None
        from assets.tiles.muckford_objects import ShantyYardGate
        for prop in self.arena.props:
            if isinstance(prop, ShantyYardGate):
                self.arena_gate = prop
                break
        if self.arena_gate:
            bx = self.arena_gate.rect.left - 60
            by = self.arena_gate.rect.bottom + 20
            bram = Villager("Bram", "Dwarf", bx, by, team_color=GREEN)
            bram.ai_controller = None
            bram.name = "Bram 'Mudhand' Carrow"
            bram.animation_state = "idle"
            self.bram = bram
            self.npcs.append(bram)
        else:
            self.bram = None

        # Team Barracks -viittaus talteen (E-interaktiota ja ikonia varten)
        self.barracks = None
        from assets.tiles.muckford_objects import TeamBarracks
        for prop in self.arena.props:
            if isinstance(prop, TeamBarracks):
                self.barracks = prop
                break

        # Esiintymislava talteen ambient-bardieventtiä varten
        self.stage = None
        for prop in self.arena.props:
            if isinstance(prop, MuckfordStage):
                self.stage = prop
                break

        # Ilmoitustaulu talteen (kylätehtävät)
        self.notice_board = None
        from assets.tiles.muckford_objects import NoticeBoard
        for prop in self.arena.props:
            if isinstance(prop, NoticeBoard):
                self.notice_board = prop
                break

        # Rivaalitiimien gladiaattoreita lorvimassa kaupungissa (liikkuvat,
        # asenteellinen dialogi). Merkitään ne rival_infolla.
        self.rival_units = []
        from npc.rival_gladiator_npc import RIVAL_GLADIATORS
        races_for = {"arrogant": "Elf", "gruff": "Dwarf", "cagey": "Goblin", "warm": "Human"}
        street_y = self.arena.height // 2
        for i, (rname, team, attitude) in enumerate(RIVAL_GLADIATORS):
            rx = self.arena.width // 2 - 400 + i * 220
            ry = street_y + 40
            race = races_for.get(attitude, "Human")
            rv = Villager(rname, race, rx, ry, team_color=GREEN)
            rv.name = rname  # VillagerAI lisää job-liitteen; palautetaan
            rv.rival_info = (rname, team, attitude)
            self.npcs.append(rv)
            self.rival_units.append(rv)

    def _open_smelter_ui(self, smelter):
        self.active_smeltery = smelter
        self.smelter_buttons = []
        
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        panel_w, panel_h = 700, 500
        px = cx - panel_w // 2
        py = cy - panel_h // 2
        
        # Actions
        # Scrap Bar (Vasemmalla)
        btn_scrap = UIButton(px + 40, py + 200, 280, 60, "Smelt Scrap Bar", None, (60, 60, 70))
        btn_scrap.action = "smelter_scrap"
        self.smelter_buttons.append(btn_scrap)
        
        # Iron Bar (Oikealla)
        btn_iron = UIButton(px + 380, py + 200, 280, 60, "Smelt Iron Bar", None, (60, 60, 70))
        btn_iron.action = "smelter_iron"
        self.smelter_buttons.append(btn_iron)
        
        # Deposit (Alhaalla)
        btn_dep = UIButton(px + 200, py + 400, 300, 50, "Deposit Resources", None, (40, 70, 40))
        btn_dep.action = "smelter_deposit"
        self.smelter_buttons.append(btn_dep)

    def handle_event(self, event):
        # Varmistetaan että pelaaja-referenssi on ajan tasalla
        self.player = self.manager.player_character
        
        # --- UNIVERSAL MAP EDITOR ---
        if self.handle_editor_event(event):
            return

        # 0. DIALOGUE POPUP HANDLING (Smeltery yms.)
        # Syöte käsitellään keskitetysti GameManager.handle_dialogue_event:issä.
        # Estetään tässä vain muu toiminta dialogin aikana.
        if self.manager.active_dialogue:
            return

        # KARTTA (M) - toggle, ja kartan ollessa auki muut eventit ohitetaan
        from systems import keybinds
        if event.type == pygame.KEYDOWN and keybinds.matches(event.key, "map"):
            self.show_map = not self.show_map
            sound_system.play_sound('click')
            return
        if self.show_map:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.show_map = False
            return
            
        # 0.5 SMELTERY UI HANDLING
        if self.active_smeltery:
            if event.type == pygame.KEYDOWN and (event.key == pygame.K_ESCAPE or keybinds.matches(event.key, "interact")):
                self.active_smeltery = None
                sound_system.play_sound('click')
                return
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Tarkista napit
                for btn in self.smelter_buttons:
                    if btn.rect.collidepoint(event.pos):
                        if btn.action == "close":
                            self.active_smeltery = None
                        else:
                            # Kutsu Smelteryn omaa logiikkaa
                            self.active_smeltery.handle_menu_action(btn.action, self.manager)
                        sound_system.play_sound('click')
                        return
            return # Estä muut toiminnot

        if self.show_pause_menu:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.show_pause_menu = False
                return
            
            # Button handling
            if self.btn_resume.is_clicked(event):
                self.show_pause_menu = False
                sound_system.play_sound('click')
            elif self.btn_hub.is_clicked(event):
                self.next_state = "hub"
                sound_system.play_sound('click')
            elif self.btn_save.is_clicked(event):
                self.manager.save_current_game()
                self.show_pause_menu = False
            elif self.btn_load.is_clicked(event):
                if self.manager.load_saved_game():
                    self.show_pause_menu = False
                    self.next_state = "hub"
            elif self.btn_options.is_clicked(event):
                # Palataan optioneista samaan kohtaan kaupunkia
                # (on_enter kunnioittaa "keep"-spawnia)
                self.manager.city_spawn_point = "keep"
                self.show_pause_menu = False
                self.next_state = "options"
                sound_system.play_sound('click')
            elif self.btn_exit.is_clicked(event):
                self.next_state = "exit"
                sound_system.play_sound('click')
            return
            
        # Mouse Click Interaction
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.show_pause_menu:
                if self._handle_click(event.pos):
                    return
                self._handle_combat_click(event.pos)
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p and CHEAT_MODE:
                self.manager.world_paused = not self.manager.world_paused

            # Commander-toimintavalikko (profiili, skillit, tiimi,
            # sponsorit, maine) suoraan pelin sisältä - palaa kaupunkiin
            if keybinds.matches(event.key, "commander_menu"):
                self.manager.manager_return_state = "muckford_city"
                self.next_state = "manager_menu"
                sound_system.play_sound('click')
                return

            if keybinds.matches(event.key, "interact"):
                # --- KALASTUS: kesken sessio -> E = tartutus ---
                if self.fishing_session:
                    if self.fishing_session.state == "REELING":
                        return  # väsytys hoituu pitämällä E pohjassa
                    hooked = self.fishing_session.hook()
                    if hooked:
                        self.manager.vfx.show_damage(
                            self.player.rect.centerx, self.player.rect.top - 30,
                            "Hooked! HOLD E to reel it in!",
                            color=(255, 210, 80))
                        sound_system.play_sound('click')
                    else:
                        self.manager.vfx.show_damage(
                            self.player.rect.centerx, self.player.rect.top - 30,
                            "Too early - it slipped away...", color=(200, 200, 200))
                        sound_system.play_sound('error')
                    self.fishing_flash = 0
                    return

                # --- KALASTUS: laiturilla E aloittaa ---
                spot = self._nearest_fishing_spot()
                if spot:
                    rod, rod_tier = fishing_system.best_rod(self.manager)
                    if rod is not None:
                        from systems import commander_progression as prog
                        power = fishing_system.skill_power(self.manager)
                        self.fishing_session = fishing_system.FishingSession(
                            power, rod_tier=rod_tier,
                            quick_wrists=prog.has_perk(self.manager, "fishing",
                                                       "quick_wrists"))
                        self.active_fishing_spot = spot
                        self.manager.vfx.show_damage(
                            self.player.rect.centerx, self.player.rect.top - 30,
                            "Cast... wait for the bite.", color=(150, 220, 255))
                        sound_system.play_sound('click')
                        water = self._water_at(spot)
                        if water:
                            water.splash(*spot)
                    else:
                        self.manager.vfx.show_damage(
                            self.player.rect.centerx, self.player.rect.top - 30,
                            "Need a Fishing Rod (Krad's Oddments sells them).",
                            color=(200, 120, 120))
                        sound_system.play_sound('error')
                    return

                # Shanty Yard -portti -> liigavalikko
                gate = getattr(self, "arena_gate", None)
                if gate:
                    door_x = gate.rect.centerx
                    door_y = gate.rect.bottom
                    if math.hypot(self.player.rect.centerx - door_x,
                                  self.player.rect.bottom - door_y) < 110:
                        self.manager.league_return_state = "muckford_city"
                        self.next_state = "league"
                        sound_system.play_sound('click')
                        return

                # Team Barracks -> käveltävä sisätila (punkat, tiimi, kehitys)
                barracks = getattr(self, "barracks", None)
                if barracks:
                    door_x = barracks.rect.centerx
                    door_y = barracks.rect.bottom
                    if math.hypot(self.player.rect.centerx - door_x,
                                  self.player.rect.bottom - door_y) < 110:
                        self.manager.barracks_return_state = "muckford_city"
                        self.next_state = "barracks_interior"
                        sound_system.play_sound('click')
                        return

                # Notice Board -> kylätehtävät
                board = getattr(self, "notice_board", None)
                if board:
                    if math.hypot(self.player.rect.centerx - board.rect.centerx,
                                  self.player.rect.bottom - board.rect.bottom) < 100:
                        self.next_state = "notice_board"
                        sound_system.play_sound('click')
                        return

                # Tarkista ollaanko Tavernan ovella
                if self.tavern_house:
                    # Ovi on vasemmalla alhaalla
                    base_x, base_y = self.tavern_house.image_pos
                    door_off = getattr(self.tavern_house, "door_offset", (self.tavern_house.rect.w//2, self.tavern_house.rect.h))
                    door_x = base_x + door_off[0]
                    door_y = base_y + door_off[1]
                    
                    # Tarkista etäisyys suoraan (pelaajan jalat vs ovi)
                    dist = math.hypot(self.player.rect.centerx - door_x, self.player.rect.bottom - door_y)
                    
                    if dist < 80:
                        self.next_state = "tavern_sunk_cask"
                        sound_system.play_sound('click')
                        return
                        
                # Tarkista ollaanko Blacksmithin ovella
                if self.blacksmith_house:
                    base_x, base_y = self.blacksmith_house.image_pos
                    door_off = getattr(self.blacksmith_house, "door_offset", (self.blacksmith_house.rect.w//2, self.blacksmith_house.rect.h))
                    door_x = base_x + door_off[0]
                    door_y = base_y + door_off[1]
                    
                    # Tarkista etäisyys
                    dist = math.hypot(self.player.rect.centerx - door_x, self.player.rect.bottom - door_y)
                    
                    if dist < 80:
                        self.next_state = "blacksmith_interior"
                        sound_system.play_sound('click')
                        return
                
                # --- KAIVOSTIEN PORTTI (itäreuna, polun korkeudella) ---
                gate = self._mine_gate_rect()
                if self.player.rect.colliderect(gate):
                    if getattr(self.manager, "mine_key_owned", False):
                        self.next_state = "mine_road"
                        sound_system.play_sound('click')
                    else:
                        debt = int(getattr(self.manager, "innkeeper_debt", 0))
                        if debt > 0:
                            msg = f"Locked. Marda holds the key - pay your {debt} silver debt first."
                        else:
                            msg = "Locked. Ask Marda at the Sunk Cask about the key."
                        self.manager.vfx.show_damage(self.player.rect.centerx,
                                                     self.player.rect.top - 30,
                                                     msg, color=(255, 120, 120))
                        sound_system.play_sound('error')
                    return

                # --- METSÄPOLKU (eteläreuna, metsävyöhykkeen kohdalla) ---
                fgate = self._forest_gate_rect()
                if self.player.rect.colliderect(fgate):
                    self.next_state = "forest_excursion"
                    sound_system.play_sound('click')
                    return

                # Market-kojut ENNEN NPC-chattia: kyläläiset kerääntyvät
                # kojujen eteen, eikä asiakas saa jäädä jutun panttivangiksi
                for stall in getattr(self, "market_stalls", []):
                    if self.player.rect.colliderect(stall.rect.inflate(30, 40)):
                        self.manager.pending_shop_id = stall.shop_id
                        self.next_state = "district_shop"
                        sound_system.play_sound('click')
                        return

                # Tarkista NPC interaktio
                for npc in self.npcs:
                    # YHDISTETTY TARKISTUS: Osuma JA logiikka
                    if self.player.rect.colliderect(npc.rect.inflate(60, 60)):
                        # Rekryprospekti - sama palkkausdialogi kuin tavernassa
                        if getattr(npc, "is_prospect", False):
                            self.manager.open_recruit_dialogue(
                                npc, return_state="muckford_city")
                            self.next_state = "dialogue_active"
                            return

                        # Hamo (bounty broker) - oma dialogi
                        if npc is getattr(self, "hamo", None) or npc.name == "Hamo":
                            self.next_state = "dialogue:hamo"
                            return

                        # Bram - Tier 0 -liigamanagerin dialogi
                        if npc is getattr(self, "bram", None):
                            self.next_state = "dialogue:dwarf_league_manager"
                            return

                        # Rivaalitiimin gladiaattori - asenteellinen dialogi
                        if getattr(npc, "rival_info", None):
                            self.manager.open_rival_dialogue(npc.rival_info,
                                                             return_state="muckford_city")
                            self.next_state = "dialogue_active"
                            return

                        # Farmer Gus interaction
                        if npc == self.farmer_gus or npc.name == "Farmer Gus":
                            self.manager.open_patron_dialogue(npc, return_state="muckford_city")
                            self.next_state = "dialogue_active"
                            return
                        
                        # Normal Patron interaction
                        self.manager.open_patron_dialogue(npc, return_state="muckford_city")
                        self.next_state = "dialogue_active"
                        return
                
                # 3. Lehmän lypsäminen
                for cow in self.animals:
                    if self.player.rect.colliderect(cow.rect.inflate(40, 40)):
                        if isinstance(cow, Cow):
                            self._interact_cow(cow)
                        elif isinstance(cow, Chicken):
                            self._pet_chicken(cow)
                        return

                # 4. Lannan keräys ja vienti
                # Keräys
                for prop in self.arena.props:
                    if self._try_interact_prop(prop, check_collision=True):
                        return # Jos interaktio onnistui, lopetetaan tähän

                # 5. Kaupungintalo (Sponsors)
                for prop in self.arena.props:
                    if isinstance(prop, TownHall) and self.player.rect.colliderect(prop.rect.inflate(40, 40)):
                        self.next_state = "sponsors"
                        sound_system.play_sound('click')
                        return
                        
                # 6. Omenapuu (Ravistus)
                for prop in self.arena.props:
                    if isinstance(prop, AppleTree) and self.player.rect.colliderect(prop.rect.inflate(40, 40)):
                        prop.shake(self.manager)
                        return

                # 8. Kerättävät (Omenat, Munat)
                # Nämä ovat propseja, joten ne käsitellään _try_interact_prop -metodissa, 
                # mutta varmistetaan että ne on lisätty sinne.
                # (Apple ja Egg lisätään arena.props listaan kun ne spawnataan)

            # --- PLAYER ABILITIES (1-5) ---
            if keybinds.matches(event.key, "spell_1"): self._use_player_ability("spell1")
            if keybinds.matches(event.key, "spell_2"): self._use_player_ability("spell2")
            if keybinds.matches(event.key, "spell_3"): self._use_player_ability("spell3")
            if event.key == pygame.K_4: self._use_player_ability("spell4")
            if keybinds.matches(event.key, "spell_5"): self._use_player_ability("spell5")
            if keybinds.matches(event.key, "spell_6"): self._use_player_ability("spell6")
            if keybinds.matches(event.key, "usable_1") and event.key != pygame.K_4:
                self._use_player_ability("usable")
            if keybinds.matches(event.key, "usable_2"): self._use_player_ability("usable2")

            # --- COMBAT CONTROLS ---
            if keybinds.matches(event.key, "dash"):
                mx, my = pygame.mouse.get_pos()
                wx = mx + self.camera_x
                wy = my + self.camera_y
                dx = wx - self.player.rect.centerx
                dy = wy - self.player.rect.centery
                self.player.perform_dash(dx, dy)

            if event.key == pygame.K_ESCAPE:
                self.show_pause_menu = True
                sound_system.play_sound('click')

    def update(self):
        super().update() # BaseMenu update (editor)
        
        if self.show_pause_menu or self.manager.show_inventory or self.manager.active_dialogue:
            return

        # 1. Pelaajan logiikka (MANUAALINEN LIIKE)
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        speed = 4.0 # Pelaajan nopeus kaupungissa
        
        # Shift = sprintti (kuluttaa staminaa VAIN liikkuessa).
        from systems import keybinds as _kb
        wants_sprint = _kb.pressed(keys, "sprint")

        # Estä manuaalinen liike jos dash on käynnissä (Commander hoitaa sen itse)
        if not self.player.is_dashing:
            if _kb.pressed(keys, "move_up"): dy = -speed
            if _kb.pressed(keys, "move_down"): dy = speed
            if _kb.pressed(keys, "move_left"): dx = -speed
            if _kb.pressed(keys, "move_right"): dx = speed

            # Pelkkä SHIFT ilman WASD: juokse hiiren osoittamaan suuntaan
            if wants_sprint and dx == 0 and dy == 0:
                mx, my = pygame.mouse.get_pos()
                wx = mx + self.camera_x - self.player.rect.centerx
                wy = my + self.camera_y - self.player.rect.centery
                dist = math.hypot(wx, wy)
                if dist > 40:  # pieni kuollut alue ettei tärise paikallaan
                    dx = (wx / dist) * speed
                    dy = (wy / dist) * speed

        # BUGIKORJAUS: sprintti kulutti staminaa vaikka hahmo seisoi
        # paikallaan - sprintataan vain kun oikeasti liikutaan
        moving = (dx != 0 or dy != 0)
        self.player.set_sprinting(wants_sprint and moving)
        if self.player.is_sprinting and self.player.current_stamina > 0.5:
            dx *= 1.5
            dy *= 1.5
        
        if dx != 0 or dy != 0:
            # Liikkuminen keskeyttää kalastuksen
            if self.fishing_session:
                self.fishing_session = None
                self.fishing_flash = 0
                self.manager.vfx.show_damage(
                    self.player.rect.centerx, self.player.rect.top - 30,
                    "Reeled in.", color=(180, 180, 180))
            self.player.animation_state = "run"
            self.player.facing_right = (dx > 0) if dx != 0 else self.player.facing_right
            
            # Liiku ja tarkista törmäykset
            self.player.rect.x += dx
            for obs in self.arena.obstacles:
                if self.player.rect.colliderect(obs.rect):
                    if dx > 0: self.player.rect.right = obs.rect.left
                    if dx < 0: self.player.rect.left = obs.rect.right
            
            self.player.rect.y += dy
            for obs in self.arena.obstacles:
                if self.player.rect.colliderect(obs.rect):
                    if dy > 0: self.player.rect.bottom = obs.rect.top
                    if dy < 0: self.player.rect.top = obs.rect.bottom
            
            # Rajoita kartalle
            self.player.rect.clamp_ip(pygame.Rect(0, 0, self.arena.width, self.arena.height))
        else:
            self.player.animation_state = "idle"

        # Päivitä pelaajan tilat (cooldowns, mana regen) ilman AI:ta
        self.player.update(self.arena.obstacles, self.manager)

        # Palkatut prospektit pois kadulta (siirtyivät tiimiin)
        self._cleanup_hired_prospects()

        # Kerätään kaikki yksiköt listaan NPC-logiikkaa varten.
        # BUGIKORJAUS: raid-rotat puuttuivat listasta -> kyläläiset eivät
        # pelänneet eivätkä vartijat puolustautuneet raidin aikana.
        living_rats = [r for r in self.raid_rats if not r.is_dead]
        all_units = [self.player] + self.npcs + self.animals + living_rats

        # Päivitä NPC:t (Animaatio ja fysiikka)
        for npc in self.npcs:
            if self.manager.world_paused: continue
            # Esiintyvä bardi pysyy lavalla (AI veti hänet töihin -> ei
            # koskaan näkynyt lavalla vaikka banneri ja musiikki tulivat)
            if npc is getattr(self, "_event_bard", None) and \
                    getattr(npc, "sim_state", "") == "PERFORMING":
                npc.animation_state = "idle"
                npc.update(self.arena.obstacles, self.manager)
                continue
            # Kutsutaan run_combat_ai, jotta VillagerAI toimii (maitotilat, lanta, jne.)
            npc.run_combat_ai(all_units, self.arena.obstacles, self.manager)
            npc.update(self.arena.obstacles, self.manager)
            
        # Päivitä Eläimet
        for cow in self.animals:
            if self.manager.world_paused: continue
            cow.update(self.arena.obstacles, self.manager)

        # Päivitä Propit (Lanta, Ruoho yms.)
        # Tämä on tärkeää ruohon takaisinkasvulle ja lannan efekteille
        # (BUGIKORJAUS: manager meni aiemmin obstacles-parametriin, jolloin
        #  esim. romukasojen E-keräys ja ruohoäänet eivät toimineet)
        for p in self.arena.props:
            if hasattr(p, "update"): p.update(None, self.manager)

        # Munien kuoriutuminen poikasiksi
        self._update_eggs()

        # Höyhen-cooldownit
        for animal in self.animals:
            cd = getattr(animal, "_feather_cd", 0)
            if cd > 0:
                animal._feather_cd = cd - 1

        # --- KALASTUSSESSION ETENEMINEN ---
        if self.fishing_session:
            session = self.fishing_session
            if session.state == "REELING":
                # Väsytys: E pohjassa kelaa, hellitys lepuuttaa siimaa
                from systems import keybinds as _kb
                pressed = _kb.pressed(pygame.key.get_pressed(), "interact")
                result = session.reel(pressed)
                spot = self.active_fishing_spot
                if result == "caught":
                    self._resolve_catch(session.caught, spot)
                elif result == "snapped":
                    self.manager.vfx.show_damage(
                        self.player.rect.centerx, self.player.rect.top - 30,
                        "The line SNAPPED!", color=(255, 110, 90))
                    sound_system.play_sound('error')
            else:
                event_name = session.update()
                if event_name == "bite":
                    self.fishing_flash = session.timer
                    sound_system.play_sound('click')
                    spot = self.active_fishing_spot
                    water = self._water_at(spot)
                    if water and spot:
                        water.splash(*spot)
                elif event_name == "escaped":
                    self.fishing_flash = 0
                    self.manager.vfx.show_damage(
                        self.player.rect.centerx, self.player.rect.top - 30,
                        "It got away...", color=(200, 200, 200))
        if self.fishing_flash > 0:
            self.fishing_flash -= 1

        # Maailmankello ja sää etenevät kaupungissa
        if not self.manager.world_paused:
            self.manager.world_clock.update()
            self._update_raids()

        # Pelaajan kaatuminen kaupungissa (esim. raidissa): raahataan turvaan
        if self.player.is_dead:
            self.player.is_dead = False
            self.player.current_hp = max(1, int(self.player.max_hp * 0.3))
            self.player.rect.center = (self.arena.width // 2, self.arena.height // 2)
            self.manager.vfx.show_damage(self.player.rect.centerx, self.player.rect.top - 30,
                                         "You were dragged to safety...", color=(255, 120, 120))
            
        for p in self.arena.floor_props:
            if hasattr(p, "update"): p.update(manager=self.manager)
            
        # Päivitä Sulatot (Prosessointi)
        for p in self.arena.props:
            if isinstance(p, Smeltery):
                if p.wood_stored > 0 and p.scrap_stored > 0:
                    p.process_timer += 1
                    if p.process_timer >= p.process_time:
                        p.process_timer = 0
                        p.wood_stored -= 1
                        p.scrap_stored -= 1
                        p.bars_ready += 1
                        self.manager.vfx.create_smoke(p.rect.centerx, p.rect.top) # Savua piipusta
            
            # Päivitä Kanalat (Hautominen)
            if isinstance(p, ChickenCoop):
                p.update(manager=self.manager)

        # Päivitä kaupunkisimulaatio (Kävely, juttelu, taloissa vierailu)
        if not self.manager.world_paused:
            self._update_simulation()
            self._update_ambient_event()

        # 3. VFX
        self.vfx.update(self.manager)
        self.manager.vfx.update()
        
        # 4. Kamera
        self._update_camera()

    def _use_player_ability(self, slot_name):
        """Käyttää kykyä hiiren osoittamaan kohtaan/kohteeseen."""
        item = self.player.equipment.get(slot_name)
        if not item: return

        # Tarkista cooldown
        if self.player.spell_cooldowns.get(slot_name, 0) > 0:
            sound_system.play_sound("error")
            return

        # Etsi kohde hiiren alta
        mx, my = pygame.mouse.get_pos()
        wx = mx + self.camera_x
        wy = my + self.camera_y
        
        # Käänny kohti kohdetta
        if wx > self.player.rect.centerx:
            self.player.facing_right = True
        else:
            self.player.facing_right = False
            
        mouse_rect = pygame.Rect(wx - 5, wy - 5, 10, 10)
        
        target = None
        # Priorisoi viholliset/NPC:t
        all_targets = self.npcs + self.animals
        for u in all_targets:
            if u.rect.colliderect(mouse_rect):
                target = u
                break
        
        # Jos ei kohdetta, käytä "dummy" kohdetta sijainnilla (AOE spelleille)
        if not target:
            # Luodaan väliaikainen objekti sijainnilla
            class DummyTarget:
                def __init__(self, x, y): self.rect = pygame.Rect(x, y, 1, 1); self.is_dead = False
            target = DummyTarget(wx, wy)

        # Yritä käyttää
        if hasattr(item, "cast"):
            if item.cast(self.player, target, self.manager):
                try:
                    from systems import commander_progression as _prog
                    _prog.on_player_spell_cast(self.manager, item)
                except Exception:
                    pass
                # Aseta cooldown
                cd = getattr(item, "cooldown_max", 60)
                self.player.spell_cooldowns[slot_name] = cd
                # Animaatio
                self.player.animation_state = "attack"
                self.player.attack_cooldown = 20

    def _update_camera(self):
        target_x = self.player.rect.centerx - SCREEN_WIDTH // 2
        target_y = self.player.rect.centery - SCREEN_HEIGHT // 2
        
        # Clamp
        self.camera_x = max(0, min(target_x, self.arena.width - SCREEN_WIDTH))
        self.camera_y = max(0, min(target_y, self.arena.height - SCREEN_HEIGHT))
        
        # Sync to manager (for HUD transparency logic)
        self.manager.camera_x = self.camera_x
        self.manager.camera_y = self.camera_y

    def _npc_speak(self, npc, topic):
        lines = DIALOGUE_TOPICS.get(topic, DIALOGUE_TOPICS["casual"])
        text = self.rng.choice(lines)
        self.manager.vfx.create_speech_bubble(npc, text, duration=120)
        
        if self.rng.random() < 0.3:
            s_id = self.rng.randint(1, 4)
            sound_system.play_sound(f"laugh_loop_{s_id}")
        else:
            talk_id = self.rng.randint(1, 8)
            sound_system.play_sound(f"talking_loop_{talk_id}")

    def _update_ambient_event(self):
        """Satunnainen ambient-tapahtuma: bardi soittaa lavalla, kyläläiset
        kokoontuvat. Tekee kaupungista elävän tuntuisen."""
        if not hasattr(self, "_event_state"):
            self._event_state = "idle"
            self._event_timer = self.rng.randint(600, 1800)  # 10-30s ennen ekaa
            self._event_bard = None
            self._event_banner = 0

        stage = getattr(self, "stage", None)
        if stage is None:
            return

        self._event_timer -= 1
        if self._event_banner > 0:
            self._event_banner -= 1

        if self._event_state == "idle":
            if self._event_timer <= 0:
                self._start_bard_performance(stage)
        elif self._event_state == "bard":
            if self._event_timer % 18 == 0:
                sx = stage.rect.centerx + self.rng.randint(-40, 40)
                sy = stage.image_pos[1] + 40
                self.manager.vfx.create_musical_note(sx, sy)
            if self._event_timer <= 0:
                self._end_bard_performance()

    def _start_bard_performance(self, stage):
        candidates = [n for n in self.npcs if hasattr(n, "sim_state")
                      and n is not getattr(self, "bram", None)
                      and not getattr(n, "rival_info", None)
                      and getattr(n, "sim_state", "") != "INSIDE"]
        if not candidates:
            self._event_timer = self.rng.randint(600, 1800)
            return
        bard = self.rng.choice(candidates)
        self._event_bard = bard
        bard.sim_state = "PERFORMING"
        bard.rect.centerx = stage.rect.centerx
        bard.rect.bottom = stage.image_pos[1] + stage.image.get_height() - 20
        bard.animation_state = "idle"
        self._event_state = "bard"
        self._event_timer = self.rng.randint(600, 1200)  # 10-20s esitys
        self._event_banner = 240
        try:
            sound_system.play_sound("talking_loop_1")
        except Exception:
            pass

    def _end_bard_performance(self):
        if self._event_bard is not None:
            if getattr(self._event_bard, "sim_state", None) == "PERFORMING":
                self._event_bard.sim_state = "IDLE"
                self._event_bard.sim_timer = 60
            self._event_bard = None
        self._event_state = "idle"
        self._event_timer = self.rng.randint(1800, 3600)  # 30-60s taukoa

    def _update_simulation(self):
        """Hoitaa kaupungin elämän: kävelyn, juttelun ja taloissa vierailun."""
        for npc in self.npcs:
            # Skipataan NPC:t joilla ei ole simulaatiotilaa (esim. Farmer Gus)
            if not hasattr(npc, "sim_state"):
                continue

            if npc.sim_state == "INSIDE":
                npc.sim_timer -= 1
                if npc.sim_timer <= 0:
                    # Tule ulos
                    npc.sim_state = "IDLE"
                    npc.sim_timer = 60
                continue

            # Jos ollaan ulkona, piirretään normaalisti
            if npc.sim_state == "IDLE":
                npc.animation_state = "idle"
                npc.sim_timer -= 1
                if npc.sim_timer <= 0:
                    # Valitse uusi toiminto
                    action = self.rng.choice(["WALK", "WALK", "WALK", "ENTER", "TALK"])
                    
                    if action == "WALK":
                        # Arvo satunnainen kohde
                        if self.gathering_spots and self.rng.random() < 0.7:
                            # Mene kokoontumispaikalle (70% todennäköisyys) - Suosii toria ja rakennuksia
                            spot = self.rng.choice(self.gathering_spots)
                            tx = spot[0] + self.rng.randint(-30, 30)
                            ty = spot[1] + self.rng.randint(-30, 30)
                        else:
                            tx = self.rng.randint(100, self.arena.width - 100)
                            ty = self.rng.randint(100, self.arena.height - 100)
                        npc.sim_target = (tx, ty)
                        npc.sim_state = "WALK"
                    
                    elif action == "ENTER" and self.buildings:
                        # Mene lähimpään tai satunnaiseen taloon
                        target_house = self.rng.choice(self.buildings)
                        npc.sim_target = target_house
                        npc.sim_state = "ENTERING"
                        
                    elif action == "TALK":
                        # Etsi lähellä oleva kaveri
                        partner = None
                        for other in self.npcs:
                            if other != npc and getattr(other, "sim_state", "") == "IDLE":
                                dist = math.hypot(other.rect.centerx - npc.rect.centerx, other.rect.centery - npc.rect.centery)
                                if dist < 150:
                                    partner = other
                                    break
                        
                        if partner:
                            # Setup conversation
                            total_lines = self.rng.randint(2, 5)
                            duration = total_lines * 100 + 40
                            topic = self.rng.choice(list(DIALOGUE_TOPICS.keys()))
                            
                            npc.sim_state = "TALK"
                            npc.sim_partner = partner
                            npc.sim_timer = duration
                            npc.sim_role = "initiator"
                            npc.sim_total_lines = total_lines
                            npc.sim_lines_spoken = 1
                            npc.sim_topic = topic
                            
                            partner.sim_state = "TALK"
                            partner.sim_partner = npc
                            partner.sim_timer = duration
                            partner.sim_role = "listener"
                            
                            # Käänny toisiaan kohti
                            npc.facing_right = partner.rect.centerx > npc.rect.centerx
                            partner.facing_right = npc.rect.centerx > partner.rect.centerx
                            
                            # Aloita keskustelu heti
                            self._npc_speak(npc, topic)
                        else:
                            npc.sim_timer = 30 # Ei löytynyt, odota hetki

            elif npc.sim_state == "WALK" or npc.sim_state == "ENTERING":
                npc.animation_state = "run"
                tx, ty = npc.sim_target
                dx = tx - npc.rect.centerx
                dy = ty - npc.rect.centery
                dist = math.hypot(dx, dy)
                
                if dist < 10:
                    # Perillä
                    if npc.sim_state == "ENTERING":
                        npc.sim_state = "INSIDE"
                        npc.sim_timer = self.rng.randint(300, 1200) # 5-20 sekuntia sisällä
                    else:
                        npc.sim_state = "IDLE"
                        npc.sim_timer = self.rng.randint(60, 180)
                else:
                    # Liiku
                    speed = 1.2 # Hidastettu kävelyvauhti
                    move_x = (dx / dist) * speed
                    move_y = (dy / dist) * speed
                    npc.rect.x += move_x
                    npc.rect.y += move_y
                    npc.facing_right = move_x > 0
                    
                    # Yksinkertainen törmäys seiniin (liukuu)
                    for obs in self.arena.obstacles:
                        if npc.rect.colliderect(obs.rect):
                            # Peruuta liike ja vaihda tilaa
                            npc.rect.x -= move_x
                            npc.rect.y -= move_y
                            npc.sim_state = "IDLE"
                            npc.sim_timer = 30
                            break

            elif npc.sim_state == "TALK":
                npc.animation_state = "idle"
                npc.sim_timer -= 1
                
                # Vain aloittaja ohjaa keskustelun kulkua
                if getattr(npc, "sim_role", "") == "initiator":
                    if not npc.sim_partner or npc.sim_partner not in self.npcs or npc.sim_partner.sim_state != "TALK":
                        npc.sim_timer = 0 # Lopeta jos kaveri lähti
                    else:
                        # Puhu vuorotellen (joka 100. frame)
                        # Ensimmäinen puhui jo alussa.
                        # Lasketaan aika alusta: duration - sim_timer
                        time_elapsed = (npc.sim_total_lines * 100 + 40) - npc.sim_timer
                        
                        if time_elapsed > 0 and time_elapsed % 100 == 0:
                             if npc.sim_lines_spoken < npc.sim_total_lines:
                                 speaker = npc.sim_partner if (npc.sim_lines_spoken % 2 != 0) else npc
                                 self._npc_speak(speaker, npc.sim_topic)
                                 npc.sim_lines_spoken += 1

                if npc.sim_timer <= 0:
                    npc.sim_state = "IDLE"
                    npc.sim_timer = self.rng.randint(30, 90)

    def _equip_from_bag(self, item):
        if item in self.manager.equipment_bag:
            self.manager.equipment_bag.remove(item)
            
            # Determine slot
            slot = getattr(item, "slot_type", "main_hand")
            
            # Equip
            old_item = self.player.equip_item_to_slot(slot, item)
            
            # Check if equip failed (returns same item)
            if old_item is item:
                # Failed (e.g. requirements)
                self.manager.equipment_bag.append(item)
                sound_system.play_sound('error')
            else:
                # Success
                if old_item:
                    self.manager.equipment_bag.append(old_item)
                sound_system.play_sound('recruit') # Equip sound

    def _unequip_slot(self, slot):
        item = self.player.unequip_slot(slot)
        if item:
            self.manager.equipment_bag.append(item)
            sound_system.play_sound('click')

    def _draw_hud(self, screen):
        """Piirtää pikavalikon (1-5) ruudun alareunaan."""
        slot_size = 50
        gap = 10
        slots = ["spell1", "spell2", "spell3", "usable", "usable2"]
        total_w = len(slots) * slot_size + (len(slots) - 1) * gap
        start_x = (SCREEN_WIDTH - total_w) // 2
        y = SCREEN_HEIGHT - 80
        
        mouse_pos = pygame.mouse.get_pos()
        
        for i, slot_name in enumerate(slots):
            x = start_x + i * (slot_size + gap)
            item = self.player.equipment.get(slot_name)
            
            # Tausta
            is_hover = pygame.Rect(x, y, slot_size, slot_size).collidepoint(mouse_pos)
            draw_item_slot_background(screen, x, y, slot_size, item, is_hover)
            
            # Numero
            draw_text(str(i + 1), font_small, (150, 150, 150), screen, x + 2, y + 2)
            
            # Item icon
            if item:
                item.draw_card_icon(screen, x, y, slot_size)
                # Cooldown overlay
                cd = self.player.spell_cooldowns.get(slot_name, 0)
                if cd > 0:
                    max_cd = getattr(item, "cooldown_max", 60)
                    pct = cd / max(1, max_cd)
                    h = int(slot_size * pct)
                    s = pygame.Surface((slot_size, h), pygame.SRCALPHA)
                    s.fill((0, 0, 0, 150))
                    screen.blit(s, (x, y + slot_size - h))

    def _head_anchor(self, unit):
        """Promptin ankkuri hahmon pään YLLE (rect on jalkojen hitbox,
        kuva on korkeampi - vanha rect.top-20 osui vatsan kohdalle)."""
        img_h = unit.image.get_height() if getattr(unit, "image", None) else \
            unit.rect.height
        return unit.rect.centerx, unit.rect.bottom - img_h - 22

    def _queue_prompt(self, x, y, key, label=None):
        """Kerää interaktiopromptit; framen lopussa piirretään vain
        pelaajaa LÄHIN (ennen: monta päällekkäistä kuvaketta)."""
        self._prompt_queue.append((x, y, key, label))

    def _flush_prompts(self, screen, offset):
        if not self._prompt_queue:
            return
        px, py = self.player.rect.center
        x, y, key, label = min(
            self._prompt_queue,
            key=lambda p: (p[0] - px) ** 2 + (p[1] - py) ** 2)
        self.manager._draw_floating_prompt(screen, x, y, key, offset, label)
        self._prompt_queue = []

    def draw(self, screen):
        screen.fill((20, 20, 25))
        offset = (self.camera_x, self.camera_y)
        self._prompt_queue = []
        
        # 1. Tausta
        self.arena.draw_background(screen, offset)
        
        # 2a. Litteät propit (pellot, palstat) lattiapassissa - eivät
        # koskaan peitä hahmoja (BUGIKORJAUS: CropPlot piirtyi heron päälle)
        flats = [p for p in self.arena.props if getattr(p, "is_flat", False)]
        for obj in flats:
            if hasattr(obj, "draw_on_screen"):
                obj.draw_on_screen(screen, offset)

        # 2. Objektit ja Hahmot (Y-Sort)
        renderables = [p for p in self.arena.props
                       if not getattr(p, "is_flat", False)] \
            + self.npcs + self.animals + self.raid_rats + [self.player]
        renderables.sort(key=lambda x: x.rect.bottom)
        
        for obj in renderables:
            # Älä piirrä jos "sisällä" talossa
            if hasattr(obj, "sim_state") and obj.sim_state == "INSIDE":
                continue
                
            if hasattr(obj, "draw_on_screen"):
                obj.draw_on_screen(screen, offset)
            elif hasattr(obj, "image"):
                screen.blit(obj.image, (obj.rect.x - offset[0], obj.rect.y - offset[1]))

        # 3. VFX
        self.vfx.draw_top(screen, offset)
        self.manager.vfx.draw_top(screen, offset)

        # 3.5 SÄÄ JA VUOROKAUDENAIKA (maailman päälle, HUDin alle)
        self.manager.world_clock.draw_overlays(screen)

        # --- POI ICONS (seurattavat merkit: quest, kauppa, areena) ---
        self._draw_poi_icons(screen, offset)

        # Ambient-eventin banneri (bardiesitys)
        if getattr(self, "_event_banner", 0) > 0:
            msg = "The bard takes the stage!"
            surf = font_title.render(msg, True, (255, 220, 120))
            sh = font_title.render(msg, True, (0, 0, 0))
            x = SCREEN_WIDTH // 2 - surf.get_width() // 2
            screen.blit(sh, (x + 2, 92))
            screen.blit(surf, (x, 90))

        # Mouse Hover Logic
        mouse_pos = pygame.mouse.get_pos()
        self._draw_hover_info(screen, offset, mouse_pos)
        
        # --- QUEST HUD (Top Left) ---
        if quest_manager:
            q = quest_manager.get_quest("quest_manure_cleanup")
            if q and q.status == "active":
                cleaned = q.progress
                required = q.definition.required_amount
                
                # Tausta
                panel_w, panel_h = 250, 60
                draw_panel(screen, 20, 20, panel_w, panel_h, color=(30, 30, 40, 200), border_color=GOLD_COLOR)
                
                draw_text("QUEST: Clean Manure", font_small, GOLD_COLOR, screen, 35, 30)
                draw_text(f"Progress: {cleaned}/{required}", font_main, WHITE, screen, 35, 50)
            elif q and q.status == "completed":
                panel_w, panel_h = 250, 60
                draw_panel(screen, 20, 20, panel_w, panel_h, color=(30, 50, 30, 200), border_color=GREEN)
                
                draw_text("QUEST COMPLETE!", font_small, GREEN, screen, 35, 30)
                draw_text("Return to Gus", font_main, WHITE, screen, 35, 50)
        
        # 4. UI Prompts
        # Taverna
        if self.tavern_house:
            base_x, base_y = self.tavern_house.image_pos
            door_off = getattr(self.tavern_house, "door_offset", (self.tavern_house.rect.w//2, self.tavern_house.rect.h))
            door_x = base_x + door_off[0]
            door_y = base_y + door_off[1]
            
            # Tarkista etäisyys
            dist = math.hypot(self.player.rect.centerx - door_x, self.player.rect.bottom - door_y)
            if dist < 100:
                self._queue_prompt(door_x, door_y - 40, "E", "Enter Tavern")
                
        # Blacksmith
        if self.blacksmith_house:
            base_x, base_y = self.blacksmith_house.image_pos
            door_off = getattr(self.blacksmith_house, "door_offset", (self.blacksmith_house.rect.w//2, self.blacksmith_house.rect.h))
            door_x = base_x + door_off[0]
            door_y = base_y + door_off[1]
            
            dist = math.hypot(self.player.rect.centerx - door_x, self.player.rect.bottom - door_y)
            if dist < 100:
                self._queue_prompt(door_x, door_y - 40, "E", "Enter Smithy")

        # Kalastus: koho vedessä + prompt laiturilla
        spot = self.active_fishing_spot if self.fishing_session \
            else self._nearest_fishing_spot()
        if spot:
            if self.fishing_session:
                # Koho keinuu; nykäisyssä painuu pinnan alle + "!"
                t = pygame.time.get_ticks() * 0.004
                bob_y = spot[1] + math.sin(t) * 3
                biting = self.fishing_session.state == "BITE"
                if biting:
                    bob_y += 7
                bx = spot[0] - offset[0]
                by = int(bob_y - offset[1])
                pygame.draw.line(screen, (230, 230, 235),
                                 (self.player.rect.centerx - offset[0],
                                  self.player.rect.centery - 18 - offset[1]),
                                 (bx, by - 4), 1)
                pygame.draw.circle(screen, (210, 60, 50), (bx, by), 5)
                pygame.draw.circle(screen, (235, 235, 235), (bx, by - 3), 3)
                if biting:
                    flash = (pygame.time.get_ticks() // 120) % 2 == 0
                    if flash:
                        draw_text("!", font_title, (255, 210, 80), screen,
                                  bx - 6, by - 58)
                    self.manager._draw_floating_prompt(
                        screen, self.player.rect.centerx,
                        self.player.rect.top - 26, "E", "HOOK IT!")

                # Väsytysvaihe: kireys- ja kelausmittarit pelaajan yllä
                if self.fishing_session.state == "REELING":
                    s = self.fishing_session
                    px = self.player.rect.centerx - offset[0] - 60
                    py = self.player.rect.top - offset[1] - 64
                    # Kireys (punainen, 100 = poikki)
                    pygame.draw.rect(screen, (30, 30, 34), (px, py, 120, 10),
                                     border_radius=4)
                    tension_col = (230, 70, 60) if s.tension > 75 else \
                        (225, 160, 70)
                    pygame.draw.rect(screen, tension_col,
                                     (px, py, int(120 * s.tension / 100), 10),
                                     border_radius=4)
                    # Kelaus (vihreä, 100 = saalis ylös)
                    pygame.draw.rect(screen, (30, 30, 34),
                                     (px, py + 14, 120, 10), border_radius=4)
                    pygame.draw.rect(screen, (110, 210, 120),
                                     (px, py + 14,
                                      int(120 * s.progress / 100), 10),
                                     border_radius=4)
                    fish_name = (s.pending_fish or {}).get("name", "???")
                    draw_text(f"{fish_name} fights!  HOLD E - ease off before it snaps",
                              font_small, (235, 225, 200), screen,
                              px - 70, py - 22)
            else:
                rod, rod_tier = fishing_system.best_rod(self.manager)
                lvl = fishing_system.get_progress(self.manager)["level"]
                label = (f"Fish (Lv {lvl}, T{rod_tier} rod)" if rod
                         else "Fish (need rod)")
                self._queue_prompt(spot[0], spot[1] - 36, "E", label)

        # NPC Prompts (Chat)
        for npc in self.npcs:
            if getattr(npc, "ai_controller", None) and getattr(npc.ai_controller, "state", 0) == "INSIDE":
                continue
                
            if self.player.rect.colliderect(npc.rect.inflate(60, 60)):
                ux = npc.rect.centerx - offset[0]
                uy = npc.rect.top - offset[1]
                self._queue_prompt(*self._head_anchor(npc), "E", "Chat")

        # Farm Prompts
        for cow in self.animals:
            if self.player.rect.colliderect(cow.rect.inflate(40, 40)):
                if isinstance(cow, Cow):
                    txt = "Milk" if cow.milk_ready else "Pet"
                else:
                    txt = "Pet"
                self._queue_prompt(*self._head_anchor(cow), "E", txt)
        
        # Muut propit
        for prop in self.arena.props:
            if self.player.rect.colliderect(prop.rect.inflate(40, 40)):
                if isinstance(prop, ManurePile):
                    count = self.manager.inventory.get("Manure", 0)
                    if count > 0:
                        self._queue_prompt(prop.rect.centerx, prop.rect.top - 20, "E", f"Dump {count}")
                elif isinstance(prop, FarmStorage):
                    self._queue_prompt(prop.rect.centerx, prop.rect.top - 20, "E", "Storage")
                elif isinstance(prop, TownHall):
                    self._queue_prompt(prop.rect.centerx, prop.rect.top - 20, "E", "Town Hall")
                elif prop is getattr(self, "arena_gate", None):
                    self._queue_prompt(prop.rect.centerx, prop.rect.bottom + 30, "E", "Enter Shanty Yard (League)")
                elif prop is getattr(self, "barracks", None):
                    self._queue_prompt(prop.rect.centerx, prop.rect.bottom + 30, "E", "Team Quarters")
                elif prop is getattr(self, "notice_board", None):
                    self._queue_prompt(prop.rect.centerx, prop.rect.bottom + 20, "E", "Notice Board")
                elif isinstance(prop, MarketStall):
                    self._queue_prompt(prop.rect.centerx, prop.rect.top - 20, "E", prop.shop["name"])
                elif isinstance(prop, MuckfordStall):
                    self._queue_prompt(prop.rect.centerx, prop.rect.top - 20, "E", "Trade")
                elif isinstance(prop, AppleTree):
                    self._queue_prompt(prop.rect.centerx, prop.rect.top - 20, "E", "Shake")
                elif isinstance(prop, Smeltery):
                    self._queue_prompt(prop.rect.centerx, prop.rect.top - 20, "E", "Smeltery")
                elif isinstance(prop, ChickenCoop):
                    self._queue_prompt(prop.rect.centerx, prop.rect.top - 20, "E", "Coop")
                elif isinstance(prop, Well):
                    self._queue_prompt(prop.rect.centerx, prop.rect.top - 20, "E", "Fetch Water")
                elif isinstance(prop, (MuckfordTree, ScrapPile, ScrapPileBig)) and not getattr(prop, "is_empty", False):
                    label = "Chop" if isinstance(prop, MuckfordTree) else "Scavenge"
                    self._queue_prompt(prop.rect.centerx, prop.rect.top - 20, "E", label)
                elif isinstance(prop, (Apple, Egg, Manure)):
                    self._queue_prompt(prop.rect.centerx, prop.rect.top - 20, "E", "Pick Up")

        # Kaivostien portin prompt
        gate = self._mine_gate_rect()
        if self.player.rect.colliderect(gate.inflate(60, 60)):
            label = "Mine Road" if getattr(self.manager, "mine_key_owned", False) else "Mine Road (Locked)"
            self._queue_prompt(gate.centerx, gate.top - 20, "E", label)

        # Metsäpolun aukon prompt
        fgate = self._forest_gate_rect()
        if self.player.rect.colliderect(fgate.inflate(60, 60)):
            self._queue_prompt(fgate.centerx, fgate.top - 20, "E", "Forest Trail")

        # Rekryprospektit: kultatimantti pään päällä + prompt lähietäisyydellä
        for unit in getattr(self, "prospects", []):
            hx, hy = self._head_anchor(unit)
            px = hx - offset[0]
            py = hy - offset[1] + 8
            if -60 < px < SCREEN_WIDTH + 60 and -60 < py < SCREEN_HEIGHT + 60:
                pts = [(px, py - 7), (px + 5, py), (px, py + 7), (px - 5, py)]
                pygame.draw.polygon(screen, (255, 215, 0), pts)
                pygame.draw.polygon(screen, (120, 90, 20), pts, 1)
            if self.player.rect.colliderect(unit.rect.inflate(60, 60)):
                self._queue_prompt(hx, hy, "E", f"Recruit: {unit.name}")

        # Piirrä pelaajaa lähin interaktioprompti (vain yksi kerrallaan)
        self._flush_prompts(screen, offset)

        # Kello, kalenteri ja sää (yläkeskellä - quest-paneeli vie
        # oikean yläkulman, joten kello ei saa jäädä sen alle)
        self.manager.world_clock.draw_hud(screen, font_small,
                                          x=SCREEN_WIDTH // 2 - 120)

        # --- RAID-BANNERIT ---
        if self.raid_state == "warning":
            if (self.raid_banner_timer // 15) % 2 == 0:  # Vilkkuu
                draw_text("!!! RAT RAID INCOMING !!!", font_title, (255, 80, 80),
                          screen, SCREEN_WIDTH // 2 - 220, 100)
        elif self.raid_state == "active":
            alive = sum(1 for r in self.raid_rats if not r.is_dead)
            draw_text(f"RAT RAID! Defend the village! ({alive} left)", font_main,
                      (255, 100, 100), screen, SCREEN_WIDTH // 2 - 200, 100)
            draw_text("Defeat the Rat King to end these raids for good.", font_small,
                      (220, 180, 180), screen, SCREEN_WIDTH // 2 - 180, 135)
        elif self.raid_result_timer > 0:
            draw_text(getattr(self, "raid_result", ""), font_main, GOLD_COLOR,
                      screen, SCREEN_WIDTH // 2 - 250, 100)

        # ALT-näppäin: Näytä nimet (kuten GameManagerissa)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LALT] or keys[pygame.K_RALT]:
            self._draw_names(screen, offset)

        # M-kartta päällimmäisenä
        if self.show_map:
            self._draw_city_map(screen)
        else:
            draw_text("[M] Map   [C] Commander", font_small, (180, 180, 180), screen, 20, SCREEN_HEIGHT - 30)

        # Smeltery Overlay
        if self.active_smeltery:
            self._draw_smeltery_ui(screen)
            
        # Dialogue Overlay (Smeltery yms.)
        if self.manager.active_dialogue:
            self.manager._draw_in_game_dialogue(screen)

        # ESC hint
        if not self.show_pause_menu:
            draw_text("ESC: Menu", font_small, WHITE, screen, 20, 20)
            
        if self.show_pause_menu:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            
            draw_text("PAUSED", font_title, GOLD_COLOR, screen, SCREEN_WIDTH//2 - 60, SCREEN_HEIGHT//2 - 180)
            
            mouse_pos = pygame.mouse.get_pos()
            for btn in self.pause_buttons:
                btn.check_hover(mouse_pos)
                btn.draw(screen)
        
        # Editor
        self.draw_editor(screen)
    
    def _draw_inventory(self, screen):
        self.inventory_buttons = []
        
        # Overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        panel_w, panel_h = 1000, 700
        px = (SCREEN_WIDTH - panel_w) // 2
        py = (SCREEN_HEIGHT - panel_h) // 2
        
        draw_panel(screen, px, py, panel_w, panel_h, title="COMMANDER INVENTORY")
        
        # --- TABS ---
        tabs = ["GEAR", "SPELLS", "MATERIALS"]
        tab_w = 150
        tab_h = 40
        tx = px + 40
        ty = py + 60
        
        for t in tabs:
            col = GOLD_COLOR if t == self.inventory_tab else GRAY
            rect = pygame.Rect(tx, ty, tab_w, tab_h)
            pygame.draw.rect(screen, (50, 50, 60), rect, border_radius=5)
            if t == self.inventory_tab:
                pygame.draw.rect(screen, col, rect, 2, border_radius=5)
            
            draw_text(t, font_main, col, screen, tx + 40, ty + 8)
            
            self.inventory_buttons.append((rect, ("tab", t)))
            tx += tab_w + 10
            
        # --- CONTENT ---
        content_y = ty + 60
        
        if self.inventory_tab == "GEAR":
            self._draw_inventory_gear(screen, px, content_y, panel_w, panel_h)
        elif self.inventory_tab == "SPELLS":
            self._draw_inventory_spells(screen, px, content_y, panel_w, panel_h)
        elif self.inventory_tab == "MATERIALS":
            self._draw_inventory_materials(screen, px, content_y, panel_w, panel_h)
            
        # Close hint
        draw_text("Press 'I' or 'ESC' to close", font_small, GRAY, screen, px + panel_w - 200, py + panel_h - 30)

    def _draw_inventory_gear(self, screen, x, y, w, h):
        # Equipped
        slots = ["main_hand", "off_hand", "body", "head"]
        slot_labels = ["Main Hand", "Off Hand", "Body", "Head"]
        
        sx = x + 50
        sy = y
        
        draw_text("EQUIPPED", font_main, WHITE, screen, sx, sy)
        sy += 40
        
        for i, slot in enumerate(slots):
            item = self.player.equipment.get(slot)
            
            # Slot Box
            rect = pygame.Rect(sx, sy, 300, 60)
            pygame.draw.rect(screen, (40, 40, 50), rect, border_radius=5)
            pygame.draw.rect(screen, (60, 60, 70), rect, 1, border_radius=5)
            
            # Icon
            icon_rect = pygame.Rect(sx + 5, sy + 5, 50, 50)
            draw_item_slot_background(screen, icon_rect.x, icon_rect.y, 50, item)
            if item:
                item.draw_card_icon(screen, icon_rect.x, icon_rect.y, 50)
            
            # Text
            lbl = slot_labels[i]
            draw_text(lbl, font_small, GRAY, screen, sx + 70, sy + 5)
            if item:
                draw_text(item.name, font_main, WHITE, screen, sx + 70, sy + 25)
                self.inventory_buttons.append((rect, ("unequip", slot)))
            else:
                draw_text("Empty", font_main, (100, 100, 100), screen, sx + 70, sy + 25)
            
            sy += 70

        # Bag
        bx = x + 400
        by = y
        draw_text("BACKPACK (Gear)", font_main, WHITE, screen, bx, by)
        by += 40
        
        gear_items = [it for it in self.manager.equipment_bag if it.type in ["weapon", "armor", "shield", "helmet", "tool", "melee", "ranged"]]
        self._draw_bag_grid(screen, gear_items, bx, by, 500, 400)

    def _draw_inventory_spells(self, screen, x, y, w, h):
        slots = ["spell1", "spell2", "spell3", "usable", "usable2"]
        labels = ["Spell 1", "Spell 2", "Spell 3", "Potion 1", "Potion 2"]
        
        sx = x + 50
        sy = y
        draw_text("EQUIPPED SPELLS & ITEMS", font_main, WHITE, screen, sx, sy)
        sy += 40
        
        for i, slot in enumerate(slots):
            item = self.player.equipment.get(slot)
            
            rect = pygame.Rect(sx, sy, 300, 60)
            pygame.draw.rect(screen, (40, 40, 50), rect, border_radius=5)
            
            icon_rect = pygame.Rect(sx + 5, sy + 5, 50, 50)
            draw_item_slot_background(screen, icon_rect.x, icon_rect.y, 50, item)
            if item:
                item.draw_card_icon(screen, icon_rect.x, icon_rect.y, 50)
            
            draw_text(labels[i], font_small, GRAY, screen, sx + 70, sy + 5)
            if item:
                draw_text(item.name, font_main, WHITE, screen, sx + 70, sy + 25)
                self.inventory_buttons.append((rect, ("unequip", slot)))
            else:
                draw_text("Empty", font_main, (100, 100, 100), screen, sx + 70, sy + 25)
            
            sy += 70
            
        bx = x + 400
        by = y
        draw_text("BACKPACK (Spells & Potions)", font_main, WHITE, screen, bx, by)
        by += 40
        
        spell_items = [it for it in self.manager.equipment_bag if it.type in ["spell", "usable", "potion", "scroll", "book"]]
        self._draw_bag_grid(screen, spell_items, bx, by, 500, 400)

    def _draw_inventory_materials(self, screen, x, y, w, h):
        sx = x + 50
        sy = y
        draw_text("CRAFTING MATERIALS", font_main, WHITE, screen, sx, sy)
        sy += 40
        
        inv = self.manager.inventory
        if not inv:
            draw_text("No materials.", font_small, GRAY, screen, sx, sy)
            return
            
        for name, count in inv.items():
            if count > 0:
                draw_text(f"{name}: {count}", font_main, WHITE, screen, sx, sy)
                sy += 30
                if sy > y + 500:
                    sy = y + 40
                    sx += 300

    def _draw_bag_grid(self, screen, items, x, y, w, h):
        cols = 6
        slot_s = 60
        gap = 10
        
        for i, item in enumerate(items):
            row = i // cols
            col = i % cols
            
            bx = x + col * (slot_s + gap)
            by = y + row * (slot_s + gap)
            
            if by + slot_s > y + h: break
            
            rect = pygame.Rect(bx, by, slot_s, slot_s)
            mp = pygame.mouse.get_pos()
            is_hover = rect.collidepoint(mp)
            
            draw_item_slot_background(screen, bx, by, slot_s, item, is_hover)
            item.draw_card_icon(screen, bx, by, slot_s)
            
            self.inventory_buttons.append((rect, ("equip", item)))
            
            if is_hover:
                draw_item_tooltip(screen, item, mp[0] + 15, mp[1] + 15, self.player)

    def _handle_inventory_click(self, pos):
        for rect, action_data in self.inventory_buttons:
            if rect.collidepoint(pos):
                action = action_data[0]
                
                if action == "tab":
                    self.inventory_tab = action_data[1]
                    sound_system.play_sound('click')
                    
                elif action == "unequip":
                    slot = action_data[1]
                    self._unequip_slot(slot)
                    
                elif action == "equip":
                    item = action_data[1]
                    self._equip_from_bag(item)
                return

    def _draw_smeltery_ui(self, screen):
        smelter = self.active_smeltery
        if not smelter: return

        # Overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Panel
        w, h = 700, 500
        x = (SCREEN_WIDTH - w) // 2
        y = (SCREEN_HEIGHT - h) // 2
        
        draw_panel(screen, x, y, w, h, title="SMELTERY")
        
        # --- STATUS & PROGRESS ---
        status_y = y + 60
        
        if smelter.current_job:
            job = smelter.current_job
            pct = job["timer"] / job["max_time"]
            
            draw_text(f"Smelting: {job['output']}", font_main, GOLD_COLOR, screen, x + 40, status_y)
            
            # Progress Bar
            bar_w = 620
            bar_h = 20
            pygame.draw.rect(screen, (40, 40, 50), (x + 40, status_y + 30, bar_w, bar_h), border_radius=5)
            pygame.draw.rect(screen, (200, 100, 50), (x + 40, status_y + 30, int(bar_w * pct), bar_h), border_radius=5)
            draw_text(f"{int(pct*100)}%", font_small, WHITE, screen, x + w//2 - 15, status_y + 30)
        else:
            draw_text("Status: Idle", font_main, (150, 150, 150), screen, x + 40, status_y)
            draw_text("Select a recipe below to start smelting.", font_small, GRAY, screen, x + 40, status_y + 30)

        # --- STORAGE INFO ---
        store_y = y + 130
        # Vasen: Scrap & Wood
        draw_text("STORAGE (Automation)", font_main, WHITE, screen, x + 40, store_y)
        draw_text(f"Scrap Iron: {smelter.scrap_stored}", font_small, (200, 200, 200), screen, x + 40, store_y + 25)
        draw_text(f"Swamp Wood: {smelter.wood_stored}", font_small, (200, 200, 200), screen, x + 40, store_y + 45)
        
        # Oikea: Player Inventory (Relevant)
        inv = self.manager.inventory
        draw_text("YOUR INVENTORY", font_main, WHITE, screen, x + 380, store_y)
        draw_text(f"Scrap Iron: {inv.get('Scrap Iron', 0)}", font_small, (200, 200, 200), screen, x + 380, store_y + 25)
        draw_text(f"Swamp Wood: {inv.get('Swamp Wood', 0)}", font_small, (200, 200, 200), screen, x + 380, store_y + 45)
        draw_text(f"Iron Ore: {inv.get('Iron Ore', 0)}", font_small, (200, 200, 200), screen, x + 530, store_y + 25)
        draw_text(f"Coal: {inv.get('Coal', 0)}", font_small, (200, 200, 200), screen, x + 530, store_y + 45)

        # --- BUTTONS ---
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.smelter_buttons:
            # Päivitä napin tila (enabled/disabled)
            if btn.action == "smelter_scrap":
                # 2 Scrap + 1 Wood
                can_afford = inv.get("Scrap Iron", 0) >= 2 and inv.get("Swamp Wood", 0) >= 1
                btn.enabled = can_afford and not smelter.current_job
                # Lisää resepti-info napin alle
                draw_text("2 Scrap + 1 Wood", font_small, GRAY, screen, btn.rect.x + 10, btn.rect.bottom + 5)
                
            elif btn.action == "smelter_iron":
                # 2 Ore + 1 Coal
                can_afford = inv.get("Iron Ore", 0) >= 2 and inv.get("Coal", 0) >= 1
                btn.enabled = can_afford and not smelter.current_job
                draw_text("2 Iron Ore + 1 Coal", font_small, GRAY, screen, btn.rect.x + 10, btn.rect.bottom + 5)
                
            elif btn.action == "smelter_deposit":
                # Onko mitään talletettavaa?
                has_stuff = inv.get("Scrap Iron", 0) > 0 or inv.get("Swamp Wood", 0) > 0
                btn.enabled = has_stuff
                draw_text("Stores Scrap & Wood for villagers", font_small, GRAY, screen, btn.rect.x + 20, btn.rect.bottom + 5)

            btn.check_hover(mouse_pos)
            btn.draw(screen)
            
        # Close hint
        draw_text("Press 'E' or 'ESC' to close", font_small, GRAY, screen, x + w - 180, y + h - 30)

    def _handle_inventory_click(self, pos):
        for rect, data in self.inventory_buttons:
            if rect.collidepoint(pos):
                action, target = data
                if action == "equip":
                    self._equip_from_bag(target)
                elif action == "unequip":
                    self._unequip_slot(target)
                return

    def _handle_click(self, pos):
        mx, my = pos
        wx = mx + self.camera_x
        wy = my + self.camera_y
        world_pos = (wx, wy)
        
        # Check Tavern
        if self.tavern_house:
             door_rect = pygame.Rect(self.tavern_house.rect.centerx - 40, self.tavern_house.rect.bottom - 40, 80, 60)
             if door_rect.collidepoint(world_pos):
                 if self._check_range(self.player.rect, door_rect):
                     self.next_state = "tavern_sunk_cask"
                     sound_system.play_sound('click')
                 return True

        # Check NPCs
        for npc in self.npcs:
            if npc.rect.inflate(40, 40).collidepoint(world_pos):
                 if self._check_range(self.player.rect, npc.rect):
                     self.manager.open_patron_dialogue(npc, return_state="muckford_city")
                     self.next_state = "dialogue_active"
                 return True

        # Check Animals
        for cow in self.animals:
            if cow.rect.inflate(40, 40).collidepoint(world_pos):
                if self._check_range(self.player.rect, cow.rect):
                    self._interact_cow(cow)
                return True

        # Check Quest Givers
        if self.farmer_gus and self.farmer_gus.rect.inflate(40, 40).collidepoint(world_pos):
            if self._check_range(self.player.rect, self.farmer_gus.rect):
                self.manager.open_patron_dialogue(self.farmer_gus, return_state="muckford_city")
                self.next_state = "dialogue_active"
            return True

        # Check Props
        for prop in self.arena.props:
            if prop.rect.inflate(20, 20).collidepoint(world_pos):
                if self._check_range(self.player.rect, prop.rect):
                    return self._try_interact_prop(prop, check_collision=False)
        return False

    def _check_range(self, r1, r2, max_dist=150):
        d = math.hypot(r1.centerx - r2.centerx, r1.centery - r2.centery)
        if d <= max_dist:
            return True
        else:
            self.manager.vfx.show_damage(r1.centerx, r1.top - 20, "Too far!", color=(200, 50, 50))
            return False

    def _spawn_guards(self):
        """Kylän omat vartijat: taistelevat raideja vastaan (HumanAI)."""
        # Älä spawnaa tuplia (populaatio voidaan luoda uudelleen on_enterissä)
        if getattr(self, "guards", None):
            return
        from units.human import Human
        from items.spears.weak_spear import WeakSpear
        self.guards = []
        cx, cy = self.arena.width // 2, self.arena.height // 2
        posts = [(cx - 250, cy - 100), (cx + 250, cy - 100), (cx, cy + 250)]
        for i, (gx, gy) in enumerate(posts):
            g = Human(f"Muckford Guard", gx, gy, GREEN, "Common")
            g.weapon_masteries.add("spear")
            g.equipment["main_hand"] = WeakSpear()
            g.calculate_final_stats()
            g.current_hp = g.max_hp
            self.npcs.append(g)
            self.manager.all_units.add(g)
            self.guards.append(g)

    def _rat_king_defeated(self):
        try:
            from quest_system import quest_manager
            if quest_manager:
                q = quest_manager.quests.get("hunt_01")
                return bool(q and q.completed)
        except Exception:
            pass
        return False

    def _update_raids(self):
        m = self.manager
        clock = m.world_clock

        if self.raid_result_timer > 0:
            self.raid_result_timer -= 1

        # Rat King kukistettu -> rauha (iso saavutus!)
        if self._rat_king_defeated():
            return

        if not hasattr(m, "next_raid_day"):
            m.next_raid_day = clock.day + 1  # Ensimmäinen raidi 2. päivänä

        if self.raid_state == "idle":
            if clock.day >= m.next_raid_day and 9 <= clock.hour <= 20:
                self.raid_state = "warning"
                self.raid_banner_timer = 300  # 5 s varoitus
                sound_system.play_sound("boss_roar")

        elif self.raid_state == "warning":
            self.raid_banner_timer -= 1
            if self.raid_banner_timer <= 0:
                self._spawn_raid()

        elif self.raid_state == "active":
            self.raid_timer -= 1
            for r in self.raid_rats:
                if not r.is_dead:
                    r.run_combat_ai(m.all_units, self.arena.obstacles, m)
                    r.update(self.arena.obstacles, m)
            if all(r.is_dead for r in self.raid_rats):
                self._end_raid()
            elif self.raid_timer <= 0:
                self._end_raid(retreated=True)

    def _spawn_raid(self):
        from units.rat import GiantRat
        m = self.manager
        self.raid_state = "active"
        self._raid_player_kills_start = m.player_character.stats.get("kills", 0)

        count = min(8, 4 + m.world_clock.day // 3)
        edges = ["top", "bottom", "left", "right"]
        for i in range(count):
            edge = random.choice(edges)
            if edge == "top":
                rx, ry = random.randint(100, self.arena.width - 100), 60
            elif edge == "bottom":
                rx, ry = random.randint(100, self.arena.width - 100), self.arena.height - 60
            elif edge == "left":
                rx, ry = 60, random.randint(100, self.arena.height - 100)
            else:
                rx, ry = self.arena.width - 60, random.randint(100, self.arena.height - 100)
            rat = GiantRat("Sewer Rat", rx, ry, team_color=ENEMY_TEAM)
            # Viemärirotat ovat heikompia kuin areenarotat - vartijat
            # pärjäävät niille, mutta pelaajan apu nopeuttaa selvästi
            rat.max_hp = 25
            rat.current_hp = 25
            rat.strength = 10
            self.raid_rats.append(rat)
            m.all_units.add(rat)
            m.vfx.create_spawn_fog(rx, ry)
        # Raidilla on aikaraja: rotat perääntyvät saaliineen 60 s jälkeen
        self.raid_timer = 3600

    def _end_raid(self, retreated=False):
        m = self.manager
        player_kills = m.player_character.stats.get("kills", 0) - self._raid_player_kills_start

        # Palkinnot: maine jos pelaaja osallistui
        if player_kills > 0:
            try:
                from quest_system import quest_manager
                if quest_manager:
                    quest_manager.add_reputation(5)
                    m.reputation = quest_manager.reputation
            except Exception:
                pass
            gold = 10 + player_kills * 3
            m.gold += gold
            self.raid_result = f"RAID REPELLED! +5 Reputation, +{gold} gold"
            m.grant_hero_xp(5 * player_kills)
        elif retreated:
            self.raid_result = "The rats retreat to the sewers with their loot..."
        else:
            self.raid_result = "The guards repelled the raid without you."
        self.raid_result_timer = 360

        # Siivoa raadot
        for r in self.raid_rats:
            if r in m.all_units:
                m.all_units.remove(r)
        self.raid_rats = []
        self.raid_state = "idle"
        m.next_raid_day = m.world_clock.day + random.randint(2, 3)

    def _update_eggs(self):
        """Keräämättömät munat voivat kuoriutua poikasiksi (tai pilaantua)."""
        for prop in list(self.arena.props):
            if not isinstance(prop, Egg):
                continue
            if not hasattr(prop, "hatch_timer"):
                prop.hatch_timer = random.randint(3600, 9000)  # 1 - 2.5 min
            prop.hatch_timer -= 1
            if prop.hatch_timer <= 0:
                self.arena.props.remove(prop)
                if prop in self.manager.all_units:
                    self.manager.all_units.remove(prop)
                # Populaatiokatto: ilman tätä kanamäärä kasvaa rajatta
                chicken_count = sum(1 for a in self.animals if isinstance(a, Chicken))
                if chicken_count < 12 and random.random() < 0.35:
                    # Kuoriutuu poikaseksi, joka kasvaa kanaksi
                    chick = Chicken(prop.rect.x, prop.rect.y, team_color=GREEN)
                    chick.make_baby()
                    self.animals.append(chick)
                    self.manager.all_units.add(chick)
                    self.manager.vfx.show_damage(prop.rect.centerx, prop.rect.top - 10,
                                                 "*peep!*", color=(255, 240, 150))
                # Muuten muna vain pilaantui hiljaisuudessa

    def _interact_cow(self, cow):
        if cow.milk_ready:
            # Tarkista onko tyhjä ämpäri
            has_bucket = False
            bucket_idx = -1
            for i, item in enumerate(self.manager.equipment_bag):
                if isinstance(item, BucketEmpty):
                    has_bucket = True
                    bucket_idx = i
                    break
            
            if has_bucket:
                # Vaihda ämpäri maitoon
                self.manager.equipment_bag.pop(bucket_idx)
                self.manager.equipment_bag.append(BucketMilk())
                cow.milk_ready = False
                sound_system.play_sound('recruit') # "Splosh" ääni
                self.manager.vfx.show_damage(cow.rect.centerx, cow.rect.top, "Milked!", color=(255, 255, 255))
                self.manager.grant_hero_xp(5, cow.rect.centerx, cow.rect.top)
                # Animal Husbandry: taitava lypsäjä saa talteen myös kannun
                # Milk-materiaalia keittiöön per taso
                husbandry = int(getattr(self.player, "husbandry", 0))
                if husbandry > 0:
                    self.manager.add_material("Milk", husbandry)
                    self.manager.vfx.show_damage(cow.rect.centerx, cow.rect.top - 30,
                                                 f"+{husbandry} Milk", color=(235, 235, 220))
            else:
                self.manager.vfx.show_damage(self.player.rect.centerx, self.player.rect.top, "Need Bucket!", color=(200, 50, 50))
        else:
            self.manager.vfx.show_damage(cow.rect.centerx, cow.rect.top, "Not ready", color=(200, 200, 200))

    def _try_interact_prop(self, prop, check_collision=False):
        # Jos check_collision on True, tarkistetaan osuuko pelaaja proppiin (E-näppäin logiikka)
        if check_collision:
            if not self.player.rect.colliderect(prop.rect.inflate(20, 20)):
                return False

        if isinstance(prop, Manure):
            # Pelaaja kerää kakan reppuunsa
            # Jos quest on aktiivinen, tämä on vaihe 1/2 (kerää -> vie kasalle)
            # Mutta yksinkertaistetaan: Pelaaja kerää reppuun, ja kun vie kasalle, quest etenee.
            
            if True: # Aina kerätään reppuun
                self.manager.add_material("Manure", 1)
                if prop in self.arena.props: self.arena.props.remove(prop)
                if prop in self.manager.all_units: self.manager.all_units.remove(prop)
                sound_system.play_sound('click')
                self.manager.grant_hero_xp(1, prop.rect.centerx, prop.rect.top)
                return True
            
        if isinstance(prop, ManurePile):
            count = self.manager.inventory.get("Manure", 0)
            if count > 0:
                self.manager.inventory["Manure"] = 0
                
                # QUEST LOGIC: Etenee kun viet kakan kasalle
                if quest_manager:
                    q = quest_manager.get_quest("quest_manure_cleanup")
                    if q and q.status == "active":
                        needed = q.definition.required_amount - q.progress
                        added = min(count, needed)
                        q.progress += added
                        
                        if q.progress >= q.definition.required_amount:
                            q.status = "completed"
                            self.manager.vfx.show_damage(prop.rect.centerx, prop.rect.top - 20, "Quest Done! Talk to Gus!", color=GOLD_COLOR)
                            sound_system.play_sound('win')
                        else:
                            self.manager.vfx.show_damage(prop.rect.centerx, prop.rect.top - 20, f"Quest: {q.progress}/{q.definition.required_amount}", color=WHITE)

                # Lisätään kaupungin varastoon (Talouskierto)
                self.manager.city_storage["Manure"] = self.manager.city_storage.get("Manure", 0) + count
                self.manager.grant_hero_xp(count, prop.rect.centerx, prop.rect.top)
                
            return True
            
        if isinstance(prop, FarmStorage):
            self.next_state = "city_storage"
            sound_system.play_sound('click')
            return True
            
        if isinstance(prop, TownHall):
            self.next_state = "sponsors"
            sound_system.play_sound('click')
            return True

        if isinstance(prop, MarketStall):
            # Market-alueen nimetty liike -> liikkeen oma kauppasivu
            self.manager.pending_shop_id = prop.shop_id
            self.next_state = "district_shop"
            sound_system.play_sound('click')
            return True

        if isinstance(prop, MuckfordStall):
            self.next_state = "market"
            sound_system.play_sound('click')
            return True
            
        if isinstance(prop, Well):
            # Tarkista onko tyhjä ämpäri
            bucket_idx = -1
            for i, item in enumerate(self.manager.equipment_bag):
                if isinstance(item, BucketEmpty):
                    bucket_idx = i
                    break
            
            if bucket_idx != -1:
                self.manager.equipment_bag.pop(bucket_idx)
                self.manager.equipment_bag.append(BucketWater())
                sound_system.play_sound('recruit') # Splash sound placeholder
                self.manager.vfx.show_damage(prop.rect.centerx, prop.rect.top - 20, "Water Fetched!", color=(100, 200, 255))
                self.manager.grant_hero_xp(2, prop.rect.centerx, prop.rect.top)
            else:
                self.manager.vfx.show_damage(prop.rect.centerx, prop.rect.top - 20, "Need Bucket!", color=(200, 50, 50))
            return True
            
        if isinstance(prop, Smeltery):
            # Jos valmiita tuotteita, kerää ne heti
            if prop.output_inventory:
                prop.interact(self.manager)
            else:
                # Avaa uusi hieno UI
                self._open_smelter_ui(prop)
            return True
            
        if isinstance(prop, (Apple, Egg)):
            self.manager.add_material(prop.loot_item, 1)
            if prop in self.arena.props: self.arena.props.remove(prop)
            if prop in self.manager.all_units: self.manager.all_units.remove(prop)
            sound_system.play_sound('click')
            self.manager.vfx.show_damage(prop.rect.centerx, prop.rect.top - 20, f"+1 {prop.loot_item}", color=WHITE)
            self.manager.grant_hero_xp(2, prop.rect.centerx, prop.rect.top)
            return True
            
        if isinstance(prop, (ScrapPile, ScrapPileBig)) and not getattr(prop, "is_empty", False):
            # Klikkaus logiikka romukasoille (puut hoidetaan combatilla)
            prop.harvest(self.manager, harvester=self.player)
            return True
            
        return False

    # =========================================================
    # POI-IKONIT (kelluvat merkit tärkeiden hahmojen/paikkojen päällä)
    # =========================================================
    def _poi_icon_list(self):
        """Palauttaa listan (world_x, world_y, kind). Quest-tila vaikuttaa
        Farmer Gusin merkkiin: ! = tarjolla, harmaa ! = kesken, ? = palautus."""
        pois = []

        # Farmer Gus: quest-merkki tilan mukaan
        gus = getattr(self, "farmer_gus", None)
        if gus and quest_manager:
            status = quest_manager.get_quest_status("quest_manure_cleanup")
            if status == "available":
                pois.append((gus.rect.centerx, gus.rect.top - 28, "quest_avail"))
            elif status == "active":
                pois.append((gus.rect.centerx, gus.rect.top - 28, "quest_active"))
            elif status == "completed":
                pois.append((gus.rect.centerx, gus.rect.top - 28, "quest_turnin"))

        # Hamo: kolikko (ostaa saaliit)
        hamo = getattr(self, "hamo", None)
        if hamo:
            pois.append((hamo.rect.centerx, hamo.rect.top - 28, "trade"))

        # Bram + areenaportti: liigabanneri
        bram = getattr(self, "bram", None)
        if bram:
            pois.append((bram.rect.centerx, bram.rect.top - 28, "league"))
        gate = getattr(self, "arena_gate", None)
        if gate:
            pois.append((gate.rect.centerx, gate.rect.top - 20, "league"))
        barracks = getattr(self, "barracks", None)
        if barracks:
            pois.append((barracks.rect.centerx, barracks.rect.top - 20, "barracks"))
        board = getattr(self, "notice_board", None)
        if board:
            # Ikoni: ! jos on lunastettavaa tai uutta tarjolla, muuten ?
            vt = self.manager.village_tasks
            kind = "notice"
            if vt:
                if any(t.status == "ready_turnin" for t in vt.active_tasks()):
                    kind = "notice_ready"
                elif vt.available_for(self.manager.reputation):
                    kind = "notice_new"
            pois.append((board.rect.centerx, board.rect.top - 15, kind))

        # Taverna (muki) ja seppä (alasin) ovien kohdalle
        if getattr(self, "tavern_house", None):
            th = self.tavern_house
            off = getattr(th, "door_offset", (th.rect.w // 2, th.rect.h))
            pois.append((th.image_pos[0] + off[0], th.image_pos[1] + off[1] - 120, "tavern"))
        if getattr(self, "blacksmith_house", None):
            bh = self.blacksmith_house
            off = getattr(bh, "door_offset", (bh.rect.w // 2, bh.rect.h))
            pois.append((bh.image_pos[0] + off[0], bh.image_pos[1] + off[1] - 120, "smith"))

        return pois

    def _draw_poi_icons(self, screen, offset):
        """Piirtää POI-ikonit kaiken päälle, jotta ne ovat aina seurattavissa."""
        bob = math.sin(pygame.time.get_ticks() * 0.004) * 4
        sw, sh = screen.get_size()
        for wx, wy, kind in self._poi_icon_list():
            sx = int(wx - offset[0])
            sy = int(wy - offset[1] + bob)
            if not (-40 < sx < sw + 40 and -40 < sy < sh + 40):
                continue
            self._draw_poi_icon(screen, sx, sy, kind)

    def _draw_poi_icon(self, screen, sx, sy, kind):
        if kind in ("quest_avail", "quest_active", "quest_turnin"):
            color = GOLD_COLOR if kind != "quest_active" else (150, 150, 150)
            char = "?" if kind == "quest_turnin" else "!"
            surf = font_title.render(char, True, color)
            shadow = font_title.render(char, True, (0, 0, 0))
            screen.blit(shadow, (sx - surf.get_width() // 2 + 2, sy - surf.get_height() + 2))
            screen.blit(surf, (sx - surf.get_width() // 2, sy - surf.get_height()))
        elif kind == "trade":
            # Kultakolikko
            pygame.draw.circle(screen, (0, 0, 0), (sx + 1, sy - 9), 12)
            pygame.draw.circle(screen, GOLD_COLOR, (sx, sy - 10), 11)
            pygame.draw.circle(screen, (180, 140, 0), (sx, sy - 10), 11, 2)
            t = font_small.render("G", True, (110, 85, 0))
            screen.blit(t, (sx - t.get_width() // 2, sy - 10 - t.get_height() // 2))
        elif kind == "league":
            # Punainen banneri (Rookie Dust Circuit)
            pygame.draw.rect(screen, (0, 0, 0), (sx - 9, sy - 30, 20, 24))
            pygame.draw.rect(screen, (170, 45, 45), (sx - 10, sy - 31, 20, 24))
            pygame.draw.polygon(screen, (170, 45, 45),
                                [(sx - 10, sy - 7), (sx + 10, sy - 7), (sx, sy + 3)])
            pygame.draw.line(screen, (230, 200, 120), (sx - 10, sy - 31), (sx + 10, sy - 31), 3)
        elif kind == "barracks":
            # Vihreä kilpimerkki (oma tiimi)
            pygame.draw.polygon(screen, (0, 0, 0),
                                [(sx - 9, sy - 30), (sx + 11, sy - 30), (sx + 11, sy - 12), (sx + 1, sy - 2), (sx - 9, sy - 12)])
            pygame.draw.polygon(screen, (70, 170, 90),
                                [(sx - 10, sy - 31), (sx + 10, sy - 31), (sx + 10, sy - 13), (sx, sy - 3), (sx - 10, sy - 13)])
            pygame.draw.line(screen, (230, 230, 210), (sx, sy - 28), (sx, sy - 8), 2)
            pygame.draw.line(screen, (230, 230, 210), (sx - 6, sy - 20), (sx + 6, sy - 20), 2)
        elif kind in ("notice", "notice_new", "notice_ready"):
            # Ilmoitustaulu: ruskea lappu, jonka päällä ! (uutta/lunastettavaa) tai ?
            pygame.draw.rect(screen, (0, 0, 0), (sx - 9, sy - 30, 20, 24))
            paper = (235, 225, 200)
            pygame.draw.rect(screen, paper, (sx - 10, sy - 31, 20, 24))
            pygame.draw.rect(screen, (120, 90, 60), (sx - 10, sy - 31, 20, 24), 2)
            if kind == "notice_ready":
                mark, col = "!", (90, 200, 110)
            elif kind == "notice_new":
                mark, col = "!", GOLD_COLOR
            else:
                mark, col = "?", (150, 150, 160)
            s = font_main.render(mark, True, col)
            screen.blit(s, (sx - s.get_width() // 2, sy - 30))
        elif kind == "tavern":
            # Olutmuki
            pygame.draw.rect(screen, (0, 0, 0), (sx - 8, sy - 24, 18, 20), border_radius=3)
            pygame.draw.rect(screen, (150, 100, 50), (sx - 9, sy - 25, 18, 20), border_radius=3)
            pygame.draw.rect(screen, (240, 235, 210), (sx - 9, sy - 29, 18, 6), border_radius=3)
            pygame.draw.arc(screen, (150, 100, 50), (sx + 6, sy - 22, 12, 14), -1.6, 1.6, 3)
        elif kind == "smith":
            # Alasin
            pygame.draw.rect(screen, (0, 0, 0), (sx - 11, sy - 22, 24, 8))
            pygame.draw.rect(screen, (90, 90, 100), (sx - 12, sy - 23, 24, 8))
            pygame.draw.rect(screen, (90, 90, 100), (sx - 5, sy - 15, 10, 8))
            pygame.draw.rect(screen, (70, 70, 80), (sx - 9, sy - 7, 18, 4))

    def _handle_combat_click(self, pos):
        mx, my = pos
        wx = mx + self.camera_x
        wy = my + self.camera_y
        
        # Käänny kohti kohdetta
        if wx > self.player.rect.centerx:
            self.player.facing_right = True
        else:
            self.player.facing_right = False
            
        mouse_rect = pygame.Rect(wx - 10, wy - 10, 20, 20)
        
        target = None
        for u in self.npcs + self.animals:
            if u.rect.colliderect(mouse_rect):
                target = u
                break
        
        # Jos ei yksikköä, tarkista puut
        if not target:
            for p in self.arena.props:
                if isinstance(p, MuckfordTree) and not getattr(p, "is_empty", False):
                    if p.rect.colliderect(mouse_rect):
                        target = p
                        break
        
        if target:
            self.player.perform_attack(target, self.manager)
        else:
            self.player.perform_attack(None, self.manager, target_pos=(wx, wy))

    def _draw_names(self, screen, offset):
        """Piirtää nimet hahmojen päälle (debug/info)."""
        for npc in self.npcs:
            if getattr(npc, "ai_controller", None) and getattr(npc.ai_controller, "state", 0) == "INSIDE":
                continue
                
            sx = npc.rect.centerx - offset[0]
            sy = npc.rect.top - offset[1] - 15
            if 0 < sx < SCREEN_WIDTH and 0 < sy < SCREEN_HEIGHT:
                draw_text(npc.name, font_small, (200, 200, 200), screen, sx - 20, sy)

    def _draw_quest_markers(self, screen, offset):
        if self.farmer_gus:
            status = "locked"
            if quest_manager:
                status = quest_manager.get_quest_status("quest_manure_cleanup")
                
            x = self.farmer_gus.rect.centerx - offset[0]
            
            # Liikkuva efekti (bobbing)
            bob = math.sin(pygame.time.get_ticks() * 0.005) * 5
            y = self.farmer_gus.rect.top - 50 - offset[1] + bob # Nostettu ylemmäs (-30 -> -50)
            
            if status == "available":
                draw_text("!", font_title, GOLD_COLOR, screen, x - 10, y) # Isompi fontti (font_title on iso)
            elif status == "active":
                # Ei merkkiä tai harmaa kysymysmerkki kun kesken
                draw_text("?", font_title, (150, 150, 150), screen, x - 15, y)
            elif status == "completed":
                draw_text("?", font_title, (100, 255, 100), screen, x - 15, y)

    def _draw_hover_info(self, screen, offset, mouse_pos):
        wx = mouse_pos[0] + offset[0]
        wy = mouse_pos[1] + offset[1]
        world_pos = (wx, wy)
        
        # Check Animals
        for cow in self.animals:
            if cow.rect.inflate(20, 20).collidepoint(world_pos):
                if isinstance(cow, Cow):
                    txt = "Milk" if cow.milk_ready else "Pet"
                else:
                    txt = "Pet" # Kanat yms.
                draw_text(txt, font_small, WHITE, screen, mouse_pos[0] + 15, mouse_pos[1])
                return

        # Check Props
        for prop in self.arena.props:
            if prop.rect.inflate(10, 10).collidepoint(world_pos):
                if isinstance(prop, Manure):
                    draw_text("Pick Up", font_small, (150, 100, 50), screen, mouse_pos[0] + 15, mouse_pos[1])
                    return
                if isinstance(prop, ManurePile):
                    draw_text("Dump Manure", font_small, GOLD_COLOR, screen, mouse_pos[0] + 15, mouse_pos[1])
                    return
                elif isinstance(prop, FarmStorage):
                    draw_text("Open Storage", font_small, GOLD_COLOR, screen, mouse_pos[0] + 15, mouse_pos[1])
                    return
                elif isinstance(prop, TownHall):
                    draw_text("Town Hall", font_small, GOLD_COLOR, screen, mouse_pos[0] + 15, mouse_pos[1])
                    return
                elif isinstance(prop, AppleTree):
                    draw_text("Shake (E)", font_small, WHITE, screen, mouse_pos[0] + 15, mouse_pos[1])
                    return
                elif isinstance(prop, Smeltery):
                    draw_text("Smeltery", font_small, (255, 100, 50), screen, mouse_pos[0] + 15, mouse_pos[1])
                    return
                elif isinstance(prop, (MuckfordTree, ScrapPile, ScrapPileBig)) and not getattr(prop, "is_empty", False):
                    label = "Chop" if isinstance(prop, MuckfordTree) else "Scavenge"
                    draw_text(label, font_small, WHITE, screen, mouse_pos[0] + 15, mouse_pos[1])
                    return


        # Check NPCs
        for npc in self.npcs:
            if npc.rect.inflate(20, 20).collidepoint(world_pos):
                draw_text("Chat", font_small, (200, 200, 200), screen, mouse_pos[0] + 15, mouse_pos[1])
                return

        # Quest Giver Hover
        if self.farmer_gus and self.farmer_gus.rect.inflate(40, 40).collidepoint(world_pos):
            draw_text("Quest", font_small, GOLD_COLOR, screen, mouse_pos[0] + 15, mouse_pos[1])
            return

    def _update_simulation(self):
        """Hoitaa kaupungin elämän: kävelyn, juttelun ja taloissa vierailun."""
        for npc in self.npcs:
            if not hasattr(npc, "sim_state"): continue # Skip static NPCs like Gus

            # --- AI INTEGRATION ---
            # Tarkista tekeekö VillagerAI töitä (State ei ole 0/IDLE)
            ai = getattr(npc, "ai_controller", None)
            is_working = False
            if ai and ai.state != 0: # 0 = STATE_IDLE
                is_working = True
            
            if is_working:
                npc.sim_state = "BUSY" # AI ohjaa
                continue
            elif npc.sim_state == "BUSY":
                # AI lopetti työt, palataan simulaatioon
                npc.sim_state = "IDLE"
            # ----------------------

            if npc.sim_state == "INSIDE":
                npc.sim_timer -= 1
                if npc.sim_timer <= 0:
                    # Tule ulos
                    npc.sim_state = "IDLE"
                    npc.sim_timer = 60
                continue

            # Jos ollaan ulkona, piirretään normaalisti
            if npc.sim_state == "IDLE":
                npc.animation_state = "idle"
                npc.sim_timer -= 1
                if npc.sim_timer <= 0:
                    # Valitse uusi toiminto
                    action = self.rng.choice(["WALK", "WALK", "WALK", "ENTER", "TALK"])
                    
                    if action == "WALK":
                        # Arvo satunnainen kohde
                        tx = self.rng.randint(100, self.arena.width - 100)
                        ty = self.rng.randint(100, self.arena.height - 100)
                        npc.sim_target = (tx, ty)
                        npc.sim_state = "WALK"
                    
                    elif action == "ENTER" and self.buildings:
                        # Mene lähimpään tai satunnaiseen taloon
                        target_house = self.rng.choice(self.buildings)
                        npc.sim_target = target_house
                        npc.sim_state = "ENTERING"
                        
                    elif action == "TALK":
                        # Etsi lähellä oleva kaveri
                        partner = None
                        for other in self.npcs:
                            if other != npc and getattr(other, "sim_state", "") == "IDLE":
                                dist = math.hypot(other.rect.centerx - npc.rect.centerx, other.rect.centery - npc.rect.centery)
                                if dist < 150:
                                    partner = other
                                    break
                        
                        if partner:
                            npc.sim_state = "TALK"
                            npc.sim_partner = partner
                            npc.sim_timer = 180 # 3 sekuntia juttelua
                            
                            partner.sim_state = "TALK"
                            partner.sim_partner = npc
                            partner.sim_timer = 180
                            
                            # Käänny toisiaan kohti
                            npc.facing_right = partner.rect.centerx > npc.rect.centerx
                            partner.facing_right = npc.rect.centerx > partner.rect.centerx
                            
                            # Puhekuplat
                            lines = ["Nice weather.", "Busy day.", "Heard about the rats?", "Need ale.", "Work, work.", "Move it.", "Hello.", "Hmm."]
                            self.manager.vfx.create_speech_bubble(npc, self.rng.choice(lines), duration=120)
                        else:
                            npc.sim_timer = 30 # Ei löytynyt, odota hetki

            elif npc.sim_state == "WALK" or npc.sim_state == "ENTERING":
                npc.animation_state = "run"
                tx, ty = npc.sim_target
                dx = tx - npc.rect.centerx
                dy = ty - npc.rect.centery
                dist = math.hypot(dx, dy)
                
                if dist < 10:
                    # Perillä
                    if npc.sim_state == "ENTERING":
                        npc.sim_state = "INSIDE"
                        npc.sim_timer = self.rng.randint(300, 1200) # 5-20 sekuntia sisällä
                    else:
                        npc.sim_state = "IDLE"
                        npc.sim_timer = self.rng.randint(60, 180)
                else:
                    # Liiku
                    speed = 1.2 # Hidastettu kävelyvauhti
                    move_x = (dx / dist) * speed
                    move_y = (dy / dist) * speed
                    npc.facing_right = move_x > 0
                    
                    # KORJAUS: Käytetään check_wall_collision sub-pixel liikkeelle
                    # Tämä estää "warppimisen" ja jumittamisen kun liike on alle 1px/frame
                    if hasattr(npc, "check_wall_collision"):
                        npc.check_wall_collision(move_x, move_y, self.arena.obstacles)
                    else:
                        npc.rect.x += int(move_x)
                        npc.rect.y += int(move_y)

            elif npc.sim_state == "TALK":
                npc.animation_state = "idle"
                npc.sim_timer -= 1
                if npc.sim_timer <= 0:
                    npc.sim_state = "IDLE"
                    npc.sim_timer = self.rng.randint(30, 90)

    def _equip_from_bag(self, item):
        if item in self.manager.equipment_bag:
            self.manager.equipment_bag.remove(item)
            
            # Determine slot
            slot = getattr(item, "slot_type", "main_hand")
            
            # Equip
            old_item = self.player.equip_item_to_slot(slot, item)
            
            # Check if equip failed (returns same item)
            if old_item is item:
                # Failed (e.g. requirements)
                self.manager.equipment_bag.append(item)
                sound_system.play_sound('error')
            else:
                # Success
                if old_item:
                    self.manager.equipment_bag.append(old_item)
                sound_system.play_sound('recruit') # Equip sound

    def _unequip_slot(self, slot):
        item = self.player.unequip_slot(slot)
        if item:
            self.manager.equipment_bag.append(item)
            sound_system.play_sound('click')