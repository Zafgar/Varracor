import pygame
import os
import random
import math
from gladiator import Gladiator
from sound_manager import sound_system
from settings import ENEMY_TEAM
from units.rat import GiantRat

class RatKing(Gladiator):
    def __init__(self, name, x, y):
        # Boss-väri ja alustus
        super().__init__(name, "Rat", x, y, ENEMY_TEAM)
        
        # --- FIX: Asetetaan base_attributes, jotta calculate_final_stats ei nollaa niitä ---
        # Gladiator-luokka käyttää näitä arvoja laskiessaan lopulliset statsit.
        self.base_attributes["max_hp"] = 800 
        self.base_attributes["str"] = 40
        self.base_attributes["dex"] = 15
        self.base_attributes["def_flat"] = 25
        self.base_attributes["mana"] = 100
        
        # Boss Stats (nämä ylikirjoittuvat calculate_final_statsissa jos ei koske base_attributesiin)
        self.speed = 0.75
        self.attack_range = 70
        self.is_boss = True   # bossipalkki ruudun yläreunaan (pelitesti 22)

        self.manager = None
        
        # Kykyjen cooldownit
        self.spit_cooldown = 120 
        self.summon_cooldown = 600 
        self.rage_triggered = False
        
        # Intro sound timer (random shouts during battle)
        self.shout_timer = random.randint(300, 900)

        # Varmistetaan että statsit päivittyvät oikein base_attributes-arvoista
        self.calculate_final_stats()
        self.current_hp = self.max_hp
        
        # Soita intro heti kun luodaan (tai kun taistelu alkaa)
        sound_system.play_sound('rat_king_intro')

        # Tila hyppyä varten
        self.is_super_jumping = False
        self.summon_pending = False
        self.summon_cast_timer = 0 # Ajastin laskeutumisen jälkeiselle huudolle

    def assign_manager(self, manager):
        self.manager = manager

    def load_assets(self):
        """Lataa Rat King -kohtaiset spritet ja skaalaa ne."""
        self.sprites = {}
        base_path = os.path.join("assets", "races", "rat")
        
        files = {
            "idle": "rat_king_idle.png",
            "run": "rat_king_run.png",
            "attack": "rat_king_attack.png",
            "hurt": "rat_king_hurt.png",
            "rage": "rat_king_rage.png",
            "spit": "rat_king_spit.png"
        }

        loaded_any = False
        target_size = 128 

        for state, filename in files.items():
            path = os.path.join(base_path, filename)
            
            if not os.path.exists(path):
                alt_name = None
                if state in ["idle", "run"]: alt_name = "giant_rat_run.png"
                elif state == "attack": alt_name = "giant_rat_attack.png"
                elif state == "hurt": alt_name = "giant_rat_hurt.png"
                
                if alt_name:
                    path = os.path.join(base_path, alt_name)

            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    orig_w, orig_h = img.get_size()
                    ratio = min(target_size / orig_w, target_size / orig_h)
                    new_size = (int(orig_w * ratio), int(orig_h * ratio))
                    img = pygame.transform.smoothscale(img, new_size)
                    self.sprites[state] = img
                    loaded_any = True
                except Exception:
                    pass
        
        if loaded_any:
            if "idle" not in self.sprites:
                self.sprites["idle"] = self.sprites.get("run") or list(self.sprites.values())[0]
            self.image = self.sprites["idle"]
            self.rect = self.image.get_rect(center=self.rect.center)
            self.big_image = self.image 
            return True
            
        return False

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        was_dead = self.is_dead
        dmg = super().take_damage(amount, damage_type, attacker, manager)
        
        if not was_dead and self.is_dead:
            # KUOLEMA
            sound_system.play_sound('rat_king_death')
        elif dmg > 0:
            # Kipuääni satunnaisesti
            if random.random() < 0.3:
                sound_system.play_sound('rat_king_hurt')
        return dmg

    def update(self, obstacles=None, manager=None):
        if self.spit_cooldown > 0: self.spit_cooldown -= 1
        if self.summon_cooldown > 0: self.summon_cooldown -= 1
        
        # Random shout logic (uhittelu taistelun aikana)
        if not self.is_dead:
            self.shout_timer -= 1
            if self.shout_timer <= 0:
                sound_system.play_sound('rat_king_intro')
                self.shout_timer = random.randint(600, 1200) # 10-20 sec välein
        
        # --- SUPER JUMP PHYSICS ---
        if self.is_super_jumping:
            # Lasketaan hyppykorkeus paraabelina (siniaalto)
            total_frames = 45.0
            current = total_frames - self.dash_timer
            if current < 0: current = 0
            
            # 0 -> 1 -> 0
            progress = current / total_frames
            # Hyppää 200 pikseliä ilmaan
            self.jump_height = math.sin(progress * math.pi) * 200 

        super().update(obstacles, manager)
        
        # Tarkistetaan laskeutuminen (super().update() vähensi dash_timeria)
        if self.is_super_jumping and not self.is_dashing:
            self.is_super_jumping = False
            self.jump_height = 0
            self.dash_speed_mult = 3.5 # Palauta normaali nopeus
            if self.summon_pending:
                self._on_land_start_summon(manager)
                self.summon_pending = False

        # --- SUMMON CHANNELING (2s delay) ---
        if self.summon_cast_timer > 0:
            self.summon_cast_timer -= 1
            self.animation_state = "rage" # Pakota huuto-animaatio
            
            if self.summon_cast_timer <= 0:
                self._spawn_minions_now(manager)
        
        if self.use_sprites:
            state = self.animation_state
            new_img = self.sprites.get(state)
            if not new_img:
                new_img = self.sprites.get("idle") or self.sprites.get("run")
            if new_img:
                self.image = new_img

    def run_combat_ai(self, all_units, obstacles=None, manager=None):
        if self.is_dead: return

        # Estä toiminta jos ollaan kutsumassa (huutamassa)
        if self.summon_cast_timer > 0: return

        if not self.rage_triggered and self.current_hp < self.max_hp * 0.4:
            self.activate_rage(manager)

        if self.summon_cooldown <= 0:
            self.summon_minions(manager)
            return 

        target = None
        if self.ai_controller:
            target = self.ai_controller.current_target
        
        if target and not target.is_dead:
            dist = math.hypot(target.rect.centerx - self.rect.centerx, target.rect.centery - self.rect.centery)
            if 100 < dist < 450 and self.spit_cooldown <= 0:
                self.perform_spit(target, manager)
                return

        super().run_combat_ai(all_units, obstacles, manager)

    def activate_rage(self, manager):
        self.rage_triggered = True
        sound_system.play_sound('rat_king_enrage')
        self.animation_state = "rage"
        self.animation_timer = 60
        
        self.strength += 15
        self.speed += 0.4
        self.attack_speed = max(20, self.attack_speed - 15) 
        
        if manager:
            manager.vfx.show_damage(self.rect.centerx, self.rect.top - 60, "RAGE!!!", color=(255, 50, 50))

    def summon_minions(self, manager):
        self.summon_cooldown = 600 # 10 sekuntia (oli 300)
        
        # 1. Laske suunta poispäin vihollisesta
        dx, dy = 0, 0
        if self.ai_controller and self.ai_controller.current_target:
            t = self.ai_controller.current_target
            dx = self.rect.centerx - t.rect.centerx
            dy = self.rect.centery - t.rect.centery
        
        if dx == 0 and dy == 0:
            dx = random.choice([-1, 1])
            dy = random.choice([-1, 1])

        l = math.hypot(dx, dy)
        if l > 0:
            # 2. ALOITA SUPERHYPPY
            self.current_stamina = max(self.current_stamina, 60)
            self.is_dashing = True
            self.is_blocking = False
            self.dash_timer = 45 # Kestää 45 framea (0.75s)
            self.dash_vector = (dx / l, dy / l)
            self.dash_speed_mult = 8.0 # 8x kävelynopeus (n. 2.5x normaali dash) -> lentää kauas
            
            self.is_super_jumping = True
            self.summon_pending = True
            sound_system.play_sound('swish') # Hyppyääni
        else:
            # Fallback jos ei voi hypätä
            self._on_land_start_summon(manager)

    def _on_land_start_summon(self, manager):
        # 3. LASKEUTUMINEN JA HUUTO (Aloita 1s odotus)
        sound_system.play_sound('rat_king_summon')
        self.animation_state = "rage" 
        self.animation_timer = 60 # Animaatio kestää 1s
        self.summon_cast_timer = 60 # Logiikka odottaa 1s ennen rottien luontia
        
        if manager:
            # Laskeutumisefekti (Tärähdys)
            manager.vfx.create_shockwave(self.rect.centerx, self.rect.bottom, color=(100, 80, 60), max_radius=70)
            manager.vfx.create_impact_sparks(self.rect.centerx, self.rect.bottom, color=(120, 100, 80), count=12)
            
            # Camera Shake (Täräytä ruutua)
            if hasattr(manager, "trigger_screen_shake"):
                manager.trigger_screen_shake(20)

    def _spawn_minions_now(self, manager):
        # 4. ROTTJEN LUONTI (Viiveen jälkeen)
        if manager:
            manager.vfx.show_damage(self.rect.centerx, self.rect.top - 60, "SUMMON!", color=(100, 255, 100))
            for _ in range(3): # 3 rottaa (oli 2)
                rx = self.rect.centerx + random.randint(-80, 80)
                ry = self.rect.centery + random.randint(-80, 80)
                arena = manager.current_arena
                arena_w = getattr(arena, "width", 1920) if arena else 1920
                arena_h = getattr(arena, "height", 1080) if arena else 1080
                if 0 < rx < arena_w and 0 < ry < arena_h:
                    rat = GiantRat("Minion", rx, ry, team_color=self.team_color)
                    manager.enemy_team.add(rat)
                    manager.all_units.add(rat)
                    manager.vfx.create_spawn_fog(rx, ry)

    def perform_spit(self, target, manager):
        self.spit_cooldown = 180 # 3 sekuntia (oli 240)
        self.animation_state = "spit"
        self.animation_timer = 30
        sound_system.play_sound('rat_king_spit')
        
        if manager:
            start = self.rect.center
            end = target.rect.center
            
            def on_hit():
                if target and not target.is_dead:
                    dmg = 20 + (self.intelligence * 0.5)
                    target.take_damage(int(dmg), "Poison", attacker=self, manager=manager)
                    target.apply_status("Poison", 180, 3) 
                    manager.vfx.create_acid_puddle(target.rect.centerx, target.rect.centery)
                    manager.vfx.show_damage(target.rect.centerx, target.rect.top, "POISONED", color=(50, 255, 50))

            # Vihreä limapallo kaaressa (oli tulipallo - näytti oudolta)
            manager.vfx.create_acid_glob(start, end, on_impact=on_hit)