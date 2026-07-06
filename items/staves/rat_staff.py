import pygame
import math
import random
from settings import *
from sound_manager import sound_system

class RatPoisonStaff:
    def __init__(self):
        self.name = "Rat Poison Staff"
        self.type = "ranged" # Sauvat ovat yleensä ranged/magic
        self.slot_type = "main_hand"
        self.damage = 10
        self.attack_range = 300
        self.rarity = "Rare"
        self.description = "Channels the toxic fumes of the sewers."
        self.cost = 450
        self.speed_bonus = 0.0
        self.weapon_group = "staff"
        self.level_required = 2
        self.in_shop = False

    def on_hit(self, attacker, target, dmg_dealt, manager):
        if target and not target.is_dead:
            # Sauva myrkyttää kohteen
            target.apply_status("Poison", 180, damage=2)
            if manager and manager.vfx:
                manager.vfx.show_damage(target.rect.centerx, target.rect.top - 20, "POISONED!", color=(100, 255, 100))

    def on_attack_start(self, attacker, target, manager):
        # Käytetään taikaääntä jos on, muuten geneerinen
        sound_system.play_sound(random.choice(['staff_1', 'staff_2', 'staff_3', 'staff_4']))
            
        if manager and manager.vfx:
            # Luodaan vihreä tulipallo/taika-ammus
            manager.vfx.create_fireball(attacker.rect.center, target.rect.center)

    def draw_card_icon(self, surface, x, y, size):
        pygame.draw.rect(surface, (20, 30, 20), (x, y, size, size), border_radius=5)
        pygame.draw.rect(surface, (60, 180, 60), (x, y, size, size), 2, border_radius=5)
        
        cx, cy = x + size//2, y + size//2
        s = size
        
        # Sauvan varsi
        pygame.draw.line(surface, (100, 60, 30), (cx + s*0.3, cy - s*0.3), (cx - s*0.3, cy + s*0.3), 3)
        
        # Hohtava pallo päässä
        orb_pos = (cx + s*0.3, cy - s*0.3)
        pygame.draw.circle(surface, (50, 255, 50), orb_pos, s*0.15)
        pygame.draw.circle(surface, (200, 255, 200), (orb_pos[0]-2, orb_pos[1]-2), s*0.05)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_timer):
        # Piirretään sauva käteen (yksinkertaistettu)
        # Koska Gladiator-luokka hoitaa piirron kutsumalla tätä, 
        # emme tarvitse monimutkaista logiikkaa tässä, jos itemiä ei ole tehty Weapon-perinnällä.
        # Mutta tässä on peruspiirto:
        hand_x = unit_rect.centerx + (10 if facing_right else -10)
        hand_y = unit_rect.centery + 5
        
        angle = -15 if facing_right else 195
        
        if attack_timer > 0:
            offset = (1 - (attack_timer / 30)) * 30
            if facing_right: angle += offset
            else: angle -= offset
            
        length = 40
        rad = math.radians(angle)
        
        top_x = hand_x + math.cos(rad) * (length * 0.7)
        top_y = hand_y + math.sin(rad) * (length * 0.7)
        
        bot_x = hand_x - math.cos(rad) * (length * 0.3)
        bot_y = hand_y - math.sin(rad) * (length * 0.3)
        
        # Poison Glow (Orb)
        pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.5
        glow_radius = 8 + int(pulse * 4)
        pygame.draw.circle(surface, (40, 200, 40), (int(top_x), int(top_y)), glow_radius)

        pygame.draw.line(surface, (100, 60, 30), (bot_x, bot_y), (top_x, top_y), 3)
        pygame.draw.circle(surface, (50, 255, 50), (int(top_x), int(top_y)), 5)