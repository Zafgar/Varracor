# bosses/boss_registry.py

print("Initializing Boss Registry...")

try:
    # Yritetään ladata Rat Kingin mission.py
    import bosses.rat_king.mission as rat_king_mission
    print("SUCCESS: Rat King mission module loaded.")
except ImportError as e:
    # Jos tämä tulostuu, vika on kansioissa tai __init__.py puuttuu!
    print(f"CRITICAL ERROR loading Rat King: {e}")
    rat_king_mission = None
except Exception as e:
    print(f"UNKNOWN ERROR loading Rat King: {e}")
    rat_king_mission = None

# Rekisteröidään moduuli ID:llä
MISSION_REGISTRY = {
    "boss_rat_king": rat_king_mission
}

def load_mission_package(mission_id):
    mod = MISSION_REGISTRY.get(mission_id)
    if mod is None:
        print(f"Registry Warning: No module found for key '{mission_id}'")
        print(f"Available keys: {list(MISSION_REGISTRY.keys())}")
    return mod