import random
from arenas.base_arena import BaseArena

# --- IMPORTS ---
# Käytämme try-except rakennetta, jotta peli ei kaadu
# jos et ole vielä luonut kaikkia areena-tiedostoja.

try:
    from arenas.tier_1.basic_arena import BasicArena
except ImportError:
    print("Notice: BasicArena file missing, using placeholder.")
    class BasicArena(BaseArena):
        def __init__(self):
            super().__init__("Basic Arena")

# ---- UUSI: Tier 1 extra areenat ----
try:
    from arenas.tier_1.rotating_colosseum import RotatingColosseum
except ImportError:
    print("Notice: RotatingColosseum not found, using BasicArena.")
    RotatingColosseum = BasicArena

try:
    from arenas.tier_1.oasis_ruins import OasisRuins
except ImportError:
    print("Notice: OasisRuins not found, using BasicArena.")
    OasisRuins = BasicArena

try:
    from arenas.tier_1.scrapring_arena import ScrapringArena
except ImportError:
    print("Notice: ScrapringArena not found, using BasicArena.")
    ScrapringArena = BasicArena

# ---- Tier 2+ ----
try:
    from arenas.tier_2.storm_arena import StormArena
except ImportError:
    print("Notice: StormArena not found, using BasicArena.")
    StormArena = BasicArena

try:
    from arenas.tier_3.spike_arena import SpikeArena
except ImportError:
    print("Notice: SpikeArena not found, using BasicArena.")
    SpikeArena = BasicArena


# Sijaintikohtaiset tunnusareenat (lore-signature). Näillä on oma
# mekaniikkansa, joka ajetaan sijainnin liigassa tierin sijaan.
LOCATION_ARENAS = {
    "rattlebridge": ScrapringArena,
}


def get_arena_for(tier, location_id=None):
    """Sijaintitietoinen valinta: jos sijainnilla on tunnusareena, käytä
    sitä; muuten kaadu takaisin tier-pohjaiseen satunnaisvalintaan."""
    if location_id:
        cls = LOCATION_ARENAS.get(str(location_id))
        if cls is not None:
            return cls()
    return get_random_arena(tier)


def get_random_arena(tier):
    """Palauttaa areenan tason (Tier) perusteella"""

    # Tier 1 (League 1-2)
    if tier <= 1:
        ArenaClass = random.choice([BasicArena, RotatingColosseum, OasisRuins])
        return ArenaClass()

    # Tier 2 (League 3-4)
    elif tier == 2:
        ArenaClass = random.choice([BasicArena, StormArena])
        return ArenaClass()

    # Tier 3+ (League 5+)
    else:
        ArenaClass = random.choice([StormArena, SpikeArena])
        return ArenaClass()
