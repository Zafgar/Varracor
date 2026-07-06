import pygame
import os
import random
from settings import *
from gladiator import Gladiator
from ai.swamp_ai import FrogAI
from sound_manager import sound_system

class GiantFrog(Gladiator):
    def __init__(self, name, x, y, team_color):
        super().__init__(name, "Giant Frog", x, y, team_color)
        self.rect = pygame.Rect(x, y, 50, 50)
        
        # Stats (Kestävä, vahva)
        self.base_attributes["str"] = 14
        self.base_attributes["dex"] = 10
        self.base_attributes["int"] = 4
        self.base_attributes["hp"] = 180
        self.calculate_final_stats()
        self.current_hp = self.max_hp
        
        self.speed = 0.9
        self.attack_range = 45
        self.mud_immune = True
        
        # Grafiikat
        self.show_main_hand = False
        self.sprites = {}
        self.hurt_timer = 0
        self.last_pos = self.rect.topleft
        self._load_sprites()
        
        self.image = self.sprites.get("idle", pygame.Surface((50, 50)))
        if not self.sprites:
            self.image.fill((40, 100, 40)) # Fallback vihreä
            
        self.ai_controller = FrogAI(self)

    def load_assets(self):
        return True

    def _load_sprites(self):
        # Oletuspolku: assets/races/swamp/frog/frog_idle_1.png
        base_path = "assets/races/swamp/frog/frog"
        actions = ["idle", "run", "attack", "hurt"]
        target_size = (70, 70)
        
        for act in actions:
            path = f"{base_path}_{act}_1.png"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.sprites[act] = pygame.transform.smoothscale(img, target_size)
                except: pass
        
        if not self.sprites:
            s = pygame.Surface(target_size)
            s.fill((40, 100, 40))
            self.sprites["idle"] = s

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        if self.is_dead: return
        
        # Hyppy-efekti (Leap Arc)
        if self.is_dashing:
            # Dash kestää n. 15 framea. Lasketaan paraabeli.
            total_duration = 15.0
            t = (total_duration - self.dash_timer) / total_duration # 0.0 -> 1.0
            
            # Korkeus kaavana: 4 * h * t * (1-t)
            peak_height = 60
            self.jump_height = peak_height * 4 * t * (1 - t)
        else:
            self.jump_height = 0

        state = "idle"
        if self.hurt_timer > 0:
            self.hurt_timer -= 1
            state = "hurt"
        elif self.attack_cooldown > 30:
            state = "attack"
        elif self.rect.topleft != self.last_pos:
            state = "run"
            
        if state in self.sprites:
            self.image = self.sprites[state]
            
        self.last_pos = self.rect.topleft

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        dmg = super().take_damage(amount, damage_type, attacker, manager)
        if dmg > 0: self.hurt_timer = 15
        return dmg

    def perform_attack(self, target, manager=None, damage_mult=1.0, range_override=None):
        if self.attack_cooldown > 0: return False
        
        self.attack_cooldown = self.attack_speed
        self.animation_state = "attack"
        self.animation_timer = 15
        
        if random.random() < 0.5:
            sound_system.play_sound(random.choice([f'frog_attack_{i}' for i in range(1, 5)]))
        
        if target:
            target.take_damage(self.strength, "Physical", attacker=self, manager=manager)
        return True
