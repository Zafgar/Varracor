"""Boil-Cider House 'The Span' — Rattlebridge inn and union hub."""

from __future__ import annotations

import pygame

from citys.rattlebridge.rattlebridge_art import load_rattlebridge_image
from citys.rattlebridge.rattlebridge_data import LOCAL_TEAMS
from menus.base_menu import BaseMenu
from settings import GOLD_COLOR, GRAY, GREEN, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from ui_kit import UIButton, draw_text, font_main, font_small, font_title, format_money


class TheSpanMenu(BaseMenu):
    REST_COST = 18

    def __init__(self, manager):
        super().__init__(manager)
        self.background = load_rattlebridge_image(
            "the_span", (SCREEN_WIDTH, SCREEN_HEIGHT)
        )
        self.feedback = ""
        self.feedback_timer = 0
        self.show_rumors = False
        cx = SCREEN_WIDTH // 2
        y = SCREEN_HEIGHT - 125
        self.btn_rest = UIButton(cx - 500, y, 280, 58,
                                 f"RENT BUNKS ({self.REST_COST} GP)", None, GREEN)
        self.btn_rumors = UIButton(cx - 190, y, 280, 58,
                                   "UNION RUMORS", None, (115, 145, 190))
        self.btn_talk = UIButton(cx + 120, y, 280, 58,
                                 "TALK TO HENDRIK", None, (170, 120, 65))
        self.btn_leave = UIButton(cx + 430, y, 220, 58,
                                  "LEAVE", None, GRAY)

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
            if self.show_rumors:
                self.show_rumors = False
            else:
                self._leave()
            return
        if self.btn_rest.is_clicked(event):
            self._rest()
        elif self.btn_rumors.is_clicked(event):
            self.show_rumors = not self.show_rumors
            sound_system.play_sound("click")
        elif self.btn_talk.is_clicked(event):
            self._talk()
        elif self.btn_leave.is_clicked(event):
            self._leave()

    def update(self):
        super().update()
        mouse = pygame.mouse.get_pos()
        for button in (self.btn_rest, self.btn_rumors,
                       self.btn_talk, self.btn_leave):
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
        screen.blit(self.background, (0, 0))
        shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        shade.fill((14, 8, 4, 90))
        screen.blit(shade, (0, 0))
        title = font_title.render("BOIL-CIDER HOUSE ‘THE SPAN’", True, GOLD_COLOR)
        self.draw_header_bar(screen, title, y=28)

        left = pygame.Rect(80, 155, 680, 650)
        right = pygame.Rect(800, 155, 1040, 650)
        self.draw_soft_panel(screen, left, alpha=215, border_alpha=185, radius=12)
        self.draw_soft_panel(screen, right, alpha=215, border_alpha=185, radius=12)

        draw_text("HENDRIK IRONSPAN", font_title, GOLD_COLOR,
                  screen, left.x + 28, left.y + 28)
        draw_text("Ironspan Union trusted keeper", font_small,
                  (175, 190, 205), screen, left.x + 30, left.y + 72)
        y = left.y + 118
        intro = (
            "Warm cider, union notices, bridgeguard gossip and disciplined "
            "workers fill the room. Hendrik permits no brawl without a cause "
            "the whole taproom accepts."
        )
        for line in self._wrap(intro, left.w - 60):
            draw_text(line, font_main, WHITE, screen, left.x + 30, y)
            y += 31
        y += 24
        draw_text("LODGING", font_main, (145, 210, 165),
                  screen, left.x + 30, y)
        y += 34
        draw_text("• Restores HP to at least 72%", font_small, WHITE,
                  screen, left.x + 42, y)
        y += 26
        draw_text("• Refills mana and stamina", font_small, WHITE,
                  screen, left.x + 42, y)
        y += 26
        draw_text("• Clears Minor injuries", font_small, WHITE,
                  screen, left.x + 42, y)
        y += 26
        draw_text("• Advances the world clock by 8 hours", font_small, WHITE,
                  screen, left.x + 42, y)
        draw_text(f"Funds: {format_money(getattr(self.manager, 'gold', 0))}",
                  font_main, GOLD_COLOR, screen, left.x + 30, left.bottom - 65)

        draw_text("RATTLEBRIDGE ARENA TALK", font_title, GOLD_COLOR,
                  screen, right.x + 28, right.y + 28)
        y = right.y + 86
        for team in LOCAL_TEAMS.values():
            card = pygame.Rect(right.x + 30, y, right.w - 60, 205)
            pygame.draw.rect(screen, (30, 31, 36), card, border_radius=10)
            pygame.draw.rect(screen, (100, 112, 125), card, 2, border_radius=10)
            draw_text(team["name"], font_main, WHITE, screen,
                      card.x + 22, card.y + 18)
            draw_text(f"Manager: {team['manager']}  |  Rep {team['reputation']}",
                      font_small, (175, 190, 205), screen,
                      card.x + 22, card.y + 52)
            draw_text(team["style"], font_small, (210, 205, 190),
                      screen, card.x + 22, card.y + 82)
            draw_text(team["relation"], font_small, (205, 165, 105),
                      screen, card.x + 22, card.y + 110)
            draw_text(" • ".join(team["members"]), font_small, GRAY,
                      screen, card.x + 22, card.y + 148)
            y += 230

        if self.show_rumors:
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

        if self.feedback_timer > 0 and self.feedback:
            box = pygame.Rect(310, 835, SCREEN_WIDTH - 620, 55)
            pygame.draw.rect(screen, (20, 20, 24), box, border_radius=9)
            pygame.draw.rect(screen, (180, 145, 85), box, 2, border_radius=9)
            draw_text(self.feedback, font_main, WHITE,
                      screen, box.x + 20, box.y + 15)

        for button in (self.btn_rest, self.btn_rumors,
                       self.btn_talk, self.btn_leave):
            button.draw(screen)
