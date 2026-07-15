import pygame
from settings import *
from ui_kit import UIButton, draw_panel, draw_text, font_title, font_main, font_small, GOLD_COLOR, WHITE, GRAY, BLUE, RED, GREEN
from menus.base_menu import BaseMenu
from sound_manager import sound_system

class MagicSchoolMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        
        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)
        
        # Koulukuntien data
        self.schools = [
            {
                "id": "pure",
                "rep_id": "prism",
                "name": "The Prism Collegium",
                "type": "Pure Magic",
                "leader": "Grand Magister Lysandra Voss",
                "desc": "The neutral foundation of all magic. Focuses on raw energy, wards, and scientific study of the Vortex.",
                "color": (100, 150, 255), # Blue/White
                "target_state": "school_pure",
                "unlocked": True
            },
            {
                "id": "holy",
                "rep_id": "radiant",
                "name": "The Radiant Synod",
                "type": "Holy Magic",
                "leader": "High Hierophant Caldor Aurelian",
                "desc": "Cleansing light and moral order. The most effective weapon against the undead and blight.",
                "color": (255, 255, 150), # Light Yellow
                "target_state": "school_holy",
                "unlocked": False,
                "req_text": "Requires: Crown Dominion Reputation"
            },
            {
                "id": "necro",
                "rep_id": "ashen",
                "name": "The Ashen Ossuary",
                "type": "Necromancy",
                "leader": "Grand Mortarch Zharok the Quiet",
                "desc": "Masters of the death threshold. They bind the restless to prevent the Vortex from using them.",
                "color": (100, 100, 100), # Ash Grey
                "target_state": "school_necro",
                "unlocked": True,
                # "req_text": "Requires: Kharak Reputation" # Avattu pelaajalle
            },
            {
                "id": "druid",
                "name": "The Verdant Covenant",
                "type": "Druidism",
                "leader": "Grand Druid Maelis Rootspeaker",
                "desc": "Guardians of the ecosystem. They heal the land and commune with nature to fight corruption.",
                "color": (50, 200, 100), # Green
                "target_state": "school_druid",
                "unlocked": False,
                "req_text": "Requires: Lupine Wardens Reputation"
            },
            {
                "id": "manip",
                "name": "The Argent Veil",
                "type": "Manipulation",
                "leader": "Veilmaster Cassian Merrow",
                "desc": "Spies and diplomats using illusion and mind magic. Knowledge is their weapon.",
                "color": (180, 180, 200), # Silver
                "target_state": None,
                "unlocked": False,
                "req_text": "Requires: High Secrecy Clearance"
            }
        ]
        
        self.school_buttons = []
        self._sync_unlocks()
        self._init_buttons()

    def _sync_unlocks(self):
        """Paivittaa 'unlocked'-tilan GameManagerin etenemisesta (cheat avaa kaikki)."""
        try:
            from magic.progression import MENU_ID_TO_SCHOOL, unlock_requirement_text
            for sc in self.schools:
                canon = MENU_ID_TO_SCHOOL.get(sc["id"], sc["id"])
                sc["unlocked"] = self.manager.is_school_unlocked(canon)
                if not sc["unlocked"] and not sc.get("req_text"):
                    sc["req_text"] = "Requires: " + unlock_requirement_text(canon)
        except Exception:
            pass

    def _init_buttons(self):
        start_y = 150
        panel_h = 130
        gap = 20
        
        # Luodaan näkymättömät napit paneelien päälle klikkausta varten
        cx = SCREEN_WIDTH // 2
        w = 900
        
        for i, school in enumerate(self.schools):
            y = start_y + i * (panel_h + gap)
            rect = pygame.Rect(cx - w//2, y, w, panel_h)
            self.school_buttons.append((rect, school))

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        if self.btn_back.is_clicked(event):
            self.next_state = "hub"
            sound_system.play_sound('click')
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            for rect, school in self.school_buttons:
                if rect.collidepoint(mouse_pos):
                    if school["target_state"]:
                        self.next_state = school["target_state"]
                        sound_system.play_sound('click')
                    else:
                        sound_system.play_sound('error')
                    return

    def draw(self, screen):
        self.draw_themed_background(screen, mood="city")
        
        self.btn_back.check_hover(pygame.mouse.get_pos())
        self.btn_back.draw(screen)
        
        _t = font_title.render("MAGIC SCHOOLS OF VARRAKOR", True, GOLD_COLOR)
        self.draw_header_bar(screen, _t, y=10)
        draw_text("Select a Collegium to study spells", font_main, (200, 200, 200), screen, SCREEN_WIDTH // 2 - 180, 90)
        
        mouse_pos = pygame.mouse.get_pos()
        
        for rect, school in self.school_buttons:
            is_hover = rect.collidepoint(mouse_pos)
            
            # Taustaväri
            bg_col = (30, 30, 40)
            if is_hover: bg_col = (40, 40, 50)
            if not school["unlocked"]: bg_col = (20, 20, 25)
            
            border_col = school["color"] if school["unlocked"] else (60, 60, 60)
            if is_hover and school["unlocked"]:
                border_col = WHITE
            
            draw_panel(screen, rect.x, rect.y, rect.w, rect.h, color=bg_col, border_color=border_col)
            
            # Tekstit
            title_col = school["color"] if school["unlocked"] else GRAY
            draw_text(school["name"], font_main, title_col, screen, rect.x + 20, rect.y + 15)
            draw_text(f"[{school['type']}]", font_small, WHITE, screen, rect.x + 20, rect.y + 40)
            
            # Näytä maine (Reputation)
            if "rep_id" in school:
                rep_val = self.manager.get_faction_rep(school["rep_id"])
                draw_text(f"Rep: {rep_val}", font_small, GOLD_COLOR, screen, rect.x + 350, rect.y + 40)
            
            # Leader
            draw_text(f"Leader: {school['leader']}", font_small, (180, 180, 180), screen, rect.right - 350, rect.y + 15)
            
            # Desc
            desc_col = (200, 200, 200) if school["unlocked"] else (100, 100, 100)
            draw_text(school["desc"], font_small, desc_col, screen, rect.x + 20, rect.y + 70)
            
            # Status / Requirement
            if not school["unlocked"]:
                if school["target_state"]:
                    draw_text("TEST >", font_main, (140, 220, 160), screen, rect.right - 120, rect.centery - 10)
                else:
                    draw_text("LOCKED", font_main, RED, screen, rect.right - 120, rect.centery - 10)
                if "req_text" in school:
                    draw_text(school["req_text"], font_small, (200, 100, 100), screen, rect.right - 350, rect.y + 40)
            elif is_hover:
                draw_text("ENTER >", font_main, GOLD_COLOR, screen, rect.right - 120, rect.centery - 10)
