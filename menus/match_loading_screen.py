import pygame
from settings import *
from menus.base_menu import BaseMenu
from ui_kit import draw_text, font_title, font_main, GOLD_COLOR, WHITE

class MatchLoadingScreen(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.timer = 0
        self.loading_text = "Traveling to location..."
        self.match_data = None # (units, limit)

    def set_match_data(self, units, limit):
        self.match_data = (units, limit)
        self.timer = 0
        self.loading_text = "Traveling to location..."

    def update(self):
        self.timer += 1
        
        # Odotetaan hetki (n. 0.5s), jotta ruutu ehtii piirtyä
        if self.timer == 10:
            self.loading_text = "Generating Terrain..."
            
        elif self.timer == 20:
            # Käynnistetään matsi
            if self.match_data:
                units, limit = self.match_data
                self.manager.start_match(units, limit)
                self.next_state = "battle"
            else:
                # Fallback jos data puuttuu
                self.next_state = "hub"

    def draw(self, screen):
        screen.fill((15, 12, 18))
        
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        
        draw_text("LOADING", font_title, GOLD_COLOR, screen, cx - 80, cy - 60)
        draw_text(self.loading_text, font_main, (150, 150, 150), screen, cx - 100, cy + 10)
        
        # Pieni pyörivä indikaattori tai palkki
        bar_w = 300
        pygame.draw.rect(screen, (40, 40, 50), (cx - bar_w//2, cy + 50, bar_w, 4))
        
        # Fake progress
        prog = min(1.0, self.timer / 20.0)
        pygame.draw.rect(screen, (100, 200, 100), (cx - bar_w//2, cy + 50, int(bar_w * prog), 4))
