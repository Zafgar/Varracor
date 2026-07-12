# Tier 2 - The Iron Circle
"""The Gilded Fangs - ihmissusilauma. Nopea frenzy-lahitaistelu (dagger/axe),
kova DPS mutta ohuempi panssari (B/A). Uusi rotu esille."""
from leagues.league_data import build_team


def create_team(tier):
    return build_team(
        "The Gilded Fangs", (90, 70, 90), tier,
        "Lycan Pack",
        "A pit-pack of lycans who fight as one and feed as one. When the frenzy "
        "takes them, mercy leaves the sand.",
        [
            {"name": "Alpha Skoll", "race": "Werewolf", "weapon": "axe",
             "lvl": 1, "str": 2, "skills": ["str_execute"]},
            {"name": "Greymane", "race": "Werewolf", "weapon": "dagger", "dex": 3},
            {"name": "Redclaw", "race": "Werewolf", "weapon": "dagger", "dex": 3},
            {"name": "Ashfur", "race": "Werewolf", "weapon": "axe"},
            {"name": "Handler Vex", "race": "Human", "weapon": "crossbow", "dex": 2},
        ],
        motto="The pack eats first.")
