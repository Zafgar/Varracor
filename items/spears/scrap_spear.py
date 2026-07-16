import pygame
import os
import math
import random
from items.base_item import Weapon
from sound_manager import sound_system

class ScrapSpear(Weapon):
    def __init__(self):
        super().__init__()
        self.name = "Splintered Pole"
        self.rarity = "Common"
        self.cost = 20
        self.description = "Long reach, but very fragile."
        
        self.type = "melee"
        self.slot_type = "main_hand"
        self.weapon_group = "spear"
        self.two_handed = True  # varaa molemmat kadet - ei kilpea/off-handia
        self.level_required = 1
        
        self.damage = 6
        self.attack_range = 55
        self.speed_bonus = -0.05
        self.scaling = {"STR": 0.3, "DEX": 0.3}
        
        self.charge_time = 0
        self.max_charge = 60
        self.charge_enabled = True
        self.last_charge_tick = 0
        
        self.image = None
        self._load_image()

    def _load_image(self):
        path = "assets/gear/spears/scrap_spear.png"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (10, 64))
                self.big_image = img
            except Exception: 
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
            pygame.draw.line(surface, (120, 90, 50), (x + size*0.2, y + size*0.8), (x + size*0.8, y + size*0.2), 3)

    def update_charge(self, owner, manager):
        # Resetoi lataus jos tauko
        now = pygame.time.get_ticks()
        if now - self.last_charge_tick > 100:
            self.charge_time = 0
        self.last_charge_tick = now

        # Hidastaa liikettä ladatessa
        owner.temp_speed_mult = 0.6
        owner.is_charging = True
        if self.charge_time < self.max_charge:
            self.charge_time += 1

    def release_charge(self, owner, manager, target_pos):
        if self.charge_time > 15 and owner.attack_cooldown <= 0:
            # CHARGE DASH
            dx = target_pos[0] - owner.rect.centerx
            dy = target_pos[1] - owner.rect.centery
            
            # Laske vahinko latauksen mukaan
            power = self.charge_time / self.max_charge
            dmg = self.calculate_damage({"str": owner.strength, "dex": owner.dexterity})
            dash_dmg = int(dmg * (1.5 + power)) # 1.5x - 2.5x vahinko
            
            if owner.perform_dash(dx, dy):
                owner.dash_damage = dash_dmg
                owner.dash_speed_mult = 4.0 # Nopea syöksy
                owner.attack_cooldown = 40 # Estä spämmäys
        else:
            owner.perform_attack(None, manager, target_pos=target_pos)
        self.charge_time = 0

    def get_swing_rect(self, unit_rect, facing_right, attack_timer, total_cooldown, attack_vector=None):
        swing_w = 40
        swing_h = 40
        
        if attack_vector:
            dx, dy = attack_vector
            dist = math.hypot(dx, dy) or 1
            offset = 50 # Pitkä kantama
            swing_x = unit_rect.centerx + (dx/dist) * offset - swing_w//2
            swing_y = unit_rect.centery + (dy/dist) * offset - swing_h//2
        else:
            swing_x = unit_rect.centerx if facing_right else unit_rect.centerx - swing_w
            swing_y = unit_rect.centery - 5
        return pygame.Rect(swing_x, swing_y, swing_w, swing_h)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown, total_cooldown=60, attack_vector=None):
        # Latausefekti (täristään)
        if self.charge_time > 0:
            shake = random.randint(-1, 1)
            unit_rect = unit_rect.move(shake, 0)
            
        if not self.image: return
        
        hand_x = unit_rect.centerx + (10 if facing_right else -10)
        hand_y = unit_rect.centery + 10
        
        angle = -80 if facing_right else 80 # Osoittaa eteen ja vähän ylös
        scale_y = 1.0
        
        prog = 1.0 - (attack_cooldown / total_cooldown) if total_cooldown > 0 else 0
        anim_duration = 0.35
        
        if attack_cooldown > 0 and attack_vector is not None and prog < anim_duration:
            anim_prog = prog / anim_duration
            
            dx, dy = attack_vector
            angle = math.degrees(math.atan2(-dy, dx)) - 90
            
            if anim_prog < 0.4:
                thrust_pct = anim_prog / 0.4
                thrust = 55 * thrust_pct
                scale_y = 1.0 + (0.3 * thrust_pct)
            else:
                thrust_pct = (anim_prog - 0.4) / 0.6
                thrust = 55 * (1.0 - thrust_pct)
                scale_y = 1.0
            
            dist = math.hypot(dx, dy) or 1
            hand_x += (dx/dist) * thrust
            hand_y += (dy/dist) * thrust
            
        img = self.image
        is_animating = (attack_cooldown > 0 and prog < anim_duration)
        
        if not facing_right and not is_animating: 
            img = pygame.transform.flip(img, True, False)
            
        if scale_y != 1.0:
            w = img.get_width()
            h = int(img.get_height() * scale_y)
            img = pygame.transform.scale(img, (w, h))
            
        rotated = pygame.transform.rotate(img, angle)
        rect = rotated.get_rect(center=(hand_x, hand_y))
        surface.blit(rotated, rect)

    def on_attack_start(self, attacker, target, manager):
        sound_system.play_sound(random.choice(['spear_1', 'spear_2', 'spear_3', 'spear_4']))