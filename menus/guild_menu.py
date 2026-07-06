import pygame
from settings import *
from ui_kit import UIButton, draw_panel, draw_text, font_title, font_main, font_small
from menus.base_menu import BaseMenu
from sound_manager import sound_system
from items.item_registry import create_fists


def draw_progress_bar(screen, x, y, w, h, pct,
                      back=(40, 40, 60), fill=(90, 180, 255), border=(180, 180, 180)):
    pct = max(0.0, min(1.0, float(pct)))
    pygame.draw.rect(screen, back, (x, y, w, h), border_radius=6)
    pygame.draw.rect(screen, fill, (x, y, int(w * pct), h), border_radius=6)
    pygame.draw.rect(screen, border, (x, y, w, h), 2, border_radius=6)


class GuildMenu(BaseMenu):
    """
    GuildMenu (drag & drop equipment)
    - ALL equip locking is handled by Gladiator.can_equip_item_to_slot(...)
    - We ONLY do slot-type sanity checks here (armor into body, spell into spell slots, etc.)
    """
    def __init__(self, manager):
        super().__init__(manager)

        # --- UI LAYOUT ---
        self.pad = 30
        self.left_panel_w = 340

        self.slots_center_x = int(SCREEN_WIDTH * 0.43)
        self.slots_center_y = int(SCREEN_HEIGHT * 0.38)

        self.bag_x = int(SCREEN_WIDTH * 0.62)
        self.bag_y = 170
        self.bag_w = SCREEN_WIDTH - self.bag_x - self.pad
        self.bag_h = SCREEN_HEIGHT - self.bag_y - self.pad

        # --- BUTTONS ---
        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)
        self.btn_prev = UIButton(0, 0, 36, 70, "<", None, GRAY)
        self.btn_next = UIButton(0, 0, 36, 70, ">", None, GRAY)
        self.btn_rename = UIButton(0, 0, 120, 34, "RENAME", None, GRAY)
        self.btn_dismiss = UIButton(0, 0, 120, 34, "DISMISS", None, (200, 60, 60))

        # Skill tree button
        self.btn_open_skill_tree = UIButton(0, 0, 200, 52, "OPEN SKILL TREE", None, GOLD_COLOR)

        # Tabs
        self.tabs = ["ARMORS", "WEAPONS", "SPELLS", "USABLES", "CRAFTING", "SKILLS"]
        self.active_tab = "WEAPONS"
        self.tab_buttons = []
        self._build_tab_buttons()

        # Rename state
        self.selected_index = 0
        self.is_renaming = False
        self.rename_text = ""

        # Drag & Drop State
        self.drag_item = None
        self.drag_source = None      # 'bag' or 'slot'
        self.drag_origin_index = None  # bag real index OR slot name str
        self.drag_origin_obj = None

        # Crafting scroll
        self.craft_scroll = 0

        # Mapping: view index -> equipment_bag real index
        self._bag_view_indices = []

        # --- FEEDBACK SYSTEM ---
        self.feedback_msg = ""
        self.feedback_timer = 0

    # -------------------------
    # TAB BUTTONS
    # -------------------------
    def _build_tab_buttons(self):
        self.tab_buttons = []
        x0 = self.bag_x
        y0 = 110
        w = int((self.bag_w - 10) / len(self.tabs))
        for i, t in enumerate(self.tabs):
            self.tab_buttons.append(UIButton(x0 + i * w, y0, w - 6, 44, t, None, GRAY))

    # -------------------------
    # CATEGORY / FILTER
    # -------------------------
    def _item_category(self, item):
        slot = getattr(item, "slot_type", "")
        slot_s = str(slot).lower()

        if slot_s in ["head", "body"]:
            return "ARMORS"
        if slot_s == "usable":
            return "USABLES"
        if slot_s == "spell" or "spell" in slot_s:
            return "SPELLS"

        # Weapons includes shields if they go to hands
        if slot_s in ["main_hand", "off_hand", "weapon", "melee", "ranged"]:
            return "WEAPONS"

        t = str(getattr(item, "type", "")).lower()
        if t in ["melee", "ranged", "weapon", "shield"]:
            return "WEAPONS"

        return "WEAPONS"

    def _get_filtered_bag_view(self):
        if self.active_tab in ["CRAFTING", "SKILLS"]:
            self._bag_view_indices = []
            return []

        out = []
        self._bag_view_indices = []
        for i, item in enumerate(self.manager.equipment_bag):
            if not item:
                continue
            cat = self._item_category(item)
            if cat == self.active_tab:
                out.append((i, item))
                self._bag_view_indices.append(i)
        return out

    # -------------------------
    # SLOT RECTS
    # -------------------------
    def get_slot_rects(self, cx, cy):
        s = 72
        return {
            'head':      pygame.Rect(cx, cy - 110, s, s),
            'body':      pygame.Rect(cx, cy + 110, s, s),
            'main_hand': pygame.Rect(cx - 120, cy, s, s),
            'off_hand':  pygame.Rect(cx + 120, cy, s, s),
            'spell1':    pygame.Rect(cx - 120, cy + 240, s, s),
            'spell2':    pygame.Rect(cx, cy + 240, s, s),
            'spell3':    pygame.Rect(cx + 120, cy + 240, s, s),
            'usable':    pygame.Rect(cx + 240, cy + 240, s, s)
        }

    # -------------------------
    # UNLOCK HELPERS
    # -------------------------
    def _spell_slot_unlocked(self, unit, idx: int) -> bool:
        val = getattr(unit, "spell_slots_unlocked", 0)
        try:
            if isinstance(val, (set, list, tuple)):
                return int(idx) in set(int(x) for x in val)
            return int(val) >= int(idx)
        except Exception:
            return False

    def _equip_check(self, unit, slot_name: str, item):
        """Return (ok: bool, reason: str) with backward compatible calls."""
        if unit is None:
            return False, "No unit."
        
        # Newer API (returns (ok, reason))
        if hasattr(unit, "can_equip_item_to_slot"):
            try:
                ok, reason = unit.can_equip_item_to_slot(slot_name, item)
                try:
                    unit.last_equip_error = str(reason or "")
                except Exception:
                    pass
                return bool(ok), str(reason or "")
            except Exception:
                return False, "Equip check failed."
        
        # Old API
        if hasattr(unit, "can_equip_to_slot"):
            try:
                ok = bool(unit.can_equip_to_slot(slot_name, item))
                reason = str(getattr(unit, "last_equip_error", "") or "")
                return ok, reason
            except TypeError:
                pass

        return True, ""

    # -------------------------
    # FEEDBACK
    # -------------------------
    def _show_feedback(self, msg):
        self.feedback_msg = str(msg)
        self.feedback_timer = 120  # ~2 seconds @60fps

    # -------------------------
    # SAFE REMOVE FROM BAG (only when equip succeeds)
    # -------------------------
    def _remove_from_equipment_bag_safe(self, real_index, item_obj):
        bag = self.manager.equipment_bag
        if isinstance(real_index, int) and 0 <= real_index < len(bag):
            if bag[real_index] is item_obj:
                bag.pop(real_index)
                return True
        # fallback search
        for i, it in enumerate(bag):
            if it is item_obj:
                bag.pop(i)
                return True
        return False

    # -------------------------
    # SLOT TYPE SANITY CHECK
    # -------------------------
    def _valid_slot_type(self, item, slot_name: str) -> bool:
        if not item:
            return True

        slot_name = str(slot_name).lower()
        item_slot = str(getattr(item, "slot_type", "")).lower()
        item_type = str(getattr(item, "type", "")).lower()

        # Spell slots accept ONLY spells
        if slot_name.startswith("spell"):
            return (item_slot == "spell") or (item_type == "spell")

        # Armor slots
        if slot_name in ["head", "body"]:
            return item_slot in ["head", "body"]

        # Usable slot
        if slot_name == "usable":
            return item_slot == "usable"

        # Hands
        if slot_name in ["main_hand", "off_hand"]:
            if item_slot in ["main_hand", "off_hand", "weapon", "melee", "ranged"]:
                return True
            if item_type in ["weapon", "melee", "ranged", "shield"]:
                return True
            return False

        return False

    # -------------------------
    # XP Helpers
    # -------------------------
    def _get_xp_ui(self, unit):
        lvl = int(getattr(unit, "level", 1) or 1)
        total_xp = int(getattr(unit, "xp", 0) or 0)
        if hasattr(unit, "xp_progress_ratio"):
            pct = float(unit.xp_progress_ratio())
            if getattr(unit, "level", 1) >= getattr(unit, "max_level", 999999):
                return lvl, "MAX", 1.0
            try:
                cur_in = int(unit.xp_progress_in_level())
                span = int(unit.xp_span_current_level())
                rem = int(unit.xp_to_next_level())
                xp_text = f"XP: {cur_in}/{span} (Next: {rem})"
            except Exception:
                xp_text = f"XP: {total_xp}"
            return lvl, xp_text, pct
        return lvl, f"XP: {total_xp}", 0.0

    # -------------------------
    # EVENTS
    # -------------------------
    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()

        if self.feedback_timer > 0:
            self.feedback_timer -= 1

        if event.type == pygame.MOUSEWHEEL and self.active_tab == "CRAFTING":
            self.craft_scroll += -event.y * 22
            self.craft_scroll = max(0, self.craft_scroll)
            return

        # Keyboard (rename + cheats)
        if event.type == pygame.KEYDOWN:
            team_list = list(self.manager.my_team)

            # RENAME MODE
            if self.is_renaming:
                if not team_list:
                    return
                unit = team_list[self.selected_index]
                if event.key == pygame.K_RETURN:
                    self.is_renaming = False
                elif event.key == pygame.K_BACKSPACE:
                    self.rename_text = self.rename_text[:-1]
                    unit.name = self.rename_text
                else:
                    self.rename_text += event.unicode
                    unit.name = self.rename_text
                return

            # CHEATS
            if CHEAT_MODE and team_list:
                if event.key == pygame.K_l:
                    unit = team_list[self.selected_index]
                    if unit.add_xp(1000):
                        sound_system.play_sound('recruit')
                        self._show_feedback(f"CHEAT: {unit.name} Leveled Up!")
                    else:
                        self._show_feedback(f"CHEAT: {unit.name} gained 1000 XP")

                if event.key == pygame.K_m:
                    self.manager.gold += 1000
                    sound_system.play_sound('coin')
                    self._show_feedback("CHEAT: +1000 Gold")

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Back
            if self.btn_back.rect.collidepoint(mouse_pos):
                self.next_state = "hub"
                sound_system.play_sound('click')
                return

            # Tabs
            for b in self.tab_buttons:
                if b.rect.collidepoint(mouse_pos):
                    self.active_tab = b.text
                    sound_system.play_sound('click')
                    self.drag_item = None
                    return

            # Nav
            if self.btn_prev.rect.collidepoint(mouse_pos):
                team_list = list(self.manager.my_team)
                if team_list:
                    self.selected_index = (self.selected_index - 1) % len(team_list)
                    self.is_renaming = False
                    sound_system.play_sound('click')
                return

            if self.btn_next.rect.collidepoint(mouse_pos):
                team_list = list(self.manager.my_team)
                if team_list:
                    self.selected_index = (self.selected_index + 1) % len(team_list)
                    self.is_renaming = False
                    sound_system.play_sound('click')
                return

            team_list = list(self.manager.my_team)

            # Rename
            if self.btn_rename.rect.collidepoint(mouse_pos) and team_list:
                self.is_renaming = True
                self.rename_text = team_list[self.selected_index].name
                return

            # Dismiss
            if self.btn_dismiss.rect.collidepoint(mouse_pos) and team_list:
                unit_to_fire = team_list[self.selected_index]
                if self.manager.dismiss_unit(unit_to_fire):
                    sound_system.play_sound('error')
                    new_len = len(self.manager.my_team)
                    if self.selected_index >= new_len:
                        self.selected_index = max(0, new_len - 1)
                return

            # Skill Tree Open
            if self.active_tab == "SKILLS":
                if self.btn_open_skill_tree.rect.collidepoint(mouse_pos):
                    if team_list:
                        unit = team_list[self.selected_index]
                        setattr(self.manager, "selected_hero", unit)
                        setattr(self.manager, "skill_tree_return_state", "guild")
                        self.next_state = "skill_tree"
                        sound_system.play_sound('click')
                    return
                return

            # Drag from Bag
            if self.active_tab != "CRAFTING":
                view = self._get_filtered_bag_view()
                bag_cols = 6
                cell = 74
                start_x = self.bag_x + 10
                start_y = self.bag_y + 10
                max_cells = bag_cols * int((self.bag_h - 20) // cell)

                for vi in range(int(max_cells)):
                    col = vi % bag_cols
                    row = vi // bag_cols
                    rect = pygame.Rect(start_x + col * cell, start_y + row * cell, 68, 68)

                    if rect.collidepoint(mouse_pos):
                        if vi < len(view):
                            real_index, item = view[vi]
                            self.drag_item = item
                            self.drag_source = 'bag'
                            self.drag_origin_index = real_index
                            self.drag_origin_obj = item
                            sound_system.play_sound('click')
                        return

            # Drag from Slot
            if team_list:
                unit = team_list[self.selected_index]
                slots = self.get_slot_rects(self.slots_center_x, self.slots_center_y)
                for name, rect in slots.items():
                    item = unit.equipment.get(name)
                    if rect.collidepoint(mouse_pos) and item:
                        if getattr(item, "name", "") == "Fists":
                            continue
                        self.drag_item = item
                        self.drag_source = 'slot'
                        self.drag_origin_index = name
                        self.drag_origin_obj = item
                        sound_system.play_sound('click')
                        return

        elif event.type == pygame.MOUSEBUTTONUP:
            if not self.drag_item:
                return

            team_list = list(self.manager.my_team)
            unit = team_list[self.selected_index] if team_list else None
            mouse_pos = pygame.mouse.get_pos()

            dropped = False

            # A) Drop to slot
            slots = self.get_slot_rects(self.slots_center_x, self.slots_center_y)
            if unit:
                for name, rect in slots.items():
                    if not rect.collidepoint(mouse_pos):
                        continue

                    # 1) Slot-type sanity
                    if not self._valid_slot_type(self.drag_item, name):
                        self._show_feedback("Wrong slot type.")
                        sound_system.play_sound('error')
                        break

                    # 2) Hard locking check (Gladiator)
                    ok, reason = self._equip_check(unit, name, self.drag_item)
                    if not ok:
                        self._show_feedback(reason or "Cannot equip.")
                        sound_system.play_sound('error')
                        break

                    # 3) SAFE MOVE:
                    # If source is slot, temporarily remove from origin first (so we don't duplicate)
                    origin_slot = None
                    origin_item = None
                    if self.drag_source == "slot":
                        origin_slot = str(self.drag_origin_index)
                        origin_item = unit.equipment.get(origin_slot)
                        # Temporarily clear origin
                        if origin_slot == "main_hand":
                            unit.equipment["main_hand"] = create_fists()
                        else:
                            unit.equipment[origin_slot] = None

                    # Equip to target
                    old_item = unit.equip_item_to_slot(name, self.drag_item)

                    # Confirm success by checking the target slot
                    success = (unit.equipment.get(name) is self.drag_item)

                    if not success:
                        # Revert origin if we came from slot
                        if origin_slot is not None:
                            unit.equipment[origin_slot] = origin_item
                            unit.calculate_final_stats()
                        self._show_feedback(getattr(unit, "last_equip_error", "") or "Cannot equip.")
                        sound_system.play_sound('error')
                        break

                    # Remove from bag ONLY after success
                    if self.drag_source == "bag":
                        self._remove_from_equipment_bag_safe(self.drag_origin_index, self.drag_origin_obj)

                    # If we displaced something from target, push it to bag (except fists/no armor)
                    if old_item and getattr(old_item, "name", "") not in ["Fists", "No Armor"]:
                        self.manager.equipment_bag.append(old_item)

                    dropped = True
                    sound_system.play_sound('recruit')
                    break

            # B) Drop to bag (unequip)
            bag_rect = pygame.Rect(self.bag_x, self.bag_y, self.bag_w, self.bag_h)
            if not dropped and bag_rect.collidepoint(mouse_pos) and unit:
                if self.drag_source == 'slot':
                    rem = unit.unequip_slot(self.drag_origin_index)
                    if rem:
                        self.manager.equipment_bag.append(rem)
                    dropped = True
                    sound_system.play_sound('click')
                elif self.drag_source == 'bag':
                    dropped = True  # cancel

            # Clear drag
            self.drag_item = None
            self.drag_source = None
            self.drag_origin_index = None
            self.drag_origin_obj = None

    # -------------------------
    # DRAW
    # -------------------------
    def draw(self, screen):
        screen.fill((20, 20, 28))
        mouse_pos = pygame.mouse.get_pos()

        self.btn_back.check_hover(mouse_pos)
        self.btn_back.draw(screen)
        draw_text("GUILD HOUSE", font_title, WHITE, screen, SCREEN_WIDTH // 2 - 140, 40)

        for b in self.tab_buttons:
            b.current_color = (90, 90, 120) if b.text == self.active_tab else (55, 55, 70)
            b.check_hover(mouse_pos)
            b.draw(screen)

        team_list = list(self.manager.my_team)
        if not team_list:
            draw_text("No heroes recruited.", font_main, GRAY, screen, 100, 200)
            return

        if self.selected_index >= len(team_list):
            self.selected_index = 0
        unit = team_list[self.selected_index]

        # --- LEFT PANEL ---
        char_x = self.pad
        char_y = 140
        panel_w = self.left_panel_w
        panel_h = SCREEN_HEIGHT - char_y - self.pad
        pygame.draw.rect(screen, (30, 30, 40),
                         (char_x, char_y, panel_w, panel_h),
                         border_radius=12)
        pygame.draw.rect(screen, (60, 60, 70), (char_x, char_y, panel_w, panel_h), 2, border_radius=12)

        # Image
        if not getattr(unit, "use_sprites", False):
            unit.draw_procedural()
        
        # Use big_image if available for better quality
        img_surf = getattr(unit, "big_image", unit.image)
        if not img_surf: img_surf = unit.image

        if img_surf:
            # Scale to fit nicely
            target_h = 280
            ratio = img_surf.get_width() / max(1, img_surf.get_height())
            target_w = int(target_h * ratio)
            if target_w > panel_w - 40:
                target_w = panel_w - 40
                target_h = int(target_w / ratio)
            
            final_img = pygame.transform.smoothscale(img_surf, (target_w, target_h))
            img_x = char_x + (panel_w - target_w) // 2
            img_y = char_y + 20
            screen.blit(final_img, (img_x, img_y))
        else:
            img_x = char_x + panel_w // 2
            img_y = char_y + 20

        # Nav Buttons (Fixed positions relative to panel)
        self.btn_prev.rect.topleft = (char_x + 10, img_y + 100)
        self.btn_next.rect.topleft = (char_x + panel_w - 46, img_y + 100)
        self.btn_prev.check_hover(mouse_pos)
        self.btn_prev.draw(screen)
        self.btn_next.check_hover(mouse_pos)
        self.btn_next.draw(screen)

        # Stats Area
        s_y = char_y + 320
        
        # Name & Level
        lvl, xp_text, pct = self._get_xp_ui(unit)
        draw_text(unit.name, font_title, WHITE, screen, char_x + 20, s_y)
        draw_text(f"Lvl {lvl} {unit.race_name}", font_small, GOLD_COLOR, screen, char_x + 20, s_y + 35)
        
        # XP Bar
        draw_progress_bar(screen, char_x + 20, s_y + 60, panel_w - 40, 8, pct)
        draw_text(xp_text, font_small, (150, 150, 150), screen, char_x + 20, s_y + 72)

        # Attributes Row
        attr_y = s_y + 100
        # Draw backgrounds for attributes
        attr_w = (panel_w - 50) // 3
        for i, (label, val, col) in enumerate([
            ("STR", int(unit.strength), RED),
            ("DEX", int(unit.dexterity), YELLOW),
            ("INT", int(unit.intelligence), (100, 150, 255))
        ]):
            ax = char_x + 20 + i * (attr_w + 5)
            pygame.draw.rect(screen, (40, 40, 50), (ax, attr_y, attr_w, 50), border_radius=6)
            draw_text(label, font_small, col, screen, ax + 10, attr_y + 5)
            draw_text(str(val), font_main, WHITE, screen, ax + 10, attr_y + 24)

        # Detailed Stats
        det_y = attr_y + 65
        
        # Helper for stat rows
        def draw_stat_row(label, current, max_val, color, y_pos):
            draw_text(label, font_small, color, screen, char_x + 25, y_pos)
            val_str = f"{int(current)} / {int(max_val)}"
            draw_text(val_str, font_small, WHITE, screen, char_x + 120, y_pos)
            # Small bar
            bar_w = 140
            bar_h = 6
            bx = char_x + 180
            pct = max(0, min(1, current / max(1, max_val)))
            pygame.draw.rect(screen, (40,40,40), (bx, y_pos+6, bar_w, bar_h))
            pygame.draw.rect(screen, color, (bx, y_pos+6, int(bar_w*pct), bar_h))

        draw_stat_row("Health", unit.current_hp, unit.max_hp, GREEN, det_y)
        draw_stat_row("Mana", unit.current_mana, unit.max_mana, (80, 120, 255), det_y + 25)
        draw_stat_row("Stamina", unit.current_stamina, unit.max_stamina, YELLOW, det_y + 50)

        # Armor & Speed
        misc_y = det_y + 85
        pygame.draw.line(screen, (50, 50, 60), (char_x + 20, misc_y), (char_x + panel_w - 20, misc_y), 1)
        
        misc_y += 10
        draw_text(f"Armor: {int(unit.defense)}", font_small, (200, 200, 220), screen, char_x + 25, misc_y)
        draw_text(f"Speed: {unit.speed:.1f}", font_small, (200, 200, 220), screen, char_x + 180, misc_y)
        
        misc_y += 25
        # Crit chance if available
        crit = getattr(unit, "crit_chance", 0.05) * 100
        draw_text(f"Crit: {int(crit)}%", font_small, (200, 100, 100), screen, char_x + 25, misc_y)

        # Rename / Dismiss
        btn_y = char_y + panel_h - 50
        
        if self.is_renaming:
            pygame.draw.rect(screen, WHITE, (char_x + 20, btn_y, panel_w - 40, 34))
            draw_text(self.rename_text, font_small, BLACK, screen, char_x + 28, btn_y + 8)
        else:
            self.btn_rename.rect.topleft = (char_x + 20, btn_y)
            self.btn_rename.check_hover(mouse_pos)
            self.btn_rename.draw(screen)
            
            self.btn_dismiss.rect.topleft = (char_x + panel_w - 140, btn_y)
            self.btn_dismiss.check_hover(mouse_pos)
            self.btn_dismiss.draw(screen)

        # --- CENTER SLOTS ---
        cx, cy = self.slots_center_x, self.slots_center_y
        slots = self.get_slot_rects(cx, cy)

        pygame.draw.circle(screen, (25, 25, 35), (cx + 36, cy + 36), 130)

        # spell slot lock by unit.spell_slots_unlocked
        # supports both: int (old) and set({1,2,3}) (new)
        for name, rect in slots.items():
            is_locked = False
            if name.startswith("spell"):
                try:
                    idx = int(name.replace("spell", ""))
                except Exception:
                    idx = 1
                if not self._spell_slot_unlocked(unit, idx):
                    is_locked = True

            col = (62, 62, 74)
            if is_locked:
                col = (60, 30, 30)
            if rect.collidepoint(mouse_pos):
                col = (85, 85, 105)

            pygame.draw.rect(screen, col, rect, border_radius=7)
            pygame.draw.rect(screen, GRAY, rect, 2, border_radius=7)

            label = "LOCKED" if is_locked else name.replace("_", " ").upper()
            txt_col = (200, 100, 100) if is_locked else (155, 155, 155)
            l_surf = font_small.render(label, True, txt_col)
            screen.blit(l_surf, (rect.centerx - l_surf.get_width() // 2, rect.top - 18))

            item = unit.equipment.get(name)
            if item and getattr(item, "name", "") not in ["Fists", "No Armor"]:
                if item == self.drag_item:
                    if hasattr(item, 'draw_card_icon'):
                        item.draw_card_icon(screen, rect.x + 6, rect.y + 6, 60)
                    s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                    s.fill((0, 0, 0, 140))
                    screen.blit(s, rect)
                else:
                    if hasattr(item, 'draw_card_icon'):
                        item.draw_card_icon(screen, rect.x + 6, rect.y + 6, 60)

                    if rect.collidepoint(mouse_pos) and not self.drag_item:
                        draw_panel(screen, mouse_pos[0] + 20, mouse_pos[1], 260, 78)
                        draw_text(item.name, font_small, WHITE, screen, mouse_pos[0] + 30, mouse_pos[1] + 16)
                        # show spell tier for quick clarity
                        if str(getattr(item, "type", "")).lower() == "spell":
                            tier = int(getattr(item, "tier", 1) or 1)
                            draw_text(f"Tier {tier}", font_small, GRAY, screen, mouse_pos[0] + 30, mouse_pos[1] + 38)

        # --- RIGHT BAG ---
        pygame.draw.rect(screen, (22, 22, 28), (self.bag_x, 140, self.bag_w, self.bag_h + 50), border_radius=12)
        pygame.draw.rect(screen, (60, 60, 75), (self.bag_x, 140, self.bag_w, self.bag_h + 50), 2, border_radius=12)

        if self.active_tab == "CRAFTING":
            self._draw_crafting(screen)
        elif self.active_tab == "SKILLS":
            self._draw_skills_tab(screen, unit, mouse_pos)
        else:
            self._draw_equipment_bag(screen, mouse_pos)

        # Dragged Icon
        if self.drag_item:
            mx, my = mouse_pos
            if hasattr(self.drag_item, 'draw_card_icon'):
                self.drag_item.draw_card_icon(screen, mx - 30, my - 30, 60)

        # --- FEEDBACK MESSAGE ---
        if self.feedback_timer > 0:
            txt_surf = font_main.render(self.feedback_msg, True, (255, 50, 50))
            bg_rect = txt_surf.get_rect(center=(SCREEN_WIDTH // 2, 100))
            bg_rect.inflate_ip(20, 10)
            pygame.draw.rect(screen, (0, 0, 0), bg_rect, border_radius=5)
            pygame.draw.rect(screen, (255, 50, 50), bg_rect, 2, border_radius=5)
            screen.blit(txt_surf, txt_surf.get_rect(center=bg_rect.center))

    # -------------------------
    # TAB DRAWERS
    # -------------------------
    def _draw_skills_tab(self, screen, unit, mouse_pos):
        x = self.bag_x + 16
        y = self.bag_y + 10
        draw_text("SKILLS", font_main, WHITE, screen, x, y)
        sp = int(getattr(unit, "skill_points", 0) or 0)
        draw_text(f"Points Available: {sp}", font_main, GOLD_COLOR, screen, x, y + 30)

        self.btn_open_skill_tree.rect.topleft = (x, y + 80)
        self.btn_open_skill_tree.check_hover(mouse_pos)
        self.btn_open_skill_tree.draw(screen)

        # quick hints about magic gating (nice UX)
        slots = sum(1 for i in (1,2,3) if self._spell_slot_unlocked(unit, i))
        tier = int(getattr(unit, "max_spell_tier", 0) or 0)
        draw_text(f"Spell Slots: {slots}/3", font_small, GRAY, screen, x, y + 150)
        draw_text(f"Max Spell Tier: {tier}", font_small, GRAY, screen, x, y + 175)

    def _draw_equipment_bag(self, screen, mouse_pos):
        view = self._get_filtered_bag_view()
        start_x, start_y = self.bag_x + 10, self.bag_y + 10
        bag_cols = 6
        cell = 74

        for i in range(len(view)):
            col, row = i % bag_cols, i // bag_cols
            bx, by = start_x + col * cell, start_y + row * cell
            rect = pygame.Rect(bx, by, 68, 68)

            pygame.draw.rect(screen, (30, 30, 35), rect, border_radius=7)

            _, item = view[i]
            if item == self.drag_item:
                s = pygame.Surface((68, 68), pygame.SRCALPHA)
                s.fill((0, 0, 0, 100))
                screen.blit(s, rect)
            else:
                if hasattr(item, 'draw_card_icon'):
                    item.draw_card_icon(screen, bx + 4, by + 4, 60)
                if rect.collidepoint(mouse_pos) and not self.drag_item:
                    draw_panel(screen, mouse_pos[0] - 260, mouse_pos[1], 250, 78)
                    draw_text(item.name, font_small, WHITE, screen, mouse_pos[0] - 250, mouse_pos[1] + 16)
                    # spell tier hint
                    if str(getattr(item, "type", "")).lower() == "spell":
                        tier = int(getattr(item, "tier", 1) or 1)
                        draw_text(f"Tier {tier}", font_small, GRAY, screen, mouse_pos[0] - 250, mouse_pos[1] + 38)

    def _draw_crafting(self, screen):
        inv = getattr(self.manager, "inventory", {})
        items = sorted([(k, v) for k, v in inv.items() if v > 0], key=lambda x: x[0])
        x, y = self.bag_x + 16, self.bag_y + 10
        draw_text("MATERIALS", font_small, GRAY, screen, x, y - 20)

        y_off = y - self.craft_scroll
        for name, count in items:
            if y_off > self.bag_y - 40 and y_off < self.bag_y + self.bag_h + 40:
                draw_text(f"{name}: {count}", font_small, WHITE, screen, x, y_off)
            y_off += 25