import pygame
from settings import *
from menus.base_menu import BaseMenu
from ui_kit import UIButton, draw_panel, draw_text, font_title, font_main, font_small, GOLD_COLOR, WHITE, GRAY, GREEN, RED
from sound_manager import sound_system

def _dt(screen, text, x, y, font, color):
    try: draw_text(text, font, color, screen, x, y)
    except Exception: draw_text(screen, text, x, y, font, color)

class LeagueMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)

        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)
        self.btn_hof = UIButton(SCREEN_WIDTH - 260, 30, 230, 50, "HALL OF FAME", None, (90, 70, 130))
        self.btn_fight = UIButton(SCREEN_WIDTH - 260, SCREEN_HEIGHT - 80, 230, 55, "FIGHT NEXT", None, GREEN)

        # Voitto / Rank Up -nappi
        self.btn_promote = UIButton(
            SCREEN_WIDTH - 260, SCREEN_HEIGHT - 160, 230, 60, "PLAY RANK UP!", "skull", (255, 215, 0)
        )
        
        # Häviö / Uusi kausi -nappi (PUNAINEN)
        self.btn_restart = UIButton(
            SCREEN_WIDTH - 260, SCREEN_HEIGHT - 160, 230, 60, "SEASON ENDED", None, RED
        )

        self.selected_mode = "TOTAL" 
        self.message = ""
        self._tab_rects = {}
        self._rebuild_layout()

    def _rebuild_layout(self):
        margin = 30
        header_h = 120
        tab_w, tab_h = 140, 46 # Slightly wider tabs for progress text
        tab_y, tab_x = margin + 60, margin

        self._tab_rects = {
            "TOTAL": pygame.Rect(tab_x + 0 * (tab_w + 10), tab_y, tab_w, tab_h),
            "1v1":   pygame.Rect(tab_x + 1 * (tab_w + 10), tab_y, tab_w, tab_h),
            "3v3":   pygame.Rect(tab_x + 2 * (tab_w + 10), tab_y, tab_w, tab_h),
            "5v5":   pygame.Rect(tab_x + 3 * (tab_w + 10), tab_y, tab_w, tab_h),
        }

        self._standings_rect = pygame.Rect(
            margin, header_h + margin, int(SCREEN_WIDTH * 0.48) - margin, SCREEN_HEIGHT - (header_h + margin * 2),
        )
        self._scout_rect = pygame.Rect(
            self._standings_rect.right + margin, self._standings_rect.y,
            SCREEN_WIDTH - (self._standings_rect.right + margin * 2), self._standings_rect.h,
        )

        self.btn_fight.rect.topleft = (SCREEN_WIDTH - 260, SCREEN_HEIGHT - 80)
        self.btn_hof.rect.topleft = (SCREEN_WIDTH - 260, 30)
        self.btn_promote.rect.topleft = (SCREEN_WIDTH - 260, SCREEN_HEIGHT - 160)
        self.btn_restart.rect.topleft = (SCREEN_WIDTH - 260, SCREEN_HEIGHT - 160)

    def _effective_enemy(self):
        if self.selected_mode == "TOTAL": return None
        return self.manager.league_engine.get_next_opponent(self.selected_mode)

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        le = self.manager.league_engine

        # --- Button Clicks ---
        if self.btn_back.is_clicked(event):
            sound_system.play_sound("click"); self.next_state = "hub"; return

        if self.btn_hof.is_clicked(event):
            sound_system.play_sound("click"); self.next_state = "hall_of_fame"; return

        # --- Tab Selection ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            for mode, r in self._tab_rects.items():
                if r.collidepoint(mouse_pos):
                    sound_system.play_sound("click")
                    self.selected_mode = mode
                    self.message = ""
                    break

        # --- Fight Logic ---
        if self.selected_mode != "TOTAL" and self.btn_fight.is_clicked(event):
            sound_system.play_sound("click")
            self._start_next_match()
            return

        # --- Season End Logic ---
        eligible, reason, opp_team = False, "", None
        try: eligible, reason, opp_team = le.check_promotion_eligibility()
        except Exception: pass
        
        season_complete = False
        try: season_complete = le.is_season_complete()
        except Exception: pass

        if eligible and opp_team:
            if self.btn_promote.is_clicked(event):
                sound_system.play_sound("click")
                self.manager.mode = "League"
                self.manager.match_mode = "PROMOTION"
                self.manager.current_enemy_team = opp_team
                self.manager.battle_size = 5
                self.next_state = "prepare"
                return

        elif season_complete and not eligible:
            # KAUSI OHI, EPÄONNISTUMINEN
            if self.btn_restart.is_clicked(event):
                sound_system.play_sound("click")
                msg = le.fail_season() # Nollaa kausi ja palauttaa voittajan nimen
                self.message = msg
                return

    def _start_next_match(self):
        # Estä jos moodi on valmis
        if self.manager.league_engine.is_mode_complete(self.selected_mode):
            self.message = "This league is already completed!"
            return

        mode = self.selected_mode
        enemy_team = self._effective_enemy()
        if not enemy_team:
            self.message = "No opponent scheduled. Check TOTAL tab."
            return

        self.manager.mode = "League"
        self.manager.match_mode = mode
        self.manager.current_enemy_team = enemy_team
        self.manager.battle_size = 1 if mode == "1v1" else (3 if mode == "3v3" else 5)
        self.next_state = "prepare"

    def update(self):
        try:
            if hasattr(self.manager, "league_engine") and self.manager.league_engine:
                self.manager.league_engine.tick_simulation(budget_ms=4.0, max_matches=1)
        except Exception: pass

    def _draw_tab(self, screen, mode: str, rect: pygame.Rect, hovered: bool):
        le = self.manager.league_engine
        
        # Data
        label = mode
        is_done = False
        
        if mode != "TOTAL":
            is_done = le.is_mode_complete(mode)
            # Hae progress: esim "1v1 1/2"
            grand_data = le.get_grand_score("PLAYER")
            played = grand_data["games"].get(mode, 0)
            
            # Kovakoodattu hätävara jos ei muuten saada tietoa (varmista että tämä vastaa engineä!)
            req = 2 
            
            label = f"{mode} {played}/{req}"
            if is_done: label += " (Done)"

        active = (mode == self.selected_mode)
        
        if mode == "TOTAL":
            base = (80, 70, 40); active_fill = (140, 120, 40); text_col = GOLD_COLOR
        else:
            if is_done: base = (40, 40, 45); active_fill = (60, 60, 65); text_col = (100, 100, 100)
            else: base = (60, 60, 70); active_fill = (40, 120, 90); text_col = WHITE

        fill = (90, 90, 110) if (hovered and not is_done) else base
        if active: fill = active_fill
            
        pygame.draw.rect(screen, fill, rect, border_radius=10)
        pygame.draw.rect(screen, (20, 20, 30), rect, 2, border_radius=10)
        _dt(screen, label, rect.x + 10, rect.y + 12, font_main, text_col)

    def draw(self, screen):
        screen.fill((14, 14, 18))
        mouse_pos = pygame.mouse.get_pos()
        le = self.manager.league_engine

        # --- HEADER (SEASON INFO) ---
        _dt(screen, "LEAGUE ARENA", 30, 20, font_title, WHITE)
        
        s_info = le.get_season_info()
        season_str = f"SEASON {s_info['number']}  |  {s_info['theme'].upper()}"
        tier_str = f"Division: {le.get_tier_name(self.selected_mode)}"
        
        _dt(screen, f"{season_str}   —   {tier_str}", 30, 70, font_main, (200, 200, 200))

        # Tabs
        for m, r in self._tab_rects.items():
            self._draw_tab(screen, m, r, r.collidepoint(mouse_pos))

        # Panels
        draw_panel(screen, self._standings_rect.x, self._standings_rect.y, self._standings_rect.w, self._standings_rect.h)
        draw_panel(screen, self._scout_rect.x, self._scout_rect.y, self._scout_rect.w, self._scout_rect.h)

        # --- Standings ---
        sx, sy = self._standings_rect.x + 18, self._standings_rect.y + 14
        title = "SEASON STANDINGS" if self.selected_mode != "TOTAL" else "GRAND SLAM STANDINGS (Total)"
        _dt(screen, title, sx, sy, font_main, GOLD_COLOR)

        headers = ["#", "Team", "W", "L", "PTS"]
        col_x = [sx, sx + 40, sx + int(self._standings_rect.w * 0.60), sx + int(self._standings_rect.w * 0.70), sx + int(self._standings_rect.w * 0.80)]
        for i, h in enumerate(headers): _dt(screen, h, col_x[i], sy + 35, font_small, (150, 150, 150))

        records = le.get_grand_slam_standings() if self.selected_mode == "TOTAL" else le.get_standings(self.selected_mode)
        row_y = sy + 65
        for idx, r in enumerate(records, start=1):
            if isinstance(r, dict):
                tid, tname = r.get('team_id'), r.get('team_name', 'Unknown')
                if tid == "PLAYER": tname = "My Guild"
                w, l, p = r.get('total_wins',0), r.get('total_losses',0), r.get('score',0)
            else:
                tid = getattr(r, "team_id", "")
                tname = "My Guild" if tid == "PLAYER" else (getattr(r.team, "name", tid) or tid)
                w, l, p = getattr(r, "wins", 0), getattr(r, "losses", 0), getattr(r, "points", 0)

            is_player = (tid == "PLAYER")
            if is_player:
                pygame.draw.rect(screen, (40, 50, 40), (self._standings_rect.x + 5, row_y - 2, self._standings_rect.w - 10, 24), border_radius=5)

            col = GOLD_COLOR if is_player else WHITE
            _dt(screen, str(idx), col_x[0], row_y, font_small, col)
            _dt(screen, str(tname)[:18], col_x[1], row_y, font_small, col)
            _dt(screen, str(w), col_x[2], row_y, font_small, col)
            _dt(screen, str(l), col_x[3], row_y, font_small, col)
            _dt(screen, str(p), col_x[4], row_y, font_small, GOLD_COLOR)
            row_y += 24
            if row_y > self._standings_rect.bottom - 20: break

        # --- Right Panel ---
        sx2, sy2 = self._scout_rect.x + 20, self._scout_rect.y + 20
        if self.selected_mode == "TOTAL":
            _dt(screen, "SEASON SUMMARY", sx2, sy2, font_main, GOLD_COLOR)
            
            # Lisää season info
            info = [
                "", f"Season {s_info['number']} ({s_info['theme']})",
                "Grand Slam combines points from all modes.",
                "--- RULES ---", "1. Finish all 1v1, 3v3, 5v5 matches.", "2. Top 2 qualify for Promotion Match.",
                "", f"Your Rank: #{le.get_player_rank()}"
            ]
            iy = sy2 + 30
            for line in info:
                _dt(screen, line, sx2, iy, font_small, WHITE)
                iy += 25
        else:
            _dt(screen, "NEXT OPPONENT", sx2, sy2, font_main, RED)
            
            # --- UUSI TARKISTUS: ONKO VALMIS? ---
            if le.is_mode_complete(self.selected_mode):
                _dt(screen, "Mode Complete! (2/2)", sx2, sy2 + 40, font_main, GREEN)
                _dt(screen, "Select another mode.", sx2, sy2 + 70, font_small, WHITE)
            else:
                enemy = self._effective_enemy()
                if enemy:
                    for i, line in enumerate(le.get_scout_report(enemy)):
                        _dt(screen, line, sx2, sy2 + 40 + i*22, font_small, (200, 200, 200))
                    
                    self.btn_fight.check_hover(mouse_pos)
                    self.btn_fight.draw(screen)
                else:
                    _dt(screen, "No opponent scheduled.", sx2, sy2 + 40, font_small, GRAY)
                    _dt(screen, "Check TOTAL tab for season status.", sx2, sy2 + 70, font_small, GRAY)
            
            # --- RECENT RESULTS (UUSI OSIO) ---
            res_y = sy2 + 250
            pygame.draw.line(screen, (60, 60, 70), (sx2, res_y - 10), (sx2 + 300, res_y - 10), 1)
            _dt(screen, "RECENT RESULTS", sx2, res_y, font_main, GOLD_COLOR)
            
            recent = le.get_recent_matches(self.selected_mode, 8)
            ry = res_y + 35
            if not recent:
                _dt(screen, "No matches recorded yet.", sx2, ry, font_small, GRAY)
            else:
                for m in recent:
                    w = m['winner']
                    l = m['loser']
                    col = (255, 255, 150) if "My Guild" in (w, l) else (180, 180, 180)
                    txt = f"Rd {m['round']}: {w} def. {l}"
                    _dt(screen, txt, sx2, ry, font_small, col)
                    ry += 22

        # --- Promotion / Season End Buttons ---
        eligible, reason, _ = False, "", None
        try: eligible, reason, _ = le.check_promotion_eligibility()
        except Exception: pass
        
        season_complete = False
        try: season_complete = le.is_season_complete()
        except Exception: pass

        if eligible:
            self.btn_promote.check_hover(mouse_pos)
            self.btn_promote.draw(screen)
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                pygame.draw.rect(screen, WHITE, self.btn_promote.rect, 3, border_radius=5)
        
        elif season_complete:
            # KAUSI OHI, mutta ei promotionia -> Restart
            self.btn_restart.check_hover(mouse_pos)
            self.btn_restart.draw(screen)
            _dt(screen, "You did not qualify. Season over.", self.btn_restart.rect.x, self.btn_restart.rect.y - 30, font_small, RED)

        self.btn_back.check_hover(mouse_pos); self.btn_back.draw(screen)
        self.btn_hof.check_hover(mouse_pos); self.btn_hof.draw(screen)
        if self.message: _dt(screen, self.message, 30, SCREEN_HEIGHT - 30, font_small, RED)