import pygame
import math
from settings import *
from sound_manager import sound_system

class RatPoisonSword:
    def __init__(self):
        self.name = "Rat Poison Sword"
        self.type = "melee"
        self.slot_type = "main_hand"
        self.damage = 14
        self.attack_range = 35
        self.rarity = "Rare"
        self.description = "Drips with deadly toxin. Applies poison on hit."
        self.cost = 450
        self.speed_bonus = 0.1
        self.weapon_group = "sword"
        self.level_required = 2
        
        # TÄMÄ LIPPU ESTÄÄ KAUPPAAN TULON (jos registry tukee sitä)
        self.in_shop = False 

    def on_hit(self, attacker, target, dmg_dealt, manager):
        if target and not target.is_dead:
            target.apply_status("Poison", 180, damage=3)
            if manager and manager.vfx:
                manager.vfx.show_damage(target.rect.centerx, target.rect.top - 20, "POISONED!", color=(100, 255, 100))

    def on_attack_start(self, attacker, target, manager):
        sound_system.play_sound('attack_melee')

    def draw_card_icon(self, surface, x, y, size):
        # Tausta (Tummanvihreä)
        pygame.draw.rect(surface, (20, 30, 20), (x, y, size, size), border_radius=5)
        pygame.draw.rect(surface, (60, 180, 60), (x, y, size, size), 2, border_radius=5)
        
        cx, cy = x + size//2, y + size//2
        s = size
        
        # Kahva (Ruskea)
        pygame.draw.line(surface, (100, 60, 30), (cx - s*0.2, cy + s*0.2), (cx - s*0.05, cy + s*0.05), 4)
        # Väistin (Harmaa)
        pygame.draw.line(surface, (100, 100, 100), (cx - s*0.15, cy + s*0.05), (cx - s*0.05, cy + s*0.15), 3)
        
        # Terä (Sahalaitainen ja vihreä)
        blade_start = (cx - s*0.05, cy + s*0.05)
        blade_end = (cx + s*0.3, cy - s*0.3)
        pygame.draw.line(surface, (150, 255, 150), blade_start, blade_end, 3)
        
        # Myrkkyä (Pisaroita)
        pygame.draw.circle(surface, (50, 255, 50), (int(cx + s*0.1), int(cy - s*0.1)), 2)
        pygame.draw.circle(surface, (50, 255, 50), (int(cx + s*0.22), int(cy - s*0.08)), 2)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_timer):
        hand_x = unit_rect.centerx + (14 if facing_right else -14)
        hand_y = unit_rect.centery + 5
        
        angle = -20 
        if attack_timer > 0:
            progress = 1 - (attack_timer / 30)
            angle = -45 + (progress * 140)
            
        if not facing_right: 
            angle = -angle
            
        length = 28
        rad = math.radians(angle - 90)
        
        end_x = hand_x + math.cos(rad) * length
        end_y = hand_y + math.sin(rad) * length
        
        # Poison Glow (Sykkivä vihreä)
        pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.5
        glow_width = 6 + int(pulse * 3)
        pygame.draw.line(surface, (40, 200, 40), (hand_x, hand_y), (end_x, end_y), glow_width)

        # Piirretään miekka (kahva + vihreä terä)
        pygame.draw.line(surface, (100, 60, 30), (hand_x, hand_y), (end_x, end_y), 4)
        
        blade_start_ratio = 0.3
        bs_x = hand_x + (end_x - hand_x) * blade_start_ratio
        bs_y = hand_y + (end_y - hand_y) * blade_start_ratio
        
        pygame.draw.line(surface, (100, 255, 100), (bs_x, bs_y), (end_x, end_y), 3)
