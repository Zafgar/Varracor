# items/tools/lumber_axes.py
"""Puunkaatokirveet tier 2-5. Korkeampi tier = parempi puumahdollisuus
per isku (MuckfordTree.chop: +5 %/tier) ja vaatii opitun Path of the
Timber -tason (forestry_level_required, valvotaan chopissa).

Tier 1 -peruskirves on items/tools/weak_lumberaxe.py (WeakLumberAxe).
Työkalutahti: 1/5/9/14/19 kuten hakut ja vavat.
"""

from items.tools.weak_lumberaxe import WeakLumberAxe


class BogironLumberAxe(WeakLumberAxe):
    """Tier 2."""

    def __init__(self):
        super().__init__()
        self.name = "Bogiron Lumber Axe"
        self.rarity = "Uncommon"
        self.cost = 45
        self.description = "Bog iron edge holds through a day of felling."
        self.tool_tier = 2
        self.forestry_level_required = 5
        self.damage = 7


class SteelheadLumberAxe(WeakLumberAxe):
    """Tier 3."""

    def __init__(self):
        super().__init__()
        self.name = "Steelhead Lumber Axe"
        self.rarity = "Rare"
        self.cost = 120
        self.description = "Sings through heartwood."
        self.tool_tier = 3
        self.forestry_level_required = 9
        self.damage = 8


class DuskforgedLumberAxe(WeakLumberAxe):
    """Tier 4."""

    def __init__(self):
        super().__init__()
        self.name = "Duskforged Lumber Axe"
        self.rarity = "Epic"
        self.cost = 300
        self.description = "Old growth falls like reeds."
        self.tool_tier = 4
        self.forestry_level_required = 14
        self.damage = 9


class VortexfellLumberAxe(WeakLumberAxe):
    """Tier 5."""

    def __init__(self):
        super().__init__()
        self.name = "Vortexfell Lumber Axe"
        self.rarity = "Legendary"
        self.cost = 900
        self.description = "The forest bows before the swing lands."
        self.tool_tier = 5
        self.forestry_level_required = 19
        self.damage = 11
