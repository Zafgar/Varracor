# menus/asset_studio_menu.py
"""Asset Studio: pelin sisäinen kehitystyökalu (F10 cheat-tilassa).

ASSETS-välilehti: kaikki koodin viittaamat asset-paikat (kuvat, äänet,
musiikki) tilatietoineen. Pudota tiedostot asset_inbox/-kansioon, valitse
paikka + inbox-tiedosto -> ASSIGN kopioi ja nimeää oikein; peli käyttää
tiedostoa heti. Ääniä voi kuunnella PLAY-napilla.

HITBOX-välilehti: valitse prop -> törmäyslaatikkoa siirretään nuolilla
(SHIFT+nuolet muuttaa kokoa), SAVE tallentaa assets/hitbox_overrides.json:iin
joka vaikuttaa peliin heti seuraavassa kartan latauksessa.
"""

from __future__ import annotations

import os

import pygame

from menus.base_menu import BaseMenu
from settings import GOLD_COLOR, GRAY, GREEN, RED, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from systems import asset_studio
from ui_kit import UIButton, draw_text, font_main, font_small, font_title

ROW_H = 26
FILTERS = ("ALL", "MISSING", "image", "sound", "music")


class AssetStudioMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.tab = "ASSETS"          # ASSETS / HITBOX
        self.filter = "ALL"
        self.catalog = asset_studio.build_catalog()
        self.inbox = asset_studio.list_inbox()
        self.selected = None         # valittu katalogirivi (dict)
        self.selected_inbox = None   # valittu inbox-tiedosto (nimi)
        self.scroll = 0
        self.inbox_scroll = 0
        self.feedback = ""
        self.feedback_timer = 0
        self._preview_cache = {}     # path -> Surface|None

        # HITBOX-tila
        self.prop_classes = asset_studio.editable_prop_classes()
        self.prop_scroll = 0
        self.selected_prop = None    # (nimi, luokka)
        self.edit_rect = None        # [dx, dy, w, h] suhteessa (0,0)-instanssiin
        self._prop_instance = None

        self.btn_leave = UIButton(SCREEN_WIDTH - 240, SCREEN_HEIGHT - 80,
                                  200, 54, "CLOSE", None, GRAY)
        self.btn_assign = UIButton(SCREEN_WIDTH - 520, SCREEN_HEIGHT - 80,
                                   250, 54, "ASSIGN TO SLOT", None, GREEN)
        self.btn_play = UIButton(SCREEN_WIDTH - 790, SCREEN_HEIGHT - 80,
                                 240, 54, "PLAY SOUND", None, (120, 170, 230))
        self.btn_save_hb = UIButton(SCREEN_WIDTH - 520, SCREEN_HEIGHT - 80,
                                    250, 54, "SAVE HITBOX", None, GREEN)
        self.btn_reset_hb = UIButton(SCREEN_WIDTH - 790, SCREEN_HEIGHT - 80,
                                     240, 54, "RESET", None, (200, 120, 90))

        self.list_rect = pygame.Rect(40, 190, 760, SCREEN_HEIGHT - 320)
        self.inbox_rect = pygame.Rect(840, SCREEN_HEIGHT - 420, SCREEN_WIDTH - 880,
                                      290)

    # ---------------------------------------------------------------- data
    def _visible_rows(self):
        rows = self.catalog
        if self.filter == "MISSING":
            rows = [r for r in rows if not r["exists"]]
        elif self.filter in ("image", "sound", "music"):
            rows = [r for r in rows if r["kind"] == self.filter]
        return rows

    def _note(self, text):
        self.feedback = text
        self.feedback_timer = 240

    def _preview_surface(self, entry):
        path = entry["path"]
        if path in self._preview_cache:
            return self._preview_cache[path]
        surf = None
        full = os.path.join(asset_studio.ROOT, path)
        if entry["exists"] and entry["kind"] == "image":
            try:
                surf = pygame.image.load(full)
                if pygame.display.get_surface():
                    surf = surf.convert_alpha()
            except Exception:
                surf = None
        self._preview_cache[path] = surf
        return surf

    def _rebuild(self):
        self.catalog = asset_studio.build_catalog()
        self.inbox = asset_studio.list_inbox()
        self._preview_cache.clear()

    def _select_prop(self, name, cls):
        self.selected_prop = (name, cls)
        try:
            inst = cls(0, 0)
        except Exception:
            self._prop_instance = None
            self.edit_rect = None
            return
        self._prop_instance = inst
        r = inst.rect
        self.edit_rect = [r.x, r.y, r.w, r.h]

    # ---------------------------------------------------------------- events
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.next_state = getattr(self.manager, "asset_studio_return_state",
                                      None) or "menu"
            return

        if self.tab == "HITBOX" and self.edit_rect and event.type == pygame.KEYDOWN:
            step = 10 if pygame.key.get_mods() & pygame.KMOD_CTRL else 2
            resize = pygame.key.get_mods() & pygame.KMOD_SHIFT
            dx = dy = 0
            if event.key == pygame.K_LEFT: dx = -step
            if event.key == pygame.K_RIGHT: dx = step
            if event.key == pygame.K_UP: dy = -step
            if event.key == pygame.K_DOWN: dy = step
            if dx or dy:
                if resize:
                    self.edit_rect[2] = max(4, self.edit_rect[2] + dx)
                    self.edit_rect[3] = max(4, self.edit_rect[3] + dy)
                else:
                    self.edit_rect[0] += dx
                    self.edit_rect[1] += dy
                return

        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            if self.list_rect.collidepoint(mx, my):
                if self.tab == "ASSETS":
                    self.scroll = max(0, self.scroll - event.y * 3)
                else:
                    self.prop_scroll = max(0, self.prop_scroll - event.y * 3)
            elif self.inbox_rect.collidepoint(mx, my):
                self.inbox_scroll = max(0, self.inbox_scroll - event.y * 3)
            return

        if self.btn_leave.is_clicked(event):
            self.next_state = getattr(self.manager, "asset_studio_return_state",
                                      None) or "menu"
            sound_system.play_sound("click")
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Välilehdet
            for i, tab in enumerate(("ASSETS", "HITBOX")):
                rect = pygame.Rect(40 + i * 190, 96, 180, 46)
                if rect.collidepoint(mx, my):
                    self.tab = tab
                    sound_system.play_sound("click")
                    return

            if self.tab == "ASSETS":
                # Suodattimet
                for i, f in enumerate(FILTERS):
                    rect = pygame.Rect(40 + i * 150, 150, 140, 32)
                    if rect.collidepoint(mx, my):
                        self.filter = f
                        self.scroll = 0
                        return
                # Katalogirivit
                if self.list_rect.collidepoint(mx, my):
                    idx = self.scroll + (my - self.list_rect.y) // ROW_H
                    rows = self._visible_rows()
                    if 0 <= idx < len(rows):
                        self.selected = rows[idx]
                        return
                # Inbox-rivit
                if self.inbox_rect.collidepoint(mx, my):
                    idx = self.inbox_scroll + (my - self.inbox_rect.y - 40) // ROW_H
                    if 0 <= idx < len(self.inbox):
                        self.selected_inbox = self.inbox[idx]["name"]
                        return
                # ASSIGN
                if self.btn_assign.is_clicked(event):
                    if not self.selected or not self.selected_inbox:
                        self._note("Pick a slot AND an inbox file first.")
                        sound_system.play_sound("error")
                        return
                    ok, msg = asset_studio.assign_asset(
                        self.selected_inbox, self.selected["path"])
                    self._note(msg)
                    sound_system.play_sound("coin" if ok else "error")
                    if ok:
                        target = self.selected["path"]
                        self._rebuild()
                        self.selected = next(
                            (r for r in self.catalog if r["path"] == target), None)
                    return
                # PLAY
                if self.btn_play.is_clicked(event):
                    if self.selected and self.selected["exists"] and \
                            self.selected["kind"] in ("sound", "music"):
                        full = os.path.join(asset_studio.ROOT, self.selected["path"])
                        try:
                            if self.selected["kind"] == "music":
                                pygame.mixer.music.load(full)
                                pygame.mixer.music.play()
                            else:
                                pygame.mixer.Sound(full).play()
                        except Exception as exc:
                            self._note(f"Play failed: {exc}")
                    else:
                        self._note("Select an existing sound/music file.")
                    return

            else:  # HITBOX
                if self.list_rect.collidepoint(mx, my):
                    idx = self.prop_scroll + (my - self.list_rect.y) // ROW_H
                    if 0 <= idx < len(self.prop_classes):
                        self._select_prop(*self.prop_classes[idx])
                        return
                if self.btn_save_hb.is_clicked(event):
                    if self.selected_prop and self.edit_rect:
                        name = self.selected_prop[0]
                        dx, dy, w, h = self.edit_rect
                        asset_studio.save_hitbox_override(name, dx, dy, w, h)
                        self._note(f"Hitbox saved for {name}.")
                        sound_system.play_sound("coin")
                    return
                if self.btn_reset_hb.is_clicked(event):
                    if self.selected_prop:
                        asset_studio.clear_hitbox_override(self.selected_prop[0])
                        self._select_prop(*self.selected_prop)
                        self._note("Override cleared (code default).")
                    return

    def update(self):
        super().update()
        pos = pygame.mouse.get_pos()
        for btn in (self.btn_leave, self.btn_assign, self.btn_play,
                    self.btn_save_hb, self.btn_reset_hb):
            btn.update_hover(pos)
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    # ---------------------------------------------------------------- draw
    def draw(self, screen):
        self.draw_themed_background(screen, mood="guild")
        title = font_title.render("ASSET STUDIO", True, GOLD_COLOR)
        self.draw_header_bar(screen, title, y=20)

        # Välilehdet
        for i, tab in enumerate(("ASSETS", "HITBOX")):
            rect = pygame.Rect(40 + i * 190, 96, 180, 46)
            active = tab == self.tab
            pygame.draw.rect(screen, (58, 52, 40) if active else (32, 32, 38),
                             rect, border_radius=8)
            pygame.draw.rect(screen, GOLD_COLOR if active else (90, 90, 100),
                             rect, 2, border_radius=8)
            draw_text(tab, font_main, WHITE, screen, rect.x + 40, rect.y + 10)

        if self.tab == "ASSETS":
            self._draw_assets(screen)
        else:
            self._draw_hitbox(screen)

        if self.feedback_timer > 0 and self.feedback:
            box = pygame.Rect(40, SCREEN_HEIGHT - 150, 900, 44)
            pygame.draw.rect(screen, (22, 22, 26), box, border_radius=8)
            pygame.draw.rect(screen, (180, 145, 85), box, 2, border_radius=8)
            draw_text(self.feedback, font_small, WHITE, screen,
                      box.x + 16, box.y + 12)

        self.btn_leave.draw(screen)

    def _draw_assets(self, screen):
        # Suodattimet
        for i, f in enumerate(FILTERS):
            rect = pygame.Rect(40 + i * 150, 150, 140, 32)
            active = f == self.filter
            pygame.draw.rect(screen, (52, 60, 46) if active else (30, 30, 36),
                             rect, border_radius=6)
            pygame.draw.rect(screen, GREEN if active else (80, 80, 90),
                             rect, 1, border_radius=6)
            draw_text(f.upper(), font_small, WHITE, screen, rect.x + 14, rect.y + 7)

        # Katalogi
        rows = self._visible_rows()
        lr = self.list_rect
        pygame.draw.rect(screen, (24, 24, 30), lr, border_radius=8)
        pygame.draw.rect(screen, (70, 70, 82), lr, 2, border_radius=8)
        max_rows = lr.h // ROW_H
        self.scroll = max(0, min(self.scroll, max(0, len(rows) - max_rows)))
        for vi, entry in enumerate(rows[self.scroll:self.scroll + max_rows]):
            y = lr.y + vi * ROW_H
            if self.selected is entry:
                pygame.draw.rect(screen, (52, 52, 66), (lr.x + 2, y, lr.w - 4, ROW_H))
            color = GREEN if entry["exists"] else RED
            pygame.draw.circle(screen, color, (lr.x + 14, y + ROW_H // 2), 5)
            draw_text(entry["path"], font_small, WHITE, screen, lr.x + 28, y + 4)
        draw_text(f"{len(rows)} slots ({sum(1 for r in rows if not r['exists'])} missing)"
                  "  -  wheel scrolls", font_small, GRAY, screen, lr.x, lr.bottom + 8)

        # Detaljipaneeli
        panel = pygame.Rect(840, 150, SCREEN_WIDTH - 880, 380)
        pygame.draw.rect(screen, (26, 26, 32), panel, border_radius=8)
        pygame.draw.rect(screen, (70, 70, 82), panel, 2, border_radius=8)
        if self.selected:
            e = self.selected
            status = "OK - file on disk" if e["exists"] else "MISSING - procedural fallback"
            draw_text(e["path"], font_main, GOLD_COLOR, screen, panel.x + 20, panel.y + 16)
            draw_text(f"{e['kind']}  |  {status}", font_small,
                      GREEN if e["exists"] else RED, screen, panel.x + 20, panel.y + 52)
            draw_text("Used by: " + ", ".join(e["sources"][:3]) +
                      (f" (+{len(e['sources']) - 3})" if len(e["sources"]) > 3 else ""),
                      font_small, (170, 170, 180), screen, panel.x + 20, panel.y + 78)
            surf = self._preview_surface(e)
            if surf:
                pw, ph = surf.get_size()
                scale = min(1.0, 240 / max(1, pw), 220 / max(1, ph))
                img = pygame.transform.smoothscale(
                    surf, (max(1, int(pw * scale)), max(1, int(ph * scale))))
                screen.blit(img, (panel.x + 20, panel.y + 120))
                draw_text(f"{pw}x{ph}px", font_small, GRAY, screen,
                          panel.x + 20, panel.bottom - 34)
            elif e["kind"] == "image":
                draw_text("No image yet - game draws this with code graphics.",
                          font_small, GRAY, screen, panel.x + 20, panel.y + 130)
        else:
            draw_text("Select a slot on the left.", font_small, GRAY, screen,
                      panel.x + 20, panel.y + 20)

        # Inbox
        ib = self.inbox_rect
        pygame.draw.rect(screen, (24, 28, 24), ib, border_radius=8)
        pygame.draw.rect(screen, (86, 110, 86), ib, 2, border_radius=8)
        draw_text(f"INBOX  (drop files into asset_inbox/)  {len(self.inbox)} files",
                  font_small, (150, 200, 160), screen, ib.x + 16, ib.y + 10)
        max_ib = (ib.h - 50) // ROW_H
        for vi, f in enumerate(self.inbox[self.inbox_scroll:self.inbox_scroll + max_ib]):
            y = ib.y + 40 + vi * ROW_H
            if f["name"] == self.selected_inbox:
                pygame.draw.rect(screen, (46, 60, 46), (ib.x + 2, y, ib.w - 4, ROW_H))
            draw_text(f"{f['name']}  ({f['kind']}, {f['size'] // 1024} KB)",
                      font_small, WHITE, screen, ib.x + 16, y + 4)

        self.btn_assign.draw(screen)
        self.btn_play.draw(screen)

    def _draw_hitbox(self, screen):
        lr = self.list_rect
        pygame.draw.rect(screen, (24, 24, 30), lr, border_radius=8)
        pygame.draw.rect(screen, (70, 70, 82), lr, 2, border_radius=8)
        max_rows = lr.h // ROW_H
        self.prop_scroll = max(0, min(self.prop_scroll,
                                      max(0, len(self.prop_classes) - max_rows)))
        overrides = asset_studio.load_hitbox_overrides()
        for vi, (name, _cls) in enumerate(
                self.prop_classes[self.prop_scroll:self.prop_scroll + max_rows]):
            y = lr.y + vi * ROW_H
            if self.selected_prop and self.selected_prop[0] == name:
                pygame.draw.rect(screen, (52, 52, 66), (lr.x + 2, y, lr.w - 4, ROW_H))
            tag = "  [custom]" if name in overrides else ""
            draw_text(name + tag, font_small,
                      GOLD_COLOR if tag else WHITE, screen, lr.x + 16, y + 4)

        panel = pygame.Rect(840, 150, SCREEN_WIDTH - 880, SCREEN_HEIGHT - 300)
        pygame.draw.rect(screen, (26, 26, 32), panel, border_radius=8)
        pygame.draw.rect(screen, (70, 70, 82), panel, 2, border_radius=8)

        if not self.selected_prop or not self._prop_instance:
            draw_text("Select a prop on the left. Arrows move the hitbox,",
                      font_small, GRAY, screen, panel.x + 20, panel.y + 20)
            draw_text("SHIFT+arrows resize, CTRL = bigger steps.",
                      font_small, GRAY, screen, panel.x + 20, panel.y + 44)
            return

        name = self.selected_prop[0]
        inst = self._prop_instance
        img = inst.image
        iw, ih = img.get_size()
        scale = min(2.0, (panel.w - 80) / max(1, iw), (panel.h - 220) / max(1, ih))
        sw, sh = max(1, int(iw * scale)), max(1, int(ih * scale))
        origin_x = panel.centerx - sw // 2
        origin_y = panel.y + 90

        draw_text(name, font_main, GOLD_COLOR, screen, panel.x + 20, panel.y + 16)
        draw_text(f"image {iw}x{ih}px  |  scale x{scale:.2f}", font_small, GRAY,
                  screen, panel.x + 20, panel.y + 50)

        shown = pygame.transform.scale(img, (sw, sh)) if scale != 1.0 else img
        screen.blit(shown, (origin_x, origin_y))
        pygame.draw.rect(screen, (110, 110, 130), (origin_x, origin_y, sw, sh), 1)

        # Törmäyslaatikko (skaalattuna kuvan origoon: instanssi luotiin (0,0):aan,
        # jolloin image_pos = (0,0) ja rect on suoraan suhteessa siihen)
        dx, dy, w, h = self.edit_rect
        hb = pygame.Rect(origin_x + int(dx * scale), origin_y + int(dy * scale),
                         max(2, int(w * scale)), max(2, int(h * scale)))
        overlay = pygame.Surface(hb.size, pygame.SRCALPHA)
        overlay.fill((90, 220, 120, 70))
        screen.blit(overlay, hb.topleft)
        pygame.draw.rect(screen, GREEN, hb, 2)

        draw_text(f"hitbox: dx={dx} dy={dy} w={w} h={h}", font_main, WHITE,
                  screen, panel.x + 20, panel.bottom - 60)
        draw_text("Arrows = move   SHIFT+arrows = resize   CTRL = x5 step",
                  font_small, GRAY, screen, panel.x + 20, panel.bottom - 30)

        self.btn_save_hb.draw(screen)
        self.btn_reset_hb.draw(screen)
