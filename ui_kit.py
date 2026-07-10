import pygame
import os
import math
from settings import *
from sound_manager import sound_system

# --- COLOR THEME (Dark Fantasy / Gold) ---
COLOR_BG_DARK   = (20, 20, 25)
COLOR_PANEL_BG  = (30, 30, 40)
COLOR_BORDER    = (60, 60, 70)
COLOR_ACCENT    = GOLD_COLOR
COLOR_HOVER     = (60, 200, 100)
COLOR_DANGER    = (200, 60, 60)
COLOR_BTN_BG    = (50, 50, 60)
COLOR_BTN_HOVER = (70, 70, 80)
COLOR_DISABLED  = (90, 90, 100)

# --- STANDARD COLORS ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 50, 200)
GRAY = (100, 100, 100)

pygame.font.init()
font_main  = pygame.font.SysFont("Segoe UI", 20, bold=True)
font_small = pygame.font.SysFont("Segoe UI", 16)
font_title = pygame.font.SysFont("Georgia", 60, bold=True)

def draw_text(text, font, color, surface, x, y):
    obj = font.render(str(text), True, color)
    surface.blit(obj, (x, y))

def format_money(amount):
    """
    Formats integer amount (Silver Pieces) into HC/PL/GP/SP string.
    1000 SP = 1 GP
    1000 GP = 1 PL
    1000 PL = 1 HC
    """
    amount = int(amount)
    if amount == 0: return "0 SP"
    
    hc = amount // 1000000000
    rem = amount % 1000000000
    pl = rem // 1000000
    rem = rem % 1000000
    gp = rem // 1000
    sp = rem % 1000
    
    parts = []
    if hc > 0: parts.append(f"{hc} HC")
    if pl > 0: parts.append(f"{pl} PL")
    if gp > 0: parts.append(f"{gp} GP")
    if sp > 0: parts.append(f"{sp} SP")
    
    return " ".join(parts)

# --- KORJATTU DRAW PANEL (Tukee nyt border_coloria) ---
def draw_panel(surface, x, y, w, h, color=COLOR_PANEL_BG, border_color=(30, 30, 35), title=None):
    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, color, rect, border_radius=10)
    pygame.draw.rect(surface, border_color, rect, 2, border_radius=10)

    if title:
        title = str(title)
        header_h = 34
        # Otsikkopalkki
        pygame.draw.rect(
            surface, border_color,
            (x, y, w, header_h),
            border_top_left_radius=10,
            border_top_right_radius=10
        )
        
        # Otsikkoteksti
        txt = font_small.render(title, True, GOLD_COLOR)
        text_rect = txt.get_rect(center=(x + w // 2, y + header_h // 2))
        surface.blit(txt, text_rect)

def draw_icon(screen, type, x, y, color):
    if type == 'sword':
        pygame.draw.line(screen, color, (x, y + 8), (x + 12, y - 8), 3)
        pygame.draw.line(screen, color, (x - 3, y + 5), (x + 3, y + 11), 3)

    elif type == 'play':
        pts = [(x, y - 8), (x, y + 8), (x + 10, y)]
        pygame.draw.polygon(screen, color, pts)

    elif type == 'skull':
        pygame.draw.circle(screen, color, (x, y - 2), 6)
        pygame.draw.rect(screen, color, (x - 3, y + 2, 6, 4))

    elif type == 'plus':
        pygame.draw.line(screen, color, (x - 6, y), (x + 6, y), 3)
        pygame.draw.line(screen, color, (x, y - 6), (x, y + 6), 3)

    elif type == 'heart':
        pygame.draw.rect(screen, color, (x - 2, y - 6, 4, 12))
        pygame.draw.rect(screen, color, (x - 6, y - 2, 12, 4))

    elif type == 'coin':
        pygame.draw.circle(screen, color, (x + 4, y), 6, 2)
        txt = font_small.render("$", True, color)
        screen.blit(txt, (x + 1, y - 10))

    elif type == 'star':
        pts = []
        outer_r = 7
        inner_r = 3
        for i in range(10):
            ang = (math.pi / 2) + i * (math.pi / 5)
            r = outer_r if i % 2 == 0 else inner_r
            pts.append((x + r * math.cos(ang), y - r * math.sin(ang)))
        pygame.draw.polygon(screen, color, pts, 2)
        
    elif type == 'shield':
        # Yksinkertainen kilpi
        pts = [(x, y + 8), (x - 6, y), (x - 6, y - 6), (x + 6, y - 6), (x + 6, y)]
        pygame.draw.polygon(screen, color, pts, 2)
        pygame.draw.line(screen, color, (x, y - 4), (x, y + 4), 1)

# --- CLASSIC UI BUTTON ---
class UIButton:
    def __init__(self, x, y, w, h, text, icon_type=None, color=WHITE, hover_color=COLOR_HOVER, action_key=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = str(text)
        self.icon_type = icon_type
        self.action_key = action_key 

        self.base_color = color
        self.hover_color = hover_color

        self.is_hovered = False
        self.enabled = True

        self.scale = 1.0
        self._last_draw_rect = self.rect.copy()
        self._cached_surf = None
        self._cached_params = None # (text, color)

    def set_enabled(self, enabled: bool):
        self.enabled = bool(enabled)
        if not self.enabled:
            self.is_hovered = False

    def _compute_draw_rect(self):
        target_scale = 1.05 if (self.is_hovered and self.enabled) else 1.0
        self.scale += (target_scale - self.scale) * 0.2

        w = int(self.rect.width * self.scale)
        h = int(self.rect.height * self.scale)
        draw_rect = pygame.Rect(0, 0, w, h)
        draw_rect.center = self.rect.center
        return draw_rect

    def update_hover(self, mouse_pos):
        if not self.enabled:
            self.is_hovered = False
            return False
        self.is_hovered = self._last_draw_rect.collidepoint(mouse_pos)
        return self.is_hovered

    def check_hover(self, mouse_pos):
        return self.update_hover(mouse_pos)

    def draw(self, screen):
        draw_rect = self._compute_draw_rect()
        self._last_draw_rect = draw_rect

        # shadow
        shadow_rect = draw_rect.copy()
        shadow_rect.y += 4
        shadow_surf = pygame.Surface((draw_rect.w, draw_rect.h), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 0))
        pygame.draw.rect(shadow_surf, (0, 0, 0, 110), shadow_surf.get_rect(), border_radius=8)
        screen.blit(shadow_surf, shadow_rect.topleft)

        # colors
        if not self.enabled:
            bg_col = COLOR_DISABLED
            border_col = COLOR_BORDER
            text_col = COLOR_BORDER
        else:
            bg_col = COLOR_BTN_HOVER if self.is_hovered else COLOR_BTN_BG
            border_col = self.hover_color if self.is_hovered else self.base_color
            text_col = border_col

        pygame.draw.rect(screen, bg_col, draw_rect, border_radius=8)
        pygame.draw.rect(screen, border_col, draw_rect, 2, border_radius=8)

        # icon
        icon_offset_x = 0
        if self.icon_type:
            icon_x = draw_rect.x + 16
            icon_y = draw_rect.centery
            draw_icon(screen, self.icon_type, icon_x, icon_y, text_col)
            icon_offset_x = 12

        # text
        # --- CACHING OPTIMIZATION ---
        if (self.text, text_col) != self._cached_params:
            self._cached_surf = font_main.render(self.text, True, text_col)
            self._cached_params = (self.text, text_col)
        
        text_surf = self._cached_surf
        text_rect = text_surf.get_rect(center=draw_rect.center)
        text_rect.x += icon_offset_x
        screen.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if not self.enabled:
            return False
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP) and getattr(event, "button", None) == 1:
            mx, my = event.pos
            return self._last_draw_rect.collidepoint((mx, my))
        return False


# --- SPRITE BUTTON ---
class SpriteButton:
    def __init__(self, x, y, img_idle, img_hover, img_pressed, label_text="BUTTON", target_width=350):
        self.base_x = x
        self.base_y = y
        self.target_width = target_width
        self.label_text = label_text
        
        self.hover_vol = 0.4
        self.click_vol = 0.6
        
        self.snd_hover = self._load_sound("assets/sfx/hover.wav", self.hover_vol)
        self.snd_click = self._load_sound("assets/sfx/click.wav", self.click_vol)

        self.images = {}
        self.images["idle"] = self._load_and_scale(img_idle)
        self.images["hover"] = self._load_and_scale(img_hover)
        self.images["pressed"] = self._load_and_scale(img_pressed)
        
        current_img = self.images["idle"]
        if current_img:
            self.width = current_img.get_width()
            self.height = current_img.get_height()
            self.rect = pygame.Rect(x - self.width // 2, y, self.width, self.height)
        else:
            self.rect = pygame.Rect(x - 100, y, 200, 60)
            self.width = 200

        self.state = "idle"
        self.is_pressed = False
        self.hover_anim_offset = 0.0
        self.was_hovering = False

    def _load_sound(self, path, volume):
        if os.path.exists(path):
            try:
                snd = pygame.mixer.Sound(path)
                snd.set_volume(volume)
                return snd
            except Exception: pass
        return None

    def _load_and_scale(self, path):
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                orig_w, orig_h = img.get_size()
                ratio = orig_h / orig_w
                new_w = self.target_width
                new_h = int(new_w * ratio)
                return pygame.transform.smoothscale(img, (new_w, new_h))
            except Exception: pass
        return None

    def check_hover(self, mouse_pos):
        pass

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        is_hovering = self.rect.collidepoint(mouse_pos)
        clicked = False

        if is_hovering and not self.was_hovering:
            if self.snd_hover: self.snd_hover.play()
            else:
                try: sound_system.play_sound("hover")
                except Exception: pass
            sound_system.play_sound("hover", volume=self.hover_vol)
        
        self.was_hovering = is_hovering

        if is_hovering:
            self.hover_anim_offset =  self.hover_anim_offset * 0.8 + (-6) * 0.2
            if pygame.mouse.get_pressed()[0]:
                self.state = "pressed"
                self.is_pressed = True
                self.hover_anim_offset = 2 
            else:
                if self.is_pressed:
                    clicked = True
                    self.is_pressed = False
                    if self.snd_click: self.snd_click.play()
                    else:
                        try: sound_system.play_sound("click")
                        except Exception: pass
                    sound_system.play_sound("click", volume=self.click_vol)
                self.state = "hover"
        else:
            self.hover_anim_offset = self.hover_anim_offset * 0.8 + (0) * 0.2
            self.state = "idle"
            self.is_pressed = False

        return clicked

    def draw(self, screen):
        img = self.images.get(self.state)
        if not img: img = self.images.get("idle")

        draw_y = self.base_y + int(self.hover_anim_offset)
        draw_x = self.base_x - (self.width // 2)

        if img:
            screen.blit(img, (draw_x, draw_y))
        else:
            color = COLOR_BTN_BG
            if "Exit" in self.label_text or "Quit" in self.label_text: color = COLOR_DANGER
            
            fallback_rect = pygame.Rect(draw_x, draw_y, 200, 60)
            pygame.draw.rect(screen, color, fallback_rect, border_radius=10)
            pygame.draw.rect(screen, COLOR_BORDER, fallback_rect, 2, border_radius=10)
            
            draw_text(self.label_text, font_main, GOLD_COLOR, screen, draw_x + 20, draw_y + 15)

# --- NEW: SLOT BACKGROUND & RARITY ---
def draw_item_slot_background(surface, x, y, size, item=None, is_hovered=False):
    """
    Piirtää hienon taustan tavaraslotille.
    Jos item on annettu, värittää reunat rarityn mukaan.
    """
    rect = pygame.Rect(x, y, size, size)
    
    # 1. Taustaväri (Tumma, hieman vaaleampi jos hiiri päällä)
    bg_col = (40, 40, 50) if is_hovered else (30, 30, 40)
    pygame.draw.rect(surface, bg_col, rect, border_radius=5)
    
    # 2. Reunaväri (Rarityn mukaan)
    border_col = (70, 70, 80) # Oletus (Empty slot)
    
    if item:
        rarity = getattr(item, "rarity", "Common")
        if rarity == "Common": border_col = (150, 150, 150)
        elif rarity == "Rare": border_col = (60, 100, 255)     # Sininen
        elif rarity == "Epic": border_col = (200, 50, 200)     # Purppura
        elif rarity == "Legendary": border_col = (255, 180, 0) # Kulta
    
    # Jos hiiri päällä, kirkastetaan reunaa
    if is_hovered:
        border_col = tuple(min(255, c + 50) for c in border_col)

    # 3. Piirrä reuna
    width = 3 if (item and getattr(item, "rarity", "Common") != "Common") else 1
    pygame.draw.rect(surface, border_col, rect, width, border_radius=5)

# --- NEW: ITEM CARD TOOLTIP ---
def _wrap_text(text, font, max_width):
    """Apu-funktio tekstin rivitykseen."""
    words = text.split(' ')
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        w, h = font.size(test_line)
        if w < max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
            
    if current_line:
        lines.append(' '.join(current_line))
    return lines

def draw_item_tooltip(surface, item, x, y, player_unit=None):
    """
    Piirtää "Item Card" -tyylisen infolaatikon.
    Näyttää: Nimi, Rarity, Statsit, Level Req, Description, Hinta.
    """
    if not item: return

    # 1. Asetukset & Värit
    bg_color = (25, 25, 30, 240)  # Tumma, melkein läpinäkymätön
    panel_border = (60, 60, 70)
    
    # Rarity-värit
    rarity = getattr(item, "rarity", "Common")
    rarity_col = (180, 180, 180) # Common
    if rarity == "Rare": rarity_col = (80, 120, 255)
    elif rarity == "Epic": rarity_col = (200, 60, 220)
    elif rarity == "Legendary": rarity_col = (255, 200, 20)
    
    # 2. Kerätään tiedot
    name = getattr(item, "name", "Unknown Item")
    slot = getattr(item, "slot_type", "Item").replace("_", " ").title()
    desc = getattr(item, "description", "")
    stats = getattr(item, "stats", {})
    req_lvl = int(getattr(item, "level_required", 1) or 1)
    cost = getattr(item, "cost", 0)

    # 3. Rakennetaan sisältö (Rivit)
    lines = [] # (text, font, color)

    # A) Tyyppi & Rarity (esim. "Common Body Armor")
    lines.append((f"{rarity} {slot}", font_small, (150, 150, 160)))

    # B) Statsit (HP, Mana, Speed, Def...)
    # Varmista että itemissä on stats-dictionary kunnossa!
    if stats:
        for k, v in stats.items():
            val_str = f"+{v}" if isinstance(v, int) and v > 0 else str(v)
            if v == 0: continue # Ei näytetä nollia
            
            # Väritetään (Speed voi olla float, käsitellään se)
            col = (100, 255, 100) # Vihreä (Buff)
            if isinstance(v, (int, float)) and v < 0: 
                col = (255, 100, 100) # Punainen (Debuff)
            
            lines.append((f"{val_str} {k}", font_small, col))
            
    # C) Level Requirement
    if req_lvl > 1:
        col = (150, 150, 150)
        txt = f"Requires Level {req_lvl}"
        if player_unit:
            if getattr(player_unit, "level", 1) < req_lvl:
                col = (255, 60, 60)
                txt = f"REQUIRES LEVEL {req_lvl}"
            else:
                col = (100, 200, 100)
        lines.append((txt, font_small, col))

    # D) Description (Rivitys)
    desc_lines = _wrap_text(desc, font_small, 230) # Max leveys 230px
    
    # 4. Lasketaan kortin koko
    padding = 12
    line_h = 20
    
    # Leveys määräytyy otsikon tai kuvauksen mukaan
    title_w = font_main.size(name)[0]
    content_w = 230
    box_w = max(content_w, title_w) + padding * 2
    
    # Korkeus: Otsikko + Tyyppi + Statsit + (Väli) + Kuvaus + Hinta
    box_h = padding + 25 + (len(lines) * line_h) 
    
    if desc:
        box_h += 10 # Väli ennen kuvausta
        box_h += len(desc_lines) * 18
        
    box_h += 25 # Hinta alhaalla
    
    # 5. Korjataan sijainti (ettei mene ruudun yli)
    sw, sh = surface.get_size()
    if x + box_w > sw: x -= box_w
    if y + box_h > sh: y -= box_h
    x, y = max(0, x), max(0, y)

    # 6. PIIRRETÄÄN KORTTI
    # Tausta
    s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    s.fill(bg_color)
    # Reuna rarityn värillä (ohut) ja paneelin värillä (paksu)
    pygame.draw.rect(s, panel_border, s.get_rect(), 3) 
    pygame.draw.rect(s, rarity_col, s.get_rect(), 1) 
    surface.blit(s, (x, y))
    
    curr_y = y + padding
    
    # Otsikko
    title_surf = font_main.render(name, True, rarity_col)
    surface.blit(title_surf, (x + padding, curr_y))
    curr_y += 28
    
    # Statsit & Tyyppi
    for txt, fnt, col in lines:
        obj = fnt.render(txt, True, col)
        surface.blit(obj, (x + padding, curr_y))
        curr_y += line_h
        
    # Kuvaus (Harmaalla, kursivoitu jos fontti tukee)
    if desc:
        curr_y += 8
        pygame.draw.line(surface, (60, 60, 70), (x+10, curr_y), (x+box_w-10, curr_y), 1)
        curr_y += 8
        for line in desc_lines:
            obj = font_small.render(line, True, (180, 180, 180))
            surface.blit(obj, (x + padding, curr_y))
            curr_y += 18
            
    # Hinta (Oikeaan alakulmaan)
    val_txt = f"Value: {format_money(cost)}"
    val_surf = font_small.render(val_txt, True, GOLD_COLOR)
    surface.blit(val_surf, (x + box_w - val_surf.get_width() - padding, y + box_h - 20))

# =========================================================
# CACHED FULLSCREEN OVERLAYS
# =========================================================
# Koko ruudun himmennyspintoja käytetään lähes joka valikossa.
# Uuden 1920x1080-pinnan luonti joka framella on turha allokaatio,
# joten samat pinnat välimuistitetaan värin perusteella.
_overlay_cache = {}

def get_fullscreen_overlay(color):
    """
    Palauttaa välimuistitetun koko ruudun kokoisen pinnan täytettynä
    annetulla värillä. RGBA-väri (4 komponenttia) tuottaa SRCALPHA-pinnan.
    ÄLÄ piirrä palautetulle pinnalle - se on jaettu.
    """
    key = tuple(color)
    surf = _overlay_cache.get(key)
    if surf is None:
        if len(key) == 4:
            surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        else:
            surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        surf.fill(key)
        _overlay_cache[key] = surf
    return surf
