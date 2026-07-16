# items/weapon_catalog.py
"""Asekatalogi: 9 perhettä x 8 tieriä = 72 asetta L30 asti, kaikki
käsin nimetty world loren mukaan. Numerot tulevat tiered_weapons-
budjeteista; käytös (LMB-hold-erikoiset, äänet, hitboxit) periytyy
perheiden weak_-toteutuksista. Special-/boss-aseet tulevat myöhemmin
erikseen."""

from items.tiered_weapons import FAMILY_CLASS

NAMES = {
    "sword": [
        "Ditch-iron Blade", "Militia Arming Sword", "Pitfighter's Edge",
        "Bastion Longsword", "Wyrmfang Sabre", "Colossus Warblade",
        "Sunforged Reaver", "Edge of the Worldwall"],
    "dagger": [
        "Bent Shiv", "Wharf-rat Sticker", "Cutpurse Fang",
        "Nightwalk Kris", "Whisper of Steel", "Viper-king's Tooth",
        "Ghostmetal Talon", "The Last Secret"],
    "axe": [
        "Split-haft Hatchet", "Bogwood Cleaver", "Pitchampion's Axe",
        "Siegebreaker Cleaver", "Wyrmjaw Broadaxe", "Colossus Feller",
        "Sunforged Headsman", "Worldsplitter"],
    "mace": [
        "Knotted Cudgel", "Quarry Maul", "Gatewarden's Bell",
        "Bastion Warhammer", "Molewatcher's Fist", "Rampart Crusher",
        "Sunforged Judgement", "Hammer of the Bastion"],
    "spear": [
        "Fire-hard Stake", "Militia Pike", "Causeway Lance",
        "Mirewood Partisan", "Hawkeye Warspear", "Fenshadow Impaler",
        "Skyline Skewer", "Reach of the Last Track"],
    "bow": [
        "Warped Shortbow", "Fowler's Bow", "Poacher's Recurve",
        "Nightwalk Longbow", "Whisperwind Bow", "Viperstring Recurve",
        "Ghostwood Longbow", "Bow of the Unseen Hand"],
    "crossbow": [
        "Jammed Arbalest", "Watchman's Crossbow", "Duelist's Latch",
        "Fieldmarshal's Arbalest", "Windcutter Crossbow",
        "Viperfang Arbalest", "Ghostbolt Engine", "Eclipse Arbalest"],
    "staff": [
        "Crooked Walking Staff", "Scribe's Cane", "Runeworn Quarterstaff",
        "Collegium Warstaff", "Third-Eye Stave", "Archon's Rod",
        "Staff of Waking Dreams", "Rod of the First Thought"],
    "book": [
        "Water-stained Primer", "Scribe's Lexicon", "Runethread Grimoire",
        "Vortex-touched Folio", "Codex of the Third Eye",
        "Archon's Concordance", "Tome of Shattered Stars",
        "The First Word"],
}

FLAVOR = {
    "sword": "An honest length of steel. Everything else is footwork.",
    "dagger": "Short arguments end quickest from behind.",
    "axe": "It does not parry. It removes.",
    "mace": "Armor is a suggestion. This is the rebuttal.",
    "spear": "The first rule of the wall: they die at arm's length.",
    "bow": "Patience, breath, release. The rest is the arrow's problem.",
    "crossbow": "Crank it once, end an argument once.",
    "staff": "The Weave runs straighter down a well-worn shaft.",
    "book": "Some pages bite back when read aloud.",
}

CATALOG = []
for _family, _names in NAMES.items():
    for _i, _name in enumerate(_names):
        CATALOG.append({
            "id": f"w_{_family}_t{_i + 1}",
            "name": _name,
            "tier": _i + 1,
            "family": _family,
            "flavor": FLAVOR.get(_family, ""),
        })

_BY_ID = {w["id"]: w for w in CATALOG}


def all_weapons():
    return [FAMILY_CLASS[w["family"]](w) for w in CATALOG]


def make_weapon(weapon_id):
    spec = _BY_ID.get(weapon_id)
    return FAMILY_CLASS[spec["family"]](spec) if spec else None


def make_weapon_by_name(name):
    """Luo aseen id:llä TAI näyttönimellä (save/load + kaupat)."""
    spec = _BY_ID.get(name)
    if spec is None:
        for w in CATALOG:
            if w["name"] == name:
                spec = w
                break
    return FAMILY_CLASS[spec["family"]](spec) if spec else None


def weapons_for_family(family):
    return [FAMILY_CLASS[w["family"]](w) for w in CATALOG
            if w["family"] == family]
