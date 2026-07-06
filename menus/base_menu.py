# menus/base_menu.py
import pygame
import random
import math
from settings import CHEAT_MODE
from tools.map_editor import MapEditor
from ui_kit import draw_text, font_small, WHITE, GOLD_COLOR

class BaseMenu:
    """
    Yhteinen menupohja:
    - next_state vaihto
    - kevyt, tyylikäs tausta (gradient + vignette + liikkuvat partikkelit)
    - soft panel helper (lasimainen paneeli)
    """

    def __init__(self, game_manager):
        self.manager = game_manager
        self.next_state = None

        # --- background cache ---
        self._bg_cache = {}   # key: (w,h,mood) -> Surface
        self._rng = random.Random(1337)

        # liikkuvat "dust" partikkelit
        self._bg_particles = []
        self._bg_init_particles(70)

        self._bg_t = 0.0

        # --- MAP EDITOR ---
        if CHEAT_MODE:
            self.map_editor = MapEditor(self.manager)

    def handle_event(self, event):
        pass

    def update(self):
        # Monet menut ei kutsu updatea -> piirrossa myös liikkuu,
        # mutta pidetään tämä varalta.
        self._bg_t += 1.0 / 60.0
        
        # Editor Update
        if CHEAT_MODE and hasattr(self, "map_editor") and self.map_editor.active:
            # Pass camera offset if available
            cam_x = getattr(self.manager, "camera_x", 0)
            cam_y = getattr(self.manager, "camera_y", 0)
            self.map_editor.update()

    def handle_editor_event(self, event):
        """Helper to call from child classes handle_event"""
        if CHEAT_MODE and hasattr(self, "map_editor"):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F8:
                self.map_editor.toggle()
                return True
            
            if self.map_editor.active:
                return self.map_editor.handle_event(event)
        return False

    # -------------------------
    # THEME BACKGROUND
    # -------------------------
    def _bg_init_particles(self, count):
        self._bg_particles.clear()
        for _ in range(count):
            self._bg_particles.append({
                "x": self._rng.uniform(0, 1280),
                "y": self._rng.uniform(0, 720),
                "vx": self._rng.uniform(8, 22),
                "vy": self._rng.uniform(-3, 3),
                "r": self._rng.uniform(1.0, 2.4),
                "a": self._rng.randint(25, 70),
            })

    def _theme_colors(self, mood: str):
        # (top, bottom, accent)
        if mood == "city":
            return (18, 18, 28), (10, 10, 16), (180, 160, 90)
        if mood == "guild":
            return (14, 20, 28), (8, 10, 14), (200, 200, 255)
        if mood == "forge":
            return (28, 16, 14), (12, 8, 8), (220, 160, 60)
        if mood == "quest":
            return (16, 26, 18), (8, 12, 10), (140, 220, 150)
        return (16, 16, 22), (8, 8, 12), (200, 180, 100)

    def _get_bg_surface(self, w, h, mood: str):
        key = (w, h, mood)
        if key in self._bg_cache:
            return self._bg_cache[key]

        top, bottom, _accent = self._theme_colors(mood)

        surf = pygame.Surface((w, h)).convert()
        # gradient fill
        for y in range(h):
            t = y / max(1, h - 1)
            r = int(top[0] * (1 - t) + bottom[0] * t)
            g = int(top[1] * (1 - t) + bottom[1] * t)
            b = int(top[2] * (1 - t) + bottom[2] * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (w, y))

        # vignette overlay
        vig = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w * 0.5, h * 0.5
        maxd = math.hypot(cx, cy)
        step = 28  # iso askel = kevyt
        for y in range(0, h, step):
            for x in range(0, w, step):
                d = math.hypot(x - cx, y - cy) / maxd
                a = int(140 * (d ** 1.6))
                if a > 0:
                    pygame.draw.rect(vig, (0, 0, 0, a), (x, y, step, step))
        surf.blit(vig, (0, 0))

        self._bg_cache[key] = surf
        return surf

    def draw_themed_background(self, screen, mood="city"):
        w, h = screen.get_size()
        base = self._get_bg_surface(w, h, mood)
        screen.blit(base, (0, 0))

        # animate particles (dust / embers)
        top, bottom, accent = self._theme_colors(mood)
        self._bg_t += 1.0 / 60.0

        # skaalataan partikkelit jos resoluutio muuttuu
        if not self._bg_particles:
            self._bg_init_particles(70)

        # piirretään omalle overlaylle (alpha)
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)

        for p in self._bg_particles:
            # suhteuta alkuarvot screeniin
            if p["x"] > w: p["x"] = self._rng.uniform(0, w)
            if p["y"] > h: p["y"] = self._rng.uniform(0, h)

            p["x"] += p["vx"] * (1.0 / 60.0)
            p["y"] += p["vy"] * (1.0 / 60.0)

            if p["x"] > w + 30:
                p["x"] = -30
                p["y"] = self._rng.uniform(0, h)
            if p["y"] < -30: p["y"] = h + 30
            if p["y"] > h + 30: p["y"] = -30

            # pieni “twinkle”
            tw = (math.sin(self._bg_t * 2.4 + p["y"] * 0.01) + 1) * 0.5
            a = int(p["a"] * (0.6 + 0.6 * tw))
            col = (accent[0], accent[1], accent[2], a)
            pygame.draw.circle(overlay, col, (int(p["x"]), int(p["y"])), int(p["r"]))

        screen.blit(overlay, (0, 0))

    # -------------------------
    # UI HELPERS
    # -------------------------
    def draw_soft_panel(self, screen, rect: pygame.Rect, alpha=110, border_alpha=140, radius=16):
        panel = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (20, 20, 28, alpha), panel.get_rect(), border_radius=radius)
        pygame.draw.rect(panel, (255, 255, 255, border_alpha), panel.get_rect(), width=2, border_radius=radius)
        screen.blit(panel, rect.topleft)

    def draw_header_bar(self, screen, title_surf, y=30):
        w, _h = screen.get_size()
        bar = pygame.Surface((w, 84), pygame.SRCALPHA)
        pygame.draw.rect(bar, (0, 0, 0, 140), bar.get_rect(), border_radius=0)
        screen.blit(bar, (0, y))
        screen.blit(title_surf, (w // 2 - title_surf.get_width() // 2, y + 18))

    def draw_editor(self, screen):
        """Draws the map editor overlay if active."""
        if CHEAT_MODE and hasattr(self, "map_editor") and self.map_editor.active:
            self.map_editor.draw(screen)
            
            # --- OVERLAY: Unit Names & Teams ---
            cam_x = getattr(self.manager, "camera_x", 0)
            cam_y = getattr(self.manager, "camera_y", 0)
            
            # 1. Existing Units
            if self.manager.current_arena:
                for p in self.manager.current_arena.props:
                    # Only draw if unit (has team_color)
                    if not hasattr(p, "team_color"): continue
                    
                    # FIX: Ensure it is a valid color tuple (skip strings like "Neutral" or None)
                    col = p.team_color
                    if not isinstance(col, (tuple, list)): continue
                    if len(col) < 3: continue
                    
                    # FIX: Älä piirrä kuolleiden päälle
                    if getattr(p, "is_dead", False): continue
                    
                    sx = p.rect.centerx - cam_x
                    sy = p.rect.top - cam_y
                    
                    if -50 < sx < screen.get_width() + 50 and -50 < sy < screen.get_height() + 50:
                        draw_text(getattr(p, "name", "Unit"), font_small, WHITE, screen, sx - 20, sy - 25)
                        pygame.draw.circle(screen, col, (sx, sy - 35), 6)
                        pygame.draw.circle(screen, WHITE, (sx, sy - 35), 7, 1)

            # 2. Ghost Unit (Placement)
            ghost = getattr(self.map_editor, "ghost_instance", None)
            if ghost:
                # Use image_pos for ghost as it tracks mouse in editor
                gx, gy = getattr(ghost, "image_pos", (0,0))
                sx = gx - cam_x + (ghost.image.get_width() // 2 if ghost.image else 0)
                sy = gy - cam_y
                
                # Get current editor color safely
                t_idx = getattr(self.map_editor, "team_color_idx", 0)
                t_colors = getattr(self.map_editor, "team_colors", [])
                current_col = WHITE
                if 0 <= t_idx < len(t_colors):
                    current_col = t_colors[t_idx][1]
                
                draw_text(getattr(ghost, "name", "Unit"), font_small, GOLD_COLOR, screen, sx - 20, sy - 45)
                pygame.draw.circle(screen, current_col, (sx, sy - 55), 8)
                pygame.draw.circle(screen, WHITE, (sx, sy - 55), 9, 1)
                
                # Team Name
                if 0 <= t_idx < len(t_colors):
                    draw_text(t_colors[t_idx][0], font_small, current_col, screen, sx - 30, sy - 65)
