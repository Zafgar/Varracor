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
            except: pass
            
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

    def handle_event(self, event):
        pass

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
            except: pass
            
            # Siirrytään latausruutuun, joka hoitaa alustukset
            self.next_state = "intro"

        if self.btn_load.update():
            print("Load clicked")

        if self.btn_options.update():
            print("Options clicked")

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