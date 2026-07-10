import pygame
import os
import math
import random
from assets.tiles.prop import Prop
from sound_manager import sound_system

class SwampTree(Prop):
    def __init__(self, x, y):
        # Iso puu (140x220)
        super().__init__(x, y, 140, 220, color=(40, 50, 30))
        
        self.loot_item = "Swamp Wood"
        self.resource_count = 3
        self.interact_timer = 0
        self.interact_max = 60 # 1 sekunti
        self.is_empty = False
        self.error_cooldown = 0
        self.max_hits = 5
        self.current_hits = self.max_hits
        self.interaction_range = 100
        self.interaction_label = "Chop"
        
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

    def update(self, obstacles=None, manager=None):
        if self.is_empty: return
        
        if self.error_cooldown > 0:
            self.error_cooldown -= 1

        if manager and manager.player_character:
            player = manager.player_character
            dist = math.hypot(player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery)
            
            keys = pygame.key.get_pressed()
            if dist < self.interaction_range and keys[pygame.K_e]:
                # Tarkistetaan työkalu
                wep = player.equipment.get("main_hand")
                t_type = getattr(wep, "tool_type", "")
                t_tier = getattr(wep, "tool_tier", 0)
                
                if t_type == "axe" and t_tier >= 1:
                    self.interact_timer += 1
                    
                    # Ääni ja efekti kesken hakkuun
                    if self.interact_timer % 30 == 0:
                        sound_system.play_sound("axe_1")
                        if hasattr(manager, "vfx"):
                             manager.vfx.create_impact_sparks(self.rect.centerx, self.rect.centery, color=(150, 100, 50), count=2)

                    if self.interact_timer >= self.interact_max:
                        self.interact_timer = 0
                        self.resource_count -= 1
                        
                        manager.add_material(self.loot_item, 2)
                        manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, f"+2 {self.loot_item}", color=(150, 255, 100))
                        if hasattr(manager, "vfx"):
                            manager.vfx.create_falling_leaves(self.rect.centerx, self.rect.centery)

                        if self.resource_count <= 0:
                            self.is_empty = True
                            self.image = self.sprites.get("empty", self.image)
                else:
                    # Väärä työkalu
                    if self.error_cooldown <= 0:
                        if hasattr(manager, "vfx"):
                             manager.vfx.show_damage(self.rect.centerx, self.rect.top - 60, "Requires Axe!", color=(255, 50, 50))
                        self.error_cooldown = 45 # Estä spämmi (0.75s)
                    self.interact_timer = 0
            else:
                self.interact_timer = 0

    def draw_on_screen(self, screen, offset):
        super().draw_on_screen(screen, offset)
        if not self.is_empty and self.interact_timer > 0:
            self.draw_interaction_bar(screen, offset, self.interact_timer / self.interact_max)
