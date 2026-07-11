"""Material-focused village tasks and future regional contract templates.

Starter contracts are installed into the current Muckford task board. Future
contracts document intended progression and can be enabled when their regions,
NPCs and turn-in locations exist.
"""

ACTIVE_MATERIAL_TASKS = [
    {
        "id": "mud_furnace_fuel",
        "title": "Fuel for the Mud Furnace",
        "giver": "Notice Board",
        "summary": "Gather 6 Coal so Muckford's Smeltery can keep working.",
        "deed_text": "kept Muckford's furnace burning through a fuel shortage",
        "rep_req": 0,
        "recommended_level": (1, 5),
        "material_family": "Metals, Ores & Smithing",
        "stages": [
            {"kind": "talk",
             "text": "Furnace contract: six sacks of usable coal. Wet soot does not count."},
            {"kind": "collect", "item": "Coal", "count": 6,
             "hint": "Coal can be found in scrap piles, mines or bought from suppliers."},
        ],
        "rewards": {"gold": 28, "reputation": 4, "xp": 12,
                    "material": {"Iron Ore": 2}},
    },
    {
        "id": "fiber_for_the_cots",
        "title": "Fiber for the Cots",
        "giver": "Sister-Medic Rhea Ashford",
        "summary": "Bring 8 Plant Fiber for bandages and replacement bedding.",
        "deed_text": "supplied clean fiber for the hospice cots",
        "rep_req": 0,
        "recommended_level": (1, 6),
        "material_family": "Woods, Fibers & Bindings",
        "stages": [
            {"kind": "talk",
             "text": "We can boil field fiber clean. Bring eight bundles and I can keep wounds out of the mud."},
            {"kind": "collect", "item": "Plant Fiber", "count": 8,
             "hint": "Harvesting fields can yield spare Plant Fiber."},
        ],
        "rewards": {"gold": 24, "reputation": 5, "xp": 10,
                    "material": {"Bandage Roll": 2}},
    },
    {
        "id": "proper_iron_batch",
        "title": "A Proper Iron Batch",
        "giver": "Notice Board",
        "summary": "Collect 5 Iron Ore for a supervised Smeltery batch.",
        "deed_text": "delivered the ore for Muckford's first proper iron batch",
        "rep_req": 5,
        "recommended_level": (4, 10),
        "material_family": "Metals, Ores & Smithing",
        "stages": [
            {"kind": "talk",
             "text": "The smith wants ore, not rust flakes. Five pieces of Iron Ore, clean enough to weigh."},
            {"kind": "collect", "item": "Iron Ore", "count": 5,
             "hint": "Mine Iron Ore from low-level ore nodes."},
        ],
        "rewards": {"gold": 40, "reputation": 6, "xp": 18,
                    "material": {"Coal": 2, "Iron Ingot": 1}},
    },
    {
        "id": "bitterleaf_standard",
        "title": "The Bitterleaf Standard",
        "giver": "Sister-Medic Rhea Ashford",
        "summary": "Gather 5 Bitterleaf so Rhea can standardize field tonics.",
        "deed_text": "helped Rhea standardize Muckford's Bitterleaf medicine",
        "rep_req": 3,
        "recommended_level": (1, 8),
        "material_family": "Herbs, Alchemy & Potions",
        "stages": [
            {"kind": "talk",
             "text": "Five healthy Bitterleaf plants. Not Bogwort, not green weeds, and not anything Hamo names after smelling it."},
            {"kind": "collect", "item": "Bitterleaf", "count": 5,
             "hint": "Bitterleaf grows in Muckford's herb plots."},
        ],
        "rewards": {"gold": 32, "reputation": 6, "xp": 14,
                    "material": {"Resin": 2}},
    },
    {
        "id": "nightcap_warning",
        "title": "Nightcap Warning",
        "giver": "Sister-Medic Rhea Ashford",
        "summary": "Collect 3 Nightcap Fungus for an antidote reference batch.",
        "deed_text": "brought Rhea a safe Nightcap sample before swamp brewers poisoned anyone",
        "rep_req": 12,
        "recommended_level": (6, 15),
        "material_family": "Herbs, Alchemy & Potions",
        "stages": [
            {"kind": "talk",
             "text": "Nightcap can cure or kill. Bring three intact caps before the tavern brewers buy them first."},
            {"kind": "collect", "item": "Nightcap Fungus", "count": 3,
             "hint": "Giant frogs and wet cave logs may yield Nightcap Fungus."},
        ],
        "rewards": {"gold": 55, "reputation": 8, "xp": 24,
                    "material": {"Focus Powder": 1}},
    },
    {
        "id": "ink_and_oaths",
        "title": "Ink and Oaths",
        "giver": "Hamo",
        "summary": "Acquire parchment and seals for a new bounty ledger.",
        "deed_text": "supplied Hamo's first properly sealed bounty ledger",
        "rep_req": 15,
        "recommended_level": (6, 15),
        "material_family": "Scrolls & Spell Components",
        "stages": [
            {"kind": "talk",
             "text": "Paper tears. Promises tear faster. Bring four Parchment Sheets and two Wax Seals."},
            {"kind": "collect", "item": "Parchment Sheet", "count": 4,
             "hint": "Muckford's market keeps basic scribing supplies."},
            {"kind": "collect", "item": "Wax Seal", "count": 2,
             "hint": "Wax Seals can be bought from contract stalls."},
        ],
        "rewards": {"gold": 62, "reputation": 7, "xp": 22,
                    "material": {"Arcane Dust": 1}},
    },
]


# These templates already name their materials, regions and intended reward
# logic. They are deliberately not injected into Muckford until the matching
# region and giver exist.
FUTURE_MATERIAL_CONTRACTS = [
    {
        "id": "blacksteel_tempering_contract",
        "region": "Rivet Row / Rattlebridge",
        "recommended_level": (10, 15),
        "materials": {"Blacksteel Ore": 5, "Tempering Flux": 2},
        "reward_materials": {"Blacksteel Ingot": 2},
        "lore": "A forge-guild trial proving the team can supply and protect a controlled Blacksteel batch.",
    },
    {
        "id": "wyrdwood_binding_contract",
        "region": "Timbercross / Wyrdwood",
        "recommended_level": (6, 20),
        "materials": {"Oakwood": 4, "Refined Binding Kit": 2,
                      "Ironbark": 2, "Moonwillow": 1},
        "reward_materials": {"Elderroot Fiber": 1},
        "lore": "Wardens test whether outsiders can harvest without damaging living groves.",
    },
    {
        "id": "tannery_monster_contract",
        "region": "Regional Tannery",
        "recommended_level": (6, 25),
        "materials": {"Tanned Hide": 4, "Leather": 3, "Direhide": 2,
                      "Trollbone Plating": 1, "Drake Scale": 1},
        "reward_materials": {"Refined Binding Kit": 2},
        "lore": "A staged leatherworker commission that introduces increasingly dangerous monster materials.",
    },
    {
        "id": "stormsilver_grounding_contract",
        "region": "Aegis Peaks",
        "recommended_level": (16, 20),
        "materials": {"Stormsilver Ore": 4, "Focus Powder": 2},
        "reward_materials": {"Stormsilver Ingot": 1,
                             "Focus Crystal Shard": 1},
        "lore": "Peak smiths require the ore to be transported under grounding chains during active storms.",
    },
    {
        "id": "sun_gold_charter_contract",
        "region": "Crown Dominion",
        "recommended_level": (21, 25),
        "materials": {"Sun-Gold Ore": 3, "Sanctified Ember": 1},
        "reward_materials": {"Sun-Gold Ingot": 1,
                             "Silver Filigree Wire": 2},
        "lore": "A licensed Crown commission where paperwork is as dangerous as the guarded ore.",
    },
    {
        "id": "grave_lotus_ossuary_contract",
        "region": "Ashen Ossuary",
        "recommended_level": (16, 25),
        "materials": {"Grave-Lotus": 3, "Soul Ash": 2},
        "reward_materials": {"Rune Plate": 1},
        "lore": "Zharok's mortarchs demand exact provenance for every death-touched reagent.",
    },
    {
        "id": "prism_focus_contract",
        "region": "Prism Collegium",
        "recommended_level": (10, 25),
        "materials": {"Arcane Dust": 4, "Mirror Dust": 2,
                      "Silver Filigree Wire": 2, "Focus Crystal Shard": 1,
                      "Spell Focus Bead": 2, "Arcane Ink": 2},
        "reward_materials": {"Rune Plate": 1},
        "lore": "A neutral-magic examination covering trinkets, inks and stable spell focus construction.",
    },
    {
        "id": "outer_shatterbelt_samples",
        "region": "Outer Shatterbelt",
        "recommended_level": (26, 30),
        "materials": {"Void-Iron": 2, "Abyssal Chitin": 2,
                      "Vortex Residue": 1},
        "reward_materials": {"Seal-Lacquer": 1},
        "lore": "A quarantine contract: every sample must arrive sealed and every carrier examined for Taint.",
    },
    {
        "id": "echo_upgrade_contract",
        "region": "Abyssal Echo hunting grounds",
        "recommended_level": (18, 30),
        "materials": {"Echo Shard": 3, "Moondew Petals": 2},
        "reward_materials": {"Seal-Lacquer": 1},
        "lore": "An enchanter studies whether lunar alchemy can quiet the repeating will inside Echo Shards.",
    },
    {
        "id": "highstone_artifact_charter",
        "region": "Highstone Sanctum / The Eye",
        "recommended_level": (30, None),
        "materials": {"Heartcore Adamant": 1, "Echo Heart": 1,
                      "Seal-Lacquer": 2},
        "reward_materials": {"Charter Seal Token": 1},
        "lore": "Arkon's final legal and ritual process before a Mythic artifact may be forged.",
    },
]


def get_active_material_tasks():
    return [dict(task) for task in ACTIVE_MATERIAL_TASKS]


def get_future_material_contracts():
    return [dict(task) for task in FUTURE_MATERIAL_CONTRACTS]
