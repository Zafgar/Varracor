import pygame
import os
import math
import random
from items.base_item import Weapon
from sound_manager import sound_system

class ScrapAxe(Weapon):
    def __init__(self):
        super().__init__()
        self.name = "Dull Hatchet"
        self.rarity = "Common"
        self.cost = 18
        self.description = "More for chopping wood than heads."
        
        self.type = "melee"
        self.slot_type = "main_hand"
        self.weapon_group = "axe"
        self.level_required = 1
        
        self.damage = 6
        self.attack_range = 32
        self.speed_bonus = -0.1
        self.scaling = {"STR": 0.6}
        
        self.charge_time = 0
        self.max_charge = 60
        self.charge_enabled = True
        self.last_charge_tick = 0
        
        self.image = None
        self._load_image()

    def _load_image(self):
        path = "assets/gear/axes/scrap_axe.png"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (24, 48))
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
            pygame.draw.line(surface, (100, 80, 40), (x + size*0.3, y + size*0.8), (x + size*0.7, y + size*0.2), 4)

    def update_charge(self, owner, manager):
        # Resetoi lataus jos tauko
        now = pygame.time.get_ticks()
        if now - self.last_charge_tick > 100:
            self.charge_time = 0
        self.last_charge_tick = now

        owner.temp_speed_mult = 0.5 # Raskas liike
        owner.is_charging = True
        if self.charge_time < self.max_charge:
            self.charge_time += 1

    def release_charge(self, owner, manager, target_pos):
        # HEAVY CHOP: Lisää vahinkoa latauksen mukaan
        mult = 1.0 + (self.charge_time / self.max_charge) * 0.8 # Max 1.8x dmg
        owner.perform_attack(None, manager, damage_mult=mult, target_pos=target_pos)
        self.charge_time = 0

    def get_swing_rect(self, unit_rect, facing_right, attack_timer, total_cooldown, attack_vector=None):
        swing_w = 50
        swing_h = 50
        
        if attack_vector:
            dx, dy = attack_vector
            dist = math.hypot(dx, dy) or 1
            offset = 35
            swing_x = unit_rect.centerx + (dx/dist) * offset - swing_w//2
            swing_y = unit_rect.centery + (dy/dist) * offset - swing_h//2
        else:
            swing_x = unit_rect.centerx if facing_right else unit_rect.centerx - swing_w
            swing_y = unit_rect.centery - 30
            
        return pygame.Rect(swing_x, swing_y, swing_w, swing_h)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown, total_cooldown=60, attack_vector=None):
        # Lataushohto
        if self.charge_time > 15:
            glow_size = int((self.charge_time / self.max_charge) * 8)
            pygame.draw.circle(surface, (255, 100, 50), (unit_rect.centerx, unit_rect.centery), 20 + glow_size, 2)

        if not self.image:
            # Fallback: Piirrä yksinkertainen kirves jos kuvaa ei ole
            hand_x = unit_rect.centerx + (12 if facing_right else -12)
            hand_y = unit_rect.centery + 5
            
            # Varsi
            end_x = hand_x + (10 if facing_right else -10)
            end_y = hand_y - 20
            pygame.draw.line(surface, (100, 80, 40), (hand_x, hand_y), (end_x, end_y), 4)
            
            # Terä
            pygame.draw.polygon(surface, (150, 150, 150), [(end_x, end_y), (end_x + 10, end_y - 10), (end_x + 10, end_y + 10)])
            return
        
        hand_x = unit_rect.centerx + (12 if facing_right else -12)
        hand_y = unit_rect.centery + 5
        
        angle = -10 if facing_right else 10
        scale = 1.0
        
        prog = 1.0 - (attack_cooldown / total_cooldown) if total_cooldown > 0 else 0
        anim_duration = 0.45 # Kirves on raskaampi
        
        if attack_cooldown > 0 and attack_vector and prog < anim_duration:
            anim_prog = prog / anim_duration
            
            dx, dy = attack_vector
            base_angle = math.degrees(math.atan2(-dy, dx)) - 90
            
            swing_arc = 140
            if anim_prog < 0.7:
                swing_pct = anim_prog / 0.7
                angle = base_angle + (swing_arc / 2) - (swing_arc * swing_pct)
                scale = 1.0 + (0.4 * math.sin(swing_pct * 3.14)) # Iso skaalaus (Heavy impact)
            else:
                angle = base_angle - (swing_arc / 2)
                
        img = self.image
        is_animating = (attack_cooldown > 0 and prog < anim_duration)
        
        if not facing_right and not is_animating: 
            img = pygame.transform.flip(img, True, False)
            
        if scale != 1.0:
            w = int(img.get_width() * scale)
            h = int(img.get_height() * scale)
            img = pygame.transform.scale(img, (w, h))
            
        rotated = pygame.transform.rotate(img, angle)
        rect = rotated.get_rect(center=(hand_x, hand_y))
        surface.blit(rotated, rect)

    def on_attack_start(self, attacker, target, manager):
        sound_system.play_sound(random.choice(['axe_1', 'axe_2', 'axe_3', 'axe_4']))