import pygame
from settings import *
from menus.base_menu import BaseMenu
from ui_kit import UIButton, draw_panel, draw_text, font_title, font_main, font_small, GOLD_COLOR, WHITE, GRAY, GREEN, RED
from sound_manager import sound_system

class CityStorageMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)
        
        # Layout
        self.panel_w = 1000
        self.panel_h = 700
        self.px = (SCREEN_WIDTH - self.panel_w) // 2
        self.py = (SCREEN_HEIGHT - self.panel_h) // 2
        
        self.deposit_buttons = []

    def update(self):
        pass

    def handle_event(self, event):
        if self.btn_back.is_clicked(event):
            self.next_state = "muckford_city"
            sound_system.play_sound('click')
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Tarkista talletusnapit (luodaan dynaamisesti draw-metodissa, mutta tarkistetaan tässä)
            # Yksinkertaistuksen vuoksi luodaan napit tässä uudestaan tarkistusta varten tai käytetään tallennettuja
            for btn in self.deposit_buttons:
                if btn.is_clicked(event):
                    self._deposit_item(btn.action_key)
                    sound_system.play_sound('click')
                    return

    def _deposit_item(self, name):
        if name in self.manager.inventory and self.manager.inventory[name] > 0:
            self.manager.inventory[name] -= 1
            self.manager.city_storage[name] = self.manager.city_storage.get(name, 0) + 1
            if self.manager.inventory[name] <= 0:
                del self.manager.inventory[name]

    def draw(self, screen):
        # Himmennetty tausta
        from ui_kit import get_fullscreen_overlay
        screen.blit(get_fullscreen_overlay((0, 0, 0, 150)), (0, 0))
        
        draw_panel(screen, self.px, self.py, self.panel_w, self.panel_h, title="VILLAGE STORAGE")
        self.btn_back.check_hover(pygame.mouse.get_pos())
        self.btn_back.draw(screen)
        
        # --- LEFT: PLAYER INVENTORY ---
        draw_text("YOUR BAG", font_title, WHITE, screen, self.px + 50, self.py + 60)
        
        y = self.py + 120
        self.deposit_buttons = []
        
        if not self.manager.inventory:
            draw_text("Empty.", font_small, GRAY, screen, self.px + 50, y)
        
        for name, count in self.manager.inventory.items():
            if count > 0:
                # Item row
                draw_text(f"{name}: {count}", font_main, WHITE, screen, self.px + 50, y + 10)
                
                # Deposit Button
                btn = UIButton(self.px + 300, y, 100, 40, "STORE >", None, (60, 60, 80))
                btn.action_key = name
                btn.check_hover(pygame.mouse.get_pos())
                btn.draw(screen)
                self.deposit_buttons.append(btn)
                
                y += 50
                if y > self.py + self.panel_h - 50: break

        # --- RIGHT: CITY STORAGE ---
        mid_x = self.px + self.panel_w // 2
        pygame.draw.line(screen, (60, 60, 70), (mid_x, self.py + 60), (mid_x, self.py + self.panel_h - 40), 2)
        
        draw_text("CITY STOCKPILE", font_title, GOLD_COLOR, screen, mid_x + 50, self.py + 60)
        
        y = self.py + 120
        if not self.manager.city_storage:
            draw_text("Storage is empty.", font_small, GRAY, screen, mid_x + 50, y)
            
        for name, count in self.manager.city_storage.items():
            if count > 0:
                draw_text(f"{name}", font_main, (200, 200, 200), screen, mid_x + 50, y)
                draw_text(f"x{count}", font_title, GOLD_COLOR, screen, mid_x + 350, y - 5)
                y += 50
