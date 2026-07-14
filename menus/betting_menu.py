# menus/betting_menu.py
"""Vintin vedonlyöntitoimisto - Arena Hallin kojulta (E).

Iso valikko jossa vedonlyönti on oikea rahantekoväline:
- Välilehdet 1v1 / 3v3 / 5v5
- Kierroksen KAIKKI ottelut: molempien tiimien saldot (W-L), ELO ja
  kertoimet; klikkaa tiimiä -> kuponki
- Panoksen säätö [-]/[+]/MAX (SHIFT = 10), pöytäraja tierin mukaan
- Useita avoimia kuponkeja (MY TICKETS -paneeli), ratkeavat kun
  kierros pelataan; tulokset myös viimeisimpien matsien syötteessä
"""
import pygame

from menus.base_menu import BaseMenu
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRAY, GOLD_COLOR
from sound_manager import sound_system
from systems import betting
from ui_kit import draw_text, font_main, font_small, font_title, format_money

GREEN_OK = (110, 200, 130)
RED_BAD = (220, 110, 100)


class BettingOfficeMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.mode = "1v1"
        self.selected = None          # (mode, team_id, opp_id)
        self.stake = 10
        self.feedback = ""
        self.feedback_col = WHITE
        self.tab_rects = {}
        self.team_rects = []          # (rect, team_id, opp_id)
        self.btn_rects = {}
        # Ratkenneet kupongit heti sisään astuttaessa
        msgs = betting.check_open_bets(manager)
        if msgs:
            self.feedback = "  |  ".join(msgs[:2])
            self.feedback_col = GOLD_COLOR

    # ------------------------------------------------------------------
    def _season(self):
        eng = self.manager.league_engine
        eng._ensure_initialized()
        return eng.seasons.get(self.mode)

    def consumes_escape(self):
        return True

    def _leave(self):
        self.next_state = getattr(self.manager, "betting_return_state",
                                  "arena_hall") or "arena_hall"

    def _flash(self, text, ok=True):
        self.feedback = text
        self.feedback_col = GREEN_OK if ok else RED_BAD

    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._leave()
            sound_system.play_sound("click")
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        pos = event.pos
        for mode, rect in self.tab_rects.items():
            if rect.collidepoint(pos):
                self.mode = mode
                self.selected = None
                sound_system.play_sound("click")
                return
        for rect, team_id, opp_id in self.team_rects:
            if rect.collidepoint(pos):
                self.selected = (self.mode, team_id, opp_id)
                limit = betting.table_limit(self.manager)
                self.stake = min(max(10, self.stake), limit)
                sound_system.play_sound("hover")
                return
        step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1
        r = self.btn_rects
        limit = betting.table_limit(self.manager)
        if r.get("minus") and r["minus"].collidepoint(pos):
            self.stake = max(1, self.stake - step)
            return
        if r.get("plus") and r["plus"].collidepoint(pos):
            self.stake = min(limit, self.stake + step)
            return
        if r.get("max") and r["max"].collidepoint(pos):
            self.stake = min(limit, max(1, int(self.manager.gold)))
            return
        if r.get("place") and r["place"].collidepoint(pos) and self.selected:
            mode, team_id, _opp = self.selected
            ok, msg = betting.place_bet(self.manager, mode, team_id,
                                        self.stake)
            self._flash(msg, ok)
            sound_system.play_sound("coin" if ok else "error")
            if ok:
                self.selected = None
            return
        if r.get("leave") and r["leave"].collidepoint(pos):
            self._leave()
            sound_system.play_sound("click")

    # ------------------------------------------------------------------
    def draw(self, screen):
        self.draw_themed_background(screen, mood="city")
        title = font_title.render("VINT'S BETTING OFFICE", True, GOLD_COLOR)
        self.draw_header_bar(screen, title)
        m = self.manager
        limit = betting.table_limit(m)
        draw_text(f"Funds: {format_money(m.gold)}", font_main, GOLD_COLOR,
                  screen, SCREEN_WIDTH - 340, 118)
        draw_text(f"Table limit: {format_money(limit)} per ticket",
                  font_small, GRAY, screen, SCREEN_WIDTH - 340, 152)

        # --- Välilehdet ---
        self.tab_rects = {}
        tx = 70
        for mode in betting.MODES:
            rect = pygame.Rect(tx, 120, 130, 46)
            active = (mode == self.mode)
            pygame.draw.rect(screen, (58, 52, 40) if active else (30, 30, 38),
                             rect, border_radius=9)
            pygame.draw.rect(screen, GOLD_COLOR if active else (90, 90, 100),
                             rect, 2, border_radius=9)
            surf = font_main.render(mode, True,
                                    GOLD_COLOR if active else WHITE)
            screen.blit(surf, surf.get_rect(center=rect.center))
            self.tab_rects[mode] = rect
            tx += 144

        season = self._season()
        if season is None:
            draw_text("No league running.", font_main, GRAY, screen, 80, 220)
            return

        # --- Kierroksen ottelut ---
        left = pygame.Rect(60, 190, 1150, 620)
        self.draw_soft_panel(screen, left)
        draw_text(f"ROUND {season.current_round + 1} FIXTURES - "
                  f"click a team to back them", font_main, WHITE, screen,
                  left.x + 24, left.y + 14)
        self.team_rects = []
        y = left.y + 62
        for a_id, b_id in betting.fixtures(season):
            self._draw_fixture_row(screen, season, a_id, b_id,
                                   left.x + 20, y, left.w - 40)
            y += 92
            if y > left.bottom - 90:
                break

        # Viimeisimmät tulokset
        draw_text("LATEST RESULTS", font_small, GOLD_COLOR, screen,
                  left.x + 24, y + 6)
        ry = y + 30
        for res in season.get_recent_matches(4):
            line = (f"R{res.get('round', '?')}: {res.get('winner', '?')} "
                    f"beat {res.get('loser', '?')}")
            draw_text(line[:88], font_small, (180, 180, 190), screen,
                      left.x + 24, ry)
            ry += 24
            if ry > left.bottom - 20:
                break

        # --- Oikea puoli: kuponki + avoimet vedot ---
        right = pygame.Rect(1240, 190, 620, 620)
        self.draw_soft_panel(screen, right)
        self._draw_bet_slip(screen, season, right)
        self._draw_open_tickets(screen, right)

        # Palaute + LEAVE
        if self.feedback:
            draw_text(self.feedback[:110], font_small, self.feedback_col,
                      screen, 70, SCREEN_HEIGHT - 190)
        leave = pygame.Rect(SCREEN_WIDTH - 300, SCREEN_HEIGHT - 120, 220, 56)
        pygame.draw.rect(screen, (90, 60, 60), leave, border_radius=10)
        surf = font_main.render("LEAVE [ESC]", True, WHITE)
        screen.blit(surf, surf.get_rect(center=leave.center))
        self.btn_rects["leave"] = leave

    # ------------------------------------------------------------------
    def _draw_fixture_row(self, screen, season, a_id, b_id, x, y, w):
        row = pygame.Rect(x, y, w, 84)
        pygame.draw.rect(screen, (26, 27, 33), row, border_radius=10)
        pygame.draw.rect(screen, (70, 66, 56), row, 1, border_radius=10)
        cell_w = (w - 110) // 2
        for side, (tid, oid) in enumerate(((a_id, b_id), (b_id, a_id))):
            cx = x + 8 if side == 0 else x + w - cell_w - 8
            cell = pygame.Rect(cx, y + 8, cell_w, 68)
            rec = season.records.get(tid)
            selected = (self.selected and self.selected[1] == tid
                        and self.selected[0] == self.mode)
            hovering = cell.collidepoint(pygame.mouse.get_pos())
            bg = (66, 60, 42) if selected else \
                ((44, 44, 54) if hovering else (33, 34, 41))
            pygame.draw.rect(screen, bg, cell, border_radius=8)
            if selected:
                pygame.draw.rect(screen, GOLD_COLOR, cell, 2,
                                 border_radius=8)
            name = season._team_name(tid)
            is_player = (rec is not None and rec.team is None)
            draw_text(name[:26], font_main,
                      (150, 220, 160) if is_player else WHITE,
                      screen, cell.x + 12, cell.y + 6)
            if rec:
                mult = betting.odds_multiplier(season, tid, oid)
                draw_text(f"{rec.wins}W-{rec.losses}L   ELO {int(rec.elo)}",
                          font_small, (170, 170, 180), screen,
                          cell.x + 12, cell.y + 38)
                odds_surf = font_main.render(f"x{mult:.2f}", True,
                                             GOLD_COLOR)
                screen.blit(odds_surf, (cell.right - 90, cell.y + 20))
            self.team_rects.append((cell, tid, oid))
        vs = font_main.render("VS", True, (200, 120, 90))
        screen.blit(vs, vs.get_rect(center=(x + w // 2, y + 42)))

    def _draw_bet_slip(self, screen, season, panel):
        draw_text("BET SLIP", font_main, GOLD_COLOR, screen,
                  panel.x + 24, panel.y + 14)
        y = panel.y + 54
        if not self.selected or self.selected[0] != self.mode:
            draw_text("Pick a team from the fixtures.", font_small, GRAY,
                      screen, panel.x + 24, y)
            self.btn_rects.pop("place", None)
            return
        _mode, tid, oid = self.selected
        mult = betting.odds_multiplier(season, tid, oid)
        draw_text(f"{season._team_name(tid)}", font_main, WHITE, screen,
                  panel.x + 24, y)
        draw_text(f"to beat {season._team_name(oid)}   pays x{mult:.2f}",
                  font_small, (180, 180, 190), screen, panel.x + 24, y + 30)
        # Panossäätö
        r = self.btn_rects
        r["minus"] = pygame.Rect(panel.x + 24, y + 66, 48, 44)
        stake_rect = pygame.Rect(panel.x + 80, y + 66, 110, 44)
        r["plus"] = pygame.Rect(panel.x + 198, y + 66, 48, 44)
        r["max"] = pygame.Rect(panel.x + 254, y + 66, 70, 44)
        r["place"] = pygame.Rect(panel.x + 350, y + 66, 200, 44)
        for key, label, col in (("minus", "-", (70, 70, 84)),
                                ("plus", "+", (70, 70, 84)),
                                ("max", "MAX", (70, 70, 84)),
                                ("place", "PLACE BET", (65, 135, 80))):
            rect = r[key]
            pygame.draw.rect(screen, col, rect, border_radius=8)
            surf = font_main.render(label, True, WHITE)
            screen.blit(surf, surf.get_rect(center=rect.center))
        pygame.draw.rect(screen, (16, 16, 22), stake_rect, border_radius=8)
        s = font_main.render(str(self.stake), True, GOLD_COLOR)
        screen.blit(s, s.get_rect(center=stake_rect.center))
        payout = int(self.stake * mult)
        draw_text(f"Stake {format_money(self.stake)}  ->  returns "
                  f"{format_money(payout)}", font_small, GOLD_COLOR,
                  screen, panel.x + 24, y + 122)
        draw_text("SHIFT = +/-10", font_small, GRAY, screen,
                  panel.x + 24, y + 146)

    def _draw_open_tickets(self, screen, panel):
        y = panel.y + 250
        bets = betting.open_bets(self.manager)
        draw_text(f"MY TICKETS ({len(bets)}/{betting.MAX_OPEN_BETS})",
                  font_main, GOLD_COLOR, screen, panel.x + 24, y)
        y += 38
        if not bets:
            draw_text("No open tickets. Fortune favors the bold.",
                      font_small, GRAY, screen, panel.x + 24, y)
            return
        for b in bets[:6]:
            pot = int(b["amount"] * b["mult"])
            draw_text(f"{b['mode']}  {b['team_name'][:20]} vs "
                      f"{b['opp_name'][:18]}", font_small, WHITE, screen,
                      panel.x + 24, y)
            draw_text(f"   {format_money(b['amount'])} @ x{b['mult']:.2f}"
                      f"  ->  {format_money(pot)}", font_small,
                      (200, 180, 120), screen, panel.x + 24, y + 20)
            y += 50
