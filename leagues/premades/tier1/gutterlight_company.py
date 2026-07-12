# Tier 1 - The Scrapring Circuit
"""Gutterlight Company - likaiset tyot, Hamon luottotiimi. Tikarit + varsijouset,
nopeat iskut (B). Hauras mutta vaarallinen jos paastetaan lahelle."""
from leagues.league_data import build_team


def create_team(tier):
    return build_team(
        "Gutterlight Company", (80, 80, 110), tier,
        "Shadow Skirmish",
        "Finders of lost things and doers of dirty work - Hamo's trusted crew. "
        "They ask no questions and leave no marks... on themselves.",
        [
            {"name": "Quill", "race": "Human", "weapon": "dagger", "dex": 4,
             "lvl": 1, "skills": ["dex_dodge"]},
            {"name": "Nix", "race": "Goblin", "weapon": "dagger", "dex": 4,
             "skills": ["dex_dodge"]},
            {"name": "Sable", "race": "Human", "weapon": "dagger", "dex": 3},
            {"name": "Ledger", "race": "Human", "weapon": "crossbow", "dex": 2},
            {"name": "Moth", "race": "Goblin", "weapon": "crossbow", "dex": 2},
        ],
        motto="Found. For a fee.")
