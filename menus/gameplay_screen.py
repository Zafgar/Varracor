import pygame
from settings import *
from menus.base_menu import BaseMenu
from sound_manager import sound_system
from ui_kit import draw_text, font_title, font_main, font_small, draw_icon, GOLD_COLOR, RED, WHITE

class GameplayScreen(BaseMenu):
    """
    Yhteinen kantaluokka kaikille pelitiloille, joissa pelaaja ohjaa hahmoa
    vapaasti (BattleScreen, ForestRoadMenu, MuckfordCityMenu).
    
    Hoitaa:
    - Kameran seurannan
    - Pelaajan ohjauksen (run_combat_ai)
    - Yksiköiden ja VFX:n päivityksen ja piirtämisen
    - HUDin piirtämisen
    """
    def __init__(self, manager):
        super().__init__(manager)
        self.player = self.manager.player_character
        self.camera_x = 0
        self.camera_y = 0
        self.arena = None # Lapsiluokan pitää asettaa tämä

    def on_enter(self):
        """Kutsutaan kun tähän tilaan siirrytään."""
        self.manager.match_in_progress = True # Asetetaan peli "käyntiin"
        self._update_camera()

    def on_exit(self):
        """Kutsutaan kun tästä tilasta poistutaan."""
        self.manager.match_in_progress = False

    def handle_event(self, event):
        # --- UNIVERSAL MAP EDITOR ---
        if self.handle_editor_event(event):
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p and CHEAT_MODE:
                self.manager.world_paused = not self.manager.world_paused

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.paused = not self.manager.paused
            sound_system.play_sound('click')

    def _update_camera(self):
        if not self.player or not self.arena: return
        
        target_x = self.player.rect.centerx - SCREEN_WIDTH // 2
        target_y = self.player.rect.centery - SCREEN_HEIGHT // 2
        
        # Clamp
        self.camera_x = max(0, min(target_x, self.arena.width - SCREEN_WIDTH))
        self.camera_y = max(0, min(target_y, self.arena.height - SCREEN_HEIGHT))
        
        # Synkronoidaan manageriin
        self.manager.camera_x = self.camera_x
        self.manager.camera_y = self.camera_y

    def _update_gameplay(self, all_units):
        """Päivittää pelilogiikan."""
        super().update() # BaseMenu update (editor)
        
        if self.manager.paused: return
        
        # Varmistetaan että peli on "käynnissä" jotta combat toimii
        self.manager.match_in_progress = True

        # 1. Päivitä managerin yksikkölista
        self.manager.all_units.empty()
        self.manager.all_units.add(all_units)

        # 2. Pelaajan ohjaus
        self.player.run_combat_ai(all_units, self.arena.obstacles, manager=self.manager)

        # 3. Muiden yksiköiden AI ja päivitys
        for unit in all_units:
            if unit != self.player:
                unit.run_combat_ai(all_units, self.arena.obstacles, manager=self.manager)
            unit.update(self.arena.obstacles, self.manager)

        # 4. Areena ja VFX
        if hasattr(self.arena, "update"):
            self.arena.update(self.manager)
        self.manager.vfx.update(obstacles=self.arena.obstacles)

        # 5. Kamera
        self._update_camera()

    def _draw_boss_bar(self, screen, all_units):
        """Piirtää Boss HP -palkin ruudun yläreunaan, jos boss on kentällä."""
        boss = None
        for u in all_units:
            if getattr(u, "is_boss", False) and not u.is_dead:
                boss = u
                break
        
        if boss:
            # Asettelu
            cx = SCREEN_WIDTH // 2
            top_y = 50
            bar_w = 800
            bar_h = 24
            
            # 1. Nimi ja Ikonit
            name_txt = boss.name.upper()
            
            # Varjo nimelle
            shad_surf = font_title.render(name_txt, True, (0, 0, 0))
            name_surf = font_title.render(name_txt, True, (255, 60, 60)) # Kirkkaampi punainen
            
            name_rect = name_surf.get_rect(center=(cx, top_y))
            
            # Piirrä pääkallot nimen viereen
            draw_icon(screen, "skull", name_rect.left - 30, name_rect.centery, RED)
            draw_icon(screen, "skull", name_rect.right + 30, name_rect.centery, RED)
            
            # Piirrä nimi
            screen.blit(shad_surf, (name_rect.x + 2, name_rect.y + 2))
            screen.blit(name_surf, name_rect)
            
            # 2. Palkin tausta (Kehys)
            bar_rect = pygame.Rect(cx - bar_w//2, top_y + 35, bar_w, bar_h)
            
            # Koristeellinen tausta palkille (musta laatikko, jossa kultareunat)
            bg_rect = bar_rect.inflate(10, 10)
            pygame.draw.rect(screen, (20, 10, 10), bg_rect, border_radius=8)
            pygame.draw.rect(screen, (100, 80, 40), bg_rect, 2, border_radius=8) # Tumma kulta
            
            # 3. HP Palkki
            # Tausta (tummanpunainen)
            pygame.draw.rect(screen, (50, 10, 10), bar_rect, border_radius=4)
            
            # Täyttö
            pct = max(0, boss.current_hp / boss.max_hp)
            fill_w = int(bar_w * pct)
            
            if fill_w > 0:
                # Liukuväri-efekti (Yläosa vaaleampi)
                fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, fill_w, bar_h)
                pygame.draw.rect(screen, (200, 20, 20), fill_rect, border_radius=4)
                # Kiilto
                shine_rect = pygame.Rect(bar_rect.x, bar_rect.y, fill_w, bar_h // 2)
                pygame.draw.rect(screen, (230, 80, 80), shine_rect, border_top_left_radius=4, border_top_right_radius=4)
            
            # Reuna (Kirkas kulta)
            pygame.draw.rect(screen, GOLD_COLOR, bar_rect, 2, border_radius=4)
            
            # 4. HP Teksti (Pieni, palkin päällä)
            hp_txt = f"{int(boss.current_hp)} / {int(boss.max_hp)}"
            txt_surf = font_small.render(hp_txt, True, (220, 220, 220))
            txt_rect = txt_surf.get_rect(center=bar_rect.center)
            # Pieni varjo tekstille
            shad_txt = font_small.render(hp_txt, True, (0, 0, 0))
            screen.blit(shad_txt, (txt_rect.x + 1, txt_rect.y + 1))
            screen.blit(txt_surf, txt_rect)

    def _draw_gameplay(self, screen, all_units):
        """Piirtää pelimaailman."""
        if not self.arena: return
        
        offset = (self.camera_x, self.camera_y)
        
        # Tausta ja lattiaefektit
        self.arena.draw_background(screen, offset)
        self.manager.vfx.draw_floor(screen, offset)
        
        # Y-Sort (hahmot ja propit)
        renderables = list(self.arena.props) + all_units
        renderables.sort(key=lambda x: x.rect.bottom)
        
        for obj in renderables:
            if hasattr(obj, "draw_on_screen"):
                obj.draw_on_screen(screen, offset)
            elif hasattr(obj, "image") and obj.image:
                screen.blit(obj.image, (obj.rect.x - offset[0], obj.rect.y - offset[1]))
        
        # Etualan efektit
        if hasattr(self.arena, "draw_foreground"):
            self.arena.draw_foreground(screen, offset)
        self.manager.vfx.draw_top(screen, offset)
        
        # HUD
        if self.player:
            self.player.draw_hud(screen)
            
        # Boss Bar
        self._draw_boss_bar(screen, all_units)
        
        # Editor
        self.draw_editor(screen)