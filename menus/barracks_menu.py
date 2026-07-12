# menus/barracks_menu.py
import pygame
from menus.base_menu import BaseMenu
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRAY, GOLD_COLOR, GREEN
from ui_kit import draw_text, font_title, font_main, font_small, UIButton
from sound_manager import sound_system


class BarracksMenu(BaseMenu):
    """
    Pelaajan tiimitila (Team Quarters). Bramin antamat köyhät tilat, joissa
    voi hallita joukkuetta: varusteet (Guild) ja jutella jäsenten kanssa.
    """

    def __init__(self, manager):
        super().__init__(manager)
        cx = SCREEN_WIDTH // 2

        self.btn_equip = UIButton(cx - 330, SCREEN_HEIGHT - 120, 300, 60,
                                  "MANAGE EQUIPMENT", None, GREEN)
        self.btn_back = UIButton(cx + 30, SCREEN_HEIGHT - 120, 300, 60,
                                 "LEAVE", None, GRAY)
        self.card_rects = []  # (rect, unit)

    def _roster(self):
        roster = list(self.manager.my_team)
        if self.manager.player_character:
            roster = [self.manager.player_character] + roster
        return roster

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.next_state = "muckford_city"
            return

        if self.btn_equip.is_clicked(event):
            self.manager.guild_return_state = "barracks"
            self.next_state = "guild"
            sound_system.play_sound('click')
            return
        if self.btn_back.is_clicked(event):
            self.next_state = "muckford_city"
            sound_system.play_sound('click')
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, unit in self.card_rects:
                if rect.collidepoint(event.pos):
                    self._talk_to(unit)
                    return

    def _talk_to(self, unit):
        if unit is self.manager.player_character:
            self.manager.selected_hero = unit
            self.manager.guild_return_state = "barracks"
            self.next_state = "commander_skills"
            return
        menu = self.manager.open_roster_dialogue(unit)
        if menu:
            self.next_state = "dialogue_active"

    def update(self):
        super().update()

    def draw(self, screen):
        self.draw_themed_background(screen, "guild")
        title = font_title.render("TEAM QUARTERS", True, GOLD_COLOR)
        self.draw_header_bar(screen, title)
        draw_text("Bram's leftover shacks - but they're yours. Click a fighter to talk; gear them below.",
                  font_small, GRAY, screen, 60, 120)

        self.card_rects = []
        roster = self._roster()
        card_w, card_h = 210, 270
        gap = 30
        per_row = max(1, (SCREEN_WIDTH - 120) // (card_w + gap))
        start_x = 60
        start_y = 170
        mouse = pygame.mouse.get_pos()
        for i, unit in enumerate(roster):
            col = i % per_row
            row = i // per_row
            x = start_x + col * (card_w + gap)
            y = start_y + row * (card_h + 20)
            rect = pygame.Rect(x, y, card_w, card_h)
            hover = rect.collidepoint(mouse)
            self.card_rects.append((rect, unit))
            if hasattr(unit, "draw_info_card"):
                unit.draw_info_card(screen, x, y, card_w, card_h, hover=hover)
            else:
                self.draw_soft_panel(screen, rect)
                draw_text(getattr(unit, "name", "Unit"), font_main, WHITE,
                          screen, x + 10, y + 10)
            if unit is self.manager.player_character:
                draw_text("(You)", font_small, GOLD_COLOR, screen,
                          x + 10, y + card_h - 24)

        self.btn_equip.draw(screen)
        self.btn_back.draw(screen)


# Runtime extensions are installed during menu imports, before GameManager is
# instantiated in main.py. This keeps old saves and large existing city modules
# compatible while new systems become available globally.
try:
    from citys.mucford.farming_expansion import install_farming_expansion
    from citys.mucford.farming_hardening import install_farming_hardening
    from citys.mucford.farming_content import install_farming_content
    from citys.mucford.farming_content_hardening import (
        install_farming_content_hardening,
    )
    from citys.mucford.farming_stations import install_farming_stations
    from citys.mucford.farming_stations_hardening import (
        install_farming_stations_hardening,
    )
    from systems.material_integration import install_material_integration
    from systems.material_integration_hardening import (
        install_material_integration_hardening,
    )
    from systems.world_map_integration import install_world_map_integration
    from systems.rattlebridge_integration import install_rattlebridge_integration

    install_farming_expansion()
    install_farming_hardening()
    install_farming_content()
    install_farming_content_hardening()
    install_farming_stations()
    install_farming_stations_hardening()
    install_material_integration()
    install_material_integration_hardening()
    install_world_map_integration()
    install_rattlebridge_integration()
except Exception as exc:
    print(f"[RuntimeExtensions] Could not install: {exc}")
