import pygame
import inspect
import os

from settings import *
from ui_kit import UIButton, draw_text, font_title, font_main, font_small, draw_panel, format_money, GOLD_COLOR, WHITE, RED
from menus.base_menu import BaseMenu
from sound_manager import sound_system

from items.item_registry import get_random_shop_items, RARITY_ORDER


# -------------------------
# Small helpers
# -------------------------
def _norm_rarity(r):
    if not r:
        return None
    r = str(r).strip()
    if not r:
        return None
    return r[:1].upper() + r[1:].lower()


def _detect_category(item):
    """
    Robust category detection vaikka item.type ei ole kunnossa.
    """
    t = getattr(item, "type", None)
    if t:
        ts = str(t).strip().lower()
        if "weapon" in ts or "melee" in ts or "ranged" in ts:
            return "Weapon"
        if "armor" in ts or "shield" in ts or "helmet" in ts:
            return "Armor"
        if "usable" in ts or "consum" in ts or "potion" in ts:
            return "Usable"

    # Heuristiikat
    if hasattr(item, "damage"):
        return "Weapon"
    if hasattr(item, "defense") or hasattr(item, "armor"):
        return "Armor"
    if hasattr(item, "heal_amount"):
        return "Usable"

    return "Misc"


def _draw_item_card_icon(item, screen, x, y, w, h):
    """
    Adapteri eri item-implementaatioille.
    Yrittää kutsua draw_card_icon oikeilla parametreilla.
    """
    fn = getattr(item, "draw_card_icon", None)
    if not callable(fn):
        return

    # Yritetään päätellä parametrien määrä
    try:
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        needed = len(params)
        if params and params[0] == "self":
            needed -= 1
    except Exception:
        needed = 5 # Oletus

    # Kutsutaan sopivalla määrällä argumentteja
    try:
        if needed >= 5: # surface, x, y, w, h
            fn(screen, x, y, w, h)
        elif needed == 4: # surface, x, y, size (käytetään w)
            fn(screen, x, y, w)
        elif needed == 3: # surface, x, y
            fn(screen, x, y)
        else:
            fn(screen, x, y)
    except TypeError:
        # Fallback jos signature-tarkistus epäonnistui
        try:
            fn(screen, x, y, w)
        except Exception:
            pass


class ShopMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)

        # ---- SHOP UI STATE ----
        self.mode = "BUY"             # "BUY" or "SELL"
        self.selected_category = "Weapon"     # "Weapon" / "Armor" / "Usable"
        self.rarity_mode = "ROLL"             # "ROLL" tai "Common/Rare/Epic..."
        self.rarity_dropdown_open = False
        self.scroll_y = 0
        self.max_scroll = 0
        
        # list of (original_index, item)
        self.display_items = []

        # ---- RECT UI ----
        self.back_rect = pygame.Rect(30, 30, 120, 50)
        
        # Mode napit (Ylhäällä)
        self.mode_rects = {
            "BUY": pygame.Rect(180, 30, 100, 50),
            "SELL": pygame.Rect(290, 30, 100, 50)
        }

        # Kategoria napit
        self.cat_rects = {
            "Weapon": pygame.Rect(220, 95, 160, 45),
            "Armor":  pygame.Rect(390, 95, 160, 45),
            "Usable": pygame.Rect(560, 95, 160, 45),
            "Misc":   pygame.Rect(730, 95, 160, 45), # Uusi kategoria materiaaleille
        }

        # Rarity nappi
        self.rarity_rect = pygame.Rect(910, 95, 260, 45)

        # dropdown options
        self.rarity_option_rects = []
        drop_x, drop_y = self.rarity_rect.x, self.rarity_rect.y + self.rarity_rect.height + 8
        opt_h = 40

        options = ["ROLL"] + RARITY_ORDER
        for idx, opt in enumerate(options):
            self.rarity_option_rects.append(
                (opt, pygame.Rect(drop_x, drop_y + idx * (opt_h + 6), self.rarity_rect.width, opt_h))
            )

        # Lataa näkymä
        self._load_view()
        
        # Load custom item frame
        self.card_frame = None
        self._load_frame_asset()

    def _load_frame_asset(self):
        path = "assets/gear/frames/item_frame.png"
        if os.path.exists(path):
            try:
                self.card_frame = pygame.image.load(path).convert_alpha()
            except Exception: pass

    # -------------------------
    # State switching
    # -------------------------
    def _back_target_state(self) -> str:
        return "shop_locations"

    # -------------------------
    # Logic
    # -------------------------
    def _filter_inventory(self, category, rarity_mode):
        """ Filtteröi pelaajan repun (SELL mode) """
        res = []
        want_r = None if rarity_mode == "ROLL" else _norm_rarity(rarity_mode)
        
        # 1. EQUIPMENT BAG (Varusteet)
        if category in ["Weapon", "Armor", "Usable"]:
            bag = self.manager.equipment_bag
            for i, item in enumerate(bag):
                if not item: continue
                
                # Category check
                cat = _detect_category(item)
                if cat != category: continue
                
                # Rarity check
                if want_r:
                    if _norm_rarity(getattr(item, "rarity", None)) != want_r:
                        continue
                
                # Tallenna tyyppi: "equip"
                res.append((i, item, "equip"))

        # 2. INVENTORY (Materiaalit / Misc)
        elif category == "Misc":
            # Materiaalit ovat sanakirjassa {nimi: määrä}
            # Luodaan niistä väliaikaisia objekteja myyntiä varten
            for name, count in self.manager.inventory.items():
                if count <= 0: continue
                
                # Luodaan simppeli objekti
                class MaterialItem:
                    def __init__(self, n, c):
                        self.name = n
                        self.count = c
                        self.cost = 10 # Oletushinta materiaalille
                        self.rarity = "Common"
                        self.description = "Crafting material."
                
                item = MaterialItem(name, count)
                # Tallenna tyyppi: "material"
                res.append((name, item, "material"))

        return res

    def _load_view(self, force_roll: bool = False):
        """ Päivittää self.display_items listan tilan mukaan """
        self.scroll_y = 0
        
        if self.mode == "BUY":
            res = []
            want_r = None if self.rarity_mode == "ROLL" else _norm_rarity(self.rarity_mode)
            
            # Käytetään managerin valmiiksi generoimaa listaa
            for i, item in enumerate(self.manager.shop_items):
                if item is None:
                    continue
                
                if _detect_category(item) != self.selected_category:
                    continue
                if want_r and _norm_rarity(getattr(item, "rarity", None)) != want_r:
                    continue
                
                res.append((i, item, "shop"))
            self.display_items = res
            
        elif self.mode == "SELL":
            # Myyntitilassa näytetään pelaajan reppu filtteröitynä
            self.display_items = self._filter_inventory(self.selected_category, self.rarity_mode)

    # -------------------------
    # UI Helpers
    # -------------------------
    def _draw_button(self, screen, rect, text, active=False, disabled=False, color_override=None):
        if disabled:
            bg = (55, 55, 65)
            fg = (130, 130, 140)
        elif color_override:
            bg = color_override if not active else (min(255, color_override[0]+30), min(255, color_override[1]+30), min(255, color_override[2]+30))
            fg = WHITE
        else:
            bg = (85, 80, 95) if active else (60, 55, 70)
            fg = WHITE if active else (210, 210, 220)

        pygame.draw.rect(screen, bg, rect, border_radius=10)
        pygame.draw.rect(screen, (25, 20, 30), rect, 2, border_radius=10)
        draw_text(text, font_main, fg, screen, rect.x + 14, rect.y + 10)

    # -------------------------
    # EVENT LOOP
    # -------------------------
    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y -= event.y * 30
            self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()

            # BACK
            if self.back_rect.collidepoint(mouse_pos):
                sound_system.play_sound("click")
                self.next_state = self._back_target_state()
                return
            
            # MODE SWITCH (BUY / SELL)
            if self.mode_rects["BUY"].collidepoint(mouse_pos):
                self.mode = "BUY"
                sound_system.play_sound("click")
                self._load_view()
                return
            
            if self.mode_rects["SELL"].collidepoint(mouse_pos):
                self.mode = "SELL"
                sound_system.play_sound("click")
                self._load_view()
                return

            # CATEGORY SWITCH
            for cat, rect in self.cat_rects.items():
                if rect.collidepoint(mouse_pos):
                    sound_system.play_sound("click")
                    self.selected_category = cat
                    self.rarity_dropdown_open = False
                    self._load_view()
                    return

            # RARITY DROPDOWN
            if self.rarity_rect.collidepoint(mouse_pos):
                sound_system.play_sound("click")
                self.rarity_dropdown_open = not self.rarity_dropdown_open
                return

            if self.rarity_dropdown_open:
                clicked_opt = None
                for opt, r in self.rarity_option_rects:
                    if r.collidepoint(mouse_pos):
                        clicked_opt = opt
                        break
                if clicked_opt:
                    sound_system.play_sound("click")
                    self.rarity_mode = clicked_opt
                    self.rarity_dropdown_open = False
                    self._load_view()
                    return

            # ITEM CARDS (BUY / SELL ACTION)
            start_x, start_y = 50, 170
            card_w, card_h = 200, 260
            padding = 20
            
            # Tarkistetaan klikkaus vain jos se on listan alueella (ettei klikata piilossa olevia)
            if mouse_pos[1] > start_y:
                # HUOM: Käytetään self.display_items, joka on päivitetty _load_view:ssä
                for i, entry in enumerate(self.display_items):
                    if entry is None: continue # Sold items are None in BUY mode list

                    # Unpack tuple (original_index, item_object)
                    orig_idx, item, item_type = entry

                    col = i % 4
                    row = i // 4
                    x = start_x + col * (card_w + padding)
                    y = start_y + row * (card_h + padding) - self.scroll_y
                    card_rect = pygame.Rect(x, y, card_w, card_h)

                    if card_rect.collidepoint(mouse_pos):
                        
                        if self.mode == "BUY":
                            # OSTA
                            if self.manager.gold >= item.cost:
                                # buy_shop_item käyttää indeksiä self.manager.shop_items listaan.
                                # Käytetään orig_idx, joka on tallennettu tupleen.
                                success = self.manager.buy_shop_item(orig_idx)
                                if success:
                                    sound_system.play_sound("coin")
                                    # Päivitä lista (item muuttuu Noneksi managerissa)
                                    self._load_view(force_roll=False) 
                                else:
                                    sound_system.play_sound("error")
                            else:
                                sound_system.play_sound("error")

                        elif self.mode == "SELL":
                            # MYY
                            if item_type == "equip":
                                if self.manager.sell_item(item):
                                    sound_system.play_sound("coin")
                                    self._load_view(force_roll=False)
                                else:
                                    sound_system.play_sound("error")
                            elif item_type == "material":
                                # Myy materiaali (yksi kerrallaan tai kaikki?)
                                # Tässä myydään 1 kpl
                                if self.manager.inventory.get(item.name, 0) > 0:
                                    self.manager.inventory[item.name] -= 1
                                    self.manager.gold += int(item.cost * 0.5)
                                    if self.manager.inventory[item.name] <= 0:
                                        del self.manager.inventory[item.name]
                                    sound_system.play_sound("coin")
                                    self._load_view(force_roll=False)
                            else:
                                sound_system.play_sound("error")
                        return

            # Close dropdown if clicked elsewhere
            self.rarity_dropdown_open = False

    # -------------------------
    # DRAW LOOP
    # -------------------------
    def draw(self, screen):
        self.draw_themed_background(screen, "city")

        title = "MARKETPLACE" if self.mode == "BUY" else "SELL ITEMS (50% Refund)"
        col = GOLD_COLOR if self.mode == "BUY" else (200, 100, 100)
        draw_text(title, font_title, col, screen, 450, 40)
        
        draw_text(f"Funds: {format_money(self.manager.gold)}", font_title, GOLD_COLOR, screen, 20, 100)

        # BACK
        self._draw_button(screen, self.back_rect, "BACK")
        
        # MODE BTNS
        self._draw_button(screen, self.mode_rects["BUY"], "BUY", active=(self.mode=="BUY"), color_override=(60, 100, 60))
        self._draw_button(screen, self.mode_rects["SELL"], "SELL", active=(self.mode=="SELL"), color_override=(100, 60, 60))

        # CATEGORY BTNS
        self._draw_button(screen, self.cat_rects["Weapon"], "WEAPONS", active=(self.selected_category == "Weapon"))
        self._draw_button(screen, self.cat_rects["Armor"], "ARMOR", active=(self.selected_category == "Armor"))
        self._draw_button(screen, self.cat_rects["Usable"], "USABLE", active=(self.selected_category == "Usable"))
        self._draw_button(screen, self.cat_rects["Misc"], "MISC", active=(self.selected_category == "Misc"))

        # RARITY BTN
        self._draw_button(screen, self.rarity_rect, f"RARITY: {self.rarity_mode}")

        # RARITY DROPDOWN
        if self.rarity_dropdown_open:
            for opt, rect in self.rarity_option_rects:
                pygame.draw.rect(screen, (55, 50, 65), rect, border_radius=10)
                pygame.draw.rect(screen, (25, 20, 30), rect, 2, border_radius=10)
                draw_text(opt, font_main, WHITE, screen, rect.x + 14, rect.y + 9)

        # ITEMS
        start_x, start_y = 50, 170
        card_w, card_h = 200, 260
        padding = 20
        
        # Laske max scroll
        rows = (len(self.display_items) + 3) // 4
        total_h = rows * (card_h + padding)
        view_h = SCREEN_HEIGHT - start_y - 20
        self.max_scroll = max(0, total_h - view_h)
        
        # Aseta leikkausalue (clipping), jotta itemit eivät piirry ylävalikon päälle
        prev_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(0, start_y, SCREEN_WIDTH, SCREEN_HEIGHT - start_y))

        mouse_pos = pygame.mouse.get_pos()
        hover_item = None

        for i, entry in enumerate(self.display_items):
            col = i % 4
            row = i // 4
            x = start_x + col * (card_w + padding)
            y = start_y + row * (card_h + padding) - self.scroll_y
            
            # Optimointi: Älä piirrä jos ruudun ulkopuolella
            if y + card_h < start_y or y > SCREEN_HEIGHT:
                continue
            
            # SOLD placeholder (vain BUY modessa)
            if entry is None:
                if self.mode == "BUY":
                    pygame.draw.rect(screen, (40, 35, 45), (x, y, card_w, card_h), border_radius=8)
                    draw_text("SOLD", font_main, (80, 70, 80), screen, x + 70, y + 110)
                continue

            # Unpack tuple
            orig_idx, item, item_type = entry

            # Card BG
            card_rect = pygame.Rect(x, y, card_w, card_h)
            is_hover = card_rect.collidepoint(mouse_pos)
            if is_hover: hover_item = item

            rarity_col = item.get_color() if hasattr(item, "get_color") else WHITE

            # --- DRAW CARD BACKGROUND / FRAME ---
            if self.card_frame:
                # Käytetään ladattua framea
                scaled_frame = pygame.transform.smoothscale(self.card_frame, (card_w, card_h))
                screen.blit(scaled_frame, (x, y))
                
                # Hover highlight
                if is_hover:
                    s = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                    s.fill((255, 255, 255, 20))
                    screen.blit(s, (x, y))
            else:
                # Fallback vanhaan tyyliin
                bg_col = (60, 55, 70) if is_hover else (50, 45, 60)
                pygame.draw.rect(screen, bg_col, (x, y, card_w, card_h), border_radius=8)
                
                # Rarity border
                pygame.draw.rect(screen, (25, 20, 30), (x, y, card_w, card_h), 2, border_radius=8)
                pygame.draw.rect(screen, rarity_col, (x+2, y+2, card_w-4, card_h-4), 1, border_radius=6)

            # Icon
            # Top 50% (0-130px)
            icon_cx = x + card_w // 2
            icon_cy = y + (card_h * 0.25) # Keskellä yläosaa
            
            if item_type == "material":
                pygame.draw.circle(screen, (150, 150, 150), (int(icon_cx), int(icon_cy)), 30)
                draw_text("MAT", font_small, (50, 50, 50), screen, int(icon_cx) - 15, int(icon_cy) - 10)
            else:
                _draw_item_card_icon(item, screen, int(icon_cx) - 50, int(icon_cy) - 50, 100, 100)

            # Stats (simple)
            # Middle section (starts at 50% height -> y + 130)
            stat_y = y + 125
            stat_col = (20, 20, 20) # Musta teksti pergamentille
            if hasattr(item, "damage"):
                draw_text(f"Dmg: {item.damage}", font_small, stat_col, screen, x + 10, stat_y)
                stat_y += 18
                draw_text(f"Range: {getattr(item, 'attack_range', 0)}", font_small, stat_col, screen, x + 10, stat_y)
                stat_y += 18
                scl = getattr(item, "scaling", {})
                if scl:
                    draw_text(f"Scale: {', '.join(scl.keys())}", font_small, stat_col, screen, x + 10, stat_y)
                
            elif hasattr(item, "defense"):
                draw_text(f"Def: {item.defense}", font_small, stat_col, screen, x + 10, stat_y)
                stat_y += 18
                grp = getattr(item, "armor_group", "")
                if grp:
                    draw_text(f"Type: {grp.capitalize()}", font_small, stat_col, screen, x + 10, stat_y)
            elif hasattr(item, "heal_amount"):
                draw_text(f"Heal: {item.heal_amount}", font_small, stat_col, screen, x + 10, stat_y)
            elif item_type == "material":
                draw_text(f"Count: {item.count}", font_small, stat_col, screen, x + 10, stat_y)

            # Price
            price_y = y + 200
            if self.mode == "BUY":
                can_afford = self.manager.gold >= item.cost
                price_col = (0, 100, 0) if can_afford else (180, 0, 0) # Tummanvihreä / Tummanpunainen
                price_txt = format_money(item.cost)
            else:
                price_col = (0, 100, 0)
                price_txt = f"{format_money(int(item.cost * 0.5))} (Sell)"

            draw_text(price_txt, font_main, price_col, screen, x + 10, price_y)
            
            # Name (Bottom 10%)
            name_y = y + card_h - 25
            name_surf = font_small.render(item.name[:22], True, (0, 0, 0)) # Musta nimi
            screen.blit(name_surf, name_surf.get_rect(center=(x + card_w // 2, name_y)))
            
        # Palauta clipping normaaliksi ennen tooltipin piirtoa
        screen.set_clip(prev_clip)
            
        # Tooltip (piirretään lopuksi päälle)
        if hover_item:
            self.draw_tooltip(screen, hover_item, mouse_pos)

    def draw_tooltip(self, screen, item, pos):
        mx, my = pos
        w, h = 250, 120
        # Pysy ruudulla
        if mx + w > SCREEN_WIDTH: mx -= w
        if my + h > SCREEN_HEIGHT: my -= h
        
        draw_panel(screen, mx + 10, my + 10, w, h, (30, 30, 35))
        
        col = item.get_color() if hasattr(item, "get_color") else WHITE
        draw_text(item.name, font_main, col, screen, mx + 20, my + 20)
        draw_text(getattr(item, "rarity", "Common"), font_small, col, screen, mx + 20, my + 45)
        
        desc = getattr(item, "description", "")[:60]
        draw_text(desc, font_small, GRAY, screen, mx + 20, my + 65)