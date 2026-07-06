import pygame
import os
from settings import *
from menus.base_menu import BaseMenu
from ui_kit import UIButton, draw_text, font_title, font_main
from sound_manager import sound_system
import random
import math

class IntroScreen(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.next_state = None
        self.start_time = 0
        self.music_path = "assets/narrator/intro_music.wav"
        self.narrator_path = "assets/narrator/intro_1.mp3"
        self.total_duration_ms = 251 * 1000 # 4min 11s

        # Aikaleimat millisekunneissa
        self.scenes = [
            {"img": "scene_1.png", "start": 0,          "text": "In the Age of War, Varrakor burned.", "vfx": "war"},
            {"img": "scene_2.png", "start": 8 * 1000,   "text": "Three Kings ruled over divided realms.", "vfx": "royal"},
            {"img": "scene_3.png", "start": 39 * 1000,  "text": "Until the world broke apart.", "vfx": "vortex"},
            {"img": "scene_4.png", "start": 60 * 1000,  "text": "Catastrophes spread across the land.", "vfx": "plague"},
            {"img": "scene_5.png", "start": 90 * 1000,  "text": "A reluctant truce was forged in shadow.", "vfx": "shadow"},
            {"img": "scene_6.png", "start": 105 * 1000, "text": "The Arenas were sanctioned by Arkon.", "vfx": "holy"},
            {"img": "scene_7.png", "start": 135 * 1000, "text": "A child found the Vortex Blade.", "vfx": "mystic"},
            {"img": "scene_8.png", "start": 155 * 1000, "text": "The Abyssal Weave awakens.", "vfx": "weave"},
            {"img": "scene_9.png", "start": 180 * 1000, "text": "Three years of war against the Rift.", "vfx": "battle"},
            {"img": "scene_10.png", "start": 215 * 1000, "text": "The road leads to Muckford...", "vfx": "storm"},
        ]
        self.loaded_images = {}
        self._load_images()

        self.current_scene_index = -1
        self.btn_skip = UIButton(SCREEN_WIDTH - 150, SCREEN_HEIGHT - 70, 120, 50, "SKIP", None, (100, 100, 100))
        
        # Käynnistetään vasta kun tähän tilaan siirrytään
        self.is_playing = False
        
        # VFX State
        self.vfx_particles = []
        self.vfx_timer = 0
        self.fade_alpha = 255 # Start black
        self.fade_state = "in" # in, out, none
        
        # Typewriter state
        self.displayed_text = ""
        self.text_timer = 0
        self.text_index = 0
        
        self.narrator_channel = None

    def _load_images(self):
        for scene in self.scenes:
            path = os.path.join("assets", "narrator", scene["img"])
            if os.path.exists(path):
                try:
                    self.loaded_images[scene["img"]] = pygame.transform.smoothscale(
                        pygame.image.load(path).convert(), 
                        (SCREEN_WIDTH, SCREEN_HEIGHT)
                    )
                except Exception as e:
                    print(f"Error loading intro scene {path}: {e}")
                    self.loaded_images[scene["img"]] = None
            else:
                self.loaded_images[scene["img"]] = None
                # Placeholder surface
                s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                s.fill((20, 20, 25))
                self.loaded_images[scene["img"]] = s
        
        # Pre-scale images for pan/zoom effect (much larger, e.g. 1.2x)
        for key, img in self.loaded_images.items():
            if img:
                self.loaded_images[key] = pygame.transform.smoothscale(img, (int(SCREEN_WIDTH * 1.2), int(SCREEN_HEIGHT * 1.2)))

    def _start_intro(self):
        self.start_time = pygame.time.get_ticks()
        self.is_playing = True
        
        # 1. Soita taustamusiikki (Loop)
        if os.path.exists(self.music_path):
            try:
                sound_system.play_music(self.music_path, loops=-1)
            except Exception as e:
                print(f"Error playing intro music {self.music_path}: {e}")
        
        # 2. Soita narraattori (Sound Effect, Once)
        if os.path.exists(self.narrator_path):
            try:
                # Ladataan äänenä, ei musiikkina
                narrator_snd = pygame.mixer.Sound(self.narrator_path)
                self.narrator_channel = narrator_snd.play()
            except Exception as e:
                print(f"Error playing narrator {self.narrator_path}: {e}")

    def handle_event(self, event):
        if self.btn_skip.is_clicked(event) or (event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_SPACE]):
            sound_system.stop_music()
            if self.narrator_channel:
                self.narrator_channel.stop()
            self.manager.loading_target_state = "forest_road"
            self.next_state = "loading"

    def update(self):
        if not self.is_playing:
            self._start_intro()

        elapsed_ms = pygame.time.get_ticks() - self.start_time

        if elapsed_ms >= self.total_duration_ms or not pygame.mixer.music.get_busy():
            # Pysäytä kaikki äänet kun intro loppuu luonnollisesti
            sound_system.stop_music()
            if self.narrator_channel:
                self.narrator_channel.stop()
            self.manager.loading_target_state = "forest_road"
            self.next_state = "loading"
            return

        # Determine current scene
        new_index = -1
        for i, scene in enumerate(self.scenes):
            if elapsed_ms >= scene["start"]:
                new_index = i
            else:
                break
        
        # Scene change logic (with fade out)
        if new_index != self.current_scene_index:
            # Jos ei olla vielä vaihtamassa, aloitetaan fade out
            if self.fade_state == "none":
                self.fade_state = "out"
            
            # Kun fade out on valmis (ruutu musta), vaihdetaan kuva
            if self.fade_state == "out" and self.fade_alpha >= 255:
                self.current_scene_index = new_index
                self.vfx_particles = [] # Clear old VFX
                self.vfx_timer = 0
                self.fade_state = "in"
                # Reset text
                self.displayed_text = ""
                self.text_timer = 0
                self.text_index = 0

        # Fade update
        if self.fade_state == "in":
            self.fade_alpha -= 5
            if self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.fade_state = "none"
        elif self.fade_state == "out":
            self.fade_alpha += 5
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                # Odotetaan tässä tilassa kunnes scene vaihtuu yllä olevassa logiikassa
        
        # Update VFX
        self._update_vfx()
        
        # Update Text (Typewriter)
        if self.current_scene_index >= 0:
            target_text = self.scenes[self.current_scene_index].get("text", "")
            if self.text_index < len(target_text):
                self.text_timer += 1
                if self.text_timer >= 3: # Speed
                    self.text_timer = 0
                    self.text_index += 1
                    self.displayed_text = target_text[:self.text_index]
        
        # Force scene change if first frame (no fade needed)
        if self.current_scene_index == -1:
            self.current_scene_index = 0

    def _update_vfx(self):
        if self.current_scene_index < 0: return
        scene = self.scenes[self.current_scene_index]
        vfx_type = scene.get("vfx", "")
        
        self.vfx_timer += 1
        
        # --- PARTICLE SPAWNERS ---
        
        if vfx_type in ["war", "battle", "plague"]:
            # Smoke / Dust
            if random.random() < 0.2:
                self.vfx_particles.append({
                    "x": random.randint(0, SCREEN_WIDTH),
                    "y": SCREEN_HEIGHT + 20,
                    "vx": random.uniform(-0.5, 0.5),
                    "vy": random.uniform(-1.5, -0.5),
                    "size": random.randint(30, 80),
                    "alpha": random.randint(50, 100),
                    "life": 300,
                    "type": "smoke",
                    "color": (50, 40, 30) if vfx_type != "plague" else (30, 50, 30)
                })
            
            # Embers (War/Battle only)
            if vfx_type in ["war", "battle"] and random.random() < 0.15:
                self.vfx_particles.append({
                    "x": random.randint(0, SCREEN_WIDTH),
                    "y": SCREEN_HEIGHT + 10,
                    "vx": random.uniform(-1, 1),
                    "vy": random.uniform(-3, -1),
                    "size": random.randint(2, 4),
                    "alpha": 255,
                    "life": 120,
                    "type": "ember",
                    "color": (255, 100, 50)
                })

        elif vfx_type == "storm":
            # Rain
            for _ in range(5):
                self.vfx_particles.append({
                    "x": random.randint(0, SCREEN_WIDTH),
                    "y": -10,
                    "vx": random.uniform(-2, 1),
                    "vy": random.uniform(10, 20),
                    "len": random.randint(10, 30),
                    "life": 60,
                    "type": "rain",
                    "color": (150, 150, 200, 150)
                })
            # Lightning flash
            if random.random() < 0.005:
                self.vfx_particles.append({"type": "flash", "life": 10, "alpha": 200})

        elif vfx_type in ["vortex", "weave", "mystic"]:
            # Floating particles / Runes
            if random.random() < 0.1:
                col = (100, 255, 200) if vfx_type != "vortex" else (50, 0, 100)
                self.vfx_particles.append({
                    "x": random.randint(0, SCREEN_WIDTH),
                    "y": random.randint(0, SCREEN_HEIGHT),
                    "vx": random.uniform(-0.5, 0.5),
                    "vy": random.uniform(-0.5, 0.5),
                    "size": random.randint(2, 5),
                    "alpha": 0,
                    "max_alpha": random.randint(100, 200),
                    "life": 180,
                    "type": "magic_dust",
                    "color": col
                })

        elif vfx_type == "holy":
            # Light rays / Dust
            if random.random() < 0.1:
                self.vfx_particles.append({
                    "x": random.randint(0, SCREEN_WIDTH),
                    "y": random.randint(0, SCREEN_HEIGHT),
                    "vx": 0, "vy": -0.2,
                    "size": random.randint(2, 6),
                    "alpha": 0, "max_alpha": 150,
                    "life": 200, "type": "magic_dust", "color": (255, 255, 200)
                })
        
        # Update particles
        for p in self.vfx_particles[:]:
            # Flash is a full-screen effect with no position
            if p.get("type") != "flash":
                p["x"] += p.get("vx", 0)
                p["y"] += p.get("vy", 0)
            p["life"] -= 1
            
            # Fade in/out for magic dust
            if p.get("type") == "magic_dust":
                if p["life"] > 150: p["alpha"] = min(p["max_alpha"], p["alpha"] + 5)
                elif p["life"] < 50: p["alpha"] = max(0, p["alpha"] - 5)
            
            if p["life"] <= 0:
                self.vfx_particles.remove(p)

    def draw(self, screen):
        screen.fill(BLACK)

        if self.current_scene_index >= 0:
            scene = self.scenes[self.current_scene_index]
            img_name = scene["img"]
            img = self.loaded_images.get(img_name)
            
            if img:
                # --- KEN BURNS EFFECT (Pan & Zoom) ---
                # Lasketaan offsetit ajan perusteella
                t = self.vfx_timer * 0.05
                
                # Eri suunnat eri efekteille
                vfx = scene.get("vfx", "")
                
                if vfx in ["war", "battle"]: # Pan Right
                    pan_x = int(t * 0.5) % (img.get_width() - SCREEN_WIDTH)
                    pan_y = (img.get_height() - SCREEN_HEIGHT) // 2
                elif vfx in ["royal", "holy"]: # Zoom In (Slow)
                    # Simuloidaan zoomia rajaamalla kuvaa
                    # Koska img on jo iso, voimme vain liikuttaa sitä
                    pan_x = (img.get_width() - SCREEN_WIDTH) // 2
                    pan_y = int(t * 0.2) % (img.get_height() - SCREEN_HEIGHT)
                else: # Pan Diagonal
                    pan_x = int(t * 0.3) % (img.get_width() - SCREEN_WIDTH)
                    pan_y = int(t * 0.2) % (img.get_height() - SCREEN_HEIGHT)
                
                draw_x, draw_y = -pan_x, -pan_y
                
                # Shake for impact scenes
                if vfx in ["vortex", "storm", "battle"]:
                    draw_x += random.randint(-2, 2)
                    draw_y += random.randint(-2, 2)
                    
                screen.blit(img, (draw_x, draw_y))
                
                # --- OVERLAYS ---
                # Vignette (Tummat kulmat)
                self._draw_vignette(screen)
                
                # Color grading (Sepia / Cold / Dark)
                if vfx in ["war", "royal"]:
                    self._draw_overlay(screen, (50, 30, 10, 40)) # Sepia
                elif vfx in ["vortex", "shadow", "plague"]:
                    self._draw_overlay(screen, (10, 0, 20, 60)) # Dark Purple
                elif vfx in ["storm", "rain"]:
                    self._draw_overlay(screen, (0, 10, 30, 50)) # Cold Blue
                
                self._draw_vfx(screen, scene.get("vfx"))
                self._draw_subtitle(screen, self.displayed_text)

        if self.fade_alpha > 0:
            fade_s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fade_s.fill((0, 0, 0, self.fade_alpha))
            screen.blit(fade_s, (0, 0))

        self.btn_skip.check_hover(pygame.mouse.get_pos())
        self.btn_skip.draw(screen)

    def _draw_vignette(self, screen):
        # Yksinkertainen vinjetti (reunat tummat)
        # Voisi olla valmiiksi ladattu kuva, mutta piirretään koodilla
        # Optimointi: Piirrä vain kerran ja cacheta, mutta tässä dynaaminen
        pass # Jätetään pois jos hidastaa, tai käytetään isoa PNG:tä

    def _draw_overlay(self, screen, color):
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill(color)
        screen.blit(s, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def _draw_vfx(self, screen, vfx_type):
        for p in self.vfx_particles:
            ptype = p.get("type")
            
            if ptype == "smoke":
                s = pygame.Surface((p["size"], p["size"]), pygame.SRCALPHA)
                col = p.get("color", (50, 50, 50))
                pygame.draw.circle(s, (*col, p["alpha"]), (p["size"]//2, p["size"]//2), p["size"]//2)
                screen.blit(s, (p["x"], p["y"]))
            
            elif ptype == "ember":
                s = pygame.Surface((p["size"]*2, p["size"]*2), pygame.SRCALPHA)
                col = p.get("color", (255, 100, 50))
                # Glowing core
                pygame.draw.circle(s, (*col, p["alpha"]), (p["size"], p["size"]), p["size"])
                screen.blit(s, (p["x"], p["y"]))
                
            elif ptype == "rain":
                col = p.get("color", (150, 150, 200, 150))
                pygame.draw.line(screen, col, (p["x"], p["y"]), (p["x"]+p["vx"], p["y"]+p["len"]), 1)
                
            elif ptype == "magic_dust":
                s = pygame.Surface((p["size"]*2, p["size"]*2), pygame.SRCALPHA)
                col = p.get("color", (255, 255, 255))
                pygame.draw.circle(s, (*col, int(p["alpha"])), (p["size"], p["size"]), p["size"])
                screen.blit(s, (p["x"], p["y"]))
                
            elif ptype == "flash":
                s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                s.fill((255, 255, 255, p["alpha"]))
                screen.blit(s, (0, 0))
        
        # Special full-screen effects
        if vfx_type == "seams":
             if random.random() < 0.1:
                x1 = random.randint(0, SCREEN_WIDTH)
                y1 = random.randint(0, SCREEN_HEIGHT)
                x2 = x1 + random.randint(-200, 200)
                y2 = y1 + random.randint(-200, 200)
                pygame.draw.line(screen, (100, 255, 200), (x1, y1), (x2, y2), 2)

    def _draw_subtitle(self, screen, text):
        if not text: return
        box_h = 100
        y = SCREEN_HEIGHT - box_h - 20
        s = pygame.Surface((SCREEN_WIDTH, box_h), pygame.SRCALPHA)
        # Gradient background for text
        for i in range(box_h):
            alpha = int(200 * (i / box_h))
            pygame.draw.line(s, (0, 0, 0, alpha), (0, i), (SCREEN_WIDTH, i))
            
        screen.blit(s, (0, y))
        txt_surf = font_main.render(text, True, (255, 255, 255))
        rect = txt_surf.get_rect(center=(SCREEN_WIDTH // 2, y + box_h // 2))
        screen.blit(txt_surf, rect)