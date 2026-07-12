# Tier 2 - The Iron Circle
"""Giltgate Goldclaws - tehokas show-tiimi (rahanpesuepailyt). Nayttava
sekakokoonpano Tortle-ankkurilla. A-taso."""
from leagues.league_data import build_team


def create_team(tier):
    return build_team(
        "Giltgate Goldclaws", (200, 170, 60), tier,
        "Showpiece Mixed",
        "Giltgate's glittering crowd-pleasers - and, the ledgers whisper, a very "
        "convenient way to wash coin. Flashy, funded, and hard to read.",
        [
            {"name": "Aurel Vance", "race": "Human", "weapon": "sword",
             "shield": True, "armor": "heavy", "elite": True, "lvl": 1, "str": 2},
            {"name": "Dax Coyle", "race": "Human", "weapon": "axe", "str": 2},
            {"name": "Bulwark Odo", "race": "Tortle", "weapon": "mace",
             "shield": True, "armor": "heavy"},
            {"name": "Sable Finn", "race": "Elf", "weapon": "bow", "dex": 3},
            {"name": "Gil", "race": "Human", "weapon": "crossbow", "dex": 2},
        ],
        motto="All that glitters is ours.")
