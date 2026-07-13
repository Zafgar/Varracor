# items/tools/fishing_rods.py
"""Vavat tier 2-5. Korkeampi tier avaa uudet kalat (systems/fishing.py
FISH_SPECIES) ja vaatii opitun kalastustason (fishing_level_required). Tier 1 -perusvapa on items/tools/fishing_rod.py (FishingRod).

Tier 2 myydään Kradilla; tier 3-5 on tarkoitus sijoittaa ylempien
tierien kaupunkeihin/palkinnoiksi - ne ovat rekisterissä valmiina.
"""

from items.tools.fishing_rod import FishingRod


class BogwoodRod(FishingRod):
    """Tier 2: Bronze-luokan suovapa."""

    def __init__(self):
        super().__init__()
        self.name = "Bogwood Rod"
        self.rarity = "Uncommon"
        self.cost = 45
        self.description = "Cured bogwood with a braided gut line."
        self.tool_tier = 2
        self.fishing_level_required = 5


class IronwireRod(FishingRod):
    """Tier 3: rautalankasiima, kestää haukia."""

    def __init__(self):
        super().__init__()
        self.name = "Ironwire Rod"
        self.rarity = "Rare"
        self.cost = 120
        self.description = "Iron wire leader - pike teeth mean nothing."
        self.tool_tier = 3
        self.fishing_level_required = 9


class DuskwillowRod(FishingRod):
    """Tier 4: joustava hämäräpaju, syville vesille."""

    def __init__(self):
        super().__init__()
        self.name = "Duskwillow Rod"
        self.rarity = "Epic"
        self.cost = 300
        self.description = "Bends double without breaking. The deep ones pull hard."
        self.tool_tier = 4
        self.fishing_level_required = 14


class VortexlineRod(FishingRod):
    """Tier 5: Vortex-säikeinen siima, loppupelin vapa."""

    def __init__(self):
        super().__init__()
        self.name = "Vortexline Rod"
        self.rarity = "Legendary"
        self.cost = 900
        self.description = "The line hums near the Vortex. So do the fish."
        self.tool_tier = 5
        self.fishing_level_required = 19
