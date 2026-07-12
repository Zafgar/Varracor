# Tier 1 - The Scrapring Circuit
"""Bridgeguard Five - 'pidetaan linja' -puolustustaktiikka. Kilpimuuri +
keihasselusta, korkea puolustus (A). Tier 1:n paras puolustusjoukkue."""
from leagues.league_data import build_team


def create_team(tier):
    return build_team(
        "Bridgeguard Five", (100, 120, 140), tier,
        "Shield Wall",
        "Old bridge-tollers who never yield a step. Break yourself on their line "
        "and the spears behind it will finish the job.",
        [
            {"name": "Sergeant Ord", "race": "Human", "weapon": "sword",
             "shield": True, "armor": "heavy", "elite": True, "lvl": 1,
             "def": 1, "str": 2, "skills": ["str_tank"]},
            {"name": "Halt", "race": "Human", "weapon": "sword", "shield": True,
             "armor": "heavy", "def": 1},
            {"name": "Ferro", "race": "Human", "weapon": "sword", "shield": True,
             "armor": "heavy"},
            {"name": "Longshanks", "race": "Human", "weapon": "spear",
             "shield": True, "def": 1},
            {"name": "Reeve", "race": "Human", "weapon": "spear", "shield": True},
        ],
        motto="Hold the bridge.")
