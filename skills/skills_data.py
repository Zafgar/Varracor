# skills/skills_data.py

SKILL_TREE = {
    # --- GENERIC OFFENSE ---
    "power_shot": {
        "name": "Power Shot",
        "desc": "Next basic attack deals 3x damage and +60% range (if your AI/logic uses it).",
        "cost": 1,
        "requires": [],
        "pos": (260, 140),
        "branch": "Offense",
        "effects": {"range_bonus": 60}
    },
    "rapid_strikes": {
        "name": "Rapid Strikes",
        "desc": "+10% attack speed.",
        "cost": 1,
        "requires": ["power_shot"],
        "pos": (260, 260),
        "branch": "Offense",
        "effects": {"cooldown_mult": 0.9}
    },
    "executioner": {
        "name": "Executioner",
        "desc": "+15% damage vs targets below 30% HP.",
        "cost": 1,
        "requires": ["rapid_strikes"],
        "pos": (260, 380),
        "branch": "Offense",
        "effects": {"executioner": True}
    },

    # --- GENERIC DEFENSE ---
    "iron_skin": {
        "name": "Iron Skin",
        "desc": "+2 defense.",
        "cost": 1,
        "requires": [],
        "pos": (520, 140),
        "branch": "Defense",
        "effects": {"defense": 2}
    },
    "second_wind": {
        "name": "Second Wind",
        "desc": "When dropping below 30% HP, heal 20 HP (once per battle).",
        "cost": 1,
        "requires": ["iron_skin"],
        "pos": (520, 260),
        "branch": "Defense",
        "effects": {"second_wind": True}
    },
    "unyielding": {
        "name": "Unyielding",
        "desc": "+20 max HP.",
        "cost": 1,
        "requires": ["second_wind"],
        "pos": (520, 380),
        "branch": "Defense",
        "effects": {"max_hp": 20}
    },

    # --- GENERIC UTILITY ---
    "mana_flow": {
        "name": "Mana Flow",
        "desc": "+10 max mana.",
        "cost": 1,
        "requires": [],
        "pos": (780, 140),
        "branch": "Utility",
        "effects": {"max_mana": 10}
    },
    "quick_step": {
        "name": "Quick Step",
        "desc": "+5% move speed.",
        "cost": 1,
        "requires": ["mana_flow"],
        "pos": (780, 260),
        "branch": "Utility",
        "effects": {"speed_mult": 1.05}
    },
    "focus": {
        "name": "Focus",
        "desc": "-5% cooldown multiplier.",
        "cost": 1,
        "requires": ["quick_step"],
        "pos": (780, 380),
        "branch": "Utility",
        "effects": {"cooldown_mult": 0.95}
    },

    # --- DEX TREE (New) ---
    "dex_agility": {
        "name": "Agility",
        "desc": "+5 Dexterity.",
        "cost": 1,
        "requires": [],
        "pos": (1040, 140),
        "branch": "Dexterity",
        "effects": {"dex": 5}
    },
    "dex_skirmisher": {
        "name": "Skirmisher",
        "desc": "Unlock Medium Armor & +5% Speed.",
        "cost": 1,
        "requires": ["dex_agility"],
        "pos": (1040, 240),
        "branch": "Dexterity",
        "effects": {"armor_prof": ["medium"], "speed_mult": 1.05}
    },
    "dex_ranger": {
        "name": "Ranger",
        "desc": "Unlock Bows & +40 Range.",
        "cost": 1,
        "requires": ["dex_agility"],
        "pos": (970, 260),
        "branch": "Dexterity",
        "effects": {"weapon_prof": ["bow", "crossbow"], "range_bonus": 40}
    },
    "dex_steady_draw": {
        "name": "Steady Draw",
        "desc": "Melee hits no longer stagger your bow draw. -50% draw stamina.",
        "cost": 2,
        "requires": ["dex_ranger"],
        "pos": (900, 380),
        "branch": "Dexterity",
        "effects": {"steady_draw": True}
    },
    "dex_sniper": {
        "name": "Sniper",
        "desc": "+10% Crit & Double Shot Chance.",
        "cost": 2,
        "requires": ["dex_ranger"],
        "pos": (970, 380),
        "branch": "Dexterity",
        "effects": {"crit_chance": 0.10, "dual_shot_chance": 0.15}
    },
    "dex_deadeye": {
        "name": "Deadeye",
        "desc": "Massive Range & Crit.",
        "cost": 3,
        "requires": ["dex_sniper"],
        "pos": (970, 500),
        "branch": "Dexterity",
        "effects": {"range_bonus": 50, "crit_chance": 0.15}
    },
    "dex_rogue": {
        "name": "Rogue",
        "desc": "Unlock Daggers & +10% Speed.",
        "cost": 1,
        "requires": ["dex_agility"],
        "pos": (1110, 260),
        "branch": "Dexterity",
        "effects": {"weapon_prof": ["dagger"], "speed_mult": 1.10}
    },
    "dex_assassin": {
        "name": "Assassin",
        "desc": "Dual Wield & Executioner (Bonus vs low HP).",
        "cost": 2,
        "requires": ["dex_rogue"],
        "pos": (1110, 380),
        "branch": "Dexterity",
        "effects": {"can_dual_wield": True, "executioner": True}
    },
    "dex_phantom": {
        "name": "Phantom",
        "desc": "Extreme Speed & Dodge.",
        "cost": 3,
        "requires": ["dex_assassin"],
        "pos": (1110, 500),
        "branch": "Dexterity",
        "effects": {"speed_mult": 1.2, "defense": 2, "max_dashes": 1}
    },

    # --- STR TREE (New) ---
    "str_might": {
        "name": "Might",
        "desc": "+5 Strength.",
        "cost": 1,
        "requires": [],
        "pos": (0, 140),
        "branch": "Strength",
        "effects": {"str": 5}
    },
    "str_veteran": {
        "name": "Veteran",
        "desc": "Unlock Medium Armor, Spears & +30 HP.",
        "cost": 1,
        "requires": ["str_might"],
        "pos": (0, 220),
        "branch": "Strength",
        "effects": {"armor_prof": ["medium"], "weapon_prof": ["spear"], "max_hp": 30}
    },
    
    # Branch 1: Barbarian (Axes/Maces, Damage)
    "str_barbarian": {
        "name": "Barbarian",
        "desc": "Unlock Axes & Maces. +30 HP.",
        "cost": 1,
        "requires": ["str_might"],
        "pos": (-140, 260),
        "branch": "Strength",
        "effects": {"weapon_prof": ["axe", "mace"], "max_hp": 30}
    },
    "str_berserker": {
        "name": "Berserker",
        "desc": "+10 STR & 10% Faster Attacks.",
        "cost": 2,
        "requires": ["str_barbarian"],
        "pos": (-140, 380),
        "branch": "Strength",
        "effects": {"str": 10, "cooldown_mult": 0.9}
    },
    "str_warlord": {
        "name": "Warlord",
        "desc": "Massive Damage & HP.",
        "cost": 3,
        "requires": ["str_berserker"],
        "pos": (-140, 500),
        "branch": "Strength",
        "effects": {"str": 15, "max_hp": 50}
    },

    # Branch 2: Tank (Shields, Heavy Armor)
    "str_knight": {
        "name": "Knight",
        "desc": "Unlock Heavy Armor & Shields.",
        "cost": 1,
        "requires": ["str_veteran"],
        "pos": (0, 300),
        "branch": "Strength",
        "effects": {"armor_prof": ["heavy"], "weapon_prof": ["shield"]}
    },
    "str_shield_master": {
        "name": "Shield Master",
        "desc": "Shields are 25% more efficient.",
        "cost": 2,
        "requires": ["str_knight"],
        "pos": (-70, 380),
        "branch": "Strength",
        "effects": {"block_stamina_mult": 0.75}
    },
    "str_juggernaut": {
        "name": "Juggernaut",
        "desc": "Ignore Heavy Armor Speed Penalty & +20 HP.",
        "cost": 2,
        "requires": ["str_knight"],
        "pos": (0, 420),
        "branch": "Strength",
        "effects": {"ignore_armor_penalty": True, "max_hp": 20}
    },
    "str_colossus": {
        "name": "Colossus",
        "desc": "+5 Defense & +100 HP.",
        "cost": 3,
        "requires": ["str_juggernaut"],
        "pos": (0, 520),
        "branch": "Strength",
        "effects": {"defense": 5, "max_hp": 100}
    },

    # Branch 3: Fighter (Swords, Dual Wield)
    "str_fighter": {
        "name": "Fighter",
        "desc": "Unlock Swords. +5 STR.",
        "cost": 1,
        "requires": ["str_might"],
        "pos": (140, 260),
        "branch": "Strength",
        "effects": {"weapon_prof": ["sword"], "str": 5}
    },
    "str_dual_wield": {
        "name": "Dual Wield",
        "desc": "Can equip off-hand weapons. +5% Speed.",
        "cost": 2,
        "requires": ["str_fighter"],
        "pos": (140, 380),
        "branch": "Strength",
        "effects": {"can_dual_wield": True, "speed_mult": 1.05}
    },
    "str_weapon_master": {
        "name": "Weapon Master",
        "desc": "+10 STR & +10 DEX.",
        "cost": 3,
        "requires": ["str_dual_wield"],
        "pos": (140, 500),
        "branch": "Strength",
        "effects": {"str": 10, "dex": 10}
    },

    # --- INT TREE (Magic) ---
    "int_scholar": {
        "name": "Scholar",
        "desc": "+5 Intelligence.",
        "cost": 1,
        "requires": [],
        "pos": (520, 20),
        "branch": "Intelligence",
        "effects": {"int": 5}
    },
    
    # Side: Relics
    "int_relic_user": {
        "name": "Relic User",
        "desc": "Unlock Relics (Off-hand).",
        "cost": 1,
        "requires": ["int_scholar"],
        "pos": (640, -60),
        "branch": "Intelligence",
        "effects": {"weapon_prof": ["relic"], "mana_regen": 0.05}
    },
    "int_cleric": {
        "name": "Cleric",
        "desc": "Unlock Medium Armor & Healing Bonus.",
        "cost": 2,
        "requires": ["int_relic_user"],
        "pos": (640, -160),
        "branch": "Intelligence",
        "effects": {"armor_prof": ["medium"], "max_mana": 30}
    },

    # Side: Battlemage
    "int_battlemage": {
        "name": "Battlemage",
        "desc": "Unlock Medium Armor & Swords.",
        "cost": 2,
        "requires": ["int_scholar"],
        "pos": (400, -60),
        "branch": "Intelligence",
        "effects": {"armor_prof": ["medium"], "weapon_prof": ["sword"], "max_hp": 40}
    },

    "int_apprentice": {
        "name": "Apprentice",
        "desc": "Unlock Slot 1, Tier 1 Spells, Staves & Books.",
        "cost": 1,
        "requires": ["int_scholar"],
        "pos": (520, -100),
        "branch": "Intelligence",
        "effects": {"unlock_spell_slot": [1], "spell_tier": 1, "max_mana": 20, "weapon_prof": ["staff", "book"]}
    },
    "int_adept": {
        "name": "Adept",
        "desc": "Unlock Spell Slot 2 & Tier 2 Spells.",
        "cost": 2,
        "requires": ["int_apprentice"],
        "pos": (520, -220),
        "branch": "Intelligence",
        "effects": {"unlock_spell_slot": [2], "spell_tier": 2, "mana_regen": 0.05}
    },
    "int_invoker": {
        "name": "Invoker",
        "desc": "Unlock Spell Slot 3 & Tier 3 Spells.",
        "cost": 2,
        "requires": ["int_adept"],
        "pos": (520, -340),
        "branch": "Intelligence",
        "effects": {"unlock_spell_slot": [3], "spell_tier": 3, "max_mana": 40}
    },
    
    # Branch: Druid (Alternative at Tier 3)
    "int_druid_form": {
        "name": "Druid Form",
        "desc": "Unlock Shapeshift (Bear). +20 STR & HP.",
        "cost": 2,
        "requires": ["int_adept"],
        "pos": (660, -340),
        "branch": "Intelligence",
        "effects": {"shapeshift": "bear", "str": 20, "max_hp": 200}
    },
    
    # --- HIGH TIER MAGIC (4-8) ---
    "int_magus": {
        "name": "Magus",
        "desc": "Unlock Tier 4 Spells.",
        "cost": 2,
        "requires": ["int_invoker"],
        "pos": (520, -460),
        "branch": "Intelligence",
        "effects": {"spell_tier": 4, "int": 5}
    },
    "int_wizard": {
        "name": "Wizard",
        "desc": "Unlock Tier 5 Spells.",
        "cost": 2,
        "requires": ["int_magus"],
        "pos": (520, -580),
        "branch": "Intelligence",
        "effects": {"spell_tier": 5, "max_mana": 50}
    },
    "int_warlock": {
        "name": "Warlock",
        "desc": "Unlock Tier 6 Spells.",
        "cost": 3,
        "requires": ["int_wizard"],
        "pos": (520, -700),
        "branch": "Intelligence",
        "effects": {"spell_tier": 6, "mana_regen": 0.1}
    },
    "int_archmage": {
        "name": "Archmage",
        "desc": "Unlock Tier 7 Spells & +10 INT.",
        "cost": 3,
        "requires": ["int_warlock"],
        "pos": (520, -820),
        "branch": "Intelligence",
        "effects": {"spell_tier": 7, "int": 10}
    },
    "int_ascendant": {
        "name": "Ascendant",
        "desc": "Unlock Tier 8 Spells (Max).",
        "cost": 4,
        "requires": ["int_archmage"],
        "pos": (520, -1060),
        "branch": "Intelligence",
        "effects": {"spell_tier": 8, "max_mana": 200, "mana_regen": 0.2}
    },
}
