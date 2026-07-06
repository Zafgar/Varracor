# mission_data.py

# --- BOSS HUNTS ---
# Nyt vain yksi bossi, jotta testaus on helppoa.
BOSS_HUNTS = {
    "boss_rat_king": {
        "id": "boss_rat_king",
        "title": "The Rat King",
        "desc": "A massive rat is eating our supplies.",
        "arena": "Rat Sewer",
        # enemies-listaa ei tässä enää tarvita pakosti, koska mission.py hoitaa sen,
        # mutta pidetään se UI:n (Quest Menu) tiedoksi:
        "enemies": [("Rat King", 1), ("Giant Rat", 4)],
        "reward_gold": 500,
        "reward_item": "Rat Tail"
    }
}

# --- MONSTER HUNTS ---
# Järjestetty alueittain: Muckford, Saffron Oasis, Vinehollow
MONSTER_HUNTS = {
    "Muckford": [
        {
            "id": "hunt_muckford_city",
            "title": "Muckford City Defense",
            "desc": "Rat armies are swarming the streets. Protect the supply lines.",
            "arena": "Muckford", # Viittaa uuteen karttaan
            "enemies": [("Giant Rat", 10), ("Rat Rider", 3)],
            "reward_gold": 250,
            "reward_rep": 150,
            "rep_changes": {"shanty": 100, "mudhand": 50}
        },
        {
            "id": "hunt_rats",
            "title": "Sewer Rat Cull",
            "desc": "Aggressive rat armies are breaching the lower city. Burn them out.",
            "arena": "Rat Sewer",
            "enemies": [("Giant Rat", 6)],
            "reward_gold": 150,
            "reward_rep": 100
        },
        {
            "id": "hunt_crypt",
            "title": "Crypt of the Undead",
            "desc": "Grave-tide columns are rising from the ruins. Hold the line.",
            "arena": "Crypt",
            "enemies": [("Skeleton", 8), ("Zombie", 8), ("Skeleton Archer", 4)],
            "reward_gold": 400,
            # "reward_rep": 2500, <-- Poistettu yleinen
            "rep_changes": {      # <-- Kohdennettu maine
                "shanty": 150,    # Turvalliset reitit romunkerääjille
                "lumen": 150,     # Tautien torjunta
                "mudhand": 50,    # Areenamanagerin kunnioitus
                "radiant": 10     # Pieni huomio kirkolta
            }
        },
        {
            "id": "hunt_bog",
            "title": "Clear the Marshes",
            "desc": "Leeches and Corrupted Crows block the trade route.",
            "arena": "Bog",
            "enemies": [("Bog Leech", 10), ("Giant Frog", 2), ("Corrupted Crow", 5)],
            "reward_gold": 200,
            # "reward_rep": 150,  <-- Poistettu yleinen maine
            "rep_changes": {      # <-- Lisätty kohdennettu maine
                "mudhand": 50,    # Bram tykkää kun reitit auki
                "shanty": 75,     # Consortium saa romua
                "hamo": 25,       # Ammattimainen tappo
                "lumen": 25       # Vähemmän tauteja
            }
        },
        {
            "id": "hunt_ghouls",
            "title": "Feral Ghoul Defense",
            "desc": "Hungry dead are wandering towards the settlement lights.",
            "arena": "Crypt", # Käytetään Crypt-karttaa toistaiseksi
            "enemies": [("Zombie", 12)],
            "reward_gold": 250,
            "rep_changes": {
                "shanty": 100,
                "lumen": 100,
                "hamo": 50        # Hamo maksaa usein ghouleista
            }
        }
    ],
    "Saffron Oasis": [
        {
            "id": "hunt_scavengers",
            "title": "Dune Scavengers",
            "desc": "Small beasts are ambushing water caravans. Clear the route.",
            "arena": "Basic Arena", # Placeholder arena
            "enemies": [("Goblin", 8)], # Goblin toimii "Scavenger" korvikkeena
            "reward_gold": 300,
            "reward_rep": 200
        }
    ],
    "Vinehollow": [
        {
            "id": "hunt_thornlings",
            "title": "Thornling Clearing",
            "desc": "Living briars are choking the trade paths. Cut them down.",
            "arena": "Basic Arena", # Placeholder arena
            "enemies": [("Goblin", 10)], # Goblin toimii "Thornling" korvikkeena (pieni, nopea)
            "reward_gold": 350,
            "reward_rep": 250
        }
    ]
}

QUEST_DATA = []