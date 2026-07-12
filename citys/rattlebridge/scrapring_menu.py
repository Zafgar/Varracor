"""The Scrapring — Tier 1 arena district and Sera Quench operations hub."""

from __future__ import annotations

import pygame

from citys.rattlebridge.rattlebridge_art import load_rattlebridge_image
from citys.rattlebridge.rattlebridge_data import (
    LOCAL_TEAMS,
    SCRAPRING_HAZARDS,
)
from menus.base_menu import BaseMenu
from settings import GOLD_COLOR, GRAY, GREEN, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from systems.world_progression import arena_access_status, league_lore_tier, party_level
from ui_kit import UIButton, draw_text, font_main, font_small, font_title


class ScrapringMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.background = load_rattlebridge_image(
            "scrapring", (SCREEN_WIDTH, SCREEN_HEIGHT)
        )
        self.selected_hazard = "crushing_gears"
        self.feedback = ""
        self.feedback_timer = 0
        self.show_teams = False
        self.hazard_buttons = {}
        for index, hazard_id in enumerate(SCRAPRING_HAZARDS):
            data = SCRAPRING_HAZARDS[hazard_id]
            self.hazard_buttons[hazard_id] = UIButton(
                95,
                250 + index * 120,
                500,
                76,
                data["name"],
                None,
                (105, 91, 75),
            )
        self.btn_briefing = UIButton(680, SCREEN_HEIGHT - 130, 310, 60,
                                     "SERA’S BRIEFING", None, (175, 105, 75))
        self.btn_teams = UIButton(1020, SCREEN_HEIGHT - 130, 280, 60,
                                  "LOCAL TEAMS", None, (100, 135, 185))
        self.btn_league = UIButton(1330, SCREEN_HEIGHT - 130, 300, 60,
                                   "ENTER TIER 1 LEAGUE", None, GREEN)
        self.btn_leave = UIButton(1660, SCREEN_HEIGHT - 130, 200, 60,
                                  "LEAVE", None, GRAY)

    def on_enter(self):
        self.manager.city_spawn_point = "scrapring"
        self.manager.current_arena_location = "rattlebridge"
        self.manager.league_return_state = "rattlebridge_scrapring"
        self._sync_access()

    def _state(self):
        state = self.manager.npc_state.setdefault("rattlebridge", {})
        state.setdefault("sera_introduced", False)
        state.setdefault("sponsor_briefings", 0)
        state.setdefault("hazards_inspected", [])
        return state

    def _sync_access(self):
        ok, reason = arena_access_status(self.manager, "rattlebridge")
        self.btn_league.set_enabled(ok)
        self.btn_league.text = "ENTER TIER 1 LEAGUE" if ok else "TIER 1 LOCKED"
        self.access_reason = reason

    def _inspect_hazard(self, hazard_id):
        self.selected_hazard = hazard_id
        state = self._state()
        if hazard_id not in state["hazards_inspected"]:
            state["hazards_inspected"].append(hazard_id)
        self.feedback = f"Sera’s staff demonstrates {SCRAPRING_HAZARDS[hazard_id]['name']}."
        self.feedback_timer = 180
        sound_system.play_sound("click")

    def _briefing(self):
        state = self._state()
        state["sera_introduced"] = True
        state["sponsor_briefings"] += 1
        self.feedback = (
            "Sera: Win cleanly, finish the sponsor objective, and make sure "
            "the crowd remembers your team name."
        )
        self.feedback_timer = 300
        sound_system.play_sound("click")

    def _enter_league(self):
        ok, reason = arena_access_status(self.manager, "rattlebridge")
        if not ok:
            self.feedback = reason
            self.feedback_timer = 220
            sound_system.play_sound("error")
            return
        self.manager.current_arena_location = "rattlebridge"
        self.manager.league_return_state = "rattlebridge_scrapring"
        self.next_state = "league"
        sound_system.play_sound("click")

    def _leave(self):
        self.manager.city_spawn_point = "scrapring"
        self.next_state = "rattlebridge_city"
        sound_system.play_sound("click")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.show_teams:
                self.show_teams = False
            else:
                self._leave()
            return
        for hazard_id, button in self.hazard_buttons.items():
            if button.is_clicked(event):
                self._inspect_hazard(hazard_id)
                return
        if self.btn_briefing.is_clicked(event):
            self._briefing()
        elif self.btn_teams.is_clicked(event):
            self.show_teams = not self.show_teams
            sound_system.play_sound("click")
        elif self.btn_league.is_clicked(event):
            self._enter_league()
        elif self.btn_leave.is_clicked(event):
            self._leave()

    def update(self):
        super().update()
        self._sync_access()
        mouse = pygame.mouse.get_pos()
        for button in self.hazard_buttons.values():
            button.update_hover(mouse)
        for button in (self.btn_briefing, self.btn_teams,
                       self.btn_league, self.btn_leave):
            button.update_hover(mouse)
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    @staticmethod
    def _wrap(text, width, font=font_main):
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

    def draw(self, screen):
        screen.blit(self.background, (0, 0))
        shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        shade.fill((7, 8, 10, 112))
        screen.blit(shade, (0, 0))
        title = font_title.render("THE SCRAPRING — TIER 1 CIRCUIT", True, GOLD_COLOR)
        self.draw_header_bar(screen, title, y=25)

        left = pygame.Rect(55, 145, 590, 755)
        right = pygame.Rect(675, 145, SCREEN_WIDTH - 730, 755)
        self.draw_soft_panel(screen, left, alpha=220, border_alpha=190, radius=12)
        self.draw_soft_panel(screen, right, alpha=220, border_alpha=190, radius=12)

        draw_text("ARENA HAZARD TRAINING", font_title, GOLD_COLOR,
                  screen, left.x + 28, left.y + 28)
        draw_text("Inspect hazards before entering the match card.",
                  font_small, (190, 195, 200), screen,
                  left.x + 30, left.y + 73)
        for hazard_id, button in self.hazard_buttons.items():
            button.rect.x = left.x + 30
            if hazard_id == self.selected_hazard:
                pygame.draw.rect(screen, (215, 175, 95),
                                 button.rect.inflate(10, 10), 3,
                                 border_radius=10)
            button.draw(screen)

        hazard = SCRAPRING_HAZARDS[self.selected_hazard]
        draw_text("SERA QUENCH", font_title, GOLD_COLOR,
                  screen, right.x + 32, right.y + 28)
        draw_text("Tier 1 manager • sponsor architect • ruthless organizer",
                  font_small, (175, 195, 210), screen,
                  right.x + 34, right.y + 74)
        draw_text(
            f"Party Lv {party_level(self.manager)}  |  Registered Arena Tier {league_lore_tier(self.manager)}",
            font_main, WHITE, screen, right.x + 34, right.y + 118)
        color = GREEN if self.btn_league.enabled else (225, 165, 95)
        for index, line in enumerate(self._wrap(self.access_reason, right.w - 68, font_small)):
            draw_text(line, font_small, color, screen,
                      right.x + 34, right.y + 158 + index * 22)

        card = pygame.Rect(right.x + 34, right.y + 230,
                           right.w - 68, 260)
        pygame.draw.rect(screen, (29, 29, 33), card, border_radius=12)
        pygame.draw.rect(screen, (132, 118, 92), card, 2, border_radius=12)
        draw_text(hazard["name"], font_title, WHITE,
                  screen, card.x + 28, card.y + 24)
        draw_text(f"Telegraph: {hazard['telegraph_frames']} frames",
                  font_main, (215, 180, 105), screen,
                  card.x + 30, card.y + 76)
        draw_text(f"Active window: {hazard['active_frames']} frames",
                  font_main, (215, 180, 105), screen,
                  card.x + 30, card.y + 111)
        draw_text(f"Base damage: {hazard['damage']}", font_main,
                  (220, 130, 110) if hazard["damage"] else (160, 205, 180),
                  screen, card.x + 30, card.y + 146)
        y = card.y + 190
        for line in self._wrap(hazard["description"], card.w - 60):
            draw_text(line, font_main, (210, 205, 192),
                      screen, card.x + 30, y)
            y += 30

        objective = pygame.Rect(right.x + 34, right.y + 525,
                                right.w - 68, 145)
        pygame.draw.rect(screen, (42, 35, 34), objective, border_radius=10)
        pygame.draw.rect(screen, (158, 90, 75), objective, 2, border_radius=10)
        draw_text("SPONSOR OBJECTIVE SYSTEM", font_main, (230, 170, 110),
                  screen, objective.x + 24, objective.y + 18)
        objective_text = (
            "Tier 1 matches may add a rotating objective: hold a marked lane, "
            "avoid a hazard cycle, protect a sponsor banner, or finish with a "
            "specific formation. Victory pays the purse; presentation builds the brand."
        )
        y = objective.y + 56
        for line in self._wrap(objective_text, objective.w - 48, font_small):
            draw_text(line, font_small, WHITE, screen,
                      objective.x + 24, y)
            y += 22

        if self.show_teams:
            modal = pygame.Rect(300, 205, SCREEN_WIDTH - 600, 610)
            pygame.draw.rect(screen, (17, 18, 22), modal, border_radius=14)
            pygame.draw.rect(screen, (180, 145, 85), modal, 3, border_radius=14)
            draw_text("LOCAL TIER 1 TEAMS", font_title, GOLD_COLOR,
                      screen, modal.x + 32, modal.y + 25)
            y = modal.y + 88
            for team in LOCAL_TEAMS.values():
                row = pygame.Rect(modal.x + 32, y, modal.w - 64, 205)
                pygame.draw.rect(screen, (31, 32, 37), row, border_radius=10)
                pygame.draw.rect(screen, (100, 118, 130), row, 2, border_radius=10)
                draw_text(team["name"], font_title, WHITE,
                          screen, row.x + 24, row.y + 18)
                draw_text(f"Manager: {team['manager']} • Reputation {team['reputation']}",
                          font_small, (180, 195, 210), screen,
                          row.x + 26, row.y + 58)
                draw_text(team["style"], font_main, (215, 205, 188),
                          screen, row.x + 26, row.y + 92)
                draw_text(team["relation"], font_small, (220, 170, 105),
                          screen, row.x + 26, row.y + 126)
                draw_text(" • ".join(team["members"]), font_small, GRAY,
                          screen, row.x + 26, row.y + 162)
                y += 230
            draw_text("[ESC] close", font_small, GRAY,
                      screen, modal.right - 130, modal.bottom - 34)

        if self.feedback_timer > 0 and self.feedback:
            box = pygame.Rect(340, 870, SCREEN_WIDTH - 680, 50)
            pygame.draw.rect(screen, (18, 18, 22), box, border_radius=8)
            pygame.draw.rect(screen, (180, 135, 80), box, 2, border_radius=8)
            draw_text(self.feedback, font_main, WHITE,
                      screen, box.x + 20, box.y + 13)

        for button in (self.btn_briefing, self.btn_teams,
                       self.btn_league, self.btn_leave):
            button.draw(screen)
