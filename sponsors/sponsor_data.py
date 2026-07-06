# sponsors/sponsor_data.py

TIER_0_NAME = "Tier 0: Rookie Dust Circuit"
MANAGER_NAME = "Bram 'Mudhand' Carrow"

SPONSORS = {
    "shanty": {
        "name": "The Shanty Consortium",
        "location": "Muckford",
        "type": "Local Backers",
        "desc": "A practical union of Muckford's repair shops, innkeepers, and small traders trying to survive the daily grind of the scrap city.",
        "goal": "Safe streets. They want to reduce crime and control the Muckford Rat-Armies.",
        "benefits": [
            "Basic Stipend: Covers food & lodging.",
            "Win Bonus: Small gold bonus for arena victories.",
            "Access: Muckford services."
        ],
        "politics": "Neutral. Independent survivors with no strong ties to the Crown Dominion.",
        "req_rep": 0,
        "color": (160, 140, 100) # Muddy brown/gold
    },
    "saffron": {
        "name": "Saffron Waterbond",
        "location": "Saffron Oasis (Sunscar Expanse)",
        "type": "Merchant Guild",
        "desc": "Guild of water merchants and well-keepers. In the desert, they control the most valuable resource: water.",
        "goal": "Secure trade routes. Eliminate Drownfoam monsters and ghouls threatening caravans.",
        "benefits": [
            "Water Reserves: Critical for desert operations.",
            "Logistics: Caravan support across the Sunscar Expanse."
        ],
        "politics": "Kharak-aligned (Minotaurs) for protection, but business comes first.",
        "req_rep": 1000,
        "color": (220, 180, 60) # Saffron yellow
    },
    "vinehollow": {
        "name": "Vinehollow Cureleaf Circle",
        "location": "Vinehollow (Wyrdwood Border)",
        "type": "Herbalist Circle",
        "desc": "A circle of herbalists and antidote brewers living on the edge of the jungle.",
        "goal": "Research & Defense. They need jungle samples and protection against spore/bug-fronts.",
        "benefits": [
            "Medical Discounts: Cheaper antidotes.",
            "Bounties: Bonus gold for rare jungle samples."
        ],
        "politics": "Sympathetic to Lupine Wardens (Werewolves), respecting nature's bounty.",
        "req_rep": 1000,
        "color": (100, 180, 100) # Herbal green
    }
}
