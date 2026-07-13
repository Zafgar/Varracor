import pygame
from settings import *
from ui_kit import UIButton, draw_text, font_title, font_main, font_small, GOLD_COLOR, WHITE, GRAY, RED, GREEN, format_money
from menus.base_menu import BaseMenu
from sound_manager import sound_system

class ShopLocationMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)
        
        # Määritellään kauppapaikat Tier-tasoittain
        self.locations = [
            # TIER 0
            {
                "id": "shanty_consortium",
                "name": "The Shanty Consortium",
                "tier": 0,
                "region": "Muckford (Rookie Dust Circuit)",
                "desc": "Basic repairs, food, and lodging. The bare minimum for survival.",
                "state": "shop", # Avaa nykyisen peruskaupan
                "unlocked": True
            },
            {
                "id": "saffron_waterbond",
                "name": "Saffron Waterbond",
                "tier": 0,
                "region": "Saffron Oasis",
                "desc": "Water merchants and desert gear. Essential for the Sunscar Expanse.",
                "state": None, # Coming soon
                "unlocked": False,
                "req_text": "Requires: Saffron Oasis Access"
            },
            {
                "id": "vinehollow_circle",
                "name": "Vinehollow Cureleaf Circle",
                "tier": 0,
                "region": "Vinehollow",
                "desc": "Herbalists selling antidotes and jungle remedies.",
                "state": None,
                "unlocked": False,
                "req_text": "Requires: Vinehollow Access"
            },
            
            # TIER 1
            {
                "id": "rivet_foundry",
                "name": "Rivet Row Foundry League",
                "tier": 1,
                "region": "Rivet Row (Scrapring Circuit)",
                "desc": "Industrial center for Blacksteel weapons and heavy armor.",
                "state": None,
                "unlocked": False,
                "req_text": "Requires: League Tier 1"
            },
            
            # TIER 2
            {
                "id": "gilded_exchange",
                "name": "Giltgate Gilded Exchange",
                "tier": 2,
                "region": "Giltgate (Iron Circle Circuit)",
                "desc": "High-end trade, betting, and fan merchandise.",
                "state": None,
                "unlocked": False,
                "req_text": "Requires: League Tier 2"
            }
        ]
        
        self.location_buttons = []
        self.scroll_y = 0
        self.max_scroll = 0
        self.list_rect = pygame.Rect(SCREEN_WIDTH // 2 - 400, 150, 800, 700)
        
        self._init_buttons()

    def _init_buttons(self):
        self.location_buttons = []
        start_y = self.list_rect.top
        btn_h = 100
        gap = 20
        
        for i, loc in enumerate(self.locations):
            y = start_y + i * (btn_h + gap)
            rect = pygame.Rect(self.list_rect.left, y, self.list_rect.width, btn_h)
            self.location_buttons.append((rect, loc))
            
        total_h = len(self.locations) * (btn_h + gap)
        self.max_scroll = max(0, total_h - self.list_rect.height)

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        if self.btn_back.is_clicked(event):
            self.next_state = "hub"
            sound_system.play_sound('click')
            return

        if event.type == pygame.MOUSEWHEEL:
            if self.list_rect.collidepoint(mouse_pos):
                self.scroll_y = max(0, min(self.max_scroll, self.scroll_y - event.y * 30))

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Tarkista napit (huomioi scroll)
            for rect, loc in self.location_buttons:
                # Siirrä rect scrollin mukaan
                scrolled_rect = rect.move(0, -self.scroll_y)
                
                # Tarkista onko näkyvissä
                if not self.list_rect.colliderect(scrolled_rect):
                    continue
                    
                if scrolled_rect.collidepoint(mouse_pos):
                    if loc["unlocked"] and loc["state"]:
                        self.next_state = loc["state"]
                        sound_system.play_sound('click')
                    else:
                        sound_system.play_sound('error')
                    return

    def draw(self, screen):
        self.draw_themed_background(screen, mood="city")
        
        self.btn_back.check_hover(pygame.mouse.get_pos())
        self.btn_back.draw(screen)
        
        _t = font_title.render("MARKET DISTRICT", True, GOLD_COLOR)
        self.draw_header_bar(screen, _t, y=10)
        draw_text(f"Funds: {format_money(self.manager.gold)}", font_main, GOLD_COLOR, screen, 50, 50)
        
        # Clip area
        prev_clip = screen.get_clip()
        screen.set_clip(self.list_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        
        for rect, loc in self.location_buttons:
            # Apply scroll
            draw_rect = rect.move(0, -self.scroll_y)
            
            # Skip if out of view
            if not self.list_rect.colliderect(draw_rect):
                continue
                
            is_hover = draw_rect.collidepoint(mouse_pos)
            
            # Taustaväri
            bg_col = (40, 40, 50)
            if is_hover: bg_col = (50, 50, 60)
            if not loc["unlocked"]: bg_col = (30, 20, 20)
            
            border_col = (100, 100, 100)
            if is_hover and loc["unlocked"]: border_col = GOLD_COLOR
            
            pygame.draw.rect(screen, bg_col, draw_rect, border_radius=10)
            pygame.draw.rect(screen, border_col, draw_rect, 2, border_radius=10)
            
            # Tekstit
            title_col = WHITE if loc["unlocked"] else (150, 100, 100)
            draw_text(loc["name"], font_main, title_col, screen, draw_rect.x + 20, draw_rect.y + 15)
            
            tier_col = (200, 200, 100) if loc["unlocked"] else (100, 100, 80)
            draw_text(f"Tier {loc['tier']} • {loc['region']}", font_small, tier_col, screen, draw_rect.x + 20, draw_rect.y + 45)
            
            desc_col = (180, 180, 180) if loc["unlocked"] else (100, 80, 80)
            draw_text(loc["desc"], font_small, desc_col, screen, draw_rect.x + 20, draw_rect.y + 70)
            
            # Status
            if not loc["unlocked"]:
                draw_text("LOCKED", font_main, RED, screen, draw_rect.right - 120, draw_rect.centery - 10)
                if "req_text" in loc:
                    draw_text(loc["req_text"], font_small, (200, 100, 100), screen, draw_rect.right - 250, draw_rect.y + 70)
            elif is_hover:
                draw_text("ENTER >", font_main, GREEN, screen, draw_rect.right - 120, draw_rect.centery - 10)

        screen.set_clip(prev_clip)