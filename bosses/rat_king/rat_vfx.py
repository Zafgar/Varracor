# bosses/rat_king/rat_vfx.py
import pygame
import random
import math

class RatVisualEffect(pygame.sprite.Sprite):
    def __init__(self, x, y, duration_ms):
        super().__init__()
        self.duration = duration_ms
        self.timer = 0
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.x = x
        self.y = y

    def update(self):
        self.timer += 16 # Oletus: 60fps (n. 16ms)
        if self.timer >= self.duration:
            self.kill()

# --- UUSI PROJEKTIILI ---
class AcidProjectile(RatVisualEffect):
    def __init__(self, start_pos, target_pos, vfx_manager):
        # Lasketaan kesto matkan perusteella (nopeus n. 8 pikseliä/frame)
        dist = math.hypot(target_pos[0]-start_pos[0], target_pos[1]-start_pos[1])
        frames = int(dist / 8)
        if frames < 30: frames = 30 # Minimi lentoaika
        
        super().__init__(start_pos[0], start_pos[1], duration_ms=frames * 16)
        
        self.start = pygame.math.Vector2(start_pos)
        self.target = pygame.math.Vector2(target_pos)
        self.manager = vfx_manager
        
        # Piirretään limapallo
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (50, 255, 50), (10, 10), 8) # Vihreä ydin
        pygame.draw.circle(self.image, (200, 255, 200), (8, 8), 3) # Kiilto
        
        self.rect = self.image.get_rect(center=start_pos)
        
        self.frames_total = frames
        self.frame_current = 0

    def update(self):
        self.frame_current += 1
        
        # 0.0 -> 1.0 (Missä kohdassa lentoa ollaan)
        t = self.frame_current / self.frames_total
        
        if t >= 1.0:
            # OSUMA MAAHAN!
            self.kill()
            # Luodaan lätäkkö kohteeseen (Käytetään VFXManagerin lattia-efektiä)
            self.manager.create_acid_puddle(self.target.x, self.target.y)
            return

        # Lineaarinen liike kohteeseen
        current_pos = self.start.lerp(self.target, t)
        
        # KAAREN LASKEMINEN (korkeus)
        # Parabeli: 4 * korkeus * t * (1-t)
        # Max korkeus 150px
        height = 150 * 4 * t * (1-t) 
        
        # Päivitä sijainti (y-akselilla miinus height, koska ylös on negatiivinen)
        self.rect.centerx = current_pos.x
        self.rect.centery = current_pos.y - height

# --- VANHAT EFEKTIT ---

class SlimePuddle(RatVisualEffect):
    def __init__(self, x, y, start_time_ignored=0):
        super().__init__(x, y, duration_ms=4000)
        self.width = 100
        self.height = 60
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.bubbles = []
        for _ in range(5): self._add_bubble()
            
    def _add_bubble(self):
        bx = random.randint(10, self.width - 10)
        by = random.randint(10, self.height - 10)
        size = random.randint(2, 5)
        self.bubbles.append([bx, by, size, random.uniform(0, 6.28)])

    def update(self):
        super().update()
        self.image.fill((0,0,0,0))
        pulse = math.sin(pygame.time.get_ticks() * 0.005) * 2
        alpha = 255
        if (self.duration - self.timer) < 1000:
            alpha = int(((self.duration - self.timer) / 1000) * 255)
            
        cx, cy = self.width // 2, self.height // 2
        pygame.draw.ellipse(self.image, (20, 60, 20, alpha), (cx - 40 - pulse, cy - 20 - pulse/2, 80 + pulse*2, 40 + pulse))
        pygame.draw.ellipse(self.image, (50, 200, 50, alpha), (cx - 35, cy - 15, 70, 30))
        
        for b in self.bubbles:
            b[3] += 0.1
            offset_y = math.sin(b[3]) * 2
            pygame.draw.circle(self.image, (150, 255, 150, alpha), (b[0], int(b[1] + offset_y)), b[2])
            
        if random.random() < 0.05:
            self.bubbles.pop(0)
            self._add_bubble()

class SummonSmoke(RatVisualEffect):
    def __init__(self, x, y, start_time_ignored=0):
        super().__init__(x, y, duration_ms=1000)
        self.image = pygame.Surface((100, 100), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.particles = []
        for _ in range(20):
            self.particles.append({
                'x': 50, 'y': 50,
                'vx': random.uniform(-2, 2), 'vy': random.uniform(-2, 2),
                'size': random.randint(5, 15), 'alpha': 255
            })

    def update(self):
        super().update()
        self.image.fill((0,0,0,0))
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['alpha'] -= 5
            p['size'] += 0.2
            if p['alpha'] > 0:
                pygame.draw.circle(self.image, (100, 100, 100, int(p['alpha'])), (int(p['x']), int(p['y'])), int(p['size']))