# skills/commander_skills_data.py

# Määritellään Commanderin oma puu.
# Koordinaatit (pos) ovat (x, y) suhteessa keskipisteeseen (0,0).
# Negatiivinen Y on ylöspäin.

COMMANDER_SKILL_TREE = {
    # --- PICKAXE BRANCH (Left) ---
    "mining_1": {
        "name": "Pickaxe Training I",
        "desc": "Allows the use of Basic Pickaxes.",
        "pos": (-100, 0),
        "cost": 1,
        "min_level": 1,
        "requires": [],
        "effects": {"weapon_prof": "pickaxe", "str": 1}
    },
    "mining_2": {
        "name": "Pickaxe Training II",
        "desc": "Better handling of mining tools. +2 STR.",
        "pos": (-100, -100),
        "cost": 2,
        "min_level": 3,
        "requires": ["mining_1"],
        "effects": {"str": 2, "mining_speed": 0.1}
    },
    "mining_3": {
        "name": "Pickaxe Master",
        "desc": "Mastery over heavy picks. +3 STR.",
        "pos": (-100, -200),
        "cost": 3,
        "min_level": 5,
        "requires": ["mining_2"],
        "effects": {"str": 3, "mining_yield": 1}
    },

    # --- LUMBER AXE BRANCH (Right) ---
    "lumber_1": {
        "name": "Lumberjack I",
        "desc": "Allows the use of Woodcutting Axes.",
        "pos": (100, 0),
        "cost": 1,
        "min_level": 1,
        "requires": [],
        "effects": {"weapon_prof": "lumber_axe", "str": 1}
    },
    "lumber_2": {
        "name": "Lumberjack II",
        "desc": "Efficient chopping technique. +2 STR.",
        "pos": (100, -100),
        "cost": 2,
        "min_level": 3,
        "requires": ["lumber_1"],
        "effects": {"str": 2, "chop_speed": 0.1}
    },
    "lumber_3": {
        "name": "Forest Lord",
        "desc": "Mastery over lumber axes. +3 STR.",
        "pos": (100, -200),
        "cost": 3,
        "min_level": 5,
        "requires": ["lumber_2"],
        "effects": {"str": 3, "wood_yield": 1}
    },
}
