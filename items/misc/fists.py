import pygame
import random
from items.base_item import Weapon
from sound_manager import sound_system

class Fists(Weapon):
    def __init__(self):
        super().__init__()
        self.name = "Fists"
        self.rarity = "Common"
        self.cost = 0
        self.description = "Your trusty knuckles."
        
        # TÄRKEÄT: Tyyppi ja slotti
        self.type = "melee" 
        self.slot_type = "main_hand"
        
        self.damage = 1         # Hieman parempi kuin 1, jotta tekee edes jotain vahinkoa
        self.attack_range = 45  # Riittävä kantama
        self.speed_bonus = 0.2  # Nyrkit ovat nopeat! (+20% hyökkäysnopeus)
        
        # Nyrkit käyttävät voimaa ja nopeutta
        self.scaling = {'STR': 0.1, 'DEX': 0.1}

    def draw_card_icon(self, surface, x, y, size):
        # Yksinkertainen nyrkki-ikoni (rusehtava ympyrä)
        pygame.draw.circle(surface, (200, 150, 100), (x+size//2, y+size//2), size//3)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_timer):
        # Normaalisti nyrkkejä ei piirretä, mutta lyönnin aikana
        # piirretään pieni "nyrkki", joka käy edessä.
        if attack_timer > 0:
            # Animaatio: Käsi menee eteen ja palaa takaisin
            # attack_timer 20 -> 0
            progress = 1 - (attack_timer / 20) # 0.0 -> 1.0
            
            # Matka eteenpäin
            reach = 15 
            offset_x = (reach * progress) if progress < 0.5 else (reach * (1-progress))
            
            direction = 1 if facing_right else -1
            hand_x = unit_rect.centerx + (15 * direction) + (offset_x * direction)
            hand_y = unit_rect.centery + 5
            
            # Piirrä nyrkki
            pygame.draw.circle(surface, (200, 150, 100), (int(hand_x), int(hand_y)), 5)

    # --- HOOKIT (Ääni ja Osuma) ---
    def on_attack_start(self, attacker, target, manager):
        # Nyrkin ääni (käytetään randomilla fist_1..4)
        fist_sounds = ['fist_1', 'fist_2', 'fist_3', 'fist_4']
        sound_system.play_sound(random.choice(fist_sounds)) 

    def on_hit(self, attacker, target, damage_dealt, manager):
        if damage_dealt > 0:
            # Pieni veri-efekti
            manager.vfx.create_blood(target.rect.centerx, target.rect.centery)