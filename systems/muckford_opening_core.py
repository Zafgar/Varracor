"""Muckford opening-arc integration.

Keeps the existing cinematic intro intact while expanding the playable Forest
Road into a staged combat tutorial. It also turns Muckford's early economy,
reputation and creature victories into requirements for founding an official
arena team.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from settings import CHEAT_MODE, ENEMY_TEAM
from sound_manager import sound_system
from ui_kit import format_money


FOREST_ROAD_WIDTH = 7200
REGISTRATION_FEE_SP = 30
REGISTRATION_REPUTATION = 8
REGISTRATION_CREATURE_WINS = 3
TEAM_NAME_MIN = 3
TEAM_NAME_MAX = 24

_PLAYER_TEAM_NAME = "Unregistered"


def _opening(manager) -> dict:
    global_data = manager.npc_state.setdefault("global", {})
    global_data.setdefault("flags", {})
    global_data.setdefault("deeds", [])
    state = global_data.setdefault("muckford_opening", {})
    state.setdefault("economy_initialized", False)
    state.setdefault("intro_complete", False)
    state.setdefault("creature_wins", 0)
    state.setdefault("bram_hint_shown", False)
    state.setdefault("team_registered", False)
    state.setdefault("team_name", "")
    state.setdefault("first_recruit_free", False)
    state.setdefault("pending_fighters", [])
    return state


def opening_progress(manager) -> dict:
    state = _opening(manager)
    return {
        "debt": int(getattr(manager, "innkeeper_debt", 0)),
        "silver": int(getattr(manager, "gold", 0)),
        "reputation": int(getattr(manager, "reputation", 0)),
        "creature_wins": int(state.get("creature_wins", 0)),
        "team_registered": bool(state.get("team_registered", False)),
        "team_name": state.get("team_name", "") or "Unregistered",
    }


def registration_status(manager) -> Tuple[bool, List[str]]:
    progress = opening_progress(manager)
    missing: List[str] = []
    if progress["debt"] > 0:
        missing.append(f"Pay Marda's debt ({format_money(progress['debt'])})")
    if progress["reputation"] < REGISTRATION_REPUTATION:
        missing.append(
            f"Earn reputation ({progress['reputation']}/{REGISTRATION_REPUTATION})"
        )
    if progress["creature_wins"] < REGISTRATION_CREATURE_WINS:
        missing.append(
            f"Defeat creatures ({progress['creature_wins']}/{REGISTRATION_CREATURE_WINS})"
        )
    if progress["silver"] < REGISTRATION_FEE_SP:
        missing.append(
            f"Save the registration fee ({format_money(progress['silver'])}/"
            f"{format_money(REGISTRATION_FEE_SP)})"
        )
    return not missing, missing


def _clean_team_name(value: str) -> str:
    value = re.sub(r"\s+", " ", str(value or "").strip())
    value = re.sub(r"[^A-Za-z0-9 '\-]", "", value)
    return value[:TEAM_NAME_MAX].strip()


def _sync_league_name(manager) -> None:
    global _PLAYER_TEAM_NAME
    state = _opening(manager)
    _PLAYER_TEAM_NAME = state.get("team_name") or "Unregistered"
    engine = getattr(manager, "league_engine", None)
    if engine is not None:
        engine.player_team_name = _PLAYER_TEAM_NAME


def register_team(manager, raw_name: str) -> Tuple[bool, str]:
    state = _opening(manager)
    if state.get("team_registered"):
        return False, "Your team is already registered."

    name = _clean_team_name(raw_name)
    if len(name) < TEAM_NAME_MIN:
        return False, f"Team name must be at least {TEAM_NAME_MIN} characters."

    eligible, missing = registration_status(manager)
    if not eligible:
        return False, missing[0]

    manager.gold -= REGISTRATION_FEE_SP
    state["team_registered"] = True
    state["team_name"] = name
    state["first_recruit_free"] = True
    manager.team_registration_pending = False
    _sync_league_name(manager)

    if hasattr(manager, "record_deed"):
        manager.record_deed(
            "muckford_team_registered",
            f"founded the arena team {name} in Muckford",
        )

    pending = state.setdefault("pending_fighters", [])
    if pending and getattr(manager, "village_tasks", None):
        spec = pending.pop(0)
        fighter = manager.village_tasks._create_fighter(spec)
        if fighter is not None:
            manager.my_team.add(fighter)
            if hasattr(manager, "_restore_unit_ai"):
                manager._restore_unit_ai(fighter)
            manager.update_all_groups()
            state["first_recruit_free"] = False

    try:
        sound_system.play_sound("recruit")
    except Exception:
        pass
    return True, f"{name} is now registered in the Rookie Dust Circuit."


def _context_opening(context: dict) -> dict:
    return (
        context.get("memory", {})
        .get("global", {})
        .get("muckford_opening", {})
    )


def _context_registration_status(context: dict) -> Tuple[bool, List[str]]:
    state = _context_opening(context)
    debt = int(context.get("innkeeper_debt", 0))
    silver = int(context.get("player", {}).get("gold", 0))
    reputation = int(context.get("reputation", 0))
    wins = int(state.get("creature_wins", 0))
    missing = []
    if debt > 0:
        missing.append(f"Marda's debt: {format_money(debt)}")
    if reputation < REGISTRATION_REPUTATION:
        missing.append(f"Reputation: {reputation}/{REGISTRATION_REPUTATION}")
    if wins < REGISTRATION_CREATURE_WINS:
        missing.append(f"Creature wins: {wins}/{REGISTRATION_CREATURE_WINS}")
    if silver < REGISTRATION_FEE_SP:
        missing.append(
            f"Registration money: {format_money(silver)}/"
            f"{format_money(REGISTRATION_FEE_SP)}"
        )
    return not missing, missing


def _patch_game_manager() -> None:
    from game_manager import GameManager

    if getattr(GameManager, "_muckford_opening_installed", False):
        return

    previous_init = GameManager.__init__
    previous_hire_recruit = GameManager.hire_recruit
    previous_hire_reference = GameManager.hire_unit_by_reference

    def __init__(self, *args, **kwargs):
        previous_init(self, *args, **kwargs)
        state = _opening(self)
        self.team_registration_pending = False
        if not CHEAT_MODE and not state.get("economy_initialized", False):
            # `gold` remains the internal save-compatible name, but stores SP.
            self.gold = 0
            state["economy_initialized"] = True
        _sync_league_name(self)

    def team_name_get(self):
        return _opening(self).get("team_name") or "Unregistered"

    def team_name_set(self, value):
        _opening(self)["team_name"] = _clean_team_name(value)
        _sync_league_name(self)

    def team_registered_get(self):
        return bool(_opening(self).get("team_registered", False))

    def team_registered_set(self, value):
        _opening(self)["team_registered"] = bool(value)

    def hire_recruit(self, index):
        state = _opening(self)
        # Only gate hiring while the Muckford opening's registration phase is
        # genuinely active (intro finished, team not yet registered). Managers
        # outside that flow - loaded saves, village-task recruits, tests - hire
        # normally instead of being silently blocked.
        if state.get("intro_complete", False) and not state.get("team_registered", False):
            return False
        if (
            state.get("first_recruit_free", False)
            and len(self.my_team) == 0
            and 0 <= index < len(self.recruit_options)
            and self.recruit_options[index] is not None
        ):
            recruit = self.recruit_options[index]
            self.my_team.add(recruit)
            self._restore_unit_ai(recruit)
            self.update_all_groups()
            self.recruit_options[index] = None
            state["first_recruit_free"] = False
            if hasattr(self, "record_deed"):
                self.record_deed(
                    "muckford_first_recruit",
                    f"signed {recruit.name} as the first fighter of {self.team_name}",
                )
            return True
        return previous_hire_recruit(self, index)

    def hire_unit_by_reference(self, unit, cost):
        state = _opening(self)
        if state.get("intro_complete", False) and not state.get("team_registered", False):
            return False
        if state.get("first_recruit_free", False) and len(self.my_team) == 0:
            self.my_team.add(unit)
            self._restore_unit_ai(unit)
            self.update_all_groups()
            if unit in self.recruit_options:
                self.recruit_options[self.recruit_options.index(unit)] = None
            state["first_recruit_free"] = False
            return True
        return previous_hire_reference(self, unit, cost)

    GameManager.__init__ = __init__
    GameManager.team_name = property(team_name_get, team_name_set)
    GameManager.team_registered = property(team_registered_get, team_registered_set)
    GameManager.hire_recruit = hire_recruit
    GameManager.hire_unit_by_reference = hire_unit_by_reference
    GameManager._muckford_opening_installed = True


def _patch_save_load() -> None:
    import save_manager

    if getattr(save_manager, "_muckford_opening_installed", False):
        return
    previous_load = save_manager.load_game

    def load_game(manager, *args, **kwargs):
        ok = previous_load(manager, *args, **kwargs)
        if ok:
            _opening(manager)
            manager.team_registration_pending = False
            _sync_league_name(manager)
        return ok

    save_manager.load_game = load_game
    save_manager._muckford_opening_installed = True


def _patch_village_fighter_rewards() -> None:
    from systems.village_task_manager import VillageTaskManager

    if getattr(VillageTaskManager, "_muckford_opening_installed", False):
        return
    previous_grant = VillageTaskManager._grant_rewards

    def _sp_labels(gained):
        labelled = []
        for text in gained or []:
            match = re.fullmatch(r"\+(\d+) Gold", str(text))
            labelled.append(
                f"+{format_money(int(match.group(1)))}" if match else text
            )
        return labelled

    def _grant_rewards(self, manager, rewards):
        fighter_spec = rewards.get("fighter")
        state = _opening(manager)
        # Only hold fighter rewards as contracts while the opening's registration
        # phase is genuinely active (intro finished, team not yet registered).
        # Outside that flow - loaded saves, tests - grant the fighter normally.
        opening_active = state.get("intro_complete", False) and not state.get("team_registered", False)
        if fighter_spec and opening_active:
            safe_rewards = dict(rewards)
            safe_rewards.pop("fighter", None)
            gained = _sp_labels(previous_grant(self, manager, safe_rewards))
            _opening(manager).setdefault("pending_fighters", []).append(
                dict(fighter_spec)
            )
            gained.append("Fighter contract held until team registration")
            return gained
        return _sp_labels(previous_grant(self, manager, rewards))

    VillageTaskManager._grant_rewards = _grant_rewards
    VillageTaskManager._muckford_opening_installed = True


def _patch_chat_effects() -> None:
    from menus.chat_menu import ChatMenu

    if getattr(ChatMenu, "_muckford_opening_installed", False):
        return
    previous_apply = ChatMenu.apply_effect

    def apply_effect(self, effect_str):
        if effect_str == "begin_team_registration":
            self.manager.team_registration_pending = True
            return
        return previous_apply(self, effect_str)

    ChatMenu.apply_effect = apply_effect
    ChatMenu._muckford_opening_installed = True


def _patch_marda_dialogue() -> None:
    from npc.base_npc import DialogueChoice, DialogueNode
    from npc.marda_shant_npc import MardaShantNPC

    if getattr(MardaShantNPC, "_muckford_opening_installed", False):
        return
    previous_nodes = MardaShantNPC.get_nodes

    def get_nodes(self, context):
        nodes = previous_nodes(self, context)
        registered = bool(_context_opening(context).get("team_registered", False))

        if "intro_debt" in nodes:
            nodes["intro_debt"].text = (
                "Don't thank me yet. Two nights on my floor, a ruined rug, "
                "and the broth I spooned into you - that's 25 SP you owe me. "
                "Gus pays for honest work, the notice board pays for errands, "
                "and Hamo buys proof of dead vermin."
            )

        if not registered and "hub" in nodes:
            hub = nodes["hub"]
            hub.choices = [
                choice
                for choice in hub.choices
                if "open_recruit_menu" not in getattr(choice, "effects", [])
            ]
            hub.choices.insert(
                0,
                DialogueChoice("I'm looking for fighters.", "team_registration_gate"),
            )
            nodes["team_registration_gate"] = DialogueNode(
                id="team_registration_gate",
                text=(
                    "Fighters sign with registered teams, not nameless drifters. "
                    "Earn some standing, kill something meaner than a tavern rat, "
                    "settle your debt, then have Bram put a name in his ledger."
                ),
                speaker=self.name,
                emotion="thinking",
                choices=[DialogueChoice("I'll speak with Bram.", "hub")],
            )
        return nodes

    MardaShantNPC.get_nodes = get_nodes
    MardaShantNPC._muckford_opening_installed = True


def _patch_bram_dialogue() -> None:
    from npc.base_npc import DialogueChoice, DialogueNode
    from npc.dwarf_league_manager import DwarfLeagueManager

    if getattr(DwarfLeagueManager, "_muckford_opening_installed", False):
        return
    previous_root = DwarfLeagueManager.get_dialogue_root
    previous_nodes = DwarfLeagueManager.get_nodes

    def get_dialogue_root(self, context):
        state = _context_opening(context)
        if not state.get("team_registered", False):
            eligible, _ = _context_registration_status(context)
            return "opening_register_ready" if eligible else "opening_register_locked"
        return previous_root(self, context)

    def get_nodes(self, context):
        nodes = previous_nodes(self, context)
        _, missing = _context_registration_status(context)
        state = _context_opening(context)
        wins = int(state.get("creature_wins", 0))
        status_text = "  |  ".join(missing) if missing else "All requirements met."

        nodes["opening_register_locked"] = DialogueNode(
            id="opening_register_locked",
            speaker=self.name,
            emotion="serious",
            text=(
                "I have heard you can handle yourself, but the Ledger does not "
                "register a team on rumours. Settle your affairs, earn Muckford's "
                "trust, bring me proof you can kill, and keep the fee in hand. "
                f"Current record: {status_text}"
            ),
            on_enter_effects=["set_flag_intro_done"],
            choices=[
                DialogueChoice("Why the creature kills?", "opening_proof"),
                DialogueChoice("I'll return when I'm ready.", None),
            ],
        )
        nodes["opening_proof"] = DialogueNode(
            id="opening_proof",
            speaker=self.name,
            emotion="thinking",
            text=(
                "Because an arena manager who freezes at the first set of teeth "
                "gets five fighters killed. Hamo says you have potential. Show me "
                f"at least {REGISTRATION_CREATURE_WINS} real victories. You have {wins}."
            ),
            choices=[DialogueChoice("Understood.", None)],
        )
        nodes["opening_register_ready"] = DialogueNode(
            id="opening_register_ready",
            speaker=self.name,
            emotion="encouraging",
            text=(
                "Muckford is talking about you. You paid what you owed, did useful "
                "work, and came back from the vermin with blood on your boots. "
                "That is enough potential for the Rookie Circuit. Give me a team "
                f"name and {format_money(REGISTRATION_FEE_SP)} for the seal."
            ),
            on_enter_effects=["set_flag_intro_done"],
            choices=[
                DialogueChoice(
                    "Open the ledger. I'll name the team.",
                    None,
                    effects=["begin_team_registration", "close_chat"],
                ),
                DialogueChoice("Not yet.", None),
            ],
        )
        return nodes

    DwarfLeagueManager.get_dialogue_root = get_dialogue_root
    DwarfLeagueManager.get_nodes = get_nodes
    DwarfLeagueManager._muckford_opening_installed = True


def _patch_league_names() -> None:
    from leagues.league_engine import LeagueEngine, LeagueSeason, PLAYER_ID

    if getattr(LeagueSeason, "_muckford_opening_installed", False):
        return
    previous_team_name = LeagueSeason._team_name
    previous_grand = LeagueEngine.get_grand_slam_standings

    def _team_name(self, team_id):
        if team_id == PLAYER_ID:
            return _PLAYER_TEAM_NAME
        return previous_team_name(self, team_id)

    def get_grand_slam_standings(self):
        standings = previous_grand(self)
        name = getattr(self, "player_team_name", None) or _PLAYER_TEAM_NAME
        for entry in standings:
            if entry.get("team_id") == PLAYER_ID:
                entry["team_name"] = name
        return standings

    LeagueSeason._team_name = _team_name
    LeagueEngine.get_grand_slam_standings = get_grand_slam_standings
    LeagueSeason._muckford_opening_installed = True


def _patch_creature_victories() -> None:
    from gladiator import Gladiator

    if getattr(Gladiator, "_muckford_opening_installed", False):
        return
    previous_take_damage = Gladiator.take_damage

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        was_dead = bool(getattr(self, "is_dead", False))
        result = previous_take_damage(
            self, amount, damage_type, attacker=attacker, manager=manager
        )
        player = getattr(manager, "player_character", None) if manager else None
        hostile = getattr(self, "team_color", None) == ENEMY_TEAM
        if (
            not was_dead
            and getattr(self, "is_dead", False)
            and attacker is player
            and hostile
        ):
            state = _opening(manager)
            if state.get("intro_complete", False):
                state["creature_wins"] = int(state.get("creature_wins", 0)) + 1
                # Guarantee bounty proof so bad loot luck cannot lock progression.
                if "rat" in str(getattr(self, "name", "")).lower():
                    manager.inventory["Rat Tail"] = (
                        int(manager.inventory.get("Rat Tail", 0)) + 1
                    )
                if hasattr(manager, "record_deed"):
                    manager.record_deed(
                        "muckford_first_creature_win",
                        "proved capable against the creatures around Muckford",
                    )
        return result

    Gladiator.take_damage = take_damage
    Gladiator._muckford_opening_installed = True


def install_muckford_opening_core() -> None:
    _patch_game_manager()
    _patch_save_load()
    _patch_village_fighter_rewards()
    _patch_chat_effects()
    _patch_marda_dialogue()
    _patch_bram_dialogue()
    _patch_league_names()
    _patch_creature_victories()
