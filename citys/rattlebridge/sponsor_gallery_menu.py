"""Sera Quench's Sponsor Gallery (Rattlebridge, Tier 1).

The player signs and drops Rattlebridge sponsor brands here. All logic lives in
``systems.sponsors``; this menu is only presentation + input. Stipends are paid
automatically after Tier 1 league matches (see game_manager.end_match).
"""
from __future__ import annotations

import pygame

from menus.base_menu import BaseMenu
from settings import SCREEN_HEIGHT, SCREEN_WIDTH, WHITE, GRAY, GREEN, RED, GOLD_COLOR
from sound_manager import sound_system
from ui_kit import UIButton, draw_text, draw_panel, font_title, font_main, font_small
from systems import sponsors


class SponsorGalleryMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.feedback = ""
        self.feedback_timer = 0
        self.selected_id = next(iter(sponsors.SPONSORS))
        self.list_rect = pygame.Rect(50, 150, 430, 620)
        self.details_rect = pygame.Rect(510, 150, SCREEN_WIDTH - 560, 620)
        self.list_buttons = []
        for i, sid in enumerate(sponsors.SPONSORS):
            btn = UIButton(self.list_rect.x + 15, self.list_rect.y + 20 + i * 74,
                           self.list_rect.w - 30, 62, sponsors.SPONSORS[sid]["name"],
                           None, (40, 40, 52))
            btn.data_id = sid
            self.list_buttons.append(btn)
        self.btn_action = UIButton(self.details_rect.centerx - 150,
                                   self.details_rect.bottom - 80, 300, 54,
                                   "SIGN", None, GREEN)
        self.btn_back = UIButton(SCREEN_WIDTH - 235, SCREEN_HEIGHT - 90,
                                 190, 55, "BACK", None, GRAY)

    def on_enter(self):
        self.manager.current_arena_location = "rattlebridge"
        sponsors.ensure_sponsor_state(self.manager)
        paid = sponsors.collect_due_stipends(self.manager)
        if paid.get("gold"):
            self.feedback = (f"Monthly stipends collected: +{paid['gold']}g "
                             f"({paid['months']} month(s)).")
            self.feedback_timer = 260

    # ------------------------------------------------------------------
    def _act(self):
        sid = self.selected_id
        if sponsors.is_signed(self.manager, sid):
            ok, msg = sponsors.drop_sponsor(self.manager, sid)
        else:
            ok, msg = sponsors.sign_sponsor(self.manager, sid)
        self.feedback = msg
        self.feedback_timer = 220
        sound_system.play_sound("coin" if ok else "error")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.next_state = "rattlebridge_scrapring"
            return
        if self.btn_back.is_clicked(event):
            self.next_state = "rattlebridge_scrapring"
            sound_system.play_sound("click")
            return
        for btn in self.list_buttons:
            if btn.is_clicked(event):
                self.selected_id = btn.data_id
                sound_system.play_sound("click")
                return
        if self.btn_action.is_clicked(event):
            self._act()

    def update(self):
        super().update()
        mouse = pygame.mouse.get_pos()
        for btn in self.list_buttons:
            btn.update_hover(mouse)
        self.btn_action.update_hover(mouse)
        self.btn_back.update_hover(mouse)
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    # ------------------------------------------------------------------
    def draw(self, screen):
        self.draw_themed_background(screen, mood="city")
        draw_text("SPONSOR GALLERY", font_title, GOLD_COLOR, screen, 50, 40)
        used = sponsors.slots_used(self.manager)
        draw_text(f"Sera Quench • Slots {used}/{sponsors.SPONSOR_SLOTS}  •  "
                  f"Gold {int(getattr(self.manager, 'gold', 0))}  •  "
                  f"Rep {sponsors._reputation(self.manager)}",
                  font_main, (200, 190, 175), screen, 52, 100)

        draw_panel(screen, self.list_rect.x, self.list_rect.y,
                   self.list_rect.w, self.list_rect.h, (28, 28, 38))
        for btn in self.list_buttons:
            sid = btn.data_id
            signed = sponsors.is_signed(self.manager, sid)
            if sid == self.selected_id:
                pygame.draw.rect(screen, GOLD_COLOR, btn.rect.inflate(6, 6), 2, border_radius=8)
            btn.base_color = (70, 70, 92) if sid == self.selected_id else (40, 40, 52)
            btn.draw(screen)
            tag = "SIGNED" if signed else ("OK" if sponsors.meets_requirements(self.manager, sid) else "LOCKED")
            col = GREEN if signed else (WHITE if tag == "OK" else (150, 90, 90))
            draw_text(tag, font_small, col, screen, btn.rect.right - 78, btn.rect.y + 8)

        self._draw_details(screen)
        self.btn_back.draw(screen)
        if self.feedback_timer > 0 and self.feedback:
            draw_text(self.feedback, font_small, GOLD_COLOR, screen, 52,
                      SCREEN_HEIGHT - 70)

    def _draw_details(self, screen):
        r = self.details_rect
        draw_panel(screen, r.x, r.y, r.w, r.h, (24, 24, 30))
        sid = self.selected_id
        s = sponsors.SPONSORS[sid]
        x, y = r.x + 30, r.y + 28
        draw_text(s["name"], font_title, s["banner"], screen, x, y)
        draw_text(f"Patron: {s['patron']}", font_main, (200, 200, 210), screen, x, y + 46)
        self._wrap(screen, s["flavor"], x, y + 86, font_small, WHITE, r.w - 60)

        y2 = y + 170
        demand_desc = {
            "win": "Win the match.",
            "clean": "Win with no fighter lost.",
            "dominant": "Win with most of the team standing.",
            "spectacle": "Win with a defeated opponent for the crowd.",
        }.get(s["demand"], s["demand"])
        align_desc = {
            "crown": "Crown Dominion interests",
            "kharak": "Horned Throne interests",
            "lupine": "Lupine Warden interests",
            "neutral": "Politically neutral",
            "underworld": "Underworld money",
        }.get(s.get("alignment", "neutral"), s.get("alignment", ""))
        rows = [
            (f"Signing bonus: {s['signing_bonus']}g", WHITE),
            (f"Monthly stipend: {s.get('monthly', 0)}g / 28 days", WHITE),
            (f"Win bonus: {s['stipend']}g  |  Rep/win: {s['rep_per_win']:+d}", WHITE),
            (f"Requires: Tier {s['required_tier']}, Rep {s['required_rep']}", (200, 200, 210)),
            (f"Demand each match: {demand_desc}", (230, 205, 150)),
            (f"Alignment: {align_desc}", (170, 180, 210)),
        ]
        if s.get("drop_rep_penalty"):
            rows.append((f"Dropping costs {s['drop_rep_penalty']} reputation.", (210, 150, 150)))
        if s.get("debt_per_payout"):
            debt = int(sponsors.ensure_sponsor_state(self.manager).get("ledger_debt", 0))
            rows.append((f"Every payout is recorded as debt (current: {debt}). "
                         "Debts are always called in.", (200, 130, 170)))
        for i, (line, col) in enumerate(rows):
            draw_text(line, font_small, col, screen, x, y2 + i * 26)

        signed = sponsors.is_signed(self.manager, sid)
        if signed:
            rec = sponsors.ensure_sponsor_state(self.manager)["signed"][sid]
            draw_text(f"Patience: {rec.get('patience', 0)}/{sponsors.MAX_PATIENCE}"
                      f"   Wins: {rec.get('wins', 0)}",
                      font_main, GREEN, screen, x, y2 + len(rows) * 26 + 14)
            self.btn_action.text = "DROP SPONSOR"
            self.btn_action.base_color = RED
            self.btn_action.set_enabled(True)
        else:
            ok, reason = sponsors.can_sign(self.manager, sid)
            self.btn_action.text = "SIGN" if ok else (reason[:28] or "LOCKED")
            self.btn_action.base_color = GREEN if ok else (90, 60, 60)
            self.btn_action.set_enabled(ok)
        self.btn_action.draw(screen)

    @staticmethod
    def _wrap(screen, text, x, y, font, color, max_width):
        words, line, lines = text.split(" "), [], []
        for w in words:
            if font.size(" ".join(line + [w]))[0] < max_width:
                line.append(w)
            else:
                lines.append(" ".join(line))
                line = [w]
        lines.append(" ".join(line))
        for i, ln in enumerate(lines):
            draw_text(ln, font, color, screen, x, y + i * 22)
