# Tier 2 - The Iron Circle
"""Coinharbor Corsairs - satamien meribossit. Aggressiivinen ryostoretki
Werewolf-karjella. A/B-taso, kova hyokkays."""
from leagues.league_data import build_team


def create_team(tier):
    return build_team(
        "Coinharbor Corsairs", (60, 110, 130), tier,
        "Sea Reavers",
        "Harbor bosses who fight like a boarding party - fast, loud, and happy to "
        "cheat. Their lycan enforcer settles arguments quickly.",
        [
            {"name": "Captain Mora", "race": "Werewolf", "weapon": "axe",
             "lvl": 1, "str": 2, "skills": ["str_execute"]},
            {"name": "Brine", "race": "Human", "weapon": "axe", "str": 2},
            {"name": "Gaff", "race": "Human", "weapon": "axe"},
            {"name": "Skipper Tull", "race": "Human", "weapon": "crossbow", "dex": 2},
            {"name": "Netty", "race": "Human", "weapon": "crossbow", "dex": 2},
        ],
        motto="Pay the toll or walk the plank.")
