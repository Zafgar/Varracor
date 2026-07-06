import random

# --- RODUT (Perustiedot) ---
RACES = {
    # Pelaajan rodut ja perusviholliset
    'Human':  {'hp_mult': 1.0, 'str_mult': 1.0, 'spd_mult': 1.0, 'defense': 0, 'resistance': 'None', 'weakness': 'None', 'desc': 'Basic'},
    'Orc':    {'hp_mult': 1.4, 'str_mult': 1.2, 'spd_mult': 0.8, 'defense': 1, 'resistance': 'Physical', 'weakness': 'Magic', 'desc': 'Tough'},
    'Elf':    {'hp_mult': 0.9, 'str_mult': 1.1, 'spd_mult': 1.3, 'defense': 0, 'resistance': 'Magic', 'weakness': 'Physical', 'desc': 'Fast'},
    'Dwarf':  {'hp_mult': 1.3, 'str_mult': 1.1, 'spd_mult': 0.7, 'defense': 3, 'resistance': 'Poison', 'weakness': 'Magic', 'desc': 'Sturdy'},
    'Undead': {'hp_mult': 1.5, 'str_mult': 0.9, 'spd_mult': 0.5, 'defense': 0, 'resistance': 'Ice', 'weakness': 'Fire', 'desc': 'Undying'},
    'Goblin': {'hp_mult': 0.6, 'str_mult': 0.8, 'spd_mult': 1.4, 'defense': 0, 'resistance': 'None', 'weakness': 'Physical', 'desc': 'Weak but fast'},
    'Troll':  {'hp_mult': 2.2, 'str_mult': 1.6, 'spd_mult': 0.7, 'defense': 2, 'resistance': 'Physical', 'weakness': 'Magic', 'desc': 'Boss'},


    # Boss Rodut
    'Dragon': {
        'hp_mult': 6.0,       # Todella paljon HP
        'str_mult': 2.0,      # Lyö kovaa
        'spd_mult': 0.8,
        'defense': 5,
        'resistance': 'Fire', # Immuuni tulelle
        'weakness': 'Ice',    # Heikko jäälle
        'desc': 'Boss'
    },
    'Giant': {
        'hp_mult': 5.0,
        'str_mult': 1.8,
        'spd_mult': 0.5,
        'defense': 8,         # Paksu nahka
        'resistance': 'Physical',
        'weakness': 'Poison',
        'desc': 'Boss'
    },
    'Fire Elemental': {
        'hp_mult': 1.0,
        'str_mult': 1.2,
        'spd_mult': 1.0,
        'defense': 2,
        'resistance': 'Fire',
        'weakness': 'Water',
        'desc': 'Elemental'
    }
}

# --- HIRVIÖLISTA (Monster Hunt moodia varten) ---
MONSTERS = {
    'Giant Rat':      {'tier': 1, 'type': 'Swarm', 'count': 5, 'arena': 'The Swamp'},
    'Slime':          {'tier': 1, 'type': 'Solo',  'arena': 'The Pit'},
    'Kobold Scout':   {'tier': 1, 'type': 'Swarm', 'count': 3, 'arena': 'The Ruins'},
    'Wolf Pack':      {'tier': 2, 'type': 'Swarm', 'count': 4, 'arena': 'The Pit'},
    'Giant Spider':   {'tier': 2, 'type': 'Solo',  'arena': 'The Ruins'}, 
    'Bandit Leader':  {'tier': 2, 'type': 'Solo',  'arena': 'The Bridge'},
    'Orc Warlord':    {'tier': 3, 'type': 'Solo',  'arena': 'The Pit'},
    'Goblin Army':    {'tier': 3, 'type': 'Swarm', 'count': 8, 'arena': 'The Ruins'},
    'Bear':           {'tier': 3, 'type': 'Solo',  'arena': 'The Swamp'},
    'Troll':          {'tier': 4, 'type': 'Solo',  'arena': 'The Bridge'}, 
    'Harpy Flock':    {'tier': 4, 'type': 'Swarm', 'count': 6, 'arena': 'The Pit'},
    'Basilisk':       {'tier': 4, 'type': 'Solo',  'arena': 'The Swamp'},
    'Minotaur':       {'tier': 5, 'type': 'Solo',  'arena': 'The Ruins'},
    'Vampire Lord':   {'tier': 5, 'type': 'Solo',  'arena': 'The Ruins'},
    'Magma Golem':    {'tier': 5, 'type': 'Solo',  'arena': 'Lava Lake'},
    'Hydra':          {'tier': 6, 'type': 'Solo',  'arena': 'The Swamp'},
    'Lich King':      {'tier': 6, 'type': 'Swarm', 'count': 4, 'arena': 'The Pit'},
    'Beholder':       {'tier': 6, 'type': 'Solo',  'arena': 'The Ruins'},
    'Ancient Dragon': {'tier': 7, 'type': 'Solo',  'arena': 'Lava Lake'},
    'Frost Giant':    {'tier': 7, 'type': 'Solo',  'arena': 'The Bridge'},
    'Demon Lord':     {'tier': 7, 'type': 'Solo',  'arena': 'Lava Lake'},
    'THE WORLD EATER':{'tier': 8, 'type': 'Solo',  'arena': 'The Pit'},
    'VOID GOD':       {'tier': 8, 'type': 'Solo',  'arena': 'The Ruins'},
    'CHRONOS':        {'tier': 8, 'type': 'Solo',  'arena': 'The Bridge'}
}

# --- NIMIGENERAATTORI ---
RACE_NAMES = {
    "Human": {
        "first": ["Alden", "Bretta", "Caden", "Dalia", "Ewan", "Fiora", "Gareth", "Hilda", "Ivar", "Jessa"],
        "last": ["Miller", "Smith", "Tanner", "Cooper", "Fletcher", "Wright", "Mason", "Carter", "Ward", "Baker"]
    },
    "Elf": {
        "first": ["Aelrindel", "Bryn", "Caelen", "Faen", "Galad", "Hael", "Idril", "Laer", "Mael", "Naer"],
        "last": ["Moonwhisper", "Starlight", "Sunfire", "Leafshade", "Windrunner", "Riverflow", "Nightbreeze", "Dawnseeker", "Starfall", "Woodsong"]
    },
    "Orc": {
        "first": ["Grog", "Hruk", "Karg", "Mog", "Nar", "Prug", "Rurg", "Thok", "Varg", "Zog"],
        "last": ["Bonecrusher", "Skullsplitter", "Ironhide", "Bloodfist", "Doomhammer", "Stormbringer", "Earthshaker", "Firecaller", "Deathdealer", "Warbringer"]
    },
    "Goblin": {
        "first": ["Zik", "Rix", "Tok", "Mik", "Nax", "Pox", "Vix", "Kax", "Lax", "Dax"],
        "last": ["Ratchewer", "Toebiter", "Shinbreaker", "Kneecapper", "Anklebiter", "Fingergnawer", "Nosepicker", "Earchewer", "Eyegouger", "Tonguebiter"]
    }
}

def get_random_name(race):
    if race not in RACE_NAMES:
        return "Unknown"
    f = random.choice(RACE_NAMES[race]["first"])
    l = random.choice(RACE_NAMES[race]["last"])
    return f"{f} {l}"