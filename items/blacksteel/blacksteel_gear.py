# items/blacksteel/blacksteel_gear.py
"""
Blacksteel-sarja (lore: Uncommon, Tier 2 / The Iron Circle). Perii weak/iron
-aseiden kayttaytymisen (piirto, lataus, swing) ja nostaa vain statsit.
Auto-loytyy item_registryn walk_packages-skannauksella.
"""
from items.swords.weak_sword import WeakSword
from items.axes.weak_axe import WeakAxe
from items.maces.weak_mace import WeakMace
from items.spears.weak_spear import WeakSpear
from items.daggers.weak_dagger import WeakDagger
from items.bows.weak_bow import WeakBow
from items.crossbows.weak_crossbow import WeakCrossbow
from items.staves.weak_staff import WeakStaff
from items.shields.weak_shield import WeakShield


def _upgrade(item, name, dmg_mult=1.75, dmg_add=2, cost_mult=2.4, level=5):
    item.name = name
    item.rarity = "Uncommon"
    item.level_required = level
    item.cost = int(getattr(item, "cost", 50) * cost_mult)
    if hasattr(item, "damage"):
        item.damage = int(getattr(item, "damage", 8) * dmg_mult) + dmg_add
    if getattr(item, "description", None):
        item.description = f"Blacksteel-grade. {item.description}"


class BlacksteelSword(WeakSword):
    def __init__(self):
        super().__init__()
        _upgrade(self, "Blacksteel Sword")
        self.scaling = {"STR": 0.7, "DEX": 0.4}


class BlacksteelAxe(WeakAxe):
    def __init__(self):
        super().__init__()
        _upgrade(self, "Blacksteel Axe")


class BlacksteelMaul(WeakMace):
    def __init__(self):
        super().__init__()
        _upgrade(self, "Blacksteel Maul", dmg_mult=1.8)


class BlacksteelPike(WeakSpear):
    def __init__(self):
        super().__init__()
        _upgrade(self, "Blacksteel Pike")


class BlacksteelDirk(WeakDagger):
    def __init__(self):
        super().__init__()
        _upgrade(self, "Blacksteel Dirk", dmg_mult=1.6)
        self.scaling = {"DEX": 0.8, "STR": 0.2}


class YewLongbow(WeakBow):
    def __init__(self):
        super().__init__()
        _upgrade(self, "Yew Longbow")


class SteelCrossbow(WeakCrossbow):
    def __init__(self):
        super().__init__()
        _upgrade(self, "Steel Crossbow", dmg_mult=1.8)


class RunedStaff(WeakStaff):
    def __init__(self):
        super().__init__()
        _upgrade(self, "Runed Staff")


class BlacksteelShield(WeakShield):
    def __init__(self):
        super().__init__()
        self.name = "Blacksteel Shield"
        self.rarity = "Uncommon"
        self.level_required = 5
        self.cost = int(getattr(self, "cost", 25) * 2.4)
        if hasattr(self, "defense"):
            self.defense = int(getattr(self, "defense", 2)) + 3
