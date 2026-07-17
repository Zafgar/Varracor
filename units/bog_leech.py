import pygame
import os
import random
from settings import *
from gladiator import Gladiator
from ai.swamp_ai import LeechAI
from sound_manager import sound_system

class BogLeech(Gladiator):
    def __init__(self, name, x, y, team_color):
        super().__init__(name, "Bog Leech", x, y, team_color)
        self.rect = pygame.Rect(x, y, 40, 20) # Matala hitbox
        
        # Stats (Nopea, heikko)
        self.base_attributes["str"] = 8
        self.base_attributes["dex"] = 14
        self.base_attributes["int"] = 2
        self.base_attributes["hp"] = 60
        self.calculate_final_stats()
        self.current_hp = self.max_hp
        
        self.speed = self.walk_speed = 1.3 * 1.85  # uusi liikeskaala (pelitesti 28); pelkka .speed ylikirjoittui updatessa
        self.attack_range = 30
        self.mud_immune = True
        
        # Grafiikat
        self.show_main_hand = False
        self.sprites = {}
        self.hurt_timer = 0
        self.last_pos = self.rect.topleft
        self._load_sprites()
        
        self.image = self.sprites.get("idle", pygame.Surface((40, 20)))
        if not self.sprites:
            self.image.fill((60, 40, 60)) # Fallback väri
            
        self.ai_controller = LeechAI(self)

    def load_assets(self):
        return True

    def _load_sprites(self):
        # Oletuspolku: assets/races/swamp/leech/leech_idle_1.png
        base_path = "assets/races/swamp/leech/leech"
        actions = ["idle", "run", "attack", "hurt"]
        target_size = (60, 30) # Visuaalinen koko hieman isompi kuin hitbox
        
        for act in actions:
            path = f"{base_path}_{act}_1.png"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.sprites[act] = pygame.transform.smoothscale(img, target_size)
                except Exception: pass
        
        if not self.sprites:
            # Koodipiirretty iilimatosiluetti (ei flat fill -laatikkoa)
            from units.placeholder_sprites import leech_frames
            self.sprites = leech_frames(
                target_size,
                body=(88, 58, 84),
                accent=(126, 86, 118),
                eye=(228, 200, 90),
            )

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        if self.is_dead: return

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
        # Erikoiskyky: Ime staminaa
        if self.attack_cooldown > 0: return False
        
        self.attack_cooldown = self.attack_speed
        self.animation_state = "attack"
        self.animation_timer = 15
        
        if random.random() < 0.5:
            sound_system.play_sound(random.choice([f'leech_attack_{i}' for i in range(1, 5)]))
        
        if target:
            target.take_damage(self.strength, "Physical", attacker=self, manager=manager)
            if hasattr(target, "current_stamina"):
                target.current_stamina = max(0, target.current_stamina - 15)
                if manager:
                    manager.vfx.show_damage(target.rect.centerx, target.rect.top - 20, "DRAIN", color=(150, 100, 200))
        return True
