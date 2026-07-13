# systems/talents.py
"""Synnynnäiset lahjakkuudet: jokainen rekryttävä taistelija on uniikki.

Talentit arvotaan generoinnissa ja vaikuttavat kahta reittiä:
- perusstatit (STR/DEX/INT/HP/DEF) leivotaan base_attributes-sanakirjaan
  (tallentuu saveen sellaisenaan)
- erikoisefektit (stamina, nopeus, kriitti, vahingonvähennys, XP-kerroin)
  menevät unit.talent_effects-sanakirjaan jonka calculate_final_stats
  kuluttaa (serialisoidaan erikseen)

Pelaaja näkee talenttien NIMET aina ("Strong", "Gifted: Sword") -
tarkat numerot vaatii Commanderin Appraiser's Eye -taidon (insight).
"""

from __future__ import annotations

import random

# name: {desc (näkyy insightilla), base: {stat: +n}, effects: {...},
#        affinity: asegruppa, weight: yleisyys, cost: hintavaikutus}
TALENTS = {
    # --- FYYSISET LAHJAT ---
    "Strong": {"desc": "+2 STR", "base": {"str": 2}, "weight": 14, "cost": 40},
    "Agile": {"desc": "+2 DEX", "base": {"dex": 2}, "weight": 14, "cost": 40},
    "Keen Mind": {"desc": "+2 INT", "base": {"int": 2}, "weight": 10,
                  "cost": 40},
    "Ox Blood": {"desc": "+25 max HP", "base": {"max_hp": 25}, "weight": 10,
                 "cost": 45},
    "Iron Hide": {"desc": "+1 natural armor",
                  "effects": {"defense": 1}, "weight": 8, "cost": 50},
    "Thick Skin": {"desc": "-5% damage taken",
                   "effects": {"damage_reduction": 0.05}, "weight": 6,
                   "cost": 60},
    "Tireless": {"desc": "+20 max stamina",
                 "effects": {"max_stamina": 20}, "weight": 10, "cost": 45},
    "Fleet-Footed": {"desc": "+6% move speed",
                     "effects": {"speed_mult": 1.06}, "weight": 8, "cost": 50},
    "Eagle Eye": {"desc": "+4% crit chance",
                  "effects": {"crit_chance": 0.04}, "weight": 7, "cost": 55},
    "Quick Learner": {"desc": "+20% XP gained",
                      "effects": {"xp_mult": 1.20}, "weight": 5, "cost": 70},

    # --- ASELAHJAT (Gifted) ---
    "Gifted: Sword": {"desc": "+25% sword damage", "affinity": "sword",
                      "weight": 6, "cost": 60},
    "Gifted: Axe": {"desc": "+25% axe damage", "affinity": "axe",
                    "weight": 5, "cost": 60},
    "Gifted: Spear": {"desc": "+25% spear damage", "affinity": "spear",
                      "weight": 5, "cost": 60},
    "Gifted: Dagger": {"desc": "+25% dagger damage", "affinity": "dagger",
                       "weight": 4, "cost": 60},
    "Gifted: Mace": {"desc": "+25% mace damage", "affinity": "mace",
                     "weight": 4, "cost": 60},
    "Gifted: Bow": {"desc": "+25% bow damage", "affinity": "bow",
                    "weight": 5, "cost": 60},
    "Gifted: Crossbow": {"desc": "+25% crossbow damage",
                         "affinity": "crossbow", "weight": 3, "cost": 60},
    "Gifted: Staff": {"desc": "+25% staff damage", "affinity": "staff",
                      "weight": 4, "cost": 60},

    # --- HARVINAISET ---
    "Born Champion": {"desc": "+1 all stats, +10 HP",
                      "base": {"str": 1, "dex": 1, "int": 1, "max_hp": 10},
                      "weight": 1, "cost": 150},
}

# Heikkoudet: tuovat väriä ja laskevat hintaa
QUIRKS = {
    "Old Wound": {"desc": "-15 max HP", "base": {"max_hp": -15}, "cost": -25},
    "Drunkard": {"desc": "-15 max stamina",
                 "effects": {"max_stamina": -15}, "cost": -20},
    "Cowardly": {"desc": "-1 DEX", "base": {"dex": -1}, "cost": -20},
    "Slow Learner": {"desc": "-15% XP gained",
                     "effects": {"xp_mult": 0.85}, "cost": -30},
}

AFFINITY_BONUS = 1.25


def roll_talents(rng: random.Random | None = None):
    """Arpoo 1-3 talenttia (painotettu) + 25 % mahdollisuus heikkouteen."""
    rng = rng or random.Random()
    roll = rng.random()
    count = 1 if roll < 0.60 else (2 if roll < 0.90 else 3)

    bag = []
    for name, spec in TALENTS.items():
        bag.extend([name] * spec["weight"])
    picked = []
    while len(picked) < count and bag:
        name = rng.choice(bag)
        if name not in picked:
            picked.append(name)
        bag = [b for b in bag if b != name]

    quirk = rng.choice(list(QUIRKS)) if rng.random() < 0.25 else None
    return picked, quirk


def apply_talents(unit, talents, quirk=None) -> int:
    """Soveltaa talentit yksikköön. Palauttaa hintavaikutuksen (SP).

    - talenttien nimet -> unit.traits (aina näkyvissä)
    - tarkat kuvaukset -> unit.talent_details (vaatii insightin)
    """
    cost_mod = 0
    if not hasattr(unit, "talent_effects") or unit.talent_effects is None:
        unit.talent_effects = {}
    if not hasattr(unit, "talent_details") or unit.talent_details is None:
        unit.talent_details = []

    entries = [(name, TALENTS[name]) for name in talents]
    if quirk:
        entries.append((quirk, QUIRKS[quirk]))

    for name, spec in entries:
        if name in unit.traits:
            continue
        unit.traits.append(name)
        unit.talent_details.append(f"{name}: {spec['desc']}")
        cost_mod += spec.get("cost", 0)
        for stat, amount in spec.get("base", {}).items():
            if stat in unit.base_attributes:
                unit.base_attributes[stat] += amount
            else:
                unit.base_attributes[stat] = amount
        for key, val in spec.get("effects", {}).items():
            if key in ("speed_mult", "xp_mult"):
                unit.talent_effects[key] = \
                    unit.talent_effects.get(key, 1.0) * val
            else:
                unit.talent_effects[key] = \
                    unit.talent_effects.get(key, 0) + val
        if "affinity" in spec:
            group = spec["affinity"]
            unit.weapon_affinities[group] = \
                unit.weapon_affinities.get(group, 1.0) * AFFINITY_BONUS

    unit.calculate_final_stats()
    unit.current_hp = unit.max_hp
    return cost_mod
