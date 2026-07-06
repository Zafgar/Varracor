import pygame
import os
from settings import *
from menus.base_menu import BaseMenu
from ui_kit import SpriteButton, draw_text, font_title, font_main, font_small, GOLD_COLOR, WHITE, GREEN, RED, format_money
from sound_manager import sound_system

# HUOM: Emme tuo QuestMenua tähän enää.

class TownHub(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        
        # 1. Taustakuva
        self.bg_image = None
        bg_path = "assets/images/hub_background.png"
        if os.path.exists(bg_path):
            try:
                raw = pygame.image.load(bg_path).convert()
                self.bg_image = pygame.transform.smoothscale(raw, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except: pass

        # --- NAPPIEN ASETTELU ---
        center_x = SCREEN_WIDTH // 2
        btn_w_large = 300
        btn_w_med = 280

        # RIVI 1
        y_row1 = 160
        gap_r1 = 350
        
        self.btn_league = SpriteButton(
            x=center_x - gap_r1, y=y_row1,
            img_idle="assets/ui/btn_league_idle.png", img_hover="assets/ui/btn_league_hover.png", img_pressed="assets/ui/btn_league_pressed.png",
            label_text="LEAGUE HALL", target_width=btn_w_large
        )
        self.btn_manager = SpriteButton(
            x=center_x, y=y_row1,
            img_idle="assets/ui/btn_manager_idle.png", img_hover="assets/ui/btn_manager_hover.png", img_pressed="assets/ui/btn_manager_pressed.png",
            label_text="MANAGER", target_width=btn_w_large
        )
        self.btn_guild = SpriteButton(
            x=center_x + gap_r1, y=y_row1,
            img_idle="assets/ui/btn_guild_idle.png", img_hover="assets/ui/btn_guild_hover.png", img_pressed="assets/ui/btn_guild_pressed.png",
            label_text="GUILD HOUSE", target_width=btn_w_large
        )

        # RIVI 2
        y_row2 = 340
        spread_r2 = 320 
        start_x_r2 = center_x - (spread_r2 * 1.5) 

        self.btn_shop = SpriteButton(
            x=start_x_r2, y=y_row2,
            img_idle="assets/ui/btn_shop_idle.png", img_hover="assets/ui/btn_shop_hover.png", img_pressed="assets/ui/btn_shop_pressed.png",
            label_text="BLACKSMITH", target_width=btn_w_med
        )
        self.btn_workshop = SpriteButton(
            x=start_x_r2 + spread_r2, y=y_row2,
            img_idle="assets/ui/btn_workshop_idle.png", img_hover="assets/ui/btn_workshop_hover.png", img_pressed="assets/ui/btn_workshop_pressed.png",
            label_text="WORKSHOP", target_width=btn_w_med
        )
        self.btn_hospital = SpriteButton(
            x=start_x_r2 + (spread_r2 * 2), y=y_row2,
            img_idle="assets/ui/btn_hospital_idle.png", img_hover="assets/ui/btn_hospital_hover.png", img_pressed="assets/ui/btn_hospital_pressed.png",
            label_text="TEMPLE", target_width=btn_w_med
        )
        self.btn_mage = SpriteButton(
            x=start_x_r2 + (spread_r2 * 3), y=y_row2,
            img_idle="assets/ui/btn_mage_idle.png", img_hover="assets/ui/btn_mage_hover.png", img_pressed="assets/ui/btn_mage_pressed.png",
            label_text="MAGE TOWER", target_width=btn_w_med
        )

        # RIVI 3
        y_row3 = 520
        gap_r3 = 350
        
        self.btn_recruit = SpriteButton(
            x=center_x - gap_r3, y=y_row3,
            img_idle="assets/ui/btn_recruit_idle.png", img_hover="assets/ui/btn_recruit_hover.png", img_pressed="assets/ui/btn_recruit_pressed.png",
            label_text="BARRACKS", target_width=btn_w_large
        )
        self.btn_hunt = SpriteButton(
            x=center_x, y=y_row3,
            img_idle="assets/ui/btn_hunt_idle.png", img_hover="assets/ui/btn_hunt_hover.png", img_pressed="assets/ui/btn_hunt_pressed.png",
            label_text="MONSTER HUNT", target_width=btn_w_large
        )
        
        # BOSS CONTRACTS NAPPI
        self.btn_contracts = SpriteButton(
            x=center_x + gap_r3, y=y_row3,
            img_idle="assets/ui/btn_boss_idle.png", 
            img_hover="assets/ui/btn_boss_hover.png",
            img_pressed="assets/ui/btn_boss_pressed.png",
            label_text="BOSS CONTRACTS", target_width=btn_w_large
        )

        # SYSTEM
        self.btn_exit = SpriteButton(
            x=SCREEN_WIDTH - 120, y=50,
            img_idle="assets/ui/btn_exit_idle.png", img_hover="assets/ui/btn_exit_hover.png", img_pressed="assets/ui/btn_exit_pressed.png",
            label_text="EXIT", target_width=180
        )

        self.buttons = [
            self.btn_league, self.btn_manager, self.btn_guild,
            self.btn_shop, self.btn_workshop, self.btn_hospital, self.btn_mage,
            self.btn_recruit, self.btn_hunt, self.btn_contracts,
            self.btn_exit
        ]
        
        self._league_bar_width = 200
        self._league_bar_height = 8

    def check_music(self):
        # Käytetään sound_systemiä, joka osaa vaihtaa biisin vain jos se on eri
        sound_system.play_music("assets/music/town_hub.wav", loops=-1)

    def update(self):
        # 0. MUSIIKKI
        self.check_music()

        # 1. LIIGAN SIMULAATIO
        if hasattr(self.manager, "league_engine") and self.manager.league_engine:
            try:
                self.manager.league_engine.tick_simulation(budget_ms=4.0, max_matches=2)
            except Exception: pass
        
        # 2. NAPPIEN LOGIIKKA
        if self.btn_league.update(): self.next_state = "dialogue:dwarf_league_manager"
        if self.btn_manager.update(): self.next_state = "manager_menu"
        if self.btn_guild.update(): self.next_state = "guild"
        if self.btn_shop.update(): self.next_state = "shop_locations"
        if self.btn_workshop.update(): self.next_state = "workshop_locations"
        if self.btn_hospital.update(): self.next_state = "hospital"
        if self.btn_mage.update(): self.next_state = "magic_school"
        if self.btn_recruit.update(): self.next_state = "recruit"
        
        if self.btn_hunt.update():
            self.manager.mode = "Monster Hunt"
            self.next_state = "mission_select" 

        if self.btn_contracts.update():
            self.next_state = "quests" 

        if self.btn_exit.update():
            self.next_state = "menu"

    def handle_event(self, event):
        super().handle_event(event)

    def draw(self, screen):
        # 1. Tausta
        if self.bg_image:
            screen.blit(self.bg_image, (0, 0))
        else:
            self.draw_themed_background(screen, mood="city")
            draw_text("CITY HUB", font_title, GOLD_COLOR, screen, 50, 50)
            
            money = self.manager.gold
            rep = self.manager.reputation
            info = f"Money: {format_money(money)}  |  Reputation: {rep}"
            draw_text(info, font_main, (200, 200, 200), screen, 50, 100)

        # 2. Napit
        for btn in self.buttons:
            btn.draw(screen)

        # 3. Simulaatio palkki
        if hasattr(self.manager, "league_engine") and self.manager.league_engine:
            le = self.manager.league_engine
            pct = getattr(le, "simulation_progress", 1.0)
            if pct < 1.0:
                bar_w, bar_h = self._league_bar_width, self._league_bar_height
                bar_x = self.btn_league.base_x - (bar_w // 2)
                bar_y = self.btn_league.base_y + 50 
                pygame.draw.rect(screen, (40, 40, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
                fill_w = int(bar_w * pct)
                pygame.draw.rect(screen, (100, 200, 255), (bar_x, bar_y, fill_w, bar_h), border_radius=4)
                draw_text("Simulating...", font_small, (180, 180, 180), screen, bar_x, bar_y - 15)

        # 4. Roster palkki alhaalla
        ry = SCREEN_HEIGHT - 120
        overlay = pygame.Surface((SCREEN_WIDTH, 120))
        overlay.fill((20, 20, 30))
        overlay.set_alpha(200) 
        screen.blit(overlay, (0, ry))

        sx = 50
        for u in self.manager.my_team:
            r_rect = pygame.Rect(sx, ry + 10, 80, 100)
            bg = (60, 60, 70) if u.current_hp > 0 else (60, 20, 20)
            pygame.draw.rect(screen, bg, r_rect, border_radius=5)
            pygame.draw.rect(screen, (100, 100, 100), r_rect, 1, border_radius=5)

            if hasattr(u, 'image') and u.image:
                sc = pygame.transform.scale(u.image, (32, 48))
                screen.blit(sc, (sx + 24, ry + 20))
            elif hasattr(u, 'draw_procedural'):
                u.draw_procedural()

            hp_pct = max(0, u.current_hp / u.max_hp)
            bar_color = GREEN if hp_pct > 0.5 else RED
            pygame.draw.rect(screen, (30,30,30), (sx + 5, ry + 80, 70, 5)) 
            pygame.draw.rect(screen, bar_color, (sx + 5, ry + 80, 70 * hp_pct, 5))
            draw_text(u.name[:8], font_small, WHITE, screen, sx + 5, ry + 90)
            sx += 90