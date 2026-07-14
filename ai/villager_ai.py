import pygame
import math
import random
from ai.base_ai import BaseAI
from assets.tiles.farm_objects import Manure, ManurePile, FarmStorage, Egg
from assets.tiles.muckford_objects import MuckfordTree, ScrapPileBig, Well, Smeltery, ChickenCoop
from crafting.swamp.scrap_pile import ScrapPile
from units.farm_animals import Cow, Chicken
from settings import WHITE
from ai.life_ai import DIALOGUE_TOPICS

# Tilat
STATE_IDLE = 0
STATE_WORK = 1
STATE_FLEE = 2
STATE_SEEK_HELP = 3
STATE_FOLLOW = 4

class VillagerAI(BaseAI):
    def __init__(self, unit):
        super().__init__(unit)
        self.state = STATE_IDLE
        self.state_timer = 0
        self.speech_timer = 0
        self.scream_cooldown = 0
        self.panic_mode = False
        self.panic_timer = 0
        self.follow_target = None
        self.work_type = None # "chop", "scavenge", "farm", "clean", "milk", "collect_egg", "build"
        self.work_target = None # BUGIKORJAUS: luettiin ennen ensimmäistä asetusta

        # NPC-NPC keskustelu
        self.chat_freeze = 0        # Seiso paikallaan keskustelun ajan
        self.pending_reply = None   # (teksti, viive frameina)
        
        # --- STUCK DETECTION ---
        self.stuck_counter = 0
        self.last_pos_check = (0, 0)
        
        # Yksilölliset ominaisuudet
        self.social_score = random.random() # Kuinka puhelias
        self.work_ethic = random.random()   # Kuinka paljon tekee töitä
        
        # Liikkeen pehmennys (ettei tärise paikallaan)
        self.flee_jitter = pygame.math.Vector2(0, 0)
        self.jitter_timer = 0
        
        # UUSI: Suunnan lukitus ja osuman reagointi
        self.flee_override_timer = 0 # Jos > 0, paetaan vaikka olisi escort
        self.direction_lock_timer = 0 # Estää suunnan vaihdon joka frame
        self.betrayer = None # Kohde jota paetaan (pelaaja jos hylkää)
        self.allow_idle_wander = True # Jos False, ulkoinen järjestelmä (CityMenu) hoitaa idle-liikkeen
        
        # UUSI: Työnjako - Arvotaan rooli
        self.job = self._assign_random_job()
        # Päivitetään nimi näkyviin (jos ei ole jo)
        if "(" not in self.unit.name:
            self.unit.name = f"{self.unit.name} ({self.job})"
            
        # Wandering logic
        self.wander_target = None
        self.wander_timer = 0

    def _assign_random_job(self):
        r = random.random()
        if r < 0.30: return "Farmer"      # 30%
        elif r < 0.55: return "Scavenger" # 25%
        elif r < 0.80: return "Lumberjack" # 25%
        else: return "Laborer"           # 20%

    def set_follow_target(self, target):
        self.state = STATE_FOLLOW
        self.follow_target = target
        self.unit.animation_state = "run"

    def trigger_betrayal(self, target):
        """Kutsutaan kun pelaaja hylkää tehtävän."""
        self.follow_target = None
        self.betrayer = target
        self.state = STATE_FLEE
        self.unit.animation_state = "scared"
        self.unit.set_sprinting(True)
        # Lukitaan suunta poispäin heti
        self.direction_lock_timer = 60
        self.flee_jitter = pygame.math.Vector2(0, 0) # Nollataan jitter jotta move_away laskee uuden

    def execute_ai(self, all_units, obstacles, manager=None):
        if self.unit.is_dead: return

        # 0. Päivitä ajastimet
        self.state_timer -= 1
        self.speech_timer -= 1
        self.scream_cooldown -= 1
        if self.panic_timer > 0: self.panic_timer -= 1
        if self.flee_override_timer > 0: self.flee_override_timer -= 1
        if self.direction_lock_timer > 0: self.direction_lock_timer -= 1

        # 0. BETRAYAL (Korkein prioriteetti: Pakene petturia)
        if self.betrayer:
            self.state = STATE_FLEE
            self.unit.animation_state = "scared"
            self.unit.set_sprinting(True)
            self.move_away_from(self.betrayer, all_units, obstacles)
            return

        # 0.5. FORCE FOLLOW (Seuraa pelaajaa sokeasti)
        # Ohitetaan kaikki paniikki- ja uhkatarkistukset.
        if self.follow_target:
            self.state = STATE_FOLLOW
            self.unit.animation_state = "run"
            
            dist = math.hypot(self.follow_target.rect.centerx - self.unit.rect.centerx,
                              self.follow_target.rect.centery - self.unit.rect.centery)
            
            if dist > 80: # Pidä etäisyyttä
                # Kiri kiinni jos jäädään jälkeen (Sprint)
                if dist > 300: self.unit.set_sprinting(True)
                else: self.unit.set_sprinting(False)

                self._move_strongly_towards(self.follow_target, dist, obstacles, all_units)
            else:
                self.unit.animation_state = "idle"
                self.unit.set_sprinting(False)
            return

        # 0.5 Osuma-reaktio (Jos otetaan vahinkoa, pakene hetki riippumatta tilasta)
        # BUGIKORJAUS: hurt_timer-attribuuttia ei ole Gladiatorilla, joten
        # reaktio ei koskaan lauennut. Käytetään osuma-animaation tilaa.
        if self.unit.animation_state == "hurt" and getattr(self.unit, "animation_timer", 0) > 8:
            self.flee_override_timer = 60 # 1 sekunti paniikkia
        
        # 1. Uhka-analyysi (Joka frame, koska selviytyminen on tärkeintä)
        # Skannataan vain lähellä olevat (Active Range)
        # Jos seurataan pelaajaa, luotetaan häneen enemmän -> lyhyempi scan range
        scan_range = 150 if self.follow_target else 400
        threat = self._find_nearest_threat(all_units, limit_dist=scan_range)
        dist = 9999
        
        if threat:
            dist = math.hypot(threat.rect.centerx - self.unit.rect.centerx, 
                              threat.rect.centery - self.unit.rect.centery)
            
        # Hystereesi paniikille: Alkaa 350px kohdalla, loppuu vasta kun uhka on kaukana (600px)
        # TAI jos on juuri otettu osumaa (flee_override)
        # Jos seurataan, panikoidaan vasta kun uhka on todella lähellä (150px)
        panic_threshold = 150 if self.follow_target else 350
        
        if dist < panic_threshold or self.flee_override_timer > 0:
            self.panic_mode = True
            self.panic_timer = 120 # Pysy paniikissa vähintään 2 sekuntia vaikka uhka katoaisi hetkeksi
        elif dist > 600 and self.panic_timer <= 0:
            self.panic_mode = False

        if self.panic_mode:
            self._clear_work_target() # Vapauta työ jos panikoidaan
            self.state = STATE_FLEE
            self.unit.animation_state = "scared"
            self.unit.set_sprinting(True)

            # Huuda apua satunnaisesti
            if self.scream_cooldown <= 0 and random.random() < 0.05:
                self.scream_cooldown = random.randint(60, 180)
                shouts = ["HELP!", "RUN!", "THEY ARE HERE!", "AAAAH!", "MERCY!", "TOO YOUNG TO DIE!"]
                if manager:
                    manager.vfx.show_damage(self.unit.rect.centerx, self.unit.rect.top - 30, random.choice(shouts), color=(255, 100, 100))
            
            # Normaali pako (BaseAI hoitaa jumiutumisen eston)
            if threat:
                self.move_away_from(threat, all_units, obstacles)
            elif self.flee_override_timer > 0:
                # Ei näkyvää uhkaa, mutta sattuu -> juokse satunnaiseen suuntaan tai eteenpäin
                self._panic_wander(obstacles)
            
            # Visuaalinen tärinä jos ollaan oikeasti jumissa (BaseAI laskee counterin)
            if self.stuck_counter > 10:
                self.unit.rect.x += random.randint(-2, 2)
                self.unit.rect.y += random.randint(-2, 2)
            
            return

        # 2. Rauhan ajan toiminta (Ei uhkia)
        self.unit.set_sprinting(False)

        # Vastausvuoro käsitellään tilasta riippumatta (myös kesken työn)
        if self.pending_reply:
            text, delay = self.pending_reply
            if delay <= 0:
                if manager:
                    manager.vfx.create_speech_bubble(self.unit, text, duration=200)
                self.pending_reply = None
            else:
                self.pending_reply = (text, delay - 1)

        # Keskustelun ajan seistään paikallaan kasvokkain
        if self.chat_freeze > 0:
            self.chat_freeze -= 1
            self.unit.animation_state = "idle"
            return

        # Tilakoneen vaihto
        if self.state_timer <= 0:
            # Priorisoidaan työt
            if self._find_farm_work(all_units, manager):
                self.state = STATE_WORK
            else:
                roll = random.random()
                if roll < self.work_ethic:
                    self.state = STATE_WORK
                    self.state_timer = random.randint(120, 300) # 2-5 sekuntia töitä
                    self.unit.animation_state = "working"
                else:
                    self.state = STATE_IDLE
                    self.state_timer = random.randint(60, 180) # 1-3 sekuntia haahuilua
                    self.unit.animation_state = "idle"

        # Toiminta tilan mukaan
        if self.state == STATE_WORK:
            # Mene kohteeseen, tee työtä ja tuota kylän varastoon
            self._handle_work(obstacles, all_units, manager)
            
        elif self.state == STATE_IDLE:
            # Oletus: Idle
            self.unit.animation_state = "idle"
            
            if self.allow_idle_wander:
                # Arvo uusi kohde jos ei ole
                if not self.wander_target:
                    if self.wander_timer > 0:
                        self.wander_timer -= 1 # Odotetaan paikallaan
                    elif random.random() < 0.02: # 2% mahdollisuus lähteä liikkeelle
                        # Valitse satunnainen kohde läheltä
                        rx = self.unit.rect.centerx + random.randint(-400, 400)
                        ry = self.unit.rect.centery + random.randint(-400, 400)
                        # Varmista että pysyy kartalla
                        if manager and manager.current_arena:
                            rx = max(50, min(rx, manager.current_arena.width - 50))
                            ry = max(50, min(ry, manager.current_arena.height - 50))
                        self.wander_target = (rx, ry)
                        self.wander_timer = 400 # Max aika kävellä
                
                # Liiku kohteeseen
                if self.wander_target:
                    self.unit.animation_state = "run"
                    self.navigate_to(self.wander_target, obstacles, all_units, manager)
                    self.wander_timer -= 1
                    
                    # Perillä?
                    dist = math.hypot(self.wander_target[0] - self.unit.rect.centerx, 
                                      self.wander_target[1] - self.unit.rect.centery)
                    
                    # Lopeta jos perillä, aika loppui tai jumissa
                    if dist < 40 or self.wander_timer <= 0 or self.stuck_counter > 5:
                        self.wander_target = None
                        self.wander_timer = random.randint(60, 200) # Tauko ennen seuraavaa liikettä
                        self.unit.animation_state = "idle"
            
            self._try_talk(manager)

        # --- STUCK DETECTION (Moved here to run in all states) ---
        # Check every 20 frames
        if self.state_timer % 20 == 0:
            dist_moved = math.hypot(self.unit.rect.centerx - self.last_pos_check[0], self.unit.rect.centery - self.last_pos_check[1])
            if dist_moved < 2: # If moved less than 2 pixels
                self.stuck_counter += 1
            else:
                self.stuck_counter = 0
            self.last_pos_check = self.unit.rect.center
            
            if self.stuck_counter > 3: # Stuck for over a second
                # BUGIKORJAUS: kohde on vapautettava, muuten esim. CropPlotin
                # being_worked_on jää ikilukkoon ja pellot eivät koskaan
                # tule kenenkään korjattaviksi
                self._clear_work_target()
                self.state = STATE_IDLE # Force re-evaluation of target
                self.state_timer = 1

    def _clear_work_target(self):
        """Vapauttaa nykyisen työkohteen."""
        if self.work_target and hasattr(self.work_target, "being_worked_on"):
            self.work_target.being_worked_on = False
        self.work_target = None

    def _find_nearest_threat(self, all_units, limit_dist=9999):
        closest = None
        min_dist = 9999
        my_team = self.unit.team_color
        mx, my = self.unit.rect.center
        
        for u in all_units:
            if u.is_dead or u == self.unit: continue
            if u.team_color == my_team: continue # Oma tiimi on turvallinen
            
            d = math.hypot(u.rect.centerx - mx, u.rect.centery - my)
            if d < min_dist and d < limit_dist:
                min_dist = d
                closest = u
        return closest

    def move_away_from(self, target, all_units, obstacles):
        # Jos suunta on lukittu, käytä vanhaa jitteriä hetki
        if self.direction_lock_timer > 0:
            dx = self.flee_jitter.x
            dy = self.flee_jitter.y
            dist = math.hypot(dx, dy) or 1
            self._move_towards(dx, dy, dist, obstacles, all_units)
            return

        tx, ty = target.rect.center
        mx, my = self.unit.rect.center
        dx = mx - tx # Vektori poispäin
        dy = my - ty
        
        # Lisätään satunnaisuutta pakenemiseen
        jitter_x = random.uniform(-0.5, 0.5) * 100
        jitter_y = random.uniform(-0.5, 0.5) * 100
        
        dx += jitter_x
        dy += jitter_y
        
        # Lukitaan tämä suunta hetkeksi (esim. 20 framea), jotta ei tärise
        self.direction_lock_timer = 20
        self.flee_jitter = pygame.math.Vector2(dx, dy)
        
        dist = math.hypot(dx, dy) or 1
        self._move_towards(dx, dy, dist, obstacles, all_units)

    def _move_strongly_towards(self, target, dist, obstacles, all_units):
        """Aggressiivisempi liikkuminen seuraamista varten (vähemmän väistelyä)."""
        dx = target.rect.centerx - self.unit.rect.centerx
        dy = target.rect.centery - self.unit.rect.centery
        
        ndx = dx / dist
        ndy = dy / dist
        
        # Vähemmän separationia (4.0 -> 1.0), enemmän targetia (1.0 -> 2.0)
        sep_x, sep_y = self._calculate_separation(all_units)
        obs_x, obs_y = self._calculate_obstacle_avoidance(obstacles)
        
        final_dx = (ndx * 2.0) + (sep_x * 1.0) + (obs_x * 3.0)
        final_dy = (ndy * 2.0) + (sep_y * 1.0) + (obs_y * 3.0)
        
        l = math.hypot(final_dx, final_dy) or 1
        speed = self.unit.speed
        
        move_x = (final_dx / l) * speed
        move_y = (final_dy / l) * speed
        
        self.unit.check_wall_collision(move_x, move_y, obstacles)
        if abs(move_x) > 0.1:
            self.unit.facing_right = (move_x > 0)

    def _panic_wander(self, obstacles):
        # Juokse satunnaiseen suuntaan kunnes rauhoittuu
        if self.direction_lock_timer <= 0:
            angle = random.random() * math.tau
            self.flee_jitter = pygame.math.Vector2(math.cos(angle) * 100, math.sin(angle) * 100)
            self.direction_lock_timer = 30
        
        dx, dy = self.flee_jitter.x, self.flee_jitter.y
        self._move_towards(dx, dy, 100, obstacles, [])

    def _try_talk(self, manager, phrases=None):
        if not manager: return

        if self.speech_timer <= 0 and random.random() < 0.005: # 0.5% per frame (harvemmin)
            self.speech_timer = random.randint(500, 1000) # 8-16s hiljaisuus

            # Etsi keskustelukumppani (lähellä oleva joutilas villager)
            partner = None
            for u in manager.all_units:
                if u is self.unit or getattr(u, "is_dead", False): continue
                if u.team_color != self.unit.team_color: continue
                ai = getattr(u, "ai_controller", None)
                if not isinstance(ai, VillagerAI): continue
                if ai.state not in (STATE_IDLE, STATE_WORK): continue
                if math.hypot(u.rect.centerx - self.unit.rect.centerx,
                              u.rect.centery - self.unit.rect.centery) < 150:
                    partner = u
                    break

            topic = random.choice(list(DIALOGUE_TOPICS.keys()))
            lines = DIALOGUE_TOPICS[topic]

            if partner:
                # --- PARIKESKUSTELU ---
                # Molemmat pysähtyvät ja kääntyvät toisiaan kohti
                self.chat_freeze = 260
                self.wander_target = None
                self.unit.facing_right = (partner.rect.centerx > self.unit.rect.centerx)

                p_ai = partner.ai_controller
                p_ai.chat_freeze = 260
                p_ai.wander_target = None
                p_ai.speech_timer = max(p_ai.speech_timer, 400)
                partner.facing_right = (self.unit.rect.centerx > partner.rect.centerx)

                # Aloittaja puhuu heti, kumppani vastaa samasta aiheesta
                opener = random.choice(lines)
                reply = random.choice([l for l in lines if l != opener] or lines)
                manager.vfx.create_speech_bubble(self.unit, opener, duration=200)
                p_ai.pending_reply = (reply, random.randint(90, 140))
            elif random.random() < 0.3: # Puhu yksikseen harvemmin
                manager.vfx.create_speech_bubble(self.unit, random.choice(lines), duration=180)

    def _find_farm_work(self, all_units, manager):
        """Etsii maatilan töitä ja asettaa tilan ja kohteen."""
        if not manager or not manager.current_arena: return False
        
        # Etsitään vain kohde, jonka luona "näytellään" työntekoa.
        # Ei tarkisteta onko kohde tyhjä tai varattu.

        # --- TYÖT ROOLIN MUKAAN ---
        # HUOM: Kynnysarvot jättävät pelaajalle aina kerättävää!
        # Villagerit tarttuvat vain "ylimäärään".

        # 1. FARMER (Maanviljelijä)
        if self.job == "Farmer":
            cows = [u for u in all_units if isinstance(u, Cow) and not u.is_dead]
            milkable = [c for c in cows if getattr(c, "milk_ready", False)]
            manure = [p for p in manager.current_arena.props if isinstance(p, Manure)]
            eggs = [p for p in manager.current_arena.props if isinstance(p, Egg)]

            # a) Lypsä VAIN jos maitolehmiä on useita (pelaajalle jää)
            if len(milkable) >= 2:
                self.work_target = random.choice(milkable)
                self.work_type = "milk"
                self._equip_tool("bucket")
                self.state_timer = random.randint(300, 500)
                return True
            # b) Siivoa lantaa VAIN jos sitä on runsaasti
            if len(manure) > 10:
                self.work_target = random.choice(manure)
                self.work_type = "clean"
                self._equip_tool("bucket")
                self.state_timer = random.randint(200, 400)
                return True
            # c) Kerää munia VAIN jos niitä lojuu paljon
            if len(eggs) >= 5:
                self.work_target = random.choice(eggs)
                self.work_type = "collect_egg"
                self.state_timer = random.randint(150, 300)
                return True
            # d) Muuten hoivaa lehmiä (ei tuota mitään)
            if cows:
                self.work_target = random.choice(cows)
                self.work_type = "farm"
                self._equip_tool("bucket")
                self.state_timer = random.randint(300, 600)
                return True

        # 2. SCAVENGER (Romunkerääjä)
        if self.job == "Scavenger":
            # Romukasat
            scrap_piles = [p for p in manager.current_arena.props if isinstance(p, (ScrapPileBig, ScrapPile))]
            if scrap_piles:
                self.work_target = random.choice(scrap_piles)
                self.work_type = "scavenge"
                self._equip_tool("pickaxe")
                self.state_timer = random.randint(300, 600)
                return True

        # 3. LUMBERJACK (Metsuri)
        if self.job == "Lumberjack":
            # Puunhakkuu
            trees = [p for p in manager.current_arena.props if isinstance(p, MuckfordTree)]
            if trees:
                self.work_target = random.choice(trees)
                self.work_type = "chop"
                self._equip_tool("axe")
                self.state_timer = random.randint(300, 600)
                return True

        # 4. LABORER (Työläinen)
        if self.job == "Laborer":
            # Etsi jokin rakennus tai kaivo
            targets = [p for p in manager.current_arena.props if isinstance(p, (Well, Smeltery, FarmStorage))]
            if targets:
                self.work_target = random.choice(targets)
                self.work_type = "build"
                self._equip_tool("bucket") # Tai vasara jos olisi
                self.state_timer = random.randint(200, 500)
                return True

        return False

    def _handle_work(self, obstacles, all_units, manager):
        """
        Mene kohteeseen -> Työskentele (animaatio + ääni) -> Kun valmis,
        tuota resurssi kylän varastoon (city_storage).
        Kynnysarvot _find_farm_workissa varmistavat, että pelaajalle jää
        aina kerättävää.
        """
        if not self.work_target:
            self.state = STATE_IDLE
            return

        self.unit.animation_state = "run"

        # 1. Liiku kohteeseen
        final_target_pos = self.work_target.rect.center
        current_target_pos = self._get_nav_target(final_target_pos, manager)
        self.navigate_to(current_target_pos, obstacles, all_units, manager)

        # 2. Tarkista etäisyys
        dist_to_final = math.hypot(final_target_pos[0] - self.unit.rect.centerx, final_target_pos[1] - self.unit.rect.centery)

        if dist_to_final < 60:
            # 3. Perillä: Työskentele
            self.state_timer -= 1

            # Käänny kohti työtä
            dx = self.work_target.rect.centerx - self.unit.rect.centerx
            if abs(dx) > 1: self.unit.facing_right = (dx > 0)

            # Animaatio ja äänet tyypin mukaan
            if self.work_type == "chop":
                self.unit.animation_state = "attack" # Hakkaa
                if self.state_timer % 45 == 0: # Joka 0.75s
                    from sound_manager import sound_system
                    sound_system.play_sound("axe_1")
                    if manager: manager.vfx.create_falling_leaves(self.work_target.rect.centerx, self.work_target.rect.centery)

            elif self.work_type == "scavenge":
                self.unit.animation_state = "attack" # Hakkaa/Tonkii
                if self.state_timer % 60 == 0:
                    from sound_manager import sound_system
                    sound_system.play_sound("mining_hit")
                    if manager: manager.vfx.create_dust_cloud(self.work_target.rect.centerx, self.work_target.rect.centery)

            elif self.work_type in ("farm", "milk"):
                self.unit.animation_state = "working"
                if self.state_timer % 120 == 0:
                    from sound_manager import sound_system
                    sound_system.play_sound("moo") # Lehmä vastaa

            else:
                self.unit.animation_state = "working"

            # 4. Kun aika loppuu: tuota resurssi ja lopeta
            if self.state_timer <= 0:
                self._finish_work(manager)
                self.state = STATE_IDLE
                self._clear_work_target()

    def _finish_work(self, manager):
        """Työ valmis: vie tuotos kylän varastoon ja päivitä maailma."""
        if not manager or not self.work_target:
            return
        t = self.work_target
        storage = manager.city_storage

        def deposit(name, amount=1):
            storage[name] = storage.get(name, 0) + amount
            manager.vfx.show_damage(self.unit.rect.centerx, self.unit.rect.top - 30,
                                    f"+{amount} {name}", color=(180, 220, 180))

        if self.work_type == "milk":
            # Lypsä vain jos maito on yhä valmiina (pelaaja voi ehtiä ensin)
            if getattr(t, "milk_ready", False):
                t.milk_ready = False
                deposit("Milk")

        elif self.work_type == "clean":
            # Poista lantaläjä maailmasta (jos pelaaja ei ehtinyt ensin)
            if t in manager.current_arena.props:
                manager.current_arena.props.remove(t)
                if t in manager.all_units:
                    manager.all_units.remove(t)
                deposit("Manure")

        elif self.work_type == "collect_egg":
            if t in manager.current_arena.props:
                manager.current_arena.props.remove(t)
                if t in manager.all_units:
                    manager.all_units.remove(t)
                deposit("Egg")

        elif self.work_type == "chop":
            # Puu tuottaa kylälle, mutta EI kuluta pelaajan hakattavia
            # osumia loppuun (jätetään aina vähintään 2)
            hits = getattr(t, "current_hits", None)
            if hits is not None and hits > 2:
                t.current_hits -= 1
            deposit(getattr(t, "resource_name", "Swamp Wood"))

        elif self.work_type == "scavenge":
            if not getattr(t, "is_empty", False):
                deposit("Scrap")
        # "farm" (hoiva) ja "build" eivät tuota mitään

    def _equip_tool(self, tool_type):
        """Etsii inventoryssa olevan työkalun ja laittaa sen käteen."""
        if not hasattr(self.unit, "inventory"): return
        
        for item in self.unit.inventory:
            # Yksinkertainen tarkistus nimen tai tyypin perusteella
            name = getattr(item, "name", "").lower()
            grp = str(getattr(item, "weapon_group", "") or "").lower()
            itype = str(getattr(item, "tool_type", "") or "").lower()
            
            is_match = False
            
            if itype == tool_type:
                is_match = True
            elif tool_type == "bucket" and "bucket" in name:
                is_match = True
            elif tool_type == "axe" and "pickaxe" in name:
                is_match = False
            elif tool_type in name or (grp and tool_type in grp):
                is_match = True

            if is_match:
                # HACK: Pakotetaan mastery, jotta Gladiator-luokka suostuu varustamaan esineen
                # (Muuten tulee "Requires Axe Training" virhe ja varustus epäonnistuu)
                if grp: self.unit.weapon_masteries.add(grp)
                self.unit.weapon_masteries.update(["axe", "pickaxe", "mace", "tool"])
                
                self.unit.equip_item(item)
                return

    def _navigate_to_target(self, target_pos, obstacles, manager):
        """Navigoi kohteeseen (käyttäen portteja tarvittaessa)."""
        nav_pos = self._get_nav_target(target_pos, manager)
        all_units = manager.all_units if manager else []
        self.navigate_to(nav_pos, obstacles, all_units, manager)

    def _find_random_building(self, manager):
        if manager and manager.current_arena:
            buildings = [p for p in manager.current_arena.props if getattr(p, "is_structure", False)]
            if buildings:
                return random.choice(buildings)
        return None

    def _get_nav_target(self, final_pos, manager):
        """Palauttaa seuraavan liikkumiskohteen (portti tai lopullinen kohde).

        BUGIKORJAUS: yksi porttipiste ajoi NPC:t viistosti päin aitaa.
        Nyt portti ylitetään kahdessa vaiheessa: ensin oman puolen
        porttipisteelle (aukon kohdalle), sitten läpi toiselle puolelle."""
        farm_rect = getattr(manager.current_arena, "farm_area", None)
        gate_pos = getattr(manager.current_arena, "farm_gate_pos", None)

        if not farm_rect or not gate_pos:
            return final_pos

        my_in_farm = farm_rect.collidepoint(self.unit.rect.center)
        target_in_farm = farm_rect.collidepoint(final_pos)

        if my_in_farm == target_in_farm:
            return final_pos

        gx, gy = gate_pos
        # Portti voi olla ylä- tai alareunassa: valitse pisteet sen mukaan
        if abs(gy - farm_rect.bottom) < abs(gy - farm_rect.y):
            outside_pt = (gx, farm_rect.bottom + 70)
            inside_pt = (gx, farm_rect.bottom - 80)
        else:
            outside_pt = (gx, farm_rect.y - 70)
            inside_pt = (gx, farm_rect.y + 80)

        own_side = inside_pt if my_in_farm else outside_pt
        # Kohdista ensin aukon x-linjalle omalla puolella, sitten läpi
        if abs(self.unit.rect.centerx - gx) > 60:
            return own_side
        return outside_pt if my_in_farm else inside_pt

    def _move_towards_point(self, target_pos, obstacles, all_units):
        """Liikuttaa yksikköä kohti pistettä, väistellen esteitä."""
        dx = target_pos[0] - self.unit.rect.centerx
        dy = target_pos[1] - self.unit.rect.centery
        dist = math.hypot(dx, dy)

        if dist < 5: return # Lähellä, ei tarvitse liikkua

        ndx, ndy = dx / dist, dy / dist

        # Perusliike
        move_x = ndx * self.unit.speed
        move_y = ndy * self.unit.speed
        
        # --- STUCK RECOVERY ---
        if self.stuck_counter > 3:
            # Yritetään liikkua poispäin lähimmästä esteestä
            closest_obs = None
            min_dist = 60
            if obstacles:
                for obs in obstacles:
                    if self.unit.rect.colliderect(obs.rect.inflate(10, 10)):
                        d = math.hypot(self.unit.rect.centerx - obs.rect.centerx, self.unit.rect.centery - obs.rect.centery)
                        if d < min_dist:
                            min_dist = d
                            closest_obs = obs
            
            if closest_obs:
                odx = self.unit.rect.centerx - closest_obs.rect.centerx
                ody = self.unit.rect.centery - closest_obs.rect.centery
                odist = math.hypot(odx, ody) or 1
                # Lisätään voimakas työntö poispäin
                move_x += (odx / odist) * self.unit.speed * 2.0
                move_y += (ody / odist) * self.unit.speed * 2.0
            else:
                # Jos ei löydy estettä, liiku satunnaiseen suuntaan
                angle = random.random() * math.tau
                move_x = math.cos(angle) * self.unit.speed
                move_y = math.sin(angle) * self.unit.speed
            
            # Normalisoidaan nopeus
            total_speed = math.hypot(move_x, move_y) or 1
            if total_speed > self.unit.speed:
                scale = self.unit.speed / total_speed
                move_x *= scale
                move_y *= scale

        self.unit.check_wall_collision(move_x, move_y, obstacles)
        if abs(move_x) > 0.1:
            self.unit.facing_right = (move_x > 0)