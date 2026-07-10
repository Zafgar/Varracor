import pygame
import os
import math
from items.base_item import Weapon
from sound_manager import sound_system

class WoodcuttersAxe(Weapon):
    def __init__(self):
        super().__init__()
        self.name = "Woodcutter's Axe"
        self.rarity = "Common"
        self.cost = 60
        self.description = "A reliable axe for gathering wood."
        
        self.type = "melee"
        self.slot_type = "main_hand"
        self.weapon_group = "lumber_axe"
        
        self.damage = 7
        self.attack_range = 60
        self.speed_bonus = -0.15
        self.scaling = {"STR": 0.7}
        
        # Tärkeät resurssien keräykseen
        self.tool_type = "axe"
        self.tool_tier = 1
        
        self.image = None
        self._load_image()

    def _load_image(self):
        # Try specific image first, fallback to weak lumberaxe
        path = "assets/gear/tools/woodcutters_axe.png"
        if not os.path.exists(path):
            path = "assets/gear/tools/weak_lumberaxe.png"
            
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (18, 45))
            except Exception: 
                pass

    def draw_card_icon(self, surface, x, y, size):
        if self.image:
            ratio = self.image.get_width() / self.image.get_height()
            new_h = size
            new_w = int(new_h * ratio)
            scaled = pygame.transform.smoothscale(self.image, (new_w, new_h))
            surface.blit(scaled, (x + (size - new_w) // 2, y))
        else:
            pygame.draw.line(surface, (139, 69, 19), (x+size*0.2, y+size*0.8), (x+size*0.8, y+size*0.2), 4)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown):
        if not self.image: return

        offset_x = 5 if facing_right else -5
        hand_x = unit_rect.centerx + offset_x
        hand_y = unit_rect.centery + 5

        base_angle = -30 if facing_right else 30
        swing = 0
        
        if attack_cooldown > 0:
            progress = 1.0 - (attack_cooldown / 60.0)
            if progress < 0: progress = 0
            swing_arc = 110
            raw_swing = math.sin(progress * 6.28)
            if facing_right: swing = raw_swing * swing_arc
            else: swing = -raw_swing * swing_arc
        
        angle = base_angle + swing

        img_to_draw = self.image
        if not facing_right:
            img_to_draw = pygame.transform.flip(self.image, True, False)

        rotated_img = pygame.transform.rotate(img_to_draw, angle)
        rect = rotated_img.get_rect(center=(hand_x, hand_y))
        
        if facing_right: rect.x += 8
        else: rect.x -= 8
        rect.y -= 12

        surface.blit(rotated_img, rect)

    def on_attack_start(self, attacker, target, manager):
        sound_system.play_sound('attack_melee')