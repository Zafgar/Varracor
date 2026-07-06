import pygame
import math
import random
from settings import *
from menus.gameplay_screen import GameplayScreen
from ui_kit import draw_text, font_title, font_main, font_small, GOLD_COLOR, WHITE
from sound_manager import sound_system
from citys.mucford.forest_road_arena import ForestRoadArena
from vfx import VortexPortal
from units.mnemonic_devourer import MnemonicDevourer

class ForestRoadMenu(GameplayScreen):
    def __init__(self, manager):
        super().__init__(manager)
        
        self.arena = ForestRoadArena()
        self.manager.current_arena = self.arena
        self.manager.current_map_vfx = self.arena.vfx
        
        # Pelaaja (alustetaan sijainti)
        self.player = self.manager.player_character
        self.player.rect.centerx = 100
        self.player.rect.centery = self.arena.height // 2
        self.player.facing_right = True
        
        # Uloskäynti (Oikea reuna)
        self.exit_rect = pygame.Rect(self.arena.width - 100, 0, 100, self.arena.height)
        
        # Äänikanavat (alustetaan myöhemmin)
        self.rain_channel = None
        self.wind_channel = None
        self.vortex_channel = None
        self.active_vortex = None
        self.devourer_unit = None
        
        # VFX State
        self.lightning_timer = 0
        self.flash_alpha = 0
        
        # Intro State
        self.intro_triggered = False
        
        # Chat Overlay (In-game dialogue)
        self.chat_overlay = None
        self.cached_chat = None # Pre-loaded chat
        
        # Combat Lock (Player cannot use abilities until battle starts)
        self.combat_locked = True
        self.transition_active = False
        self.transition_timer = 0

    def on_enter(self):
        super().on_enter() # Tärkeä: Asettaa match_in_progress = True
        self.manager.current_arena = self.arena
        self.manager.current_map_vfx = self.arena.vfx
        self.player.rect.centerx = 100
        self.player.rect.centery = self.arena.height // 2
        self._update_camera()
        
        # Musiikki
        sound_system.play_music('assets/music/swamp_theme.mp3')
        
        # Ambient Sounds
        if not self.rain_channel: self.rain_channel = sound_system.play_sound('rain_medium', loops=-1)
        if not self.wind_channel: self.wind_channel = sound_system.play_sound('wind_outside', loops=-1)
        
        # --- PRELOAD DIALOGUE ---
        # Ladataan dialogi valmiiksi muistiin tässä vaiheessa (latausruudun jälkeen),
        # jotta peli ei nyi ("lagi") kun pelaaja kävelee triggeriin.
        flags = self.manager.npc_state.setdefault("global", {}).setdefault("flags", {})
        if not flags.get("forest_intro_done", False):
            self.cached_chat = self.manager.open_dialogue("commander_self")

    def on_exit(self):
        super().on_exit()
        # Pysäytä ambientit
        if self.rain_channel: self.rain_channel.stop()
        if self.wind_channel: self.wind_channel.stop()
        self.rain_channel = None
        self.wind_channel = None
        if self.vortex_channel:
            self.vortex_channel.stop()
            self.vortex_channel = None
        
        # Pysäytä myös musiikki
        sound_system.stop_music()

    def handle_dialogue_effect(self, effect):
        """Kutsutaan GameManagerista kun dialogissa on efekti."""
        if effect == "spawn_vortex":
            # Luo Vortex keskelle tietä (kiinteä sijainti)
            vx = self.arena.width // 2
            vy = self.arena.height // 2
            vortex = VortexPortal(vx, vy, duration=999999) # Pysyy auki kunnes kosketetaan
            self.manager.vfx.add_effect(vortex)
            self.active_vortex = vortex
            self.manager.trigger_screen_shake(15) # Kovempi tärinä (oli 10)
            
            # Äänet: Spawn (kerta) + Loop (jatkuva)
            sound_system.play_sound('vortex_spawn')
            self.vortex_channel = sound_system.play_sound('vortex_loop', loops=-1)
            
        elif effect == "fight_devourer":
            if self.devourer_unit:
                self.devourer_unit.is_pacified = False
                self.combat_locked = False # Unlock player abilities
                sound_system.play_music('assets/music/mnemonic_battle.wav') # Start battle music
                sound_system.play_sound('boss_roar')
                
                # SAFEGUARD: Varmistetaan että peli tietää meidän tavanneen (ettei intro toistu)
                if "mnemonic_devourer" in self.manager.npc_state:
                    self.manager.npc_state["mnemonic_devourer"]["flags"]["met_devourer"] = True
                
                # Jos taistelu jatkuu (HP vajaa), aktivoi KILL MODE
                if self.devourer_unit.current_hp < self.devourer_unit.max_hp:
                    self.devourer_unit.is_enraged = True
                    self.devourer_unit.ability_3_cooldown = 120 # Aloita imu pian
        
        elif effect == "wipe_memory_effect":
            # Välähdys ja ääni
            self.flash_alpha = 255
            sound_system.play_sound('magic_fail') # Placeholder ääni
            
        elif effect == "steal_sword":
            # Poista pääase
            if not CHEAT_MODE:
                self.player.equipment["main_hand"] = None
                self.player.calculate_final_stats()
            
        elif effect == "teleport_city":
            self.transition_active = True
            self.transition_timer = 300 # 5 sekuntia (pidempi blackout)
            self.manager.city_spawn_point = "bed" # Herää sängystä
            
            # --- REVIVE PLAYER ---
            self.player.is_dead = False
            self.player.current_hp = self.player.max_hp
            self.player.current_mana = self.player.max_mana
            self.player.current_stamina = self.player.max_stamina
            
            # Pysäytä kaikki äänet (hiljaisuus)
            pygame.mixer.stop()
            sound_system.stop_music()
            self.rain_channel = None
            self.wind_channel = None
            self.vortex_channel = None
            
            # --- CLEAR VFX ---
            # Tyhjennetään kaikki partikkelit, jotta ne eivät seuraa seuraavaan ruutuun
            self.manager.vfx.particles.empty()
            self.manager.vfx.floor_particles.empty()
            self.manager.vfx.texts.empty()

    def handle_event(self, event):
        # 1. Chat Overlay input
        if self.chat_overlay:
            self.chat_overlay.handle_event(event)
            return

        # Varmistetaan että pelaaja-referenssi on ajan tasalla
        self.player = self.manager.player_character

        # Emme tarvitse enää manuaalista input-käsittelyä tässä,
        # koska Commander.run_combat_ai hoitaa sen update-loopissa.

        # GameplayScreen hoitaa pausettamisen (ESC)
        super().handle_event(event)

    def update(self):
        super().update() # BaseMenu update (editor)
        
        # --- AMBIENT SOUND CHECK ---
        # Varmistetaan että taustaäänet pysyvät päällä (myös dialogin aikana)
        if self.rain_channel and not self.rain_channel.get_busy():
            self.rain_channel = sound_system.play_sound('rain_medium', loops=-1)
        if self.wind_channel and not self.wind_channel.get_busy():
            self.wind_channel = sound_system.play_sound('wind_outside', loops=-1)

        # --- TRANSITION SEQUENCE ---
        if self.transition_active:
            self.transition_timer -= 1
            if self.transition_timer <= 0:
                self.next_state = "muckford_intro"
            return # Estä muu päivitys

        # --- VORTEX INTERACTION ---
        if self.active_vortex:
            if self.active_vortex.alive():
                # Tarkista etäisyys (Triggeröi kauempaa, jotta pelaaja ei kävele syliin)
                dist_to_vortex = math.hypot(self.player.rect.centerx - self.active_vortex.rect.centerx,
                                            self.player.rect.centery - self.active_vortex.rect.centery)
                
                if dist_to_vortex < 350:
                    # Tallenna sijainti ennen poistoa (FIX CRASH)
                    vortex_pos = self.active_vortex.rect.center

                    # Lopeta efekti ja ääni
                    self.active_vortex.kill()
                    self.active_vortex = None
                    
                    if self.vortex_channel:
                        self.vortex_channel.stop()
                        self.vortex_channel = None
                    
                    sound_system.play_sound('vortex_end')
                    
                    # Spawn Mnemonic Devourer
                    self.devourer_unit = MnemonicDevourer()
                    self.devourer_unit.rect.center = vortex_pos
                    self.devourer_unit.is_pacified = True
                    # Käännä pelaajaa kohti
                    self.devourer_unit.facing_right = (self.player.rect.centerx > self.devourer_unit.rect.centerx)
                    self.manager.all_units.add(self.devourer_unit) # Lisää piirrettäviin
                    
                    # Käynnistä dialogi
                    npc_data = self.manager.npc_state.setdefault("commander_self", {"flags": {}})
                    npc_data["flags"]["vortex_touched"] = True
                    self.chat_overlay = self.manager.open_dialogue("commander_self")
            else:
                # Vortex katosi itsestään
                self.active_vortex = None
                if self.vortex_channel:
                    self.vortex_channel.stop()
                    self.vortex_channel = None

        # --- DEVOURER INTERACTION ---
        if self.devourer_unit:
            # 1. Vääristymäefektit ympärillä
            if random.random() < 0.1:
                self.manager.vfx.create_void_particles(
                    self.devourer_unit.rect.centerx + random.randint(-20, 20),
                    self.devourer_unit.rect.centery + random.randint(-40, 40)
                )
            
            # 2. Lähestymis-dialogi ("Hello")
            dist = math.hypot(self.player.rect.centerx - self.devourer_unit.rect.centerx,
                              self.player.rect.centery - self.devourer_unit.rect.centery)
            
            # Varmistetaan että NPC data on olemassa
            if "mnemonic_devourer" not in self.manager.npc_state:
                self.manager.npc_state["mnemonic_devourer"] = {"relationship": 0, "flags": {}, "history": []}
            flags = self.manager.npc_state["mnemonic_devourer"]["flags"]

            if dist < 180 and not flags.get("met_devourer", False) and not self.chat_overlay:
                flags["next_dialogue_node"] = "root" # Aloita alusta
                self.chat_overlay = self.manager.open_dialogue("mnemonic_devourer")
                
            # 3. Taistelun seuranta (Mid-fight cutscene)
            # Triggeröi vain jos taistelu on käynnissä ja dialogi ei ole jo auki
            if not self.combat_locked and not self.devourer_unit.is_dead and not self.chat_overlay:
                dev_hp_pct = self.devourer_unit.current_hp / self.devourer_unit.max_hp
                player_hp_pct = self.player.current_hp / self.player.max_hp
                
                trigger_dialogue_node_id = None
                
                # A: Pelaaja voittamassa (Devourer < 50% HP)
                if dev_hp_pct <= 0.50:
                    if not flags.get("mid_fight_strong_done"):
                        trigger_dialogue_node_id = "fight_interrupted_strong"
                        flags["mid_fight_strong_done"] = True
                
                # B: Pelaaja häviämässä (Player < 20% HP)
                elif player_hp_pct <= 0.20:
                    if not flags.get("mid_fight_weak_done"):
                        trigger_dialogue_node_id = "fight_interrupted_weak"
                        flags["mid_fight_weak_done"] = True
                    
                if trigger_dialogue_node_id:
                    self.devourer_unit.is_pacified = True
                    # Varmista ettei pelaaja kuole dialogin aikana (jos dotteja)
                    self.player.current_hp = max(self.player.current_hp, 10)
                    flags["next_dialogue_node"] = trigger_dialogue_node_id
                    self.chat_overlay = self.manager.open_dialogue("mnemonic_devourer")
                    return # Pysäytä päivitys dialogin ajaksi

            # 4. Taistelun LOPETUS (Devourer 1 HP:ssä tai pelaaja kuollut)
            if not self.combat_locked and not self.chat_overlay and not flags.get("final_dialogue_done"):
                if self.devourer_unit.current_hp <= 1 or self.player.current_hp <= 0:
                    flags["final_dialogue_done"] = True
                    self.devourer_unit.is_pacified = True # Pysäytä Devourer
                    self.combat_locked = True # Lukitse pelaajan kontrollit
                    flags["next_dialogue_node"] = "final_reveal"
                    self.chat_overlay = self.manager.open_dialogue("mnemonic_devourer")
                    return # Pysäytä päivitys dialogin ajaksi

        # 1. Chat Overlay update
        if self.chat_overlay:
            self.chat_overlay.update()
            if self.chat_overlay.next_state:
                self.chat_overlay = None
            return

        # Tarkista dialogiefektit
        if hasattr(self.manager, "pending_dialogue_effect") and self.manager.pending_dialogue_effect:
            self.handle_dialogue_effect(self.manager.pending_dialogue_effect)
            self.manager.pending_dialogue_effect = None

        # --- UPDATE UNITS ---
        # Päivitä all_units AINA, jotta hit detection toimii
        self.manager.all_units.empty()
        self.manager.all_units.add(self.player)
        if self.devourer_unit:
            self.manager.all_units.add(self.devourer_unit)

        # 1. PLAYER CONTROL
        if self.combat_locked:
            # WALKING MODE: Vain liikkuminen, ei taistelua
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            speed = 4.0
            if keys[pygame.K_w]: dy = -speed
            if keys[pygame.K_s]: dy = speed
            if keys[pygame.K_a]: dx = -speed
            if keys[pygame.K_d]: dx = speed
            
            if dx != 0 or dy != 0:
                self.player.facing_right = (dx > 0) if dx != 0 else self.player.facing_right
                self.player.rect.x += dx
                self.player.rect.y += dy
                self.player.rect.clamp_ip(pygame.Rect(0, 0, self.arena.width, self.arena.height))
                self.player.animation_state = "run"
            else:
                self.player.animation_state = "idle"
            self.player.update(self.arena.obstacles, self.manager)
        else:
            # BATTLE MODE: Täysi kontrolli (Commander-luokka hoitaa inputin)
            self.player.run_combat_ai(self.manager.all_units, self.arena.obstacles, self.manager)
            self.player.update(self.arena.obstacles, self.manager)
        
        # 2. DEVOURER AI
        if self.devourer_unit and not self.manager.world_paused:
            self.devourer_unit.run_combat_ai(self.manager.all_units, self.arena.obstacles, self.manager)
            self.devourer_unit.update(self.arena.obstacles, self.manager)

        # 3. Arena Props Update (Päivitä puut, puskat ja efektit)
        if hasattr(self.arena, "update"):
            self.arena.update(self.manager)
        
        # 3. VFX & Camera
        self.manager.vfx.update(obstacles=self.arena.obstacles)
        self._update_camera()
        
        # Tarkista onko intro nähty ja onko pelaaja liikkunut tarpeeksi
        flags = self.manager.npc_state.setdefault("global", {}).setdefault("flags", {})
        if not flags.get("forest_intro_done", False) and self.player.rect.centerx > 400:
            self.intro_triggered = True
            flags["forest_intro_done"] = True
            # Use cached chat if available, otherwise load it now
            if self.cached_chat:
                self.chat_overlay = self.cached_chat
            else:
                self.chat_overlay = self.manager.open_dialogue("commander_self")
        
        # --- LIGHTNING LOGIC ---
        if self.lightning_timer > 0:
            self.lightning_timer -= 1
        else:
            if random.random() < 0.005: # Harvakseen
                self.lightning_timer = random.randint(10, 30)
                self.flash_alpha = 200
                sound_system.play_sound(random.choice(['thunder_1', 'thunder_2', 'thunder_3', 'thunder_4']))
        
        if self.flash_alpha > 0:
            self.flash_alpha -= 10
        
    def draw(self, screen):
        # Custom draw to ensure correct layering and HUD
        offset = (self.camera_x, self.camera_y)
        
        self.arena.draw_background(screen, offset)
        self.manager.vfx.draw_floor(screen, offset)
        
        # Units & Props (Lisätään arena.props listaan)
        units_to_draw = [self.player] + list(self.arena.props)
        if self.devourer_unit:
            units_to_draw.append(self.devourer_unit)
            
        # Y-Sort
        units_to_draw.sort(key=lambda u: u.rect.bottom)
        
        for u in units_to_draw:
            if hasattr(u, "draw_on_screen"):
                u.draw_on_screen(screen, offset)
            elif hasattr(u, "image") and u.image: # Piirrä myös objektit joilla ei ole draw_on_screen
                screen.blit(u.image, (u.rect.x - offset[0], u.rect.y - offset[1]))
        
        # Sääefektit (Sade)
        if hasattr(self.arena, "draw_foreground"):
            self.arena.draw_foreground(screen, offset)

        self.manager.vfx.draw_top(screen, offset)
        
        # --- NIGHT OVERLAY ---
        # Piirretään NYT, jotta se jää HUDin ja Dialogin alle
        night = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        night.fill((10, 10, 20)) # Tumma sininen yö
        night.set_alpha(180) # Melko pimeää
        screen.blit(night, (0, 0))
        
        # --- LIGHTNING FLASH ---
        if self.flash_alpha > 0:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash.fill((200, 200, 255))
            flash.set_alpha(self.flash_alpha)
            screen.blit(flash, (0, 0))
        
        # HUD (Only if combat unlocked)
        if not self.combat_locked:
            self.player.draw_hud(screen)
            if self.devourer_unit:
                self._draw_boss_bar(screen, [self.devourer_unit])
        
        # Piirrä dialogi päälle
        if self.chat_overlay:
            self.chat_overlay.draw(screen)
        
        # Editor
        self.draw_editor(screen)
        
        # --- MEMORY WIPE TRANSITION ---
        if self.transition_active:
            # Fade to black + Void particles
            alpha = int(255 * (1.0 - (self.transition_timer / 300.0)))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(alpha)
            screen.blit(overlay, (0, 0))
            
            # Piirrä teksti kun ruutu on tarpeeksi tumma
            if alpha > 200:
                draw_text("Memory Lost...", font_title, (150, 100, 200), screen, SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2)