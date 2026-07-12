# Tier 1 - The Scrapring Circuit
"""Timbercross Wardens - metsanreunan rajapartio. Haltiajouset + ihmisrunko
kilvella. Kaukovoima suojatun etulinjan takaa (A/B)."""
from leagues.league_data import build_team


def create_team(tier):
    return build_team(
        "Timbercross Wardens", (60, 120, 75), tier,
        "Guarded Ranged",
        "Border wardens who fight like a patrol: a shielded line up front, arrows "
        "from the treeline. Patient, precise, hard to rush.",
        [
            {"name": "Warden Aelis", "race": "Elf", "weapon": "bow", "dex": 4,
             "lvl": 1, "skills": ["dex_crit"]},
            {"name": "Corin", "race": "Elf", "weapon": "bow", "dex": 3,
             "skills": ["dex_crit"]},
            {"name": "Thistle", "race": "Elf", "weapon": "bow", "dex": 3},
            {"name": "Hollin Oak", "race": "Human", "weapon": "spear",
             "shield": True, "armor": "heavy", "def": 1},
            {"name": "Bram Reed", "race": "Human", "weapon": "sword", "shield": True},
        ],
        motto="The woods have eyes and arrows.")
