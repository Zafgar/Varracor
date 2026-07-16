# menus/school_spell_shop.py
"""Koulukohtainen loitsukauppa (data-vetoinen). Näyttää katalogin loitsut
annetulle koululle rikkaine selitteineen ja hoitaa oston equipment_bagiin.

Malli otettu Ashen Ossuarysta (necro), mutta hienompi: vasen loitsulista
tier-merkkeineen + oikea iso yksityiskohtapaneeli (describe()) + BUY.

Loitsut ostetaan kyseisestä koulusta - eri koulut avaavat eri kaupat.
Käyttö taistelussa vaatii hahmolta riittävän spell-tierin (tuleva kytkentä)."""
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from ui_kit import (UIButton, draw_panel, draw_text, font_title, font_main,
                    font_small, GOLD_COLOR, WHITE, GRAY, GREEN, RED,
                    format_money)
from menus.base_menu import BaseMenu
from sound_manager import sound_system
from spells.spell_registry import (get_catalog_school_spells,
                                    get_pure_catalog_spells)

TIER_BADGE = {
    1: (150, 170, 210), 2: (150, 170, 210), 3: (140, 210, 160),
    4: (140, 210, 160), 5: (120, 170, 235), 6: (120, 170, 235),
    7: (200, 130, 235), 8: (240, 200, 120),
}


class SchoolSpellShop(BaseMenu):
    def __init__(self, manager, school, title, subtitle, accent,
                 back_state="magic_school"):
        super().__init__(manager)
        self.school = school
        self.title = title
        self.subtitle = subtitle
        self.accent = accent
        self.back_state = back_state
        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)
        self.selected = 0
        self.scroll = 0
        self._row_rects = []      # (rect, index)
        self._buy_rect = None
        self.spells = self._load_spells()

    def _load_spells(self):
        if self.school == "pure":
            spells = get_pure_catalog_spells()
        else:
            spells = get_catalog_school_spells(self.school)
        spells.sort(key=lambda s: (int(getattr(s, "tier", 0)),
                                    getattr(s, "name", "")))
        return spells

    # ---- osto ----
    def _owned(self, spell):
        name = getattr(spell, "name", None)
        return any(getattr(it, "name", None) == name
                   for it in self.manager.equipment_bag)

    # Koulun fraktio: maine avaa paremmat loitsut (tier-portit)
    _SCHOOL_FACTION = {"pure": "prism", "holy": "radiant",
                       "necromancy": "ashen", "druidism": "lupine"}

    def _rep_required(self, spell):
        """Korkeampi tier vaatii enemmän koulun mainetta: (tier-1)*10."""
        return max(0, (int(getattr(spell, "tier", 1)) - 1) * 10)

    def _rep_ok(self, spell):
        fac = self._SCHOOL_FACTION.get(self.school)
        if fac is None:
            return True
        try:
            return int(self.manager.get_faction_rep(fac)) >= \
                self._rep_required(spell)
        except Exception:
            return True

    def _buy(self, spell):
        if self._owned(spell):
            sound_system.play_sound('error')
            return
        if not self._rep_ok(spell):
            sound_system.play_sound('error')
            return
        cost = int(getattr(spell, "cost", 0))
        if self.manager.gold < cost:
            sound_system.play_sound('error')
            return
        self.manager.gold -= cost
        # Lisää TUORE olio (katalogin instanssit ovat jaettuja tälle näkymälle)
        from spells.catalog import make_catalog_spell
        fresh = make_catalog_spell(getattr(spell, "spell_id", "")) or spell
        self.manager.equipment_bag.append(fresh)
        sound_system.play_sound('buy')

    def handle_event(self, event):
        if self.btn_back.is_clicked(event):
            self.next_state = self.back_state
            sound_system.play_sound('click')
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, idx in self._row_rects:
                if rect.collidepoint(event.pos):
                    self.selected = idx
                    sound_system.play_sound('click')
                    return
            if self._buy_rect and self._buy_rect.collidepoint(event.pos):
                if 0 <= self.selected < len(self.spells):
                    self._buy(self.spells[self.selected])
                return
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll - event.y)

    def update(self):
        return self.next_state

    # ---- piirto ----
    def draw(self, screen):
        self.draw_themed_background(screen, mood="city")
        self.btn_back.check_hover(pygame.mouse.get_pos())
        self.btn_back.draw(screen)

        draw_text(self.title, font_title, self.accent, screen, 180, 34)
        draw_text(self.subtitle, font_small, (200, 200, 210), screen, 184, 100)
        draw_text(f"Funds: {format_money(self.manager.gold)}", font_main,
                  GOLD_COLOR, screen, SCREEN_WIDTH - 300, 44)

        self._draw_list(screen)
        self._draw_detail(screen)

    def _draw_list(self, screen):
        self._row_rects = []
        lx, ly, lw = 40, 150, 520
        lh = SCREEN_HEIGHT - 190
        draw_panel(screen, lx, ly, lw, lh, (16, 16, 22),
                   border_color=self.accent)
        if not self.spells:
            draw_text("No spells offered here yet.", font_main, GRAY, screen,
                      lx + 24, ly + 30)
            return
        row_h = 76
        max_rows = (lh - 20) // row_h
        self.scroll = max(0, min(self.scroll,
                                 max(0, len(self.spells) - max_rows)))
        mouse = pygame.mouse.get_pos()
        for vis, i in enumerate(range(self.scroll,
                                      min(len(self.spells),
                                          self.scroll + max_rows))):
            sp = self.spells[i]
            y = ly + 12 + vis * row_h
            rect = pygame.Rect(lx + 10, y, lw - 20, row_h - 8)
            self._row_rects.append((rect, i))
            sel = (i == self.selected)
            owned = self._owned(sp)
            hover = rect.collidepoint(mouse)
            bg = (48, 44, 30) if sel else (30, 30, 38) if hover else (22, 22, 28)
            draw_panel(screen, rect.x, rect.y, rect.w, rect.h, bg,
                       border_color=self.accent if sel else (60, 60, 70))
            # Tier-merkki
            tcol = TIER_BADGE.get(int(getattr(sp, "tier", 1)), (150, 150, 160))
            pygame.draw.circle(screen, tcol, (rect.x + 32, rect.centery), 20)
            draw_text(f"T{sp.tier}", font_main, (10, 10, 14), screen,
                      rect.x + 20, rect.centery - 11)
            draw_text(sp.name, font_main, WHITE if not owned else (150, 200, 160),
                      screen, rect.x + 66, rect.y + 10)
            sub = f"{getattr(sp, 'damage_type', 'Magic')} | " \
                  f"{getattr(sp, 'archetype', 'spell')}"
            draw_text(sub, font_small, (180, 180, 190), screen,
                      rect.x + 66, rect.y + 40)
            if owned:
                draw_text("OWNED", font_small, (150, 220, 160), screen,
                          rect.right - 90, rect.y + 12)
            elif not self._rep_ok(sp):
                draw_text(f"Rep {self._rep_required(sp)}", font_small, RED,
                          screen, rect.right - 100, rect.y + 12)
                draw_text(format_money(int(getattr(sp, "cost", 0))),
                          font_small, (140, 130, 120), screen,
                          rect.right - 100, rect.y + 36)
            else:
                afford = self.manager.gold >= int(getattr(sp, "cost", 0))
                draw_text(format_money(int(getattr(sp, "cost", 0))), font_main,
                          GOLD_COLOR if afford else RED, screen,
                          rect.right - 110, rect.y + 26)

    def _draw_detail(self, screen):
        dx, dy = 590, 150
        dw = SCREEN_WIDTH - dx - 40
        dh = SCREEN_HEIGHT - 190
        draw_panel(screen, dx, dy, dw, dh, (18, 17, 24),
                   border_color=self.accent)
        self._buy_rect = None
        if not (0 <= self.selected < len(self.spells)):
            return
        sp = self.spells[self.selected]
        draw_text(sp.name, font_title, self.accent, screen, dx + 24, dy + 18)
        # Rikas selite (describe) rivitettynä; legacy-loitsut -> description
        if hasattr(sp, "describe"):
            body = sp.describe()
        else:
            body = getattr(sp, "description", "")
        oy = dy + 96
        for line in body.split("\n"):
            if oy > dy + dh - 90:
                break
            for wrapped in self._wrap(line, font_small, dw - 48):
                draw_text(wrapped, font_small, (215, 212, 205), screen,
                          dx + 24, oy)
                oy += 22
        # BUY-nappi
        owned = self._owned(sp)
        afford = self.manager.gold >= int(getattr(sp, "cost", 0))
        brect = pygame.Rect(dx + dw - 240, dy + dh - 70, 216, 52)
        self._buy_rect = brect
        if owned:
            col, label = (60, 90, 66), "OWNED"
        elif not self._rep_ok(sp):
            col = (90, 55, 55)
            label = f"NEEDS {self._rep_required(sp)} REPUTATION"
        elif not afford:
            col, label = (90, 55, 55), "TOO EXPENSIVE"
        else:
            col, label = (65, 135, 80), f"BUY  {format_money(int(sp.cost))}"
        draw_panel(screen, brect.x, brect.y, brect.w, brect.h, col,
                   border_color=WHITE)
        tw = font_main.render(label, True, WHITE)
        screen.blit(tw, tw.get_rect(center=brect.center))

    @staticmethod
    def _wrap(text, font, width):
        if not text:
            return [""]
        words = text.split(" ")
        lines, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if font.size(trial)[0] <= width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines


# --- Konkreettiset koulut (teemat) ---
def make_radiant_synod(manager):
    return SchoolSpellShop(
        manager, "holy", "THE RADIANT SYNOD",
        "Cleansing light and solar fire. Buy Holy spells here.",
        (255, 240, 170))


def make_verdant_covenant(manager):
    return SchoolSpellShop(
        manager, "druidism", "THE VERDANT COVENANT",
        "Nature's growth and rot. Buy Druid spells here.",
        (120, 210, 120))


def make_ashen_catalog(manager):
    return SchoolSpellShop(
        manager, "necromancy", "THE ASHEN OSSUARY",
        "Death's threshold. Buy Necromancy spells here.",
        (150, 210, 160), back_state="magic_school")


def make_prism_catalog(manager):
    return SchoolSpellShop(
        manager, "pure", "THE PRISM COLLEGIUM",
        "Raw Weave, elements and wards. Buy Pure spells here.",
        (120, 150, 255))
