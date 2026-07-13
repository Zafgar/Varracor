# menus/asset_studio_menu.py
"""Asset Studio: pelin sisäinen kehitystyökalu (F10 cheat-tilassa).

ASSETS: kaikki koodin viittaamat asset-paikat tilatietoineen. Pudota
tiedostot asset_inbox/-kansioon, valitse paikka + tiedosto -> ASSIGN
kopioi ja nimeää oikein; peli käyttää tiedostoa heti. Äänille PLAY.

UNITS: elävä esikatselupenkki - valitse rotu/olento, hahmo piirtyy
täsmälleen pelin renderöijällä (animaatiot mukana). Pue ase/kilpi/
kypärä/panssari nuolinapeista ja katso miten ne piirtyvät hahmolle;
ATTACK/WALK/FLIP/BLOCK testaavat animaatiot.

PROPS: elävä esikatselu + hitbox-editori. Propin update() ajetaan
joka frame (savut, kasvu yms. näkyvät), CHOP/SHAKE testaavat
käyttäytymiset efekteineen (lehdet, omenat), VARIANT kiertää mallit.
Törmäyslaatikko säätyy nuolilla ja tallentuu hitbox_overrides.jsoniin.
"""

from __future__ import annotations

import inspect
import os

import pygame

from menus.base_menu import BaseMenu
from settings import GOLD_COLOR, GRAY, GREEN, RED, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from systems import asset_studio
from ui_kit import UIButton, draw_text, font_main, font_small, font_title

ROW_H = 26
FILTERS = ("ALL", "MISSING", "image", "sound", "music")
TABS = ("ASSETS", "UNITS", "PROPS")
EQUIP_SLOTS = ("main_hand", "off_hand", "head", "body")
SLOT_LABELS = {"main_hand": "WEAPON", "off_hand": "OFF-HAND",
               "head": "HELMET", "body": "ARMOR"}


class _StudioWorld:
    """Kevyt manager-korvike proppien käyttäytymistesteihin.

    Propit kutsuvat manager.vfx-efektejä, add_materialia yms. - tämä
    kerää ne studion omaan mini-maailmaan koskematta oikeaan peliin.
    """

    def __init__(self):
        from vfx import VFXManager

        class _Arena:
            def __init__(self):
                self.props = []
                self.obstacles = []
                self.width = 4000
                self.height = 4000

        class _Units:
            def __init__(self):
                self._items = []

            def add(self, obj):
                self._items.append(obj)

            def remove(self, obj):
                if obj in self._items:
                    self._items.remove(obj)

            def __iter__(self):
                return iter(self._items)

            def __contains__(self, obj):
                return obj in self._items

        self.vfx = VFXManager()
        self.current_arena = _Arena()
        self.all_units = _Units()
        self.inventory = {}
        self.city_storage = {}
        self.player_character = None
        self.world_clock = None
        self.npc_state = {}

    def add_material(self, name, amount=1):
        self.inventory[name] = int(self.inventory.get(name, 0)) + int(amount)

    def grant_hero_xp(self, *args, **kwargs):
        pass


class _StudioAxe:
    """Testikirves CHOP-toimintoon."""
    tool_type = "axe"
    tool_tier = 3
    name = "Studio Axe"


class _StudioChopper:
    """Testihakkaaja: tarpeeksi attribuutteja chop/mine-kutsuille."""
    def __init__(self):
        self.current_weapon = _StudioAxe()
        self.chop_speed = 0.0
        self.wood_yield = 0
        self.mining_yield = 0
        self.mining_speed = 0.0
        self.rect = pygame.Rect(0, 0, 32, 48)


class AssetStudioMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.tab = "ASSETS"
        self.feedback = ""
        self.feedback_timer = 0

        # --- ASSETS ---
        self.filter = "ALL"
        self.catalog = asset_studio.build_catalog()
        self.inbox = asset_studio.list_inbox()
        self.selected = None
        self.selected_inbox = None
        self.scroll = 0
        self.inbox_scroll = 0
        self._preview_cache = {}

        # --- UNITS ---
        self.unit_factories = asset_studio.preview_unit_factories()
        self.unit_scroll = 0
        self.pen_unit = None          # esikatteluyksikkö
        self.pen_label = None
        self.pen_walking = False
        self.pen_walk_dir = 1
        self.equip_lists = asset_studio.equipable_items()
        self.equip_index = {slot: -1 for slot in EQUIP_SLOTS}  # -1 = ei mitään

        # --- PROPS ---
        self.prop_classes = asset_studio.editable_prop_classes()
        self.prop_scroll = 0
        self.selected_prop = None
        self.edit_rect = None
        self._prop_instance = None
        self._prop_world = None       # _StudioWorld propin efekteille
        self._prop_has_variant = False
        self._prop_variant = 1

        # --- Napit ---
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

        self.list_rect = pygame.Rect(40, 190, 700, SCREEN_HEIGHT - 320)
        self.inbox_rect = pygame.Rect(780, SCREEN_HEIGHT - 420,
                                      SCREEN_WIDTH - 820, 290)
        self.pen_rect = pygame.Rect(780, 150, SCREEN_WIDTH - 820,
                                    SCREEN_HEIGHT - 300)

        # UNITS-toimintonapit penkin alalaitaan
        bx, by = self.pen_rect.x + 20, self.pen_rect.bottom - 66
        self.btn_attack = UIButton(bx, by, 150, 48, "ATTACK", None, (200, 110, 90))
        self.btn_walk = UIButton(bx + 160, by, 150, 48, "WALK", None, (120, 170, 230))
        self.btn_flip = UIButton(bx + 320, by, 120, 48, "FLIP", None, GRAY)
        self.btn_block = UIButton(bx + 450, by, 130, 48, "BLOCK", None, (150, 150, 190))

        # PROPS-toimintonapit
        self.btn_chop = UIButton(bx, by, 140, 48, "CHOP", None, (200, 140, 80))
        self.btn_shake = UIButton(bx + 150, by, 140, 48, "SHAKE", None, (140, 190, 110))
        self.btn_variant = UIButton(bx + 300, by, 150, 48, "VARIANT", None, GRAY)

    # ================================================================ helpers
    def _note(self, text):
        self.feedback = str(text)
        self.feedback_timer = 240

    def _visible_rows(self):
        rows = self.catalog
        if self.filter == "MISSING":
            rows = [r for r in rows if not r["exists"]]
        elif self.filter in ("image", "sound", "music"):
            rows = [r for r in rows if r["kind"] == self.filter]
        return rows

    def _preview_surface(self, entry):
        path = entry["path"]
        if path in self._preview_cache:
            return self._preview_cache[path]
        surf = None
        if entry["exists"] and entry["kind"] == "image":
            try:
                surf = pygame.image.load(os.path.join(asset_studio.ROOT, path))
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

    # ---------------------------------------------------------------- units
    # Penkki renderöi yksikön virtuaalimaailmaan ja skaalaa 2x, jotta
    # varusteet ja animaatiot erottuvat kunnolla
    PEN_ANCHOR = (2000, 2000)   # yksikön "maailmapiste"
    PEN_VIEW = (430, 300)       # virtuaali-ikkunan koko (world px)
    PEN_SCALE = 2

    def _spawn_pen_unit(self, label, factory):
        ax, ay = self.PEN_ANCHOR
        try:
            unit = factory(ax, ay)
        except Exception as exc:
            self._note(f"Spawn failed: {exc}")
            return
        unit.rect.centerx = ax
        unit.rect.bottom = ay
        unit.ai_controller = None      # penkissä ohjataan käsin
        unit.facing_right = True
        self.pen_unit = unit
        self.pen_label = label
        self.pen_walking = False
        self.equip_index = {slot: -1 for slot in EQUIP_SLOTS}

    def _cycle_equip(self, slot, step):
        if not self.pen_unit:
            self._note("Pick a unit first.")
            return
        names = self.equip_lists.get(slot, [])
        if not names:
            return
        idx = self.equip_index[slot] + step
        idx = max(-1, min(len(names) - 1, idx))
        self.equip_index[slot] = idx
        equipment = getattr(self.pen_unit, "equipment", None)
        if equipment is None:
            self._note("Unit has no equipment slots.")
            return
        if idx < 0:
            if slot == "main_hand":
                from items.item_registry import create_fists
                equipment[slot] = create_fists()
            else:
                equipment[slot] = None
        else:
            from items.item_registry import create_item
            item = create_item(names[idx])
            if item is None:
                self._note(f"create_item failed: {names[idx]}")
                return
            equipment[slot] = item

    def _pen_equip_name(self, slot):
        idx = self.equip_index[slot]
        names = self.equip_lists.get(slot, [])
        return names[idx] if 0 <= idx < len(names) else "-"

    # ---------------------------------------------------------------- props
    def _select_prop(self, name, cls):
        self.selected_prop = (name, cls)
        self._prop_world = _StudioWorld()
        self._prop_has_variant = "variant" in inspect.signature(cls.__init__).parameters
        self._prop_variant = 1
        self._make_prop_instance()

    def _make_prop_instance(self):
        name, cls = self.selected_prop
        # Prop maailmapisteeseen (0,0), piirto-offset laskee paneelisijainnin
        try:
            if self._prop_has_variant:
                inst = cls(0, 0, variant=self._prop_variant)
            else:
                inst = cls(0, 0)
        except Exception as exc:
            self._note(f"Prop failed: {exc}")
            self._prop_instance = None
            self.edit_rect = None
            return
        self._prop_instance = inst
        r = inst.rect
        self.edit_rect = [r.x, r.y, r.w, r.h]

    def _prop_offset(self):
        """Offset jolla (0,0)-prop piirtyy penkin keskelle."""
        inst = self._prop_instance
        iw = inst.image.get_width() if inst and inst.image else 100
        ih = inst.image.get_height() if inst and inst.image else 100
        ox = -(self.pen_rect.centerx - iw // 2)
        oy = -(self.pen_rect.y + max(80, (self.pen_rect.h - 160 - ih) // 2))
        return ox, oy

    # ================================================================ events
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.next_state = getattr(self.manager, "asset_studio_return_state",
                                      None) or "menu"
            return

        if self.tab == "PROPS" and self.edit_rect and event.type == pygame.KEYDOWN:
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
                elif self.tab == "UNITS":
                    self.unit_scroll = max(0, self.unit_scroll - event.y * 3)
                else:
                    self.prop_scroll = max(0, self.prop_scroll - event.y * 3)
            elif self.inbox_rect.collidepoint(mx, my) and self.tab == "ASSETS":
                self.inbox_scroll = max(0, self.inbox_scroll - event.y * 3)
            return

        if self.btn_leave.is_clicked(event):
            self.next_state = getattr(self.manager, "asset_studio_return_state",
                                      None) or "menu"
            sound_system.play_sound("click")
            return

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        mx, my = event.pos

        # Välilehdet
        for i, tab in enumerate(TABS):
            if pygame.Rect(40 + i * 190, 96, 180, 46).collidepoint(mx, my):
                self.tab = tab
                sound_system.play_sound("click")
                return

        if self.tab == "ASSETS":
            self._handle_assets_click(event, mx, my)
        elif self.tab == "UNITS":
            self._handle_units_click(event, mx, my)
        else:
            self._handle_props_click(event, mx, my)

    def _handle_assets_click(self, event, mx, my):
        for i, f in enumerate(FILTERS):
            if pygame.Rect(40 + i * 150, 150, 140, 32).collidepoint(mx, my):
                self.filter = f
                self.scroll = 0
                return
        if self.list_rect.collidepoint(mx, my):
            idx = self.scroll + (my - self.list_rect.y) // ROW_H
            rows = self._visible_rows()
            if 0 <= idx < len(rows):
                self.selected = rows[idx]
            return
        if self.inbox_rect.collidepoint(mx, my):
            idx = self.inbox_scroll + (my - self.inbox_rect.y - 40) // ROW_H
            if 0 <= idx < len(self.inbox):
                self.selected_inbox = self.inbox[idx]["name"]
            return
        if self.btn_assign.is_clicked(event):
            if not self.selected or not self.selected_inbox:
                self._note("Pick a slot AND an inbox file first.")
                sound_system.play_sound("error")
                return
            ok, msg = asset_studio.assign_asset(self.selected_inbox,
                                                self.selected["path"])
            self._note(msg)
            sound_system.play_sound("coin" if ok else "error")
            if ok:
                target = self.selected["path"]
                self._rebuild()
                self.selected = next(
                    (r for r in self.catalog if r["path"] == target), None)
            return
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

    def _handle_units_click(self, event, mx, my):
        if self.list_rect.collidepoint(mx, my):
            idx = self.unit_scroll + (my - self.list_rect.y) // ROW_H
            if 0 <= idx < len(self.unit_factories):
                self._spawn_pen_unit(*self.unit_factories[idx])
            return
        # Varusterivit: < nimi > -nuolet
        if self.pen_unit and hasattr(self.pen_unit, "equipment"):
            ex = self.pen_rect.x + 20
            for si, slot in enumerate(EQUIP_SLOTS):
                y = self.pen_rect.y + 56 + si * 40
                if pygame.Rect(ex + 110, y, 28, 28).collidepoint(mx, my):
                    self._cycle_equip(slot, -1)
                    return
                if pygame.Rect(ex + 420, y, 28, 28).collidepoint(mx, my):
                    self._cycle_equip(slot, +1)
                    return
        if self.btn_attack.is_clicked(event):
            u = self.pen_unit
            if u and hasattr(u, "attack_cooldown"):
                u.attack_cooldown = getattr(u, "attack_speed", 60)
                u.attack_vector = (10 if u.facing_right else -10, 0)
                u.animation_state = "attack"
            return
        if self.btn_walk.is_clicked(event):
            self.pen_walking = not self.pen_walking
            return
        if self.btn_flip.is_clicked(event):
            if self.pen_unit:
                self.pen_unit.facing_right = not self.pen_unit.facing_right
            return
        if self.btn_block.is_clicked(event):
            u = self.pen_unit
            if u and hasattr(u, "is_blocking"):
                u.is_blocking = not u.is_blocking
            return

    def _handle_props_click(self, event, mx, my):
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
                self._make_prop_instance()
                self._note("Override cleared (code default).")
            return
        inst = self._prop_instance
        if not inst:
            return
        if self.btn_chop.is_clicked(event) and hasattr(inst, "chop"):
            chopper = _StudioChopper()
            chopper.rect.center = inst.rect.center
            try:
                inst.chop(chopper, chopper.current_weapon, self._prop_world)
                got = dict(self._prop_world.inventory)
                self._note(f"Chop! World inventory: {got}")
            except Exception as exc:
                self._note(f"Chop failed: {exc}")
            return
        if self.btn_shake.is_clicked(event) and hasattr(inst, "shake"):
            try:
                inst.shake(self._prop_world)
                self._note("Shake! Watch for drops around the prop.")
            except Exception as exc:
                self._note(f"Shake failed: {exc}")
            return
        if self.btn_variant.is_clicked(event) and self._prop_has_variant:
            self._prop_variant = self._prop_variant % 3 + 1
            self._make_prop_instance()
            self._note(f"Variant {self._prop_variant}")
            return

    # ================================================================ update
    def update(self):
        super().update()
        pos = pygame.mouse.get_pos()
        for btn in (self.btn_leave, self.btn_assign, self.btn_play,
                    self.btn_save_hb, self.btn_reset_hb, self.btn_attack,
                    self.btn_walk, self.btn_flip, self.btn_block,
                    self.btn_chop, self.btn_shake, self.btn_variant):
            btn.update_hover(pos)
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

        # UNITS-penkin simulointi
        u = self.pen_unit
        if u and self.tab == "UNITS":
            if getattr(u, "attack_cooldown", 0) > 0:
                u.attack_cooldown -= 1
                if u.attack_cooldown <= 0 and getattr(u, "animation_state", "") == "attack":
                    u.animation_state = "idle"
            if self.pen_walking:
                u.rect.x += 2 * self.pen_walk_dir
                u.facing_right = self.pen_walk_dir > 0
                ax = self.PEN_ANCHOR[0]
                span = self.PEN_VIEW[0] // 2 - 60
                if u.rect.centerx > ax + span:
                    self.pen_walk_dir = -1
                elif u.rect.centerx < ax - span:
                    self.pen_walk_dir = 1

        # PROPS-maailman simulointi (animaatiot, tippuneet objektit, VFX)
        if self.tab == "PROPS" and self._prop_instance and self._prop_world:
            world = self._prop_world
            try:
                self._prop_instance.update(None, world)
            except Exception:
                pass
            for extra in list(world.current_arena.props):
                try:
                    extra.update(None, world)
                except Exception:
                    pass
            try:
                world.vfx.update(None)
            except Exception:
                pass

    # ================================================================ draw
    def draw(self, screen):
        self.draw_themed_background(screen, mood="guild")
        title = font_title.render("ASSET STUDIO", True, GOLD_COLOR)
        self.draw_header_bar(screen, title, y=20)

        for i, tab in enumerate(TABS):
            rect = pygame.Rect(40 + i * 190, 96, 180, 46)
            active = tab == self.tab
            pygame.draw.rect(screen, (58, 52, 40) if active else (32, 32, 38),
                             rect, border_radius=8)
            pygame.draw.rect(screen, GOLD_COLOR if active else (90, 90, 100),
                             rect, 2, border_radius=8)
            draw_text(tab, font_main, WHITE, screen, rect.x + 34, rect.y + 10)

        if self.tab == "ASSETS":
            self._draw_assets(screen)
        elif self.tab == "UNITS":
            self._draw_units(screen)
        else:
            self._draw_props(screen)

        if self.feedback_timer > 0 and self.feedback:
            box = pygame.Rect(40, SCREEN_HEIGHT - 110, 680, 44)
            pygame.draw.rect(screen, (22, 22, 26), box, border_radius=8)
            pygame.draw.rect(screen, (180, 145, 85), box, 2, border_radius=8)
            draw_text(self.feedback[:80], font_small, WHITE, screen,
                      box.x + 16, box.y + 12)

        self.btn_leave.draw(screen)

    # ---------------------------------------------------------------- assets
    def _draw_assets(self, screen):
        for i, f in enumerate(FILTERS):
            rect = pygame.Rect(40 + i * 150, 150, 140, 32)
            active = f == self.filter
            pygame.draw.rect(screen, (52, 60, 46) if active else (30, 30, 36),
                             rect, border_radius=6)
            pygame.draw.rect(screen, GREEN if active else (80, 80, 90),
                             rect, 1, border_radius=6)
            draw_text(f.upper(), font_small, WHITE, screen, rect.x + 14, rect.y + 7)

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

        panel = pygame.Rect(780, 150, SCREEN_WIDTH - 820, 380)
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

    # ---------------------------------------------------------------- units
    def _draw_units(self, screen):
        lr = self.list_rect
        pygame.draw.rect(screen, (24, 24, 30), lr, border_radius=8)
        pygame.draw.rect(screen, (70, 70, 82), lr, 2, border_radius=8)
        max_rows = lr.h // ROW_H
        self.unit_scroll = max(0, min(self.unit_scroll,
                                      max(0, len(self.unit_factories) - max_rows)))
        for vi, (label, _f) in enumerate(
                self.unit_factories[self.unit_scroll:self.unit_scroll + max_rows]):
            y = lr.y + vi * ROW_H
            if self.pen_label == label:
                pygame.draw.rect(screen, (52, 52, 66), (lr.x + 2, y, lr.w - 4, ROW_H))
            draw_text(label, font_small, WHITE, screen, lr.x + 16, y + 4)
        draw_text("Click a unit to spawn it in the pen.", font_small, GRAY,
                  screen, lr.x, lr.bottom + 8)

        pen = self.pen_rect
        pygame.draw.rect(screen, (22, 26, 22), pen, border_radius=8)
        pygame.draw.rect(screen, (70, 82, 70), pen, 2, border_radius=8)

        u = self.pen_unit
        if not u:
            draw_text("The pen renders units with the REAL game renderer -",
                      font_small, GRAY, screen, pen.x + 20, pen.y + 20)
            draw_text("equipment, animations and sprites look exactly like in play.",
                      font_small, GRAY, screen, pen.x + 20, pen.y + 44)
            return

        draw_text(self.pen_label, font_main, GOLD_COLOR, screen, pen.x + 20, pen.y + 16)

        # Varusterivit
        if hasattr(u, "equipment"):
            ex = pen.x + 20
            for si, slot in enumerate(EQUIP_SLOTS):
                y = pen.y + 56 + si * 40
                draw_text(SLOT_LABELS[slot], font_small, (170, 170, 180),
                          screen, ex, y + 5)
                for bx, txt in ((ex + 110, "<"), (ex + 420, ">")):
                    r = pygame.Rect(bx, y, 28, 28)
                    pygame.draw.rect(screen, (40, 40, 48), r, border_radius=6)
                    pygame.draw.rect(screen, (110, 110, 125), r, 1, border_radius=6)
                    draw_text(txt, font_main, WHITE, screen, r.x + 8, r.y + 1)
                draw_text(self._pen_equip_name(slot), font_small, WHITE, screen,
                          ex + 150, y + 5)
        else:
            draw_text("(no equipment slots on this creature)", font_small, GRAY,
                      screen, pen.x + 20, pen.y + 60)

        # Itse hahmo pelin renderöijällä virtuaali-ikkunaan, skaalaus 2x.
        # Lattiaviiva jalkoihin (view'n alalaidasta 40 world px ylös).
        vw, vh = self.PEN_VIEW
        ax, ay = self.PEN_ANCHOR
        view = pygame.Surface((vw, vh), pygame.SRCALPHA)
        offset = (ax - vw // 2, ay - (vh - 40))
        floor_view_y = vh - 40
        pygame.draw.line(view, (60, 74, 58), (0, floor_view_y),
                         (vw, floor_view_y), 2)
        try:
            if hasattr(u, "draw_procedural") and not getattr(u, "use_sprites", False):
                u.draw_procedural()
            u.draw_on_screen(view, offset)
        except Exception as exc:
            draw_text(f"Render error: {exc}", font_small, RED, screen,
                      pen.x + 640, pen.y + 60)
        scaled = pygame.transform.scale(
            view, (vw * self.PEN_SCALE, vh * self.PEN_SCALE))
        view_x = pen.right - vw * self.PEN_SCALE - 24
        view_y = pen.bottom - vh * self.PEN_SCALE - 100
        screen.blit(scaled, (view_x, view_y))
        pygame.draw.rect(screen, (58, 70, 58),
                         (view_x, view_y, vw * self.PEN_SCALE, vh * self.PEN_SCALE), 1)

        state = []
        if getattr(u, "attack_cooldown", 0) > 0:
            state.append("attacking")
        if self.pen_walking:
            state.append("walking")
        if getattr(u, "is_blocking", False):
            state.append("blocking")
        draw_text("state: " + (", ".join(state) or "idle"), font_small, GRAY,
                  screen, pen.x + 20, self.btn_attack.rect.y - 28)

        for btn in (self.btn_attack, self.btn_walk, self.btn_flip, self.btn_block):
            btn.draw(screen)

    # ---------------------------------------------------------------- props
    def _draw_props(self, screen):
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

        pen = self.pen_rect
        pygame.draw.rect(screen, (24, 26, 30), pen, border_radius=8)
        pygame.draw.rect(screen, (70, 70, 82), pen, 2, border_radius=8)

        inst = self._prop_instance
        if not self.selected_prop or not inst:
            draw_text("Select a prop. It runs LIVE: update() every frame,",
                      font_small, GRAY, screen, pen.x + 20, pen.y + 20)
            draw_text("CHOP/SHAKE trigger behaviours with effects; arrows tune",
                      font_small, GRAY, screen, pen.x + 20, pen.y + 44)
            draw_text("the hitbox (SHIFT=resize, CTRL=x5), SAVE persists it.",
                      font_small, GRAY, screen, pen.x + 20, pen.y + 68)
            return

        name = self.selected_prop[0]
        draw_text(name, font_main, GOLD_COLOR, screen, pen.x + 20, pen.y + 16)
        iw = inst.image.get_width() if inst.image else 0
        ih = inst.image.get_height() if inst.image else 0
        draw_text(f"image {iw}x{ih}px  |  live update() running", font_small,
                  GRAY, screen, pen.x + 20, pen.y + 46)

        # Mini-maailma: prop + sen synnyttämät objektit + VFX, clipattuna penkkiin
        offset = self._prop_offset()
        clip_before = screen.get_clip()
        screen.set_clip(pen.inflate(-6, -6))
        try:
            inst.draw_on_screen(screen, offset)
            world = self._prop_world
            if world:
                for extra in world.current_arena.props:
                    try:
                        extra.draw_on_screen(screen, offset)
                    except Exception:
                        pass
                try:
                    world.vfx.draw_top(screen, offset)
                except Exception:
                    pass
        except Exception as exc:
            draw_text(f"Render error: {exc}", font_small, RED, screen,
                      pen.x + 20, pen.y + 80)
        finally:
            screen.set_clip(clip_before)

        # Hitbox-overlay (maailma -> ruutu samalla offsetilla)
        if self.edit_rect:
            dx, dy, w, h = self.edit_rect
            hb = pygame.Rect(dx - offset[0], dy - offset[1], max(2, w), max(2, h))
            overlay = pygame.Surface(hb.size, pygame.SRCALPHA)
            overlay.fill((90, 220, 120, 70))
            screen.blit(overlay, hb.topleft)
            pygame.draw.rect(screen, GREEN, hb, 2)
            draw_text(f"hitbox: dx={dx} dy={dy} w={w} h={h}", font_main, WHITE,
                      screen, pen.x + 20, self.btn_chop.rect.y - 28)

        if hasattr(inst, "chop"):
            self.btn_chop.draw(screen)
        if hasattr(inst, "shake"):
            self.btn_shake.draw(screen)
        if self._prop_has_variant:
            self.btn_variant.draw(screen)
        self.btn_save_hb.draw(screen)
        self.btn_reset_hb.draw(screen)
