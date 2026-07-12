# Tier 1 - The Scrapring Circuit
"""Rattlebridge Runners - Sera Quenchin suosikki: kurinalainen, siisti,
vahadramainen kilpilinja. A-taso, helppo markkinoida."""
from leagues.league_data import build_team


def create_team(tier):
    return build_team(
        "Rattlebridge Runners", (90, 110, 165), tier,
        "Disciplined Line",
        "Sera Quench's poster team: clean, drilled, no theatrics. Bookies love a "
        "safe bet and the crowd loves a winner.",
        [
            {"name": "Captain Maro", "race": "Human", "weapon": "sword",
             "shield": True, "armor": "heavy", "elite": True, "lvl": 1, "str": 2,
             "skills": ["str_tank"]},
            {"name": "Sela Quick", "race": "Human", "weapon": "sword", "shield": True},
            {"name": "Boden", "race": "Human", "weapon": "sword", "shield": True},
            {"name": "Pike Harrow", "race": "Human", "weapon": "spear", "def": 1},
            {"name": "Wisp", "race": "Human", "weapon": "crossbow", "dex": 2},
        ],
        motto="Clean wins, clean coin.")
