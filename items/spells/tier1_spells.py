# items/spells/tier1_spells.py
"""
Ensimmaiset loitsut (Tier 1 spell tier). Magia alkaa nakya Tier 2 -areenalla.
Firebolt = hyokkaava projektiili, Minor Heal = kaverin parannus. Auto-loytyy
item_registryn walk_packages-skannauksella.
"""
from items.base_item import Spell


class Firebolt(Spell):
    def __init__(self):
        super().__init__()
        self.name = "Firebolt"
        self.tier = 1
        self.rarity = "Common"
        self.cost = 80
        self.description = "A dart of fire. Cheap, quick, reliable."
        self.slot_type = "spell1"
        self.mana_cost = 10
        self.cooldown_max = 90
        self.range = 320
        self.damage = 16
        self.scaling = {"INT": 1.0}
        self.is_skillshot = True
        self.projectile_speed = 11
        self.projectile_color = (255, 140, 40)
        self.projectile_size = 11


class MinorHeal(Spell):
    def __init__(self):
        super().__init__()
        self.name = "Minor Heal"
        self.tier = 1
        self.rarity = "Common"
        self.cost = 90
        self.description = "Knits a wounded ally's flesh back together."
        self.slot_type = "spell1"
        self.mana_cost = 14
        self.cooldown_max = 150
        self.range = 260
        self.heal_amount = 30
        self.scaling = {"INT": 0.8}
        self.is_skillshot = False
        self.projectile_color = (120, 255, 120)

    def cast(self, caster, target, manager, target_pos=None):
        """Parantaa kohteen (kaveri) - ei projektiili."""
        if target is None:
            target = caster
        amt = int(self.heal_amount + caster.intelligence * self.scaling.get("INT", 0))
        if hasattr(target, "heal"):
            target.heal(amt, manager)
        else:
            target.current_hp = min(target.max_hp, target.current_hp + amt)
        if manager:
            manager.vfx.show_damage(target.rect.centerx, target.rect.top - 20,
                                    f"+{amt}", color=(120, 255, 120))
        return True
