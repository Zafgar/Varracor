import pygame
import os
import random
from assets.tiles.prop import HarvestableProp
from sound_manager import sound_system


class VoidIronNode(HarvestableProp):
    """Void-Iron -suoni. Pelitesti 16: yhtenäinen keräyskanava
    (E TAI klikkaus; hakku-iskut, latauspalkki). Vaatii Tier 3 hakun."""

    def __init__(self, x, y):
        super().__init__(x, y, 80, 80, color=(20, 20, 30))

        self.loot_item = "Void-Iron"
        self.resource_name = "Void-Iron"
        self.resource_count = random.randint(1, 2) # Harvinainen, 1-2 kpl
        self.vfx_timer = 0
        self.interaction_range = 80
        self.interaction_label = "Mine"
        self.required_tool = "pickaxe"
        self.required_tier = 3
        self.harvest_sound = "mining_hit"
        # Hidas louhinta: 3 iskua per malmi (~1.5 s kuten ennen)
        self.swing_interval = 30
        self.channel_swings_needed = 3
        self._restart_pending = False

        self.sprites = {}
        self._load_images()
        self.image = self.sprites.get("idle", self.image)

        # Estää liikkumisen
        self.rect = pygame.Rect(x + 10, y + 20, 60, 50)

    def _load_images(self):
        base = "assets/crafting/swamp/void_iron"
        for state in ["idle", "hit", "empty"]:
            path = f"{base}_{state}.png"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.sprites[state] = pygame.transform.scale(img, (80, 80))
                except Exception: pass

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        return 0

    def harvest(self, manager=None, harvester=None):
        """Yksi louhintasykli: +1 Void-Iron."""
        if self.is_empty or manager is None:
            return
        self.resource_count -= 1
        manager.add_material(self.loot_item, 1)
        manager.vfx.show_damage(self.rect.centerx, self.rect.top - 20,
                                f"+1 {self.loot_item}", color=(200, 100, 255))
        sound_system.play_sound("mining_success")
        # VFX: Void purkaus
        if hasattr(manager, "vfx"):
            for _ in range(5):
                manager.vfx.create_void_particles(self.rect.centerx,
                                                  self.rect.centery)
        if self.resource_count <= 0:
            self.is_empty = True
            self.image = self.sprites.get("empty", self.image)
            sound_system.play_sound("mining_break")
        else:
            self._restart_pending = True

    def update(self, obstacles=None, manager=None):
        if self.is_empty: return

        # Idle VFX (Void Glow)
        self.vfx_timer += 1
        if self.vfx_timer > 20:
            self.vfx_timer = 0
            if manager and hasattr(manager, "vfx"):
                manager.vfx.create_void_particles(self.rect.centerx, self.rect.centery)

        self.update_channel(manager)
        if self._restart_pending and not self.channel_active and \
                not self.is_empty and manager is not None:
            self._restart_pending = False
            player = getattr(manager, "player_character", None)
            if player is not None:
                self.try_begin_channel(player, manager)
