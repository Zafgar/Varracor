import pygame
import os
import random
import math
from settings import *
from gladiator import Gladiator
from ai.bird_ai import BirdAI
from sound_manager import sound_system

class CorruptedCrow(Gladiator):
    def __init__(self, name, x, y, team_color):
        super().__init__(name, "Corrupted", x, y, team_color)
        
        # Pieni hitbox
        self.rect = pygame.Rect(x, y, 30, 30)
        
        # Stats: Nopea, heikko, ärsyttävä
        self.base_attributes["str"] = 8
        self.base_attributes["dex"] = 20 # Erittäin nopea
        self.base_attributes["int"] = 5
        self.base_attributes["hp"] = 50  # Glass cannon
        self.calculate_final_stats()
        self.current_hp = self.max_hp
        
        self.speed = 2.5 # Todella nopea
        self.attack_range = 30
        
        # Kyvyt
        self.scream_cooldown = 0
        self.scream_max_cooldown = 600 # 10 sekuntia (60fps)
        
        # Grafiikat
        self.show_main_hand = False
        self.sprites = {}
        self.anim_timer = 0
        self._load_sprites()
        
        # Idle on lista frameja, otetaan ensimmäinen
        idle_frames = self.sprites.get("idle")
        if isinstance(idle_frames, list) and idle_frames:
            self.image = idle_frames[0]
        else:
            self.image = pygame.Surface((30, 30))
            
        self.ai_controller = BirdAI(self)

    def load_assets(self):
        return True

    def _load_sprites(self):
        # Polku: assets/races/corrupted/birds/
        base_path = os.path.join("assets", "races", "corrupted", "birds")
        
        # Idle (2 framea)
        self.sprites["idle"] = []
        for i in range(1, 3):
            self._load_frame(f"corrupted_crow_idle_{i}.png", base_path, "idle", list_target=True)
            
        # Fly (4 framea)
        self.sprites["fly"] = []
        for i in range(1, 5):
            self._load_frame(f"corrupted_crow_fly_{i}.png", base_path, "fly", list_target=True)
            
        # Attack (1 frame)
        self._load_frame("corrupted_crow_attack.png", base_path, "attack")
        
        # Hurt (1 frame)
        self._load_frame("corrupted_crow_hurt.png", base_path, "hurt")

        # Fallback
        if not self.sprites.get("idle"):
            s = pygame.Surface((30, 30))
            s.fill((50, 0, 50))
            self.sprites["idle"] = [s]

    def _load_frame(self, filename, path, key, list_target=False):
        full_path = os.path.join(path, filename)
        if os.path.exists(full_path):
            try:
                img = pygame.image.load(full_path).convert_alpha()
                # Skaalataan sopivaksi (n. 48x48 visuaalisesti)
                scaled = pygame.transform.smoothscale(img, (48, 48))
                if list_target:
                    if key not in self.sprites: self.sprites[key] = []
                    self.sprites[key].append(scaled)
                else:
                    self.sprites[key] = scaled
            except: pass

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        if self.is_dead: return
        
        if self.scream_cooldown > 0:
            self.scream_cooldown -= 1
            
        self.anim_timer += 1
        
        # Animaatio logiikka
        state = self.animation_state # AI asettaa: fly, idle
        if self.attack_cooldown > 0: state = "attack"
        if getattr(self, "hurt_timer", 0) > 0: state = "hurt"
        
        img = None
        
        if state == "fly" and "fly" in self.sprites and self.sprites["fly"]:
            frames = self.sprites["fly"]
            idx = (self.anim_timer // 5) % len(frames) # Nopea räpyttely
            img = frames[idx]
        elif state == "attack" and "attack" in self.sprites:
            img = self.sprites["attack"]
        elif state == "hurt" and "hurt" in self.sprites:
            img = self.sprites["hurt"]
        elif "idle" in self.sprites:
            frames = self.sprites["idle"]
            idx = (self.anim_timer // 15) % len(frames)
            img = frames[idx]
            
        if img:
            self.image = img
            if not self.facing_right:
                self.image = pygame.transform.flip(self.image, True, False)

    def perform_scream(self, manager):
        """AoE Silence 3s, 10s cooldown."""
        if self.scream_cooldown > 0: return
        
        self.scream_cooldown = self.scream_max_cooldown
        self.animation_state = "attack" # Käytetään attack-kuvaa huutoon
        
        if manager:
            # Visuaalinen efekti (Shockwave)
            manager.vfx.create_shockwave(self.rect.centerx, self.rect.centery, color=(100, 0, 100), max_radius=100)
            manager.vfx.show_damage(self.rect.centerx, self.rect.top - 30, "SCREAM!", color=(200, 50, 200))
            
            # Etsi kohteet
            center = self.rect.center
            radius = 150
            
            for u in manager.all_units:
                if u.is_dead or u == self or u.team_color == self.team_color: continue
                
                dist = math.hypot(u.rect.centerx - center[0], u.rect.centery - center[1])
                if dist < radius:
                    # Silence 3 sekuntia (180 framea)
                    u.apply_status("Silence", 180)
                    manager.vfx.show_damage(u.rect.centerx, u.rect.top - 20, "SILENCED", color=(150, 150, 150))

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        # MELEE IMMUNITY ILMASSA
        # Jos lintu on korkealla (> 40px) ja hyökkäys on fyysinen melee
        is_melee = attacker and getattr(attacker, "weapon_type", "melee") == "melee"
        
        if self.jump_height > 40 and damage_type == "Physical" and is_melee:
            if manager:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 20, "MISS (High)", color=(200, 200, 200))
            return 0
            
        return super().take_damage(amount, damage_type, attacker, manager)

    def prevent_overlap(self, all_units):
        # Linnut lentävät, joten ne eivät tönäise muita yksiköitä (eivätkä toisiaan)
        pass

    def _resolve_stuck_state(self, obstacles, manager):
        # Ylikirjoitetaan: Jos lennetään, ei välitetä seinistä (paitsi kartan reunoista)
        if self.jump_height > 5:
             # Vain kartan reunat
             if manager and getattr(manager, "current_arena", None):
                arena = manager.current_arena
                aw = getattr(arena, "width", 2000)
                ah = getattr(arena, "height", 2000)
                force = 4.0
                if self.rect.left < 0: self.rect.x += force
                if self.rect.right > aw: self.rect.x -= force
                if self.rect.top < 0: self.rect.y += force
                if self.rect.bottom > ah: self.rect.y -= force
        else:
            super()._resolve_stuck_state(obstacles, manager)

    def check_wall_collision(self, dx, dy, obstacles):
        # Jos lennetään, ignorataan esteet
        if self.jump_height > 5:
            # Käytetään super-luokan logiikkaa tyhjällä estelistalla,
            # jotta sub-pixel liike (float -> int) toimii oikein.
            super().check_wall_collision(dx, dy, [])
        else:
            super().check_wall_collision(dx, dy, obstacles)
