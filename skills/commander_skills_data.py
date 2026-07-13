# skills/commander_skills_data.py

# Määritellään Commanderin oma puu.
# Koordinaatit (pos) ovat (x, y) suhteessa keskipisteeseen (0,0).
# Negatiivinen Y on ylöspäin.

COMMANDER_SKILL_TREE = {
    # --- PICKAXE BRANCH (Left) ---
    "mining_1": {
        "name": "Pickaxe Training I",
        "desc": "Allows the use of Basic Pickaxes.",
        "pos": (-160, 0),
        "cost": 1,
        "min_level": 1,
        "requires": [],
        "effects": {"weapon_prof": "pickaxe", "str": 1}
    },
    "mining_2": {
        "name": "Pickaxe Training II",
        "desc": "Better handling of mining tools. +2 STR.",
        "pos": (-160, -100),
        "cost": 2,
        "min_level": 3,
        "requires": ["mining_1"],
        "effects": {"str": 2, "mining_speed": 0.1}
    },
    "mining_3": {
        "name": "Pickaxe Master",
        "desc": "Mastery over heavy picks. +3 STR.",
        "pos": (-160, -200),
        "cost": 3,
        "min_level": 5,
        "requires": ["mining_2"],
        "effects": {"str": 3, "mining_yield": 1}
    },

    # --- HARVESTING BRANCH (Centre) ---
    "harvesting_1": {
        "name": "Harvesting I",
        "desc": "Use basic sickles and harvest carrots, potatoes and onions.",
        "pos": (0, 80),
        "cost": 1,
        "min_level": 1,
        "requires": [],
        "effects": {"weapon_prof": "harvest_tool", "dex": 1}
    },
    "harvesting_2": {
        "name": "Harvesting II",
        "desc": "Use iron harvesting tools for cabbage and turnips. Better yields.",
        "pos": (0, -20),
        "cost": 2,
        "min_level": 3,
        "requires": ["harvesting_1"],
        "effects": {"weapon_prof": "harvest_tool", "dex": 2,
                    "harvest_yield": 1}
    },
    "harvesting_3": {
        "name": "Master Harvester",
        "desc": "Use guild scythes, harvest medicinal herbs and find quality produce.",
        "pos": (0, -120),
        "cost": 3,
        "min_level": 5,
        "requires": ["harvesting_2"],
        "effects": {"weapon_prof": "harvest_tool", "dex": 3,
                    "harvest_quality": 0.20}
    },

    # --- ANIMAL HUSBANDRY BRANCH (Far Left) ---
    # Lypsy tuottaa Milk-materiaalia keittiöön ja kanat munivat tiheämmin.
    "husbandry_1": {
        "name": "Animal Husbandry I",
        "desc": "Gentle hands: milking also fills a jug of Milk, hens lay more often.",
        "pos": (-320, 80),
        "cost": 1,
        "min_level": 1,
        "requires": [],
        "effects": {"husbandry": 1, "dex": 1}
    },
    "husbandry_2": {
        "name": "Animal Husbandry II",
        "desc": "Herd whisperer: even more Milk per milking and quicker layers.",
        "pos": (-320, -20),
        "cost": 2,
        "min_level": 3,
        "requires": ["husbandry_1"],
        "effects": {"husbandry": 1, "dex": 1}
    },

    # --- TRADE BRANCH (Far Right) ---
    # Vaikuttaa market-alueen liikkeiden hintoihin (systems/faction_reputation).
    "trade_1": {
        "name": "Haggler",
        "desc": "Shopkeepers warm to you: prices as if your standing were 10 higher.",
        "pos": (320, 80),
        "cost": 1,
        "min_level": 1,
        "requires": [],
        "effects": {"haggler": 1, "int": 1}
    },
    "trade_2": {
        "name": "Silver Tongue",
        "desc": "A famous customer: prices as if your standing were 20 higher.",
        "pos": (320, -20),
        "cost": 2,
        "min_level": 3,
        "requires": ["trade_1"],
        "effects": {"haggler": 1, "int": 2}
    },

    # --- LUMBER AXE BRANCH (Right) ---
    "lumber_1": {
        "name": "Lumberjack I",
        "desc": "Allows the use of Woodcutting Axes.",
        "pos": (160, 0),
        "cost": 1,
        "min_level": 1,
        "requires": [],
        "effects": {"weapon_prof": "lumber_axe", "str": 1}
    },
    "lumber_2": {
        "name": "Lumberjack II",
        "desc": "Efficient chopping technique. +2 STR.",
        "pos": (160, -100),
        "cost": 2,
        "min_level": 3,
        "requires": ["lumber_1"],
        "effects": {"str": 2, "chop_speed": 0.1}
    },
    "lumber_3": {
        "name": "Forest Lord",
        "desc": "Mastery over lumber axes. +3 STR.",
        "pos": (160, -200),
        "cost": 3,
        "min_level": 5,
        "requires": ["lumber_2"],
        "effects": {"str": 3, "wood_yield": 1}
    },
}
