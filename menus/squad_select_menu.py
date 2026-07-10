import pygame
from settings import *
from ui_kit import UIButton, draw_text, draw_panel, font_title, font_main, font_small, WHITE, GOLD_COLOR, RED, GREEN

class SquadSelectMenu:
    def __init__(self, manager, mission_id):
        self.manager = manager
        self.mission_id = mission_id
        self.next_state = None
        
        self.selected_units = [] # Lista valituista yksiköistä
        self.max_units = 10 # Raja
        
        # UI
        self.close_btn = UIButton(SCREEN_WIDTH - 150, 30, 120, 40, "CANCEL", color=(150, 50, 50))
        self.fight_btn = UIButton(SCREEN_WIDTH - 220, SCREEN_HEIGHT - 80, 180, 60, "START FIGHT", color=(50, 150, 50))
        
        # Automaattisesti valitse 3 ensimmäistä (tai kaikki jos alle 3)
        available = []
        if self.manager.player_character: available.append(self.manager.player_character)
        available.extend(list(self.manager.my_team))
        self.selected_units = available[:min(len(available), 3)]

    def update(self):
        mx, my = pygame.mouse.get_pos()
        self.close_btn.check_hover((mx, my))
        self.fight_btn.check_hover((mx, my))
        return self.next_state

    def handle_event(self, event):
        if self.close_btn.is_clicked(event):
            self.next_state = "quests" # Palaa takaisin tehtävälistaan
            return

        if self.fight_btn.is_clicked(event):
            if len(self.selected_units) > 0:
                print(f"Squad confirmed: {len(self.selected_units)} heroes.")
                # Käynnistä taistelu valituilla yksiköillä!
                if self.manager.start_boss_hunt(self.mission_id, self.selected_units):
                    self.next_state = "battle"
            else:
                print("Select at least one hero!")
            return

        # Yksiköiden valinta klikkaamalla
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            
            # Listan layout
            start_x = 50
            start_y = 120
            item_h = 90
            
            roster = []
            if self.manager.player_character: roster.append(self.manager.player_character)
            roster.extend(list(self.manager.my_team))
            for i, unit in enumerate(roster):
                rect = pygame.Rect(start_x, start_y + i * (item_h + 10), 700, item_h)
                
                if rect.collidepoint((mx, my)):
                    if unit in self.selected_units:
                        self.selected_units.remove(unit) # Poista valinta
                    else:
                        if len(self.selected_units) < self.max_units:
                            self.selected_units.append(unit) # Valitse
    
    def draw(self, screen):
        # Tumma overlay tausta
        from ui_kit import get_fullscreen_overlay
        screen.blit(get_fullscreen_overlay((10, 10, 15, 245)), (0, 0))
        
        draw_text(f"PREPARE SQUAD", font_title, GOLD_COLOR, screen, 50, 40)
        draw_text(f"Selected: {len(self.selected_units)} / {self.max_units}", font_main, WHITE, screen, 300, 50)
        
        # Napit
        self.close_btn.draw(screen)
        self.fight_btn.draw(screen)
        
        # Piirrä lista
        start_x = 50
        start_y = 120
        item_h = 90
        
        roster = []
        if self.manager.player_character: roster.append(self.manager.player_character)
        roster.extend(list(self.manager.my_team))
        for i, unit in enumerate(roster):
            bx = start_x
            by = start_y + i * (item_h + 10)
            
            is_selected = unit in self.selected_units
            
            # Värit
            bg_col = (40, 60, 40) if is_selected else (30, 30, 35)
            border_col = GREEN if is_selected else (60, 60, 60)
            
            draw_panel(screen, bx, by, 700, item_h, color=bg_col, border_color=border_col)
            
            # 1. Nimi ja Level
            draw_text(f"{unit.name}", font_main, WHITE, screen, bx + 20, by + 10)
            draw_text(f"Lvl {getattr(unit, 'level', 1)} {getattr(unit, 'race_name', '')}", font_small, GOLD_COLOR, screen, bx + 20, by + 35)
            
            # 2. Attribuutit (STR, DEX, INT)
            stats_y = by + 60
            s_str = int(getattr(unit, "strength", 0))
            s_dex = int(getattr(unit, "dexterity", 0))
            s_int = int(getattr(unit, "intelligence", 0))
            
            draw_text(f"STR: {s_str}", font_small, (255, 100, 100), screen, bx + 20, stats_y)
            draw_text(f"DEX: {s_dex}", font_small, (100, 255, 100), screen, bx + 100, stats_y)
            draw_text(f"INT: {s_int}", font_small, (100, 100, 255), screen, bx + 180, stats_y)
            
            # 3. Varusteet (Main Hand & Spell)
            # Haetaan varusteet turvallisesti
            equip = getattr(unit, "equipment", {})
            wep = equip.get("main_hand")
            wep_name = wep.name if wep else "Fists"
            
            spell = equip.get("spell1")
            spell_name = spell.name if spell else "None"
            
            draw_text(f"Weapon: {wep_name}", font_small, (200, 200, 200), screen, bx + 350, by + 20)
            draw_text(f"Spell: {spell_name}", font_small, (150, 150, 255), screen, bx + 350, by + 45)
            
            # Valinta-merkki
            if is_selected:
                draw_text("DEPLOY", font_main, GREEN, screen, bx + 580, by + 30)