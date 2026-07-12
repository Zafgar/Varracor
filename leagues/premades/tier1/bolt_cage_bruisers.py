# Tier 1 - The Scrapring Circuit
"""Bolt Cage Bruisers - hakkimatsien raaka voima. Orkkeja, nuijia, jattimainen
HP - mutta ei kaukoasetta eika kilpia. Tier 1:n raain nyrkki (A+)."""
from leagues.league_data import build_team

_NAMES = ["Krunt", "Vasha", "Gorm", "Big Edda", "Thokk"]


def create_team(tier):
    roster = []
    for i, n in enumerate(_NAMES):
        roster.append({
            "name": n, "race": "Orc",
            "weapon": "mace" if i % 2 == 0 else "axe",
            "armor": "light", "str": 4, "hp": 35, "skills": ["str_tank"],
        })
    return build_team(
        "Bolt Cage Bruisers", (170, 80, 70), tier,
        "Brutal Cage",
        "Cage-match maulers who fight through broken bones. They hit like a "
        "collapsing scaffold - just don't let them corner you.",
        roster, motto="Break 'em in the cage.")
