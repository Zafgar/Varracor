import pygame
import os
import math
import random
from items.base_item import Weapon
from sound_manager import sound_system
from vfx import ArrowProjectile

class ScrapBow(Weapon):
    def __init__(self):
        super().__init__()
        self.name = "Scrap Bow"
        self.rarity = "Common"
        self.cost = 30
        self.description = "A simple bow made of scrap wood."
        
        self.type = "ranged"
        self.slot_type = "main_hand"
        self.weapon_group = "bow"
        self.level_required = 1
        
        self.damage = 6
        self.attack_range = 270
        self.speed_bonus = 0.0
        self.scaling = {"DEX": 0.8}
        
        self.charge_time = 0
        self.max_charge = 60 # 1 sekunti täyteen lataukseen
        self.charge_enabled = True
        self.last_charge_tick = 0
        
        self.image = None
        self._load_image()

    def _load_image(self):
        path = "assets/gear/bows/scrap_bow.png"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (20, 48))
                self.big_image = img
            except Exception: pass

    def draw_card_icon(self, surface, x, y, size):
        img = getattr(self, "big_image", self.image)
        if img:
            ratio = img.get_width() / img.get_height()
            new_h = size
            new_w = int(new_h * ratio)
            scaled = pygame.transform.smoothscale(img, (new_w, new_h))
            surface.blit(scaled, (x + (size - new_w) // 2, y))
        else:
            # Fallback
            pygame.draw.arc(surface, (150, 100, 50), (x + size*0.2, y + size*0.2, size*0.6, size*0.6), -1.5, 1.5, 3)
            pygame.draw.line(surface, (200, 200, 200), (x + size*0.5, y + size*0.2), (x + size*0.5, y + size*0.8), 1)

    def update_charge(self, owner, manager):
        # Resetoi lataus jos edellisestä kerrasta on aikaa (esim. stun tai napin vapautus)
        now = pygame.time.get_ticks()
        if now - self.last_charge_tick > 100:
            self.charge_time = 0
        self.last_charge_tick = now

        # Hidastaa liikettä ladatessa
        owner.temp_speed_mult = 0.5
        owner.is_charging = True
        
        # Kuluta staminaa ladatessa: jännitys on raskasta ilman harjoitusta.
        # DEX keventää; Steady Draw -skill puolittaa.
        drain = max(0.15, 0.9 - (owner.dexterity * 0.02))
        if getattr(owner, "has_steady_draw", False):
            drain *= 0.5
        if owner.current_stamina > drain:
            owner.current_stamina -= drain
        else:
            # Jos stamina loppuu, lataus ei etene (tai voisi pakottaa laukauksen)
            return
        
        if self.charge_time < self.max_charge:
            self.charge_time += 1
            
    def release_charge(self, owner, manager, target_pos):
        if self.charge_time > 0 and owner.attack_cooldown <= 0: # Sallitaan nopeat laukaukset, jos ei jäähyä
            # Laske voima (0.0 - 1.0)
            power = self.charge_time / self.max_charge
            
            # Stats
            dmg = self.calculate_damage({"dex": owner.dexterity})
            final_dmg = int(dmg * (0.5 + power * 0.5)) # 50% - 100% vahinko
            speed = 10 + power * 15 # Nopeus kasvaa latauksella
            
            # Luo ammus
            arrow = ArrowProjectile(owner.rect.centerx, owner.rect.centery, target_pos, speed, final_dmg, owner, manager, max_range=self.attack_range)
            manager.vfx.add_projectile(arrow)
            
            sound_system.play_sound("attack_bow")
            owner.attack_cooldown = 30 # Fire rate
            
        self.charge_time = 0 # Nollaa lataus

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown, total_cooldown=60, attack_vector=None):
        # Laske kulma kursorin/kohteen suuntaan
        angle = 0
        if attack_vector:
            dx, dy = attack_vector
            # atan2 antaa kulman radiaaneina (0 on oikealle, kasvaa myötäpäivään pygame-koordinaateissa)
            # pygame.transform.rotate kääntää vastapäivään.
            angle = -math.degrees(math.atan2(dy, dx))
        else:
            angle = 0 if facing_right else 180

        # Luodaan väliaikainen pinta jousen piirtämistä ja kääntämistä varten
        s_size = 80
        s = pygame.Surface((s_size, s_size), pygame.SRCALPHA)
        cx, cy = s_size // 2, s_size // 2
        
        # Jos ladataan, piirrä jännitys
        draw_offset = 0
        if self.charge_time > 0:
            draw_offset = int((self.charge_time / self.max_charge) * 10)
            
        # Piirretään jousi pinnalle (osoittaen oikealle oletuksena)
        # Kaari
        rect = pygame.Rect(cx - 10, cy - 20, 20, 40)
        pygame.draw.arc(s, (139, 69, 19), rect, -1.0, 1.0, 3)
        
        # Jänne (String)
        string_x = cx - 5 - draw_offset
        pygame.draw.line(s, (200, 200, 200), (cx + 8, cy - 18), (string_x, cy), 1)
        pygame.draw.line(s, (200, 200, 200), (string_x, cy), (cx + 8, cy + 18), 1)

        # Käännetään ja piirretään
        rotated = pygame.transform.rotate(s, angle)
        r_rect = rotated.get_rect(center=(unit_rect.centerx, unit_rect.centery))
        surface.blit(rotated, r_rect)