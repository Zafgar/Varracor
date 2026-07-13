# citys/mucford/market_data.py
"""Muckfordin market-alueen kaupat.

Toiminta siirtyy valikoista pelikenttään: market-alueella on erilliset
liikkeet (vihannes, ase, panssari+kilpi, juoma, sekatavara), joihin
kävellään ja joista aukeaa kunkin kaupan omanlaisensa kauppasivu.

Jokaisella kaupalla on OMA maine-faktio (manager.reputations[faction]) -
kanta-asiakkuus TÄSSÄ liikkeessä laskee TÄMÄN liikkeen hintoja, ei muiden.

goods-rivit: {"name", "price" (perushinta), "kind": "item"|"material",
              "class": item-rekisterin luontinimi (jos eri kuin name)}
"""

from collections import OrderedDict

MARKET_SHOPS = OrderedDict({
    "greenmarket": {
        "name": "Fenna's Greenmarket",
        "keeper": "Old Fenna",
        "keeper_race": "Human",
        "kind": "produce",
        "faction": "muckford_growers",
        "faction_label": "Muckford Growers",
        "awning": (74, 118, 66),
        "flavor": "Mud-grown, marsh-picked, still cheaper than starving.",
        "goods": (
            {"name": "Apple", "price": 4, "kind": "material"},
            {"name": "Egg", "price": 4, "kind": "material"},
            {"name": "Bitterleaf", "price": 7, "kind": "material"},
            {"name": "Bogwort", "price": 6, "kind": "material"},
            {"name": "Nightcap Fungus", "price": 9, "kind": "material"},
        ),
    },
    "scrap_arms": {
        "name": "Grett's Scrap Arms",
        "keeper": "Grett Iron-Tooth",
        "keeper_race": "Orc",
        "kind": "weapons",
        "faction": "muckford_smiths",
        "faction_label": "Shanty Smiths",
        "awning": (128, 58, 54),
        "flavor": "Every blade killed a rat before you. Proven steel. Ish.",
        "goods": (
            {"name": "Scrap Blade", "price": 28, "kind": "item"},
            {"name": "Dull Hatchet", "price": 26, "kind": "item"},
            {"name": "Splintered Pole", "price": 24, "kind": "item"},
            {"name": "Rusty Shiv", "price": 20, "kind": "item"},
            {"name": "Scrap Bow", "price": 30, "kind": "item"},
            {"name": "Jammed Crossbow", "price": 34, "kind": "item"},
        ),
    },
    "mudguard_armory": {
        "name": "The Mudguard",
        "keeper": "Sella Twoplates",
        "keeper_race": "Dwarf",
        "kind": "armor",
        "faction": "muckford_smiths",
        "faction_label": "Shanty Smiths",
        "awning": (86, 96, 122),
        "flavor": "Dents included free of charge. They prove it works.",
        "goods": (
            {"name": "Padded Vest", "price": 26, "kind": "item"},
            {"name": "Leather Cap", "price": 16, "kind": "item"},
            {"name": "Rusty Mail", "price": 48, "kind": "item"},
            {"name": "Iron Helm", "price": 34, "kind": "item"},
            {"name": "Pot Lid", "price": 14, "kind": "item"},
            {"name": "Wooden Buckler", "price": 24, "kind": "item"},
        ),
    },
    "bittersip": {
        "name": "The Bittersip",
        "keeper": "Mirelda Vex",
        "keeper_race": "Goblin",
        "kind": "potions",
        "faction": "muckford_brewers",
        "faction_label": "Marsh Brewers",
        "awning": (104, 74, 122),
        "flavor": "Shake before drinking. Pray after.",
        "goods": (
            {"name": "Weak Health Potion", "price": 30, "kind": "item"},
            {"name": "Bitterleaf", "price": 8, "kind": "material"},
            {"name": "Nightcap Fungus", "price": 10, "kind": "material"},
        ),
    },
    "oddments": {
        "name": "Krad's Oddments",
        "keeper": "Krad",
        "keeper_race": "Goblin",
        "kind": "general",
        "faction": "muckford_traders",
        "faction_label": "Shanty Traders",
        "awning": (122, 104, 58),
        "flavor": "Found honestly. Mostly. Do not ask about the bucket.",
        "goods": (
            {"name": "Empty Bucket", "price": 5, "kind": "item",
             "class": "BucketEmpty"},
            {"name": "Weak Pickaxe", "price": 12, "kind": "item",
             "class": "WeakPickaxe"},
            {"name": "Twisted Stick", "price": 18, "kind": "item"},
            {"name": "Heavy Branch", "price": 22, "kind": "item"},
        ),
    },
})
