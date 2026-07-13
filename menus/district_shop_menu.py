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
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, entry in self.row_rects:
                if rect.collidepoint(event.pos):
                    self._buy(entry)
                    return

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

        panel = pygame.Rect(240, 150, SCREEN_WIDTH - 480, 640)
        self.draw_soft_panel(screen, panel, alpha=205, border_alpha=180, radius=12)

        draw_text(f"{self.shop['keeper']} ({self.shop['keeper_race']})",
                  font_main, WHITE, screen, panel.x + 30, panel.y + 20)
        draw_text(self.shop["flavor"], font_small, (195, 190, 178),
                  screen, panel.x + 30, panel.y + 54)

        rep = self._rep()
        pct = discount_percent(self._effective_rep())
        rep_color = GREEN if pct < 0 else ((225, 165, 95) if pct > 0 else WHITE)
        sign = "+" if pct > 0 else ""
        haggler = self._haggler_bonus()
        haggler_note = f"  [Haggler +{haggler}]" if haggler else ""
        draw_text(f"Your standing with {self.shop['faction_label']}: {rep}"
                  f"{haggler_note}  ({sign}{pct}% prices)", font_small, rep_color,
                  screen, panel.x + 30, panel.y + 88)
        draw_text(f"Funds: {format_money(getattr(self.manager, 'gold', 0))}",
                  font_main, GOLD_COLOR, screen, panel.right - 280, panel.y + 20)

        # Tuoterivit
        self.row_rects = []
        y = panel.y + 140
        draw_text("WARES (click to buy, hover for details)", font_main,
                  (150, 200, 165), screen, panel.x + 30, y - 34)
        mouse_pos = pygame.mouse.get_pos()
        hovered_entry = None
        for entry in self.shop["goods"]:
            row = pygame.Rect(panel.x + 26, y, panel.w - 52, 56)
            hover = row.collidepoint(mouse_pos)
            if hover:
                hovered_entry = entry
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
