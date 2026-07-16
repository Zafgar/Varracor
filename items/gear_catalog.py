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

    # ===== ARMOR REWORK (pelitesti 26): vartalot =====
    "juggernaut": [
        "Scrapbolt Harness", "Quarry Plate", "Gatewarden's Bulk",
        "Siegebreaker Plate", "Molewatcher's Fortress", "Rampart Colossus",
        "The Unmoved Mountain", "Heart of the Bastion"],
    "ranger": [
        "Marsh-stalker Wraps", "Fowler's Jerkin", "Causeway Runner's Kit",
        "Mirewood Trailguard", "Hawkeye Halfcoat", "Fenshadow Weave",
        "Skyline Strider Garb", "Mantle of the Last Track"],
    "battlemage": [
        "Conscript's Runevest", "Sparkbound Brigandine", "Hexguard Lamellar",
        "Warcaster's Panoply", "Stormscript Cuirass", "Runeblood Warplate",
        "Archmagus Vanguard", "Panoply of the Ninth Seal"],
    "bloodweave": [
        "Stained Shroud", "Mourner's Wrap", "Red-thread Vestment",
        "Gravecloth Regalia", "Sanguine Cerements", "Robe of Quiet Veins",
        "Shroud of the Pale Court", "Vestment of the Long Hunger"],
    "verdant": [
        "Mosscloak", "Bogbark Wrap", "Thornwoven Coat",
        "Wildgrove Mantle", "Heartwood Carapace", "Mistletoe Regalia",
        "Cloak of the Green Sleep", "Second Skin of the Forest"],
    "zealot": [
        "Lay Brother's Mail", "Votive Hauberk", "Litany-scored Mail",
        "Consecrated Warcoat", "Radiant Vigil Plate", "Mail of the Unbroken Hymn",
        "Aurora Sanctified Plate", "Raiment of the First Dawn"],

    # ===== Kypärät (head) =====
    "greathelm": [
        "Dented Pot Helm", "Militia Greathelm", "Pitchampion's Visage",
        "Bastion Greathelm", "Wyrmjaw Helm", "Colossus Crown-helm",
        "Sunforged Warcrown", "Helm of the Worldwall"],
    "warhelm": [
        "Cracked Halfhelm", "Watchman's Sallet", "Duelist's Crest",
        "Fieldmarshal's Helm", "Windcutter Sallet", "Viperfang Helm",
        "Ghostface Warhelm", "Crest of the Eclipse"],
    "hood": [
        "Sackcloth Hood", "Poacher's Cowl", "Cutpurse Shadowcap",
        "Nightwalk Cowl", "Whisperweave Hood", "Cowl of Missing Faces",
        "Ghoststep Veil", "Hood of the Unseen Hand"],
    "circlet": [
        "Copper Band", "Scribe's Fillet", "Runeworn Circlet",
        "Collegium Diadem", "Third-Eye Circlet", "Archon's Halo-band",
        "Crown of Waking Dreams", "Circlet of the First Thought"],
    "veilmask": [
        "Linen Halfmask", "Mummer's Visor", "Hexblade's Veil",
        "Bladedancer's Mask", "Mask of Quiet Steps", "Veil of Twin Moons",
        "Faceless Regalia", "Mask of the Last Secret"],

    # ===== Kilvet (off-hand) =====
    "buckler": [
        "Pot-lid Buckler", "Skirmisher's Disc", "Duelist's Roundel",
        "Wasp-steel Buckler", "Mirrorguard Disc", "Serpent-coil Buckler",
        "Ghostmetal Roundel", "Eye of the Storm"],
    "aegis": [
        "Plank Kite Shield", "Militia Aegis", "Pitfighter's Ward",
        "Bastion Kite", "Wyrmscale Aegis", "Colossus Ward",
        "Sunforged Aegis", "Aegis of the Worldwall"],
    "bulwark_shield": [
        "Door-plank Pavise", "Quarry Tower Shield", "Gatewarden's Pavise",
        "Siegewall Bulwark", "Molewatcher's Gate", "Rampart Pavise",
        "The Standing Wall", "Gate of the Bastion"],
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
    # Armor rework (pelitesti 26)
    "juggernaut": "You do not dodge in this. You do not need to.",
    "ranger": "Light enough to run the causeways, tough enough to "
              "shrug the reeds.",
    "battlemage": "Steel that carries a spell the way a scabbard "
                  "carries a blade.",
    "bloodweave": "The thread was white once. It fed well.",
    "verdant": "It grows back faster than they can cut it away.",
    "zealot": "Every ring of this mail has heard a hymn.",
    "greathelm": "The world through a slit: small, loud, survivable.",
    "warhelm": "Keeps your skull whole and your eyes on the field.",
    "hood": "Faces are for people who want to be remembered.",
    "circlet": "Thought moves easier when the temples are cool.",
    "veilmask": "Half the face, twice the doubt in their guard.",
    "buckler": "Catch the blade, not the blow. Then answer.",
    "aegis": "A soldier's honest wall - carried, not built.",
    "bulwark_shield": "When it is planted, the argument is over.",
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
    """Ei-koulusidonnaiset taistelijavarusteet (vartalot, kypärät,
    kilvet) - myydään sepältä/panssarikauppiaalta."""
    from items.tiered_gear import LINES
    return [TieredGear(g) for g in CATALOG
            if LINES[g["line"]].get("school") is None
            and LINES[g["line"]]["kind"] in ("armor", "shield")]


def make_gear_by_name(name):
    """Luo varusteen gear_id:llä TAI näyttönimellä (save/load käyttää)."""
    spec = _BY_ID.get(name)
    if spec is None:
        for g in CATALOG:
            if g["name"] == name:
                spec = g
                break
    return TieredGear(spec) if spec else None
