import pygame
import os
import math
import random
from items.base_item import Weapon
from sound_manager import sound_system

class ScrapBook(Weapon):
    def __init__(self):
        super().__init__()
        self.name = "Ruined Notes"
        self.rarity = "Common"
        self.cost = 25
        self.description = "Most pages are missing or illegible."
        
        self.type = "ranged"
        self.slot_type = "main_hand"
        self.weapon_group = "book"
        self.level_required = 1
        
        self.damage = 5
        self.attack_range = 240
        self.speed_bonus = 0.0
        self.scaling = {'INT': 0.7}
        
        self.passive_bonuses = {"mana": 10, "mana_regen": 0.02}
        
        self.image = None
        self._load_image()

    def _load_image(self):
        path = "assets/gear/books/scrap_book.png"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (24, 30))
                self.big_image = img
            except: pass

    def draw_card_icon(self, surface, x, y, size):
        img = getattr(self, "big_image", self.image)
        if img:
            ratio = img.get_width() / img.get_height()
            new_h = size
            new_w = int(new_h * ratio)
            scaled = pygame.transform.smoothscale(img, (new_w, new_h))
            surface.blit(scaled, (x + (size - new_w) // 2, y))
        else:
            pygame.draw.rect(surface, (80, 60, 40), (x+size*0.2, y+size*0.2, size*0.6, size*0.6))

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown, total_cooldown=60):
        from items.books.weak_book import WeakBook
        WeakBook.draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown, total_cooldown)

    def on_attack_start(self, attacker, target, manager):
        sound_system.play_sound(random.choice(['book_1', 'book_2', 'book_3', 'book_4']))
        manager.vfx.create_fireball(attacker.rect.center, target.rect.center)