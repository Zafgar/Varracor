import pygame
import math
from items.base_item import Spell
from vfx import MagicProjectile

class LightningBolt(Spell):
    def __init__(self):
        super().__init__()
        self.name = "Lightning Bolt"
        self.tier = 1
        self.rarity = "Common"
        self.cost = 110
        self.description = "A fast bolt of electricity."
        
        self.mana_cost = 18
        self.cooldown_max = 100
        self.range = 400
        self.damage = 10
        self.scaling = {"INT": 1.1}
        
        # Projectile settings
        self.is_skillshot = True
        self.projectile_speed = 20 # Nopea
        self.projectile_color = (100, 200, 255) # Syaani
        self.projectile_size = 8

    def draw_card_icon(self, surface, x, y, size):
        # Salama-ikoni
        pad = size * 0.2
        rect = pygame.Rect(x + pad, y + pad, size - pad*2, size - pad*2)
        
        points = [
            (rect.centerx + 5, rect.top), (rect.left, rect.centery), (rect.centerx - 2, rect.centery),
            (rect.centerx - 5, rect.bottom), (rect.right, rect.centery), (rect.centerx + 2, rect.centery)
        ]
        pygame.draw.polygon(surface, (100, 200, 255), points)

    def cast(self, caster, target, manager, target_pos=None):
        if not target_pos and target:
            target_pos = target.rect.center
            
        if target_pos:
            dmg = self.damage + (caster.intelligence * self.scaling.get("INT", 0))
            proj = ChainLightningProjectile(caster.rect.centerx, caster.rect.centery, target_pos, self.projectile_speed, int(dmg), caster, manager)
            manager.vfx.add_projectile(proj)
            return True
        return False

class ChainLightningProjectile(MagicProjectile):
    def __init__(self, x, y, target_pos, speed, damage, owner, manager, bounces=3, hit_list=None):
        super().__init__(x, y, target_pos, speed, damage, owner, manager, color=(100, 200, 255), size=8)
        self.bounces = bounces
        self.hit_list = hit_list if hit_list is not None else []

    def on_hit(self, target):
        target.take_damage(self.damage, "Magic", self.owner, self.manager)
        self.hit_list.append(target)
        self.manager.vfx.create_impact_sparks(self.rect.centerx, self.rect.centery, color=self.color, count=5)
        
        if self.bounces > 0:
            best_t = None
            best_d = 250 # Bounce range
            
            for u in self.manager.all_units:
                if u.is_dead or u == self.owner or u.team_color == self.owner.team_color or u in self.hit_list:
                    continue
                d = math.hypot(u.rect.centerx - self.rect.centerx, u.rect.centery - self.rect.centery)
                if d < best_d:
                    best_d = d
                    best_t = u
            
            if best_t:
                # Visual arc to next target
                self.manager.vfx.create_lightning(self.rect.center, best_t.rect.center)
                
                # Spawn new projectile for the bounce
                new_dmg = int(self.damage * 0.8)
                new_proj = ChainLightningProjectile(self.rect.centerx, self.rect.centery, best_t.rect.center, self.speed, new_dmg, self.owner, self.manager, self.bounces - 1, self.hit_list)
                self.manager.vfx.add_projectile(new_proj)
        
        self.kill()
        
    def on_wall_hit(self):
        self.manager.vfx.create_impact_sparks(self.rect.centerx, self.rect.centery, color=self.color, count=3)
        self.kill()