import pygame
import random
from items.base_item import Weapon
from sound_manager import sound_system

class ApprenticeBook(Weapon):
    def __init__(self):
        super().__init__()
        self.name = "Apprentice Book"
        self.rarity = "Common"
        self.description = "Contains basic cantrips. Ranged magic attacks."
        self.cost = 80
        self.level_required = 1
        
        # --- MAGIC WEAPON ---
        self.type = "ranged"    # AI pysyy kaukana
        self.slot_type = "main_hand"
        self.weapon_group = "book" # Skill Tree: Book Focus
        self.weapon_effect = "magic" 
        
        self.damage = 7
        self.attack_range = 140
        self.speed_bonus = 0.0
        
        # Puhdas INT skaalaus
        self.scaling = {'INT': 1.1, 'STR': 0.0}

    def draw_card_icon(self, surface, x, y, size):
        # Kirjan kannet
        rect = pygame.Rect(x+size*0.25, y+size*0.25, size*0.5, size*0.6)
        pygame.draw.rect(surface, (80, 40, 40), rect, border_radius=2)
        # Sivut
        pygame.draw.rect(surface, (220, 220, 200), (rect.x+2, rect.y+2, rect.w-4, rect.h-4))

    def draw_equipped(self, surface, unit_rect, facing_right, attack_timer):
        # Kirja leijuu käden edessä
        hand_x = unit_rect.centerx + (18 if facing_right else -18)
        hand_y = unit_rect.centery + 2
        
        # Pieni "leijumisliike"
        import math
        hover = math.sin(pygame.time.get_ticks() * 0.005) * 2
        
        book_rect = pygame.Rect(hand_x-6, hand_y-8 + hover, 12, 16)
        pygame.draw.rect(surface, (100, 50, 50), book_rect)
        pygame.draw.rect(surface, (255, 255, 255), book_rect.inflate(-4, -4))

    def on_attack_start(self, attacker, target, manager):
        # Ääni
        sound_system.play_sound(random.choice(['book_1', 'book_2', 'book_3', 'book_4']))
        
        # Visuaalinen efekti (ammus)
        start = attacker.rect.center
        end = target.rect.center
        
        if hasattr(manager, "vfx") and hasattr(manager.vfx, "create_projectile"):
            # Luodaan pieni sininen pallo
            manager.vfx.create_projectile(start, end, color=(100, 200, 255), speed=8)