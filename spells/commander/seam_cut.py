import pygame
import math
import random
from items.base_item import Spell
from sound_manager import sound_system
from vfx import Projectile

# --- CUSTOM VFX CLASS (Embedded) ---
class SlashWave(Projectile):
    """
    A massive, piercing wave of void energy.
    Defined here to keep the spell self-contained.
    """
    def __init__(self, x, y, target_pos, damage, owner, manager, max_range=600):
        speed = 22
        duration = int(max_range / speed) # Laske kesto kantaman perusteella
        
        # Create the visual surface
        size = 140
        img = pygame.Surface((size, size), pygame.SRCALPHA)
        
        super().__init__(x, y, target_pos, speed, damage, owner, manager, image=img, duration=duration)
        
        self.hit_list = [] # For piercing logic
        self.base_image = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # --- DRAW THE SLASH (Crescent Shape) ---
        # Draw facing RIGHT (0 degrees) so rotation works correctly
        rect = pygame.Rect(0, 0, size, size)
        
        # 1. Dark Void Trail (Back)
        pygame.draw.arc(self.base_image, (20, 0, 40), rect.inflate(-20, -20), -1.0, 1.0, 20)
        # 2. Teal Energy (Body)
        pygame.draw.arc(self.base_image, (50, 255, 200), rect.inflate(-40, -40), -0.9, 0.9, 12)
        # 3. White Core (Sharp Edge)
        pygame.draw.arc(self.base_image, (255, 255, 255), rect.inflate(-60, -60), -0.8, 0.8, 4)
        
        # Rotate to face target
        self.image = pygame.transform.rotate(self.base_image, self.angle)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, obstacles=None):
        # Move manually to handle piercing (super().update kills on hit)
        self.pos_x += self.vx
        self.pos_y += self.vy
        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)
        
        self.timer += 1
        if self.timer >= self.duration:
            self.kill()
            return

        # Trail particles
        if self.timer % 2 == 0:
             self.manager.vfx.create_impact_sparks(self.rect.centerx, self.rect.centery, color=(50, 255, 200), count=2)

        # Collision (Piercing)
        for unit in self.manager.all_units:
            if unit == self.owner or getattr(unit, "team_color", None) == getattr(self.owner, "team_color", None): continue
            if getattr(unit, "is_dead", False): continue
            
            if self.rect.colliderect(getattr(unit, "hurt_rect", unit.rect)):
                if unit not in self.hit_list:
                    self.hit_list.append(unit)
                    
                    # Damage & Effects
                    unit.take_damage(self.damage, "Magic", self.owner, self.manager)
                    sound_system.play_sound("vortex_wave_impact")
                    
                    # Visuals
                    self.manager.vfx.create_impact_sparks(unit.rect.centerx, unit.rect.centery, color=(100, 255, 255), count=10)
                    self.manager.trigger_hit_stop(4) # Game Feel
                    self.manager.trigger_screen_shake(2)

    def on_wall_hit(self):
        pass # Pierce walls (Reality cut)

class SeamCut(Spell):
    def __init__(self):
        super().__init__()
        self.name = "Vortex Slash" # Nimi vastaamaan visuaalia
        self.tier = 1
        self.rarity = "Legendary"
        self.cost = 0
        self.description = "Launch a wave of void energy that pierces enemies."
        
        self.mana_cost = 10
        self.stamina_cost = 10
        self.cooldown_max = 45 # 0.75 sekunti (todella nopea)
        self.range = 550 # Rajattu kantama (pelaaja näkee mihin se loppuu)
        self.damage = 15
        self.scaling = {"INT": 0.8, "DEX": 0.4} # Tarkkuus ja taika
        
        self.is_skillshot = True # Nyt tähdättävä!
        
        self.icon_color = (50, 255, 200) # Abyssal Teal

    def draw_card_icon(self, surface, x, y, size):
        pad = size * 0.2
        rect = pygame.Rect(x + pad, y + pad, size - pad*2, size - pad*2)
        cx, cy = rect.center
        
        # Pystysuora viilto
        pygame.draw.line(surface, self.icon_color, (cx, rect.top), (cx, rect.bottom), 4)
        # Hehku
        pygame.draw.line(surface, (255, 255, 255), (cx, rect.top + 5), (cx, rect.bottom - 5), 2)
        # Poikkiviivat (tikit)
        pygame.draw.line(surface, self.icon_color, (cx - 5, cy - 10), (cx + 5, cy - 10), 2)
        pygame.draw.line(surface, self.icon_color, (cx - 5, cy + 10), (cx + 5, cy + 10), 2)

    def cast(self, caster, target, manager, target_pos=None):
        # Skillshot tarvitsee suunnan (target_pos)
        dest = target_pos
        if not dest and target:
            dest = target.rect.center
        
        if not dest: return False
            
        # 1. Tarkista resurssit
        if caster.current_mana < self.mana_cost or caster.current_stamina < self.stamina_cost:
            return False

        # 2. EXECUTE
        dmg = self.calculate_damage({"int": caster.intelligence, "dex": caster.dexterity})
        
        # Luo ammus (Custom SlashWave defined above)
        manager.vfx.add_projectile(SlashWave(caster.rect.centerx, caster.rect.centery, dest, dmg, caster, manager, max_range=self.range))
        
        # Lisäefektit: Tärinä ja ääni
        manager.trigger_screen_shake(4)

        sound_system.play_sound("cmd_vortex_slash")
        
        # Resurssit vähennetään Commander-luokassa (koska emme vähennä niitä tässä manuaalisesti)
        # Mutta koska tämä on hybrid, vähennetään stamina tässä
        caster.current_stamina -= self.stamina_cost
        
        return True
        
    def calculate_damage(self, stats):
        base = self.damage
        bonus = (stats.get("int", 0) * self.scaling["INT"]) + (stats.get("dex", 0) * self.scaling["DEX"])
        return int(base + bonus)