# menus/market_menu.py
"""
Muckfordin markkinakoju: pelaaja myy keräämiään resursseja ja ostaa
perustavaroita. Hinnat: lore/world_data.py -> MARKET_PRICES.

- Klikkaa omaa tavaraa      -> myy 1 kpl (SHIFT = myy kaikki)
- Klikkaa kaupan tavaraa    -> osta 1 kpl
- ESC / BACK                -> takaisin kaupunkiin
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
        self._flash(f"Sold {amount}x {name} for {total}g")

    def _buy(self, key):
        entry = MARKET_PRICES["buy"][key]
        price = entry["price"]
        if self.manager.gold < price:
            sound_system.play_sound("error")
            self._flash("Not enough gold!")
            return
        self.manager.gold -= price

        if entry["kind"] == "material":
            self.manager.add_material(key, 1)
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
            else:
                # Ei saatu luotua -> palauta rahat
                self.manager.gold += price
                self._flash("Out of stock!")
                return
        sound_system.play_sound("coin")
        self._flash(f"Bought {key} for {price}g")

    def _flash(self, text):
        self.feedback = text
        self.feedback_timer = 120

    # =========================================================
    # INPUT
    # =========================================================
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.next_state = "muckford_city"
            return
        if self.btn_back.is_clicked(event):
            self.next_state = "muckford_city"
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mods = pygame.key.get_mods()
            sell_all = bool(mods & pygame.KMOD_SHIFT)
            for rect, name in self.sell_rects:
                if rect.collidepoint(event.pos):
                    self._sell(name, 9999 if sell_all else 1)
                    return
            for rect, key in self.buy_rects:
                if rect.collidepoint(event.pos):
                    self._buy(key)
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
        draw_text(f"Gold: {format_money(self.manager.gold)}", font_main,
                  GOLD_COLOR, screen, SCREEN_WIDTH - 320, 130)

        mouse = pygame.mouse.get_pos()
        panel_w = 560
        row_h = 44

        # --- VASEN: MYY ---
        left = pygame.Rect(SCREEN_WIDTH // 2 - panel_w - 40, 170, panel_w, 640)
        self.draw_soft_panel(screen, left)
        draw_text("YOUR GOODS (click = sell 1, SHIFT = all)", font_main, WHITE,
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
            pygame.draw.rect(screen, (50, 50, 62) if hover else (32, 32, 42),
                             row, border_radius=6)
            draw_text(f"{name}  x{count}", font_main, WHITE, screen,
                      row.x + 12, row.y + 8)
            draw_text(f"{price}g / kpl", font_main, GOLD_COLOR, screen,
                      row.right - 110, row.y + 8)
            self.sell_rects.append((row, name))
            y += row_h
            if y > left.bottom - row_h:
                break

        # --- OIKEA: OSTA ---
        right = pygame.Rect(SCREEN_WIDTH // 2 + 40, 170, panel_w, 640)
        self.draw_soft_panel(screen, right)
        draw_text("FOR SALE (click = buy 1)", font_main, WHITE,
                  screen, right.x + 20, right.y + 15)

        self.buy_rects = []
        y = right.y + 60
        for key, entry in MARKET_PRICES["buy"].items():
            row = pygame.Rect(right.x + 12, y, panel_w - 24, row_h - 4)
            hover = row.collidepoint(mouse)
            afford = self.manager.gold >= entry["price"]
            bg = (50, 62, 50) if (hover and afford) else (32, 42, 32)
            if not afford:
                bg = (42, 32, 32)
            pygame.draw.rect(screen, bg, row, border_radius=6)
            draw_text(key, font_main, WHITE if afford else GRAY, screen,
                      row.x + 12, row.y + 8)
            draw_text(f"{entry['price']}g", font_main,
                      GOLD_COLOR if afford else GRAY, screen,
                      row.right - 80, row.y + 8)
            self.buy_rects.append((row, key))
            y += row_h

        # Palaute
        if self.feedback_timer > 0:
            draw_text(self.feedback, font_main, GREEN, screen,
                      SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 150)

        self.btn_back.draw(screen)
