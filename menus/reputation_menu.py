import pygame
from settings import *
from ui_kit import UIButton, draw_panel, draw_text, font_title, font_main, font_small, GOLD_COLOR, WHITE, GRAY
from menus.base_menu import BaseMenu
from sound_manager import sound_system
from reputation.reputation_data import REPUTATION_FACTIONS, get_rank_title

class ReputationMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)
        
        # Layout
        self.list_w = 450
        self.list_rect = pygame.Rect(50, 120, self.list_w, SCREEN_HEIGHT - 150)
        self.details_rect = pygame.Rect(550, 120, SCREEN_WIDTH - 600, SCREEN_HEIGHT - 150)
        
        self.scroll_y = 0
        self.max_scroll = 0
        
        self.selected_faction = None # (cat_id, faction_id, data)
        
        # Valitaan oletuksena ensimmäinen
        first_cat = list(REPUTATION_FACTIONS.keys())[0]
        first_fac = list(REPUTATION_FACTIONS[first_cat]["factions"].keys())[0]
        self.selected_faction = (first_cat, first_fac, REPUTATION_FACTIONS[first_cat]["factions"][first_fac])

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        if self.btn_back.is_clicked(event):
            self.next_state = "manager_menu"
            sound_system.play_sound('click')
            return

        if event.type == pygame.MOUSEWHEEL:
            if self.list_rect.collidepoint(mouse_pos):
                self.scroll_y = max(0, min(self.max_scroll, self.scroll_y - event.y * 30))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.list_rect.collidepoint(mouse_pos):
                # Hit test list items
                y_offset = self.list_rect.y - self.scroll_y + 10
                
                for cat_id, cat_data in REPUTATION_FACTIONS.items():
                    # Category Header takes space
                    y_offset += 40 
                    
                    for fac_id, fac_data in cat_data["factions"].items():
                        rect = pygame.Rect(self.list_rect.x + 10, y_offset, self.list_w - 40, 50)
                        if rect.collidepoint(mouse_pos):
                            self.selected_faction = (cat_id, fac_id, fac_data)
                            sound_system.play_sound('click')
                            return
                        y_offset += 60
                    
                    y_offset += 20 # Gap between categories

    def draw(self, screen):
        self.draw_themed_background(screen, mood="guild")
        
        self.btn_back.check_hover(pygame.mouse.get_pos())
        self.btn_back.draw(screen)
        
        _t = font_title.render("REPUTATION & STANDING", True, GOLD_COLOR)
        self.draw_header_bar(screen, _t, y=10)
        
        # --- LEFT LIST (Scrollable) ---
        draw_panel(screen, self.list_rect.x, self.list_rect.y, self.list_rect.w, self.list_rect.h, (30, 30, 40))
        
        # Calculate content height
        total_h = 20
        for cat_data in REPUTATION_FACTIONS.values():
            total_h += 40 + len(cat_data["factions"]) * 60 + 20
        self.max_scroll = max(0, total_h - self.list_rect.h)
        
        # Clip
        prev_clip = screen.get_clip()
        screen.set_clip(self.list_rect.inflate(-4, -4))
        
        y_offset = self.list_rect.y - self.scroll_y + 10
        mouse_pos = pygame.mouse.get_pos()
        
        for cat_id, cat_data in REPUTATION_FACTIONS.items():
            # Category Header
            draw_text(cat_data["label"], font_main, (200, 200, 200), screen, self.list_rect.x + 20, y_offset)
            pygame.draw.line(screen, (100, 100, 100), (self.list_rect.x + 20, y_offset + 30), (self.list_rect.right - 20, y_offset + 30), 1)
            y_offset += 40
            
            for fac_id, fac_data in cat_data["factions"].items():
                # Item Rect
                rect = pygame.Rect(self.list_rect.x + 10, y_offset, self.list_w - 40, 50)
                
                # Selection / Hover
                is_selected = self.selected_faction and self.selected_faction[1] == fac_id
                is_hover = rect.collidepoint(mouse_pos)
                
                bg_col = (50, 50, 60)
                if is_selected: bg_col = (70, 70, 90)
                elif is_hover: bg_col = (60, 60, 70)
                
                pygame.draw.rect(screen, bg_col, rect, border_radius=6)
                if is_selected:
                    pygame.draw.rect(screen, GOLD_COLOR, rect, 2, border_radius=6)
                
                # Name & Score
                score = self.manager.get_faction_rep(fac_id)
                col = fac_data.get("color", WHITE)
                
                draw_text(fac_data["name"], font_small, col, screen, rect.x + 10, rect.y + 15)
                draw_text(str(score), font_main, WHITE, screen, rect.right - 50, rect.y + 12)
                
                y_offset += 60
            
            y_offset += 20
            
        screen.set_clip(prev_clip)
        
        # --- RIGHT DETAILS ---
        draw_panel(screen, self.details_rect.x, self.details_rect.y, self.details_rect.w, self.details_rect.h, (25, 25, 30))
        
        if self.selected_faction:
            cat_id, fac_id, data = self.selected_faction
            score = self.manager.get_faction_rep(fac_id)
            rank_title = get_rank_title(score)
            
            dx = self.details_rect.x + 40
            dy = self.details_rect.y + 40
            
            # Header
            draw_text(data["name"], font_title, data["color"], screen, dx, dy)
            draw_text(f"Category: {REPUTATION_FACTIONS[cat_id]['label']}", font_small, (150, 150, 150), screen, dx, dy + 60)
            
            # Description
            self._draw_multiline_text(screen, data["desc"], dx, dy + 100, font_main, (220, 220, 220), 700)
            
            # Status Bar
            bar_y = dy + 200
            bar_w = 600
            bar_h = 30
            
            draw_text(f"Current Standing: {rank_title} ({score})", font_main, WHITE, screen, dx, bar_y - 30)
            
            # Progress bar background
            pygame.draw.rect(screen, (40, 40, 40), (dx, bar_y, bar_w, bar_h), border_radius=5)
            
            # Fill (0-100 scale for visual, clamped)
            # Jos infamy, punainen palkki
            fill_col = data["color"]
            if cat_id == "INFAMY": fill_col = (200, 50, 50)
            
            pct = max(0, min(1.0, score / 10000.0))
            pygame.draw.rect(screen, fill_col, (dx, bar_y, int(bar_w * pct), bar_h), border_radius=5)
            pygame.draw.rect(screen, (100, 100, 100), (dx, bar_y, bar_w, bar_h), 2, border_radius=5)
            
            # Threshold markers
            for th, title in [(1000, "Recog"), (3000, "Friend"), (6000, "Respect"), (9000, "Exalted")]:
                tx = dx + int(bar_w * (th / 10000.0))
                pygame.draw.line(screen, (150, 150, 150), (tx, bar_y - 5), (tx, bar_y + bar_h + 5), 2)
                draw_text(str(th), font_small, (150, 150, 150), screen, tx - 10, bar_y + bar_h + 10)

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
            draw_text(line, font, color, surface, x, y + i * 25)
