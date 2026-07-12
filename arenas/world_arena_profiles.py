"""Regional arena identities layered over the existing arena classes.

The current renderer has a small set of reusable arena implementations. These
profiles preserve each city's lore, level band and planned signature hazards so
bespoke arena maps can be implemented incrementally without changing league
progression or save data.
"""

from __future__ import annotations

from lore.world_map_data import LOCATIONS, get_circuit_for_location


ARENA_PROFILES = {
    "shanty_yard": {
        "biome": "mud shanty",
        "hazards": ("scrap barricades", "mud slow zones", "unstable fencing"),
        "combat_focus": "basic positioning and survival",
    },
    "saffron_oasis": {
        "biome": "desert oasis",
        "hazards": ("heat pressure", "dry sand slow zones", "water-control circles"),
        "combat_focus": "stamina conservation",
    },
    "vinehollow": {
        "biome": "jungle margin",
        "hazards": ("slippery moss", "poison drums", "concealing vines"),
        "combat_focus": "terrain awareness and antidote planning",
    },
    "rattlebridge": {
        "biome": "bridge scrapyard",
        "hazards": ("moving scrap gates", "narrow bridge lanes", "fall zones"),
        "combat_focus": "lane control and sponsor-ready spectacle",
    },
    "rivet_row": {
        "biome": "industrial cage",
        "hazards": ("bolt pistons", "steam vents", "closing cage walls"),
        "combat_focus": "close-quarters pressure",
    },
    "timbercross": {
        "biome": "forest palisade",
        "hazards": ("falling timber", "stake lanes", "Warden boundary circles"),
        "combat_focus": "protecting space without damaging sacred ground",
    },
    "giltgate": {
        "biome": "gold market amphitheatre",
        "hazards": ("betting modifiers", "contract objectives", "rotating merchant cover"),
        "combat_focus": "objective play and calculated risk",
    },
    "ledgerford": {
        "biome": "court arena",
        "hazards": ("rule clauses", "penalty zones", "timed legal objectives"),
        "combat_focus": "precision under changing rules",
    },
    "coinharbor": {
        "biome": "tidal harbor pit",
        "hazards": ("rising water", "dock cranes", "Water-risen intrusions"),
        "combat_focus": "wave control and wet terrain",
    },
    "kestrel_way": {
        "biome": "caravan ring",
        "hazards": ("moving wagons", "cargo cover", "sand gusts"),
        "combat_focus": "adapting to changing lanes",
    },
    "spirewatch": {
        "biome": "elegant peak arena",
        "hazards": ("duel circles", "precision pylons", "line-of-sight crystals"),
        "combat_focus": "elite positioning and controlled magic",
    },
    "windstep": {
        "biome": "suspension arena",
        "hazards": ("wind knockback", "skychain bridges", "open edges"),
        "combat_focus": "knockback control",
    },
    "gleamhold": {
        "biome": "crystal crucible",
        "hazards": ("spell reflections", "resonance bursts", "crystal cover"),
        "combat_focus": "spell timing and area restraint",
    },
    "moonwatch": {
        "biome": "moonlit forest ring",
        "hazards": ("shifting moonlight", "living roots", "Taint cleanse zones"),
        "combat_focus": "mobility and corruption management",
    },
    "kharak_tor": {
        "biome": "stone grand ring",
        "hazards": ("honor lanes", "siege obstacles", "endurance phases"),
        "combat_focus": "military formation and endurance",
    },
    "crownhold": {
        "biome": "royal lion court",
        "hazards": ("royal decrees", "Sun-Gold ward lines", "propaganda objectives"),
        "combat_focus": "discipline under political spectacle",
    },
    "bonewind_necropolis": {
        "biome": "ossuary circle",
        "hazards": ("bone walls", "soul winds", "controlled undead waves"),
        "combat_focus": "death magic and attrition",
    },
    "highstone_sanctum": {
        "biome": "mythic mountain colosseum",
        "hazards": ("Charter trials", "Vortex simulations", "Titan judgment phases"),
        "combat_focus": "complete team mastery before Vortex descent",
    },
}


def get_arena_profile(location_id: str) -> dict | None:
    location_id = str(location_id)
    location = LOCATIONS.get(location_id)
    profile = ARENA_PROFILES.get(location_id)
    if not location or not profile or location.get("arena_tier") is None:
        return None
    result = dict(profile)
    result.update({
        "location_id": location_id,
        "location_name": location["name"],
        "arena_name": location["arena_name"],
        "arena_tier": int(location["arena_tier"]),
        "level_range": tuple(location["level_range"]),
        "region": location["region"],
        "circuit": get_circuit_for_location(location_id),
    })
    return result


def apply_arena_profile(arena, location_id: str):
    """Annotate an existing arena instance with regional identity data."""
    profile = get_arena_profile(location_id)
    if arena is None or profile is None:
        return arena
    arena.world_location_id = location_id
    arena.world_arena_profile = profile
    arena.display_name = profile["arena_name"]
    arena.region_name = profile["location_name"]
    arena.recommended_level_range = profile["level_range"]
    arena.signature_hazards = profile["hazards"]
    arena.combat_focus = profile["combat_focus"]
    return arena
