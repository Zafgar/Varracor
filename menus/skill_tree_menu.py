import pygame
import math
from settings import *
from ui_kit import UIButton, draw_text, font_title, font_main, font_small, draw_panel
from menus.base_menu import BaseMenu
from sound_manager import sound_system
from skills.skills_data import SKILL_TREE as SKILLS
from skills.skill_system import can_unlock, unlock_skill


class SkillTreeMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)

        self.btn_back = UIButton(30, 30, 140, 52, "BACK", None, GRAY)

        self.target_unit = None

        # --- CAMERA ---
        # cam_x/cam_y = ruudun koordinaatit world-origolle (0,0)
        self.cam_x = SCREEN_WIDTH // 2
        self.cam_y = SCREEN_HEIGHT // 2

        # zoom
        self.zoom = 1.0
        self.ZOOM_MIN = 0.60
        self.ZOOM_MAX = 1.50

        # dragging
        self.is_dragging = False
        self.drag_start = (0, 0)
        self.drag_total = 0.0
        self.last_mouse_pos = (0, 0)

        # click vs drag reliability
        self.mouse_down_node = None
        self.mouse_down_pos = (0, 0)

        # node visuals
        self.NODE_R = 28
        self.NODE_R_HOVER = 33

        # tooltip
        self._last_hover_id = None

        # precompute bounds (updated if SKILLS changes)
        self._bounds_dirty = True
        self._world_bounds = (-200, 200, -200, 200)  # minx,maxx,miny,maxy

    # -------------------------
    # lifecycle
    # -------------------------
    def set_unit(self, unit):
        self.target_unit = unit
        self.zoom = 1.0
        self._bounds_dirty = True
        
        # Calculate center of the tree content
        self._rebuild_bounds()
        minx, maxx, miny, maxy = self._world_bounds
        cx = (minx + maxx) / 2
        cy = (miny + maxy) / 2

        # Center world(cx, cy) at screen center
        self.cam_x = (SCREEN_WIDTH // 2) - cx
        self.cam_y = (SCREEN_HEIGHT // 2) - cy

    # -------------------------
    # world/screen transforms
    # -------------------------
    def _world_to_screen(self, wx, wy):
        sx = self.cam_x + wx * self.zoom
        sy = self.cam_y + wy * self.zoom
        return int(sx), int(sy)

    def _screen_to_world(self, sx, sy):
        wx = (sx - self.cam_x) / self.zoom
        wy = (sy - self.cam_y) / self.zoom
        return wx, wy

    # -------------------------
    # bounds & clamping
    # -------------------------
    def _rebuild_bounds(self):
        if not SKILLS:
            self._world_bounds = (-200, 200, -200, 200)
            self._bounds_dirty = False
            return

        xs, ys = [], []
        for _, data in SKILLS.items():
            px, py = data.get("pos", (0, 0))
            xs.append(px)
            ys.append(py)

        minx = min(xs) - 140
        maxx = max(xs) + 140
        miny = min(ys) - 140
        maxy = max(ys) + 140
        self._world_bounds = (minx, maxx, miny, maxy)
        self._bounds_dirty = False

    def _clamp_camera(self):
        if self._bounds_dirty:
            self._rebuild_bounds()

        minx, maxx, miny, maxy = self._world_bounds

        # Pidä puu "järkevästi lähellä" ruutua
        margin = 160

        # sx = cam_x + wx*zoom
        # halutaan: (cam_x + maxx*zoom) >= margin  AND (cam_x + minx*zoom) <= W - margin
        min_cam_x = margin - (maxx * self.zoom)
        max_cam_x = (SCREEN_WIDTH - margin) - (minx * self.zoom)

        min_cam_y = margin - (maxy * self.zoom)
        max_cam_y = (SCREEN_HEIGHT - margin) - (miny * self.zoom)

        self.cam_x = max(min_cam_x, min(max_cam_x, self.cam_x))
        self.cam_y = max(min_cam_y, min(max_cam_y, self.cam_y))

    # -------------------------
    # hit testing
    # -------------------------
    def _pick_node(self, mouse_pos):
        if not self.target_unit:
            return None

        mx, my = mouse_pos
        best_id = None
        best_d2 = 10**18

        for s_id, data in SKILLS.items():
            px, py = data.get("pos", (0, 0))
            cx, cy = self._world_to_screen(px, py)

            r = int(self.NODE_R * self.zoom)
            r = max(16, min(42, r))

            dx = mx - cx
            dy = my - cy
            d2 = dx * dx + dy * dy
            if d2 <= (r * r) and d2 < best_d2:
                best_d2 = d2
                best_id = s_id

        return best_id

    # -------------------------
    # colors
    # -------------------------
    def get_branch_color(self, s_id):
        s = (s_id or "").lower()

        # STR (Left)
        if any(x in s for x in ["str", "barb", "knight", "titan", "juggernaut", "fighter", "berserker"]):
            return (220, 80, 80)

        # DEX (Right)
        if any(x in s for x in ["dex", "sin", "snip", "duel", "eagle", "shadow", "rogue", "ranger"]):
            return (80, 220, 80)

        # INT (Top)
        if any(x in s for x in ["int", "pyro", "cler", "bmage", "spell", "relic", "arcane"]):
            return (80, 80, 240)

        # WEAPONS/PROF (Bottom)
        if any(x in s for x in ["weapon", "prof_", "sword", "axe", "bow", "crossbow", "dagger", "staff", "shield", "armor"]):
            return (200, 180, 50)

        return (180, 180, 180)

    # -------------------------
    # input
    # -------------------------
    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()

        # back
        if self.btn_back.is_clicked(event):
            self.next_state = "guild"
            if hasattr(self.manager, "skill_tree_return_state"):
                self.next_state = self.manager.skill_tree_return_state
            sound_system.play_sound("click")
            return

        # zoom with wheel (pygame.MOUSEWHEEL) or old buttons 4/5
        if event.type == pygame.MOUSEWHEEL:
            self._handle_zoom(event.y, mouse_pos)
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in (4, 5):
                dy = 1 if event.button == 4 else -1
                self._handle_zoom(dy, mouse_pos)
                return

        # right click = recenter
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self.cam_x = SCREEN_WIDTH // 2
            self.cam_y = SCREEN_HEIGHT // 2 - 120
            self._clamp_camera()
            sound_system.play_sound("click")
            return

        # dragging / click (LMB)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_back.rect.collidepoint(mouse_pos):
                return

            # Always reset drag_total on new click (fixes "must spam click" bug)
            self.drag_total = 0.0
            self.drag_start = mouse_pos
            self.last_mouse_pos = mouse_pos

            hit = self._pick_node(mouse_pos)
            if hit is not None:
                # Candidate click on node (confirmed on MOUSEBUTTONUP if no drag)
                self.mouse_down_node = hit
                self.mouse_down_pos = mouse_pos
                self.is_dragging = False
                return

            # Clicked empty space => start panning
            self.mouse_down_node = None
            self.is_dragging = True
            self.drag_start = mouse_pos
            self.last_mouse_pos = mouse_pos
            return

        # mouse move
        if event.type == pygame.MOUSEMOTION:
            # If we pressed on a node but start moving, treat as panning instead of "failed click"
            if (not self.is_dragging) and self.mouse_down_node is not None:
                dx0 = mouse_pos[0] - self.mouse_down_pos[0]
                dy0 = mouse_pos[1] - self.mouse_down_pos[1]
                if abs(dx0) + abs(dy0) > 6.0:
                    self.is_dragging = True
                    self.mouse_down_node = None
                    self.last_mouse_pos = self.mouse_down_pos

            if self.is_dragging:
                mx, my = mouse_pos
                lx, ly = self.last_mouse_pos
                dx = mx - lx
                dy = my - ly

                self.cam_x += dx
                self.cam_y += dy
                self._clamp_camera()

                self.drag_total += abs(dx) + abs(dy)
                self.last_mouse_pos = mouse_pos
                return

        # mouse up
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_drag = self.drag_total > 6.0
            self.is_dragging = False

            # confirm click unlock only if it was not a drag
            if (not was_drag) and self.target_unit and self.mouse_down_node:
                hit_id = self._pick_node(mouse_pos)
                if hit_id == self.mouse_down_node:
                    ok, msg = unlock_skill(self.target_unit, hit_id)
                    if ok:
                        # --- FIX: RECALCULATE STATS IMMEDIATELY ---
                        if hasattr(self.target_unit, "calculate_final_stats"):
                            self.target_unit.calculate_final_stats()
                        
                        sound_system.play_sound("recruit")
                        print(f"Unlocked {SKILLS[hit_id].get('name','Skill')}!")
                    else:
                        sound_system.play_sound("error")
                        print(f"Cannot unlock: {msg}")

            self.mouse_down_node = None
            self.drag_total = 0.0
            return

    def _handle_zoom(self, wheel_y, mouse_pos):
        if not self.target_unit:
            return

        old_zoom = self.zoom
        step = 0.08
        new_zoom = self.zoom + (step * wheel_y)
        new_zoom = max(self.ZOOM_MIN, min(self.ZOOM_MAX, new_zoom))
        if abs(new_zoom - old_zoom) < 0.0001:
            return

        # keep world point under cursor fixed
        mx, my = mouse_pos
        wx, wy = self._screen_to_world(mx, my)

        self.zoom = new_zoom
        self.cam_x = mx - wx * self.zoom
        self.cam_y = my - wy * self.zoom

        self._clamp_camera()

    # -------------------------
    # draw
    # -------------------------
    def draw(self, screen):
        screen.fill((15, 20, 25))

        # background grid (scaled)
        self._draw_grid(screen)

        if not self.target_unit:
            draw_text("No unit selected.", font_title, RED, screen, 400, 300)
            self.btn_back.check_hover(pygame.mouse.get_pos())
            self.btn_back.draw(screen)
            return

        if self._bounds_dirty:
            self._rebuild_bounds()
        self._clamp_camera()

        mouse_pos = pygame.mouse.get_pos()
        hovered_id = self._pick_node(mouse_pos)

        # 1) connections
        self._draw_connections(screen)

        # 2) nodes
        self._draw_nodes(screen, hovered_id)

        # 3) UI overlay
        self._draw_ui(screen, mouse_pos)

        # 4) tooltip
        if hovered_id:
            self._draw_tooltip(screen, hovered_id, mouse_pos)

    def _draw_grid(self, screen):
        # grid respects zoom a bit (not perfect but looks good)
        step_world = 100
        step = int(step_world * self.zoom)
        step = max(40, min(140, step))

        off_x = int(self.cam_x) % step
        off_y = int(self.cam_y) % step

        for x in range(off_x, SCREEN_WIDTH, step):
            pygame.draw.line(screen, (30, 35, 40), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(off_y, SCREEN_HEIGHT, step):
            pygame.draw.line(screen, (30, 35, 40), (0, y), (SCREEN_WIDTH, y))

    def _draw_connections(self, screen):
        unlocked_set = getattr(self.target_unit, "unlocked_skills", set())

        for s_id, data in SKILLS.items():
            px, py = data.get("pos", (0, 0))
            start = self._world_to_screen(px, py)

            requires_list = data.get("requires", [])
            branch_col = self.get_branch_color(s_id)

            for p_id in requires_list:
                if p_id not in SKILLS:
                    continue
                ppos = SKILLS[p_id].get("pos", (0, 0))
                end = self._world_to_screen(ppos[0], ppos[1])

                # default
                line_col = (60, 60, 60)
                width = max(2, int(2 * self.zoom))

                # if requires unlocked -> brighter
                if p_id in unlocked_set:
                    line_col = (branch_col[0] // 2, branch_col[1] // 2, branch_col[2] // 2)
                    width = max(3, int(3 * self.zoom))

                # if both unlocked -> gold
                if (p_id in unlocked_set) and (s_id in unlocked_set):
                    line_col = (255, 215, 0)
                    width = max(4, int(4 * self.zoom))

                pygame.draw.line(screen, line_col, start, end, width)

    def _draw_nodes(self, screen, hovered_id):
        unlocked_set = getattr(self.target_unit, "unlocked_skills", set())
        sp = int(getattr(self.target_unit, "skill_points", 0) or 0)

        for s_id, data in SKILLS.items():
            px, py = data.get("pos", (0, 0))
            cx, cy = self._world_to_screen(px, py)

            base_r = int(self.NODE_R * self.zoom)
            base_r = max(18, min(44, base_r))
            r = base_r

            is_unlocked = s_id in unlocked_set
            can_buy, reason = can_unlock(self.target_unit, s_id)

            if is_unlocked:
                fill = (255, 215, 0)
                border = (255, 255, 220)
                text_col = (20, 20, 20)
            elif can_buy:
                fill = self.get_branch_color(s_id)
                border = (200, 200, 200)
                text_col = WHITE
            else:
                fill = (40, 40, 40)
                border = (70, 70, 70)
                text_col = (120, 120, 120)

            if hovered_id == s_id:
                r = int(self.NODE_R_HOVER * self.zoom)
                r = max(r, base_r + 4)
                border = (255, 255, 255)

            pygame.draw.circle(screen, fill, (cx, cy), r)
            pygame.draw.circle(screen, border, (cx, cy), r, max(2, int(3 * self.zoom)))

            # short label
            name = data.get("name", "??")
            short = name[:2].upper()
            if "Proficiency" in name or s_id.startswith("prof_"):
                short = "WP"
            if "Spell Slot" in name or "Spell" in name and "Slot" in name:
                short = "SP"

            txt = font_small.render(short, True, text_col)
            screen.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))

    def _draw_ui(self, screen, mouse_pos):
        # top bar
        pygame.draw.rect(screen, (20, 20, 20), (0, 0, SCREEN_WIDTH, 110))
        pygame.draw.line(screen, (50, 50, 50), (0, 110), (SCREEN_WIDTH, 110))

        draw_text(
            f"SKILL TREE: {self.target_unit.name} (Lvl {getattr(self.target_unit,'level',1)})",
            font_title, WHITE, screen, 260, 22
        )

        pts = int(getattr(self.target_unit, "skill_points", 0) or 0)
        draw_text(
            f"Skill Points: {pts}",
            font_main, GOLD_COLOR if pts > 0 else GRAY, screen, 260, 70
        )

        # hints
        draw_text("LMB: unlock | Drag: pan | Wheel: zoom | RMB: recenter",
                  font_small, GRAY, screen, SCREEN_WIDTH - 520, 75)

        # branch legend (small)
        lx, ly = 30, 120
        legend = [
            ("STR", (220, 80, 80)),
            ("DEX", (80, 220, 80)),
            ("INT", (80, 80, 240)),
            ("PROF", (200, 180, 50)),
        ]
        for i, (t, c) in enumerate(legend):
            pygame.draw.rect(screen, c, (lx, ly + i * 22, 14, 14), border_radius=3)
            draw_text(t, font_small, (220, 220, 220), screen, lx + 22, ly - 2 + i * 22)

        # back
        self.btn_back.check_hover(mouse_pos)
        self.btn_back.draw(screen)

    # -------------------------
    # tooltip
    # -------------------------
    def _wrap(self, text, max_chars=44):
        if not text:
            return []
        words = str(text).split()
        lines = []
        cur = ""
        for w in words:
            if len(cur) + len(w) + 1 > max_chars:
                if cur:
                    lines.append(cur.rstrip())
                cur = w + " "
            else:
                cur += w + " "
        if cur.strip():
            lines.append(cur.rstrip())
        return lines

    def _draw_tooltip(self, screen, s_id, pos):
        data = SKILLS.get(s_id, {})
        if not data:
            return

        mx, my = pos
        x, y = mx + 25, my + 25
        w, h = 420, 210

        if x + w > SCREEN_WIDTH:
            x -= (w + 50)
        if y + h > SCREEN_HEIGHT:
            y -= (h + 50)

        # background panel
        draw_panel(screen, x, y, w, h, (30, 30, 40))

        name = data.get("name", s_id)
        desc = data.get("desc", "")

        unlocked_set = getattr(self.target_unit, "unlocked_skills", set())
        is_unlocked = s_id in unlocked_set
        can_buy, reason = can_unlock(self.target_unit, s_id)

        cost = int(data.get("cost", 1))
        min_lvl = int(data.get("min_level", 1))
        sp = int(getattr(self.target_unit, "skill_points", 0) or 0)
        lvl = int(getattr(self.target_unit, "level", 1) or 1)

        # title
        draw_text(name, font_main, GOLD_COLOR if is_unlocked else WHITE, screen, x + 12, y + 10)

        # status line
        status = "UNLOCKED" if is_unlocked else ("AVAILABLE" if can_buy else "LOCKED")
        col = (100, 255, 100) if is_unlocked else ((255, 215, 0) if can_buy else (255, 90, 90))
        draw_text(status, font_small, col, screen, x + w - 110, y + 14)

        # cost / level
        cost_col = WHITE if sp >= cost else (255, 90, 90)
        lvl_col = WHITE if lvl >= min_lvl else (255, 90, 90)
        draw_text(f"Cost: {cost} SP", font_small, cost_col, screen, x + 12, y + 38)
        draw_text(f"Req Lvl: {min_lvl}", font_small, lvl_col, screen, x + 140, y + 38)

        # requires_list
        requires_list = data.get("requires", [])
        if requires_list:
            pr_names = []
            for pid in requires_list:
                pd = SKILLS.get(pid, {})
                pr_names.append(pd.get("name", pid))
            pr_line = "Prereq: " + ", ".join(pr_names)
            pr_lines = self._wrap(pr_line, 50)
            yy = y + 58
            for line in pr_lines[:2]:
                draw_text(line, font_small, (190, 190, 190), screen, x + 12, yy)
                yy += 18
        else:
            yy = y + 58

        # desc
        yy += 6
        for line in self._wrap(desc, 50)[:4]:
            draw_text(line, font_small, (220, 220, 220), screen, x + 12, yy)
            yy += 18

        # effects
        eff = data.get("effects", {})
        if eff:
            # pretty print a few key effects
            parts = []
            for k, v in eff.items():
                parts.append(f"{k}: {v}")
            eff_text = "Effects: " + " | ".join(parts)
            for line in self._wrap(eff_text, 50)[:3]:
                draw_text(line, font_small, (120, 255, 120), screen, x + 12, yy)
                yy += 18

        # lock reason (if any)
        if (not is_unlocked) and (not can_buy) and reason:
            yy += 4
            for line in self._wrap(f"Locked: {reason}", 50)[:2]:
                draw_text(line, font_small, (255, 120, 120), screen, x + 12, yy)
                yy += 18