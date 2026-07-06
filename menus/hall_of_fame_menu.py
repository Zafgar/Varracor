import pygame
from menus.base_menu import BaseMenu
from settings import *
from ui_kit import UIButton, draw_text, font_title, font_main, font_small, draw_panel, GOLD_COLOR, WHITE, RED, GRAY

try:
    from sound_manager import sound_system
except Exception:
    sound_system = None

def _dt(surface, text, x, y, font, color):
    try: return draw_text(text, font, color, surface, x, y)
    except: return draw_text(surface, text, x, y, font, color)

class HallOfFameMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)

    def handle_event(self, event):
        if self.btn_back.is_clicked(event):
            if sound_system: sound_system.play_sound("click")
            self.next_state = "league"

    # --- LISÄTTY UPDATE-METODI ---
    def update(self):
        """Päivittää simulaatiota taustalla, jotta tilastot pysyvät ajan tasalla."""
        try:
            if hasattr(self.manager, "league_engine") and self.manager.league_engine:
                # Ajetaan simulaatiota pienellä budjetilla (esim. 4ms)
                self.manager.league_engine.tick_simulation(budget_ms=4.0, max_matches=5)
        except: pass
    # -----------------------------

    def draw(self, screen):
        screen.fill((10, 10, 15))
        self.btn_back.check_hover(pygame.mouse.get_pos())
        self.btn_back.draw(screen)

        # Header
        _dt(screen, "HALL OF FAME", SCREEN_WIDTH // 2 - 140, 30, font_title, GOLD_COLOR)
        _dt(screen, "Top 10 Legends of the Arena", SCREEN_WIDTH // 2 - 180, 80, font_main, (200, 200, 200))

        # Hae data
        top_list = []
        try:
            if hasattr(self.manager, "league_engine"):
                top_list = self.manager.league_engine.get_top_10_gladiators(player_roster=self.manager.my_team)
        except: pass

        # Piirrä lista
        start_y = 140
        row_h = 50
        
        # Headers
        col_rank = 100
        col_name = 200
        col_race = 500
        col_kills = 700
        
        headers_y = start_y - 30
        _dt(screen, "#", col_rank, headers_y, font_small, GRAY)
        _dt(screen, "Name", col_name, headers_y, font_small, GRAY)
        _dt(screen, "Team", col_race, headers_y, font_small, GRAY)
        _dt(screen, "Kills", col_kills, headers_y, font_small, GRAY)

        pygame.draw.line(screen, (50, 50, 60), (50, start_y - 10), (SCREEN_WIDTH - 50, start_y - 10), 2)

        if not top_list:
            _dt(screen, "No legends yet...", SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2, font_main, GRAY)
            return

        for i, unit in enumerate(top_list):
            y = start_y + i * row_h
            
            # Highlight top 3
            color = WHITE
            if i == 0: color = GOLD_COLOR
            elif i == 1: color = (192, 192, 192) # Silver
            elif i == 2: color = (205, 127, 50)  # Bronze

            # Rank
            _dt(screen, str(i + 1), col_rank, y, font_main, color)
            
            # Name
            name = getattr(unit, "name", "Unknown")
            _dt(screen, name, col_name, y, font_main, color)
            
            # Team Name
            team_name = "Unknown"
            if hasattr(unit, "hof_stats"):
                team_name = unit.hof_stats.get("team_name", "Unknown")
            elif hasattr(unit, "race_name"):
                team_name = unit.race_name
            _dt(screen, str(team_name), col_race, y, font_small, (200, 200, 200))
            
            # Kills
            kills = 0
            if hasattr(unit, "hof_stats"):
                kills = unit.hof_stats.get("kills", 0)
            _dt(screen, str(kills), col_kills, y, font_main, RED)
            
            # Pieni viiva väliin
            pygame.draw.line(screen, (30, 30, 40), (50, y + 35), (SCREEN_WIDTH - 50, y + 35), 1)