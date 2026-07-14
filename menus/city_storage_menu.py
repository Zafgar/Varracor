import pygame
from settings import *
from menus.base_menu import BaseMenu
from ui_kit import (UIButton, draw_panel, draw_text, font_title, font_main,
                    font_small, GOLD_COLOR, WHITE, GRAY, GREEN, RED)
from sound_manager import sound_system

# Pelitesti 18: varastointi PALKITSEE - kyläläiset kokkaavat ja nikkaroivat
# varastosta, joten lahjoitukset kasvattavat mainetta
DONATIONS_PER_REP = 10


class CityStorageMenu(BaseMenu):
    """Kylän varasto (pelitesti 18): rullattavat listat, järkevät fontit
    ja syy tallettaa - joka 10. lahjoitettu tavara antaa +1 mainetta."""

    def __init__(self, manager):
        super().__init__(manager)
        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)

        # Layout
        self.panel_w = 1240
        self.panel_h = 780
        self.px = (SCREEN_WIDTH - self.panel_w) // 2
        self.py = (SCREEN_HEIGHT - self.panel_h) // 2

        self.deposit_buttons = []
        self.bag_scroll = 0
        self.city_scroll = 0
        self.feedback = ""
        self.feedback_timer = 0

    def update(self):
        super().update()
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.next_state = "muckford_city"
            return
        if self.btn_back.is_clicked(event):
            self.next_state = "muckford_city"
            sound_system.play_sound('click')
            return

        # Rullaus: hiiren puoli ratkaisee kumpaa listaa vieritetään
        if event.type == pygame.MOUSEWHEEL:
            mx, _my = pygame.mouse.get_pos()
            mid_x = self.px + self.panel_w // 2
            if mx < mid_x:
                self.bag_scroll = max(0, self.bag_scroll - event.y)
            else:
                self.city_scroll = max(0, self.city_scroll - event.y)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mods = pygame.key.get_mods()
            for btn in self.deposit_buttons:
                if btn.is_clicked(event):
                    self._deposit_item(btn.action_key,
                                       all_of=bool(mods & pygame.KMOD_SHIFT))
                    sound_system.play_sound('click')
                    return

    def _deposit_item(self, name, all_of=False):
        inv = self.manager.inventory
        have = int(inv.get(name, 0))
        if have <= 0:
            return
        amount = have if all_of else 1
        inv[name] = have - amount
        if inv[name] <= 0:
            del inv[name]
        store = self.manager.city_storage
        store[name] = store.get(name, 0) + amount

        # Lahjoitukset kerryttävät mainetta (syy tallettaa!)
        donated = int(getattr(self.manager, "storage_donations", 0)) + amount
        rep_gain = donated // DONATIONS_PER_REP
        self.manager.storage_donations = donated % DONATIONS_PER_REP
        if rep_gain > 0:
            try:
                from quest_system import quest_manager
                if quest_manager:
                    quest_manager.add_reputation(rep_gain)
                self.manager.reputation = getattr(
                    self.manager, "reputation", 0) + rep_gain
            except Exception:
                pass
            self.feedback = (f"The village thanks you! "
                             f"+{rep_gain} reputation")
            self.feedback_timer = 200
            sound_system.play_sound('win')
        else:
            left = DONATIONS_PER_REP - self.manager.storage_donations
            self.feedback = (f"Stored {amount}x {name}. "
                             f"{self.manager.storage_donations}/"
                             f"{DONATIONS_PER_REP} toward +1 rep")
            self.feedback_timer = 160

    # ------------------------------------------------------------------
    def draw(self, screen):
        # Himmennetty tausta
        from ui_kit import get_fullscreen_overlay
        screen.blit(get_fullscreen_overlay((0, 0, 0, 150)), (0, 0))

        draw_panel(screen, self.px, self.py, self.panel_w, self.panel_h,
                   title="VILLAGE STORAGE")
        self.btn_back.check_hover(pygame.mouse.get_pos())
        self.btn_back.draw(screen)

        draw_text("Villagers cook, craft and build from the stockpile - "
                  f"every {DONATIONS_PER_REP} goods donated earn +1 "
                  "reputation.", font_small, (185, 200, 185), screen,
                  self.px + 40, self.py + 46)

        row_h = 34
        list_top = self.py + 120
        list_bottom = self.py + self.panel_h - 60
        max_rows = (list_bottom - list_top) // row_h
        mid_x = self.px + self.panel_w // 2

        # --- VASEN: YOUR BAG ---
        draw_text("YOUR BAG", font_main, WHITE, screen,
                  self.px + 40, self.py + 82)
        draw_text("(STORE = 1, SHIFT = all, wheel scrolls)", font_small,
                  GRAY, screen, self.px + 180, self.py + 88)

        self.deposit_buttons = []
        bag_items = [(n, c) for n, c in sorted(self.manager.inventory.items())
                     if c > 0]
        if not bag_items:
            draw_text("Empty.", font_small, GRAY, screen,
                      self.px + 40, list_top)
        max_scroll = max(0, len(bag_items) - max_rows)
        self.bag_scroll = min(self.bag_scroll, max_scroll)
        y = list_top
        for name, count in bag_items[self.bag_scroll:
                                     self.bag_scroll + max_rows]:
            draw_text(f"{name}", font_small, WHITE, screen,
                      self.px + 40, y + 7)
            draw_text(f"x{count}", font_small, GOLD_COLOR, screen,
                      self.px + 330, y + 7)
            btn = UIButton(self.px + 420, y, 110, row_h - 6, "STORE >",
                           None, (60, 60, 80))
            btn.action_key = name
            btn.check_hover(pygame.mouse.get_pos())
            btn.draw(screen)
            self.deposit_buttons.append(btn)
            y += row_h
        if max_scroll > 0:
            draw_text(f"{self.bag_scroll + 1}-"
                      f"{min(len(bag_items), self.bag_scroll + max_rows)}"
                      f" / {len(bag_items)}", font_small, GRAY, screen,
                      self.px + 40, list_bottom + 8)

        # --- OIKEA: CITY STOCKPILE (kaksi saraketta, rullattava) ---
        pygame.draw.line(screen, (60, 60, 70), (mid_x, self.py + 76),
                         (mid_x, self.py + self.panel_h - 40), 2)
        draw_text("CITY STOCKPILE", font_main, GOLD_COLOR, screen,
                  mid_x + 40, self.py + 82)

        city_items = [(n, c) for n, c
                      in sorted(self.manager.city_storage.items())
                      if c > 0 and n != "Unknown"]
        if not city_items:
            draw_text("Storage is empty.", font_small, GRAY, screen,
                      mid_x + 40, list_top)
        col_w = (self.panel_w // 2 - 80) // 2
        rows_per_col = max_rows
        per_page = rows_per_col * 2
        max_scroll_c = max(0, (len(city_items) - per_page + rows_per_col)
                           // rows_per_col)
        self.city_scroll = min(self.city_scroll, max_scroll_c)
        start = self.city_scroll * rows_per_col
        visible = city_items[start:start + per_page]
        for i, (name, count) in enumerate(visible):
            col = i // rows_per_col
            row = i % rows_per_col
            cx = mid_x + 40 + col * col_w
            cy = list_top + row * row_h
            draw_text(name[:20], font_small, (200, 200, 200), screen,
                      cx, cy + 7)
            surf = font_small.render(f"x{count}", True, GOLD_COLOR)
            screen.blit(surf, (cx + col_w - surf.get_width() - 16, cy + 7))
        if len(city_items) > per_page or self.city_scroll > 0:
            draw_text(f"{start + 1}-{min(len(city_items), start + per_page)}"
                      f" / {len(city_items)}  (wheel scrolls)", font_small,
                      GRAY, screen, mid_x + 40, list_bottom + 8)

        if self.feedback_timer > 0:
            draw_text(self.feedback, font_small, GREEN, screen,
                      self.px + 40, self.py + self.panel_h - 34)
