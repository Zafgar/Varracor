import pygame
import random
import math
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

class SwampBubble:
    def __init__(self, map_w, map_h):
        self.x = random.randint(0, map_w)
        self.y = random.randint(0, map_h)
        self.size = 0
        self.max_size = random.randint(4, 8)
        self.timer = 0
        self.life = random.randint(60, 120)
        self.popped = False

    def update(self):
        self.timer += 1
        if not self.popped:
            # Kasvaa
            if self.size < self.max_size:
                self.size += 0.1
            # Puhkeaa lopussa
            if self.timer > self.life:
                self.popped = True
                self.timer = 0 # Reset timer for pop animation
        else:
            # Puhkeamis-animaatio (katoaa)
            if self.timer > 10:
                return False # Dead
        return True

    def draw(self, screen, offset):
        rx = self.x - offset[0]
        ry = self.y - offset[1]
        
        if -10 < rx < SCREEN_WIDTH + 10 and -10 < ry < SCREEN_HEIGHT + 10:
            if not self.popped:
                # Piirrä kupla
                pygame.draw.circle(screen, (100, 150, 100), (rx, ry), int(self.size), 1)
                pygame.draw.circle(screen, (150, 200, 150), (rx - 1, ry - 1), 1) # Highlight
            else:
                # "Pop" rengas
                r = int(self.size + self.timer)
                pygame.draw.circle(screen, (150, 200, 150), (rx, ry), r, 1)

class Firefly:
    """Hehkuva tulikärpänen, joka vilkkuu hitaasti."""
    def __init__(self, map_w, map_h):
        self.x = random.randint(0, map_w)
        self.y = random.randint(0, map_h)
        self.z = random.uniform(0, 100) # Vaiheistus vilkkumiselle
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, 0.5)
        self.map_w = map_w
        self.map_h = map_h

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.z += 0.05 # Vilkkumisnopeus
        
        # Wrap around
        if self.x < 0: self.x = self.map_w
        if self.x > self.map_w: self.x = 0
        if self.y < 0: self.y = self.map_h
        if self.y > self.map_h: self.y = 0

    def draw(self, screen, offset):
        # Laske alpha siniaallolla (0..255)
        alpha = (math.sin(self.z) + 1) * 0.5 * 255
        if alpha < 20: return # Ei piirretä jos liian himmeä
        
        sx = self.x - offset[0]
        sy = self.y - offset[1]
        
        if -10 < sx < SCREEN_WIDTH + 10 and -10 < sy < SCREEN_HEIGHT + 10:
            s = pygame.Surface((6, 6), pygame.SRCALPHA)
            # Kellertävän vihreä hehku
            col = (200, 255, 100, int(alpha))
            # Ydin
            pygame.draw.circle(s, (255, 255, 200, int(alpha)), (3, 3), 1)
            # Hehku
            pygame.draw.circle(s, col, (3, 3), 3)
            screen.blit(s, (sx - 3, sy - 3))

class MosquitoSwarm:
    """
    Hyttysparvi. Joukko pieniä pisteitä jotka liikkuvat ryppäässä.
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.bugs = []
        for _ in range(10): # 10 hyttystä per parvi
            self.bugs.append({
                'off_x': random.randint(-20, 20),
                'off_y': random.randint(-20, 20),
                'speed': random.uniform(0.1, 0.3),
                'phase': random.uniform(0, 6.28)
            })
        self.timer = random.uniform(0, 100)

    def update(self):
        self.timer += 0.05
        # Parvi ajelehtii hitaasti
        self.x += math.sin(self.timer) * 0.2
        self.y += math.cos(self.timer * 0.7) * 0.2
        
        # Yksittäiset hyttyset pörräävät
        for b in self.bugs:
            b['phase'] += b['speed']
            b['off_x'] += math.sin(b['phase']) * 0.5
            b['off_y'] += math.cos(b['phase']) * 0.5
            
            # Pidetään ne kasassa (vetovoima keskustaan)
            if b['off_x'] > 25: b['off_x'] -= 0.5
            if b['off_x'] < -25: b['off_x'] += 0.5
            if b['off_y'] > 25: b['off_y'] -= 0.5
            if b['off_y'] < -25: b['off_y'] += 0.5

    def draw(self, screen, offset):
        sx = self.x - offset[0]
        sy = self.y - offset[1]
        
        # Optimointi
        if not (-50 < sx < SCREEN_WIDTH + 50 and -50 < sy < SCREEN_HEIGHT + 50):
            return
            
        for b in self.bugs:
            bx = sx + b['off_x']
            by = sy + b['off_y']
            # Musta pieni piste (hyttynen)
            pygame.draw.rect(screen, (10, 10, 10), (bx, by, 2, 2))

class SwampGas:
    """Vihreä kaasupilvi joka nousee maasta."""
    def __init__(self, map_w, map_h):
        self.x = random.randint(0, map_w)
        self.y = random.randint(0, map_h)
        self.radius = random.randint(10, 30)
        self.alpha = 0
        self.life = random.randint(100, 200)
        self.timer = 0
        self.vy = random.uniform(-0.5, -0.2) # Nousee ylös

    def update(self):
        self.y += self.vy
        self.timer += 1
        
        # Fade in / Fade out
        if self.timer < 30:
            self.alpha = int((self.timer / 30) * 100)
        elif self.timer > self.life - 30:
            self.alpha = int(((self.life - self.timer) / 30) * 100)
        
        return self.timer < self.life

    def draw(self, screen, offset):
        sx = self.x - offset[0]
        sy = self.y - offset[1]
        
        if -50 < sx < SCREEN_WIDTH + 50 and -50 < sy < SCREEN_HEIGHT + 50:
            s = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
            # Myrkyllisen vihreä
            pygame.draw.circle(s, (50, 100, 50, self.alpha), (self.radius, self.radius), self.radius)
            screen.blit(s, (sx - self.radius, sy - self.radius))

class CloudShadow:
    """Iso pilven varjo joka liikkuu maassa."""
    def __init__(self, map_w, map_h):
        self.x = random.randint(0, map_w)
        self.y = random.randint(0, map_h)
        self.w = random.randint(400, 800)
        self.h = random.randint(200, 500)
        self.speed = random.uniform(0.5, 1.5)
        self.map_w = map_w
        
        self.image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        # Musta ellipsi, alpha 40 (haalea varjo)
        pygame.draw.ellipse(self.image, (0, 0, 0, 40), (0, 0, self.w, self.h))

    def update(self):
        self.x += self.speed
        if self.x > self.map_w:
            self.x = -self.w

    def draw(self, screen, offset):
        sx = self.x - offset[0]
        sy = self.y - offset[1]
        if -self.w < sx < SCREEN_WIDTH and -self.h < sy < SCREEN_HEIGHT:
            screen.blit(self.image, (sx, sy))

class MapVFX:
    def __init__(self):
        self.map_width = int(SCREEN_WIDTH * 4.0)
        self.map_height = int(SCREEN_HEIGHT * 4.0)
        
        # Sumu
        self.fog_layers = []
        for _ in range(80):
            self.fog_layers.append(self._make_fog())
            
        # Kuplat
        self.bubbles = []
        
        # Kaasu
        self.gas_clouds = []
        
        # Hyttysparvet (n. 40 parvea ympäri karttaa)
        self.swarms = []
        for _ in range(100):
            self.swarms.append(MosquitoSwarm(random.randint(0, self.map_width), random.randint(0, self.map_height)))
            
        # Tulikärpäset (n. 60 kpl)
        self.fireflies = [Firefly(self.map_width, self.map_height) for _ in range(150)]

        # Pilvien varjot
        self.cloud_shadows = []
        for _ in range(15):
            self.cloud_shadows.append(CloudShadow(self.map_width, self.map_height))

    def _make_fog(self):
        return {
            'x': random.randint(0, self.map_width),
            'y': random.randint(0, self.map_height),
            'vx': random.uniform(0.2, 0.6),
            'vy': random.uniform(-0.1, 0.1),
            'radius': random.randint(150, 300),
            'alpha': random.randint(15, 30) # Hieman näkyvämpi
        }

    def update(self, manager):
        # Sumu liikkuu hitaasti
        for f in self.fog_layers:
            f['x'] += f['vx']
            f['y'] += f['vy']
            if f['x'] > self.map_width + 200: f['x'] = -200
            if f['y'] > self.map_height + 200: f['y'] = -200
            if f['y'] < -200: f['y'] = self.map_height + 200
            
        # Kuplat
        if random.random() < 0.1: # Uusi kupla
            self.bubbles.append(SwampBubble(self.map_width, self.map_height))
            
        self.bubbles = [b for b in self.bubbles if b.update()]
        
        # Kaasu
        if random.random() < 0.05:
            self.gas_clouds.append(SwampGas(self.map_width, self.map_height))
        self.gas_clouds = [g for g in self.gas_clouds if g.update()]
        
        for s in self.swarms: s.update()
        for f in self.fireflies: f.update()
        for c in self.cloud_shadows: c.update()

    def draw_floor(self, screen, offset):
        # Kuplat piirretään lattian päälle, mutta hahmojen alle
        for b in self.bubbles:
            b.draw(screen, offset)
        # Kaasu myös hahmojen alle (tai päälle, riippuu mausta, tässä alla)
        for g in self.gas_clouds:
            g.draw(screen, offset)

    def draw_top(self, screen, offset):
        # Pilvien varjot (piirretään kaiken päälle, mutta haaleana)
        for c in self.cloud_shadows:
            c.draw(screen, offset)

        # Sumu piirretään kaiken päälle
        for f in self.fog_layers:
            sx = f['x'] - offset[0]
            sy = f['y'] - offset[1]
            r = f['radius']
            
            # Optimointi: Piirrä vain jos ruudulla
            if -r*2 < sx < SCREEN_WIDTH + r*2 and -r*2 < sy < SCREEN_HEIGHT + r*2:
                s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                # Vihertävä sumu
                color = (180, 200, 180, f['alpha'])
                pygame.draw.circle(s, color, (r, r), r)
                screen.blit(s, (sx - r, sy - r))
        
        # Hyttyset
        for s in self.swarms:
            s.draw(screen, offset)
            
        # Tulikärpäset (hohtavat pimeässä)
        for f in self.fireflies:
            f.draw(screen, offset)
