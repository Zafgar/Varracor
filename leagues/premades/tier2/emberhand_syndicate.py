# Tier 2 - The Iron Circle
"""Emberhand Syndicate - 'arcane muscle': sauva-kayttaja + lahitaistelurunko.
Sauva on toistaiseksi kauko-ase; oikeat loitsut lisataan Tier 2 -spell-passissa.
B/A-taso."""
from leagues.league_data import build_team


def create_team(tier):
    return build_team(
        "Emberhand Syndicate", (170, 90, 60), tier,
        "Arcane Muscle",
        "Hired spell-hands backed by hired blades. Rumor says the Emberhands dabble "
        "in things the Collegium would frown upon.",
        [
            {"name": "Adept Lysa", "race": "Elf", "weapon": "staff",
             "armor": "cloth", "int": 5, "lvl": 1, "skills": ["int_mana"],
             "spells": ["Firebolt", "Minor Heal"]},
            {"name": "Bost", "race": "Human", "weapon": "sword", "shield": True,
             "armor": "heavy"},
            {"name": "Karth", "race": "Human", "weapon": "sword", "shield": True},
            {"name": "Grim", "race": "Orc", "weapon": "axe", "str": 2},
            {"name": "Vell", "race": "Human", "weapon": "crossbow", "dex": 2},
        ],
        motto="Coin buys fire.")
