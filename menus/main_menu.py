import pygame
import os
import random
import math
import sys
try:
    import cv2  # type: ignore
except ImportError:
    cv2 = None
from settings import *
from menus.base_menu import BaseMenu
from sound_manager import sound_system
from ui_kit import font_title, font_main, draw_text, SpriteButton, GOLD_COLOR

# --- KIPINÄ PARTIKKELI LUOKKA ---
class Spark:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(SCREEN_HEIGHT, SCREEN_HEIGHT + 100)
        self.speed = random.uniform(1.0, 3.0)
        self.drift = random.uniform(-0.5, 0.5)
        colors = [(255, 100, 50), (255, 180, 50), (255, 220, 100), (200, 50, 20)]
        self.color = random.choice(colors)
        self.size = random.randint(2, 4)
        self.alpha = 255
        self.decay = random.uniform(1, 3)

    def update(self):
        self.y -= self.speed
        self.x += self.drift
        self.alpha -= self.decay
        self.x += math.sin(pygame.time.get_ticks() * 0.005 + self.y) * 0.5

    def draw(self, screen):
        if self.alpha > 0:
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            rgba = self.color + (int(self.alpha),)
            pygame.draw.circle(s, rgba, (self.size, self.size), self.size)
            screen.blit(s, (self.x, self.y))


# --- MAIN MENU ---
class MainMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        
        # --- AUDIO RESET (KORJAUS 1) ---
        # Tämä varmistaa, että City Hubin tai taistelun äänet eivät jää päälle.
        print("Entering Main Menu: Resetting Audio...")
        pygame.mixer.stop()       # Pysäyttää kaikki efektit/ambientit
        pygame.mixer.music.stop() # Pysäyttää edellisen musiikin
        
        # --- MUSIIKIN LATAUS (KORJAUS 2) ---
        # Yritetään ladata .wav tai .mp3
        music_files = [
            "assets/videos/mainmenu/main.mp4", # UUSI: Videon ääni ensisijaisena
            "assets/music/menu_theme.wav",
            "assets/music/menu_theme.mp3"
        ]
        
        music_loaded = False
        for path in music_files:
            if os.path.exists(path):
                try:
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.set_volume(0.4)
                    pygame.mixer.music.play(-1, fade_ms=2000)
                    print(f"Main Menu Music Loaded: {path}")
                    music_loaded = True
                    break
                except Exception as e:
                    print(f"Error loading {path}: {e}")
        
        if not music_loaded:
            print("WARNING: Main menu music NOT found! (Checked .wav and .mp3)")

        # 2. Taustakuva
        self.bg_image = None
        bg_path = "assets/images/menu_background.png"
        if os.path.exists(bg_path):
            try:
                raw = pygame.image.load(bg_path).convert()
                self.bg_image = pygame.transform.smoothscale(raw, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except Exception: pass
            
        # 2.5 VIDEO BACKGROUND
        self.video_cap = None
        self.video_surf = None
        video_path = "assets/videos/mainmenu/main.mp4"
        
        if ENABLE_VIDEO_BACKGROUND and cv2 and os.path.exists(video_path):
            try:
                self.video_cap = cv2.VideoCapture(video_path)
                if not self.video_cap.isOpened():
                    self.video_cap = None
                else:
                    print(f"Video background loaded: {video_path}")
            except Exception as e:
                print(f"Error loading video: {e}")

        # 3. NAPIT
        start_y = SCREEN_HEIGHT // 2 + 20
        gap = 110 

        # START
        self.btn_start = SpriteButton(
            x=SCREEN_WIDTH // 2, y=start_y,
            img_idle="assets/ui/btn_start_idle.png",
            img_hover="assets/ui/btn_start_hover.png",
            img_pressed="assets/ui/btn_start_pressed.png",
            label_text="START GAME", target_width=400 
        )

        # LOAD
        self.btn_load = SpriteButton(
            x=SCREEN_WIDTH // 2, y=start_y + gap,
            img_idle="assets/ui/btn_load_idle.png",
            img_hover="assets/ui/btn_load_hover.png",
            img_pressed="assets/ui/btn_load_pressed.png",
            label_text="LOAD GAME", target_width=400 
        )

        # OPTIONS
        self.btn_options = SpriteButton(
            x=SCREEN_WIDTH // 2, y=start_y + gap * 2,
            img_idle="assets/ui/btn_options_idle.png",
            img_hover="assets/ui/btn_options_hover.png",
            img_pressed="assets/ui/btn_options_pressed.png",
            label_text="OPTIONS", target_width=400 
        )

        # EXIT
        self.btn_exit = SpriteButton(
            x=SCREEN_WIDTH // 2, y=start_y + gap * 3,
            img_idle="assets/ui/btn_exit_idle.png",
            img_hover="assets/ui/btn_exit_hover.png",
            img_pressed="assets/ui/btn_exit_pressed.png",
            label_text="EXIT GAME", target_width=400 
        )
        
        self.buttons = [self.btn_start, self.btn_load, self.btn_options, self.btn_exit]
        
        # UUSI: Test Map Button (Vain Cheat Mode)
        if CHEAT_MODE:
            self.btn_test = SpriteButton(
                x=SCREEN_WIDTH - 150, y=SCREEN_HEIGHT - 80,
                img_idle="assets/ui/btn_options_idle.png",
                img_hover="assets/ui/btn_options_hover.png",
                img_pressed="assets/ui/btn_options_pressed.png",
                label_text="TEST MAP", target_width=200 
            )
            self.buttons.append(self.btn_test)
            
        self.sparks = []

        # LOAD-paneeli: slottilista + poisto
        self.show_load_panel = False
        self.load_slot_rects = []    # (rect, slot)
        self.delete_rects = []       # (rect, slot)
        self.delete_armed = None     # slot jonka poisto odottaa vahvistusta
        self.load_feedback = ""

    def consumes_escape(self):
        return self.show_load_panel

    def handle_event(self, event):
        if not self.show_load_panel:
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.show_load_panel = False
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            import save_manager
            # Poistonapit ensin (rivin sisällä)
            for rect, slot in self.delete_rects:
                if rect.collidepoint(event.pos):
                    if self.delete_armed == slot:
                        save_manager.delete_slot(slot)
                        self.delete_armed = None
                        self.load_feedback = "Save deleted."
                        sound_system.play_sound("click")
                    else:
                        self.delete_armed = slot
                        self.load_feedback = "Click the X again to delete."
                        sound_system.play_sound("hover")
                    return
            for rect, slot in self.load_slot_rects:
                if rect.collidepoint(event.pos):
                    if save_manager.load_from_slot(self.manager, slot):
                        pygame.mixer.music.fadeout(1000)
                        self.show_load_panel = False
                        # Lataus vie suoraan pelimaailmaan
                        self.next_state = "muckford_city"
                        sound_system.play_sound("click")
                    else:
                        self.load_feedback = "Could not load that save."
                        sound_system.play_sound("error")
                    return
            # Klikkaus paneelin ulkopuolelle sulkee
            self.show_load_panel = False
            self.delete_armed = None

    def update(self):
        # --- VIDEO UPDATE ---
        if self.video_cap:
            ret, frame = self.video_cap.read()
            if not ret:
                self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.video_cap.read()
            
            if ret:
                # Zoom 5% (1.05x)
                target_w = int(SCREEN_WIDTH * 1.05)
                target_h = int(SCREEN_HEIGHT * 1.05)
                frame = cv2.resize(frame, (target_w, target_h))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.video_surf = pygame.image.frombuffer(frame.tobytes(), (target_w, target_h), "RGB")

        # Kipinät
        if len(self.sparks) < 60: 
            if random.random() < 0.2:
                self.sparks.append(Spark())
        
        for spark in self.sparks[:]:
            spark.update()
            if spark.alpha <= 0 or spark.y < 0:
                self.sparks.remove(spark)

        # --- NAPPIEN PÄIVITYS ---
        
        if self.btn_start.update():
            # Fadeout musiikille kun peli alkaa
            pygame.mixer.music.fadeout(1000)
            
            try: sound_system.play_sound("battle_start") 
            except Exception: pass
            
            # Siirrytään latausruutuun, joka hoitaa alustukset
            self.next_state = "intro"

        if self.show_load_panel:
            return  # paneeli nappaa syötteet handle_eventissä

        if self.btn_load.update():
            # Avaa slottivalitsin (klikkaus lataa, X poistaa)
            self.show_load_panel = True
            self.delete_armed = None
            self.load_feedback = ""
            try: sound_system.play_sound("click")
            except Exception: pass

        if self.btn_options.update():
            self.next_state = "options"

        if self.btn_exit.update():
            self.next_state = "exit"
            
        # Test Map Action
        if CHEAT_MODE and hasattr(self, "btn_test") and self.btn_test.update():
            self.next_state = "test_arena"

    def draw(self, screen):
        if self.video_surf:
            # Keskitetään zoomattu video
            vw = self.video_surf.get_width()
            vh = self.video_surf.get_height()
            screen.blit(self.video_surf, ((SCREEN_WIDTH - vw)//2, (SCREEN_HEIGHT - vh)//2))
        elif self.bg_image:
            screen.blit(self.bg_image, (0, 0))
        else:
            self.draw_themed_background(screen, mood="city")
            title = "AUTO ARENA"
            subtitle = "Gladiator Tycoon"
            draw_text(title, font_title, (0, 0, 0), screen, SCREEN_WIDTH//2 - 146, 154)
            draw_text(title, font_title, GOLD_COLOR, screen, SCREEN_WIDTH//2 - 150, 150)
            draw_text(subtitle, font_main, (200, 200, 200), screen, SCREEN_WIDTH//2 - 100, 220)

        for spark in self.sparks:
            spark.draw(screen)

        for btn in self.buttons:
            btn.draw(screen)

        if self.show_load_panel:
            self._draw_load_panel(screen)

    def _draw_load_panel(self, screen):
        """Slottilista: klikkaus lataa, X poistaa (kahdella klikillä)."""
        import save_manager
        from ui_kit import font_small, font_header

        shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 185))
        screen.blit(shade, (0, 0))
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 380, SCREEN_HEIGHT // 2 - 330,
                            760, 660)
        pygame.draw.rect(screen, (24, 22, 20), panel, border_radius=14)
        pygame.draw.rect(screen, GOLD_COLOR, panel, 3, border_radius=14)
        draw_text("LOAD GAME - choose a save", font_header, GOLD_COLOR,
                  screen, panel.x + 30, panel.y + 22)
        draw_text("[ESC] back", font_small, (150, 150, 160), screen,
                  panel.right - 120, panel.y + 32)

        self.load_slot_rects = []
        self.delete_rects = []
        y = panel.y + 86
        mouse = pygame.mouse.get_pos()
        for row in save_manager.list_slots():
            slot = row["slot"]
            rect = pygame.Rect(panel.x + 26, y, panel.w - 52, 78)
            hover = rect.collidepoint(mouse)
            label = "QUICKSAVE" if slot == 0 else f"SLOT {slot}"
            if row["exists"]:
                pygame.draw.rect(screen, (44, 40, 34) if hover else (34, 32, 28),
                                 rect, border_radius=9)
                pygame.draw.rect(screen, GOLD_COLOR if hover else (120, 100, 70),
                                 rect, 2, border_radius=9)
                draw_text(label, font_small, (150, 150, 160), screen,
                          rect.x + 16, rect.y + 8)
                draw_text(row["name"][:30], font_main, (235, 228, 210), screen,
                          rect.x + 16, rect.y + 32)
                draw_text(row["game_date"], font_small, (150, 200, 165),
                          screen, rect.x + 300, rect.y + 12)
                draw_text(f"saved {row['saved_at']}", font_small,
                          (140, 140, 150), screen, rect.x + 300, rect.y + 42)
                self.load_slot_rects.append((rect, slot))
                # Poistonappi rivin oikeassa reunassa
                del_rect = pygame.Rect(rect.right - 54, rect.y + 20, 38, 38)
                armed = self.delete_armed == slot
                pygame.draw.rect(screen, (120, 40, 34) if armed else (56, 36, 34),
                                 del_rect, border_radius=8)
                pygame.draw.rect(screen, (230, 110, 90), del_rect, 2,
                                 border_radius=8)
                xs = font_main.render("X", True, (255, 200, 190))
                screen.blit(xs, xs.get_rect(center=del_rect.center))
                self.delete_rects.append((del_rect, slot))
            else:
                pygame.draw.rect(screen, (28, 27, 25), rect, border_radius=9)
                pygame.draw.rect(screen, (70, 66, 60), rect, 1, border_radius=9)
                draw_text(label, font_small, (110, 108, 100), screen,
                          rect.x + 16, rect.y + 8)
                draw_text("- Empty -", font_main, (110, 108, 100), screen,
                          rect.x + 16, rect.y + 34)
            y += 90
        if self.load_feedback:
            draw_text(self.load_feedback, font_small, (255, 190, 120),
                      screen, panel.x + 30, panel.bottom - 34)