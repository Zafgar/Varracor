# boss_registry.py

try:
    # Nyt Boss-logiikka asuu suoraan kartan mission-tiedostossa
    import maps.rat_sewer.mission as rat_king_module
except ImportError as e:
    print(f"ERROR: Ei voitu ladata Rat Kingiä: {e}")
    rat_king_module = None

MISSION_REGISTRY = {
    "boss_rat_king": rat_king_module
}

def load_mission_package(boss_id):
    """Hakee oikean mission-moduulin ID:n perusteella"""
    return MISSION_REGISTRY.get(boss_id)