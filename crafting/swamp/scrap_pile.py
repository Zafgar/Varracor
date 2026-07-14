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
        self.glimmer_timer = random.randint(0, 100)
        # Yhtenäinen keräyskanava (pelitesti 16): 2 tonkaisua ~0.5 s välein
        self.swing_interval = 24
        self.channel_swings_needed = 2
        
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
                except Exception: pass

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        return 0

    def harvest(self, manager=None, harvester=None):
        # Sama saalislogiikka kuin ennen, mutta kanavan lopusta kutsuttuna
        super().harvest(manager, harvester)
        if self.is_empty:
            self.image = self.sprites.get("empty", self.image)

    def update(self, obstacles=None, manager=None):
        if self.is_empty: return

        # Välkehdintä (Glimmer) - Kiinnittää huomion
        self.glimmer_timer += 1
        if self.glimmer_timer > 120:
            self.glimmer_timer = 0
            if manager and hasattr(manager, "vfx"):
                manager.vfx.create_ore_glimmer(self.rect.centerx, self.rect.centery)

        # Yhtenäinen keräyskanava (E tai klikkaus; ks. HarvestableProp)
        self.update_channel(manager)
