# Tier 1 - The Scrapring Circuit
"""Rattlebridge Runners - Sera Quenchin suosikki: kurinalainen, siisti,
vahadramainen kilpilinja. Managerina Corwin Hale. Riveissa kaapio Olek
Ironside ja Pure Magic -noviisi Miri Vale. A-taso, helppo markkinoida."""
from leagues.league_data import build_team


def create_team(tier):
    t = build_team(
        "Rattlebridge Runners", (90, 110, 165), tier,
        "Disciplined Line",
        "Sera Quench's poster team: clean, drilled, no theatrics. Bookies love a "
        "safe bet and the crowd loves a winner.",
        [
            {"name": "Jax Merrin", "race": "Human", "weapon": "sword",
             "shield": True, "armor": "heavy", "elite": True, "lvl": 1, "str": 2,
             "skills": ["str_tank"]},
            {"name": "Sila Vorn", "race": "Human", "weapon": "sword", "shield": True},
            {"name": "Brenna Kest", "race": "Human", "weapon": "spear", "def": 1},
            {"name": "Olek Ironside", "race": "Dwarf", "weapon": "crossbow", "dex": 2},
            {"name": "Miri Vale", "race": "Human", "weapon": "staff",
             "armor": "cloth", "int": 4, "lvl": 1, "skills": ["int_mana"],
             "spells": ["Spark Bolt"]},
        ],
        motto="Clean wins, clean coin.")
    t.manager = "Corwin Hale"
    return t
