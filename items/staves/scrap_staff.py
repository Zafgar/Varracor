import pygame
import os
import math
import random
from items.base_item import Weapon
from sound_manager import sound_system
from vfx import MagicProjectile

class ScrapStaff(Weapon):
    def __init__(self):
        super().__init__()
        self.name = "Twisted Stick"
        self.rarity = "Common"
        self.cost = 15
        self.description = "Barely holds any magical charge."
        
        self.type = "ranged"
        self.slot_type = "main_hand"
        self.weapon_group = "staff"
        self.level_required = 1
        
        self.damage = 6
        self.attack_range = 250 # Vakio kantama
        self.speed_bonus = -0.05
        self.scaling = {"INT": 0.8}
        
        self.passive_bonuses = {"mana": 5}
        
        self.charge_time = 0
        self.max_charge = 90 # 1.5s max charge
        self.charge_enabled = True
        self.last_charge_tick = 0
        
        self.image = None
        self._load_image()

    def _load_image(self):
        path = "assets/gear/staves/scrap_staff.png"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (12, 60))
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
            pygame.draw.line(surface, (100, 80, 40), (x + size*0.3, y + size*0.8), (x + size*0.7, y + size*0.2), 3)

    def update_charge(self, owner, manager):
        # Resetoi lataus jos tauko
        now = pygame.time.get_ticks()
        if now - self.last_charge_tick > 100:
            self.charge_time = 0
        self.last_charge_tick = now

        # Sauvaa voi ladata liikkeessä (ei hidasta)
        owner.is_charging = True
        if self.charge_time < self.max_charge:
            self.charge_time += 1
            
    def release_charge(self, owner, manager, target_pos):
        if self.charge_time > 0 and owner.attack_cooldown <= 0:
            # Tarkista stamina (Sauvan lataus on ilmainen, joten laukaus maksaa)
            base_cost = 10
            cost = max(2, int(base_cost - (owner.intelligence * 0.3)))
            
            if owner.current_stamina < cost: return
            owner.current_stamina -= cost
            
            power = self.charge_time / self.max_charge
            
            dmg = self.calculate_damage({"int": owner.intelligence})
            final_dmg = int(dmg * (1.0 + power * 1.0)) # 100% - 200% dmg
            
            size = 6 + int(power * 10) # Koko kasvaa
            
            proj = MagicProjectile(owner.rect.centerx, owner.rect.centery, target_pos, 12, final_dmg, owner, manager, size=size)
            manager.vfx.add_projectile(proj)
            
            sound_system.play_sound("staff_1")
            owner.attack_cooldown = 40
            
        self.charge_time = 0

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown, total_cooldown=60, attack_vector=None):
        hand_x = unit_rect.centerx + (12 if facing_right else -12)
        hand_y = unit_rect.centery
        
        # Piirrä sauva
        pygame.draw.line(surface, (100, 80, 60), (hand_x, hand_y - 20), (hand_x, hand_y + 20), 3)
        
        # Latausefekti (pallo sauvan päässä)
        if self.charge_time > 0:
            power = self.charge_time / self.max_charge
            r = 4 + int(power * 8)
            
            # Sykkivä väri
            alpha = 150 + int(math.sin(pygame.time.get_ticks() * 0.02) * 50)
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (100, 150, 255, alpha), (r, r), r)
            surface.blit(s, (hand_x - r, hand_y - 20 - r))