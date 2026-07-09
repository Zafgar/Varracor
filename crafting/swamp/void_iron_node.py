import pygame
import os
import math
import random
from assets.tiles.prop import Prop
from sound_manager import sound_system

class VoidIronNode(Prop):
    def __init__(self, x, y):
        super().__init__(x, y, 80, 80, color=(20, 20, 30))
        
        self.loot_item = "Void-Iron"
        self.resource_count = random.randint(1, 2) # Harvinainen, 1-2 kpl
        self.interact_timer = 0
        self.interact_max = 90 # 1.5 sekuntia (hitaampi)
        self.vfx_timer = 0
        self.is_empty = False
        self.error_cooldown = 0
        self.interaction_range = 80
        self.interaction_label = "Mine"
        
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

    def update(self, obstacles=None, manager=None):
        if self.is_empty: return
        
        if self.error_cooldown > 0:
            self.error_cooldown -= 1

        # Idle VFX (Void Glow)
        self.vfx_timer += 1
        if self.vfx_timer > 20:
            self.vfx_timer = 0
            if manager and hasattr(manager, "vfx"):
                manager.vfx.create_void_particles(self.rect.centerx, self.rect.centery)

        # Interaction
        if manager and manager.player_character:
            player = manager.player_character
            dist = math.hypot(player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery)
            
            keys = pygame.key.get_pressed()
            if dist < self.interaction_range and keys[pygame.K_e]:
                # Tarkistetaan työkalu (Vaatii Tier 3 Pickaxe)
                wep = player.equipment.get("main_hand")
                t_type = getattr(wep, "tool_type", "")
                t_tier = getattr(wep, "tool_tier", 0)
                
                if t_type == "pickaxe" and t_tier >= 3:
                    self.interact_timer += 1
                    
                    if self.interact_timer >= self.interact_max:
                        self.interact_timer = 0
                        self.resource_count -= 1
                        
                        manager.add_material(self.loot_item, 1)
                        manager.vfx.show_damage(self.rect.centerx, self.rect.top - 20, f"+1 {self.loot_item}", color=(200, 100, 255))
                        sound_system.play_sound("mining_success")
                        
                        # VFX: Void purkaus
                        if hasattr(manager, "vfx"):
                            for _ in range(5):
                                manager.vfx.create_void_particles(self.rect.centerx, self.rect.centery)
                        
                        if self.resource_count <= 0:
                            self.is_empty = True
                            self.image = self.sprites.get("empty", self.image)
                            sound_system.play_sound("mining_break")
                else:
                    # Väärä työkalu tai liian pieni tier
                    if self.error_cooldown <= 0:
                        msg = "Requires Pickaxe (Tier 3)!" if t_type == "pickaxe" else "Requires Pickaxe!"
                        if hasattr(manager, "vfx"):
                             manager.vfx.show_damage(self.rect.centerx, self.rect.top - 60, msg, color=(255, 50, 50))
                        self.error_cooldown = 45 # Estä spämmi
                    self.interact_timer = 0
            else:
                self.interact_timer = 0

    def draw_on_screen(self, screen, offset):
        super().draw_on_screen(screen, offset)
        if not self.is_empty and self.interact_timer > 0:
            self.draw_interaction_bar(screen, offset, self.interact_timer / self.interact_max)
