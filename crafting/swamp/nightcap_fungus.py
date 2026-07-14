import pygame
import os
import random
from assets.tiles.prop import HarvestableProp
from sound_manager import sound_system


class NightcapFungus(HarvestableProp):
    """Nightcap-sieni. Pelitesti 16: yhtenäinen keräyskanava (E TAI
    klikkaus; poiminta-animaatio ja latauspalkki, ei työkaluvaatimusta)."""

    def __init__(self, x, y):
        # Koko: 60x60
        super().__init__(x, y, 60, 60, color=(80, 60, 100))

        self.loot_item = "Nightcap Fungus"
        self.resource_name = "Nightcap Fungus"
        self.resource_count = random.randint(3, 5) # 3-5 keräystä
        self.vfx_timer = 0
        self.interaction_range = 80
        self.interaction_label = "Pick"
        self.harvest_sound = "grass_pickup"
        # Nopea poiminta: 2 "nyppäisyä" per sieni
        self.swing_interval = 26
        self.channel_swings_needed = 2
        self._restart_pending = False

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
                except Exception: pass

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        # Ei ota vahinkoa, kerätään keräyskanavalla
        return 0

    def on_channel_swing(self, player, manager):
        if manager and hasattr(manager, "vfx"):
            manager.vfx.create_spores(self.rect.centerx, self.rect.centery)
        sound_system.play_sound_at(self.harvest_sound, self.rect.centerx,
                                   self.rect.centery, manager)

    def harvest(self, manager=None, harvester=None):
        """Yksi poimintasykli: +1 sieni."""
        if self.is_empty or manager is None:
            return
        self.resource_count -= 1
        manager.add_material(self.loot_item, 1)
        manager.vfx.show_damage(self.rect.centerx, self.rect.top - 20,
                                f"+1 {self.loot_item}", color=(100, 255, 100))
        sound_system.play_sound("recruit")
        # VFX: Pöllähdys
        if hasattr(manager, "vfx"):
            manager.vfx.create_spore_burst(self.rect.centerx,
                                           self.rect.centery)
        if self.resource_count <= 0:
            self.is_empty = True
            self.image = self.sprites.get("empty", self.image)
        else:
            self._restart_pending = True

    def update(self, obstacles=None, manager=None):
        if self.is_empty: return

        # Idle VFX (Itiöitä)
        self.vfx_timer += 1
        if self.vfx_timer > 40:
            self.vfx_timer = 0
            if manager and hasattr(manager, "vfx"):
                manager.vfx.create_spores(self.rect.centerx, self.rect.centery)

        self.update_channel(manager)
        if self._restart_pending and not self.channel_active and \
                not self.is_empty and manager is not None:
            self._restart_pending = False
            player = getattr(manager, "player_character", None)
            if player is not None:
                self.try_begin_channel(player, manager)
