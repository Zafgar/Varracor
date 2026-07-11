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
        self.btn_back = UIButton(cx - 100, SCREEN_HEIGHT - 90, 200, 55, "LEAVE", None, GRAY)
        self.row_buttons = []  # (rect, action, task_id)
        self.feedback = ""
        self.feedback_timer = 0

    def _flash(self, msg):
        self.feedback = msg
        self.feedback_timer = 180

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.next_state = "muckford_city"
            return
        if self.btn_back.is_clicked(event):
            self.next_state = "muckford_city"
            sound_system.play_sound('click')
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

    def draw(self, screen):
        self.draw_themed_background(screen, "quest")
        title = font_title.render("NOTICE BOARD", True, GOLD_COLOR)
        self.draw_header_bar(screen, title)

        vt = self.manager.village_tasks
        rep = self.manager.reputation
        draw_text(f"Reputation: {rep}   (higher fame unlocks more work)",
                  font_small, GRAY, screen, 60, 120)

        self.row_buttons = []
        if not vt:
            draw_text("The board is empty.", font_main, GRAY, screen, 80, 200)
            self.btn_back.draw(screen)
            return

        y = 170
        # Aktiiviset / lunastettavat ensin
        active = vt.active_tasks()
        available = vt.available_for(rep)

        if active:
            draw_text("YOUR TASKS", font_main, WHITE, screen, 60, y); y += 40
            for t in active:
                y = self._draw_task_row(screen, t, y, active=True)
            y += 10

        draw_text("AVAILABLE", font_main, WHITE, screen, 60, y); y += 40
        if not available:
            draw_text("Nothing new right now. Come back when you're better known.",
                      font_small, GRAY, screen, 80, y); y += 40
        for t in available:
            y = self._draw_task_row(screen, t, y, active=False)

        # Urotekojen muisti
        deeds = self.manager.get_deeds() if hasattr(self.manager, "get_deeds") else []
        if deeds:
            y = max(y, SCREEN_HEIGHT - 220)
            draw_text("THE VILLAGE REMEMBERS", font_small, (150, 220, 255), screen, 60, y)
            y += 26
            for d in deeds[-3:]:
                draw_text(f"- You {d['text']}.", font_small, (170, 190, 210), screen, 80, y)
                y += 22

        if self.feedback_timer > 0:
            draw_text(self.feedback, font_main, GOLD_COLOR, screen,
                      60, SCREEN_HEIGHT - 130)
        self.btn_back.draw(screen)

    def _draw_task_row(self, screen, task, y, active):
        panel = pygame.Rect(60, y, SCREEN_WIDTH - 120, 66)
        self.draw_soft_panel(screen, panel)
        draw_text(task.title, font_main, GOLD_COLOR, screen, 80, y + 8)
        draw_text(task.summary, font_small, (200, 200, 200), screen, 80, y + 36)

        # Toimintonappi oikealla
        btn_rect = pygame.Rect(SCREEN_WIDTH - 260, y + 14, 170, 40)
        if active and task.status == "ready_turnin":
            self._button(screen, btn_rect, "TURN IN", (70, 170, 90))
            self.row_buttons.append((btn_rect, "turnin", task.id))
        elif active:
            # Näytä nykyinen vaihe vihjeenä
            st = task.current_stage
            hint = (st.get("hint") if st else "") or "In progress"
            draw_text(hint, font_small, (255, 220, 120), screen,
                      SCREEN_WIDTH - 400, y + 24)
        else:
            self._button(screen, btn_rect, "ACCEPT", (90, 140, 200))
            self.row_buttons.append((btn_rect, "accept", task.id))
        return y + 78

    def _button(self, screen, rect, label, color):
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, rect, 2, border_radius=8)
        surf = font_small.render(label, True, WHITE)
        screen.blit(surf, (rect.centerx - surf.get_width() // 2,
                           rect.centery - surf.get_height() // 2))
