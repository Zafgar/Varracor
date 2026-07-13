"""Muckford city progression and official team registration UI."""
from __future__ import annotations

import math

import pygame

from settings import GOLD_COLOR, GRAY, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from ui_kit import draw_text, font_main, font_small, font_title, format_money
from systems.muckford_opening_core import (
    REGISTRATION_CREATURE_WINS,
    REGISTRATION_FEE_SP,
    REGISTRATION_REPUTATION,
    TEAM_NAME_MAX,
    _clean_team_name,
    _opening,
    _sync_league_name,
    opening_progress,
    register_team,
)


def _patch_muckford_city() -> None:
    from citys.mucford.muckford_city_menu import MuckfordCityMenu

    if getattr(MuckfordCityMenu, "_muckford_opening_installed", False):
        return

    previous_init = MuckfordCityMenu.__init__
    previous_on_enter = MuckfordCityMenu.on_enter
    previous_handle = MuckfordCityMenu.handle_event
    previous_update = MuckfordCityMenu.update
    previous_draw = MuckfordCityMenu.draw

    def __init__(self, manager):
        previous_init(self, manager)
        self._team_registration_active = False
        self._team_name_buffer = ""
        self._team_registration_error = ""
        self._team_registration_result_timer = 0

    def _activate_registration(self):
        self._team_registration_active = True
        self._team_name_buffer = ""
        self._team_registration_error = "Type a team name."
        self.manager.team_registration_pending = False
        pygame.key.start_text_input()

    def on_enter(self):
        previous_on_enter(self)
        _sync_league_name(self.manager)
        if getattr(self.manager, "team_registration_pending", False):
            self._activate_team_registration()

    def _registration_buttons(self):
        panel = pygame.Rect(
            SCREEN_WIDTH // 2 - 430,
            SCREEN_HEIGHT // 2 - 230,
            860,
            460,
        )
        confirm = pygame.Rect(panel.centerx - 260, panel.bottom - 92, 240, 52)
        cancel = pygame.Rect(panel.centerx + 20, panel.bottom - 92, 240, 52)
        return panel, confirm, cancel

    def _confirm_registration(self):
        ok, message = register_team(self.manager, self._team_name_buffer)
        self._team_registration_error = message
        if ok:
            self._team_registration_active = False
            pygame.key.stop_text_input()
            self._team_registration_result_timer = 300
            try:
                self.manager.vfx.show_damage(
                    self.player.rect.centerx,
                    self.player.rect.top - 45,
                    f"TEAM REGISTERED: {self.manager.team_name}",
                    color=GOLD_COLOR,
                )
            except Exception:
                pass

    def handle_event(self, event):
        if getattr(self.manager, "team_registration_pending", False):
            self._activate_team_registration()

        if self._team_registration_active:
            _, confirm, cancel = self._registration_buttons()
            if event.type == pygame.TEXTINPUT:
                self._team_name_buffer = _clean_team_name(
                    self._team_name_buffer + event.text
                )
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self._team_name_buffer = self._team_name_buffer[:-1]
                elif event.key == pygame.K_RETURN:
                    self._confirm_team_registration()
                elif event.key == pygame.K_ESCAPE:
                    self._team_registration_active = False
                    pygame.key.stop_text_input()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if confirm.collidepoint(event.pos):
                    self._confirm_team_registration()
                elif cancel.collidepoint(event.pos):
                    self._team_registration_active = False
                    pygame.key.stop_text_input()
                return
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            gate = getattr(self, "arena_gate", None)
            # Route the gate to Bram for registration only while the opening's
            # registration phase is genuinely active (intro finished, team not
            # yet registered). Otherwise fall through to the normal gate -> league.
            opening = (self.manager.npc_state.get("global", {})
                       .get("muckford_opening", {}))
            opening_active = (opening.get("intro_complete", False)
                              and not self.manager.team_registered)
            if gate and opening_active:
                distance = math.hypot(
                    self.player.rect.centerx - gate.rect.centerx,
                    self.player.rect.bottom - gate.rect.bottom,
                )
                if distance < 110:
                    self.next_state = "dialogue:dwarf_league_manager"
                    try:
                        sound_system.play_sound("click")
                    except Exception:
                        pass
                    return

        return previous_handle(self, event)

    def update(self):
        if self._team_registration_active:
            return
        previous_update(self)
        if getattr(self.manager, "team_registration_pending", False):
            self._activate_team_registration()
            return

        state = _opening(self.manager)
        if (
            state.get("intro_complete", False)
            and int(state.get("creature_wins", 0)) >= REGISTRATION_CREATURE_WINS
            and not state.get("bram_hint_shown", False)
            and not state.get("team_registered", False)
            and not self.manager.active_dialogue
            and getattr(self, "hamo", None) is not None
        ):
            state["bram_hint_shown"] = True
            self.manager.start_dialogue(
                self.hamo,
                "Hamo's papers rustle as he looks over the blood on your gear. "
                "You have potential, stranger. Bram Mudhand should see this. "
                "Settle your debts, build some reputation, save the registration "
                "fee, then ask him to put a team name in the Ledger.",
                options=[
                    {
                        "text": "I'll talk to Bram.",
                        "action": "close_dialogue",
                    }
                ],
            )
        if self._team_registration_result_timer > 0:
            self._team_registration_result_timer -= 1

    def _draw_opening_tracker(self, screen):
        progress = opening_progress(self.manager)
        if progress["team_registered"]:
            panel = pygame.Rect(SCREEN_WIDTH - 410, 24, 380, 84)
            pygame.draw.rect(screen, (15, 17, 22), panel, border_radius=10)
            pygame.draw.rect(screen, GOLD_COLOR, panel, 2, border_radius=10)
            draw_text(
                "REGISTERED TEAM",
                font_small,
                GRAY,
                screen,
                panel.x + 18,
                panel.y + 13,
            )
            draw_text(
                progress["team_name"],
                font_main,
                GOLD_COLOR,
                screen,
                panel.x + 18,
                panel.y + 42,
            )
            return

        panel = pygame.Rect(SCREEN_WIDTH - 500, 24, 470, 190)
        pygame.draw.rect(screen, (15, 17, 22), panel, border_radius=10)
        pygame.draw.rect(screen, (170, 140, 85), panel, 2, border_radius=10)
        draw_text(
            "FOUND AN ARENA TEAM",
            font_main,
            GOLD_COLOR,
            screen,
            panel.x + 18,
            panel.y + 14,
        )
        lines = [
            (
                f"Marda debt: {format_money(progress['debt'])}",
                progress["debt"] <= 0,
            ),
            (
                f"Reputation: {progress['reputation']}/{REGISTRATION_REPUTATION}",
                progress["reputation"] >= REGISTRATION_REPUTATION,
            ),
            (
                f"Creature wins: {progress['creature_wins']}/{REGISTRATION_CREATURE_WINS}",
                progress["creature_wins"] >= REGISTRATION_CREATURE_WINS,
            ),
            (
                f"Fee: {format_money(progress['silver'])}/"
                f"{format_money(REGISTRATION_FEE_SP)}",
                progress["silver"] >= REGISTRATION_FEE_SP,
            ),
        ]
        for index, (label, done) in enumerate(lines):
            mark = "[X]" if done else "[ ]"
            color = (130, 230, 150) if done else WHITE
            draw_text(
                f"{mark} {label}",
                font_small,
                color,
                screen,
                panel.x + 20,
                panel.y + 55 + index * 28,
            )
        draw_text(
            "Talk to Bram at the Shanty Yard gate.",
            font_small,
            GRAY,
            screen,
            panel.x + 20,
            panel.bottom - 28,
        )

    def _draw_registration(self, screen):
        panel, confirm, cancel = self._registration_buttons()
        shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 205))
        screen.blit(shade, (0, 0))
        pygame.draw.rect(screen, (24, 24, 30), panel, border_radius=16)
        pygame.draw.rect(screen, GOLD_COLOR, panel, 3, border_radius=16)
        draw_text(
            "BRAM'S ROOKIE CIRCUIT LEDGER",
            font_title,
            GOLD_COLOR,
            screen,
            panel.x + 52,
            panel.y + 34,
        )
        draw_text(
            f"Registration seal: {format_money(REGISTRATION_FEE_SP)}",
            font_main,
            WHITE,
            screen,
            panel.x + 52,
            panel.y + 120,
        )
        draw_text(
            "This name will appear in league standings and match history.",
            font_small,
            GRAY,
            screen,
            panel.x + 52,
            panel.y + 158,
        )
        input_rect = pygame.Rect(panel.x + 52, panel.y + 210, panel.w - 104, 66)
        pygame.draw.rect(screen, (12, 13, 17), input_rect, border_radius=8)
        pygame.draw.rect(screen, (170, 145, 90), input_rect, 2, border_radius=8)
        shown = self._team_name_buffer or "Type team name..."
        color = WHITE if self._team_name_buffer else GRAY
        draw_text(
            shown,
            font_main,
            color,
            screen,
            input_rect.x + 18,
            input_rect.y + 20,
        )
        draw_text(
            f"{len(self._team_name_buffer)}/{TEAM_NAME_MAX}",
            font_small,
            GRAY,
            screen,
            input_rect.right - 70,
            input_rect.bottom + 8,
        )
        draw_text(
            self._team_registration_error,
            font_small,
            (255, 190, 120),
            screen,
            panel.x + 52,
            panel.y + 310,
        )
        for rect, label, color_value in (
            (confirm, "REGISTER TEAM", (65, 135, 80)),
            (cancel, "CANCEL", (95, 75, 70)),
        ):
            pygame.draw.rect(screen, color_value, rect, border_radius=8)
            pygame.draw.rect(screen, WHITE, rect, 2, border_radius=8)
            text = font_main.render(label, True, WHITE)
            screen.blit(text, text.get_rect(center=rect.center))

    def draw(self, screen):
        previous_draw(self, screen)
        self._draw_muckford_opening_tracker(screen)
        if self._team_registration_active:
            self._draw_team_registration(screen)

    MuckfordCityMenu.__init__ = __init__
    MuckfordCityMenu._activate_team_registration = _activate_registration
    MuckfordCityMenu._registration_buttons = _registration_buttons
    MuckfordCityMenu._confirm_team_registration = _confirm_registration
    MuckfordCityMenu.on_enter = on_enter
    MuckfordCityMenu.handle_event = handle_event
    MuckfordCityMenu.update = update
    MuckfordCityMenu._draw_muckford_opening_tracker = _draw_opening_tracker
    MuckfordCityMenu._draw_team_registration = _draw_registration
    MuckfordCityMenu.draw = draw
    MuckfordCityMenu._muckford_opening_installed = True


def install_muckford_city_opening() -> None:
    _patch_muckford_city()
