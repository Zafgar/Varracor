"""Runtime integration for Bram's docket, promotion match and Tier 0 finale."""
from __future__ import annotations

import pygame

from systems.tier0_finale import (
    ensure_finale_state,
    finale_state_from_memory,
    promotion_lock_reason,
    finale_requirements,
    return_docket_to_bram,
)


_INSTALLED = False


def _patch_game_manager() -> None:
    from game_manager import GameManager

    if getattr(GameManager, "_tier0_finale_installed", False):
        return
    previous_init = GameManager.__init__
    previous_effect = GameManager.handle_dialogue_effect

    def __init__(self, *args, **kwargs):
        previous_init(self, *args, **kwargs)
        ensure_finale_state(self)

    def handle_dialogue_effect(self, effect):
        if effect == "return_promotion_docket":
            ok, message = return_docket_to_bram(self)
            try:
                color = (255, 215, 0) if ok else (225, 90, 80)
                self.vfx.show_damage(
                    self.player_character.rect.centerx,
                    self.player_character.rect.top - 42,
                    message,
                    color=color,
                )
            except Exception:
                pass
            self.pending_finale_message = message
            return ok
        return previous_effect(self, effect)

    GameManager.__init__ = __init__
    GameManager.handle_dialogue_effect = handle_dialogue_effect
    GameManager._tier0_finale_installed = True


def _patch_bram_dialogue() -> None:
    from npc.base_npc import DialogueChoice, DialogueNode
    from npc.dwarf_league_manager import DwarfLeagueManager

    # Opening integration may replace Bram's methods after this integration was
    # imported. Mark the actual wrappers rather than the class so this function
    # can safely re-wrap the newest methods and remain the outermost story layer.
    if (
        getattr(DwarfLeagueManager.get_dialogue_root, "_tier0_finale_wrapper", False)
        and getattr(DwarfLeagueManager.get_nodes, "_tier0_finale_wrapper", False)
    ):
        return
    previous_root = DwarfLeagueManager.get_dialogue_root
    previous_nodes = DwarfLeagueManager.get_nodes

    def get_dialogue_root(self, context):
        memory = context.get("memory", {})
        state = finale_state_from_memory(memory)
        inventory = context.get("inventory", {})
        flags = (memory.get("tier0_world") or {}).get("story_flags", {})
        kingsreach = (memory.get("global") or {}).get("kingsreach_toll", {})
        kingsreach_done = bool(flags.get("kingsreach_cleared") or kingsreach.get("completed"))
        has_docket = int(inventory.get("Crown Promotion Docket", 0)) > 0
        if kingsreach_done and has_docket and not state.get("docket_returned"):
            return "tier0_docket"
        if state.get("docket_returned") and not flags.get("tier1_promoted"):
            return "tier0_waiting"
        if flags.get("tier1_promoted") and not state.get("ceremony_complete"):
            return "tier0_promoted"
        return previous_root(self, context)

    def get_nodes(self, context):
        nodes = previous_nodes(self, context)
        memory = context.get("memory", {})
        finale_state_from_memory(memory)
        defeated = set((memory.get("tier0_world") or {}).get("defeated_bosses", ()))
        crisis = "a major Muckford crisis" if defeated else "the work still waiting outside the Yard"
        nodes["tier0_docket"] = DialogueNode(
            id="tier0_docket",
            speaker=self.name,
            emotion="thinking",
            text=(
                "That red Crown fold in your hand is Captain Dorn's promotion docket. "
                "Kingsreach does not issue those to tourists. Put it on my ledger and I can tie your road papers to the Rookie Dust standings."
            ),
            choices=[
                DialogueChoice(
                    text="Give Bram the Crown Promotion Docket.",
                    next_node_id="tier0_docket_accepted",
                    effects=["return_promotion_docket"],
                ),
                DialogueChoice(text="Not yet.", next_node_id=None),
            ],
        )
        nodes["tier0_docket_accepted"] = DialogueNode(
            id="tier0_docket_accepted",
            speaker=self.name,
            emotion="serious",
            text=(
                "Stamped and entered. Now the rules are simple: finish Top 2 across every Rookie Dust format, "
                f"prove you handled {crisis}, then win the promotion match. I will not sell Sera Quench a team that collapses outside the ring."
            ),
            choices=[
                DialogueChoice(text="Show me the league ledger.", next_node_id=None, effects=["enter_league"]),
                DialogueChoice(text="I will return when ready.", next_node_id=None),
            ],
        )
        nodes["tier0_waiting"] = DialogueNode(
            id="tier0_waiting",
            speaker=self.name,
            emotion="serious",
            text=(
                "The Crown docket is in my ledger. Your promotion now needs two proofs: a winning Rookie Dust season "
                "and a Muckford deed worth putting my name behind. Check the Grand Slam page; it will tell you what is missing."
            ),
            choices=[
                DialogueChoice(text="Open the Grand Slam ledger.", next_node_id=None, effects=["enter_league"]),
                DialogueChoice(text="I have more work to do.", next_node_id=None),
            ],
        )
        nodes["tier0_promoted"] = DialogueNode(
            id="tier0_promoted",
            speaker=self.name,
            emotion="encouraging",
            text=(
                "You won it. Do not leave through the back door like another hired blade. "
                "The Yard is gathering, Marda is pretending not to care, and Hamo has already tried to sell tickets to your farewell."
            ),
            choices=[DialogueChoice(text="Then let the Yard see us leave.", next_node_id=None)],
        )
        return nodes

    get_dialogue_root._tier0_finale_wrapper = True
    get_nodes._tier0_finale_wrapper = True
    DwarfLeagueManager.get_dialogue_root = get_dialogue_root
    DwarfLeagueManager.get_nodes = get_nodes


def _promotion_click(event, button) -> bool:
    return bool(
        event.type == pygame.MOUSEBUTTONDOWN
        and getattr(event, "button", 0) == 1
        and button.rect.collidepoint(getattr(event, "pos", pygame.mouse.get_pos()))
    )


def _patch_league_menu() -> None:
    from menus.league_menu import LeagueMenu
    from sound_manager import sound_system

    if getattr(LeagueMenu, "_tier0_finale_installed", False):
        return
    previous_handle = LeagueMenu.handle_event
    previous_draw = LeagueMenu.draw

    def handle_event(self, event):
        engine = self.manager.league_engine
        eligible = False
        try:
            eligible, _reason, _opponent = engine.check_promotion_eligibility()
        except Exception:
            pass
        if eligible and _promotion_click(event, self.btn_promote):
            status = finale_requirements(self.manager)
            if int(getattr(engine, "tier", 1)) == 1 and not status["ready"]:
                self.message = promotion_lock_reason(self.manager)
                try:
                    sound_system.play_sound("error")
                except Exception:
                    pass
                return
        return previous_handle(self, event)

    def draw(self, screen):
        engine = self.manager.league_engine
        try:
            eligible, _reason, _opponent = engine.check_promotion_eligibility()
        except Exception:
            eligible = False
        if eligible and int(getattr(engine, "tier", 1)) == 1:
            status = finale_requirements(self.manager)
            self.btn_promote.text = "PLAY FINAL MATCH!" if status["ready"] else "FINAL LOCKED"
            if not status["ready"] and not self.message:
                self.message = promotion_lock_reason(self.manager)
        else:
            self.btn_promote.text = "PLAY RANK UP!"
        return previous_draw(self, screen)

    LeagueMenu.handle_event = handle_event
    LeagueMenu.draw = draw
    LeagueMenu._tier0_finale_installed = True


def _patch_loot_screen() -> None:
    from menus.post_battle_menu import LootScreenMenu

    if getattr(LootScreenMenu, "_tier0_finale_installed", False):
        return
    previous_handle = LootScreenMenu.handle_event

    def handle_event(self, event):
        if self.btn_claim.is_clicked(event):
            self.manager.apply_rewards()
            if self.manager.is_game_over:
                self.next_state = "menu"
            elif getattr(self.manager, "match_mode", "") == "PROMOTION" and self.manager.match_result == "VICTORY":
                # GameManager.end_match already reports the promotion result. Only
                # apply the tier change here as a compatibility fallback.
                engine = getattr(self.manager, "league_engine", None)
                if engine and int(getattr(engine, "tier", 1)) < 2:
                    engine.promote_player()
                self.next_state = "promotion_ceremony"
            else:
                self.next_state = "hub"
            return
        return previous_handle(self, event)

    LootScreenMenu.handle_event = handle_event
    LootScreenMenu._tier0_finale_installed = True


def _patch_world_travel() -> None:
    import systems.world_progression as world_progression

    current = world_progression.location_status
    if getattr(current, "_tier0_finale_wrapper", False):
        return

    def location_status(manager, location_id):
        result = current(manager, location_id)
        if str(location_id) != "rattlebridge":
            return result
        state = ensure_finale_state(manager)
        flags = (
            getattr(manager, "npc_state", {})
            .get("tier0_world", {})
            .get("story_flags", {})
        )
        inventory = getattr(manager, "inventory", {})
        missing = []
        if not flags.get("tier1_promoted"):
            missing.append("formal Arena Tier 1 promotion")
        if int(inventory.get("Stamped Crown Travel Papers", 0)) <= 0:
            missing.append("Stamped Crown Travel Papers")
        if not state.get("ceremony_complete"):
            missing.append("Bram's Shanty Yard farewell and recommendation")
        if missing:
            result["can_travel"] = False
            result["reason"] = "Rattlebridge professional gate requires " + ", ".join(missing) + "."
        return result

    location_status._tier0_finale_wrapper = True
    world_progression.location_status = location_status


def install_tier0_finale_integration() -> None:
    global _INSTALLED
    # Bram may be wrapped later by the opening integration, so every call checks
    # the actual live method markers and repairs ordering if necessary.
    _patch_game_manager()
    _patch_bram_dialogue()
    _patch_league_menu()
    _patch_loot_screen()
    _patch_world_travel()
    _INSTALLED = True
