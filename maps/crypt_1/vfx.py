import pygame
import random
import math
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from assets.tiles.crypt_vfx import CryptFlies

class Bat:
    def __init__(self, x, y, facing_right):
        self.x = float(x)
        self.y = float(y)
        self.facing_right = facing_right
        
        if self.facing_right:
            self.vx = random.uniform(3, 6)
        else:
            self.vx = random.uniform(-6, -3)
            
        self.vy = random.uniform(-0.5, 0.5)
        self.timer = 0
        
    def update(self):
        self.x += self.vx
        self.y += self.vy + math.sin(self.timer * 0.2) * 1.5
        self.timer += 1
        
    def draw(self, screen, offset):
        # Draw a simple bat silhouette
        # Flap wings
        flap = math.sin(self.timer * 0.4)
        wing_y = -8 if flap > 0 else 2
        
        cx, cy = int(self.x - offset[0]), int(self.y - offset[1])
        
        color = (10, 5, 15) # Very dark
        
        # Body
        pygame.draw.circle(screen, color, (cx, cy), 3)
        
        # Wings
        wing_span = 12
        pts = []
        if not self.facing_right:
            # Flying left
            pts = [
                (cx + wing_span, cy + wing_y), # Right wing tip (back)
                (cx, cy),                      # Center
                (cx - wing_span, cy + wing_y)  # Left wing tip (front)
            ]
        else:
            pts = [
                (cx - wing_span, cy + wing_y),
                (cx, cy),
                (cx + wing_span, cy + wing_y)
            ]
            
        pygame.draw.lines(screen, color, False, pts, 2)

class MapVFX:
    def __init__(self):
        # Alustetaan kärpäset isolle alueelle
        self.map_width = 4000
        self.map_height = 3000
        self.flies = CryptFlies(4000, 3000, count=50)

        # --- DARKNESS ---
        self.darkness = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        # Tumma sinertävä/violetti sävy, alpha ~60-80
        self.darkness.fill((10, 10, 25, 70))
        
        # --- RAIN ---
        self.rain = []
        for _ in range(150):
            self.rain.append(self._make_drop())
            
        # --- FOG ---
        self.fog_blobs = []
        for _ in range(40):
            self.fog_blobs.append(self._make_fog())
            
        # --- BATS ---
        self.bats = []

    def _make_drop(self):
        return {
            'x': random.randint(0, SCREEN_WIDTH),
            'y': random.randint(-SCREEN_HEIGHT, SCREEN_HEIGHT),
            'speed': random.randint(12, 18),
            'len': random.randint(10, 25)
        }
        
    def _make_fog(self):
        return {
            'x': random.randint(0, self.map_width),
            'y': random.randint(0, self.map_height),
            'vx': random.uniform(0.2, 0.5) * (1 if random.random() < 0.5 else -1),
            'radius': random.randint(80, 160),
            'alpha': random.randint(15, 35)
        }

    def update(self, manager):
        self.flies.update()
        
        # Rain
        for r in self.rain:
            r['y'] += r['speed']
            r['x'] -= 1 # Wind
            if r['y'] > SCREEN_HEIGHT:
                r['y'] = random.randint(-50, -10)
                r['x'] = random.randint(0, SCREEN_WIDTH + 50)
                
        # Fog
        for f in self.fog_blobs:
            f['x'] += f['vx']
            # Wrap
            if f['x'] < -200: f['x'] = self.map_width + 200
            if f['x'] > self.map_width + 200: f['x'] = -200
            
        # Bats
        if random.random() < 0.008: # Spawn chance
            # Spawn relative to camera
            cam_x = manager.camera_x
            cam_y = manager.camera_y
            
            spawn_left = random.random() < 0.5
            start_x = (cam_x - 50) if spawn_left else (cam_x + SCREEN_WIDTH + 50)
            start_y = cam_y + random.randint(50, SCREEN_HEIGHT // 2)
            
            self.bats.append(Bat(start_x, start_y, facing_right=spawn_left))
            
        for b in self.bats[:]:
            b.update()
            # Remove if too far from camera
            if abs(b.x - manager.camera_x) > SCREEN_WIDTH * 1.5:
                self.bats.remove(b)

    def draw_floor(self, screen, offset):
        pass
        
    def draw_top(self, screen, offset):
        # 1. Flies (World Space - needs offset)
        self.flies.draw(screen, offset)
        
        # 2. Fog (World Space)
        for f in self.fog_blobs:
            # Draw only if visible
            sx = f['x'] - offset[0]
            sy = f['y'] - offset[1]
            r = f['radius']
            if -r*2 < sx < SCREEN_WIDTH + r*2 and -r*2 < sy < SCREEN_HEIGHT + r*2:
                s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                color = (200, 210, 200, f['alpha'])
                pygame.draw.circle(s, color, (r, r), r)
                screen.blit(s, (sx - r, sy - r))

        # 3. Bats (World Space)
        for b in self.bats:
            b.draw(screen, offset)

        # 4. Rain (Screen Space)
        for r in self.rain:
            start = (r['x'], r['y'])
            end = (r['x'] - 2, r['y'] + r['len'])
            pygame.draw.line(screen, (150, 150, 170), start, end, 1)

        # 5. Darkness (Screen Space - Topmost)
        screen.blit(self.darkness, (0, 0))