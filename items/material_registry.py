# items/material_registry.py

# Määritellään kategoriat
CAT_ORE = "Ore"
CAT_MONSTER = "Monster Part"
CAT_MAGIC = "Magic Dust"
CAT_SPECIAL = "Special"

# Tietokanta kaikista materiaaleista
MATERIAL_DB = {
    # --- TIER 1 ---
    "Rat Tail": {
        "name": "Rat Tail",
        "rarity": "Common",
        "category": CAT_MONSTER,
        "desc": "A grimy tail from a giant rat. Alchemists use it.",
        "icon": "assets/icons/materials/rat_tail.png", # Polku
        "value": 10
    },
    "Scrap Iron": {
        "name": "Scrap Iron",
        "rarity": "Common",
        "category": CAT_ORE,
        "desc": "Rusted metal from old war machines found in Muckford.",
        "value": 5
    },
    "Iron Ore": {
        "name": "Iron Ore",
        "rarity": "Common",
        "category": CAT_ORE,
        "desc": "Standard iron ore. Used for basic weapons.",
        "value": 15
    },
    "Coal": {
        "name": "Coal",
        "rarity": "Common",
        "category": CAT_ORE,
        "desc": "Fuel for the smeltery.",
        "value": 5
    },
    
    # --- TIER 2 ---
    "Bone Fragment": {
        "name": "Bone Fragment",
        "rarity": "Common",
        "category": CAT_MONSTER,
        "desc": "Splintered bone from a skeleton. Surprisingly hard.",
        "value": 20
    },
    "Spider Silk": {
        "name": "Spider Silk",
        "rarity": "Uncommon",
        "category": CAT_MONSTER,
        "desc": "Strong and lightweight silk.",
        "value": 40
    },
    "Nightcap Fungus": {
        "name": "Nightcap Fungus",
        "rarity": "Uncommon",
        "category": CAT_SPECIAL,
        "desc": "Rare swamp mushroom. Valued by Vinehollow healers.",
        "value": 35
    },
    "Blacksteel Ore": {
        "name": "Blacksteel Ore",
        "rarity": "Uncommon",
        "category": CAT_ORE,
        "desc": "Industrial grade metal from Rivet Row. Resistant to taint.",
        "value": 45
    },
    "Vortex Residue": {
        "name": "Vortex Residue",
        "rarity": "Rare",
        "category": CAT_MAGIC,
        "desc": "Glowing sludge from the edge of the Vortex. Prism Collegium buys this.",
        "value": 120
    },
    "Stormsilver Ore": {
        "name": "Stormsilver Ore",
        "rarity": "Rare",
        "category": CAT_ORE,
        "desc": "Conductive metal from Aegis Peaks. Used in magic gear.",
        "value": 120
    },
    "Void-Iron": {
        "name": "Void-Iron",
        "rarity": "Very Rare",
        "category": CAT_ORE,
        "desc": "Cold, black metal from the Vortex edge. Used for Vortexforged gear.",
        "value": 1500 # 1.5 PL
    },
    "Sun-Gold Ore": {
        "name": "Sun-Gold Ore",
        "rarity": "Very Rare",
        "category": CAT_ORE,
        "desc": "Royal metal from the deepest Crownlands mines.",
        "value": 800
    },
    "Swamp Wood": {
        "name": "Swamp Wood",
        "rarity": "Common",
        "category": CAT_SPECIAL,
        "desc": "Rot-resistant wood from the marshes.",
        "value": 8
    },
    "Apple": {
        "name": "Apple",
        "rarity": "Common",
        "category": "Food",
        "desc": "A fresh red apple.",
        "value": 2
    },
    "Egg": {
        "name": "Egg",
        "rarity": "Common",
        "category": "Food",
        "desc": "A fresh chicken egg.",
        "value": 3
    },
    "Chicken Meat": {
        "name": "Chicken Meat",
        "rarity": "Common",
        "category": "Food",
        "desc": "Raw chicken meat.",
        "value": 5
    },
    "Scrap Metal Bar": {
        "name": "Scrap Metal Bar",
        "rarity": "Uncommon",
        "category": CAT_ORE,
        "desc": "Refined scrap metal, ready for crafting.",
        "value": 15
    },
    "Iron Bar": {
        "name": "Iron Bar",
        "rarity": "Common",
        "category": CAT_ORE,
        "desc": "Refined iron ingot.",
        "value": 25
    },

    # --- TIER 3 / SPECIAL ---
    "Ethereal Dust": {
        "name": "Ethereal Dust",
        "rarity": "Rare",
        "category": CAT_MAGIC,
        "desc": "Glowing dust that hums with energy.",
        "value": 200
    },
    "Golem Core": {
        "name": "Golem Core",
        "rarity": "Epic",
        "category": CAT_SPECIAL,
        "desc": "The pulsating heart of an Iron Golem.",
        "value": 500
    },
    "Heartcore Adamant": {
        "name": "Heartcore Adamant",
        "rarity": "Mythic",
        "category": CAT_ORE,
        "desc": "A shard from the Eye of the Vortex. Priceless.",
        "value": 10000
    }
}

def get_material_info(name):
    """Hakee materiaalin tiedot. Jos ei löydy, palauttaa geneerisen 'Junk' tiedon."""
    return MATERIAL_DB.get(name, {
        "name": name,
        "rarity": "Common",
        "category": "Junk",
        "desc": "Unknown item.",
        "value": 1
    })