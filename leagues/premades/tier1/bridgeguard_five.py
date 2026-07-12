# Tier 1 - The Scrapring Circuit
"""Bridgeguard Five - 'pidetaan linja' -puolustustaktiikka. Elakoitynyt
kapteeni Halden Pike johtaa; kentalla orkki Bruk, kaapio Sel Copper ja
taikanoviisi Enna Reed. Kilpimuuri + keihasselusta (A). Tier 1:n paras
puolustus, johon sillanvartijat luottavat."""
from leagues.league_data import build_team


def create_team(tier):
    t = build_team(
        "Bridgeguard Five", (100, 120, 140), tier,
        "Shield Wall",
        "Old bridge-tollers who never yield a step. Break yourself on their line "
        "and the spears behind it will finish the job.",
        [
            {"name": "Yara Pike", "race": "Human", "weapon": "sword",
             "shield": True, "armor": "heavy", "elite": True, "lvl": 1,
             "def": 1, "str": 2, "skills": ["str_tank"]},
            {"name": "Toma Crest", "race": "Human", "weapon": "sword",
             "shield": True, "armor": "heavy", "def": 1},
            {"name": "Bruk", "race": "Orc", "weapon": "mace",
             "armor": "heavy", "str": 2},
            {"name": "Sel Copper", "race": "Dwarf", "weapon": "spear",
             "shield": True, "def": 1},
            {"name": "Enna Reed", "race": "Human", "weapon": "staff",
             "armor": "cloth", "int": 4, "lvl": 1, "skills": ["int_mana"],
             "spells": ["Spark Bolt"]},
        ],
        motto="Hold the bridge.")
    t.manager = "Halden Pike"
    return t
