import pygame
import math
from settings import *
from sound_manager import sound_system

class RatPoisonBow:
    def __init__(self):
        self.name = "Rat Poison Bow"
        self.type = "ranged"
        self.slot_type = "main_hand"
        self.damage = 12
        self.attack_range = 250
        self.rarity = "Rare"
        self.description = "Arrows coated in sewer sludge."
        self.cost = 450
        self.speed_bonus = 0.1
        self.weapon_group = "bow"
        self.two_handed = True  # varaa molemmat kadet - ei kilpea/off-handia
        self.level_required = 2
        self.in_shop = False

    def on_hit(self, attacker, target, dmg_dealt, manager):
        if target and not target.is_dead:
            target.apply_status("Poison", 180, damage=3)
            if manager and manager.vfx:
                manager.vfx.show_damage(target.rect.centerx, target.rect.top - 20, "POISONED!", color=(100, 255, 100))

    def on_attack_start(self, attacker, target, manager):
        sound_system.play_sound('attack_bow')
        if manager and manager.vfx:
            # Luodaan nuoli (oletetaan että create_arrow on olemassa, kuten WeakBow:ssa)
            manager.vfx.create_arrow(attacker.rect.center, target.rect.center)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown):
        offset_x = 5 if facing_right else -5
        hand_x = unit_rect.centerx + offset_x
        hand_y = unit_rect.centery
        
        top = (hand_x, hand_y - 15)
        bot = (hand_x, hand_y + 15)
        mid = (hand_x + (8 if facing_right else -8), hand_y)
        
        pull = 0
        if attack_cooldown > 0 and attack_cooldown < 20:
             pull = (1 - (attack_cooldown/20)) * 10
        
        pull_x = hand_x + (-10 if facing_right else 10) * (pull/10)
        
        # Poison Glow
        pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.5
        glow_width = 4 + int(pulse * 2)
        pygame.draw.lines(surface, (40, 200, 40), False, [top, mid, bot], glow_width)

        # Jousen runko (Vihreä)
        pygame.draw.lines(surface, (60, 100, 60), False, [top, mid, bot], 2)
        # Jänne
        pygame.draw.lines(surface, (200, 200, 200), False, [top, (pull_x, hand_y), bot], 1)

        if pull > 2:
            tip_x = pull_x + (20 if facing_right else -20)
            # Nuoli (Myrkynvihreä)
            pygame.draw.line(surface, (50, 255, 50), (pull_x, hand_y), (tip_x, hand_y), 2)

    def draw_card_icon(self, surface, x, y, size):
        pygame.draw.rect(surface, (20, 30, 20), (x, y, size, size), border_radius=5)
        pygame.draw.rect(surface, (60, 180, 60), (x, y, size, size), 2, border_radius=5)
        
        cx, cy = x + size//2, y + size//2
        s = size
        
        # Jousen kaari (Vihertävä puu)
        rect = pygame.Rect(x + s*0.2, y + s*0.2, s*0.6, s*0.6)
        pygame.draw.arc(surface, (100, 140, 80), rect, -0.5, 3.14 + 0.5, 3)
        
        # Jänne
        pygame.draw.line(surface, (200, 200, 200), (x + s*0.2, y + s*0.5), (x + s*0.8, y + s*0.5), 1)
        
        # Nuoli (Vihreä kärki)
        pygame.draw.line(surface, (160, 120, 80), (cx, cy + s*0.1), (cx, cy - s*0.2), 2)
        pygame.draw.polygon(surface, (50, 255, 50), [(cx, cy - s*0.25), (cx - 3, cy - s*0.18), (cx + 3, cy - s*0.18)])
