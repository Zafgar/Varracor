"""Boil-Cider House 'The Span' — Rattlebridge inn and union hub."""

from __future__ import annotations

import pygame

from citys.rattlebridge.interior_scenes import get_scene
from citys.rattlebridge.rattlebridge_data import LOCAL_TEAMS
from menus.base_menu import BaseMenu
from settings import GOLD_COLOR, GRAY, GREEN, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from ui_kit import UIButton, draw_text, font_main, font_small, font_title, format_money


class TheSpanMenu(BaseMenu):
    REST_COST = 18

    def __init__(self, manager):
        super().__init__(manager)
        # Koodilla maalattu tupa: takka, siiderikattila, unionin väkeä.
        self.scene = get_scene("span")
        self.feedback = ""
        self.feedback_timer = 0
        self.show_rumors = False
        self.show_teams = False
        cx = SCREEN_WIDTH // 2
        y = SCREEN_HEIGHT - 96
        self.btn_rest = UIButton(cx - 640, y, 270, 58,
                                 f"RENT BUNKS ({self.REST_COST} GP)", None, GREEN)
        self.btn_rumors = UIButton(cx - 350, y, 250, 58,
                                   "UNION RUMORS", None, (115, 145, 190))
        self.btn_teams = UIButton(cx - 80, y, 250, 58,
                                  "ARENA TALK", None, (150, 110, 150))
        self.btn_talk = UIButton(cx + 190, y, 270, 58,
                                 "TALK TO HENDRIK", None, (170, 120, 65))
        self.btn_leave = UIButton(cx + 480, y, 190, 58,
                                  "LEAVE", None, GRAY)
        self._buttons = (self.btn_rest, self.btn_rumors, self.btn_teams,
                         self.btn_talk, self.btn_leave)

    def on_enter(self):
        self.manager.city_spawn_point = "the_span"
        try:
            sound_system.play_music("assets/music/tavern_theme.mp3")
        except Exception:
            pass

    def _roster(self):
        roster = []
        if getattr(self.manager, "player_character", None):
            roster.append(self.manager.player_character)
        roster.extend(list(getattr(self.manager, "my_team", ())))
        return roster

    def _advance_hours(self, hours):
        clock = getattr(self.manager, "world_clock", None)
        if not clock:
            return
        clock.minutes += hours * 60.0
        while clock.minutes >= 1440:
            clock.minutes -= 1440
            clock.advance_day()

    def _rest(self):
        if int(getattr(self.manager, "gold", 0)) < self.REST_COST:
            self.feedback = "Hendrik does not extend credit to arena teams."
            self.feedback_timer = 180
            sound_system.play_sound("error")
            return
        self.manager.gold -= self.REST_COST
        for unit in self._roster():
            unit.current_hp = min(
                unit.max_hp,
                max(unit.current_hp, int(unit.max_hp * 0.72)),
            )
            unit.current_mana = getattr(unit, "max_mana", 0)
            unit.current_stamina = getattr(unit, "max_stamina", 100)
            if getattr(unit, "injury_severity", None) == "Minor":
                unit.injured = False
                unit.injury_severity = None
        self._advance_hours(8)
        self.feedback = "The team rests in dry union bunks. Minor injuries settle."
        self.feedback_timer = 240
        sound_system.play_sound("coin")

    def _talk(self):
        state = self.manager.npc_state.setdefault("rattlebridge", {})
        state["hendrik_spoken"] = True
        sightings = int(state.get("hush_mantle_sightings", 0))
        if sightings:
            text = (
                "Hendrik lowers his voice: every silent-fog sighting was near "
                "a cargo bell or an unguarded lower stair."
            )
        else:
            text = (
                "Hendrik: Warm cider, dry boots, and no fighting without cause. "
                "Earn the union's trust below the bridge."
            )
        self.feedback = text
        self.feedback_timer = 360
        sound_system.play_sound("click")

    def _leave(self):
        self.manager.city_spawn_point = "the_span"
        self.next_state = "rattlebridge_city"
        sound_system.play_sound("click")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.show_rumors or self.show_teams:
                self.show_rumors = False
                self.show_teams = False
            else:
                self._leave()
            return
        if self.btn_rest.is_clicked(event):
            self._rest()
        elif self.btn_rumors.is_clicked(event):
            self.show_rumors = not self.show_rumors
            self.show_teams = False
            sound_system.play_sound("click")
        elif self.btn_teams.is_clicked(event):
            self.show_teams = not self.show_teams
            self.show_rumors = False
            sound_system.play_sound("click")
        elif self.btn_talk.is_clicked(event):
            self._talk()
        elif self.btn_leave.is_clicked(event):
            self._leave()

    def update(self):
        super().update()
        mouse = pygame.mouse.get_pos()
        for button in self._buttons:
            button.update_hover(mouse)
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    @staticmethod
    def _wrap(text, width):
        words = text.split()
        lines = []
        current = ""
        for word in words:
            trial = word if not current else f"{current} {word}"
            if font_main.size(trial)[0] <= width:
                current = trial
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def draw(self, screen):
        # Maalattu tupa animaatioineen on näkymän tähti.
        self.scene.draw(screen)
        title = font_title.render("BOIL-CIDER HOUSE ‘THE SPAN’", True, GOLD_COLOR)
        self.draw_header_bar(screen, title, y=24)

        # Kompakti majoituskortti - ei peitä tupaa.
        card = pygame.Rect(36, SCREEN_HEIGHT - 420, 470, 280)
        self.draw_soft_panel(screen, card, alpha=185, border_alpha=170, radius=12)
        draw_text("HENDRIK IRONSPAN", font_main, GOLD_COLOR,
                  screen, card.x + 24, card.y + 20)
        draw_text("Ironspan Union trusted keeper", font_small,
                  (175, 190, 205), screen, card.x + 24, card.y + 52)
        bullets = (
            "Bunks restore HP to 72%+, mana & stamina",
            "Minor injuries settle overnight",
            "Advances the world clock by 8 hours",
        )
        y = card.y + 96
        for line in bullets:
            draw_text(f"• {line}", font_small, WHITE, screen, card.x + 28, y)
            y += 30
        draw_text(f"Funds: {format_money(getattr(self.manager, 'gold', 0))}",
                  font_main, GOLD_COLOR, screen, card.x + 24, card.bottom - 48)

        if self.show_teams:
            self._draw_teams_modal(screen)
        if self.show_rumors:
            self._draw_rumors_modal(screen)

        if self.feedback_timer > 0 and self.feedback:
            box = pygame.Rect(310, SCREEN_HEIGHT - 175, SCREEN_WIDTH - 620, 55)
            pygame.draw.rect(screen, (20, 20, 24), box, border_radius=9)
            pygame.draw.rect(screen, (180, 145, 85), box, 2, border_radius=9)
            draw_text(self.feedback, font_main, WHITE,
                      screen, box.x + 20, box.y + 15)

        for button in self._buttons:
            button.draw(screen)

    def _draw_teams_modal(self, screen):
        modal = pygame.Rect(340, 130, SCREEN_WIDTH - 680, 720)
        pygame.draw.rect(screen, (17, 18, 22), modal, border_radius=14)
        pygame.draw.rect(screen, (150, 110, 150), modal, 3, border_radius=14)
        draw_text("RATTLEBRIDGE ARENA TALK", font_title, GOLD_COLOR,
                  screen, modal.x + 32, modal.y + 24)
        y = modal.y + 90
        for team in LOCAL_TEAMS.values():
            card = pygame.Rect(modal.x + 30, y, modal.w - 60, 195)
            pygame.draw.rect(screen, (30, 31, 36), card, border_radius=10)
            pygame.draw.rect(screen, (100, 112, 125), card, 2, border_radius=10)
            draw_text(team["name"], font_main, WHITE, screen,
                      card.x + 22, card.y + 16)
            draw_text(f"Manager: {team['manager']}  |  Rep {team['reputation']}",
                      font_small, (175, 190, 205), screen,
                      card.x + 22, card.y + 50)
            draw_text(team["style"], font_small, (210, 205, 190),
                      screen, card.x + 22, card.y + 78)
            draw_text(team["relation"], font_small, (205, 165, 105),
                      screen, card.x + 22, card.y + 106)
            draw_text(" • ".join(team["members"]), font_small, GRAY,
                      screen, card.x + 22, card.y + 142)
            y += 215
        draw_text("[ESC] close", font_small, GRAY,
                  screen, modal.right - 130, modal.bottom - 35)

    def _draw_rumors_modal(self, screen):
        modal = pygame.Rect(360, 260, SCREEN_WIDTH - 720, 470)
        pygame.draw.rect(screen, (17, 18, 22), modal, border_radius=14)
        pygame.draw.rect(screen, (185, 145, 85), modal, 3, border_radius=14)
        draw_text("UNION RUMORS", font_title, GOLD_COLOR,
                  screen, modal.x + 32, modal.y + 26)
        rumors = (
            "• Three lower-deck grates were welded shut from the inside.",
            "• A cargo bell vanished into fog without making a sound.",
            "• Sera is testing sponsor objectives during ordinary matches.",
            "• Bridgeguard Five refuses to patrol Canal Seven after midnight.",
            "• Rivet Row buyers are quietly paying extra for Nightcap Fungus.",
        )
        ry = modal.y + 95
        for rumor in rumors:
            draw_text(rumor, font_main, WHITE, screen, modal.x + 45, ry)
            ry += 58
        draw_text("[ESC] close", font_small, GRAY,
                  screen, modal.right - 130, modal.bottom - 35)
