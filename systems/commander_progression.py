# systems/commander_progression.py
"""Commanderin kykypolut (Paths): jokainen tekeminen on OMA puunsa
omalla XP:llään, joka nousee suoraan tekemisestä:

- Path of the Arena  (combat)  - XP tapoista ja voitoista otteluissa
- Path of the Weave  (arcane)  - XP loitsimisesta (pohjustaa Abyssal-magian)
- Path of the Line   (fishing) - XP saaliista
- Path of the Homestead (building) - tulossa House Buildingin myötä

Tasot 1-30. Milestone-perkit avautuvat tasoilla automaattisesti ja
niiden statsivaikutukset syötetään sankarille apply_to_hero():lla
(Commander.calculate_final_stats lukee _progression_effects-sanakirjan).
Tila elää manager.npc_state["paths"] -> tallentuu saveen sellaisenaan.

HUOM: farming ja ruoanlaitto EIVÄT ole Commander-polkuja - ne kuuluvat
kylälle ja keittiölle.
"""

from __future__ import annotations

MAX_LEVEL = 30

# Milestonet: (taso, id, nimi, kuvaus, statsivaikutukset sankarille)
PATHS = {
    "combat": {
        "name": "Path of the Arena",
        "desc": "Kills and victories harden the Commander.",
        "color": (210, 110, 90),
        "xp_base": 24, "xp_slope": 14,
        "locked": False,
        "milestones": (
            (3, "arena_footing", "Arena Footing", "+10 max HP",
             {"max_hp": 10}),
            (6, "killer_instinct", "Killer Instinct", "+1 STR, +1 DEX",
             {"str": 1, "dex": 1}),
            (10, "crowd_roar", "Crowd's Roar", "+15 max stamina",
             {"max_stamina": 15}),
            (15, "veteran_scars", "Veteran's Scars", "+1 DEF, +15 max HP",
             {"defense": 1, "max_hp": 15}),
            (20, "duelists_eye", "Duelist's Eye", "+3% crit chance",
             {"crit_chance": 0.03}),
            (25, "warlords_poise", "Warlord's Poise", "+2 STR, +1 DEF",
             {"str": 2, "defense": 1}),
            (30, "arena_legend", "Arena Legend", "+30 max HP, +5% crit",
             {"max_hp": 30, "crit_chance": 0.05}),
        ),
    },
    "arcane": {
        "name": "Path of the Weave",
        "desc": "Every cast attunes the Commander to the Weave - and one day, the Abyss.",
        "color": (150, 110, 220),
        "xp_base": 22, "xp_slope": 13,
        "locked": False,
        "milestones": (
            (3, "mana_well", "Mana Well", "+10 max mana",
             {"max_mana": 10}),
            (6, "steady_weave", "Steady Weave", "+0.05 mana regen",
             {"mana_regen": 0.05}),
            (10, "deep_reserves", "Deep Reserves", "+15 max mana, +1 INT",
             {"max_mana": 15, "int": 1}),
            (15, "strainhardened", "Strain-Hardened", "+20 max strain",
             {"max_strain": 20}),
            (20, "twin_current", "Twin Current", "+0.10 mana regen",
             {"mana_regen": 0.10}),
            (25, "veilsight", "Veilsight", "+2 INT, +20 max mana",
             {"int": 2, "max_mana": 20}),
            (30, "abyssal_gate", "Abyssal Gate", "The Abyss notices you. (Abyssal magic hook)",
             {"max_strain": 30, "int": 2}),
        ),
    },
    "fishing": {
        "name": "Path of the Line",
        "desc": "Patience by the water. Rods T1-T5 unlock at levels 1/7/13/20/26.",
        "color": (110, 180, 200),
        "xp_base": 18, "xp_slope": 12,
        "locked": False,
        "milestones": (
            (5, "quick_wrists", "Quick Wrists", "Reeling builds less tension",
             {}),
            (7, "bogwood_grip", "Bogwood Grip", "Tier 2 rods usable", {}),
            (10, "sharp_hook", "Sharp Hook", "Treasure bites more often", {}),
            (13, "ironwire_grip", "Ironwire Grip", "Tier 3 rods usable", {}),
            (18, "double_catch", "Double Catch", "Chance to land two fish",
             {}),
            (20, "duskwillow_grip", "Duskwillow Grip", "Tier 4 rods usable", {}),
            (26, "vortexline_grip", "Vortexline Grip", "Tier 5 rods usable", {}),
            (30, "master_of_line", "Master of the Line", "The water hides nothing from you.",
             {}),
        ),
    },
    "building": {
        "name": "Path of the Homestead",
        "desc": "House building is coming - foundations, walls, a hall of your own.",
        "color": (190, 160, 90),
        "xp_base": 26, "xp_slope": 15,
        "locked": True,   # avautuu House Building -ominaisuuden myötä
        "milestones": (
            (3, "steady_hands", "Steady Hands", "Coming with House Building", {}),
            (10, "framewright", "Framewright", "Coming with House Building", {}),
            (20, "hallmason", "Hallmason", "Coming with House Building", {}),
            (30, "master_builder", "Master Builder", "Coming with House Building", {}),
        ),
    },
}


# ---------------------------------------------------------------- tila

def _store(manager) -> dict:
    return manager.npc_state.setdefault("paths", {})


def get_path(manager, path_id: str) -> dict:
    """Polun pysyvä tila {level, xp}. Migratoi vanhan fishing-avaimen."""
    store = _store(manager)
    if path_id not in store:
        # Vanha kalastusdata uuteen kotiin
        if path_id == "fishing" and "fishing" in manager.npc_state:
            old = manager.npc_state.pop("fishing")
            store[path_id] = {"level": int(old.get("level", 1)),
                              "xp": int(old.get("xp", 0))}
        else:
            store[path_id] = {"level": 1, "xp": 0}
    return store[path_id]


def xp_needed(path_id: str, level: int) -> int:
    spec = PATHS[path_id]
    return spec["xp_base"] + level * spec["xp_slope"]


def grant_xp(manager, path_id: str, amount: int) -> bool:
    """Lisää XP:tä polulle. Palauttaa True jos taso nousi.
    Päivittää sankarin statsit jos milestone aukesi."""
    if path_id not in PATHS or PATHS[path_id].get("locked"):
        return False
    state = get_path(manager, path_id)
    if state["level"] >= MAX_LEVEL:
        return False
    state["xp"] += max(0, int(amount))
    leveled = False
    while state["level"] < MAX_LEVEL and \
            state["xp"] >= xp_needed(path_id, state["level"]):
        state["xp"] -= xp_needed(path_id, state["level"])
        state["level"] += 1
        leveled = True
    if leveled:
        apply_to_hero(manager)
    return leveled


def has_perk(manager, path_id: str, perk_id: str) -> bool:
    level = get_path(manager, path_id)["level"]
    for lvl, pid, *_rest in PATHS[path_id]["milestones"]:
        if pid == perk_id:
            return level >= lvl
    return False


def unlocked_milestones(manager, path_id: str):
    level = get_path(manager, path_id)["level"]
    return [m for m in PATHS[path_id]["milestones"] if m[0] <= level]


def apply_to_hero(manager) -> None:
    """Kokoaa kaikkien polkujen milestone-statsit sankarille.
    Commander.calculate_final_stats lukee _progression_effects-dictin."""
    hero = getattr(manager, "player_character", None)
    if hero is None:
        return
    totals = {}
    for path_id, spec in PATHS.items():
        if spec.get("locked"):
            continue
        level = get_path(manager, path_id)["level"]
        for lvl, _pid, _name, _desc, effects in spec["milestones"]:
            if lvl <= level:
                for key, val in effects.items():
                    totals[key] = totals.get(key, 0) + val
    hero._progression_effects = totals
    try:
        hero.calculate_final_stats()
    except Exception:
        pass


# ---------------------------------------------------------------- koukut

def on_match_end(manager, win: bool) -> None:
    """Combat-XP ottelun päätteeksi: tapot + voitto (vain jos sankari
    itse taisteli)."""
    hero = getattr(manager, "player_character", None)
    if hero is None or hero not in getattr(manager, "last_fighters", []):
        return
    kills = int(getattr(hero, "stats", {}).get("kills", 0))
    xp = kills * 8 + (12 if win else 4)
    if grant_xp(manager, "combat", xp):
        _celebrate(manager, hero, "combat")


def on_player_spell_cast(manager, spell) -> None:
    """Arcane-XP jokaisesta sankarin onnistuneesta loitsusta."""
    hero = getattr(manager, "player_character", None)
    if hero is None:
        return
    cost = int(getattr(spell, "mana_cost", 5))
    if grant_xp(manager, "arcane", max(2, cost // 2)):
        _celebrate(manager, hero, "arcane")


def _celebrate(manager, hero, path_id):
    level = get_path(manager, path_id)["level"]
    name = PATHS[path_id]["name"]
    try:
        manager.vfx.show_damage(hero.rect.centerx, hero.rect.top - 60,
                                f"{name} {level}!", color=(255, 215, 0))
    except Exception:
        pass
