# skills/school_trees_data.py
"""Koulukohtaiset erikoistumispuut (lyhyet). Pelaajan suunnittelu:

- Necromancy: Summoner (montako/minkä tasoisia olentoja), Life Steal (varasta
  elämää itselle), Curses (kiroukset)
- Druidism: Shapeshift (muodonmuutos), Life (heal/HoT + vahinko), Control
  (esteet, slow/pysäytys, aluevaikutus)
- Holy: Pure Healing (elämä + suoja), Buffs (tiimin STR/INT/Stamina + vähennä
  vahinkoa)

Puut ovat LYHYITÄ: pisteitä on rajallisesti eikä kaikkea voi ottaa, ja koulut
sitovat hahmoa - yhden koulun valinta sulkee muut (exclusive_group). Efektit
kertyvät unit.school_effects-sanakirjaan, josta loitsut lukevat ne.

Jokainen entry-node vaatii int_apprentice (hahmon on osattava loitsia).
"""

# Efektit tallentuvat unit.school_effects[key] += arvo (paitsi flagit True).
SCHOOL_TREE = {
    # ================= NECROMANCY =================
    "necro_initiate": {
        "name": "Necro Initiate", "branch": "Necromancy", "school": "necromancy",
        "exclusive_group": "caster_school",
        "desc": "Commit to Necromancy. Opens the death paths.",
        "cost": 1, "requires": ["int_apprentice"], "pos": (1300, -260),
        "effects": {"school_necromancy": True},
    },
    # -- Summoner --
    "necro_summon_1": {
        "name": "Bind the Dead", "branch": "Necromancy", "school": "necromancy",
        "desc": "Raise one extra minion; summons are sturdier.",
        "cost": 1, "requires": ["necro_initiate"], "pos": (1200, -140),
        "effects": {"summon_max": 1},
    },
    "necro_summon_2": {
        "name": "Grave Legion", "branch": "Necromancy", "school": "necromancy",
        "desc": "+1 minion and summon higher-tier undead.",
        "cost": 2, "requires": ["necro_summon_1"], "pos": (1200, -20),
        "effects": {"summon_max": 1, "summon_tier": 1},
    },
    # -- Life Steal --
    "necro_steal_1": {
        "name": "Leech", "branch": "Necromancy", "school": "necromancy",
        "desc": "Your necrotic spells steal 15% of damage as health.",
        "cost": 1, "requires": ["necro_initiate"], "pos": (1300, -140),
        "effects": {"lifesteal_pct": 0.15},
    },
    "necro_steal_2": {
        "name": "Vampiric Grasp", "branch": "Necromancy", "school": "necromancy",
        "desc": "Life steal rises to 40% total.",
        "cost": 2, "requires": ["necro_steal_1"], "pos": (1300, -20),
        "effects": {"lifesteal_pct": 0.25},
    },
    # -- Curses --
    "necro_curse_1": {
        "name": "Hex", "branch": "Necromancy", "school": "necromancy",
        "desc": "Curses weaken the afflicted. +1 curse power.",
        "cost": 1, "requires": ["necro_initiate"], "pos": (1400, -140),
        "effects": {"curse_power": 1},
    },
    "necro_curse_2": {
        "name": "Doom", "branch": "Necromancy", "school": "necromancy",
        "desc": "Deepen the rot. +2 curse power.",
        "cost": 2, "requires": ["necro_curse_1"], "pos": (1400, -20),
        "effects": {"curse_power": 2},
    },

    # ================= DRUIDISM =================
    "druid_initiate": {
        "name": "Druid Initiate", "branch": "Druidism", "school": "druidism",
        "exclusive_group": "caster_school",
        "desc": "Commit to Druidism. Opens the wild paths.",
        "cost": 1, "requires": ["int_apprentice"], "pos": (1620, -260),
        "effects": {"school_druidism": True},
    },
    # -- Shapeshift --
    "druid_shift_1": {
        "name": "Beast Form", "branch": "Druidism", "school": "druidism",
        "desc": "Unlock one shapeshift form.",
        "cost": 1, "requires": ["druid_initiate"], "pos": (1520, -140),
        "effects": {"shapeshift_rank": 1},
    },
    "druid_shift_2": {
        "name": "Dire Form", "branch": "Druidism", "school": "druidism",
        "desc": "A mightier form with bonus stats.",
        "cost": 2, "requires": ["druid_shift_1"], "pos": (1520, -20),
        "effects": {"shapeshift_rank": 1},
    },
    # -- Life --
    "druid_life_1": {
        "name": "Rejuvenate", "branch": "Druidism", "school": "druidism",
        "desc": "Stronger heal-over-time. +1 HoT power.",
        "cost": 1, "requires": ["druid_initiate"], "pos": (1620, -140),
        "effects": {"hot_power": 1},
    },
    "druid_life_2": {
        "name": "Wild Bloom", "branch": "Druidism", "school": "druidism",
        "desc": "+2 HoT power and a nature damage spell.",
        "cost": 2, "requires": ["druid_life_1"], "pos": (1620, -20),
        "effects": {"hot_power": 2, "nature_damage": 1},
    },
    # -- Control --
    "druid_control_1": {
        "name": "Entangle", "branch": "Druidism", "school": "druidism",
        "desc": "Roots and slows. +1 control power.",
        "cost": 1, "requires": ["druid_initiate"], "pos": (1720, -140),
        "effects": {"control_power": 1},
    },
    "druid_control_2": {
        "name": "Wall of Thorns", "branch": "Druidism", "school": "druidism",
        "desc": "Raise barriers to shape the field. +2 control power.",
        "cost": 2, "requires": ["druid_control_1"], "pos": (1720, -20),
        "effects": {"control_power": 2},
    },

    # ================= HOLY =================
    "holy_initiate": {
        "name": "Holy Initiate", "branch": "Holy", "school": "holy",
        "exclusive_group": "caster_school",
        "desc": "Commit to the Radiant Synod. Opens the light paths.",
        "cost": 1, "requires": ["int_apprentice"], "pos": (1940, -260),
        "effects": {"school_holy": True},
    },
    # -- Pure Healing --
    "holy_heal_1": {
        "name": "Mend", "branch": "Holy", "school": "holy",
        "desc": "Stronger direct heals. +1 heal power.",
        "cost": 1, "requires": ["holy_initiate"], "pos": (1880, -140),
        "effects": {"heal_power": 1},
    },
    "holy_heal_2": {
        "name": "Sanctuary", "branch": "Holy", "school": "holy",
        "desc": "+2 heal power and shield your target.",
        "cost": 2, "requires": ["holy_heal_1"], "pos": (1880, -20),
        "effects": {"heal_power": 2, "holy_shield": 1},
    },
    # -- Buffs --
    "holy_buff_1": {
        "name": "Blessing", "branch": "Holy", "school": "holy",
        "desc": "Bless the team: +STR/INT/Stamina. +1 team buff.",
        "cost": 1, "requires": ["holy_initiate"], "pos": (2000, -140),
        "effects": {"team_buff": 1},
    },
    "holy_buff_2": {
        "name": "Aegis of Dawn", "branch": "Holy", "school": "holy",
        "desc": "+2 team buff and team-wide damage reduction.",
        "cost": 2, "requires": ["holy_buff_1"], "pos": (2000, -20),
        "effects": {"team_buff": 2, "team_damage_reduction": 1},
    },
}


def school_of(skill_id):
    return SCHOOL_TREE.get(skill_id, {}).get("school")


# Efektiavaimet jotka kertyvät unit.school_effects-sanakirjaan (numerot summautuvat,
# muut talletetaan True/arvo). Flag-avaimet alkavat "school_".
def is_school_node(skill_id):
    return skill_id in SCHOOL_TREE
