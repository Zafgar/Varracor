# loot_data.py

# --- LOOT DROPS (Hirviöt) ---
LOOT_DROPS = {
    'Giant Rat': [{'item': 'Rat Tail', 'chance': 0.8, 'min': 1, 'max': 2}],
    'Rat Rider': [
        {'item': 'Rat Tail', 'chance': 0.8, 'min': 1, 'max': 2},
        {'item': 'Saddle Scrap', 'chance': 0.4, 'min': 1, 'max': 1},
    ],
    'Skeleton':  [{'item': 'Bone Dust', 'chance': 0.6, 'min': 1, 'max': 3}],
    'Skeleton Archer': [
        {'item': 'Bone Dust', 'chance': 0.6, 'min': 1, 'max': 2},
        {'item': 'Cracked Arrow', 'chance': 0.4, 'min': 1, 'max': 3},
    ],
    'Zombie': [
        {'item': 'Rotten Flesh', 'chance': 0.7, 'min': 1, 'max': 2},
        {'item': 'Bone Dust', 'chance': 0.3, 'min': 1, 'max': 1},
    ],
    'Corrupted Crow': [
        {'item': 'Black Feather', 'chance': 0.7, 'min': 1, 'max': 2},
        {'item': 'Vortex Residue', 'chance': 0.1, 'min': 1, 'max': 1},
    ],
    'Slime':     [{'item': 'Slime Goo', 'chance': 0.7, 'min': 1, 'max': 3}],
    'Goblin':    [{'item': 'Broken Tooth', 'chance': 0.5, 'min': 1, 'max': 1}],
    'Orc':       [{'item': 'Orc Skin', 'chance': 0.4, 'min': 1, 'max': 1}],
    'Dragon':    [{'item': 'Dragon Scale', 'chance': 1.0, 'min': 1, 'max': 2}],
    'Troll':     [{'item': 'Troll Hide', 'chance': 1.0, 'min': 1, 'max': 2}],
    'Spider Queen': [{'item': 'Spider Silk', 'chance': 1.0, 'min': 2, 'max': 4}],
    'Spiderling':   [{'item': 'Spider Silk', 'chance': 0.3, 'min': 1, 'max': 1}],
    
    # --- SWAMP ENEMIES ---
    'Bog Leech': [
        {'item': 'Slime Goo', 'chance': 0.5, 'min': 1, 'max': 2},
        {'item': 'Vortex Residue', 'chance': 0.1, 'min': 1, 'max': 1} # Rare drop
    ],
    'Giant Frog': [
        {'item': 'Nightcap Fungus', 'chance': 0.4, 'min': 1, 'max': 2},
        {'item': 'Slime Goo', 'chance': 0.6, 'min': 1, 'max': 2}
    ],
    
    # --- RAT KING LOOT ---
    'Rat King': [
        # Unique Gear (Arpoo yhden näistä 100% varmuudella)
        {'one_of': ['Rat Poison Sword', 'Rat Poison Bow', 'Rat Poison Staff', 'Rat King Shield'], 'chance': 1.0, 'min': 1, 'max': 1},
        {'item': 'Rat Fang', 'chance': 1.0, 'min': 2, 'max': 5},
        {'item': 'Toxic Sludge', 'chance': 1.0, 'min': 1, 'max': 3},
        {'item': 'Sewer Moss', 'chance': 0.8, 'min': 1, 'max': 3},
        {'item': 'Plague Bone', 'chance': 0.5, 'min': 1, 'max': 2},
        {'item': 'King\'s Fur', 'chance': 1.0, 'min': 1, 'max': 1},
    ]
}

# --- BLUEPRINTS (Crafting) ---
# type: 'weapon', 'armor', 'helmet', 'shield', 'usable'
BLUEPRINTS = {
    # WEAPONS
    # --- IRON SERIES (Seppä: kaivoksen rautaharkoista) ---
    'Iron Sword': {
        'type': 'weapon',
        'desc': 'A standard soldier\'s blade. Forged from mine iron.',
        'cost': 25,
        'mats': {'Iron Bar': 2, 'Swamp Wood': 1}
    },
    'Iron Axe': {
        'type': 'weapon',
        'desc': 'A heavy woodsman\'s axe, reforged for war.',
        'cost': 25,
        'mats': {'Iron Bar': 2, 'Swamp Wood': 1}
    },
    'Iron Mace': {
        'type': 'weapon',
        'desc': 'Crushes armor and bone alike.',
        'cost': 25,
        'mats': {'Iron Bar': 3}
    },
    'Bent Spear': {
        'type': 'weapon',
        'desc': 'Long reach, slightly crooked shaft.',
        'cost': 20,
        'mats': {'Iron Bar': 1, 'Swamp Wood': 2}
    },
    'Iron Dagger': {
        'type': 'weapon',
        'desc': 'Quick, light and easy to hide.',
        'cost': 15,
        'mats': {'Iron Bar': 1}
    },
    'Light Crossbow': {
        'type': 'weapon',
        'desc': 'Slow to load, hits like a mule.',
        'cost': 30,
        'mats': {'Iron Bar': 2, 'Swamp Wood': 2}
    },
    'Rat Poison Sword': {
        'type': 'weapon',
        'desc': 'Drips with deadly toxin.',
        'cost': 450,
        'mats': {'Rat Fang': 2, 'Toxic Sludge': 1}
    },
    'Rat Poison Bow': {
        'type': 'weapon',
        'desc': 'Arrows coated in sewer sludge.',
        'cost': 450,
        'mats': {'Rat Fang': 2, 'Sewer Moss': 1}
    },
    'Rat Poison Staff': {
        'type': 'weapon',
        'desc': 'Channels toxic fumes.',
        'cost': 450,
        'mats': {'Plague Bone': 1, 'Toxic Sludge': 1}
    },
    
    # SHIELDS
    'Wooden Shield': {
        'type': 'shield',
        'desc': 'Blocks basic attacks',
        'cost': 50,
        'mats': {'Slime Goo': 2}
    },
    'Rat King Shield': {
        'type': 'shield',
        'desc': 'Heavy shield from sewer scrap.',
        'cost': 600,
        'mats': {'King\'s Fur': 1, 'Rat Fang': 5}
    },
    
    # --- SCRAP SERIES (Blacksmith) ---
    'Scrap Sword': {
        'type': 'weapon',
        'desc': 'A crude blade made from scrap metal.',
        'cost': 25,
        'mats': {'Scrap Metal Bar': 2, 'Swamp Wood': 1}
    },
    'Scrap Axe': {
        'type': 'weapon',
        'desc': 'Heavy scrap metal attached to a handle.',
        'cost': 25,
        'mats': {'Scrap Metal Bar': 2, 'Swamp Wood': 1}
    },
    'Scrap Mace': {
        'type': 'weapon',
        'desc': 'A lump of scrap metal on a stick.',
        'cost': 25,
        'mats': {'Scrap Metal Bar': 3, 'Swamp Wood': 1}
    },
    'Scrap Dagger': {
        'type': 'weapon',
        'desc': 'A sharp shard of scrap metal.',
        'cost': 20,
        'mats': {'Scrap Metal Bar': 1, 'Swamp Wood': 1}
    },
    'Scrap Spear': {
        'type': 'weapon',
        'desc': 'Pointy scrap metal on a long pole.',
        'cost': 25,
        'mats': {'Scrap Metal Bar': 2, 'Swamp Wood': 2}
    },
    'Scrap Shield': {
        'type': 'shield',
        'desc': 'A plate of scrap metal with a handle.',
        'cost': 25,
        'mats': {'Scrap Metal Bar': 2, 'Swamp Wood': 1}
    },
    'Scrap Bow': {
        'type': 'weapon',
        'desc': 'Reinforced bow.',
        'cost': 30,
        'mats': {'Scrap Metal Bar': 1, 'Swamp Wood': 2}
    },
    'Scrap Crossbow': {
        'type': 'weapon',
        'desc': 'Mechanical shooter.',
        'cost': 35,
        'mats': {'Scrap Metal Bar': 2, 'Swamp Wood': 2}
    },
    'Scrap Staff': {
        'type': 'weapon',
        'desc': 'Conductive pole.',
        'cost': 30,
        'mats': {'Scrap Metal Bar': 1, 'Swamp Wood': 2}
    },
    'Scrap Book': {
        'type': 'weapon',
        'desc': 'Metal bound tome.',
        'cost': 30,
        'mats': {'Scrap Metal Bar': 1, 'Swamp Wood': 1, 'Rat Tail': 2}
    },

    # --- WEAK SERIES (Blacksmith) ---
    'Weak Sword': {
        'type': 'weapon',
        'desc': 'A basic sword, better than scrap.',
        'cost': 50,
        'mats': {'Iron Bar': 2, 'Swamp Wood': 1}
    },
    'Weak Axe': {
        'type': 'weapon',
        'desc': 'A standard hand-axe.',
        'cost': 50,
        'mats': {'Iron Bar': 2, 'Swamp Wood': 1}
    },
    'Weak Mace': {
        'type': 'weapon',
        'desc': 'A simple mace with an iron head.',
        'cost': 50,
        'mats': {'Iron Bar': 3, 'Swamp Wood': 1}
    },
    'Weak Dagger': {
        'type': 'weapon',
        'desc': 'A sharp iron dagger.',
        'cost': 40,
        'mats': {'Iron Bar': 1, 'Swamp Wood': 1}
    },
    'Weak Spear': {
        'type': 'weapon',
        'desc': 'A long pole with an iron tip.',
        'cost': 50,
        'mats': {'Iron Bar': 1, 'Swamp Wood': 2}
    },
    'Weak Shield': {
        'type': 'shield',
        'desc': 'A simple shield reinforced with iron.',
        'cost': 50,
        'mats': {'Iron Bar': 2, 'Swamp Wood': 2}
    }
}

# --- FALLBACK STATS (Jos item-luokkaa ei löydy) ---
NEW_GEAR_STATS = {
    'Rusty Sword': {'damage': 8, 'speed_penalty': 0.1, 'range': 40, 'type': 'melee'},
    'Bone Club':   {'damage': 12, 'speed_penalty': 0.2, 'range': 45, 'type': 'melee'},
}