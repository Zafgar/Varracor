import pygame
from settings import *
from ui_kit import UIButton, draw_panel, draw_text, font_title, font_main, font_small, GOLD_COLOR, WHITE, GRAY, GREEN, RED, ORANGE
from menus.base_menu import BaseMenu
from sound_manager import sound_system

# --- DATA ---
RECRUIT_TIERS = {
    0: {
        "name": "Tier 0 - The Rookie Dust Circuit",
        "req_league": 1,
        "inns": [
            {"name": "The Sunk Cask", "loc": "Muckford", "keeper": "Marda Shant", "desc": "Cheap contracts, debt-ridden fighters.", "id": "sunk_cask", "status": "OPEN"},
            {"name": "The Saffron Cup", "loc": "Saffron Oasis", "keeper": "Qadir Waterbond", "desc": "Spearmen and desert guides.", "id": "saffron_cup", "status": "WIP"},
            {"name": "Cureleaf Roost", "loc": "Vinehollow", "keeper": "Eira Cureleaf", "desc": "Hunters and poison experts.", "id": "cureleaf", "status": "WIP"}
        ]
    },
    1: {
        "name": "Tier 1 - The Scrapring Circuit",
        "req_league": 2,
        "inns": [
            {"name": "The Span", "loc": "Rattlebridge", "keeper": "Hendrik Ironspan", "desc": "Disciplined shield-bearers.", "id": "span", "status": "WIP"},
            {"name": "The Rivet & Wrench", "loc": "Rivet Row", "keeper": "Kessa Mallory", "desc": "Tanks and mechanics.", "id": "rivet", "status": "WIP"}
        ]
    },
    2: {
        "name": "Tier 2 - The Iron Circle Circuit",
        "req_league": 3,
        "inns": [
            {"name": "The Gilded Ledger", "loc": "Giltgate", "keeper": "Marcellus Vane", "desc": "Mercenaries and show-gladiators.", "id": "gilded", "status": "WIP"},
            {"name": "The Keel & Cup", "loc": "Coinharbor", "keeper": "Salla Waveknot", "desc": "Sailors and net-fighters.", "id": "keel", "status": "WIP"},
            {"name": "Kestrel's Rest", "loc": "Caravanserai", "keeper": "Old Rafiq", "desc": "Caravan guards and snipers.", "id": "kestrel", "status": "WIP"}
        ]
    },
    3: {
        "name": "Tier 3 - The Steel Arena Circuit",
        "req_league": 4,
        "inns": [
            {"name": "The Prism & Rapier", "loc": "Spirewatch", "keeper": "Aria Sable", "desc": "Duelists and mages.", "id": "prism", "status": "WIP"},
            {"name": "Moonfang Lodge", "loc": "Moonwatch", "keeper": "Lysa Moonmark", "desc": "Wardens and druids.", "id": "moonfang", "status": "WIP"}
        ]
    },
    4: {
        "name": "Tier 4 - The Silver League Circuit",
        "req_league": 5,
        "inns": [
            {"name": "The Horn & Hearth", "loc": "Kharak-Tor", "keeper": "Matron Urzha", "desc": "Veterans and heavy infantry.", "id": "horn", "status": "WIP"}
        ]
    }
}

class RecruitMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)
        
        # Cheat Mode Button
        self.btn_cheat = None
        if CHEAT_MODE:
            self.btn_cheat = UIButton(SCREEN_WIDTH - 250, 30, 220, 50, "CHEAT RECRUIT", None, (100, 50, 50))

        self.selected_tier = 0
        self.tier_buttons = []
        self._init_tier_buttons()

    def _init_tier_buttons(self):
        start_y = 150
        for t in range(5):
            btn = UIButton(50, start_y + t * 70, 300, 60, f"Tier {t}", None, GRAY)
            self.tier_buttons.append(btn)

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        if self.btn_back.is_clicked(event):
            self.next_state = getattr(self.manager, "recruit_return_state",
                                      None) or "hub"
            sound_system.play_sound('click')
            return

        if self.btn_cheat and self.btn_cheat.is_clicked(event):
            # Oikotie suoraan majataloon
            self.next_state = "tavern_sunk_cask"
            sound_system.play_sound('click')
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Tier Selection
            for i, btn in enumerate(self.tier_buttons):
                if btn.rect.collidepoint(mouse_pos):
                    # Check lock
                    req = RECRUIT_TIERS[i]["req_league"]
                    if self.manager.league_level >= req:
                        self.selected_tier = i
                        sound_system.play_sound('click')
                    else:
                        sound_system.play_sound('error')
                    return

            # Inn Selection (Right Panel)
            data = RECRUIT_TIERS[self.selected_tier]
            inns = data["inns"]
            
            start_x = 400
            start_y = 150
            card_h = 120
            
            for i, inn in enumerate(inns):
                rect = pygame.Rect(start_x, start_y + i * (card_h + 20), 800, card_h)
                if rect.collidepoint(mouse_pos):
                    if inn["status"] == "OPEN":
                        if inn["id"] == "sunk_cask":
                            self.next_state = "tavern_sunk_cask"
                            sound_system.play_sound('click')
                    else:
                        # WIP
                        sound_system.play_sound('error')

    def draw(self, screen):
        screen.fill((15, 15, 20))
        self.draw_themed_background(screen, mood="city")
        
        self.btn_back.check_hover(pygame.mouse.get_pos())
        self.btn_back.draw(screen)
        
        if self.btn_cheat:
            self.btn_cheat.check_hover(pygame.mouse.get_pos())
            self.btn_cheat.draw(screen)
        
        draw_text("TRAVEL & RECRUITMENT", font_title, GOLD_COLOR, screen, SCREEN_WIDTH // 2 - 200, 30)
        
        # --- LEFT: TIERS ---
        draw_text("SELECT CIRCUIT", font_main, WHITE, screen, 50, 110)
        
        mouse_pos = pygame.mouse.get_pos()
        for i, btn in enumerate(self.tier_buttons):
            req = RECRUIT_TIERS[i]["req_league"]
            is_locked = self.manager.league_level < req
            is_selected = (i == self.selected_tier)
            
            if is_locked:
                btn.text = f"Tier {i} (Locked)"
                btn.base_color = (40, 20, 20)
                btn.enabled = False
            else:
                btn.text = RECRUIT_TIERS[i]["name"].split(" - ")[1] # Show name only
                btn.base_color = (60, 60, 80) if not is_selected else (100, 100, 150)
                btn.enabled = True
                
            if is_selected:
                pygame.draw.rect(screen, GOLD_COLOR, btn.rect.inflate(4,4), 2, border_radius=8)
                
            btn.check_hover(mouse_pos)
            btn.draw(screen)

        # --- RIGHT: INNS ---
        data = RECRUIT_TIERS[self.selected_tier]
        draw_text(data["name"].upper(), font_title, ORANGE, screen, 400, 100)
        
        start_x = 400
        start_y = 150
        card_h = 120
        
        for i, inn in enumerate(data["inns"]):
            rect = pygame.Rect(start_x, start_y + i * (card_h + 20), 800, card_h)
            is_hover = rect.collidepoint(mouse_pos)
            
            # Bg
            col = (30, 30, 40)
            if is_hover: col = (40, 40, 50)
            if inn["status"] == "WIP": col = (25, 25, 30)
            
            draw_panel(screen, rect.x, rect.y, rect.w, rect.h, color=col, border_color=(60, 60, 70))
            
            # Text
            name_col = GOLD_COLOR if inn["status"] == "OPEN" else GRAY
            draw_text(inn["name"], font_main, name_col, screen, rect.x + 20, rect.y + 15)
            draw_text(f"Location: {inn['loc']}", font_small, WHITE, screen, rect.x + 20, rect.y + 45)
            draw_text(f"Keeper: {inn['keeper']}", font_small, (150, 150, 200), screen, rect.x + 300, rect.y + 45)
            
            draw_text(inn["desc"], font_small, (180, 180, 180), screen, rect.x + 20, rect.y + 75)
            
            # Status Badge
            status = inn["status"]
            scol = GREEN if status == "OPEN" else RED
            draw_text(status, font_main, scol, screen, rect.right - 100, rect.centery - 10)
