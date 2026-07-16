# items/gear_catalog.py
"""Varustekatalogi: 9 linjaa x 8 tieriä, kaikki käsin nimetty (vaivaa!).
Numerot tulevat gear_scaling-budjeteista automaattisesti."""

from items.tiered_gear import TieredGear

# Nimet per linja, tierit 1-8 (matala -> legendaarinen)
NAMES = {
    "warrior": [
        "Dented Breastplate", "Militia Warplate", "Pitfighter's Cuirass",
        "Bastion Plate", "Wyrmscale Hauberk", "Colossus Warplate",
        "Sunforged Aegisplate", "Worldbreaker Plate"],
    "skirmisher": [
        "Patched Leathers", "Scout's Jerkin", "Duelist's Harness",
        "Shadowstitch Vest", "Windrunner Garb", "Viper-king Skins",
        "Ghostweave Harness", "Eclipse Shroudmail"],
    "arcanist": [
        "Apprentice Robe", "Scribe's Vestment", "Runethread Robe",
        "Vortex-touched Vestment", "Robe of the Third Eye",
        "Archon's Regalia", "Robe of Shattered Stars",
        "Vestment of the First Weave"],
    "pure_focus": [
        "Cracked Prism", "Glass Resonator", "Attuned Lens",
        "Collegium Prism", "Refractor of Voss", "Singing Crystal",
        "Prime Refractor", "Heart of the Prism"],
    "necro_summoner": [
        "Knuckle-bone Charm", "Gravewax Idol", "Sealed Urn",
        "Choir of Skulls", "Legion Phylactery", "Ossuary Crown-shard",
        "Voice of the Quiet", "Throne of the Restless"],
    "necro_leech": [
        "Tick-bone Fetish", "Red Thirst Vial", "Marrow Siphon",
        "Hungering Idol", "Vein-drinker Talisman", "Heartsblood Chalice",
        "The Pale Leech", "Maw of a Thousand Wounds"],
    "druid_life": [
        "Sprouted Acorn", "Dew-heart Charm", "Evergreen Talisman",
        "Blooming Heartwood", "Springtide Relic", "Worldroot Cutting",
        "Tear of the Green", "Seed of the First Forest"],
    "druid_wild": [
        "Claw-mark Totem", "Beast-tooth Fetish", "Alpha's Knuckle",
        "Dire Pelt Totem", "Stoneclaw Idol", "Heart of the Pack",
        "Old Growth Fang", "Wyrmblood Totem"],
    "holy_light": [
        "Tin Censer", "Wax-blessed Icon", "Pilgrim's Reliquary",
        "Dawnlight Censer", "Beacon of Aurelian", "Saint's Radiance",
        "Chalice of First Light", "Fragment of the True Sun"],
}

FLAVOR = {
    "warrior": "Hammered for the wall of shields. It asks only that you "
               "stand and hold.",
    "skirmisher": "Cut for those who answer steel with footwork and a "
                  "grin.",
    "arcanist": "The threads remember every spell cast through them.",
    "pure_focus": "Raw Weave bends cleaner through a well-cut prism.",
    "necro_summoner": "The dead listen better when you carry something "
                      "of theirs.",
    "necro_leech": "What you spill, it drinks - and pours back into you.",
    "druid_life": "Green life coiled tight, waiting for a wound to fill.",
    "druid_wild": "The beast within settles when it smells old blood.",
    "holy_light": "Light gathered patiently, ounce by blessed ounce.",
}

CATALOG = []
for _line, _names in NAMES.items():
    for _i, _name in enumerate(_names):
        CATALOG.append({
            "id": f"{_line}_t{_i + 1}",
            "name": _name,
            "tier": _i + 1,
            "line": _line,
            "flavor": FLAVOR.get(_line, ""),
        })

_BY_ID = {g["id"]: g for g in CATALOG}


def all_gear():
    return [TieredGear(g) for g in CATALOG]


def make_gear(gear_id):
    spec = _BY_ID.get(gear_id)
    return TieredGear(spec) if spec else None


def gear_for_school(school):
    """Koulun erikoistumisvarusteet kauppaan. Pure saa myös arcanist-kaavut
    (yleiset caster-vartalot myydään Prismistä)."""
    from items.tiered_gear import LINES
    out = []
    for g in CATALOG:
        line = LINES[g["line"]]
        if line.get("school") == school:
            out.append(TieredGear(g))
        elif school == "pure" and g["line"] == "arcanist":
            out.append(TieredGear(g))
    return out


def martial_gear():
    """Soturilinjat (warrior/skirmisher) - myydään sepältä myöhemmin."""
    return [TieredGear(g) for g in CATALOG
            if g["line"] in ("warrior", "skirmisher")]
