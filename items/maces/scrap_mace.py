import pygame
import os
import math
import random
from items.base_item import Weapon
from sound_manager import sound_system

class ScrapMace(Weapon):
    def __init__(self):
        super().__init__()
        self.name = "Heavy Branch"
        self.rarity = "Common"
        self.cost = 12
        self.description = "Just a heavy stick found on the ground."
        
        self.type = "melee"
        self.slot_type = "main_hand"
        self.weapon_group = "mace"
        self.level_required = 1
        
        self.damage = 7
        self.attack_range = 32
        self.speed_bonus = -0.15
        self.scaling = {"STR": 0.7}
        
        self.charge_time = 0
        self.max_charge = 60
        self.charge_enabled = True
        self.last_charge_tick = 0
        
        self.image = None
        self._load_image()

    def _load_image(self):
        path = "assets/gear/maces/scrap_mace.png"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (20, 48))
                self.big_image = img
            except: 
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
            pygame.draw.line(surface, (100, 70, 30), (x + size*0.3, y + size*0.8), (x + size*0.7, y + size*0.2), 6)

    def update_charge(self, owner, manager):
        now = pygame.time.get_ticks()
        if now - self.last_charge_tick > 100:
            self.charge_time = 0
        self.last_charge_tick = now

        owner.temp_speed_mult = 0.4 # Hyvin hidas lataus
        owner.is_charging = True
        if self.charge_time < self.max_charge:
            self.charge_time += 1

    def release_charge(self, owner, manager, target_pos):
        # SKULL CRUSHER: Max latauksella varma stunni (tai pidempi)
        mult = 1.0 + (self.charge_time / self.max_charge) * 0.5 # Max 1.5x dmg
        
        # Jos täysi lataus, pakota stun (Gladiator.take_damage hoitaa stunin vahingon perusteella, 
        # mutta voimme lisätä damagea reilusti varmistaaksemme sen)
        if self.charge_time >= self.max_charge:
            mult *= 1.3 # Extra bonus täydestä
            if manager: manager.trigger_screen_shake(6)
            
        owner.perform_attack(None, manager, damage_mult=mult, target_pos=target_pos)
        self.charge_time = 0

    def get_swing_rect(self, unit_rect, facing_right, attack_timer, total_cooldown, attack_vector=None):
        # Nuija lyö lyhyesti mutta leveästi
        swing_w = 50
        swing_h = 50
        if attack_vector:
            dx, dy = attack_vector
            dist = math.hypot(dx, dy) or 1
            offset = 30
            swing_x = unit_rect.centerx + (dx/dist) * offset - swing_w//2
            swing_y = unit_rect.centery + (dy/dist) * offset - swing_h//2
        else:
            swing_x = unit_rect.centerx if facing_right else unit_rect.centerx - swing_w
            swing_y = unit_rect.centery - 20
        return pygame.Rect(swing_x, swing_y, swing_w, swing_h)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown, total_cooldown=60, attack_vector=None):
        if self.charge_time > 15:
            glow_size = int((self.charge_time / self.max_charge) * 8)
            pygame.draw.circle(surface, (200, 200, 255), (unit_rect.centerx, unit_rect.centery), 20 + glow_size, 2)

        if not self.image:
            # Fallback: Piirrä nuija
            hand_x = unit_rect.centerx + (12 if facing_right else -12)
            hand_y = unit_rect.centery + 5
            
            # Varsi
            end_x = hand_x + (10 if facing_right else -10)
            end_y = hand_y - 20
            pygame.draw.line(surface, (100, 70, 30), (hand_x, hand_y), (end_x, end_y), 4)
            
            # Pää
            pygame.draw.circle(surface, (80, 80, 80), (end_x, end_y), 8)
            return
        
        hand_x = unit_rect.centerx + (12 if facing_right else -12)
        hand_y = unit_rect.centery + 5
        angle = -15 if facing_right else 15
        
        prog = 1.0 - (attack_cooldown / total_cooldown) if total_cooldown > 0 else 0
        if attack_cooldown > 0 and attack_vector and prog < 0.4:
            dx, dy = attack_vector
            base_angle = math.degrees(math.atan2(-dy, dx)) - 90
            swing_pct = prog / 0.4
            angle = base_angle + 60 - (120 * swing_pct)

        img = self.image
        if not facing_right and attack_cooldown <= 0: img = pygame.transform.flip(img, True, False)
        
        rotated = pygame.transform.rotate(img, angle)
        surface.blit(rotated, rotated.get_rect(center=(hand_x, hand_y)))

    def on_attack_start(self, attacker, target, manager):
        sound_system.play_sound(random.choice(['mace_1', 'mace_2', 'mace_3', 'mace_4']))