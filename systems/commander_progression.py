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
        # Vortex-magia on (ehkä) ainoa magia jonka Commander oppii - polku
        # AVAA spell slotit ja tierit tasovaatimusten takaa.
        "name": "Path of the Vortex",
        "desc": "Vortex magic may be the only magic a Commander ever learns. Casting deepens it.",
        "color": (150, 110, 220),
        "xp_base": 22, "xp_slope": 13,
        "locked": False,
        "milestones": (
            (1, "first_sigil", "First Sigil", "Spell Slot 1 + Spell Tier I",
             {"unlock_spell_slot": [1], "max_spell_tier": 1, "max_mana": 5}),
            (4, "mana_well", "Mana Well", "+10 max mana",
             {"max_mana": 10}),
            (8, "second_sigil", "Second Sigil", "Spell Slot 2",
             {"unlock_spell_slot": [2], "mana_regen": 0.05}),
            (12, "vortex_tier_2", "Vortex Tier II", "Spell Tier II, +1 INT",
             {"max_spell_tier": 2, "int": 1}),
            (16, "third_sigil", "Third Sigil", "Spell Slot 3, +15 max strain",
             {"unlock_spell_slot": [3], "max_strain": 15}),
            (20, "vortex_tier_3", "Vortex Tier III", "Spell Tier III, +0.10 regen",
             {"max_spell_tier": 3, "mana_regen": 0.10}),
            (25, "veilsight", "Veilsight", "+2 INT, +20 max mana",
             {"int": 2, "max_mana": 20}),
            (30, "abyssal_gate", "Abyssal Gate", "Spell Tier IV. The Abyss notices you.",
             {"max_spell_tier": 4, "max_strain": 25, "int": 2}),
        ),
    },
    "mining": {
        "name": "Path of the Vein",
        "desc": "Every ore struck teaches the stone's language.",
        "color": (170, 150, 130),
        "xp_base": 20, "xp_slope": 12,
        "locked": False,
        "tools": ((1, "Weak Pickaxe"), (5, "Bogiron Pickaxe"),
                  (9, "Steelhead Pickaxe"), (14, "Duskforged Pickaxe"),
                  (19, "Vortexbite Pickaxe")),
        "milestones": (
            (4, "sure_strike", "Sure Strike", "Better ore chance per hit",
             {"mining_speed": 0.05}),
            (8, "ore_sense", "Ore Sense", "+1 mining yield",
             {"mining_yield": 1}),
            (14, "stone_shoulders", "Stone Shoulders", "+1 STR, +10 max HP",
             {"str": 1, "max_hp": 10}),
            (20, "deep_delver", "Deep Delver", "Even better ore chance",
             {"mining_speed": 0.08}),
            (26, "gem_eye", "Gem Eye", "+1 mining yield",
             {"mining_yield": 1}),
            (30, "heart_of_the_vein", "Heart of the Vein", "+2 STR, ore mastery",
             {"str": 2, "mining_speed": 0.07, "mining_yield": 1}),
        ),
    },
    "smithing": {
        "name": "Path of the Anvil",
        "desc": "Forged blades remember the hand that made them.",
        "color": (215, 140, 70),
        "xp_base": 24, "xp_slope": 14,
        "locked": False,
        "milestones": (
            (5, "apprentice_hammer", "Apprentice Hammer", "+1 STR",
             {"str": 1}),
            (10, "sparing_hammer", "Sparing Hammer", "15% chance to save materials when forging",
             {}),
            (16, "temper_master", "Temper Master", "+1 DEF, +10 max HP",
             {"defense": 1, "max_hp": 10}),
            (23, "anvil_rhythm", "Anvil Rhythm", "+15 max stamina",
             {"max_stamina": 15}),
            (30, "runesmith", "Runesmith", "+2 STR, +1 DEF (rune forging hook)",
             {"str": 2, "defense": 1}),
        ),
    },
    "forestry": {
        "name": "Path of the Timber",
        "desc": "The marsh forest yields to a practiced axe.",
        "color": (120, 170, 90),
        "xp_base": 20, "xp_slope": 12,
        "locked": False,
        "tools": ((1, "Weak Lumber Axe"), (5, "Bogiron Lumber Axe"),
                  (9, "Steelhead Lumber Axe"), (14, "Duskforged Lumber Axe"),
                  (19, "Vortexfell Lumber Axe")),
        "milestones": (
            (4, "clean_swing", "Clean Swing", "Better wood chance per hit",
             {"chop_speed": 0.06}),
            (9, "heartwood", "Heartwood", "+1 wood from felled trees",
             {"wood_yield": 1}),
            (15, "lumber_back", "Lumber Back", "+15 max stamina",
             {"max_stamina": 15}),
            (22, "old_growth", "Old Growth", "Even better wood chance",
             {"chop_speed": 0.08}),
            (30, "forest_bond", "Forest Bond", "+1 wood, +1 STR",
             {"wood_yield": 1, "str": 1}),
        ),
    },
    "fishing": {
        "name": "Path of the Line",
        "desc": "Patience by the water. A new rod every few levels.",
        "color": (110, 180, 200),
        "xp_base": 18, "xp_slope": 12,
        "locked": False,
        # Työkalutikkaat: uusi väline ~4 tason välein (yksi per areenatier)
        "tools": ((1, "Fishing Rod"), (5, "Bogwood Rod"),
                  (9, "Ironwire Rod"), (14, "Duskwillow Rod"),
                  (19, "Vortexline Rod")),
        "milestones": (
            (4, "quick_wrists", "Quick Wrists", "Reeling builds less tension",
             {}),
            (10, "sharp_hook", "Sharp Hook", "Treasure bites more often", {}),
            (18, "double_catch", "Double Catch", "Chance to land two fish",
             {}),
            (24, "steady_line", "Steady Line", "+10 max stamina",
             {"max_stamina": 10}),
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
    slots = set()
    max_tier = 0
    for path_id, spec in PATHS.items():
        if spec.get("locked"):
            continue
        level = get_path(manager, path_id)["level"]
        for lvl, _pid, _name, _desc, effects in spec["milestones"]:
            if lvl <= level:
                for key, val in effects.items():
                    if key == "unlock_spell_slot":
                        slots.update(int(x) for x in val)
                    elif key == "max_spell_tier":
                        max_tier = max(max_tier, int(val))
                    else:
                        totals[key] = totals.get(key, 0) + val
    if slots:
        totals["unlock_spell_slot"] = sorted(slots)
    if max_tier:
        totals["max_spell_tier"] = max_tier
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


def next_tool(manager, path_id: str):
    """Seuraava avautuva työkalu (taso, nimi) tai None jos kaikki auki."""
    spec = PATHS.get(path_id, {})
    level = get_path(manager, path_id)["level"]
    for lvl, name in spec.get("tools", ()):
        if lvl > level:
            return (lvl, name)
    return None


def tool_allowed(manager, attacker, tool, path_id: str, attr: str):
    """Onko työkalu käyttäjänsä tasolle sallittu? Palauttaa (ok, req).
    Koskee vain sankaria - NPC:t saavat käyttää mitä vain."""
    hero = getattr(manager, "player_character", None) if manager else None
    if hero is None or attacker is not hero:
        return True, 0
    req = int(getattr(tool, attr, 1) or 1)
    level = get_path(manager, path_id)["level"]
    return level >= req, req


def on_ore_mined(manager, attacker, dropped: int) -> None:
    """Mining-XP jokaisesta sankarin malmi-iskusta (dropista enemmän)."""
    hero = getattr(manager, "player_character", None) if manager else None
    if hero is None or attacker is not hero:
        return
    if grant_xp(manager, "mining", 2 + dropped * 6):
        _celebrate(manager, hero, "mining")


def on_tree_chopped(manager, attacker, felled: bool) -> None:
    """Forestry-XP puun hakkuusta; kaadosta bonus. Kaadot etenevät myös
    Woodsman Alderin First Swing -questia."""
    hero = getattr(manager, "player_character", None) if manager else None
    if hero is None or attacker is not hero:
        return
    if grant_xp(manager, "forestry", 6 if felled else 2):
        _celebrate(manager, hero, "forestry")
    if felled:
        try:
            from quest_system import quest_manager
            q = quest_manager.get_quest("quest_first_swing") if quest_manager else None
            if q and q.status == "active":
                q.progress += 1
                need = q.definition.required_amount
                if q.progress >= need:
                    q.status = "completed"
                    manager.vfx.show_damage(hero.rect.centerx,
                                            hero.rect.top - 40,
                                            "Quest Done! See Alder!",
                                            color=(255, 210, 90))
                else:
                    manager.vfx.show_damage(hero.rect.centerx,
                                            hero.rect.top - 40,
                                            f"Trees felled: {q.progress}/{need}",
                                            color=(220, 220, 220))
        except Exception:
            pass


def on_item_crafted(manager, recipe_cost: int) -> None:
    """Smithing-XP taotusta esineestä (kalliimpi = enemmän oppia)."""
    hero = getattr(manager, "player_character", None) if manager else None
    if hero is None:
        return
    if grant_xp(manager, "smithing", 8 + max(0, int(recipe_cost)) // 10):
        _celebrate(manager, hero, "smithing")


def _celebrate(manager, hero, path_id):
    level = get_path(manager, path_id)["level"]
    name = PATHS[path_id]["name"]
    try:
        manager.vfx.show_damage(hero.rect.centerx, hero.rect.top - 60,
                                f"{name} {level}!", color=(255, 215, 0))
    except Exception:
        pass
