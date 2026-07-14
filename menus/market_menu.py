# menus/market_menu.py
"""
Muckfordin markkinakoju: pelaaja myy keräämiään resursseja ja ostaa
perustavaroita. Hinnat: lore/world_data.py -> MARKET_PRICES.

Pelitesti 14: klikkaus ei enää myy/osta heti - rivi VALITAAN, määrä
säädetään [-]/[+]-napeilla (SHIFT = 10 kerrallaan, MAX-nappi) ja
kauppa vahvistetaan CONFIRM-napilla. Estää vahinkomyynnit.
"""
import pygame
from menus.base_menu import BaseMenu
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRAY, GOLD_COLOR, GREEN
from ui_kit import draw_text, font_main, font_title, font_small, UIButton, format_money
from sound_manager import sound_system
from lore.world_data import MARKET_PRICES


class MarketMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        cx = SCREEN_WIDTH // 2
        self.btn_back = UIButton(cx - 100, SCREEN_HEIGHT - 90, 200, 55, "BACK", None, GRAY)
        self.sell_rects = []  # (rect, material_name)
        self.buy_rects = []   # (rect, shop_key)
        self.feedback = ""
        self.feedback_timer = 0
        # Vahvistuspaneeli: {"side": "sell"/"buy", "key": nimi, "qty": n}
        self.pending = None
        self._confirm_rects = {}  # nappi -> rect (piirto täyttää)

    # =========================================================
    # KAUPPALOGIIKKA
    # =========================================================
    def _sellable_items(self):
        """Pelaajan inventaarion materiaalit joilla on markkinahinta."""
        prices = MARKET_PRICES["sell"]
        out = []
        for name, count in sorted(self.manager.inventory.items()):
            if count > 0 and name in prices:
                out.append((name, count, prices[name]))
        return out

    def _sell(self, name, amount=1):
        prices = MARKET_PRICES["sell"]
        have = self.manager.inventory.get(name, 0)
        amount = min(amount, have)
        if amount <= 0:
            return
        total = prices[name] * amount
        self.manager.inventory[name] = have - amount
        if self.manager.inventory[name] <= 0:
            del self.manager.inventory[name]
        self.manager.gold += total
        sound_system.play_sound("coin")
        self._flash(f"Sold {amount}x {name} for {format_money(total)}")

    def _buy(self, key, amount=1):
        entry = MARKET_PRICES["buy"][key]
        amount = max(1, int(amount))
        total = entry["price"] * amount
        if self.manager.gold < total:
            sound_system.play_sound("error")
            self._flash("Not enough coin!")
            return
        bought = 0
        for _ in range(amount):
            if entry["kind"] == "material":
                self.manager.add_material(key, 1)
                bought += 1
            else:
                # Varusteet luodaan luokan nimellä
                item = None
                if entry.get("class") == "BucketEmpty":
                    from items.tools.bucket import BucketEmpty
                    item = BucketEmpty()
                else:
                    from items.item_registry import create_item
                    item = create_item(entry.get("class", key))
                if item:
                    self.manager.equipment_bag.append(item)
                    bought += 1
                else:
                    break
        if bought == 0:
            self._flash("Out of stock!")
            return
        self.manager.gold -= entry["price"] * bought
        sound_system.play_sound("coin")
        self._flash(f"Bought {bought}x {key} for "
                    f"{format_money(entry['price'] * bought)}")

    def _flash(self, text):
        self.feedback = text
        self.feedback_timer = 120

    # =========================================================
    # VAHVISTUSPANEELI
    # =========================================================
    def _pending_limits(self):
        """(yksikköhinta, maksimimäärä) valitulle riville."""
        p = self.pending
        if not p:
            return 0, 0
        if p["side"] == "sell":
            unit = MARKET_PRICES["sell"].get(p["key"], 0)
            max_q = int(self.manager.inventory.get(p["key"], 0))
        else:
            unit = MARKET_PRICES["buy"][p["key"]]["price"]
            max_q = self.manager.gold // unit if unit > 0 else 0
        return unit, max(0, max_q)

    def _adjust_qty(self, delta):
        _unit, max_q = self._pending_limits()
        self.pending["qty"] = max(1, min(max_q or 1,
                                         self.pending["qty"] + delta))

    def _confirm_pending(self):
        p = self.pending
        self.pending = None
        if not p:
            return
        if p["side"] == "sell":
            self._sell(p["key"], p["qty"])
        else:
            self._buy(p["key"], p["qty"])

    # =========================================================
    # INPUT
    # =========================================================
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.pending:
                self.pending = None
                return
            self.next_state = "muckford_city"
            return
        if self.pending and event.type == pygame.KEYDOWN and \
                event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._confirm_pending()
            return
        if self.btn_back.is_clicked(event):
            self.next_state = "muckford_city"
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Vahvistuspaneelin napit ensin
            if self.pending:
                step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1
                r = self._confirm_rects
                if r.get("minus") and r["minus"].collidepoint(event.pos):
                    self._adjust_qty(-step)
                    return
                if r.get("plus") and r["plus"].collidepoint(event.pos):
                    self._adjust_qty(step)
                    return
                if r.get("max") and r["max"].collidepoint(event.pos):
                    _u, max_q = self._pending_limits()
                    self.pending["qty"] = max(1, max_q)
                    return
                if r.get("confirm") and r["confirm"].collidepoint(event.pos):
                    self._confirm_pending()
                    return
                if r.get("cancel") and r["cancel"].collidepoint(event.pos):
                    self.pending = None
                    sound_system.play_sound("click")
                    return

            mods = pygame.key.get_mods()
            for rect, name in self.sell_rects:
                if rect.collidepoint(event.pos):
                    have = int(self.manager.inventory.get(name, 0))
                    qty = have if (mods & pygame.KMOD_SHIFT) else 1
                    self.pending = {"side": "sell", "key": name,
                                    "qty": max(1, qty)}
                    sound_system.play_sound("click")
                    return
            for rect, key in self.buy_rects:
                if rect.collidepoint(event.pos):
                    self.pending = {"side": "buy", "key": key, "qty": 1}
                    sound_system.play_sound("click")
                    return

    def update(self):
        super().update()
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    # =========================================================
    # DRAW
    # =========================================================
    def draw(self, screen):
        self.draw_themed_background(screen, "city")
        title = font_title.render("MUCKFORD MARKET", True, GOLD_COLOR)
        self.draw_header_bar(screen, title)

        # Kulta
        draw_text(f"Funds: {format_money(self.manager.gold)}", font_main,
                  GOLD_COLOR, screen, SCREEN_WIDTH - 320, 130)

        mouse = pygame.mouse.get_pos()
        panel_w = 560
        row_h = 44

        # --- VASEN: MYY ---
        left = pygame.Rect(SCREEN_WIDTH // 2 - panel_w - 40, 170, panel_w, 640)
        self.draw_soft_panel(screen, left)
        draw_text("YOUR GOODS (click = choose amount)", font_main, WHITE,
                  screen, left.x + 20, left.y + 15)

        self.sell_rects = []
        items = self._sellable_items()
        if not items:
            draw_text("Nothing to sell. The village pays for milk,", font_small,
                      GRAY, screen, left.x + 20, left.y + 70)
            draw_text("eggs, wood, scrap, manure...", font_small,
                      GRAY, screen, left.x + 20, left.y + 92)
        y = left.y + 60
        for name, count, price in items:
            row = pygame.Rect(left.x + 12, y, panel_w - 24, row_h - 4)
            hover = row.collidepoint(mouse)
            selected = (self.pending and self.pending["side"] == "sell"
                        and self.pending["key"] == name)
            bg = (66, 62, 44) if selected else \
                ((50, 50, 62) if hover else (32, 32, 42))
            pygame.draw.rect(screen, bg, row, border_radius=6)
            if selected:
                pygame.draw.rect(screen, GOLD_COLOR, row, 2, border_radius=6)
            draw_text(f"{name}  x{count}", font_main, WHITE, screen,
                      row.x + 12, row.y + 8)
            draw_text(format_money(price), font_main, GOLD_COLOR, screen,
                      row.right - 110, row.y + 8)
            self.sell_rects.append((row, name))
            y += row_h
            if y > left.bottom - row_h:
                break

        # --- OIKEA: OSTA ---
        right = pygame.Rect(SCREEN_WIDTH // 2 + 40, 170, panel_w, 640)
        self.draw_soft_panel(screen, right)
        draw_text("FOR SALE (click = choose amount)", font_main, WHITE,
                  screen, right.x + 20, right.y + 15)

        self.buy_rects = []
        y = right.y + 60
        for key, entry in MARKET_PRICES["buy"].items():
            row = pygame.Rect(right.x + 12, y, panel_w - 24, row_h - 4)
            hover = row.collidepoint(mouse)
            afford = self.manager.gold >= entry["price"]
            selected = (self.pending and self.pending["side"] == "buy"
                        and self.pending["key"] == key)
            bg = (50, 62, 50) if (hover and afford) else (32, 42, 32)
            if not afford:
                bg = (42, 32, 32)
            if selected:
                bg = (66, 62, 44)
            pygame.draw.rect(screen, bg, row, border_radius=6)
            if selected:
                pygame.draw.rect(screen, GOLD_COLOR, row, 2, border_radius=6)
            draw_text(key, font_main, WHITE if afford else GRAY, screen,
                      row.x + 12, row.y + 8)
            draw_text(format_money(entry['price']), font_main,
                      GOLD_COLOR if afford else GRAY, screen,
                      row.right - 80, row.y + 8)
            self.buy_rects.append((row, key))
            y += row_h

        # --- VAHVISTUSPANEELI ---
        if self.pending:
            self._draw_confirm_bar(screen)

        # Palaute
        if self.feedback_timer > 0:
            draw_text(self.feedback, font_main, GREEN, screen,
                      SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 150)

        self.btn_back.draw(screen)

    def _draw_confirm_bar(self, screen):
        p = self.pending
        unit, max_q = self._pending_limits()
        p["qty"] = max(1, min(p["qty"], max_q or 1))
        total = unit * p["qty"]
        verb = "SELL" if p["side"] == "sell" else "BUY"
        bar = pygame.Rect(SCREEN_WIDTH // 2 - 430, SCREEN_HEIGHT - 260,
                          860, 96)
        pygame.draw.rect(screen, (24, 24, 32), bar, border_radius=12)
        pygame.draw.rect(screen, GOLD_COLOR, bar, 2, border_radius=12)
        draw_text(f"{verb} {p['key']}", font_main, WHITE, screen,
                  bar.x + 24, bar.y + 12)
        draw_text(f"{format_money(unit)} each   (max {max_q})", font_small,
                  GRAY, screen, bar.x + 24, bar.y + 52)

        r = {}
        r["minus"] = pygame.Rect(bar.x + 330, bar.y + 24, 48, 48)
        qty_rect = pygame.Rect(bar.x + 386, bar.y + 24, 90, 48)
        r["plus"] = pygame.Rect(bar.x + 484, bar.y + 24, 48, 48)
        r["max"] = pygame.Rect(bar.x + 540, bar.y + 24, 64, 48)
        r["confirm"] = pygame.Rect(bar.right - 236, bar.y + 24, 130, 48)
        r["cancel"] = pygame.Rect(bar.right - 96, bar.y + 24, 72, 48)
        for key_, label, col in (("minus", "-", (70, 70, 84)),
                                 ("plus", "+", (70, 70, 84)),
                                 ("max", "MAX", (70, 70, 84)),
                                 ("confirm", verb, (65, 135, 80)),
                                 ("cancel", "X", (120, 60, 60))):
            rect = r[key_]
            pygame.draw.rect(screen, col, rect, border_radius=8)
            surf = font_main.render(label, True, WHITE)
            screen.blit(surf, surf.get_rect(center=rect.center))
        pygame.draw.rect(screen, (16, 16, 22), qty_rect, border_radius=8)
        qsurf = font_main.render(str(p["qty"]), True, GOLD_COLOR)
        screen.blit(qsurf, qsurf.get_rect(center=qty_rect.center))
        draw_text(f"Total {format_money(total)}", font_main, GOLD_COLOR,
                  screen, bar.x + 640, bar.y - 34)
        draw_text("SHIFT = +/-10, ENTER = confirm", font_small, GRAY,
                  screen, bar.x + 24, bar.bottom + 8)
        self._confirm_rects = r
