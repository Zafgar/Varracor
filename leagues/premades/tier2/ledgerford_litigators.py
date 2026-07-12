# Tier 2 - The Iron Circle
"""Ledgerford Litigators - voittaa saantokikkailulla. Kurinalainen
puolustusmuuri (kilvet + keihaat). A-taso, korkea puolustus."""
from leagues.league_data import build_team


def create_team(tier):
    return build_team(
        "Ledgerford Litigators", (120, 130, 150), tier,
        "Legalist Wall",
        "They win on technicalities as often as on the sand. Frustrating, "
        "immovable, and always one clause ahead of you.",
        [
            {"name": "Advocate Renn", "race": "Human", "weapon": "sword",
             "shield": True, "armor": "heavy", "lvl": 1, "def": 1},
            {"name": "Clerk Dovey", "race": "Human", "weapon": "sword",
             "shield": True, "armor": "heavy"},
            {"name": "Bailiff Kord", "race": "Human", "weapon": "sword",
             "shield": True, "armor": "heavy"},
            {"name": "Subpoena", "race": "Human", "weapon": "spear",
             "shield": True, "def": 1},
            {"name": "Writ Hollis", "race": "Human", "weapon": "spear", "shield": True},
        ],
        motto="Objection sustained.")
