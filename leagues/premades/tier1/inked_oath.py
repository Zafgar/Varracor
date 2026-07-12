# Tier 1 - The Scrapring Circuit
"""The Inked Oath - sopimusnojainen: tekee tismalleen mita paperissa lukee.
Metodinen sekakokoonpano (keihas + miekka + varsijousi). Tasapainoinen B/A."""
from leagues.league_data import build_team


def create_team(tier):
    return build_team(
        "The Inked Oath", (120, 90, 140), tier,
        "Methodical",
        "Contract-bound mercenaries who do exactly what the paper says - no more, "
        "no less. Predictable, and lethally consistent.",
        [
            {"name": "Notary Sarn", "race": "Human", "weapon": "sword",
             "shield": True, "armor": "heavy", "lvl": 1, "def": 1},
            {"name": "Clause", "race": "Human", "weapon": "spear", "def": 1},
            {"name": "Seal", "race": "Human", "weapon": "spear"},
            {"name": "Writ", "race": "Human", "weapon": "crossbow", "dex": 2},
            {"name": "Codex", "race": "Elf", "weapon": "crossbow", "dex": 2},
        ],
        motto="As written.")
