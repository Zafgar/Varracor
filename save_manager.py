# save_manager.py
"""
Tallennusjärjestelmä: serialisoi pelin ydintilan JSON-tiedostoon.

Tallennetaan:
  - Talous (kulta, maine, kausitiedot)
  - Inventaario, varusteet ja kylän varastot
  - Joukkue (yksiköt statseineen, skilleineen ja varusteineen)
  - Commander (taso, skillit, varusteet)
  - Questien tila
  - Liigan perustiedot (tier, kausinumero)

Tunnetut rajoitukset (v1):
  - Liigan sarjataulukko ja ELO generoituvat uudelleen latauksessa
  - NPC-muisti tallennetaan sellaisenaan (vain JSON-yhteensopivat arvot)
"""
import json
import os
import time

SAVE_DIR = "saves"
SAVE_FILE = os.path.join(SAVE_DIR, "savegame.json")
SAVE_VERSION = 1


# =========================================================
# ITEMS & SPELLS
# =========================================================
def _serialize_item(item):
    """Palauttaa itemistä/loitsusta luontitiedot tai None."""
    if item is None:
        return None
    cls = type(item).__name__
    if cls == "Fists":
        return None  # Nyrkit luodaan automaattisesti
    return {"class": cls, "name": str(getattr(item, "name", cls))}


def _create_saved_item(data):
    """Luo itemin tai loitsun tallennetuista tiedoista."""
    if not data:
        return None
    from items.item_registry import create_item
    from spells.spell_registry import get_spell_by_name

    # 1. Loitsu luokan nimellä (get_spell_by_name palauttaa luokan)
    spell_cls = get_spell_by_name(data["class"])
    if spell_cls:
        try:
            return spell_cls()
        except Exception as e:
            print(f"[Save] WARNING: could not create spell {data['class']}: {e}")
            return None

    # 2. Item luokan nimellä, sitten display-nimellä
    item = create_item(data["class"])
    if item is None and data.get("name"):
        item = create_item(data["name"])
    return item


# =========================================================
# UNITS
# =========================================================
def _serialize_unit(u):
    eq = {}
    for slot, item in getattr(u, "equipment", {}).items():
        eq[slot] = _serialize_item(item)
    return {
        "class": type(u).__name__,
        "name": u.name,
        "race": getattr(u, "race_name", "Human"),
        "quality": getattr(u, "quality", None),
        "level": int(getattr(u, "level", 1)),
        "xp": int(getattr(u, "xp", 0)),
        "skill_points": int(getattr(u, "skill_points", 0)),
        "unlocked_skills": sorted(getattr(u, "unlocked_skills", [])),
        "traits": list(getattr(u, "traits", [])),
        "personality": getattr(u, "personality", None),
        "origin": getattr(u, "origin", None),
        "weapon_affinities": dict(getattr(u, "weapon_affinities", {})),
        "base_attributes": dict(getattr(u, "base_attributes", {})),
        "cost": int(getattr(u, "cost", 0)),
        "training_count": int(getattr(u, "training_count", 0)),
        "stats": dict(getattr(u, "stats", {})),
        "equipment": eq,
    }


def _unit_class_map():
    """Luokkanimi -> luokka. Lazy import kiertoriippuvuuksien takia."""
    from units.human import Human
    from units.orc import Orc
    from units.elf import Elf
    from units.goblin import Goblin
    mapping = {"Human": Human, "Orc": Orc, "Elf": Elf, "Goblin": Goblin}
    # Harvinaisemmat rekrytoitavat (jos moduulit löytyvät)
    optional = [
        ("units.bard", "Bard"),
        ("units.elf_bard", "ElfBard"),
        ("units.villager", "Villager"),
        ("units.werewolf", "Werewolf"),
        ("units.tortle", "Tortle"),
        ("units.dwarf", "Dwarf"),
        ("units.gnome", "Gnome"),
    ]
    import importlib
    for mod_name, cls_name in optional:
        try:
            mod = importlib.import_module(mod_name)
            if hasattr(mod, cls_name):
                mapping[cls_name] = getattr(mod, cls_name)
        except Exception:
            pass
    return mapping


def _apply_unit_state(unit, data):
    """Palauttaa tallennetut kentät yksikköön ja laskee statsit uudelleen."""
    unit.level = data.get("level", 1)
    unit.xp = data.get("xp", 0)
    unit.skill_points = data.get("skill_points", 0)
    unit.unlocked_skills = set(data.get("unlocked_skills", []))
    unit.traits = list(data.get("traits", []))
    if data.get("personality"):
        unit.personality = data["personality"]
    if data.get("origin"):
        unit.origin = data["origin"]
    if data.get("weapon_affinities"):
        unit.weapon_affinities = dict(data["weapon_affinities"])
    if data.get("base_attributes"):
        unit.base_attributes = dict(data["base_attributes"])
    unit.cost = data.get("cost", unit.cost)
    unit.training_count = data.get("training_count", 0)
    if data.get("stats"):
        unit.stats = dict(data["stats"])

    # Varusteet suoraan slotteihin (data tulee validista pelitilasta,
    # joten proficiency-tarkistuksia ei ajeta uudelleen)
    for slot, item_data in data.get("equipment", {}).items():
        if slot not in unit.equipment:
            continue
        item = _create_saved_item(item_data)
        if item is not None:
            unit.equipment[slot] = item
        elif slot != "main_hand":  # main_handiin jää oletusnyrkit
            unit.equipment[slot] = None

    try:
        unit.calculate_final_stats()
    except Exception as e:
        print(f"[Save] WARNING: stat recalc failed for {unit.name}: {e}")
    unit.current_hp = unit.max_hp
    unit.current_mana = unit.max_mana
    unit.current_stamina = unit.max_stamina
    unit.is_dead = False


def _create_saved_unit(data, team_color):
    classes = _unit_class_map()
    UnitClass = classes.get(data.get("class"))
    if UnitClass is None:
        print(f"[Save] WARNING: unknown unit class '{data.get('class')}', using Human.")
        from units.human import Human
        UnitClass = Human

    name = data.get("name", "Unknown")
    try:
        # Human/Elf ottavat quality-parametrin
        if data.get("quality") is not None:
            unit = UnitClass(name, 0, 0, team_color, data["quality"])
        else:
            unit = UnitClass(name, 0, 0, team_color)
    except TypeError:
        unit = UnitClass(name, 0, 0, team_color)

    _apply_unit_state(unit, data)
    return unit


# =========================================================
# QUESTS
# =========================================================
def _serialize_quests(quest_manager):
    if not quest_manager:
        return {}
    out = {}
    for qid, q in quest_manager.quests.items():
        out[qid] = {
            "status": q.status,
            "is_finished": q.is_finished,
            "progress": q.progress,
        }
    return out


def _apply_quests(quest_manager, data, reputation):
    if not quest_manager:
        return
    quest_manager.reputation = reputation
    for qid, qdata in data.items():
        q = quest_manager.quests.get(qid)
        if q:
            q.status = qdata.get("status", q.status)
            q.is_finished = qdata.get("is_finished", False)
            q.progress = qdata.get("progress", 0)
    quest_manager.check_unlocks()


# =========================================================
# JSON SAFETY
# =========================================================
def _json_safe(value):
    """Suodattaa rakenteesta pois kaikki mikä ei ole JSON-serialisoitavaa."""
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()
                if _is_jsonable_leaf_or_container(v)}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value
                if _is_jsonable_leaf_or_container(v)]
    return value


def _is_jsonable_leaf_or_container(v):
    return isinstance(v, (dict, list, tuple, set, str, int, float, bool)) or v is None


# =========================================================
# PUBLIC API
# =========================================================
def has_save():
    return os.path.exists(SAVE_FILE)


def save_game(manager):
    """Tallentaa pelitilan. Palauttaa True onnistuessa."""
    try:
        from quest_system import quest_manager
    except ImportError:
        quest_manager = None

    try:
        data = {
            "version": SAVE_VERSION,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            # --- Talous & kausi ---
            "gold": manager.gold,
            "reputation": manager.reputation,
            "reputations": dict(manager.reputations),
            "league_level": manager.league_level,
            "season_wins": manager.season_wins,
            "season_losses": manager.season_losses,
            "matches_played": manager.matches_played,
            "season_length": manager.season_length,
            "battle_size": manager.battle_size,
            "hunt_tier": manager.hunt_tier,
            # --- Inventaario ---
            "inventory": dict(manager.inventory),
            "city_storage": dict(manager.city_storage),
            "equipment_bag": [d for d in (_serialize_item(i) for i in manager.equipment_bag) if d],
            # --- Joukkue ---
            "roster": [_serialize_unit(u) for u in manager.my_team],
            "commander": _serialize_unit(manager.player_character) if manager.player_character else None,
            # --- Questit & NPC:t ---
            "quests": _serialize_quests(quest_manager),
            "village_tasks": manager.village_tasks.to_dict() if getattr(manager, "village_tasks", None) else {},
            "has_smith": bool(getattr(manager, "has_smith", False)),
            "quest_reputation": quest_manager.reputation if quest_manager else 0,
            "npc_state": _json_safe(manager.npc_state),
            # --- Liiga (perustiedot) ---
            "league_tier": manager.league_engine.tier,
            "league_season_number": manager.league_engine.season_number,
            # --- Maailmankello & velka ---
            "world_clock": manager.world_clock.to_dict(),
            "innkeeper_debt": int(getattr(manager, "innkeeper_debt", 0)),
            "next_raid_day": int(getattr(manager, "next_raid_day", 0)),
            "mine_key_owned": bool(getattr(manager, "mine_key_owned", False)),
        }

        os.makedirs(SAVE_DIR, exist_ok=True)
        # Kirjoitetaan ensin väliaikaistiedostoon, ettei epäonnistunut
        # tallennus tuhoa vanhaa savea
        tmp = SAVE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, SAVE_FILE)
        print(f"[Save] Game saved to {SAVE_FILE}")
        return True
    except Exception as e:
        print(f"[Save] ERROR: saving failed: {e}")
        return False


def load_game(manager):
    """Lataa pelitilan manageriin. Palauttaa True onnistuessa."""
    if not has_save():
        print("[Save] No save file found.")
        return False

    try:
        from quest_system import quest_manager
    except ImportError:
        quest_manager = None

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[Save] ERROR: could not read save file: {e}")
        return False

    try:
        from settings import PLAYER_TEAM

        # --- Talous & kausi ---
        manager.gold = data.get("gold", manager.gold)
        manager.reputation = data.get("reputation", 0)
        manager.reputations = dict(data.get("reputations", {}))
        manager.league_level = data.get("league_level", 1)
        manager.season_wins = data.get("season_wins", 0)
        manager.season_losses = data.get("season_losses", 0)
        manager.matches_played = data.get("matches_played", 0)
        manager.season_length = data.get("season_length", 5)
        manager.battle_size = data.get("battle_size", 3)
        manager.hunt_tier = data.get("hunt_tier", 1)

        # --- Inventaario ---
        manager.inventory.clear()
        manager.inventory.update(data.get("inventory", {}))
        manager.city_storage = dict(data.get("city_storage", {}))
        manager.equipment_bag = []
        for item_data in data.get("equipment_bag", []):
            item = _create_saved_item(item_data)
            if item:
                manager.equipment_bag.append(item)

        # --- Joukkue ---
        manager.my_team.empty()
        for unit_data in data.get("roster", []):
            unit = _create_saved_unit(unit_data, PLAYER_TEAM)
            manager.my_team.add(unit)
            if hasattr(manager, "_restore_unit_ai"):
                manager._restore_unit_ai(unit)

        # --- Commander ---
        if data.get("commander") and manager.player_character:
            _apply_unit_state(manager.player_character, data["commander"])

        # --- Questit ---
        manager.has_smith = bool(data.get("has_smith", False))
        if getattr(manager, "village_tasks", None) and data.get("village_tasks"):
            manager.village_tasks.from_dict(data["village_tasks"])

        _apply_quests(quest_manager, data.get("quests", {}),
                      data.get("quest_reputation", 0))
        if quest_manager:
            manager.reputation = quest_manager.reputation

        # --- NPC-muisti ---
        if data.get("npc_state"):
            manager.npc_state = data["npc_state"]

        # --- Maailmankello & velka ---
        if data.get("world_clock"):
            manager.world_clock.from_dict(data["world_clock"])
        manager.innkeeper_debt = int(data.get("innkeeper_debt", 0))
        if data.get("next_raid_day"):
            manager.next_raid_day = int(data["next_raid_day"])
        manager.mine_key_owned = bool(data.get("mine_key_owned", False))

        # --- Liiga ---
        manager.league_engine.tier = data.get("league_tier", 1)
        manager.league_engine.season_number = data.get("league_season_number", 1)
        manager.league_engine._initialized = False  # Kausi generoituu uudelleen

        manager.update_all_groups()
        manager.refresh_hub()
        print(f"[Save] Game loaded (saved {data.get('timestamp', '?')})")
        return True
    except Exception as e:
        print(f"[Save] ERROR: loading failed: {e}")
        return False
