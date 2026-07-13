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

        self.btn_equip = UIButton(cx - 480, SCREEN_HEIGHT - 120, 300, 60,
                                  "MANAGE EQUIPMENT", None, GREEN)
        self.btn_recruits = UIButton(cx - 150, SCREEN_HEIGHT - 120, 300, 60,
                                     "RECRUIT FIGHTERS", None, (120, 170, 230))
        self.btn_back = UIButton(cx + 180, SCREEN_HEIGHT - 120, 300, 60,
                                 "LEAVE", None, GRAY)
        self.card_rects = []       # (rect, unit)
        self.action_rects = []     # (rect, "skills"|"dismiss", unit)
        self.pending_dismiss = None  # varmistus: klikkaa kahdesti
        self.feedback = ""
        self.feedback_timer = 0

    def _roster(self):
        roster = list(self.manager.my_team)
        if self.manager.player_character:
            roster = [self.manager.player_character] + roster
        return roster

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.next_state = getattr(self.manager, "barracks_return_state",
                                      None) or "muckford_city"
            return

        if self.btn_equip.is_clicked(event):
            self.manager.guild_return_state = "barracks"
            self.next_state = "guild"
            sound_system.play_sound('click')
            return
        if self.btn_recruits.is_clicked(event):
            self.manager.recruit_return_state = "barracks"
            self.next_state = "recruit"
            sound_system.play_sound('click')
            return
        if self.btn_back.is_clicked(event):
            self.next_state = getattr(self.manager, "barracks_return_state",
                                      None) or "muckford_city"
            sound_system.play_sound('click')
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Korttien toimintonapit ensin (SKILLS / DISMISS)
            for rect, action, unit in self.action_rects:
                if rect.collidepoint(event.pos):
                    if action == "skills":
                        self.manager.selected_hero = unit
                        self.manager.skill_tree_return_state = "barracks"
                        self.next_state = ("commander_skills"
                                           if unit is self.manager.player_character
                                           else "skill_tree")
                        sound_system.play_sound('click')
                    elif action == "dismiss":
                        self._dismiss(unit)
                    return
            for rect, unit in self.card_rects:
                if rect.collidepoint(event.pos):
                    self._talk_to(unit)
                    return

    def _dismiss(self, unit):
        """Erottaa taistelijan tiimistä. Vaatii kaksi klikkausta
        (vahinkoerotusten estämiseksi). Commanderia ei voi erottaa."""
        if unit is self.manager.player_character:
            return
        if self.pending_dismiss is not unit:
            self.pending_dismiss = unit
            self.feedback = f"Click DISMISS again to release {unit.name}."
            self.feedback_timer = 240
            sound_system.play_sound('hover')
            return
        self.manager.my_team.remove(unit)
        self.manager.update_all_groups()
        self.pending_dismiss = None
        self.feedback = f"{unit.name} left the team."
        self.feedback_timer = 240
        sound_system.play_sound('click')

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
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    def draw(self, screen):
        self.draw_themed_background(screen, "guild")
        title = font_title.render("TEAM QUARTERS", True, GOLD_COLOR)
        self.draw_header_bar(screen, title)
        draw_text("Bram's leftover shacks - but they're yours. Click a fighter to talk; gear them below.",
                  font_small, GRAY, screen, 60, 120)

        self.card_rects = []
        self.action_rects = []
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
            y = start_y + row * (card_h + 58)
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

            # Toimintonapit kortin alle: SKILLS aina, DISMISS vain muille
            by = y + card_h + 6
            skills_rect = pygame.Rect(x, by, 100, 34)
            pygame.draw.rect(screen, (48, 60, 48), skills_rect, border_radius=7)
            pygame.draw.rect(screen, GREEN, skills_rect, 1, border_radius=7)
            draw_text("SKILLS", font_small, WHITE, screen,
                      skills_rect.x + 20, skills_rect.y + 8)
            self.action_rects.append((skills_rect, "skills", unit))
            if unit is not self.manager.player_character:
                dis_rect = pygame.Rect(x + 110, by, 100, 34)
                arming = self.pending_dismiss is unit
                pygame.draw.rect(screen, (86, 40, 36) if arming else (56, 40, 40),
                                 dis_rect, border_radius=7)
                pygame.draw.rect(screen, (220, 110, 90), dis_rect, 1,
                                 border_radius=7)
                draw_text("DISMISS", font_small,
                          (255, 200, 190) if arming else WHITE, screen,
                          dis_rect.x + 12, dis_rect.y + 8)
                self.action_rects.append((dis_rect, "dismiss", unit))

        if self.feedback_timer > 0 and self.feedback:
            box = pygame.Rect(60, SCREEN_HEIGHT - 180, 760, 42)
            pygame.draw.rect(screen, (22, 22, 26), box, border_radius=8)
            pygame.draw.rect(screen, (180, 145, 85), box, 2, border_radius=8)
            draw_text(self.feedback, font_small, WHITE, screen,
                      box.x + 16, box.y + 11)

        self.btn_equip.draw(screen)
        self.btn_recruits.draw(screen)
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
    from systems.muckford_opening_integration import (
        install_muckford_opening_integration,
    )

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
    install_muckford_opening_integration()
except Exception as exc:
    print(f"[RuntimeExtensions] Could not install: {exc}")
