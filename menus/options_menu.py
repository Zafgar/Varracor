# menus/options_menu.py
import pygame
from menus.base_menu import BaseMenu
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRAY, GOLD_COLOR
from ui_kit import (draw_text, font_main, font_title, font_small, UIButton,
                    COLOR_TRIM)
from sound_manager import sound_system
from systems import keybinds
from systems import display_settings


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
    """Asetukset: äänenvoimakkuudet + näppäinasettelu (CONTROLS).
    Näppäimen voi sitoa uudelleen klikkaamalla riviä ja painamalla uutta
    näppäintä. Palaa tilaan, josta tultiin (manager.options_return_state)."""

    def __init__(self, manager):
        super().__init__(manager)

        # Vasen palsta: äänet
        col_x = SCREEN_WIDTH // 2 - 620
        slider_w = 380
        self.music_slider = Slider(col_x + 60, 280, slider_w,
                                   "MUSIC VOLUME", sound_system.music_volume)
        self.sfx_slider = Slider(col_x + 60, 400, slider_w,
                                 "SOUND EFFECTS", sound_system.sfx_volume)

        self.btn_back = UIButton(col_x + 130, SCREEN_HEIGHT - 160, 240, 55,
                                 "BACK", None, GRAY)
        self.btn_reset = UIButton(col_x + 130, SCREEN_HEIGHT - 240, 240, 55,
                                  "RESET KEYS", None, (200, 140, 90))

        # Vasen palsta, alaosa: näyttöasetukset
        self.mode_rects = []       # (rect, mode)
        self.res_prev_rect = None
        self.res_next_rect = None
        self.display_feedback = ""

        # Oikea palsta: kontrollit
        self.bind_rows = []        # (rect, action)
        self.awaiting_bind = None  # toiminto jota sidotaan
        self.bind_feedback = ""

    def _return_state(self):
        return getattr(self.manager, "options_return_state", None) or "menu"

    def _close(self):
        sound_system.save_options()
        keybinds.save()
        sound_system.play_sound("click")
        self.next_state = self._return_state()

    def handle_event(self, event):
        # --- REBIND-TILA: seuraava näppäin sidotaan ---
        if self.awaiting_bind:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.bind_feedback = "Rebind cancelled."
                else:
                    keybinds.set_key(self.awaiting_bind, event.key)
                    keybinds.save()
                    self.bind_feedback = (
                        f"{dict(keybinds.LABELS).get(self.awaiting_bind, self.awaiting_bind)}"
                        f" is now {pygame.key.name(event.key).upper()}")
                    sound_system.play_sound("click")
                self.awaiting_bind = None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.awaiting_bind = None
                self.bind_feedback = "Rebind cancelled."
            return

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

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Näyttötila-napit
            for rect, mode in self.mode_rects:
                if rect.collidepoint(event.pos):
                    if mode != display_settings.get_mode():
                        ok = display_settings.apply(mode=mode)
                        display_settings.save()
                        self.display_feedback = (
                            f"{display_settings.MODE_LABELS[mode]} applied."
                            if ok else "Could not switch mode.")
                        sound_system.play_sound("click")
                    return
            # Resoluution selaus < >
            step = 0
            if self.res_prev_rect and self.res_prev_rect.collidepoint(event.pos):
                step = -1
            elif self.res_next_rect and self.res_next_rect.collidepoint(event.pos):
                step = 1
            if step:
                choices = display_settings.available_resolutions()
                sizes = [s for _lbl, s in choices]
                try:
                    idx = sizes.index(display_settings.get_resolution())
                except ValueError:
                    idx = 0
                new_size = sizes[(idx + step) % len(sizes)]
                display_settings.apply(resolution=new_size)
                display_settings.save()
                self.display_feedback = f"Resolution: {display_settings.resolution_label()}"
                sound_system.play_sound("click")
                return
            for rect, action in self.bind_rows:
                if rect.collidepoint(event.pos):
                    self.awaiting_bind = action
                    self.bind_feedback = ""
                    sound_system.play_sound("hover")
                    return
            # Instant cast -kytkimet (slotit 1-8)
            for rect, slot in getattr(self, "instant_rects", []):
                if rect.collidepoint(event.pos):
                    from systems import hotbar_prefs
                    on = hotbar_prefs.toggle_instant(slot)
                    self.bind_feedback = (
                        f"Slot {slot}: instant cast "
                        f"{'ON' if on else 'OFF'}")
                    sound_system.play_sound("click")
                    return

        if self.btn_reset.is_clicked(event):
            keybinds.reset_defaults()
            self.bind_feedback = "Controls reset to defaults."
            sound_system.play_sound("click")
            return

        if self.btn_back.is_clicked(event):
            self._close()

    def update(self):
        super().update()

    def draw(self, screen):
        self.draw_themed_background(screen, "guild")

        title = font_title.render("OPTIONS", True, GOLD_COLOR)
        self.draw_header_bar(screen, title, y=10)

        # --- VASEN: ÄÄNET ---
        left = pygame.Rect(SCREEN_WIDTH // 2 - 660, 170, 560,
                           SCREEN_HEIGHT - 260)
        self.draw_soft_panel(screen, left)
        draw_text("AUDIO", font_main, GOLD_COLOR, screen, left.x + 30,
                  left.y + 20)
        self.music_slider.draw(screen)
        self.sfx_slider.draw(screen)

        # --- DISPLAY: ikkunatila + resoluutio ---
        draw_text("DISPLAY", font_main, GOLD_COLOR, screen, left.x + 30,
                  left.y + 420)
        self.mode_rects = []
        mouse = pygame.mouse.get_pos()
        active_mode = display_settings.get_mode()
        bx = left.x + 30
        by = left.y + 462
        for mode in display_settings.MODES:
            label = display_settings.MODE_LABELS[mode]
            w = font_small.size(label)[0] + 32
            rect = pygame.Rect(bx, by, w, 40)
            selected = (mode == active_mode)
            hover = rect.collidepoint(mouse)
            if selected:
                pygame.draw.rect(screen, (70, 60, 30), rect, border_radius=7)
                pygame.draw.rect(screen, GOLD_COLOR, rect, 2, border_radius=7)
            else:
                pygame.draw.rect(screen, (40, 40, 52) if not hover else (50, 50, 66),
                                 rect, border_radius=7)
                pygame.draw.rect(screen, COLOR_TRIM if hover else (100, 100, 115),
                                 rect, 1, border_radius=7)
            draw_text(label, font_small, WHITE if selected else (190, 190, 200),
                      screen, rect.x + 16, rect.y + 10)
            self.mode_rects.append((rect, mode))
            bx += w + 12

        # Resoluutiorivi: < AUTO (2560x1440) >
        ry = by + 58
        draw_text("RESOLUTION", font_small, GRAY, screen, left.x + 30, ry)
        row = pygame.Rect(left.x + 30, ry + 26, 400, 40)
        pygame.draw.rect(screen, (32, 32, 42), row, border_radius=7)
        pygame.draw.rect(screen, (100, 100, 115), row, 1, border_radius=7)
        self.res_prev_rect = pygame.Rect(row.x, row.y, 44, row.h)
        self.res_next_rect = pygame.Rect(row.right - 44, row.y, 44, row.h)
        for r, ch in ((self.res_prev_rect, "<"), (self.res_next_rect, ">")):
            hov = r.collidepoint(mouse)
            pygame.draw.rect(screen, (56, 50, 34) if hov else (44, 44, 56), r,
                             border_radius=7)
            surf = font_main.render(ch, True, GOLD_COLOR if hov else WHITE)
            screen.blit(surf, surf.get_rect(center=r.center))
        lbl = display_settings.resolution_label()
        surf = font_small.render(lbl, True, WHITE)
        screen.blit(surf, surf.get_rect(center=row.center))
        note = ("Window size (borderless/fullscreen use desktop size)"
                if active_mode == "windowed"
                else "Resolution applies in WINDOWED mode")
        draw_text(note, font_small, (130, 130, 145), screen,
                  left.x + 30, row.bottom + 8)
        if self.display_feedback:
            draw_text(self.display_feedback, font_small, (170, 230, 170),
                      screen, left.x + 30, row.bottom + 34)

        self.btn_reset.draw(screen)
        self.btn_back.draw(screen)
        draw_text("ESC to go back", font_small, GRAY, screen,
                  left.x + 30, left.bottom - 36)

        # --- OIKEA: KONTROLLIT ---
        right = pygame.Rect(SCREEN_WIDTH // 2 - 60, 170, 700,
                            SCREEN_HEIGHT - 260)
        self.draw_soft_panel(screen, right)
        draw_text("CONTROLS", font_main, GOLD_COLOR, screen, right.x + 30,
                  right.y + 20)
        draw_text("Click a row, then press the new key.", font_small, GRAY,
                  screen, right.x + 230, right.y + 24)

        self.bind_rows = []
        mouse = pygame.mouse.get_pos()
        row_y = right.y + 62
        row_h = 34
        for action, label in keybinds.LABELS:
            rect = pygame.Rect(right.x + 20, row_y, right.w - 40, row_h - 4)
            hover = rect.collidepoint(mouse)
            waiting = (self.awaiting_bind == action)
            if waiting:
                pygame.draw.rect(screen, (70, 60, 30), rect, border_radius=6)
                pygame.draw.rect(screen, GOLD_COLOR, rect, 1, border_radius=6)
            elif hover:
                pygame.draw.rect(screen, (44, 44, 58), rect, border_radius=6)
                pygame.draw.rect(screen, COLOR_TRIM, rect, 1, border_radius=6)
            draw_text(label, font_small, WHITE, screen, rect.x + 14,
                      rect.y + 6)
            key_txt = "PRESS A KEY..." if waiting else keybinds.key_name(action)
            key_col = GOLD_COLOR if waiting else (200, 220, 255)
            surf = font_small.render(key_txt, True, key_col)
            screen.blit(surf, (rect.right - surf.get_width() - 16, rect.y + 6))
            self.bind_rows.append((rect, action))
            row_y += row_h

        # Kiinteät kontrollit (info)
        row_y += 8
        for label, key_txt in keybinds.FIXED:
            draw_text(label, font_small, (150, 150, 160), screen,
                      right.x + 34, row_y + 4)
            surf = font_small.render(key_txt, True, (150, 150, 160))
            screen.blit(surf, (right.right - surf.get_width() - 36, row_y + 4))
            row_y += 28

        # --- INSTANT CAST (pelitesti 17) ---
        # Slotit 1-8: päällä = näppäin castaa heti kursorin suuntaan,
        # pois = näppäin valitsee ja klikkaus castaa (vanha tapa)
        from systems import hotbar_prefs
        row_y += 10
        draw_text("INSTANT CAST (per slot: key casts toward cursor)",
                  font_small, GOLD_COLOR, screen, right.x + 30, row_y)
        row_y += 30
        self.instant_rects = []
        slot_list = ["spell1", "spell2", "spell3", "spell4", "spell5",
                     "spell6", "usable", "usable2"]
        chip_w = (right.w - 60) // 8
        for i, slot in enumerate(slot_list):
            rect = pygame.Rect(right.x + 30 + i * chip_w, row_y,
                               chip_w - 6, 34)
            on = hotbar_prefs.is_instant(slot)
            pygame.draw.rect(screen, (48, 66, 48) if on else (38, 38, 46),
                             rect, border_radius=7)
            pygame.draw.rect(screen,
                             (130, 210, 140) if on else (100, 100, 110),
                             rect, 1, border_radius=7)
            txt = f"{i + 1} {'ON' if on else 'off'}"
            surf = font_small.render(txt, True,
                                     (180, 235, 185) if on else GRAY)
            screen.blit(surf, surf.get_rect(center=rect.center))
            self.instant_rects.append((rect, slot))

        if self.bind_feedback:
            draw_text(self.bind_feedback, font_small, (170, 230, 170), screen,
                      right.x + 30, right.bottom - 36)
