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

    def _draw_sponsor_flags(self, screen):
        """Sponsorilippu kummankin joukkueen päädyssä (pelitesti 18).
        Pelaajan pääty (vasen) liehuttaa allekirjoitetun sponsorin väriä
        ja nimeä; vastustajan pääty saa tiiminsä väristä viiriä."""
        m = self.manager
        if m.mode != "League" or not m.current_arena:
            return
        import math as _math
        arena = m.current_arena
        w = getattr(arena, "width", SCREEN_WIDTH)
        h = getattr(arena, "height", SCREEN_HEIGHT)
        ox, oy = int(m.camera_x), int(m.camera_y)
        t = pygame.time.get_ticks() * 0.004

        # Pelaajan sponsori
        p_name, p_col = "UNSPONSORED", (120, 120, 128)
        sp_id = getattr(m, "tier0_sponsor", None)
        if sp_id:
            try:
                from sponsors.sponsor_data import SPONSORS
                data = SPONSORS.get(sp_id)
                if data:
                    p_name, p_col = data["name"], data["color"]
            except Exception:
                pass
        # Vastustajan viiri: väri tiimin nimestä
        e_team = getattr(m, "current_enemy_team", None)
        e_name = getattr(e_team, "name", "Rivals")
        seed = sum(ord(c) for c in e_name)
        e_col = (90 + seed * 7 % 130, 70 + seed * 13 % 120,
                 70 + seed * 29 % 130)

        for side, (fx, fy, name, col) in enumerate((
                (170, h // 2 - 160, p_name, p_col),
                (w - 170, h // 2 - 160, e_name, e_col))):
            sx, sy = fx - ox, fy - oy
            if not (-140 < sx < SCREEN_WIDTH + 140):
                continue
            # Tanko
            pygame.draw.line(screen, (70, 58, 44), (sx, sy + 190),
                             (sx, sy), 6)
            pygame.draw.circle(screen, (200, 180, 120), (sx, sy - 4), 5)
            # Liehuva lippu (aaltoileva polygoni)
            direction = 1 if side == 0 else -1
            pts_top = []
            pts_bot = []
            for k in range(7):
                px = sx + direction * k * 14
                wave = _math.sin(t + k * 0.8) * (2 + k)
                pts_top.append((px, sy + 6 + wave))
                pts_bot.append((px, sy + 52 + wave * 0.7))
            pts = pts_top + pts_bot[::-1]
            pygame.draw.polygon(screen, col, pts)
            pygame.draw.polygon(screen, (30, 26, 24), pts, 2)
            # Nimi lipun alla
            tag = font_small.render(name[:22], True, (235, 228, 205))
            bg = pygame.Surface((tag.get_width() + 10,
                                 tag.get_height() + 4), pygame.SRCALPHA)
            bg.fill((12, 12, 16, 170))
            tx = sx - tag.get_width() // 2 + direction * 40
            screen.blit(bg, (tx - 5, sy + 200))
            screen.blit(tag, (tx, sy + 202))

    def draw(self, screen):
        # 1. Piirretään koko pelitilanne Managerin kautta
        # (Tämä piirtää areenan, hahmot JA VFX:n)
        self.manager.draw_game(screen)

        # 1.5 Sponsoriliput joukkueiden päädyissä (liigamatsit)
        try:
            self._draw_sponsor_flags(screen)
        except Exception:
            pass

        # 1.6 Loot Popup (jos auki)
        if self.show_loot:
            self.draw_loot_popup(screen)

        # 1.7 Sponsoritavoite-banneri (Rattlebridgen Tier 1 -matsit)
        objective = getattr(self.manager, "current_match_objective", None)
        if objective and not self.manager.match_over:
            name = f"SPONSOR OBJECTIVE: {objective['name'].upper()}"
            desc = objective["desc"]
            width = max(font_main.size(name)[0], font_small.size(desc)[0]) + 44
            banner = pygame.Rect(SCREEN_WIDTH // 2 - width // 2, 14, width, 66)
            pygame.draw.rect(screen, (20, 18, 24), banner, border_radius=10)
            pygame.draw.rect(screen, (200, 150, 90), banner, 2, border_radius=10)
            draw_text(name, font_main, (230, 185, 110), screen,
                      banner.x + 22, banner.y + 8)
            draw_text(desc, font_small, WHITE, screen,
                      banner.x + 22, banner.y + 40)

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
            from ui_kit import get_fullscreen_overlay
            screen.blit(get_fullscreen_overlay((0, 0, 0, 150)), (0, 0))

            # Tekstit
            res_text = self.manager.match_result # "VICTORY" tai "DEFEAT"
            res_color = GREEN if res_text == "VICTORY" else RED
            
            draw_text(res_text, font_title, res_color, screen, SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 50)
            # Sponsoritavoitteen tulos (jos matsissa oli tavoite)
            obj_result = getattr(self.manager, "last_objective_result", None)
            if obj_result:
                if obj_result.get("completed"):
                    line = (f"Sponsor objective '{obj_result['name']}' COMPLETE  "
                            f"+{obj_result['gold']}g, +{obj_result['reputation']} rep")
                    color = (150, 220, 150)
                else:
                    line = f"Sponsor objective '{obj_result['name']}' missed."
                    color = (200, 160, 120)
                draw_text(line, font_main, color, screen,
                          SCREEN_WIDTH//2 - font_main.size(line)[0]//2,
                          SCREEN_HEIGHT//2 + 10)
            draw_text("Click to continue...", font_main, WHITE, screen, SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 50)

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