import pygame
import random
from settings import *
from ui_kit import UIButton, draw_text, font_title, font_main, WHITE, GREEN, RED, GOLD_COLOR, draw_panel, font_small
from menus.gameplay_screen import GameplayScreen
from sound_manager import sound_system

class BattleScreen(GameplayScreen):
    def __init__(self, manager):
        super().__init__(manager)
        # Nappi pelin pysäyttämiseen
        self.btn_pause = UIButton(SCREEN_WIDTH - 120, 20, 100, 40, "PAUSE", None, (100, 100, 100))
        # Nappi pakenemiseen (vain Monster Huntissa)
        self.btn_run = UIButton(SCREEN_WIDTH - 120, 70, 100, 40, "RUN", None, (200, 60, 60))
        self.show_loot = False

    def handle_event(self, event):
        # 1. Pause-nappi
        if self.btn_pause.is_clicked(event):
            self.manager.paused = not self.manager.paused
            self.btn_pause.text = "RESUME" if self.manager.paused else "PAUSE"

        # 2. Run-nappi (Vain jos Monster Hunt on käynnissä)
        if self.manager.mode == "Monster Hunt":
            if self.btn_run.is_clicked(event):
                # KORJATTU: Käytetään current_mission_logic -muuttujaa
                if hasattr(self.manager, "current_mission_logic") and hasattr(self.manager.current_mission_logic, "retreat"):
                    self.manager.current_mission_logic.retreat()
        
        # 3. Kameran lukitus (L-näppäin)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_l:
                self.manager.camera_locked = not self.manager.camera_locked

            if event.key == pygame.K_p and CHEAT_MODE:
                self.manager.world_paused = not self.manager.world_paused

            # 4. Loot Popup (I-näppäin)
            if event.key == pygame.K_i:
                self.show_loot = not self.show_loot

        # 2. Jos matsi on ohi, klikkaus vie raporttiin
        if self.manager.match_over:
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                
                # --- AUDIO STOP (LISÄTTY) ---
                # Kun pelaaja klikkaa "Click to continue", pysäytetään meteli.
                print("Leaving Battle: Stopping all audio.")
                pygame.mixer.stop()       # Pysäyttää efektit ja ambientin
                sound_system.stop_music() # Pysäyttää musiikin ja nollaa tilan
                # ----------------------------
                
                # Jos Monster Hunt (Swarm), mennään uuteen Swarm-valikkoon
                if self.manager.mode == "Monster Hunt":
                    self.next_state = "swarm_report"
                else:
                    self.next_state = "battle_report" 

    def update(self):
        # Jos ei ole pausella ja peli on käynnissä, päivitetään manageria
        if not self.manager.paused and not self.manager.match_over:
            self.manager.update_match()

    def draw(self, screen):
        # 1. Piirretään koko pelitilanne Managerin kautta
        # (Tämä piirtää areenan, hahmot JA VFX:n)
        self.manager.draw_game(screen)

        # 1.6 Loot Popup (jos auki)
        if self.show_loot:
            self.draw_loot_popup(screen)

        # 2. UI Overlay (Napit jne.)
        self.btn_pause.draw(screen)
        
        # Piirrä RUN-nappi vain Monster Huntissa
        if self.manager.mode == "Monster Hunt":
            self.btn_run.draw(screen)

        # 3. Wave Announcement (Värisevä teksti)
        # KORJATTU: Käytetään current_mission_logic -muuttujaa
        if hasattr(self.manager, "current_mission_logic"):
            eng = self.manager.current_mission_logic
            if hasattr(eng, "announcement_timer") and eng.announcement_timer > 0:
                # Lasketaan tärinä
                shake_amt = 4
                off_x = random.randint(-shake_amt, shake_amt)
                off_y = random.randint(-shake_amt, shake_amt)
                
                text = eng.announcement_text
                # Piirretään keskelle ruutua isolla
                # Käytetään punaista/oranssia väriä
                draw_text(text, font_title, (255, 100, 50), screen, (SCREEN_WIDTH // 2 - 100) + off_x, (SCREEN_HEIGHT // 2 - 100) + off_y)

        # 3. Victory/Defeat Overlay
        # Piirretään tämä vain kun taistelu on ohi
        if self.manager.match_over:
            # Tumma tausta
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0,0))

            # Tekstit
            res_text = self.manager.match_result # "VICTORY" tai "DEFEAT"
            res_color = GREEN if res_text == "VICTORY" else RED
            
            draw_text(res_text, font_title, res_color, screen, SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 50)
            draw_text("Click to continue...", font_main, WHITE, screen, SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 20)

    def draw_loot_popup(self, screen):
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        w, h = 400, 500
        
        # Taustapaneeli
        draw_panel(screen, cx - w//2, cy - h//2, w, h, (30, 30, 35), (100, 100, 100))
        
        # Otsikko
        draw_text("CURRENT LOOT", font_title, GOLD_COLOR, screen, cx - 110, cy - h//2 + 30)
        
        # Loot lista
        loot = self.manager.round_rewards.get('loot', {})
        
        if not loot:
            draw_text("No loot collected yet.", font_main, (150, 150, 150), screen, cx - 90, cy)
        else:
            start_y = cy - h//2 + 100
            for i, (name, count) in enumerate(loot.items()):
                # Estä ylivuoto jos tavaraa on paljon
                if start_y + i * 30 > cy + h//2 - 50:
                    draw_text("... and more ...", font_small, (150, 150, 150), screen, cx - 50, start_y + i * 30)
                    break
                
                draw_text(f"{name}: {count}", font_main, WHITE, screen, cx - w//2 + 40, start_y + i * 30)
        
        draw_text("Press 'I' to close", font_small, (150, 150, 150), screen, cx - 60, cy + h//2 - 30)

    def draw_player_hud(self, screen):
        pc = self.manager.player_character
        if not pc or pc.is_dead or pc not in self.manager.active_player_units:
            return

        # --- HUD CONFIG ---
        bar_w = 300
        bar_h = 16
        slot_size = 50
        gap = 10
        
        cx = SCREEN_WIDTH // 2
        base_y = SCREEN_HEIGHT - 80

        # --- 1. HP & MANA BARS ---
        # HP (Red)
        hp_pct = max(0, pc.current_hp / pc.max_hp)
        hp_rect_bg = pygame.Rect(cx - bar_w - 10, base_y, bar_w, bar_h)
        hp_rect_fill = pygame.Rect(cx - bar_w - 10, base_y, int(bar_w * hp_pct), bar_h)
        
        pygame.draw.rect(screen, (60, 20, 20), hp_rect_bg, border_radius=4)
        pygame.draw.rect(screen, (200, 50, 50), hp_rect_fill, border_radius=4)
        pygame.draw.rect(screen, (30, 10, 10), hp_rect_bg, 2, border_radius=4)
        
        hp_text = f"{int(pc.current_hp)} / {int(pc.max_hp)}"
        draw_text(hp_text, font_small, WHITE, screen, hp_rect_bg.centerx - 30, hp_rect_bg.y - 2)

        # Mana (Blue)
        mana_pct = max(0, pc.current_mana / max(1, pc.max_mana))
        mana_rect_bg = pygame.Rect(cx + 10, base_y, bar_w, bar_h)
        mana_rect_fill = pygame.Rect(cx + 10, base_y, int(bar_w * mana_pct), bar_h)
        
        pygame.draw.rect(screen, (20, 20, 60), mana_rect_bg, border_radius=4)
        pygame.draw.rect(screen, (50, 100, 220), mana_rect_fill, border_radius=4)
        pygame.draw.rect(screen, (10, 10, 30), mana_rect_bg, 2, border_radius=4)
        
        mana_text = f"{int(pc.current_mana)} / {int(pc.max_mana)}"
        draw_text(mana_text, font_small, WHITE, screen, mana_rect_bg.centerx - 30, mana_rect_bg.y - 2)

        # --- 2. HOTBAR SLOTS (1-5) ---
        slots_y = base_y + 25
        total_w = 5 * slot_size + 4 * gap
        start_x = cx - total_w // 2
        
        slot_keys = ["spell1", "spell2", "spell3", "usable", None] # 5th slot empty/reserved
        
        for i in range(5):
            sx = start_x + i * (slot_size + gap)
            rect = pygame.Rect(sx, slots_y, slot_size, slot_size)
            
            # Background
            pygame.draw.rect(screen, (40, 40, 50), rect, border_radius=4)
            pygame.draw.rect(screen, (100, 100, 100), rect, 2, border_radius=4)
            
            # Number
            draw_text(str(i + 1), font_small, GOLD_COLOR, screen, sx + 2, slots_y + 2)
            
            # Item Icon
            key = slot_keys[i]
            if key:
                item = pc.equipment.get(key)
                if item and hasattr(item, "draw_card_icon"):
                    item.draw_card_icon(screen, sx + 4, slots_y + 4, slot_size - 8)