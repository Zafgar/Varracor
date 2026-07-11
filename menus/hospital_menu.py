import pygame
from settings import *
from ui_kit import UIButton, draw_panel, draw_text, font_title, font_main, font_small, format_money, GOLD_COLOR, WHITE, GRAY, RED, YELLOW, GREEN, BLACK
from menus.base_menu import BaseMenu
from sound_manager import sound_system

class HospitalMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        # Back-nappi (30, 30) koordinaateissa, koko 120x50
        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)
        self.btn_heal_all = UIButton(SCREEN_WIDTH - 360, 20, 200, 40, "HEAL ALL (50 SP)", "heart", WHITE, GREEN)

    def handle_event(self, event):
        # --- TAPA 1: UI Kitin oma tarkistus ---
        if self.btn_back.is_clicked(event): 
            print("BACK BUTTON CLICKED (UI Kit)") # Debuggaus
            self.next_state = "hub"
            return 

        if self.btn_heal_all.is_clicked(event): 
            self.manager.heal_team()
        
        # --- TAPA 2: Suora hiiren kuuntelu (Varmistus) ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # 1. FORCE BACK: Tarkistetaan suoraan osuuko hiiri Back-nappiin
            # Napin koordinaatit: x=30, y=30, w=120, h=50
            back_rect = pygame.Rect(30, 30, 120, 50)
            
            if back_rect.collidepoint(mouse_pos):
                print("BACK BUTTON CLICKED (Direct Check)") # Debuggaus
                self.next_state = "hub"
                sound_system.play_sound('click') # Valinnainen ääni
                return # Poistutaan heti, ettei tehdä muuta

            # 2. Muu logiikka (koulutus ja parannus)
            char_y = 150
            for u in self.manager.my_team:
                cost = getattr(u, 'upgrade_cost', 100)
                cx = SCREEN_WIDTH // 2
                
                # Rects
                btn_str = pygame.Rect(cx - 50,  char_y + 10, 60, 40)
                btn_dex = pygame.Rect(cx + 20,  char_y + 10, 60, 40)
                btn_int = pygame.Rect(cx + 90,  char_y + 10, 60, 40)
                btn_heal= pygame.Rect(cx + 200, char_y + 10, 100, 40)
                
                # Logic - Kutsutaan train_unit
                clicked_stat = None
                if btn_str.collidepoint(mouse_pos): clicked_stat = 'str'
                elif btn_dex.collidepoint(mouse_pos): clicked_stat = 'dex'
                elif btn_int.collidepoint(mouse_pos): clicked_stat = 'int'
                
                if clicked_stat:
                    if self.manager.train_unit(u, clicked_stat):
                        sound_system.play_sound('recruit')
                    else:
                        sound_system.play_sound('error')

                # Heal logic
                if btn_heal.collidepoint(mouse_pos):
                    if self.manager.gold >= 10 and u.current_hp < u.max_hp:
                        self.manager.gold -= 10
                        u.heal(50)
                        sound_system.play_sound('heal')
                    else:
                        sound_system.play_sound('error')

                char_y += 80

    def draw(self, screen):
        screen.fill((15, 15, 20))
        self.btn_back.draw(screen)
        self.btn_heal_all.draw(screen)
        draw_text("SAINT LUMEN FIELD HOSPICE", font_title, WHITE, screen, 400, 50)
        draw_text("Sister-Medic Rhea Ashford - \"Arena wounds heal. Vortex taint gets quarantined.\"",
                  font_small, GRAY, screen, 400, 88)
        draw_text(f"Funds: {format_money(self.manager.gold)}", font_title, GOLD_COLOR, screen, 20, 100)
        
        char_y = 150
        for u in self.manager.my_team:
            cost = getattr(u, 'upgrade_cost', 100)
            level = getattr(u, 'level', 1) 
            
            # Taustapaneeli
            draw_panel(screen, 100, char_y, 900, 70)
            
            # Unit Info
            draw_text(f"{u.name}", font_main, WHITE, screen, 120, char_y + 10)
            draw_text(f"Lvl {level} {u.race_name}", font_small, GRAY, screen, 120, char_y + 40)
            
            # Stats
            draw_text(f"STR: {int(u.strength)}", font_small, RED, screen, 280, char_y + 15)
            draw_text(f"DEX: {int(u.dexterity)}", font_small, YELLOW, screen, 280, char_y + 30)
            draw_text(f"INT: {int(u.intelligence)}", font_small, (100,100,255), screen, 280, char_y + 45)
            
            # HP Bar
            hp_pct = u.current_hp / u.max_hp
            pygame.draw.rect(screen, (50,0,0), (350, char_y+25, 100, 10))
            pygame.draw.rect(screen, GREEN, (350, char_y+25, 100*hp_pct, 10))
            draw_text(f"{int(u.current_hp)}/{int(u.max_hp)}", font_small, WHITE, screen, 350, char_y+40)

            # Training Buttons
            cx = SCREEN_WIDTH // 2
            can_train = self.manager.gold >= cost
            bg_col = (60, 60, 70) if can_train else (40, 20, 20)
            
            # Napit
            pygame.draw.rect(screen, bg_col, (cx - 50, char_y + 10, 60, 40), border_radius=5)
            draw_text("+STR", font_small, RED, screen, cx - 45, char_y + 20)

            pygame.draw.rect(screen, bg_col, (cx + 20, char_y + 10, 60, 40), border_radius=5)
            draw_text("+DEX", font_small, YELLOW, screen, cx + 25, char_y + 20)

            pygame.draw.rect(screen, bg_col, (cx + 90, char_y + 10, 60, 40), border_radius=5)
            draw_text("+INT", font_small, (100,150,255), screen, cx + 95, char_y + 20)
            
            # Hinta
            price_col = GOLD_COLOR if can_train else RED
            draw_text(format_money(cost), font_small, price_col, screen, cx + 30, char_y + 55)

            # Heal Button
            heal_col = GREEN if self.manager.gold >= 10 and u.current_hp < u.max_hp else GRAY
            pygame.draw.rect(screen, heal_col, (cx + 200, char_y + 10, 100, 40), border_radius=5)
            draw_text("HEAL 10 SP", font_small, BLACK, screen, cx + 215, char_y + 20)
            
            char_y += 80