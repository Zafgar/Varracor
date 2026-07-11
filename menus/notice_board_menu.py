# menus/notice_board_menu.py
import pygame
from menus.base_menu import BaseMenu
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRAY, GOLD_COLOR, GREEN
from ui_kit import draw_text, font_title, font_main, font_small, UIButton
from sound_manager import sound_system


class NoticeBoardMenu(BaseMenu):
    """
    Kylän ilmoitustaulu: tarjolla olevat tehtävät (maineen mukaan),
    aktiiviset ja lunastettavat. Pelaaja hyväksyy ja lunastaa tehtäviä.
    Palauttaa muckford_cityyn.
    """

    def __init__(self, manager):
        super().__init__(manager)
        cx = SCREEN_WIDTH // 2
        self.btn_back = UIButton(cx - 100, SCREEN_HEIGHT - 90, 200, 55,
                                 "LEAVE", None, GRAY)
        self.row_buttons = []  # (rect, action, task_id)
        self.feedback = ""
        self.feedback_timer = 0
        self.scroll_y = 0
        self.content_height = 0
        self.viewport = pygame.Rect(45, 155, SCREEN_WIDTH - 90,
                                    SCREEN_HEIGHT - 275)

    def _flash(self, msg):
        self.feedback = msg
        self.feedback_timer = 180

    def _max_scroll(self):
        return max(0, int(self.content_height - self.viewport.h))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.next_state = "muckford_city"
            return
        if self.btn_back.is_clicked(event):
            self.next_state = "muckford_city"
            sound_system.play_sound('click')
            return
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y = max(
                0,
                min(self._max_scroll(), self.scroll_y - event.y * 48),
            )
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, action, tid in self.row_buttons:
                if rect.collidepoint(event.pos):
                    self._do(action, tid)
                    return

    def _do(self, action, task_id):
        vt = self.manager.village_tasks
        if not vt:
            return
        if action == "accept":
            if vt.accept(task_id):
                t = vt.get(task_id)
                self._flash(f"Accepted: {t.title}")
                sound_system.play_sound('click')
        elif action == "turnin":
            gained = vt.complete(self.manager, task_id)
            if gained:
                self._flash("Reward: " + ", ".join(gained))
                sound_system.play_sound('coin')

    def update(self):
        super().update()
        if self.feedback_timer > 0:
            self.feedback_timer -= 1
        self.scroll_y = max(0, min(self.scroll_y, self._max_scroll()))

    def draw(self, screen):
        self.draw_themed_background(screen, "quest")
        title = font_title.render("NOTICE BOARD", True, GOLD_COLOR)
        self.draw_header_bar(screen, title)

        vt = self.manager.village_tasks
        rep = self.manager.reputation
        draw_text(f"Reputation: {rep}   (higher fame unlocks more work)",
                  font_small, GRAY, screen, 60, 120)
        draw_text("Mouse wheel scrolls contracts", font_small, GRAY,
                  screen, SCREEN_WIDTH - 330, 120)

        self.row_buttons = []
        if not vt:
            draw_text("The board is empty.", font_main, GRAY, screen, 80, 200)
            self.btn_back.draw(screen)
            return

        active = vt.active_tasks()
        available = vt.available_for(rep)
        deeds = self.manager.get_deeds() if hasattr(self.manager, "get_deeds") else []

        # Draw all board content to a transparent scrolling surface. This keeps
        # eleven-plus material contracts usable at high reputation.
        estimated = 120 + (len(active) + len(available)) * 110
        if deeds:
            estimated += 115
        self.content_height = max(self.viewport.h, estimated)
        board = pygame.Surface((self.viewport.w, self.content_height),
                               pygame.SRCALPHA)
        board.fill((0, 0, 0, 0))

        y = 5
        if active:
            draw_text("YOUR TASKS", font_main, WHITE, board, 15, y)
            y += 38
            for task in active:
                y = self._draw_task_row(board, task, y, active=True,
                                        screen_offset=self.viewport.topleft)
            y += 8

        draw_text("AVAILABLE", font_main, WHITE, board, 15, y)
        y += 38
        if not available:
            draw_text("Nothing new right now. Come back when you're better known.",
                      font_small, GRAY, board, 35, y)
            y += 45
        for task in available:
            y = self._draw_task_row(board, task, y, active=False,
                                    screen_offset=self.viewport.topleft)

        if deeds:
            y += 8
            draw_text("THE VILLAGE REMEMBERS", font_small, (150, 220, 255),
                      board, 15, y)
            y += 26
            for deed in deeds[-3:]:
                draw_text(f"- You {deed['text']}.", font_small,
                          (170, 190, 210), board, 35, y)
                y += 22

        self.content_height = max(self.viewport.h, y + 20)
        self.scroll_y = max(0, min(self.scroll_y, self._max_scroll()))

        old_clip = screen.get_clip()
        screen.set_clip(self.viewport)
        screen.blit(board, self.viewport.topleft,
                    area=pygame.Rect(0, self.scroll_y,
                                     self.viewport.w, self.viewport.h))
        screen.set_clip(old_clip)

        # Convert board-local hit rectangles to their currently visible screen
        # positions after the content has been drawn.
        visible_buttons = []
        for rect, action, task_id in self.row_buttons:
            screen_rect = rect.move(self.viewport.x,
                                    self.viewport.y - self.scroll_y)
            if self.viewport.contains(screen_rect):
                visible_buttons.append((screen_rect, action, task_id))
        self.row_buttons = visible_buttons

        if self._max_scroll() > 0:
            track = pygame.Rect(self.viewport.right - 7, self.viewport.y,
                                5, self.viewport.h)
            pygame.draw.rect(screen, (45, 43, 40), track, border_radius=3)
            thumb_h = max(35, int(track.h * self.viewport.h /
                                  max(self.viewport.h, self.content_height)))
            travel = track.h - thumb_h
            thumb_y = track.y + int(travel * self.scroll_y /
                                    max(1, self._max_scroll()))
            pygame.draw.rect(screen, (145, 125, 85),
                             (track.x, thumb_y, track.w, thumb_h),
                             border_radius=3)

        if self.feedback_timer > 0:
            draw_text(self.feedback, font_main, GOLD_COLOR, screen,
                      60, SCREEN_HEIGHT - 130)
        self.btn_back.draw(screen)

    def _material_tag(self, task):
        level = getattr(task, "recommended_level", None)
        family = getattr(task, "material_family", None)
        parts = []
        if level:
            low, high = level
            parts.append(f"Lv {low}+" if high is None else f"Lv {low}-{high}")
        if family:
            short = {
                "Metals, Ores & Smithing": "METAL",
                "Woods, Fibers & Bindings": "FIBER",
                "Hides, Bones & Monster Parts": "MONSTER",
                "Herbs, Alchemy & Potions": "ALCHEMY",
                "Magic, Runes & Trinkets": "ARCANE",
                "Scrolls & Spell Components": "SCRIPT",
            }.get(family, family.upper())
            parts.append(short)
        return "  |  ".join(parts)

    def _draw_task_row(self, surface, task, y, active, screen_offset):
        panel = pygame.Rect(15, y, self.viewport.w - 30, 94)
        self.draw_soft_panel(surface, panel)
        draw_text(task.title, font_main, GOLD_COLOR, surface,
                  panel.x + 18, panel.y + 8)

        tag = self._material_tag(task)
        if tag:
            draw_text(tag, font_small, (145, 205, 175), surface,
                      panel.x + 18, panel.y + 35)
            summary_y = panel.y + 59
        else:
            summary_y = panel.y + 42
        draw_text(task.summary, font_small, (200, 200, 200), surface,
                  panel.x + 18, summary_y)

        btn_rect = pygame.Rect(panel.right - 195, panel.y + 18, 170, 40)
        if active and task.status == "ready_turnin":
            self._button(surface, btn_rect, "TURN IN", (70, 170, 90))
            self.row_buttons.append((btn_rect, "turnin", task.id))
        elif active:
            stage = task.current_stage
            hint = (stage.get("hint") if stage else "") or "In progress"
            draw_text(hint, font_small, (255, 220, 120), surface,
                      panel.right - 410, panel.y + 66)
        else:
            self._button(surface, btn_rect, "ACCEPT", (90, 140, 200))
            self.row_buttons.append((btn_rect, "accept", task.id))
        return y + 106

    def _button(self, screen, rect, label, color):
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, rect, 2, border_radius=8)
        surf = font_small.render(label, True, WHITE)
        screen.blit(surf, (rect.centerx - surf.get_width() // 2,
                           rect.centery - surf.get_height() // 2))
