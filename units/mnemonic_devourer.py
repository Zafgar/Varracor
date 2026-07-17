import pygame
import os
import random
import math
from items.item_registry import create_fists
from gladiator import Gladiator
from sound_manager import sound_system
from vfx import VortexMissile

class MnemonicDevourer(Gladiator):
    def __init__(self, name="Mnemonic Devourer", x=0, y=0, team_color=(100, 0, 150)):
        super().__init__(name, "Vortex", x, y, team_color)
        
        # Stats (STR 40 -> perushyökkäys 100, Ability 2 ~160)
        self.base_attributes["str"] = 40
        self.base_attributes["dex"] = 10
        self.base_attributes["int"] = 20
        self.base_attributes["hp"] = 30000
        self.base_attributes["max_hp"] = 30000
        self.base_attributes["mana"] = 200
        self.base_attributes["def_flat"] = 5
        
        self.calculate_final_stats()
        
        # Custom Fists for high basic attack damage
        devourer_fists = create_fists()
        devourer_fists.damage = 100 # Base damage for Mnemonic Devourer's fists
        devourer_fists.scaling = {"STR": 0.0} # No STR scaling for fists, fixed damage
        self.equipment["main_hand"] = devourer_fists
        self.current_hp = self.max_hp
        self.current_mana = self.max_mana
        self.is_boss = True
        
        # Assets
        self.sprites = {}
        # Varmistetaan että base_image on aina olemassa (update käyttää sitä),
        # vaikka sprite-tiedostot puuttuisivat (procedural fallback)
        self.base_image = self.image
        self.load_assets()
        self.is_pacified = False
        self.scream_channel = None
        self.ability_timer = 0
        self.ability_target = None
        self.ability_1_cooldown = 180 # Alussa pieni viive (3s)
        self.ability_2_cooldown = 400 # Teleport strike cooldown
        self.ability_2_phase = 0
        self.ability_3_cooldown = 600 # Vortex Pull cooldown
        self.ability_3_phase = 0
        self.is_enraged = False
        self.suction_channel = None

    def load_assets(self):
        base_path = "assets/races/vortex/Mnemonicdevourer"
        
        def _load(name):
            path = os.path.join(base_path, f"{name}.png")
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    # Skaalaa tarvittaessa (oletus n. 64x64 tai isompi bossille)
                    return pygame.transform.smoothscale(img, (80, 80))
                except Exception: pass
            return None

        # Load animations
        self.sprites["idle"] = [_load("idle")]
        self.sprites["run"] = [_load("run")]
        self.sprites["hurt"] = _load("hurt")
        self.sprites["attack_start"] = _load("attack")
        self.sprites["cast"] = _load("ability_1") # Cast pose
        
        # Abilities visuals
        self.sprites["ability_1"] = _load("ability_1")
        self.sprites["ability_2"] = _load("ability_2")
        self.sprites["ability_3"] = _load("ability_3")
        
        # Fallback: koodipiirretty leijuva kauhio PUUTTUVIIN tiloihin
        # (boss näkyy bossina ilman assetteja, ei harmaana laatikkona)
        from units.placeholder_sprites import horror_frames
        placeholder = horror_frames(
            (80, 80),
            body=(74, 52, 104),     # vortex-violetti
            accent=(150, 96, 200),
            eye=(120, 230, 210),
        )
        if not self.sprites["idle"][0]:
            self.sprites["idle"] = [placeholder["idle"]]
        if not self.sprites["run"][0]:
            self.sprites["run"] = [placeholder["run"]]
        for state, key in (("hurt", "hurt"), ("attack_start", "attack"),
                           ("cast", "cast"), ("ability_1", "cast"),
                           ("ability_2", "attack"), ("ability_3", "cast")):
            if not self.sprites.get(state):
                self.sprites[state] = placeholder[key]

        # Set default image
        self.image = self.sprites["idle"][0]
        self.base_image = self.image
        self.use_sprites = True

        # Update rect size but keep position
        c = self.rect.center
        self.rect = pygame.Rect(0, 0, 40, 30) # Hitbox jaloissa
        self.rect.center = c
        return True

    def run_combat_ai(self, all_units, obstacles=None, manager=None):
        if self.is_pacified: return
        
        # --- BOSS AI: Trigger Abilities ---
        if not self.is_channeling:
            target = None
            
            # Hae kohde
            if self.ai_controller:
                target = getattr(self.ai_controller, "current_target", None)
                if not target:
                    target = self.ai_controller.find_best_target(all_units, manager)
            
            if target and not getattr(target, "is_dead", True):
                dist = math.hypot(target.rect.centerx - self.rect.centerx, target.rect.centery - self.rect.centery)
                
                # Ability 3 (Vortex Pull) - Vain jos ENRAGED (Kill Mode) JA LÄHELLÄ
                if self.is_enraged and self.ability_3_cooldown <= 0 and dist < 400:
                    self.perform_ability_3(target, manager)
                    return
                
                # Ability 2 (Teleport Strike) - Jos kaukana tai satunnaisesti
                if self.ability_2_cooldown <= 0 and (dist > 200 or random.random() < 0.02):
                    self.perform_ability_2(target, manager)
                    return

                # Ability 1 (Missiles) - Satunnaisesti
                if self.ability_1_cooldown <= 0 and random.random() < 0.03:
                    self.perform_ability_1(target, manager)
                    return # Skipataan normaali liike tällä framella, koska kyky alkaa

        super().run_combat_ai(all_units, obstacles, manager)

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        
        if self.ability_1_cooldown > 0:
            self.ability_1_cooldown -= 1
            if self.is_enraged and self.ability_1_cooldown > 0: self.ability_1_cooldown -= 1 # 2x nopeus
            
        if self.ability_2_cooldown > 0:
            self.ability_2_cooldown -= 1
            if self.is_enraged and self.ability_2_cooldown > 0: self.ability_2_cooldown -= 1 # 2x nopeus
            
        if self.ability_3_cooldown > 0:
            self.ability_3_cooldown -= 1
        
        # Ability 1: Channeling logic
        # KORJAUS: Tarkistetaan ability_timer, koska Gladiator.update nollaa is_channeling-lipun
        # LISÄKORJAUS: Varmistetaan ettei Ability 2 ole käynnissä (koska se käyttää samaa timeria)
        # LISÄKORJAUS 2: Varmistetaan ettei Ability 3 ole käynnissä
        if self.ability_timer > 0 and self.ability_2_phase == 0 and self.ability_3_phase == 0:
            self.is_channeling = True # Pidetään kanavointi päällä (estää liikkumisen)
            self.animation_state = "cast" # Pakotetaan cast-animaatio
            self.ability_timer -= 1
            
            # VFX: Channeling particles
            if manager and self.ability_timer % 5 == 0:
                manager.vfx.create_void_particles(self.rect.centerx + random.randint(-40, 40), self.rect.centery + random.randint(-40, 40))
            
            # Spawn missile periodically (e.g. every 40 frames)
            if self.ability_timer % 40 == 0:
                if self.ability_target and not self.ability_target.is_dead:
                    missile = VortexMissile(self.rect.centerx, self.rect.top - 50, self.ability_target, damage=40, owner=self, manager=manager)
                    manager.vfx.add_projectile(missile)

            if self.ability_timer <= 0:
                self.is_channeling = False
                if self.scream_channel:
                    self.scream_channel.stop()
        
        # Ability 2: Teleport Strike Logic
        if self.ability_2_phase > 0:
            self.is_channeling = True
            self.ability_timer -= 1
            
            # Phase 1: Flicker / Väreily (1s)
            if self.ability_2_phase == 1:
                if self.ability_timer % 4 == 0:
                    self.image.set_alpha(random.randint(50, 200)) # Väreilee
                
                if self.ability_timer <= 0:
                    # Siirry Phase 2: Katoaminen
                    self.ability_2_phase = 2
                    self.ability_timer = 30 # 0.5s poissa
                    self.image.set_alpha(0) # Näkymätön
                    if manager:
                        manager.vfx.create_void_particles(self.rect.centerx, self.rect.centery)
            
            # Phase 2: Vanish & Teleport
            elif self.ability_2_phase == 2:
                if self.ability_timer <= 0:
                    # Siirry Phase 3: Ilmestyminen ja isku
                    self.ability_2_phase = 3
                    self.ability_timer = 70 # Pidempi lataus (aikaa väistää)
                    
                    # Teleporttaa kohteen viereen (taakse)
                    if self.ability_target and not self.ability_target.is_dead:
                        offset = 60 if self.ability_target.facing_right else -60
                        self.rect.centerx = self.ability_target.rect.centerx - offset
                        self.rect.centery = self.ability_target.rect.centery
                        self.facing_right = (self.rect.centerx < self.ability_target.rect.centerx)
                    
                    self.image.set_alpha(255) # Näkyviin
                    sound_system.play_sound('devourer_laugh')
                    if manager:
                        manager.vfx.create_shockwave(self.rect.centerx, self.rect.centery, color=(100, 0, 200), max_radius=80)
                        # Varoitus-aura (Punainen)
                        manager.vfx.create_charge_aura(self, duration=45, color=(255, 50, 50))

            # Phase 3: Strike
            elif self.ability_2_phase == 3:
                self.animation_state = "attack"
                # Iskuhetki (esim. puolivälissä animaatiota)
                if self.ability_timer == 25:
                    # AoE Isku
                    if manager:
                        manager.vfx.create_shockwave(self.rect.centerx, self.rect.centery, color=(150, 0, 255), max_radius=150, width=5)
                        manager.vfx.create_impact_sparks(self.rect.centerx, self.rect.centery, color=(200, 50, 200), count=20)
                        
                        hit_rect = self.rect.inflate(140, 140) # Iso alue
                        for u in manager.all_units:
                            if u != self and u.team_color != self.team_color and not u.is_dead:
                                if hit_rect.colliderect(u.rect):
                                    dmg = 60 + (self.strength * 2.5) # Kova damage
                                    u.take_damage(dmg, "Physical", self, manager)
                                    u.apply_status("Stun", 180) # 3s Stun
                
                if self.ability_timer <= 0:
                    self.ability_2_phase = 0
                    self.is_channeling = False
                    
        # Ability 3: Vortex Pull Logic
        if self.ability_3_phase > 0:
            self.is_channeling = True
            self.ability_timer -= 1
            
            # Phase 1: Shout (Windup)
            if self.ability_3_phase == 1:
                self.animation_state = "cast"
                if self.ability_timer <= 0:
                    self.ability_3_phase = 2
                    self.ability_timer = 180 # 3 sekuntia imua
                    self.suction_channel = sound_system.play_sound('vortex_suction', loops=-1)
            
            # Phase 2: Suction (Imu)
            elif self.ability_3_phase == 2:
                if manager:
                    # Vedä kaikkia vihollisia kohti keskustaa
                    center = pygame.math.Vector2(self.rect.center)
                    for u in manager.all_units:
                        if u != self and u.team_color != self.team_color and not u.is_dead:
                            u_pos = pygame.math.Vector2(u.rect.center)
                            vec = center - u_pos
                            dist = vec.length()
                            if 10 < dist < 800: # Laajempi imualue
                                pull_strength = 12.0 # ERITTÄIN voimakas imu (oli 4.0)
                                move = vec.normalize() * pull_strength
                                u.rect.x += move.x
                                u.rect.y += move.y
                    
                    # VFX: Imu-partikkelit
                    manager.vfx.create_suction_particles(self.rect.centerx, self.rect.centery)
                    if self.ability_timer % 3 == 0: # Tiheämpi efekti
                        manager.vfx.create_suction_particles(self.rect.centerx, self.rect.centery)

                    if self.ability_timer % 5 == 0:
                        manager.trigger_screen_shake(5) # Kovempi tärinä

                if self.ability_timer <= 0:
                    self.ability_3_phase = 3
                    self.ability_timer = 40 # Impulssivaiheen kesto
                    if self.suction_channel: self.suction_channel.stop()
                    sound_system.play_sound('vortex_wave_load') # Latausääni
            
            # Phase 3: Impulse (Tiivistys ennen räjähdystä)
            elif self.ability_3_phase == 3:
                self.is_channeling = True
                self.ability_timer -= 1
                
                if manager:
                    # Impulssi-efekti (renkaat imeytyvät sisään)
                    if self.ability_timer % 8 == 0:
                        manager.vfx.create_reverse_shockwave(self.rect.centerx, self.rect.centery, color=(200, 0, 255), max_radius=500, duration=15, width=5)
                    
                    manager.trigger_screen_shake(15) # Väkivaltainen tärinä ennen räjähdystä

                if self.ability_timer <= 0:
                    self.ability_3_phase = 4 # Räjähdys
                    self.ability_timer = 0

            # Phase 4: Explosion
            elif self.ability_3_phase == 4:
                if self.ability_timer <= 0:
                    sound_system.play_sound('vortex_blast')
                    if manager:
                        # Massiivinen räjähdys
                        manager.vfx.create_shockwave(self.rect.centerx, self.rect.centery, color=(200, 0, 255), max_radius=600, width=40)
                        manager.vfx.create_shockwave(self.rect.centerx, self.rect.centery, color=(255, 255, 255), max_radius=300, width=15)
                        manager.vfx.create_impact_sparks(self.rect.centerx, self.rect.centery, color=(200, 50, 255), count=120)
                        manager.trigger_screen_shake(50) # Kova tärinä

                        for u in manager.all_units:
                            if u != self and u.team_color != self.team_color and not u.is_dead:
                                if math.hypot(u.rect.centerx - self.rect.centerx, u.rect.centery - self.rect.centery) < 600:
                                    u.take_damage(200, "Magic", self, manager) # Tappava vahinko
                    self.ability_3_phase = 0
                    self.is_channeling = False

        # Animation logic override
        target_img = self.base_image
        
        if self.animation_state == "hurt" and self.sprites.get("hurt"):
            target_img = self.sprites["hurt"]
        elif self.animation_state == "attack" and self.sprites.get("attack_start"):
            target_img = self.sprites["attack_start"]
        elif self.animation_state == "cast" and self.sprites.get("cast"):
            target_img = self.sprites["cast"]
        elif self.animation_state == "run" and self.sprites.get("run"):
            target_img = self.sprites["run"][0]
            
        if target_img and target_img != self.image:
            self.image = target_img

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        dmg = super().take_damage(amount, damage_type, attacker, manager)
        
        # Scripted immortality: Cannot die, stops at 1 HP to allow dialogue trigger
        if self.current_hp <= 0:
            self.current_hp = 1
            self.is_dead = False
            
        return dmg

    # --- ABILITIES ---
    # Nämä voidaan kytkeä AI:hin tai Spelleihin myöhemmin
    
    def perform_ability_1(self, target, manager):
        # VORTEX BARRAGE: Karjuu ja ampuu ohjuksia
        if self.is_channeling: return
        
        self.animation_state = "cast"
        self.is_channeling = True # Pysäyttää liikkumisen (Gladiator.run_combat_ai tarkistaa tämän)
        self.ability_1_cooldown = 900 # 15 sekunnin cooldown kyvylle
        
        # Kesto 5-8 sekuntia (300 - 480 framea)
        duration = random.randint(300, 480)
        self.ability_timer = duration
        self.ability_target = target
        
        # Ääni
        self.scream_channel = sound_system.play_sound('devourer_scream_loop', loops=-1)
        
        # VFX: Start burst
        if manager:
            manager.vfx.create_shockwave(self.rect.centerx, self.rect.centery, color=(100, 0, 200), max_radius=120)

    def perform_ability_2(self, target, manager):
        # TELEPORT STRIKE
        if self.is_channeling: return
        
        self.is_channeling = True
        self.ability_2_phase = 1
        self.ability_timer = 60 # Phase 1 kesto
        self.ability_target = target
        self.ability_2_cooldown = 600 # 10s cooldown

    def perform_ability_3(self, target, manager):
        # VORTEX PULL (KILL MODE)
        if self.is_channeling: return
        
        self.is_channeling = True
        self.ability_3_phase = 1
        self.ability_timer = 60 # Huudon kesto
        self.ability_3_cooldown = 900 # 15s cooldown
        sound_system.play_sound('vortex_shout')
        if manager:
             manager.vfx.create_charge_aura(self, duration=60, color=(255, 0, 255))