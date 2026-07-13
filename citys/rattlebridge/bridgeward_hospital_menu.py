"""Bridgeward Chapel-Hospital — expensive Tier 1 injury treatment."""

from __future__ import annotations

import pygame

from citys.rattlebridge.interior_scenes import get_scene
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
        # Koodilla maalattu kappelisairaala: aurinkoikkuna, vuoteet, karanteeni.
        self.scene = get_scene("chapel")
        self.feedback = ""
        self.feedback_timer = 0
        self.selected = "triage"
        self.service_buttons = {}
        start_y = 285
        for index, service_id in enumerate(self.SERVICES):
            data = self.SERVICES[service_id]
            self.service_buttons[service_id] = UIButton(
                96,
                start_y + index * 142,
                480,
                88,
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
        # Maalattu kappelisali kynttilöineen ja valokeiloineen taustana.
        self.scene.draw(screen)
        title = font_title.render("BRIDGEWARD CHAPEL-HOSPITAL", True, GOLD_COLOR)
        self.draw_header_bar(screen, title, y=24)

        left = pygame.Rect(60, 150, 560, 620)
        self.draw_soft_panel(screen, left, alpha=185, border_alpha=170, radius=12)

        draw_text("PRIOR JANNIK VOSS", font_main, GOLD_COLOR,
                  screen, left.x + 32, left.y + 24)
        draw_text("Sacred medicine. Commercial accounting.", font_small,
                  (180, 190, 200), screen, left.x + 34, left.y + 60)
        draw_text("SELECT TREATMENT", font_main, WHITE,
                  screen, left.x + 34, left.y + 104)

        for service_id, button in self.service_buttons.items():
            button.rect.x = left.x + 36
            if service_id == self.selected:
                pygame.draw.rect(screen, (210, 180, 105),
                                 button.rect.inflate(10, 10), 3,
                                 border_radius=12)
            button.draw(screen)
            description = self.SERVICES[service_id]["description"]
            draw_text(description, font_small, (215, 212, 200), screen,
                      button.rect.x + 12, button.rect.bottom + 6)

        # Kompakti tilannekortti oikealla - kappeli jää näkyviin.
        right = pygame.Rect(SCREEN_WIDTH - 590, 150, 530, 470)
        self.draw_soft_panel(screen, right, alpha=185, border_alpha=170, radius=12)
        minor, serious = self._injury_count()
        draw_text("ROSTER CONDITION", font_main, GOLD_COLOR,
                  screen, right.x + 30, right.y + 22)
        draw_text(f"Minor injuries: {minor}", font_small,
                  (220, 190, 105), screen, right.x + 32, right.y + 62)
        draw_text(f"Serious injuries: {serious}", font_small,
                  (225, 120, 105), screen, right.x + 32, right.y + 92)
        draw_text(f"Funds: {format_money(getattr(self.manager, 'gold', 0))}",
                  font_small, GOLD_COLOR, screen, right.x + 32, right.y + 122)

        selected = self.SERVICES[self.selected]
        draw_text(selected["name"], font_main, WHITE,
                  screen, right.x + 30, right.y + 172)
        draw_text(f"Price: {selected['cost']} GP", font_small, GOLD_COLOR,
                  screen, right.x + 32, right.y + 206)
        y = right.y + 244
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
        for line in self._wrap(explanation, right.w - 64):
            draw_text(line, font_small, (215, 212, 200), screen,
                      right.x + 32, y)
            y += 27
        draw_text("‘Healing is sacred. Specialist treatment is expensive.’",
                  font_small, (190, 180, 155),
                  screen, right.x + 30, right.bottom - 46)

        if self.feedback_timer > 0 and self.feedback:
            box = pygame.Rect(370, SCREEN_HEIGHT - 190, SCREEN_WIDTH - 740, 50)
            pygame.draw.rect(screen, (20, 20, 24), box, border_radius=8)
            pygame.draw.rect(screen, (170, 145, 90), box, 2, border_radius=8)
            draw_text(self.feedback, font_main, WHITE,
                      screen, box.x + 20, box.y + 13)

        self.btn_treat.draw(screen)
        self.btn_leave.draw(screen)
