import pygame
import os
import math
import random
from items.base_item import Weapon
from sound_manager import sound_system
from vfx import MagicProjectile

class WeakBook(Weapon):
    def __init__(self):
        super().__init__()
        self.name = "Apprentice Tome"
        self.rarity = "Common"
        self.cost = 60
        self.description = "A basic spellbook for casting magic missiles."
        
        self.type = "ranged" # Magic projectile
        self.slot_type = "main_hand"
        self.weapon_group = "book"
        self.level_required = 2
        
        self.damage = 7
        self.attack_range = 260
        self.speed_bonus = 0.0
        self.scaling = {'INT': 0.8}
        
        self.charge_enabled = True
        self.passive_bonuses = {"mana": 20, "mana_regen": 0.05}
        
        self.image = None
        self._load_image()

    def _load_image(self):
        path = "assets/gear/books/weak_book.png"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (24, 30))
                self.big_image = img
            except Exception: pass

    def draw_card_icon(self, surface, x, y, size):
        img = getattr(self, "big_image", self.image)
        if img:
            ratio = img.get_width() / img.get_height()
            new_h = size
            new_w = int(new_h * ratio)
            scaled = pygame.transform.smoothscale(img, (new_w, new_h))
            surface.blit(scaled, (x + (size - new_w) // 2, y))
        else:
            pygame.draw.rect(surface, (80, 40, 40), (x+size*0.2, y+size*0.2, size*0.6, size*0.6))

    def update_charge(self, owner, manager):
        pass # Ei latausta
        
    def release_charge(self, owner, manager, target_pos):
        if owner.attack_cooldown <= 0:
            # Stamina cost
            base_cost = 8
            cost = max(2, int(base_cost - (owner.intelligence * 0.3)))
            
            if owner.current_stamina < cost: return
            owner.current_stamina -= cost
            
            dmg = self.calculate_damage({"int": owner.intelligence})
            # Pieni, nopea ammus
            proj = MagicProjectile(owner.rect.centerx, owner.rect.centery, target_pos, 16, dmg, owner, manager, color=(150, 100, 255), size=7)
            manager.vfx.add_projectile(proj)
            
            sound_system.play_sound("book_1")
            owner.attack_cooldown = 22

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown, total_cooldown=60, attack_vector=None):
        hand_x = unit_rect.centerx + (14 if facing_right else -14)
        hand_y = unit_rect.centery + 5
        
        # Kirja kädessä
        pygame.draw.rect(surface, (80, 40, 40), (hand_x - 6, hand_y - 8, 12, 16))
        pygame.draw.line(surface, (200, 200, 200), (hand_x, hand_y - 8), (hand_x, hand_y + 8), 1)
