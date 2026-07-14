import pygame
import os
import random
from assets.tiles.prop import HarvestableProp
from sound_manager import sound_system


class SwampTree(HarvestableProp):
    """Hökkelimetsän puu. Pelitesti 16: käyttää yhtenäistä keräyskanavaa
    (E TAI klikkaus aloittaa; iskut, latauspalkki ja liike keskeyttää).
    Melee-lyönti kirveellä toimii yhä chop()-polun kautta."""

    def __init__(self, x, y):
        # Iso puu (140x220)
        super().__init__(x, y, 140, 220, color=(40, 50, 30))

        self.loot_item = "Swamp Wood"
        self.resource_name = "Swamp Wood"
        self.resource_count = 3          # keräyssyklejä per puu
        self.max_hits = 5
        self.current_hits = self.max_hits
        self.interaction_range = 100
        self.interaction_label = "Chop"
        self.required_tool = "axe"
        self.required_tier = 1
        self.harvest_sound = "axe_1"
        # Kanava: 2 iskua per sykli (~1 s), jatkuu automaattisesti
        self.swing_interval = 30
        self.channel_swings_needed = 2
        self._restart_pending = False

        self.sprites = {}
        self._load_images()
        self.image = self.sprites.get("idle", self.image)

        # Törmäys vain juuressa
        self.rect = pygame.Rect(x + 50, y + 180, 40, 30)

    def _load_images(self):
        base = "assets/crafting/swamp/swamp_tree"
        for state in ["idle", "hit", "empty"]:
            path = f"{base}_{state}.png"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.sprites[state] = pygame.transform.scale(img, (140, 220))
                except Exception: pass

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        # Ohjataan vahinko chop-metodiin
        tool = getattr(attacker, "current_weapon", None)
        self.chop(attacker, tool, manager)
        return 0

    def chop(self, attacker, tool, manager):
        if self.is_empty: return

        # 1. Työkalutarkistus
        tool_type = getattr(tool, "tool_type", "none")
        # Fallback weapon groupille
        if tool_type == "none":
             grp = getattr(tool, "weapon_group", "")
             if "axe" in grp: tool_type = "axe"

        if tool_type != "axe":
            if manager:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, "Need Axe!", color=(200, 50, 50))
                sound_system.play_sound("error")
            return

        # 2. Osuma
        self.current_hits -= 1
        sound_system.play_sound("axe_1")

        if manager:
            manager.vfx.create_impact_sparks(self.rect.centerx, self.rect.centery, color=(150, 100, 50), count=3)
            manager.vfx.create_falling_leaves(self.rect.centerx, self.rect.centery)

        # 3. Resurssi per isku (Chance)
        if random.random() < 0.4: # 40% chance per hit
            if manager:
                manager.add_material(self.loot_item, 1)
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, f"+1 {self.loot_item}", color=(150, 255, 100))

        # 4. Kaatuu
        if self.current_hits <= 0:
            self._fell(manager)

    def _fell(self, manager):
        self.is_empty = True
        # Kanto-grafiikka
        if self.image:
            w, h = self.image.get_size()
            stump_h = 40
            if h > stump_h:
                stump = self.image.subsurface((0, h - stump_h, w, stump_h)).copy()
                self.image = stump
                self.image_pos = (self.image_pos[0], self.image_pos[1] + h - stump_h)
        if manager:
            manager.add_material(self.loot_item, 2) # Bonus lopussa
            manager.vfx.show_damage(self.rect.centerx, self.rect.top - 60, "Timber!", color=(255, 200, 100))
            sound_system.play_sound("mining_break")

    # --- Yhtenäinen keräyskanava ---
    def on_channel_swing(self, player, manager):
        sound_system.play_sound_at("axe_1", self.rect.centerx,
                                   self.rect.centery, manager)
        if manager:
            manager.vfx.create_impact_sparks(self.rect.centerx,
                                             self.rect.centery,
                                             color=(150, 100, 50), count=2)

    def harvest(self, manager=None, harvester=None):
        """Yksi hakkuusykli: +2 puuta; puu kaatuu kun syklit loppuvat."""
        if self.is_empty or manager is None:
            return
        manager.add_material(self.loot_item, 2)
        manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40,
                                f"+2 {self.loot_item}", color=(150, 255, 100))
        manager.vfx.create_falling_leaves(self.rect.centerx,
                                          self.rect.centery)
        self.resource_count -= 1
        if self.resource_count <= 0:
            self._fell(manager)
            self.image = self.sprites.get("empty", self.image)
        else:
            self._restart_pending = True

    def update(self, obstacles=None, manager=None):
        if self.is_empty: return
        self.update_channel(manager)
        if self._restart_pending and not self.channel_active and \
                not self.is_empty and manager is not None:
            self._restart_pending = False
            player = getattr(manager, "player_character", None)
            if player is not None:
                self.try_begin_channel(player, manager)
