# menus/paths_menu.py
"""Commander Paths: kykypolkujen seurantanäkymä.

Jokainen polku piirretään omana pystypuunaan: tasomerkki juuressa,
XP-palkki, ja milestone-nodet runkoa pitkin (avatut hehkuvat polun
värillä, seuraava korostettu, lukitut himmeinä). Building-polku näkyy
lukittuna kunnes House Building saapuu.
"""

from __future__ import annotations

import math

import pygame

from menus.base_menu import BaseMenu
from settings import GOLD_COLOR, GRAY, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from systems import commander_progression as prog
from ui_kit import UIButton, draw_text, font_main, font_small, font_title


class PathsMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)
        self.path_ids = list(prog.PATHS.keys())

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.next_state = "manager_menu"
            return
        if self.btn_back.is_clicked(event):
            self.next_state = "manager_menu"
            sound_system.play_sound("click")
            return

    def update(self):
        super().update()
        self.btn_back.update_hover(pygame.mouse.get_pos())

    # ------------------------------------------------------------- draw
    def draw(self, screen):
        self.draw_themed_background(screen, mood="guild")
        title = font_title.render("COMMANDER PATHS", True, GOLD_COLOR)
        self.draw_header_bar(screen, title, y=22)
        draw_text("Every craft is its own tree - it grows by DOING.",
                  font_small, (185, 180, 168), screen,
                  SCREEN_WIDTH // 2 - 190, 92)

        n = len(self.path_ids)
        col_w = min(420, (SCREEN_WIDTH - 120) // n)
        total_w = col_w * n
        start_x = (SCREEN_WIDTH - total_w) // 2
        top = 140
        bottom = SCREEN_HEIGHT - 60

        for i, path_id in enumerate(self.path_ids):
            self._draw_path(screen, prog.PATHS[path_id], path_id,
                            pygame.Rect(start_x + i * col_w + 14, top,
                                        col_w - 28, bottom - top))

        self.btn_back.check_hover(pygame.mouse.get_pos())
        self.btn_back.draw(screen)

    def _draw_path(self, screen, spec, path_id, rect):
        locked = spec.get("locked", False)
        color = spec["color"] if not locked else (95, 95, 100)
        state = prog.get_path(self.manager, path_id)
        level = state["level"] if not locked else 0

        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((18, 18, 24, 215))
        screen.blit(panel, rect.topleft)
        pygame.draw.rect(screen, color, rect, 2, border_radius=12)

        # Otsikko + tasoympyrä
        draw_text(spec["name"], font_main, color, screen,
                  rect.x + 18, rect.y + 14)
        badge_c = (rect.x + 40, rect.y + 84)
        pygame.draw.circle(screen, (26, 26, 32), badge_c, 26)
        pygame.draw.circle(screen, color, badge_c, 26, 3)
        lvl_txt = font_title.render(str(level) if not locked else "-",
                                    True, WHITE)
        screen.blit(lvl_txt, lvl_txt.get_rect(center=badge_c))
        draw_text(f"/ {prog.MAX_LEVEL}", font_small, GRAY, screen,
                  badge_c[0] + 32, badge_c[1] - 8)

        # XP-palkki
        bar = pygame.Rect(rect.x + 18, rect.y + 122, rect.w - 36, 12)
        pygame.draw.rect(screen, (30, 30, 36), bar, border_radius=5)
        if locked:
            draw_text("Locked - coming with House Building", font_small,
                      GRAY, screen, bar.x, bar.y + 20)
        elif level >= prog.MAX_LEVEL:
            pygame.draw.rect(screen, color, bar, border_radius=5)
            draw_text("MASTERED", font_small, color, screen, bar.x, bar.y + 20)
        else:
            need = prog.xp_needed(path_id, level)
            fill = int(bar.w * min(1.0, state["xp"] / max(1, need)))
            pygame.draw.rect(screen, color,
                             (bar.x, bar.y, fill, bar.h), border_radius=5)
            draw_text(f"{state['xp']} / {need} XP", font_small,
                      (200, 200, 205), screen, bar.x, bar.y + 20)

        # Puun runko + milestone-nodet
        trunk_x = rect.x + 40
        trunk_top = rect.y + 190
        trunk_bottom = rect.bottom - 30
        pygame.draw.line(screen, (70, 66, 58), (trunk_x, trunk_top),
                         (trunk_x, trunk_bottom), 4)

        milestones = spec["milestones"]
        span = trunk_bottom - trunk_top
        next_found = False
        t = pygame.time.get_ticks() * 0.004
        for mi, (mlvl, _pid, name, desc, _fx) in enumerate(milestones):
            y = trunk_bottom - int(span * (mi + 1) / (len(milestones) + 0.4))
            unlocked = (not locked) and level >= mlvl
            is_next = (not locked) and not unlocked and not next_found
            if is_next:
                next_found = True

            if unlocked:
                glow = 5 + int(math.sin(t + mi) * 2)
                pygame.draw.circle(screen, color, (trunk_x, y), 9 + glow, 1)
                pygame.draw.circle(screen, color, (trunk_x, y), 8)
                pygame.draw.circle(screen, WHITE, (trunk_x, y), 3)
                name_col, desc_col = WHITE, (185, 185, 190)
            elif is_next:
                pygame.draw.circle(screen, (40, 40, 46), (trunk_x, y), 8)
                pygame.draw.circle(screen, color, (trunk_x, y), 8, 2)
                name_col, desc_col = color, (160, 160, 166)
            else:
                pygame.draw.circle(screen, (36, 36, 42), (trunk_x, y), 7)
                pygame.draw.circle(screen, (75, 75, 82), (trunk_x, y), 7, 1)
                name_col, desc_col = (120, 120, 128), (95, 95, 102)

            draw_text(f"{mlvl}  {name}", font_small, name_col, screen,
                      trunk_x + 22, y - 14)
            draw_text(desc[:38], font_small, desc_col, screen,
                      trunk_x + 22, y + 2)
