# Tier 1 - The Scrapring Circuit
"""Cog Wardens - Scrapringin koneistoa huoltavat nikkarit, jotka tappelevat
niilla samoilla vempaimilla. Gnomi-nikkareita ja Ironspan Unionin kaapio;
varsijousia, tikareita ja kipinaansat (Spark Snare). Hauras mutta ilkea
kontrollitiimi: hidastaa ja polttaa ennen kuin ehdit lahelle (B).

Managerina Yorik Sparkspanner, vanha ratasmestari joka virittaa areenan
murskaavat rattaat ja hoyrytuprut - ja tietaa tarkalleen milloin ne
lauukeavat kesken matsin."""
from leagues.league_data import build_team


def create_team(tier):
    t = build_team(
        "Cog Wardens", (150, 130, 70), tier,
        "Gadget Control",
        "The tinkers who keep the Scrapring's gears turning - and turn them on "
        "you. Snares, sparks and steam soften a foe long before the bolt lands.",
        [
            {"name": "Pib Cogwhistle", "race": "Gnome", "weapon": "crossbow",
             "elite": True, "dex": 3, "lvl": 1, "skills": ["dex_dodge", "arena_instincts", "arena_instincts_2"]},
            {"name": "Wren Boltwright", "race": "Gnome", "weapon": "crossbow",
             "dex": 3, "skills": ["arena_instincts"]},
            {"name": "Fizz Sparkspanner", "race": "Gnome", "weapon": "dagger",
             "dex": 2, "skills": ["arena_instincts"]},
            {"name": "Durgan Coalvein", "race": "Dwarf", "weapon": "axe",
             "armor": "heavy", "shield": True, "def": 1, "str": 1},
            {"name": "Kesk Brasspin", "race": "Gnome", "weapon": "crossbow",
             "dex": 2, "skills": ["arena_instincts"]},
        ],
        motto="Mind the gears.")
    t.manager = "Yorik Sparkspanner"
    return t
