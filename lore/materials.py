"""Canonical crafting and gathering materials for Varrakor.

This module is the single machine-readable source for world materials.  It is
safe to import from gameplay code, quests, shops and future station modules.
Human-readable lore lives in ``docs/MATERIALS.md``.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Dict, Iterable, Optional


RARITY_ORDER = ("Common", "Uncommon", "Rare", "Very Rare", "Mythic")
RARITY_COLORS = {
    "Common": (205, 205, 205),
    "Uncommon": (100, 205, 115),
    "Rare": (105, 145, 235),
    "Very Rare": (188, 105, 225),
    "Mythic": (240, 183, 65),
}


def _m(category, rarity, level_min, level_max, source, station, uses, lore,
       sell_price, aliases=(), special_grade=None):
    return {
        "category": category,
        "rarity": rarity,
        "level_min": int(level_min),
        "level_max": None if level_max is None else int(level_max),
        "source": source,
        "station": station,
        "uses": list(uses),
        "lore": lore,
        "sell_price": int(sell_price),
        "aliases": list(aliases),
        "special_grade": special_grade,
    }


MATERIALS = OrderedDict({
    # ------------------------------------------------------------------
    # Metals, ores and smithing
    # ------------------------------------------------------------------
    "Scrap Iron": _m(
        "Metals, Ores & Smithing", "Common", 1, 5,
        "Scrap piles, ruined wagons and battlefield salvage",
        "Smeltery / Blacksmith",
        ("Crude weapons", "Scrap Metal Bar", "early station construction"),
        "Muckford survives by reforging yesterday's wreckage into tomorrow's tools.",
        3,
    ),
    "Coal": _m(
        "Metals, Ores & Smithing", "Common", 1, None,
        "Mines, charcoal burners and industrial stores",
        "Smeltery",
        ("forge fuel", "iron smelting", "high-temperature processing"),
        "Every serious forge in Varrakor measures its future in sacks of coal.",
        3,
    ),
    "Iron Ore": _m(
        "Metals, Ores & Smithing", "Common", 4, 10,
        "Surface mines and low mountain veins",
        "Smeltery",
        ("Iron Ingot", "basic tools", "Iron-tier equipment"),
        "Reliable, ugly and everywhere civilization has managed to endure.",
        6,
    ),
    "Iron Ingot": _m(
        "Metals, Ores & Smithing", "Common", 6, 10,
        "Smelted from Iron Ore and Coal",
        "Blacksmith",
        ("Iron weapons", "armor", "tools", "station upgrades"),
        "The first material that marks a fighter as properly equipped rather than merely armed.",
        12, aliases=("Iron Bar",),
    ),
    "Blacksteel Ore": _m(
        "Metals, Ores & Smithing", "Uncommon", 10, 15,
        "Deep mines beneath Crown and Kharak territory",
        "Advanced Smeltery",
        ("Blacksteel Ingot", "Steel-tier equipment"),
        "Dark ore that refuses a weak flame and punishes careless miners with brittle fractures.",
        26,
    ),
    "Tempering Flux": _m(
        "Metals, Ores & Smithing", "Uncommon", 11, None,
        "Salt flats, alchemical suppliers and forge guilds",
        "Smeltery / Blacksmith",
        ("Blacksteel processing", "rare metal tempering", "quality upgrades"),
        "A guarded mixture of mineral salts that lets rare metals cool without tearing themselves apart.",
        22,
    ),
    "Blacksteel Ingot": _m(
        "Metals, Ores & Smithing", "Uncommon", 11, 15,
        "Smelted from Blacksteel Ore with Tempering Flux",
        "Blacksmith",
        ("Steel weapons", "heavy armor", "advanced tools"),
        "Blacksteel carries a dull sheen and a reputation for surviving battles its owners do not.",
        42,
    ),
    "Stormsilver Ore": _m(
        "Metals, Ores & Smithing", "Rare", 16, 20,
        "Storm-struck veins in the Aegis Peaks",
        "Master Smeltery",
        ("Stormsilver Ingot", "magical focuses", "elite armor"),
        "The ore hums before lightning and keeps a faint charge after the storm has passed.",
        75, aliases=("Stormsilver",),
    ),
    "Stormsilver Ingot": _m(
        "Metals, Ores & Smithing", "Rare", 16, 20,
        "Refined from Stormsilver Ore under controlled arcane grounding",
        "Master Blacksmith / Enchanter",
        ("elite armor", "spell foci", "rune-bearing weapons"),
        "Properly grounded Stormsilver conducts magic without surrendering its edge.",
        115, aliases=("Stormsilver Bar",),
    ),
    "Sun-Gold Ore": _m(
        "Metals, Ores & Smithing", "Very Rare", 21, 25,
        "Crown-controlled mines and sanctioned holy excavations",
        "Sanctified Smeltery",
        ("Sun-Gold Ingot", "holy regalia", "legendary equipment"),
        "The Crown calls every vein a divine inheritance and every unsanctioned miner a thief.",
        210, aliases=("Sun-Gold", "Sun-Gold Vein"),
    ),
    "Sun-Gold Ingot": _m(
        "Metals, Ores & Smithing", "Very Rare", 21, 25,
        "Refined from Sun-Gold Ore in a consecrated furnace",
        "Master Blacksmith / Holy Enchanter",
        ("holy weapons", "legendary armor", "sanctified trinkets"),
        "It holds light strangely, as if dawn remains trapped beneath the metal's skin.",
        325, aliases=("Sun-Gold Bar",),
    ),
    "Void-Iron": _m(
        "Metals, Ores & Smithing", "Very Rare", 26, 30,
        "Outer Shatterbelt and stabilized Vortex fractures",
        "Void Forge",
        ("Abyss-resistant equipment", "Vortex seals", "anti-corruption plating"),
        "Cold even in flame, Void-Iron rejects part of the Abyss that created it.",
        300, aliases=("Void Iron",),
    ),
    "Heartcore Adamant": _m(
        "Metals, Ores & Smithing", "Mythic", 30, None,
        "The Eye of the Abyssal Vortex",
        "Artifact Forge",
        ("artifact frames", "mythic armor", "world-class weapons"),
        "No known mundane tool can mark it; only Vortex forces can persuade it to change shape.",
        1600,
    ),

    # ------------------------------------------------------------------
    # Woods, fibers and bindings
    # ------------------------------------------------------------------
    "Plant Fiber": _m(
        "Woods, Fibers & Bindings", "Common", 1, None,
        "Farm waste, reeds, grasses and lowland plants",
        "Quartermaster Workbench",
        ("bowstrings", "cloth", "bandages", "bindings"),
        "Individually weak fibers become dependable when twisted, layered and kept dry.",
        2,
    ),
    "Rough Timber": _m(
        "Woods, Fibers & Bindings", "Common", 1, 5,
        "Muckford forest edge, salvage timber and common logging",
        "Carpenter / Quartermaster Workbench",
        ("Crude handles", "shield frames", "station construction"),
        "Warped, wet and full of knots, but Muckford builds half its life from it.",
        4, aliases=("Swamp Wood",),
    ),
    "Resin": _m(
        "Woods, Fibers & Bindings", "Common", 1, 10,
        "Tree wounds, resin traps and apothecary stores",
        "Carpenter / Alchemy Bench",
        ("bow lamination", "waterproofing", "potion stabilization"),
        "A sticky bridge between woodcraft and alchemy, valued because it seals what mud would ruin.",
        5,
    ),
    "Oakwood": _m(
        "Woods, Fibers & Bindings", "Common", 6, 10,
        "Managed forests and Crown timber roads",
        "Carpenter / Bowyer",
        ("Iron-tier bows", "shield frames", "weapon hafts"),
        "Straight-grained Oakwood is the first timber professional soldiers trust with their lives.",
        12,
    ),
    "Refined Binding Kit": _m(
        "Woods, Fibers & Bindings", "Uncommon", 6, None,
        "Crafted from treated fiber, resin, fasteners and guild cord",
        "Quartermaster Workbench",
        ("Uncommon equipment", "reinforced cloth", "leatherwork", "bow assembly"),
        "A standardized guild bundle that makes advanced crafting repeatable instead of improvised.",
        24,
    ),
    "Ironbark": _m(
        "Woods, Fibers & Bindings", "Uncommon", 11, 15,
        "Protected groves of the Wyrdwood",
        "Wyrdwood Carpenter / Druid",
        ("armored bows", "living shields", "druid equipment"),
        "Its bark hardens like plate when cut, which is why the Wardens ration every legal harvest.",
        38,
    ),
    "Moonwillow": _m(
        "Woods, Fibers & Bindings", "Rare", 16, 20,
        "Harvested from moonlit Wyrdwood stands",
        "Master Bowyer / Druidic Workbench",
        ("magical bows", "druid staves", "lunar focuses"),
        "Moonwillow bends toward moonlight even after felling and remembers the shape of careful hands.",
        88,
    ),
    "Elderroot Fiber": _m(
        "Woods, Fibers & Bindings", "Very Rare", 21, 25,
        "Sacred roots beneath Elderroot Grove",
        "Verdant Covenant Artisan",
        ("living armor", "legendary bindings", "druid relics"),
        "The fiber is not fully dead; it tightens around worthy wearers and rejects corruption.",
        245,
    ),

    # ------------------------------------------------------------------
    # Hides, bones and monster parts
    # ------------------------------------------------------------------
    "Tanned Hide": _m(
        "Hides, Bones & Monster Parts", "Common", 1, 10,
        "Processed from common beast hides",
        "Tannery",
        ("light armor", "pouches", "straps", "padding"),
        "The smell of a tannery is the price every frontier town pays for durable gear.",
        8,
    ),
    "Leather": _m(
        "Hides, Bones & Monster Parts", "Common", 6, 15,
        "Refined from selected Tanned Hide",
        "Tannery / Leatherworker",
        ("Iron-tier armor parts", "quivers", "gloves", "tool grips"),
        "Proper Leather is selected, oiled and cut for load-bearing work rather than simple patching.",
        16,
    ),
    "Direhide": _m(
        "Hides, Bones & Monster Parts", "Uncommon", 11, 20,
        "Dangerous predators and corrupted great beasts",
        "Advanced Tannery",
        ("heavy leather armor", "monster-resistant gear"),
        "Direhide keeps scars from the creature that wore it and often resists ordinary needles.",
        45,
    ),
    "Trollbone Plating": _m(
        "Hides, Bones & Monster Parts", "Rare", 16, 20,
        "Prepared from mature troll bone",
        "Bonewright / Blacksmith",
        ("regenerative heavy armor", "shield reinforcement"),
        "Even separated from the troll, the bone slowly closes hairline fractures around itself.",
        105,
    ),
    "Drake Scale": _m(
        "Hides, Bones & Monster Parts", "Very Rare", 21, 25,
        "Drakes and lesser dragons",
        "Master Tannery / Blacksmith",
        ("fire-resistant armor", "heat shields", "legendary gear"),
        "Each scale is a small shield grown in flame, difficult to pierce and harder to shape.",
        260, aliases=("Dragon Scale",),
    ),
    "Abyssal Chitin": _m(
        "Hides, Bones & Monster Parts", "Very Rare", 26, 30,
        "Armored Vortex creatures",
        "Void Forge / Taint Laboratory",
        ("corruption-resistant armor", "Vortex expedition gear"),
        "A shell adapted to impossible pressure and Taint; mishandled fragments continue to twitch.",
        285,
    ),
    "Echo Heart": _m(
        "Hides, Bones & Monster Parts", "Mythic", 30, None,
        "Major Abyssal Echo bosses",
        "Artifact Forge",
        ("artifact cores", "mythic trinkets", "Vortex engines"),
        "The heart repeats the final intent of the creature it powered, sometimes for centuries.",
        1750,
    ),

    # ------------------------------------------------------------------
    # Herbs, alchemy and potions
    # ------------------------------------------------------------------
    "Bitterleaf": _m(
        "Herbs, Alchemy & Potions", "Common", 1, None,
        "Muckford fields, marsh edges and apothecary gardens",
        "Herbalist Station",
        ("basic healing potions", "bandages", "recovery meals"),
        "Its taste is memorable enough that soldiers know a real field tonic before it is swallowed.",
        7, aliases=("Bogwort", "Medicinal Herb"),
    ),
    "Sunblossom": _m(
        "Herbs, Alchemy & Potions", "Uncommon", 6, 15,
        "Sunny clearings, temple gardens and warm southern terraces",
        "Alchemy Bench / Holy Apothecary",
        ("stamina potions", "holy remedies", "strong restoratives"),
        "The flower turns toward the strongest clean light, even inside a sealed room.",
        24, aliases=("Sunleaf",),
    ),
    "Nightcap Fungus": _m(
        "Herbs, Alchemy & Potions", "Uncommon", 6, 15,
        "Wet caves, frog territories and shaded marsh logs",
        "Alchemy Bench",
        ("antidotes", "sleep draughts", "toxin studies"),
        "Safe in measured doses, dangerous in damp handfuls and beloved by reckless swamp brewers.",
        22,
    ),
    "Moondew Petals": _m(
        "Herbs, Alchemy & Potions", "Rare", 16, 20,
        "Collected before dawn from lunar flowers",
        "Advanced Alchemy Bench",
        ("mana potions", "focus restoratives", "lunar inks"),
        "The dew evaporates after sunrise unless the petals are sealed in silver or glass.",
        72, aliases=("Moonpetal",),
    ),
    "Grave-Lotus": _m(
        "Herbs, Alchemy & Potions", "Rare", 16, 25,
        "Old battlefields, necromantic marshes and guarded ossuary pools",
        "Necromantic Apothecary",
        ("necromantic reagents", "dangerous corruption cleanses"),
        "It blooms where memory, blood and death have soaked the same ground for years.",
        84,
    ),
    "Vortex Residue": _m(
        "Herbs, Alchemy & Potions", "Very Rare", 26, 30,
        "Vortex creatures, unstable fractures and contaminated relics",
        "Taint Laboratory / Master Alchemy",
        ("highest-tier potions", "Void catalysts", "corruption research"),
        "Powerful enough to transform a formula and unstable enough to transform the brewer.",
        240,
    ),

    # ------------------------------------------------------------------
    # Magic, runes and trinkets
    # ------------------------------------------------------------------
    "Arcane Dust": _m(
        "Magic, Runes & Trinkets", "Uncommon", 6, 20,
        "Disenchanted items, spell residue and Prism Collegium stores",
        "Enchanter / Scriptorium",
        ("enchanting", "Arcane Ink", "rune activation"),
        "A neutral magical powder whose value lies in accepting almost any stable pattern.",
        26,
    ),
    "Silver Filigree Wire": _m(
        "Magic, Runes & Trinkets", "Uncommon", 10, 20,
        "Jeweler guilds and fine metal workshops",
        "Jeweler / Enchanter",
        ("rings", "amulets", "focus cages", "precision components"),
        "Thin enough to stitch magic into jewelry without smothering the stone it surrounds.",
        34,
    ),
    "Mirror Dust": _m(
        "Magic, Runes & Trinkets", "Uncommon", 10, 20,
        "Argent Veil workshops, illusion mirrors and shattered scrying glass",
        "Manipulation Enchanter",
        ("illusion trinkets", "mind wards", "reflective inks"),
        "Every grain catches an angle that does not quite belong to the room around it.",
        36,
    ),
    "Focus Powder": _m(
        "Magic, Runes & Trinkets", "Uncommon", 11, 20,
        "Ground focus crystals and specialist alchemists",
        "Alchemy Bench / Enchanter",
        ("spell stabilization", "mana potions", "focus crafting"),
        "Its quality varies with the crystal: ordinary batches are Uncommon, flawless batches Rare.",
        38, special_grade="Uncommon/Rare",
    ),
    "Focus Crystal Shard": _m(
        "Magic, Runes & Trinkets", "Rare", 16, 25,
        "Aegis crystal caverns, spellcaster bosses and broken foci",
        "Enchanter / Scriptorium",
        ("rare caster equipment", "master stations", "focus upgrades"),
        "A shard still holds the directional bias of the original crystal and must be matched carefully.",
        95,
    ),
    "Rune Plate": _m(
        "Magic, Runes & Trinkets", "Rare", 16, 25,
        "Runesmiths, old vaults and sanctioned guild foundries",
        "Rune Desk / Blacksmith",
        ("rare weapon upgrades", "armor runes", "sealed enchantments"),
        "A prepared plate carries a rune safely; carving directly into finished gear often ruins both.",
        110,
    ),
    "Sanctified Ember": _m(
        "Magic, Runes & Trinkets", "Rare", 16, 25,
        "Radiant Synod braziers and purified undead sites",
        "Holy Enchanter",
        ("holy trinkets", "undead wards", "purification seals"),
        "The ember does not consume ordinary fuel and dims in the presence of deliberate corruption.",
        105,
    ),
    "Soul Ash": _m(
        "Magic, Runes & Trinkets", "Rare", 16, 25,
        "Necromantic remains, Ossuary rites and destroyed soul vessels",
        "Necromantic Enchanter",
        ("necromantic trinkets", "spirit bindings", "death wards"),
        "Not a soul, but the residue left when one is forced through an unnatural shape.",
        100,
    ),
    "Echo Shard": _m(
        "Magic, Runes & Trinkets", "Rare", 18, 30,
        "Lesser Abyssal Echo bosses",
        "Enchanter / Artifact Forge",
        ("legendary upgrades", "echo weapons", "artifact preparation"),
        "A splinter of a boss's repeating identity; collectors call its exceptional grade Epic.",
        145, special_grade="Epic",
    ),
    "Seal-Lacquer": _m(
        "Magic, Runes & Trinkets", "Very Rare", 22, 30,
        "Highstone Sanctum under charter control",
        "Highstone Rune Desk",
        ("anti-corruption coating", "legal artifact seals", "Vortex equipment"),
        "Highstone's secret lacquer bonds law, ritual and material into one protective seal.",
        275,
    ),
    "Charter Seal Token": _m(
        "Magic, Runes & Trinkets", "Mythic", 30, None,
        "Granted by Highstone Sanctum and Arkon's officials",
        "Artifact Registry / Forge",
        ("legalizing artifacts", "mythic crafting permission", "endgame contracts"),
        "The token is less a currency than proof that Highstone accepts responsibility for what is made.",
        2000,
    ),

    # ------------------------------------------------------------------
    # Scrolls and spell components
    # ------------------------------------------------------------------
    "Parchment Sheet": _m(
        "Scrolls & Spell Components", "Common", 1, None,
        "Scribes, tanners and market stationery stalls",
        "Scriptorium",
        ("scrolls", "spellbooks", "contracts", "maps"),
        "Good parchment survives mud, travel and repeated erasure better than cheap paper ever could.",
        4,
    ),
    "Wax Seal": _m(
        "Scrolls & Spell Components", "Common", 1, None,
        "Markets, beekeepers and contract offices",
        "Scriptorium",
        ("sealed scrolls", "contracts", "ritual packets"),
        "A seal proves who closed a document; in Varrakor, that can matter more than what it says.",
        3,
    ),
    "Arcane Ink": _m(
        "Scrolls & Spell Components", "Uncommon", 6, None,
        "Mixed from ink, Arcane Dust and stabilizers",
        "Scriptorium",
        ("spell scrolls", "rune diagrams", "enchanted contracts"),
        "Arcane Ink remembers the order of its strokes and punishes corrections made without solvent.",
        28,
    ),
    "Spell Focus Bead": _m(
        "Scrolls & Spell Components", "Uncommon", 6, 15,
        "Prism Collegium workshops and specialist jewelers",
        "Scriptorium / Enchanter",
        ("mid-tier spells", "staff upgrades", "portable spell foci"),
        "A small bead gives a spell one stable place to begin, reducing dangerous drift in the pattern.",
        32,
    ),
})


# Crafted intermediates are not world-gathering materials, but they remain
# valid inventory keys and receive codex descriptions.
CRAFTED_COMPONENTS = {
    "Scrap Metal Bar": {
        "rarity": "Common",
        "level_min": 1,
        "level_max": 5,
        "station": "Smeltery",
        "lore": "A compacted billet of sorted scrap used by Muckford's crude smiths.",
        "sell_price": 8,
    },
    "Bandage Roll": {
        "rarity": "Common",
        "level_min": 1,
        "level_max": 10,
        "station": "Quartermaster Workbench",
        "lore": "Clean layered fiber prepared for the Recovery Ward.",
        "sell_price": 7,
    },
    "Treated Timber": {
        "rarity": "Common",
        "level_min": 1,
        "level_max": 10,
        "station": "Quartermaster Workbench",
        "lore": "Rough Timber sealed with Resin for permanent construction.",
        "sell_price": 10,
    },
    "Leather Straps": {
        "rarity": "Uncommon",
        "level_min": 6,
        "level_max": 20,
        "station": "Quartermaster Workbench",
        "lore": "Load-bearing straps cut from Leather with a Refined Binding Kit.",
        "sell_price": 18,
    },
    "Reinforced Cloth": {
        "rarity": "Uncommon",
        "level_min": 6,
        "level_max": 20,
        "station": "Quartermaster Workbench",
        "lore": "Layered Plant Fiber locked into shape by a Refined Binding Kit.",
        "sell_price": 20,
    },
    "Precision Components": {
        "rarity": "Rare",
        "level_min": 16,
        "level_max": 30,
        "station": "Guild Artisan Bench",
        "lore": "Fine mechanisms combining Iron, silver wire and stabilized focus powder.",
        "sell_price": 65,
    },
}


ALIASES = {}
for _name, _data in MATERIALS.items():
    for _alias in _data.get("aliases", ()):
        ALIASES[_alias] = _name

# Additional migration aliases from older builds and shorthand lore names.
ALIASES.update({
    "Blacksteel Bar": "Blacksteel Ingot",
    "Stormsilver Bar": "Stormsilver Ingot",
    "Sun-Gold Bar": "Sun-Gold Ingot",
    "Moonpetal Petals": "Moondew Petals",
    "Arcane Powder": "Focus Powder",
    "Echo Fragment": "Echo Shard",
})


COMMON_MARKET_STOCK = {
    "Coal": 7,
    "Plant Fiber": 5,
    "Rough Timber": 9,
    "Resin": 11,
    "Parchment Sheet": 8,
    "Wax Seal": 6,
}


def canonical_material_name(name: str) -> str:
    """Return the current canonical inventory key for a legacy material name."""
    return ALIASES.get(str(name), str(name))


def get_material(name: str) -> Optional[dict]:
    canonical = canonical_material_name(name)
    data = MATERIALS.get(canonical)
    if data is None:
        return None
    result = dict(data)
    result["name"] = canonical
    return result


def get_material_or_component(name: str) -> Optional[dict]:
    canonical = canonical_material_name(name)
    data = get_material(canonical)
    if data:
        data["kind"] = "world_material"
        return data
    component = CRAFTED_COMPONENTS.get(canonical)
    if component:
        result = dict(component)
        result.update({"name": canonical, "category": "Crafted Components",
                       "source": f"Crafted at {component['station']}",
                       "uses": ["station upgrades", "crafting recipes"],
                       "kind": "crafted_component"})
        return result
    return None


def iter_materials(category: Optional[str] = None,
                   rarity: Optional[str] = None) -> Iterable[tuple[str, dict]]:
    for name, data in MATERIALS.items():
        if category and data["category"] != category:
            continue
        if rarity and data["rarity"] != rarity:
            continue
        yield name, data


def material_names() -> set[str]:
    return set(MATERIALS) | set(CRAFTED_COMPONENTS)


def resource_tiers_view() -> dict:
    """Build the legacy ``world_data.RESOURCE_TIERS`` shape from this registry."""
    currency = {
        "Common": "SP",
        "Uncommon": "GP",
        "Rare": "GP",
        "Very Rare": "PL",
        "Mythic": "HC",
    }
    arena_tiers = {
        "Common": (0, 1),
        "Uncommon": (1, 2),
        "Rare": (3, 4),
        "Very Rare": (4, 5),
        "Mythic": (5, 5),
    }
    result = {}
    for rarity in RARITY_ORDER:
        resources = {
            name: data["lore"]
            for name, data in MATERIALS.items()
            if data["rarity"] == rarity
        }
        result[rarity] = {
            "tiers": arena_tiers[rarity],
            "currency": currency[rarity],
            "resources": resources,
        }
    return result
