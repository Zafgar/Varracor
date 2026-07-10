import pygame
import os
import math
import random
from items.base_item import Weapon
from sound_manager import sound_system
from vfx import ArrowProjectile

class ScrapCrossbow(Weapon):
    def __init__(self):
        super().__init__()
        self.name = "Jammed Crossbow"
        self.rarity = "Common"
        self.cost = 25
        self.description = "Misfires constantly, but works."
        
        self.type = "ranged"
        self.slot_type = "main_hand"
        self.weapon_group = "crossbow"
        self.level_required = 1
        
        self.damage = 14 # Kovempi vahinko
        self.attack_range = 350
        self.speed_bonus = -0.1
        self.scaling = {"DEX": 0.7, "STR": 0.2}
        
        self.is_loaded = False
        self.load_progress = 0
        self.load_time = 90 # 1.5 sekuntia lataus
        self.charge_enabled = True
        self.last_charge_tick = 0
        self.just_finished_loading = False # UUSI: Estää välittömän laukaisun latauksen jälkeen
        
        self.image = None
        self._load_image()

    def _load_image(self):
        path = "assets/gear/crossbows/scrap_crossbow.png"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (32, 24))
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
            pygame.draw.line(surface, (100, 80, 60), (x+size*0.2, y+size*0.5), (x+size*0.8, y+size*0.5), 4)

    def update_charge(self, owner, manager):
        # Jos ei ladattu, lataa
        if not self.is_loaded:
            # Resetoi lataus jos tauko (pelaaja päästi napin irti)
            now = pygame.time.get_ticks()
            if now - self.last_charge_tick > 100:
                self.load_progress = 0
            self.last_charge_tick = now

            owner.temp_speed_mult = 0.0 # Pysähdy lataamaan
            owner.is_charging = True
            
            # Kuluta staminaa (raskas viritys)
            drain = max(0.2, 0.8 - (owner.strength * 0.02)) # STR auttaa varsijousen virityksessä
            if owner.current_stamina > drain:
                owner.current_stamina -= drain
            else:
                return # Ei jaksa virittää
            
            self.load_progress += 1
            
            if self.load_progress >= self.load_time:
                self.is_loaded = True
                self.just_finished_loading = True # Merkkaa että lataus valmistui juuri
                self.load_progress = 0
                sound_system.play_sound("click") # Latausääni
                if manager: manager.vfx.show_damage(owner.rect.centerx, owner.rect.top - 20, "LOADED", color=(255, 255, 0))
        
        # Jos ladattu, ei tee mitään (odottaa vapautusta ampuakseen)

    def release_charge(self, owner, manager, target_pos):
        if self.is_loaded and owner.attack_cooldown <= 0:
            # UUSI: Jos lataus valmistui juuri tässä painalluksessa, älä ammu vielä
            if self.just_finished_loading:
                self.just_finished_loading = False
                return

            # Ammu heti
            dmg = self.calculate_damage({"dex": owner.dexterity, "str": owner.strength})
            bolt = ArrowProjectile(owner.rect.centerx, owner.rect.centery, target_pos, 25, dmg, owner, manager, is_bolt=True, max_range=self.attack_range)
            manager.vfx.add_projectile(bolt)
            
            sound_system.play_sound("crossbow_1")
            self.is_loaded = False
            self.just_finished_loading = False
            owner.attack_cooldown = 20
        else:
            # Jos vapauttaa kesken latauksen, lataus nollautuu
            self.load_progress = 0

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown, total_cooldown=60, attack_vector=None):
        # Laske kulma
        angle = 0
        if attack_vector:
            dx, dy = attack_vector
            angle = -math.degrees(math.atan2(dy, dx))
        else:
            angle = 0 if facing_right else 180

        # Piirto pinnalle
        s_size = 64
        s = pygame.Surface((s_size, s_size), pygame.SRCALPHA)
        cx, cy = s_size // 2, s_size // 2
        
        # Piirrä varsijousi (osoittaen oikealle)
        color = (100, 80, 60)
        # Runko
        pygame.draw.line(s, color, (cx - 10, cy), (cx + 10, cy), 4)
        # Kaari
        pygame.draw.line(s, (150, 150, 150), (cx + 5, cy - 10), (cx + 5, cy + 10), 2)
        
        # Latauspalkki pään päällä jos ladataan
        if self.load_progress > 0 and not self.is_loaded:
            pct = self.load_progress / self.load_time
            bx = unit_rect.centerx - 15
            by = unit_rect.top - 15
            pygame.draw.rect(surface, (50, 50, 50), (bx, by, 30, 4))
            pygame.draw.rect(surface, (255, 200, 0), (bx, by, int(30 * pct), 4))
            
        if self.is_loaded:
            # Näytä nuoli valmiina
            pygame.draw.line(s, (200, 200, 200), (cx - 5, cy), (cx + 8, cy), 1)

        # Käännä ja piirrä
        rotated = pygame.transform.rotate(s, angle)
        r_rect = rotated.get_rect(center=(unit_rect.centerx, unit_rect.centery))
        surface.blit(rotated, r_rect)