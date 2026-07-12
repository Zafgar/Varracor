"""Bridgeward Chapel-Hospital — expensive Tier 1 injury treatment."""

from __future__ import annotations

import pygame

from citys.rattlebridge.rattlebridge_art import load_rattlebridge_image
from menus.base_menu import BaseMenu
from settings import GOLD_COLOR, GRAY, GREEN, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from ui_kit import UIButton, draw_text, font_main, font_small, font_title, format_money


class BridgewardHospitalMenu(BaseMenu):
    SERVICES = {
        "triage": {
            "name": "Bridge Triage",
            "cost": 45,
            "description": "Heal roster to 55% HP and clear Minor injuries.",
        },
        "specialist": {
            "name": "Arena Specialist",
            "cost": 125,
            "description": "Heal roster to 90%; Serious injuries become Minor.",
        },
        "full": {
            "name": "Prior’s Full Recovery",
            "cost": 240,
            "description": "Full HP and remove all current injuries.",
        },
    }

    def __init__(self, manager):
        super().__init__(manager)
        self.background = load_rattlebridge_image(
            "bridgeward_hospital", (SCREEN_WIDTH, SCREEN_HEIGHT)
        )
        self.feedback = ""
        self.feedback_timer = 0
        self.selected = "triage"
        self.service_buttons = {}
        start_y = 300
        for index, service_id in enumerate(self.SERVICES):
            data = self.SERVICES[service_id]
            self.service_buttons[service_id] = UIButton(
                140,
                start_y + index * 150,
                540,
                92,
                f"{data['name']} — {data['cost']} GP",
                None,
                (115, 128, 105),
            )
        self.btn_treat = UIButton(
            SCREEN_WIDTH - 650,
            SCREEN_HEIGHT - 145,
            330,
            62,
            "AUTHORIZE TREATMENT",
            None,
            GREEN,
        )
        self.btn_leave = UIButton(
            SCREEN_WIDTH - 285,
            SCREEN_HEIGHT - 145,
            210,
            62,
            "LEAVE",
            None,
            GRAY,
        )

    def on_enter(self):
        self.manager.city_spawn_point = "hospital"

    def _roster(self):
        units = []
        commander = getattr(self.manager, "player_character", None)
        if commander:
            units.append(commander)
        units.extend(list(getattr(self.manager, "my_team", ())))
        return units

    def _injury_count(self):
        minor = 0
        serious = 0
        for unit in self._roster():
            severity = getattr(unit, "injury_severity", None)
            if severity == "Serious":
                serious += 1
            elif severity == "Minor" or getattr(unit, "injured", False):
                minor += 1
        return minor, serious

    def _treat(self):
        data = self.SERVICES[self.selected]
        cost = data["cost"]
        if int(getattr(self.manager, "gold", 0)) < cost:
            self.feedback = "Prior Jannik refuses treatment until payment clears."
            self.feedback_timer = 220
            sound_system.play_sound("error")
            return
        self.manager.gold -= cost
        for unit in self._roster():
            if self.selected == "triage":
                unit.current_hp = max(unit.current_hp, int(unit.max_hp * 0.55))
                if getattr(unit, "injury_severity", None) != "Serious":
                    unit.injured = False
                    unit.injury_severity = None
            elif self.selected == "specialist":
                unit.current_hp = max(unit.current_hp, int(unit.max_hp * 0.90))
                if getattr(unit, "injury_severity", None) == "Serious":
                    unit.injury_severity = "Minor"
                    unit.injured = True
                else:
                    unit.injured = False
                    unit.injury_severity = None
            else:
                unit.current_hp = unit.max_hp
                unit.injured = False
                unit.injury_severity = None
        state = self.manager.npc_state.setdefault("rattlebridge", {})
        state["hospital_spent"] = int(state.get("hospital_spent", 0)) + cost
        state["hospital_visits"] = int(state.get("hospital_visits", 0)) + 1
        self.feedback = (
            f"{data['name']} completed. Prior Jannik records every coin."
        )
        self.feedback_timer = 260
        sound_system.play_sound("coin")

    def _leave(self):
        self.manager.city_spawn_point = "hospital"
        self.next_state = "rattlebridge_city"
        sound_system.play_sound("click")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._leave()
            return
        for service_id, button in self.service_buttons.items():
            if button.is_clicked(event):
                self.selected = service_id
                sound_system.play_sound("click")
                return
        if self.btn_treat.is_clicked(event):
            self._treat()
        elif self.btn_leave.is_clicked(event):
            self._leave()

    def update(self):
        super().update()
        mouse = pygame.mouse.get_pos()
        for button in self.service_buttons.values():
            button.update_hover(mouse)
        self.btn_treat.update_hover(mouse)
        self.btn_leave.update_hover(mouse)
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    @staticmethod
    def _wrap(text, width):
        words = str(text).split()
        lines = []
        current = ""
        for word in words:
            trial = word if not current else f"{current} {word}"
            if font_main.size(trial)[0] <= width:
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
        shade.fill((8, 10, 12, 100))
        screen.blit(shade, (0, 0))
        title = font_title.render("BRIDGEWARD CHAPEL-HOSPITAL", True, GOLD_COLOR)
        self.draw_header_bar(screen, title, y=28)

        left = pygame.Rect(80, 145, 690, 760)
        right = pygame.Rect(805, 145, SCREEN_WIDTH - 885, 760)
        self.draw_soft_panel(screen, left, alpha=220, border_alpha=190, radius=12)
        self.draw_soft_panel(screen, right, alpha=220, border_alpha=190, radius=12)

        draw_text("PRIOR JANNIK VOSS", font_title, GOLD_COLOR,
                  screen, left.x + 32, left.y + 28)
        draw_text("Sacred medicine. Commercial accounting.", font_small,
                  (180, 190, 200), screen, left.x + 34, left.y + 74)
        draw_text("SELECT TREATMENT", font_main, WHITE,
                  screen, left.x + 34, left.y + 112)

        for service_id, button in self.service_buttons.items():
            button.rect.x = left.x + 34
            if service_id == self.selected:
                pygame.draw.rect(screen, (210, 180, 105),
                                 button.rect.inflate(10, 10), 3,
                                 border_radius=12)
            button.draw(screen)
            description = self.SERVICES[service_id]["description"]
            draw_text(description, font_small, (205, 202, 190), screen,
                      button.rect.x + 12, button.rect.bottom + 8)

        minor, serious = self._injury_count()
        draw_text("ROSTER CONDITION", font_title, GOLD_COLOR,
                  screen, right.x + 32, right.y + 28)
        draw_text(f"Minor injuries: {minor}", font_main,
                  (220, 190, 105), screen, right.x + 34, right.y + 90)
        draw_text(f"Serious injuries: {serious}", font_main,
                  (225, 120, 105), screen, right.x + 34, right.y + 130)
        draw_text(f"Available funds: {format_money(getattr(self.manager, 'gold', 0))}",
                  font_main, GOLD_COLOR, screen, right.x + 34, right.y + 180)

        selected = self.SERVICES[self.selected]
        card = pygame.Rect(right.x + 34, right.y + 245,
                           right.w - 68, 285)
        pygame.draw.rect(screen, (29, 30, 34), card, border_radius=10)
        pygame.draw.rect(screen, (120, 125, 118), card, 2, border_radius=10)
        draw_text(selected["name"], font_title, WHITE,
                  screen, card.x + 28, card.y + 24)
        draw_text(f"Price: {selected['cost']} GP", font_main, GOLD_COLOR,
                  screen, card.x + 30, card.y + 74)
        y = card.y + 125
        explanation = {
            "triage": (
                "Fast arena medicine for bruises, cuts and minor fractures. "
                "Serious injuries remain untreated."
            ),
            "specialist": (
                "Bridgeward surgeons reset major injuries and stabilize the "
                "team for the next match, but recovery is not complete."
            ),
            "full": (
                "Jannik reserves the chapel's best surgeons, holy lamps and "
                "private recovery beds for a complete restoration."
            ),
        }[self.selected]
        for line in self._wrap(explanation, card.w - 60):
            draw_text(line, font_main, (210, 205, 192), screen,
                      card.x + 30, y)
            y += 31

        quote = (
            "‘Healing is sacred. Specialist treatment is expensive.’"
        )
        draw_text(quote, font_main, (180, 170, 145),
                  screen, right.x + 34, right.bottom - 110)

        if self.feedback_timer > 0 and self.feedback:
            box = pygame.Rect(370, 900, SCREEN_WIDTH - 740, 50)
            pygame.draw.rect(screen, (20, 20, 24), box, border_radius=8)
            pygame.draw.rect(screen, (170, 145, 90), box, 2, border_radius=8)
            draw_text(self.feedback, font_main, WHITE,
                      screen, box.x + 20, box.y + 13)

        self.btn_treat.draw(screen)
        self.btn_leave.draw(screen)
