import pygame
from settings import *
from ui_kit import UIButton, draw_panel, draw_text, font_title, font_main, font_small, GOLD_COLOR, WHITE, GRAY, GREEN, RED, ORANGE, format_money
from menus.base_menu import BaseMenu
from sound_manager import sound_system
from loot_data import BLUEPRINTS

class WorkshopMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)
        
        # Tabs
        self.tabs = ["WEAPONS", "ARMOR", "SHIELDS", "USABLE", "MATERIALS"]
        self.active_tab = "WEAPONS"
        self.tab_buttons = []
        
        # Layout
        total_w = 1400
        gap = 30
        left_w = 500
        right_w = total_w - left_w - gap
        start_x = (SCREEN_WIDTH - total_w) // 2
        self.left_rect = pygame.Rect(start_x, 180, left_w, 700)
        self.right_rect = pygame.Rect(start_x + left_w + gap, 180, right_w, 700)
        
        self.selected_recipe = None
        
        # Craft button (centered in right panel bottom)
        cx = self.right_rect.centerx
        self.btn_craft = UIButton(cx - 100, self.right_rect.bottom - 100, 200, 60, "CRAFT", None, GREEN)
        
        self.scroll_y = 0
        self.max_scroll = 0
        
        self._build_tabs()

    def update(self):
        pass

    def _build_tabs(self):
        self.tab_buttons = []
        
        # Center tabs
        tab_w = 180
        tab_h = 50
        gap = 10
        total_w = len(self.tabs) * tab_w + (len(self.tabs) - 1) * gap
        start_x = (SCREEN_WIDTH - total_w) // 2
        y = 110
        
        for i, t in enumerate(self.tabs):
            x = start_x + i * (tab_w + gap)
            self.tab_buttons.append(UIButton(x, y, tab_w, tab_h, t, None, GRAY))

    def get_filtered_recipes(self):
        res = []
        for name, data in BLUEPRINTS.items():
            t = data.get('type', 'misc')
            
            if self.active_tab == "WEAPONS" and t == 'weapon': res.append(name)
            elif self.active_tab == "ARMOR" and t in ['armor', 'helmet']: res.append(name) # Armor & Helmets
            elif self.active_tab == "SHIELDS" and t == 'shield': res.append(name)
            elif self.active_tab == "USABLE" and t == 'usable': res.append(name)
            
        return res

    def can_craft(self, recipe_name):
        data = BLUEPRINTS[recipe_name]
        # 1. Gold check
        if self.manager.gold < data['cost']: return False
        # Cheat Mode bypass
        if CHEAT_MODE: return True
        # 2. Mats check
        for mat, count in data['mats'].items():
            if self.manager.inventory.get(mat, 0) < count:
                return False
        return True

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        if event.type == pygame.MOUSEWHEEL:
            if self.left_rect.collidepoint(mouse_pos):
                self.scroll_y = max(0, min(self.max_scroll, self.scroll_y - event.y * 30))
        
        if self.btn_back.is_clicked(event):
            self.next_state = "workshop_locations"
            sound_system.play_sound('click')
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Tabs
            for b in self.tab_buttons:
                if b.rect.collidepoint(mouse_pos):
                    self.active_tab = b.text
                    self.selected_recipe = None
                    self.scroll_y = 0 # Reset scroll
                    sound_system.play_sound('click')
                    return

            # Recipe List
            recipes = self.get_filtered_recipes()
            
            # Calculate list geometry for hit testing
            item_h = 70
            list_top = self.left_rect.top + 20
            
            # Only check clicks inside the left panel
            if self.left_rect.collidepoint(mouse_pos):
                # Adjust mouse_y by scroll
                relative_y = mouse_pos[1] - list_top + self.scroll_y
                if relative_y >= 0:
                    idx = int(relative_y // item_h)
                    if 0 <= idx < len(recipes):
                        self.selected_recipe = recipes[idx]
                        sound_system.play_sound('click')
                        return

            # Craft Button
            if self.selected_recipe and self.btn_craft.rect.collidepoint(mouse_pos):
                if self.can_craft(self.selected_recipe):
                    if self.manager.craft_item(self.selected_recipe, None):
                        sound_system.play_sound('recruit') # Craft sound
                    else:
                        sound_system.play_sound('error')
                else:
                    sound_system.play_sound('error')

    def _draw_materials(self, screen, mouse_pos):
        inv = self.manager.inventory
        # Filter out zero count items just in case
        items = sorted([(k, v) for k, v in inv.items() if v > 0])
        
        item_h = 70
        
        # Calculate max scroll
        total_h = len(items) * item_h
        view_h = self.left_rect.height - 40
        self.max_scroll = max(0, total_h - view_h)
        
        # Clip for scrolling
        prev_clip = screen.get_clip()
        clip_rect = self.left_rect.inflate(-20, -20)
        screen.set_clip(clip_rect)
        
        start_y = self.left_rect.top + 20 - self.scroll_y
        
        if not items:
            draw_text("No materials found.", font_main, GRAY, screen, self.left_rect.centerx - 80, self.left_rect.top + 50)

        for i, (name, count) in enumerate(items):
            y = start_y + i * item_h
            if y + item_h < self.left_rect.top or y > self.left_rect.bottom: continue
            
            rect = pygame.Rect(self.left_rect.left + 20, y, self.left_rect.width - 40, item_h - 10)
            is_hover = rect.collidepoint(mouse_pos)
            col = (50, 50, 60) if not is_hover else (70, 70, 80)
            
            pygame.draw.rect(screen, col, rect, border_radius=8)
            pygame.draw.rect(screen, (80, 80, 90), rect, 1, border_radius=8)
            draw_text(name, font_main, WHITE, screen, rect.x + 20, rect.y + 18)
            draw_text(f"x{count}", font_main, GOLD_COLOR, screen, rect.right - 80, rect.y + 18)

        screen.set_clip(prev_clip)

    def draw(self, screen):
        # Background
        self.draw_themed_background(screen, mood="forge")
        
        self.btn_back.check_hover(pygame.mouse.get_pos())
        self.btn_back.draw(screen)
        
        draw_text("WORKSHOP", font_title, ORANGE, screen, SCREEN_WIDTH // 2 - 100, 40)
        draw_text(f"Funds: {format_money(self.manager.gold)}", font_title, GOLD_COLOR, screen, 50, 50)

        mouse_pos = pygame.mouse.get_pos()

        # Tabs
        for b in self.tab_buttons:
            b.base_color = (180, 120, 60) if b.text == self.active_tab else (50, 50, 60)
            b.check_hover(mouse_pos)
            b.draw(screen)

        # --- LEFT PANEL (RECIPES) ---
        self.draw_soft_panel(screen, self.left_rect)
        
        if self.active_tab == "MATERIALS":
            self._draw_materials(screen, mouse_pos)
        else:
            recipes = self.get_filtered_recipes()
            item_h = 70
            
            # Calculate max scroll
            total_h = len(recipes) * item_h
            view_h = self.left_rect.height - 40
            self.max_scroll = max(0, total_h - view_h)
            
            # Clip for scrolling
            prev_clip = screen.get_clip()
            clip_rect = self.left_rect.inflate(-20, -20)
            screen.set_clip(clip_rect)
            
            start_y = self.left_rect.top + 20 - self.scroll_y
            
            for i, name in enumerate(recipes):
                y = start_y + i * item_h
                
                # Optimization: Don't draw if out of view
                if y + item_h < self.left_rect.top or y > self.left_rect.bottom:
                    continue
                    
                rect = pygame.Rect(self.left_rect.left + 20, y, self.left_rect.width - 40, item_h - 10)
                
                is_selected = (name == self.selected_recipe)
                is_hover = rect.collidepoint(mouse_pos)
                
                col = (60, 50, 50)
                if is_selected: col = (120, 90, 50)
                elif is_hover: col = (80, 70, 70)
                
                pygame.draw.rect(screen, col, rect, border_radius=8)
                if is_selected:
                    pygame.draw.rect(screen, GOLD_COLOR, rect, 2, border_radius=8)
                
                # Text
                can_make = self.can_craft(name)
                txt_col = WHITE if can_make else (180, 100, 100)
                draw_text(name, font_main, txt_col, screen, rect.x + 20, rect.y + 18)
                
                # Cost hint
                cost = BLUEPRINTS[name]['cost']
                cost_col = GREEN if self.manager.gold >= cost else RED
                draw_text(format_money(cost), font_small, cost_col, screen, rect.right - 100, rect.y + 22)

            screen.set_clip(prev_clip)

        # --- RIGHT PANEL (DETAILS) ---
        self.draw_soft_panel(screen, self.right_rect)
        
        if self.active_tab == "MATERIALS":
            draw_text("MATERIAL STORAGE", font_title, GOLD_COLOR, screen, self.right_rect.centerx - 140, self.right_rect.top + 50)
            total_mats = sum([v for v in self.manager.inventory.values() if v > 0])
            draw_text(f"Total Items: {total_mats}", font_main, WHITE, screen, self.right_rect.centerx - 80, self.right_rect.top + 100)
            draw_text("Gather materials from missions and monster drops.", font_small, GRAY, screen, self.right_rect.centerx - 180, self.right_rect.top + 140)
            
        elif self.selected_recipe:
            data = BLUEPRINTS[self.selected_recipe]
            cx = self.right_rect.centerx
            top_y = self.right_rect.top + 50
            
            # Title
            draw_text(self.selected_recipe.upper(), font_title, ORANGE, screen, self.right_rect.left + 50, top_y)
            
            # Description
            draw_text(data['desc'], font_main, (200, 200, 200), screen, self.right_rect.left + 50, top_y + 60)
            
            # Cost
            cost_col = GREEN if self.manager.gold >= data['cost'] else RED
            draw_text(f"Cost: {format_money(data['cost'])}", font_main, cost_col, screen, self.right_rect.left + 50, top_y + 110)
            
            # Materials Header
            draw_text("REQUIRED MATERIALS:", font_main, GOLD_COLOR, screen, self.right_rect.left + 50, top_y + 180)
            
            # Materials List
            mat_y = top_y + 230
            for mat, req in data['mats'].items():
                owned = self.manager.inventory.get(mat, 0)
                col = GREEN if owned >= req else RED
                
                # Material bar background
                bar_rect = pygame.Rect(self.right_rect.left + 50, mat_y, self.right_rect.width - 100, 50)
                pygame.draw.rect(screen, (40, 35, 40), bar_rect, border_radius=8)
                pygame.draw.rect(screen, (60, 55, 60), bar_rect, 1, border_radius=8)
                
                draw_text(f"{mat}", font_main, WHITE, screen, bar_rect.x + 20, bar_rect.y + 12)
                draw_text(f"{owned} / {req}", font_main, col, screen, bar_rect.right - 100, bar_rect.y + 12)
                
                mat_y += 60
                
            # Craft Button
            self.btn_craft.base_color = GREEN if self.can_craft(self.selected_recipe) else GRAY
            self.btn_craft.check_hover(mouse_pos)
            self.btn_craft.draw(screen)
            
        else:
            draw_text("Select a blueprint to view details.", font_main, GRAY, screen, self.right_rect.centerx - 160, self.right_rect.centery)