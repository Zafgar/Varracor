import pygame
import math
from items.base_item import Spell
from sound_manager import sound_system
from vfx import MagicProjectile


class Smite(Spell):
    """Radiant Synodin ensimmäinen loitsu: pyhän valon isku joka polttaa
    epäpyhää. Tekee kohtuullista vahinkoa - ja TUPLASTI epäkuolleisiin
    (luurangot, zombit). 'Kivi' hahmolle jolla on Holy-suunta auki.

    Kouluportti (tuleva): school='holy'."""

    def __init__(self):
        super().__init__()
        self.name = "Smite"
        self.tier = 1
        self.rarity = "Rare"
        self.cost = 300
        self.school = "holy"
        self.description = ("A lance of holy light. Double damage against "
                            "the undead.")
        self.mana_cost = 20
        self.cooldown_max = 120   # 2 s
        self.range = 380
        self.damage = 16
        self.scaling = {"INT": 0.9}
        self.is_skillshot = True
        self.projectile_speed = 16
        self.projectile_color = (255, 240, 170)
        self.projectile_size = 10
        self.icon_color = (255, 240, 170)

    def cast(self, caster, target, manager, target_pos=None):
        if caster.current_mana < self.mana_cost:
            return False
        if not target_pos and target:
            target_pos = target.rect.center
        if not target_pos:
            return False
        caster.current_mana -= self.mana_cost
        dmg = int(self.damage + caster.intelligence * self.scaling.get("INT", 0))
        proj = SmiteBolt(caster.rect.centerx, caster.rect.centery, target_pos,
                         self.projectile_speed, dmg, caster, manager)
        manager.vfx.add_projectile(proj)
        try:
            sound_system.play_sound("holy_cast")
        except Exception:
            pass
        return True

    def draw_card_icon(self, surface, x, y, size):
        rect = pygame.Rect(x, y, size, size)
        pygame.draw.rect(surface, (40, 36, 16), rect, border_radius=8)
        pygame.draw.rect(surface, (255, 240, 170), rect, 2, border_radius=8)
        cx, cy = x + size // 2, y + size // 2
        # säteilevä risti
        pygame.draw.line(surface, (255, 255, 220), (cx, y + 6), (cx, y + size - 6), 4)
        pygame.draw.line(surface, (255, 255, 220),
                         (x + 8, cy - 4), (x + size - 8, cy - 4), 4)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy - 4), 3)


def _is_undead(unit):
    if getattr(unit, "is_undead", False):
        return True
    return getattr(unit, "unit_type", "") == "Undead" or \
        type(unit).__name__.startswith("Undead")


class SmiteBolt(MagicProjectile):
    def __init__(self, x, y, target_pos, speed, damage, owner, manager):
        super().__init__(x, y, target_pos, speed, damage, owner, manager,
                         color=(255, 240, 170), size=10)

    def on_hit(self, target):
        dmg = self.damage
        if _is_undead(target):
            dmg *= 2  # pyhä valo palaa epäkuolleissa kaksinkerroin
        target.take_damage(dmg, "Holy", self.owner, self.manager)
        self.manager.vfx.create_impact_sparks(self.rect.centerx,
                                               self.rect.centery,
                                               color=(255, 250, 210), count=8)
        self.kill()

    def on_wall_hit(self):
        self.manager.vfx.create_impact_sparks(self.rect.centerx,
                                               self.rect.centery,
                                               color=(255, 250, 210), count=4)
        self.kill()
