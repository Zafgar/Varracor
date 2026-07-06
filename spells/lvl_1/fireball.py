import pygame
import random
import math
from items.base_item import Spell
from sound_manager import sound_system
from vfx import MagicProjectile

class Fireball(Spell):
    def __init__(self):
        super().__init__()
        self.name = "Fireball"
        self.description = "Explosive fire damage."
        self.mana_cost = 25
        self.cooldown_max = 180  # 3 sekuntia (60 fps)
        self.range = 300
        self.cost = 200
        self.damage = 20
        self.tier = 1
        self.scaling = {"INT": 1.2}

        # Projectile settings
        self.is_skillshot = True
        self.projectile_speed = 12
        self.projectile_color = (255, 100, 50) # Oranssi
        self.projectile_size = 12

    def draw_card_icon(self, surface, x, y, size):
        # Piirrä ikoni (Tulipallo)
        pad = size * 0.2
        rect = pygame.Rect(x + pad, y + pad, size - pad*2, size - pad*2)
        
        cx, cy = rect.center
        pygame.draw.circle(surface, (200, 50, 0), (cx, cy), size * 0.3)
        pygame.draw.circle(surface, (255, 150, 0), (cx, cy), size * 0.2)
        pygame.draw.circle(surface, (255, 255, 100), (cx, cy), size * 0.1)

    def cast(self, caster, target, manager, target_pos=None):
        if not target_pos and target:
            target_pos = target.rect.center
            
        if target_pos:
            dmg = self.damage + (caster.intelligence * self.scaling.get("INT", 0))
            # Luodaan räjähtävä ammus
            proj = ExplosiveFireball(caster.rect.centerx, caster.rect.centery, target_pos, self.projectile_speed, int(dmg), caster, manager)
            manager.vfx.add_projectile(proj)
            return True
        return False

class ExplosiveFireball(MagicProjectile):
    def __init__(self, x, y, target_pos, speed, damage, owner, manager):
        super().__init__(x, y, target_pos, speed, damage, owner, manager, color=(255, 100, 0), size=14)
        
    def update(self, obstacles=None):
        super().update(obstacles)
        # Lisää vana (Trail)
        if random.random() < 0.6:
            self.manager.vfx.create_impact_sparks(self.rect.centerx, self.rect.centery, color=(255, 150, 50), count=1)

    def on_hit(self, target):
        self.explode()
        
    def on_wall_hit(self):
        self.explode()

    def explode(self):
        self.manager.vfx.create_fireburst(self.rect.centerx, self.rect.centery)
        # AoE Damage
        for u in self.manager.all_units:
            if u.is_dead: continue
            # Tarkista etäisyys räjähdykseen
            d = math.hypot(u.rect.centerx - self.rect.centerx, u.rect.centery - self.rect.centery)
            if d < 80: # Räjähdyssäde
                u.take_damage(self.damage, "Fire", self.owner, self.manager)
                if hasattr(u, "apply_status"):
                    u.apply_status("Burn", 180, 2)
        self.kill()
