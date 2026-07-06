import pygame
import math
from items.base_item import Spell
from sound_manager import sound_system

class VortexWarp(Spell):
    def __init__(self):
        super().__init__()
        self.name = "Vortex Warp"
        self.tier = 1 # Commander Spells have their own progression, but tier 1 for base
        self.rarity = "Legendary" # Commander magic is unique
        self.cost = 0 # Not sold in shops
        self.description = "Stitch reality to warp to a new location."
        
        self.mana_cost = 15
        self.stamina_cost = 15 # Hybrid cost (physical/magical strain)
        self.cooldown_max = 120 # 2 seconds
        self.range = 250
        
        self.is_skillshot = True # Aimed
        
        # Commander Magic Theme Colors
        self.icon_color = (50, 255, 200) # Abyssal Teal

    def draw_card_icon(self, surface, x, y, size):
        # Abstrakti "solmu" tai "repeämä"
        pad = size * 0.2
        rect = pygame.Rect(x + pad, y + pad, size - pad*2, size - pad*2)
        cx, cy = rect.center
        
        # Ulkorengas (Vortex)
        pygame.draw.circle(surface, (20, 60, 50), (cx, cy), size * 0.35, 2)
        # Sisäosa (Warp)
        pygame.draw.line(surface, self.icon_color, (rect.left, rect.top), (rect.right, rect.bottom), 3)
        pygame.draw.line(surface, self.icon_color, (rect.right, rect.top), (rect.left, rect.bottom), 3)
        pygame.draw.circle(surface, (200, 255, 255), (cx, cy), size * 0.1)

    def cast(self, caster, target, manager, target_pos=None):
        if not target_pos: return False
        
        # 1. Tarkista resurssit (Mana + Stamina)
        if caster.current_mana < self.mana_cost or caster.current_stamina < self.stamina_cost:
            return False

        # 2. Tarkista etäisyys
        dx = target_pos[0] - caster.rect.centerx
        dy = target_pos[1] - caster.rect.centery
        dist = math.hypot(dx, dy)
        
        if dist > self.range:
            # Clamp to max range
            ratio = self.range / dist
            target_pos = (caster.rect.centerx + dx * ratio, caster.rect.centery + dy * ratio)

        # 3. Tarkista seinät (Ei voi warpata seinän sisään)
        # Luodaan dummy rect kohteeseen
        dest_rect = caster.rect.copy()
        dest_rect.center = target_pos
        
        if manager.current_arena:
            for obs in manager.current_arena.obstacles:
                if dest_rect.colliderect(getattr(obs, "rect", obs)):
                    # Estetty! (Voisimme tehdä "nearest valid" logiikan, mutta fail on selkeämpi)
                    return False

        # 4. EXECUTE WARP
        start_pos = caster.rect.center
        
        # VFX: Echo (Jätä kuva lähtöpaikkaan)
        manager.vfx.create_after_image(caster)
        # VFX: Seam (Lanka lähtö- ja loppupisteen välille)
        manager.vfx.create_warp_seam(start_pos, target_pos)
        
        # VFX: Imploosio lähdössä ja räjähdys saapumisessa
        manager.vfx.create_reverse_shockwave(start_pos[0], start_pos[1], color=(50, 255, 200), max_radius=50, duration=15)
        manager.vfx.create_shockwave(target_pos[0], target_pos[1], color=(50, 255, 200), max_radius=80, width=5)
        manager.trigger_screen_shake(6)
        
        # Siirrä hahmo
        caster.rect.center = target_pos
        
        # Resurssit
        caster.current_mana -= self.mana_cost
        caster.current_stamina -= self.stamina_cost
        
        # Ääni (Matala humahdus/repeämä)
        sound_system.play_sound("cmd_vortex_warp")
        
        return True