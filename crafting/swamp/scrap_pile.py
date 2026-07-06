import pygame
import os
import random
import math
from assets.tiles.prop import HarvestableProp
from sound_manager import sound_system

class ScrapPile(HarvestableProp):
    def __init__(self, x, y):
        super().__init__(x, y, 70, 50, color=(100, 80, 60))
        
        self.resource_name = "Scrap Iron"
        self.interact_timer = 0
        self.interact_max = 30 # 0.5s (Faster)
        self.glimmer_timer = random.randint(0, 100)
        
        # HarvestableProp asetukset
        self.min_drop = 1
        self.max_drop = 3
        self.harvest_sound = "mining_hit"
        self.interaction_range = 80
        self.interaction_label = "Scavenge"
        
        # Ladataan kuvat
        self.sprites = {}
        self._load_images()
        self.image = self.sprites.get("idle", self.image)
        
        # Ei estä liikkumista
        self.rect = pygame.Rect(x + 5, y + 10, 60, 30)

    def _load_images(self):
        base = "assets/crafting/swamp/scrap"
        for state in ["idle", "hit", "empty"]:
            path = f"{base}_{state}.png"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.sprites[state] = pygame.transform.scale(img, (70, 50))
                except: pass

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        return 0

    # Ylikirjoitetaan harvest, koska tässä on erikoislogiikkaa (interact timer)
    # Mutta jos AI kutsuu harvest(), se käyttää HarvestableProp:n logiikkaa (instant)
    # Pelaaja käyttää update-loopin interactia.

    def update(self, obstacles=None, manager=None):
        if self.is_empty: return

        # Välkehdintä (Glimmer) - Kiinnittää huomion
        self.glimmer_timer += 1
        if self.glimmer_timer > 120:
            self.glimmer_timer = 0
            if manager and hasattr(manager, "vfx"):
                manager.vfx.create_ore_glimmer(self.rect.centerx, self.rect.centery)

        if manager and manager.player_character:
            player = manager.player_character
            dist = math.hypot(player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery)
            
            keys = pygame.key.get_pressed()
            if dist < self.interaction_range and keys[pygame.K_e]:
                self.interact_timer += 1
                
                if self.interact_timer >= self.interact_max:
                    self.is_empty = True
                    self.image = self.sprites.get("empty", self.image)
                    
                    count = random.randint(self.min_drop, self.max_drop)
                    manager.add_material(self.resource_name, count)
                    manager.vfx.show_damage(self.rect.centerx, self.rect.top - 20, f"+{count} {self.resource_name}", color=(200, 200, 200))
                    sound_system.play_sound("recruit")
                    
                    # Pölypilvi
                    if hasattr(manager, "vfx"):
                        manager.vfx.create_dust_cloud(self.rect.centerx, self.rect.centery)
            else:
                self.interact_timer = 0

    def draw_on_screen(self, screen, offset):
        super().draw_on_screen(screen, offset)
        if not self.is_empty and self.interact_timer > 0:
            self.draw_interaction_bar(screen, offset, self.interact_timer / self.interact_max)
