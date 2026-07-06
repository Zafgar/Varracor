import pygame
import math
import random

# --- PERUSLUOKKA ---
class WeaponEffect:
    def __init__(self, duration):
        self.duration = duration
        self.timer = duration
        self.is_finished = False

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.is_finished = True

    def draw(self, surface):
        pass

# --- NUOLI (BOWS) ---
class VisualArrow(WeaponEffect):
    def __init__(self, start_pos, target_pos, color=(200, 200, 200), speed=15):
        super().__init__(duration=60)
        self.pos = pygame.math.Vector2(start_pos)
        self.target = pygame.math.Vector2(target_pos)
        self.color = color
        
        # Lasketaan suunta ja nopeus
        direction = self.target - self.pos
        self.dist_total = direction.length()
        
        if self.dist_total > 0:
            self.velocity = direction.normalize() * speed
            self.angle = math.degrees(math.atan2(-direction.y, direction.x))
        else:
            self.velocity = pygame.math.Vector2(0, 0)
            
        self.dist_traveled = 0

    def update(self):
        self.pos += self.velocity
        self.dist_traveled += self.velocity.length()
        
        # Jos osui perille (tai meni ohi)
        if self.dist_traveled >= self.dist_total:
            self.is_finished = True
            
        super().update()

    def draw(self, surface):
        # Piirretään viiva ja kärki
        start = self.pos
        # Häntä osoittaa taaksepäin
        if self.velocity.length() > 0:
            tail = start - self.velocity.normalize() * 20
            pygame.draw.line(surface, self.color, start, tail, 2)
            pygame.draw.circle(surface, (255, 255, 255), (int(start.x), int(start.y)), 3)

# --- OSUMAKIPINÄT (SWORDS/HITS) ---
class ImpactSparks(WeaponEffect):
    def __init__(self, x, y, color=(255, 200, 50), count=6):
        super().__init__(duration=15)
        self.particles = []
        self.color = color
        
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 5)
            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "size": random.uniform(2, 4)
            })

    def update(self):
        super().update()
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["size"] *= 0.85 # Kutistuu

    def draw(self, surface):
        for p in self.particles:
            if p["size"] > 0.5:
                r = pygame.Rect(p["x"], p["y"], p["size"], p["size"])
                pygame.draw.rect(surface, self.color, r)

# --- DAMAGE TEXT (YLEINEN) ---
class DamageNumber(WeaponEffect):
    def __init__(self, x, y, text, color=(255, 255, 255)):
        super().__init__(duration=40)
        self.x = x
        self.y = y
        self.text = str(text)
        self.color = color
        self.font = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self.y_offset = 0

    def update(self):
        super().update()
        self.y_offset -= 0.5 # Leijuu ylös

    def draw(self, surface):
        alpha = int(255 * (self.timer / self.duration))
        img = self.font.render(self.text, True, self.color)
        img.set_alpha(alpha)
        surface.blit(img, (self.x - img.get_width()//2, self.y + self.y_offset))