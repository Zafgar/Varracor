# menus/district_shop_menu.py
"""Market-alueen liikkeen kauppasivu.

Avautuu kaupungin kojusta (manager.pending_shop_id). Sivu mukautuu liikkeen
tuotteisiin (vihannes/ase/panssari/juoma/sekatavara) ja näyttää hinnat
PAIKALLISELLA maineella korjattuna: kanta-asiakkuus tässä liikkeessä laskee
tämän liikkeen hintoja. Jokainen ostos kasvattaa liikkeen faktion mainetta.
"""

from __future__ import annotations

import pygame

from citys.mucford.market_data import MARKET_SHOPS
from items.item_registry import create_item
from lore.world_data import MARKET_PRICES
from menus.base_menu import BaseMenu
from settings import GOLD_COLOR, GRAY, GREEN, RED, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from systems.faction_reputation import (
    discount_percent, get_faction_rep, on_purchase, shop_price,
)
from ui_kit import (
    UIButton, draw_item_tooltip, draw_text, font_main, font_small, font_title,
    format_money,
)


class DistrictShopMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        shop_id = getattr(manager, "pending_shop_id", None)
        if shop_id not in MARKET_SHOPS:
            shop_id = next(iter(MARKET_SHOPS))
        self.shop_id = shop_id
        self.shop = MARKET_SHOPS[shop_id]
        self.feedback = ""
        self.feedback_timer = 0
        self.row_rects = []
        self.sell_rects = []   # (rect, materiaalinimi)
        # Esikatselukappaleet hover-infokorttia varten (luodaan kerran)
        self._previews = {}
        for entry in self.shop["goods"]:
            if entry["kind"] == "item":
                try:
                    self._previews[entry["name"]] = create_item(
                        entry.get("class", entry["name"]))
                except Exception:
                    self._previews[entry["name"]] = None
        self.btn_leave = UIButton(SCREEN_WIDTH - 260, SCREEN_HEIGHT - 96,
                                  210, 58, "LEAVE", None, GRAY)
        # Ostovahvistus: klikkaus VALITSEE rivin, BUY-nappi ostaa.
        # Estää vahinko-ostot pelkällä klikillä.
        self.selected_entry = None
        self.btn_buy = UIButton(SCREEN_WIDTH - 490, SCREEN_HEIGHT - 96,
                                210, 58, "BUY", None, (65, 135, 80))

    # ------------------------------------------------------------------
    def _rep(self) -> int:
        return get_faction_rep(self.manager, self.shop["faction"])

    def _haggler_bonus(self) -> int:
        """Commander-puun Haggler: hinnat kuin maine olisi +10/taso."""
        hero = getattr(self.manager, "player_character", None)
        return 10 * int(getattr(hero, "haggler", 0))

    def _effective_rep(self) -> int:
        return self._rep() + self._haggler_bonus()

    def _final_price(self, entry) -> int:
        return shop_price(entry["price"], self._effective_rep())

    def _sell_price(self, name) -> int:
        """Liikkeen maksama hinta: markkinoiden perushinta korjattuna
        maineella (hyvä maine -> maksavat enemmän, huono -> vähemmän).
        EI KOSKAAN yli 60 % liikkeen omasta myyntihinnasta - muuten
        osta-halvalla-myy-takaisin -rahasilmukka olisi mahdollinen."""
        base = int(MARKET_PRICES.get("sell", {}).get(name, 1))
        pct = discount_percent(self._effective_rep())
        price = max(1, round(base * (1.0 - pct / 100.0)))
        for entry in self.shop["goods"]:
            if entry["name"] == name:
                price = min(price, max(1, int(entry["price"] * 0.6)))
                break
        return price

    def _sellable_goods(self):
        """(nimi, määrä, yksikköhinta) pelaajan repusta joita liike ostaa."""
        inv = getattr(self.manager, "inventory", {})
        out = []
        for name in self.shop.get("buys", ()):
            count = int(inv.get(name, 0))
            if count > 0:
                out.append((name, count, self._sell_price(name)))
        return out

    def _sell(self, name, sell_all=False):
        inv = self.manager.inventory
        count = int(inv.get(name, 0))
        if count <= 0:
            return
        amount = count if sell_all else 1
        unit_price = self._sell_price(name)
        total = unit_price * amount
        inv[name] = count - amount
        if inv[name] <= 0:
            del inv[name]
        self.manager.gold += total
        on_purchase(self.manager, self.shop["faction"])
        self.feedback = (f"Sold {amount}x {name} for {format_money(total)}.")
        self.feedback_timer = 200
        sound_system.play_sound("coin")

    def _buy(self, entry):
        price = self._final_price(entry)
        if int(getattr(self.manager, "gold", 0)) < price:
            self.feedback = f"{self.shop['keeper']}: Come back with coin."
            self.feedback_timer = 200
            sound_system.play_sound("error")
            return False
        if entry["kind"] == "material":
            try:
                self.manager.add_material(entry["name"], 1)
            except Exception:
                inv = self.manager.inventory
                inv[entry["name"]] = int(inv.get(entry["name"], 0)) + 1
        else:
            item = create_item(entry.get("class", entry["name"]))
            if item is None:
                self.feedback = "Out of stock (unknown ware)."
                self.feedback_timer = 200
                sound_system.play_sound("error")
                return False
            self.manager.equipment_bag.append(item)
        self.manager.gold -= price
        on_purchase(self.manager, self.shop["faction"])
        self.feedback = f"Bought {entry['name']} for {format_money(price)}."
        self.feedback_timer = 200
        sound_system.play_sound("coin")
        return True

    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.next_state = "muckford_city"
            return
        if self.btn_leave.is_clicked(event):
            self.next_state = "muckford_city"
            sound_system.play_sound("click")
            return
        if self.selected_entry is not None and self.btn_buy.is_clicked(event):
            self._buy(self.selected_entry)
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Myyntirivit: klikkaus myy 1, SHIFT+klikkaus myy kaikki
            for rect, name in self.sell_rects:
                if rect.collidepoint(event.pos):
                    mods = pygame.key.get_mods()
                    self._sell(name, sell_all=bool(mods & pygame.KMOD_SHIFT))
                    return
            for rect, entry in self.row_rects:
                if rect.collidepoint(event.pos):
                    if self.selected_entry is entry:
                        # Toinen klikkaus samaan riviin = osta
                        self._buy(entry)
                    else:
                        self.selected_entry = entry
                        sound_system.play_sound("hover")
                    return
            # Klikkaus muualle poistaa valinnan
            self.selected_entry = None

    def update(self):
        super().update()
        self.btn_leave.update_hover(pygame.mouse.get_pos())
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    # ------------------------------------------------------------------
    def draw(self, screen):
        self.draw_themed_background(screen, mood="city")
        awning = self.shop.get("awning", (110, 90, 60))

        title = font_title.render(self.shop["name"].upper(), True, GOLD_COLOR)
        self.draw_header_bar(screen, title, y=24)

        # Katosraita otsikon alle liikkeen värillä
        stripe = pygame.Rect(0, 96, SCREEN_WIDTH, 20)
        pygame.draw.rect(screen, awning, stripe)
        for x in range(0, SCREEN_WIDTH, 52):
            pygame.draw.rect(screen, tuple(max(0, c - 34) for c in awning),
                             (x, 96, 24, 20))

        # Yläpalkki: pitäjä, maine ja varat
        head = pygame.Rect(160, 150, SCREEN_WIDTH - 320, 104)
        self.draw_soft_panel(screen, head, alpha=205, border_alpha=180, radius=12)
        draw_text(f"{self.shop['keeper']} ({self.shop['keeper_race']})",
                  font_main, WHITE, screen, head.x + 30, head.y + 14)
        draw_text(self.shop["flavor"], font_small, (195, 190, 178),
                  screen, head.x + 30, head.y + 46)
        rep = self._rep()
        pct = discount_percent(self._effective_rep())
        rep_color = GREEN if pct < 0 else ((225, 165, 95) if pct > 0 else WHITE)
        sign = "+" if pct > 0 else ""
        haggler = self._haggler_bonus()
        haggler_note = f"  [Haggler +{haggler}]" if haggler else ""
        draw_text(f"Your standing with {self.shop['faction_label']}: {rep}"
                  f"{haggler_note}  ({sign}{pct}% prices)", font_small, rep_color,
                  screen, head.x + 30, head.y + 74)
        draw_text(f"Funds: {format_money(getattr(self.manager, 'gold', 0))}",
                  font_main, GOLD_COLOR, screen, head.right - 280, head.y + 14)

        mouse_pos = pygame.mouse.get_pos()

        # --- VASEN: YOUR GOODS (myynti, kuten Muckford Marketissa) ---
        left = pygame.Rect(160, 274, 620, 560)
        self.draw_soft_panel(screen, left, alpha=205, border_alpha=180, radius=12)
        draw_text("YOUR GOODS (click = sell 1, SHIFT = all)", font_main,
                  (150, 200, 165), screen, left.x + 26, left.y + 18)
        self.sell_rects = []
        sy = left.y + 62
        goods = self._sellable_goods()
        if not goods:
            draw_text(f"{self.shop['keeper']} buys: " +
                      ", ".join(self.shop.get("buys", ())[:5]) + "...",
                      font_small, (150, 150, 160), screen,
                      left.x + 26, sy + 6)
        for name, count, unit_price in goods[:8]:
            row = pygame.Rect(left.x + 22, sy, left.w - 44, 48)
            hover = row.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (44, 44, 52) if hover else (32, 33, 39),
                             row, border_radius=8)
            pygame.draw.rect(screen, awning, row, 1, border_radius=8)
            draw_text(f"{name}  x{count}", font_main, WHITE, screen,
                      row.x + 16, row.y + 12)
            price_surf = font_main.render(format_money(unit_price), True,
                                          GOLD_COLOR)
            screen.blit(price_surf, (row.right - price_surf.get_width() - 16,
                                     row.y + 12))
            self.sell_rects.append((row, name))
            sy += 58

        # --- OIKEA: FOR SALE ---
        panel = pygame.Rect(820, 274, SCREEN_WIDTH - 980, 560)
        self.draw_soft_panel(screen, panel, alpha=205, border_alpha=180, radius=12)

        # Tuoterivit
        self.row_rects = []
        y = panel.y + 62
        draw_text("FOR SALE (click to select, then BUY)",
                  font_main, (150, 200, 165), screen, panel.x + 26, panel.y + 18)
        hovered_entry = None
        for entry in self.shop["goods"]:
            row = pygame.Rect(panel.x + 22, y, panel.w - 44, 56)
            hover = row.collidepoint(mouse_pos)
            if hover:
                hovered_entry = entry
            selected = self.selected_entry is entry
            if selected:
                pygame.draw.rect(screen, (58, 54, 38), row, border_radius=9)
                pygame.draw.rect(screen, GOLD_COLOR, row, 2, border_radius=9)
            else:
                pygame.draw.rect(screen, (44, 44, 52) if hover else (32, 33, 39),
                                 row, border_radius=9)
                pygame.draw.rect(screen, awning, row, 2, border_radius=9)
            draw_text(entry["name"], font_main, WHITE, screen,
                      row.x + 20, row.y + 14)
            kind_label = "material" if entry["kind"] == "material" else "equipment"
            draw_text(kind_label, font_small, (150, 150, 160), screen,
                      row.x + 360, row.y + 18)
            base = entry["price"]
            final = self._final_price(entry)
            price_color = GREEN if final < base else (RED if final > base else GOLD_COLOR)
            if final != base:
                # Perushinta yliviivattuna (sisäinen yksikkö on SP)
                draw_text(format_money(base), font_small, (130, 130, 140),
                          screen, row.right - 260, row.y + 18)
                pygame.draw.line(screen, (130, 130, 140),
                                 (row.right - 264, row.y + 27),
                                 (row.right - 200, row.y + 27), 2)
            draw_text(format_money(final), font_main, price_color, screen,
                      row.right - 160, row.y + 14)
            self.row_rects.append((row, entry))
            y += 66

        if self.feedback_timer > 0 and self.feedback:
            box = pygame.Rect(panel.x + 26, panel.bottom - 70, panel.w - 52, 48)
            pygame.draw.rect(screen, (22, 22, 26), box, border_radius=8)
            pygame.draw.rect(screen, (180, 145, 85), box, 2, border_radius=8)
            draw_text(self.feedback, font_main, WHITE, screen,
                      box.x + 18, box.y + 12)

        if self.selected_entry is not None:
            self.btn_buy.text = (
                f"BUY  {format_money(self._final_price(self.selected_entry))}")
            self.btn_buy.draw(screen)
        self.btn_leave.draw(screen)

        # Hover-infokortti PÄÄLLIMMÄISENÄ: varusteista täysi item-kortti
        # (statsit, level req), materiaaleista lyhyt kuvaus
        if hovered_entry is not None:
            mx, my = mouse_pos
            tx = min(mx + 24, SCREEN_WIDTH - 340)
            if hovered_entry["kind"] == "item":
                preview = self._previews.get(hovered_entry["name"])
                if preview is not None:
                    draw_item_tooltip(screen, preview, tx, my + 16,
                                      player_unit=self.manager.player_character)
            else:
                tip = pygame.Rect(tx, my + 16, 300, 54)
                pygame.draw.rect(screen, (25, 25, 30), tip, border_radius=8)
                pygame.draw.rect(screen, (120, 120, 135), tip, 2, border_radius=8)
                draw_text(hovered_entry["name"], font_small, WHITE, screen,
                          tip.x + 12, tip.y + 8)
                draw_text("Material - stored in your inventory.", font_small,
                          (160, 160, 170), screen, tip.x + 12, tip.y + 28)
