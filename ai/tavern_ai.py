import pygame
import sys
import random
import math
from ai.life_ai import LifeAI, DIALOGUE_TOPICS
from sound_manager import sound_system
from assets.tiles.house_objects import InnFood, InnDrink, HouseDoor, InnBed, InnDoubleBed

class TavernAI(LifeAI):
    def __init__(self, unit):
        super().__init__(unit)
        
        self.ordering_type = None # "drink" tai "food"
        
        # Juominen
        self.has_drink = False
        self.drink_amount = 0
        
        # Syöminen
        self.has_food = False
        self.food_amount = 0
        
        self.carried_item = None # Visuaalinen objekti
        
        # Pelaajan lähestyminen
        self.seek_cooldown = random.randint(600, 2000) # Ei heti alussa
        self.waiting_for_player = False
        
        # Nukkuminen
        self.my_bed = None
        self.song_channel = None # Musiikkikanava

    def execute_ai(self, all_units, obstacles, manager=None):
        if self.unit.is_dead: return

        self.state_timer -= 1
        self.update_needs() # LifeAI hoitaa tarpeet
        
        if self.seek_cooldown > 0: self.seek_cooldown -= 1

        # --- REPLY LOGIC ---
        if self.reply_timer > 0:
            self.reply_timer -= 1
            if self.reply_timer <= 0:
                self._say_something(manager, is_reply=True)

        # --- STATE TRANSITIONS ---
        if self.state_timer <= 0:
            # Jos ollaan tilausjonossa, siirrytään juomaan (eikä päätetä uutta toimintoa)
            if self.state == "ordering_wait":
                # LUODAAN ESINE
                if self.ordering_type == "drink":
                    self.has_drink = True
                    self.drink_amount = 100
                    # Luo visuaalinen juoma
                    if manager and manager.current_arena:
                        drink_var = random.randint(1, 3)
                        self.carried_item = InnDrink(self.unit.rect.centerx, self.unit.rect.centery, drink_var)
                        manager.current_arena.props.append(self.carried_item)
                        
                    if manager:
                        manager.vfx.create_speech_bubble(self.unit, "Ah, ale!", duration=60)
                        
                elif self.ordering_type == "food":
                    self.has_food = True
                    self.food_amount = 100
                    # Luo visuaalinen ruoka
                    if manager and manager.current_arena:
                        food_var = random.randint(1, 3)
                        self.carried_item = InnFood(self.unit.rect.centerx, self.unit.rect.centery, food_var)
                        manager.current_arena.props.append(self.carried_item)
                        
                    if manager:
                        manager.vfx.create_speech_bubble(self.unit, "Finally, food.", duration=60)
                
                self._plan_find_seat(obstacles)
            
            # Jos istuminen loppuu (juoma loppu tai kyllästynyt)
            elif self.state == "sitting":
                # KORJAUS: Jos on ruokaa/juomaa jäljellä, ÄLÄ nouse pöydästä
                # FAILSAFE: Vähennä määrää reilusti joka kerta kun ajastin nollautuu, jotta ei istuta ikuisesti
                if self.has_drink or self.has_food:
                    if self.has_drink: self.drink_amount -= 40
                    if self.has_food: self.food_amount -= 40
                    
                    # Tarkista loppuiko nyt
                    if self.drink_amount <= 0: self.has_drink = False
                    if self.food_amount <= 0: self.has_food = False
                
                # Tarkista uudestaan vähennyksen jälkeen
                if self.has_drink or self.has_food:
                    self.state_timer = 200 # Jatka istumista
                else:
                    # Tuhoa esine jos jäi käteen (varmuuden vuoksi)
                    if self.carried_item:
                        if manager and manager.current_arena and self.carried_item in manager.current_arena.props:
                            manager.current_arena.props.remove(self.carried_item)
                        self.carried_item.kill()
                        self.carried_item = None
                    
                    # Nouse pöydästä
                    self.state = "idle"
                    self.state_timer = 60
                
            # UUSI: Jos lämmittely loppuu, nollaa kylmyys
            elif self.state == "warming":
                self.cold = 0
                self.state = "idle"
                self.state_timer = 60

            # UUSI: Jos juttelu loppuu, nollaa sosiaalinen tarve
            elif self.state == "chatting":
                self.social = 0
                self.state = "idle"
                self.state_timer = 60

            # Jos odotus pelaajalle loppuu (pelaaja ei reagoinut)
            elif self.state == "waiting_for_player":
                self.state = "idle"
                self.state_timer = 60

            # Jos nukkuminen loppuu (herää itsestään)
            elif self.state == "sleeping":
                self._wake_up()
                self.state = "idle"
                self.state_timer = 60

            # Jos poistuminen kestää liian kauan (jumissa), katoa
            elif self.state == "leaving":
                # Force remove jos jumissa
                self.state = "gone"

            # UUSI: Bardin esitys loppuu
            elif self.state == "performing":
                self.state = "idle"
                self.state_timer = 60
                self.stop_music()

            else:
                self._decide_next_action(obstacles, all_units, manager)

        # --- PÄIVITÄ KANNETTAVAN ESINEEN SIJAINTI ---
        if self.carried_item:
            self.carried_item.update_position(self.unit)

        # --- EXECUTE CURRENT STATE ---
        if self.state == "move_to":
            self._execute_move(obstacles, all_units, manager)
            
        elif self.state == "sleeping":
            self.unit.animation_state = "idle"
            # ZZZ efekti
            if manager and random.random() < 0.02:
                manager.vfx.create_speech_bubble(self.unit, "Zzz...", duration=60)
            # Piilota hahmoa hieman (nukkuu peiton alla / hämärässä)
            if self.unit.image: self.unit.image.set_alpha(150)

        elif self.state == "performing":
            self.unit.animation_state = "sing"
            
            # NUOTIT JA EFEKTIT
            if manager and random.random() < 0.05: # Joka 20. frame (n. 3 kertaa sekunnissa)
                # Nuotti pään yläpuolelle
                nx = self.unit.rect.centerx + random.randint(-10, 10)
                ny = self.unit.rect.top - 10
                manager.vfx.create_musical_note(nx, ny)

        elif self.state == "ordering_wait":
            self.unit.animation_state = "idle"
            # Odotetaan state_timerin kulumista loppuun (siirtymä yllä)

        elif self.state == "sitting":
            self.unit.animation_state = "idle"
            
            # Juo satunnaisesti (jos on juomaa)
            if self.has_drink and self.drink_amount > 0:
                if random.random() < 0.02: # Nopeutettu lisää (oli 0.01)
                    self.drink_amount -= 20 # Nopeutettu (oli 15)
                    self.thirst = max(0, self.thirst - 20)
                    s_id = random.randint(1, 4)
                    sound_system.play_sound(f"drink_loop_{s_id}")
                    if manager:
                        # Visuaalinen efekti (teksti + roiskeet)
                        manager.vfx.show_damage(self.unit.rect.centerx, self.unit.rect.top - 40, "Gulp", color=(150, 200, 255))
                        manager.vfx.create_impact_sparks(self.unit.rect.centerx, self.unit.rect.centery - 10, color=(220, 200, 100), count=3)
                
                if self.drink_amount <= 0:
                    self.has_drink = False
                    self.thirst = random.randint(0, 20) # Ei nollaan, jotta jano palaa joskus
                    # Tuhoa juoma
                    if self.carried_item:
                        if manager.current_arena and self.carried_item in manager.current_arena.props:
                            manager.current_arena.props.remove(self.carried_item)
                        self.carried_item.kill()
                        self.carried_item = None

            # Syö satunnaisesti (jos on ruokaa)
            if self.has_food and self.food_amount > 0:
                if random.random() < 0.02: # Nopeutettu lisää
                    self.food_amount -= 20 # Nopeutettu
                    self.hunger = max(0, self.hunger - 20)
                    s_id = random.randint(1, 4)
                    sound_system.play_sound(f"eat_loop_{s_id}")
                    if manager:
                        # Visuaalinen efekti (teksti + murut)
                        manager.vfx.show_damage(self.unit.rect.centerx, self.unit.rect.top - 40, "Crunch", color=(200, 150, 100))
                        manager.vfx.create_impact_sparks(self.unit.rect.centerx, self.unit.rect.centery - 10, color=(160, 100, 60), count=3)
                
                # Lisää höyryä ruokaan jos sitä on jäljellä
                if random.random() < 0.1 and manager and hasattr(manager.current_arena, "vfx"):
                    if self.carried_item:
                        # Höyryä lautaselta
                        manager.current_arena.vfx.add_steam(self.carried_item.image_pos[0] + 12, self.carried_item.image_pos[1])

                if self.food_amount <= 0:
                    self.has_food = False
                    self.hunger = random.randint(0, 20)
                    # Tuhoa ruoka
                    if self.carried_item:
                        if manager.current_arena and self.carried_item in manager.current_arena.props:
                            manager.current_arena.props.remove(self.carried_item)
                        self.carried_item.kill()
                        self.carried_item = None
            
            # Juttele istuessa
            if self.chat_turns > 0:
                self._execute_chat(manager)
            elif self.social > 35: # KORJAUS: Puhuvat hieman harvemmin (oli 20)
                self._find_neighbor_to_chat(all_units, manager)

        elif self.state == "warming":
            self.unit.animation_state = "idle"
            if self.target_obj:
                # Käänny kohti tulta
                self.unit.facing_right = (self.target_obj.rect.centerx > self.unit.rect.centerx)

        elif self.state == "chatting":
            self._execute_chat(manager)
            # Pidä hahmo paikallaan jos keskustelu on kesken
            if self.chat_turns > 0 or self.reply_timer > 0:
                # Estä tilan vaihtuminen (idleksi)
                self.state_timer = max(self.state_timer, 100)

        elif self.state == "idle":
            self.unit.animation_state = "idle"
            
        elif self.state == "seeking_player":
            self._execute_seek_player(obstacles, all_units, manager)
            
        elif self.state == "waiting_for_player":
            self.unit.animation_state = "idle"
            # Käänny kohti pelaajaa
            if manager and manager.player_character:
                self.unit.facing_right = (manager.player_character.rect.centerx > self.unit.rect.centerx)

        # Muut tilat (idle, leaving) hoitaa LifeAI tai BaseAI
        elif self.state == "leaving":
            self._execute_move(obstacles, all_units, manager)

    def _decide_next_action(self, obstacles, all_units, manager=None):
        # Nollaa kumppani
        self.conversation_partner = None
        
        # KORJAUS: Jos on juomaa tai ruokaa kädessä, etsi istumapaikka (prioriteetti 1)
        if self.has_drink or self.has_food:
            self._plan_find_seat(obstacles)
            return
        
        # BARD LOGIC: Jos nimi on Bard, esiinny välillä
        if self.unit.name == "Bard":
            if random.random() < 0.2: # Hieman harvemmin, koska liikkuminen vie aikaa
                self._plan_perform(obstacles)
                # Jos tila on heti performing (esim. ei takkaa), laula heti
                if self.state == "performing":
                    self._sing_song(manager)
                return
        
        # Prioriteetti: Jano/Nälkä > Kylmä > Sosiaalinen > Idle
        if self.thirst > 80 and not self.has_drink:
            self._plan_get_drink(obstacles)
        elif self.hunger > 80 and not self.has_food:
            self._plan_get_food(obstacles)
        elif self.tiredness > 90:
            self._plan_sleep(obstacles)
        elif self.cold > 70:
            self._plan_warm_up(obstacles)
        elif self.social > 70: # KORJAUS: Hieman korkeampi kynnys (oli 60)
            self._plan_socialize(obstacles, all_units)
        elif self.seek_cooldown <= 0 and random.random() < 0.05: # 5% mahdollisuus jos cooldown ohi
            self._plan_approach_player()
        elif random.random() < 0.005: # Pieni mahdollisuus lähteä pois (jos ei ole recruit)
            # Vain Villagerit lähtevät, Recruitit pysyvät
            if isinstance(self.unit, getattr(sys.modules[__name__], "Villager", type(None))): # Hacky check or check class name
                if "Villager" in self.unit.__class__.__name__:
                    self._plan_leave(obstacles)
                    return
            self._plan_wander(obstacles)
        else:
            self._plan_wander(obstacles)

    def request_performance(self, obstacles, manager):
        """Pelaaja pyysi biisiä (maksua vastaan)."""
        # Heitä ruoat/juomat pois heti
        self.has_food = False
        self.has_drink = False
        if self.carried_item:
            if manager and manager.current_arena and self.carried_item in manager.current_arena.props:
                manager.current_arena.props.remove(self.carried_item)
            self.carried_item.kill()
            self.carried_item = None
            
        self._plan_perform(obstacles)
        # Pakota tila heti, jos ollaan jo lähellä, tai anna move_to hoitaa
        if manager:
            manager.vfx.create_speech_bubble(self.unit, "With pleasure!", duration=90)

    def _plan_perform(self, obstacles):
        # Etsi takka (Fireplace)
        fires = [o for o in obstacles if "Fireplace" in o.__class__.__name__]
        if fires:
            target = random.choice(fires)
            self.target_obj = target
            # Mene takan viereen (oikealle puolelle ja hieman eteen)
            self.target_pos = (target.rect.right + 30, target.rect.bottom + 20)
            self.state = "move_to"
            self.next_state = "performing"
            self.state_timer = 500
        else:
            # Ei takkaa, esiinny tässä
            self.state = "performing"
            self.state_timer = 1800 # 30 sekuntia (pidempi sessio)

    def stop_music(self):
        if self.song_channel:
            self.song_channel.stop()
            self.song_channel = None

    def _sing_song(self, manager):
        if not manager: return
        songs = [
            "♫ The Rat King gnaws on bones of old... ♫",
            "♫ Muckford's mud is deep and cold... ♫",
            "♫ The Vortex swirls in violet hue... ♫",
            "♫ Heroes rise, but debts are due... ♫"
        ]
        manager.vfx.create_speech_bubble(self.unit, random.choice(songs), duration=200)
        
        # Soita musiikkia
        self.stop_music() # Pysäytä edellinen jos on
        song_id = random.randint(1, 4)
        self.song_channel = sound_system.play_sound(f"bard_song_{song_id}", loops=-1)

    def _plan_leave(self, obstacles):
        # Etsi uloskäynti (TavernMenussa määritelty exit_rect, mutta tässä arvioidaan)
        # Oletetaan että ovi on alhaalla keskellä (kuten TavernMenussa)
        # Koordinaatit: width/2, height - 50. Arvioidaan width=1800 -> 900, 1250
        self.target_pos = (900, 1250)
        self.state = "leaving"
        self.state_timer = 1000 # Aikaa poistua
        self.next_state = "gone"

    def _plan_sleep(self, obstacles):
        # Etsi vapaa sänky
        beds = [o for o in obstacles if isinstance(o, (InnBed, InnDoubleBed))]
        free_beds = [b for b in beds if b.occupied_by is None]
        
        if free_beds:
            target = random.choice(free_beds)
            self.target_obj = target
            # Varaa sänky heti ettei muut mene sinne
            target.occupied_by = self.unit
            self.my_bed = target
            
            self.target_pos = (target.rect.centerx, target.rect.centery)
            self.state = "move_to"
            self.next_state = "sleeping"
            self.state_timer = 600
        else:
            # Ei sänkyjä, haahuile
            self.tiredness -= 10 # Vähennä vähän ettei jumita loopissa
            self._plan_wander(obstacles)

    def _wake_up(self):
        self.tiredness = 0
        if self.my_bed:
            self.my_bed.occupied_by = None
            self.my_bed = None
        if self.unit.image: self.unit.image.set_alpha(255)
        self.state = "idle"

    def _plan_approach_player(self):
        # Yritetään lähestyä pelaajaa
        self.state = "seeking_player"
        self.state_timer = 600 # 10 sekuntia aikaa löytää
        self.seek_cooldown = random.randint(3000, 6000) # Pitkä cooldown ettei spammaa

    def _execute_seek_player(self, obstacles, all_units, manager):
        if not manager or not manager.player_character:
            self.state = "idle"
            return
            
        target = manager.player_character
        dist = math.hypot(target.rect.centerx - self.unit.rect.centerx, 
                          target.rect.centery - self.unit.rect.centery)
        
        if dist < 70:
            # Perillä
            self.state = "waiting_for_player"
            self.state_timer = 300 # Odota 5 sekuntia vastausta
            
            # Sano jotain
            lines = ["Commander?", "A word?", "Excuse me.", "Hey you.", "Got a minute?"]
            if manager.reputation > 500:
                lines = ["Commander!", "An honor.", "Sir?", "May I speak?"]
            
            manager.vfx.create_speech_bubble(self.unit, random.choice(lines), duration=120)
            
            # Soita reaktioääni (huomio)
            s_id = random.randint(1, 4)
            sound_system.play_sound(f"reaction_{s_id}")
        else:
            # Liiku kohti
            dx = target.rect.centerx - self.unit.rect.centerx
            dy = target.rect.centery - self.unit.rect.centery
            self._move_towards(dx, dy, dist, obstacles, all_units)

    def _plan_get_drink(self, obstacles):
        # Etsi tiski (Counter)
        counters = [o for o in obstacles if "Counter" in o.__class__.__name__]
        if counters:
            target = random.choice(counters)
            self.target_obj = target
            # Mene satunnaiseen kohtaan tiskin eteen
            offset_x = random.randint(10, target.rect.w - 10)
            offset_y = random.randint(30, 60) # Vaihtelua syvyyssuunnassa
            self.target_pos = (target.rect.x + offset_x, target.rect.bottom + offset_y)
            self.state = "move_to"
            self.next_state = "ordering"
            self.state_timer = 400
            self.ordering_type = "drink"
        else:
            self.state = "idle"
            self.state_timer = 60

    def _plan_get_food(self, obstacles):
        # Etsi tiski (Counter) - sama paikka kuin juomalle
        counters = [o for o in obstacles if "Counter" in o.__class__.__name__]
        if counters:
            target = random.choice(counters)
            self.target_obj = target
            # Mene satunnaiseen kohtaan tiskin eteen
            offset_x = random.randint(10, target.rect.w - 10)
            offset_y = random.randint(30, 60)
            self.target_pos = (target.rect.x + offset_x, target.rect.bottom + offset_y)
            self.state = "move_to"
            self.next_state = "ordering"
            self.state_timer = 400
            self.ordering_type = "food"
        else:
            self.state = "idle"
            self.state_timer = 60

    def _plan_find_seat(self, obstacles):
        # Etsi pöytä
        tables = [o for o in obstacles if "Table" in o.__class__.__name__]
        if tables:
            target = random.choice(tables)
            self.target_obj = target
            # Satunnainen kohta pöydän ympärillä
            # KORJAUS: Kasvatetaan sädettä (80px), jotta ei mennä pöydän sisään tärisemään
            radius = 85 
            angle = random.uniform(0, 6.28)
            self.target_pos = (target.rect.centerx + math.cos(angle)*radius, target.rect.centery + math.sin(angle)*radius)
            self.state = "move_to"
            self.next_state = "sitting"
            self.state_timer = 400
        else:
            # Ei pöytiä, seisoskele jossain
            self._plan_wander(obstacles)
            self.next_state = "sitting"

    def _plan_warm_up(self, obstacles):
        # Etsi takka (Fireplace)
        fires = [o for o in obstacles if "Fireplace" in o.__class__.__name__]
        if fires:
            target = random.choice(fires)
            self.target_obj = target
            # Satunnainen sijainti takan edessä (ettei kaikki mene samaan pisteeseen)
            offset_x = random.randint(-60, 60)
            offset_y = random.randint(40, 90)
            self.target_pos = (target.rect.centerx + offset_x, target.rect.bottom + offset_y)
            self.state = "move_to"
            self.next_state = "warming"
            self.state_timer = 400
        else:
            self.state = "idle"
            self.state_timer = 60

    def _plan_socialize(self, obstacles, all_units):
        tables = [o for o in obstacles if "Table" in o.__class__.__name__]
        
        # Yritä mennä pöytään (70% todennäköisyys)
        if tables and random.random() < 0.7:
            target = random.choice(tables)
            self.target_obj = target
            radius = 85
            angle = random.uniform(0, 6.28)
            self.target_pos = (target.rect.centerx + math.cos(angle)*radius, target.rect.centery + math.sin(angle)*radius)
            self.state = "move_to"
            self.next_state = "chatting"
            self.state_timer = 400
            self.chat_turns = random.randint(6, 12) # Pitkä keskustelu
        else:
            # Etsi kaveri
            friends = [u for u in all_units if u != self.unit and not u.is_dead and u.name != "Commander" and u.name != "Marda Shant"]
            if friends:
                target = random.choice(friends)
                self.conversation_partner = target
                # Mene lähelle
                self.target_pos = (target.rect.centerx + random.choice([-40, 40]), target.rect.centery)
                self.state = "move_to"
                self.next_state = "chatting"
                self.state_timer = 400
                self.chat_turns = random.randint(6, 12)
            else:
                self.state = "idle"
                self.state_timer = 60

    def _plan_wander(self, obstacles):
        self.state = "move_to"
        self.next_state = "idle"
        self.state_timer = random.randint(150, 300) # Satunnainen kesto
        # Satunnainen piste (karkea arvio alueesta)
        self.target_pos = (random.randint(200, 1600), random.randint(200, 1100))

    def _on_arrive(self, manager):
        if self.next_state == "ordering":
            self.state = "ordering_wait" # Odotetaan hetki ennen juomista
            self.state_timer = 60 # 1 sekunti
            if manager: 
                if self.ordering_type == "drink":
                    shout = random.choice(["Ale!", "Mead!", "Beer!", "Thirsty!", "More!", "Grog!", "Barkeep!"])
                else:
                    shout = random.choice(["Stew!", "Meat!", "Bread!", "Hungry!", "Food!", "Service!"])
                manager.vfx.create_speech_bubble(self.unit, shout, duration=90)
                
                # Soita reaktioääni (tilaus)
                s_id = random.randint(1, 4)
                sound_system.play_sound(f"reaction_{s_id}")
        elif self.next_state == "sleeping":
            self.state = "sleeping"
            self.state_timer = random.randint(1000, 2000) # Nuku pitkään
        elif self.next_state == "sitting":
            self.state = "sitting"
            self.state_timer = random.randint(600, 1200) # Istu 10-20s
            if self.target_obj:
                self.unit.facing_right = (self.target_obj.rect.centerx > self.unit.rect.centerx)
        elif self.next_state == "warming":
            self.state = "warming"
            self.state_timer = 300
        elif self.next_state == "chatting":
            self.state = "chatting"
            self.state_timer = 300
        elif self.next_state == "idle":
            self.state = "idle"
            self.state_timer = 60
        elif self.next_state == "performing":
            self.state = "performing"
            self.state_timer = 1800 # 30 sekuntia
            self._sing_song(manager)
            self.unit.facing_right = False # Käänny yleisöön (vasemmalle)
        elif self.next_state == "gone":
            self.state = "gone"
        else:
            self.state = "idle"
            self.state_timer = 60
        self.next_state = None

    def _execute_chat(self, manager):
        self.unit.animation_state = "idle"
        
        # Käänny kumppania tai kohdetta kohti
        if self.conversation_partner:
            self.unit.facing_right = (self.conversation_partner.rect.centerx > self.unit.rect.centerx)
        elif self.target_obj:
            self.unit.facing_right = (self.target_obj.rect.centerx > self.unit.rect.centerx)

        # Puhu ajoittain (esim. kun timer on 250)
        # Vain jos ei olla vastaamassa juuri nyt
        if self.state_timer == 250 and manager and self.reply_timer <= 0:
            # Jos ollaan yksin, puhutaan harvemmin (ei spammia)
            if not self.conversation_partner:
                if random.random() < 0.2: # 20% mahdollisuus yksinpuheluun
                    self._say_something(manager)
            else:
                # Jos on kaveri, aloitetaan keskustelu
                self._say_something(manager)

    def receive_chat(self, sender, topic=None):
        """Toinen hahmo puhui minulle."""
        # Älä keskeytä juomista
        if self.state in ["drinking", "ordering"]: return

        self.conversation_partner = sender
        self.current_topic = topic

        self.state = "chatting" # Pakota kuuntelutilaan
        self.state_timer = max(self.state_timer, 200) # Pysy paikallaan hetki
        
        # Käänny puhujaa kohti
        if sender:
            self.unit.facing_right = (sender.rect.centerx > self.unit.rect.centerx)
        # Vastaa viiveellä (n. 2-3 sekuntia, jotta ehtii lukea edellisen)
        self.reply_timer = random.randint(200, 300) # Hitaampi tahti (3-5s)
        
    def _find_neighbor_to_chat(self, all_units, manager):
        for u in all_units:
            if u != self.unit and not u.is_dead and u.name != "Commander" and u.name != "Marda Shant":
                dist = math.hypot(u.rect.centerx - self.unit.rect.centerx, u.rect.centery - self.unit.rect.centery)
                if dist < 150: # KORJAUS: Kasvatettu sädettä (oli 120)
                    self.conversation_partner = u
                    self.chat_turns = random.randint(4, 8)
                    self._say_something(manager)
                    return

    def _get_player_comment(self, manager):
        if not manager or not manager.player_character: return None
        
        player = manager.player_character
        dist = math.hypot(player.rect.centerx - self.unit.rect.centerx, 
                          player.rect.centery - self.unit.rect.centery)
        
        # Only react if player is somewhat close
        if dist > 400: return None
        
        rep = manager.reputation
        chance = 0.05 # Base chance
        
        if rep > 100: chance += 0.1
        if rep > 500: chance += 0.2
        if rep > 1000: chance += 0.4
        
        # If very close, higher chance
        if dist < 150: chance += 0.3
        
        if random.random() > chance: return None
        
        lines = []
        
        # Reputation lines
        if rep < 50:
            lines.extend(["Who's that?", "New face.", "Fresh meat.", "Don't know him."])
        elif rep < 300:
            lines.extend(["That's the Commander.", "Heard they're okay.", "Not bad in the arena.", "Seen him fight."])
        elif rep < 1000:
            lines.extend(["Rising star!", "I'd bet on them.", "Looking strong, Commander.", "Good to see you."])
        else: # 1000+
            lines.extend(["The Legend!", "An honor, Commander.", "Drinks on me!", "The Champion is here!", "Everyone make way!"])
            
        # League Rank lines
        if hasattr(manager, "league_engine"):
            rank = manager.league_engine.get_player_rank()
            if rank == 1:
                lines.append("Rank 1! The King of the Pit.")
            elif rank <= 3:
                lines.append(f"Rank {rank}. So close to the top.")
            elif rank <= 10:
                lines.append(f"Rank {rank}. Not bad.")
            elif rank > 10:
                lines.append("Need to climb that ladder.")
                
        return random.choice(lines) if lines else None

    # Ylikirjoitetaan LifeAI:n metodi, jotta voidaan lisätä pelaajakommentit
    def _say_something(self, manager, is_reply=False):
        if not is_reply:
            player_comment = self._get_player_comment(manager)
            if player_comment:
                manager.vfx.create_speech_bubble(self.unit, player_comment, duration=240)
                return
        
        # Muuten käytä normaalia LifeAI:n logiikkaa
        super()._say_something(manager, is_reply)

        # Keskustelun jatkuminen (Ping-pong)
        if self.conversation_partner:
            # Tarkistetaan onko kumppanilla receive_chat
            ai = getattr(self.conversation_partner, "ai_controller", None)
            if ai and hasattr(ai, "receive_chat"):
                if self.chat_turns > 0:
                    self.chat_turns -= 1
                    ai.chat_turns = self.chat_turns
                    ai.receive_chat(self.unit, self.current_topic)
