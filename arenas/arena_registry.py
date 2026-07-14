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

try:
    from arenas.tier_3.ember_quarry import EmberQuarry
except ImportError:
    print("Notice: EmberQuarry not found, using BasicArena.")
    EmberQuarry = BasicArena


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


# Areenapoolit: vähintään 3 areenaa joka tasolla.
# Tier 0 (engine 1): puhtaita suoja-areenoita ilman erikoismekaniikkoja.
# Tier 2+: mukana kevyet, telegraafatut ympäristövaarat.
TIER_POOLS = {
    1: [BasicArena, RotatingColosseum, OasisRuins],
    2: [BasicArena, StormArena, ScrapringArena],
    3: [StormArena, SpikeArena, EmberQuarry],
}


def get_random_arena(tier):
    """Palauttaa areenan tason (Tier) perusteella"""
    if tier <= 1:
        pool = TIER_POOLS[1]
    elif tier == 2:
        pool = TIER_POOLS[2]
    else:
        pool = TIER_POOLS[3]
    return random.choice(pool)()
