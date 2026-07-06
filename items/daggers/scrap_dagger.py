import pygame
import os
import math
import random
from items.base_item import Weapon
from sound_manager import sound_system

class ScrapDagger(Weapon):
    def __init__(self):
        super().__init__()
        self.name = "Rusty Shiv"
        self.rarity = "Common"
        self.cost = 10
        self.description = "Barely sharp enough to cut."
        
        self.type = "melee"
        self.slot_type = "main_hand"
        self.weapon_group = "dagger"
        self.level_required = 1
        
        self.damage = 3
        self.attack_range = 25
        self.speed_bonus = 0.05 # Hieman hitaampi kuin weak dagger
        self.scaling = {"DEX": 0.6}
        
        self.charge_time = 0
        self.max_charge = 40 # Nopea lataus
        self.charge_enabled = True
        self.last_charge_tick = 0
        
        self.image = None
        self._load_image()

    def _load_image(self):
        path = "assets/gear/daggers/scrap_dagger.png"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (12, 24))
                self.big_image = img
            except: 
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
            pygame.draw.line(surface, (100, 100, 100), (x + size*0.4, y + size*0.6), (x + size*0.6, y + size*0.4), 3)

    def update_charge(self, owner, manager):
        # Resetoi lataus jos tauko
        now = pygame.time.get_ticks()
        if now - self.last_charge_tick > 100:
            self.charge_time = 0
        self.last_charge_tick = now

        owner.temp_speed_mult = 0.8 # Kevyt hidastus
        owner.is_charging = True
        if self.charge_time < self.max_charge:
            self.charge_time += 1

    def release_charge(self, owner, manager, target_pos):
        if self.charge_time > 10 and owner.attack_cooldown <= 0:
            # Stamina cost for throw
            base_cost = 15
            cost = max(5, int(base_cost - (owner.dexterity * 0.3)))
            
            if owner.current_stamina < cost:
                self.charge_time = 0 # Resetoi jos ei onnistu
                return
            owner.current_stamina -= cost
            
            # THROW DAGGER
            power = self.charge_time / self.max_charge
            dmg = self.calculate_damage({"dex": owner.dexterity})
            throw_dmg = int(dmg * (0.8 + power * 0.5))
            speed = 18
            
            # Luodaan ammus (käytetään tikarin kuvaa jos on)
            img = self.image
            proj_img = None
            if img:
                # Käännetään kuva osoittamaan oikealle (oletus on pysty)
                proj_img = pygame.transform.rotate(img, -90)
            
            from vfx import Projectile
            proj = Projectile(owner.rect.centerx, owner.rect.centery, target_pos, speed, throw_dmg, owner, manager, image=proj_img)
            manager.vfx.add_projectile(proj)
            owner.attack_cooldown = 30
        else:
            owner.perform_attack(None, manager, target_pos=target_pos)
        self.charge_time = 0

    def get_swing_rect(self, unit_rect, facing_right, attack_timer, total_cooldown, attack_vector=None):
        swing_w = 30
        swing_h = 30
        
        if attack_vector:
            dx, dy = attack_vector
            dist = math.hypot(dx, dy) or 1
            offset = 20 # Lyhyt kantama
            swing_x = unit_rect.centerx + (dx/dist) * offset - swing_w//2
            swing_y = unit_rect.centery + (dy/dist) * offset - swing_h//2
        else:
            swing_x = unit_rect.centerx if facing_right else unit_rect.centerx - swing_w
            swing_y = unit_rect.centery - 10
        return pygame.Rect(swing_x, swing_y, swing_w, swing_h)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown, total_cooldown=60, attack_vector=None):
        # Latausindikaattori (pieni tähti)
        if self.charge_time > 10:
            pygame.draw.circle(surface, (200, 255, 255), (unit_rect.centerx, unit_rect.top - 10), 3)
            
        if not self.image: return
        
        hand_x = unit_rect.centerx + (14 if facing_right else -14)
        hand_y = unit_rect.centery + 8
        
        angle = -90 if facing_right else 90 # Osoittaa eteenpäin
        scale = 1.0
        
        prog = 1.0 - (attack_cooldown / total_cooldown) if total_cooldown > 0 else 0
        anim_duration = 0.25 # Tikari on nopea
        
        if attack_cooldown > 0 and attack_vector and prog < anim_duration:
            anim_prog = prog / anim_duration
            
            dx, dy = attack_vector
            angle = math.degrees(math.atan2(-dy, dx)) - 90
            
            # Pisto (edestakaisin)
            if anim_prog < 0.5:
                # Ulos
                stab_pct = anim_prog / 0.5
                stab_len = 30 * stab_pct
                scale = 1.0 + (0.2 * stab_pct)
            else:
                # Sisään
                stab_pct = (anim_prog - 0.5) / 0.5
                stab_len = 30 * (1.0 - stab_pct)
                scale = 1.0
            
            # Siirrä kättä piston suuntaan
            dist = math.hypot(dx, dy) or 1
            hand_x += (dx/dist) * stab_len
            hand_y += (dy/dist) * stab_len
            
        img = self.image
        is_animating = (attack_cooldown > 0 and prog < anim_duration)
        
        if not facing_right and not is_animating: 
            img = pygame.transform.flip(img, True, False)
            
        if scale != 1.0:
            w = int(img.get_width() * scale)
            h = int(img.get_height() * scale)
            img = pygame.transform.scale(img, (w, h))
            
        rotated = pygame.transform.rotate(img, angle)
        rect = rotated.get_rect(center=(hand_x, hand_y))
        surface.blit(rotated, rect)

    def on_attack_start(self, attacker, target, manager):
        sound_system.play_sound(random.choice(['dagger_1', 'dagger_2', 'dagger_3', 'dagger_4']))