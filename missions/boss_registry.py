# boss_registry.py

try:
    # Nyt Boss-logiikka asuu suoraan kartan mission-tiedostossa
    import maps.rat_sewer.mission as rat_king_module
except ImportError as e:
    print(f"ERROR: Ei voitu ladata Rat Kingiä: {e}")
    rat_king_module = None

try:
    import maps.bog_1.boss_troll as forest_troll_module
except ImportError as e:
    print(f"ERROR: Ei voitu ladata Forest Trollia: {e}")
    forest_troll_module = None

MISSION_REGISTRY = {
    "boss_rat_king": rat_king_module,
    "boss_forest_troll": forest_troll_module,
}

def load_mission_package(boss_id):
    """Hakee oikean mission-moduulin ID:n perusteella"""
    return MISSION_REGISTRY.get(boss_id)