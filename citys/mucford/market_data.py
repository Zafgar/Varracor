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
        "buys": ("Apple", "Egg", "Milk", "Carrot", "Potato",
                 "Onion", "Cabbage", "Turnip", "Medicinal Herb",
                 "Bitterleaf", "Bogwort", "Nightcap Fungus",
                 "Quality Produce"),
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
        "buys": ("Scrap", "Scrap Iron", "Iron Ore", "Iron Bar",
                 "Rat Tail", "Coal"),
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
        "buys": ("Scrap Iron", "Iron Bar", "Spider Silk", "Direhide",
                 "Leather Straps"),
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
            # Armor rework (pelitesti 26): tier 1-2 -varusteet katalogista.
            # Hinnat täytetään moduulin lopussa gear-katalogin hinnoilla
            # (_fill_mudguard_tier_gear) - EI käsin kovakoodattuja.
            {"name": "__TIER_GEAR__", "price": 0, "kind": "item"},
        ),
    },
    "bittersip": {
        "buys": ("Bitterleaf", "Bogwort", "Nightcap Fungus",
                 "Spirit Essence", "Venom Gland", "Mudfin", "Bog Perch"),
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
        "buys": ("Feather", "Manure", "Rat Tail", "Swamp Wood",
                 "Stone", "Scrap", "Coal", "Rough Timber"),
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
            {"name": "Fishing Rod", "price": 18, "kind": "item",
             "class": "FishingRod"},
            {"name": "Bogwood Rod", "price": 45, "kind": "item",
             "class": "BogwoodRod"},
            {"name": "Twisted Stick", "price": 18, "kind": "item"},
            {"name": "Heavy Branch", "price": 22, "kind": "item"},
        ),
    },
})


def _fill_scrap_arms_tier_weapons():
    """Aseet L30 asti (pelitesti 27): Grett myy tier 1-2 -aseet suoraan
    asekatalogista - hinnat katalogista, ei kovakoodattuja kopioita."""
    from items.weapon_catalog import make_weapon
    rows = []
    for wid in ("w_sword_t1", "w_dagger_t1", "w_axe_t1", "w_mace_t1",
                "w_spear_t1", "w_bow_t1", "w_crossbow_t1", "w_staff_t1",
                "w_book_t1",
                "w_sword_t2", "w_axe_t2", "w_bow_t2"):
        w = make_weapon(wid)
        rows.append({"name": w.name, "price": w.cost, "kind": "item"})
    shop = MARKET_SHOPS["scrap_arms"]
    shop["goods"] = tuple(list(shop["goods"]) + rows)


def _fill_mudguard_tier_gear():
    """Armor rework (pelitesti 26): Mudguard myy tier 1-2 -taistelija-
    varusteet suoraan katalogista - nimet JA hinnat gear_catalogista,
    ei käsin ylläpidettäviä kopioita. Placeholder '__TIER_GEAR__'
    korvataan aidoilla riveillä importin yhteydessä."""
    from items.gear_catalog import make_gear
    rows = []
    for gid in ("juggernaut_t1", "ranger_t1", "battlemage_t1",
                "greathelm_t1", "warhelm_t1", "hood_t1", "circlet_t1",
                "veilmask_t1", "buckler_t1", "aegis_t1",
                "bulwark_shield_t1",
                "warrior_t2", "skirmisher_t2", "greathelm_t2",
                "aegis_t2"):
        g = make_gear(gid)
        rows.append({"name": g.name, "price": g.cost, "kind": "item"})
    shop = MARKET_SHOPS["mudguard_armory"]
    goods = [e for e in shop["goods"] if e["name"] != "__TIER_GEAR__"]
    shop["goods"] = tuple(goods + rows)


_fill_mudguard_tier_gear()
_fill_scrap_arms_tier_weapons()
