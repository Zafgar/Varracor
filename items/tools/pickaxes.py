# items/tools/pickaxes.py
"""Hakut tier 2-5. Korkeampi tier = parempi malmimahdollisuus per isku
(IronOre: 5 % + 5 %/tier) ja vaatii opitun Path of the Vein -tason
(mining_level_required, valvotaan IronOre.take_hitissä).

Tier 1 -perushakku on items/tools/weak_pickaxe.py (WeakPickaxe).
Työkalutahti: uusi väline ~4 tason välein (1/5/9/14/19) - jokainen
areenatier tuo uuden perustyökalun.
"""

from items.tools.weak_pickaxe import WeakPickaxe


class BogironPickaxe(WeakPickaxe):
    """Tier 2: suoraudasta taottu."""

    def __init__(self):
        super().__init__()
        self.name = "Bogiron Pickaxe"
        self.rarity = "Uncommon"
        self.cost = 45
        self.description = "Bog iron head - bites deeper than scrap."
        self.tool_tier = 2
        self.mining_level_required = 5
        self.damage = 6


class SteelheadPickaxe(WeakPickaxe):
    """Tier 3: teräskärki."""

    def __init__(self):
        super().__init__()
        self.name = "Steelhead Pickaxe"
        self.rarity = "Rare"
        self.cost = 120
        self.description = "Tempered steel. The vein gives up its secrets."
        self.tool_tier = 3
        self.mining_level_required = 9
        self.damage = 7


class DuskforgedPickaxe(WeakPickaxe):
    """Tier 4: hämärätaottu."""

    def __init__(self):
        super().__init__()
        self.name = "Duskforged Pickaxe"
        self.rarity = "Epic"
        self.cost = 300
        self.description = "Forged at dusk, quenched in marsh water."
        self.tool_tier = 4
        self.mining_level_required = 14
        self.damage = 8


class VortexbitePickaxe(WeakPickaxe):
    """Tier 5: Vortex-purenta, loppupelin hakku."""

    def __init__(self):
        super().__init__()
        self.name = "Vortexbite Pickaxe"
        self.rarity = "Legendary"
        self.cost = 900
        self.description = "Stone remembers the Vortex. This makes it forget."
        self.tool_tier = 5
        self.mining_level_required = 19
        self.damage = 10
