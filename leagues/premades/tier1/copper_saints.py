# Tier 1 - The Scrapring Circuit
"""The Copper Saints - hyväntekevaisyys-maineella ratsastavat, myyvat tietoa
sivussa. Raskas kilpimuuri, korkea puolustus (A). Hitaita mutta sitkeita."""
from leagues.league_data import build_team


def create_team(tier):
    return build_team(
        "The Copper Saints", (180, 140, 70), tier,
        "Armored Wall",
        "They ride on a charity reputation and sell what they overhear. Slow, "
        "heavily armored, and almost impossible to put down.",
        [
            {"name": "Brother Cael", "race": "Human", "weapon": "sword",
             "shield": True, "armor": "heavy", "elite": True, "lvl": 1,
             "def": 1, "skills": ["str_tank"]},
            {"name": "Sister Vane", "race": "Human", "weapon": "mace",
             "shield": True, "armor": "heavy"},
            {"name": "Halden", "race": "Human", "weapon": "sword",
             "shield": True, "armor": "heavy"},
            {"name": "Prior Otho", "race": "Human", "weapon": "sword", "shield": True},
            {"name": "Almsman Ree", "race": "Human", "weapon": "crossbow", "dex": 2},
        ],
        motto="Mercy, for a price.")
