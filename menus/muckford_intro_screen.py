import pygame
import os
import random
import math
from settings import *
from menus.base_menu import BaseMenu
from ui_kit import UIButton, draw_text, font_title, font_main
from sound_manager import sound_system

class MuckfordIntroScreen(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.next_state = None
        self.start_time = 0
        
        # Audio paths
        # Tarkistetaan polku (Käyttäjän mukaan assets/narrator)
        self.music_path = "assets/narrator/muckford_intro.wav"
        if not os.path.exists(self.music_path):
             self.music_path = "assets/music/muckford_intro.wav"

        self.narrator_path = "assets/narrator/intro_2.mp3"
        
        # Kokonaiskesto (3min 40s = 220s)
        self.total_duration_ms = 220 * 1000 

        # Kohtaukset ja ajoitukset (millisekunteina)
        # end_time on hetki jolloin kuva vaihtuu SEURAAVAAN
        self.scenes = [
            {"img": "muckford_1.png", "end_time": 30000,  "vfx": "scene_1", "text": "Fragments of memory... rain and mud..."}, 
            {"img": "muckford_2.png", "end_time": 45000,  "vfx": "scene_2", "text": "Muckford. A city built on refuse and regret."}, 
            {"img": "muckford_3.png", "end_time": 63000,  "vfx": "scene_3", "text": "The Sunk Cask. A warm light in the damp fog."}, 
            {"img": "muckford_4.png", "end_time": 102000, "vfx": "scene_4", "text": "Inside, the air is thick with smoke and stories."}, 
            {"img": "muckford_5.png", "end_time": 142000, "vfx": "scene_5", "text": "Marda Shant keeps the books. She knows everyone's price."}, 
            {"img": "muckford_6.png", "end_time": 163000, "vfx": "scene_6", "text": "A hot meal. A cold ale. Simple comforts."}, 
            {"img": "muckford_7.png", "end_time": 180000, "vfx": "scene_7", "text": "But in the shadows, eyes are watching. Always watching."}, 
            {"img": "muckford_8.png", "end_time": 220000, "vfx": "scene_8", "text": "Your journey begins here. Or perhaps... it ends."}, 
        ]
        
        self.loaded_images = {}
        self._load_images()

        self.current_scene_index = -1
        self.btn_skip = UIButton(SCREEN_WIDTH - 150, SCREEN_HEIGHT - 70, 120, 50, "SKIP", None, (100, 100, 100))
        
        self.is_playing = False
        self.narrator_channel = None
        self.narrator_snd = None # Tallenna viittaus ääneen, jotta se ei katoa
        
        # VFX State
        self.vfx_particles = []
        self.vfx_timer = 0
        self.fade_alpha = 255 # Start black
        self.fade_state = "in" # in, out, none
        
        # Scene specific vars
        self.zoom_scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.light_flicker = 0

    def _load_images(self):
        for scene in self.scenes:
            path = os.path.join("assets", "narrator", scene["img"])
            if os.path.exists(path):
                try:
                    # Ladataan ja skaalataan hieman isommaksi zoom/pan efektejä varten (1.1x)
                    raw = pygame.image.load(path).convert()
                    w = int(SCREEN_WIDTH * 1.1)
                    h = int(SCREEN_HEIGHT * 1.1)
                    self.loaded_images[scene["img"]] = pygame.transform.smoothscale(raw, (w, h))
                except Exception as e:
                    print(f"Error loading scene {path}: {e}")
                    self.loaded_images[scene["img"]] = None
            else:
                # Placeholder
                s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                s.fill((20, 20, 25))
                self.loaded_images[scene["img"]] = s

    def _start_intro(self):
        self.start_time = pygame.time.get_ticks()
        self.is_playing = True
        
        # 1. Background Music
        # Soitetaan looppina (-1) taustalla
        if os.path.exists(self.music_path):
            sound_system.play_music(self.music_path, loops=-1)
            pygame.mixer.music.set_volume(0.4) # Hieman kovemmalle kuin oletus 0.3
        else:
            print(f"DEBUG: Music file not found at {self.music_path}")
        
        # 2. Narrator (Sound Effect)
        if os.path.exists(self.narrator_path):
            try:
                self.narrator_snd = pygame.mixer.Sound(self.narrator_path)
                self.narrator_snd.set_volume(1.0) # Varmista äänenvoimakkuus
                self.narrator_channel = self.narrator_snd.play()
            except Exception as e:
                print(f"Error playing narrator: {e}")

    def handle_event(self, event):
        if self.btn_skip.is_clicked(event) or (event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_SPACE]):
            self._finish_intro()

    def _finish_intro(self):
        sound_system.stop_music()
        if self.narrator_channel:
            self.narrator_channel.stop()
        
        # Siirry tavernaan (herääminen)
        self.manager.city_spawn_point = "bed"
        self.next_state = "tavern_sunk_cask"

    def update(self):
        if not self.is_playing:
            self._start_intro()

        elapsed_ms = pygame.time.get_ticks() - self.start_time

        if elapsed_ms >= self.total_duration_ms:
            self._finish_intro()
            return

        # Determine current scene
        new_index = 0
        for i, scene in enumerate(self.scenes):
            if elapsed_ms < scene["end_time"]:
                new_index = i
                break
            new_index = i # Fallback to last

        # Scene change logic
        if new_index != self.current_scene_index:
            if self.fade_state == "none":
                self.fade_state = "out"
            
            if self.fade_state == "out" and self.fade_alpha >= 255:
                self.current_scene_index = new_index
                self.vfx_particles = [] 
                self.vfx_timer = 0
                self.fade_state = "in"
                # Reset transform vars
                self.zoom_scale = 1.0
                self.pan_x = 0
                self.pan_y = 0

        # Fade update
        if self.fade_state == "in":
            self.fade_alpha = max(0, self.fade_alpha - 5)
            if self.fade_alpha == 0: self.fade_state = "none"
        elif self.fade_state == "out":
            self.fade_alpha = min(255, self.fade_alpha + 5)

        self._update_vfx()

    def _update_vfx(self):
        if self.current_scene_index < 0: return
        scene = self.scenes[self.current_scene_index]
        vfx = scene.get("vfx", "")
        self.vfx_timer += 1
        
        # Resetoi flicker joka frame, jotta se ei jää päälle vääriin kohtauksiin
        self.light_flicker = 0
        
        # --- SCENE SPECIFIC LOGIC ---
        
        if vfx == "scene_1": # Rain + mud road
            # Zoom in slowly
            self.zoom_scale = 1.0 + (self.vfx_timer * 0.0002)
            # Rain
            self._spawn_rain()
            # Teal sparks
            if random.random() < 0.05:
                self._spawn_particle("teal_spark")
            # Ripples
            if random.random() < 0.1:
                self._spawn_particle("ripple", y_range=(SCREEN_HEIGHT//2, SCREEN_HEIGHT))

        elif vfx == "scene_2": # Muckford exterior
            # Pan right
            self.pan_x = -int(self.vfx_timer * 0.5)
            # Smoke
            if random.random() < 0.1:
                self._spawn_particle("smoke", x_range=(0, SCREEN_WIDTH), y_range=(0, SCREEN_HEIGHT//2))
            # Fog/Haze
            if random.random() < 0.05:
                self._spawn_particle("fog")
            # Flicker lights (handled in draw)
            self.light_flicker = random.randint(0, 8) # Hyvin hento

        elif vfx == "scene_3": # Sunk Cask exterior
            # Pan/Zoom to door (Center/Bottom)
            self.zoom_scale = 1.0 + (self.vfx_timer * 0.0005)
            self.pan_y = -int(self.vfx_timer * 0.2)
            # Rain + Splash
            self._spawn_rain()
            if random.random() < 0.2:
                self._spawn_particle("splash", y_range=(SCREEN_HEIGHT-100, SCREEN_HEIGHT))
            self.light_flicker = random.randint(15, 35) # Hillitty hehku (oli 100-150)

        elif vfx == "scene_4": # Sunk Cask interior
            # Candle flicker
            self.light_flicker = random.randint(10, 25) # Hillitty (oli 50-100)
            # Smoke/Haze ceiling
            if random.random() < 0.1:
                self._spawn_particle("smoke", y_range=(0, 200))
            # Dust
            if random.random() < 0.2:
                self._spawn_particle("dust")

        elif vfx == "scene_5": # Marda Shant
            # Coin flash
            if random.random() < 0.02:
                self._spawn_particle("glint", x_range=(SCREEN_WIDTH//2, SCREEN_WIDTH), y_range=(SCREEN_HEIGHT//2, SCREEN_HEIGHT))
            # Shadow movement (subtle)
            self.pan_x = math.sin(self.vfx_timer * 0.01) * 5

        elif vfx == "scene_6": # Food and Ale
            # Steam
            if random.random() < 0.1:
                self._spawn_particle("steam", x_range=(SCREEN_WIDTH//2 - 100, SCREEN_WIDTH//2 + 100))
            # Flicker
            self.light_flicker = random.randint(2, 8) # (oli 5-15)

        elif vfx == "scene_7": # Rats
            # Eye pulse (handled in draw)
            # Dripping water
            if random.random() < 0.1:
                self._spawn_particle("drip")
            # Shadow creep
            self.fade_alpha = max(self.fade_alpha, int(math.sin(self.vfx_timer * 0.02) * 50))

        elif vfx == "scene_8": # Strongbox
            # Glint
            if random.random() < 0.01:
                self._spawn_particle("glint", x_range=(SCREEN_WIDTH//2 - 50, SCREEN_WIDTH//2 + 50))
            # Dimming
            if self.vfx_timer % 200 > 150:
                self.fade_alpha = max(self.fade_alpha, 100)

        # Update particles
        for p in self.vfx_particles[:]:
            p["life"] -= 1
            p["x"] += p.get("vx", 0)
            p["y"] += p.get("vy", 0)
            if p["type"] == "rain":
                p["y"] += 15 # Fast rain
            elif p["type"] == "steam":
                p["alpha"] = max(0, p["alpha"] - 2)
            
            if p["life"] <= 0:
                self.vfx_particles.remove(p)

    def _spawn_rain(self):
        for _ in range(4):
            self.vfx_particles.append({
                "type": "rain", "x": random.randint(0, SCREEN_WIDTH), "y": -20,
                "vx": random.uniform(-1, 1), "vy": 0, "len": random.randint(10, 20),
                "color": (150, 150, 200, 100), "life": 60
            })

    def _spawn_particle(self, ptype, x_range=(0, SCREEN_WIDTH), y_range=(0, SCREEN_HEIGHT)):
        x = random.randint(x_range[0], x_range[1])
        y = random.randint(y_range[0], y_range[1])
        
        if ptype == "teal_spark":
            self.vfx_particles.append({
                "type": "spark", "x": x, "y": y, "vx": random.uniform(-0.5, 0.5), "vy": random.uniform(-0.5, 0.5),
                "size": random.randint(2, 4), "color": (50, 255, 200), "life": 60, "alpha": 200
            })
        elif ptype == "ripple":
            self.vfx_particles.append({
                "type": "ripple", "x": x, "y": y, "size": 5, "max_size": 30, "life": 40, "color": (100, 150, 200)
            })
        elif ptype == "smoke":
            self.vfx_particles.append({
                "type": "smoke", "x": x, "y": y, "vx": 0.5, "vy": -0.5,
                "size": random.randint(20, 50), "life": 120, "alpha": 50, "color": (50, 50, 50)
            })
        elif ptype == "fog":
            self.vfx_particles.append({
                "type": "smoke", "x": -50, "y": y, "vx": 1.0, "vy": 0,
                "size": 100, "life": 300, "alpha": 30, "color": (200, 200, 220)
            })
        elif ptype == "dust":
            self.vfx_particles.append({
                "type": "spark", "x": x, "y": y, "vx": random.uniform(-0.2, 0.2), "vy": random.uniform(-0.2, 0.2),
                "size": 2, "color": (200, 200, 150), "life": 100, "alpha": 150
            })
        elif ptype == "glint":
            self.vfx_particles.append({
                "type": "glint", "x": x, "y": y, "life": 10, "size": 20
            })
        elif ptype == "steam":
            self.vfx_particles.append({
                "type": "smoke", "x": x, "y": y, "vx": 0, "vy": -1.0,
                "size": random.randint(10, 20), "life": 60, "alpha": 100, "color": (200, 200, 200)
            })
        elif ptype == "drip":
            self.vfx_particles.append({
                "type": "rain", "x": x, "y": y, "vx": 0, "vy": 0, "len": 5, "life": 30, "color": (100, 100, 150, 200)
            })

    def draw(self, screen):
        screen.fill((0, 0, 0))
        
        if self.current_scene_index >= 0:
            scene = self.scenes[self.current_scene_index]
            img = self.loaded_images.get(scene["img"])
            
            if img:
                # Apply Pan/Zoom
                w, h = img.get_size()
                # Center crop based on zoom
                crop_w = int(SCREEN_WIDTH / self.zoom_scale)
                crop_h = int(SCREEN_HEIGHT / self.zoom_scale)
                
                # Center point + pan
                cx = w // 2 + self.pan_x
                cy = h // 2 + self.pan_y
                
                # Clamp
                cx = max(crop_w//2, min(w - crop_w//2, cx))
                cy = max(crop_h//2, min(h - crop_h//2, cy))
                
                rect = pygame.Rect(cx - crop_w//2, cy - crop_h//2, crop_w, crop_h)
                sub = img.subsurface(rect)
                scaled = pygame.transform.smoothscale(sub, (SCREEN_WIDTH, SCREEN_HEIGHT))
                screen.blit(scaled, (0, 0))
                
                # --- OVERLAYS ---
                # Light Flicker
                if self.light_flicker > 0:
                    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                    # Käytetään normaalia alpha-blendausta (ei ADD) ja neutraalimpaa väriä
                    s.fill((255, 240, 220, self.light_flicker))
                    screen.blit(s, (0, 0))
                
                # Particles
                for p in self.vfx_particles:
                    ptype = p["type"]
                    if ptype == "rain":
                        pygame.draw.line(screen, p["color"], (p["x"], p["y"]), (p["x"], p["y"]+p["len"]), 1)
                    elif ptype == "spark":
                        s = pygame.Surface((p["size"]*2, p["size"]*2), pygame.SRCALPHA)
                        pygame.draw.circle(s, (*p["color"], p["alpha"]), (p["size"], p["size"]), p["size"])
                        screen.blit(s, (p["x"], p["y"]))
                    elif ptype == "smoke":
                        s = pygame.Surface((p["size"]*2, p["size"]*2), pygame.SRCALPHA)
                        pygame.draw.circle(s, (*p["color"], p["alpha"]), (p["size"], p["size"]), p["size"])
                        screen.blit(s, (p["x"], p["y"]))
                    elif ptype == "ripple":
                        radius = int(p["size"] + (p["max_size"] - p["size"]) * (1 - p["life"]/40))
                        pygame.draw.ellipse(screen, (*p["color"], 100), (p["x"]-radius, p["y"]-radius//2, radius*2, radius), 1)
                    elif ptype == "glint":
                        # Star shape
                        cx, cy = p["x"], p["y"]
                        sz = p["size"]
                        pygame.draw.line(screen, WHITE, (cx-sz, cy), (cx+sz, cy), 2)
                        pygame.draw.line(screen, WHITE, (cx, cy-sz), (cx, cy+sz), 2)
                
                # Scene 7: Rat Eyes
                if scene["vfx"] == "scene_7":
                    pulse = abs(math.sin(self.vfx_timer * 0.1)) * 255
                    for _ in range(3): # Muutama silmäpari
                        ex = random.randint(100, SCREEN_WIDTH-100)
                        ey = random.randint(SCREEN_HEIGHT//2, SCREEN_HEIGHT-100)
                        if random.random() < 0.05:
                            pygame.draw.circle(screen, (255, 0, 0, int(pulse)), (ex, ey), 3)
                            pygame.draw.circle(screen, (255, 0, 0, int(pulse)), (ex+10, ey), 3)
                            
                # Tekstitys
                self._draw_subtitle(screen, scene.get("text", ""))

        # Fade Overlay
        if self.fade_alpha > 0:
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, self.fade_alpha))
            screen.blit(s, (0, 0))
            
        self.btn_skip.check_hover(pygame.mouse.get_pos())
        self.btn_skip.draw(screen)

    def _draw_subtitle(self, screen, text):
        if not text: return
        
        box_h = 100
        y = SCREEN_HEIGHT - box_h - 20
        
        s = pygame.Surface((SCREEN_WIDTH, box_h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180)) # Puoliläpinäkyvä musta laatikko
        screen.blit(s, (0, y))
        
        txt_surf = font_main.render(text, True, (255, 255, 255))
        rect = txt_surf.get_rect(center=(SCREEN_WIDTH // 2, y + box_h // 2))
        screen.blit(txt_surf, rect)
