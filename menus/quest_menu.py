import pygame
from settings import *
from ui_kit import draw_panel, draw_text, font_main, font_small, font_title, UIButton
from quest_system import quest_manager
from menus.chat_menu import ChatMenu 

class QuestMenu:
    def __init__(self, game_manager):
        self.gm = game_manager
        self.next_state = None
        
        # --- TAB SYSTEM ---
        self.current_tab = "active" # "active" tai "completed"
        
        # UI asettelu
        self.list_x = 50
        self.list_y = 180 
        self.item_h = 70
        
        # Napit
        self.close_btn = UIButton(SCREEN_WIDTH - 150, 20, 130, 40, "Back to Hub", color=(200, 60, 60))
        
        # Tab-napit
        self.btn_tab_active = UIButton(50, 120, 150, 40, "Open Contracts", color=(50, 150, 50))
        self.btn_tab_completed = UIButton(210, 120, 150, 40, "Archive", color=(80, 80, 100))
        
        # CHAT INTEGRAATIO
        self.chat_overlay = None 

    def update(self):
        # 1. Chat overlay
        if self.chat_overlay:
            self.chat_overlay.update()
            if self.chat_overlay.next_state: 
                self.chat_overlay = None 
            return self.next_state

        # 2. TRIGGER CHECKS (Automaattiset keskustelut)
        npc_data = self.gm.npc_state.get("griznak_quest_giver", {})
        flags = npc_data.get("flags", {})
        
        # A) Intro: Jos pelaaja ei ole tavannut Griznakia -> Avaa chat
        if not flags.get("intro_done", False) and self.chat_overlay is None:
            self.chat_overlay = self.gm.open_dialogue("griznak_quest_giver")
            return

        # B) Reaktio: Jos taistelu päättyi ja Griznakilla on kommentoitavaa -> Avaa chat
        # (Tämä rivi varmistaa, että onnittelut/haukkumiset tulevat heti)
        if quest_manager.pending_reaction and self.chat_overlay is None:
            self.chat_overlay = self.gm.open_dialogue("griznak_quest_giver")
            return

        # 3. Päivitykset
        # Varmistetaan että unlockit tarkistetaan
        quest_manager.check_unlocks()
        
        mx, my = pygame.mouse.get_pos()
        self.close_btn.check_hover((mx, my))
        self.btn_tab_active.check_hover((mx, my))
        self.btn_tab_completed.check_hover((mx, my))
        
        return self.next_state

    def handle_event(self, event):
        if self.chat_overlay:
            self.chat_overlay.handle_event(event)
            return

        if self.close_btn.is_clicked(event):
            self.next_state = "hub"
            return

        # Tabien vaihto
        if self.btn_tab_active.is_clicked(event):
            self.current_tab = "active"
        if self.btn_tab_completed.is_clicked(event):
            self.current_tab = "completed"

        # Listan klikkaukset (Vain jos ollaan Active-tabissa)
        if self.current_tab == "active":
            mx, my = pygame.mouse.get_pos()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                
                # --- KORJAUS 1: Lisätty .values(), jotta saadaan oliot eikä avaimia ---
                visible_quests = [q for q in quest_manager.quests.values() if not q.completed]
                
                for i, q in enumerate(visible_quests):
                    rect = pygame.Rect(self.list_x, self.list_y + i * (self.item_h + 10), 600, self.item_h)
                    if rect.collidepoint((mx, my)):
                        if q.unlocked:
                            print(f"Selecting squad for: {q.title}")
                            self.next_state = f"squad_select:{q.boss_id}" 

    def draw(self, surface):
        # 1. Tausta
        surface.fill((20, 20, 25)) 
        
        # Koristeita
        draw_text("Griznak's Contracts", font_title, GOLD_COLOR, surface, 50, 30)
        
        # Griznakin kommentti
        dialogue = quest_manager.get_goblin_dialogue()
        draw_panel(surface, SCREEN_WIDTH - 450, 80, 280, 80, color=(40, 40, 50), border_color=GOLD_COLOR)
        draw_text(f'"{dialogue}"', font_small, (200, 200, 200), surface, SCREEN_WIDTH - 430, 95)
        
        draw_text(f"Reputation: {quest_manager.reputation}", font_main, (100, 255, 100), surface, SCREEN_WIDTH - 250, 180)

        # 2. Napit (Tabit ja Close)
        if self.current_tab == "active":
            self.btn_tab_active.color = (50, 200, 50)
            self.btn_tab_completed.color = (60, 60, 80)
        else:
            self.btn_tab_active.color = (40, 80, 40)
            self.btn_tab_completed.color = (100, 100, 200)

        self.btn_tab_active.draw(surface)
        self.btn_tab_completed.draw(surface)
        self.close_btn.draw(surface)

        # 3. Quest Lista
        # --- KORJAUS 2: Lisätty .values() ---
        if self.current_tab == "active":
            visible_quests = [q for q in quest_manager.quests.values() if not q.completed]
            if not visible_quests:
                draw_text("No available contracts right now.", font_main, (150, 150, 150), surface, self.list_x, self.list_y)
        else:
            # --- KORJAUS 3: Lisätty .values() ---
            visible_quests = [q for q in quest_manager.quests.values() if q.completed]
            if not visible_quests:
                draw_text("No completed contracts yet.", font_main, (150, 150, 150), surface, self.list_x, self.list_y)

        # Piirrä lista
        for i, q in enumerate(visible_quests):
            bx = self.list_x
            by = self.list_y + i * (self.item_h + 10)
            bw = 600
            bh = self.item_h
            
            if q.completed:
                bg_col, border_col = (30, 40, 30), (50, 100, 50)
                status_txt, status_col = "DONE", (100, 255, 100)
            elif q.unlocked:
                bg_col, border_col = (40, 40, 50), (100, 100, 120)
                mx, my = pygame.mouse.get_pos()
                if self.current_tab == "active" and not self.chat_overlay and pygame.Rect(bx, by, bw, bh).collidepoint((mx, my)):
                    bg_col, border_col = (50, 50, 70), GOLD_COLOR
                status_txt, status_col = "AVAILABLE", GOLD_COLOR
            else:
                bg_col, border_col = (20, 20, 25), (50, 50, 50)
                status_txt, status_col = f"LOCKED (Req: {q.rep_req} Rep)", (150, 50, 50)

            draw_panel(surface, bx, by, bw, bh, color=bg_col, border_color=border_col)
            draw_text(q.title, font_main, (255, 255, 255) if q.unlocked else (100, 100, 100), surface, bx + 20, by + 10)
            draw_text(q.description, font_small, (180, 180, 180) if q.unlocked else (80, 80, 80), surface, bx + 20, by + 35)
            
            draw_text(status_txt, font_main, status_col, surface, bx + 450, by + 10)
            
            if q.unlocked or q.completed:
                draw_text(f"Reward: {q.reward_text}", font_small, GOLD_COLOR, surface, bx + 450, by + 40)

        # 4. Chat Overlay
        if self.chat_overlay:
            self.chat_overlay.draw(surface)