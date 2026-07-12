# Tier 1 - The Scrapring Circuit
"""Rivet Row Renegades - teollisuusalueen kovikset improvisoiduilla varusteilla
(scrap-aseet vaikka Tier 1). Aggressiivisia mutta alivarustettuja (C - Tier 1:n
heikoin, mutta arvaamattomia)."""
from leagues.league_data import build_team

_NAMES = ["Sprocket", "Dregs", "Molla", "Rust", "Kip"]


def create_team(tier):
    roster = []
    for i, n in enumerate(_NAMES):
        roster.append({
            "name": n,
            "race": "Human" if i % 2 == 0 else "Goblin",
            "weapon": ["axe", "dagger", "mace", "dagger", "axe"][i],
            "scrap": True,          # improvisoitu, alivarustettu
            "dex": 2,
        })
    return build_team(
        "Rivet Row Renegades", (110, 100, 90), tier,
        "Improvised Aggro",
        "Foundry toughs who arm themselves from the scrap heap - accused of the "
        "metal theft that supplies them. Under-geared, but they fight mean.",
        roster, motto="We take what we need.")
