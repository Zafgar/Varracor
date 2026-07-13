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
    except Exception: return draw_text(surface, text, x, y, font, color)

class HallOfFameMenu(BaseMenu):
    TABS = ("LEGENDS", "CHRONICLE", "TEAMS")

    def __init__(self, manager):
        super().__init__(manager)
        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)
        self.tab = "LEGENDS"
        self.tab_buttons = {}
        for i, tab in enumerate(self.TABS):
            self.tab_buttons[tab] = UIButton(
                180 + i * 200, 30, 180, 50, tab, None, (60, 55, 90))

    def handle_event(self, event):
        if self.btn_back.is_clicked(event):
            if sound_system: sound_system.play_sound("click")
            self.next_state = "league"
            return
        for tab, btn in self.tab_buttons.items():
            if btn.is_clicked(event):
                self.tab = tab
                if sound_system: sound_system.play_sound("click")
                return

    # --- LISÄTTY UPDATE-METODI ---
    def update(self):
        """Päivittää simulaatiota taustalla, jotta tilastot pysyvät ajan tasalla."""
        try:
            if hasattr(self.manager, "league_engine") and self.manager.league_engine:
                # Ajetaan simulaatiota pienellä budjetilla (esim. 4ms)
                self.manager.league_engine.tick_simulation(budget_ms=4.0, max_matches=5)
        except Exception: pass
    # -----------------------------

    def draw(self, screen):
        screen.fill((10, 10, 15))
        mouse = pygame.mouse.get_pos()
        self.btn_back.check_hover(mouse)
        self.btn_back.draw(screen)
        for tab, btn in self.tab_buttons.items():
            btn.base_color = (95, 80, 140) if tab == self.tab else (60, 55, 90)
            btn.check_hover(mouse)
            btn.draw(screen)

        _dt(screen, "HALL OF FAME", SCREEN_WIDTH // 2 - 140, 30, font_title, GOLD_COLOR)
        if self.tab == "CHRONICLE":
            self._draw_chronicle(screen)
            return
        if self.tab == "TEAMS":
            self._draw_teams(screen)
            return
        _dt(screen, "Top 10 Legends of the Arena", SCREEN_WIDTH // 2 - 180, 80, font_main, (200, 200, 200))

        # Hae data
        top_list = []
        try:
            if hasattr(self.manager, "league_engine"):
                top_list = self.manager.league_engine.get_top_10_gladiators(player_roster=self.manager.my_team)
        except Exception: pass

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

    # ------------------------------------------------------------------
    # ALL-TIME KRONIKKA: miten Hall of Fame on kehittynyt koko pelin ajan
    # ------------------------------------------------------------------
    def _draw_chronicle(self, screen):
        _dt(screen, "How the arena remembers every season", SCREEN_WIDTH // 2 - 230, 80,
            font_main, (200, 200, 200))
        entries = []
        try:
            entries = self.manager.league_engine.get_chronicle(14)
        except Exception:
            pass
        if not entries:
            _dt(screen, "No recorded seasons yet. Finish a season to begin the chronicle.",
                SCREEN_WIDTH // 2 - 330, SCREEN_HEIGHT // 2, font_main, GRAY)
            return
        y = 140
        for e in entries:
            kind = e.get("type", "season")
            color = GOLD_COLOR if kind == "promotion" else (
                (225, 120, 105) if kind == "relegation" else WHITE)
            head = (f"Tier {max(0, e.get('tier', 1) - 1)}  •  Season {e.get('season', '?')}"
                    f"  •  {kind.upper()}")
            _dt(screen, head, 110, y, font_main, color)
            line = f"Champion: {e.get('champion', '?')}   |   Your rank: #{e.get('player_rank', '?')}"
            if e.get("top_killer"):
                line += f"   |   Top killer: {e['top_killer']} ({e.get('top_kills', 0)})"
            _dt(screen, line, 130, y + 32, font_small, (200, 200, 205))
            if e.get("note"):
                _dt(screen, e["note"], 130, y + 56, font_small, (150, 150, 160))
            pygame.draw.line(screen, (40, 40, 52), (100, y + 82),
                             (SCREEN_WIDTH - 100, y + 82), 1)
            y += 96
            if y > SCREEN_HEIGHT - 90:
                break

    # ------------------------------------------------------------------
    # TIIMIT PER TIER: koko jarjestelman joukkueet + nykyisen tierin tilanne
    # ------------------------------------------------------------------
    def _draw_teams(self, screen):
        _dt(screen, "Every circuit, every team", SCREEN_WIDTH // 2 - 160, 80,
            font_main, (200, 200, 200))
        current_tier = 0
        live_names = []
        try:
            engine = self.manager.league_engine
            current_tier = max(0, int(engine.tier) - 1)
            live_names = [row["team_name"]
                          for row in engine.get_grand_slam_standings()]
        except Exception:
            pass
        try:
            from lore.world_data import get_tier_teams
        except Exception:
            get_tier_teams = lambda t: []
        col_w = SCREEN_WIDTH // 3 - 40
        for tier in range(6):
            col = tier % 3
            row = tier // 3
            x = 70 + col * (col_w + 40)
            y = 130 + row * 420
            header = f"TIER {tier}"
            color = GOLD_COLOR if tier == current_tier else (170, 170, 185)
            _dt(screen, header, x, y, font_main, color)
            if tier == current_tier:
                _dt(screen, "(current - live standings)", x + 120, y + 6,
                    font_small, GOLD_COLOR)
            names = []
            if tier == current_tier and live_names:
                names = live_names[:8]
            else:
                try:
                    names = [t.get("name", "?") for t in get_tier_teams(tier)][:8]
                except Exception:
                    names = []
            ty = y + 40
            if not names:
                _dt(screen, "- rumors only -", x + 14, ty, font_small, GRAY)
            for i, name in enumerate(names):
                marker = f"{i + 1}." if tier == current_tier else "•"
                _dt(screen, f"{marker} {name}", x + 14, ty, font_small,
                    WHITE if tier == current_tier else (185, 185, 195))
                ty += 30
