"""Persistent NPC, quest, fishing and boss progression for Whisper Marsh."""
from __future__ import annotations

import math
import random
from typing import List, Sequence

import pygame

from assets.tiles.prop import Prop
from settings import ENEMY_TEAM, GOLD_COLOR, GRAY, GREEN, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from ui_kit import draw_text, font_main, font_small
from units.villager import Villager
from units.whisper_pool_boss import WhisperPoolMaw


_INSTALLED = False


QUEST_OBJECTIVES = {
    0: "Speak with Surveyor Kessa Fenmark at the Survey Post.",
    1: "Build the Dry Shelter at the Survey Post.",
    2: "Find Ferryman Noll beside Whisper Pool.",
    3: "Build the Raised Boardwalk at the Survey Post.",
    4: "Survey all three Whisper Pool markers.",
    5: "Build the Tackle Bench at the Survey Post.",
    6: "Catch one fish from a marked bank.",
    7: "Defeat the Whisper Pool Maw.",
    8: "Whisper Marsh survey complete.",
}


def _safe_sound(name: str) -> None:
    try:
        sound_system.play_sound(name)
    except Exception:
        pass


def whisper_marsh_story_state(manager) -> dict:
    global_data = manager.npc_state.setdefault("global", {})
    state = global_data.setdefault("whisper_marsh_story", {})
    state.setdefault("quest_stage", 0)
    state.setdefault("ferryman_rescued", False)
    state.setdefault("mapped_points", [])
    state.setdefault("first_fish_caught", False)
    state.setdefault("fish_caught", 0)
    state.setdefault("catches", {})
    state.setdefault("boss_unlocked", False)
    state.setdefault("boss_defeated", False)
    state.setdefault("boss_reward_claimed", False)
    state.setdefault("intro_seen", False)
    state.setdefault("completed", False)
    return state


def sync_whisper_marsh_story(manager) -> bool:
    """Advance only prerequisite-driven stages and return whether state changed."""
    from citys.mucford.forest_excursion import outskirts_state

    state = whisper_marsh_story_state(manager)
    camp_stage = int(outskirts_state(manager).get("camp_stage", 0))
    stage = int(state.get("quest_stage", 0))
    changed = False

    if stage == 1 and camp_stage >= 1:
        state["quest_stage"] = 2
        changed = True
    elif stage == 3 and camp_stage >= 2:
        state["quest_stage"] = 4
        changed = True
    elif stage == 4 and len(set(state.get("mapped_points", ()))) >= 3:
        state["quest_stage"] = 5
        changed = True
    elif stage == 5 and camp_stage >= 3:
        state["quest_stage"] = 6
        changed = True
    elif stage == 6 and state.get("first_fish_caught"):
        state["quest_stage"] = 7
        state["boss_unlocked"] = True
        changed = True
    elif state.get("boss_defeated") and stage < 8:
        state["quest_stage"] = 8
        state["completed"] = True
        changed = True
    return changed


def marsh_objective(manager) -> str:
    sync_whisper_marsh_story(manager)
    stage = int(whisper_marsh_story_state(manager).get("quest_stage", 0))
    return QUEST_OBJECTIVES.get(stage, QUEST_OBJECTIVES[8])


class MarshStoryMarker(Prop):
    def __init__(self, marker_id: str, x: int, y: int, label: str, complete=False, style="survey"):
        super().__init__(x, y, 78, 88, color=(0, 0, 0))
        self.marker_id = str(marker_id)
        self.label = str(label)
        self.complete = bool(complete)
        self.style = style
        self.rect = pygame.Rect(x + 12, y + 46, 54, 35)
        self.image_pos = (x, y)
        self.has_shadow = True
        self.blocks_projectiles = False
        self._redraw()

    def _redraw(self):
        image = pygame.Surface((78, 88), pygame.SRCALPHA)
        if self.style == "ferryman":
            pygame.draw.ellipse(image, (74, 58, 42), (6, 56, 66, 20))
            pygame.draw.line(image, (115, 83, 49), (20, 67), (63, 31), 7)
            pygame.draw.arc(image, (176, 151, 91), (47, 12, 22, 22), 0, math.tau, 3)
            pygame.draw.line(image, (91, 70, 47), (58, 33), (58, 58), 4)
        else:
            pygame.draw.line(image, (75, 56, 39), (39, 84), (39, 18), 6)
            pygame.draw.polygon(image, (137, 104, 63), [(39, 18), (72, 31), (39, 45)])
            pygame.draw.rect(image, (181, 151, 93), (10, 48, 58, 25), border_radius=4)
            pygame.draw.line(image, (72, 82, 67), (17, 55), (61, 67), 2)
            pygame.draw.line(image, (72, 82, 67), (61, 55), (17, 67), 2)
        color = (75, 173, 103) if self.complete else (232, 188, 83)
        pygame.draw.circle(image, color, (15, 15), 9, 3)
        if self.complete:
            pygame.draw.line(image, color, (10, 15), (14, 20), 3)
            pygame.draw.line(image, color, (14, 20), (22, 9), 3)
        self.image = image


class MarshDialogueMixin:
    """Small dialogue state helper attached to ForestExcursionMenu instances."""

    @staticmethod
    def wrap(text: str, font, width: int) -> List[str]:
        lines = []
        current = ""
        for word in str(text).split():
            trial = word if not current else f"{current} {word}"
            if font.size(trial)[0] <= width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines


def _ensure_dialogue_fields(menu) -> None:
    if not hasattr(menu, "marsh_dialogue_active"):
        menu.marsh_dialogue_active = False
        menu.marsh_dialogue_name = ""
        menu.marsh_dialogue_pages = []
        menu.marsh_dialogue_index = 0


def _open_dialogue(menu, name: str, pages: Sequence[str]) -> None:
    _ensure_dialogue_fields(menu)
    menu.marsh_dialogue_name = str(name)
    menu.marsh_dialogue_pages = [str(page) for page in pages]
    menu.marsh_dialogue_index = 0
    menu.marsh_dialogue_active = True
    _safe_sound("click")


def _spawn_named_villager(name, race, x, y, role):
    npc = Villager(name, race, x, y, team_color=GREEN)
    npc.ai_controller = None
    npc.name = name
    npc.marsh_story_role = role
    return npc


def _refresh_story_props(menu) -> None:
    arena = menu.arena
    for prop in list(getattr(menu, "marsh_story_props", [])):
        if prop in arena.props:
            arena.props.remove(prop)
    menu.marsh_story_props = []
    menu.marsh_npcs = []
    menu.marsh_markers = []

    state = whisper_marsh_story_state(menu.manager)
    stage = int(state.get("quest_stage", 0))

    kessa = _spawn_named_villager("Surveyor Kessa Fenmark", "Human", 635, 390, "kessa")
    brik = _spawn_named_villager("Brik Sealrunner", "Goblin", 880, 455, "brik")
    menu.marsh_npcs.extend((kessa, brik))

    if stage == 2 and not state.get("ferryman_rescued"):
        noll = _spawn_named_villager("Ferryman Noll", "Human", 2525, 1515, "noll_lost")
        menu.marsh_npcs.append(noll)
        marker = MarshStoryMarker("noll_bell", 2460, 1470, "Ferryman's bell", style="ferryman")
        menu.marsh_markers.append(marker)
    elif state.get("ferryman_rescued"):
        noll = _spawn_named_villager("Ferryman Noll", "Human", 725, 455, "noll_safe")
        menu.marsh_npcs.append(noll)

    if stage == 4:
        mapped = set(state.get("mapped_points", ()))
        marker_data = (
            ("pool_west", 2460, 1260, "Survey western pool bank"),
            ("pool_east", 3330, 1420, "Survey eastern pool bank"),
            ("pool_south", 2900, 1810, "Survey southern pool bank"),
        )
        for marker_id, x, y, label in marker_data:
            marker = MarshStoryMarker(marker_id, x, y, label, marker_id in mapped)
            menu.marsh_markers.append(marker)

    menu.marsh_story_props = list(menu.marsh_npcs) + list(menu.marsh_markers)
    arena.props.extend(menu.marsh_story_props)


def _kessa_dialogue(menu) -> None:
    from citys.mucford.forest_excursion import outskirts_state

    state = whisper_marsh_story_state(menu.manager)
    stage = int(state.get("quest_stage", 0))
    camp_stage = int(outskirts_state(menu.manager).get("camp_stage", 0))
    if stage == 0:
        state["quest_stage"] = 1
        state["intro_seen"] = True
        sync_whisper_marsh_story(menu.manager)
        pages = (
            "Farmer Gus says you reopened the Low Fields road. Good. Out here, roads drown faster than people build them.",
            "Start with a Dry Shelter at the Survey Post. Then find Ferryman Noll. His bell stopped near Whisper Pool three nights ago.",
            "This marsh is open country, Commander. The level warning is advice, not a wall. Decide how much danger you can afford.",
        )
        try:
            menu.manager.record_tier0_event("flag", "whisper_marsh_survey_started")
        except Exception:
            pass
    elif stage == 1:
        pages = (f"Build the Dry Shelter at the Survey Post. Current camp stage: {camp_stage}/3.",)
    elif stage == 2:
        pages = ("Noll's brass ferry bell was last heard beyond the Greywash, near the western edge of Whisper Pool.",)
    elif stage == 3:
        pages = ("Noll is alive. Build the Raised Boardwalk so we can carry charts across the channel without losing them to the water.",)
    elif stage == 4:
        count = len(set(state.get("mapped_points", ())))
        pages = (f"Survey the three marked banks around Whisper Pool. Charts completed: {count}/3.",)
    elif stage == 5:
        pages = ("The pool is mapped. Finish the Tackle Bench. Noll believes the water only reveals its deepest paths to a hooked line.",)
    elif stage == 6:
        pages = ("Use any marked fishing bank and bring in one catch. Watch line tension; pulling without rest will snap it.",)
    elif stage == 7:
        pages = (
            "Your line woke something below the old ferry route. The Whisper Pool Maw has surfaced on the western bank.",
            "It is not guarding treasure. It is defending a nest older than Muckford. End the threat before it follows the fishers upstream.",
        )
    else:
        pages = (
            "The pool is charted, Noll is safe and the Maw is dead. The route toward Drowned Chapel can now be planned properly.",
            "Muckford finally has a marsh outpost instead of a damp place where people disappear.",
        )
    _open_dialogue(menu, "Surveyor Kessa Fenmark", pages)
    _refresh_story_props(menu)


def _brik_dialogue(menu) -> None:
    state = whisper_marsh_story_state(menu.manager)
    stage = int(state.get("quest_stage", 0))
    if stage < 2:
        pages = (
            "Hamo sent me with seals, blank bounty slips and strict instructions not to become monster food.",
            "Help Kessa establish the post. Once the road holds, Hamo can turn marsh kills into regular work.",
        )
    elif stage < 7:
        pages = (
            "Hamo pays for proof, not stories. Bog Tick shells, Spore Toad glands and anything with too many teeth all count.",
            "The deeper pool beasts grow stronger as the Survey Post improves. That is opportunity, provided you survive it.",
        )
    else:
        pages = (
            "A boss carcass beside a mapped fishing pool? Hamo will invent three contracts before breakfast.",
            "Kessa calls it a survey victory. I call it a new revenue category.",
        )
    _open_dialogue(menu, "Brik Sealrunner", pages)


def _noll_dialogue(menu, lost: bool) -> None:
    state = whisper_marsh_story_state(menu.manager)
    if lost and int(state.get("quest_stage", 0)) == 2:
        state["ferryman_rescued"] = True
        state["quest_stage"] = 3
        menu.manager.gold += 12
        pages = (
            "Easy! I am alive. The pool kept moving the bank every time the fog came down.",
            "Something struck the ferry from below. Four pale eyes, a mouth like a lantern cage. It stopped when my bell sank.",
            "Get me back to Kessa. I can mark the safe banks once the boardwalk is raised. Take 12 SP from my emergency tin.",
        )
        try:
            menu.manager.record_tier0_event("quest", "whisper_marsh_ferryman_rescued")
        except Exception:
            pass
        _refresh_story_props(menu)
    elif int(state.get("quest_stage", 0)) < 6:
        pages = (
            "The old ferry route cuts close to Whisper Pool. Map all three banks before casting a line.",
            "A ripple that moves against the wind is not a ripple. Remember that.",
        )
    elif int(state.get("quest_stage", 0)) == 6:
        pages = (
            "Cast at a marked bank. Set the hook on the splash, then reel while the line is green. Release before it reaches red.",
            "Greywash fish tire quickly. Whisper Pool fish fight like they remember every hook.",
        )
    else:
        pages = ("The ferry can run again when Kessa gives the word. I will not cross the pool until the Maw stays dead.",)
    _open_dialogue(menu, "Ferryman Noll", pages)


def _try_story_interaction(menu) -> bool:
    state = whisper_marsh_story_state(menu.manager)
    for npc in getattr(menu, "marsh_npcs", ()):
        if not menu._near(npc.rect, 72):
            continue
        role = getattr(npc, "marsh_story_role", "")
        if role == "kessa":
            _kessa_dialogue(menu)
        elif role == "brik":
            _brik_dialogue(menu)
        elif role == "noll_lost":
            _noll_dialogue(menu, True)
        else:
            _noll_dialogue(menu, False)
        return True

    if int(state.get("quest_stage", 0)) == 4:
        for marker in getattr(menu, "marsh_markers", ()):
            if marker.style != "survey" or not menu._near(marker.rect, 76):
                continue
            mapped = state.setdefault("mapped_points", [])
            if marker.marker_id not in mapped:
                mapped.append(marker.marker_id)
                marker.complete = True
                marker._redraw()
                _safe_sound("recruit")
                count = len(set(mapped))
                menu._flash(f"Whisper Pool charted: {count}/3")
                if count >= 3:
                    sync_whisper_marsh_story(menu.manager)
                    menu._flash("Pool survey complete. Build the Tackle Bench.")
                    _refresh_story_props(menu)
            return True
    return False


def _nearest_fishing_anchor(menu):
    if not whisper_marsh_story_state(menu.manager).get("first_fish_caught"):
        minimum_stage = 6
    else:
        minimum_stage = 6
    if int(whisper_marsh_story_state(menu.manager).get("quest_stage", 0)) < minimum_stage:
        return None
    if not getattr(menu.manager, "get_fishing_spots", lambda: [])():
        return None
    best = None
    best_distance = 10**9
    for anchor in menu.manager.get_fishing_spots():
        distance = math.hypot(menu.player.rect.centerx - anchor.x, menu.player.rect.centery - anchor.y)
        if distance < 92 and distance < best_distance:
            best = anchor
            best_distance = distance
    return best


def _try_start_fishing(menu) -> bool:
    anchor = _nearest_fishing_anchor(menu)
    if anchor is None:
        return False
    menu.manager.pending_fishing_anchor = anchor
    menu.manager.fishing_return_state = "forest_excursion"
    menu.manager.pending_local_area = "marsh_fishing"
    menu.next_state = "regional_staging"
    _safe_sound("click")
    return True


def _spawn_or_restore_boss(menu) -> None:
    state = whisper_marsh_story_state(menu.manager)
    menu.whisper_pool_boss = None
    if not state.get("boss_unlocked") or state.get("boss_defeated"):
        return
    boss = WhisperPoolMaw("Whisper Pool Maw", 2500, 1610, ENEMY_TEAM)
    menu.whisper_pool_boss = boss
    menu.monsters.add(boss)
    menu._set_event("The Whisper Pool Maw has surfaced beside the old ferry route!")


def _process_boss(menu) -> None:
    boss = getattr(menu, "whisper_pool_boss", None)
    if boss is None:
        return
    if getattr(boss, "pending_spawn", None):
        for spawn in list(boss.pending_spawn):
            menu.monsters.add(spawn)
        boss.pending_spawn = []
        menu._flash("The Maw calls Mire-Lurker Spawn from the pool!")
    if not boss.is_dead:
        return
    state = whisper_marsh_story_state(menu.manager)
    if state.get("boss_defeated"):
        return
    state["boss_defeated"] = True
    state["boss_unlocked"] = False
    state["quest_stage"] = 8
    state["completed"] = True
    if not state.get("boss_reward_claimed"):
        menu.manager.gold += 60
        menu.manager.reputation = int(getattr(menu.manager, "reputation", 0)) + 5
        menu.manager.inventory["Whisper Maw Scale"] = int(menu.manager.inventory.get("Whisper Maw Scale", 0)) + 1
        state["boss_reward_claimed"] = True
    try:
        menu.manager.record_tier0_event("boss", "whisper_pool_maw")
        menu.manager.record_tier0_event("quest", "whisper_marsh_survey_complete")
    except Exception:
        pass
    menu._flash("Whisper Pool secured. +60 SP, +5 reputation, Whisper Maw Scale.", 360)
    _refresh_story_props(menu)


def _draw_dialogue(menu, screen) -> None:
    if not getattr(menu, "marsh_dialogue_active", False):
        return
    panel = pygame.Rect(170, SCREEN_HEIGHT - 255, SCREEN_WIDTH - 340, 200)
    overlay = pygame.Surface(panel.size, pygame.SRCALPHA)
    overlay.fill((22, 26, 24, 238))
    screen.blit(overlay, panel.topleft)
    pygame.draw.rect(screen, (161, 143, 86), panel, 3, border_radius=9)
    draw_text(menu.marsh_dialogue_name, font_main, GOLD_COLOR, screen, panel.x + 24, panel.y + 18)
    page = menu.marsh_dialogue_pages[menu.marsh_dialogue_index]
    y = panel.y + 61
    for line in MarshDialogueMixin.wrap(page, font_main, panel.w - 48)[:4]:
        draw_text(line, font_main, WHITE, screen, panel.x + 24, y)
        y += 29
    draw_text("[E / Enter] continue    [Esc] close", font_small, GRAY, screen, panel.right - 355, panel.bottom - 27)


def _patch_regional_staging_fishing_factory() -> None:
    from menus.regional_staging_menu import RegionalStagingMenu

    if getattr(RegionalStagingMenu, "_marsh_fishing_factory_installed", False):
        return
    previous_new = RegionalStagingMenu.__new__

    def __new__(cls, manager, *args, **kwargs):
        if getattr(manager, "pending_local_area", None) == "marsh_fishing":
            manager.pending_local_area = None
            from minigames.marsh_fishing import MarshFishingMenu

            return MarshFishingMenu(manager)
        return previous_new(cls, manager, *args, **kwargs)

    RegionalStagingMenu.__new__ = staticmethod(__new__)
    RegionalStagingMenu._marsh_fishing_factory_installed = True


def _patch_forest_excursion_story() -> None:
    from citys.mucford.forest_excursion import ForestExcursionMenu

    if getattr(ForestExcursionMenu, "_whisper_story_installed", False):
        return

    previous_init = ForestExcursionMenu.__init__
    previous_enter = ForestExcursionMenu.on_enter
    previous_handle = ForestExcursionMenu.handle_event
    previous_update = ForestExcursionMenu.update
    previous_draw = ForestExcursionMenu.draw
    previous_prompt = ForestExcursionMenu._nearest_prompt

    def __init__(self, manager):
        previous_init(self, manager)
        _ensure_dialogue_fields(self)
        self.marsh_story_props = []
        self.marsh_npcs = []
        self.marsh_markers = []
        self.whisper_pool_boss = None

    def on_enter(self):
        result = previous_enter(self)
        _ensure_dialogue_fields(self)
        self.marsh_dialogue_active = False
        self.marsh_dialogue_pages = []
        # Replace the former random ferryman event with the persistent named quest.
        if getattr(self, "lost_traveler_pos", None):
            self.lost_traveler_pos = None
            self.lost_traveler_found = True
            if "ferryman" in str(getattr(self, "event_banner", "")).lower():
                self.event_banner = "An old ferry bell answers somewhere near Whisper Pool."
        sync_whisper_marsh_story(self.manager)
        _refresh_story_props(self)
        _spawn_or_restore_boss(self)
        return result

    def handle_event(self, event):
        _ensure_dialogue_fields(self)
        if self.marsh_dialogue_active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.marsh_dialogue_active = False
                    return
                if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.marsh_dialogue_index += 1
                    if self.marsh_dialogue_index >= len(self.marsh_dialogue_pages):
                        self.marsh_dialogue_active = False
                    return
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            if _try_story_interaction(self):
                return
            if _try_start_fishing(self):
                return
        return previous_handle(self, event)

    def update(self):
        if getattr(self, "marsh_dialogue_active", False):
            if self.feedback_timer > 0:
                self.feedback_timer -= 1
            return
        old_stage = int(whisper_marsh_story_state(self.manager).get("quest_stage", 0))
        result = previous_update(self)
        changed = sync_whisper_marsh_story(self.manager)
        new_stage = int(whisper_marsh_story_state(self.manager).get("quest_stage", 0))
        if changed:
            _refresh_story_props(self)
            if old_stage == 1 and new_stage == 2:
                self._flash("Dry Shelter complete. Find Ferryman Noll near Whisper Pool.")
            elif old_stage == 3 and new_stage == 4:
                self._flash("Boardwalk complete. Three pool survey markers are now active.")
            elif old_stage == 5 and new_stage == 6:
                self._flash("Tackle Bench complete. Fishing banks are now active.")
            elif old_stage == 6 and new_stage == 7:
                self._flash("The first catch disturbed something beneath Whisper Pool.")
                _spawn_or_restore_boss(self)
        _process_boss(self)
        return result

    def _nearest_prompt(self):
        for npc in getattr(self, "marsh_npcs", ()):
            if self._near(npc.rect, 72):
                return npc.rect, f"Talk to {npc.name}"
        state = whisper_marsh_story_state(self.manager)
        if int(state.get("quest_stage", 0)) == 4:
            for marker in getattr(self, "marsh_markers", ()):
                if marker.style == "survey" and not marker.complete and self._near(marker.rect, 76):
                    return marker.rect, marker.label
        anchor = _nearest_fishing_anchor(self)
        if anchor is not None:
            return pygame.Rect(anchor.x - 16, anchor.y - 16, 32, 32), f"Fish at {anchor.water_name}"
        return previous_prompt(self)

    def draw(self, screen):
        result = previous_draw(self, screen)
        state = whisper_marsh_story_state(self.manager)
        objective = QUEST_OBJECTIVES.get(int(state.get("quest_stage", 0)), QUEST_OBJECTIVES[8])
        objective_surface = font_small.render(f"MARSH SURVEY: {objective}", True, (214, 201, 145))
        screen.blit(objective_surface, (36, 108))
        _draw_dialogue(self, screen)
        return result

    ForestExcursionMenu.__init__ = __init__
    ForestExcursionMenu.on_enter = on_enter
    ForestExcursionMenu.handle_event = handle_event
    ForestExcursionMenu.update = update
    ForestExcursionMenu._nearest_prompt = _nearest_prompt
    ForestExcursionMenu.draw = draw
    ForestExcursionMenu._whisper_story_installed = True


def _patch_world_map_metadata() -> None:
    from lore.world_map_data import LOCATIONS

    location = LOCATIONS.get("whisper_marsh")
    if not location:
        return
    location["services"] = (
        "foraging",
        "monster hunting",
        "survey-post development",
        "fishing",
        "named marsh survey",
    )
    location["boss"] = "Whisper Pool Maw"
    location["story_state"] = "playable quest chain"


def install_whisper_marsh_story() -> None:
    global _INSTALLED
    _patch_world_map_metadata()
    _patch_regional_staging_fishing_factory()
    if _INSTALLED:
        return
    _patch_forest_excursion_story()
    _INSTALLED = True


_patch_world_map_metadata()
