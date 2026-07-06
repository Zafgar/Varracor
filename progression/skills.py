# progression/skills.py
# Skill tree definitions + helpers (unlocking, validation)

from __future__ import annotations

from typing import Any, Dict, Tuple, Optional


SKILLS: Dict[str, Dict[str, Any]] = {
    # =========================
    # STRENGTH TREE
    # =========================
    "str_core_1": {
        "name": "Power Training I",
        "tree": "Strength",
        "pos": (220, 120),
        "cost": 1,
        "requires": [],
        "desc": "+2 STR. Perus voimapohja.",
        "effects": {"str": 2},
    },
    "str_core_2": {
        "name": "Power Training II",
        "tree": "Strength",
        "pos": (220, 220),
        "cost": 1,
        "requires": ["str_core_1"],
        "desc": "+2 STR.",
        "effects": {"str": 2},
    },
    "str_tank": {
        "name": "Iron Frame",
        "tree": "Strength",
        "pos": (120, 320),
        "cost": 1,
        "requires": ["str_core_1"],
        "desc": "+25 Max HP.",
        "effects": {"max_hp": 25},
    },
    "str_bulwark": {
        "name": "Bulwark",
        "tree": "Strength",
        "pos": (120, 420),
        "cost": 1,
        "requires": ["str_tank"],
        "desc": "+2 Defense.",
        "effects": {"defense": 2},
    },
    "str_execute": {
        "name": "Executioner",
        "tree": "Strength",
        "pos": (320, 320),
        "cost": 2,
        "requires": ["str_core_2"],
        "desc": "Kun vihun HP ≤ 30%, teet +25% lisää melee-damagea.",
        "effects": {"execute_threshold": 0.30, "execute_bonus": 0.25},
    },
    "str_lifesteal": {
        "name": "Blood Drinker",
        "tree": "Strength",
        "pos": (320, 420),
        "cost": 2,
        "requires": ["str_execute"],
        "desc": "Lifesteal 6% (parantuu melee-hitistä).",
        "effects": {"lifesteal": 0.06},
    },

    # =========================
    # DEXTERITY TREE
    # =========================
    "dex_core_1": {
        "name": "Agility I",
        "tree": "Dexterity",
        "pos": (620, 120),
        "cost": 1,
        "requires": [],
        "desc": "+2 DEX.",
        "effects": {"dex": 2},
    },
    "dex_core_2": {
        "name": "Agility II",
        "tree": "Dexterity",
        "pos": (620, 220),
        "cost": 1,
        "requires": ["dex_core_1"],
        "desc": "+2 DEX.",
        "effects": {"dex": 2},
    },
    "dex_crit": {
        "name": "Keen Strikes",
        "tree": "Dexterity",
        "pos": (520, 320),
        "cost": 1,
        "requires": ["dex_core_1"],
        "desc": "+6% Crit chance.",
        "effects": {"crit_chance": 0.06},
    },
    "dex_dodge": {
        "name": "Footwork",
        "tree": "Dexterity",
        "pos": (720, 320),
        "cost": 1,
        "requires": ["dex_core_2"],
        "desc": "+8% Dodge chance.",
        "effects": {"dodge_chance": 0.08},
    },
    "dex_speed": {
        "name": "Quickstep",
        "tree": "Dexterity",
        "pos": (720, 420),
        "cost": 1,
        "requires": ["dex_dodge"],
        "desc": "+0.15 Move speed.",
        "effects": {"speed": 0.15},
    },

    # =========================
    # INTELLIGENCE TREE
    # =========================
    "int_core_1": {
        "name": "Study I",
        "tree": "Intelligence",
        "pos": (1020, 120),
        "cost": 1,
        "requires": [],
        "desc": "+2 INT.",
        "effects": {"int": 2},
    },
    "int_core_2": {
        "name": "Study II",
        "tree": "Intelligence",
        "pos": (1020, 220),
        "cost": 1,
        "requires": ["int_core_1"],
        "desc": "+2 INT.",
        "effects": {"int": 2},
    },
    "int_mana": {
        "name": "Deep Reserves",
        "tree": "Intelligence",
        "pos": (920, 320),
        "cost": 1,
        "requires": ["int_core_1"],
        "desc": "+20 Max Mana.",
        "effects": {"max_mana": 20},
    },
    "int_power": {
        "name": "Spell Power",
        "tree": "Intelligence",
        "pos": (1120, 320),
        "cost": 1,
        "requires": ["int_core_2"],
        "desc": "+15% spell power.",
        "effects": {"spell_power": 0.15},
    },
    "int_cdr": {
        "name": "Arcane Efficiency",
        "tree": "Intelligence",
        "pos": (1120, 420),
        "cost": 2,
        "requires": ["int_power"],
        "desc": "-10% cooldown multiplier (nopeammat iskut/spellit).",
        "effects": {"cooldown_reduction": 0.10},
    },

    # =========================
    # PROFICIENCY TREE (Weapons / Armor / Spells)
    # =========================
    "prof_core": {
        "name": "Proficiency Basics",
        "tree": "Proficiency",
        "pos": (1420, 120),
        "cost": 1,
        "requires": [],
        "desc": "Avaa perus käyttöoikeudet: Cloth + Dagger + Unarmed.",
        "effects": {
            "unlock_armor": ["Cloth"],
            "unlock_weapon": ["Dagger", "Unarmed"],
        },
    },

    # Weapons
    "wp_sword": {
        "name": "Sword Training",
        "tree": "Proficiency",
        "pos": (1320, 220),
        "cost": 1,
        "requires": ["prof_core"],
        "desc": "Osaat käyttää Sword-aseita.",
        "effects": {"unlock_weapon": ["Sword"]},
    },
    "wp_axe": {
        "name": "Axe Training",
        "tree": "Proficiency",
        "pos": (1520, 220),
        "cost": 1,
        "requires": ["prof_core"],
        "desc": "Osaat käyttää Axe-aseita.",
        "effects": {"unlock_weapon": ["Axe"]},
    },
    "wp_mace": {
        "name": "Mace Training",
        "tree": "Proficiency",
        "pos": (1320, 300),
        "cost": 1,
        "requires": ["prof_core"],
        "desc": "Osaat käyttää Mace-aseita.",
        "effects": {"unlock_weapon": ["Mace"]},
    },
    "wp_spear": {
        "name": "Spear Training",
        "tree": "Proficiency",
        "pos": (1520, 300),
        "cost": 1,
        "requires": ["prof_core"],
        "desc": "Osaat käyttää Spear-aseita.",
        "effects": {"unlock_weapon": ["Spear"]},
    },
    "wp_bow": {
        "name": "Bow Training",
        "tree": "Proficiency",
        "pos": (1320, 380),
        "cost": 1,
        "requires": ["prof_core"],
        "desc": "Osaat käyttää Bow-aseita.",
        "effects": {"unlock_weapon": ["Bow"]},
    },
    "wp_crossbow": {
        "name": "Crossbow Training",
        "tree": "Proficiency",
        "pos": (1520, 380),
        "cost": 1,
        "requires": ["prof_core"],
        "desc": "Osaat käyttää CrossBow-aseita.",
        "effects": {"unlock_weapon": ["CrossBow"]},
    },
    "wp_staff": {
        "name": "Staff Training",
        "tree": "Proficiency",
        "pos": (1320, 460),
        "cost": 1,
        "requires": ["prof_core"],
        "desc": "Osaat käyttää Staff-aseita.",
        "effects": {"unlock_weapon": ["Staff"]},
    },
    "wp_book": {
        "name": "Book Focus",
        "tree": "Proficiency",
        "pos": (1520, 460),
        "cost": 1,
        "requires": ["prof_core", "int_core_1"],
        "desc": "Osaat käyttää Book-focusia (mage polku alkaa tästä).",
        "effects": {"unlock_weapon": ["Book"]},
    },

    # Armor
    "arm_medium": {
        "name": "Medium Armor",
        "tree": "Proficiency",
        "pos": (1420, 260),
        "cost": 1,
        "requires": ["prof_core"],
        "desc": "Osaat käyttää Medium armoria.",
        "effects": {"unlock_armor": ["Medium"]},
    },
    "arm_heavy": {
        "name": "Heavy Armor",
        "tree": "Proficiency",
        "pos": (1420, 340),
        "cost": 2,
        "requires": ["arm_medium", "str_core_1"],
        "desc": "Osaat käyttää Heavy armoria.",
        "effects": {"unlock_armor": ["Heavy"]},
    },
    "arm_shield": {
        "name": "Shield Training",
        "tree": "Proficiency",
        "pos": (1420, 420),
        "cost": 1,
        "requires": ["arm_medium"],
        "desc": "Osaat käyttää Shieldiä off-handissa.",
        "effects": {"unlock_shield": True},
    },

    # Spell slots unlock (EI level-lukkoa)
    "spell_slot_1": {
        "name": "Spell Slot I",
        "tree": "Proficiency",
        "pos": (1620, 560),
        "cost": 1,
        "requires": ["wp_book"],
        "desc": "Avaa Spell Slot 1 (voit equipata spellin slot1).",
        "effects": {"spell_slots": 1, "spell_tier_max": 1},
    },
    "spell_slot_2": {
        "name": "Spell Slot II",
        "tree": "Proficiency",
        "pos": (1620, 640),
        "cost": 2,
        "requires": ["spell_slot_1", "int_core_2"],
        "desc": "Avaa Spell Slot 2.",
        "effects": {"spell_slots": 2},
    },
    "spell_slot_3": {
        "name": "Spell Slot III",
        "tree": "Proficiency",
        "pos": (1620, 720),
        "cost": 2,
        "requires": ["spell_slot_2", "int_cdr"],
        "desc": "Avaa Spell Slot 3.",
        "effects": {"spell_slots": 3},
    },

    # Spell tier unlock (1..8) – EI level-lukkoa
    "spell_tier_2": {
        "name": "Spell Tier II",
        "tree": "Proficiency",
        "pos": (1520, 560),
        "cost": 1,
        "requires": ["spell_slot_1"],
        "desc": "Voit käyttää tier 2 spellejä.",
        "effects": {"spell_tier_max": 2},
    },
    "spell_tier_3": {
        "name": "Spell Tier III",
        "tree": "Proficiency",
        "pos": (1520, 640),
        "cost": 1,
        "requires": ["spell_tier_2", "spell_slot_2"],
        "desc": "Voit käyttää tier 3 spellejä.",
        "effects": {"spell_tier_max": 3},
    },
    "spell_tier_4": {
        "name": "Spell Tier IV",
        "tree": "Proficiency",
        "pos": (1520, 720),
        "cost": 2,
        "requires": ["spell_tier_3"],
        "desc": "Voit käyttää tier 4 spellejä.",
        "effects": {"spell_tier_max": 4},
    },
    "spell_tier_5": {
        "name": "Spell Tier V",
        "tree": "Proficiency",
        "pos": (1520, 800),
        "cost": 2,
        "requires": ["spell_tier_4", "spell_slot_3"],
        "desc": "Voit käyttää tier 5 spellejä.",
        "effects": {"spell_tier_max": 5},
    },
    "spell_tier_6": {
        "name": "Spell Tier VI",
        "tree": "Proficiency",
        "pos": (1520, 880),
        "cost": 2,
        "requires": ["spell_tier_5"],
        "desc": "Voit käyttää tier 6 spellejä.",
        "effects": {"spell_tier_max": 6},
    },
    "spell_tier_7": {
        "name": "Spell Tier VII",
        "tree": "Proficiency",
        "pos": (1520, 960),
        "cost": 3,
        "requires": ["spell_tier_6"],
        "desc": "Voit käyttää tier 7 spellejä.",
        "effects": {"spell_tier_max": 7},
    },
    "spell_tier_8": {
        "name": "Spell Tier VIII",
        "tree": "Proficiency",
        "pos": (1520, 1040),
        "cost": 3,
        "requires": ["spell_tier_7"],
        "desc": "Voit käyttää tier 8 spellejä.",
        "effects": {"spell_tier_max": 8},
    },
}


def _normalize_effects(effects: Dict[str, Any]) -> Dict[str, Any]:
    """Map old effect keys -> the keys Gladiator already understands.
    We KEEP original keys too, so nothing else breaks.
    """
    out: Dict[str, Any] = dict(effects or {})

    # Weapon/armor unlocks -> proficiencies
    if "unlock_weapon" in out:
        w = out.get("unlock_weapon")
        w_list = w if isinstance(w, list) else [w]
        existing = out.get("weapon_prof")
        if existing is None:
            out["weapon_prof"] = list(w_list)
        else:
            ex_list = existing if isinstance(existing, list) else [existing]
            out["weapon_prof"] = list(dict.fromkeys([*ex_list, *w_list]))

    if "unlock_armor" in out:
        a = out.get("unlock_armor")
        a_list = a if isinstance(a, list) else [a]
        existing = out.get("armor_prof")
        if existing is None:
            out["armor_prof"] = list(a_list)
        else:
            ex_list = existing if isinstance(existing, list) else [existing]
            out["armor_prof"] = list(dict.fromkeys([*ex_list, *a_list]))

    if out.get("unlock_shield"):
        # Shield counts as a WEAPON proficiency in this project (hard-lock in GuildMenu/Gladiator)
        existing = out.get("weapon_prof")
        if existing is None:
            out["weapon_prof"] = ["Shield"]
        elif isinstance(existing, list):
            if "Shield" not in existing:
                existing.append("Shield")
        else:
            out["weapon_prof"] = [existing, "Shield"]

    # Spell slot unlocks: spell_slots = 1/2/3 -> unlock_spell_slot = same number
    if "spell_slots" in out and "unlock_spell_slot" not in out:
        try:
            out["unlock_spell_slot"] = int(out["spell_slots"])
        except Exception:
            pass

    # Spell tier max: spell_tier_max -> max_spell_tier
    if "spell_tier_max" in out and "max_spell_tier" not in out:
        try:
            out["max_spell_tier"] = int(out["spell_tier_max"])
        except Exception:
            pass

    # Cooldown reduction -> cooldown_mult (Gladiator uses multiplier)
    if "cooldown_reduction" in out and "cooldown_mult" not in out:
        try:
            red = float(out["cooldown_reduction"])
            out["cooldown_mult"] = max(0.05, 1.0 - red)
        except Exception:
            pass

    return out


def get_skill(skill_id: str) -> Optional[Dict[str, Any]]:
    s = SKILLS.get(skill_id)
    if not s:
        return None
    out = dict(s)
    out["effects"] = _normalize_effects(dict(s.get("effects", {}) or {}))
    return out


def can_unlock(unit, skill_id: str) -> Tuple[bool, str]:
    s = SKILLS.get(skill_id)
    if not unit:
        return False, "No unit selected."
    if not s:
        return False, "Skill not found."

    unlocked = getattr(unit, "unlocked_skills", set()) or set()
    if skill_id in unlocked:
        return False, "Already unlocked."

    cost = int(s.get("cost", 1) or 1)
    points = int(getattr(unit, "skill_points", 0) or 0)
    if points < cost:
        return False, f"Not enough skill points. Need {cost}."

    req = list(s.get("requires", []) or [])
    missing = [r for r in req if r not in unlocked]
    if missing:
        return False, "Requires: " + ", ".join(missing)

    # min_level is optional future feature (spells do NOT rely on this)
    min_level = int(s.get("min_level", 1) or 1)
    lvl = int(getattr(unit, "level", 1) or 1)
    if lvl < min_level:
        return False, f"Requires level {min_level}."

    return True, "OK"


def unlock_skill(unit, skill_id: str) -> Tuple[bool, str]:
    ok, msg = can_unlock(unit, skill_id)
    if not ok:
        return False, msg

    if not hasattr(unit, "unlocked_skills") or getattr(unit, "unlocked_skills") is None:
        unit.unlocked_skills = set()
    if not hasattr(unit, "skill_points") or getattr(unit, "skill_points") is None:
        unit.skill_points = 0

    s = SKILLS[skill_id]
    cost = int(s.get("cost", 1) or 1)

    unit.skill_points -= cost
    unit.unlocked_skills.add(skill_id)

    return True, f"Unlocked: {s.get('name', skill_id)}"
