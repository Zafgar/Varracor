import pygame
import os
import math
from items.base_item import Weapon
from sound_manager import sound_system

class WeakPickaxe(Weapon):
    def __init__(self):
        super().__init__()
        self.name = "Weak Pickaxe"
        self.rarity = "Common"
        self.cost = 50
        self.description = "A rusty tool used for mining Tier 1 rocks."
        
        self.type = "melee"
        self.slot_type = "main_hand"
        
        # TÄRKEÄ: Tämä yhdistää aseen Commanderin "Pickaxe Training" -taitoon
        self.weapon_group = "pickaxe" 
        
        self.damage = 5
        self.attack_range = 60
        self.speed_bonus = -0.1
        self.scaling = {"STR": 0.6}
        
        # Resurssien keräys logiikkaa varten
        self.tool_type = "pickaxe"
        self.tool_tier = 1
        
        self.image = None
        self._load_image()

    def _load_image(self):
        path = "assets/gear/tools/weak_pickaxe.png"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                # Original 700x1100 -> Skaalataan hahmoon sopivaksi (n. 25x40)
                self.image = pygame.transform.smoothscale(img, (25, 40))
            except Exception: 
                print(f"Failed to load {path}")
                self.image = None

    def draw_card_icon(self, surface, x, y, size):
        if self.image:
            # Säilytetään kuvasuhde ikonissa
            ratio = self.image.get_width() / self.image.get_height()
            new_h = size
            new_w = int(new_h * ratio)
            scaled = pygame.transform.smoothscale(self.image, (new_w, new_h))
            surface.blit(scaled, (x + (size - new_w) // 2, y))
        else:
            # Fallback piirto jos kuvaa ei ole
            pygame.draw.line(surface, (100, 100, 100), (x+size*0.2, y+size*0.2), (x+size*0.8, y+size*0.8), 4)
            pygame.draw.line(surface, (150, 150, 150), (x+size*0.2, y+size*0.2), (x+size*0.5, y+size*0.2), 6)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown):
        # Jos kuvaa ei ole, ei piirretä mitään (tai fallback viiva)
        if not self.image:
            return

        # Käden sijainti
        offset_x = 5 if facing_right else -5
        hand_x = unit_rect.centerx + offset_x
        hand_y = unit_rect.centery + 5

        # Lasketaan kulma (heilahdus lyödessä)
        base_angle = -45 if facing_right else 45
        swing = 0
        
        if attack_cooldown > 0:
            # Lyöntianimaatio
            progress = 1.0 - (attack_cooldown / 60.0) # Oletetaan 60 attack speed
            if progress < 0: progress = 0
            
            # "Menee pään päälle ja sieltä iskee alas"
            # Siniaalto: 0 -> 1 (Windup) -> 0 -> -1 (Strike) -> 0
            swing_arc = 100
            raw_swing = math.sin(progress * 6.28)
            
            if facing_right: swing = raw_swing * swing_arc
            else: swing = -raw_swing * swing_arc
        
        angle = base_angle + swing

        # Käännetään kuva suunnan mukaan
        img_to_draw = self.image
        if not facing_right:
            img_to_draw = pygame.transform.flip(self.image, True, False)

        # Pyöritetään
        rotated_img = pygame.transform.rotate(img_to_draw, angle)
        
        # Asetetaan kuva käden kohdalle (kahva käteen)
        rect = rotated_img.get_rect(center=(hand_x, hand_y))
        
        # Hienosäätö: Siirretään kuvaa hieman ylös/ulos jotta se näyttää olevan kädessä
        offset_dist = 10
        if facing_right:
            rect.x += offset_dist
        else:
            rect.x -= offset_dist
        rect.y -= 15

        surface.blit(rotated_img, rect)

    def on_attack_start(self, attacker, target, manager):
        sound_system.play_sound('attack_melee')
        # Tähän voisi lisätä "clink" äänen jos osuu kiveen
