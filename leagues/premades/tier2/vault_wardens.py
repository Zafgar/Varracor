# Tier 2 - The Iron Circle
"""The Vault Wardens - eliittivartijat blacksteel-varustein. Tasapainoinen
kova runko (orkit + ihmiset). A-taso."""
from leagues.league_data import build_team


def create_team(tier):
    return build_team(
        "The Vault Wardens", (150, 120, 80), tier,
        "Elite Guard",
        "The guild vaults' own guard, loaned to the arena for a fee. Drilled, "
        "blacksteel-clad, and utterly without theatrics.",
        [
            {"name": "Warden-Captain Hruk", "race": "Orc", "weapon": "mace",
             "armor": "heavy", "elite": True, "lvl": 1, "str": 3},
            {"name": "Sten", "race": "Human", "weapon": "sword",
             "shield": True, "armor": "heavy"},
            {"name": "Odval", "race": "Human", "weapon": "sword",
             "shield": True, "armor": "heavy"},
            {"name": "Grosh", "race": "Orc", "weapon": "axe", "str": 2},
            {"name": "Perrin", "race": "Human", "weapon": "crossbow", "dex": 2},
        ],
        motto="Nothing gets past the Wardens.")
