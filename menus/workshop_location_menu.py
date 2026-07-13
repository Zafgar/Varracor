import pygame
from settings import *
from ui_kit import UIButton, draw_text, font_title, font_main, font_small, GOLD_COLOR, WHITE, GRAY
from menus.base_menu import BaseMenu
from sound_manager import sound_system

class WorkshopLocationMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)
        
        # Määritellään sijainnit
        self.locations = [
            {
                "name": "The Shanty Consortium",
                "region": "Muckford (The Sundered Heartlands)",
                "desc": "A cheap logistical hub near the Abyssal Vortex where newcomers flock.",
                "state": "workshop", # Tämä avaa nykyisen WorkshopMenun
                "unlocked": True
            },
            # Esimerkki tulevasta paikasta
            {
                "name": "Ironhold Forge",
                "region": "High Mountains",
                "desc": "Legendary dwarven smithy known for heavy plate armor.",
                "state": None,
                "unlocked": False
            }
        ]
        
        self.location_buttons = []
        self._init_buttons()

    def _init_buttons(self):
        start_y = 150
        for i, loc in enumerate(self.locations):
            # Luodaan iso painikealue kullekin sijainnille
            btn = UIButton(SCREEN_WIDTH // 2 - 350, start_y + i * 140, 700, 120, "", None, (40, 40, 50))
            btn.data = loc
            self.location_buttons.append(btn)

    def handle_event(self, event):
        if self.btn_back.is_clicked(event):
            self.next_state = "hub"
            sound_system.play_sound('click')
            return

        for btn in self.location_buttons:
            if btn.is_clicked(event):
                loc = btn.data
                if loc["unlocked"] and loc["state"]:
                    self.next_state = loc["state"]
                    sound_system.play_sound('click')
                else:
                    sound_system.play_sound('error')
                return

    def draw(self, screen):
        self.draw_themed_background(screen, mood="forge")
        
        self.btn_back.check_hover(pygame.mouse.get_pos())
        self.btn_back.draw(screen)
        
        _t = font_title.render("SELECT WORKSHOP LOCATION", True, GOLD_COLOR)
        self.draw_header_bar(screen, _t, y=10)
        
        mouse_pos = pygame.mouse.get_pos()
        
        for btn in self.location_buttons:
            loc = btn.data
            rect = btn.rect
            is_hover = rect.collidepoint(mouse_pos)
            
            # Taustaväri
            bg_col = (50, 50, 60) if is_hover else (30, 30, 40)
            if not loc["unlocked"]: bg_col = (20, 20, 25)
            
            border_col = GOLD_COLOR if is_hover and loc["unlocked"] else (60, 60, 70)
            
            pygame.draw.rect(screen, bg_col, rect, border_radius=10)
            pygame.draw.rect(screen, border_col, rect, 2, border_radius=10)
            
            # Tekstit
            title_col = WHITE if loc["unlocked"] else GRAY
            draw_text(loc["name"], font_main, title_col, screen, rect.x + 20, rect.y + 15)
            
            region_col = (200, 200, 100) if loc["unlocked"] else (100, 100, 80)
            draw_text(loc["region"], font_small, region_col, screen, rect.x + 20, rect.y + 45)
            
            desc_col = (180, 180, 180) if loc["unlocked"] else (80, 80, 80)
            draw_text(loc["desc"], font_small, desc_col, screen, rect.x + 20, rect.y + 75)
            
            # Tila-indikaattori
            if not loc["unlocked"]:
                draw_text("LOCKED", font_main, (150, 50, 50), screen, rect.right - 120, rect.centery - 10)
            elif is_hover:
                draw_text("ENTER >", font_main, GOLD_COLOR, screen, rect.right - 120, rect.centery - 10)
