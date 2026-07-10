# menus/options_menu.py
import pygame
from menus.base_menu import BaseMenu
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRAY, GOLD_COLOR
from ui_kit import draw_text, font_main, font_title, font_small, UIButton
from sound_manager import sound_system


class Slider:
    """Yksinkertainen vaakasuora liukusäädin (0.0 - 1.0)."""

    def __init__(self, x, y, w, label, value=1.0):
        self.rect = pygame.Rect(x, y, w, 12)
        self.label = label
        self.value = max(0.0, min(1.0, value))
        self.dragging = False

    @property
    def handle_x(self):
        return self.rect.x + int(self.value * self.rect.w)

    def handle_event(self, event):
        """Palauttaa True jos arvo muuttui."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            grab = self.rect.inflate(20, 28)
            if grab.collidepoint(event.pos):
                self.dragging = True
                return self._set_from_mouse(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was = self.dragging
            self.dragging = False
            return False if not was else None  # None = drag paattyi
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            return self._set_from_mouse(event.pos[0])
        return False

    def _set_from_mouse(self, mx):
        new = max(0.0, min(1.0, (mx - self.rect.x) / self.rect.w))
        changed = abs(new - self.value) > 0.001
        self.value = new
        return changed

    def draw(self, screen):
        # Label + prosentti
        draw_text(self.label, font_main, WHITE, screen, self.rect.x, self.rect.y - 34)
        pct = f"{int(self.value * 100)}%"
        draw_text(pct, font_main, GOLD_COLOR, screen, self.rect.right + 20, self.rect.y - 8)

        # Ura
        pygame.draw.rect(screen, (40, 40, 50), self.rect, border_radius=6)
        # Täyttö
        fill = pygame.Rect(self.rect.x, self.rect.y, int(self.value * self.rect.w), self.rect.h)
        pygame.draw.rect(screen, (180, 150, 80), fill, border_radius=6)
        pygame.draw.rect(screen, (120, 120, 140), self.rect, 2, border_radius=6)
        # Kahva
        pygame.draw.circle(screen, (230, 210, 150), (self.handle_x, self.rect.centery), 12)
        pygame.draw.circle(screen, (90, 80, 50), (self.handle_x, self.rect.centery), 12, 2)


class OptionsMenu(BaseMenu):
    """Asetukset: musiikin ja efektien äänenvoimakkuus. Palaa tilaan,
    josta tultiin (manager.options_return_state)."""

    def __init__(self, manager):
        super().__init__(manager)
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        slider_w = 400
        self.music_slider = Slider(cx - slider_w // 2, cy - 80, slider_w,
                                   "MUSIC VOLUME", sound_system.music_volume)
        self.sfx_slider = Slider(cx - slider_w // 2, cy + 40, slider_w,
                                 "SOUND EFFECTS", sound_system.sfx_volume)

        self.btn_back = UIButton(cx - 100, cy + 160, 200, 55, "BACK", None, GRAY)
        self._sfx_preview_cd = 0

    def _return_state(self):
        return getattr(self.manager, "options_return_state", None) or "menu"

    def _close(self):
        sound_system.save_options()
        sound_system.play_sound("click")
        self.next_state = self._return_state()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._close()
            return

        changed = self.music_slider.handle_event(event)
        if changed:
            sound_system.set_music_volume(self.music_slider.value)

        result = self.sfx_slider.handle_event(event)
        if result:
            sound_system.set_sfx_volume(self.sfx_slider.value)
        if result is None:  # drag päättyi -> ääninäyte uudella tasolla
            sound_system.play_sound("click")

        if self.btn_back.is_clicked(event):
            self._close()

    def update(self):
        super().update()

    def draw(self, screen):
        self.draw_themed_background(screen, "guild")

        title = font_title.render("OPTIONS", True, GOLD_COLOR)
        self.draw_header_bar(screen, title)

        panel = pygame.Rect(SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 - 200, 600, 460)
        self.draw_soft_panel(screen, panel)

        self.music_slider.draw(screen)
        self.sfx_slider.draw(screen)

        self.btn_back.draw(screen)
        draw_text("ESC palaa takaisin", font_small, GRAY, screen,
                  SCREEN_WIDTH // 2 - 60, panel.bottom - 40)
