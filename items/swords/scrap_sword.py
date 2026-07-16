import pygame
import os
import math
import random
from items.base_item import Weapon
from sound_manager import sound_system

class ScrapSword(Weapon):
    def __init__(self):
        super().__init__()
        self.name = "Scrap Blade"
        self.rarity = "Common"
        self.cost = 15
        self.description = "A piece of sharpened scrap metal."
        
        self.type = "melee"
        self.slot_type = "main_hand"
        self.weapon_group = "sword"
        self.level_required = 1
        
        self.damage = 5
        self.attack_range = 38
        self.speed_bonus = -0.05
        self.scaling = {"STR": 0.4, "DEX": 0.2}
        
        self.charge_time = 0
        self.max_charge = 60
        self.charge_enabled = True
        self.last_charge_tick = 0
        
        self.image = None
        self._load_image()

    def _load_image(self):
        path = "assets/gear/swords/scrap_sword.png"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (20, 48))
                self.big_image = img
            except Exception: 
                print(f"Failed to load {path}")
                self.image = None
                self.big_image = None

    def draw_card_icon(self, surface, x, y, size):
        img = getattr(self, "big_image", self.image)
        if img:
            ratio = img.get_width() / img.get_height()
            new_h = size
            new_w = int(new_h * ratio)
            scaled = pygame.transform.smoothscale(img, (new_w, new_h))
            surface.blit(scaled, (x + (size - new_w) // 2, y))
        else:
            pygame.draw.line(surface, (100, 100, 100), (x + size*0.2, y + size*0.8), (x + size*0.8, y + size*0.2), 4)

    def update_charge(self, owner, manager):
        # Resetoi lataus jos tauko
        now = pygame.time.get_ticks()
        if now - self.last_charge_tick > 100:
            self.charge_time = 0
        self.last_charge_tick = now

        owner.temp_speed_mult = 0.4 # Raskas lataus
        owner.is_charging = True
        if self.charge_time < self.max_charge:
            self.charge_time += 1

    def release_charge(self, owner, manager, target_pos):
        # TAYSI LATAUS: LUNGE SLASH - askel eteen + raskas viilto
        # (systems/charge_specials.py; sama pelaajalle ja AI:lle)
        if self.charge_time >= self.max_charge:
            from systems import charge_specials
            charge_specials.lunge_slash(owner, self, manager, target_pos)
            self.charge_time = 0
            return
        if self.charge_time > 15:
            # POWER HIT
            power = self.charge_time / self.max_charge
            mult = 1.5 + (power * 1.5) # 1.5x - 3.0x vahinko
            
            owner.perform_attack(None, manager, damage_mult=mult, target_pos=target_pos)
            if manager: 
                manager.trigger_screen_shake(5)
        else:
            owner.perform_attack(None, manager, target_pos=target_pos)
        self.charge_time = 0

    def get_swing_rect(self, unit_rect, facing_right, attack_timer, total_cooldown, attack_vector=None):
        # Miekka lyö eteenpäin
        swing_w = 60
        swing_h = 40
        
        if attack_vector:
            dx, dy = attack_vector
            dist = math.hypot(dx, dy) or 1
            offset = 30
            swing_x = unit_rect.centerx + (dx/dist) * offset - swing_w//2
            swing_y = unit_rect.centery + (dy/dist) * offset - swing_h//2
        else:
            swing_x = unit_rect.centerx if facing_right else unit_rect.centerx - swing_w
            swing_y = unit_rect.centery - 20

        swing_rect = pygame.Rect(swing_x, swing_y, swing_w, swing_h)
        return swing_rect

    def on_attack_start(self, attacker, target, manager):
        sound_system.play_sound(random.choice(['sword_1', 'sword_2', 'sword_3', 'sword_4']))

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown, total_cooldown=60, attack_vector=None):
        # Lataushohto
        if self.charge_time > 15:
            glow_size = int((self.charge_time / self.max_charge) * 10)
            pygame.draw.circle(surface, (255, 200, 50), (unit_rect.centerx, unit_rect.centery), 20 + glow_size, 2)
            
        if not self.image: return
        
        # Pivot point (Käsi)
        hand_x = unit_rect.centerx + (12 if facing_right else -12)
        hand_y = unit_rect.centery + 5
        
        angle = -20 if facing_right else 20 # Idle asento
        scale = 1.0
        
        # Laske progress (0.0 -> 1.0)
        prog = 1.0 - (attack_cooldown / total_cooldown) if total_cooldown > 0 else 0
        
        # Animaation kesto (esim. 35% cooldownista)
        anim_duration = 0.35
        
        if attack_cooldown > 0 and attack_vector and prog < anim_duration:
            # Skaalaa progress animaation kestoon (0..1)
            anim_prog = prog / anim_duration
            
            # Laske kulma kursorin suuntaan
            dx, dy = attack_vector
            base_angle = math.degrees(math.atan2(-dy, dx)) - 90 # -90 korjaa spriten pystyasennon
            
            swing_arc = 120
            if anim_prog < 0.7:
                # Iskuvaihe
                swing_pct = anim_prog / 0.7
                angle = base_angle + (swing_arc / 2) - (swing_arc * swing_pct)
                scale = 1.0 + (0.3 * math.sin(swing_pct * 3.14)) # Kasvaa keskellä iskua (Impact!)
            else:
                # Pieni palautusliike
                angle = base_angle - (swing_arc / 2)
                
        img = self.image
        
        # Flipataan jos idle TAI animaatio on ohi (mutta cooldown käy vielä)
        is_animating = (attack_cooldown > 0 and prog < anim_duration)
        
        if not facing_right and not is_animating: 
            img = pygame.transform.flip(img, True, False)
            
        # Skaalaus (Impact effect)
        if scale != 1.0:
            w = int(img.get_width() * scale)
            h = int(img.get_height() * scale)
            img = pygame.transform.scale(img, (w, h))
            
        rotated = pygame.transform.rotate(img, angle)
        rect = rotated.get_rect(center=(hand_x, hand_y))
        surface.blit(rotated, rect)