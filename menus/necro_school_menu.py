import pygame
from settings import *
from ui_kit import UIButton, draw_panel, draw_text, font_title, font_main, font_small, GOLD_COLOR, WHITE, GRAY, GREEN, RED, format_money
from menus.base_menu import BaseMenu
from sound_manager import sound_system
from menus.chat_menu import ChatMenu

class NecroSchoolMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)
        
        self.tabs = ["OFFERINGS", "SPELLS", "ITEMS"]
        self.active_tab = "OFFERINGS"
        self.tab_buttons = []
        
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        
        # Offerings
        self.btn_offer_1 = UIButton(cx - 220, cy + 50, 200, 60, "OFFER 1", None, (60, 100, 60))
        self.btn_offer_5 = UIButton(cx + 20, cy + 50, 200, 60, "OFFER 5", None, (60, 100, 60))
        
        # Shop items (Placeholder data - laajenna myöhemmin oikeilla itemeillä)
        self.shop_items = [
            {"name": "Raise Skeleton", "type": "Spell", "cost": 400, "rep_req": 500, "desc": "Summon a weak skeleton warrior."},
            {"name": "Bone Armor", "type": "Spell", "cost": 600, "rep_req": 1500, "desc": "Cover yourself in protective bones."},
            {"name": "Life Drain", "type": "Spell", "cost": 800, "rep_req": 3000, "desc": "Steal health from enemies."},
            {"name": "Skull Staff", "type": "Item", "cost": 1200, "rep_req": 5000, "desc": "A staff focusing necrotic energy."}
        ]
        
        self._init_tabs()
        
        # CHAT INTEGRAATIO
        self.chat_overlay = None

    def update(self):
        # 1. Chat overlay
        if self.chat_overlay:
            self.chat_overlay.update()
            if self.chat_overlay.next_state: 
                self.chat_overlay = None 
            return self.next_state

        # 2. TRIGGER CHECKS (Intro)
        npc_data = self.manager.npc_state.get("grand_mortarch", {})
        flags = npc_data.get("flags", {})
        
        if not flags.get("intro_done", False) and self.chat_overlay is None:
            self.chat_overlay = self.manager.open_dialogue("grand_mortarch")
            return self.next_state

    def _init_tabs(self):
        self.tab_buttons = []
        start_x = SCREEN_WIDTH // 2 - 300
        y = 120
        w = 200
        for i, t in enumerate(self.tabs):
            btn = UIButton(start_x + i * w, y, w - 10, 50, t, None, GRAY)
            self.tab_buttons.append(btn)

    def handle_event(self, event):
        if self.chat_overlay:
            self.chat_overlay.handle_event(event)
            return

        mouse_pos = pygame.mouse.get_pos()
        
        if self.btn_back.is_clicked(event):
            self.next_state = "magic_school"
            sound_system.play_sound('click')
            return

        # Tabs
        for btn in self.tab_buttons:
            if btn.is_clicked(event):
                self.active_tab = btn.text
                sound_system.play_sound('click')
                return

        if self.active_tab == "OFFERINGS":
            if self.btn_offer_1.is_clicked(event):
                self._offer_essence(1)
            elif self.btn_offer_5.is_clicked(event):
                self._offer_essence(5)
        
        elif self.active_tab in ["SPELLS", "ITEMS"]:
            # Tähän tulisi ostologiikka (klikkaus listaan)
            pass

    def _offer_essence(self, amount):
        current = self.manager.inventory.get("Spirit Essence", 0)
        if current >= amount:
            self.manager.inventory["Spirit Essence"] -= amount
            if self.manager.inventory["Spirit Essence"] <= 0:
                del self.manager.inventory["Spirit Essence"]
            
            # Add Rep (15 per essence)
            rep_gain = amount * 15
            self.manager.modify_faction_rep("ashen", rep_gain)
            sound_system.play_sound('recruit') # Chime sound
        else:
            sound_system.play_sound('error')

    def draw(self, screen):
        self.draw_themed_background(screen, mood="city") # Maybe a darker mood later
        
        self.btn_back.check_hover(pygame.mouse.get_pos())
        self.btn_back.draw(screen)
        
        draw_text("THE ASHEN OSSUARY", font_title, (150, 150, 150), screen, SCREEN_WIDTH // 2 - 200, 40)
        
        rep = self.manager.get_faction_rep("ashen")
        draw_text(f"Standing: {rep}", font_main, GOLD_COLOR, screen, SCREEN_WIDTH // 2 - 60, 90)

        # Tabs
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.tab_buttons:
            btn.base_color = (100, 100, 120) if btn.text == self.active_tab else (50, 50, 60)
            btn.check_hover(mouse_pos)
            btn.draw(screen)

        # Content
        if self.active_tab == "OFFERINGS":
            self._draw_offerings(screen)
        else:
            self._draw_shop(screen)

        # Chat Overlay
        if self.chat_overlay:
            self.chat_overlay.draw(screen)

    def _draw_offerings(self, screen):
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        
        draw_panel(screen, cx - 300, cy - 150, 600, 400, (30, 30, 35))
        
        draw_text("SPIRIT ESSENCE EXCHANGE", font_main, WHITE, screen, cx - 140, cy - 120)
        draw_text("The Ossuary rewards those who bind the restless.", font_small, (180, 180, 180), screen, cx - 180, cy - 90)
        
        essence = self.manager.inventory.get("Spirit Essence", 0)
        draw_text(f"You have: {essence} Essence", font_title, (100, 255, 100), screen, cx - 120, cy - 30)
        
        self.btn_offer_1.check_hover(pygame.mouse.get_pos())
        self.btn_offer_1.draw(screen)
        draw_text("+15 Rep", font_small, GOLD_COLOR, screen, self.btn_offer_1.rect.centerx - 30, self.btn_offer_1.rect.bottom + 5)
        
        self.btn_offer_5.check_hover(pygame.mouse.get_pos())
        self.btn_offer_5.draw(screen)
        draw_text("+75 Rep", font_small, GOLD_COLOR, screen, self.btn_offer_5.rect.centerx - 30, self.btn_offer_5.rect.bottom + 5)

    def _draw_shop(self, screen):
        # Simplified list for now
        start_y = 200
        cx = SCREEN_WIDTH // 2
        
        rep = self.manager.get_faction_rep("ashen")
        
        # Filter items based on tab
        visible_items = []
        for item in self.shop_items:
            if self.active_tab == "SPELLS" and item["type"] == "Spell": visible_items.append(item)
            if self.active_tab == "ITEMS" and item["type"] == "Item": visible_items.append(item)

        if not visible_items:
            draw_text("No items available in this category yet.", font_main, GRAY, screen, cx - 150, start_y + 50)
            return

        for i, item in enumerate(visible_items):
            y = start_y + i * 100
            rect = pygame.Rect(cx - 350, y, 700, 80)
            
            can_buy_rep = rep >= item["rep_req"]
            can_buy_gold = self.manager.gold >= item["cost"]
            
            bg_col = (40, 40, 50) if can_buy_rep else (30, 20, 20)
            draw_panel(screen, rect.x, rect.y, rect.w, rect.h, bg_col)
            
            name_col = WHITE if can_buy_rep else (150, 100, 100)
            draw_text(item["name"], font_main, name_col, screen, rect.x + 20, rect.y + 15)
            draw_text(item["desc"], font_small, (180, 180, 180), screen, rect.x + 20, rect.y + 45)
            
            # Requirements
            req_col = GREEN if can_buy_rep else RED
            draw_text(f"Req: {item['rep_req']} Rep", font_small, req_col, screen, rect.right - 250, rect.y + 15)
            
            cost_col = GOLD_COLOR if can_buy_gold else RED
            draw_text(format_money(item['cost']), font_main, cost_col, screen, rect.right - 120, rect.y + 25)
            
            if not can_buy_rep:
                draw_text("LOCKED", font_main, RED, screen, rect.right - 100, rect.y + 50)
