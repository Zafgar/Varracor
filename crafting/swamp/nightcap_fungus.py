import pygame
import os
import random
import math
from assets.tiles.prop import Prop
from sound_manager import sound_system

class NightcapFungus(Prop):
    def __init__(self, x, y):
        # Koko: 60x60
        super().__init__(x, y, 60, 60, color=(80, 60, 100))
        
        self.loot_item = "Nightcap Fungus"
        self.resource_count = random.randint(3, 5) # 3-5 keräystä
        self.interact_timer = 0
        self.interact_max = 60 # 1 sekunti per keräys
        self.vfx_timer = 0
        self.is_empty = False
        self.interaction_range = 80
        self.interaction_label = "Pick"
        
        # Ladataan kuvat
        self.sprites = {}
        self._load_images()
        self.image = self.sprites.get("idle", self.image)
        
        # Ei estä liikkumista
        self.rect = pygame.Rect(x + 15, y + 30, 30, 30)
        self.blocks_projectiles = False

    def _load_images(self):
        base = "assets/crafting/swamp/nightcap"
        for state in ["idle", "hit", "empty"]:
            path = f"{base}_{state}.png"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.sprites[state] = pygame.transform.scale(img, (60, 60))
                except: pass

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        # Ei ota vahinkoa, kerätään E-näppäimellä
        return 0

    def update(self, obstacles=None, manager=None):
        if self.is_empty: return
        
        # Idle VFX (Itiöitä)
        self.vfx_timer += 1
        if self.vfx_timer > 40:
            self.vfx_timer = 0
            if manager and hasattr(manager, "vfx"):
                manager.vfx.create_spores(self.rect.centerx, self.rect.centery)

        # Interaction Logic (Hold E)
        if manager and manager.player_character:
            player = manager.player_character
            dist = math.hypot(player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery)
            
            keys = pygame.key.get_pressed()
            if dist < self.interaction_range and keys[pygame.K_e]:
                self.interact_timer += 1
                
                # Keräys valmis
                if self.interact_timer >= self.interact_max:
                    self.interact_timer = 0
                    self.resource_count -= 1
                    
                    # Loot
                    manager.add_material(self.loot_item, 1)
                    manager.vfx.show_damage(self.rect.centerx, self.rect.top - 20, f"+1 {self.loot_item}", color=(100, 255, 100))
                    sound_system.play_sound("recruit")
                    
                    # VFX: Pöllähdys
                    if hasattr(manager, "vfx"):
                        manager.vfx.create_spore_burst(self.rect.centerx, self.rect.centery)
                    
                    # Tyhjä?
                    if self.resource_count <= 0:
                        self.is_empty = True
                        self.image = self.sprites.get("empty", self.image)
            else:
                self.interact_timer = 0

    def draw_on_screen(self, screen, offset):
        super().draw_on_screen(screen, offset)
        if not self.is_empty and self.interact_timer > 0:
            self.draw_interaction_bar(screen, offset, self.interact_timer / self.interact_max)
