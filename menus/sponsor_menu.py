import pygame
from settings import *
from ui_kit import UIButton, draw_text, font_title, font_main, font_small, draw_panel, GOLD_COLOR, WHITE, GRAY, GREEN, RED
from menus.base_menu import BaseMenu
from sound_manager import sound_system
from sponsors.sponsor_data import SPONSORS, TIER_0_NAME, MANAGER_NAME

class SponsorMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        
        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)
        
        # Layout
        self.list_w = 400
        self.list_rect = pygame.Rect(50, 150, self.list_w, 600)
        self.details_rect = pygame.Rect(500, 150, 800, 600)
        
        self.selected_id = "shanty" # Oletusvalinta
        self.sponsor_buttons = []
        self._init_list()
        
        # Sopimusnappi (Placeholder logiikka)
        self.btn_sign = UIButton(self.details_rect.centerx - 100, self.details_rect.bottom - 80, 200, 50, "SIGN CONTRACT", None, GREEN)

    def _init_list(self):
        start_y = self.list_rect.top + 20
        for s_id, data in SPONSORS.items():
            btn = UIButton(self.list_rect.left + 20, start_y, self.list_w - 40, 60, data["name"], None, (40, 40, 50))
            btn.data_id = s_id
            self.sponsor_buttons.append(btn)
            start_y += 70

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        if self.btn_back.is_clicked(event):
            self.next_state = "manager_menu"
            sound_system.play_sound('click')
            return

        # Listan valinta
        if event.type == pygame.MOUSEBUTTONDOWN:
            for btn in self.sponsor_buttons:
                if btn.rect.collidepoint(mouse_pos):
                    self.selected_id = btn.data_id
                    sound_system.play_sound('click')
                    return
            
            # Sign contract (Placeholder)
            if self.btn_sign.rect.collidepoint(mouse_pos):
                # Tähän tulee myöhemmin logiikka sopimuksen tallentamiseen
                sound_system.play_sound('error') # "Not implemented yet" ääni tai click
                print(f"Contract requested with {self.selected_id}")

    def draw(self, screen):
        self.draw_themed_background(screen, mood="city")
        
        self.btn_back.check_hover(pygame.mouse.get_pos())
        self.btn_back.draw(screen)
        
        # Header
        _t = font_title.render("SPONSORSHIP CONTRACTS", True, GOLD_COLOR)
        self.draw_header_bar(screen, _t, y=10)
        draw_text(f"Circuit: {TIER_0_NAME}  |  Overseer: {MANAGER_NAME}", font_main, (180, 180, 180), screen, SCREEN_WIDTH // 2 - 220, 80)
        
        # --- LEFT LIST ---
        draw_panel(screen, self.list_rect.x, self.list_rect.y, self.list_rect.w, self.list_rect.h, (30, 30, 40))
        
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.sponsor_buttons:
            is_selected = (btn.data_id == self.selected_id)
            
            # Väritä valittu
            if is_selected:
                btn.base_color = (80, 80, 100)
                btn.hover_color = (90, 90, 110)
                pygame.draw.rect(screen, GOLD_COLOR, btn.rect.inflate(4, 4), 2, border_radius=8)
            else:
                btn.base_color = (40, 40, 50)
            
            btn.check_hover(mouse_pos)
            btn.draw(screen)

        # --- RIGHT DETAILS ---
        draw_panel(screen, self.details_rect.x, self.details_rect.y, self.details_rect.w, self.details_rect.h, (25, 25, 30))
        
        if self.selected_id:
            data = SPONSORS[self.selected_id]
            dx = self.details_rect.x + 40
            dy = self.details_rect.y + 40
            
            # Nimi ja Tyyppi
            draw_text(data["name"], font_title, data["color"], screen, dx, dy)
            draw_text(f"{data['type']}  •  {data['location']}", font_main, (200, 200, 200), screen, dx, dy + 50)
            
            # Kuvaus
            self._draw_multiline_text(screen, data["desc"], dx, dy + 90, font_small, WHITE, 700)
            
            # Goal
            dy += 160
            draw_text("OBJECTIVE:", font_main, GOLD_COLOR, screen, dx, dy)
            self._draw_multiline_text(screen, data["goal"], dx, dy + 30, font_small, (220, 220, 220), 700)
            
            # Benefits
            dy += 100
            draw_text("CONTRACT BENEFITS:", font_main, GREEN, screen, dx, dy)
            for i, ben in enumerate(data["benefits"]):
                draw_text(f"• {ben}", font_small, WHITE, screen, dx + 20, dy + 30 + (i * 25))
                
            # Politics
            dy += 120
            draw_text("POLITICAL STANCE:", font_main, (150, 150, 200), screen, dx, dy)
            self._draw_multiline_text(screen, data["politics"], dx, dy + 30, font_small, (180, 180, 200), 700)
            
            # Sign Button
            # Tarkista maine (placeholder)
            player_rep = self.manager.reputation
            req_rep = data.get("req_rep", 0)
            
            if player_rep >= req_rep:
                self.btn_sign.text = "SIGN CONTRACT"
                self.btn_sign.base_color = GREEN
                self.btn_sign.enabled = True
            else:
                self.btn_sign.text = f"REQ: {req_rep} REP"
                self.btn_sign.base_color = (100, 50, 50)
                self.btn_sign.enabled = False
                
            self.btn_sign.check_hover(mouse_pos)
            self.btn_sign.draw(screen)

    def _draw_multiline_text(self, surface, text, x, y, font, color, max_width):
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] < max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        lines.append(' '.join(current_line))
        
        for i, line in enumerate(lines):
            draw_text(line, font, color, surface, x, y + i * 20)
