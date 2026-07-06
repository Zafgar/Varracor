# reputation/reputation_data.py
from settings import GOLD_COLOR, RED, GREEN, WHITE, BLUE

# Määritellään tasot (Pisteet -> Titteli)
REP_RANKS = [
    (-5000, "Hated"),
    (-1000, "Suspicious"),
    (0,     "Neutral"),
    (1000,  "Recognized"),
    (3000,  "Friendly"),
    (6000,  "Respected"),
    (9000,  "Exalted"),
    (10000, "Legendary")
]

def get_rank_title(score):
    title = "Unknown"
    for threshold, t in REP_RANKS:
        if score >= threshold:
            title = t
        else:
            break
    return title

# Faktioiden data kategorioittain
REPUTATION_FACTIONS = {
    "GENERAL": {
        "label": "General Standing",
        "desc": "Your overall renown in Varrakor.",
        "factions": {
            "global": {
                "name": "Global Fame",
                "desc": "Your total accumulated fame. Determines your League eligibility and general respect.",
                "color": GOLD_COLOR
            }
        }
    },
    "REALMS": {
        "label": "The Three Realms",
        "desc": "Political power that unlocks elite sponsors and schools.",
        "factions": {
            "crown": {
                "name": "The Crown Dominion",
                "desc": "Humans. Values order, trade protection, and law. Unlocks Holy & Manipulation schools.",
                "color": (100, 150, 255) # Royal Blue
            },
            "kharak": {
                "name": "Horned Throne of Kharak",
                "desc": "Minotaurs. Values endurance, reliability, and warfront duty. Unlocks Necromancy school.",
                "color": (200, 80, 40) # Brick Red
            },
            "lupine": {
                "name": "The Lupine Wardens",
                "desc": "Werewolves. Values nature protection and cleansing taint. Unlocks Druidism school.",
                "color": (80, 180, 80) # Forest Green
            }
        }
    },
    "SCHOOLS": {
        "label": "Schools of Magic",
        "desc": "Academic standing required to learn Tier 3+ spells.",
        "factions": {
            "prism": {
                "name": "The Prism Collegium",
                "desc": "Pure Magic. Neutral researchers of the Vortex. Values data and fundamentals.",
                "color": (200, 100, 255) # Purple
            },
            "radiant": {
                "name": "The Radiant Synod",
                "desc": "Holy Magic. Values moral purity and destroying the undead.",
                "color": (255, 255, 150) # Light Yellow
            },
            "ashen": {
                "name": "The Ashen Ossuary",
                "desc": "Necromancy. Values discipline over death. Located in Kharak/Sunscar.",
                "color": (100, 100, 100) # Ash Grey
            },
            "verdant": {
                "name": "The Verdant Covenant",
                "desc": "Druidism. Values ecological balance. Located in Wyrdwood.",
                "color": (50, 200, 100) # Bright Green
            },
            "argent": {
                "name": "The Argent Veil",
                "desc": "Manipulation. Values secrecy and leverage. Dangerous to deal with.",
                "color": (180, 180, 200) # Silver
            }
        }
    },
    "ARENA": {
        "label": "Arena Circuit",
        "desc": "Standing with managers determines match quality and pay.",
        "factions": {
            "mudhand": {
                "name": "Bram 'Mudhand' Carrow",
                "desc": "Tier 0 Manager. Values open routes in Muckford and rookies who survive the bog.",
                "color": (160, 140, 100) # Mud
            },
            "sera": {
                "name": "Sera Quench (T1)",
                "desc": "Values showmanship and marketability. 'Make yourself a product.'",
                "color": (255, 100, 150) # Hot Pink
            },
            "vessik": {
                "name": "Vessik 'Coincroak' (T2)",
                "desc": "Values betting potential and profit.",
                "color": GOLD_COLOR
            },
            "caelith": {
                "name": "Lord Caelith Vaelor (T3)",
                "desc": "Values skill, elegance, and technique. Hates brute force.",
                "color": (100, 200, 255) # Cyan
            },
            "hessa": {
                "name": "Hessa Ironhorn (T4)",
                "desc": "Values honor and fair play. Hates match-fixing.",
                "color": (200, 50, 50) # Red
            }
        }
    },
    "NEUTRAL": {
        "label": "Neutral & Special",
        "desc": "Powers operating outside the realms.",
        "factions": {
            "highstone": {
                "name": "Highstone Sanctum",
                "desc": "The highest authority. Required for Tier 5 and legendary Vortex ops.",
                "color": WHITE
            },
            "hamo": {
                "name": "Hamo (Bounty Broker)",
                "desc": "Gatekeeper to high-value boss hunts. Values reliable kills.",
                "color": (255, 165, 0) # Orange
            },
            "shanty": {
                "name": "The Shanty Consortium",
                "desc": "Muckford merchants and scavengers. Values open trade routes and scrap.",
                "color": (180, 180, 180)
            },
            "lumen": {
                "name": "Saint Lumen Hospice",
                "desc": "Sister-Medic Rhea Ashford. Values disease prevention and cleansing the taint.",
                "color": (200, 255, 255) # Pale Cyan
            }
        }
    },
    "INFAMY": {
        "label": "The Underworld",
        "desc": "Criminal standing. Closes official doors, opens illegal ones.",
        "factions": {
            "gutter": {
                "name": "The Gutter Ledger",
                "desc": "Tracks crimes and unpaid debts. High standing here means you are a trusted criminal.",
                "color": (150, 50, 50) # Dark Red
            }
        }
    }
}
