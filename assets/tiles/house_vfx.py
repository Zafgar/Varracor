import pygame
import random
import math

class FireplaceEffect:
    """Savua ja valoa tulisijaan."""
    def __init__(self, x, y, spread=15, speed_y=-1.2):
        self.x = x
        self.y = y
        self.spread = spread
        self.speed_y = speed_y
        self.particles = []
        

    def update(self):
        # Lisää savua
        if random.random() < 0.3:
            self.particles.append({
                'x': self.x + random.uniform(-self.spread, self.spread),
                'y': self.y + 25, # Savu lähtee alempaa (tulisijan pesästä)
                'vx': random.uniform(-0.3, 0.3),
                'vy': random.uniform(self.speed_y - 0.3, self.speed_y + 0.3), # Nousee ylös
                'life': random.randint(80, 150),
                'size': random.randint(5, 10),
                'alpha': 120,
                'color': (80, 80, 80) # Harmaa
            })
            
        # Lisää kipinöitä (Sparks)
        if random.random() < 0.2:
             self.particles.append({
                'x': self.x + random.uniform(-self.spread, self.spread),
                'y': self.y + 30,
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(self.speed_y - 1.0, self.speed_y), # Nopeammin ylös
                'life': random.randint(20, 40),
                'size': random.randint(2, 4),
                'alpha': 255,
                'color': (255, 200, 50) # Kulta/Oranssi
            })
        
        # Päivitä hiukkaset
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            p['size'] += 0.05
            p['alpha'] = max(0, p['alpha'] - 0.8)
            if p['life'] <= 0:
                self.particles.remove(p)

    def draw(self, screen, offset):

        # 2. Savu
        for p in self.particles:
            sx = p['x'] - offset[0]
            sy = p['y'] - offset[1]
            s = pygame.Surface((int(p['size']), int(p['size'])), pygame.SRCALPHA)
            col = p.get('color', (80, 80, 80))
            s.fill((col[0], col[1], col[2], int(p['alpha'])))
            screen.blit(s, (sx, sy))

class CandleLight:
    """Pieni lepatteleva kynttilänvalo."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = random.uniform(0, 100)

    def update(self):
        self.timer += 0.1

    def draw(self, screen, offset):
        sx = self.x - offset[0]
        sy = self.y - offset[1]
        
        # Flicker (Lepatusta)
        flicker = math.sin(self.timer * 0.5) * 2 + math.cos(self.timer * 1.3) * 1.5
        r = 12 + flicker
        
        # Glow (Lämmin oranssi/keltainen)
        s = pygame.Surface((int(r*4), int(r*4)), pygame.SRCALPHA)
        # Outer soft glow
        pygame.draw.circle(s, (255, 160, 40, 30), (int(r*2), int(r*2)), int(r*1.5))
        # Inner bright glow
        pygame.draw.circle(s, (255, 220, 100, 60), (int(r*2), int(r*2)), int(r*0.8))
        
        screen.blit(s, (sx - r*2, sy - r*2))

class SteamParticle:
    """Pieni nouseva höyry ruoasta."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-0.2, 0.2)
        self.vy = random.uniform(-0.8, -0.4)
        self.life = random.randint(40, 80)
        self.size = random.randint(2, 5)
        self.alpha = 150

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.alpha = max(0, self.alpha - 2)

    def draw(self, screen, offset):
        s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        s.fill((200, 200, 200, self.alpha))
        screen.blit(s, (self.x - offset[0], self.y - offset[1]))

class HouseVFX:
    """Hallinnoi sisätilojen efektejä (Pöly + Tulisijat)."""
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.effects = [] # Tulisijat yms.
        self.particles = []
        self.candles = [] # Kynttilät
        self.steam = [] # Ruoan höyry
        for _ in range(50):
            self.particles.append(self._make_particle())

    def add_fireplace(self, x, y, spread=15, speed_y=-1.2):
        self.effects.append(FireplaceEffect(x, y, spread, speed_y))

    def add_candle(self, x, y):
        self.candles.append(CandleLight(x, y))

    def add_steam(self, x, y):
        self.steam.append(SteamParticle(x, y))

    def _make_particle(self):
        return {
            'x': random.randint(0, self.w),
            'y': random.randint(0, self.h),
            'vx': random.uniform(-0.2, 0.2),
            'vy': random.uniform(-0.1, 0.1),
            'size': random.randint(1, 3),
            'alpha': random.randint(50, 150),
            'phase': random.uniform(0, 6.28)
        }

    def update(self):
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['phase'] += 0.05
            
            # Kellunta
            p['y'] += math.sin(p['phase']) * 0.1
            
            # Wrap
            if p['x'] < 0: p['x'] = self.w
            if p['x'] > self.w: p['x'] = 0
            if p['y'] < 0: p['y'] = self.h
            if p['y'] > self.h: p['y'] = 0

        for e in self.effects:
            e.update()
            
        for c in self.candles:
            c.update()
            
        for s in self.steam[:]:
            s.update()
            if s.life <= 0:
                self.steam.remove(s)

    def draw(self, screen, offset=(0,0)):
        for p in self.particles:
            sx = p['x'] - offset[0]
            sy = p['y'] - offset[1]
            
            s = pygame.Surface((p['size'], p['size']), pygame.SRCALPHA)
            s.fill((255, 255, 200, p['alpha'])) # Kellertävä pöly
            screen.blit(s, (sx, sy))
            
        for e in self.effects:
            e.draw(screen, offset)
            
        for c in self.candles:
            c.draw(screen, offset)
            
        for s in self.steam:
            s.draw(screen, offset)
