import pygame
import os
import math
import random
from items.base_item import Weapon
from sound_manager import sound_system
from vfx import MagicProjectile

class WeakStaff(Weapon):
    def __init__(self):
        super().__init__()
        self.name = "Apprentice Staff"
        self.rarity = "Common"
        self.cost = 60
        self.description = "A polished wooden staff with a small crystal."
        
        self.type = "ranged" # Battle Mage: Ampuu taikaa
        self.slot_type = "main_hand"
        self.weapon_group = "staff"
        self.level_required = 2
        
        self.damage = 7
        self.attack_range = 280
        self.speed_bonus = 0.0
        self.scaling = {"INT": 0.9}
        
        # Staff antaa manaa
        self.passive_bonuses = {"mana": 20}
        
        self.charge_time = 0
        self.max_charge = 80 # Hieman nopeampi kuin Scrap (90)
        self.charge_enabled = True
        self.last_charge_tick = 0
        
        self.image = None
        self._load_image()

    def _load_image(self):
        path = "assets/gear/staves/weak_staff.png"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (12, 64))
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
            pygame.draw.line(surface, (120, 100, 80), (x + size*0.5, y + size*0.1), (x + size*0.5, y + size*0.9), 3)
            pygame.draw.circle(surface, (100, 200, 255), (x + size*0.5, y + size*0.2), size*0.15)

    def update_charge(self, owner, manager):
        now = pygame.time.get_ticks()
        if now - self.last_charge_tick > 100:
            self.charge_time = 0
        self.last_charge_tick = now

        owner.is_charging = True
        if self.charge_time < self.max_charge:
            self.charge_time += 1
            
    def release_charge(self, owner, manager, target_pos):
        if self.charge_time > 0 and owner.attack_cooldown <= 0:
            base_cost = 10
            cost = max(2, int(base_cost - (owner.intelligence * 0.3)))
            
            if owner.current_stamina < cost: return
            owner.current_stamina -= cost
            
            power = self.charge_time / self.max_charge
            dmg = self.calculate_damage({"int": owner.intelligence})
            final_dmg = int(dmg * (1.0 + power * 1.2)) # Parempi bonus (1.2x)
            
            size = 8 + int(power * 12)
            
            proj = MagicProjectile(owner.rect.centerx, owner.rect.centery, target_pos, 14, final_dmg, owner, manager, size=size)
            manager.vfx.add_projectile(proj)
            
            sound_system.play_sound("staff_1")
            owner.attack_cooldown = owner.attack_speed  # keskitetty rytmi (weapon_feel)
            
        self.charge_time = 0

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown, total_cooldown=60, attack_vector=None):
        hand_x = unit_rect.centerx + (12 if facing_right else -12)
        hand_y = unit_rect.centery
        
        # Piirrä sauva (Fallback jos ei kuvaa, tai kuva jos on)
        if self.image:
            img = self.image
            if not facing_right:
                img = pygame.transform.flip(img, True, False)
            rect = img.get_rect(center=(hand_x, hand_y))
            surface.blit(img, rect)
        else:
            pygame.draw.line(surface, (120, 100, 80), (hand_x, hand_y - 20), (hand_x, hand_y + 20), 3)
        
        if self.charge_time > 0:
            power = self.charge_time / self.max_charge
            r = 4 + int(power * 10)
            alpha = 150 + int(math.sin(pygame.time.get_ticks() * 0.02) * 50)
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (100, 200, 255, alpha), (r, r), r)
            surface.blit(s, (hand_x - r, hand_y - 20 - r))
