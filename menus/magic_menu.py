import pygame
from settings import *
from ui_kit import UIButton, draw_panel, draw_text, font_title, font_main, font_small, format_money, GOLD_COLOR, RED, GRAY
from menus.base_menu import BaseMenu
from sound_manager import sound_system


class MagicMenu(BaseMenu):
    """
    Magic Shop UI:
      - 1920x1080-friendly responsive grid
      - Tier tabs (1..8) filter
      - Scrollable card grid (mouse wheel)
      - Keeps metadata for "LEARNED" slots even after purchase (shop slot becomes None)

    Notes:
      - This menu renders whatever is in manager.magic_shop_items.
      - If you want "ALL spells always visible", make your GameManager populate magic_shop_items with the full catalogue
        (right now your generate_shop() uses get_spell_shop_items(5) so it only shows 5 random spells).
    """

    HEADER_H = 120
    TABS_H = 46
    FOOTER_PAD = 22

    def __init__(self, manager):
        super().__init__(manager)

        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)

        self.selected_tier = 1
        self.scroll_y = 0

        # Slot metadata: persists even if the shop slot becomes None after buying.
        # idx -> dict(name, tier, description, mana_cost, range, cost, rarity, draw_fn)
        self._slot_meta = {}

        # Layout cache for hit-testing in handle_event()
        self._layout = None

        self._sync_slot_meta()

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    def _sync_slot_meta(self):
        """Cache per-slot metadata so LEARNED slots can still show tier/name after purchase."""
        shop_items = getattr(self.manager, "magic_shop_items", []) or []

        # Trim meta if shop shrinks
        dead_keys = [k for k in self._slot_meta.keys() if k >= len(shop_items)]
        for k in dead_keys:
            self._slot_meta.pop(k, None)

        for idx, item in enumerate(shop_items):
            if item is None:
                continue

            if idx not in self._slot_meta:
                tier = int(getattr(item, "tier", 1) or 1)
                name = str(getattr(item, "name", "Unknown Spell"))
                desc = str(getattr(item, "description", ""))
                mana = int(getattr(item, "mana_cost", 0) or 0)
                rng = int(getattr(item, "range", 0) or 0)
                cost = int(getattr(item, "cost", 0) or 0)
                rarity = str(getattr(item, "rarity", ""))

                # Prefer draw_card_icon (your spells usually implement it), fallback to draw_icon.
                draw_fn = None
                if hasattr(item, "draw_card_icon"):
                    draw_fn = item.draw_card_icon
                elif hasattr(item, "draw_icon"):
                    draw_fn = item.draw_icon

                self._slot_meta[idx] = {
                    "tier": tier,
                    "name": name,
                    "description": desc,
                    "mana_cost": mana,
                    "range": rng,
                    "cost": cost,
                    "rarity": rarity,
                    "draw_fn": draw_fn,
                }

    def _wrap_lines(self, text, font, max_width):
        """Basic word wrap using pygame font metrics."""
        if not text:
            return []
        words = text.split()
        lines = []
        cur = ""

        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def _get_slots_for_tier(self, tier):
        """Return list of (orig_idx, current_item, meta) for selected tier."""
        self._sync_slot_meta()
        shop_items = getattr(self.manager, "magic_shop_items", []) or []

        slots = []
        for idx in range(len(shop_items)):
            meta = self._slot_meta.get(idx)
            if not meta:
                # Item has never been seen (should be rare), skip.
                continue
            if int(meta.get("tier", 1)) != int(tier):
                continue
            slots.append((idx, shop_items[idx], meta))
        return slots

    def _compute_layout(self, screen, slots_count):
        """Compute and store layout used for drawing + clicking."""
        w, h = SCREEN_WIDTH, SCREEN_HEIGHT

        # Tabs rects (8 tiers)
        tabs_y = self.HEADER_H
        tabs_rect = pygame.Rect(0, tabs_y, w, self.TABS_H)

        # Content rect
        content_y = tabs_y + self.TABS_H + 14
        content_h = h - content_y - self.FOOTER_PAD
        content_rect = pygame.Rect(0, content_y, w, content_h)

        # Grid metrics (responsive)
        left_margin = 70
        right_margin = 70
        top_pad = 10
        bottom_pad = 10

        card_w = 250
        card_h = 310
        pad = 22

        usable_w = max(1, w - left_margin - right_margin)
        cols = max(1, (usable_w + pad) // (card_w + pad))
        cols = int(max(1, min(cols, 7)))

        grid_w = int(cols * card_w + (cols - 1) * pad)
        grid_left = int((w - grid_w) // 2)
        grid_top = content_y + top_pad

        rows = (slots_count + cols - 1) // cols if slots_count > 0 else 0
        total_h = rows * (card_h + pad) - pad if rows > 0 else 0
        view_h = content_h - top_pad - bottom_pad
        max_scroll = max(0, total_h - view_h)

        # Tier tab rects (centered row)
        tab_w = 108
        tab_h = 36
        tab_pad = 10
        tabs_total_w = 8 * tab_w + 7 * tab_pad
        tabs_left = (w - tabs_total_w) // 2

        tier_tabs = []
        for i in range(8):
            x = tabs_left + i * (tab_w + tab_pad)
            y = tabs_y + (self.TABS_H - tab_h) // 2
            tier_tabs.append((i + 1, pygame.Rect(x, y, tab_w, tab_h)))

        self._layout = {
            "tabs_rect": tabs_rect,
            "tier_tabs": tier_tabs,
            "content_rect": content_rect,
            "grid_left": grid_left,
            "grid_top": grid_top,
            "cols": cols,
            "card_w": card_w,
            "card_h": card_h,
            "pad": pad,
            "view_h": view_h,
            "max_scroll": max_scroll,
        }

        self.scroll_y = max(0, min(self.scroll_y, max_scroll))

    def _scroll(self, delta):
        """delta > 0 scroll down (content moves up)."""
        if not self._layout:
            return
        max_scroll = self._layout.get("max_scroll", 0)
        self.scroll_y = max(0, min(self.scroll_y + delta, max_scroll))

    def _hit_test_tab(self, mouse_pos):
        if not self._layout:
            return None
        for tier, r in self._layout["tier_tabs"]:
            if r.collidepoint(mouse_pos):
                return tier
        return None

    def _hit_test_card(self, mouse_pos, slots_count):
        """Return the index within the filtered slots list, or None."""
        if not self._layout:
            return None

        content_rect = self._layout["content_rect"]
        if not content_rect.collidepoint(mouse_pos):
            return None

        grid_left = self._layout["grid_left"]
        grid_top = self._layout["grid_top"]
        cols = self._layout["cols"]
        card_w = self._layout["card_w"]
        card_h = self._layout["card_h"]
        pad = self._layout["pad"]

        mx, my = mouse_pos

        local_x = mx - grid_left
        local_y = my - (grid_top - self.scroll_y)

        if local_x < 0 or local_y < 0:
            return None

        cell_w = card_w + pad
        cell_h = card_h + pad

        col = int(local_x // cell_w)
        row = int(local_y // cell_h)
        if col < 0 or col >= cols or row < 0:
            return None

        index = row * cols + col
        if index < 0 or index >= slots_count:
            return None

        in_x = local_x - col * cell_w
        in_y = local_y - row * cell_h
        if in_x > card_w or in_y > card_h:
            return None

        return index

    # ---------------------------------------------------------------------
    # Events
    # ---------------------------------------------------------------------
    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()

        if self.btn_back.is_clicked(event):
            self.next_state = "magic_school"
            sound_system.play_sound('click')
            return

        slots = self._get_slots_for_tier(self.selected_tier)
        self._compute_layout(None, len(slots))

        if event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_8:
                new_tier = (event.key - pygame.K_0)
                if 1 <= new_tier <= 8:
                    self.selected_tier = new_tier
                    self.scroll_y = 0
                    sound_system.play_sound("click")
                    return
            if event.key == pygame.K_LEFT:
                self.selected_tier = max(1, self.selected_tier - 1)
                self.scroll_y = 0
                sound_system.play_sound("click")
                return
            if event.key == pygame.K_RIGHT:
                self.selected_tier = min(8, self.selected_tier + 1)
                self.scroll_y = 0
                sound_system.play_sound("click")
                return

        if event.type == pygame.MOUSEWHEEL:
            if self._layout and self._layout["content_rect"].collidepoint(mouse_pos):
                self._scroll(-event.y * 60)
                return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                clicked_tier = self._hit_test_tab(mouse_pos)
                if clicked_tier is not None and clicked_tier != self.selected_tier:
                    self.selected_tier = clicked_tier
                    self.scroll_y = 0
                    sound_system.play_sound("click")
                    return

            if event.button == 4:
                if self._layout and self._layout["content_rect"].collidepoint(mouse_pos):
                    self._scroll(-70)
                    return
            if event.button == 5:
                if self._layout and self._layout["content_rect"].collidepoint(mouse_pos):
                    self._scroll(70)
                    return

            if event.button == 1:
                hit = self._hit_test_card(mouse_pos, len(slots))
                if hit is None:
                    return

                orig_idx, item, meta = slots[hit]
                if item is None:
                    sound_system.play_sound("error")
                    return

                if self.manager.buy_shop_item(orig_idx, is_magic=True):
                    sound_system.play_sound('buy')
                else:
                    sound_system.play_sound('error')
                return

    # ---------------------------------------------------------------------
    # Drawing
    # ---------------------------------------------------------------------
    def draw(self, screen):
        self.draw_themed_background(screen, mood="city")

        mouse_pos = pygame.mouse.get_pos()
        self.btn_back.check_hover(mouse_pos)

        slots = self._get_slots_for_tier(self.selected_tier)
        self._compute_layout(screen, len(slots))

        top_rect = pygame.Rect(0, 0, SCREEN_WIDTH, self.HEADER_H)
        self.draw_soft_panel(screen, top_rect, alpha=140, border_alpha=100, radius=0)

        self.btn_back.draw(screen)
        draw_text("THE PRISM COLLEGIUM", font_title, (190, 155, 255), screen, 330, 28)
        draw_text("Browse spells by tier • Mouse wheel to scroll", font_small, (190, 190, 210), screen, 330, 78)
        draw_text(f"Funds: {format_money(self.manager.gold)}", font_title, GOLD_COLOR, screen, 40, 70)

        tabs_strip = self._layout["tabs_rect"]
        self.draw_soft_panel(screen, tabs_strip, alpha=110, border_alpha=70, radius=0)

        for tier, r in self._layout["tier_tabs"]:
            hover = r.collidepoint(mouse_pos)
            selected = (tier == self.selected_tier)

            alpha = 170 if selected else (140 if hover else 115)
            border_alpha = 120 if selected else 80
            self.draw_soft_panel(screen, r, alpha=alpha, border_alpha=border_alpha, radius=12)

            label_col = (230, 210, 255) if selected else (200, 200, 220)
            draw_text(f"TIER {tier}", font_small, label_col, screen, r.x + 18, r.y + 10)

        content_rect = self._layout["content_rect"]
        panel_rect = content_rect.inflate(-90, -12)
        self.draw_soft_panel(screen, panel_rect, alpha=90, border_alpha=70, radius=18)

        grid_left = self._layout["grid_left"]
        grid_top = self._layout["grid_top"]
        cols = self._layout["cols"]
        card_w = self._layout["card_w"]
        card_h = self._layout["card_h"]
        pad = self._layout["pad"]

        screen.set_clip(panel_rect)

        hovered_card = None

        for idx_in_view, (orig_idx, item, meta) in enumerate(slots):
            col = idx_in_view % cols
            row = idx_in_view // cols

            x = grid_left + col * (card_w + pad)
            y = (grid_top + row * (card_h + pad)) - self.scroll_y

            card_rect = pygame.Rect(x, y, card_w, card_h)

            if card_rect.bottom < panel_rect.top - 10 or card_rect.top > panel_rect.bottom + 10:
                continue

            is_hover = card_rect.collidepoint(mouse_pos)

            self.draw_soft_panel(screen, card_rect, alpha=150 if is_hover else 130, border_alpha=95, radius=16)

            inner = card_rect.inflate(-10, -10)
            base_col = (28, 18, 50) if not is_hover else (45, 30, 80)
            pygame.draw.rect(screen, base_col, inner, border_radius=14)

            icon_box = pygame.Rect(inner.x + (inner.w - 104) // 2, inner.y + 14, 104, 104)
            pygame.draw.rect(screen, (10, 6, 24), icon_box, border_radius=10)
            pygame.draw.rect(screen, (90, 70, 130), icon_box, 1, border_radius=10)

            draw_fn = None
            if item is not None:
                if hasattr(item, "draw_card_icon"):
                    draw_fn = item.draw_card_icon
                elif hasattr(item, "draw_icon"):
                    draw_fn = item.draw_icon
            else:
                draw_fn = meta.get("draw_fn")

            if draw_fn:
                try:
                    draw_fn(screen, icon_box.x, icon_box.y, icon_box.w)
                except TypeError:
                    pass
                except Exception:
                    pass

            name = meta.get("name", "Unknown")
            rarity = meta.get("rarity", "")
            name_col = (220, 220, 255) if item is not None else (120, 120, 150)
            draw_text(name, font_small, name_col, screen, inner.x + 12, inner.y + 126)
            if rarity:
                rar_col = (160, 160, 200) if item is not None else (100, 100, 130)
                draw_text(rarity, font_small, rar_col, screen, inner.x + 12, inner.y + 146)

            mana = meta.get("mana_cost", 0)
            rng = meta.get("range", 0)
            tier = meta.get("tier", 1)

            stat_col = (120, 210, 255) if item is not None else (90, 130, 160)
            draw_text(f"Mana: {mana}", font_small, stat_col, screen, inner.x + 12, inner.y + 174)
            draw_text(f"Range: {rng}", font_small,
                      (180, 180, 220) if item is not None else (110, 110, 140),
                      screen, inner.x + 12, inner.y + 196)
            draw_text(f"Tier {tier}", font_small,
                      (200, 180, 255) if item is not None else (120, 110, 160),
                      screen, inner.x + 12, inner.y + 218)

            if item is None:
                draw_text("LEARNED", font_title, (120, 120, 160), screen, inner.x + 12, inner.y + 248)
            else:
                can_afford = self.manager.gold >= int(getattr(item, "cost", meta.get("cost", 0)) or 0)
                price_col = GOLD_COLOR if can_afford else RED
                draw_text(format_money(int(getattr(item, 'cost', meta.get('cost', 0)) or 0)),
                          font_title, price_col, screen, inner.x + 12, inner.y + 248)

            if is_hover:
                hovered_card = (card_rect, item, meta)

        screen.set_clip(None)

        max_scroll = self._layout["max_scroll"]
        if max_scroll > 0:
            bar_area = pygame.Rect(panel_rect.right + 16, panel_rect.top + 10, 14, panel_rect.h - 20)
            pygame.draw.rect(screen, (20, 15, 30), bar_area, border_radius=10)
            pygame.draw.rect(screen, (90, 70, 130), bar_area, 1, border_radius=10)

            view_h = self._layout["view_h"]
            total_h = view_h + max_scroll
            thumb_h = max(30, int(bar_area.h * (view_h / max(1, total_h))))
            t = 0 if max_scroll == 0 else (self.scroll_y / max_scroll)
            thumb_y = int(bar_area.y + t * (bar_area.h - thumb_h))
            thumb = pygame.Rect(bar_area.x + 2, thumb_y, bar_area.w - 4, thumb_h)
            pygame.draw.rect(screen, (170, 140, 255), thumb, border_radius=8)

        draw_text(f"Tier {self.selected_tier} • {len(slots)} spell(s) available in shop",
                  font_small, (200, 200, 220), screen, 70, SCREEN_HEIGHT - 26)

        if hovered_card:
            card_rect, item, meta = hovered_card
            desc = meta.get("description", "") or ""
            if desc:
                tw, th = 360, 110
                tx = min(mouse_pos[0] + 18, SCREEN_WIDTH - tw - 12)
                ty = min(mouse_pos[1] + 18, SCREEN_HEIGHT - th - 12)
                draw_panel(screen, tx, ty, tw, th, (20, 15, 30))
                pygame.draw.rect(screen, (90, 70, 130), (tx, ty, tw, th), 1, border_radius=6)

                lines = self._wrap_lines(desc, font_small, tw - 20)
                y = ty + 10
                for line in lines[:5]:
                    draw_text(line, font_small, WHITE, screen, tx + 10, y)
                    y += 18
