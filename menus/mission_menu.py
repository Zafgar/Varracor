import pygame
from settings import *
from ui_kit import UIButton, draw_panel, draw_text, font_title, font_main, font_small, GOLD_COLOR, WHITE, GRAY, GREEN, RED, format_money
from menus.base_menu import BaseMenu
from mission_data import MONSTER_HUNTS, BOSS_HUNTS
from sound_manager import sound_system

class MissionMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        
        cx = SCREEN_WIDTH // 2
        
        # Napit
        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)
        self.btn_start = UIButton(cx - 100, 750, 200, 60, "DEPLOY SQUAD", "sword", GREEN)
        
        self.selected_mission = None
        
        # Flatten missions list (Kerätään kaikki tehtävät yhteen listaan)
        self.missions = []
        
        # Region Tabs
        self.regions = ["Muckford", "Saffron Oasis", "Vinehollow"]
        self.selected_region = "Muckford"
        self.region_buttons = []
        self._init_region_buttons()
        
        self.last_mode = None
        self.refresh_missions()

    def _init_region_buttons(self):
        cx = SCREEN_WIDTH // 2
        start_x = cx - 300
        y = 100
        w = 200
        
        self.region_buttons = []
        for i, reg in enumerate(self.regions):
            btn = UIButton(start_x + i * w, y, w - 10, 40, reg, None, GRAY)
            self.region_buttons.append(btn)

    def refresh_missions(self):
        self.missions = []
        self.last_mode = self.manager.mode
        self.selected_mission = None
        
        if self.manager.mode == "Monster Hunt":
            # Haetaan tehtävät valitun alueen mukaan
            region_data = MONSTER_HUNTS.get(self.selected_region, [])
            for m in region_data:
                self.missions.append(m)
        else:
            # Boss Hunt (ei aluejakoa toistaiseksi)
            for m in BOSS_HUNTS.values():
                self.missions.append(m)

    def update(self):
        if self.manager.mode != self.last_mode:
            self.refresh_missions()
        super().update()

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_back.rect.collidepoint(mouse_pos):
                self.next_state = "hub"
                sound_system.play_sound('click')
                return

            # Region Tabs (Vain Monster Huntissa)
            if self.manager.mode == "Monster Hunt":
                for i, btn in enumerate(self.region_buttons):
                    if btn.rect.collidepoint(mouse_pos):
                        self.selected_region = self.regions[i]
                        self.refresh_missions()
                        sound_system.play_sound('click')
                        return

            # List selection
            cx = SCREEN_WIDTH // 2
            # Listan alku riippuu moodista (Boss Huntissa ei ole tabeja)
            list_start_y = 160 if self.manager.mode == "Monster Hunt" else 120
            
            for i, m in enumerate(self.missions):
                # Simple list layout
                rect = pygame.Rect(cx - 300, list_start_y + i * 80, 600, 70)
                if rect.collidepoint(mouse_pos):
                    self.selected_mission = m
                    sound_system.play_sound('click')

            # Start
            if self.selected_mission and self.btn_start.rect.collidepoint(mouse_pos):
                self.manager.selected_mission = self.selected_mission
                self.next_state = "mission_prepare"
                sound_system.play_sound('click')

    def draw(self, screen):
        screen.fill((15, 15, 20))
        self.draw_themed_background(screen, mood="quest")
        
        cx = SCREEN_WIDTH // 2
        
        header = "ACTIVE SWARMS" if self.manager.mode == "Monster Hunt" else "BOSS TARGETS"
        draw_text(header, font_title, GOLD_COLOR, screen, cx - 150, 30)
        
        mouse_pos = pygame.mouse.get_pos()
        self.btn_back.check_hover(mouse_pos); self.btn_back.draw(screen)
        
        # Draw Region Tabs (Vain Monster Hunt)
        list_y = 120
        if self.manager.mode == "Monster Hunt":
            list_y = 160
            for i, btn in enumerate(self.region_buttons):
                # Highlight selected
                btn.base_color = (100, 100, 150) if self.regions[i] == self.selected_region else (40, 40, 50)
                btn.check_hover(mouse_pos)
                btn.draw(screen)
        
        # List missions
        for m in self.missions:
            rect = pygame.Rect(cx - 300, list_y, 600, 70)
            is_sel = (self.selected_mission == m)
            
            # Style
            bg_col = (50, 50, 60) if is_sel else (30, 30, 40)
            if rect.collidepoint(mouse_pos): bg_col = (60, 60, 70)
            border_col = GOLD_COLOR if is_sel else (60, 60, 70)
            
            pygame.draw.rect(screen, bg_col, rect, border_radius=8)
            pygame.draw.rect(screen, border_col, rect, 2, border_radius=8)
            
            # Text
            draw_text(m['title'], font_main, WHITE, screen, rect.x + 20, rect.y + 15)
            
            # Location hint in list
            loc = m.get('arena', 'Unknown')
            draw_text(f"Loc: {loc}", font_small, (150, 150, 150), screen, rect.x + 20, rect.y + 40)
            
            # --- SHOW BEST WAVE IN LIST ---
            best_wave = 0
            arena_type = m.get('arena', '')
            is_wave_mission = arena_type in ["Muckford", "Crypt", "Bog"] or "Swarm" in m.get('title', '')

            if "Crypt" in arena_type:
                best_wave = getattr(self.manager, "crypt_best_wave", 0)
            elif "Bog" in arena_type:
                best_wave = getattr(self.manager, "bog_best_wave", 0)
            elif "Muckford" in arena_type:
                best_wave = getattr(self.manager, "muckford_best_wave", 0)
            
            if best_wave > 0:
                draw_text(f"Best: Wave {best_wave}", font_small, (100, 255, 100), screen, rect.x + 250, rect.y + 40)

            # Reward hint
            if is_wave_mission:
                draw_text("Scales w/ Waves", font_small, GOLD_COLOR, screen, rect.right - 140, rect.y + 25)
            else:
                rew = m.get('reward_gold', 0)
                draw_text(format_money(rew), font_main, GOLD_COLOR, screen, rect.right - 100, rect.y + 20)
            
            list_y += 80
            
        # Selected Details Panel
        if self.selected_mission:
            panel_y = 550
            draw_panel(screen, cx - 350, panel_y, 700, 180, color=(25, 25, 30), border_color=GOLD_COLOR)
            
            m = self.selected_mission
            
            # Title
            draw_text(m['title'].upper(), font_main, GOLD_COLOR, screen, cx - 330, panel_y + 20)
            
            # Description (What is happening)
            draw_text(f"SITUATION: {m['desc']}", font_small, WHITE, screen, cx - 330, panel_y + 50)
            
            # Location
            draw_text(f"LOCATION: {m.get('arena', 'Unknown Region')}", font_small, (100, 200, 255), screen, cx - 330, panel_y + 75)
            
            # Style/Theme (Derived from enemies or explicit field)
            enemies = m.get('enemies', [])
            enemy_names = [e[0] for e in enemies]
            theme_text = "Unknown Threat"
            if any("Skeleton" in n or "Zombie" in n or "Undead" in n for n in enemy_names):
                theme_text = "The Undead are rising from their graves."
            elif any("Rat" in n for n in enemy_names):
                theme_text = "Vermin swarm, spreading disease."
            elif any("Goblin" in n for n in enemy_names):
                theme_text = "Goblin raiders are gathering."
            elif any("Orc" in n for n in enemy_names):
                theme_text = "Orc warband spotted."
            
            draw_text(f"INTEL: {theme_text}", font_small, (255, 100, 100), screen, cx - 330, panel_y + 100)
            
            # --- SHOW BEST WAVE IN DETAILS ---
            best_wave = 0
            arena_type = m.get('arena', '')
            if "Crypt" in arena_type:
                best_wave = getattr(self.manager, "crypt_best_wave", 0)
            elif "Bog" in arena_type:
                best_wave = getattr(self.manager, "bog_best_wave", 0)
            elif "Muckford" in arena_type:
                best_wave = getattr(self.manager, "muckford_best_wave", 0)

            if best_wave > 0:
                draw_text(f"Best Wave: {best_wave}", font_main, (100, 255, 100), screen, cx + 150, panel_y + 20)
            
            self.btn_start.check_hover(mouse_pos)
            self.btn_start.draw(screen)