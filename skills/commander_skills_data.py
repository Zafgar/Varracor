# skills/commander_skills_data.py

# Määritellään Commanderin omat puut.
# Koordinaatit (pos) ovat (x, y) suhteessa keskipisteeseen (0,0).
# Negatiivinen Y on ylöspäin.

# --- COMMAND TREE (johtaminen) ---
# Pelaajapalaute: commander-pisteiden pitää olla JOHTAMISvalintoja
# (tiimin koko, taisteluhuudot, läsnäolo) - ei crafting/combat-syvyyttä.
# Elämäntaitobonukset elävät omalla TRADECRAFT-välilehdellään alla.
COMMANDER_COMMAND_TREE = {
    "leader_1": {
        "name": "Recruiter I",
        "desc": "A larger banner draws more blades: team capacity 8 "
                "(barracks bunks still required).",
        "pos": (0, 0),
        "cost": 2,
        "min_level": 3,
        "requires": [],
        "effects": {"team_cap": 8}
    },
    "leader_2": {
        "name": "Recruiter II",
        "desc": "Your name alone fills the roster: team capacity 10.",
        "pos": (0, -110),
        "cost": 3,
        "min_level": 7,
        "requires": ["leader_1"],
        "effects": {"team_cap": 10}
    },
    "shout_rally": {
        "name": "Rally Cry",
        "desc": "Battle shout [G]: your fighters break off and regroup "
                "on you for 5 seconds.",
        "pos": (-170, 0),
        "cost": 1,
        "min_level": 2,
        "requires": [],
        "effects": {"shout": "rally"}
    },
    "shout_charge": {
        "name": "Charge Order",
        "desc": "Battle shout [H]: your fighters sprint at the nearest "
                "enemy and attack with everything for 5 seconds.",
        "pos": (-170, -110),
        "cost": 2,
        "min_level": 4,
        "requires": ["shout_rally"],
        "effects": {"shout": "charge"}
    },
    "drillmaster": {
        "name": "Drillmaster",
        "desc": "Victories mean more under your drills: team gains double "
                "morale from won matches.",
        "pos": (170, 0),
        "cost": 2,
        "min_level": 3,
        "requires": [],
        "effects": {"drillmaster": 1}
    },
    "iron_presence": {
        "name": "Iron Presence",
        "desc": "Defeats sting less with you at the front: team loses "
                "only half morale from lost matches.",
        "pos": (170, -110),
        "cost": 2,
        "min_level": 5,
        "requires": ["drillmaster"],
        "effects": {"iron_presence": 1}
    },
}

COMMANDER_SKILL_TREE = {
    # --- PICKAXE BRANCH (Left) ---
    # HUOM: Hakkujen/kirveiden KÄYTTÖOIKEUS tulee Commander Paths -poluista
    # (Path of the Vein / Timber, systems/commander_progression.py).
    # Nämä pistepuun noodit antavat BONUKSIA polkujen päälle.
    "mining_1": {
        "name": "Pickaxe Training I",
        "desc": "Miner's grip and stance. +1 STR, +5% mining speed.",
        "pos": (-160, 0),
        "cost": 1,
        "min_level": 1,
        "requires": [],
        "effects": {"str": 1, "mining_speed": 0.05}
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

    # --- ANGLER BRANCH (Far Left, husbandryn yläpuoli) ---
    # systems/fishing.py: -15 % odotus & +ikkuna / taso, harvinaiset kalat
    "fishing_1": {
        "name": "Angler",
        "desc": "Patient hands: fish bite sooner and the hook window is longer.",
        "pos": (-320, -120),
        "cost": 1,
        "min_level": 1,
        "requires": ["husbandry_1"],
        "effects": {"fishing": 1}
    },
    "fishing_2": {
        "name": "Marsh Angler",
        "desc": "You read the water: rare fish take the bait far more often.",
        "pos": (-320, -220),
        "cost": 2,
        "min_level": 3,
        "requires": ["fishing_1"],
        "effects": {"fishing": 1, "dex": 1}
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

    # --- APPRAISER (Insight) ---
    # Paljastaa taistelijoiden talenttien tarkat vaikutukset korteilla
    "insight_1": {
        "name": "Appraiser's Eye",
        "desc": "See the exact effects of a fighter's innate talents.",
        "pos": (460, 80),
        "cost": 1,
        "min_level": 2,
        "requires": [],
        "effects": {"insight": 1, "int": 1}
    },

    # --- LUMBER AXE BRANCH (Right) ---
    "lumber_1": {
        "name": "Lumberjack I",
        "desc": "Woodsman's swing. +1 STR, +5% chopping speed.",
        "pos": (160, 0),
        "cost": 1,
        "min_level": 1,
        "requires": [],
        "effects": {"str": 1, "chop_speed": 0.05}
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
